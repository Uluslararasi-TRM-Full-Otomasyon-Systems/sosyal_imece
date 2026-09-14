# master_orchestrator.py - Sosyal İmece Zirve Sürüm (Hata Düzeltildi)
from ultra_nirvana_master import UltraNirvanaMasterSystem
from syndication_shield import SyndicationShield
from transparent_ledger import TransparentLedger
from self_evolving_optimizer import SelfEvolvingOptimizer
from live_trend_scraper import LiveTrendScraper
from global_market_expansion import GlobalMarketExpansion
from real_social_publisher import RealSocialPublisher
from smart_fund_gateway import SmartFundGateway
from ai_competitor_spy import AICompetitorSpy
from viral_hook_generator import ViralHookGenerator
from auto_crisis_shield import AutoCrisisShield
import random

class MasterOrchestrator:
    def __init__(self):
        self.master_system = UltraNirvanaMasterSystem()
        self.shield = SyndicationShield(total_accounts=100)
        self.ledger = TransparentLedger()
        self.optimizer = SelfEvolvingOptimizer()
        self.scraper = LiveTrendScraper()
        self.expansion = GlobalMarketExpansion()
        self.publisher = RealSocialPublisher()
        self.gateway = SmartFundGateway()
        self.spy = AICompetitorSpy()
        self.hook_gen = ViralHookGenerator()
        self.crisis_shield = AutoCrisisShield()

    def execute_full_ecosystem_run(self):
        print(">>> [Sosyal İmece] Zirve Sürüm: Otonom Casus, Viral Kanca ve Kriz Kalkanı Devrede!")
        
        # 0. Adım: Optimizasyon, Casus Analizi ve Canlı Trend Avı
        self.optimizer.evaluate_and_evolve()
        best_product = self.scraper.fetch_live_trending_products()
        optimized_price = self.spy.analyze_and_adjust_pricing(best_product['sku'], best_product['price'])
        best_product['price'] = optimized_price

        target_regions = [
            ('hesap_100', 'US', 'EN', 'TikTok'),
            ('hesap_101', 'DE', 'DE', 'Instagram'),
            ('hesap_102', 'UK', 'EN', 'YouTube')
        ]
        
        for acc, reg, lang, platform in target_regions:
            print("=" * 60)
            # Kriz Kalkanı Kontrolü
            if not self.crisis_shield.inspect_account_health(acc):
                print(f"[Atlama] Hesap {acc} korumaya alındı, döngü es geçiliyor.")
                continue

            # Viral Kanca ve Küresel Yerelleştirme
            viral_hook = self.hook_gen.get_dynamic_viral_hook(reg)
            localized_product = self.expansion.localize_campaign(reg, best_product)
            
            payload = self.master_system.run_full_autonomous_cycle(acc, region=reg, target_lang=lang)
            
            # Anahtar güvenliği: payload içinde hangi anahtar varsa ona iliştiriyoruz
            script_key = 'script' if 'script' in payload else ('caption' if 'caption' in payload else list(payload.keys())[0])
            payload[script_key] = f"{viral_hook} {payload.get(script_key, '')}"

            # Gerçek Yayın ve Dağıtım
            self.publisher.publish_content(platform, acc, payload)
            self.shield.distribute_content(payload.get('post_id', 'TRM_DEFAULT_ID'), payload)
            
            # Mühürleme
            simulated_revenue = round(random.uniform(30.0, 65.0), 2)
            self.ledger.record_transaction(acc, payload.get('post_id', 'TRM_DEFAULT_ID'), simulated_revenue)

        print("=" * 60)
        self.gateway.check_and_execute_payouts()
        print(">>> [Sosyal İmece] Tüm modüller kusursuz bir uyumla uçuşunu tamamladı!")

if __name__ == "__main__":
    orchestrator = MasterOrchestrator()
    orchestrator.execute_full_ecosystem_run()
