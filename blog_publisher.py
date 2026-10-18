# ============================================
# BLOG OTOMASYON SISTEMI
# WordPress, Blogger, Medium, Tumblr icin
# TAM OTOMATIK - 4 BLOG TEK MERKEZDEN
# ============================================

import os
import time
import random
import schedule
import requests
import threading
from datetime import datetime
from trm_live_config import load_trm_environment
from http.server import HTTPServer, BaseHTTPRequestHandler

load_trm_environment()

# ============================================
# WORDPRESS BOT
# ============================================
class WordPressBot:
    def __init__(self, site_url, username, password):
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_url = f"{self.site_url}/wp-json/wp/v2"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'TRM-Blog-Bot/1.0'
        })
    
    def gonderi_yayinla(self, baslik, icerik, etiketler=None, kategori=None):
        try:
            data = {
                'title': baslik,
                'content': icerik,
                'status': 'publish'
            }
            if etiketler:
                data['tags'] = etiketler
            if kategori:
                data['categories'] = [kategori]
            
            response = self.session.post(f"{self.api_url}/posts", json=data)
            if response.status_code == 201:
                print(f"✅ WordPress: '{baslik}' basariyla yayinlandi")
                return response.json()
            else:
                print(f"❌ WordPress hatasi: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ WordPress baglanti hatasi: {e}")
            return None


# ============================================
# BLOGGER BOT
# ============================================
class BloggerBot:
    def __init__(self, blog_id, api_key):
        self.blog_id = blog_id
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/blogger/v3"
        self.session = requests.Session()
    
    def gonderi_yayinla(self, baslik, icerik, etiketler=None):
        try:
            url = f"{self.base_url}/blogs/{self.blog_id}/posts/?key={self.api_key}"
            data = {
                'kind': 'blogger#post',
                'title': baslik,
                'content': icerik
            }
            if etiketler:
                data['labels'] = etiketler
            
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                print(f"✅ Blogger: '{baslik}' basariyla yayinlandi")
                return response.json()
            else:
                print(f"❌ Blogger hatasi: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Blogger baglanti hatasi: {e}")
            return None


# ============================================
# MEDIUM BOT
# ============================================
class MediumBot:
    def __init__(self, integration_token):
        self.token = integration_token
        self.base_url = "https://api.medium.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.user_id = self._get_user_id()
    
    def _get_user_id(self):
        try:
            response = self.session.get(f"{self.base_url}/me")
            if response.status_code == 200:
                return response.json()['data']['id']
        except:
            return None
        return None
    
    def gonderi_yayinla(self, baslik, icerik, etiketler=None, yayin_durumu='public'):
        if not self.user_id:
            print("❌ Medium: Kullanici ID alinamadi")
            return None
        
        try:
            data = {
                'title': baslik,
                'contentFormat': 'html',
                'content': icerik,
                'publishStatus': yayin_durumu
            }
            if etiketler:
                data['tags'] = etiketler[:5]
            
            url = f"{self.base_url}/users/{self.user_id}/posts"
            response = self.session.post(url, json=data)
            
            if response.status_code == 201:
                print(f"✅ Medium: '{baslik}' basariyla yayinlandi")
                return response.json()
            else:
                print(f"❌ Medium hatasi: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Medium baglanti hatasi: {e}")
            return None


# ============================================
# BASIT WEB SUNUCUSU (Render icin)
# ============================================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"TRM Blog Bot is running!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"✅ Basit web sunucusu {port} numarali portta baslatildi.")
    server.serve_forever()

threading.Thread(target=run_http_server, daemon=True).start()


# ============================================
# BLOG YONETICISI (4 BLOG BIRDEN)
# ============================================
class BlogYoneticisi:
    def __init__(self):
        print("""
╔══════════════════════════════════════════════════╗
║  📝 TRM BLOG OTOMASYON SISTEMI                  ║
║  WordPress | Blogger | Medium | Tumblr          ║
║  4 Blog Tek Merkezden Yonetim                   ║
╚══════════════════════════════════════════════════╝
        """)
        
        # WordPress Bloglari (4 blog icin)
        self.wordpress_bloglari = []
        for i in range(1, 5):
            try:
                wp = WordPressBot(
                    site_url=os.getenv(f'WP{i}_URL', ''),
                    username=os.getenv(f'WP{i}_USER', ''),
                    password=os.getenv(f'WP{i}_PASS', '')
                )
                self.wordpress_bloglari.append(wp)
            except:
                pass
        
        # Blogger Bloglari
        self.blogger_bloglari = []
        blogger1 = BloggerBot(
            blog_id=os.getenv('BLOGGER1_ID', ''),
            api_key=os.getenv('BLOGGER_API_KEY', '')
        )
        self.blogger_bloglari.append(blogger1)
        
        # Medium
        self.medium = MediumBot(
            integration_token=os.getenv('MEDIUM_TOKEN', '')
        )
        
        # Urun listesi (diger botlarla ortak)
        self.urunler = [
            {
                'id': 1,
                'ad': 'Xiaomi Akilli Bileklik',
                'fiyat': 449,
                'link': 'https://www.trendyol.com/pd/xiaomi/mi-smart-band-6-akilli-bileklik-6024890',
                'aciklama': 'Kalp atisi takibi, adim sayar, uyku analizi, 14 gun pil omru, suya dayanikli',
                'kategori': 'elektronik'
            },
            {
                'id': 2,
                'ad': 'ChefMax Dograyici',
                'fiyat': 449,
                'link': 'https://www.trendyol.com/chefmax/1000-watt-3-5-lt-cam-hazneli-dograyici-seti-p-52965241',
                'aciklama': '1000W guc, 3.5L cam hazne, 2 kademeli hiz, paslanmaz celik bicaklar',
                'kategori': 'mutfak'
            },
            {
                'id': 3,
                'ad': 'Korkmaz Titanium Tava',
                'fiyat': 199,
                'link': 'https://www.trendyol.com/korkmaz/a530-bella-titanium-tava-26-cm-p-2525668',
                'aciklama': '26 cm titanyum tava, yapismaz yuzey, tum ocaklarla uyumlu, bulasik makinesinde yikanabilir',
                'kategori': 'mutfak'
            },
            {
                'id': 4,
                'ad': 'Piper Termal Corap',
                'fiyat': 49,
                'link': 'https://www.trendyol.com/piper/erkek-termal-corap-3-lu-siyah-p-209319889',
                'aciklama': '3 lu set termal corap, kislik, yunlu, sicak tutar',
                'kategori': 'giyim'
            }
        ]
        
        print(f"✅ {len(self.wordpress_bloglari)} WordPress blogu hazir")
        print(f"✅ {len(self.blogger_bloglari)} Blogger blogu hazir")
        print("✅ Medium hazir")
        print("📦 Urun sayisi: 4")
    
    def blog_icerigi_hazirla(self, urun):
        bugun = datetime.now().strftime('%d %B %Y')
        
        icerik = f"""
<h1>{urun['ad']} - {urun['fiyat']} TL</h1>

<p><strong>Kategori:</strong> {urun['kategori']}</p>

<p>{urun['aciklama']}</p>

<h2>Urun Ozellikleri</h2>
<ul>
    <li>Yuksek kaliteli malzeme</li>
    <li>Uygun fiyat</li>
    <li>Hizli kargo</li>
    <li>Musteri memnuniyeti garantili</li>
</ul>

<p><a href="{urun['link']}" target="_blank">Urunu gormek ve satin almak icin tiklayin</a></p>

<p><em>Bu yazi {bugun} tarihinde TRM Otomasyon Sistemi tarafindan otomatik olusturulmustur.</em></p>
"""
        return icerik
    
    def tum_bloglara_paylas(self, urun):
        baslik = f"{urun['ad']} - {urun['fiyat']} TL"
        icerik = self.blog_icerigi_hazirla(urun)
        etiketler = [urun['kategori'], 'firsat', 'indirim', 'alisveris']
        
        print(f"\n[{datetime.now().strftime('%H:%M')}] 📝 BLOG PAYLASIMI BASLIYOR...")
        print(f"📦 Urun: {urun['ad']}")
        
        basarili = 0
        basarisiz = 0
        
        for blog in self.wordpress_bloglari:
            try:
                blog.gonderi_yayinla(baslik, icerik, etiketler)
                basarili += 1
            except:
                basarisiz += 1
        
        for blog in self.blogger_bloglari:
            try:
                blog.gonderi_yayinla(baslik, icerik, etiketler)
                basarili += 1
            except:
                basarisiz += 1
        
        try:
            self.medium.gonderi_yayinla(baslik, icerik, etiketler)
            basarili += 1
        except:
            basarisiz += 1
        
        print(f"📊 Blog paylasim raporu: {basarili} basarili, {basarisiz} basarisiz")
        return basarili, basarisiz
    
    def otomatik_paylasim_baslat(self):
        print("""
⏰ ZAMANLAMA AYARLARI:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 Bloglar: Gunde 2 kez (10:00 ve 16:00)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """)
        
        schedule.every().day.at("10:00").do(
            lambda: self.tum_bloglara_paylas(random.choice(self.urunler))
        )
        
        schedule.every().day.at("16:00").do(
            lambda: self.tum_bloglara_paylas(random.choice(self.urunler))
        )
        
        schedule.every(1).minutes.do(
            lambda: self.tum_bloglara_paylas(random.choice(self.urunler))
        ).tag('ilk')
        
        print("✅ Otomatik blog paylasim sistemi basladi!")
        
        time.sleep(300)
        schedule.clear('ilk')
        
        while True:
            schedule.run_pending()
            time.sleep(60)


# ============================================
# ANA PROGRAM
# ============================================
if __name__ == "__main__":
    try:
        blog = BlogYoneticisi()
        blog.otomatik_paylasim_baslat()
    except KeyboardInterrupt:
        print("\n\n🛑 Sistem durduruldu. Gorusmek uzere!")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        print("Sistem yeniden baslatiliyor...")
        time.sleep(5)
        os.system('python blog_publisher.py')
