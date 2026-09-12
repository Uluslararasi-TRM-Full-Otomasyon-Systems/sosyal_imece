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
    "system_name": "SOSYAL İMECE",
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
