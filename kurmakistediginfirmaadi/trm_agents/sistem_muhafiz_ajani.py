# trm_agents/sistem_muhafiz_ajani.py
import os
import sys
import time
import subprocess
import requests

class SistemMuhafizAjani:
    def __init__(self):
        self.ajanin_adi = "162. Otonom Sistem Muhafızı ve Nöbetçi Uzmanı"
        self.panel_url = "http://localhost:8501"
        self.log_dosyasi = "muhafiz_nobet_defteri.txt"
        self.calisiyor_mu = True

    def nobet_defterine_yaz(self, mesaj):
        zaman = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_dosyasi, "a", encoding="utf-8") as f:
            f.write(f"[{zaman}] 🐾 {mesaj}\n")
        print(f"[{zaman}] Muhafız: {mesaj}")

    def paneli_kontrol_et(self):
        """Streamlit panelinin ayakta olup olmadığını kontrol eder, çöktüyse otonom ateşler."""
        try:
            response = requests.get(self.panel_url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            return False
        return False

    def sunucuyu_yeniden_atesle(self):
        self.nobet_defterine_yaz("⚠️ PANEL ÇÖKMÜŞ VEYA KAPANMIŞ! Otonom olarak yeniden ateşleniyor...")
        # Arka planda Streamlit'i tekrar ayağa kaldırır
        subprocess.Popen(["python", "api_server_2.py"], shell=True)
        self.nobet_defterine_yaz("🚀 Streamlit sunucusu CMD üzerinden başarıyla yeniden ayağa kaldırıldı.")

    def nobet_tut(self):
        self.nobet_defterine_yaz("🛡️ Muhafız göreve başladı. Mareşal Fahri Güzel'in sistemi bana emanettir.")
        while self.calisiyor_mu:
            if not self.paneli_kontrol_et():
                self.sunucuyu_yeniden_atesle()
            else:
                # Her şey yolundaysa sessizce nöbete devam eder
                pass
            time.sleep(30) # 30 saniyede bir devriye gezer

if __name__ == "__main__":
    muhafiz = SistemMuhafizAjani()
    muhafiz.nobet_tut()