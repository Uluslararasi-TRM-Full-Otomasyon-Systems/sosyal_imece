import streamlit as st
import json
import os

st.set_page_config(page_title="Sosyal İmece & IR-SA A.Ş. Kontrol Paneli", page_icon="🌐", layout="wide")

st.title("🌐 Sosyal İmece Ekosistemi - Canlı Yönetim ve Dağıtım Paneli")
st.markdown("---")

# Metrikler ve Özet Alanı
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Aktif Filo Hesabı", value="100", delta="6 Hesap / Kişi")
with col2:
    st.metric(label="Günlük Paylaşım Görevi", value="1,200", delta="%100 Otonom")
with col3:
    st.metric(label="IR-SA A.Ş. Payı (%70)", value="₺ 42,500", delta="Komisyon Geliri")
with col4:
    st.metric(label="İmece Havuzu (%30)", value="₺ 18,210", delta="Sosyal Adalet Fonu")

st.markdown("### 📊 İmece Havuz ve Emekli Dağıtım Durumu")

# Rapor Verisi Okuma Simülasyonu / Yükleme
report_path = "data/reports/daily_performance_report.json"
if os.path.exists(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)
    st.json(report_data)
else:
    st.info("Günlük performans raporu bekleniyor. Orchestrator çalıştırıldığında veriler buraya yansıyacaktır.")

st.markdown("---")
st.markdown("### 🗺️ İl Bazlı Yoksulluk Oranları & %20 İmece Refah Payı Matrisi")
provinces_data = [
    {"İl": "Ankara", "Yoksulluk Oranı (%)": 12.4, "Refah Payı Eklenen": "%20.0", "Durum": "Aktif Dağıtım"},
    {"İl": "İstanbul", "Yoksulluk Oranı (%)": 14.1, "Refah Payı Eklenen": "%20.0", "Durum": "Aktif Dağıtım"},
    {"İl": "İzmir", "Yoksulluk Oranı (%)": 11.8, "Refah Payı Eklenen": "%20.0", "Durum": "Aktif Dağıtım"},
    {"İl": "Hatay", "Yoksulluk Oranı (%)": 21.5, "Refah Payı Eklenen": "%20.0", "Durum": "Öncelikli Dağıtım"},
    {"İl": "Van", "Yoksulluk Oranı (%)": 26.2, "Refah Payı Eklenen": "%20.0", "Durum": "Öncelikli Dağıtım"}
]
st.table(provinces_data)

st.markdown("---")
st.markdown("**Sistem Kuralı:** İmece Havuzundaki kalan fonlar Türkiye'deki 55 yaş üzeri tüm emeklilere tam olarak pay edilir ve her ayın 02'sinde bakiye sıfırlanır.")
