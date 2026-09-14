# app.py - Sosyal İmece Tam Entegre Flask API Sunucusu
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from threading import Thread
import time
from ultra_nirvana_master import UltraNirvanaMasterSystem

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-CEO-Key"],
        "max_age": 3600
    }
}, supports_credentials=True)

CEO_API_KEY = os.getenv("CEO_API_KEY")

def verify_ceo_key():
    data = request.get_json(silent=True) or {}
    ceo_key = data.get('ceo_key') or request.headers.get('X-CEO-Key')
    
    if not CEO_API_KEY:
        return False, jsonify({"status": "error", "message": "Sunucuda CEO_API_KEY tanımlı değil!"}), 500
        
    if not ceo_key:
        return False, jsonify({"status": "error", "message": "CEO Anahtarı eksik!"}), 401
        
    if ceo_key != CEO_API_KEY:
        return False, jsonify({"status": "error", "message": "Geçersiz CEO Anahtarı!"}), 401
        
    return True, None, None

# --- ULTRA NIRVANA OTONOM ARKA PLAN DÖNGÜSÜ ---
def run_nirvana_background_loop():
    master_system = UltraNirvanaMasterSystem()
    while True:
        print(">>> [Background Daemon] Ultra Nirvana otonom döngüsü çalışıyor...")
        master_system.run_full_autonomous_cycle(account_id="hesap_otonom", region="US", target_lang="EN")
        # 1 saatlik döngü aralığı
        time.sleep(3600) 

def init_nirvana_daemon():
    t = Thread(target=run_nirvana_background_loop, daemon=True)
    t.start()
# ----------------------------------------------

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "system": "Sosyal İmece Arka Uç Sistemi - Ultra Nirvana Master & Engagement",
        "message": "Flask API sunucusu tam entegre modüllerle çalışıyor."
    })

@app.route('/ceo/run-cycle', methods=['POST'])
def ceo_run_cycle():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
        
    data = request.json or {}
    account_id = data.get('account_id', 'hesap_api')
    region = data.get('region', 'US')
    target_lang = data.get('target_lang', 'EN')
    
    master_system = UltraNirvanaMasterSystem()
    result = master_system.run_full_autonomous_cycle(account_id=account_id, region=region, target_lang=target_lang)
    
    return jsonify({"status": "success", "data": result})

@app.route('/ceo/approve-login', methods=['POST'])
def ceo_approve_login():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
    data = request.json or {}
    user_id = data.get('user_id')
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) sisteme başarıyla eklendi/onaylandı."})

@app.route('/ceo/reject-login', methods=['POST'])
def ceo_reject_login():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
    data = request.json or {}
    user_id = data.get('user_id')
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) sistemden çıkarıldı/reddedildi."})

@app.route('/ceo/passive-user', methods=['POST'])
def ceo_passive_user():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
    data = request.json or {}
    user_id = data.get('user_id')
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) pasif duruma alındı."})

@app.route('/ceo/force-logout', methods=['POST'])
def ceo_force_logout():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
    data = request.json or {}
    user_id = data.get('user_id')
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) oturumu sonlandırıldı."})

@app.route('/ceo/approve-all-pending', methods=['POST'])
def ceo_approve_all_pending():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
    # Demo: Rastgele sayı (gerçek sistemde veritabanından alınırdı)
    import random
    count = random.randint(5, 15)
    return jsonify({"status": "success", "message": f"Tüm bekleyen kullanıcılar onaylandı.", "count": count})

@app.route('/ceo/close-all-sessions', methods=['POST'])
def ceo_close_all_sessions():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
    # Demo: Rastgele sayı (gerçek sistemde veritabanından alınırdı)
    import random
    count = random.randint(10, 25)
    return jsonify({"status": "success", "message": f"Tüm aktif oturumlar kapatıldı.", "count": count})

if __name__ == '__main__':
    init_nirvana_daemon()
    app.run(host='0.0.0.0', port=5000, debug=True)
