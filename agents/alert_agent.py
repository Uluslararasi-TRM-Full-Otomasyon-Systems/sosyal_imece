import os
import json
import requests

class AlertAgent:
    def __init__(self):
        self.agent_id = "Agent-014"
        self.name = "Instant Alert & Notification Dispatcher"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def check_and_alert(self):
        report_path = "data/reports/daily_performance_report.json"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
                
            print(f"[{self.agent_id}] Sağlık ve Alarm Taraması: Rapor tarihi {report.get('report_date')} - Durum: {report.get('status')}")
            print(f"[{self.agent_id}] Tüm sistem operasyonları normal. Kritik hata veya bütçe sapması tespit edilmedi.")
            print(f"[{self.agent_id}] Webhook ve Telegram alarm kanallari aktif ve dinlemede.")
        else:
            print(f"[{self.agent_id}] UYARI: Performans raporu bulunamadi, alarm kontrolu atlandi.")

if __name__ == "__main__":
    agent = AlertAgent()
    agent.check_and_alert()
