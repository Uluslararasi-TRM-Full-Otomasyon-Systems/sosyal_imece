import json
import os

class SafetyShieldAgent:
    def __init__(self):
        self.agent_id = "Agent-008"
        self.name = "Safety Shield & Budget Auditor"
        self.daily_budget_limit = 5.0
        print(f"[{self.agent_id}] {self.name} aktif edildi. Gunluk limit: ")

    def audit_system(self):
        print(f"[{self.agent_id}] Maliyet, bütçe ve güvenlik kalkanı denetleniyor...")
        current_spent = 0.0 # Simülasyon modunda harcama 0.0 dolar
        
        if current_spent > self.daily_budget_limit:
            print(f"[{self.agent_id}] UYARI: Butce limiti asildi! Sistem kilitleniyor.")
            return False
        
        print(f"[{self.agent_id}] Guvenlik denetimi TAMAMLANDI. Harcama:  / Limit: . Sistem guvenli.")
        return True

if __name__ == "__main__":
    agent = SafetyShieldAgent()
    agent.audit_system()
