import streamlit as st
import sqlite3
import os
from derya_cevaplayici import derya_otonom_yanitla

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

st.set_page_config(page_title="TRM Otonom Esnaf Kontrol Paneli", layout="wide", page_icon="🌸")

st.title("🌸 TRM Akıllı Esnaf - Derya Canlı İletişim & Otomasyon Paneli")

def veritabani_baglan():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

tab1, tab2 = st.tabs(["📊 İşletme Listesi & Durumlar", "💬 Derya Canlı WhatsApp Sohbet & Test Paneli"])

with tab1:
    st.subheader("Kayıtlı İşletmeler")
    conn = veritabani_baglan()
    esnaflar = conn.execute("SELECT * FROM esnaflar").fetchall()
    conn.close()
    
    if esnaflar:
        for e in esnaflar:
            st.write(f"🏢 **{e['isletme']}** | 📞 {e['telefon']} | 🔑 Kod: `{e['kod']}` | Durum: `{e['durum']}`")
    else:
        st.info("Henüz kayıtlı işletme bulunamadı.")

with tab2:
    st.subheader("👩‍💼 Derya Otonom Canlı Mesajlaşma Akışı")
    
    conn = veritabani_baglan()
    esnaflar = conn.execute("SELECT id, isletme FROM esnaflar").fetchall()
    
    if esnaflar:
        secilen_esnaf = st.selectbox("Sohbeti Yönetmek / İzlemek İstediğiniz İşletmeyi Seçin:", esnaflar, format_func=lambda x: x["isletme"])
        
        if secilen_esnaf:
            st.markdown(f"### 💬 {secilen_esnaf['isletme']} ile Sohbet Akışı")
            
            # Mesaj geçmişini çekme
            mesajlar = conn.execute(
                "SELECT gonderen, mesaj, tarih FROM mesajlar WHERE esnaf_id = ? ORDER BY id ASC", 
                (secilen_esnaf["id"],)
            ).fetchall()
            
            # Sohbet Balonlarını Gösterme
            chat_container = st.container()
            with chat_container:
                if mesajlar:
                    for m in mesajlar:
                        if m["gonderen"] == "DERYA":
                            st.chat_message("assistant", avatar="🌸").write(f"**Derya:** {m['mesaj']}  \n*<sub>{m['tarih']}</sub>*")
                        else:
                            st.chat_message("user", avatar="🏪").write(f"**{secilen_esnaf['isletme']}:** {m['mesaj']}  \n*<sub>{m['tarih']}</sub>*")
                else:
                    st.info("Bu işletme ile henüz bir mesajlaşma geçmişi yok.")
            
            st.divider()
            
            # Canlı Test & Mesaj Simülasyonu
            st.subheader("🧪 Esnaf Yanıtı Simüle Et (Derya'nın Cevabını Test Et)")
            col1, col2 = st.columns([4, 1])
            
            with col1:
                esnaf_yazisi = st.text_input("Esnafın yazdığı mesajı buraya girin (Örn: Bu sistem ücretli mi?):", key="esnaf_input")
            
            with col2:
                st.write("") # Hizalama boşluğu
                st.write("")
                gonder_btn = st.button("📩 Mesajı Al & Derya Yanıtlasın", type="primary")
            
            if gonder_btn and esnaf_yazisi:
                # 1. Esnaf mesajını kaydet
                conn.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'ESNAF', ?)",
                             (secilen_esnaf["id"], esnaf_yazisi))
                conn.commit()
                
                # 2. Derya AI otonom yanıt üretsin
                derya_cevabi = derya_otonom_yanitla(esnaf_yazisi, secilen_esnaf["isletme"])
                
                # 3. Derya'nın yanıtını kaydet
                conn.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'DERYA', ?)",
                             (secilen_esnaf["id"], derya_cevabi))
                conn.commit()
                
                st.success("✅ Derya mesajı algıladı ve otonom yanıtını iletti!")
                st.rerun()

    conn.close()