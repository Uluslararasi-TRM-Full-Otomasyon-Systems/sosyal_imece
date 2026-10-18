#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM JSON → SQLite (trm_veritabani.db) Veri Aktarım Betiği
=========================================================

Eski JSON tabanlı veri saklamanın (modül durumları, loglar, yönlendirme ve
satıcı verileri, kuyruklar) tamamını merkezi trm_veritabani.db'ye taşır.

ÇALIŞTIRMA
----------
    python trm_migrasyon.py                  # içe aktar + emekliye ayrılan dosyaları arşivle
    python trm_migrasyon.py --sadece-ice-aktar   # arşivleme yapma
    python trm_migrasyon.py --force          # daha önce aktarılmışları tekrar aktar

Davranış kuralları:
- Idempotent: her dosya için ayarlar tablosuna damga (marker) vurur; ikinci
  çalıştırmada aynı dosyayı tekrar aktarmaz (--force ile zorlanır).
- Yıkıcı DEĞİLDİR: kaynak JSON dosyaları silinmez; kod tarafında yazıcıları
  trm_db'ye taşınmış (emekliye ayrılmış) dosyalar _json_arsiv/<zaman>/ içine
  TAŞINIR. Yazarı hâlâ JSON'a yazan dosyalar yerinde bırakılır.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from trm_db import trm_db, _json_yaz, _json_coz  # noqa: E402

ARSIV_KOKU = BASE_DIR / "_json_arsiv"


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------

def _json_yukle(yol: Path) -> Optional[Any]:
    if not yol.exists():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"  [UYARI] {yol.name} okunamadı/atlandı: {exc}")
        return None


def _jsonl_yukle(yol: Path) -> List[Dict]:
    kayitlar: List[Dict] = []
    if not yol.exists():
        return kayitlar
    try:
        for satir in yol.read_text(encoding="utf-8-sig").splitlines():
            satir = satir.strip()
            if not satir:
                continue
            try:
                kayitlar.append(json.loads(satir))
            except json.JSONDecodeError:
                continue
    except Exception as exc:
        print(f"  [UYARI] {yol.name} okunamadı/atlandı: {exc}")
    return kayitlar


def _zaman_al(kayit: Dict, varsayilan: str) -> str:
    for alan in ("timestamp", "zaman", "time", "created_at", "updated_at",
                 "last_sent_at", "queued_at", "generated_at"):
        deger = kayit.get(alan)
        if isinstance(deger, str) and deger.strip():
            return deger.strip()
        if isinstance(deger, (int, float)):
            try:
                return datetime.fromtimestamp(deger).isoformat(timespec="seconds")
            except Exception:
                continue
    return varsayilan


def _damga_var(db, dosya: Path) -> bool:
    return db.ayar_oku(f"migrasyon:{dosya.name}") is not None


def _damga_vur(db, dosya: Path, adet: int, hedef: str) -> None:
    db.ayar_kaydet(f"migrasyon:{dosya.name}", {
        "kaynak": str(dosya),
        "hedef_tablo": hedef,
        "aktarilan_kayit": adet,
        "zaman": datetime.now().isoformat(timespec="seconds"),
    })


# ---------------------------------------------------------------------------
# 1) AJANLAR → ajanlar
# ---------------------------------------------------------------------------

def ajanlari_aktar(db, force: bool) -> int:
    print("\n[1/6] Ajan kayıt defterleri → ajanlar tablosu")
    toplam = 0
    for yol in [BASE_DIR / "data" / "agents.json", BASE_DIR / "data" / "dataagents.json"]:
        if not yol.exists() or (not force and _damga_var(db, yol)):
            continue
        veri = _json_yukle(yol)
        ajan_listesi = veri.get("agents", []) if isinstance(veri, dict) else (veri or [])
        adet = 0
        for ajan in ajan_listesi:
            if not isinstance(ajan, dict):
                continue
            ajan_id = ajan.get("id", ajan.get("agent_id"))
            kod = ajan.get("code") or (f"AGT-{ajan_id}" if ajan_id is not None else None)
            if not kod:
                continue
            db.ajan_kaydet(
                ad=str(ajan.get("name") or kod),
                ajan_kodu=str(kod),
                rol=ajan.get("role"),
                tur=ajan.get("category") or "import",
                durum=str(ajan.get("status") or "beklemede"),
                detay={
                    "web": ajan.get("web"),
                    "last_heartbeat": ajan.get("last_heartbeat"),
                    "performance": ajan.get("performance"),
                    "kaynak_dosya": yol.name,
                },
            )
            adet += 1
        _damga_vur(db, yol, adet, "ajanlar")
        print(f"  {yol.name:<35} → {adet} ajan")
        toplam += adet
    return toplam


# ---------------------------------------------------------------------------
# 2) SATICI HAVUZU → satici_havuzu (affiliate ortak / yerel ortak / üye)
# ---------------------------------------------------------------------------

def _ortak_listesi(veri: Dict, anahtarlar: List[str]) -> List[Dict]:
    for anahtar in anahtarlar:
        liste = veri.get(anahtar)
        if isinstance(liste, list):
            return liste
    return []


def saticilari_aktar(db, force: bool) -> int:
    print("\n[2/6] Satıcı / ortak / üye havuzları → satici_havuzu tablosu")
    toplam = 0

    plan = [
        (BASE_DIR / "affiliate_partners.json", "affiliate",
         {"recruited_partners": "aktif", "pending_partners": "beklemede",
          "partners": "aktif", "passive_partners": "pasif"}),
        (BASE_DIR / "local_partners.json", "yerel",
         {"recruited_partners": "aktif", "pending_partners": "beklemede",
          "passive_partners": "pasif"}),
    ]

    for yol, tur, durum_eslesme in plan:
        if not yol.exists() or (not force and _damga_var(db, yol)):
            continue
        veri = _json_yukle(yol)
        if not isinstance(veri, dict):
            if isinstance(veri, list):
                # Üst düzey liste (ör. üye arşivi) → plandaki ilk listeye sar
                veri = {next(iter(durum_eslesme)): veri}
            else:
                continue
        adet = 0
        for anahtar, durum in durum_eslesme.items():
            for ortak in _ortak_listesi(veri, [anahtar]):
                if not isinstance(ortak, dict):
                    continue
                kod = (ortak.get("partner_id") or ortak.get("satici_kodu")
                       or ortak.get("uye_id") or ortak.get("id"))
                ad_parcalari = [ortak.get(a) for a in ("name", "ad", "isim", "ad_soyad") if ortak.get(a)]
                if not ad_parcalari and ortak.get("Ad"):
                    ad_parcalari = [ortak.get("Ad"), ortak.get("Soyad")]
                ad = " ".join(str(p) for p in ad_parcalari if p) or (
                    f"{tur.capitalize()} {kod}" if kod else f"{tur.capitalize()}")
                kayit_durum = str(ortak.get("Durum") or ortak.get("durum") or durum).lower()
                ek_detay = {k: v for k, v in ortak.items()
                            if k not in ("name", "ad", "isim", "ad_soyad")}
                db.satici_ekle(
                    ad=str(ad),
                    satici_kodu=str(kod) if kod is not None else None,
                    tur=tur,
                    eposta=ortak.get("email") or ortak.get("eposta") or ortak.get("E_Posta"),
                    telefon=ortak.get("phone") or ortak.get("telefon") or ortak.get("Telefon"),
                    ulke=ortak.get("country") or ortak.get("ulke"),
                    sehir=ortak.get("city") or ortak.get("sehir") or ortak.get("Il"),
                    kategori=ortak.get("category") or ortak.get("kategori") or ortak.get("Uye_Turu"),
                    durum=kayit_durum,
                    detay={"kaynak_dosya": yol.name, "orijinal": ek_detay},
                )
                adet += 1
        _damga_vur(db, yol, adet, "satici_havuzu")
        print(f"  {yol.name:<55} → {adet} kayıt (tur={tur})")
        toplam += adet
    return toplam


# ---------------------------------------------------------------------------
# 3) MODÜL DURUMLARI → modul_durumlari
# ---------------------------------------------------------------------------

def modul_durumlarini_aktar(db, force: bool) -> int:
    print("\n[3/6] Modül durum dosyaları → modul_durumlari tablosu")
    plan = [
        ("trm_worker", ["worker_state", "status", "state"], BASE_DIR / "worker_status.json"),
        ("healthcheck", ["last_status", "status"], BASE_DIR / "healthcheck_status.json"),
        ("guardian_orchestrator", ["status", "state"], BASE_DIR / "guardian_orchestrator_status.json"),
        ("live_agents", ["system_status", "status"], BASE_DIR / "live_agents_state.json"),
    ]
    toplam = 0
    for modul, alanlar, yol in plan:
        if not yol.exists() or (not force and _damga_var(db, yol)):
            continue
        veri = _json_yukle(yol)
        if veri is None:
            continue
        durum = "bilinmiyor"
        if isinstance(veri, dict):
            for alan in alanlar:
                if veri.get(alan):
                    durum = str(veri[alan])
                    break
        elif isinstance(veri, str):
            durum = veri
        db.modul_durumu_kaydet(modul, durum, {"kaynak_dosya": yol.name, "orijinal": veri})
        _damga_vur(db, yol, 1, "modul_durumlari")
        print(f"  {yol.name:<35} → modul '{modul}' durum='{durum}'")
        toplam += 1
    return toplam


# ---------------------------------------------------------------------------
# 4) LOGLAR → trm_loglar
# ---------------------------------------------------------------------------

def loglari_aktar(db, force: bool) -> int:
    print("\n[4/6] Log dosyaları → trm_loglar tablosu")

    # (yol, modul, tip) — tip: "json_liste" | "json_sozluk" | "jsonl"
    plan = [
        (BASE_DIR / "intelligence_log.json", "istihbarat", "json_karma"),
        (BASE_DIR / "sentinel_alerts.json", "sentinel", "json_karma"),
        (BASE_DIR / "etkilesim_kayitlari.json", "etkilesim_swarm", "json_liste"),
        (BASE_DIR / "dagitim_audit_log.json", "imece_dagitim", "json_karma"),
        (BASE_DIR / "arsivci_meryem_arsiv_log.json", "arsivci_meryem", "json_karma"),
        (BASE_DIR / "sepet_tetikleme_loglari.json", "sepet_tetikleme", "json_liste"),
        (BASE_DIR / "sesli_asistan_loglari.json", "sesli_asistan", "json_liste"),
        (BASE_DIR / "magazanolsun_webhook_events.jsonl", "magazanolsun_webhook", "jsonl"),
        (BASE_DIR / "guardian_central_log.jsonl", "guardian_merkezi", "jsonl"),
        (BASE_DIR / "logs" / "inter_agent_bus.jsonl", "inter_agent_bus", "jsonl"),
        (BASE_DIR / "data" / "smda_batch_log.jsonl", "smda", "jsonl"),
    ]

    toplam = 0
    for yol, modul, tip in plan:
        if not yol.exists() or (not force and _damga_var(db, yol)):
            continue
        adet = 0
        simdi = datetime.now().isoformat(timespec="seconds")

        def _kaydet(kayit: Dict, alt_modul: Optional[str] = None) -> None:
            nonlocal adet
            if not isinstance(kayit, dict):
                return
            mesaj = (kayit.get("message") or kayit.get("mesaj") or kayit.get("log_line")
                     or kayit.get("error_type") or kayit.get("event") or kayit.get("mode")
                     or json.dumps(kayit, ensure_ascii=False, default=str)[:200])
            seviye = str(kayit.get("severity") or kayit.get("level") or kayit.get("seviye")
                         or ("kritik" if kayit.get("error_type") else "info"))
            zaman = _zaman_al(kayit, simdi)
            db.yaz(
                "INSERT INTO trm_loglar (zaman, seviye, modul, mesaj, detay) VALUES (?, ?, ?, ?, ?)",
                (zaman, seviye, alt_modul or modul, str(mesaj), _json_yaz(kayit)),
            )
            adet += 1

        if tip == "jsonl":
            for kayit in _jsonl_yukle(yol):
                _kaydet(kayit)
        else:
            veri = _json_yukle(yol)
            if isinstance(veri, list):
                for kayit in veri:
                    _kaydet(kayit)
            elif isinstance(veri, dict):
                # intelligence_log gibi hem liste hem sözlük biçiminde yazılmış dosyalar
                dugum_listesi = [(None, veri)] if not any(
                    isinstance(v, list) for v in veri.values()
                ) else [(str(anahtar), deger) for anahtar, deger in veri.items()
                        if isinstance(deger, list)]
                for alt_modul, liste in dugum_listesi:
                    for kayit in liste:
                        _kaydet(kayit, modul if alt_modul is None else f"{modul}.{alt_modul}")

        _damga_vur(db, yol, adet, "trm_loglar")
        print(f"  {yol.name:<40} → {adet} log (modul={modul})")
        toplam += adet
    return toplam


# ---------------------------------------------------------------------------
# 5) KUYRUKLAR → is_kuyrugu
# ---------------------------------------------------------------------------

def kuyruklari_aktar(db, force: bool) -> int:
    print("\n[5/6] Kuyruk dosyaları → is_kuyrugu tablosu")
    toplam = 0
    simdi = datetime.now().isoformat(timespec="seconds")

    adaylar: List[tuple] = []
    kuyruk_dizini = BASE_DIR / "data" / "queues"
    if kuyruk_dizini.exists():
        for yol in sorted(kuyruk_dizini.glob("*.json")):
            adaylar.append((yol, yol.stem, "bekliyor"))
    adaylar.append((BASE_DIR / "product_queue.json", "product_queue", "bekliyor"))

    sosyal_kuyruk = BASE_DIR / "sosyal_medya_kuyruk.json"
    if sosyal_kuyruk.exists():
        adaylar.append((sosyal_kuyruk, "sosyal_medya", "bekliyor"))

    for yol, kuyruk_adi, durum in adaylar:
        if not yol.exists() or (not force and _damga_var(db, yol)):
            continue
        veri = _json_yukle(yol)
        if veri is None:
            continue
        # sosyal_medya_kuyruk.json: [{items: [...]}] (payload zarfı) — son zarfın öğeleri
        if kuyruk_adi == "sosyal_medya" and isinstance(veri, list) and veri:
            son_zarf = veri[-1] if isinstance(veri[-1], dict) else {}
            veri = son_zarf.get("items", [])
        if isinstance(veri, dict):
            veri = veri.get("items", [])
        if not isinstance(veri, list):
            continue
        adet = 0
        for kayit in veri:
            if not isinstance(kayit, dict):
                continue
            zaman = _zaman_al(kayit, simdi)
            db.yaz(
                """
                INSERT INTO is_kuyrugu (kuyruk_adi, payload, durum, oncelik,
                                        deneme_sayisi, hata_mesaji, kuyruk_zamani)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (kuyruk_adi, _json_yaz(kayit),
                 durum if kuyruk_adi != "failed" else "hata",
                 int(kayit.get("oncelik", 5)),
                 int(kayit.get("retry_count", 0)),
                 kayit.get("last_error"),
                 zaman),
            )
            adet += 1
        _damga_vur(db, yol, adet, "is_kuyrugu")
        print(f"  {yol.name:<40} → {adet} iş (kuyruk={kuyruk_adi})")
        toplam += adet
    return toplam


# ---------------------------------------------------------------------------
# 6) CEO ERİŞİM DEPOSU → ceo_erisimi
# ---------------------------------------------------------------------------

def ceo_erisimini_aktar(db, force: bool) -> int:
    print("\n[6/6] CEO erişim deposu → ceo_erisimi tablosu")
    yol = BASE_DIR / "data" / "ceo_access_store.json"
    if not yol.exists() or (not force and _damga_var(db, yol)):
        return 0
    veri = _json_yukle(yol)
    if not isinstance(veri, dict):
        return 0
    adet = 0
    for durum_adi, db_durum in (("pending", "beklemede"), ("active", "aktif"), ("passive", "pasif")):
        for kayit in veri.get(durum_adi, []):
            kullanici_id = kayit.get("user_id") if isinstance(kayit, dict) else None
            if not kullanici_id:
                continue
            db.yaz(
                """
                INSERT INTO ceo_erisimi (kullanici_id, ad, durum, son_islem, guncelleme)
                VALUES (?, ?, ?, 'migrasyon', ?)
                ON CONFLICT(kullanici_id) DO NOTHING
                """,
                (str(kullanici_id), kayit.get("name") or kullanici_id, db_durum,
                 _zaman_al(kayit, datetime.now().isoformat(timespec="seconds"))),
            )
            adet += 1
    _damga_vur(db, yol, adet, "ceo_erisimi")
    print(f"  {yol.name:<35} → {adet} kullanıcı")
    return adet


# ---------------------------------------------------------------------------
# Arşivleme — yazıcıları trm_db'ye taşınmış (emekli) dosyalar
# ---------------------------------------------------------------------------

EMEKLI_DOSYALAR = [
    "intelligence_log.json",
    "sentinel_alerts.json",
    "worker_status.json",
    "healthcheck_status.json",
    "guardian_orchestrator_status.json",
    "live_agents_state.json",
    "sesli_asistan_loglari.json",
    "data/agents.json",
    "data/dataagents.json",
    "data/ceo_access_store.json",
    "data/smda_batch_log.jsonl",
    "data/queues/products.json",
    "data/queues/contents.json",
    "data/queues/publish.json",
    "data/queues/failed.json",
    "product_queue.json",
]


def emeklileri_arsivle(db) -> List[str]:
    print("\n[ARŞİV] Yazıcıları trm_db'ye taşınmış JSON dosyaları arşivleniyor...")
    hedef_kok = ARSIV_KOKU / datetime.now().strftime("%Y%m%d_%H%M%S")
    hedef_kok.mkdir(parents=True, exist_ok=True)
    tasinanlar: List[str] = []
    for bagil in EMEKLI_DOSYALAR:
        yol = BASE_DIR / bagil
        if not yol.exists():
            continue
        hedef = hedef_kok / bagil
        hedef.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(yol), str(hedef))
            tasinanlar.append(bagil)
            print(f"  _json_arsiv/{hedef_kok.name}/{bagil}")
        except Exception as exc:
            print(f"  [UYARI] {bagil} taşınamadı: {exc}")
    # Kuyruk kilit dosyaları artık gereksiz
    for kilit in (BASE_DIR / "data" / "queues").glob("*.lock"):
        try:
            kilit.unlink()
            print(f"  silindi: {kilit.name} (dosya kilidi artık gereksiz)")
        except Exception:
            pass
    if tasinanlar:
        db.ayar_kaydet("migrasyon:arsiv_klasoru", {
            "klasor": str(hedef_kok),
            "dosya_sayisi": len(tasinanlar),
            "zaman": datetime.now().isoformat(timespec="seconds"),
        })
    else:
        hedef_kok.rmdir()
        print("  Arşivlenecek emekli dosya bulunamadı.")
    return tasinanlar


# ---------------------------------------------------------------------------
# Ana akış
# ---------------------------------------------------------------------------

def main() -> int:
    arg_yuzey = argparse.ArgumentParser(description="JSON → trm_veritabani.db aktarımı")
    arg_yuzey.add_argument("--sadece-ice-aktar", action="store_true",
                           help="Arşivleme yapma, sadece içe aktar")
    arg_yuzey.add_argument("--force", action="store_true",
                           help="Daha önce aktarılanları da tekrar aktar")
    argumanlar = arg_yuzey.parse_args()

    print("=" * 66)
    print("TRM JSON → SQLite (trm_veritabani.db) Aktarım Sihirbazı")
    print("=" * 66)

    db = trm_db()

    ajanlari_aktar(db, argumanlar.force)
    saticilari_aktar(db, argumanlar.force)
    modul_durumlarini_aktar(db, argumanlar.force)
    loglari_aktar(db, argumanlar.force)
    kuyruklari_aktar(db, argumanlar.force)
    ceo_erisimini_aktar(db, argumanlar.force)

    if not argumanlar.sadece_ice_aktar:
        emeklileri_arsivle(db)

    print("\n" + "=" * 66)
    rapor = db.durum_raporu()
    print(f"AKTARIM TAMAM — {rapor['veritabani']}")
    print(f"Boyut: {rapor['boyut_mb']} MB | Toplam kayıt: {rapor['toplam_kayit']}")
    print("-" * 66)
    for ad, adet in sorted(rapor["tablolar"].items()):
        if adet:
            print(f"  {ad:<22} {adet:>7} satır")
    print("=" * 66)
    db.kapat()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
