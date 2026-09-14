# dispatch_queue_manager.py - SQLite Kalıcı ve Çoklu İş Parçacıklı Kuyruk Yöneticisi
import sqlite3
import time
import threading
from datetime import datetime

class DispatchQueueManager:
    def __init__(self, db_name="trm_dispatch_queue.db"):
        self.db_name = db_name
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT,
                    post_id TEXT,
                    payload TEXT,
                    status TEXT,
                    queued_at TEXT
                )
            ''')
            conn.commit()

    def add_to_queue(self, task_item):
        queued_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = 'pending'
        payload_str = str(task_item)
        account_id = task_item.get('account_id', 'unknown')
        post_id = task_item.get('post_id', 'unknown')

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO task_queue (account_id, post_id, payload, status, queued_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (account_id, post_id, payload_str, status, queued_at))
            conn.commit()
        print(f"[Dispatch Queue DB] Yeni görev veritabanına kaydedildi: Hesap {account_id} | Post {post_id}")

    def process_single_task(self, task_row):
        task_id, account_id, post_id, payload, status = task_row
        print(f"[Worker Thread] İşleniyor -> Hesap: {account_id} | Post ID: {post_id}")
        time.sleep(1) # Dağıtım simülasyonu
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE task_queue SET status = 'completed' WHERE id = ?", (task_id,))
            conn.commit()
        print(f"[Worker Thread] Tamamlandı -> Post ID: {post_id}")

    def process_queue_parallel(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, account_id, post_id, payload, status FROM task_queue WHERE status = 'pending'")
            pending_tasks = cursor.fetchall()

        if not pending_tasks:
            print("[Dispatch Queue DB] Kuyrukta bekleyen görev bulunmuyor.")
            return

        print(f"[Dispatch Queue DB] Toplam {len(pending_tasks)} görev paralel iş parçacıklarıyla başlatılıyor...")
        threads = []
        for task_row in pending_tasks:
            t = threading.Thread(target=self.process_single_task, args=(task_row,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        print("[Dispatch Queue DB] Tüm paralel dağıtım görevleri başarıyla tamamlandı.")

if __name__ == "__main__":
    manager = DispatchQueueManager()
    manager.add_to_queue({"account_id": "hesap_101", "post_id": "TRM_PARALLEL_01"})
    manager.add_to_queue({"account_id": "hesap_102", "post_id": "TRM_PARALLEL_02"})
    manager.process_queue_parallel()
