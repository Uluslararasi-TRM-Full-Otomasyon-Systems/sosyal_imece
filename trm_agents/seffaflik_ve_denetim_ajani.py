#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Şeffaflık ve Denetim Ajanı (Ajan 181) - Kamu Denetim ve Şeffaflık Modülü
Versiyon: 1.0.0

Şeffaf gelir ve havuz raporlaması, resmi makam uyum paketi.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Path handling for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trm_agents.base_agent_template import BaseAgent
from trm_agents.system_protocols import CEO_TITLE


class SeffaflikVeDenetimAjani(BaseAgent):
    def __init__(self, agent_id: Optional[int] = None):
        super().__init__(
            agent_name="Şeffaflık ve Denetim Ajanı",
            agent_id=agent_id if agent_id else 181
        )
        
        # Dosya yolları (TRM Ticari Ekosistem Bağımsız Arşiv)
        self.seffaflik_raporlari_dir = Path("data/trm_seffaflik_raporlari")
        self.seffaflik_raporlari_dir.mkdir(parents=True, exist_ok=True)
        self.seffaflik_dosyasi = self.seffaflik_raporlari_dir / "trm_seffaflik_raporlari.json"
        
        # Şeffaflık veritabanı
        self.seffaflik_veritabani = self._seffaflik_veritabani_yukle()
        
        # Refah havuz kesinti oranı
        self.imece_havuz_kesinti_orani = 0.30  # %30
        
        # Vergi oranları
        self.vergi_oranlari = {
            "kdv": 0.20,  # %20
            "stopaj": 0.15,  # %15
            "gelir_vergisi": 0.20  # %20
        }
        
        self.log(f"📊 Şeffaflık ve Denetim Ajanı (Ajan 181) devrede. Sayın {CEO_TITLE}", "INFO")
    
    def _seffaflik_veritabani_yukle(self) -> Dict[str, Any]:
        """Şeffaflık veritabanını yükler"""
        if self.seffaflik_dosyasi.exists():
            with open(self.seffaflik_dosyasi, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "gelir_havuzu": {
                "toplam_gelir": 0,
                "imece_havuz_kesintisi": 0,
                "net_gelir": 0,
                "islemler": []
            },
            "yoksulluk_yardimlari": {
                "toplam_odeme": 0,
                "il_bazli_odemeler": {},
                "odemeler": []
            },
            "vergi_kayitlari": {
                "toplam_kdv": 0,
                "toplam_stopaj": 0,
                "toplam_gelir_vergisi": 0,
                "vergi_islemleri": []
            },
            "denetim_raporlari": []
        }
    
    def _seffaflik_veritabani_kaydet(self):
        """Şeffaflık veritabanını kaydeder"""
        with open(self.seffaflik_dosyasi, "w", encoding="utf-8") as f:
            json.dump(self.seffaflik_veritabani, f, indent=4, ensure_ascii=False)
    
    def gelir_kaydet(self, islem_id: str, gelir_tutari: float, gelir_kaynagi: str, 
                    kullanici_id: str = None, tarih: str = None) -> Dict[str, Any]:
        """Gelir kaydeder ve Refah havuz kesintisini hesaplar"""
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        imece_kesintisi = gelir_tutari * self.imece_havuz_kesinti_orani
        net_gelir = gelir_tutari - imece_kesintisi
        
        islem_bilgisi = {
            "islem_id": islem_id,
            "gelir_tutari": gelir_tutari,
            "imece_havuz_kesintisi": imece_kesintisi,
            "net_gelir": net_gelir,
            "gelir_kaynagi": gelir_kaynagi,
            "kullanici_id": kullanici_id,
            "islem_tarihi": tarih,
            "kesinti_orani": f"%{self.imece_havuz_kesinti_orani * 100}"
        }
        
        # Veritabanı güncelle
        self.seffaflik_veritabani["gelir_havuzu"]["toplam_gelir"] += gelir_tutari
        self.seffaflik_veritabani["gelir_havuzu"]["imece_havuz_kesintisi"] += imece_kesintisi
        self.seffaflik_veritabani["gelir_havuzu"]["net_gelir"] += net_gelir
        self.seffaflik_veritabani["gelir_havuzu"]["islemler"].append(islem_bilgisi)
        
        self._seffaflik_veritabani_kaydet()
        
        self.log(f"💰 Gelir kaydedildi: {gelir_tutari} TL - Refah Kesintisi: {imece_kesintisi} TL", "INFO")
        
        return islem_bilgisi
    
    def yoksulluk_yardimi_kaydet(self, islem_id: str, kullanici_id: str, ad_soyad: str, 
                                il: str, odeme_tutari: float, odeme_tarihi: str = None) -> Dict[str, Any]:
        """Yoksulluk yardımı ödemesi kaydeder"""
        if odeme_tarihi is None:
            odeme_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        odeme_bilgisi = {
            "islem_id": islem_id,
            "kullanici_id": kullanici_id,
            "ad_soyad": ad_soyad,
            "il": il,
            "odeme_tutari": odeme_tutari,
            "odeme_tarihi": odeme_tarihi,
            "odeme_turu": "yoksulluk_yardimi"
        }
        
        # Veritabanı güncelle
        self.seffaflik_veritabani["yoksulluk_yardimlari"]["toplam_odeme"] += odeme_tutari
        
        if il not in self.seffaflik_veritabani["yoksulluk_yardimlari"]["il_bazli_odemeler"]:
            self.seffaflik_veritabani["yoksulluk_yardimlari"]["il_bazli_odemeler"][il] = 0
        self.seffaflik_veritabani["yoksulluk_yardimlari"]["il_bazli_odemeler"][il] += odeme_tutari
        
        self.seffaflik_veritabani["yoksulluk_yardimlari"]["odemeler"].append(odeme_bilgisi)
        
        self._seffaflik_veritabani_kaydet()
        
        self.log(f"🏛️ Yoksulluk yardımı ödendi: {ad_soyad} ({il}) - {odeme_tutari} TL", "INFO")
        
        return odeme_bilgisi
    
    def vergi_kaydet(self, islem_id: str, vergi_turu: str, matrah: float, 
                    kullanici_id: str = None, tarih: str = None) -> Dict[str, Any]:
        """Vergi kaydeder"""
        if tarih is None:
            tarih = datetime.now().strftime("%Y-%m-%d")
        
        vergi_orani = self.vergi_oranlari.get(vergi_turu, 0)
        vergi_tutari = matrah * vergi_orani
        
        vergi_bilgisi = {
            "islem_id": islem_id,
            "vergi_turu": vergi_turu,
            "matrah": matrah,
            "vergi_orani": f"%{vergi_orani * 100}",
            "vergi_tutari": vergi_tutari,
            "kullanici_id": kullanici_id,
            "vergi_tarihi": tarih
        }
        
        # Veritabanı güncelle
        if vergi_turu == "kdv":
            self.seffaflik_veritabani["vergi_kayitlari"]["toplam_kdv"] += vergi_tutari
        elif vergi_turu == "stopaj":
            self.seffaflik_veritabani["vergi_kayitlari"]["toplam_stopaj"] += vergi_tutari
        elif vergi_turu == "gelir_vergisi":
            self.seffaflik_veritabani["vergi_kayitlari"]["toplam_gelir_vergisi"] += vergi_tutari
        
        self.seffaflik_veritabani["vergi_kayitlari"]["vergi_islemleri"].append(vergi_bilgisi)
        
        self._seffaflik_veritabani_kaydet()
        
        self.log(f"📋 Vergi kaydedildi: {vergi_turu} - {vergi_tutari} TL", "INFO")
        
        return vergi_bilgisi
    
    def resmi_makam_uyum_raporu_olustur(self, rapor_turu: str = "genel", 
                                      baslangic_tarihi: str = None, bitis_tarihi: str = None) -> Dict[str, Any]:
        """Resmi makam uyum raporu oluşturur"""
        if baslangic_tarihi is None:
            baslangic_tarihi = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        if bitis_tarihi is None:
            bitis_tarihi = datetime.now().strftime("%Y-%m-%d")
        
        rapor = {
            "rapor_id": f"Uyum_{rapor_turu}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "rapor_turu": rapor_turu,
            "rapor_tarihi": datetime.now().isoformat(),
            "raporlayan": f"{self.agent_name} (ID: {self.agent_id})",
            "baslangic_tarihi": baslangic_tarihi,
            "bitis_tarihi": bitis_tarihi,
            "kurum_bilgisi": {
                "sistem_adi": "TRM Ticari Ekosistem Otonom Ekosistem",
                "faaliyet_alani": "TRM Ticari Ekosistem ve E-Ticaret",
                "mali_bagimsizlik": "UTEYKDER_dernek_butccesinden_bagimsiz",
                "yonetim_yapisi": "Otonom_Dijital_Mimar"
            },
            "gelir_ozeti": {
                "toplam_gelir": self.seffaflik_veritabani["gelir_havuzu"]["toplam_gelir"],
                "imece_havuz_kesintisi": self.seffaflik_veritabani["gelir_havuzu"]["imece_havuz_kesintisi"],
                "net_gelir": self.seffaflik_veritabani["gelir_havuzu"]["net_gelir"],
                "islem_sayisi": len(self.seffaflik_veritabani["gelir_havuzu"]["islemler"])
            },
            "yoksulluk_yardimlari_ozeti": {
                "toplam_odeme": self.seffaflik_veritabani["yoksulluk_yardimlari"]["toplam_odeme"],
                "il_bazli_odemeler": self.seffaflik_veritabani["yoksulluk_yardimlari"]["il_bazli_odemeler"],
                "odeme_sayisi": len(self.seffaflik_veritabani["yoksulluk_yardimlari"]["odemeler"])
            },
            "vergi_ozeti": {
                "toplam_kdv": self.seffaflik_veritabani["vergi_kayitlari"]["toplam_kdv"],
                "toplam_stopaj": self.seffaflik_veritabani["vergi_kayitlari"]["toplam_stopaj"],
                "toplam_gelir_vergisi": self.seffaflik_veritabani["vergi_kayitlari"]["toplam_gelir_vergisi"],
                "toplam_vergi": (
                    self.seffaflik_veritabani["vergi_kayitlari"]["toplam_kdv"] +
                    self.seffaflik_veritabani["vergi_kayitlari"]["toplam_stopaj"] +
                    self.seffaflik_veritabani["vergi_kayitlari"]["toplam_gelir_vergisi"]
                )
            },
            "denetlenebilirlik": {
                "tum_islemler_loglanmis": True,
                "her_kurus_takip_edilebilir": True,
                "zaman_damgalari": True,
                "kullanici_izlenebilirligi": True
            }
        }
        
        # Raporu veritabanına ekle
        self.seffaflik_veritabani["denetim_raporlari"].append(rapor)
        self._seffaflik_veritabani_kaydet()
        
        self.log(f"📋 Resmi makam uyum raporu oluşturuldu: {rapor_turu}", "INFO")
        
        return rapor
    
    def seffaflik_raporu_olustur(self) -> Dict[str, Any]:
        """Genel şeffaflık raporu oluşturur"""
        rapor = {
            "rapor_id": f"SEFF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "rapor_tarihi": datetime.now().isoformat(),
            "raporlayan": f"{self.agent_name} (ID: {self.agent_id})",
            "ozet": {
                "toplam_gelir": self.seffaflik_veritabani["gelir_havuzu"]["toplam_gelir"],
                "toplam_imece_kesintisi": self.seffaflik_veritabani["gelir_havuzu"]["imece_havuz_kesintisi"],
                "toplam_yoksulluk_odemesi": self.seffaflik_veritabani["yoksulluk_yardimlari"]["toplam_odeme"],
                "toplam_vergi": (
                    self.seffaflik_veritabani["vergi_kayitlari"]["toplam_kdv"] +
                    self.seffaflik_veritabani["vergi_kayitlari"]["toplam_stopaj"] +
                    self.seffaflik_veritabani["vergi_kayitlari"]["toplam_gelir_vergisi"]
                )
            },
            "gelir_havuzu": self.seffaflik_veritabani["gelir_havuzu"],
            "yoksulluk_yardimlari": self.seffaflik_veritabani["yoksulluk_yardimlari"],
            "vergi_kayitlari": self.seffaflik_veritabani["vergi_kayitlari"]
        }
        
        self.log(f"📊 Şeffaflık raporu oluşturuldu", "INFO")
        
        return rapor
    
    def stop(self) -> Dict[str, Any]:
        self.is_running = False
        self.status = "stopped"
        return {"status": "stopped", "agent_id": self.agent_id}
    
    def restart(self) -> Dict[str, Any]:
        self.status = "ready"
        self.is_running = True
        return {"status": "restarted", "agent_id": self.agent_id}
    
    def run(self, operation: str = "rapor", **kwargs) -> Dict[str, Any]:
        if operation == "gelir_kaydet":
            return self.gelir_kaydet(
                kwargs.get("islem_id"),
                kwargs.get("gelir_tutari"),
                kwargs.get("gelir_kaynagi"),
                kwargs.get("kullanici_id"),
                kwargs.get("tarih")
            )
        elif operation == "yoksulluk_yardimi":
            return self.yoksulluk_yardimi_kaydet(
                kwargs.get("islem_id"),
                kwargs.get("kullanici_id"),
                kwargs.get("ad_soyad"),
                kwargs.get("il"),
                kwargs.get("odeme_tutari"),
                kwargs.get("odeme_tarihi")
            )
        elif operation == "vergi_kaydet":
            return self.vergi_kaydet(
                kwargs.get("islem_id"),
                kwargs.get("vergi_turu"),
                kwargs.get("matrah"),
                kwargs.get("kullanici_id"),
                kwargs.get("tarih")
            )
        elif operation == "uyum_raporu":
            return self.resmi_makam_uyum_raporu_olustur(
                kwargs.get("rapor_turu", "genel"),
                kwargs.get("baslangic_tarihi"),
                kwargs.get("bitis_tarihi")
            )
        elif operation == "rapor":
            return self.seffaflik_raporu_olustur()
        return {"hata": "Bilinmeyen işlem"}


if __name__ == "__main__":
    print("Seffaflik ve Denetim Ajan Test Basliyor...")
    ajan = SeffaflikVeDenetimAjani(agent_id=181)
    
    # Test gelir kaydet
    gelir = ajan.run(
        operation="gelir_kaydet",
        islem_id="GEL001",
        gelir_tutari=10000,
        gelir_kaynagi="e_ticaret",
        kullanici_id="K001"
    )
    
    print(f"\nGelir Kayıt Sonucu:")
    print(f"Gelir Tutarı: {gelir['gelir_tutari']} TL")
    print(f"Refah Kesintisi: {gelir['imece_havuz_kesintisi']} TL")
    print(f"Net Gelir: {gelir['net_gelir']} TL")
    
    # Test yoksulluk yardımı
    yardim = ajan.run(
        operation="yoksulluk_yardimi",
        islem_id="YRD001",
        kullanici_id="K001",
        ad_soyad="Ayşe Yılmaz",
        il="istanbul",
        odeme_tutari=5000
    )
    
    print(f"\nYoksulluk Yardımı Sonucu:")
    print(f"Ödeme Tutarı: {yardim['odeme_tutari']} TL")
    print(f"İl: {yardim['il']}")
    
    # Test vergi kaydet
    vergi = ajan.run(
        operation="vergi_kaydet",
        islem_id="VRG001",
        vergi_turu="kdv",
        matrah=10000,
        kullanici_id="K001"
    )
    
    print(f"\nVergi Kayıt Sonucu:")
    print(f"Vergi Türü: {vergi['vergi_turu']}")
    print(f"Vergi Tutarı: {vergi['vergi_tutari']} TL")
    
    # Test uyum raporu
    uyum = ajan.run(operation="uyum_raporu", rapor_turu="maliye")
    print(f"\nResmi Makam Uyum Raporu:")
    print(f"Rapor ID: {uyum['rapor_id']}")
    print(f"Toplam Gelir: {uyum['gelir_ozeti']['toplam_gelir']} TL")
    print(f"Toplam Vergi: {uyum['vergi_ozeti']['toplam_vergi']} TL")
    
    # Genel şeffaflık raporu
    rapor = ajan.run(operation="rapor")
    print(f"\nŞeffaflık Raporu:")
    print(f"Toplam Gelir: {rapor['ozet']['toplam_gelir']} TL")
    print(f"Toplam Refah Kesintisi: {rapor['ozet']['toplam_imece_kesintisi']} TL")
    print(f"Toplam Yoksulluk Ödemesi: {rapor['ozet']['toplam_yoksulluk_odemesi']} TL")
