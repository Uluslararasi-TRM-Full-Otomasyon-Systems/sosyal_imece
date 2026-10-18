import streamlit as st
from datetime import datetime, date
import json
import os

class UyumDenetimPanelEntegrasyonu:
    def __init__(self, agent_id=102):
        self.agent_id = agent_id
        self.storage_file = "uyye_hak_edis_listesi.json"
        
    def hesapla_hak_edis(self, katilim_tarihi_str):
        """Yeni üyenin sisteme giriş tarihine göre bir sonraki ayın 1'ini hak ediş olarak belirler."""
        try:
            katilim_tarihi = datetime.strptime(katilim_tarihi_str, "%Y-%m-%d").date()
            if katilim_tarihi.month == 12:
                hak_edis_tarihi = date(katilim_tarihi.year + 1, 1, 1)
            else:
                hak_edis_tarihi = date(katilim_tarihi.year, katilim_tarihi.month + 1, 1)
            return hak_edis_tarihi.strftime("%Y-%m-%d")
        except Exception as e:
            return f"Tarih Hesaplama Hatası: {e}"

    def render_panel(self):
        st.subheader("⚖️ Uyum Denetim Konseyi - Refah Hak Ediş Modülü (Ajan 102)")
        st.info("💡 Sisteme sonradan dahil olan üyelerin refah payı hak ediş tarihlerini (her ayın 1'i kuralı) otomatik denetler ve kaydeder.")
        
        with st.form("uye_kayit_formu"):
            col1, col2 = st.columns(2)
            with col1:
                uye_id = st.text_input("Üye ID / Kodu", placeholder="UYE_010")
                uye_adi = st.text_input("Üye Adı Soyadı", placeholder="İsim Soyisim")
            with col2:
                giris_tarihi = st.date_input("Sisteme Giriş Tarihi", value=date.today())
                
            kaydet_btn = st.form_submit_button("🛡️ Üyeyi Kaydet ve Hak Ediş Hesapla")
            
            if kaydet_btn:
                hesaplanan_hak_edis = self.hesapla_hak_edis(str(giris_tarihi))
                
                yeni_kayit = {
                    "uye_id": uye_id,
                    "uye_adi": uye_adi,
                    "giris_tarihi": str(giris_tarihi),
                    "hak_edis_tarihi": hesaplanan_hak_edis,
                    "status": "Aktif/Beklemede"
                }
                
                # Veriyi JSON dosyasına kaydet
                data = []
                if os.path.exists(self.storage_file):
                    try:
                        with open(self.storage_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    except:
                        data = []
                
                data.append(yeni_kayit)
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
                st.success(f"✅ Üye başarıyla kaydedildi! İlk Refah Payı Hak Ediş Tarihi: **{hesaplanan_hak_edis}**")

        # Kayıtlı Üyeleri Listeleme
        if os.path.exists(self.storage_file):
            st.markdown("---")
            st.subheader("📋 Kayıtlı Öncü ve Yeni Kadro Listesi")
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    kayitlar = json.load(f)
                if kayitlar:
                    st.json(kayitlar)
                else:
                    st.warning("Henüz kayıtlı üye bulunmuyor.")
            except Exception as e:
                st.error(f"Kayıtlar okunurken hata oluştu: {e}")

# Çalıştırmak için:
# panel_agent = UyumDenetimPanelEntegrasyonu()
# panel_agent.render_panel()