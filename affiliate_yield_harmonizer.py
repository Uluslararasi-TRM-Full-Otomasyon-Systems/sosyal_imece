import os
import json
from datetime import datetime

class AffiliateYieldHarmonizer:
    def __init__(self):
        self.ledger_path = "data_cluster/yield_ledger.json"
        os.makedirs("data_cluster", exist_ok=True)

    def harmonize_and_distribute(self, total_revenue):
        """trendurunlermarket.com ve trendurunlermarket.com gelirlerini otonom olarak havuzda dengeler."""
        tmu_share = total_revenue * 0.70  # %70 Sistem Büyüme & Operasyon
        imece_share = total_revenue * 0.30 # %30 UTEYKDER / TRM Ticari Ekosistem Fonu
        
        ledger_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_revenue": total_revenue,
            "tmu_operational_fund": tmu_share,
            "sosyal_imece_fund": imece_share,
            "status": "HARMONIZED"
        }

        with open(self.ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger_entry, f, indent=4)

        print(f"💰 [Yield Harmonizer] Toplam Gelir Dağıtıldı: {total_revenue} TL -> Refah Fonu: {imece_share} TL")
        return ledger_entry

if __name__ == "__main__":
    harmonizer = AffiliateYieldHarmonizer()
    harmonizer.harmonize_and_distribute(100000.0) # Örnek 100k ciro simülasyonu