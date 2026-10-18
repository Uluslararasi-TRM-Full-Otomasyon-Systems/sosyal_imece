"""Publish explicitly approved product drafts to the TRM store API."""

import ast
import json
import logging
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import requests
from trm_live_config import get_live_settings, load_trm_environment


logger = logging.getLogger(__name__)


class MagazaAPIBridge:
    """Read approved product tasks from SQLite and submit them to the store."""

    def __init__(
        self,
        db_path="trm_dispatch_queue.db",
        api_base_url=None,
        token_url=None,
        client_id=None,
        client_secret=None,
        access_token=None,
        queue_table="task_queue",
        simulate=None,
        timeout=20,
        session=None,
    ):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", queue_table):
            raise ValueError("Gecersiz SQLite kuyruk tablo adi")
        load_trm_environment(Path(__file__).resolve().parent)
        live_settings = get_live_settings()["store"]
        self.db_path = str(db_path)
        self.api_base_url = (api_base_url or live_settings["api_base_url"] or "https://api.trendurunlermarket.com/v1").rstrip("/")
        self.token_url = token_url or live_settings["token_url"] or f"{self.api_base_url}/oauth/token"
        self.client_id = client_id or live_settings["client_id"]
        self.client_secret = client_secret or live_settings["client_secret"]
        self.access_token = access_token or live_settings["access_token"]
        self.queue_table = queue_table
        self.simulate = not live_settings["requested_live"] if simulate is None else bool(simulate)
        self.live_configuration_missing = []
        if not self.simulate:
            if not (api_base_url or live_settings["api_base_url"]):
                self.live_configuration_missing.append("TRM_STORE_API_BASE_URL")
            has_token = bool(self.access_token)
            has_oauth = bool(self.client_id and self.client_secret and (token_url or live_settings["token_url"]))
            if not (has_token or has_oauth):
                self.live_configuration_missing.append(
                    "TRM_STORE_ACCESS_TOKEN veya client_id/client_secret/token_url"
                )
        self.timeout = timeout
        self.session = session or requests.Session()

    @staticmethod
    def _parse_payload(value):
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _approved(row, payload):
        candidates = [row.get("status"), payload.get("status"), payload.get("approval_status")]
        for key in ("approval", "moderation"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.extend((nested.get("status"), nested.get("decision")))
            elif isinstance(nested, str):
                candidates.append(nested)
        return any(str(value or "").strip().casefold() == "approved" for value in candidates)

    @staticmethod
    def _product(payload):
        for key in ("product", "product_draft", "urun", "urun_taslagi", "draft"):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                return candidate
        product_keys = {"title", "name", "urun_adi", "price", "fiyat"}
        return payload if product_keys.intersection(payload) else None

    def _read_approved(self, connection):
        rows = connection.execute(f'SELECT * FROM "{self.queue_table}"').fetchall()
        columns = [column[1] for column in connection.execute(
            f'PRAGMA table_info("{self.queue_table}")'
        ).fetchall()]
        approved = []
        for values in rows:
            row = dict(zip(columns, values))
            stored_payload = self._parse_payload(row.get("payload"))
            payload = stored_payload.get("payload", stored_payload)
            if not isinstance(payload, dict):
                continue
            product = self._product(payload)
            task_type = str(payload.get("task_type", "")).casefold()
            is_product = product is not None or "product" in task_type or "urun" in task_type
            if self._approved(row, payload) and is_product and product:
                approved.append((row, payload, product))
        return approved

    def _authenticate(self):
        if self.simulate:
            return "simulated-access-token"
        if self.access_token:
            return self.access_token
        if not self.client_id or not self.client_secret:
            raise ValueError("Canli OAuth icin client_id ve client_secret gereklidir")
        response = self.session.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValueError("OAuth yanitinda access_token bulunamadi")
        return token

    def publish_approved_products(self):
        result = {"durum": "completed", "simulasyon": self.simulate, "gonderilen": 0, "kayitlar": [], "hatalar": []}
        if self.live_configuration_missing:
            result["durum"] = "error"
            result["hatalar"].append({
                "error": "Canlı mağaza yapılandırması eksik: " + ", ".join(self.live_configuration_missing)
            })
            return result
        try:
            with closing(sqlite3.connect(self.db_path)) as connection:
                connection.row_factory = sqlite3.Row
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS magaza_api_submissions (
                        source_key TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        response_json TEXT,
                        submitted_at TEXT NOT NULL
                    )"""
                )
                approved = self._read_approved(connection)
                if not self.simulate:
                    live_approved = []
                    for record in approved:
                        row, payload, _product = record
                        if payload.get("affiliate_link_status") == "fallback_redirect":
                            result["hatalar"].append({
                                "source_key": str(row.get("post_id") or row.get("id") or ""),
                                "error": "Komisyon ortaklığı doğrulanmamış fallback yönlendirme canlı mağazaya gönderilmedi",
                            })
                        else:
                            live_approved.append(record)
                    approved = live_approved
                token = self._authenticate() if approved and not self.simulate else None
                for row, _payload, product in approved:
                    source_key = str(row.get("post_id") or row.get("id") or "")
                    if not source_key:
                        result["hatalar"].append({"source_key": "", "error": "Kuyruk kaydinda id/post_id yok"})
                        continue
                    already_sent = connection.execute(
                        "SELECT 1 FROM magaza_api_submissions WHERE source_key = ? AND status = 'submitted'",
                        (source_key,),
                    ).fetchone()
                    if already_sent:
                        continue
                    if self.simulate:
                        result["kayitlar"].append({"source_key": source_key, "durum": "simulated", "product": product})
                        continue
                    try:
                        response = self.session.post(
                            f"{self.api_base_url}/products",
                            json=product,
                            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                            timeout=self.timeout,
                        )
                        response.raise_for_status()
                        try:
                            response_body = response.json()
                        except ValueError:
                            response_body = {"response": response.text[:1000]}
                        connection.execute(
                            "INSERT OR REPLACE INTO magaza_api_submissions (source_key, status, response_json, submitted_at) VALUES (?, 'submitted', ?, ?)",
                            (source_key, json.dumps(response_body, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
                        )
                        result["gonderilen"] += 1
                        result["kayitlar"].append({"source_key": source_key, "durum": "submitted", "response": response_body})
                    except requests.RequestException as exc:
                        logger.exception("Onayli urun magazaya gonderilemedi")
                        result["hatalar"].append({"source_key": source_key, "error": f"{exc.__class__.__name__}: {exc}"})
                connection.commit()
        except (requests.RequestException, sqlite3.Error, OSError, ValueError) as exc:
            logger.exception("Magaza API kuyrugu islenemedi")
            result["durum"] = "error"
            result["hatalar"].append({"error": f"{exc.__class__.__name__}: {exc}"})
        if result["hatalar"] and result["durum"] != "error":
            result["durum"] = "partial_error"
        return result


if __name__ == "__main__":
    print(json.dumps(MagazaAPIBridge().publish_approved_products(), ensure_ascii=False, indent=2))