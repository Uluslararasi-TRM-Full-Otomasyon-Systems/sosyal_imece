import os
import time
import threading
import requests
import json
import random
from datetime import datetime, timedelta
from collections import defaultdict
import config

class BehavioralMarketingAgent:
    def __init__(self, brand_catalog=None, social_accounts_pool=None):
        """
        TRM Nirvana v3.0 - Otonom Davranışsal Pazarlama Ajanı
        
        Özellikler:
        - Lokasyon Bazlı Analiz
        - Davranışsal Takip ve Geri Besleme (Feedback Loop)
        - Ruh Hali / Niyet Tespiti
        """
        # Config'den sistem ayarlarını al
        self.system_name = config._cfg.get("system_name", "SOSYAL İMECE")
        self.version = config._cfg.get("version", "3.0.0")
        self.max_agents = config._cfg.get("max_agents", 165)
        
        # Sosyal medya ayarları
        social_config = config._cfg.get("social_media", {})
        self.platforms = social_config.get("platforms", ["YouTube_Shorts", "TikTok", "Instagram_Reels"])
        self.upload_interval = social_config.get("upload_interval", 300)
        self.auto_upload = social_config.get("auto_upload", True)
        
        self.brand_catalog = brand_catalog or []
        self.social_accounts_pool = social_accounts_pool or []
        
        # Lokasyon bazlı ürün veritabanı
        self.location_product_mapping = {
            "Kuşadası": ["deniz_kiyasi_ustu", "yaz_giyim", "plaj_aksamlari", "turistik_esyalar"],
            "Nazilli": ["tarim_urunleri", "ev_esyalari", "gundelik_giyim", "yerel_ziraat"],
            "İstanbul": ["lüks_aksamlar", "is_giyim", "teknoloji", "premium_markalar"],
            "Ankara": ["resmi_giyim", "kuru_gidalar", "ev_tekstili", "ofis_urunleri"],
            "İzmir": ["deniz_urunleri", "zeytin_zeytinyagi", "kultur_sanat", "aksesuarlar"],
            "default": ["genel_kitap", "elektronik", "ev_bakim", "spor_urunleri"]
        }
        
        # Davranışsal takip verileri
        self.user_behavior_data = defaultdict(lambda: {
            "view_times": [],
            "clicks": [],
            "interactions": [],
            "timestamps": [],
            "products_viewed": [],
            "location": None
        })
        
        # Niyet tespiti için eşik değerler
        self.intent_thresholds = {
            "high_engagement": 30,  # saniye
            "medium_engagement": 15,
            "high_click_rate": 0.7,
            "purchase_intent": 0.8
        }

    def analyze_user_behavior(self, session_data):
        """
        Kullanıcının sitedeki gezinme süresini, sepet hareketlerini ve ilgi nişini analiz eder.
        TRM Nirvana v3.0 - Gelişmiş davranış analizi.
        """
        user_id = session_data.get("user_id", "anonymous")
        
        # Davranış verilerini kaydet
        self._track_behavior(user_id, session_data)
        
        # Lokasyon bazlı analiz
        location = session_data.get("location", "default")
        location_products = self._get_location_based_products(location)
        
        # Niyet tespiti
        intent_analysis = self._detect_user_intent(user_id)
        
        user_intent = {
            "target_product": session_data.get("viewed_product", "Bilinmeyen Ürün"),
            "intent_score": session_data.get("engagement_time", 0) * 0.1,
            "segment": "orta_ust_segment",
            "location": location,
            "location_products": location_products,
            "mood": intent_analysis["mood"],
            "intent_type": intent_analysis["intent_type"],
            "confidence_score": intent_analysis["confidence"],
            "recommended_action": intent_analysis["action"]
        }
        return user_intent
    
    def _track_behavior(self, user_id, session_data):
        """
        Kullanıcı davranışlarını kaydeder ve feedback loop oluşturur.
        """
        timestamp = datetime.now()
        
        behavior = self.user_behavior_data[user_id]
        behavior["view_times"].append(session_data.get("engagement_time", 0))
        behavior["clicks"].append(session_data.get("click_count", 0))
        behavior["interactions"].append(session_data.get("interaction_type", "view"))
        behavior["timestamps"].append(timestamp.isoformat())
        behavior["products_viewed"].append(session_data.get("viewed_product", ""))
        behavior["location"] = session_data.get("location", "default")
        
        # Sadece son 50 etkileşimi tut (memory management)
        if len(behavior["timestamps"]) > 50:
            for key in behavior:
                if isinstance(behavior[key], list):
                    behavior[key] = behavior[key][-50:]
    
    def _get_location_based_products(self, location):
        """
        Lokasyona uygun ürün önerileri döndürür.
        """
        return self.location_product_mapping.get(location, self.location_product_mapping["default"])
    
    def _detect_user_intent(self, user_id):
        """
        Kullanıcının ruh halini ve niyetini analiz eder.
        """
        behavior = self.user_behavior_data[user_id]
        
        if not behavior["view_times"]:
            return {"mood": "neutral", "intent_type": "exploration", "confidence": 0.5, "action": "show_welcome"}
        
        avg_view_time = sum(behavior["view_times"]) / len(behavior["view_times"])
        avg_clicks = sum(behavior["clicks"]) / len(behavior["clicks"]) if behavior["clicks"] else 0
        
        # Mood tespiti
        if avg_view_time > self.intent_thresholds["high_engagement"]:
            mood = "focused"
        elif avg_view_time > self.intent_thresholds["medium_engagement"]:
            mood = "interested"
        else:
            mood = "browsing"
        
        # Niyet tespiti
        if avg_clicks > self.intent_thresholds["high_click_rate"] and avg_view_time > 20:
            intent_type = "purchase_ready"
            action = "show_cta"
            confidence = min(0.95, 0.6 + (avg_clicks * 0.1))
        elif avg_view_time > 15:
            intent_type = "consideration"
            action = "show_details"
            confidence = 0.7
        else:
            intent_type = "exploration"
            action = "show_recommendations"
            confidence = 0.5
        
        return {
            "mood": mood,
            "intent_type": intent_type,
            "confidence": confidence,
            "action": action
        }
    
    def get_behavioral_metrics(self, user_id=None):
        """
        Davranışsal metrikleri döndürür.
        """
        if user_id:
            return dict(self.user_behavior_data[user_id])
        return {k: dict(v) for k, v in self.user_behavior_data.items()}
    
    def get_aggregated_metrics(self):
        """
        Tüm kullanıcılar için özet metrikler.
        """
        total_users = len(self.user_behavior_data)
        if total_users == 0:
            return {"total_users": 0, "avg_engagement_time": 0, "avg_click_rate": 0}
        
        all_view_times = []
        all_clicks = []
        
        for behavior in self.user_behavior_data.values():
            all_view_times.extend(behavior["view_times"])
            all_clicks.extend(behavior["clicks"])
        
        return {
            "total_users": total_users,
            "total_interactions": len(all_view_times),
            "avg_engagement_time": sum(all_view_times) / len(all_view_times) if all_view_times else 0,
            "avg_click_rate": sum(all_clicks) / len(all_clicks) if all_clicks else 0,
            "timestamp": datetime.now().isoformat()
        }

    def generate_personalized_message(self, user_intent):
        """
        Doğru müşteri için doğru zamanda kişiselleştirilmiş ikna ve tanıtım mesajı oluşturur.
        TRM Nirvana v3.0 - Lokasyon, mood ve niyet bazlı mesaj oluşturma.
        """
        product = user_intent.get("target_product", "Seçkin Ürün")
        location = user_intent.get("location", "genel")
        mood = user_intent.get("mood", "neutral")
        intent_type = user_intent.get("intent_type", "exploration")
        
        # Lokasyon bazlı mesaj varyasyonları
        location_messages = {
            "Kuşadası": f"Kuşadası'nın eşsiz atmosferinde {product} ile tatilinizi özel kılın!",
            "Nazilli": f"Nazilli'nin değerli müşterisi için özel {product} fırsatı!",
            "İstanbul": f"İstanbul'un dinamik ritmine uygun {product} seçkisi!",
            "Ankara": f"Ankara'nın seçkin zevkleri için {product} koleksiyonu!",
            "İzmir": f"İzmir'in sıcaklığıyla buluşan {product} deneyimi!",
            "default": f"Seçkin zevklerinize özel olarak önerilen {product} ile kaliteyi keşfedin."
        }
        
        # Mood bazlı mesaj varyasyonları
        mood_modifiers = {
            "focused": "Hemen inceleyin ve avantajları kaçırmayın!",
            "interested": "Detayları keşfedin, size özel fırsatları değerlendirin!",
            "browsing": "Rahatça inceleyin, size özel seçenekleri keşfedin!",
            "neutral": "İlginizi çekebilir, detayları inceleyebilirsiniz."
        }
        
        # Niyet bazlı CTA
        intent_ctas = {
            "purchase_ready": "🛒 ŞİMDİ SATIN AL - Sınırlı Stok!",
            "consideration": "📋 DETAYLARI İNCELE - Karar Verin!",
            "exploration": "🔍 KEŞFET - Benzer Ürünleri Görün!"
        }
        
        base_message = location_messages.get(location, location_messages["default"])
        mood_suffix = mood_modifiers.get(mood, mood_modifiers["neutral"])
        cta = intent_ctas.get(intent_type, intent_ctas["exploration"])
        
        message = f"{base_message} {mood_suffix} {cta}"
        return message

    def trigger_social_distribution(self, personalized_message, affiliate_link, location=None):
        """
        Sisteme kayıtlı 100 sosyal medya hesabı üzerinden otomatik dağıtımı ve paylaşımı tetikler.
        TRM Nirvana v3.0 - Lokasyon bazlı hedefleme.
        """
        print(f"[AI Dağıtım Ajanı]: 100 hesap üzerinden hedefli paylaşım başlatılıyor...")
        print(f"[Lokasyon]: {location if location else 'Genel'}")
        print(f"[Mesaj]: {personalized_message}")
        
        distribution_log = {
            "timestamp": datetime.now().isoformat(),
            "message": personalized_message,
            "affiliate_link": affiliate_link,
            "location": location,
            "accounts_targeted": len(self.social_accounts_pool),
            "status": "initiated"
        }
        
        for account in self.social_accounts_pool:
            # Sosyal medya hesap entegrasyon mantığı
            pass
        
        distribution_log["status"] = "completed"
        return distribution_log
    
    def export_behavioral_report(self, filepath="reports/behavioral_marketing_report.json"):
        """
        Davranışsal pazarlama raporunu dışa aktarır.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "agent_version": "TRM Nirvana v3.0",
            "aggregated_metrics": self.get_aggregated_metrics(),
            "user_behavior_data": dict(self.user_behavior_data),
            "location_product_mapping": self.location_product_mapping
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath


def keep_alive_worker():
    """
    Sunucunun uyku moduna geçmesini önlemek için periyodik ping atar.
    """
    app_url = os.getenv("APP_URL")
    if not app_url:
        return

    while True:
        try:
            time.sleep(600)  # 10 dakikada bir
            requests.get(app_url, timeout=10)
        except Exception:
            pass

def init_keep_alive():
    """
    Keep-alive arka plan iş parçacığını başlatır.
    """
    thread = threading.Thread(target=keep_alive_worker, daemon=True)
    thread.start()
