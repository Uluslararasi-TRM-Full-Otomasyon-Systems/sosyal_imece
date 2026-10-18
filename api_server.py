from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from derya_cevaplayici import derya_otonom_yanitla

app = Flask(__name__)
CORS(app)  # HTML panelin API ile sorunsuz haberleşmesini sağlar

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

def veritabani_baglan():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Esnaf Listesi API (Çoklu kanal destekli güncel yapı)
@app.route('/api/esnaflar', methods=['GET'])
def get_esnaflar():
    conn = veritabani_baglan()
    # Tablonuzdaki sütunlara göre esnafları çekiyoruz
    cursor = conn.execute("SELECT id, isletme, telefon, kod, durum FROM esnaflar")
    rows = cursor.fetchall()
    conn.close()
    
    esnaflar_listesi = []
    for row in rows:
        esnaflar_listesi.append({
            "id": row["id"],
            "ad": row["isletme"],
            "kod": row["kod"],
            "telefon": row["telefon"],
            "durum": row["durum"] if "durum" in row.keys() else "onayli",
            "kanal": "whatsapp",  # Varsayılan kanal
            "son_mesaj": "Sistem aktif ✅",
            "online": True
        })
    
    return jsonify(esnaflar_listesi)

# 2. Mesaj Geçmişi API
@app.route('/api/mesajlar/<int:esnaf_id>', methods=['GET'])
def get_mesajlar(esnaf_id):
    conn = veritabani_baglan()
    mesajlar = conn.execute(
        "SELECT id, gonderen, mesaj, tarih FROM mesajlar WHERE esnaf_id = ? ORDER BY id ASC", 
        (esnaf_id,)
    ).fetchall()
    conn.close()
    
    formatli_mesajlar = []
    for m in mesajlar:
        # Giden/gelen yönü tablodaki gonderen bilgisine göre belirlenir
        yon = "out" if str(m["gonderen"]).upper() == "ESNAF" else "in"
        formatli_mesajlar.append({
            "id": m["id"],
            "yon": yon,
            "icerik": m["mesaj"],
            "zaman": m["tarih"]
        })
        
    return jsonify(formatli_mesajlar)

# 3. Mesaj Gönder & Derya Yanıtlasın API
@app.route('/api/mesaj_gonder', methods=['POST'])
def mesaj_gonder():
    data = request.json or {}
    esnaf_id = data.get('esnaf_id')
    esnaf_mesaj = data.get('mesaj')
    
    if not esnaf_id or not esnaf_mesaj:
        return jsonify({"status": "hata", "mesaj": "Eksik parametre"}), 400
    
    conn = veritabani_baglan()
    esnaf = conn.execute("SELECT isletme FROM esnaflar WHERE id = ?", (esnaf_id,)).fetchone()
    isletme_adi = esnaf["isletme"] if esnaf else "İşletme"
    
    # 1. Esnafın mesajını kaydet
    conn.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'ESNAF', ?)",
                 (esnaf_id, esnaf_mesaj))
    conn.commit()
    
    # 2. Derya Otonom Yanıt Üretsin
    derya_cevabi = derya_otonom_yanitla(esnaf_mesaj, isletme_adi)
    
    # 3. Derya'nın yanıtını kaydet
    conn.execute("INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'DERYA', ?)",
                 (esnaf_id, derya_cevabi))
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "basarili",
        "cevap": derya_cevabi,
        "yanit": derya_cevabi
    })

if __name__ == '__main__':
    print("🚀 TRM Eko Sistem Asistanı Derya API Servisi Başlatılıyor...")
    app.run(host='0.0.0.0', port=5000, debug=True)