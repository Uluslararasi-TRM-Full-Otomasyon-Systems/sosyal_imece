#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Organic Growth & Warm-up Phase Agent
- Yeni sosyal medya hesapları için organik büyüme stratejisi
- Ürün satışı yerine bilgilendirici içerikler
- UTEYKDER projeleri, çevre, yaşam kalitesi ve Endeksa verilerine dayalı içerikler
- Facebook, Instagram, TikTok, Telegram, YouTube, Blog için içerik kuyruğu
"""

import json
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import threading
import time
from nirvana_trends_agent import NirvanaTrendsAgent

class OrganicWarmupAgent:
    def __init__(self, db_path="./data/trm_ticari_analiz.db"):
        self.db_path = Path(db_path)
        self.running = False
        self.thread = None
        self._init_database()
        
        # Nirvana modülleri entegrasyonu
        self.nirvana_agent = NirvanaTrendsAgent(db_path)
        self.nirvana_enabled = True
        
        # Platformlar
        self.platforms = ["facebook", "instagram", "tiktok", "telegram", "youtube", "blog"]
        
        # İçerik kategorileri
        self.content_categories = {
            "uteykder": {
                "name": "UTEYKDER Projeleri",
                "topics": [
                    "Sağlık İçin Elele projesi ile toplum sağlığı farkındalığı",
                    "Duy Algıla ve Farklı Yaşa engelli bireyler için sosyal entegrasyon",
                    "Eğitimde Fırsat Eşitliği ile her çocuk için eşit başlangıç",
                    "Gençlik Saha Koçluğu ile geleceğin liderlerini yetiştirme",
                    "Kadın Güçlenmesi programları ve toplumsal cinsiyet eşitliği"
                ],
                "hashtags": ["#UTEYKDER", "#SosyalSorumluluk", "#ToplumDayanışması", "#Eğitim", "#Sağlık"]
            },
            "cevre": {
                "name": "Çevre ve Sürdürülebilirlik",
                "topics": [
                    "Sıfır atık yaşam tarzı ve pratik ipuçları",
                    "Geri dönüşümün önemi ve doğaya katkı",
                    "Yeşil enerji transition ve yenilenebilir kaynaklar",
                    "İklim değişikliği ile mücadele bireysel adımlar",
                    "Organik tarım ve yerel üretici desteği"
                ],
                "hashtags": ["#Çevre", "#Sürdürülebilirlik", "#YeşilYaşam", "#GeriDönüşüm", "#İklimDeğişikliği"]
            },
            "yasam_kalitesi": {
                "name": "Yaşam Kalitesi",
                "topics": [
                    "Dengeli beslenme ve sağlıklı yaşam alışkanlıkları",
                    "Stres yönetimi ve mental sağlık farkındalığı",
                    "Ergonomik çalışma ortamı ve verimlilik",
                    "Düzenli egzersiz ve fiziksel aktivite önemi",
                    "Kaliteli uyku ve yaşam döngüsü optimizasyonu"
                ],
                "hashtags": ["#YaşamKalitesi", "#SağlıklıYaşam", "#MentalSağlık", "#Denge", "#BilinçliTüketim"]
            },
            "endeksa": {
                "name": "Endeksa Veri Analizleri",
                "topics": [
                    "Konut fiyatları trendleri ve piyasa analizi",
                    "Bölgesel gayrimenkul yatırım fırsatları",
                    "Kira artış oranları ve sektörel etkiler",
                    "İnşaat sektörü göstergeleri ve öngörüler",
                    "Şehirleşme dinamikleri ve altyapı yatırımları"
                ],
                "hashtags": ["#Endeksa", "#Gayrimenkul", "#PiyasaAnalizi", "#Yatırım", "#Ekonomi"]
            }
        }
        
        # İçerik formatları
        self.content_formats = {
            "short": {"length": 50, "emoji_count": 2},
            "medium": {"length": 150, "emoji_count": 3},
            "long": {"length": 300, "emoji_count": 4}
        }
        
        # Görsel açıklamaları
        self.image_descriptions = {
            "infographic": "Bilgilendirici infografik",
            "photo": "İlham verici fotoğraf",
            "quote": "Motivasyon alıntısı görseli",
            "data_chart": "Veri görselleştirmesi",
            "illustration": "Özgül illüstrasyon"
        }
    
    def _init_database(self):
        """Organik büyüme için veritabanı tabloları"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organic_content_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    content_category TEXT,
                    content_format TEXT,
                    content_text TEXT,
                    hashtags TEXT,
                    image_description TEXT,
                    status TEXT,
                    scheduled_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organic_growth_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    content_category TEXT,
                    engagement_rate REAL,
                    reach_count INTEGER,
                    interaction_count INTEGER,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warmup_phase_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phase TEXT,
                    action TEXT,
                    platform TEXT,
                    result TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[OrganicWarmupAgent] Veritabanı hatası: {e}")
    
    def generate_organic_content(self, category: str, format_type: str = "medium", platform: str = "facebook") -> Dict:
        """Organik içerik üret (Nirvana entegrasyonlu)"""
        try:
            if category not in self.content_categories:
                return {"error": "Kategori bulunamadı"}
            
            cat_data = self.content_categories[category]
            format_data = self.content_formats.get(format_type, self.content_formats["medium"])
            
            # Konu seç
            topic = random.choice(cat_data["topics"])
            
            # İçerik oluştur
            content_text = self._create_content_text(topic, format_data)
            
            # Nirvana: Trend Jacking entegrasyonu
            if self.nirvana_enabled and random.random() < 0.3:  # %30 ihtimalle trend ekle
                active_trends = self.nirvana_agent.get_active_trends(3)
                if "error" not in active_trends and active_trends["trends"]:
                    trend = random.choice(active_trends["trends"])
                    content_text = self.nirvana_agent.integrate_trend_to_content(
                        trend["trend_keyword"], content_text
                    )
            
            # Hashtag'leri ekle
            hashtags = " ".join(random.sample(cat_data["hashtags"], min(3, len(cat_data["hashtags"]))))
            
            # Görsel açıklaması
            image_desc = random.choice(list(self.image_descriptions.values()))
            
            # Nirvana: Görsel/Video üretimi
            generated_media_url = None
            if self.nirvana_enabled:
                visual_type = "infographic" if platform in ["facebook", "instagram"] else "short_video"
                media_result = self.nirvana_agent.generate_visual_media(image_desc, visual_type)
                if "error" not in media_result:
                    generated_media_url = media_result.get("generated_media_url")
            
            # Platform bazlı optimizasyon
            content_text = self._optimize_for_platform(content_text, platform)
            
            content = {
                "platform": platform,
                "content_category": category,
                "content_format": format_type,
                "content_text": content_text,
                "hashtags": hashtags,
                "image_description": image_desc,
                "generated_media_url": generated_media_url,
                "status": "ready",
                "scheduled_time": (datetime.now() + timedelta(minutes=random.randint(5, 30))).isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            # Veritabanına kaydet
            self._save_content_to_queue(content)
            
            return content
            
        except Exception as e:
            print(f"[OrganicWarmupAgent] İçerik üretme hatası: {e}")
            return {"error": str(e)}
    
    def _create_content_text(self, topic: str, format_data: Dict) -> str:
        """İçerik metni oluştur"""
        # Emoji'ler
        emojis = ["🌱", "🌍", "💚", "📊", "🎯", "💡", "🚀", "⭐", "🔥", "💪"]
        selected_emojis = random.sample(emojis, min(format_data["emoji_count"], len(emojis)))
        emoji_string = " ".join(selected_emojis)
        
        # İçerik yapısı
        content = f"{emoji_string}\n\n{topic}\n\n"
        
        # Uzatma (uzun format için)
        if format_data["length"] > 100:
            extensions = [
                "Bu konuda neler düşünüyorsunuz? Yorumlarınızı bekliyoruz!",
                "Deneyimlerinizi paylaşarak topluluğumuzu zenginleştirin.",
                "Birlikte öğrenip büyüyoruz! 💪",
                "Siz de bu konuda ne yapıyorsunuz? Anlatın!",
                "Fikirlerinizi ve önerilerinizi duymak isteriz."
            ]
            content += random.choice(extensions) + "\n\n"
        
        # Etkileşim çağrısı
        ctas = [
            "👇 Yorumlarda buluşalım!",
            "💬 Düşünceleriniz neler?",
            "🤝 Deneyimlerinizi paylaşın",
            "📢 Bu mesajı paylaşın!"
        ]
        content += random.choice(ctas)
        
        return content
    
    def _optimize_for_platform(self, content: str, platform: str) -> str:
        """Platform bazlı içerik optimizasyonu"""
        if platform == "tiktok":
            # TikTok için daha kısa ve enerjik
            lines = content.split("\n")
            content = "\n".join(lines[:5]) + "\n\n#fyp #viral"
        elif platform == "twitter":
            # Twitter için karakter limiti
            if len(content) > 277:
                content = content[:277] + "..."
        elif platform == "instagram":
            # Instagram için daha görsel odaklı
            content = content + "\n\n📸 İçeriğimizi beğenmeyi unutmayın!"
        elif platform == "youtube":
            # YouTube için daha detaylı
            content = content + "\n\n🔔 Abone olup bildirimleri açmayı unutmayın!"
        elif platform == "telegram":
            # Telegram için daha bilgilendirici
            content = content + "\n\n📱 Kanalımızı takip edin!"
        elif platform == "blog":
            # Blog için daha uzun ve detaylı
            content = content + "\n\nDevamı için blogumuzu ziyaret edin."
        
        return content
    
    def _save_content_to_queue(self, content: Dict):
        """İçeriği kuyruğa kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO organic_content_queue 
                (platform, content_category, content_format, content_text, hashtags, image_description, status, scheduled_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (content["platform"], content["content_category"], content["content_format"],
                  content["content_text"], content["hashtags"], content["image_description"],
                  content["status"], content["scheduled_time"]))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[OrganicWarmupAgent] Kuyruk kayıt hatası: {e}")
    
    def get_content_queue(self, platform: str = None, limit: int = 20) -> Dict:
        """İçerik kuyruğunu getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if platform:
                cursor.execute('''
                    SELECT * FROM organic_content_queue 
                    WHERE platform = ? AND status = "ready"
                    ORDER BY scheduled_time ASC 
                    LIMIT ?
                ''', (platform, limit))
            else:
                cursor.execute('''
                    SELECT * FROM organic_content_queue 
                    WHERE status = "ready"
                    ORDER BY scheduled_time ASC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            queue = [dict(zip(columns, row)) for row in rows]
            conn.close()
            
            return {
                "total_ready": len(queue),
                "content_queue": queue,
                "platform_filter": platform
            }
        except Exception as e:
            print(f"[OrganicWarmupAgent] Kuyruk okuma hatası: {e}")
            return {"error": str(e)}
    
    def mark_content_published(self, content_id: int, platform: str):
        """İçeriği yayınlandı olarak işaretle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE organic_content_queue 
                SET status = "published" 
                WHERE id = ?
            ''', (content_id,))
            conn.commit()
            conn.close()
            
            # Log kaydı
            self._log_warmup_action("content_published", platform, f"Content ID {content_id} marked as published")
            
            return {"success": True, "content_id": content_id}
        except Exception as e:
            print(f"[OrganicWarmupAgent] Yayın işaretleme hatası: {e}")
            return {"error": str(e)}
    
    def generate_batch_content(self, count: int = 10) -> Dict:
        """Toplu içerik üretimi"""
        generated = []
        for _ in range(count):
            # Rastgele kategori ve platform seç
            category = random.choice(list(self.content_categories.keys()))
            platform = random.choice(self.platforms)
            format_type = random.choice(list(self.content_formats.keys()))
            
            content = self.generate_organic_content(category, format_type, platform)
            if content and "error" not in content:
                generated.append(content)
        
        return {
            "total_generated": len(generated),
            "contents": generated
        }
    
    def get_warmup_phase_status(self) -> Dict:
        """Warm-up fazı durumu"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Kuyruk istatistikleri
            cursor.execute('''
                SELECT platform, COUNT(*) as count 
                FROM organic_content_queue 
                WHERE status = "ready"
                GROUP BY platform
            ''')
            platform_stats = dict(cursor.fetchall())
            
            # Kategori istatistikleri
            cursor.execute('''
                SELECT content_category, COUNT(*) as count 
                FROM organic_content_queue 
                WHERE status = "ready"
                GROUP BY content_category
            ''')
            category_stats = dict(cursor.fetchall())
            
            # Toplam içerik
            cursor.execute('SELECT COUNT(*) FROM organic_content_queue WHERE status = "ready"')
            total_ready = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_ready_content": total_ready,
                "platform_distribution": platform_stats,
                "category_distribution": category_stats,
                "supported_platforms": self.platforms,
                "content_categories": list(self.content_categories.keys())
            }
        except Exception as e:
            print(f"[OrganicWarmupAgent] Durum sorgulama hatası: {e}")
            return {"error": str(e)}
    
    def _log_warmup_action(self, action: str, platform: str, result: str):
        """Warm-up eylemini logla"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO warmup_phase_log (phase, action, platform, result)
                VALUES (?, ?, ?, ?)
            ''', ("warmup_phase", action, platform, result))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[OrganicWarmupAgent] Log kayıt hatası: {e}")
    
    def start_background_content_generation(self, interval_seconds=180):
        """Arka planda sürekli içerik üretimi (Nirvana entegrasyonlu)"""
        def generate():
            self.running = True
            # Nirvana arka plan işlemlerini başlat
            if self.nirvana_enabled:
                self.nirvana_agent.start_background_nirvana_processing(interval_seconds)
            
            while self.running:
                # Her platform için 1 içerik üret
                for platform in self.platforms:
                    category = random.choice(list(self.content_categories.keys()))
                    format_type = random.choice(list(self.content_formats.keys()))
                    
                    content = self.generate_organic_content(category, format_type, platform)
                    if content and "error" not in content:
                        print(f"[OrganicWarmup] {platform}: {category} içeriği üretildi")
                        
                        # Nirvana: Etkileşim simülasyonu
                        if self.nirvana_enabled and random.random() < 0.4:  # %40 ihtimalle
                            engagement = self.nirvana_agent.simulate_engagement(
                                content.get("id", 0), platform
                            )
                            if engagement and "error" not in engagement:
                                print(f"[OrganicWarmup] {platform}: Etkileşim simüle edildi")
                
                # Toplu içerik üretimi (arada sırada)
                if random.random() < 0.3:  # %30 ihtimalle
                    batch = self.generate_batch_content(5)
                    print(f"[OrganicWarmup] Toplu içerik üretimi: {batch['total_generated']} içerik")
                
                time.sleep(interval_seconds)
        
        if not self.running:
            self.thread = threading.Thread(target=generate, daemon=True)
            self.thread.start()
            print("[OrganicWarmupAgent] Arka plan içerik üretimi başlatıldı")
    
    def stop_background_content_generation(self):
        """Arka plan içerik üretimini durdur"""
        self.running = False
        if self.thread:
            self.thread.join()
        # Nirvana arka plan işlemlerini durdur
        if self.nirvana_enabled:
            self.nirvana_agent.stop_background_nirvana_processing()
        print("[OrganicWarmupAgent] Arka plan içerik üretimi durduruldu")
    
    def get_nirvana_status(self) -> Dict:
        """Nirvana modülleri durumunu getir"""
        if self.nirvana_enabled:
            return self.nirvana_agent.get_nirvana_status()
        return {"nirvana_enabled": False}

if __name__ == "__main__":
    agent = OrganicWarmupAgent()
    print("[OK] Organic Growth & Warm-up Phase Agent başlatıldı")
    
    # Test içerik üretimi
    content = agent.generate_organic_content("uteykder", "medium", "facebook")
    print(f"Test İçeriği: {content}")
    
    # Toplu içerik üretimi
    batch = agent.generate_batch_content(5)
    print(f"Toplu İçerik: {batch}")
    
    # Durum
    status = agent.get_warmup_phase_status()
    print(f"Warm-up Durumu: {status}")
