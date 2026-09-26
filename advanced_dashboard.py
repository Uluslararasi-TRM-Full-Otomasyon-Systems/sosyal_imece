#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Nirvana v3.0 - GeliÅmiÅ YÃ¶netim Paneli
Ãoklu sayfa yapÄ±sÄ± ile tÃ¼m bilgileri gÃ¶sterir
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote
import sqlite3
import matplotlib.pyplot as plt
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    from SYSTEM_MANAGER_24_7 import SystemManager24_7
except ImportError:
    SystemManager24_7 = None  # type: ignore

try:
    from DRIVE_SOCIAL_MANAGER import DriveSocialManager
except ImportError:
    DriveSocialManager = None  # type: ignore

try:
    from SATIS_ALARM_SISTEMI import SalesAlarmSystem
except ImportError:
    SalesAlarmSystem = None  # type: ignore

class AdvancedDashboardHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, dashboard_manager, **kwargs):
        self.dashboard_manager = dashboard_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """GET isteklerini yÃ¶net"""
        path = unquote(self.path)
        
        if path == '/':
            self.send_main_page()
        elif path == '/system-status':
            self._send_manager_json('get_system_status')
        elif path == '/daily-stats':
            self._send_manager_json('get_daily_stats')
        elif path == '/error-logs':
            self._send_manager_json('get_error_logs')
        elif path == '/social-posts':
            self._send_manager_json('get_social_posts')
        elif path == '/ai-performance':
            self._send_manager_json('get_ai_performance')
        elif path == '/web-scraping':
            self._send_manager_json('get_web_scraping_status')
        elif path == '/sales-graphs':
            self._send_manager_json('get_sales_graphs')
        elif path == '/high-commission':
            self._send_manager_json('get_high_commission_products')
        elif path == '/sold-products':
            self._send_manager_json('get_sold_products')
        elif path == '/commission-tracking':
            self._send_manager_json('get_commission_tracking')
        elif path == '/daily-commission':
            self._send_manager_json('get_daily_commission')
        elif path == '/24h-reset':
            self._send_manager_json('get_24h_reset_status')
        elif path.startswith('/api/'):
            self.send_api_response(path)
        else:
            self.send_404()

    def _send_manager_json(self, method_name):
        getter = getattr(self.dashboard_manager, method_name)
        self.send_response(200, 'application/json', json.dumps(getter(), ensure_ascii=False, default=str))

    def send_404(self):
        self.send_response(404, 'text/plain', 'Not Found')
    
    def send_main_page(self):
        """Ana sayfayÄ± gÃ¶nder"""
        html_content = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>TRM Nirvana v3.0 - GeliÅmiÅ YÃ¶netim Paneli</title>
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
    <h1 class="title">ULUSLARARASI TRM FULL OTOMASYON (Trend Ürünler Market) PANELÝ - GeliÅmiÅ YÃ¶netim</h1>
    <div class="nav-tabs">
        <a href="#" class="nav-tab active" onclick="showTab('system-status')">1. Sistem Durumu</a>
        <a href="#" class="nav-tab" onclick="showTab('daily-stats')">2. GÃ¼nlÃ¼k Ä°statistikler</a>
        <a href="#" class="nav-tab" onclick="showTab('error-logs')">3. Hata LoglarÄ±</a>
        <a href="#" class="nav-tab" onclick="showTab('social-posts')">4. Sosyal Medya</a>
        <a href="#" class="nav-tab" onclick="showTab('ai-performance')">5. AI Performans</a>
        <a href="#" class="nav-tab" onclick="showTab('web-scraping')">6. Web Veri Toplama</a>
        <a href="#" class="nav-tab" onclick="showTab('sales-graphs')">7. SatÄ±Å Grafikleri</a>
        <a href="#" class="nav-tab" onclick="showTab('high-commission')">8. %20+ Komisyon</a>
        <a href="#" class="nav-tab" onclick="showTab('sold-products')">9. SatÄ±lan ÃrÃ¼nler</a>
        <a href="#" class="nav-tab" onclick="showTab('commission-tracking')">10. Komisyon Takibi</a>
        <a href="#" class="nav-tab" onclick="showTab('daily-commission')">11. GÃ¼nlÃ¼k Komisyon</a>
        <a href="#" class="nav-tab" onclick="showTab('24h-reset')">12. 24 Saat SÄ±fÄ±rla</a>
    </div>
</div>

<div class="content-area">
    <div class="loading" id="loading">
        <div class="spinner"></div>
        <p style="color:#ffdd99;margin-top:10px;">Veriler yÃ¼kleniyor...</p>
    </div>

    <!-- Tab 1: Sistem Durumu -->
    <div id="system-status" class="tab-content active">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð¥ï¸ Sistem Durumu</h2>
        <div class="stats-grid" id="system-stats">
            <!-- Sistem istatistikleri buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSystemStatus()">ð Yenile</button>
    </div>

    <!-- Tab 2: GÃ¼nlÃ¼k Ä°statistikler -->
    <div id="daily-stats" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð GÃ¼nlÃ¼k Ä°statistikler</h2>
        <div class="stats-grid" id="daily-stats-grid">
            <!-- GÃ¼nlÃ¼k istatistikler buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshDailyStats()">ð Yenile</button>
    </div>

    <!-- Tab 3: Hata LoglarÄ± -->
    <div id="error-logs" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð Hata LoglarÄ±</h2>
        <div class="log-container" id="error-logs-container">
            <!-- Hata loglarÄ± buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshErrorLogs()">ð Yenile</button>
    </div>

    <!-- Tab 4: Sosyal Medya -->
    <div id="social-posts" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð± Sosyal Medyada PaylaÅÄ±lan Ä°Ã§erikler</h2>
        <div id="social-posts-container">
            <!-- Sosyal medya iÃ§erikleri buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSocialPosts()">ð Yenile</button>
    </div>

    <!-- Tab 5: AI Performans -->
    <div id="ai-performance" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð¤ Yapay Zeka Performans Tablosu</h2>
        <div class="stats-grid" id="ai-performance-grid">
            <!-- AI performans verileri buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshAIPerformance()">ð Yenile</button>
    </div>

    <!-- Tab 6: Web Veri Toplama -->
    <div id="web-scraping" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð Web Veri Toplama Durumu</h2>
        <div class="stats-grid" id="web-scraping-grid">
            <!-- Web scraping durumu buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshWebScraping()">ð Yenile</button>
    </div>

    <!-- Tab 7: SatÄ±Å Grafikleri -->
    <div id="sales-graphs" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð En Ãok SatÄ±Å YapÄ±lan ÃrÃ¼n Grafikleri</h2>
        <div class="chart-container" id="sales-graphs-container">
            <!-- SatÄ±Å grafikleri buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSalesGraphs()">ð Yenile</button>
    </div>

    <!-- Tab 8: %20+ Komisyon -->
    <div id="high-commission" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð¥ YÃ¼ksek Komisyon OranlÄ± ÃrÃ¼n Listeleri</h2>
        <div id="high-commission-container">
            <!-- YÃ¼ksek komisyonlu Ã¼rÃ¼nler buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshHighCommission()">ð Yenile</button>
    </div>

    <!-- Tab 9: SatÄ±lan ÃrÃ¼nler -->
    <div id="sold-products" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð trendurunlermarket.com Ãzerinden SatÄ±lan ÃrÃ¼nler</h2>
        <div id="sold-products-container">
            <!-- SatÄ±lan Ã¼rÃ¼nler buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshSoldProducts()">ð Yenile</button>
    </div>

    <!-- Tab 10: Komisyon Takibi -->
    <div id="commission-tracking" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð° ÃrÃ¼n AlÄ±cÄ±ya UlaÅtÄ±ktan Sonraki 14 GÃ¼n Sonunda Komisyon Takibi</h2>
        <div id="commission-tracking-container">
            <!-- Komisyon takibi buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshCommissionTracking()">ð Yenile</button>
    </div>

    <!-- Tab 11: GÃ¼nlÃ¼k Komisyon -->
    <div id="daily-commission" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð¸ GÃ¼nlÃ¼k Yatan Komisyon Listeleri</h2>
        <div id="daily-commission-container">
            <!-- GÃ¼nlÃ¼k komisyonlar buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refreshDailyCommission()">ð Yenile</button>
    </div>

    <!-- Tab 12: 24 Saat SÄ±fÄ±rla -->
    <div id="24h-reset" class="tab-content">
        <h2 style="color:#ffdd99;margin-bottom:20px;">ð 24 Saat Sonunda Ekran Verilerinin Otomatik SÄ±fÄ±rlanmasÄ±</h2>
        <div class="stats-grid" id="24h-reset-grid">
            <!-- 24 saat sÄ±fÄ±rlama durumu buraya yÃ¼klenecek -->
        </div>
        <button class="refresh-btn" onclick="refresh24hReset()">ð Yenile</button>
    </div>
</div>

<script>
let currentTab = 'system-status';

function showTab(tabName) {
    // TÃ¼m tab'leri gizle
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // TÃ¼m nav tab'lerini pasif yap
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // SeÃ§ili tab'i gÃ¶ster
    document.getElementById(tabName).classList.add('active');
    
    // SeÃ§ili nav tab'i aktif yap
    event.target.classList.add('active');
    
    currentTab = tabName;
    
    // Tab verilerini yÃ¼kle
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
        console.error('Tab verisi yÃ¼klenemedi:', error);
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
    const governance = data.governance_status || {};
    const governanceEntries = Object.entries(governance);
    const governanceMarkup = governanceEntries.length
        ? governanceEntries.map(([name, item]) => `
        <tr>
            <td>${name}</td>
            <td>${item.status || 'Hazirlaniyor'}</td>
            <td>${item.message || 'Governance Katmani Hazirlaniyor...'}</td>
            <td>${item.timestamp || '-'}</td>
        </tr>
        `).join('')
        : `
        <tr>
            <td colspan="4">Governance Katmani Hazirlaniyor...</td>
        </tr>
        `;
    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data.uptime || '0s'}</div>
            <div class="stat-label">â° ÃalÄ±Åma SÃ¼resi</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.auto_restarts || 0}</div>
            <div class="stat-label">ð Otomatik Yeniden BaÅlatma</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.health_score || 100}%</div>
            <div class="stat-label">ð SaÄlÄ±k Skoru</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.errors || 0}</div>
            <div class="stat-label">â Hata SayÄ±sÄ±</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.warnings || 0}</div>
            <div class="stat-label">â ï¸ UyarÄ± SayÄ±sÄ±</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.processes_running || 0}</div>
            <div class="stat-label">ð¤ ÃalÄ±Åan Process'ler</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.memory_usage || '0%'}</div>
            <div class="stat-label">ð¾ Bellek KullanÄ±mÄ±</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.cpu_usage || '0%'}</div>
            <div class="stat-label">â¡ CPU KullanÄ±mÄ±</div>
        </div>
        <div class="chart-container" style="grid-column: 1 / -1;">
            <h3 style="color:#ffdd99;margin-bottom:15px;">Governance Status</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Meta-Ajan</th>
                        <th>Durum</th>
                        <th>Mesaj</th>
                        <th>Zaman</th>
                    </tr>
                </thead>
                <tbody>${governanceMarkup}</tbody>
            </table>
        </div>
    `;
}

// DiÄer update fonksiyonlarÄ± buraya eklenecek...

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

// Sayfa yÃ¼klendiÄinde ilk tab'i yÃ¼kle
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
        """API yanÄ±tÄ± gÃ¶nder"""
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
        """HTTP yaniti gonder (BaseHTTPRequestHandler.send_response ile cakismasin)."""
        if content_type is None and content is None:
            BaseHTTPRequestHandler.send_response(self, status_code)
            return
        if isinstance(content, bytes):
            body = content
        else:
            body = (content or "").encode("utf-8")
        ctype = content_type or "text/html; charset=utf-8"
        if "charset" not in ctype and (ctype.startswith("text/") or ctype == "application/json"):
            ctype = f"{ctype}; charset=utf-8"
        BaseHTTPRequestHandler.send_response(self, status_code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        pass  # Log mesajlarÄ±nÄ± gÃ¶sterme

class AdvancedDashboardManager:
    def __init__(self):
        self.system_manager = None
        self.drive_social_manager = None
        self.sales_alarm_system = None
        
        # VeritabanÄ± baÄlantÄ±sÄ±
        self.db_conn = None
        self.init_database()
    
    def init_database(self):
        """VeritabanÄ±nÄ± baÅlat"""
        try:
            self.db_conn = sqlite3.connect('trm_dashboard.db')
            cursor = self.db_conn.cursor()
            
            # TablolarÄ± oluÅtur
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
            logger.error(f"VeritabanÄ± baÅlatma hatasÄ±: {e}")

    def get_governance_status(self) -> Dict:
        """Governance katmani saglik kaydini al."""
        report_path = os.path.join("trm_agents", "governance", "governance_report.json")

        if not os.path.exists(report_path):
            return {}

        try:
            with open(report_path, "r", encoding="utf-8") as report_file:
                data = json.load(report_file)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Governance durum kaydi okunamadi: {e}")
            return {}
    
    def get_system_status(self) -> Dict:
        """Sistem durumunu al"""
        try:
            # Sistem bilgilerini al
            import psutil
            governance_status = self.get_governance_status()
            
            status = {
                'uptime': '0s',
                'auto_restarts': 0,
                'health_score': 100,
                'errors': 0,
                'warnings': 0,
                'processes_running': 0,
                'memory_usage': f"{psutil.virtual_memory().percent:.1f}%",
                'cpu_usage': f"{psutil.cpu_percent():.1f}%",
                'governance_status': governance_status,
                'last_update': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Sistem durumu alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_daily_stats(self) -> Dict:
        """GÃ¼nlÃ¼k istatistikleri al"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # VeritabanÄ±ndan gÃ¼nlÃ¼k istatistikleri al
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
            logger.error(f"GÃ¼nlÃ¼k istatistikleri alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_error_logs(self) -> Dict:
        """Hata loglarÄ±nÄ± al"""
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
            logger.error(f"Hata loglarÄ± alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_social_posts(self) -> Dict:
        """Sosyal medya paylaÅÄ±mlarÄ±nÄ± al"""
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
            logger.error(f"Sosyal medya paylaÅÄ±mlarÄ± alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_ai_performance(self) -> Dict:
        """AI performansÄ±nÄ± al"""
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
            logger.error(f"AI performansÄ± alma hatasÄ±: {e}")
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
            logger.error(f"Web scraping durumu alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_sales_graphs(self) -> Dict:
        """SatÄ±Å grafiklerini al"""
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
            logger.error(f"SatÄ±Å grafikleri alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_high_commission_products(self) -> Dict:
        """YÃ¼ksek komisyonlu Ã¼rÃ¼nleri al"""
        try:
            products = {
                'total_high_commission': 0,
                'products': [],
                'avg_commission': 0.0,
                'last_update': datetime.now().isoformat()
            }
            
            return products
            
        except Exception as e:
            logger.error(f"YÃ¼ksek komisyonlu Ã¼rÃ¼nleri alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_sold_products(self) -> Dict:
        """SatÄ±lan Ã¼rÃ¼nleri al"""
        try:
            sold = {
                'total_sold': 0,
                'products': [],
                'total_commission': 0.0,
                'last_update': datetime.now().isoformat()
            }
            
            return sold
            
        except Exception as e:
            logger.error(f"SatÄ±lan Ã¼rÃ¼nleri alma hatasÄ±: {e}")
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
            logger.error(f"Komisyon takibi alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_daily_commission(self) -> Dict:
        """GÃ¼nlÃ¼k komisyonlarÄ± al"""
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
            logger.error(f"GÃ¼nlÃ¼k komisyonlarÄ± alma hatasÄ±: {e}")
            return {'error': str(e)}
    
    def get_24h_reset_status(self) -> Dict:
        """24 saat sÄ±fÄ±rlama durumunu al"""
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
            logger.error(f"24 saat sÄ±fÄ±rlama durumu alma hatasÄ±: {e}")
            return {'error': str(e)}

class AdvancedDashboardServer:
    def __init__(self):
        self.dashboard_manager = AdvancedDashboardManager()
        self.server = None
    
    async def start(self, port=9003):
        """Sunucuyu baÅlat"""
        try:
            handler = lambda *args, **kwargs: AdvancedDashboardHandler(*args, dashboard_manager=self.dashboard_manager, **kwargs)
            self.server = HTTPServer(('localhost', port), handler)
            
            # Sunucuyu ayrÄ± thread'de baÅlat
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            print(f"ð GeliÅmiÅ YÃ¶netim Paneli baÅlatÄ±ldÄ±: http://localhost:{port}")
            return True
            
        except Exception as e:
            print(f"â GeliÅmiÅ yÃ¶netim paneli baÅlatÄ±lamadÄ±: {e}")
            return False
    
    def stop(self):
        """Sunucuyu durdur"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

# Ana baÅlatÄ±cÄ±
async def main():
    """Ana fonksiyon"""
    print("""
===============================================
    TRM NIRVANA v3.0 - GELÄ°ÅMÄ°Å YÃNETÄ°M PANELÄ°
===============================================
  ð Ãoklu Sayfa YapÄ±sÄ±
  ð 12 FarklÄ± Panel
  ð GerÃ§ek ZamanlÄ± Veriler
  ð Grafiksel GÃ¶sterim
  ð± Mobil Uyumlu
===============================================
    """)
    
    server = AdvancedDashboardServer()
    
    if await server.start():
        print("ð GeliÅmiÅ yÃ¶netim paneli aktif!")
        print("ð Ana panel: http://localhost:9000")
        print("ð GeliÅmiÅ panel: http://localhost:9003")
        
        try:
            # ProgramÄ± aÃ§Ä±k tut
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nð GeliÅmiÅ yÃ¶netim paneli durduruluyor...")
            server.stop()

if __name__ == "__main__":
    asyncio.run(main())
