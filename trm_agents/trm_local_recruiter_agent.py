
import random
import time

def random_delay(min_sec=5, max_sec=60):
    time.sleep(random.uniform(min_sec, max_sec))

def get_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0"
    ])

# -*- coding: utf-8 -*-
"""
164. TRM Yerli Piyasa ve Tedarikçi Destek Ajanı
Türkiye'deki yerli üreticileri, KOBİ'leri ve esnafları bulup sisteme dahil eder.
"""
import logging
import random
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class TRMLocalRecruiterAgent:
    def __init__(self):
        self.agent_id = 164
        self.agent_name = "TRM_Local_Recruiter"
        self.target_cities = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Gaziantep", "Şanlıurfa", "Mersin"]
        self.local_partners_db = Path(__file__).parent.parent / "local_partners.json"
        self._initialize_database()

    def _initialize_database(self):
        """Initialize local partners database file if it doesn't exist"""
        if not self.local_partners_db.exists():
            initial_data = {
                "recruited_partners": [],
                "pending_partners": [],
                "total_partners": 0
            }
            with open(self.local_partners_db, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=4)
            logger.info("✅ Yerli partner veritabanı başlatıldı.")

    def scan_local_businesses(self, city: Optional[str] = None) -> List[Dict]:
        """
        Scan for local businesses in Turkish cities
        """
        logger.info(f"🔍 {city or 'Tüm Türkiye'} piyasasında yerli firmalar taranıyor...")
        
        simulated_local_businesses = [
            {"firm_name": "İstanbul Tekstil Atölyesi", "city": "İstanbul", "business_type": "Tekstil", "contact_email": "info@istanbultextil.com"},
            {"firm_name": "Ankara El Sanatları Dükkanı", "city": "Ankara", "business_type": "El Sanatları", "contact_email": "iletisim@ankarasanat.com"},
            {"firm_name": "İzmir Organik Gıda Üreticisi", "city": "İzmir", "business_type": "Organik Gıda", "contact_email": "info@izmirorganik.com"},
            {"firm_name": "Bursa Ahşap Mobilya", "city": "Bursa", "business_type": "Mobilya", "contact_email": "bursa@mobilya.com"},
        ]
        
        logger.info(f"🎯 {len(simulated_local_businesses)} yerli firma bulundu!")
        return simulated_local_businesses

    def generate_local_pitch_message(self, firm_name: str, business_type: str) -> str:
        """
        Generate professional and sincere Turkish pitch for local businesses
        """
        pitch = f"""
Sayın {firm_name} Yönetimi,

Uzun zamandır Türkiye'nin dört bir yanında yerli üreticilerle, KOBİ'lerle ve esnafla iletişim halindeyiz, onların hikayelerini dinliyoruz. Hepimizin ortak derdi var: Ürettiklerimizi doğru kitleye ulaştırmak, reklam maliyetlerini azaltmak ve sürdürülebilir bir gelir modeli oluşturmak.

Tam da bu yüzden TRM Nirvana v3.0 Ekosistemi'ni oluşturduk. Bu sistem tamamen ÜCRETSİZ bir refah ve reklam destek modelidir. Amacımız, yerli üreticiye can suyu vermek, esnafın ürünlerini Türkiye'nin her yerine ve hatta dünyaya ulaştırmak.

Sistem nasıl çalışır?
- 164 otonom ajanımız, sizin için en uygun pazarlama stratejilerini otomatik olarak oluşturur ve uygular
- trendurunlermarket.com sitemiz, ürünleriniz için örnek ve model mağaza olarak hizmet verir
- Sosyal medya platformlarında (TikTok, Instagram, YouTube, Facebook) sizin adınıza içerikler üretilir ve yayınlanır
- Tüm bu süreçleri tek bir panelden kolayca takip edebilirsiniz
- Hiçbir ön ödeme ya da komisyon yok, tamamen destek amaçlı

Sizin hikayenizi, ürünlerinizi ve emeğinizi Türkiye'nin dört bir yanına taşımak için yanınızdayız. Haydi birlikte yerli üretimi ve yerli esnafı büyütelim!

Saygılarım ve sevgilerimle,

M. Fahri Güzel
Trend Rota Market (TRM) Kurucusu
E-Posta: mehmetfahriguzel@gmail.com
Web: trendurunlermarket.com
"""
        return pitch

    def add_local_partner_to_system(self, partner_data: Dict) -> bool:
        """
        Add local partner to central database automatically
        """
        try:
            with open(self.local_partners_db, "r", encoding="utf-8") as f:
                db = json.load(f)
            
            new_partner = {
                "partner_id": f"TRM_LOCAL_{db['total_partners'] + 1}",
                **partner_data,
                "joined_at": datetime.now().isoformat(),
                "status": "ACTIVE"
            }
            
            db["recruited_partners"].append(new_partner)
            db["total_partners"] += 1
            
            with open(self.local_partners_db, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=4)
            
            logger.info(f"✅ Yerli partner {partner_data['firm_name']} başarıyla sisteme eklendi!")
            return True
        except Exception as e:
            logger.error(f"❌ Yerli partner eklenirken hata oluştu: {str(e)}")
            return False

    def run(self):
        """Main agent run loop"""
        logger.info(f"🚀 Agent {self.agent_name} (#{self.agent_id}) başlatılıyor...")
        
        # Scan all target cities
        for city in self.target_cities:
            businesses = self.scan_local_businesses(city)
            # Simulate adding some partners
            if random.random() < 0.2:  # 20% chance for demo purposes
                selected_business = random.choice(businesses)
                logger.info(f"✨ Yerli firma {selected_business['firm_name']} sistemimize katılmak istedi!")
                self.add_local_partner_to_system(selected_business)
        
        logger.info(f"✅ Agent {self.agent_name} taramasını tamamladı.")

if __name__ == "__main__":
    agent = TRMLocalRecruiterAgent()
    agent.run()
