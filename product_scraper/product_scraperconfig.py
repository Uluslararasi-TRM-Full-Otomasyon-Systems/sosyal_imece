import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from trm_live_config import load_trm_environment

load_trm_environment(PROJECT_ROOT)

# Dropbox
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_TARGET_PATH = "/Uluslararasi TRM Full Otomasyon Ürünler Deposu/01_MagazaNolSun"

# Hedef Siteler - Gıda, Kozmetik, Kişisel Bakım kategorileri
TARGET_URLS = [
    # Magazanolsun için
    "https://magazanolsun.com/gida",
    "https://magazanolsun.com/kozmetik",
    "https://magazanolsun.com/kisisel-bakim",
    "https://magazanolsun.com/best-sellers",
    "https://magazanolsun.com/trending",
    # Trendyol için örnek kategoriler
    "https://www.trendyol.com/gida-saglik-ve-ozel-bakim-x-c-143",
    "https://www.trendyol.com/kozmetik-x-c-109461",
    # N11 için örnek kategoriler
    "https://www.n11.com/gida-urunleri",
    "https://www.n11.com/kozmetik-ve-kisisel-bakim",
]

# Tarama Ayarları
SCRAPE_INTERVAL_HOURS = 6  # Her 6 saatte bir tara
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
