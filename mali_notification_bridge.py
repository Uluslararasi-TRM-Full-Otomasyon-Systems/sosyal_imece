import logging
import threading
import os
import tempfile

logger = logging.getLogger("MaliNotificationBridge")

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

def _speak_text(text: str):
    if not TTS_AVAILABLE:
        logger.info(f"[SESLİ ANONS (LOG)]: {text}")
        return
    try:
        tts = gTTS(text=text, lang='tr', slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_path = fp.name
        tts.save(temp_path)
        os.startfile(temp_path)
    except Exception as e:
        logger.warning(f"Ses sentez uyarısı (atlandı): {e}")

def async_broadcast_with_voice(distribution_result: dict):
    summary = distribution_result.get("summary", {})
    total_dist = summary.get("total_distributed", 0)
    users_count = summary.get("total_users", 0)
    announcement = f"TRM Ticari Ekosistem dağıtımı tamamlandı. {users_count} üyeye toplam {total_dist:,.2f} Türk Lirası tahsis edildi."
    
    logger.info(f"[BİLDİRİM] {announcement}")
    t = threading.Thread(target=_speak_text, args=(announcement,), daemon=True)
    t.start()
