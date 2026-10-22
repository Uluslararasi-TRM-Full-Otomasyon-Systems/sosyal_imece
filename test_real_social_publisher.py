#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""real_social_publisher çevrimdışı testleri.

Gerçek ağa çıkmaz: urllib.request.urlopen taklit edilir. İki şekilde de koşar:
    python test_real_social_publisher.py          # kendi runner'ı (geçen/atlayan özeti basar)
    python -m unittest test_real_social_publisher.py
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

import real_social_publisher as rsp

FAKE_TOKEN = "000000000:SAHTE_TEST_TOKEN"
FAKE_CHAT = "-1001234567890"


class FakeResponse:
    def __init__(self, body: dict, status: int = 200):
        self._body = json.dumps(body).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def settings(mode="simulate", telegram=None):
    channels = {} if telegram is None else {"telegram": telegram}
    missing = [] if channels.get("telegram") else ["Telegram bot token ve chat/channel ID birlikte tanımlanmalıdır"]
    return {
        "distribution": {
            "mode": mode,
            "channels": channels,
            "requested_live": mode == "live",
            "ready": not missing,
            "missing": missing,
        }
    }


def temp_db() -> sqlite3.Connection:
    path = Path(tempfile.mkdtemp()) / "test.db"
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE organic_content_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT, content_category TEXT, content_format TEXT, content_text TEXT,
            hashtags TEXT, image_description TEXT, status TEXT, scheduled_time TEXT, created_at TEXT
        )
        """
    )
    rsp.ensure_schema(conn)
    return conn


def queue_row(conn, platform="telegram", category="product_promo", text="Ürün tanıtımı", status="pending"):
    conn.execute(
        "INSERT INTO organic_content_queue (platform, content_category, content_format, content_text,"
        " hashtags, image_description, status, scheduled_time, created_at)"
        " VALUES (?, ?, 'text', ?, '#trm', '', ?, 'now', 'now')",
        (platform, category, text, status),
    )
    conn.commit()
    return conn.execute("SELECT max(id) AS i FROM organic_content_queue").fetchone()["i"]


def install_urlopen(monkeytarget, handler):
    monkeytarget["calls"] = []

    def fake_urlopen(request, timeout=None):
        monkeytarget["calls"].append(request.full_url)
        return handler(request)

    original = rsp.urllib.request.urlopen
    rsp.urllib.request.urlopen = fake_urlopen
    return original


def ok_handler(request):
    return FakeResponse({"ok": True, "result": {"message_id": 55123, "chat": {"id": 1}}})


def run_case(name, fn):
    try:
        sonuc = fn()
    except AssertionError as exc:
        print(f"FAIL {name}: {exc}")
        return "fail"
    if sonuc == "skip":
        print(f"SKIP {name}")
        return "skip"
    print(f"PASS {name}")
    return "pass"


def test_no_credentials_is_not_configured():
    publisher = rsp.RealSocialPublisher(settings=settings("live"), load_environment=False)
    outcome = publisher.publish("telegram", "merhaba")
    assert outcome["status"] == rsp.STATUS_NOT_CONFIGURED, outcome
    assert outcome["post_id"] is None, outcome
    assert publisher.live_gate_open() is False, "kimlik olmadan live kapısı açılmamalı"


def test_unwired_channels_are_not_configured():
    publisher = rsp.RealSocialPublisher(settings=settings(), load_environment=False)
    for platform in rsp.UNCONFIGURED_CHANNELS:
        outcome = publisher.publish(platform, "merhaba")
        assert outcome["status"] == rsp.STATUS_NOT_CONFIGURED, (platform, outcome)
        assert outcome["post_id"] is None, outcome


def test_live_send_records_verified_post_id():
    state = {}
    original = install_urlopen(state, ok_handler)
    try:
        creds = {"bot_token": FAKE_TOKEN, "chat_id": FAKE_CHAT}
        publisher = rsp.RealSocialPublisher(settings=settings("live", creds), load_environment=False)
        conn = temp_db()
        row_id = queue_row(conn)
        summary = publisher.drain_queue(conn)
        assert len(state["calls"]) == 1, state["calls"]
        assert "api.telegram.org" in state["calls"][0], state["calls"][0]
        assert "/sendMessage" in state["calls"][0], state["calls"][0]
        item = summary[0]
        assert item["outcome"]["post_id"] == "55123", item
        assert item["status"] == rsp.STATUS_SENT, item
        row = conn.execute("SELECT * FROM organic_content_queue WHERE id = ?", (row_id,)).fetchone()
        assert row["status"] == "sent", dict(row)
        assert row["external_post_id"] == "55123", dict(row)
        log = conn.execute("SELECT * FROM publication_log ORDER BY id DESC LIMIT 1").fetchone()
        assert log["post_id"] == "55123" and log["channel_status"] == "sent", dict(log)
        conn.close()
    finally:
        rsp.urllib.request.urlopen = original


def test_rejected_send_stays_logged_not_sent():
    def deny(request):
        body = io.BytesIO(
            json.dumps({"ok": False, "error_code": 401, "description": "Unauthorized"}).encode("utf-8")
        )
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, body)

    state = {}
    original = install_urlopen(state, deny)
    try:
        creds = {"bot_token": FAKE_TOKEN, "chat_id": FAKE_CHAT}
        publisher = rsp.RealSocialPublisher(settings=settings("live", creds), load_environment=False)
        conn = temp_db()
        row_id = queue_row(conn)
        summary = publisher.drain_queue(conn)
        item = summary[0]
        assert item["outcome"]["status"] == rsp.STATUS_FAILED, item
        assert item["outcome"]["post_id"] is None, item
        assert FAKE_TOKEN not in str(item["outcome"]["error"]), "token hata metnine sızmamalı"
        row = conn.execute("SELECT * FROM organic_content_queue WHERE id = ?", (row_id,)).fetchone()
        assert row["status"] == rsp.STATUS_LOGGED_NOT_SENT, dict(row)
        assert row["external_post_id"] is None, dict(row)
        conn.close()
    finally:
        rsp.urllib.request.urlopen = original


def test_ok_without_message_id_is_not_success():
    state = {}
    original = install_urlopen(state, lambda request: FakeResponse({"ok": True, "result": {}}))
    try:
        creds = {"bot_token": FAKE_TOKEN, "chat_id": FAKE_CHAT}
        publisher = rsp.RealSocialPublisher(settings=settings("live", creds), load_environment=False)
        outcome = publisher.publish("telegram", "merhaba")
        assert outcome["status"] == rsp.STATUS_FAILED, outcome
        assert outcome["post_id"] is None, outcome
    finally:
        rsp.urllib.request.urlopen = original


def test_warmup_ticks_are_never_published():
    state = {}
    original = install_urlopen(state, ok_handler)
    try:
        creds = {"bot_token": FAKE_TOKEN, "chat_id": FAKE_CHAT}
        publisher = rsp.RealSocialPublisher(settings=settings("live", creds), load_environment=False)
        conn = temp_db()
        queue_row(conn, category="organic_warmup", text="Warm-up tick #1")
        summary = publisher.drain_queue(conn)
        assert state["calls"] == [], "warm-up tiklemesi ağa gitmemeli"
        assert summary[0]["status"] == rsp.STATUS_LOGGED_NOT_SENT, summary[0]
        conn.close()
    finally:
        rsp.urllib.request.urlopen = original


def test_social_agents_delegates_without_faking_success():
    try:
        from agents import social_agents
    except ImportError:
        return "skip"

    stub = rsp.RealSocialPublisher(settings=settings("simulate"), load_environment=False)
    state = {}
    original = install_urlopen(state, ok_handler)
    try:
        social_agents._publisher = stub
        res = social_agents.dispatch_multichannel_campaign(
            {"title": "Deneme Ürün", "link": "https://trendurunlermarket.com/x", "campaign": "Test"}
        )
        assert state["calls"] == [], "ağa çıkmamalıydı"
        assert res["multi_channel_status"] == "not_sent", res
        assert res["sent_channels"] == [], res
        assert all(item["post_id"] is None for item in res["results"].values()), res
        assert res["results"]["telegram"]["status"] == rsp.STATUS_NOT_CONFIGURED, res["results"]["telegram"]
    finally:
        rsp.urllib.request.urlopen = original
        social_agents._publisher = None


def test_discovery_enrolls_only_an_administered_channel():
    def yonetilen(request):
        sohbet = {"id": -1001234567890, "type": "channel", "username": "aydin_ili_trm"}
        uyelik = {"status": "administrator", "user": {"id": 1, "is_bot": True}}
        return FakeResponse({"ok": True, "result": [
            {"update_id": 1, "my_chat_member": {"chat": sohbet, "new_chat_member": uyelik}},
        ]})

    def yonetilmeyen(request):
        sohbet = {"id": 42, "type": "private", "username": None}
        uyelik = {"status": "left", "user": {"id": 1, "is_bot": True}}
        return FakeResponse({"ok": True, "result": [
            {"update_id": 2, "my_chat_member": {"chat": sohbet, "new_chat_member": uyelik}},
        ]})

    publisher = rsp.RealSocialPublisher(
        settings=settings("live", {"bot_token": FAKE_TOKEN, "chat_id": FAKE_CHAT}),
        load_environment=False,
    )
    state = {}
    original = install_urlopen(state, yonetilen)
    try:
        kesif = publisher.discover_chats()
        assert kesif["ok"] is True, kesif
        assert kesif["secim"] and kesif["secim"]["chat_id"] == "-1001234567890", kesif
        assert kesif["secim"]["yayin_yetkisi"] is True, kesif
        assert FAKE_TOKEN not in json.dumps(kesif), "token sızdı"
    finally:
        rsp.urllib.request.urlopen = original

    bos = {}
    original = install_urlopen(bos, yonetilmeyen)
    try:
        kesif = publisher.discover_chats()
        assert kesif["secim"] is None, kesif
        assert kesif["secilebilir"] == [], kesif
    finally:
        rsp.urllib.request.urlopen = original


def test_live_window_is_memory_only_and_always_reverts():
    creds = {"bot_token": FAKE_TOKEN, "chat_id": FAKE_CHAT}
    publisher = rsp.RealSocialPublisher(settings=settings("simulate", creds), load_environment=False)
    environ_onceki = dict(os.environ)
    assert publisher.live_gate_open() is False, "simulate modunda kapı açık olmamalı"

    with rsp.gecici_canli_pencere(publisher, acik=True):
        assert publisher.live_gate_open() is True, "pencere kapıyı açmalı"
    assert publisher.settings["distribution"]["mode"] == "simulate"
    assert publisher.live_gate_open() is False

    # pencere kapanışı istisnada da garantili
    try:
        with rsp.gecici_canli_pencere(publisher, acik=True):
            raise RuntimeError("gönderim patladı")
    except RuntimeError:
        pass
    assert publisher.settings["distribution"]["requested_live"] is False
    assert publisher.settings["distribution"]["mode"] == "simulate"
    assert os.environ == environ_onceki, "--live ortamı değiştirmemeli"

    # --live olmadan pencere hiç açılmaz
    with rsp.gecici_canli_pencere(publisher, acik=False):
        assert publisher.live_gate_open() is False


def _yuru(fn):
    """Vakayı koşar; fonksiyon 'skip' dönerse unittest'e de atlandı diye bildirir."""
    if fn() == "skip":
        raise unittest.SkipTest("bu kurulumda ilgili modül yok")


class YayıncıBirimTestleri(unittest.TestCase):
    """Aynı vakaların unittest keşfi ile koşulabilen hali.

    Bu köprü olmadan `python -m unittest test_real_social_publisher.py` hiçbir TestCase
    bulamaz ve 0 testle "OK" yazarak yanlış-yeşil verir.
    """

    def test_kimlik_yoksa_not_configured(self):
        _yuru(test_no_credentials_is_not_configured)

    def test_entegrasyonu_olmayan_kanallar_not_configured(self):
        _yuru(test_unwired_channels_are_not_configured)

    def test_canli_gonderim_dogrulanmis_post_id_yazar(self):
        _yuru(test_live_send_records_verified_post_id)

    def test_platform_reddi_sent_sayilmaz(self):
        _yuru(test_rejected_send_stays_logged_not_sent)

    def test_ok_ama_message_id_yoksa_basarisiz(self):
        _yuru(test_ok_without_message_id_is_not_success)

    def test_warmup_tiklemesi_asla_gonderilmez(self):
        _yuru(test_warmup_ticks_are_never_published)

    def test_social_agents_sahte_basari_dondurmaz(self):
        _yuru(test_social_agents_delegates_without_faking_success)

    def test_kesif_yalnizca_yonetici_olunan_kanali_aday_gosterir(self):
        _yuru(test_discovery_enrolls_only_an_administered_channel)

    def test_canli_pencere_bellek_icidir_ve_geri_doner(self):
        _yuru(test_live_window_is_memory_only_and_always_reverts)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    cases = [
        ("kimlik yoksa not_configured", test_no_credentials_is_not_configured),
        ("entegrasyonu olmayan kanallar not_configured", test_unwired_channels_are_not_configured),
        ("canlı gönderim doğrulanmış post_id yazar", test_live_send_records_verified_post_id),
        ("platform reddi sent sayılmaz", test_rejected_send_stays_logged_not_sent),
        ("ok ama message_id yoksa başarısız", test_ok_without_message_id_is_not_success),
        ("warm-up tiklemesi asla gönderilmez", test_warmup_ticks_are_never_published),
        ("social_agents sahte başarı döndürmez", test_social_agents_delegates_without_faking_success),
        ("keşif yalnızca yönetici olunan kanalı aday gösterir", test_discovery_enrolls_only_an_administered_channel),
        ("canlı pencere bellek içi ve her durumda geri döner", test_live_window_is_memory_only_and_always_reverts),
    ]
    sonuclar = [run_case(name, fn) for name, fn in cases]
    gecen = sonuclar.count("pass")
    atlanan = sonuclar.count("skip")
    basarisiz = sonuclar.count("fail")
    ozet = f"\n{gecen}/{len(sonuclar)} test geçti"
    if atlanan:
        ozet += f" · {atlanan} atlandı (bu kurulumda ilgili modül yok)"
    if basarisiz:
        ozet += f" · {basarisiz} BAŞARISIZ"
    print(ozet)
    return 0 if basarisiz == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
