#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed sosyal yayın katmanı.

Başarı yalnızca platformun döndürduğu doğrulanmış gönderi kimliğiyle ilan edilir.
Kimlik bilgisi yoksa, kanal entegrasyonu yoksa veya HTTP yanıtı doğrulanamazsa
gönderi "sent" sayılmaz ve kuyruk satırı `logged_not_sent` olarak işaretlenir.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from trm_live_config import get_live_settings, load_trm_environment

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "trm_ticari_analiz.db"
CHANNELS_PATH = ROOT / "config" / "single_active_set.json"

STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_NOT_CONFIGURED = "not_configured"
STATUS_LOGGED_NOT_SENT = "logged_not_sent"

HTTP_TIMEOUT_SECONDS = 20
QUEUED_STATES = ("pending", "queued", "new")

# Bu kanalların resmî API entegrasyonu yazılmadı; olduğumuz gibi göstermiyoruz.
UNCONFIGURED_CHANNELS = (
    "facebook",
    "instagram",
    "tiktok",
    "youtube",
    "whatsapp",
    "blogger",
    "medium",
    "wordpress",
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS publication_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            channel_status TEXT NOT NULL,
            queue_table TEXT,
            queue_id INTEGER,
            content_excerpt TEXT,
            post_id TEXT,
            http_status INTEGER,
            error TEXT,
            timestamp TEXT NOT NULL
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(organic_content_queue)")}
    for column in ("external_post_id", "sent_at"):
        if column not in columns:
            conn.execute(f"ALTER TABLE organic_content_queue ADD COLUMN {column} TEXT")
    conn.commit()


def result(platform: str, status: str, *, post_id=None, http_status=None, error=None, reason=None):
    return {
        "platform": platform,
        "status": status,
        "post_id": post_id,
        "http_status": http_status,
        "error": error,
        "reason": reason,
    }


class RealSocialPublisher:
    def __init__(self, settings=None, load_environment: bool = True):
        if load_environment:
            load_trm_environment()
        self.settings = settings if settings is not None else get_live_settings()

    @property
    def telegram(self) -> dict:
        return self.settings["distribution"]["channels"].get("telegram", {})

    def live_gate_open(self) -> bool:
        distribution = self.settings["distribution"]
        return bool(distribution["requested_live"] and distribution["ready"])

    def publish(self, platform: str, text: str):
        key = str(platform or "").strip().casefold()
        body = str(text or "").strip()
        if not body:
            return result(key, STATUS_FAILED, error="gönderi metni boş")
        if key == "telegram":
            return self.publish_telegram(body)
        if key in UNCONFIGURED_CHANNELS:
            return result(key, STATUS_NOT_CONFIGURED, reason="resmî API entegrasyonu yok")
        return result(key, STATUS_NOT_CONFIGURED, reason="bilinmeyen kanal")

    def publish_telegram(self, text: str):
        credentials = self.telegram
        token = str(credentials.get("bot_token") or "").strip()
        chat_id = str(credentials.get("chat_id") or "").strip()
        if not (token and chat_id):
            missing = [
                name
                for name, value in (("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id))
                if not value
            ]
            return result(
                "telegram",
                STATUS_NOT_CONFIGURED,
                reason="kasada eksik: " + ", ".join(missing),
            )

        payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"User-Agent": "trm-live-worker/1.0", "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                http_status = response.status
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return result(
                "telegram",
                STATUS_FAILED,
                http_status=exc.code,
                error=_scrub(_read_error(exc), token),
            )
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return result("telegram", STATUS_FAILED, error=_scrub(str(exc), token))

        # message_id olmadan "gönderildi" demiyoruz: Telegram ok=true'yu reddedilmiş
        # iletimlerde de dönebiliyor (ör. kanal üyeliği olmayan chat).
        message_id = (body.get("result") or {}).get("message_id") if body.get("ok") else None
        if not message_id:
            return result(
                "telegram",
                STATUS_FAILED,
                http_status=http_status,
                error=_scrub(str(body.get("description") or "message_id yok"), token),
            )
        return result("telegram", STATUS_SENT, post_id=str(message_id), http_status=http_status)

    def probe_telegram(self) -> dict:
        """getMe ile token'ın canlılığını doğrular; token ve chat_id değerini asla döndürmez."""
        credentials = self.telegram
        token = str(credentials.get("bot_token") or "").strip()
        chat_id = str(credentials.get("chat_id") or "").strip()
        diagnostics = {
            "token_shape_ok": bool(re.fullmatch(r"\d{6,}:[A-Za-z0-9_-]{30,}", token)),
            "token_length": len(token),
            "chat_shape_ok": bool(re.fullmatch(r"@?[A-Za-z0-9_]{5,32}|-\d{5,20}|\d{8,}", chat_id)),
            "chat_length": len(chat_id),
            "get_me": None,
            "chat_erisimi": None,
            "status": STATUS_NOT_CONFIGURED if not (token and chat_id) else None,
        }
        if not (token and chat_id):
            return diagnostics
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/getMe",
            headers={"User-Agent": "trm-live-worker/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            diagnostics["get_me"] = {"ok": False, "http_status": exc.code, "detail": _scrub(_read_error(exc), token)}
            return diagnostics
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            diagnostics["get_me"] = {"ok": False, "detail": _scrub(str(exc), token)}
            return diagnostics
        result_row = body.get("result") or {}
        diagnostics["get_me"] = {
            "ok": bool(body.get("ok")),
            "http_status": 200,
            "bot_username": result_row.get("username"),
            "detail": result_row.get("username") or str(body.get("description") or "sonuç yok"),
        }
        # Token'ın canlı olması mesajın gideceği yeri kanıtlamaz: hedef sohbeti
        # de sormadan "ready" demiyoruz.
        if diagnostics["get_me"]["ok"]:
            diagnostics["chat_erisimi"] = _get_chat(token, chat_id)
        return diagnostics

    def channel_inventory(self, probe: dict | None = None):
        rows = []
        credentials = self.telegram
        credentials_present = bool(credentials.get("bot_token") and credentials.get("chat_id"))
        get_me = (probe or {}).get("get_me") or {}
        chat_erisimi = (probe or {}).get("chat_erisimi") or {}
        if not credentials_present:
            token_test = "kimlik yok"
        elif get_me.get("ok"):
            token_test = f"getMe ok (@{get_me.get('bot_username')})"
        elif get_me:
            token_test = f"getMe reddedildi (http={get_me.get('http_status', '?')})"
        else:
            token_test = "test edilmedi"
        status = (
            "ready"
            if credentials_present and self.live_gate_open() and get_me.get("ok") and chat_erisimi.get("ok")
            else STATUS_NOT_CONFIGURED
            if not credentials_present
            else "credential_rejected"
            if get_me and not get_me.get("ok")
            else "chat_unreachable"
            if get_me.get("ok") and chat_erisimi and not chat_erisimi.get("ok")
            else "gate_closed"
        )
        if status == "ready":
            missing = ""
        elif status == "credential_rejected":
            missing = "kasadaki token geçersiz: @BotFather ile yeni token al, DPAPI kasasına yaz"
        elif status == "chat_unreachable":
            missing = (
                "token geçerli ama TELEGRAM_CHAT_ID bu botla erişilebilir değil ("
                + str(chat_erisimi.get("detail") or chat_erisimi.get("http_status") or "getChat ok dönmedi")
                + "); kanalı aç, botu admin yap, @kanalAdi veya -100... id'sini kasaya yaz"
            )
        else:
            missing = _telegram_gap(self.settings)
        rows.append(
            {
                "platform": "telegram",
                "integration": "var (Bot API)",
                "credentials": "kasada dolu" if credentials_present else "eksik",
                "token_test": token_test,
                "status": status,
                "missing": missing,
            }
        )
        for platform in UNCONFIGURED_CHANNELS:
            rows.append(
                {
                    "platform": platform,
                    "integration": "yok",
                    "credentials": "yok",
                    "token_test": "ilgili kanal API'si yok",
                    "status": STATUS_NOT_CONFIGURED,
                    "missing": "resmî API entegrasyonu + kimlik bilgisi",
                }
            )
        return rows

    def log_publication(
        self,
        conn: sqlite3.Connection,
        outcome: dict,
        *,
        queue_table: str | None = None,
        queue_id: int | None = None,
        excerpt: str | None = None,
    ) -> int:
        channel_status = STATUS_SENT if outcome["status"] == STATUS_SENT else outcome["status"]
        cursor = conn.execute(
            """
            INSERT INTO publication_log (
                platform, channel_status, queue_table, queue_id,
                content_excerpt, post_id, http_status, error, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                outcome["platform"],
                channel_status,
                queue_table,
                queue_id,
                (excerpt or "")[:180] or None,
                outcome["post_id"],
                outcome["http_status"],
                outcome["error"] or outcome["reason"],
                utc_stamp(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)

    def drain_queue(self, conn: sqlite3.Connection, table: str = "organic_content_queue", limit: int = 10):
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE lower(coalesce(status, '')) IN ({', '.join('?' * len(QUEUED_STATES))})"
            " ORDER BY id LIMIT ?",
            (*QUEUED_STATES, limit),
        ).fetchall()
        summary = []
        for row in rows:
            platform = _field(row, "platform", "unknown") or "unknown"
            content_category = _field(row, "content_category")
            text = _compose_text(row)
            if content_category == "organic_warmup":
                outcome = result(platform, STATUS_NOT_CONFIGURED, reason="warm-up tiklemesi içerik değil, gönderilmez")
            elif not self.live_gate_open():
                outcome = result(platform, STATUS_NOT_CONFIGURED, reason="TRM_DISTRIBUTION_MODE=live değil")
            else:
                outcome = self.publish(platform, text)
            new_status = STATUS_SENT if outcome["status"] == STATUS_SENT else STATUS_LOGGED_NOT_SENT
            self.log_publication(
                conn,
                outcome,
                queue_table=table,
                queue_id=row["id"],
                excerpt=text,
            )
            conn.execute(
                f"UPDATE {table} SET status = ?, external_post_id = ?, sent_at = ? WHERE id = ?",
                (
                    new_status,
                    outcome["post_id"],
                    utc_stamp() if outcome["post_id"] else None,
                    row["id"],
                ),
            )
            conn.commit()
            summary.append({"id": row["id"], "platform": platform, "outcome": outcome, "status": new_status})
        return summary

    def discover_chats(self) -> dict:
        """getUpdates'u tarayıp bu botun gerçekten eklendiği sohbetleri bulur.

        Aday yoksa hiçbir şey yazmaz; token değerini asla döndürmez.
        """
        token = str(self.telegram.get("bot_token") or "").strip()
        if not token:
            return {"ok": False, "sebep": "kasada TELEGRAM_BOT_TOKEN yok", "adaylar": []}
        http_status, body = _get_updates(token)
        if not body or not body.get("ok"):
            return {
                "ok": False,
                "http_status": http_status,
                "sebep": _scrub((body or {}).get("description") or "getUpdates ok dönmedi", token),
                "adaylar": [],
            }
        adaylar = {}
        for update in body.get("result") or []:
            for tur in ("my_chat_member", "chat_member", "channel_post", "message"):
                payload = update.get(tur)
                sohbet = payload.get("chat") if isinstance(payload, dict) else None
                if not isinstance(sohbet, dict):
                    continue
                kim = str(sohbet.get("id"))
                satir = adaylar.setdefault(
                    kim,
                    {
                        "chat_id": kim,
                        "tip": sohbet.get("type"),
                        "kullanici_adi": sohbet.get("username") or "-",
                        "durum": None,
                        "olaylar": set(),
                    },
                )
                satir["olaylar"].add(tur)
                if tur == "my_chat_member":
                    uyelik = (payload.get("new_chat_member") or {}).get("status")
                    if uyelik in ("creator", "administrator", "member") or satir["durum"] is None:
                        satir["durum"] = uyelik
        satirlar = []
        for satir in adaylar.values():
            satir["olaylar"] = sorted(satir["olaylar"])
            satir["yayin_yetkisi"] = satir["durum"] in ("creator", "administrator")
            satirlar.append(satir)
        satirlar.sort(key=lambda s: s["chat_id"])
        # Yalnızca tek anlamlı aday kasaya yazılır: kanal/süpergrup ve bu bot yöneticisi.
        secilebilir = [
            s for s in satirlar
            if s["tip"] in ("channel", "supergroup") and s["durum"] in ("creator", "administrator")
        ]
        return {
            "ok": True,
            "http_status": http_status,
            "guncelleme_sayisi": len(body.get("result") or []),
            "adaylar": satirlar,
            "secilebilir": [s["chat_id"] for s in secilebilir],
            "secim": secilebilir[0] if len(secilebilir) == 1 else None,
        }

    def status_report(self, conn: sqlite3.Connection, probe: dict | None = None):
        queue_rows = {}
        if _table_exists(conn, "organic_content_queue"):
            for row in conn.execute("SELECT status, count(*) AS n FROM organic_content_queue GROUP BY status"):
                queue_rows[row["status"]] = row["n"]
        last_posts = conn.execute(
            "SELECT platform, channel_status, post_id, http_status, error, timestamp"
            " FROM publication_log ORDER BY id DESC LIMIT 5"
        ).fetchall()
        return {"channels": self.channel_inventory(probe), "queue": queue_rows, "last_posts": last_posts}


def _scrub(text: str, token: str) -> str:
    return str(text).replace(token, "***") if token else str(text)


def _get_chat(token: str, chat_id: str) -> dict:
    """Hedef sohbetin BU bot için erişilebilirliğini okuma çağrısıyla doğrular."""
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/getChat",
        data=urllib.parse.urlencode({"chat_id": chat_id}).encode("utf-8"),
        headers={"User-Agent": "trm-live-worker/1.0", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"ok": False, "http_status": exc.code, "detail": _scrub(_read_error(exc), token)[:200]}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "detail": _scrub(str(exc), token)}
    sohbet = body.get("result") or {}
    return {"ok": bool(body.get("ok")), "http_status": 200, "chat_type": sohbet.get("type")}


def _read_error(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", "replace")[:300]
    except OSError:
        return str(exc)


def _get_updates(token: str) -> tuple:
    """Botun gördüğü güncellemeleri ve böylece gerçek sohbet kimliklerini okur."""
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/getUpdates",
        data=urllib.parse.urlencode({"limit": 100, "timeout": 0}).encode("utf-8"),
        headers={"User-Agent": "trm-live-worker/1.0", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, {"ok": False, "description": _scrub(_read_error(exc), token)}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return None, {"ok": False, "description": _scrub(str(exc), token)}


@contextlib.contextmanager
def gecici_canli_pencere(publisher: "RealSocialPublisher", acik: bool = False):
    """Tek gönderim için canlı pencere; yalnızca bellek içi ayarı değiştirir.

    Kasa ve os.environ'a dokunmaz, dolayısıyla süreç bittiğinde kalıcı `live`
    bırakmak imkânsızdır. `ready` sahte olarak True yapılmaz: kimlik eksikse
    kapı kapalı kalır.
    """
    dagitim = publisher.settings["distribution"]
    onceki = (dagitim.get("mode"), dagitim.get("requested_live"))
    if acik:
        dagitim["mode"] = "live"
        dagitim["requested_live"] = True
    try:
        yield publisher
    finally:
        dagitim["mode"], dagitim["requested_live"] = onceki


def _write_vault_chat_id(chat_id: str) -> dict:
    """TELEGRAM_CHAT_ID'yi DPAPI kasasına şifreli yedek alarak yazar; değeri yazdırmaz."""
    import shutil
    from core.dpapi_vault import DpapiVaultError, ProtectedLocalVault

    try:
        vault = ProtectedLocalVault.from_default_location()
        veri = vault.load()
        if veri is None:
            return {"ok": False, "sebep": "kasa okunamadı"}
        yedek = vault.path.with_name(
            f"{vault.path.name}.yedek-kesif-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        )
        shutil.copy2(vault.path, yedek)
        environment = veri["environment"]
        environment["TELEGRAM_CHAT_ID"] = chat_id
        environment["TELEGRAM_TARGET_CHANNEL"] = chat_id
        veri["environment"] = environment
        vault.save(veri)
    except (DpapiVaultError, OSError) as exc:
        return {"ok": False, "sebep": str(exc)[:200]}
    geri = ProtectedLocalVault.from_default_location().load()["environment"].get("TELEGRAM_CHAT_ID", "")
    return {"ok": geri == chat_id, "yedek": yedek.name, "uzunluk": len(geri)}


def _telegram_gap(settings) -> str:
    missing = list(settings["distribution"]["missing"])
    if not missing and not settings["distribution"]["requested_live"]:
        missing.append("TRM_DISTRIBUTION_MODE=live")
    return "; ".join(missing)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _compose_text(row: sqlite3.Row) -> str:
    body = _field(row, "content_text")
    tags = _field(row, "hashtags")
    return (body + "\n\n" + tags).strip()


def _field(row: sqlite3.Row, key: str, default: str = "") -> str:
    return str(row[key] if key in row.keys() else default) or default


def _print_table(headers, rows):
    widths = [max(len(str(headers[i])), *(len(str(r[i])) for r in rows)) if rows else len(str(headers[i])) for i in range(len(headers))]
    line = "+".join("-" * (w + 2) for w in widths)
    line = f"+{line}+"

    def render(values):
        return "| " + " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(values)) + " |"

    print(line)
    print(render(headers))
    print(line)
    for row in rows:
        print(render(row))
    if not rows:
        print(render([""] * len(headers)))
    print(line)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="TRM fail-closed sosyal yayın katmanı")
    parser.add_argument("--durum", action="store_true", help="Kanal ve kuyruk durumunu yazdır (varsayılan)")
    parser.add_argument("--kuyruk-gonder", action="store_true", help="Bekleyen kuyruk satırlarını dürüstçe işle")
    parser.add_argument("--dogrulama-gonderi", action="store_true", help="Telegram kanalına tek doğrulama mesajı gönder")
    parser.add_argument("--kanal-testi", action="store_true", help="getMe + getChat ile kanal erişimini doğrular (değer yazdırmaz)")
    parser.add_argument("--kanal-kesif", action="store_true", help="getUpdates'taki gerçek sohbetleri tarar, tek anlamlı kanalı kasaya yazar")
    parser.add_argument("--metin", default=None, help="Doğrulama mesajı metni")
    parser.add_argument(
        "--live",
        action="store_true",
        help="yalnızca bu komuttaki gönderim için bellek içi canlı pencere açar; kasa/env değişmez",
    )
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)

    publisher = RealSocialPublisher()
    conn = connect()
    ensure_schema(conn)
    probe = publisher.probe_telegram()

    if args.kanal_kesif:
        kesif = publisher.discover_chats()
        print(
            f"[KEŞİF] getUpdates http={kesif.get('http_status', '-')} "
            f"sohbet={len(kesif['adaylar'])} "
            f"yayın-yetkili-aday={len(kesif.get('secilebilir', []))}"
        )
        if not kesif["ok"]:
            print(f"[KEŞİF] başarısız: {kesif.get('sebep')}")
            conn.close()
            return 1
        if kesif["adaylar"]:
            _print_table(
                ["CHAT_ID", "TIP", "KULLANICI_ADI", "BOT_DURUMU", "OLAYLAR"],
                [[a["chat_id"], a["tip"], a["kullanici_adi"], a["durum"] or "-", ",".join(a["olaylar"])] for a in kesif["adaylar"]],
            )
        secim = kesif.get("secim")
        if not secim:
            print(
                "[KEŞİF] Kasaya yazılacak tek bir kanal adayı yok. Botu kanalın yöneticisi yap; "
                "bu olduktan sonra keşif -100… kimliğini buradan okuyacağız."
            )
            conn.close()
            return 1
        kayit = _write_vault_chat_id(secim["chat_id"])
        print(
            f"[KEŞİF] kanal id kasaya yazıldı: ok={kayit.get('ok')} uzunluk={kayit.get('uzunluk')} "
            f"yedek={kayit.get('yedek')} sebep={kayit.get('sebep', '-')}"
        )
        if not kayit.get("ok"):
            conn.close()
            return 1
        os.environ["TELEGRAM_CHAT_ID"] = secim["chat_id"]
        os.environ["TELEGRAM_TARGET_CHANNEL"] = secim["chat_id"]
        publisher.settings = get_live_settings()
        probe = publisher.probe_telegram()

    if args.kanal_testi:
        get_me = probe["get_me"] or {}
        chat_erisimi = probe["chat_erisimi"] or {}
        print(
            "[KANAL TESTI] telegram · "
            f"token_shape_ok={probe['token_shape_ok']} token_length={probe['token_length']} "
            f"chat_shape_ok={probe['chat_shape_ok']} chat_length={probe['chat_length']} "
            f"get_me_ok={get_me.get('ok')} http={get_me.get('http_status', '-')} "
            f"bot=@{get_me.get('bot_username') or '-'} detail={get_me.get('detail', 'kimlik eksik')}"
        )
        print(
            "[KANAL TESTI] hedef sohbet · "
            f"getChat_ok={chat_erisimi.get('ok')} tip={chat_erisimi.get('chat_type') or '-'} "
            f"ayrinti={chat_erisimi.get('detail') or chat_erisimi.get('http_status') or '-'}"
        )
        if not get_me.get("ok") or not chat_erisimi.get("ok"):
            conn.close()
            return 1

    if args.dogrulama_gonderi:
        with gecici_canli_pencere(publisher, acik=args.live):
            pencere = publisher.settings["distribution"]
            if args.live:
                print(f"[PENCERE] tek seferlik canlı deneme · mode={pencere['mode']} gate={publisher.live_gate_open()}")
            if not publisher.live_gate_open():
                print(
                    f"[RED] Gerçek gönderim kapalı: {pencere['mode']!r} modu. "
                    f"TRM_DISTRIBUTION_MODE=live gerekiyor. Gönderi yapılmadı."
                )
                conn.close()
                return 2
            text = args.metin or f"TRM yayın kanalı doğrulama mesajı · {utc_stamp()} UTC"
            outcome = publisher.publish("telegram", text)
            log_id = publisher.log_publication(conn, outcome, excerpt=text)
            son = 0 if outcome["status"] == STATUS_SENT else 1
        if son == 0:
            print(
                f"[GÖNDERİLDİ] telegram · message_id={outcome['post_id']} · "
                f"http={outcome['http_status']} · publication_log id={log_id}"
            )
        else:
            print(f"[GÖNDERİLMEDİ] telegram · {outcome['status']} · {outcome['error'] or outcome['reason']}")
        if args.live:
            print(
                f"[PENCERE KAPANDI] mode kalıcı olarak {publisher.settings['distribution']['mode']!r}; "
                "kasa ve ortam değişmedi."
            )
        conn.close()
        return son

    if args.kuyruk_gonder:
        summary = publisher.drain_queue(conn, limit=args.limit)
        if not summary:
            print("[KUYRUK] İşlenecek pending/queued/new satır yok.")
        for item in summary:
            outcome = item["outcome"]
            print(
                f"[KUYRUK] id={item['id']} kanal={item['platform']} durum={item['status']}"
                f" post_id={outcome['post_id'] or '-'} sebep={outcome['error'] or outcome['reason'] or 'doğrulandı'}"
            )

    report = publisher.status_report(conn, probe)
    print("\nKANAL DURUMU")
    _print_table(
        ["KANAL", "ENTEGRASYON", "KIMLIK", "TOKEN TESTI", "DURUM", "EKSIK"],
        [
            [row["platform"], row["integration"], row["credentials"], row["token_test"], row["status"], row["missing"]]
            for row in report["channels"]
        ],
    )

    print("\nKUYRUK SAYAÇLARI (organic_content_queue)")
    if report["queue"]:
        _print_table(["DURUM", "SATIR"], [[key, value] for key, value in sorted(report["queue"].items())])
    else:
        print("  (satır yok)")

    print("\nSON YAYIN KAYITLARI (publication_log)")
    if report["last_posts"]:
        _print_table(
            ["KANAL", "DURUM", "POST_ID", "HTTP", "SEBEP / ZAMAN"],
            [
                [
                    row["platform"],
                    row["channel_status"],
                    row["post_id"] or "-",
                    row["http_status"] or "-",
                    (row["error"] or row["timestamp"]),
                ]
                for row in report["last_posts"]
            ],
        )
    else:
        print("  (henüz yayın kaydı yok)")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
