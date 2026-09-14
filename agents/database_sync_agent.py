import os
import json
import sqlite3
from datetime import datetime

class DatabaseSyncAgent:
    def __init__(self):
        self.agent_id = "Agent-013"
        self.name = "Automated Database Sync Master"
        print(f"[{self.agent_id}] {self.name} aktif edildi.")

    def sync_to_db(self):
        db_path = "data/trm_ecosystem.db"
        os.makedirs("data", exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabloları oluştur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fleet_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_date TEXT,
                account_id TEXT,
                product_name TEXT,
                platform TEXT,
                proxy_assigned TEXT,
                status TEXT
            )
        ''')
        
        queue_path = "data/master_fleet_queue.json"
        if os.path.exists(queue_path):
            with open(queue_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
                
            # Verileri toplu olarak SQL veritabanına aktar
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            records = [
                (now, item.get("account_id"), item.get("product_name"), item.get("platform"), item.get("proxy_assigned", "local"), item.get("status", "SUCCESS"))
                for item in queue
            ]
            
            cursor.executemany('''
                INSERT INTO fleet_executions (execution_date, account_id, product_name, platform, proxy_assigned, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', records)
            
            conn.commit()
            print(f"[{self.agent_id}] Toplam {len(records)} gorev merkezi SQLite veritabanina ({db_path}) basariyla senkronize edildi.")
        else:
            print(f"[{self.agent_id}] UYARI: Senkronize edilecek kuyruk bulunamadi.")
            
        conn.close()

if __name__ == "__main__":
    agent = DatabaseSyncAgent()
    agent.sync_to_db()
