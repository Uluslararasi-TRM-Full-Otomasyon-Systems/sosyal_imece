# -*- coding: utf-8 -*-
"""
config.py
MASTER_CONTROLLER.py ve diğer modüllerin ihtiyaç duyduğu sabitleri
global_config.json dosyasından okuyup dışa açan köprü modül.

ÖNEMLİ: Bu dosya bir Python MODÜLÜDÜR (import config), global_config.json
ise bir VERİ dosyasıdır. İkisi farklı şeylerdir; bu modül aradaki köprüdür.

GÜVENLİK: JSON okuma hatalarında sistem çökmesini engellemek için
kapsamlı hata yakalama ve güvenli varsayılan konfigürasyon döndürülür.
"""

import os
import json
import logging
import sys

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dosya yolunu mutlak olarak resolve et
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_BASE_DIR, "global_config.json")

# Güvenli varsayılan konfigürasyon
DEFAULT_CONFIG = {
    "system_name": "TRM TICARI",
    "version": "3.0.0",
    "max_agents": 165,
    "social_media": {
        "default_video": "content/videos/default_video.mp4",
        "default_language": "tr",
        "platforms": ["YouTube_Shorts", "TikTok", "Instagram_Reels"],
        "upload_interval": 300,
        "max_retries": 3,
        "auto_upload": True
    },
    "api_keys": {
        "youtube_api_key": "",
        "tiktok_api_key": "",
        "instagram_access_token": "",
        "twitter_api_key": "",
        "twitter_api_secret": "",
        "gemini_api_key": ""
    },
    "logging": {
        "level": "INFO",
        "file": "logs/system.log"
    },
    "sistem": {
        "max_ajan_sayisi": 165,
        "log_klasoru": "./logs",
        "rapor_klasoru": "./reports"
    }
}


def _load_global_config():
    """global_config.json dosyasını okur. Hata durumunda güvenli varsayılan konfigürasyon döndürür.
    
    Hata Yakalama:
    - FileNotFoundError: Dosya bulunamazsa varsayılan konfigürasyon kullanılır
    - json.JSONDecodeError: JSON format hatası varsa varsayılan konfigürasyon kullanılır
    - PermissionError: Okuma izni yoksa varsayılan konfigürasyon kullanılır
    - OSError: Dosya okuma/yazma hataları için
    - ValueError: Boş veya geçersiz içerik için
    - Diğer hatalar: Beklenmedik hatalarda varsayılan konfigürasyon kullanılır
    
    Tüm hatalar loglanır ve Streamlit bağlamında varsa st.error ile kullanıcıya bildirilir.
    """
    try:
        # Dosya yolunun varlığını kontrol et
        if not os.path.exists(_CONFIG_PATH):
            logger.warning(f"Config dosyası bulunamadı: {_CONFIG_PATH}. Varsayılan konfigürasyon kullanılıyor.")
            _try_show_error(f"⚠️ Config dosyası bulunamadı: {_CONFIG_PATH}\nVarsayılan konfigürasyon kullanılıyor.")
            return DEFAULT_CONFIG.copy()
        
        # Dosya boyutunu kontrol et (boş dosya kontrolü)
        if os.path.getsize(_CONFIG_PATH) == 0:
            logger.warning(f"Config dosyası boş: {_CONFIG_PATH}. Varsayılan konfigürasyon kullanılıyor.")
            _try_show_error(f"⚠️ Config dosyası boş: {_CONFIG_PATH}\nVarsayılan konfigürasyon kullanılıyor.")
            return DEFAULT_CONFIG.copy()
        
        # Dosyayı oku ve JSON'u parse et
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"Config dosyası sadece boşluk içeriyor: {_CONFIG_PATH}. Varsayılan konfigürasyon kullanılıyor.")
                _try_show_error(f"⚠️ Config dosyası sadece boşluk içeriyor: {_CONFIG_PATH}\nVarsayılan konfigürasyon kullanılıyor.")
                return DEFAULT_CONFIG.copy()
            config = json.loads(content)
        
        # Config'in geçerli bir sözlük olduğunu kontrol et
        if not isinstance(config, dict):
            logger.error(f"❌ Config dosyası geçerli bir JSON nesnesi değil: {_CONFIG_PATH}. Varsayılan konfigürasyon kullanılıyor.")
            _try_show_error(f"❌ Config dosyası geçerli bir JSON nesnesi değil: {_CONFIG_PATH}\nVarsayılan konfigürasyon kullanılıyor.")
            return DEFAULT_CONFIG.copy()
        
        logger.info(f"✅ Config dosyası başarıyla yüklendi: {_CONFIG_PATH}")
        return config
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON format hatası in {_CONFIG_PATH} (satır {e.lineno}, sütun {e.colno}): {e.msg}\nVarsayılan konfigürasyon kullanılıyor.")
        _try_show_error(f"❌ JSON format hatası in {_CONFIG_PATH} (satır {e.lineno}, sütun {e.colno}): {e.msg}\nVarsayılan konfigürasyon kullanılıyor.")
        return DEFAULT_CONFIG.copy()
        
    except PermissionError as e:
        logger.error(f"❌ Dosya okuma izni hatası {_CONFIG_PATH}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        _try_show_error(f"❌ Dosya okuma izni hatası {_CONFIG_PATH}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        return DEFAULT_CONFIG.copy()
        
    except OSError as e:
        logger.error(f"❌ Dosya sistemi hatası {_CONFIG_PATH}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        _try_show_error(f"❌ Dosya sistemi hatası {_CONFIG_PATH}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        return DEFAULT_CONFIG.copy()
        
    except ValueError as e:
        logger.error(f"❌ Geçersiz içerik hatası {_CONFIG_PATH}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        _try_show_error(f"❌ Geçersiz içerik hatası {_CONFIG_PATH}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        return DEFAULT_CONFIG.copy()
        
    except Exception as e:
        logger.error(f"❌ Beklenmedik hata config yüklenirken: {type(e).__name__}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        _try_show_error(f"❌ Beklenmedik hata config yüklenirken: {type(e).__name__}: {e}\nVarsayılan konfigürasyon kullanılıyor.")
        return DEFAULT_CONFIG.copy()


def _try_show_error(message):
    """Streamlit bağlamında varsa st.error ile hata mesajı gösterir."""
    try:
        import streamlit as st
        if hasattr(st, 'error'):
            st.error(message)
    except ImportError:
        # Streamlit yüklü değilse sessizce geç
        pass
    except Exception:
        # Streamlit bağlamı yoksa sessizce geç
        pass


# Config'i yükle
_cfg = _load_global_config()

# --- Dışa açılan sabitler -------------------------------------------------
_sistem = _cfg.get("sistem", {})

MAX_AJAN_SAYISI = _sistem.get("max_ajan_sayisi", 165)

LOG_DIR = _sistem.get("log_klasoru", "./logs")
REPORT_DIR = _sistem.get("rapor_klasoru", "./reports")

# Gerekli klasörlerin var olduğundan emin ol
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    logger.info(f"✅ Klasörler hazır: LOG_DIR={LOG_DIR}, REPORT_DIR={REPORT_DIR}")
except Exception as e:
    logger.error(f"❌ Klasör oluşturma hatası: {e}")
    LOG_DIR = "./logs"
    REPORT_DIR = "./reports"
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)


def _load_dotenv_if_present():
    """Load locally protected Windows settings; never read project .env files."""
    try:
        from trm_live_config import load_trm_environment

        source = load_trm_environment(_BASE_DIR)
        if source:
            logger.info("Protected local configuration loaded from %s", source)
    except Exception:
        logger.warning("Protected local configuration is unavailable; live integrations remain locked.")


_load_dotenv_if_present()


class SecureConfig:
    """LLM ve entegrasyon anahtarlarını ortam değişkeninden okuyan güvenli köprü."""

    def __init__(self):
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()

    def is_llm_configured(self) -> bool:
        return bool(self.openrouter_api_key or self.gemini_api_key or self.groq_api_key)

    def configured_llm_providers(self):
        names = []
        if self.groq_api_key:
            names.append("groq")
        if self.gemini_api_key:
            names.append("gemini")
        if self.openrouter_api_key:
            names.append("openrouter")
        return names


config = SecureConfig()


def get_social_media_config():
    """Sosyal medya yöneticisinin beklediği sözlük (değerler ortamdan)."""
    placeholder = {
        "messaging": "your_messaging_api_token_here",
        "facebook": "your_facebook_access_token_here",
        "instagram": "your_instagram_access_token_here",
        "twitter_key": "your_twitter_api_key_here",
        "twitter_secret": "your_twitter_api_secret_here",
    }
    return {
        "messaging": {
            "api_token": os.getenv("DISCORD_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or placeholder["messaging"],
            "phone_number": os.getenv("DISCORD_CHANNEL_ID") or os.getenv("TELEGRAM_CHAT_ID") or "",
        },
        "facebook": {
            "access_token": os.getenv("FACEBOOK_ACCESS_TOKEN") or placeholder["facebook"],
        },
        "instagram": {
            "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN") or placeholder["instagram"],
        },
        "twitter": {
            "api_key": os.getenv("TWITTER_API_KEY") or placeholder["twitter_key"],
            "api_secret": os.getenv("TWITTER_API_SECRET") or placeholder["twitter_secret"],
        },
    }


# product_scraper/main.py uyumluluğu
TARGET_URLS = [
    "https://magazanolsun.com/gida",
    "https://magazanolsun.com/kozmetik",
    "https://magazanolsun.com/kisisel-bakim",
]
SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
DROPBOX_TARGET_PATH = os.getenv(
    "DROPBOX_TARGET_PATH",
    "/Uluslararasi TRM Full Otomasyon Ürünler Deposu/01_MagazaNolSun",
)
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN", "")
