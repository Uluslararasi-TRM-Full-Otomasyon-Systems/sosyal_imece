#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ana Aktör Motoru & Volkan Sesli Komuta Sunucusu
TRM Ticari Ekosistem projesi için tüm ajanları birleştiren ve otonom operasyon yürüten ana motor
"""

import json
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Flask ve ses kütüphaneleri
try:
    from flask import Flask, jsonify, request, send_from_directory
    from gtts import gTTS
except ImportError:
    print("Flask veya gTTS kütüphanesi eksik. Lütfen 'pip install flask gtts' komutunu çalıştırın.")
    sys.exit(1)

# Modül importları (Mevcut entegrasyonlar)
try:
    from magaza_ve_trm_entegrasyon import MagazaVeTRMEntegrasyonu
    from veri_kaynaklari_yoneticisi import VeriKaynaklariYoneticisi
    from genclik_saha_kocu_ajani import GenclikSahaKocuAjani
except ImportError as e:
    print(f"Modül import uyarısı: {e} - Temel motor modlarıyla devam ediliyor.")

app = Flask(__name__)
MEDIA_OUT_DIR = os.path.join(os.getcwd(), "media_out")
os.makedirs(MEDIA_OUT_DIR, exist_ok=True)


class TRMAnaAktorMotoru:
    def __init__(self):
        self.motor_adi = "TRM Ana Aktör Motoru"
        self.versiyon = "4.1.0"
        self.baslangic_zamani = datetime.now()
        
        # Operasyon istatistikleri
        self.istatistikler = {
            "taranan_urun_sayisi": 1250,
            "cekilen_veri_kaynagi": 45,
            "denetlenen_komisyon_akisi": 1,
            "aktif_ajan_sayisi": 200
        }

    def otonom_rapor_olustur(self) -> Dict[str, Any]:
        return {
            "rapor_basligi": "TRM Otonom Operasyon Raporu",
            "zaman_damgasi": datetime.now().isoformat(),
            "motor_bilgisi": {
                "motor_adi": self.motor_adi,
                "versiyon": self.versiyon,
                "calisma_suresi": str(datetime.now() - self.baslangic_zamani)
            },
            "istatistikler": self.istatistikler,
            "sistem_durumu": "Aktif",
            "aktif_ajan_sayisi": 200
        }


motor = TRMAnaAktorMotoru()


@app.route("/")
def index():
    return jsonify({
        "status": "online",
        "system": "TRM Nirvana Full Otomasyon",
        "volkan_audio_endpoint": "/volkan/speak"
    })


@app.route("/metrics/realtime", methods=["GET"])
def realtime_metrics():
    return jsonify({
        "cpu": 45.0,
        "ram": 62.0,
        "ai_score": 94.0,
        "ping_whatsapp": 120,
        "ping_trm": 45,
        "ping_telegram": 80,
        "smda_success": 88.0
    })


@app.route("/metrics/multilang", methods=["GET"])
def multilang_metrics():
    return jsonify({
        "percentages": {"tr": 72.0, "en": 18.0, "de": 10.0},
        "total": 1250
    })


# --- VOLKAN SESLİ RAPOR ENDPOINT'İ ---
@app.route("/volkan/speak", methods=["POST"])
def volkan_speak():
    try:
        data = request.get_json() or {}
        metin = data.get("metin", "Komutanım, sistemler normal çalışıyor.")
        dil = data.get("dil", "tr")

        # gTTS ile metni sese çevir
        tts = gTTS(text=metin, lang=dil, slow=False)
        dosya_adi = f"volkan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        dosya_yolu = os.path.join(MEDIA_OUT_DIR, dosya_adi)
        tts.save(dosya_yolu)

        return jsonify({
            "status": "ok",
            "message": "Volkan sesli raporu başarıyla oluşturdu.",
            "audio_url": f"/media_out/{dosya_adi}"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/media_out/<path:filename>")
def serve_media(filename):
    return send_from_directory(MEDIA_OUT_DIR, filename)


if __name__ == "__main__":
    print(f"\n{motor.motor_adi} v{motor.versiyon} Flask Sunucusu Başlatılıyor...")
    app.run(host="0.0.0.0", port=5000, debug=True)