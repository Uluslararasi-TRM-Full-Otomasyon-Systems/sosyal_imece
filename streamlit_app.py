import os
import streamlit as st
import requests
import json

st.set_page_config(page_title="Sosyal İmece & TRM Komuta Merkezi", layout="wide")

st.title("🌐 TRM / Sosyal İmece / UTEYKDER Komuta Merkezi")
st.markdown("---")

API_BASE = "http://localhost:5000"

tab1, tab2 = st.tabs(["📢 Çok Kanallı Sosyal Yayın", "💰 Sosyal İmece Mali Dağıtım"])

with tab1:
    st.subheader("Sosyal Medya Ajan Yayıncılığı (4 Kanal)")
    title = st.text_input("Ürün / İçerik Başlığı", "Trend Akıllı Bileklik & Sağlık Asistanı")
    link = st.text_input("Affiliate Link", "https://trendurunlermarket.com/akilli-bileklik")
    campaign = st.text_input("Kampanya Adı", "Yaz-2026-Otomasyon")
    
    if st.button("🚀 Kampanyayı Ateşle"):
        with st.spinner("Ajanlar yayın yapıyor..."):
            res = requests.post(f"{API_BASE}/api/agents/publish", json={
                "title": title, "link": link, "campaign": campaign
            })
            st.json(res.json())

with tab2:
    st.subheader("Sosyal İmece Gelir Dağıtım Motoru (Kademeli Kural Seti)")
    col1, col2 = st.columns(2)
    with col1:
        ceo_key = st.text_input("CEO API Anahtarı", value=os.getenv("CEO_API_KEY", ""), type="password")
        net_profit = st.number_input("Net Kâr (TL)", value=150000.0, step=5000.0)
    
    with col2:
        default_users = json.dumps([
            {"id": "uye_fahri", "age": 63},
            {"id": "uye_genc", "age": 29},
            {"id": "uye_olgun", "age": 57}
        ], indent=2, ensure_ascii=False)
        users_json = st.text_area("Üye Listesi (JSON)", value=default_users, height=130)
    
    if st.button("💰 İmece Dağıtımını Tetikle ve Sesli Anons Yap"):
        try:
            users_list = json.loads(users_json)
            headers = {"X-CEO-Key": ceo_key, "Content-Type": "application/json"}
            payload = {"net_profit": net_profit, "users": users_list}
            with st.spinner("Mali motor hesaplıyor ve sesli anons tetikleniyor..."):
                res = requests.post(f"{API_BASE}/api/imece/distribute", json=payload, headers=headers)
                st.json(res.json())
        except Exception as e:
            st.error(f"JSON / İstek hatası: {e}")
