import streamlit as st
from gtts import gTTS
import os

class TanitimVeSosyalMedyaAjani:
    def __init__(self):
        pass

    def tanitim_metni_uret(self, proje_adi, faaliyet_turu, hedef_kitle):
        tanitim = (
            f"[{proje_adi}] Projesi için {faaliyet_turu} faaliyet alanında, "
            f"{hedef_kitle} hedef kitleye yönelik otonom tanıtım ve sözleşme altyapısı başarıyla oluşturuldu."
        )
        return tanitim

    def sesli_okuma_yap(self, metin):
        # gTTS ile Türkçe ses dosyası oluşturuyoruz
        tts = gTTS(text=metin, lang='tr', slow=False)
        ses_dosyasi = "tanitim_ses.mp3"
        tts.save(ses_dosyasi)
        return ses_dosyasi

def main():
    st.title("İR-SA AŞ. & UTEYKDER - Sözleşme ve Sesli Tanıtım Paneli")
    st.subheader("Görünmez Fabrika Otonom Yönetim Sistemi")
    
    st.divider()
    
    proje_adi = st.text_input("Proje Adı:", "TRM Ticari Dünyası")
    faaliyet_turu = st.text_input("Faaliyet Türü:", "E-Ticaret ve Dijital Kooperatif")
    hedef_kitle = st.text_input("Hedef Kitle:", "Girişimciler ve Dijital İştirakçiler")
    
    if st.button("Tanıtım Metni Üret ve Sesli Dinle"):
        with st.spinner("Otonom sistem metni hazırlıyor ve seslendiriyor..."):
            ajans = TanitimVeSosyalMedyaAjani()
            sonuc = ajans.tanitim_metni_uret(proje_adi, faaliyet_turu, hedef_kitle)
            
            st.success("Metin Başarıyla Üretildi:")
            st.write(sonuc)
            
            # Ses dosyasını oluştur ve arayüzde oynatıcı olarak göster
            ses_dosyasi = ajans.sesli_okuma_yap(sonuc)
            st.audio(ses_dosyasi, format='audio/mp3')

if __name__ == "__main__":
    main()