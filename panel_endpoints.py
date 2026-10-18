import os
import time
import hashlib
import json
from datetime import datetime
from pathlib import Path

# İlgili diğer modüllerimizi içeri aktarıyoruz
try:
    from social_media_distribution_agent import run_social_agent
    from conversation_log import ConversationLog
except ImportError:
    # Fallback/Mock fonksiyonlar eğer dosyalar henüz yolda değilse
    def run_social_agent(loop=False, dry_run=True, **kwargs):
        return {"status": "mock_success", "message": "Ajan test modunda çalıştırıldı."}
    class ConversationLog:
        @staticmethod
        def get_last_minute_rate(): return 5
        @staticmethod
        def get_last_24h_grouped_by_language(): return {"tr": 80, "en": 15, "de": 5}
        @staticmethod
        def get_last_24h_hourly(): return [10, 12, 15, 20, 25, 30, 35, 40]

# gTTS opsiyonel — kurulu değilse /volkan/speak demo moda düşer
try:
    from gtts import gTTS
    _HAS_GTTS = True
except ImportError:
    _HAS_GTTS = False

MEDIA_OUT_DIR = Path(__file__).resolve().parent / "media_out"
MEDIA_OUT_DIR.mkdir(parents=True, exist_ok=True)

# "Volkan" için kullanılan ses profili — bkz. PanelEndpoints.speak_as_volkan
# DÜRÜST NOT: gTTS bir kişinin sesini KLONLAYAMAZ. Bu sadece Türkçe standart
# gTTS sesine "Volkan" etiketi verilmiş halidir, Volkan'ın gerçek sesi değildir.
# Gerçek ses klonlaması (örn. ElevenLabs, RVC, Coqui XTTS) ayrı bir servis,
# API anahtarı ve Volkan'ın kendi ses örnekleri gerektirir — bu proje
# kapsamında sağlanmadı.
VOLKAN_VOICE_LANG = "tr"


class PanelEndpoints:
    @staticmethod
    def handle_dashboard_stats():
        """Panelin ana sayfa istatistiklerini ve osiloskop verilerini döner."""
        return {
            "status": "success",
            "last_minute_rate": ConversationLog.get_last_minute_rate(),
            "languages": ConversationLog.get_last_24h_grouped_by_language(),
            "hourly_activity": ConversationLog.get_last_24h_hourly(),
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def trigger_social_agent_endpoint(payload=None):
        """Web panelinden veya API üzerinden sosyal medya ajanını tetikler.
        NOT: Kampanya sistemi sadeleştirildi; artık yalnızca ürün ve refah
        duyuruları desteklenir (bkz. social_media_distribution_agent.py)."""
        if payload is None:
            payload = {}

        dry_run = payload.get("dry_run", True)
        max_products = payload.get("max_products", 3)
        max_imece = payload.get("max_imece", 1)
        force_campaign = payload.get("force_campaign", None)  # artık kullanılmıyor, geriye dönük uyumluluk için kabul edilir

        try:
            result = run_social_agent(
                loop=False,
                dry_run=dry_run,
                max_products=max_products,
                max_imece=max_imece,
            )
            return {
                "status": "success",
                "message": "Sosyal medya ajanı başarıyla tetiklendi.",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ajan tetiklenirken hata oluştu: {str(e)}"
            }

    @staticmethod
    def speak_as_volkan(text, lang=VOLKAN_VOICE_LANG):
        """
        Verilen metni "Volkan" etiketli sesli bildirime çevirir.

        DÜRÜST NOT: Bu, gTTS'in standart Türkçe sesidir — Volkan'ın gerçek
        sesinin klonu DEĞİLDİR. gTTS teknik olarak belirli bir kişinin
        sesini klonlamaz, sadece dile göre genel bir sentetik ses üretir.
        Gerçek "Volkan'ın sesi" için ElevenLabs/Coqui XTTS gibi bir ses
        klonlama servisi + Volkan'ın ses örnekleri gerekir.
        """
        text = (text or "Sistem bildirimi.").strip()[:500]
        if not _HAS_GTTS:
            return {
                "status": "error",
                "demo": True,
                "message": "gTTS kurulu değil (pip install gTTS). Sesli bildirim üretilemedi.",
            }
        try:
            tag = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
            out_name = f"volkan_{int(time.time())}_{tag}.mp3"
            out_path = MEDIA_OUT_DIR / out_name
            gTTS(text=text, lang=lang, slow=False).save(str(out_path))
            return {
                "status": "success",
                "audio_file": out_name,
                "audio_url": f"/social/media/{out_name}",
                "text": text,
                "note": (
                    "Bu ses Volkan'ın gerçek sesi değildir; gTTS'in standart "
                    "Türkçe sesine 'Volkan' etiketi verilmiştir."
                ),
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
