"""Idempotent distribution outbox for approved TRM affiliate campaigns."""

import ast
import json
import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
from trm_live_config import get_live_settings, load_trm_environment


logger = logging.getLogger(__name__)


class AutonomousDistributionEngine:
    DEFAULT_SIMULATION_CHANNELS = ("telegram", "social_media", "external_api")

    def __init__(self, db_path="trm_kuyruk.db", mode=None, channels=None, session=None, timeout=15):
        load_trm_environment(Path(__file__).resolve().parent)
        live_settings = get_live_settings()["distribution"]
        mode = mode or live_settings["mode"]
        if mode not in {"simulate", "live"}:
            raise ValueError("mode 'simulate' veya 'live' olmalidir")
        self.db_path = str(db_path)
        self.mode = mode
        self.channels = channels
        if self.channels is None and mode == "live":
            self.channels = live_settings["channels"]
        self.session = session or requests.Session()
        self.timeout = timeout

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

    def _channel_targets(self):
        if self.channels is None:
            if self.mode == "simulate":
                return {name: {} for name in self.DEFAULT_SIMULATION_CHANNELS}
            return {}
        if isinstance(self.channels, dict):
            return self.channels
        if isinstance(self.channels, (list, tuple)):
            return {str(name): {} for name in self.channels}
        raise ValueError("channels bir kanal listesi veya yapılandırma sözlüğü olmalıdır")

    def _send_live(self, channel, config, message, payload):
        config = config if isinstance(config, dict) else {}
        if channel.casefold() == "telegram":
            token = config.get("bot_token")
            chat_id = config.get("chat_id")
            if not token or not chat_id:
                raise ValueError("Telegram canlı aktarımı bot_token ve chat_id gerektirir")
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            body = {"chat_id": chat_id, "text": message, "disable_web_page_preview": False}
        else:
            url = str(config.get("webhook_url") or "")
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError(f"{channel} canlı aktarımı için güvenli HTTPS webhook_url gereklidir")
            body = {
                "event": "affiliate_campaign_approved",
                "channel": channel,
                "product": payload.get("product"),
                "hooks": payload.get("social_media_hooks", []),
                "affiliate_url": payload.get("affiliate_link_draft"),
                "message": message,
            }
        response = self.session.post(
            url,
            json=body,
            headers=config.get("headers", {}),
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            return response.json()
        except (ValueError, AttributeError):
            return {"http_status": getattr(response, "status_code", None)}

    @staticmethod
    def _load_processed_tasks(connection, processed_source_keys):
        rows = connection.execute(
            "SELECT id, post_id, payload FROM task_queue "
            "WHERE account_id = 'trm_hizli_kazanc' AND status = 'approved' ORDER BY id"
        ).fetchall()
        tasks = []
        for queue_id, post_id, stored_text in rows:
            stored = AutonomousDistributionEngine._parse_payload(stored_text)
            payload = stored.get("payload", stored)
            if not isinstance(payload, dict):
                continue
            if payload.get("etiket") != "gelir_getiren_gorev" or payload.get("status") != "approved":
                continue
            if processed_source_keys is not None and post_id not in processed_source_keys:
                continue
            tasks.append((queue_id, post_id, payload))
        return tasks

    def distribute_processed(self, store_result):
        result = {
            "durum": "completed",
            "mode": self.mode,
            "incelenen": 0,
            "dagitilan": 0,
            "yinelenen_atlandi": 0,
            "hatalar": [],
            "kanal_sonuclari": [],
        }
        try:
            if not isinstance(store_result, dict):
                raise ValueError("Mağaza köprüsü sonucu sözlük olmalıdır")
            processed = [
                item.get("source_key")
                for item in store_result.get("kayitlar", [])
                if item.get("durum") in {"simulated", "submitted"} and item.get("source_key")
            ]
            processed_source_keys = set(processed)
            targets = self._channel_targets()
            if self.mode == "live" and not targets:
                result["durum"] = "error"
                result["hatalar"].append({"error": "Canlı dağıtım için en az bir kanal yapılandırılmalıdır"})
                return result

            with closing(sqlite3.connect(self.db_path, timeout=10)) as connection:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS distribution_outbox (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_key TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT NOT NULL,
                        affiliate_url TEXT,
                        response_json TEXT,
                        created_at TEXT NOT NULL,
                        UNIQUE(source_key, channel, mode)
                    )"""
                )
                connection.commit()
                tasks = self._load_processed_tasks(connection, processed_source_keys)
                result["incelenen"] = len(tasks)

                for _queue_id, source_key, payload in tasks:
                    product = payload.get("product") or {}
                    hooks = payload.get("social_media_hooks") or []
                    affiliate_url = payload.get("affiliate_link_draft") or product.get("affiliate_url")
                    if self.mode == "live" and (
                        payload.get("affiliate_link_status") == "fallback_redirect"
                        or payload.get("commission_eligible") is False
                    ):
                        result["hatalar"].append({
                            "source_key": source_key,
                            "error": "Komisyon ortaklığı doğrulanmamış fallback canlı trafik kanallarına gönderilmedi",
                        })
                        continue
                    if not hooks or not affiliate_url:
                        result["hatalar"].append({"source_key": source_key, "error": "Kanca veya affiliate yönlendirmesi eksik"})
                        continue
                    message = f"{str(hooks[0]).strip()}\n\n{affiliate_url}"

                    for channel, config in targets.items():
                        existing = connection.execute(
                            "SELECT status FROM distribution_outbox WHERE source_key = ? AND channel = ? AND mode = ?",
                            (source_key, str(channel), self.mode),
                        ).fetchone()
                        if existing and existing[0] in {"simulated", "sent"}:
                            result["yinelenen_atlandi"] += 1
                            continue
                        try:
                            if self.mode == "simulate":
                                status = "simulated"
                                response_body = {"queued": True, "channel": str(channel)}
                            else:
                                response_body = self._send_live(str(channel), config, message, payload)
                                status = "sent"
                            connection.execute(
                                """INSERT INTO distribution_outbox
                                   (source_key, channel, mode, status, message, affiliate_url, response_json, created_at)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                   ON CONFLICT(source_key, channel, mode) DO UPDATE SET
                                       status = excluded.status,
                                       message = excluded.message,
                                       affiliate_url = excluded.affiliate_url,
                                       response_json = excluded.response_json,
                                       created_at = excluded.created_at""",
                                (
                                    source_key,
                                    str(channel),
                                    self.mode,
                                    status,
                                    message,
                                    str(affiliate_url),
                                    json.dumps(response_body, ensure_ascii=False),
                                    datetime.now(timezone.utc).isoformat(),
                                ),
                            )
                            connection.commit()
                            result["dagitilan"] += 1
                            result["kanal_sonuclari"].append({
                                "source_key": source_key,
                                "channel": str(channel),
                                "status": status,
                            })
                        except Exception as exc:
                            connection.rollback()
                            logger.exception("Kampanya dağıtımı başarısız: %s", channel)
                            result["hatalar"].append({
                                "source_key": source_key,
                                "channel": str(channel),
                                "error": f"{exc.__class__.__name__}: {exc}",
                            })
        except (sqlite3.Error, OSError, ValueError, requests.RequestException) as exc:
            logger.exception("Otonom dağıtım katmanı çalıştırılamadı")
            result["durum"] = "error"
            result["hatalar"].append({"error": f"{exc.__class__.__name__}: {exc}"})

        if result["hatalar"] and result["durum"] != "error":
            result["durum"] = "partial_error" if result["dagitilan"] else "error"
        return result