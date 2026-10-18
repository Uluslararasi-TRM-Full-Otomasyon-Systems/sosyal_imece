# omni_web_dashboard.py - Tarayıcı Tabanlı Canlı Omni-Panel Arayüzü
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        # Log verilerini oku
        pulse_data = "Veri yok"
        if os.path.exists("data_cluster/cloud_pulse.json"):
            with open("data_cluster/cloud_pulse.json", "r", encoding="utf-8") as f:
                logs = json.load(f)
                pulse_data = json.dumps(logs[-1], indent=2, ensure_ascii=False)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <title>Uluslararası TRM & TRM Ticari Ekosistem - Canlı Omni Panel</title>
            <style>
                body {{ background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; }}
                .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
                h1 {{ color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 15px; }}
                .card {{ background: #0f172a; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 5px solid #22c55e; }}
                pre {{ color: #a5f3fc; font-family: monospace; font-size: 14px; }}
                .status-badge {{ background: #22c55e; color: #022c22; padding: 5px 12px; border-radius: 20px; font-weight: bold; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 Uluslararası TRM & TRM Ticari Ekosistem <span class="status-badge">CANLI & AKTİF</span></h1>
                <p>60 Milyonluk Dağıtık Ağ, 100 Hesap Otonom Swarm ve Bulut Nabız Paneli</p>
                <div class="card">
                    <h3>📡 Son Bulut Nabız Verisi (Cloud Pulse)</h3>
                    <pre>{pulse_data}</pre>
                </div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode("utf-8"))

def run(server_class=HTTPServer, handler_class=DashboardHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"🚀 Canlı Web Paneli yayında! Tarayıcından şu adrese gidebilirsin: http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()