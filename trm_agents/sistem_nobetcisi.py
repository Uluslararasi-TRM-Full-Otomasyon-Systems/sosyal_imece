#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sistem Nöbetçisi ve Ototonarım Ajanı (Ajan 175)
Versiyon: 2.0.0 (Güvenlik ve Şeffaflık Entegreli Sürüm)
"""

import os
import glob
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Path handling for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trm_agents.base_agent_template import BaseAgent
from trm_agents.system_protocols import CEO_TITLE


class SistemNobetcisiAjani(BaseAgent):
    def __init__(self, agent_id: Optional[int] = None, hedef_klasor: str = "."):
        super().__init__(
            agent_name="Sistem Nöbetçisi ve Ototonarım Ajanı",
            agent_id=agent_id if agent_id else 175
        )
        self.hedef_klasor = hedef_klasor
        self.saglik_raporu_dosyasi = "sistem_saglik_durumu.json"
        
        # Yeni ajan entegrasyonları
        self.siber_kalkan_ajani = None
        self.seffaflik_ajani = None
        
        try:
            from trm_agents.siber_kalkan_ajani import SiberKalkanVeTehditAvcisi
            self.siber_kalkan_ajani = SiberKalkanVeTehditAvcisi(agent_id=180)
            self.log(f"🛡️ Siber Kalkan ve Tehdit Avcısı (Ajan 180) entegre edildi", "INFO")
        except Exception as e:
            self.log(f"⚠️ Siber Kalkan Ajanı entegrasyonu başarısız: {e}", "WARNING")
        
        try:
            from trm_agents.seffaflik_ve_denetim_ajani import SeffaflikVeDenetimAjani
            self.seffaflik_ajani = SeffaflikVeDenetimAjani(agent_id=181)
            self.log(f"📊 Şeffaflık ve Denetim Ajanı (Ajan 181) entegre edildi", "INFO")
        except Exception as e:
            self.log(f"⚠️ Şeffaflık Ajanı entegrasyonu başarısız: {e}", "WARNING")
        
        self.log(f"🛡️ Sistem Nöbetçisi (Ajan 175) devrede. Sayın {CEO_TITLE} için 7/24 akıllı tarama aktif.", "INFO")

    def tum_dosyalari_tara(self) -> Dict[str, Any]:
        self.log("🔍 Ekosistemdeki gerçek Python kaynak kodları taranıyor...", "INFO")
        
        python_dosyalari = glob.glob(os.path.join(self.hedef_klasor, "**/*.py"), recursive=True)
        bulunan_hatalar = []
        taranan_dosya_sayisi = 0

        # Sadece gerçek kod içeren klasör veya modülleri hedefleyelim (veya düz metin .py'leri eleyelim)
        metin_bazli_py_dosyalari = [
            "ACIL_SATIS_HAVUZU.py", "GUNLUK_KONTROL_LISTESI.py", 
                    "muhafiz_nobet_defteri.py", "PANEL_ACICI_REHBERI.py", "requirements.py",
            "SISTEM_ENVANTERI.py", "TAM_KOD_ANALIZI.py", "test.py", "TRM_SOHBET_GECMISI.py"
        ]

        for dosya in python_dosyalari:
            if "venv" in dosya or ".git" in dosya:
                continue
            
            dosya_adi = os.path.basename(dosya)
            if dosya_adi in metin_bazli_py_dosyalari:
                continue # Düz metin içeren dokümanları syntax taramasından hariç tut
            
            taranan_dosya_sayisi += 1
            try:
                with open(dosya, "r", encoding="utf-8") as f:
                    kod_icerik = f.read()
                
                compile(kod_icerik, dosya, 'exec')
                
            except SyntaxError as se:
                hata_detayi = f"Syntax Hatası [{dosya}]: Satır {se.lineno} - {se.text}"
                bulunan_hatalar.append(hata_detayi)
                self.log(f"❌ {hata_detayi}", "ERROR")
            except Exception as e:
                pass

        rapor = {
            "tarih": datetime.now().isoformat(),
            "taranan_dosya_sayisi": taranan_dosya_sayisi,
            "tespit_edilen_hata_sayisi": len(bulunan_hatalar),
            "hatalar": bulunan_hatalar,
            "durum": "Kritik Sorun Yok - Sistem Sağlıklı" if not bulunan_hatalar else "Dikkat: Hatalar Tespit Edildi"
        }

        try:
            with open(self.saglik_raporu_dosyasi, "w", encoding="utf-8") as f:
                json.dump(rapor, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"⚠️ Sağlık raporu kaydedilemedi: {e}", "WARNING")

        return rapor

    def kapsamli_sistem_izleme(self) -> Dict[str, Any]:
        """Kapsamlı sistem izleme: sağlık + güvenlik + şeffaflık"""
        self.log("🔍 Kapsamlı sistem izleme başlatılıyor...", "INFO")
        
        # Sistem sağlık taraması
        saglik_raporu = self.tum_dosyalari_tara()
        
        # Güvenlik izleme
        guvenlik_raporu = {"durum": "guvenlik_ajani_yok", "detaylar": {}}
        if self.siber_kalkan_ajani:
            try:
                guvenlik_raporu = self.siber_kalkan_ajani.run(operation="rapor")
                self.log(f"🛡️ Güvenlik raporu alındı: {guvenlik_raporu['toplam_hesap']} hesap izleniyor", "INFO")
            except Exception as e:
                self.log(f"⚠️ Güvenlik raporu alınamadı: {e}", "WARNING")
        
        # Şeffaflık izleme
        seffaflik_raporu = {"durum": "seffaflik_ajani_yok", "detaylar": {}}
        if self.seffaflik_ajani:
            try:
                seffaflik_raporu = self.seffaflik_ajani.run(operation="rapor")
                self.log(f"📊 Şeffaflık raporu alındı", "INFO")
            except Exception as e:
                self.log(f"⚠️ Şeffaflık raporu alınamadı: {e}", "WARNING")
        
        # Kapsamlı rapor
        kapsamli_rapor = {
            "izleme_tarihi": datetime.now().isoformat(),
            "izleyen": f"{self.agent_name} (ID: {self.agent_id})",
            "sistem_sagligi": saglik_raporu,
            "guvenlik_durumu": guvenlik_raporu,
            "seffaflik_durumu": seffaflik_raporu,
            "genel_durum": "SAGLIKLI"
        }
        
        # Genel durum belirleme
        if saglik_raporu["tespit_edilen_hata_sayisi"] > 0:
            kapsamli_rapor["genel_durum"] = "KRITIK_SORUN"
        elif guvenlik_raporu.get("izole_edilmis_hesap", 0) > 0:
            kapsamli_rapor["genel_durum"] = "GUVENLIK_UYARISI"
        
        # Raporu kaydet
        try:
            with open(self.saglik_raporu_dosyasi, "w", encoding="utf-8") as f:
                json.dump(kapsamli_rapor, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"⚠️ Kapsamlı rapor kaydedilemedi: {e}", "WARNING")
        
        return kapsamli_rapor
    
    def stop(self) -> Dict[str, Any]:
        self.is_running = False
        self.status = "stopped"
        return {"status": "stopped", "agent_id": self.agent_id}
    
    def restart(self) -> Dict[str, Any]:
        self.status = "ready"
        self.is_running = True
        return {"status": "restarted", "agent_id": self.agent_id}

    def run(self, operation: str = "tara", **kwargs) -> Dict[str, Any]:
        if operation == "tara":
            return self.tum_dosyalari_tara()
        elif operation == "kapsamli_izleme":
            return self.kapsamli_sistem_izleme()
        return {"hata": "Bilinmeyen işlem"}


if __name__ == "__main__":
    print("Sistem Nobetcisi Ajan Kapsamli Izleme Baslatiyor...")
    nobetci = SistemNobetcisiAjani(agent_id=175)
    sonuc = nobetci.kapsamli_sistem_izleme()
    
    print(f"\nSistem Sagligi:")
    print(f"  Taranan Dosya: {sonuc['sistem_sagligi']['taranan_dosya_sayisi']}")
    print(f"  Hata Durumu: {sonuc['sistem_sagligi']['durum']}")
    
    print(f"\nGuvenlik Durumu:")
    if sonuc['guvenlik_durumu'].get('durum') != 'guvenlik_ajani_yok':
        print(f"  Toplam Hesap: {sonuc['guvenlik_durumu']['toplam_hesap']}")
        print(f"  Aktif Hesap: {sonuc['guvenlik_durumu']['aktif_hesap']}")
        print(f"  Engellenen Tehdit: {sonuc['guvenlik_durumu']['engellenen_tehdit']}")
    else:
        print(f"  Guvenlik Ajan Aktif Degil")
    
    print(f"\nSeffaflik Durumu:")
    if sonuc['seffaflik_durumu'].get('ozet'):
        print(f"  Toplam Gelir: {sonuc['seffaflik_durumu']['ozet']['toplam_gelir']} TL")
        print(f"  Toplam Refah Kesintisi: {sonuc['seffaflik_durumu']['ozet']['toplam_imece_kesintisi']} TL")
    else:
        print(f"  Seffaflik Ajan Aktif Degil")
    
    print(f"\nGenel Durum: {sonuc['genel_durum']}")
    print(f"Rapor Dosyasi: {nobetci.saglik_raporu_dosyasi}")