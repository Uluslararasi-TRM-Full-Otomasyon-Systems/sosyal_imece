# trm_api_server.py
# TRM Ekosistem — Güvenlik + ParaPuan REST API (Flask)
# Çalıştır: python trm_api_server.py
import sqlite3
import os
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

app = Flask(__name__, static_folder=".")
CORS(app)

# ---------------------------------------------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_dict(rows):
    return [dict(r) for r in rows]

def init_db():
    """Sunucu başlarken tüm tabloların var olduğundan emin olur."""
    conn = db()
    cur = conn.cursor()
    
    # Esnaflar Tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS esnaflar(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ad TEXT, kod TEXT UNIQUE, durum TEXT DEFAULT 'TEMIZ',
          ihlal_sebebi TEXT, parapuan INTEGER DEFAULT 0,
          tespit_zamani TEXT, telefon TEXT, email TEXT
        )
    """)
    
    # İhlaller Tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ihlaller(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          esnaf_id INTEGER, esnaf_adi TEXT, tip TEXT, siddet TEXT,
          aciklama TEXT, zaman TEXT
        )
    """)
    
    # ParaPuan Tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parapuan(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          musteri_id TEXT, esnaf_id INTEGER, tip TEXT,
          puan INTEGER, bakiye INTEGER, zaman TEXT
        )
    """)
    
    conn.commit()
    conn.close()

# ---------------------------------------------------------------
# SAĞLIK
# ---------------------------------------------------------------
@app.route("/health")
def health():
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        conn.close()
        return jsonify({
            "status": "ok",
            "db": DB_PATH,
            "tables": tables,
            "time": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ===============================================================
# 🛡️ GÜVENLİK & KARA LİSTE
# ===============================================================
@app.route("/api/guvenlik/esnaflar")
def guvenlik_esnaflar():
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, ad, kod, durum, ihlal_sebebi AS sebep, parapuan, tespit_zamani FROM esnaflar ORDER BY durum DESC, id DESC")
        data = rows_to_dict(cur.fetchall())
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/guvenlik/ihlaller")
def guvenlik_ihlaller():
    limit = int(request.args.get("limit", 50))
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT id, esnaf_adi AS esnaf, tip, siddet, aciklama, zaman FROM ihlaller ORDER BY zaman DESC LIMIT ?", (limit,))
        data = rows_to_dict(cur.fetchall())
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/guvenlik/ozet")
def guvenlik_ozet():
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM esnaflar")
        total = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM esnaflar WHERE durum='KARA_LISTE'")
        bl = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM ihlaller")
        ih = cur.fetchone()[0] or 0
        conn.close()
        return jsonify({
            "blacklist": bl,
            "toplam_ihlal": ih,
            "denetlenen": total,
            "oran": round((bl / total) * 100, 1) if total else 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/guvenlik/af/<int:esnaf_id>", methods=["POST"])
def guvenlik_af(esnaf_id):
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("UPDATE esnaflar SET durum='TEMIZ', ihlal_sebebi='' WHERE id=?", (esnaf_id,))
        conn.commit()
        changed = cur.rowcount
        conn.close()
        if changed == 0:
            return jsonify({"error": "Esnaf bulunamadı"}), 404
        return jsonify({"status": "ok", "id": esnaf_id, "yeni_durum": "TEMIZ"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/guvenlik/incele/<int:esnaf_id>")
def guvenlik_incele(esnaf_id):
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM esnaflar WHERE id=?", (esnaf_id,))
        e = cur.fetchone()
        if not e:
            conn.close()
            return jsonify({"error": "Esnaf yok"}), 404
        e = dict(e)
        cur.execute("SELECT * FROM ihlaller WHERE esnaf_id=? ORDER BY zaman DESC", (esnaf_id,))
        e["ihlaller"] = rows_to_dict(cur.fetchall())
        conn.close()
        return jsonify(e)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================================================
# 💳 PARAPUAN HAVUZU
# ===============================================================
@app.route("/api/parapuan/ozet")
def parapuan_ozet():
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(bakiye),0) FROM (SELECT musteri_id, MAX(bakiye) AS bakiye FROM parapuan GROUP BY musteri_id)")
        toplam = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(DISTINCT musteri_id) FROM parapuan")
        musteri = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(DISTINCT esnaf_id) FROM parapuan")
        esnaf = cur.fetchone()[0] or 0
        cur.execute("SELECT COALESCE(SUM(ABS(puan)),0) FROM parapuan WHERE tip='ÇAPRAZ_TRANSFER' AND zaman >= datetime('now','-1 day')")
        gunluk = cur.fetchone()[0] or 0
        conn.close()
        return jsonify({
            "toplam_bakiye": toplam,
            "toplam_musteri": musteri,
            "katilimci_esnaf": esnaf,
            "gunluk_capraz": gunluk,
            "haftalik_delta": 5
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/parapuan/islemler")
def parapuan_islemler():
    limit = int(request.args.get("limit", 30))
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.zaman, p.musteri_id AS musteri, COALESCE(e.ad, 'Esnaf #' || p.esnaf_id) AS esnaf,
                   p.tip, p.puan, p.bakiye
            FROM parapuan p
            LEFT JOIN esnaflar e ON e.id = p.esnaf_id
            ORDER BY p.zaman DESC LIMIT ?
        """, (limit,))
        data = rows_to_dict(cur.fetchall())
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/parapuan/liderlik")
def parapuan_liderlik():
    limit = int(request.args.get("limit", 20))
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("""
            SELECT musteri_id AS musteri,
                   MAX(bakiye) AS bakiye,
                   MAX(zaman) AS son_islem
            FROM parapuan GROUP BY musteri_id
            ORDER BY bakiye DESC LIMIT ?
        """, (limit,))
        rows = rows_to_dict(cur.fetchall())
        for r in rows:
            r["ortak_havuz"] = 50
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===============================================================
if __name__ == "__main__":
    init_db()  # Tabloları uygulama ayağa kalkarken garantiye al
    print("=" * 60)
    print("🛡️  TRM Güvenlik + 💳 ParaPuan API Sunucusu")
    print(f"📍 DB: {DB_PATH}")
    print("🌐 http://localhost:5000/health")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)