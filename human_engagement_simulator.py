# human_engagement_simulator.py - Otonom Organik Etkileşim ve İnsan Davranışı Simülasyonu
import time
import random
from proxy_shield_manager import ProxyShieldManager

class HumanEngagementSimulator:
    def __init__(self):
        self.proxy_manager = ProxyShieldManager()

    def simulate_human_jitter(self, min_sec=1, max_sec=3):
        """
        Agent-213: Bot imzası bırakmamak için işlemlere insani rastgele gecikmeler (jitter) ekler.
        """
        delay = random.randint(min_sec, max_sec)
        print(f"[Quantum Jitter] Algoritma maskelemesi aktif: {delay} saniye insani bekleme uygulanıyor...")
        time.sleep(delay)

    def trigger_organic_chain(self, post_id, primary_account, engagement_accounts):
        """
        Agent-201: Bir hesap içerik paylaştığında, diğer hesapların zincirleme ve doğal 
        şekilde etkileşime girmesini sağlar.
        """
        print(f"[Engagement Chain] Ana Hesap ({primary_account}) için içerik paylaşıldı. Post ID: {post_id}")
        
        for idx, account in enumerate(engagement_accounts):
            # Doğru metot adı olan get_safe_route kullanılıyor
            safe_route = self.proxy_manager.get_safe_route(account)
            
            # İnsani gecikme simülasyonu
            self.simulate_human_jitter(min_sec=1, max_sec=2)
            
            action_type = random.choice(["like_and_comment", "save_post", "share_to_story"])
            print(f"-> [Çapraz Etkileşim] Hesap: {account} | Proxy: {safe_route['proxy']} | Eylem: {action_type}")
            
        print(f"[Engagement Chain Tamamlandı] Post ID: {post_id} için organik etkileşim halkası kapatıldı.")
        return True

if __name__ == "__main__":
    simulator = HumanEngagementSimulator()
    sample_accounts = [f"hesap_{i:03d}" for i in range(1, 4)]
    simulator.trigger_organic_chain(post_id="TRM_POST_9988", primary_account="hesap_000", engagement_accounts=sample_accounts)
