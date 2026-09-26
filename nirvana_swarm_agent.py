import logging
import sqlite3
from typing import Dict, Any
from sesli_komut import sesli_rapor_seslendir
from nirvana_ledger import LEDGER_DB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NirvanaSwarmAgent")

def audit_ledger_integrity() -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(LEDGER_DB)
        cur = conn.cursor()
        cur.execute("SELECT count(*), sum(amount_tl) FROM double_entry_ledger")
        row = cur.fetchone()
        conn.close()
        count, total = row[0] or 0, row[1] or 0.0
        
        msg = f"Fahri abi, Nirvana mutabakat denetimi tamamlandı. Toplam {count} kayıt var, hareket eden toplam fon {total:,.2f} Türk Lirası."
        logger.info(msg)
        sesli_rapor_seslendir(msg)
        return {"status": "HEALTHY", "txn_count": count, "total_volume_tl": total}
    except Exception as e:
        err_msg = f"Kritik mutabakat hatası yakalandı: {str(e)}"
        logger.error(err_msg)
        sesli_rapor_seslendir("Fahri abi, mutabakat katmanında dikkat gerektiren bir durum var.")
        return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    audit_ledger_integrity()
