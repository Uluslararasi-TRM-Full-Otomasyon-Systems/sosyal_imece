import os
import sys
import time
import schedule

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from product_scraperconfig import TARGET_URLS, SCRAPE_INTERVAL_HOURS, DROPBOX_TARGET_PATH, DROPBOX_ACCESS_TOKEN
from magazanolsun_scraper import MagazaNolSunScraper
from dropbox_uploader import DropboxUploader

def scrape_and_upload():
    print(f"🕒 {time.strftime('%Y-%m-%d %H:%M:%S')} - Tarama başlıyor...")
    
    scraper = MagazaNolSunScraper()
    uploader = DropboxUploader(DROPBOX_ACCESS_TOKEN)
    
    for url in TARGET_URLS:
        try:
            products = scraper.get_products(url)
            for product in products:
                trm_json = scraper.to_json(product)
                uploader.upload_product(trm_json, DROPBOX_TARGET_PATH)
            print(f"✅ {len(products)} ürün işlendi: {url}")
        except Exception as e:
            print(f"❌ Hata: {url} - {str(e)}")

# Zamanlayıcı
schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(scrape_and_upload)

if __name__ == "__main__":
    print("🚀 TRM Ürün Toplayıcı Bot Başladı")
    scrape_and_upload()  # Hemen bir kez çalıştır
    
    while True:
        schedule.run_pending()
        time.sleep(60)
