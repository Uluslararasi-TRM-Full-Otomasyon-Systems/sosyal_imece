#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Otonom Ekosistemi - Web Scraper (Ana Veri Cekici) Modulu
"""

import logging
import requests
import json  # JSON dosyasına yazmak için eklendi
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
import random
import time

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TRMWebScraper:
    def __init__(self):
        self.base_url = "https://trendurunlermarket.com"
        self.headers_base = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        self.max_retries = 3

    def get_random_headers(self) -> Dict:
        return self.headers_base.copy()

    def urun_verisi_cek(self, urun_id: str) -> Optional[Dict]:
        """Proxy kullanmadan dogrudan baglanti ile urun verisini ceker"""
        hedef_url = f"{self.base_url}/urun/{urun_id}"
        logger.info(f"🚀 TRM Ajani istek baslatiyor: {hedef_url}")

        for attempt in range(self.max_retries):
            try:
                time.sleep(random.uniform(1, 2))
                response = requests.get(hedef_url, headers=self.get_random_headers(), timeout=20)
                
                if response.status_code == 200:
                    logger.info("🎯 Baglanti Basarili! Veri okunuyor.")
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    urun_detay = {
                        "urun_id": urun_id,
                        "title": soup.find("h1").text.strip() if soup.find("h1") else "TRM Trend Urun",
                        "price": "Otonom Belirlenecek",
                        "fetched_at": datetime.now().isoformat(),
                        "mask_status": "VERIFIED_DIRECT"
                    }
                    return urun_detay
                else:
                    logger.error(f"❌ Baglanti Hatasi! Kod: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Scraper calisirken hata: {str(e)}")
        return None

class LiveWebScraper:
    """Fetch public trend pages and convert findings to dispatch-queue JSON."""

    DEFAULT_SOURCES = [
        {
            "name": "Google Trends TR",
            "url": "https://trends.google.com/trending/rss?geo=TR",
        }
    ]

    def __init__(self, sources=None, timeout=15, session=None):
        self.sources = list(sources) if sources is not None else list(self.DEFAULT_SOURCES)
        self.timeout = timeout
        self.session = session or requests.Session()
        self.errors = []

    @staticmethod
    def _source_parts(source):
        if isinstance(source, str):
            return {"name": source, "url": source}
        if not isinstance(source, dict) or not source.get("url"):
            raise ValueError("Her kaynak bir URL veya url alanli sozluk olmalidir")
        return source

    @staticmethod
    def _text(element):
        return element.get_text(" ", strip=True) if element else ""

    def _parse_response(self, response, source):
        soup = BeautifulSoup(response.content, "html.parser")
        records = []
        feed_entries = soup.find_all(["item", "entry"])
        if feed_entries:
            for entry in feed_entries:
                title = self._text(entry.find("title"))
                link_element = entry.find("link")
                link = (link_element.get("href") or "") if link_element else ""
                if not link and link_element:
                    link = self._text(link_element)
                description = self._text(entry.find(["description", "summary"]))
                published = self._text(entry.find(["pubdate", "published", "updated"]))
                if title:
                    records.append({
                        "title": title,
                        "url": link,
                        "description": description,
                        "published_at": published,
                    })
            return records

        selectors = source.get("selectors", ["h1", "h2", "h3"])
        for selector in selectors:
            for element in soup.select(selector):
                title = self._text(element)
                if not title:
                    continue
                anchor = element if element.name == "a" else element.find("a")
                records.append({
                    "title": title,
                    "url": anchor.get("href", "") if anchor else "",
                    "description": "",
                    "published_at": "",
                })
        return records

    def fetch_trends(self):
        from hashlib import sha256

        self.errors = []
        trends = []
        seen = set()
        for raw_source in self.sources:
            try:
                source = self._source_parts(raw_source)
                response = self.session.get(
                    source["url"],
                    headers={"User-Agent": "TRM-LiveWebScraper/1.0"},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                for item in self._parse_response(response, source):
                    identity = item["url"] or item["title"]
                    trend_id = sha256(
                        f"{source['name']}|{identity}".encode("utf-8")
                    ).hexdigest()[:20]
                    if trend_id in seen:
                        continue
                    seen.add(trend_id)
                    trends.append({
                        "trend_id": trend_id,
                        "source": source["name"],
                        **item,
                        "observed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    })
            except (requests.RequestException, ValueError, KeyError) as exc:
                self.errors.append({
                    "source": str(raw_source),
                    "error": f"{exc.__class__.__name__}: {exc}",
                })
            except Exception as exc:
                logger.exception("Trend kaynagi okunamadi")
                self.errors.append({
                    "source": str(raw_source),
                    "error": f"{exc.__class__.__name__}: {exc}",
                })
        return trends

    @staticmethod
    def queue_items(trends):
        """Return dictionaries accepted by DispatchQueueManager.add_to_queue."""
        return [
            {
                "account_id": "trm_live_web_scraper",
                "post_id": f"trend-{trend['trend_id']}",
                "payload": {
                    "task_type": "trend_signal",
                    "status": "pending_review",
                    "trend": trend,
                },
            }
            for trend in trends
        ]

    def fetch_trends_json(self):
        return json.dumps(self.queue_items(self.fetch_trends()), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    scraper = TRMWebScraper()
    print("--- TRM WEB SCRAPER - GERCEK URUN TESTI ---")
    urun_id = "TKU1466744" 
    test_sonuc = scraper.urun_verisi_cek(urun_id)
    
    if test_sonuc:
        # Veriyi json dosyasına kaydet
        with open("trend_raporlari.json", "w", encoding="utf-8") as f:
            json.dump([test_sonuc], f, ensure_ascii=False, indent=4)
        print("✅ Veri trend_raporlari.json dosyasına yazıldı.")
    
    print(f"Test Sonucu: {test_sonuc}")