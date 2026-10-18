#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Competitive Intelligence & Behavioral Targeting Agent
- Lokasyon bazlı ve içerik bazlı tüketici reaksiyonlarını takip eder.
- Tıklama, video izleme süresi ve anlık etkileşim verilerini işler.
- Hedef kitle içinde doğru ürün/içerik eşleştirmesi yapar.
- Kullanıcının anlık ruh hali ve davranış analizine göre akıllı öneriler sunar.
"""

import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class CompetitiveIntelligenceAgent:
    def __init__(self, storage_path="./data/intelligence_records.json", db_path="./data/trm_ticari_analiz.db"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)
        self.records = self._load_records()
        self._init_sqlite_tables()
        
        # Ruh hali ve davranış analizi için ağırlıklandırma matrisi
        self.mood_weights = {
            "happy": {"video": 1.3, "image": 0.9, "text": 0.7},
            "neutral": {"video": 1.0, "image": 1.0, "text": 1.0},
            "sad": {"video": 0.8, "image": 1.1, "text": 1.2},
            "excited": {"video": 1.4, "image": 0.8, "text": 0.6},
            "curious": {"video": 1.1, "image": 1.0, "text": 1.3}
        }
        
        # Bölge bazlı tercih matrisi
        self.region_preferences = {
            "istanbul": {"tech": 0.9, "fashion": 0.8, "food": 0.7},
            "ankara": {"tech": 0.7, "fashion": 0.7, "food": 0.9},
            "izmir": {"tech": 0.6, "fashion": 0.9, "food": 0.8},
            "yurtici": {"tech": 0.7, "fashion": 0.7, "food": 0.8},
            "yurtdisi": {"tech": 0.8, "fashion": 0.8, "food": 0.6}
        }

    def _init_sqlite_tables(self):
        """SQLite tablolarını oluştur"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
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
                    our_action_plan TEXT,
                    user_mood TEXT,
                    content_type TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS behavioral_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    region TEXT,
                    avg_dwell_time REAL,
                    avg_click_count REAL,
                    dominant_mood TEXT,
                    preferred_content_type TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[CompetitiveIntelligence] SQLite tablo oluşturma hatası: {e}")

    def _load_records(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_records(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[CompetitiveIntelligence] Kayıt hatası: {e}")

    def record_competitor_move(self, competitor_name, strategy, reaction, score, action_plan, 
                                region="yurtici", dwell_time=0, click_count=1, user_mood="neutral", 
                                content_type="mixed"):
        """
        Bölgedeki etkileşimleri, izleme sürelerini, tüketici reaksiyonlarını ve 
        lokasyon bazlı verileri kayda alır. SQLite'a da kaydeder.
        """
        record = {
            "id": len(self.records) + 1,
            "timestamp": datetime.now().isoformat(),
            "competitor_name": competitor_name,
            "region": region,
            "promotional_strategy": strategy,
            "customer_reaction": reaction,
            "dwell_time_seconds": dwell_time,
            "click_count": click_count,
            "success_score": score,
            "our_action_plan": action_plan,
            "user_mood": user_mood,
            "content_type": content_type
        }
        self.records.append(record)
        self._save_records()
        
        # SQLite'a kaydet
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO intelligence_records 
                (timestamp, competitor_name, region, promotional_strategy, customer_reaction,
                 dwell_time_seconds, click_count, success_score, our_action_plan, user_mood, content_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (record["timestamp"], competitor_name, region, strategy, reaction,
                  dwell_time, click_count, score, action_plan, user_mood, content_type))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[CompetitiveIntelligence] SQLite kayıt hatası: {e}")
        
        return {
            "success": True,
            "message": "Davranışsal istihbarat ve etkileşim verisi başarıyla işlendi.",
            "record_id": record["id"]
        }

    def analyze_behavioral_match(self, region: str, user_mood_indicator: str, 
                                 product_category: str, dwell_time: float = 0, 
                                 click_count: int = 1) -> Dict:
        """
        Lokasyon, kullanıcının o anki etkileşim / ruh hali, video izleme süresi 
        ve tıklama davranışına göre en doğru ürün tanıtım görselini ve içerik 
        stratejisini belirler.
        """
        # Bölge ve ruh hali ağırlıklarını al
        region_prefs = self.region_preferences.get(region.lower(), self.region_preferences["yurtici"])
        mood_weights = self.mood_weights.get(user_mood_indicator.lower(), self.mood_weights["neutral"])
        
        # İçerik türü önerisi (video/image/text)
        content_scores = {
            "video": mood_weights["video"] * region_prefs.get(product_category.lower(), 0.7),
            "image": mood_weights["image"] * region_prefs.get(product_category.lower(), 0.7),
            "text": mood_weights["text"] * region_prefs.get(product_category.lower(), 0.7)
        }
        
        best_content_type = max(content_scores, key=content_scores.get)
        confidence_score = content_scores[best_content_type]
        
        # Video izleme süresi ve tıklama davranışına göre ekstra analiz
        engagement_level = "low"
        if dwell_time > 30 and click_count > 3:
            engagement_level = "high"
        elif dwell_time > 15 or click_count > 1:
            engagement_level = "medium"
        
        matched_strategy = {
            "region": region,
            "user_mood": user_mood_indicator,
            "recommended_product_category": product_category,
            "recommended_content_type": best_content_type,
            "engagement_level": engagement_level,
            "dwell_time_analysis": f"{dwell_time}s izleme süresi",
            "click_pattern": f"{click_count} tıklama",
            "action": f"Kullanıcının {user_mood_indicator} ruh hali ve {region} bölgesi tercihlerine göre "
                      f"{best_content_type} içeriği önerildi. {confidence_score:.2f} güven skoru.",
            "confidence_score": round(confidence_score, 2),
            "content_scores": content_scores
        }
        
        return matched_strategy

    def record_behavioral_pattern(self, session_id: str, region: str, dwell_time: float, 
                                  click_count: int, dominant_mood: str, 
                                  preferred_content_type: str) -> Dict:
        """
        Kullanıcı davranış kalıplarını SQLite'a kaydeder
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO behavioral_patterns 
                (session_id, region, avg_dwell_time, avg_click_count, dominant_mood, preferred_content_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, region, dwell_time, click_count, dominant_mood, preferred_content_type))
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": "Davranış kalıbı başarıyla kaydedildi",
                "session_id": session_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_intelligence_summary(self, limit: int = 20) -> Dict:
        """Tüm biriken istihbarat ve reaksiyon özetlerini döner (JSON + SQLite)"""
        # SQLite'dan son kayıtları al
        sqlite_records = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM intelligence_records 
                ORDER BY id DESC LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            sqlite_records = [dict(zip(columns, row)) for row in rows]
            conn.close()
        except Exception as e:
            print(f"[CompetitiveIntelligence] SQLite okuma hatası: {e}")
        
        return {
            "total_records": len(self.records),
            "json_records": self.records[-limit:],
            "sqlite_records": sqlite_records,
            "total_sqlite_records": len(sqlite_records)
        }

    def get_regional_insights(self, region: str) -> Dict:
        """Belirli bir bölge için istihbarat özeti"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) as total, AVG(success_score) as avg_score, 
                       AVG(dwell_time_seconds) as avg_dwell, AVG(click_count) as avg_clicks
                FROM intelligence_records 
                WHERE region = ?
            ''', (region,))
            row = cursor.fetchone()
            conn.close()
            
            if row and row[0] > 0:
                return {
                    "region": region,
                    "total_records": row[0],
                    "average_success_score": round(row[1], 2) if row[1] else 0,
                    "average_dwell_time": round(row[2], 2) if row[2] else 0,
                    "average_click_count": round(row[3], 2) if row[3] else 0
                }
            else:
                return {"region": region, "message": "Bu bölge için kayıt bulunamadı"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    agent = CompetitiveIntelligenceAgent()
    print("[OK] Competitive Intelligence & Behavioral Agent aktif.")
    print("[OK] SQLite tabloları oluşturuldu.")
    print("[OK] Gelişmiş davranış analizi modülleri yüklendi.")