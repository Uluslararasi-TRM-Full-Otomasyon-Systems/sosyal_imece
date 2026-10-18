#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Merkezi Veritabanı Katmanı — trm_veritabani.db
=================================================

TRM Ekosistemi'nin tüm verisini (modül durumları, loglar, kullanıcı/satıcı
yönlendirme verileri, otomasyon akışları, iş kuyrukları) tek bir SQLite
veritabanında toplar. Eski, birbiriyle çakışan ve kilitsiz read-modify-write
yapan JSON dosyalarının yerini alır.

YAPININ 3 TEMEL TAŞI
--------------------
1) Merkezi bağlantı : Proje kökünde tek dosya — trm_veritabani.db.
                      Ayrı ayrı dağınık database.db / agent_ecosystem.db /
                      data/queues/*.json dosyaları dönemi biter.

2) Eşzamanlılık     : Süreç içindeki TÜM yazma işlemleri ayrı bir "yazıcı
                      (writer) thread" üzerindeki kuyruktan sırayla işlenir
                      → iki yazma asla iç içe girmez, kilit/yarış durumu
                      oluşmaz. Flask / FastAPI / trm_worker gibi ayrı
                      süreçler arasında ise WAL modu + busy_timeout +
                      otomatik yeniden deneme çakışmayı engeller.
                      "%100 çakışma önleme" bu iki katmanla sağlanır.

3) Otomatik şema    : İlk erişimde (ya da yeni bir tablo eklendiğinde)
                      eksik tablolar CREATE TABLE IF NOT EXISTS ile
                      otomatik oluşturulur. Elle migration gerekmez.

KULLANIM
--------
    from trm_db import trm_db

    db = trm_db()                     # ilk çağrıda tabloları oluşturur
    db.log_yaz("info", "satis", "Yeni sipariş", {"siparis_id": 1234})
    db.modul_durumu_kaydet("api_server_2", "calisiyor")
    db.yonlendirme_kaydet(kullanici_id="u1", kanal="whatsapp", hedef="urun-9")
    db.satici_ekle(ad="Ali Yılmaz", tur="satici")
    db.kuyruga_ekle("products", {"title": "Ürün X"})
    kayit = db.kuyruktan_cek("products")

TÜM MODÜLLER BU TEK KATMANI KULLANIR; bu dosyanın dışında doğrudan
sqlite3.connect(trm_veritabani.db) çağrısı YAPILMAMALIDIR.
"""

from __future__ import annotations

import atexit
import json
import os
import queue
import sqlite3
import sys
import threading
import time
from concurrent.futures import Future
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

BASE_DIR = Path(__file__).resolve().parent
VARSAYILAN_DB_YOLU = BASE_DIR / "trm_veritabani.db"

# Windows konsolu (cp1254) Türkçe karakterleri bozmasın
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Süreçler arası bekleme ayarları
BUSY_TIMEOUT_MS = 10_000        # başka süreç yazarken SQLite'ın bekleme süresi
YAZICI_ZAMAN_ASIMI_S = 60       # tek bir yazma işleminin azami süresi
KILIT_YENIDEN_DENE = 120        # "database is locked" durumunda deneme sayısı


def _simdi() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json_yaz(veri: Any) -> Optional[str]:
    if veri is None:
        return None
    if isinstance(veri, str):
        return veri
    return json.dumps(veri, ensure_ascii=False, default=str)


def _json_coz(metin: Optional[str], varsayilan: Any = None) -> Any:
    if not metin:
        return varsayilan
    try:
        return json.loads(metin)
    except (json.JSONDecodeError, TypeError):
        return varsayilan


# ---------------------------------------------------------------------------
# ŞEMA — Otomatik oluşturulan tablolar
# ---------------------------------------------------------------------------

SEMA_SQL = """
CREATE TABLE IF NOT EXISTS trm_loglar (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    zaman   TEXT NOT NULL,
    seviye  TEXT NOT NULL DEFAULT 'info',
    modul   TEXT NOT NULL DEFAULT 'genel',
    mesaj   TEXT NOT NULL,
    detay   TEXT
);
CREATE INDEX IF NOT EXISTS idx_trm_loglar_zaman  ON trm_loglar(zaman);
CREATE INDEX IF NOT EXISTS idx_trm_loglar_modul ON trm_loglar(modul);
CREATE INDEX IF NOT EXISTS idx_trm_loglar_seviye ON trm_loglar(seviye);

CREATE TABLE IF NOT EXISTS modul_durumlari (
    modul_adi       TEXT PRIMARY KEY,
    durum           TEXT NOT NULL DEFAULT 'bilinmiyor',
    detay           TEXT,
    son_guncelleme  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS yonlendirmeler (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    zaman        TEXT NOT NULL,
    kullanici_id TEXT,
    kullanici_adi TEXT,
    kanal        TEXT,
    kaynak       TEXT,
    hedef        TEXT,
    satici_kodu  TEXT,
    amac         TEXT,
    durum        TEXT DEFAULT 'yapildi',
    detay        TEXT
);
CREATE INDEX IF NOT EXISTS idx_yonlendirmeler_kullanici ON yonlendirmeler(kullanici_id);
CREATE INDEX IF NOT EXISTS idx_yonlendirmeler_satici   ON yonlendirmeler(satici_kodu);
CREATE INDEX IF NOT EXISTS idx_yonlendirmeler_zaman    ON yonlendirmeler(zaman);

CREATE TABLE IF NOT EXISTS satici_havuzu (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    satici_kodu    TEXT UNIQUE,
    ad             TEXT NOT NULL,
    tur            TEXT DEFAULT 'satici',
    eposta         TEXT,
    telefon        TEXT,
    ulke           TEXT,
    sehir          TEXT,
    kategori       TEXT,
    durum          TEXT DEFAULT 'aktif',
    puan           REAL DEFAULT 0,
    detay          TEXT,
    kayit_zamani   TEXT NOT NULL,
    son_guncelleme TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_satici_havuzu_durum ON satici_havuzu(durum);
CREATE INDEX IF NOT EXISTS idx_satici_havuzu_tur   ON satici_havuzu(tur);

CREATE TABLE IF NOT EXISTS otomasyon_akislari (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    akis_adi TEXT NOT NULL,
    adim     TEXT,
    durum    TEXT DEFAULT 'basladi',
    detay    TEXT,
    zaman    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_otomasyon_akislari_akis ON otomasyon_akislari(akis_adi);
CREATE INDEX IF NOT EXISTS idx_otomasyon_akislari_zaman ON otomasyon_akislari(zaman);

CREATE TABLE IF NOT EXISTS is_kuyrugu (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kuyruk_adi      TEXT NOT NULL,
    payload         TEXT NOT NULL,
    durum           TEXT NOT NULL DEFAULT 'bekliyor',
    oncelik         INTEGER NOT NULL DEFAULT 5,
    deneme_sayisi   INTEGER NOT NULL DEFAULT 0,
    hata_mesaji     TEXT,
    kuyruk_zamani   TEXT NOT NULL,
    islenme_zamani  TEXT,
    bitis_zamani    TEXT
);
CREATE INDEX IF NOT EXISTS idx_is_kuyrugu_ad_durum ON is_kuyrugu(kuyruk_adi, durum);
CREATE INDEX IF NOT EXISTS idx_is_kuyrugu_sira ON is_kuyrugu(durum, oncelik, id);
CREATE INDEX IF NOT EXISTS idx_is_kuyrugu_zaman ON is_kuyrugu(kuyruk_zamani);

CREATE TABLE IF NOT EXISTS ajanlar (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ajan_kodu       TEXT UNIQUE,
    ad              TEXT NOT NULL,
    rol             TEXT,
    tur             TEXT,
    durum           TEXT DEFAULT 'beklemede',
    son_kalp_atisi  TEXT,
    detay           TEXT,
    kayit_zamani    TEXT NOT NULL,
    son_guncelleme  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ajanlar_durum ON ajanlar(durum);

CREATE TABLE IF NOT EXISTS ayarlar (
    anahtar        TEXT PRIMARY KEY,
    deger          TEXT,
    son_guncelleme TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ceo_erisimi (
    kullanici_id TEXT PRIMARY KEY,
    ad           TEXT,
    durum        TEXT NOT NULL DEFAULT 'beklemede',
    son_islem    TEXT,
    guncelleme   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ceo_erisimi_durum ON ceo_erisimi(durum);

-- Aşağıdaki tablolar agent_ecosystem_backend.py (FastAPI :8000) ile birebir
-- uyumlu olacak şekilde merkez veritabanına dahil edilmiştir.
CREATE TABLE IF NOT EXISTS agencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_id INTEGER,
    name TEXT NOT NULL,
    type TEXT,
    status TEXT DEFAULT 'idle',
    last_active TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (agency_id) REFERENCES agencies(id)
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
CREATE TABLE IF NOT EXISTS brand_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name TEXT NOT NULL,
    proposal_amount REAL,
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'pending',
    agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
CREATE TABLE IF NOT EXISTS customer_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    request_text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_time TEXT,
    event_type TEXT,
    status TEXT DEFAULT 'scheduled',
    agent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);
CREATE TABLE IF NOT EXISTS system_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL UNIQUE,
    metric_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

TABLO_ADLARI = [
    "trm_loglar", "modul_durumlari", "yonlendirmeler", "satici_havuzu",
    "otomasyon_akislari", "is_kuyrugu", "ajanlar", "ayarlar", "ceo_erisimi",
    "agencies", "agents", "tasks", "brand_proposals", "customer_requests",
    "calendar_events", "system_status",
]


# ---------------------------------------------------------------------------
# Ana sınıf
# ---------------------------------------------------------------------------

class TRMVeritabani:
    """trm_veritabani.db üzerinde iş parçacığı ve süreç güvenli veri katmanı.

    Yazma modeli: çağıran thread, işi kuyruğa bırakır ve (isteğe bağlı)
    sonucu bekler. Tek bir yazıcı thread işleri FIFO sırayla, tek bir
    bağlantı üzerinden uygular → çakışma imkânsız.
    """

    _ornek: Optional["TRMVeritabani"] = None
    _ornek_kilidi = threading.Lock()

    def __init__(self, db_yolu: Optional[os.PathLike | str] = None):
        yol = os.environ.get("TRM_VERITABANI_YOLU") or db_yolu or VARSAYILAN_DB_YOLU
        self.db_yolu = Path(yol)
        self.db_yolu.parent.mkdir(parents=True, exist_ok=True)

        self.zaman_asimi = YAZICI_ZAMAN_ASIMI_S
        self._kapaniyor = False
        self._yazma_kuyrugu: "queue.Queue" = queue.Queue()

        self._baglanti = sqlite3.connect(
            str(self.db_yolu),
            timeout=BUSY_TIMEOUT_MS / 1000.0,
            isolation_level="DEFERRED",
            check_same_thread=False,
        )
        self._baglanti.row_factory = sqlite3.Row
        self._baglanti.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        self._baglanti.execute("PRAGMA journal_mode=WAL")
        self._baglanti.execute("PRAGMA synchronous=NORMAL")
        self._baglanti.execute("PRAGMA foreign_keys=ON")

        self._yazici_thread = threading.Thread(
            target=self._yazici_dongusu, name="TRM-DB-Yazici", daemon=True
        )
        self._yazici_thread.start()

        # Otomatik tablo oluşturma (başlangıç fonksiyonu)
        self.tablolari_olustur()

        atexit.register(self.kapat)
        print(f"[TRM-DB] trm_veritabani.db hazır → {self.db_yolu} "
              f"({len(TABLO_ADLARI)} tablo, WAL modu, yazıcı kuyruğu aktif)")

    # ------------------------------------------------------------------
    # Tekil (singleton) erişim
    # ------------------------------------------------------------------

    @classmethod
    def ornek_al(cls, db_yolu: Optional[os.PathLike | str] = None) -> "TRMVeritabani":
        with cls._ornek_kilidi:
            if cls._ornek is None:
                cls._ornek = TRMVeritabani(db_yolu)
            return cls._ornek

    # ------------------------------------------------------------------
    # Yazıcı thread (eşzamanlılık çekirdeği)
    # ------------------------------------------------------------------

    def _yazici_dongusu(self) -> None:
        while True:
            isi = self._yazma_kuyrugu.get()
            if isi is None:
                break
            tip, deger, future = isi
            try:
                with self._baglanti:  # işlem sonunda otomatik commit
                    sonuc = self._islemi_uygula(tip, deger)
                if future is not None:
                    future.set_result(sonuc)
            except BaseException as exc:  # noqa: BLE001 — çağırana iletmeli
                if future is not None:
                    future.set_exception(exc)
                else:
                    print(f"[TRM-DB] Yazma hatası (beklemesiz iş): {exc}")
        try:
            self._baglanti.close()
        except Exception:
            pass

    def _islemi_uygula(self, tip: str, deger: Any) -> Any:
        if tip == "exec":
            sql, params = deger
            cur = self._tekrar_dene(lambda: self._baglanti.execute(sql, params))
            return {"lastrowid": cur.lastrowid, "rowcount": cur.rowcount}
        if tip == "execmany":
            sql, dizi = deger
            cur = self._tekrar_dene(lambda: self._baglanti.executemany(sql, dizi))
            return {"rowcount": cur.rowcount}
        if tip == "script":
            self._baglanti.executescript(deger)
            return True
        if tip == "fn":
            return deger(self._baglanti)
        raise ValueError(f"Bilinmeyen işlem tipi: {tip}")

    def _tekrar_dene(self, f: Callable[[], Any]) -> Any:
        """Süreçler arası 'database is locked' hatalarına karşı yeniden dene."""
        for deneme in range(KILIT_YENIDEN_DENE):
            try:
                return f()
            except sqlite3.OperationalError as exc:
                mesaj = str(exc).lower()
                if "locked" in mesaj or "busy" in mesaj:
                    time.sleep(min(0.05 * (deneme + 1), 1.0))
                    continue
                raise
        raise sqlite3.OperationalError("Veritabanı uzun süre kilitli kaldı")

    # ------------------------------------------------------------------
    # Düşük seviye API
    # ------------------------------------------------------------------

    def yaz(self, sql: str, params: Sequence = (), bekle: bool = True) -> Optional[Dict]:
        """Tek SQL yazma işlemi. Kuyruğa girer, yazıcı thread sırayla uygular.

        bekle=True  → sonucu ({"lastrowid", "rowcount"}) döndürür.
        bekle=False → işi kuyruğa bırakır, beklemez (ateşle-ve-unut).
        """
        future = Future() if bekle else None
        self._yazma_kuyrugu.put(("exec", (sql, tuple(params)), future))
        if future is not None:
            return future.result(timeout=self.zaman_asimi)
        return None

    def yaz_coklu(self, islemler: List[Tuple[str, Sequence]], bekle: bool = True) -> Optional[List[int]]:
        """Birden çok yazma işlemini TEK işlem (transaction) içinde uygular.

        islemler: [(sql, params), ...] → her satırın lastrowid listesi.
        Ya hepsi uygulanır ya da hiçbiri.
        """
        future = Future() if bekle else None

        def _uygula(conn: sqlite3.Connection) -> List[int]:
            sonuc: List[int] = []
            for sql, params in islemler:
                cur = self._tekrar_dene(lambda s=sql, p=params: conn.execute(s, tuple(p)))
                sonuc.append(cur.lastrowid)
            return sonuc

        self._yazma_kuyrugu.put(("fn", _uygula, future))
        if future is not None:
            return future.result(timeout=self.zaman_asimi)
        return None

    def yaz_fonksiyon(self, fn: Callable[[sqlite3.Connection], Any], bekle: bool = True) -> Any:
        """Birden fazla sorguyu atomik yapmak için ham bağlantı veren API.

        fn, yazıcı thread içinde tek işlem bağlamında çalışır; fn içinde
        commit/rollback YAPILMAZ (otomatik yönetilir).
        """
        future = Future() if bekle else None
        self._yazma_kuyrugu.put(("fn", fn, future))
        if future is not None:
            return future.result(timeout=self.zaman_asimi)
        return None

    def oku(self, sql: str, params: Sequence = ()) -> List[Dict]:
        """Okuma (SELECT). WAL sayesinde yazarken bile engellenmez."""
        conn = sqlite3.connect(str(self.db_yolu), timeout=BUSY_TIMEOUT_MS / 1000.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
            satirlar = self._tekrar_dene(lambda: conn.execute(sql, tuple(params)).fetchall())
            return [dict(satir) for satir in satirlar]
        finally:
            conn.close()

    def oku_tek(self, sql: str, params: Sequence = ()) -> Optional[Dict]:
        satirlar = self.oku(sql, params)
        return satirlar[0] if satirlar else None

    # ------------------------------------------------------------------
    # Otomatik tablo oluşturma
    # ------------------------------------------------------------------

    def tablolari_olustur(self) -> bool:
        """Eksik tabloları oluşturur (idempotent — her açılışta güvenle çalışır)."""
        future = Future()
        self._yazma_kuyrugu.put(("script", SEMA_SQL, future))
        return bool(future.result(timeout=self.zaman_asimi))

    # ------------------------------------------------------------------
    # LOGLAR — trm_loglar
    # ------------------------------------------------------------------

    def log_yaz(self, seviye: str = "info", modul: str = "genel",
                mesaj: str = "", detay: Any = None, bekle: bool = True) -> Optional[int]:
        sonuc = self.yaz(
            "INSERT INTO trm_loglar (zaman, seviye, modul, mesaj, detay) VALUES (?, ?, ?, ?, ?)",
            (_simdi(), seviye, modul, mesaj, _json_yaz(detay)),
            bekle=bekle,
        )
        return sonuc["lastrowid"] if sonuc else None

    def loglari_getir(self, adet: int = 100, modul: Optional[str] = None,
                      seviye: Optional[str] = None) -> List[Dict]:
        sorgu = "SELECT * FROM trm_loglar"
        kosullar: List[str] = []
        params: List[Any] = []
        if modul:
            kosullar.append("modul = ?"); params.append(modul)
        if seviye:
            kosullar.append("seviye = ?"); params.append(seviye)
        if kosullar:
            sorgu += " WHERE " + " AND ".join(kosullar)
        sorgu += " ORDER BY id DESC LIMIT ?"
        params.append(int(adet))
        return self.oku(sorgu, params)

    def log_sayisi(self, modul: Optional[str] = None) -> int:
        if modul:
            satir = self.oku_tek("SELECT COUNT(*) AS n FROM trm_loglar WHERE modul = ?", (modul,))
        else:
            satir = self.oku_tek("SELECT COUNT(*) AS n FROM trm_loglar")
        return int(satir["n"]) if satir else 0

    def eski_loglari_sil(self, gun: int = 30) -> int:
        """Bakım: X günden eski logları siler, silinen satır sayısını döndürür."""
        sinir = (datetime.now() - timedelta(days=gun)).isoformat(timespec="seconds")
        sonuc = self.yaz("DELETE FROM trm_loglar WHERE zaman < ?", (sinir,))
        return sonuc["rowcount"] if sonuc else 0

    # ------------------------------------------------------------------
    # MODÜL DURUMLARI — modul_durumlari
    # ------------------------------------------------------------------

    def modul_durumu_kaydet(self, modul_adi: str, durum: str, detay: Any = None) -> bool:
        sonuc = self.yaz(
            """
            INSERT INTO modul_durumlari (modul_adi, durum, detay, son_guncelleme)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(modul_adi) DO UPDATE SET
                durum = excluded.durum,
                detay = excluded.detay,
                son_guncelleme = excluded.son_guncelleme
            """,
            (modul_adi, durum, _json_yaz(detay), _simdi()),
        )
        return bool(sonuc and sonuc["rowcount"])

    def modul_durumlari_getir(self) -> List[Dict]:
        return self.oku("SELECT * FROM modul_durumlari ORDER BY modul_adi")

    def modul_durumu_getir(self, modul_adi: str) -> Optional[Dict]:
        satir = self.oku_tek("SELECT * FROM modul_durumlari WHERE modul_adi = ?", (modul_adi,))
        if satir and "detay" in satir:
            satir["detay"] = _json_coz(satir.get("detay"))
        return satir

    # ------------------------------------------------------------------
    # YÖNLENDİRMELER — yonlendirmeler
    # ------------------------------------------------------------------

    def yonlendirme_kaydet(self, kullanici_id: Optional[str] = None,
                           kullanici_adi: Optional[str] = None,
                           kanal: Optional[str] = None,
                           kaynak: Optional[str] = None,
                           hedef: Optional[str] = None,
                           satici_kodu: Optional[str] = None,
                           amac: Optional[str] = None,
                           durum: str = "yapildi",
                           detay: Any = None) -> Optional[int]:
        sonuc = self.yaz(
            """
            INSERT INTO yonlendirmeler
            (zaman, kullanici_id, kullanici_adi, kanal, kaynak, hedef,
             satici_kodu, amac, durum, detay)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (_simdi(), kullanici_id, kullanici_adi, kanal, kaynak, hedef,
             satici_kodu, amac, durum, _json_yaz(detay)),
        )
        return sonuc["lastrowid"] if sonuc else None

    def yonendirmeleri_getir(self, adet: int = 100,
                             kullanici_id: Optional[str] = None,
                             satici_kodu: Optional[str] = None) -> List[Dict]:
        sorgu = "SELECT * FROM yonlendirmeler"
        kosullar: List[str] = []
        params: List[Any] = []
        if kullanici_id:
            kosullar.append("kullanici_id = ?"); params.append(kullanici_id)
        if satici_kodu:
            kosullar.append("satici_kodu = ?"); params.append(satici_kodu)
        if kosullar:
            sorgu += " WHERE " + " AND ".join(kosullar)
        sorgu += " ORDER BY id DESC LIMIT ?"
        params.append(int(adet))
        satirlar = self.oku(sorgu, params)
        for satir in satirlar:
            satir["detay"] = _json_coz(satir.get("detay"))
        return satirlar

    # ------------------------------------------------------------------
    # SATICI HAVUZU — satici_havuzu
    # ------------------------------------------------------------------

    def satici_ekle(self, ad: str, satici_kodu: Optional[str] = None,
                    tur: str = "satici", eposta: Optional[str] = None,
                    telefon: Optional[str] = None, ulke: Optional[str] = None,
                    sehir: Optional[str] = None, kategori: Optional[str] = None,
                    durum: str = "aktif", puan: float = 0.0,
                    detay: Any = None) -> str:
        """Satıcı/ortak/üye kaydını ekler veya günceller (satici_kodu ile upsert)."""
        if not satici_kodu:
            rastgele = f"{int(time.time() * 1000) % 1_000_000_000:09d}"
            satici_kodu = f"{tur.upper()}-{datetime.now().strftime('%Y%m%d')}-{rastgele[-6:]}"
        self.yaz(
            """
            INSERT INTO satici_havuzu
            (satici_kodu, ad, tur, eposta, telefon, ulke, sehir, kategori,
             durum, puan, detay, kayit_zamani, son_guncelleme)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(satici_kodu) DO UPDATE SET
                ad = excluded.ad, tur = excluded.tur, eposta = excluded.eposta,
                telefon = excluded.telefon, ulke = excluded.ulke, sehir = excluded.sehir,
                kategori = excluded.kategori, durum = excluded.durum,
                puan = excluded.puan, detay = excluded.detay,
                son_guncelleme = excluded.son_guncelleme
            """,
            (satici_kodu, ad, tur, eposta, telefon, ulke, sehir, kategori,
             durum, float(puan), _json_yaz(detay), _simdi(), _simdi()),
        )
        return satici_kodu

    def saticilari_getir(self, tur: Optional[str] = None,
                          durum: Optional[str] = None,
                          adet: int = 500) -> List[Dict]:
        sorgu = "SELECT * FROM satici_havuzu"
        kosullar: List[str] = []
        params: List[Any] = []
        if tur:
            kosullar.append("tur = ?"); params.append(tur)
        if durum:
            kosullar.append("durum = ?"); params.append(durum)
        if kosullar:
            sorgu += " WHERE " + " AND ".join(kosullar)
        sorgu += " ORDER BY id DESC LIMIT ?"
        params.append(int(adet))
        satirlar = self.oku(sorgu, params)
        for satir in satirlar:
            satir["detay"] = _json_coz(satir.get("detay"))
        return satirlar

    def satici_durum_guncelle(self, satici_kodu: str, durum: str, puan: Optional[float] = None) -> bool:
        sonuc = self.yaz(
            "UPDATE satici_havuzu SET durum = ?, son_guncelleme = ? WHERE satici_kodu = ?",
            (durum, _simdi(), satici_kodu),
        )
        if puan is not None:
            self.yaz("UPDATE satici_havuzu SET puan = ? WHERE satici_kodu = ?",
                     (float(puan), satici_kodu))
        return bool(sonuc and sonuc["rowcount"])

    # ------------------------------------------------------------------
    # OTOMASYON AKIŞLARI — otomasyon_akislari
    # ------------------------------------------------------------------

    def akis_adimi_kaydet(self, akis_adi: str, adim: Optional[str] = None,
                          durum: str = "basladi", detay: Any = None) -> Optional[int]:
        sonuc = self.yaz(
            """
            INSERT INTO otomasyon_akislari (akis_adi, adim, durum, detay, zaman)
            VALUES (?, ?, ?, ?, ?)
            """,
            (akis_adi, adim, durum, _json_yaz(detay), _simdi()),
        )
        return sonuc["lastrowid"] if sonuc else None

    def akislari_getir(self, akis_adi: Optional[str] = None, adet: int = 200) -> List[Dict]:
        if akis_adi:
            satirlar = self.oku(
                "SELECT * FROM otomasyon_akislari WHERE akis_adi = ? ORDER BY id DESC LIMIT ?",
                (akis_adi, int(adet)),
            )
        else:
            satirlar = self.oku("SELECT * FROM otomasyon_akislari ORDER BY id DESC LIMIT ?",
                                (int(adet),))
        for satir in satirlar:
            satir["detay"] = _json_coz(satir.get("detay"))
        return satirlar

    # ------------------------------------------------------------------
    # İŞ KUYRUĞU — is_kuyrugu (eski QUEUE_MANAGER / data/queues/*.json yerine)
    # ------------------------------------------------------------------

    def kuyruga_ekle(self, kuyruk_adi: str, payload: Any, oncelik: int = 5) -> Optional[int]:
        sonuc = self.yaz(
            """
            INSERT INTO is_kuyrugu (kuyruk_adi, payload, durum, oncelik, kuyruk_zamani)
            VALUES (?, ?, 'bekliyor', ?, ?)
            """,
            (kuyruk_adi, _json_yaz(payload), int(oncelik), _simdi()),
        )
        return sonuc["lastrowid"] if sonuc else None

    def kuyruktan_cek(self, kuyruk_adi: str) -> Optional[Dict]:
        """Kuyruğun sıradaki işini ATOMİK olarak çeker ve kuyruktan düşürür.

        Öncelik küçük olan önce; eşitlikte önce giren önce (FIFO).
        Bu işlem tek transaction'da SELECT+DELETE yapar → iki thread aynı
        işi asla iki kez alamaz.
        """
        def _cek(conn: sqlite3.Connection) -> Optional[Dict]:
            satir = self._tekrar_dene(lambda: conn.execute(
                """
                SELECT id, payload, oncelik, kuyruk_zamani FROM is_kuyrugu
                WHERE kuyruk_adi = ? AND durum = 'bekliyor'
                ORDER BY oncelik ASC, id ASC LIMIT 1
                """,
                (kuyruk_adi,),
            ).fetchone())
            if satir is None:
                return None
            self._tekrar_dene(lambda: conn.execute(
                "DELETE FROM is_kuyrugu WHERE id = ?", (satir["id"],)
            ))
            return {
                "id": satir["id"],
                "payload": _json_coz(satir["payload"]),
                "oncelik": satir["oncelik"],
                "queued_at": satir["kuyruk_zamani"],
            }

        return self.yaz_fonksiyon(_cek)

    def kuyruktan_al(self, kuyruk_adi: str) -> Optional[Dict]:
        """İşi 'isleniyor' olarak REZERVE eder (kuyrukta kalır). Uzun işler için.

        Bitirirken kuyruk_sonuc(id, durum) çağrılmalıdır.
        """
        def _al(conn: sqlite3.Connection) -> Optional[Dict]:
            satir = self._tekrar_dene(lambda: conn.execute(
                """
                SELECT id, payload, oncelik FROM is_kuyrugu
                WHERE kuyruk_adi = ? AND durum = 'bekliyor'
                ORDER BY oncelik ASC, id ASC LIMIT 1
                """,
                (kuyruk_adi,),
            ).fetchone())
            if satir is None:
                return None
            self._tekrar_dene(lambda: conn.execute(
                "UPDATE is_kuyrugu SET durum = 'isleniyor', islenme_zamani = ? WHERE id = ?",
                (_simdi(), satir["id"]),
            ))
            return {"id": satir["id"], "payload": _json_coz(satir["payload"]),
                    "oncelik": satir["oncelik"]}

        return self.yaz_fonksiyon(_al)

    def kuyruk_sonuc(self, is_id: int, durum: str, hata_mesaji: Optional[str] = None,
                     deneme_artir: bool = False) -> bool:
        sonuc = self.yaz(
            """
            UPDATE is_kuyrugu
            SET durum = ?, hata_mesaji = ?, bitis_zamani = ?,
                deneme_sayisi = deneme_sayisi + ?
            WHERE id = ?
            """,
            (durum, hata_mesaji, _simdi(), 1 if deneme_artir else 0, int(is_id)),
        )
        return bool(sonuc and sonuc["rowcount"])

    def kuyruk_boyut(self, kuyruk_adi: Optional[str] = None,
                     durum: Optional[str] = "bekliyor") -> int:
        sorgu = "SELECT COUNT(*) AS n FROM is_kuyrugu"
        kosullar: List[str] = []
        params: List[Any] = []
        if kuyruk_adi:
            kosullar.append("kuyruk_adi = ?"); params.append(kuyruk_adi)
        if durum:
            kosullar.append("durum = ?"); params.append(durum)
        if kosullar:
            sorgu += " WHERE " + " AND ".join(kosullar)
        satir = self.oku_tek(sorgu, params)
        return int(satir["n"]) if satir else 0

    def kuyruk_gozlemle(self, kuyruk_adi: str, adet: int = 5) -> List[Dict]:
        satirlar = self.oku(
            "SELECT id, payload, oncelik, kuyruk_zamani FROM is_kuyrugu "
            "WHERE kuyruk_adi = ? AND durum = 'bekliyor' ORDER BY oncelik ASC, id ASC LIMIT ?",
            (kuyruk_adi, int(adet)),
        )
        for satir in satirlar:
            satir["payload"] = _json_coz(satir["payload"])
        return satirlar

    def kuyruk_eski_temizle(self, max_saat: int = 48,
                            kuyruk_adi: Optional[str] = None) -> int:
        """Eski kayıtları temizler (eski clear_stale davranışının karşılığı).

        Belirtilen saatten eski, 'isleniyor' olmayan tüm kayıtları siler.
        """
        sinir = (datetime.now() - timedelta(hours=max_saat)).isoformat(timespec="seconds")
        if kuyruk_adi:
            sonuc = self.yaz(
                "DELETE FROM is_kuyrugu WHERE kuyruk_zamani < ? AND kuyruk_adi = ? AND durum != 'isleniyor'",
                (sinir, kuyruk_adi),
            )
        else:
            sonuc = self.yaz(
                "DELETE FROM is_kuyrugu WHERE kuyruk_zamani < ? AND durum != 'isleniyor'",
                (sinir,),
            )
        return sonuc["rowcount"] if sonuc else 0

    def kuyruk_istatistik(self, kuyruk_adi: Optional[str] = None) -> List[Dict]:
        if kuyruk_adi:
            return self.oku(
                "SELECT kuyruk_adi, durum, COUNT(*) AS adet FROM is_kuyrugu "
                "WHERE kuyruk_adi = ? GROUP BY kuyruk_adi, durum", (kuyruk_adi,))
        return self.oku(
            "SELECT kuyruk_adi, durum, COUNT(*) AS adet FROM is_kuyrugu "
            "GROUP BY kuyruk_adi, durum ORDER BY kuyruk_adi")

    # ------------------------------------------------------------------
    # AJANLAR — ajanlar
    # ------------------------------------------------------------------

    def ajan_kaydet(self, ad: str, ajan_kodu: Optional[str] = None, rol: Optional[str] = None,
                    tur: Optional[str] = None, durum: str = "beklemede",
                    detay: Any = None) -> str:
        if not ajan_kodu:
            ajan_kodu = ad.strip().replace(" ", "_").upper()[:60]
        self.yaz(
            """
            INSERT INTO ajanlar (ajan_kodu, ad, rol, tur, durum, son_kalp_atisi, detay,
                                 kayit_zamani, son_guncelleme)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ajan_kodu) DO UPDATE SET
                ad = excluded.ad, rol = excluded.rol, tur = excluded.tur,
                durum = excluded.durum, son_kalp_atisi = excluded.son_kalp_atisi,
                detay = excluded.detay, son_guncelleme = excluded.son_guncelleme
            """,
            (ajan_kodu, ad, rol, tur, durum, _simdi(), _json_yaz(detay), _simdi(), _simdi()),
        )
        return ajan_kodu

    def ajan_durum_guncelle(self, ajan_kodu: str, durum: str) -> bool:
        sonuc = self.yaz(
            "UPDATE ajanlar SET durum = ?, son_kalp_atisi = ?, son_guncelleme = ? WHERE ajan_kodu = ?",
            (durum, _simdi(), _simdi(), ajan_kodu),
        )
        return bool(sonuc and sonuc["rowcount"])

    def ajanlari_getir(self, durum: Optional[str] = None, adet: int = 1000) -> List[Dict]:
        if durum:
            satirlar = self.oku("SELECT * FROM ajanlar WHERE durum = ? ORDER BY id LIMIT ?",
                                (durum, int(adet)))
        else:
            satirlar = self.oku("SELECT * FROM ajanlar ORDER BY id LIMIT ?", (int(adet),))
        for satir in satirlar:
            satir["detay"] = _json_coz(satir.get("detay"))
        return satirlar

    # ------------------------------------------------------------------
    # AYARLAR — ayarlar (key/value)
    # ------------------------------------------------------------------

    def ayar_kaydet(self, anahtar: str, deger: Any) -> bool:
        sonuc = self.yaz(
            """
            INSERT INTO ayarlar (anahtar, deger, son_guncelleme) VALUES (?, ?, ?)
            ON CONFLICT(anahtar) DO UPDATE SET
                deger = excluded.deger, son_guncelleme = excluded.son_guncelleme
            """,
            (anahtar, _json_yaz(deger), _simdi()),
        )
        return bool(sonuc and sonuc["rowcount"])

    def ayar_oku(self, anahtar: str, varsayilan: Any = None) -> Any:
        satir = self.oku_tek("SELECT deger FROM ayarlar WHERE anahtar = ?", (anahtar,))
        if not satir:
            return varsayilan
        return _json_coz(satir.get("deger"), varsayilan)

    # ------------------------------------------------------------------
    # CEO ERİŞİM YÖNETİMİ — ceo_erisimi (eski data/ceo_access_store.json)
    # ------------------------------------------------------------------

    def ceo_talep_ekle(self, kullanici_id: str, ad: Optional[str] = None) -> None:
        self.yaz(
            """
            INSERT INTO ceo_erisimi (kullanici_id, ad, durum, son_islem, guncelleme)
            VALUES (?, ?, 'beklemede', 'talep', ?)
            ON CONFLICT(kullanici_id) DO NOTHING
            """,
            (kullanici_id, ad or kullanici_id, _simdi()),
        )

    def ceo_onayla(self, kullanici_id: str, ad: Optional[str] = None) -> None:
        self.yaz(
            """
            INSERT INTO ceo_erisimi (kullanici_id, ad, durum, son_islem, guncelleme)
            VALUES (?, COALESCE(?, ?), 'aktif', 'onay', ?)
            ON CONFLICT(kullanici_id) DO UPDATE SET
                durum = 'aktif', son_islem = 'onay', guncelleme = excluded.guncelleme
            """,
            (kullanici_id, ad, kullanici_id, _simdi()),
        )

    def ceo_pasiflestir(self, kullanici_id: str, ad: Optional[str] = None) -> None:
        self.yaz(
            """
            INSERT INTO ceo_erisimi (kullanici_id, ad, durum, son_islem, guncelleme)
            VALUES (?, COALESCE(?, ?), 'pasif', 'pasif', ?)
            ON CONFLICT(kullanici_id) DO UPDATE SET
                durum = 'pasif', son_islem = 'pasif', guncelleme = excluded.guncelleme
            """,
            (kullanici_id, ad, kullanici_id, _simdi()),
        )

    def ceo_sil(self, kullanici_id: str, durum: Optional[str] = None) -> int:
        """CEO erişim kaydını siler. durum verilirse yalnız o durumdakini siler.

        Dönüş: silinen satır sayısı.
        """
        if durum:
            sonuc = self.yaz(
                "DELETE FROM ceo_erisimi WHERE kullanici_id = ? AND durum = ?",
                (kullanici_id, durum),
            )
        else:
            sonuc = self.yaz("DELETE FROM ceo_erisimi WHERE kullanici_id = ?", (kullanici_id,))
        return sonuc["rowcount"] if sonuc else 0

    def ceo_tumunu_onayla(self) -> int:
        sonuc = self.yaz(
            "UPDATE ceo_erisimi SET durum = 'aktif', son_islem = 'toplu_onay', guncelleme = ? WHERE durum = 'beklemede'",
            (_simdi(),),
        )
        return sonuc["rowcount"] if sonuc else 0

    def ceo_tum_oturumlari_kapat(self) -> int:
        sonuc = self.yaz(
            "DELETE FROM ceo_erisimi WHERE durum = 'aktif'",
        )
        return sonuc["rowcount"] if sonuc else 0

    def ceo_durumlar(self) -> Dict[str, List[Dict]]:
        """Eski ceo_access_store.json biçimi: {"pending": [...], "active": [...], "passive": [...]}"""
        eslesme = {"beklemede": "pending", "aktif": "active", "pasif": "passive"}
        sonuc: Dict[str, List[Dict]] = {"pending": [], "active": [], "passive": []}
        for satir in self.oku("SELECT * FROM ceo_erisimi ORDER BY guncelleme"):
            kayit = {
                "user_id": satir["kullanici_id"],
                "name": satir.get("ad") or satir["kullanici_id"],
                "updated_at": satir.get("guncelleme"),
            }
            sonuc[eslesme.get(satir["durum"], "pending")].append(kayit)
        return sonuc

    # ------------------------------------------------------------------
    # DURUM RAPORU (panel / denetim için)
    # ------------------------------------------------------------------

    def durum_raporu(self) -> Dict:
        tablolar: Dict[str, int] = {}
        toplam = 0
        for satir in self.oku(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            ad = satir["name"]
            sayim = self.oku_tek(f'SELECT COUNT(*) AS n FROM "{ad}"')
            adet = int(sayim["n"]) if sayim else 0
            tablolar[ad] = adet
            toplam += adet
        try:
            boyut = os.path.getsize(self.db_yolu)
        except OSError:
            boyut = 0
        mod = self.oku("PRAGMA journal_mode")
        return {
            "veritabani": str(self.db_yolu),
            "boyut_mb": round(boyut / (1024 * 1024), 3),
            "journal_mode": mod[0]["journal_mode"] if mod else "bilinmiyor",
            "yazici_kuyruk_uzunlugu": self._yazma_kuyrugu.qsize(),
            "yazici_thread_canli": self._yazici_thread.is_alive(),
            "toplam_kayit": toplam,
            "tablolar": tablolar,
            "zaman": _simdi(),
        }

    # ------------------------------------------------------------------
    # KAPANIŞ
    # ------------------------------------------------------------------

    def kapat(self) -> None:
        """Kuyruktaki tüm bekleyen işleri tamamlar, yazıcı thread'i kapatır."""
        if self._kapaniyor:
            return
        self._kapaniyor = True
        self._yazma_kuyrugu.put(None)  # FIFO: önceki tüm işler bitince kapanır
        self._yazici_thread.join(timeout=self.zaman_asimi)
        if TRMVeritabani._ornek is self:
            TRMVeritabani._ornek = None

    def __enter__(self) -> "TRMVeritabani":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.kapat()


def trm_db() -> TRMVeritabani:
    """Merkezi veritabanı tekil (singleton) örneğini döndürür.

    İlk çağrıda veritabanını açar, WAL modunu ayarlar ve eksik tabloları
    otomatik oluşturur. Proje içinde veri erişimi HER ZAMAN bu fonksiyon
    üzerinden yapılmalıdır.
    """
    return TRMVeritabani.ornek_al()


# ---------------------------------------------------------------------------
# ÖZ KENDİ TESTİ — python trm_db.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 62)
    print("TRM Merkezi Veritabanı — Eşzamanlılık ve Doğru Davranış Testi")
    print("=" * 62)

    db = trm_db()

    # 1) Temel CRUD
    db.modul_durumu_kaydet("test_modul", "calisiyor", {"nabiz": 1})
    assert db.modul_durumu_getir("test_modul")["durum"] == "calisiyor"

    kod = db.satici_ekle(ad="Test Satıcı", tur="satici", sehir="İstanbul")
    assert db.saticilari_getir(tur="satici")[0]["satici_kodu"] == kod

    db.yonlendirme_kaydet(kullanici_id="u-1", kanal="whatsapp", hedef="urun-1", satici_kodu=kod)
    assert len(db.yonendirmeleri_getir(kullanici_id="u-1")) == 1

    db.akis_adimi_kaydet("test_akis", "adim-1", "basladi", {"x": 1})
    assert len(db.akislari_getir("test_akis")) >= 1

    db.ayar_kaydet("test_anahtar", {"liste": [1, 2, 3]})
    assert db.ayar_oku("test_anahtar")["liste"] == [1, 2, 3]

    db.ajan_kaydet("Test Ajanı", rol="denetim")
    assert len(db.ajanlari_getir()) >= 1

    # 2) Kuyruk: FIFO + öncelik + atomik çekme
    for i in range(5):
        db.kuyruga_ekle("test_kuyruk", {"sira": i}, oncelik=5)
    db.kuyruga_ekle("test_kuyruk", {"sira": "acil"}, oncelik=1)
    ilk = db.kuyruktan_cek("test_kuyruk")
    assert ilk["payload"]["sira"] == "acil", "Öncelikli iş önce gelmeli"
    ikinci = db.kuyruktan_cek("test_kuyruk")
    assert ikinci["payload"]["sira"] == 0, "FIFO sırası bozulmamalı"

    # 3) EŞZAMANLILIK: 8 thread x 250 yazma = 2000 log; hiçbiri kaybolmamalı
    KALIP = 250
    THREAD_SAYISI = 8

    def _yazar(isci_no: int) -> None:
        for i in range(KALIP):
            db.log_yaz("info", "es_zamanlilik_testi",
                       f"thread-{isci_no} kayit-{i}", {"isci": isci_no, "i": i})

    basla = time.time()
    ipler = [threading.Thread(target=_yazar, args=(n,)) for n in range(THREAD_SAYISI)]
    for t in ipler:
        t.start()
    for t in ipler:
        t.join()
    sure = time.time() - basla

    yazilan = db.log_sayisi("es_zamanlilik_testi")
    print(f"  8 thread eşzamanlı → {yazilan} log kaydı / {sure:.2f} sn")
    assert yazilan == THREAD_SAYISI * KALIP, \
        f"Kayıp var! {THREAD_SAYISI * KALIP} bekleniyordu, {yazilan} yazıldı"

    # 4) Eşzamanlı kuyruk tüketimi: iki thread aynı işi asla iki kez alamaz
    for i in range(100):
        db.kuyruga_ekle("test_tuketim", {"is": i})
    alinan: List[int] = []
    kilit = threading.Lock()

    def _tukeci() -> None:
        while True:
            is_ = db.kuyruktan_cek("test_tuketim")
            if is_ is None:
                return
            with kilit:
                alinan.append(is_["payload"]["is"])

    t1 = threading.Thread(target=_tukeci)
    t2 = threading.Thread(target=_tukeci)
    t1.start(); t2.start(); t1.join(); t2.join()
    print(f"  2 tüketici thread → {len(alinan)} iş alındı (100 olmalı, tekrarsız)")
    assert sorted(alinan) == list(range(100)), "Kuyrukta çift-alım veya kayıp var!"

    # 5) Aynı anda çekişen iş parçacıklarından modül durumu güncelleme
    def _durumcu() -> None:
        for _ in range(100):
            db.modul_durumu_kaydet("es_zamanlilik_modul", "calisiyor", {"ts": _simdi()})

    d1 = threading.Thread(target=_durumcu)
    d2 = threading.Thread(target=_durumcu)
    d1.start(); d2.start(); d1.join(); d2.join()
    assert db.modul_durumu_getir("es_zamanlilik_modul")["durum"] == "calisiyor"

    print()
    print("[OK] Tüm eşzamanlılık testleri geçti — kayıp/çakışma yok.")
    print()
    rapor = db.durum_raporu()
    print(f"Veritabanı : {rapor['veritabani']}")
    print(f"Boyut      : {rapor['boyut_mb']} MB | Mod: {rapor['journal_mode']}")
    print(f"Toplam     : {rapor['toplam_kayit']} kayıt")
    for ad, adet in sorted(rapor["tablolar"].items()):
        print(f"  - {ad:<22} {adet:>7} satır")
    db.kapat()
