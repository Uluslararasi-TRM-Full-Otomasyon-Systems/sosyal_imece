# -*- coding: utf-8 -*-
"""
TRM Muhasebe ve Finans Yönetim Ajanı (Sponsorluk/Bağış Hariç Saf Ticari & Prim Yapısı)
"""
import os
import sys
import json
import logging
from datetime import datetime

# Ana dizini python path'ine ekleyelim
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from config import REPORT_DIR
except ImportError:
    REPORT_DIR = "./reports"

logger = logging.getLogger("TRMAccountingAgent")

class TRMAccountingAgent:
    def __init__(self):
        self.agent_name = "TRMAccountingAgent"
        self.version = "2.0.0"
        
    def run(self):
        print("\n[START] TRM Muhasebe ve Finans Yönetim Ajanı Aktif Hale Getirildi...")
        
        # Temel Finansal Veriler (Örnek / Canlı Simülasyon)
        brut_gelir = 50000.0
        kurumlar_vergisi_orani = 0.20
        vergi = brut_gelir * kurumlar_vergisi_orani
        net_kar = brut_gelir - vergi
        
        print(f"[M. Fahri Güzel Anonim Şirketi (Finans Motoru)] Brüt Gelir: {brut_gelir} TL")
        print(f"[M. Fahri Güzel Anonim Şirketi (Finans Motoru)] Hesaplanan Kurumlar Vergisi: {vergi} TL")
        print(f"[M. Fahri Güzel Anonim Şirketi (Finans Motoru)] Net Kâr: {net_kar} TL")
        
        # Güvenli Pazarlama Primi ve Gider Pusulası Listesi
        print("\n--- A.Ş. GÜVENLİ PAZARLAMA PRİMİ VE GİDER PUSULASI LİSTESİ (MALİYE UYUMLU) ---")
        prim_listesi = [
            {"isim": "Ahmet Yılmaz", "rol": "Fahri Üye/Ortak", "brut": 5000, "stopaj_orani": 0.10},
            {"isim": "Ayşe Demir", "rol": "Fahri Üye/Ortak", "brut": 7500, "stopaj_orani": 0.10}
        ]
        
        gider_pusulalari = []
        for p in prim_listesi:
            stopaj = p["brut"] * p["stopaj_orani"]
            bankaya_yatacak = p["brut"] - stopaj
            print(f"Hizmet Alan: {p['isim']} ({p['rol']}) | Brüt Primi: {p['brut']} TL | Stopaj: {stopaj} TL | Bankaya Yatacak: {bankaya_yatacak} TL")
            gider_pusulalari.append({
                "isim": p["isim"],
                "brut_prim": p["brut"],
                "stopaj": stopaj,
                "net_odenen": bankaya_yatacak
            })

        # Raporu kaydet
        os.makedirs(REPORT_DIR, exist_ok=True)
        rapor_yolu = os.path.join(REPORT_DIR, "mali_ve_prim_raporu.json")
        rapor_verisi = {
            "tarih": datetime.now().isoformat(),
            "brut_gelir": brut_gelir,
            "vergi": vergi,
            "net_kar": net_kar,
            "gider_pusulalari": gider_pusulalari
        }
        
        try:
            with open(rapor_yolu, "w", encoding="utf-8") as f:
                json.dump(rapor_verisi, f, ensure_ascii=False, indent=4)
            print(f"Mali rapor kaydedildi: {rapor_yolu}")
        except Exception as e:
            logger.error(f"Rapor kaydedilemedi: {e}")
            
        print("[END] TRM Muhasebe ve Finans Yönetim Ajanı Mali Raporlamayı Tamamladı.\n")

if __name__ == "__main__":
    agent = TRMAccountingAgent()
    agent.run()