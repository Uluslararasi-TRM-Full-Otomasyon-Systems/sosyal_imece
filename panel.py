import streamlit as st
import json
from imece_dagitim_motoru import hesapla_ve_dagit

st.set_page_config(page_title="Sosyal İmece Otonom Panel", layout="wide")

st.title("🌟 Sosyal İmece & TRM Full Otomasyon Paneli")

tab1, tab2 = st.tabs(["🏛️ 55+ Adalet & Zenginlik Payı Dağıtımı", "🤖 Şefkatli Rehber & Mülakat Logları"])

with tab1:
    st.subheader("55+ Refah ve Zenginlik Payı Dağıtım Simülasyonu")
    col1, col2 = st.columns(2)
    with col1:
        havuz_input = st.number_input("Dağıtılacak Toplam İmece Havuzu (TL)", min_value=1000.0, value=100000.0, step=5000.0)
    
    ornek_uyeler = [
        {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
        {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
        {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
        {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
    ]

    sonuc_dagitim = hesapla_ve_dagit(havuz_input, ornek_uyeler)

    if "detaylar" in sonuc_dagitim:
        st.metric("Toplam Aktarılan Fon", f"{havuz_input:,.2f} TL")
        c1, c2 = st.columns(2)
        c1.metric("Toplam Onaylı Üye", sonuc_dagitim["n_toplam_uye"])
        c2.metric("55+ Kıdemli Üye", sonuc_dagitim["n_55_plus_uye"])
        st.write("### 📊 Hesap Dağıtım Dökümü")
        st.dataframe(sonuc_dagitim["detaylar"])

with tab2:
    st.subheader("Aday Mülakat Audit Logları")
    try:
        with open("applicant_audits.json", "r", encoding="utf-8") as f:
            audits = json.load(f)
        st.dataframe(audits)
    except Exception as e:
        st.info("Henüz audit log kaydı bulunamadı veya dosya okunamadı.")
