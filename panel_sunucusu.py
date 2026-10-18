#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Ekosistem Yönetim Paneli Sunucusu
HTML panelini web sunucusu olarak çalıştırır
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import TCPServer
import webbrowser
from pathlib import Path

class PanelHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Panel için özel HTTP istek işleyici"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def end_headers(self):
        """CORS ve diğer başlıkları ekle"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        """Özel log formatı"""
        print(f"[PANEL SUNUCU] {format % args}")

def panel_baslat(port=8080, otomatik_ac=True):
    """
    Panel sunucusunu başlatır
    
    Args:
        port: Port numarası (varsayılan: 8080)
        otomatik_ac: Tarayıcıyı otomatik aç (varsayılan: True)
    """
    # Panel dosyasının varlığını kontrol et
    panel_dosyasi = "TRM Ticari Ekosistem Sistemi Yönetim ve Denetim paneli.html"
    
    if not os.path.exists(panel_dosyasi):
        print(f"HATA: {panel_dosyasi} dosyasi bulunamadi!")
        print(f"Calisma dizini: {os.getcwd()}")
        return False
    
    print("=" * 60)
    print("TRM TICARI EKOSISTEMI YONETIM PANELI SUNUCUSU")
    print("=" * 60)
    print(f"Panel dosyasi: {panel_dosyasi}")
    print(f"Port: {port}")
    print(f"URL: http://localhost:{port}/{panel_dosyasi}")
    print("=" * 60)
    
    try:
        # Sunucuyu oluştur
        server = TCPServer(("0.0.0.0", port), PanelHTTPRequestHandler)
        server.allow_reuse_address = True
        
        print("Sunucu baslatiliyor...")
        print(f"Panel su adresten erisilebilir: http://localhost:{port}/{panel_dosyasi}")
        print("Durdurmak icin Ctrl+C")
        print()
        
        # Tarayıcıyı otomatik aç
        if otomatik_ac:
            url = f"http://localhost:{port}/{panel_dosyasi}"
            print(f"Tarayici aciliyor: {url}")
            webbrowser.open(url)
        
        # Sunucuyu çalıştır
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\nSunucu durduruldu")
        return True
    except OSError as e:
        if e.errno == 10048:  # Port zaten kullanımda
            print(f"HATA: Port {port} zaten kullanimda!")
            print(f"Farkli bir port deneyin: python panel_sunucusu.py --port 8081")
        else:
            print(f"Sunucu hatasi: {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TRM Ticari Ekosistem Yönetim Paneli Sunucusu")
    parser.add_argument("--port", type=int, default=8080, help="Port numarası (varsayılan: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Tarayıcıyı otomatik açma")
    
    args = parser.parse_args()
    
    panel_baslat(port=args.port, otomatik_ac=not args.no_browser)
