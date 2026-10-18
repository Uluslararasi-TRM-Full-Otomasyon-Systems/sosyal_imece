# -*- coding: utf-8 -*-
"""
KaranlikVeriAjani — v2.0 GERÇEK İMPLEMENTASYON
------------------------------------------------
Eskisi: return "Karanlık veride boşluklar yakalandı."  ← sahte

Yenisi:
  1. Google Trends TR RSS  → günün gerçek trend kelimelerini çeker
  2. Hepsiburada arama     → o trend kelime için kaç ürün var, fiyat aralığı
  3. Trendyol arama        → aynı kelime için rakip ürün sayısı
  4. Fark analizi          → "az ürün + yüksek arama = pazar boşluğu" tespiti

Gereksinimler (requirements.txt'e ekle):
    requests>=2.31.0
    beautifulsoup4>=4.12.0
    feedparser>=6.0.0
    python-dotenv>=1.0.0
"""

import time
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [KaranlikVeri] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SABITLER
# ---------------------------------------------------------------------------
GOOGLE_TRENDS_RSS = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=TR&hl=tr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Trendyol ve Hepsiburada arama sayfaları
TRENDYOL_ARAMA = "https://www.trendyol.com/sr?q={kelime}&qt={kelime}&st={kelime}"
HEPSIBURADA_ARAMA = "https://www.hepsiburada.com/ara?q={kelime}"

# Pazar boşluğu eşiği: Trendyol'da bu sayıdan az ürün varsa "boşluk" say
BOSLUK_ESIGI = 200


class KaranlikVeriAjani:
    """
    Ajan 204 — Pazar Boşluğu Dedektifi
    Gerçek trend + gerçek rakip sayısı → gerçek fırsat skoru
    """

    def __init__(self, maksimum_trend: int = 5, istek_arasi_bekleme: float = 1.5):
        self.ajan_id = 204
        self.maksimum_trend = maksimum_trend          # kaç trend kelime analiz edilsin
        self.bekleme = istek_arasi_bekleme             # sunucuya nazik ol, spam yapma
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ------------------------------------------------------------------
    # 1. ADIM: Google Trends TR'den gerçek trend kelimeleri çek
    # ------------------------------------------------------------------
    def _trend_kelimelerini_cek(self) -> list[str]:
        """RSS feed'den günün TR trendlerini döndürür."""
        logger.info("Google Trends TR RSS çekiliyor...")
        try:
            feed = feedparser.parse(GOOGLE_TRENDS_RSS)
            kelimeler = [entry.title for entry in feed.entries[: self.maksimum_trend]]
            if not kelimeler:
                # RSS boş döndüyse (Google zaman zaman kısıtlar) yedek liste
                logger.warning("Trends RSS boş döndü, yedek liste kullanılıyor.")
                kelimeler = ["bluetooth kulaklık", "robot süpürge", "akıllı saat", "mini projeksiyon", "taşınabilir şarj"]
            logger.info(f"Trendler alındı: {kelimeler}")
            return kelimeler
        except Exception as e:
            logger.error(f"Trends RSS hatası: {e}")
            return ["bluetooth kulaklık", "robot süpürge", "akıllı saat"]

    # ------------------------------------------------------------------
    # 2. ADIM: Trendyol'da o kelime için ürün sayısını çek
    # ------------------------------------------------------------------
    def _trendyol_urun_sayisi(self, kelime: str) -> Optional[int]:
        url = TRENDYOL_ARAMA.format(kelime=requests.utils.quote(kelime))
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            # Trendyol "X ürün listeleniyor" metnini arar
            # Örnek: <div class="dscrptn">1.248 ürün</div>
            for selector in [
                "div.dscrptn",
                "div.totalCount",
                "span.product-count",
                "h2.product-list-heading",
            ]:
                element = soup.select_one(selector)
                if element:
                    metin = element.get_text(strip=True)
                    # Sayıyı çıkar: "1.248 ürün" → 1248
                    sayi_str = "".join(filter(str.isdigit, metin.replace(".", "").replace(",", "")))
                    if sayi_str:
                        return int(sayi_str)

            # Alternatif: listelenen ürün kartlarını say
            kartlar = soup.select("div.p-card-wrppr, div.product-item")
            if kartlar:
                return len(kartlar)  # sayfa başına yaklaşık sayı

            return None
        except requests.RequestException as e:
            logger.warning(f"Trendyol isteği başarısız ({kelime}): {e}")
            return None

    # ------------------------------------------------------------------
    # 3. ADIM: Hepsiburada'da aynı kelime için ürün sayısını çek
    # ------------------------------------------------------------------
    def _hepsiburada_urun_sayisi(self, kelime: str) -> Optional[int]:
        url = HEPSIBURADA_ARAMA.format(kelime=requests.utils.quote(kelime))
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            # Hepsiburada "X ürün bulundu" span'ı
            for selector in [
                "span.product-count",
                "div.totalResults",
                "strong.result-count",
                "span[data-bind*='totalCount']",
            ]:
                element = soup.select_one(selector)
                if element:
                    metin = element.get_text(strip=True)
                    sayi_str = "".join(filter(str.isdigit, metin.replace(".", "").replace(",", "")))
                    if sayi_str:
                        return int(sayi_str)

            kartlar = soup.select("li.productListContent-item, div.product-list-item")
            if kartlar:
                return len(kartlar)

            return None
        except requests.RequestException as e:
            logger.warning(f"Hepsiburada isteği başarısız ({kelime}): {e}")
            return None

    # ------------------------------------------------------------------
    # 4. ADIM: Pazar boşluğu skoru hesapla
    # ------------------------------------------------------------------
    def _bosluk_skoru_hesapla(
        self,
        trend_sirasi: int,
        trendyol_sayi: Optional[int],
        hepsi_sayi: Optional[int],
    ) -> dict:
        """
        Skor mantığı:
          - Trend sırası düşük (1 = en popüler) → yüksek talep
          - Platform ürün sayısı az → düşük arz
          - Talep yüksek + arz düşük = FIRSAT
        """
        toplam_arz = (trendyol_sayi or 0) + (hepsi_sayi or 0)

        if toplam_arz == 0:
            # Veri çekemedik, tarafsız
            skor = 50
            yorum = "⚠️ Ürün sayısı alınamadı, manuel doğrulama gerekli"
        elif toplam_arz < BOSLUK_ESIGI:
            skor = min(95, 100 - trend_sirasi * 5 + (BOSLUK_ESIGI - toplam_arz) // 4)
            yorum = "🟢 FIRSAT: Yüksek talep, düşük arz tespit edildi!"
        elif toplam_arz < BOSLUK_ESIGI * 5:
            skor = 50 - trend_sirasi * 3
            yorum = "🟡 ORTA: Rekabet var ama girilebilir"
        else:
            skor = max(10, 30 - trend_sirasi * 5)
            yorum = "🔴 DOYMUŞ: Yüksek rekabet, zor pazar"

        return {
            "skor": max(0, min(100, skor)),
            "yorum": yorum,
            "toplam_arz_tahmini": toplam_arz,
        }

    # ------------------------------------------------------------------
    # ANA METOD — Panel'in çağırdığı yer
    # ------------------------------------------------------------------
    def kesfet(self) -> str:
        """
        api_server_2.py ile uyumlu — string döndürür.
        Detaylı analiz için kesfet_detayli() kullan.
        """
        try:
            sonuclar = self.kesfet_detayli()
            if not sonuclar:
                return "⚠️ Trend verisi alınamadı, lütfen internet bağlantısını kontrol edin."

            # En iyi fırsatı öne çıkar
            en_iyi = max(sonuclar, key=lambda x: x["firsat_skoru"])
            return (
                f"🔍 {len(sonuclar)} trend analiz edildi. "
                f"En büyük fırsat: '{en_iyi['kelime']}' "
                f"(Fırsat Skoru: {en_iyi['firsat_skoru']}/100) — {en_iyi['yorum']}"
            )
        except Exception as e:
            logger.error(f"kesfet() hatası: {e}")
            return f"❌ Analiz sırasında hata: {e}"

    def kesfet_detayli(self) -> list[dict]:
        """Panel dışında kullanmak için tam veri döndürür."""
        trendler = self._trend_kelimelerini_cek()
        sonuclar = []

        for sira, kelime in enumerate(trendler, start=1):
            logger.info(f"[{sira}/{len(trendler)}] '{kelime}' analiz ediliyor...")

            ty_sayi = self._trendyol_urun_sayisi(kelime)
            time.sleep(self.bekleme)

            hb_sayi = self._hepsiburada_urun_sayisi(kelime)
            time.sleep(self.bekleme)

            analiz = self._bosluk_skoru_hesapla(sira, ty_sayi, hb_sayi)

            sonuc = {
                "kelime": kelime,
                "trend_sirasi": sira,
                "trendyol_urun_sayisi": ty_sayi,
                "hepsiburada_urun_sayisi": hb_sayi,
                "firsat_skoru": analiz["skor"],
                "yorum": analiz["yorum"],
                "toplam_arz_tahmini": analiz["toplam_arz_tahmini"],
                "analiz_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            sonuclar.append(sonuc)
            logger.info(f"  → Skor: {analiz['skor']}/100 | {analiz['yorum']}")

        # Fırsat skoruna göre sırala (en iyisi üste)
        return sorted(sonuclar, key=lambda x: x["firsat_skoru"], reverse=True)


# ---------------------------------------------------------------------------
# Bağımsız test: python karanlik_veri_ajani.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ajan = KaranlikVeriAjani(maksimum_trend=3)

    print("\n" + "=" * 60)
    print("  KARANLIK VERİ AJANI — CANLI TEST")
    print("=" * 60)

    sonuclar = ajan.kesfet_detayli()
    for s in sonuclar:
        print(f"\n📌 Kelime       : {s['kelime']}")
        print(f"   Trend Sırası : #{s['trend_sirasi']}")
        print(f"   Trendyol     : {s['trendyol_urun_sayisi']} ürün")
        print(f"   Hepsiburada  : {s['hepsiburada_urun_sayisi']} ürün")
        print(f"   Fırsat Skoru : {s['firsat_skoru']}/100")
        print(f"   Yorum        : {s['yorum']}")
        print(f"   Zaman        : {s['analiz_zamani']}")

    print("\n" + "-" * 60)
    print("Panel özeti:", ajan.kesfet())
    print("=" * 60)
