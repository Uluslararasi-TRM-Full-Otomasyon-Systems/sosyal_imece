import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)
# Tüm originlerden gelen isteklere izin ver (Geliştirme aşaması için)
CORS(app, resources={r"/ceo/*": {"origins": "*"}})

CEO_API_KEY = os.getenv("CEO_API_KEY")

def verify_ceo_key():
    """Gelen isteğin JSON veya Header gövdesindeki CEO anahtarını doğrular."""
    data = request.get_json(silent=True) or {}
    # İster JSON içinde 'ceo_key' olarak gelsin, ister Header'da 'X-CEO-Key' olarak
    ceo_key = data.get('ceo_key') or request.headers.get('X-CEO-Key')
    
    if not CEO_API_KEY:
        return False, jsonify({"status": "error", "message": "Sunucuda CEO_API_KEY tanımlı değil!"}), 500
        
    if not ceo_key or ceo_key != CEO_API_KEY:
        return False, jsonify({"status": "error", "message": "Geçersiz veya eksik CEO Anahtarı!"}), 401
        
    return True, None, None

@app.route('/', methods=['GET'])
def index():
    """Ana dizine girildiğinde 404 hatası vermek yerine sistemin çalıştığını gösterir."""
    return jsonify({
        "status": "online",
        "system": "Sosyal İmece Arka Uç Sistemi",
        "message": "Flask API sunucusu sorunsuz çalışıyor ve CEO paneli bağlantısını bekliyor."
    })

@app.route('/ceo/approve-login', methods=['POST'])
def ceo_approve_login():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
        
    data = request.json or {}
    user_id = data.get('user_id')
    
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) sisteme başarıyla eklendi/onaylandı."})

@app.route('/ceo/approve-passive', methods=['POST'])
def ceo_approve_passive():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
        
    data = request.json or {}
    user_id = data.get('user_id')
    
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) pasif durumda tutulmak üzere onaylandı."})

@app.route('/ceo/reject-login', methods=['POST'])
def ceo_reject_login():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
        
    data = request.json or {}
    user_id = data.get('user_id')
    
    return jsonify({"status": "success", "message": f"Kullanıcı ({user_id}) sistemden çıkarıldı/reddedildi."})

@app.route('/ceo/approve-all-pending', methods=['POST'])
def ceo_approve_all_pending():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
        
    return jsonify({"status": "success", "message": "Bekleyen tüm erişim talepleri onaylandı."})

@app.route('/ceo/close-all-sessions', methods=['POST'])
def ceo_close_all_sessions():
    is_valid, error_response, status_code = verify_ceo_key()
    if not is_valid:
        return error_response, status_code
        
    return jsonify({"status": "success", "message": "Tüm aktif oturumlar acil olarak kapatıldı."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)