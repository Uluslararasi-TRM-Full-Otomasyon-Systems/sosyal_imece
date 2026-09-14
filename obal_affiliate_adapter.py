# global_affiliate_adapter.py - Küresel Afiliyet ve Çoklu Platform Dağıtım Modülü

class GlobalAffiliateAdapter:
    def __init__(self, target_platform='trendurunlermarket.com'):
        self.target_platform = target_platform
        self.global_networks = [
            {'name': 'Trend Ürünler Market', 'domain': 'trendurunlermarket.com', 'status': 'Active (Pilot)'},
            {'name': 'Global Network A', 'domain': 'example-global-store-1.com', 'status': 'Parametric Ready'},
            {'name': 'Global Network B', 'domain': 'example-global-store-2.com', 'status': 'Parametric Ready'}
        ]

    def switch_target(self, new_domain):
        self.target_platform = new_domain
        print(f'>>> [Global Adapter] Hedef platform değiştirildi: {new_domain}')

    def generate_trackable_links(self, account_id, product_sku):
        # 100 hesap için benzersiz izlenebilir afiliyet linki üretimi[cite: 2]
        return f'https://{self.target_platform}/ref/{account_id}/sku/{product_sku}'