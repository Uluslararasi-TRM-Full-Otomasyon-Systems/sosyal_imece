#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Nirvana v3.0 - Gelişmiş Yönetim Paneli
Çoklu sayfa yapısı ile tüm bilgileri gösterir
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import sqlite3
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Sistem modülleri
from SYSTEM_MANAGER_24_7 import SystemManager24_7
from DRIVE_SOCIAL_MANAGER import DriveSocialManager
from SATIS_ALARM_SISTEMI import SalesAlarmSystem

class AdvancedDashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, dashboard_manager, **kwargs):
        self.dashboard_manager = dashboard_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET isteklerini yönet"""
        path = unquote(self.path)
        
        if path == '/':
            self.send_main_page()
        elif path == '/system-status':
            self.send_system_status()
        elif path == '/daily-stats':
            self.send_daily_stats()
        elif path == '/error-logs':
            self.send_error_logs()
        elif path == '/social-posts':
            self.send_social_posts()
        elif path == '/ai-performance':
            self.send_ai_performance()
        elif path == '/web-scraping':
            self.send_web_scraping()
        elif path == '/sales-graphs':
            self.send_sales_graphs()
        elif path == '/high-commission':
            self.send_high_commission()
        elif path == '/sold-products':
            self.send_sold_products()
        elif path == '/commission-tracking':
            self.send_commission_tracking()
        elif path == '/daily-commission':
            self.send_daily_commission()
        elif path == '/24h-reset':
            self.send_24h_reset()
        elif path.startswith('/api/'):
            self.send_api_response(path)
        else:
            self.send_404()
    
    def send_main_page(self):
        """Ana sayfayı gönder"""
        html_content = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>TRM Nirvana v3.0 - Gelişmiş Yönetim Paneli</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{background:radial-gradient(circle at 20%30%,#0a0f1e,#03060c);font-family:'Segoe UI',system-ui;color:#eef;padding:20px;min-height:100vh;}
        .header{background:rgba(15,22,36,0.9);backdrop-filter:blur(20px);border-radius:2rem;padding:2rem;margin-bottom:2rem;border:1px solid rgba(255,170,51,0.4);}
        .title{font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#ffd966,#ffaa33,#ffdd99,#ffcc66);-webkit-background-clip:text;background-clip:text;color:transparent;text-align:center;margin-bottom:1rem;}
        .nav-tabs{display:flex;gap:10px;margin-bottom:2rem;flex-wrap:wrap;}
        .nav-tab{background:#1e2a3a;border:2px solid #ffaa55;color:#ffdd99;padding:12px 24px;border-radius:15px;cursor:pointer;transition:all 0.3s;font-weight:bold;text-decoration:none;}
        .nav-tab:hover{background:#ffaa33;color:#000;transform:scale(1.05);}
        .nav-tab.active{background:#ffaa33;color:#000;}
        .content-area{background:rgba(15,22,36,0.85);backdrop-filter:blur(20px);border-radius:2rem;padding:2rem;border:1px solid rgba(255,170,51,0.4);min-height:600px;}
        .tab-content{display:none;}
        .tab-content.active{display:block;}
        .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin:20px 0;}
        .stat-card{background:#0a0f18cc;border-radius:15px;padding:20px;text-align:center;border:1px solid #2a3344;}
        .stat-value{font-size:2rem;font-weight:bold;color:#ffd966;margin-bottom:10px;}
        .stat-label{color:#ffaa88;font-size:14px;}
        .chart-container{background:#0a0f18cc;border-radius:15px;padding:20px;margin:20px 0;border:1px solid #2a3344;}
        .log-container{background:#0a0f18cc;border-radius:15px;padding:20px;margin:20px 0;border:1px solid #2a3344;max-height:400px;overflow-y:auto;}
        .log-entry{font-family:'Courier New',monospace;font-size:12px;color:#eef;margin:5px 0;padding:10px;background:#1e2a3a;border-radius:5px;}
        .log-error{border-left:4px solid #ef4444;}
        .log-warning{border-left:4px solid #f59e0b;}
        .log-info{border-left:4px solid #3b82f6;}
        .table{width:100%;border-collapse:collapse;margin:20px 0;}
        .table th,.table td{border:1px solid #2a3344;padding:12px;text-align:left;}
        .table th{background:#1e2a3a;color:#ffdd99;font-weight:bold;}
        .table tr:nth-child(even){background:#0a0f18cc;}
        .refresh-btn{background:#1e2a3a;border:2px solid #ffaa55;color:#fff;padding:10px 20px;border-radius:10px;cursor:pointer;margin:10px 0;}
        .refresh-btn:hover{background:#ffaa33;color:#000;}
        .loading{display:none;text-align:center;padding:20px;}
        .loading.active{display:block;}
        .spinner{border:4px solid rgba(255,170,51,0.3);border-top:4px solid #ffaa33;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:20px auto;}
        @keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
    </style>
</head>
<body>
<div class="header">
    <h1 class="title">ULUSLARARASI TRM FULL OTOMASYON (Trend �r�nler Market) PANEL� - Gelişmiş Yönetim</h1>
    <div class="nav-tabs">
        <a href="#" class="nav-tab active" onclick="showTab('system-status')">1. Sistem Durumu</a>
        <a href="#" class="nav-tab" onclick="showTab('daily-stats')">2. Günlük İstatistikler</a>
        <a href="#" class="nav-tab" onclick="showTab('error-logs')">3. Hata Logları</a>
        <a href="#" class="nav-tab" onclick="showTab('social-posts')">4. Sosyal Medya</a>
        <a href="#" class="nav-tab" onclick="showTab('ai-performance')">5. AI Performans</a>
        <a href="#" class="nav-tab" onclick="showTab('web-scraping')">6. Web Veri Toplama</a>
        <a href="#" class="nav-tab" onclick="showTab('sales-graphs')">7. Satış Grafikleri</a>
        <a href="#" class="nav-tab" onclick="showTab('high-commission')">8. %20+ Komisyon</a>
        <a href="#" class="nav-tab" onclick="showTab('sold-products')">9. Satılan Ürünler</a>
        <a href="#" class="nav-tab" onclick="showTab('commission-tracking')">10. Komisyon Takibi</a>
        <a href="#" class="nav-tab" onclick="showTab('daily-commission')">11. Günlük Komisyon</a>
        <a href="#" class="nav-tab" onclick="showTab('24h-reset')">12. 24 Saat Sıfırla</a>
    </div>
</div>

<div class="content-area">
    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p style="color:#ffdd99;margin-top:10px;">Veriler yükleniyor...</p>
    </div>

    <!-- Tab 1: Sistem Durumu -->
    <div id="system-status" class="tab-content active">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🖥️ Sistem Durumu</h2>
        <div class="stats-grid" id="system-stats">
            <!-- Sistem istatistikleri buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSystemStatus()">🔄 Yenile</button>
    </div>

    <!-- Tab 2: Günlük İstatistikler -->
    <div id="daily-stats" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">📊 Günlük İstatistikler</h2>
        <div class="stats-grid" id="daily-stats-grid">
            <!-- Günlük istatistikler buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshDailyStats()">🔄 Yenile</button>
    </div>

    <!-- Tab 3: Hata Logları -->
    <div id="error-logs" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🔍 Hata Logları</h2>
        <div class="log-container" id="error-logs-container">
            <!-- Hata logları buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshErrorLogs()">🔄 Yenile</button>
    </div>

    <!-- Tab 4: Sosyal Medya -->
    <div id="social-posts" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">📱 Sosyal Medyada Paylaşılan İçerikler</h2>
        <div id="social-posts-container">
            <!-- Sosyal medya içerikleri buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSocialPosts()">🔄 Yenile</button>
    </div>

    <!-- Tab 5: AI Performans -->
    <div id="ai-performance" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🤖 Yapay Zeka Performans Tablosu</h2>
        <div class="stats-grid" id="ai-performance-grid">
            <!-- AI performans verileri buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshAIPerformance()">🔄 Yenile</button>
    </div>

    <!-- Tab 6: Web Veri Toplama -->
    <div id="web-scraping" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🌐 Web Veri Toplama Durumu</h2>
        <div class="stats-grid" id="web-scraping-grid">
            <!-- Web scraping durumu buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshWebScraping()">🔄 Yenile</button>
    </div>

    <!-- Tab 7: Satış Grafikleri -->
    <div id="sales-graphs" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">📈 En Çok Satış Yapılan Ürün Grafikleri</h2>
        <div class="chart-container" id="sales-graphs-container">
            <!-- Satış grafikleri buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSalesGraphs()">🔄 Yenile</button>
    </div>

    <!-- Tab 8: %20+ Komisyon -->
    <div id="high-commission" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🔥 Yüksek Komisyon Oranlı Ürün Listeleri</h2>
        <div id="high-commission-container">
            <!-- Yüksek komisyonlu ürünler buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshHighCommission()">🔄 Yenile</button>
    </div>

    <!-- Tab 9: Satılan Ürünler -->
    <div id="sold-products" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🛒 trendurunlermarket.com Üzerinden Satılan Ürünler</h2>
        <div id="sold-products-container">
            <!-- Satılan ürünler buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSoldProducts()">🔄 Yenile</button>
    </div>

    <!-- Tab 10: Komisyon Takibi -->
    <div id="commission-tracking" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">💰 Ürün Alıcıya Ulaştıktan Sonraki 14 Gün Sonunda Komisyon Takibi</h2>
        <div id="commission-tracking-container">
            <!-- Komisyon takibi buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshCommissionTracking()">🔄 Yenile</button>
    </div>

    <!-- Tab 11: Günlük Komisyon -->
    <div id="daily-commission" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">💸 Günlük Yatan Komisyon Listeleri</h2>
        <div id="daily-commission-container">
            <!-- Günlük komisyonlar buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshDailyCommission()">🔄 Yenile</button>
    </div>

    <!-- Tab 12: 24 Saat Sıfırla -->
    <div id="24h-reset" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">🔄 24 Saat Sonunda Ekran Verilerinin Otomatik Sıfırlanması</h2>
        <div class="stats-grid" id="24h-reset-grid">
            <!-- 24 saat sıfırlama durumu buraya yüklenecek -->
        </div>
        <button class="refresh-btn" onclick="refresh24hReset()">🔄 Yenile</button>
    </div>
</div>

<script>
let currentTab = 'system-status';

function showTab(tabName) {
    // Tüm tab'leri gizle
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Tüm nav tab'lerini pasif yap
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Seçili tab'i göster
    document.getElementById(tabName).classList.add('active');
    
    // Seçili nav tab'i aktif yap
    event.target.classList.add('active');
    
    currentTab = tabName;
    
    // Tab verilerini yükle
    loadTabData(tabName);
}

function showLoading() {
    document.getElementById('loading').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading').classList.remove('active');
}

async function loadTabData(tabName) {
    showLoading();
    
    try {
        const response = await fetch(`/api/${tabName}`);
        const data = await response.json();
        
        updateTabContent(tabName, data);
    } catch (error) {
        console.error('Tab verisi yüklenemedi:', error);
    } finally {
        hideLoading();
    }
}

function updateTabContent(tabName, data) {
    switch(tabName) {
        case 'system-status':
            updateSystemStatus(data);
            break;
        case 'daily-stats':
            updateDailyStats(data);
            break;
        case 'error-logs':
            updateErrorLogs(data);
            break;
        case 'social-posts':
            updateSocialPosts(data);
            break;
        case 'ai-performance':
            updateAIPerformance(data);
            break;
        case 'web-scraping':
            updateWebScraping(data);
            break;
        case 'sales-graphs':
            updateSalesGraphs(data);
            break;
        case 'high-commission':
            updateHighCommission(data);
            break;
        case 'sold-products':
            updateSoldProducts(data);
            break;
        case 'commission-tracking':
            updateCommissionTracking(data);
            break;
        case 'daily-commission':
            updateDailyCommission(data);
            break;
        case '24h-reset':
            update24hReset(data);
            break;
    }
}

function updateSystemStatus(data) {
    const container = document.getElementById('system-stats');
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data.uptime || '0s'}</div>
            <div class="stat-label">⏰ Çalışma Süresi</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.auto_restarts || 0}</div>
            <div class="stat-label">🔄 Otomatik Yeniden Başlatma</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.health_score || 100}%</div>
            <div class="stat-label">📊 Sağlık Skoru</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.errors || 0}</div>
            <div class="stat-label">❌ Hata Sayısı</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.warnings || 0}</div>
            <div class="stat-label">⚠️ Uyarı Sayısı</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.processes_running || 0}</div>
            <div class="stat-label">🤖 Çalışan Process'ler</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.memory_usage || '0%'}</div>
            <div class="stat-label">💾 Bellek Kullanımı</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.cpu_usage || '0%'}</div>
            <div class="stat-label">⚡ CPU Kullanımı</div>
        </div>
    `;
}

// Diğer update fonksiyonları buraya eklenecek...

async function refreshSystemStatus() {
    await loadTabData('system-status');
}

async function refreshDailyStats() {
    await loadTabData('daily-stats');
}

async function refreshErrorLogs() {
    await loadTabData('error-logs');
}

async function refreshSocialPosts() {
    await loadTabData('social-posts');
}

async function refreshAIPerformance() {
    await loadTabData('ai-performance');
}

async function refreshWebScraping() {
    await loadTabData('web-scraping');
}

async function refreshSalesGraphs() {
    await loadTabData('sales-graphs');
}

async function refreshHighCommission() {
    await loadTabData('high-commission');
}

async function refreshSoldProducts() {
    await loadTabData('sold-products');
}

async function refreshCommissionTracking() {
    await loadTabData('commission-tracking');
}

async function refreshDailyCommission() {
    await loadTabData('daily-commission');
}

async function refresh24hReset() {
    await loadTabData('24h-reset');
}

// Sayfa yüklendiğinde ilk tab'i yükle
document.addEventListener('DOMContentLoaded', function() {
    loadTabData('system-status');
});

// Her 30 saniyede bir verileri yenile
setInterval(() => {
    if (currentTab) {
        loadTabData(currentTab);
    }
}, 30000);
</script>
</body>
</html>
        """
        
        self.send_response(200, 'text/html', html_content)
    
    def send_api_response(self, path):
        """API yanıtı gönder"""
        try:
            endpoint = path.replace('/api/', '')
            
            if endpoint == 'system-status':
                data = self.dashboard_manager.get_system_status()
            elif endpoint == 'daily-stats':
                data = self.dashboard_manager.get_daily_stats()
            elif endpoint == 'error-logs':
                data = self.dashboard_manager.get_error_logs()
            elif endpoint == 'social-posts':
                data = self.dashboard_manager.get_social_posts()
            elif endpoint == 'ai-performance':
                data = self.dashboard_manager.get_ai_performance()
            elif endpoint == 'web-scraping':
                data = self.dashboard_manager.get_web_scraping_status()
            elif endpoint == 'sales-graphs':
                data = self.dashboard_manager.get_sales_graphs()
            elif endpoint == 'high-commission':
                data = self.dashboard_manager.get_high_commission_products()
            elif endpoint == 'sold-products':
                data = self.dashboard_manager.get_sold_products()
            elif endpoint == 'commission-tracking':
                data = self.dashboard_manager.get_commission_tracking()
            elif endpoint == 'daily-commission':
                data = self.dashboard_manager.get_daily_commission()
            elif endpoint == '24h-reset':
                data = self.dashboard_manager.get_24h_reset_status()
            else:
                data = {'error': 'Endpoint not found'}
            
            self.send_response(200, 'application/json', json.dumps(data))
            
        except Exception as e:
            self.send_response(500, 'application/json', json.dumps({'error': str(e)}))
    
    def send_response(self, status_code, content_type=None, content=None):
        """HTTP yanıtı gönder (BaseHTTPRequestHandler ile çakışmasın)."""
        if content_type is None and content is None:
            BaseHTTPRequestHandler.send_response(self, status_code)
            return
        body = content if isinstance(content, bytes) else (content or "").encode("utf-8")
        ctype = content_type or "text/html; charset=utf-8"
        if "charset" not in ctype and (ctype.startswith("text/") or ctype == "application/json"):
            ctype = f"{ctype}; charset=utf-8"
        BaseHTTPRequestHandler.send_response(self, status_code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        pass  # Log mesajlarını gösterme

class AdvancedDashboardManager:
    def __init__(self):
        self.system_manager = None
        self.drive_social_manager = None
        self.sales_alarm_system = None
        
        # Veritabanı bağlantısı
        self.db_conn = None
        self.init_database()
    
    def init_database(self):
        """Veritabanını başlat"""
        try:
            self.db_conn = sqlite3.connect('trm_dashboard.db')
            cursor = self.db_conn.cursor()
            
            # Tabloları oluştur
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    uptime INTEGER,
                    auto_restarts INTEGER,
                    health_score INTEGER,
                    errors INTEGER,
                    warnings INTEGER,
                    processes_running INTEGER,
                    memory_usage TEXT,
                    cpu_usage TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    products_captured INTEGER,
                    high_commission INTEGER,
                    social_published INTEGER,
                    estimated_commission REAL,
                    success_rate REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    module TEXT,
                    message TEXT,
                    details TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS social_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    platform TEXT,
                    content_type TEXT,
                    product_name TEXT,
                    status TEXT,
                    engagement INTEGER
                )
            ''')
            
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"Veritabanı başlatma hatası: {e}")
    
    def get_system_status(self) -> Dict:
        """Sistem durumunu al"""
        try:
            # Sistem bilgilerini al
            import psutil
            
            status = {
                'uptime': '0s',
                'auto_restarts': 0,
                'health_score': 100,
                'errors': 0,
                'warnings': 0,
                'processes_running': 0,
                'memory_usage': f"{psutil.virtual_memory().percent:.1f}%",
                'cpu_usage': f"{psutil.cpu_percent():.1f}%",
                'last_update': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Sistem durumu alma hatası: {e}")
            return {'error': str(e)}
    
    def get_daily_stats(self) -> Dict:
        """Günlük istatistikleri al"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Veritabanından günlük istatistikleri al
            cursor = self.db_conn.cursor()
            cursor.execute('''
                SELECT * FROM daily_stats WHERE date = ? ORDER BY id DESC LIMIT 1
            ''', (today,))
            
            result = cursor.fetchone()
            
            if result:
                return {
                    'date': result[1],
                    'products_captured': result[2],
                    'high_commission': result[3],
                    'social_published': result[4],
                    'estimated_commission': result[5],
                    'success_rate': result[6]
                }
            else:
                return {
                    'date': today,
                    'products_captured': 0,
                    'high_commission': 0,
                    'social_published': 0,
                    'estimated_commission': 0.0,
                    'success_rate': 0.0
                }
                
        except Exception as e:
            logger.error(f"Günlük istatistikleri alma hatası: {e}")
            return {'error': str(e)}
    
    def get_error_logs(self) -> Dict:
        """Hata loglarını al"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                SELECT * FROM error_logs ORDER BY id DESC LIMIT 50
            ''')
            
            results = cursor.fetchall()
            
            logs = []
            for row in results:
                logs.append({
                    'timestamp': row[1],
                    'level': row[2],
                    'module': row[3],
                    'message': row[4],
                    'details': row[5]
                })
            
            return {'logs': logs}
            
        except Exception as e:
            logger.error(f"Hata logları alma hatası: {e}")
            return {'error': str(e)}
    
    def get_social_posts(self) -> Dict:
        """Sosyal medya paylaşımlarını al"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                SELECT * FROM social_posts ORDER BY id DESC LIMIT 50
            ''')
            
            results = cursor.fetchall()
            
            posts = []
            for row in results:
                posts.append({
                    'timestamp': row[1],
                    'platform': row[2],
                    'content_type': row[3],
                    'product_name': row[4],
                    'status': row[5],
                    'engagement': row[6]
                })
            
            return {'posts': posts}
            
        except Exception as e:
            logger.error(f"Sosyal medya paylaşımları alma hatası: {e}")
            return {'error': str(e)}
    
    def get_ai_performance(self) -> Dict:
        """AI performansını al"""
        try:
            # AI performans metrikleri
            performance = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'avg_response_time': 0.0,
                'tokens_used': 0,
                'models_used': {
                    'deepseek': 0,
                    'claude': 0
                },
                'last_update': datetime.now().isoformat()
            }
            
            return performance
            
        except Exception as e:
            logger.error(f"AI performansı alma hatası: {e}")
            return {'error': str(e)}
    
    def get_web_scraping_status(self) -> Dict:
        """Web scraping durumunu al"""
        try:
            status = {
                'last_scrape': None,
                'total_scraped': 0,
                'successful_scrapes': 0,
                'failed_scrapes': 0,
                'avg_scrape_time': 0.0,
                'sites_scraped': [],
                'last_update': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Web scraping durumu alma hatası: {e}")
            return {'error': str(e)}
    
    def get_sales_graphs(self) -> Dict:
        """Satış grafiklerini al"""
        try:
            graphs = {
                'daily_sales': [],
                'top_products': [],
                'commission_trends': [],
                'platform_performance': {},
                'last_update': datetime.now().isoformat()
            }
            
            return graphs
            
        except Exception as e:
            logger.error(f"Satış grafikleri alma hatası: {e}")
            return {'error': str(e)}
    
    def get_high_commission_products(self) -> Dict:
        """Yüksek komisyonlu ürünleri al"""
        try:
            products = {
                'total_high_commission': 0,
                'products': [],
                'avg_commission': 0.0,
                'last_update': datetime.now().isoformat()
            }
            
            return products
            
        except Exception as e:
            logger.error(f"Yüksek komisyonlu ürünleri alma hatası: {e}")
            return {'error': str(e)}
    
    def get_sold_products(self) -> Dict:
        """Satılan ürünleri al"""
        try:
            sold = {
                'total_sold': 0,
                'products': [],
                'total_commission': 0.0,
                'last_update': datetime.now().isoformat()
            }
            
            return sold
            
        except Exception as e:
            logger.error(f"Satılan ürünleri alma hatası: {e}")
            return {'error': str(e)}
    
    def get_commission_tracking(self) -> Dict:
        """Komisyon takibini al"""
        try:
            tracking = {
                'pending_commissions': [],
                'confirmed_commissions': [],
                'total_pending': 0.0,
                'total_confirmed': 0.0,
                'last_update': datetime.now().isoformat()
            }
            
            return tracking
            
        except Exception as e:
            logger.error(f"Komisyon takibi alma hatası: {e}")
            return {'error': str(e)}
    
    def get_daily_commission(self) -> Dict:
        """Günlük komisyonları al"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            daily = {
                'date': today,
                'commissions': [],
                'total_commission': 0.0,
                'pending_commission': 0.0,
                'confirmed_commission': 0.0,
                'last_update': datetime.now().isoformat()
            }
            
            return daily
            
        except Exception as e:
            logger.error(f"Günlük komisyonları alma hatası: {e}")
            return {'error': str(e)}
    
    def get_24h_reset_status(self) -> Dict:
        """24 saat sıfırlama durumunu al"""
        try:
            # Son 24 saatlik verileri kontrol et
            last_reset = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            status = {
                'last_reset': last_reset.isoformat(),
                'hours_until_reset': 24 - datetime.now().hour,
                'minutes_until_reset': 60 - datetime.now().minute,
                'data_cleared': False,
                'last_update': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"24 saat sıfırlama durumu alma hatası: {e}")
            return {'error': str(e)}

class AdvancedDashboardServer:
    def __init__(self):
        self.dashboard_manager = AdvancedDashboardManager()
        self.server = None
    
    async def start(self, port=9003):
        """Sunucuyu başlat"""
        try:
            handler = lambda *args, **kwargs: AdvancedDashboardHandler(*args, dashboard_manager=self.dashboard_manager, **kwargs)
            self.server = HTTPServer(('localhost', port), handler)
            
            # Sunucuyu ayrı thread'de başlat
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            print(f"🌐 Gelişmiş Yönetim Paneli başlatıldı: http://localhost:{port}")
            return True
            
        except Exception as e:
            print(f"❌ Gelişmiş yönetim paneli başlatılamadı: {e}")
            return False
    
    def stop(self):
        """Sunucuyu durdur"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

# Ana başlatıcı
async def main():
    """Ana fonksiyon"""
    print("""
===============================================
    TRM NIRVANA v3.0 - GELİŞMİŞ YÖNETİM PANELİ
===============================================
  🌐 Çoklu Sayfa Yapısı
  📊 12 Farklı Panel
  🔄 Gerçek Zamanlı Veriler
  📈 Grafiksel Gösterim
  📱 Mobil Uyumlu
===============================================
    """)
    
    server = AdvancedDashboardServer()
    
    if await server.start():
        print("🌐 Gelişmiş yönetim paneli aktif!")
        print("📊 Ana panel: http://localhost:9000")
        print("🌐 Gelişmiş panel: http://localhost:9003")
        
        try:
            # Programı açık tut
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Gelişmiş yönetim paneli durduruluyor...")
            server.stop()

if __name__ == "__main__":
    asyncio.run(main())
