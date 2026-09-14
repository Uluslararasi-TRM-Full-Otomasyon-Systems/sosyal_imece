import sys
import os
import json
import time

from agents.trend_agent import TrendProductAgent
from agents.social_agent import SocialQueueAgent
from agents.logger_agent import ExecutionLoggerAgent
from agents.fleet_agent import FleetManagerAgent
from agents.fleet_logger_agent import FleetExecutionLoggerAgent
from agents.affiliate_agent import AffiliateInjectorAgent
from agents.content_generator_agent import ContentVariationAgent
from agents.shield_agent import SafetyShieldAgent
from agents.live_broadcast_agent import LiveBroadcastAgent
from agents.analytics_agent import AnalyticsAgent
from agents.rate_proxy_agent import RateProxyAgent
from agents.self_healing_agent import SelfHealingAgent
from agents.database_sync_agent import DatabaseSyncAgent
from agents.alert_agent import AlertAgent
from agents.live_api_gateway_agent import LiveApiGatewayAgent
from agents.session_rotation_agent import SessionRotationAgent
from agents.live_webhook_notifier import LiveWebhookNotifier
from agents.conversion_optimizer_agent import ConversionOptimizerAgent
from agents.budget_reinvestment_agent import BudgetReinvestmentAgent
from agents.content_compliance_agent import ContentComplianceAgent
from agents.support_chatbot_agent import SupportChatbotAgent
from agents.imece_pool_distribution_agent import ImecePoolDistributionAgent

class SosyalImeceOrchestrator:
    def __init__(self):
        self.mode = "SIMULATION"
        if os.path.exists("config.env"):
            with open("config.env", "r", encoding="utf-8") as f:
                for line in f:
                    if "SYSTEM_MODE=" in line:
                        parts = line.strip().split("=")
                        if len(parts) > 1:
                            self.mode = parts[1].strip()

        print(f"[INIT] Sosyal Imece Ekosistemi baslatildi. Mod: {self.mode}")

    def ignite_system(self):
        print(f"\n[FIRE] 22 Ajanli Tam Otonom Sosyal Imece & IR-SA A.S. Master Dongu Baslatiliyor...\n" + "="*70)

        # -1. Adım: Veri Bütünlüğü (Agent-012)
        print("\n--> ADIM -1: Veri Butunlugu ve Self-Healing Taramasi...")
        healer = SelfHealingAgent()
        healer.audit_and_heal()

        # 0. Adım: Güvenlik Kalkanı (Agent-008)
        print("\n--> ADIM 0: Guvenlik Kalkani ve Butce Denetimi...")
        shield = SafetyShieldAgent()
        if not shield.audit_system():
            print("[CRITICAL] Guvenlik denetimi basarisiz! Sistem durduruluyor.")
            return

        # 1. Adım: Trend Ürün Tarama (Agent-001)
        print("\n--> ADIM 1: Trend ve Urun Tarama Baslatiliyor...")
        agent_1 = TrendProductAgent()
        agent_1.fetch_simulated_products()

        # 2. Adım: Sosyal Medya Kuyruğu (6 Hesap Kuralı) (Agent-002)
        print("\n--> ADIM 2: Sosyal Medya Kuyrugu Olusturuluyor (6 Hesap Kurali)...")
        agent_2 = SocialQueueAgent()
        agent_2.build_queue()

        # 3. Adım: Simülasyon (Agent-003)
        print("\n--> ADIM 3: Temel Simulasyon ve Loglama Calistiriliyor...")
        agent_3 = ExecutionLoggerAgent()
        agent_3.process_queue()

        # 4. Adım: Filo Ölçeklendirmesi (Agent-004)
        print("\n--> ADIM 4: Katilimci Hesaplari Filo Olceklendirmesi Yapiliyor...")
        agent_4 = FleetManagerAgent()
        agent_4.multiply_tasks()

        # 5. Adım: IR-SA A.Ş. Affiliate Komisyon Enjeksiyonu (Agent-006)
        print("\n--> ADIM 5: IR-SA A.S. Affiliate Komisyon Linkleri Enjekte Ediliyor...")
        agent_6 = AffiliateInjectorAgent()
        agent_6.inject_links()

        # 6. Adım: İçerik Varyasyonları (Agent-007)
        print("\n--> ADIM 6: Platform Bazli Icerik Varyasyonlari Olusturuluyor...")
        agent_7 = ContentVariationAgent()
        agent_7.generate_variations()

        # 6.1. Adım: Dijital İmza ve Uyumluluk (Agent-020)
        print("\n--> ADIM 6.1: Dijital Imza ve Algoritma Uyumlulugu Denetimi...")
        agent_20 = ContentComplianceAgent()
        agent_20.secure_content()

        # 6.2. Adım: Oturum ve Proxy Rotasyonu (Agent-016)
        print("\n--> ADIM 6.2: Dinamik Proxy ve Oturum Çerezleri Rotasyonu...")
        agent_16 = SessionRotationAgent()
        agent_16.rotate_sessions()

        # 6.5. Adım: Rate-Limit Güvencesi (Agent-011)
        print("\n--> ADIM 6.5: Proxy ve Rate-Limit Guvencesi Uygulaniyor...")
        agent_11 = RateProxyAgent()
        agent_11.optimize_traffic_flow()

        # 7. Adım: Master Filo İcrası (Agent-005)
        print("\n--> ADIM 7: Master Filo İcra ve Denetimi Baslatiliyor...")
        agent_5 = FleetExecutionLoggerAgent()
        agent_5.process_fleet_queue()

        # 7.2. Adım: Canlı API Ağ Geçidi (Agent-015)
        print("\n--> ADIM 7.2: Canli API Ag Gecidi ve Uretim Sevkiyati...")
        agent_15 = LiveApiGatewayAgent()
        agent_15.dispatch_live_payloads()

        # 7.5. Adım: Veritabanı Senkronizasyonu (Agent-013)
        print("\n--> ADIM 7.5: Merkezi Veritabani Senkronizasyonu Yapiliyor...")
        agent_13 = DatabaseSyncAgent()
        agent_13.sync_to_db()

        # 8. Adım: Canlı Dağıtım ve Webhook (Agent-009 & Agent-017)
        print("\n--> ADIM 8: Canli Dagitim, Webhook ve Telegram Bildirimleri...")
        agent_9 = LiveBroadcastAgent()
        agent_9.broadcast_tasks()
        
        agent_17 = LiveWebhookNotifier()
        agent_17.send_live_alert("IR-SA A.S. komisyon gorevleri uretim hattindan basariyla gecirildi.")

        # 8.2. Adım: Otonom Destek ve Yönlendirme (Agent-021)
        print("\n--> ADIM 8.2: Otonom Musteri Yonlendirme ve Etkilesim...")
        agent_21 = SupportChatbotAgent()
        agent_21.monitor_engagement()

        # 8.5. Adım: CTR Optimizasyonu ve İmece Havuz Dağıtımı (Agent-018, Agent-019 & Agent-022)
        print("\n--> ADIM 8.5: CTR Optimizasyonu ve Imece Havuz Sosyal Adalet Dagitimi...")
        agent_18 = ConversionOptimizerAgent()
        agent_18.optimize_conversions()
        
        agent_19 = BudgetReinvestmentAgent()
        agent_19.optimize_budgets()

        agent_22 = ImecePoolDistributionAgent()
        agent_22.process_financial_distribution()

        # 9. Adım: Analitik ve Gelir Raporu (%70 / %30 Dağıtım Özeti) (Agent-010)
        print("\n--> ADIM 9: Analitik ve Komisyon Gelir Raporu Olusturuluyor...")
        agent_10 = AnalyticsAgent()
        agent_10.generate_report()

        # 10. Adım: Sağlık Denetimi (Agent-014)
        print("\n--> ADIM 10: Sistem Alarm ve Saglik Denetimi Yapiliyor...")
        agent_14 = AlertAgent()
        agent_14.check_and_alert()

        print("\n" + "="*70)
        print("[SUCCESS] Tum 22 ajanli Sosyal Imece & IR-SA A.S. otonom sistemi kusursuzca tamamlandi!")

if __name__ == "__main__":
    engine = SosyalImeceOrchestrator()
    engine.ignite_system()
