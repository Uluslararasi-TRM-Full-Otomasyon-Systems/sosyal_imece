# ultra_nirvana_master.py - Sosyal İmece Tam Entegre Master Kontrolcüsü (Optimizasyon Katmanı Dahil)

from global_affiliate_adapter import GlobalAffiliateAdapter
from proxy_shield_manager import ProxyShieldManager
from niche_trend_scout import NicheTrendScout
from global_localization_agent import GlobalLocalizationAgent
from human_engagement_simulator import HumanEngagementSimulator
from short_video_synthesizer import ShortVideoSynthesizer
from crypto_arbitrage_scout import CryptoArbitrageScout
from dynamic_niche_profiler import DynamicNicheProfiler
from dispatch_queue_manager import DispatchQueueManager
from self_evolving_optimizer import SelfEvolvingOptimizer

class UltraNirvanaMasterSystem:
    def __init__(self, target_platform='trendurunlermarket.com'):
        self.adapter = GlobalAffiliateAdapter(target_platform)
        self.shield = ProxyShieldManager()
        self.scout = NicheTrendScout()
        self.localizer = GlobalLocalizationAgent()
        self.engagement_simulator = HumanEngagementSimulator()
        self.video_synthesizer = ShortVideoSynthesizer()
        self.crypto_scout = CryptoArbitrageScout()
        self.dnp = DynamicNicheProfiler()
        self.queue_manager = DispatchQueueManager()
        self.optimizer = SelfEvolvingOptimizer()

    def run_full_autonomous_cycle(self, account_id, region='TR', target_lang='EN'):
        print(f'>>> [Master Cycle Basladi] Hedef Platform: {self.adapter.target_platform}')
        
        # 0. Coğrafi ve Demografik İstihbarat (DNP) Analizi
        region_profile = self.dnp.analyze_region_profile(region)
        
        # 0.1 Otonom Optimizasyon: En İyi Kanca Stratejisini Seç
        optimal_hook = self.optimizer.get_best_hook_strategy()
        
        # 1. Trendleri Tara
        trends = self.scout.scan_market_trends(region)
        top_product = trends[0]
        
        # 2. Güvenli Rota Ata (Proxy & User-Agent)
        route = self.shield.get_safe_route(account_id)
        
        # 3. Afiliyet Linki Üret
        aff_link = self.adapter.generate_trackable_links(account_id, top_product['sku'])
        
        # 4. Küresel Yerelleştirme ve Evrimleşmiş Kanca Uyarlaması
        raw_copy = f"[{region_profile['demographic']} | Strateji: {optimal_hook}] {top_product['name']} - Firsati kacirma! {aff_link}"
        localized_copy = self.localizer.localize_copy(raw_copy, target_lang)
        
        # 5. Dikey Video Kreatifi Üret (Agent-303)
        video_creative = self.video_synthesizer.generate_short_creative(top_product['name'], aff_link)
        
        # 6. Kripto Sinyal Kontrolü (Agent-404)
        crypto_signal = self.crypto_scout.fetch_signal()
        
        # 7. Otonom Organik Etkileşim Zincirini Tetikle
        post_id = f"TRM_{top_product['sku'].upper()}_{random_suffix()}"
        engagement_pool = [f"hesap_{i:03d}" for i in range(1, 4)]
        self.engagement_simulator.trigger_organic_chain(post_id, primary_account=account_id, engagement_accounts=engagement_pool)

        # 8. Görevi SQLite Veritabanı Kuyruğuna Ekle
        task_payload = {
            'account_id': account_id,
            'region': region,
            'region_profile': region_profile,
            'optimal_hook': optimal_hook,
            'route': route,
            'affiliate_link': aff_link,
            'final_copy': localized_copy,
            'video_creative': video_creative,
            'crypto_signal': crypto_signal,
            'post_id': post_id,
            'engagement_status': 'success'
        }
        self.queue_manager.add_to_queue(task_payload)
        
        print(f'>>> [Master Cycle Tamamlandi] Hesap: {account_id} | Bölge: {region} | Kanca: {optimal_hook}')
        return task_payload

def random_suffix():
    import random
    return str(random.randint(1000, 9999))

if __name__ == '__main__':
    system = UltraNirvanaMasterSystem()
    
    # Optimizasyon destekli çoklu hesap döngüsü
    tasks_config = [
        ('hesap_100', 'US', 'EN'),
        ('hesap_101', 'TR', 'TR')
    ]
    
    for acc, reg, lang in tasks_config:
        system.run_full_autonomous_cycle(acc, region=reg, target_lang=lang)
        print("-" * 50)
