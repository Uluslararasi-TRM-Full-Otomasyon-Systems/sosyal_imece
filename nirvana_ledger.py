import sqlite3
import json
from datetime import datetime
from typing import Dict, Any

LEDGER_DB = "trm_enterprise_ledger.db"

def init_ledger():
    conn = sqlite3.connect(LEDGER_DB)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS double_entry_ledger (
            txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            account_from TEXT,
            account_to TEXT,
            amount_tl REAL,
            category TEXT,
            metadata_json TEXT
        )
    """)
    conn.commit()
    conn.close()

def record_double_entry_transaction(from_acc: str, to_acc: str, amount_tl: float, category: str, meta: Dict[str, Any]):
    init_ledger()
    conn = sqlite3.connect(LEDGER_DB)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO double_entry_ledger (timestamp, account_from, account_to, amount_tl, category, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().isoformat(), from_acc, to_acc, amount_tl, category, json.dumps(meta, ensure_ascii=False)))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_ledger()
    record_double_entry_transaction("MAGAZANOLSUN_ESCROW", "IMECE_REFRESH_POOL", 607.2, "REFRESH_PAY", {"test": True})
    print("✅ Ledger DB initialize edildi ve örnek mutabakat yazıldı.")
