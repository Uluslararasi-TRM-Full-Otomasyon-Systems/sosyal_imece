#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Küresel Psikolog AI Ajanı - TRM Ticari Dünyası Entegrasyonu
- Karakter analizi ve motivasyon değerlendirme
- Otonom onay/reddetme sistemi
"""

import sys
import io
import json
import os
import logging
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List

# UTF-8 encoding fix for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KarakterAnalizi:
    """Karakter Analizi Veri Yapısı"""
    aday_id: str
    ad: str
    soyad: str
    motivasyon_cümlesi: str
    risk_puani: float
    sapitma_skoru: float
    vizyon_uyusma: float
    karar: str  # "OTONOM ONAYLANDI", "REDDEDILDI", "YUKSEK RISK"
    analiz_notu: str
    analiz_tarihi: str

class KureselPsikologAjani:
    def __init__(self):
        self.karakter_analizleri_dosyasi = "karakter_analizleri.json"
        self.otonom_onayli_uyeler_dosyasi = "otonom_onayli_uyeler.json"
        self.analizler = []
        self.analiz_yukle()
    
    def analiz_yukle(self):
        """Karakter analizlerini yükle"""
        try:
            if os.path.exists(self.karakter_analizleri_dosyasi):
                with open(self.karakter_analizleri_dosyasi, 'r', encoding='utf-8') as f:
                    self.analizler = json.load(f)
        except Exception as e:
            logger.error(f"Analiz yükleme hatası: {e}")
            self.analizler = []
    
    def analiz_kaydet(self, analiz: KarakterAnalizi):
        """Karakter analizini kaydet"""
        try:
            self.analizler.append(asdict(analiz))
            with open(self.karakter_analizleri_dosyasi, 'w', encoding='utf-8') as f:
                json.dump(self.analizler, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Karakter analizi kaydedildi: {analiz.aday_id}")
        except Exception as e:
            logger.error(f"❌ Analiz kaydetme hatası: {e}")
    
    def otonom_uye_kaydet(self, uye_verileri: Dict):
        """Otonom onaylı üyeyi kaydet"""
        try:
            uyeler = []
            if os.path.exists(self.otonom_onayli_uyeler_dosyasi):
                with open(self.otonom_onayli_uyeler_dosyasi, 'r', encoding='utf-8') as f:
                    uyeler = json.load(f)
            
            uye_verileri['onay_tarihi'] = datetime.now().isoformat()
            uyeler.append(uye_verileri)
            
            with open(self.otonom_onayli_uyeler_dosyasi, 'w', encoding='utf-8') as f:
                json.dump(uyeler, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Otonom onaylı üye kaydedildi: {uye_verileri.get('ad')} {uye_verileri.get('soyad')}")
            return True
        except Exception as e:
            logger.error(f"❌ Otonom üye kaydetme hatası: {e}")
            return False
    
    def kelime_analizi(self, metin: str) -> Dict:
        """Metin içindeki pozitif/negatif kelime analizi"""
        pozitif_kelimeler = [
            'işbirliği', 'yardım', 'destek', 'gelişim', 'başarı', 'vizyon', 'hedef',
            'katkı', 'paylaşım', 'dayanışma', 'güven', 'sorumluluk', 'önem', 'değer',
            'fayda', 'iyilik', 'barış', 'huzur', 'mutluluk', 'sevgi', 'saygı',
            'çalışkan', 'azim', 'kararlı', 'istekli', 'hevesli', 'coşkulu'
        ]
        
        negatif_kelimeler = [
            'kazanç', 'para', 'para', 'borsa', 'yatırım', 'spekülasyon', 'kâr',
            'hile', 'dolandırıcılık', 'kandırma', 'yanlış', 'yalan', 'sahte',
            'bencil', 'kibir', 'arrogant', 'hakaret', 'saldırgan', 'tehdit',
            'şüphe', 'güvenilmez', 'riskli', 'tehlikeli'
        ]
        
        metin_lower = metin.lower()
        pozitif_sayisi = sum(1 for kelime in pozitif_kelimeler if kelime in metin_lower)
        negatif_sayisi = sum(1 for kelime in negatif_kelimeler if kelime in metin_lower)
        
        toplam_kelime = len(metin.split())
        vizyon_uyusma = (pozitif_sayisi / max(toplam_kelime, 1)) * 100
        
        return {
            'pozitif_sayisi': pozitif_sayisi,
            'negatif_sayisi': negatif_sayisi,
            'vizyon_uyusma': vizyon_uyusma
        }
    
    def sapitma_analizi(self, metin: str) -> float:
        """Metin sapıtma analizi (tekrar, tutarsızlık vb.)"""
        kelimeler = metin.split()
        kelime_frekans = {}
        
        for kelime in kelimeler:
            kelime_lower = kelime.lower().strip('.,!?;:')
            kelime_frekans[kelime_lower] = kelime_frekans.get(kelime_lower, 0) + 1
        
        # Aynı kelimenin tekrar oranı
        tekrar_orani = sum(1 for freq in kelime_frekans.values() if freq > 2) / max(len(kelimeler), 1)
        
        # Cümle uzunluğu tutarsızlığı
        cumleler = re.split(r'[.!?]', metin)
        cumle_uzunluklari = [len(c.split()) for c in cumleler if c.strip()]
        
        if len(cumle_uzunluklari) > 1:
            ortalama_uzunluk = sum(cumle_uzunluklari) / len(cumle_uzunluklari)
            sapma = sum(abs(u - ortalama_uzunluk) for u in cumle_uzunluklari) / len(cumle_uzunluklari)
            sapitma_skoru = (tekrar_orani * 50) + (sapma / max(ortalama_uzunluk, 1) * 50)
        else:
            sapitma_skoru = tekrar_orani * 50
        
        return min(sapitma_skoru, 100)
    
    def muracaat_degerlendir_ve_onayla(self, aday_verileri: Dict) -> Dict:
        """Müracaatı değerlendir ve otonom onayla"""
        try:
            ad = aday_verileri.get('ad', '')
            soyad = aday_verileri.get('soyad', '')
            motivasyon = aday_verileri.get('motivasyon_cümlesi', '')
            
            if not motivasyon:
                return {
                    'durum': 'hata',
                    'mesaj': 'Motivasyon cümlesi bulunamadı'
                }
            
            # Kelime analizi
            kelime_sonuc = self.kelime_analizi(motivasyon)
            
            # Sapıtma analizi
            sapitma_skoru = self.sapitma_analizi(motivasyon)
            
            # Risk puanı hesapla
            vizyon_uyusma = kelime_sonuc['vizyon_uyusma']
            negatif_oran = kelime_sonuc['negatif_sayisi'] / max(len(motivasyon.split()), 1)
            
            risk_puani = (negatif_oran * 100) + (sapitma_skoru * 0.3) - (vizyon_uyusma * 0.5)
            risk_puani = max(0, min(100, risk_puani))
            
            # Karar mekanizması
            if risk_puani < 30 and vizyon_uyusma > 20:
                karar = "OTONOM ONAYLANDI"
                analiz_notu = f"Vizyon uyumu yüksek ({vizyon_uyusma:.1f}%), risk puanı düşük ({risk_puani:.1f}). Aday ekosistem değerleriyle uyumlu."
            elif risk_puani > 60 or negatif_oran > 0.3:
                karar = "REDDEDILDI"
                analiz_notu = f"Yüksek risk tespit edildi (Risk: {risk_puani:.1f}%, Negatif içerik: {negatif_oran*100:.1f}%). Ekosistem vizyonuyla uyuşmazlık."
            else:
                karar = "YUKSEK RISK"
                analiz_notu = f"Orta risk seviyesi (Risk: {risk_puani:.1f}%). Ek değerlendirme gerekebilir."
            
            # Analiz kaydı oluştur
            aday_id = f"ADAY-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            analiz = KarakterAnalizi(
                aday_id=aday_id,
                ad=ad,
                soyad=soyad,
                motivasyon_cümlesi=motivasyon,
                risk_puani=risk_puani,
                sapitma_skoru=sapitma_skoru,
                vizyon_uyusma=vizyon_uyusma,
                karar=karar,
                analiz_notu=analiz_notu,
                analiz_tarihi=datetime.now().isoformat()
            )
            
            self.analiz_kaydet(analiz)
            
            # Otonom onaylanmışsa üyeyi kaydet
            if karar == "OTONOM ONAYLANDI":
                self.otonom_uye_kaydet(aday_verileri)
            
            return {
                'durum': 'basarili',
                'karar': karar,
                'risk_puani': risk_puani,
                'sapitma_skoru': sapitma_skoru,
                'vizyon_uyusma': vizyon_uyusma,
                'analiz_notu': analiz_notu,
                'aday_id': aday_id
            }
            
        except Exception as e:
            logger.error(f"❌ Değerlendirme hatası: {e}")
            return {
                'durum': 'hata',
                'mesaj': f'Değerlendirme sırasında hata: {str(e)}'
            }
    
    def tum_analizleri_listele(self) -> List[Dict]:
        """Tüm karakter analizlerini listele"""
        return self.analizler

def main():
    """Test fonksiyonu"""
    print("🧠 Küresel Psikolog AI Ajanı Başlatılıyor...")
    print("=" * 60)
    
    ajan = KureselPsikologAjani()
    
    # Test müracaatı
    test_aday = {
        'ad': 'Ahmet',
        'soyad': 'Yılmaz',
        'motivasyon_cümlesi': 'Ekosisteme katkı sağlamak ve işbirliği içinde çalışmak istiyorum. Vizyonunuzu desteklemek için elimden geleni yapacağım.'
    }
    
    sonuc = ajan.muracaat_degerlendir_ve_onayla(test_aday)
    print(f"Değerlendirme Sonucu: {sonuc}")
    
    # Negatif test
    negatif_aday = {
        'ad': 'Mehmet',
        'soyad': 'Demir',
        'motivasyon_cümlesi': 'Sadece para kazanmak istiyorum. Borsa ve spekülasyonlarla hızlı kâr elde etmek istiyorum.'
    }
    
    negatif_sonuc = ajan.muracaat_degerlendir_ve_onayla(negatif_aday)
    print(f"Negatif Sonuç: {negatif_sonuc}")
    
    print("=" * 60)
    print("✅ Test tamamlandı!")

if __name__ == "__main__":
    main()
