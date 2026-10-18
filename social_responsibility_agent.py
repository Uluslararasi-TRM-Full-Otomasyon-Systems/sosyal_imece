#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Social Responsibility Agent - Sosyal Sorumluluk & Toplum Ağları Entegrasyonu
- trendurunlermarket.com ve uteykder.org.tr projeleri için otomatik içerik üretimi
- "Sağlık İçin Elele", "Duy Algıla ve Farklı Yaşa" gibi projeler için trafik köprüsü
- trendurunlermarket.com e-ticaret akışı ile organik entegrasyon
"""

import json
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import time

class SocialResponsibilityAgent:
    def __init__(self, db_path="./data/trm_ticari_analiz.db"):
        self.db_path = Path(db_path)
        self.running = False
        self.thread = None
        self._init_database()
        
        # Sosyal sorumluluk projeleri
        self.projects = {
            "saglik_icin_elele": {
                "name": "Sağlık İçin Elele",
                "organization": "trendurunlermarket.com",
                "description": "Toplum sağlığı için farkındalık ve destek programı",
                "target_audience": ["gençler", "aileler", "sağlık çalışanları"],
                "keywords": ["sağlık", "farkındalık", "destek", "dayanışma"]
            },
            "duy_algila_farkli_yasa": {
                "name": "Duy Algıla ve Farklı Yaşa",
                "organization": "uteykder.org.tr",
                "description": "Engelli bireyler için sosyal entegrasyon projesi",
                "target_audience": ["engelli bireyler", "aileler", "öğretmenler"],
                "keywords": ["engellilik", "entegrasyon", "farkındalık", "eğitim"]
            },
            "cevre_dostu_refah": {
                "name": "Çevre Dostu Refah",
                "organization": "trendurunlermarket.com",
                "description": "Sürdürülebilir çevre için topluluk projesi",
                "target_audience": ["çevre bilinci", "gençler", "yerel topluluklar"],
                "keywords": ["çevre", "sürdürülebilirlik", "geri dönüşüm", "yeşil"]
            },
            "egitimde_firsat_esitligi": {
                "name": "Eğitimde Fırsat Eşitliği",
                "organization": "uteykder.org.tr",
                "description": "Her çocuk için eşit eğitim fırsatı",
                "target_audience": ["öğrenciler", "öğretmenler", "aileler"],
                "keywords": ["eğitim", "eşitlik", "fırsat", "kalkınma"]
            }
        }
        
        # E-ticaret entegrasyon ürün kategorileri
        self.ecommerce_categories = {
            "saglik": ["saglik_urunleri", "vitaminler", "spor_ekipmanlari"],
            "egitim": ["kitaplar", "egitim_materyalleri", "teknoloji_urunleri"],
            "cevre": ["cevre_dostu_urunler", "geri_donustum_urunleri", "organik_urunler"],
            "engellilik": ["ozel_ekipmanlar", "teknolojik_yardimcilar", "erisilebilir_urunler"]
        }
        
        # İçerik şablonları
        self.content_templates = {
            "social_media": [
                "{project_name} projesi ile {keyword} farkındalığı oluşturuyoruz! 🌟 {organization} #sosyalSorumluluk",
                "Birlikte daha güçlüyüz! {project_name} için {target_audience} ile dayanışma içindeyiz. 💪 #toplumDayanışması",
                "{description} kapsamında {keyword} çalışmalarımız devam ediyor. Katılın, fark yaratın! 🤝 #{organization}",
                "Her adım bir fark! {project_name} ile {keyword} alanında ilerliyoruz. 🚀 #sosyalEtki"
            ],
            "blog": [
                "{project_name}: {description} - Toplumsal etki yaratma yolculuğumuz",
                "{keyword} ve {target_audience}: {project_name} projesinden dersler",
                "{organization} bünyesinde {project_name} ile sosyal değişim nasıl oluyor?",
                "Sosyal sorumluluk bilinci: {project_name} projesinin başarı hikayeleri"
            ],
            "newsletter": [
                "📧 {project_name} Bülteni: {keyword} alanındaki son gelişmeler",
                "🎯 {organization} Haberleri: {project_name} projemizden güncellemeler",
                "💡 {project_name}: {description} - Bu ayın öne çıkan aktiviteleri"
            ]
        }
    
    def _init_database(self):
        """Sosyal sorumluluk projeleri için veritabanı tabloları"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    name TEXT,
                    organization TEXT,
                    description TEXT,
                    target_audience TEXT,
                    keywords TEXT,
                    status TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    content_type TEXT,
                    content_text TEXT,
                    platform TEXT,
                    status TEXT,
                    engagement_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ecommerce_integration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    product_category TEXT,
                    product_name TEXT,
                    traffic_source TEXT,
                    conversion_rate REAL,
                    revenue REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_impact_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    metric_type TEXT,
                    metric_value REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SocialResponsibilityAgent] Veritabanı hatası: {e}")
    
    def _initialize_projects(self):
        """Projeleri veritabanına yükle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for project_id, project_data in self.projects.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO social_projects 
                    (project_id, name, organization, description, target_audience, keywords, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id,
                    project_data["name"],
                    project_data["organization"],
                    project_data["description"],
                    json.dumps(project_data["target_audience"]),
                    json.dumps(project_data["keywords"]),
                    "active"
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SocialResponsibilityAgent] Proje yükleme hatası: {e}")
    
    def generate_content(self, project_id, content_type="social_media", platform="twitter"):
        """Otomatik içerik üretimi"""
        try:
            if project_id not in self.projects:
                return {"error": "Proje bulunamadı"}
            
            project = self.projects[project_id]
            templates = self.content_templates.get(content_type, self.content_templates["social_media"])
            template = random.choice(templates)
            
            # İçerik değişkenlerini doldur
            content_text = template.format(
                project_name=project["name"],
                organization=project["organization"],
                description=project["description"],
                target_audience=random.choice(project["target_audience"]),
                keyword=random.choice(project["keywords"])
            )
            
            content = {
                "project_id": project_id,
                "content_type": content_type,
                "content_text": content_text,
                "platform": platform,
                "status": "ready",
                "engagement_score": random.uniform(0.5, 0.95),
                "created_at": datetime.now().isoformat()
            }
            
            # Veritabanına kaydet
            self._save_content_to_db(content)
            
            return content
            
        except Exception as e:
            print(f"[SocialResponsibilityAgent] İçerik üretme hatası: {e}")
            return None
    
    def _save_content_to_db(self, content):
        """İçeriği veritabanına kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO social_content 
                (project_id, content_type, content_text, platform, status, engagement_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (content["project_id"], content["content_type"], content["content_text"],
                  content["platform"], content["status"], content["engagement_score"]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SocialResponsibilityAgent] İçerik kayıt hatası: {e}")
    
    def create_ecommerce_bridge(self, project_id, product_category=None):
        """E-ticaret entegrasyonu ve trafik köprüsü"""
        try:
            if project_id not in self.projects:
                return {"error": "Proje bulunamadı"}
            
            project = self.projects[project_id]
            
            # Proje anahtar kelimesine göre ürün kategorisi belirle
            if not product_category:
                main_keyword = project["keywords"][0]
                if main_keyword in ["sağlık", "farkındalık", "destek"]:
                    product_category = "saglik"
                elif main_keyword in ["eğitim", "eşitlik", "fırsat"]:
                    product_category = "egitim"
                elif main_keyword in ["çevre", "sürdürülebilirlik"]:
                    product_category = "cevre"
                else:
                    product_category = "engellilik"
            
            # Ürün seçimi
            products = self.ecommerce_categories.get(product_category, [])
            if not products:
                return {"error": "Ürün kategorisi bulunamadı"}
            
            product_name = random.choice(products)
            
            # Trafik kaynağı ve metrikler
            traffic_source = f"{project['organization']}/{project_id}"
            conversion_rate = random.uniform(0.02, 0.08)
            revenue = random.uniform(50, 500)
            
            integration = {
                "project_id": project_id,
                "product_category": product_category,
                "product_name": product_name,
                "traffic_source": traffic_source,
                "conversion_rate": round(conversion_rate, 4),
                "revenue": round(revenue, 2),
                "created_at": datetime.now().isoformat()
            }
            
            # Veritabanına kaydet
            self._save_ecommerce_integration_to_db(integration)
            
            return integration
            
        except Exception as e:
            print(f"[SocialResponsibilityAgent] E-ticaret entegrasyon hatası: {e}")
            return None
    
    def _save_ecommerce_integration_to_db(self, integration):
        """E-ticaret entegrasyonunu veritabanına kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ecommerce_integration 
                (project_id, product_category, product_name, traffic_source, conversion_rate, revenue)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (integration["project_id"], integration["product_category"], integration["product_name"],
                  integration["traffic_source"], integration["conversion_rate"], integration["revenue"]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SocialResponsibilityAgent] E-ticaret kayıt hatası: {e}")
    
    def record_impact_metric(self, project_id, metric_type, metric_value):
        """Sosyal etki metriği kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO social_impact_metrics (project_id, metric_type, metric_value)
                VALUES (?, ?, ?)
            ''', (project_id, metric_type, metric_value))
            conn.commit()
            conn.close()
            
            return {"success": True, "metric_type": metric_type, "value": metric_value}
        except Exception as e:
            print(f"[SocialResponsibilityAgent] Metrik kayıt hatası: {e}")
            return {"error": str(e)}
    
    def get_projects_summary(self):
        """Projeler özeti"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM social_projects WHERE status = "active"')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            projects = [dict(zip(columns, row)) for row in rows]
            conn.close()
            
            # Her proje için metrikleri topla
            for project in projects:
                project_id = project["project_id"]
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT metric_type, AVG(metric_value) as avg_value 
                    FROM social_impact_metrics 
                    WHERE project_id = ? 
                    GROUP BY metric_type
                ''', (project_id,))
                metrics = cursor.fetchall()
                project["metrics"] = {row[0]: round(row[1], 2) for row in metrics}
            
            return {
                "total_projects": len(projects),
                "projects": projects,
                "organizations": list(set(p["organization"] for p in projects))
            }
        except Exception as e:
            print(f"[SocialResponsibilityAgent] Proje özeti hatası: {e}")
            return {"error": str(e)}
    
    def get_content_queue(self, limit=20):
        """İçerik kuyruğu"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM social_content 
                WHERE status = "ready" 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            content_queue = [dict(zip(columns, row)) for row in rows]
            conn.close()
            
            return {
                "total_ready": len(content_queue),
                "content_queue": content_queue
            }
        except Exception as e:
            print(f"[SocialResponsibilityAgent] İçerik kuyruğu hatası: {e}")
            return {"error": str(e)}
    
    def get_ecommerce_analytics(self, project_id=None):
        """E-ticaret analitiği"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if project_id:
                cursor.execute('''
                    SELECT * FROM ecommerce_integration 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 50
                ''', (project_id,))
            else:
                cursor.execute('''
                    SELECT * FROM ecommerce_integration 
                    ORDER BY created_at DESC 
                    LIMIT 50
                ''')
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            integrations = [dict(zip(columns, row)) for row in rows]
            conn.close()
            
            # Özet metrikler
            total_revenue = sum(i["revenue"] for i in integrations)
            avg_conversion = sum(i["conversion_rate"] for i in integrations) / len(integrations) if integrations else 0
            
            return {
                "total_integrations": len(integrations),
                "total_revenue": round(total_revenue, 2),
                "average_conversion_rate": round(avg_conversion, 4),
                "integrations": integrations[:10]
            }
        except Exception as e:
            print(f"[SocialResponsibilityAgent] E-ticaret analitiği hatası: {e}")
            return {"error": str(e)}
    
    def start_background_content_generation(self, interval_seconds=120):
        """Arka planda sürekli içerik üretimi"""
        def generate():
            self.running = True
            while self.running:
                for project_id in self.projects.keys():
                    # İçerik üret
                    content = self.generate_content(project_id, "social_media", "twitter")
                    if content:
                        print(f"[SocialResponsibility] {project_id}: İçerik üretildi")
                    
                    # E-ticaret köprüsü oluştur
                    bridge = self.create_ecommerce_bridge(project_id)
                    if bridge:
                        print(f"[SocialResponsibility] {project_id}: E-ticaret köprüsü oluşturuldu")
                    
                    # Rastgele etki metriği kaydet
                    metric_types = ["reach", "engagement", "conversion", "donation"]
                    metric_type = random.choice(metric_types)
                    metric_value = random.uniform(10, 1000)
                    self.record_impact_metric(project_id, metric_type, metric_value)
                
                time.sleep(interval_seconds)
        
        if not self.running:
            self.thread = threading.Thread(target=generate, daemon=True)
            self.thread.start()
            print("[SocialResponsibilityAgent] Arka plan içerik üretimi başlatıldı")
    
    def stop_background_content_generation(self):
        """Arka plan içerik üretimini durdur"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("[SocialResponsibilityAgent] Arka plan içerik üretimi durduruldu")

if __name__ == "__main__":
    agent = SocialResponsibilityAgent()
    agent._initialize_projects()
    print("[OK] Social Responsibility Agent başlatıldı")
    
    # Test içerik üretimi
    content = agent.generate_content("saglik_icin_elele", "social_media", "twitter")
    print(f"Test İçeriği: {content}")
    
    # Test e-ticaret köprüsü
    bridge = agent.create_ecommerce_bridge("saglik_icin_elele")
    print(f"Test E-ticaret Köprüsü: {bridge}")
    
    # Proje özeti
    summary = agent.get_projects_summary()
    print(f"Proje Özeti: {summary}")
