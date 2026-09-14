# proxy_shield_manager.py - Akıllı Proxy ve Parmak İzi Rotasyon Modülü
import random

class ProxyShieldManager:
    def __init__(self, proxy_list=None):
        self.proxy_list = proxy_list or [
            'http://proxy1.nirvana-network.internal:8080',
            'http://proxy2.nirvana-network.internal:8080',
            'http://proxy3.nirvana-network.internal:8080'
        ]
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15',
            'Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36'
        ]

    def get_safe_route(self, account_id):
        proxy = random.choice(self.proxy_list)
        ua = random.choice(self.user_agents)
        print(f'>>> [Proxy Shield] Hesap {account_id} için güvenli hat atandı.')
        return {'proxy': proxy, 'user_agent': ua}
