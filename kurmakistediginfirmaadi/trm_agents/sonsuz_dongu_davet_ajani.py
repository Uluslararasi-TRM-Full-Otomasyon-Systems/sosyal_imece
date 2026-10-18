# -*- coding: utf-8 -*-
from datetime import datetime

class SonsuzDonguDavetAjani:
    def __init__(self):
        self.ajan_id = 170
        self.isim = "Sonsuz Döngü Otomatik Davet Ajanı"
        
    def basari_raporu_ve_davetiye_uret(self, pilot_grup_kazanc_durumu):
        """Sistemin başarısını otonom olarak toplumsal fayda raporuna dönüştürür ve yeni derneklere davet atar."""
        if pilot_grup_kazanc_durumu == "BAŞARILI":
            return {
                "rapor_tarihi": datetime.now().strftime("%Y-%m-%d"),
                "hedef_kurum": "UTEYKDER / Sivil Toplum Kuruluşları",
                "olusturulan_davetiye": "TRM Ticari Ekosistem v4.0 Yeni Dezavantajlı Katılımcı Alım Raporu",
                "mesaj": "Sistemimiz otonom gelir modelini kanıtlamıştır. Yeni kontenjanlar açılmıştır.",
                "durum": "OTOMATİK MAİL GÖNDERİME HAZIR"
            }
        return {"durum": "TAKİPTE"}