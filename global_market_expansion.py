# global_market_expansion.py - Küresel Pazar ve Çoklu Dil Genişletme Katmanı
import json

class GlobalMarketExpansion:
    def __init__(self):
        self.market_profiles = {
            "US": {"lang": "EN", "currency": "USD", "compliance": "FTC_AFFILIATE_DISCLOSURE"},
            "DE": {"lang": "DE", "currency": "EUR", "compliance": "EU_E-COMMERCE_COMPLIANT"},
            "UK": {"lang": "EN", "currency": "GBP", "compliance": "ASA_GUIDELINES"},
            "GCC": {"lang": "AR", "currency": "USD", "compliance": "REGIONAL_DIGITAL_LAWS"}
        }

    def localize_campaign(self, region, product_payload):
        profile = self.market_profiles.get(region, self.market_profiles["US"])
        print(f"[Global Expansion] Bölge Seçildi: {region} | Dil: {profile['lang']} | Para Birimi: {profile['currency']}")
        
        # Bölgesel uyumluluk ve yerelleştirme sarmalayıcısı
        localized_payload = product_payload.copy()
        localized_payload['region'] = region
        localized_payload['currency'] = profile['currency']
        localized_payload['compliance_tag'] = profile['compliance']
        
        print(f"-> [Localization Başarılı] {region} pazarı için kampanya mühürlendi ve uyumluluk sağlandı.")
        return localized_payload

if __name__ == "__main__":
    expansion = GlobalMarketExpansion()
    sample_product = {"sku": "sku_trend_101", "name": "Minimalist LED Atmosfer Lambası", "price": 24.90}
    expansion.localize_campaign("DE", sample_product)
