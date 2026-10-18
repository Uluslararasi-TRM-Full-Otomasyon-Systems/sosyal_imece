#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Orchestrator API - Entegre Sürüm (Competitive Intelligence Eklendi)
Panel ile gerçek zamanlı log akışı ve Guardian Orchestrator entegrasyonu
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import json
import yaml
import logging
import time
import random
import threading
from pathlib import Path
from datetime import datetime, timedelta
from guardian_orchestrator import Orchestrator as GuardianOrchestrator
from database_manager import DatabaseManager
from auth_manager import AuthManager, require_auth, optional_auth
from behavioral_persona_agent import get_persona_agent, BehavioralPersonaAgent
from competitive_intelligence_agent import CompetitiveIntelligenceAgent  # ★ EKLENDİ
from market_signal_agent import MarketSignalAgent  # ★ YENİ EKLENDİ
from social_responsibility_agent import SocialResponsibilityAgent  # ★ YENİ EKLENDİ
from organic_warmup_agent import OrganicWarmupAgent  # ★ YENİ EKLENDİ
from nirvana_trends_agent import NirvanaTrendsAgent  # ★ YENİ EKLENDİ
from sales_alarm_bridge import SalesAlarmBridge  # ★ YENİ EKLENDİ

app = Flask(__name__)

# ============================================
# SQLITE DATABASE ENTEGRASYONU (Otomatik Oluşturma)
# ============================================
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'trm_ticari_analiz.db'

# Veritabanı otomatik oluşturma
import sqlite3
def init_database():
    """SQLite veritabanını otomatik oluştur ve tablaları hazırla"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ajanlar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            name TEXT,
            role TEXT,
            web TEXT,
            status TEXT,
            last_heartbeat TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # İstihbarat kayıtları tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intelligence_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            competitor_name TEXT,
            region TEXT,
            promotional_strategy TEXT,
            customer_reaction TEXT,
            dwell_time_seconds INTEGER,
            click_count INTEGER,
            success_score REAL,
            our_action_plan TEXT
        )
    ''')
    
    # Davranış analizi tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS behavior_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            product_id TEXT,
            category TEXT,
            click_count INTEGER,
            dwell_time_seconds INTEGER,
            region TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[OK] SQLite veritabanı oluşturuldu: {DB_PATH}")

init_database()
db = DatabaseManager()

# ============================================
# AUTHENTICATION ENTEGRASYONU
# ============================================
auth_manager = AuthManager()
DEFAULT_API_KEY = auth_manager.get_default_api_key()

# ============================================
# COMPETITIVE INTELLIGENCE AGENT ENTEGRASYONU
# ============================================
try:
    intelligence_agent = CompetitiveIntelligenceAgent()
    INTELLIGENCE_AGENT_ACTIVE = True
    print("[OK] Competitive Intelligence Agent başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Competitive Intelligence Agent entegrasyon hatası: {e}")
    intelligence_agent = None
    INTELLIGENCE_AGENT_ACTIVE = False

# ============================================
# MARKET SIGNAL AGENT ENTEGRASYONU (YENİ)
# ============================================
try:
    market_agent = MarketSignalAgent(use_simulation=True)
    MARKET_AGENT_ACTIVE = True
    print("[OK] Market Signal Agent başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Market Signal Agent entegrasyon hatası: {e}")
    market_agent = None
    MARKET_AGENT_ACTIVE = False

# ============================================
# SOCIAL RESPONSIBILITY AGENT ENTEGRASYONU (YENİ)
# ============================================
try:
    social_agent = SocialResponsibilityAgent()
    social_agent._initialize_projects()
    SOCIAL_AGENT_ACTIVE = True
    print("[OK] Social Responsibility Agent başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Social Responsibility Agent entegrasyon hatası: {e}")
    social_agent = None
    SOCIAL_AGENT_ACTIVE = False

# ============================================
# ORGANIC WARM-UP AGENT ENTEGRASYONU (YENİ)
# ============================================
try:
    warmup_agent = OrganicWarmupAgent()
    WARMUP_AGENT_ACTIVE = True
    print("[OK] Organic Warm-up Agent başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Organic Warm-up Agent entegrasyon hatası: {e}")
    warmup_agent = None
    WARMUP_AGENT_ACTIVE = False

# ============================================
# SALES ALARM BRIDGE ENTEGRASYONU (YENİ)
# ============================================
try:
    sales_alarm_bridge = SalesAlarmBridge()
    SALES_ALARM_ACTIVE = True
    print("[OK] Sales Alarm Bridge başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Sales Alarm Bridge entegrasyon hatası: {e}")
    sales_alarm_bridge = None
    SALES_ALARM_ACTIVE = False

# ============================================
# WEBSOCKET (SOCKET.IO) ENTEGRASYONU
# ============================================
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
connected_clients = 0

# ============================================
# GUARDIAN ORCHESTRATOR ENTEGRASYONU
# ============================================
try:
    config_file = Path(__file__).parent / "config" / "global_config.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        config_data.setdefault("sistem", {})["max_ajan_sayisi"] = 200
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    else:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "sistem": {
                "max_ajan_sayisi": 200,
                "log_klasoru": "./logs",
                "rapor_klasoru": "./reports"
            },
            "sunucu": {"host": "0.0.0.0", "port": 8080}
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
    
    guardian_orchestrator = GuardianOrchestrator()
    original_simulation = guardian_orchestrator.guardian.human_behavior_simulation
    guardian_orchestrator.guardian.human_behavior_simulation = lambda x: 0.0
    guardian_orchestrator.create_agents(200)
    guardian_orchestrator.guardian.human_behavior_simulation = original_simulation
    guardian_logger = guardian_orchestrator.logger
    GUARDIAN_ACTIVE = True
    print("[OK] Guardian Orchestrator başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Guardian Orchestrator entegrasyon hatası: {e}")
    guardian_orchestrator = None
    guardian_logger = None
    GUARDIAN_ACTIVE = False

# ============================================
# BEHAVIORAL & PERSONA AI AGENT ENTEGRASYONU
# ============================================
try:
    persona_agent = get_persona_agent()
    PERSONA_AGENT_ACTIVE = True

    def persona_update_callback(profile_data):
        try:
            socketio.emit('persona_update', {
                'type': 'new_persona_inference',
                'data': profile_data,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"[PersonaAI] WebSocket callback hatası: {e}")

    persona_agent.register_update_callback(persona_update_callback)
    print("[OK] Behavioral & Persona AI Agent başarıyla entegre edildi")
except Exception as e:
    print(f"[WARNING] Persona AI Agent entegrasyon hatası: {e}")
    persona_agent = None
    PERSONA_AGENT_ACTIVE = False

# ★★★ CORS GÜÇLÜ AYARLAR - file:// protokolü için ★★★
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
}, supports_credentials=True)

LOG_FILE = 'trm_orchestrator.log'
PANEL_FILE = 'TRM_EKOSISTEM_TICARI_KURESEL_BESLİ_KONTROL_PANELI.html'
SYSTEM_START_TIME = datetime.now()

# ============================================
# WEBSOCKET EVENT HANDLERS
# ============================================

@socketio.on('connect')
def handle_connect():
    global connected_clients
    connected_clients += 1
    print(f'[WebSocket] Client connected. Total clients: {connected_clients}')
    if GUARDIAN_ACTIVE and guardian_orchestrator:
        emit('initial_status', {
            'active_agents': db.get_active_agents_count(),
            'total_agents': db.get_total_agents_count(),
            'guardian_active': True,
            'uptime': get_system_uptime()
        })

@socketio.on('disconnect')
def handle_disconnect():
    global connected_clients
    connected_clients -= 1
    print(f'[WebSocket] Client disconnected. Total clients: {connected_clients}')

@socketio.on('request_status')
def handle_request_status():
    status_data = get_status_data()
    emit('status_update', status_data)

@socketio.on('request_agents')
def handle_request_agents():
    emit('agents_update', db.get_agents_dict())

@socketio.on('request_behavior_analytics')
def handle_request_behavior_analytics():
    if PERSONA_AGENT_ACTIVE and persona_agent:
        data = persona_agent.get_dashboard_data(limit=50)
        emit('behavior_analytics_update', {
            'type': 'full_dashboard',
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    else:
        emit('behavior_analytics_update', {
            'type': 'error',
            'message': 'Persona Agent aktif değil',
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('request_persona_distribution')
def handle_request_persona_distribution():
    data = db.get_behavior_persona_distribution()
    summary = db.get_behavior_summary_stats()
    emit('persona_distribution_update', {
        'distribution': data,
        'summary': summary,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('request_session_profile')
def handle_request_session_profile(data):
    session_id = data.get('session_id') if data else None
    if not session_id:
        emit('session_profile_update', {'error': 'session_id gerekli'})
        return
    if PERSONA_AGENT_ACTIVE and persona_agent:
        profile = persona_agent.get_session_details(session_id)
        emit('session_profile_update', {
            'session_id': session_id,
            'profile': profile,
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('track_interaction')
def handle_track_interaction(data):
    if not PERSONA_AGENT_ACTIVE or not persona_agent:
        emit('interaction_result', {'success': False, 'message': 'Persona Agent aktif değil'})
        return
    try:
        result = persona_agent.process_interaction(
            session_id=data.get('session_id'),
            product_id=data.get('product_id'),
            category=data.get('category'),
            click_count=data.get('click_count', 1),
            dwell_time_seconds=data.get('dwell_time_seconds', 0),
            region=data.get('region', 'yurtici')
        )
        emit('interaction_result', {
            'success': True,
            'profile': result
        })
    except Exception as e:
        emit('interaction_result', {'success': False, 'error': str(e)})

@socketio.on('toggle_simulation')
def handle_toggle_simulation(data):
    if not PERSONA_AGENT_ACTIVE or not persona_agent:
        emit('simulation_status', {'active': False, 'message': 'Persona Agent aktif değil'})
        return
    try:
        enable = data.get('enable', True) if data else True
        if enable:
            interval = data.get('interval_seconds', 2) if data else 2
            sessions = data.get('sessions_count', 15) if data else 15
            persona_agent.start_background_simulation(
                interval_seconds=interval,
                sessions_count=sessions
            )
            emit('simulation_status', {
                'active': True,
                'interval_seconds': interval,
                'sessions_count': sessions,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
        else:
            persona_agent.stop_background_simulation()
            emit('simulation_status', {
                'active': False,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
    except Exception as e:
        emit('simulation_status', {'active': False, 'error': str(e)})

# ============================================
# REAL-TIME VERİ YAYINLAMA FONKSİYONLARI
# ============================================

def get_status_data():
    tamamlanan_gorev = 0
    aktif_ajan = db.get_active_agents_count()
    total_agents = db.get_total_agents_count()
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = f.readlines()
            success_keywords = ['SUCCESS', 'COMPLETE', 'DONE', 'TAMAMLANDI', 'ISLEM', 'INFO']
            tamamlanan_gorev = sum(1 for line in logs if any(kw in line.upper() for kw in success_keywords))
    
    if GUARDIAN_ACTIVE and guardian_orchestrator:
        guardian_log_file = Path(__file__).parent / 'logs' / 'system.log'
        if guardian_log_file.exists():
            with open(guardian_log_file, 'r', encoding='utf-8') as f:
                guardian_logs = f.readlines()
                tamamlanan_gorev += sum(1 for line in guardian_logs if any(kw in line.upper() for kw in success_keywords))
    
    kazanc = tamamlanan_gorev * 150
    gelir = tamamlanan_gorev * 1250
    gider = tamamlanan_gorev * 350
    net_kar = gelir - gider
    satis = max(12, tamamlanan_gorev * 2)
    
    return {
        'status': 'running',
        'active_agents': aktif_ajan,
        'total_agents': total_agents,
        'uptime': get_system_uptime(),
        'last_update': datetime.now().isoformat(),
        'orchestrator_active': True,
        'guardian_active': GUARDIAN_ACTIVE,
        'toplam_kazanc': f'{kazanc:,} TL',
        'hedef_ulasma': f'%{min(12 + (tamamlanan_gorev * 2), 100)}',
        'satis_hacmi': str(satis),
        'gelir': f'{gelir:,} TL',
        'gider': f'{gider:,} TL',
        'net_kar': f'{net_kar:,} TL',
        'tamamlanan_gorev': str(tamamlanan_gorev),
        'dolar_kuru': '18.45',
        'euro_kuru': '19.78'
    }

def broadcast_status_update():
    while True:
        try:
            status_data = get_status_data()
            socketio.emit('status_update', status_data)
            time.sleep(3)
        except Exception as e:
            print(f'[WebSocket] Broadcast error: {e}')
            time.sleep(5)

def broadcast_agent_update():
    last_agents_state = None
    while True:
        try:
            current_agents = db.get_agents_dict()
            if current_agents != last_agents_state:
                socketio.emit('agents_update', current_agents)
                last_agents_state = current_agents
            time.sleep(5)
        except Exception as e:
            print(f'[WebSocket] Agent broadcast error: {e}')
            time.sleep(10)

def broadcast_log_update():
    last_log_size = 0
    while True:
        try:
            if os.path.exists(LOG_FILE):
                current_log_size = os.path.getsize(LOG_FILE)
                if current_log_size > last_log_size:
                    with open(LOG_FILE, 'r', encoding='utf-8') as f:
                        f.seek(last_log_size)
                        new_logs = f.readlines()
                        if new_logs:
                            socketio.emit('log_update', {'logs': [line.strip() for line in new_logs if line.strip()]})
                            last_log_size = current_log_size
            time.sleep(1)
        except Exception as e:
            print(f'[WebSocket] Log broadcast error: {e}')
            time.sleep(5)

def broadcast_behavior_analytics():
    while True:
        try:
            if PERSONA_AGENT_ACTIVE and persona_agent:
                summary = db.get_behavior_summary_stats()
                persona_dist = db.get_behavior_persona_distribution()
                recent = db.get_recent_behavior_with_personas(limit=30)
                socketio.emit('behavior_analytics_stream', {
                    'type': 'periodic_update',
                    'summary_stats': summary,
                    'persona_distribution': persona_dist,
                    'recent_activities': recent,
                    'persona_agent_active': PERSONA_AGENT_ACTIVE,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                socketio.emit('behavior_analytics_stream', {
                    'type': 'agent_inactive',
                    'persona_agent_active': False,
                    'timestamp': datetime.now().isoformat()
                })
            time.sleep(5)
        except Exception as e:
            print(f'[WebSocket] Behavior Analytics broadcast error: {e}')
            time.sleep(10)

# ============================================
# TEMEL FLASK ROUTE'LARI
# ============================================

@app.route('/')
@app.route('/panel')
def serve_panel():
    try:
        if os.path.exists(PANEL_FILE):
            return send_from_directory('.', PANEL_FILE)
        else:
            return jsonify({'error': 'Panel dosyası bulunamadı'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestrator-logs', methods=['GET'])
def get_orchestrator_logs():
    try:
        limit = request.args.get('limit', 50, type=int)
        if not os.path.exists(LOG_FILE):
            return jsonify([])
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            logs = [line.strip() for line in lines[-limit:] if line.strip()]
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orchestrator-status', methods=['GET'])
def get_orchestrator_status():
    try:
        active_agents = db.get_active_agents_count()
        total_agents = db.get_total_agents_count()
        uptime = get_system_uptime()
        return jsonify({
            'status': 'running',
            'active_agents': active_agents,
            'total_agents': total_agents,
            'uptime': uptime,
            'last_update': datetime.now().isoformat(),
            'guardian_active': GUARDIAN_ACTIVE
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        tamamlanan_gorev = 0
        aktif_ajan = db.get_active_agents_count()
        total_agents = db.get_total_agents_count()
        
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = f.readlines()
                success_keywords = ['SUCCESS', 'COMPLETE', 'DONE', 'TAMAMLANDI', 'ISLEM', 'INFO']
                tamamlanan_gorev = sum(1 for line in logs if any(kw in line.upper() for kw in success_keywords))
        
        if GUARDIAN_ACTIVE and guardian_orchestrator:
            guardian_log_file = Path(__file__).parent / 'logs' / 'system.log'
            if guardian_log_file.exists():
                with open(guardian_log_file, 'r', encoding='utf-8') as f:
                    guardian_logs = f.readlines()
                    tamamlanan_gorev += sum(1 for line in guardian_logs if any(kw in line.upper() for kw in success_keywords))
        
        kazanc = tamamlanan_gorev * 150
        gelir = tamamlanan_gorev * 1250
        gider = tamamlanan_gorev * 350
        net_kar = gelir - gider
        satis = max(12, tamamlanan_gorev * 2)
        
        return jsonify({
            'status': 'running',
            'active_agents': aktif_ajan,
            'total_agents': total_agents,
            'uptime': get_system_uptime(),
            'last_update': datetime.now().isoformat(),
            'orchestrator_active': True,
            'guardian_active': GUARDIAN_ACTIVE,
            'toplam_kazanc': f'{kazanc:,} TL',
            'hedef_ulasma': f'%{min(12 + (tamamlanan_gorev * 2), 100)}',
            'satis_hacmi': str(satis),
            'gelir': f'{gelir:,} TL',
            'gider': f'{gider:,} TL',
            'net_kar': f'{net_kar:,} TL',
            'tamamlanan_gorev': str(tamamlanan_gorev),
            'dolar_kuru': '18.45',
            'euro_kuru': '19.78'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
@require_auth(auth_manager)
def text_to_speech():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text parameter required'}), 400
        text = data['text']
        if guardian_logger:
            guardian_logger.info(f"🔊 TTS komutu: {text}")
        return jsonify({
            'status': 'success',
            'message': 'TTS komutu loglandı',
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'guardian_active': GUARDIAN_ACTIVE,
        'agents_loaded': db.get_total_agents_count(),
        'database_active': True,
        'intelligence_agent_active': INTELLIGENCE_AGENT_ACTIVE,
        'market_agent_active': MARKET_AGENT_ACTIVE,
        'social_agent_active': SOCIAL_AGENT_ACTIVE,
        'warmup_agent_active': WARMUP_AGENT_ACTIVE
    })

# ============================================
# ★ COMPETITIVE INTELLIGENCE API ENDPOINT'LERİ (YENİ)
# ============================================

@app.route('/api/intelligence/record', methods=['POST'])
def record_intelligence():
    """Dış mecralardaki rakip tanıtım stratejilerini ve müşteri tepkilerini kaydet"""
    try:
        if not INTELLIGENCE_AGENT_ACTIVE or not intelligence_agent:
            return jsonify({"success": False, "error": "Competitive Intelligence Agent aktif değil"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Geçersiz veya boş veri"}), 400
        
        result = intelligence_agent.record_competitor_move(
            competitor_name=data.get("competitor_name", "Bilinmeyen Rakip"),
            strategy=data.get("promotional_strategy", ""),
            reaction=data.get("customer_reaction", ""),
            score=data.get("success_score", 0.5),
            action_plan=data.get("our_action_plan", "")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/intelligence/summary', methods=['GET'])
def get_intelligence_summary_api():
    """Kaydedilen dış pazar istihbarat özetlerini listele"""
    try:
        if not INTELLIGENCE_AGENT_ACTIVE or not intelligence_agent:
            return jsonify({"success": False, "error": "Competitive Intelligence Agent aktif değil"}), 503
        
        records = intelligence_agent.get_intelligence_summary()
        return jsonify({"success": True, "data": records})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# ★ MARKET SIGNAL API ENDPOINT'LERİ (YENİ)
# ============================================

@app.route('/api/market/signals', methods=['GET'])
def get_market_signals():
    """Piyasa sinyallerini getir"""
    try:
        if not MARKET_AGENT_ACTIVE or not market_agent:
            return jsonify({"success": False, "error": "Market Signal Agent aktif değil"}), 503
        
        limit = request.args.get('limit', 20, type=int)
        signals = market_agent.get_all_signals(limit)
        return jsonify({"success": True, "data": signals})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/market/signals/summary', methods=['GET'])
def get_market_signals_summary():
    """Piyasa sinyalleri özetini getir"""
    try:
        if not MARKET_AGENT_ACTIVE or not market_agent:
            return jsonify({"success": False, "error": "Market Signal Agent aktif değil"}), 503
        
        summary = market_agent.get_signal_summary()
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/market/analyze', methods=['POST'])
def analyze_market_signal():
    """Belirli bir trading pair için piyasa analizi yap"""
    try:
        if not MARKET_AGENT_ACTIVE or not market_agent:
            return jsonify({"success": False, "error": "Market Signal Agent aktif değil"}), 503
        
        data = request.get_json()
        pair = data.get("pair", "BTCUSDT")
        signal = market_agent.analyze_market_signal(pair)
        
        if signal:
            return jsonify({"success": True, "data": signal})
        else:
            return jsonify({"success": False, "error": "Sinyal oluşturulamadı"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# ★ SOCIAL RESPONSIBILITY API ENDPOINT'LERİ (YENİ)
# ============================================

@app.route('/api/social/projects', methods=['GET'])
def get_social_projects():
    """Sosyal sorumluluk projelerini getir"""
    try:
        if not SOCIAL_AGENT_ACTIVE or not social_agent:
            return jsonify({"success": False, "error": "Social Responsibility Agent aktif değil"}), 503
        
        summary = social_agent.get_projects_summary()
        return jsonify({"success": True, "data": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/social/content', methods=['POST'])
def generate_social_content():
    """Sosyal sorumluluk içeriği üret"""
    try:
        if not SOCIAL_AGENT_ACTIVE or not social_agent:
            return jsonify({"success": False, "error": "Social Responsibility Agent aktif değil"}), 503
        
        data = request.get_json()
        project_id = data.get("project_id", "saglik_icin_elele")
        content_type = data.get("content_type", "social_media")
        platform = data.get("platform", "twitter")
        
        content = social_agent.generate_content(project_id, content_type, platform)
        
        if content:
            return jsonify({"success": True, "data": content})
        else:
            return jsonify({"success": False, "error": "İçerik oluşturulamadı"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/social/content/queue', methods=['GET'])
def get_social_content_queue():
    """Sosyal içerik kuyruğunu getir"""
    try:
        if not SOCIAL_AGENT_ACTIVE or not social_agent:
            return jsonify({"success": False, "error": "Social Responsibility Agent aktif değil"}), 503
        
        limit = request.args.get('limit', 20, type=int)
        queue = social_agent.get_content_queue(limit)
        return jsonify({"success": True, "data": queue})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/social/ecommerce/bridge', methods=['POST', 'GET'])
def create_ecommerce_bridge():
    """E-ticaret köprüsü oluştur (POST) veya durumunu getir (GET)"""
    try:
        if not SOCIAL_AGENT_ACTIVE or not social_agent:
            return jsonify({"success": False, "error": "Social Responsibility Agent aktif değil"}), 503
        
        if request.method == 'POST':
            data = request.get_json()
            project_id = data.get("project_id", "saglik_icin_elele")
            product_category = data.get("product_category", None)
            
            bridge = social_agent.create_ecommerce_bridge(project_id, product_category)
            
            if bridge:
                return jsonify({"success": True, "data": bridge})
            else:
                return jsonify({"success": False, "error": "Köprü oluşturulamadı"}), 500
        else:  # GET method
            project_id = request.args.get('project_id', None)
            analytics = social_agent.get_ecommerce_analytics(project_id)
            return jsonify({"success": True, "data": analytics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/social/ecommerce/analytics', methods=['GET'])
def get_ecommerce_analytics():
    """E-ticaret analitiğini getir"""
    try:
        if not SOCIAL_AGENT_ACTIVE or not social_agent:
            return jsonify({"success": False, "error": "Social Responsibility Agent aktif değil"}), 503
        
        project_id = request.args.get('project_id', None)
        analytics = social_agent.get_ecommerce_analytics(project_id)
        return jsonify({"success": True, "data": analytics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# ★ ORGANIC WARM-UP API ENDPOINT'LERİ (YENİ)
# ============================================

@app.route('/api/organic/warmup/status', methods=['GET'])
def get_warmup_status():
    """Warm-up fazı durumunu getir"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        status = warmup_agent.get_warmup_phase_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/organic/content/generate', methods=['POST'])
def generate_organic_content():
    """Organik içerik üret"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        data = request.get_json()
        category = data.get("category", "uteykder")
        format_type = data.get("format_type", "medium")
        platform = data.get("platform", "facebook")
        
        content = warmup_agent.generate_organic_content(category, format_type, platform)
        
        if content and "error" not in content:
            return jsonify({"success": True, "data": content})
        else:
            return jsonify({"success": False, "error": "İçerik oluşturulamadı"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/organic/content/queue', methods=['GET'])
def get_organic_content_queue():
    """Organik içerik kuyruğunu getir"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        platform = request.args.get('platform', None)
        limit = request.args.get('limit', 20, type=int)
        queue = warmup_agent.get_content_queue(platform, limit)
        return jsonify({"success": True, "data": queue})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/organic/content/batch', methods=['POST'])
def generate_batch_organic_content():
    """Toplu organik içerik üret"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        data = request.get_json()
        count = data.get("count", 10)
        
        batch = warmup_agent.generate_batch_content(count)
        return jsonify({"success": True, "data": batch})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/organic/content/publish', methods=['POST'])
def mark_organic_content_published():
    """İçeriği yayınlandı olarak işaretle"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        data = request.get_json()
        content_id = data.get("content_id")
        platform = data.get("platform", "facebook")
        
        if not content_id:
            return jsonify({"success": False, "error": "content_id gerekli"}), 400
        
        result = warmup_agent.mark_content_published(content_id, platform)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# ★ NIRVANA LEVEL API ENDPOINT'LERİ (YENİ)
# ============================================

@app.route('/api/nirvana/status', methods=['GET'])
def get_nirvana_status():
    """Nirvana modülleri durumunu getir"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        status = warmup_agent.get_nirvana_status()
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nirvana/trends', methods=['GET'])
def get_nirvana_trends():
    """Aktif trendleri getir"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        limit = request.args.get('limit', 20, type=int)
        trends = warmup_agent.nirvana_agent.get_active_trends(limit)
        return jsonify({"success": True, "data": trends})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nirvana/trends/simulate', methods=['POST'])
def simulate_trend_jacking():
    """Trend jacking simülasyonu"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        trend = warmup_agent.nirvana_agent.simulate_trend_jacking()
        
        if trend and "error" not in trend:
            return jsonify({"success": True, "data": trend})
        else:
            return jsonify({"success": False, "error": "Trend oluşturulamadı"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nirvana/visual/generate', methods=['POST'])
def generate_nirvana_visual():
    """Görsel/video medya üretimi"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        data = request.get_json()
        description = data.get("description", "Bilgilendirici içerik")
        visual_type = data.get("visual_type", "infographic")
        
        media = warmup_agent.nirvana_agent.generate_visual_media(description, visual_type)
        
        if media and "error" not in media:
            return jsonify({"success": True, "data": media})
        else:
            return jsonify({"success": False, "error": "Medya oluşturulamadı"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nirvana/engagement/simulate', methods=['POST'])
def simulate_nirvana_engagement():
    """Etkileşim simülasyonu"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        data = request.get_json()
        content_id = data.get("content_id", 1)
        platform = data.get("platform", "facebook")
        
        engagement = warmup_agent.nirvana_agent.simulate_engagement(content_id, platform)
        
        if engagement and "error" not in engagement:
            return jsonify({"success": True, "data": engagement})
        else:
            return jsonify({"success": False, "error": "Etkileşim oluşturulamadı"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nirvana/engagement/metrics', methods=['GET'])
def get_nirvana_engagement_metrics():
    """Etkileşim metriklerini getir"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        content_id = request.args.get('content_id', None)
        metrics = warmup_agent.nirvana_agent.get_engagement_metrics(content_id)
        return jsonify({"success": True, "data": metrics})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/nirvana/content/integrate-trend', methods=['POST'])
def integrate_trend_to_content():
    """Trend'i içeriğe entegre et"""
    try:
        if not WARMUP_AGENT_ACTIVE or not warmup_agent:
            return jsonify({"success": False, "error": "Organic Warm-up Agent aktif değil"}), 503
        
        data = request.get_json()
        trend_keyword = data.get("trend_keyword", "#SürdürülebilirGelecek")
        content_text = data.get("content_text", "")
        
        integrated_content = warmup_agent.nirvana_agent.integrate_trend_to_content(trend_keyword, content_text)
        
        return jsonify({"success": True, "data": {"integrated_content": integrated_content}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# YARDIMCI FONKSİYONLAR
# ============================================

def get_system_uptime():
    uptime = datetime.now() - SYSTEM_START_TIME
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{uptime.days}d {hours:02d}:{minutes:02d}:{seconds:02d}"

# ============================================
# GUARDIAN API ENDPOINT'LERİ
# ============================================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    try:
        return jsonify(db.get_agents_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/count', methods=['GET'])
def get_agent_count():
    try:
        active = db.get_active_agents_count()
        total = db.get_total_agents_count()
        return jsonify({
            "total": total,
            "active": active,
            "inactive": total - active
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/sync', methods=['POST'])
@require_auth(auth_manager)
def sync_agents():
    try:
        data = request.json
        target_count = data.get("max_ajan_sayisi", 200)
        db.set_max_agents(target_count)
        if guardian_logger:
            guardian_logger.info(f"✅ {target_count} ajan senkronize edildi")
        return jsonify({
            "success": True,
            "max_agents": target_count,
            "message": f"{target_count} ajan senkronize edildi"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/register', methods=['POST'])
@require_auth(auth_manager)
def register_agent():
    try:
        data = request.json
        agent_id = data.get("agent_id")
        agent_name = data.get("name", f"Agent-{agent_id:03d}")
        
        existing = db.get_agent_by_id(agent_id)
        if existing:
            agent_data = {
                "id": agent_id,
                "name": agent_name,
                "role": data.get("role", existing.get("role")),
                "web": data.get("web", existing.get("web")),
                "status": data.get("status", existing.get("status")),
                "last_heartbeat": datetime.now().isoformat()
            }
            db.insert_agent(agent_data)
        else:
            new_agent = {
                "id": agent_id,
                "name": agent_name,
                "role": data.get("role", "Standard Agent"),
                "web": data.get("web", "trendurunlermarket.com"),
                "status": data.get("status", "active"),
                "last_heartbeat": datetime.now().isoformat()
            }
            db.insert_agent(new_agent)
        
        if GUARDIAN_ACTIVE and guardian_orchestrator:
            guardian_orchestrator.guardian.record_operation(agent_id, "register")
        
        updated_agent = db.get_agent_by_id(agent_id)
        return jsonify({"success": True, "agent": updated_agent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/heal', methods=['POST'])
@require_auth(auth_manager)
def trigger_healing():
    try:
        data = request.json
        if guardian_logger:
            guardian_logger.info(f"🔧 Self-Healing tetiklendi: {data}")
        return jsonify({
            "success": True,
            "message": "Self-Healing başlatıldı"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# BEHAVIORAL & PERSONA AI API ENDPOINT'LERİ
# ============================================

@app.route('/api/behavior-analytics', methods=['GET'])
def get_behavior_analytics():
    try:
        limit = request.args.get('limit', 50, type=int)
        if PERSONA_AGENT_ACTIVE and persona_agent:
            data = persona_agent.get_dashboard_data(limit=limit)
            return jsonify({
                'success': True,
                'persona_agent_active': True,
                'data': data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            summary = db.get_behavior_summary_stats()
            persona_dist = db.get_behavior_persona_distribution()
            recent = db.get_recent_behavior_with_personas(limit=limit)
            return jsonify({
                'success': True,
                'persona_agent_active': False,
                'data': {
                    'summary_stats': summary,
                    'persona_distribution': persona_dist,
                    'recent_activities': recent
                },
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/behavior-analytics/track', methods=['POST'])
@optional_auth(auth_manager)
def track_behavior_interaction():
    try:
        if not PERSONA_AGENT_ACTIVE or not persona_agent:
            return jsonify({'success': False, 'message': 'Persona AI Agent aktif değil'}), 503
        data = request.get_json()
        if not data or 'session_id' not in data:
            return jsonify({'success': False, 'error': 'session_id gerekli'}), 400

        profile = persona_agent.process_interaction(
            session_id=data['session_id'],
            product_id=data.get('product_id'),
            category=data.get('category'),
            click_count=data.get('click_count', 1),
            dwell_time_seconds=data.get('dwell_time_seconds', 0),
            region=data.get('region', 'yurtici')
        )
        return jsonify({'success': True, 'profile': profile, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/behavior-analytics/persona-distribution', methods=['GET'])
def get_persona_distribution():
    try:
        distribution = db.get_behavior_persona_distribution()
        summary = db.get_behavior_summary_stats()
        return jsonify({'success': True, 'distribution': distribution, 'summary_stats': summary, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/behavior-analytics/summary', methods=['GET'])
def get_behavior_summary():
    try:
        stats = db.get_behavior_summary_stats()
        return jsonify({'success': True, 'summary': stats, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SİSTEM KONTROL PANELİ API'LERİ (HTML Panel Entegrasyonu)
# ============================================

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Sistem durumunu döndür - HTML panel için"""
    try:
        import psutil
        
        # Sistem metrikleri
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Veritabanı ajan sayısı
        total_agents = db.get_total_agents_count()
        active_agents = db.get_active_agents_count()
        
        # Watchdog durum dosyasını oku
        watchdog_status = {}
        try:
            with open('trm_watchdog_status.json', 'r', encoding='utf-8') as f:
                watchdog_status = json.load(f)
        except:
            pass
        
        return jsonify({
            'success': True,
            'system_status': 'running' if active_agents > 0 else 'idle',
            'active_agents': active_agents,
            'total_agents': total_agents,
            'cpu_load': cpu_percent,
            'memory_load': memory.percent,
            'disk_load': disk.percent,
            'watchdog_status': watchdog_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/start', methods=['POST'])
@require_auth(auth_manager)
def start_system():
    """Sistemi başlat - HTML panel butonu için"""
    try:
        # MASTER_CONTROLLER'ı başlat
        import subprocess
        import os
        
        # MASTER_CONTROLLER'ı arka planda başlat
        try:
            subprocess.Popen(['python', 'MASTER_CONTROLLER.py'], 
                           cwd=os.path.dirname(os.path.abspath(__file__)),
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0)
            
            return jsonify({
                'success': True,
                'message': 'Sistem başlatılıyor...',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'Sistem başlatılamadı: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/stop', methods=['POST'])
@require_auth(auth_manager)
def stop_system():
    """Sistemi durdur - HTML panel butonu için"""
    try:
        # MASTER_CONTROLLER süreçlerini bul ve durdur
        import psutil
        
        stopped_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'MASTER_CONTROLLER' in cmdline:
                        proc.terminate()
                        stopped_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return jsonify({
            'success': True,
            'message': f'{stopped_count} süreç durduruldu',
            'stopped_count': stopped_count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/metrics', methods=['GET'])
def get_system_metrics():
    """Gerçek zamanlı sistem metrikleri - HTML panel için"""
    try:
        import psutil
        
        # CPU, Memory, Disk
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Ajan durumu
        total_agents = db.get_total_agents_count()
        active_agents = db.get_active_agents_count()
        
        # Son loglar
        recent_logs = db.get_recent_logs(limit=10)
        
        return jsonify({
            'success': True,
            'metrics': {
                'cpu_load': cpu_percent,
                'memory_load': memory.percent,
                'disk_load': disk.percent,
                'active_agents': active_agents,
                'total_agents': total_agents,
                'agent_health': (active_agents / total_agents * 100) if total_agents > 0 else 0
            },
            'recent_logs': recent_logs,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ANA ÇALIŞTIRMA
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("TRM Orchestrator API (Nirvana Level - Tam Kapsamlı Üretim)")
    print("=" * 60)
    print(f"Guardian Orchestrator:         {'[OK] Aktif' if GUARDIAN_ACTIVE else '[FAIL] Pasif'}")
    print(f"Persona AI Agent:              {'[OK] Aktif' if PERSONA_AGENT_ACTIVE else '[FAIL] Pasif'}")
    print(f"Competitive Intelligence Agent: {'[OK] Aktif' if INTELLIGENCE_AGENT_ACTIVE else '[FAIL] Pasif'}")
    print(f"Market Signal Agent:           {'[OK] Aktif' if MARKET_AGENT_ACTIVE else '[FAIL] Pasif'}")
    print(f"Social Responsibility Agent:   {'[OK] Aktif' if SOCIAL_AGENT_ACTIVE else '[FAIL] Pasif'}")
    print(f"Organic Warm-up Agent:         {'[OK] Aktif' if WARMUP_AGENT_ACTIVE else '[FAIL] Pasif'}")
    print(f"  - Nirvana Trends Agent:     {'[OK] Aktif' if WARMUP_AGENT_ACTIVE else '[FAIL] Pasif'}")
    print(f"SQLite Database:               [OK] Aktif")
    print("=" * 60)
    print("Intelligence Record API:       http://localhost:5000/api/intelligence/record (POST)")
    print("Intelligence Summary API:      http://localhost:5000/api/intelligence/summary (GET)")
    print("Market Signals API:            http://localhost:5000/api/market/signals (GET)")
    print("Market Analysis API:           http://localhost:5000/api/market/analyze (POST)")
    print("Social Projects API:           http://localhost:5000/api/social/projects (GET)")
    print("Social Content API:            http://localhost:5000/api/social/content (POST)")
    print("E-commerce Bridge API:         http://localhost:5000/api/social/ecommerce/bridge (POST)")
    print("Organic Warm-up Status API:    http://localhost:5000/api/organic/warmup/status (GET)")
    print("Organic Content Queue API:     http://localhost:5000/api/organic/content/queue (GET)")
    print("Organic Content Generate API:  http://localhost:5000/api/organic/content/generate (POST)")
    print("=" * 60)
    print("* NIRVANA LEVEL FEATURES *")
    print("Nirvana Status API:            http://localhost:5000/api/nirvana/status (GET)")
    print("Trend Jacking API:             http://localhost:5000/api/nirvana/trends (GET)")
    print("Trend Simulation API:          http://localhost:5000/api/nirvana/trends/simulate (POST)")
    print("Visual Generation API:         http://localhost:5000/api/nirvana/visual/generate (POST)")
    print("Engagement Simulation API:     http://localhost:5000/api/nirvana/engagement/simulate (POST)")
    print("Engagement Metrics API:        http://localhost:5000/api/nirvana/engagement/metrics (GET)")
    print("Trend Integration API:        http://localhost:5000/api/nirvana/content/integrate-trend (POST)")
    print("=" * 60)
    
    # Arka plan izleme thread'leri
    status_thread = threading.Thread(target=broadcast_status_update, daemon=True)
    status_thread.start()
    agent_thread = threading.Thread(target=broadcast_agent_update, daemon=True)
    agent_thread.start()
    log_thread = threading.Thread(target=broadcast_log_update, daemon=True)
    log_thread.start()
    behavior_thread = threading.Thread(target=broadcast_behavior_analytics, daemon=True)
    behavior_thread.start()
    
    # Yeni ajanlar için arka plan izleme
    if MARKET_AGENT_ACTIVE and market_agent:
        market_thread = threading.Thread(target=market_agent.start_background_monitoring, args=(60,), daemon=True)
        market_thread.start()
        print("[Market Signal Agent] Arka plan izleme başlatıldı")
    
    if SOCIAL_AGENT_ACTIVE and social_agent:
        social_thread = threading.Thread(target=social_agent.start_background_content_generation, args=(120,), daemon=True)
        social_thread.start()
        print("[Social Responsibility Agent] Arka plan içerik üretimi başlatıldı")
    
    if WARMUP_AGENT_ACTIVE and warmup_agent:
        warmup_thread = threading.Thread(target=warmup_agent.start_background_content_generation, args=(180,), daemon=True)
        warmup_thread.start()
        print("[Organic Warm-up Agent] Arka plan içerik üretimi başlatıldı")
    
    print("=" * 60)
    print("Tüm modüller paralel ve 7/24 kesintisiz çalışmaya hazır.")
    print("Organik büyüme warm-up fazı aktif - ürün satışı yerine bilgilendirici içerikler.")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
# --- ŞEFKATLİ REHBER MÜLAKAT KÖPRÜSÜ ---
try:
    from sefkatli_rehber_agent import analyze_applicant_dialogue, ANAC_SELAMLAMA_SABLONLARI
    
    @app.route('/api/sefkatli-rehber/greet', methods=['GET'])
    def api_rehber_greet():
        return jsonify({
            "success": True,
            "persona": "Şefkatli Rehber (40-50 Yaş Anaç / Bilge Refah Rehberi)",
            "welcome_message": ANAC_SELAMLAMA_SABLONLARI[0]
        })

    @app.route('/api/sefkatli-rehber/interview', methods=['POST'])
    def api_rehber_interview():
        data = request.json or {}
        applicant_id = data.get('applicant_id', f'APL-{int(datetime.now().timestamp())}')
        candidate_text = data.get('text', '')
        region = data.get('region', 'Türkiye')
        
        result = analyze_applicant_dialogue(applicant_id, candidate_text, region)
        return jsonify({
            "success": True,
            "persona": "Şefkatli Rehber",
            "mülakat_sonucu": result
        })
    print("[OK] Şefkatli Rehber (Anaç Mülakat Agent) API köprüsü bağlandı")
except Exception as e:
    print(f"[INFO] Şefkatli Rehber modülü yükleme durumu: {e}")

# --- ŞEFKATLİ REHBER MÜLAKAT KÖPRÜSÜ ---
try:
    from sefkatli_rehber_agent import analyze_applicant_dialogue, ANAC_SELAMLAMA_SABLONLARI
    
    @app.route('/api/sefkatli-rehber/greet', methods=['GET'])
    def api_rehber_greet():
        return jsonify({
            "success": True,
            "persona": "Şefkatli Rehber (40-50 Yaş Anaç / Bilge Refah Rehberi)",
            "welcome_message": ANAC_SELAMLAMA_SABLONLARI[0]
        })

    @app.route('/api/sefkatli-rehber/interview', methods=['POST'])
    def api_rehber_interview():
        data = request.json or {}
        applicant_id = data.get('applicant_id', f'APL-{int(datetime.now().timestamp())}')
        candidate_text = data.get('text', '')
        region = data.get('region', 'Türkiye')
        
        result = analyze_applicant_dialogue(applicant_id, candidate_text, region)
        return jsonify({
            "success": True,
            "persona": "Şefkatli Rehber",
            "mülakat_sonucu": result
        })
    print("[OK] Şefkatli Rehber (Anaç Mülakat Agent) API köprüsü bağlandı")
except Exception as e:
    print(f"[INFO] Şefkatli Rehber modülü yükleme durumu: {e}")
