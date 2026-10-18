
import random
import time

def random_delay(min_sec=5, max_sec=60):
    time.sleep(random.uniform(min_sec, max_sec))

def get_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0"
    ])

import os
import json
from datetime import datetime

class TRMGatekeeperAgent:
    def __init__(self):
        self.agent_id = 166
        self.agent_name = "TRM Gatekeeper Ajanı"
        self.version = "1.0.0"
        self.website_url = os.getenv("TRM_PUBLIC_DOMAIN", "trendurunlermarket.com")
        self.applications_db = os.path.join("data", "gatekeeper_applications.json")
        self.support_requests_db = os.path.join("data", "gatekeeper_support_requests.json")
        self.ensure_data_directory()

    def ensure_data_directory(self):
        """Veri dizinlerinin varlığını kontrol eder ve yoksa oluşturur."""
        os.makedirs("data", exist_ok=True)
        # Veritabanı dosyalarını başlat
        if not os.path.exists(self.applications_db):
            with open(self.applications_db, "w", encoding="utf-8") as f:
                json.dump([], f)
        if not os.path.exists(self.support_requests_db):
            with open(self.support_requests_db, "w", encoding="utf-8") as f:
                json.dump([], f)

    def manage_website_api(self, mock_applications=None):
        """
        Web sitesinden gelecek ön üye başvuru form verilerini otonom olarak dinler ve toplar.
        Gerçek sistemde API veya veritabanı entegrasyonu olacaktır.
        """
        if mock_applications is None:
            # Mock başvuru verileri
            mock_applications = [
                {
                    "application_id": "APP-2026-001",
                    "name": "Mehmet Yılmaz",
                    "email": "mehmet.yilmaz@email.com",
                    "phone": "+90 555 123 4567",
                    "motivation": "Bu topluluğa katılarak hem kendimi geliştirmek hem de değerli katkılar sağlamak istiyorum. Sabırlı ve çalışkan bir insanım.",
                    "experience": "3 yıllık e-ticaret deneyimi",
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                {
                    "application_id": "APP-2026-002",
                    "name": "Ayşe Kaya",
                    "email": "ayse.kaya@email.com",
                    "phone": "+90 555 234 5678",
                    "motivation": "Hızlı para kazanmak için katılıyorum. Çok fazla çalışmak istemiyorum.",
                    "experience": "Yeni başlıyorum",
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            ]

        print("\n--- WEB SİTESİ ENTEGRASYONU: BAŞVURULAR TOPLANIYOR ---")
        print(f"Web sitesi: {self.website_url}")
        print(f"Toplanan başvuru sayısı: {len(mock_applications)}")

        # Başvuruları veritabanına kaydet
        with open(self.applications_db, "r+", encoding="utf-8") as f:
            existing_applications = json.load(f)
            for app in mock_applications:
                # Daha önce eklenmemişse ekle
                if not any(a["application_id"] == app["application_id"] for a in existing_applications):
                    existing_applications.append(app)
                    print(f"Yeni başvuru kaydedildi: {app['application_id']} - {app['name']}")
            f.seek(0)
            json.dump(existing_applications, f, ensure_ascii=False, indent=2)
            f.truncate()

        return mock_applications

    def analyze_candidate_profile(self, applications=None):
        """
        Başvuran adayların formda verdikleri yanıtları analiz eder.
        Sabır, dürüstlük ve çalışma isteğini puanlar. Suistimal potansiyeli yüksek olanları eler.
        """
        if applications is None:
            # Veritabanından son başvuruları al
            with open(self.applications_db, "r", encoding="utf-8") as f:
                applications = json.load(f)

        print("\n--- ADAY PROFİL ANALİZİ ---")
        analysis_results = []

        for app in applications:
            # Basit analiz kuralları (gerçek sistemde NLP kullanılabilir)
            motivation = app["motivation"].lower()
            
            # Puanlama kriterleri
            patience_score = 0  # Sabır puanı
            honesty_score = 0   # Dürüstlük puanı
            work_ethic_score = 0  # Çalışma isteği puanı

            # Sabır işaretleri
            patience_keywords = ["sabır", "sabırlı", "uzun süre", "devamlı", "sürekli", "istekli"]
            for keyword in patience_keywords:
                if keyword in motivation:
                    patience_score += 1

            # Dürüstlük işaretleri
            honesty_keywords = ["dürüst", "güvenilir", "şeffaf", "gerçekçi"]
            for keyword in honesty_keywords:
                if keyword in motivation:
                    honesty_score += 1

            # Çalışma isteği işaretleri
            work_keywords = ["çalışkan", "çalışmak", "üretmek", "geliştirmek", "katkı", "iş birliği"]
            for keyword in work_keywords:
                if keyword in motivation:
                    work_ethic_score += 1

            # Suistimal potansiyeli (olumsuz işaretler)
            red_flags = ["hızlı para", "kolay para", "çok çalışmak istemiyorum", "kısa yoldan", "hızlı zengin"]
            red_flag_count = 0
            for flag in red_flags:
                if flag in motivation:
                    red_flag_count += 1

            # Toplam puan ve karar
            total_score = patience_score + honesty_score + work_ethic_score
            is_approved = total_score >= 2 and red_flag_count == 0
            status = "ONAYLANDI" if is_approved else "REDDEDİLDİ"

            result = {
                "application_id": app["application_id"],
                "name": app["name"],
                "patience_score": patience_score,
                "honesty_score": honesty_score,
                "work_ethic_score": work_ethic_score,
                "total_score": total_score,
                "red_flags": red_flag_count,
                "status": status,
                "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            analysis_results.append(result)

            # Detaylı çıktı
            print(f"\nAday: {app['name']} ({app['application_id']})")
            print(f"  Sabır Puanı: {patience_score}, Dürüstlük Puanı: {honesty_score}, Çalışma İsteği: {work_ethic_score}")
            print(f"  Toplam Puan: {total_score}, Kırmızı Bayrak: {red_flag_count}")
            print(f"  SONUÇ: {status}")

        return analysis_results

    def trigger_applicant_contact(self, mock_support_requests=None):
        """
        "Formu dolduramadım, teknik desteğe ihtiyacım var" butonuna basan adaylar için
        otomatik iletişim kaydı açar ve arka plan tetikleyicisini hazırlar.
        """
        if mock_support_requests is None:
            # Mock destek talepleri
            mock_support_requests = [
                {
                    "request_id": "SUPPORT-2026-001",
                    "name": "Ali Demir",
                    "email": "ali.demir@email.com",
                    "phone": "+90 555 345 6789",
                    "issue": "Formu gönderirken hata alıyorum",
                    "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "BEKLEMEDE"
                }
            ]

        print("\n--- 'YAPAMIYORUM' DESTEK MODÜLÜ ---")
        print(f"Toplanan destek talebi sayısı: {len(mock_support_requests)}")

        # Destek taleplerini veritabanına kaydet
        with open(self.support_requests_db, "r+", encoding="utf-8") as f:
            existing_requests = json.load(f)
            for req in mock_support_requests:
                if not any(r["request_id"] == req["request_id"] for r in existing_requests):
                    existing_requests.append(req)
                    print(f"Yeni destek talebi kaydedildi: {req['request_id']} - {req['name']}")
                    print(f"  İletişim tetikleyicisi hazırlanıyor: E-posta/SMS bekleniyor...")
            f.seek(0)
            json.dump(existing_requests, f, ensure_ascii=False, indent=2)
            f.truncate()

        return mock_support_requests

    def run(self, mock_applications=None, mock_support_requests=None):
        """Ajanın ana çalışma döngüsü."""
        print(f"\n[START] {self.agent_name} Aktif Hale Getirildi...")
        print(f"Ajan ID: {self.agent_id}, Sürüm: {self.version}")

        # 1. Web sitesi entegrasyonu ve başvuruları toplama
        applications = self.manage_website_api(mock_applications)

        # 2. Aday profili analizi
        analysis_results = self.analyze_candidate_profile(applications)

        # 3. Destek talepleri yönetimi
        support_requests = self.trigger_applicant_contact(mock_support_requests)

        print(f"\n[END] {self.agent_name} Görevleri Tamamladı.")
        print(f"  Toplanan başvuru: {len(applications)}")
        print(f"  Analiz edilen aday: {len(analysis_results)}")
        print(f"  Kaydedilen destek talebi: {len(support_requests)}")

if __name__ == "__main__":
    agent = TRMGatekeeperAgent()
    agent.run()
