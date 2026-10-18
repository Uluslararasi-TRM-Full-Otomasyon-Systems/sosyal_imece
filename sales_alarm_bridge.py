#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sales Alarm Bridge - Telegram Satış Bildirim Sistemi
- trendurunlermarket.com e-ticaret köprüsünden satış verilerini izler
- Yeni sipariş/satış olduğunda anında Telegram bildirimi gönderir
- Mevcut Telegram bot sisteminden bağımsız çalışır
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

class SalesAlarmBridge:
    def __init__(self, db_path="./data/trm_ticari_analiz.db"):
        self.db_path = Path(db_path)
        self._init_database()
        
        # Telegram bot ayarları
        self.telegram_bot_token = os.getenv("SALES_ALARM_TELEGRAM_TOKEN", "")
        self.telegram_chat_id = os.getenv("SALES_ALARM_CHAT_ID", "")
        self.telegram_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)
        
        # Satış alarmı ayarları
        self.alarm_enabled = True
        self.min_order_amount = 0.0  # Minimum sipariş tutarı (TL)
        self.notification_cooldown = 60  # Bildirim aralığı (saniye)
        self.last_notification_time = None
        
        # Bildirim formatı
        self.notification_templates = {
            "new_order": "💰 YENİ SİPARİŞ / SATIŞ GELDİ!\n\n🛒 Sipariş No: {order_id}\n💵 Tutar: {amount} TL\n📦 Ürün: {product_name}\n👤 Müşteri: {customer_name}\n⏰ Zaman: {timestamp}",
            "high_value": "🔥 YÜKSEK TUTARLI SİPARİŞ!\n\n💰 {amount} TL\n🛒 {product_name}\n👤 {customer_name}",
            "daily_summary": "📊 GÜNLÜK SATIŞ ÖZETİ\n\n💰 Toplam Tutar: {total_amount} TL\n📦 Sipariş Sayısı: {order_count}\n📈 Ortalama Tutar: {avg_amount} TL"
        }
    
    def _init_database(self):
        """Satış alarmı için veritabanı tabloları"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales_alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    order_amount REAL,
                    product_name TEXT,
                    customer_name TEXT,
                    notification_sent INTEGER DEFAULT 0,
                    notification_time TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales_alarm_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT,
                    config_value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales_notification_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    notification_type TEXT,
                    message TEXT,
                    status TEXT,
                    error_message TEXT,
                    sent_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SalesAlarmBridge] Veritabanı hatası: {e}")
    
    def send_telegram_notification(self, message: str) -> Dict:
        """Telegram bildirimi gönder"""
        if not self.telegram_enabled:
            return {"success": False, "error": "Telegram ayarları eksik"}
        
        if not self.alarm_enabled:
            return {"success": False, "error": "Alarm devre dışı"}
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("ok"):
                return {
                    "success": True,
                    "message_id": data.get("result", {}).get("message_id"),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": data.get("description", "Bilinmeyen hata")}
                
        except Exception as e:
            print(f"[SalesAlarmBridge] Telegram gönderim hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def process_new_sale(self, order_data: Dict) -> Dict:
        """Yeni satış verisini işle ve bildirim gönder"""
        try:
            order_id = order_data.get("order_id", f"ORD-{int(datetime.now().timestamp())}")
            order_amount = float(order_data.get("amount", 0))
            product_name = order_data.get("product_name", "Bilinmeyen Ürün")
            customer_name = order_data.get("customer_name", "Misafir")
            
            # Minimum tutar kontrolü
            if order_amount < self.min_order_amount:
                return {"success": False, "error": "Minimum tutar altında", "order_id": order_id}
            
            # Bildirim aralığı kontrolü
            if self.last_notification_time:
                time_diff = (datetime.now() - datetime.fromisoformat(self.last_notification_time)).total_seconds()
                if time_diff < self.notification_cooldown:
                    return {"success": False, "error": "Cooldown süresi aktif", "order_id": order_id}
            
            # Bildirim mesajı oluştur
            template = self.notification_templates["new_order"]
            message = template.format(
                order_id=order_id,
                amount=order_amount,
                product_name=product_name,
                customer_name=customer_name,
                timestamp=datetime.now().strftime("%H:%M:%S")
            )
            
            # Yüksek tutarlı sipariş için özel bildirim
            if order_amount >= 1000:
                message = self.notification_templates["high_value"].format(
                    amount=order_amount,
                    product_name=product_name,
                    customer_name=customer_name
                )
            
            # Telegram bildirimi gönder
            notification_result = self.send_telegram_notification(message)
            
            # Veritabanına kaydet
            self._save_sale_record(order_id, order_amount, product_name, customer_name, notification_result)
            self._log_notification(order_id, "new_order", message, notification_result)
            
            # Son bildirim zamanını güncelle
            if notification_result.get("success"):
                self.last_notification_time = datetime.now().isoformat()
            
            return {
                "success": notification_result.get("success", False),
                "order_id": order_id,
                "amount": order_amount,
                "notification_result": notification_result
            }
            
        except Exception as e:
            print(f"[SalesAlarmBridge] Satış işleme hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def _save_sale_record(self, order_id: str, amount: float, product_name: str, customer_name: str, notification_result: Dict):
        """Satış kaydını veritabanına kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sales_alarms 
                (order_id, order_amount, product_name, customer_name, notification_sent, notification_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, amount, product_name, customer_name,
                  1 if notification_result.get("success") else 0,
                  datetime.now().isoformat() if notification_result.get("success") else None))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SalesAlarmBridge] Satış kayıt hatası: {e}")
    
    def _log_notification(self, order_id: str, notification_type: str, message: str, result: Dict):
        """Bildirim logunu kaydet"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sales_notification_log 
                (order_id, notification_type, message, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, notification_type, message,
                  "success" if result.get("success") else "failed",
                  result.get("error", "") if not result.get("success") else None))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[SalesAlarmBridge] Log kayıt hatası: {e}")
    
    def get_sales_statistics(self, hours: int = 24) -> Dict:
        """Satış istatistiklerini getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Son X saatlik satışlar
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(order_amount) as total, AVG(order_amount) as avg
                FROM sales_alarms 
                WHERE created_at >= datetime('now', '-' || ? || ' hours')
            ''', (hours,))
            
            stats = cursor.fetchone()
            conn.close()
            
            return {
                "period_hours": hours,
                "total_orders": stats[0] or 0,
                "total_amount": stats[1] or 0.0,
                "average_amount": stats[2] or 0.0
            }
        except Exception as e:
            print(f"[SalesAlarmBridge] İstatistik hatası: {e}")
            return {"error": str(e)}
    
    def get_recent_sales(self, limit: int = 10) -> Dict:
        """Son satışları getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sales_alarms 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            sales = [dict(zip(columns, row)) for row in rows]
            conn.close()
            
            return {
                "total_recent": len(sales),
                "recent_sales": sales
            }
        except Exception as e:
            print(f"[SalesAlarmBridge] Son satışlar hatası: {e}")
            return {"error": str(e)}
    
    def send_daily_summary(self) -> Dict:
        """Günlük satış özeti gönder"""
        try:
            stats = self.get_sales_statistics(24)
            
            if stats.get("total_orders", 0) == 0:
                return {"success": False, "error": "Bugün satış yok"}
            
            message = self.notification_templates["daily_summary"].format(
                total_amount=stats["total_amount"],
                order_count=stats["total_orders"],
                avg_amount=stats["average_amount"]
            )
            
            result = self.send_telegram_notification(message)
            
            return {
                "success": result.get("success", False),
                "statistics": stats,
                "notification_result": result
            }
            
        except Exception as e:
            print(f"[SalesAlarmBridge] Günlük özet hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def update_config(self, config_key: str, config_value: str) -> Dict:
        """Yapılandırma güncelle"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO sales_alarm_config (config_key, config_value, updated_at)
                VALUES (?, ?, ?)
            ''', (config_key, config_value, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            # Yapılandırmayı uygula
            if config_key == "alarm_enabled":
                self.alarm_enabled = config_value.lower() == "true"
            elif config_key == "min_order_amount":
                self.min_order_amount = float(config_value)
            elif config_key == "notification_cooldown":
                self.notification_cooldown = int(config_value)
            
            return {"success": True, "config_key": config_key, "config_value": config_value}
        except Exception as e:
            print(f"[SalesAlarmBridge] Yapılandırma hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def get_config(self) -> Dict:
        """Yapılandırmayı getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sales_alarm_config')
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            config = {row[1]: row[2] for row in rows}
            conn.close()
            
            return {
                "telegram_enabled": self.telegram_enabled,
                "alarm_enabled": self.alarm_enabled,
                "min_order_amount": self.min_order_amount,
                "notification_cooldown": self.notification_cooldown,
                "custom_config": config
            }
        except Exception as e:
            print(f"[SalesAlarmBridge] Yapılandırma okuma hatası: {e}")
            return {"error": str(e)}
    
    def get_alarm_status(self) -> Dict:
        """Alarm durumunu getir"""
        try:
            config = self.get_config()
            recent_sales = self.get_recent_sales(5)
            stats = self.get_sales_statistics(24)
            
            return {
                "status": "active" if self.alarm_enabled and self.telegram_enabled else "inactive",
                "telegram_enabled": self.telegram_enabled,
                "alarm_enabled": self.alarm_enabled,
                "configuration": config,
                "recent_activity": recent_sales,
                "statistics": stats
            }
        except Exception as e:
            print(f"[SalesAlarmBridge] Durum sorgulama hatası: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test
    bridge = SalesAlarmBridge()
    print("[OK] Sales Alarm Bridge başlatıldı")
    
    # Test satışı
    test_order = {
        "order_id": "TEST-001",
        "amount": 1500.00,
        "product_name": "Xiaomi Akıllı Bileklik",
        "customer_name": "Ahmet Yılmaz"
    }
    
    result = bridge.process_new_sale(test_order)
    print(f"Test Sonucu: {result}")
    
    # Durum
    status = bridge.get_alarm_status()
    print(f"Alarm Durumu: {status}")
