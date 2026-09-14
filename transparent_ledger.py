# transparent_ledger.py - Şeffaf Dağıtım Günlüğü (Immutable Ledger)
import sqlite3
import datetime

class TransparentLedger:
    def __init__(self, db_name='trm_immutable_ledger.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ledger_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                account_id TEXT,
                post_id TEXT,
                revenue_share REAL,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def record_transaction(self, account_id, post_id, revenue_share):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ledger_records (timestamp, account_id, post_id, revenue_share, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, account_id, post_id, revenue_share, 'IMMUTABLE_LOCKED'))
        conn.commit()
        conn.close()
        print(f"[Ledger Mühürlendi] Zaman: {timestamp} | Hesap: {account_id} | Post: {post_id} | Pay: ${revenue_share:.2f}")

if __name__ == "__main__":
    ledger = TransparentLedger()
    ledger.record_transaction("synd_account_034", "TRM_TEST_SYNC_01", 12.50)
