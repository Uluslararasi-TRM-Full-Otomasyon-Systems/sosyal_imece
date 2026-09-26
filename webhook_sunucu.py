from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from trm_master_pipeline import master_siparis_ve_havuz_dongusu
from sosyal_ajan_bildirim import ajan_duyuru_uret

class TRMWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/webhook/trm-siparis":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            aktif_uyeler = data.get("uyeler", [
                {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
                {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
                {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
                {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
            ])
            siparis = {
                "sepet_id": data.get("sepet_id", "TRM-WEBHOOK-999"),
                "uye_id": data.get("uye_id", "APL-55-ALTIN"),
                "tutar": float(data.get("tutar", 1000.0)),
                "komisyon_orani": float(data.get("komisyon_orani", 0.20))
            }
            
            loop_res = master_siparis_ve_havuz_dongusu(siparis, aktif_uyeler)
            duyuru_res = ajan_duyuru_uret(loop_res)
            
            response_payload = {
                "status": "WEBHOOK_PROCESSED",
                "loop": loop_res,
                "duyuru": duyuru_res
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_payload, ensure_ascii=False, indent=2).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[WEBHOOK LOG] {args[0]}")

if __name__ == "__main__":
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, TRMWebhookHandler)
    print("🚀 TRM Webhook Sunucusu http://127.0.0.1:8080/webhook/trm-siparis dinlemede...")
    httpd.serve_forever()
