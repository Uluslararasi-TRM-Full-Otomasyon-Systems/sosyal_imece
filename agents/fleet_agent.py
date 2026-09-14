import os
import json

class FleetManagerAgent:
    def __init__(self):
        self.agent_id = "Agent-004"
        self.name = "Fleet & Account Multiplier"
        print(f"[{self.agent_id}] {self.name} aktif edildi. 100 Kisilik Ag hazirlaniyor...")

    def multiply_tasks(self):
        if not os.path.exists("data/social_queue.json"):
            print(f"[{self.agent_id}] HATA: Temel kuyruk dosyasi bulunamadi!")
            return

        with open("data/social_queue.json", "r", encoding="utf-8") as f:
            base_queue = json.load(f)

        master_queue = []
        # 100 kişinin hesabına dağıtım simülasyonu
        for user_id in range(1, 101):
            for task in base_queue:
                cloned_task = task.copy()
                cloned_task["account_id"] = f"User-{user_id:03d}"
                cloned_task["simulation_note"] = f"{user_id}. kisinin hesabindan paylasilacak"
                master_queue.append(cloned_task)

        os.makedirs("data", exist_ok=True)
        with open("data/master_fleet_queue.json", "w", encoding="utf-8") as f:
            json.dump(master_queue, f, ensure_ascii=False, indent=4)

        print(f"[{self.agent_id}] 12 temel paylasim gorevi, 100 farkli kisinin sosyal medya hesaplarina entegre edildi.")
        print(f"[{self.agent_id}] MUAZZAM OLCEK: Toplam {len(master_queue)} adet paylasim gorevi data/master_fleet_queue.json dosyasina yazildi!")

if __name__ == "__main__":
    agent = FleetManagerAgent()
    agent.multiply_tasks()
