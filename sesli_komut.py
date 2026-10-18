import os
import json
from datetime import datetime

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

def sesli_rapor_seslendir(metin: str, dosya_adi: str = "trm_asistan_yanit.mp3"):
    """
    TRM otonom raporlarını ve 55+ zenginlik dağılım özetlerini sesli dosyaya çevirir.
    """
    kayit_bilgi = {
        "timestamp": datetime.now().isoformat(),
        "metin": metin,
        "tts_motoru": "gTTS" if GTTS_AVAILABLE else "text_fallback",
        "dosya": dosya_adi
    }

    if GTTS_AVAILABLE:
        tts = gTTS(text=metin, lang='tr', slow=False)
        tts.save(dosya_adi)
        print(f"🔊 Sesli asistan yanıtı üretildi: {dosya_adi}")
    else:
        print("⚠️ gTTS kütüphanesi yüklü değil, metin tabanlı ses simülasyonu aktif.")

    log_dosyasi = "sesli_asistan_loglari.json"
    history = []
    try:
        with open(log_dosyasi, "r", encoding="utf-8") as f:
            history = json.load(f)
    except FileNotFoundError:
        pass
    history.append(kayit_bilgi)
    with open(log_dosyasi, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return kayit_bilgi

if __name__ == "__main__":
    test_metin = "Fahri abi, TRM TRM Ticari Ekosistem 55+ zenginlik payı ve afiliyet sepet eşleşmesi başarıyla tamamlandı. Kuşadası bölge varlık çarpanı 1.226 onaylandı."
    res = sesli_rapor_seslendir(test_metin)
    print(json.dumps(res, ensure_ascii=False, indent=2))
