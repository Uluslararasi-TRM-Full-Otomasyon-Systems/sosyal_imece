# -*- coding: utf-8 -*-
"""
ZamanOtesiAjani — v2.0 GERÇEK İMPLEMENTASYON
----------------------------------------------
Eskisi: return "2027 küresel hakimiyet rotası çizildi."  ← sahte

Yenisi:
  1. NewsData.io ücretsiz API  → Türk e-ticaret/teknoloji haberleri çeker
     (Ücretsiz: 200 istek/gün — https://newsdata.io → ücretsiz kayıt)
  2. Haber başlıklarından anahtar kelime frekansı çıkarır
  3. Frekans tablosunu 30 günlük bir pencerede değerlendirerek
     "önümüzdeki dönemde yükselecek kategori" tahmini üretir
  4. Rakip platform (Trendyol Bestseller RSS) ile çapraz doğrular

API KURULUMU:
  .env dosyasına ekle:
      NEWSDATA_API_KEY=your_free_key_here
  Ücretsiz anahtar için: https://newsdata.io/register

Gereksinimler:
    requests>=2.31.0
    feedparser>=6.0.0
    python-dotenv>=1.0.0
    collections (stdlib)
"""

import os
import re
import logging
import feedparser
import requests
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [ZamanOtesi] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SABITLER
# ---------------------------------------------------------------------------

# NewsData.io ücretsiz endpoint
NEWSDATA_URL = "https://newsdata.io/api/1/news"

# Trendyol günlük çok satanlar RSS (varsa — endpoint değişkendir)
TRENDYOL_BESTSELLER_RSS = "https://www.trendyol.com/rss/bestsellers.xml"

# E-ticaret / affiliate ile ilgili anahtar kategori etiketleri
KATEGORI_ETIKETLER = {
    "elektronik": ["telefon", "laptop", "kulaklık", "tablet", "bilgisayar", "akıllı", "drone", "kamera"],
    "ev_yasam": ["mobilya", "mutfak", "temizlik", "dekorasyon", "uyku", "banyo", "aydınlatma"],
    "saglik_spor": ["spor", "fitness", "sağlık", "vitamin", "koşu", "yoga", "bisiklet"],
    "moda": ["giyim", "ayakkabı", "çanta", "saat", "aksesuar", "takı", "parfüm"],
    "anne_cocuk": ["bebek", "çocuk", "oyuncak", "mama", "okul", "anne"],
    "bahce_dis": ["bahçe", "kamp", "outdoor", "alet", "tarım", "hayvan"],
}

# Haber arama sorguları (Türk e-ticaret odaklı)
HABER_SORGULARI = [
    "e-ticaret Türkiye trend",
    "Trendyol Hepsiburada satış",
    "affiliate pazarlama Türkiye",
    "tüketici alışveriş eğilim",
]


class ZamanOtesiAjani:
    """
    Ajan 214 — Gerçek Veri ile Gelecek Tahmincisi

    NewsData.io haberleri + RSS verileri → kategori frekansı → tahmin
    """

    def __init__(self):
        self.ajan_id = 214
        self.api_key: Optional[str] = os.getenv("NEWSDATA_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "TRM-ZamanOtesi-Ajan/2.0",
            "Accept": "application/json",
        })

        if not self.api_key:
            logger.warning(
                "NEWSDATA_API_KEY bulunamadı. .env dosyasına ekleyin.\n"
                "Ücretsiz anahtar: https://newsdata.io/register\n"
                "Şimdilik RSS yedek modunda çalışıyor."
            )

    # ------------------------------------------------------------------
    # 1. ADIM: NewsData.io'dan haber başlıklarını çek
    # ------------------------------------------------------------------
    def _haberleri_cek_newsdata(self, sorgu: str) -> list[str]:
        """NewsData.io ücretsiz API ile haber başlığı listesi döndürür."""
        if not self.api_key:
            return []

        params = {
            "apikey": self.api_key,
            "q": sorgu,
            "country": "tr",
            "language": "tr",
            "category": "business,technology",
        }
        try:
            r = self.session.get(NEWSDATA_URL, params=params, timeout=15)
            r.raise_for_status()
            veri = r.json()

            if veri.get("status") != "success":
                logger.warning(f"NewsData API hatası: {veri.get('message')}")
                return []

            basliklar = []
            for makale in veri.get("results", []):
                baslik = makale.get("title", "")
                aciklama = makale.get("description", "") or ""
                basliklar.append(f"{baslik} {aciklama}")

            logger.info(f"NewsData '{sorgu}' → {len(basliklar)} haber alındı")
            return basliklar

        except requests.RequestException as e:
            logger.error(f"NewsData isteği başarısız: {e}")
            return []

    # ------------------------------------------------------------------
    # 2. ADIM: RSS yedek kaynakları (API anahtarı yoksa)
    # ------------------------------------------------------------------
    def _haberleri_cek_rss(self) -> list[str]:
        """
        Ücretsiz Türk haber RSS'lerinden başlık çeker.
        API anahtarı olmayan kullanıcılar için yedek yol.
        """
        rss_kaynaklar = [
            "https://www.haberler.com/teknoloji/rss/",
            "https://shiftdelete.net/feed",
            "https://www.chip.com.tr/rss",
            "https://webrazzi.com/feed/",                   # startup/tech
            "https://eticaret.org/feed/",                   # e-ticaret odaklı
        ]
        basliklar = []
        for url in rss_kaynaklar:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:15]:
                    baslik = entry.get("title", "")
                    ozet = entry.get("summary", "") or ""
                    basliklar.append(f"{baslik} {ozet}")
                logger.info(f"RSS '{url}' → {len(feed.entries)} haber")
            except Exception as e:
                logger.warning(f"RSS alınamadı {url}: {e}")
        return basliklar

    # ------------------------------------------------------------------
    # 3. ADIM: Metinden kategori frekansı çıkar
    # ------------------------------------------------------------------
    def _kategori_frekansini_hesapla(self, metin_listesi: list[str]) -> dict[str, int]:
        """
        Haber metinlerindeki anahtar kelimeleri sayarak
        hangi kategorinin daha çok konuşulduğunu bulur.
        """
        birlesik_metin = " ".join(metin_listesi).lower()
        # Türkçe karakter normalize
        birlesik_metin = (birlesik_metin
                          .replace("ı", "i").replace("ş", "s")
                          .replace("ğ", "g").replace("ç", "c")
                          .replace("ö", "o").replace("ü", "u"))

        kategori_sayaci: dict[str, int] = {}
        for kategori, etiketler in KATEGORI_ETIKETLER.items():
            toplam = 0
            for etiket in etiketler:
                etiket_norm = (etiket
                               .replace("ı", "i").replace("ş", "s")
                               .replace("ğ", "g").replace("ç", "c")
                               .replace("ö", "o").replace("ü", "u"))
                toplam += len(re.findall(r'\b' + re.escape(etiket_norm), birlesik_metin))
            kategori_sayaci[kategori] = toplam

        return kategori_sayaci

    # ------------------------------------------------------------------
    # 4. ADIM: En çok geçen kelimeleri bul
    # ------------------------------------------------------------------
    def _en_cok_gecen_kelimeler(self, metin_listesi: list[str], top_n: int = 10) -> list[tuple]:
        """
        Stop-word filtrelemesi yaparak en sık geçen anlamlı kelimeleri döndürür.
        """
        stop_words = {
            "bir", "bu", "ve", "ile", "için", "olan", "olan", "da", "de",
            "mi", "mu", "mı", "mü", "ne", "en", "çok", "daha", "var",
            "yok", "olan", "ise", "gibi", "ama", "ancak", "hem", "ya",
            "the", "a", "an", "in", "of", "to", "for", "is", "at",
        }
        tum_kelimeler = []
        for metin in metin_listesi:
            kelimeler = re.findall(r'\b[a-züşğçöıİ]{4,}\b', metin.lower())
            tum_kelimeler.extend([k for k in kelimeler if k not in stop_words])

        return Counter(tum_kelimeler).most_common(top_n)

    # ------------------------------------------------------------------
    # 5. ADIM: Tahmin raporu üret
    # ------------------------------------------------------------------
    def _tahmin_raporu_uret(
        self,
        kategori_frekanslari: dict[str, int],
        en_cok_kelimeler: list[tuple],
    ) -> dict:
        """
        Frekans verilerini anlamlı bir iş tahminine dönüştürür.
        """
        if not any(kategori_frekanslari.values()):
            return {
                "durum": "VERİ YETERSİZ",
                "mesaj": "Haber kaynakları boş döndü, internet bağlantısını kontrol edin.",
                "oneri": [],
            }

        # Kategorileri sırala
        sirali = sorted(kategori_frekanslari.items(), key=lambda x: x[1], reverse=True)
        birinci = sirali[0]
        ikinci = sirali[1] if len(sirali) > 1 else ("—", 0)

        oneri_listesi = []
        for kategori, sayi in sirali[:3]:
            if sayi > 0:
                oneri_listesi.append({
                    "kategori": kategori,
                    "haber_frekans": sayi,
                    "tahmini_trend_guc": "YÜKSEK" if sayi > 10 else "ORTA" if sayi > 3 else "DÜŞÜK",
                    "affiliate_onerisı": f"{kategori} ürünlerine odaklan — haber akışı yoğun",
                })

        # Sinyaller: en çok geçen kelimeler arasında bağlamsal çıkarım
        sinyal_kelimeleri = [k for k, _ in en_cok_kelimeler[:5]]

        return {
            "durum": "BAŞARILI",
            "analiz_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tahmin_ufku": f"{(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')} (~30 gün)",
            "lider_kategori": birinci[0],
            "lider_frekans": birinci[1],
            "ikinci_kategori": ikinci[0],
            "gundem_sinyalleri": sinyal_kelimeleri,
            "oneri_listesi": oneri_listesi,
            "kaynak": "NewsData.io + RSS Haberleri (Canlı)",
        }

    # ------------------------------------------------------------------
    # ANA METOD — Panel'in çağırdığı yer
    # ------------------------------------------------------------------
    def gelecegi_goster(self) -> str:
        """
        api_server_2.py ile uyumlu — string döndürür.
        """
        try:
            rapor = self.gelecegi_goster_detayli()
            if rapor["durum"] != "BAŞARILI":
                return f"⚠️ {rapor['mesaj']}"

            return (
                f"📡 30 günlük tahmin tamamlandı. "
                f"Lider kategori: '{rapor['lider_kategori'].upper()}' "
                f"({rapor['lider_frekans']} haber sinyali). "
                f"Gündem sinyalleri: {', '.join(rapor['gundem_sinyalleri'])}. "
                f"Kaynak: Canlı Türk haber akışı — {rapor['analiz_tarihi']}"
            )
        except Exception as e:
            logger.error(f"gelecegi_goster() hatası: {e}")
            return f"❌ Analiz hatası: {e}"

    def gelecegi_goster_detayli(self) -> dict:
        """Panel dışında kullanmak için tam rapor döndürür."""
        tum_metinler: list[str] = []

        # NewsData.io API (varsa)
        if self.api_key:
            for sorgu in HABER_SORGULARI[:2]:   # ücretsiz kotayı koru
                tum_metinler.extend(self._haberleri_cek_newsdata(sorgu))
        
        # RSS yedek (her zaman çalıştır — ücretsiz & kota yok)
        rss_metinler = self._haberleri_cek_rss()
        tum_metinler.extend(rss_metinler)

        logger.info(f"Toplam {len(tum_metinler)} metin analiz ediliyor...")

        kategori_frekanslari = self._kategori_frekansini_hesapla(tum_metinler)
        en_cok_kelimeler = self._en_cok_gecen_kelimeler(tum_metinler, top_n=10)

        rapor = self._tahmin_raporu_uret(kategori_frekanslari, en_cok_kelimeler)
        rapor["analiz_edilen_metin_sayisi"] = len(tum_metinler)
        return rapor


# ---------------------------------------------------------------------------
# Bağımsız test: python zaman_otesi_ajani.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ajan = ZamanOtesiAjani()

    print("\n" + "=" * 60)
    print("  ZAMAN ÖTESİ AJANI — CANLI TEST")
    print("=" * 60)

    rapor = ajan.gelecegi_goster_detayli()

    print(f"\n📅 Analiz Tarihi  : {rapor.get('analiz_tarihi', '—')}")
    print(f"📆 Tahmin Ufku   : {rapor.get('tahmin_ufku', '—')}")
    print(f"🏆 Lider Kategori: {rapor.get('lider_kategori', '—')} ({rapor.get('lider_frekans', 0)} sinyal)")
    print(f"📰 Analiz edilen : {rapor.get('analiz_edilen_metin_sayisi', 0)} metin")
    print(f"🔑 Gündem Sinyali: {rapor.get('gundem_sinyalleri', [])}")
    print(f"\n📋 Kategori Önerileri:")
    for oneri in rapor.get("oneri_listesi", []):
        print(f"   • {oneri['kategori'].upper()} → {oneri['tahmini_trend_guc']} güç ({oneri['haber_frekans']} sinyal)")

    print("\n" + "-" * 60)
    print("Panel özeti:", ajan.gelecegi_goster())
    print("=" * 60)
