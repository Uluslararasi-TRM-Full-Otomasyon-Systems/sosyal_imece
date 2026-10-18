#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from typing import Dict, Any

class TanitimVeSosyalMedyaAjani:
    def __init__(self, agent_id: int = 175):
        self.agent_id = agent_id
        self.tanitim_gecmisi_dosyasi = "sosyal_medya_tanitim_loglari.json"
        self._dosya_kontrol()

    def _dosya_kontrol(self):
        if not os.path.exists(self.tanitim_gecmisi_dosyasi):
            with open(self.tanitim_gecmisi_dosyasi, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)

    def tanitim_metni_uret(self, proje_adi: str, faaliyet_turu: str, hedef_kitle: str = "Genel Kamuoyu") -> Dict[str, Any]:
        timestamp = datetime.now().isoformat()
        
        tweet_metni = (
            f"🌟 Birlikte Güçlüyüz! {proje_adi} ile dayanışma ağımızı büyütüyoruz. "
            f"'{faaliyet_turu}' hareketimize katılarak siz de bu iyilik zincirinin bir parçası olun. "
            f"Gelin, geleceği birlikte inşa edelim! 🤝✨ #TRMTicari #Dayanışma"
        )
        
        linkedin_metni = (
            f"Değerli paydaşlarımız ve bağışçılarımız,\n\n"
            f"TRM Ticari Ekosistem inisiyatifi olarak hayata geçirdiğimiz {proje_adi} kapsamında "
            f"'{faaliyet_turu}' çalışmalarımız tüm hızıyla sürüyor. Şeffaf, güvenli ve yasal kanıt zinciriyle "
            f"desteklenen bu projede {hedef_kitle} odaklı büyümemizi sürdürüyoruz.\n\n"
            f"Siz de toplumsal dönüşümümüze katkı sunmak için sitemizi ziyaret edebilirsiniz."
        )

        kayit = {
            "agent_id": self.agent_id,
            "proje_adi": proje_adi,
            "faaliyet_turu": faaliyet_turu,
            "hedef_kitle": hedef_kitle,
            "tweet_metni": tweet_metni,
            "linkedin_metni": linkedin_metni,
            "timestamp": timestamp,
            "durum": "basarili"
        }

        try:
            with open(self.tanitim_gecmisi_dosyasi, "r+", encoding="utf-8") as f:
                veriler = json.load(f)
                veriler.append(kayit)
                f.seek(0)
                json.dump(veriler, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

        return kayit