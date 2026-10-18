#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hukuki Sözleşme ve Alacak Ajanı (Ajan 178) - Sözleşme, Hesap Güvencesi ve Tazminat Takip Modülü
Versiyon: 1.0.0

6 işletme hesabı İR-SA AŞ. yetki sözleşmesi, şifre teslimi izlenebilirliği,
İR-SA AŞ. sorumluluk güvencesi, hesap kapatma ve 1 yıllık alacak/tazminat hesaplayıcısı.
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


class HukukiSozlesmeVeAlacakAjani(BaseAgent):
    def __init__(self, agent_id: Optional[int] = None):
        super().__init__(
            agent_name="Hukuki Sözleşme ve Alacak Ajanı",
            agent_id=agent_id if agent_id else 178
        )
        
        # Dosya yolları
        self.sozlesme_loglari_dir = Path("data/hukuki_sozlesme_ve_alacak_loglari")
        self.sozlesme_loglari_dir.mkdir(parents=True, exist_ok=True)
        self.sozlesme_dosyasi = self.sozlesme_loglari_dir / "hukuki_sozlesme_ve_alacak_loglari.json"
        
        # Sözleşme şablonları
        self.sozlesme_sablonlari = self._sozlesme_sablonlari_olustur()
        
        # Kullanıcı veritabanı
        self.kullanici_veritabani = self._kullanici_veritabani_yukle()
        
        # Hesap sayısı
        self.isletme_hesap_sayisi = 6
        
        # Tahmini aylık refah geliri (hesaplama için)
        self.tahmini_aylik_imece_geliri = 5000  # TL
        
        self.log(f"⚖️ Hukuki Sözleşme ve Alacak Ajanı (Ajan 178) devrede. Sayın {CEO_TITLE}", "INFO")
    
    def _sozlesme_sablonlari_olustur(self) -> Dict[str, str]:
        """Sözleşme şablonları"""
        return {
            "yetki_sozlesmesi": """
            İR-SA AŞ. YETKİ SÖZLEŞMESİ
            
            Madde 1: İşletme Hesaplarının Yönetimi
            Kullanıcı, sistemde açılacak {hesap_sayisi} adet işletme hesabının illegal olmamak şartıyla
            İR-SA AŞ.'nin yönetimine bırakılmasını kabul eder.
            
            Madde 2: Sorumluluk Güvencesi
            İR-SA AŞ. yönetimi altındaki hesaplarda hukuki yönden yanlış paylaşımlar sonucu
            hesap sahibi zarar görürse ve kişi bunu belge/şahitlerle ispatlarsa, İR-SA AŞ. tüm zararı karşılar.
            
            Madde 3: Hesap Kapatma Yükümlülüğü
            Kullanıcı, sistem kurallarına aykırı davranarak veya kendi inisiyatifiyle hesapları
            tamamen/geçici kapatması suretiyle sistem gelirlerini sekteye uğratması durumunda,
            İR-SA AŞ. bu hesapların 1 yıllık refah havuz hesabına aktaracağı tahmini para miktarını
            hesaplayabilir ve kişi hakkında "sistem gelirlerini sekteye uğratma" gerekçesiyle alacak davası/tazminat
            dosyası açabilir.
            
            Madde 4: Şifre Teslimi
            Sistem tarafından açılan hesapların şifreleri kullanıcıya WhatsApp üzerinden
            (ekran görüntüsü kanıtı ve sistem içi loglamayla) iletilecektir.
            
            Tarih: {tarih}
            Kullanıcı ID: {kullanici_id}
            """,
            
            "sorumluluk_guvencesi": """
            İR-SA AŞ. SORUMLULUK GÜVENCESİ TAHHÜTNAMESİ
            
            İR-SA AŞ., yönetimi altındaki hesaplarda hukuki yönden yanlış paylaşımlar sonucu
            hesap sahibinin uğrayacağı zararları belge/şahitlerle ispatlanması halinde tamamen karşılar.
            
            Bu taahhütname, İR-SA AŞ.'nin hukuki ve mali sorumluluğunu pekiştirmek amacıyla
            düzenlenmiştir ve yasal geçerliliğe sahiptir.
            
            Tarih: {tarih}
            Kullanıcı ID: {kullanici_id}
            """,
            
            "alacak_davasi_taslak": """
            ALACAK DAVASI / TAZMİNAT DOSYASI TASLAĞI
            
            Davacı: İR-SA AŞ.
            Davalı: {ad_soyad} (TC: {tc_no})
            
            Dava Konusu: Sistem Gelirlerini Sekteye Uğratma Nedeniyle Alacak Davası
            
            Davanın Gerekçesi:
            Davalı, sistem kurallarına aykırı davranarak veya kendi inisiyatifiyle {hesap_sayisi} adet
            işletme hesabını tamamen/geçici kapatmış, bu suretle sistem gelirlerini sekteye uğratmıştır.
            
            Talep Edilen Tazminat Miktarı: {tazminat_miktari} TL
            (1 yıllık tahmini refah geliri: {tahmini_gelir} TL)
            
            Hesap Kapatma Tarihi: {kapatma_tarihi}
            Tahmini Zarar Süresi: 12 ay
            
            Deliller:
            - Hesap kapatma logları
            - Sistem gelir kayıpları
            - Refah havuz hesap kayıtları
            
            Tarih: {tarih}
            Dosya No: {dosya_no}
            """
        }
    
    def _kullanici_veritabani_yukle(self) -> Dict[str, Any]:
        """Kullanıcı veritabanını yükler"""
        if self.sozlesme_dosyasi.exists():
            with open(self.sozlesme_dosyasi, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"kullanicilar": {}, "sozlesmeler": {}, "alacak_davaları": {}}
    
    def _kullanici_veritabani_kaydet(self):
        """Kullanıcı veritabanını kaydeder"""
        with open(self.sozlesme_dosyasi, "w", encoding="utf-8") as f:
            json.dump(self.kullanici_veritabani, f, indent=4, ensure_ascii=False)
    
    def yetki_sozlesmesi_imzala(self, kullanici_id: str, ad_soyad: str, tc_no: str, 
                               telefon: str, eposta: str) -> Dict[str, Any]:
        """İR-SA AŞ. yetki sözleşmesini imzalar"""
        tarih = datetime.now().strftime("%Y-%m-%d")
        
        # Sözleşme metni oluştur
        sozlesme_metni = self.sozlesme_sablonlari["yetki_sozlesmesi"].format(
            hesap_sayisi=self.isletme_hesap_sayisi,
            tarih=tarih,
            kullanici_id=kullanici_id
        )
        
        sozlesme_bilgisi = {
            "sozlesme_id": f"SOZ_{kullanici_id}_{tarih}",
            "sozlesme_turu": "yetki_sozlesmesi",
            "kullanici_id": kullanici_id,
            "ad_soyad": ad_soyad,
            "tc_no": tc_no,
            "telefon": telefon,
            "eposta": eposta,
            "imza_tarihi": tarih,
            "sozlesme_metni": sozlesme_metni,
            "onay_durumu": "onayli",
            "hesap_sayisi": self.isletme_hesap_sayisi
        }
        
        # Kullanıcı bilgilerini kaydet
        self.kullanici_veritabani["kullanicilar"][kullanici_id] = {
            "kullanici_id": kullanici_id,
            "ad_soyad": ad_soyad,
            "tc_no": tc_no,
            "telefon": telefon,
            "eposta": eposta,
            "kayit_tarihi": tarih,
            "hesap_durumu": "aktif",
            "hesaplar": []
        }
        
        # Sözleşmeyi kaydet
        self.kullanici_veritabani["sozlesmeler"][kullanici_id] = sozlesme_bilgisi
        
        self._kullanici_veritabani_kaydet()
        
        self.log(f"📝 Yetki sözleşmesi imzalandı: {ad_soyad} ({kullanici_id})", "INFO")
        
        return sozlesme_bilgisi
    
    def hesap_olustur(self, kullanici_id: str, platform: str, hesap_adi: str) -> Dict[str, Any]:
        """İşletme hesabı oluşturur"""
        kullanici = self.kullanici_veritabani["kullanicilar"].get(kullanici_id)
        
        if not kullanici:
            return {"hata": "Kullanıcı bulunamadı"}
        
        if len(kullanici["hesaplar"]) >= self.isletme_hesap_sayisi:
            return {"hata": f"Maksimum {self.isletme_hesap_sayisi} hesap limitine ulaşıldı"}
        
        hesap_bilgisi = {
            "hesap_id": f"HES_{kullanici_id}_{platform}_{len(kullanici['hesaplar'])+1}",
            "platform": platform,
            "hesap_adi": hesap_adi,
            "olusturma_tarihi": datetime.now().strftime("%Y-%m-%d"),
            "durum": "aktif",
            "sifre": None,
            "sifre_teslim_durumu": "bekliyor"
        }
        
        kullanici["hesaplar"].append(hesap_bilgisi)
        self._kullanici_veritabani_kaydet()
        
        self.log(f"🔐 Hesap oluşturuldu: {hesap_adi} ({platform})", "INFO")
        
        return hesap_bilgisi
    
    def sifre_teslimi_kaydet(self, kullanici_id: str, hesap_id: str, 
                            sifre: str, teslim_yontemi: str = "whatsapp") -> Dict[str, Any]:
        """Şifre teslimini kaydeder"""
        kullanici = self.kullanici_veritabani["kullanicilar"].get(kullanici_id)
        
        if not kullanici:
            return {"hata": "Kullanıcı bulunamadı"}
        
        hesap = None
        for h in kullanici["hesaplar"]:
            if h["hesap_id"] == hesap_id:
                hesap = h
                break
        
        if not hesap:
            return {"hata": "Hesap bulunamadı"}
        
        teslim_bilgisi = {
            "teslim_id": f"TES_{kullanici_id}_{hesap_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "kullanici_id": kullanici_id,
            "hesap_id": hesap_id,
            "sifre": sifre,
            "teslim_yontemi": teslim_yontemi,
            "teslim_tarihi": datetime.now().isoformat(),
            "ekran_goruntusu_kaniti": True,
            "sistem_logu": True,
            "teslim_durumu": "tamamlandi"
        }
        
        hesap["sifre"] = sifre
        hesap["sifre_teslim_durumu"] = "teslim_edildi"
        hesap["teslim_bilgisi"] = teslim_bilgisi
        
        self._kullanici_veritabani_kaydet()
        
        self.log(f"📱 Şifre teslim edildi: {hesap['hesap_adi']} via {teslim_yontemi}", "INFO")
        
        return teslim_bilgisi
    
    def sorumluluk_guvencesi_tahhut(self, kullanici_id: str) -> Dict[str, Any]:
        """İR-SA AŞ. sorumluluk güvencesi taahhüdünü işler"""
        kullanici = self.kullanici_veritabani["kullanicilar"].get(kullanici_id)
        
        if not kullanici:
            return {"hata": "Kullanıcı bulunamadı"}
        
        tarih = datetime.now().strftime("%Y-%m-%d")
        
        taahhut_metni = self.sozlesme_sablonlari["sorumluluk_guvencesi"].format(
            tarih=tarih,
            kullanici_id=kullanici_id
        )
        
        taahhut_bilgisi = {
            "taahhut_id": f"TAH_{kullanici_id}_{tarih}",
            "kullanici_id": kullanici_id,
            "ad_soyad": kullanici["ad_soyad"],
            "taahhut_tarihi": tarih,
            "taahhut_metni": taahhut_metni,
            "guvence_durumu": "aktif"
        }
        
        kullanici["sorumluluk_guvencesi"] = taahhut_bilgisi
        self._kullanici_veritabani_kaydet()
        
        self.log(f"🛡️ Sorumluluk güvencesi taahhüdü: {kullanici['ad_soyad']}", "INFO")
        
        return taahhut_bilgisi
    
    def hesap_kapatma_ve_tazminat_hesapla(self, kullanici_id: str, kapatma_nedeni: str, 
                                         kapatma_turu: str = "tamamen") -> Dict[str, Any]:
        """Hesap kapatma ve 1 yıllık alacak/tazminat hesaplar"""
        kullanici = self.kullanici_veritabani["kullanicilar"].get(kullanici_id)
        
        if not kullanici:
            return {"hata": "Kullanıcı bulunamadı"}
        
        # Tazminat hesapla (1 yıllık tahmini refah geliri)
        tahmini_yillik_zarar = self.tahmini_aylik_imece_geliri * 12 * len(kullanici["hesaplar"])
        
        # Dosya numarası oluştur
        dosya_no = f"DAVA_{kullanici_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Alacak davası taslağı oluştur
        dava_taslak = self.sozlesme_sablonlari["alacak_davasi_taslak"].format(
            ad_soyad=kullanici["ad_soyad"],
            tc_no=kullanici["tc_no"],
            hesap_sayisi=len(kullanici["hesaplar"]),
            tazminat_miktari=tahmini_yillik_zarar,
            tahmini_gelir=self.tahmini_aylik_imece_geliri * 12,
            kapatma_tarihi=datetime.now().strftime("%Y-%m-%d"),
            tarih=datetime.now().strftime("%Y-%m-%d"),
            dosya_no=dosya_no
        )
        
        # Hesapları kapat
        for hesap in kullanici["hesaplar"]:
            hesap["durum"] = kapatma_turu
            hesap["kapatma_tarihi"] = datetime.now().strftime("%Y-%m-%d")
            hesap["kapatma_nedeni"] = kapatma_nedeni
        
        kullanici["hesap_durumu"] = kapatma_turu
        
        # Alacak davası bilgisini kaydet
        alacak_davasi = {
            "dava_id": dosya_no,
            "kullanici_id": kullanici_id,
            "ad_soyad": kullanici["ad_soyad"],
            "tc_no": kullanici["tc_no"],
            "dava_tarihi": datetime.now().strftime("%Y-%m-%d"),
            "kapatma_nedeni": kapatma_nedeni,
            "kapatma_turu": kapatma_turu,
            "hesap_sayisi": len(kullanici["hesaplar"]),
            "tahmini_yillik_zarar": tahmini_yillik_zarar,
            "dava_taslak": dava_taslak,
            "dava_durumu": "hazirlaniyor"
        }
        
        self.kullanici_veritabani["alacak_davaları"][dosya_no] = alacak_davasi
        self._kullanici_veritabani_kaydet()
        
        self.log(f"⚖️ Alacak davası dosyası hazırlandı: {kullanici['ad_soyad']} - {tahmini_yillik_zarar} TL", "WARNING")
        
        return alacak_davasi
    
    def rapor_olustur(self) -> Dict[str, Any]:
        """Genel rapor oluşturur"""
        rapor = {
            "rapor_id": f"HUKUK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "rapor_tarihi": datetime.now().isoformat(),
            "raporlayan": f"{self.agent_name} (ID: {self.agent_id})",
            "toplam_kullanici": len(self.kullanici_veritabani["kullanicilar"]),
            "toplam_sozlesme": len(self.kullanici_veritabani["sozlesmeler"]),
            "toplam_alacak_davasi": len(self.kullanici_veritabani["alacak_davaları"]),
            "aktif_hesaplar": 0,
            "kapatilmis_hesaplar": 0,
            "toplam_tahmini_zarar": 0,
            "kullanici_detaylari": []
        }
        
        for kullanici_id, kullanici in self.kullanici_veritabani["kullanicilar"].items():
            aktif = sum(1 for h in kullanici["hesaplar"] if h["durum"] == "aktif")
            kapatilmis = sum(1 for h in kullanici["hesaplar"] if h["durum"] != "aktif")
            
            rapor["aktif_hesaplar"] += aktif
            rapor["kapatilmis_hesaplar"] += kapatilmis
            
            rapor["kullanici_detaylari"].append({
                "kullanici_id": kullanici_id,
                "ad_soyad": kullanici["ad_soyad"],
                "hesap_sayisi": len(kullanici["hesaplar"]),
                "aktif_hesaplar": aktif,
                "kapatilmis_hesaplar": kapatilmis,
                "hesap_durumu": kullanici["hesap_durumu"]
            })
        
        # Toplam tahmini zarar
        for dava_id, dava in self.kullanici_veritabani["alacak_davaları"].items():
            rapor["toplam_tahmini_zarar"] += dava["tahmini_yillik_zarar"]
        
        self.log(f"📊 Hukuki rapor oluşturuldu: {rapor['toplam_kullanici']} kullanıcı", "INFO")
        
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
        if operation == "sozlesme_imzala":
            return self.yetki_sozlesmesi_imzala(
                kwargs.get("kullanici_id"),
                kwargs.get("ad_soyad"),
                kwargs.get("tc_no"),
                kwargs.get("telefon"),
                kwargs.get("eposta")
            )
        elif operation == "hesap_olustur":
            return self.hesap_olustur(
                kwargs.get("kullanici_id"),
                kwargs.get("platform"),
                kwargs.get("hesap_adi")
            )
        elif operation == "sifre_teslim":
            return self.sifre_teslimi_kaydet(
                kwargs.get("kullanici_id"),
                kwargs.get("hesap_id"),
                kwargs.get("sifre"),
                kwargs.get("teslim_yontemi", "whatsapp")
            )
        elif operation == "guvence":
            return self.sorumluluk_guvencesi_tahhut(kwargs.get("kullanici_id"))
        elif operation == "tazminat":
            return self.hesap_kapatma_ve_tazminat_hesapla(
                kwargs.get("kullanici_id"),
                kwargs.get("kapatma_nedeni"),
                kwargs.get("kapatma_turu", "tamamen")
            )
        elif operation == "rapor":
            return self.rapor_olustur()
        return {"hata": "Bilinmeyen işlem"}


if __name__ == "__main__":
    print("Hukuki Sozlesme ve Alacak Ajan Test Basliyor...")
    ajan = HukukiSozlesmeVeAlacakAjani(agent_id=178)
    
    # Test sözleşme imzala
    sozlesme = ajan.run(
        operation="sozlesme_imzala",
        kullanici_id="H001",
        ad_soyad="Mehmet Demir",
        tc_no="12345678901",
        telefon="5551234567",
        eposta="mehmet@example.com"
    )
    
    print(f"\nSozlesme Sonucu:")
    print(f"Ad Soyad: {sozlesme['ad_soyad']}")
    print(f"Sozlesme ID: {sozlesme['sozlesme_id']}")
    print(f"Hesap Sayisi: {sozlesme['hesap_sayisi']}")
    
    # Test hesap oluştur
    hesap = ajan.run(
        operation="hesap_olustur",
        kullanici_id="H001",
        platform="instagram",
        hesap_adi="mehmet_demir_official"
    )
    
    print(f"\nHesap Sonucu:")
    print(f"Hesap ID: {hesap['hesap_id']}")
    print(f"Platform: {hesap['platform']}")
    
    # Test şifre teslimi
    sifre = ajan.run(
        operation="sifre_teslim",
        kullanici_id="H001",
        hesap_id=hesap['hesap_id'],
        sifre="secure123",
        teslim_yontemi="whatsapp"
    )
    
    print(f"\nSifre Teslim Sonucu:")
    print(f"Teslim ID: {sifre['teslim_id']}")
    print(f"Teslim Durumu: {sifre['teslim_durumu']}")
    
    # Test sorumluluk güvencesi
    guvence = ajan.run(operation="guvence", kullanici_id="H001")
    print(f"\nGuvence Sonucu:")
    print(f"Taahhut ID: {guvence['taahhut_id']}")
    
    # Test tazminat hesapla
    tazminat = ajan.run(
        operation="tazminat",
        kullanici_id="H001",
        kapatma_nedeni="sistem_kurallarina_aykirilik",
        kapatma_turu="tamamen"
    )
    
    print(f"\nTazminat Sonucu:")
    print(f"Dava ID: {tazminat['dava_id']}")
    print(f"Tahmini Yillik Zarar: {tazminat['tahmini_yillik_zarar']} TL")
    
    # Rapor
    rapor = ajan.run(operation="rapor")
    print(f"\nRapor Sonucu:")
    print(f"Toplam Kullanici: {rapor['toplam_kullanici']}")
    print(f"Toplam Sozlesme: {rapor['toplam_sozlesme']}")
    print(f"Toplam Alacak Davasi: {rapor['toplam_alacak_davasi']}")
