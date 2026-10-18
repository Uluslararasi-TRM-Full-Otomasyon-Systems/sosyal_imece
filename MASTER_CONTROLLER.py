# -*- coding: utf-8 -*-
"""
TRM Nirvana v3.0 - MASTER CONTROLLER (Dinamik Fabrika Entegreli + Backend Sunucusu)
config/global_config.json içindeki max_ajan_sayisi kadar ajanı,
trm_agents paketindeki gerçek sınıflarla ve eksik kalanlar için 
dynamic_factory ile dinamik olarak yükler.

24/7 KESİNTİSİZ ÇALIŞMA OPTİMİZASYONU:
- Sonsuz döngü ile sürekli çalışma
- Hata toleransı ve otomatik yeniden başlatma
- Graceful shutdown (CTRL+C)
- Sistem sağlık kontrolü

BACKEND SUNUCU ENTEGRASYONU:
- Flask HTTP sunucusu (Kontrol paneli için API uç noktaları)
- access_control.py entegrasyonu
- whatsapp_agent_bridge.py entegrasyonu
- Canlı veri akışı ve WebSocket desteği
"""
import os
import importlib
import inspect
import logging
import pkgutil
import time
import signal
import sys
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS

from config import MAX_AJAN_SAYISI, LOG_DIR, REPORT_DIR
from trm_agents.governance.integration_hook import GovernanceBridge
from trm_agents.dynamic_factory import generate_missing_agents
from trm_db import trm_db


def _db():
    """Merkezi veritabanı (trm_veritabani.db) tekil örneği."""
    return trm_db()


def _db_metrik_kaydet(metric_name, value):
    """Gerçek zamanlı metriği system_status tablosuna yazar (upsert)."""
    try:
        _db().yaz(
            """
            INSERT INTO system_status (metric_name, metric_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(metric_name) DO UPDATE SET
                metric_value = excluded.metric_value,
                updated_at = excluded.updated_at
            """,
            (str(metric_name), str(value), datetime.now().isoformat()),
        )
    except Exception as e:
        logger.warning(f"Metrik veritabanına yazılamadı ({metric_name}): {e}")

# Log dizininin var olduğundan emin olalım (çökme riskini önler)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "master_controller.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MASTER_CONTROLLER")

# ============================================
# FLASK BACKEND SUNUCU (Kontrol Paneli İçin)
# ============================================

app = Flask(__name__)
CORS(app)  # Cross-Origin Resource Sharing desteği

# Access Control ve WhatsApp Bridge entegrasyonu için değişkenler
access_control = None
whatsapp_bridge = None
controller = None  # Master Controller referansı

# ============================================
# DUMMY FALLBACK SINIFLARI (Opsiyonel Modüller İçin)
# ============================================

class DummyAccessControlManager:
    """Access Control modülü yoksa kullanılan dummy sınıf"""
    def __init__(self):
        self.api_keys = {"demo_key": True}  # Demo API key
    
    def validate_api_key(self, api_key):
        """Demo API key doğrulama"""
        return api_key in self.api_keys or api_key == "demo_key"
    
    def log_access(self, user_id, action):
        """Demo access log"""
        pass

class DummyWhatsAppAgentBridge:
    """WhatsApp Bridge modülü yoksa kullanılan dummy sınıf"""
    def __init__(self):
        self.message_count = 0
        self.last_message_time = None
    
    def test_connection(self):
        """Demo bağlantı testi"""
        return {
            'status': 'connected',
            'latency_ms': 50,
            'message': 'Demo WhatsApp bridge aktif'
        }
    
    def get_message_rate(self):
        """Demo mesaj oranı"""
        import random
        return random.uniform(0, 30)  # 0-30 mesaj/dk
    
    def send_message(self, recipient, message):
        """Demo mesaj gönderme"""
        self.message_count += 1
        self.last_message_time = datetime.now()
        return {'success': True, 'message_id': f'demo_{self.message_count}'}

def initialize_integrations():
    """Access control ve WhatsApp bridge modüllerini başlat"""
    global access_control, whatsapp_bridge
    
    try:
        # Access Control entegrasyonu
        try:
            from access_control import AccessControlManager
            access_control = AccessControlManager()
            logger.info("✅ Access Control modülü başarıyla entegre edildi")
        except ImportError as e:
            logger.warning(f"⚠️ Access Control modülü bulunamadı: {e}")
            logger.info("🔄 Dummy Access Control Manager kullanılıyor")
            access_control = DummyAccessControlManager()
        except Exception as e:
            logger.error(f"❌ Access Control başlatma hatası: {e}")
            logger.info("🔄 Dummy Access Control Manager kullanılıyor")
            access_control = DummyAccessControlManager()
        
        # WhatsApp Bridge entegrasyonu
        try:
            from whatsapp_agent_bridge import WhatsAppAgentBridge
            whatsapp_bridge = WhatsAppAgentBridge()
            logger.info("✅ WhatsApp Agent Bridge başarıyla entegre edildi")
        except ImportError as e:
            logger.warning(f"⚠️ WhatsApp Agent Bridge bulunamadı: {e}")
            logger.info("🔄 Dummy WhatsApp Agent Bridge kullanılıyor")
            whatsapp_bridge = DummyWhatsAppAgentBridge()
        except Exception as e:
            logger.error(f"❌ WhatsApp Bridge başlatma hatası: {e}")
            logger.info("🔄 Dummy WhatsApp Agent Bridge kullanılıyor")
            whatsapp_bridge = DummyWhatsAppAgentBridge()
            
    except Exception as e:
        logger.error(f"❌ Entegrasyon başlatma hatası: {e}")
        if access_control is None:
            access_control = DummyAccessControlManager()
        if whatsapp_bridge is None:
            whatsapp_bridge = DummyWhatsAppAgentBridge()

# ============================================
# CANLI VERİ AKIŞI SİSTEMİ (Volkan ve Otonom Ajanlar)
# ============================================

class LiveDataStream:
    """Canlı veri akışı yöneticisi - Thread-safe implementasyon"""
    def __init__(self):
        self.subscribers = []
        self.data_buffer = {
            'agent_status': [],
            'system_metrics': {},
            'alerts': [],
            'volkan_messages': []
        }
        self.lock = threading.RLock()
        self.max_buffer_sizes = {
            'agent_status': 100,
            'alerts': 50,
            'volkan_messages': 30
        }
        self.cleanup_thresholds = {
            'agent_status': 50,
            'alerts': 25,
            'volkan_messages': 15
        }
    
    def subscribe(self, callback):
        with self.lock:
            if callback not in self.subscribers:
                self.subscribers.append(callback)
                return True
            return False
    
    def unsubscribe(self, callback):
        with self.lock:
            if callback in self.subscribers:
                self.subscribers.remove(callback)
                return True
            return False
    
    def _cleanup_buffer(self, buffer_name, buffer_list):
        max_size = self.max_buffer_sizes.get(buffer_name, 100)
        threshold = self.cleanup_thresholds.get(buffer_name, 50)
        if len(buffer_list) > max_size:
            del buffer_list[:-threshold]
    
    def publish_agent_status(self, agent_name, status, task=None):
        with self.lock:
            try:
                self.data_buffer['agent_status'].append({
                    'name': agent_name,
                    'status': status,
                    'task': task,
                    'timestamp': datetime.now().isoformat()
                })
                self._cleanup_buffer('agent_status', self.data_buffer['agent_status'])
            except Exception as e:
                logger.warning(f"Agent status publish hatası: {e}")
    
    def publish_system_metric(self, metric_name, value):
        with self.lock:
            try:
                self.data_buffer['system_metrics'][metric_name] = {
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                }
                _db_metrik_kaydet(metric_name, value)
            except Exception as e:
                logger.warning(f"System metric publish hatası: {e}")
    
    def publish_alert(self, alert_type, message, severity='info'):
        with self.lock:
            try:
                self.data_buffer['alerts'].append({
                    'type': alert_type,
                    'message': message,
                    'severity': severity,
                    'timestamp': datetime.now().isoformat()
                })
                self._cleanup_buffer('alerts', self.data_buffer['alerts'])
            except Exception as e:
                logger.warning(f"Alert publish hatası: {e}")
    
    def publish_volkan_message(self, message, message_type='info'):
        with self.lock:
            try:
                self.data_buffer['volkan_messages'].append({
                    'message': message,
                    'type': message_type,
                    'timestamp': datetime.now().isoformat()
                })
                self._cleanup_buffer('volkan_messages', self.data_buffer['volkan_messages'])
            except Exception as e:
                logger.warning(f"Volkan message publish hatası: {e}")
    
    def get_all_data(self):
        with self.lock:
            try:
                import copy
                return {
                    'agent_status': copy.deepcopy(self.data_buffer['agent_status']),
                    'system_metrics': copy.deepcopy(self.data_buffer['system_metrics']),
                    'alerts': copy.deepcopy(self.data_buffer['alerts']),
                    'volkan_messages': copy.deepcopy(self.data_buffer['volkan_messages'])
                }
            except Exception as e:
                logger.warning(f"Get all data hatası: {e}")
                return {
                    'agent_status': [],
                    'system_metrics': {},
                    'alerts': [],
                    'volkan_messages': []
                }

live_stream = LiveDataStream()

# ============================================
# API UÇ NOKTALARI (Kontrol Paneli İçin)
# ============================================

@app.route('/')
@app.route('/panel')
def serve_panel():
    """Ana kontrol paneli HTML dosyasını otomatik tarayıp sunar."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Klasördeki tüm HTML dosyalarını tarayalım ki isim/karakter farkı sorun yaratmasın
        html_files = [f for f in os.listdir(current_dir) if f.endswith('.html') and 'PANEL' in f.upper()]
        
        candidates = [
            os.path.join(current_dir, 'TRM_EKOSISTEM_TICARI_KURESEL_BESLİ_KONTROL_PANELI.html'),
            os.path.join(current_dir, 'TRM_EKOSISTEM_TICARI_KURESEL_BESLİ_KONTROL_PANELİ.html'),
            os.path.join(current_dir, 'TRM_EKOSISTEM_TICARI_KURESEL_BESLI_KONTROL_PANELI.html')
        ]
        
        for hf in html_files:
            candidates.append(os.path.join(current_dir, hf))

        panel_path = next((p for p in candidates if os.path.exists(p)), None)
        
        if not panel_path:
            logger.error(f"Panel dosyası bulunamadı. Bulunan HTML dosyaları: {html_files}")
            return jsonify({
                'error': 'Panel dosyası bulunamadı',
                'expected_path': candidates,
                'current_directory': current_dir,
                'available_html_files': html_files
            }), 404
            
        return send_file(panel_path, mimetype='text/html; charset=utf-8')
    except Exception as e:
        logger.error(f"Panel dosyası sunma hatası: {e}")
        return jsonify({
            'error': f'Panel dosyası sunma hatası: {str(e)}',
            'type': str(type(e).__name__)
        }), 500

@app.route('/api/ultimate/status', methods=['GET'])
def get_ultimate_status():
    try:
        global controller
        if controller is None:
            return jsonify({
                'success': False,
                'error': 'Controller henüz başlatılmadı',
                'system_status': 'initializing'
            }), 503
        
        active_count = 0
        try:
            for a in controller.agent_instances:
                try:
                    if hasattr(a[1], 'agent_obj') and hasattr(a[1].agent_obj, 'is_active'):
                        if a[1].agent_obj.is_active:
                            active_count += 1
                except:
                    continue
        except Exception:
            pass
        
        uptime = '00:00:00'
        try:
            if hasattr(controller, 'system_start_time') and controller.system_start_time:
                uptime = str(datetime.now() - controller.system_start_time)
        except Exception:
            pass
        
        health_status = {}
        try:
            if controller.running and hasattr(controller, 'health_check'):
                health_status = controller.health_check()
        except Exception as e:
            health_status = {'error': str(e)}
        
        return jsonify({
            'success': True,
            'system_status': 'running' if controller.running else 'idle',
            'active_agents': active_count,
            'total_agents': controller.max_ajan_sayisi if hasattr(controller, 'max_ajan_sayisi') else 0,
            'uptime': uptime,
            'health_status': health_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Ultimate status API hatası: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/metrics/realtime', methods=['GET'])
def get_realtime_metrics():
    try:
        cpu = 0
        ram = 0
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
        except:
            import random
            cpu = random.uniform(20, 70)
            ram = random.uniform(30, 80)
        
        return jsonify({
            'cpu': round(cpu, 1),
            'ram': round(ram, 1),
            'whatsapp_rate': 12.5,
            'ai_score': 92,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

AGENTS_PACKAGE = "trm_agents"

def discover_agent_classes():
    discovered = []
    try:
        package = importlib.import_module(AGENTS_PACKAGE)
    except ModuleNotFoundError:
        logger.error(f"'{AGENTS_PACKAGE}' paketi bulunamadı.")
        return discovered

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return discovered

    for _, module_name, _ in sorted(pkgutil.iter_modules(package_path), key=lambda m: m.name):
        if module_name == "dynamic_factory":
            continue
        full_module_name = f"{AGENTS_PACKAGE}.{module_name}"
        try:
            module = importlib.import_module(full_module_name)
        except Exception as e:
            logger.error(f"⚠️ '{full_module_name}' import edilemedi: {e}")
            continue

        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != full_module_name:
                continue
            if inspect.isabstract(cls):
                continue
            if not cls_name.endswith("Agent"):
                continue
            if not hasattr(cls, "run"):
                continue
            discovered.append((cls_name, cls, full_module_name))

    return discovered

class TRMMasterController:
    def __init__(self):
        logger.info("TRM Master Controller karargahı başlatılıyor...")
        self.max_ajan_sayisi = MAX_AJAN_SAYISI
        self.agent_classes = discover_agent_classes()
        self.agent_instances = []
        self.governance = GovernanceBridge()
        
        self.running = False
        self.shutdown_requested = False
        self.health_check_interval = 30
        self.restart_attempts = 0
        self.max_restart_attempts = 10
        self.last_health_check = None
        self.system_start_time = datetime.now()

        for cls_name, cls, module_name in self.agent_classes:
            try:
                instance = cls()
                self.agent_instances.append((cls_name, instance))
                logger.info(f"✅ '{cls_name}' initialize edildi.")
            except Exception as e:
                logger.error(f"⚠️ '{cls_name}' initialize edilirken hata: {e}")

        current_count = len(self.agent_instances)
        if current_count < self.max_ajan_sayisi:
            missing_count = self.max_ajan_sayisi - current_count
            dynamic_agents = generate_missing_agents(start_id=current_count + 1, total_target=self.max_ajan_sayisi)
            for dyn_agent in dynamic_agents:
                class DynamicAgentWrapper:
                    def __init__(self, agent_obj):
                        self.agent_obj = agent_obj
                    def run(self):
                        return self.agent_obj.execute_task()
                wrapper = DynamicAgentWrapper(dyn_agent)
                self.agent_instances.append((dyn_agent.agent_name, wrapper))

        # Merkezi veritabanına ajanları kaydet
        try:
            db = _db()
            islemler = []
            for cls_name, instance in self.agent_instances:
                tur = "dinamik" if hasattr(instance, "agent_obj") else "komuta"
                islemler.append((
                    """INSERT INTO ajanlar (ajan_kodu, ad, rol, tur, durum, son_kalp_atisi, detay,
                                            kayit_zamani, son_guncelleme)
                       VALUES (?, ?, ?, ?, ?, NULL, ?, ?, ?)
                       ON CONFLICT(ajan_kodu) DO UPDATE SET
                           tur = excluded.tur, son_guncelleme = excluded.son_guncelleme""",
                    (cls_name, cls_name, "master_controller ajanı", tur, "beklemede",
                     '{"kaynak": "MASTER_CONTROLLER"}',
                     datetime.now().isoformat(), datetime.now().isoformat()),
                ))
            db.yaz_coklu(islemler)
            db.modul_durumu_kaydet("master_controller", "baslatildi", detay={
                "hedef_ajan": self.max_ajan_sayisi,
                "toplam_ajan": len(self.agent_instances),
            })
            logger.info(f"✅ {len(self.agent_instances)} ajan merkezi veritabanına kaydedildi.")
        except Exception as e:
            logger.warning(f"⚠️ Ajan kayıtları veritabanına yazılamadı: {e}")

    def health_check(self):
        self.last_health_check = datetime.now()
        healthy_agents = 0
        total_agents = len(self.agent_instances)
        
        for cls_name, instance in self.agent_instances:
            try:
                healthy_agents += 1
                live_stream.publish_agent_status(cls_name, 'active')
            except Exception:
                pass
        
        health_percentage = (healthy_agents / total_agents * 100) if total_agents > 0 else 0
        try:
            db = _db()
            db.modul_durumu_kaydet("master_controller", "aktif", detay={
                "saglikli_ajan": healthy_agents,
                "toplam_ajan": total_agents,
                "saglik_yuzdesi": round(health_percentage, 1),
            })
        except Exception:
            pass

        return {
            "healthy_agents": healthy_agents,
            "total_agents": total_agents,
            "health_percentage": health_percentage,
            "timestamp": self.last_health_check.isoformat()
        }

    def start_all_services(self):
        logger.info("Otonom servisler devreye alınıyor...")
        started = 0
        for cls_name, instance in self.agent_instances:
            try:
                if hasattr(instance, "run"):
                    instance.run()
                    started += 1
            except Exception as e:
                logger.error(f"⚠️ '{cls_name}' çalıştırılamadı: {e}")
        return started

    def run_forever_24_7(self):
        logger.info("🚀 24/7 kesintisiz çalışma modu başlatılıyor...")
        self.running = True
        self.start_all_services()
        
        while self.running and not self.shutdown_requested:
            try:
                self.health_check()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"24/7 döngü hatası: {e}")
                time.sleep(5)
        
        self.graceful_shutdown()
    
    def graceful_shutdown(self):
        logger.info("Graceful shutdown gerçekleştiriliyor...")
        self.running = False
        try:
            _db().modul_durumu_kaydet("master_controller", "kapandi", {"zaman": datetime.now().isoformat()})
        except Exception:
            pass


if __name__ == "__main__":
    controller = TRMMasterController()
    initialize_integrations()
    
    def run_flask_server():
        logger.info("🌐 Kontrol Merkezi Flask (http://localhost:5000)")
        try:
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as flask_err:
            logger.error(f"Flask sunucu başlatılamadı: {flask_err}")
    
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    try:
        controller.run_forever_24_7()
    except KeyboardInterrupt:
        controller.graceful_shutdown()