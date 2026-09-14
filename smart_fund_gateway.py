# smart_fund_gateway.py - Kripto ve Akıllı Sözleşme Fon Dağıtım Kapısı
import sqlite3
import datetime

class SmartFundGateway:
    def __init__(self, db_name='trm_immutable_ledger.db', payout_threshold=50.0):
        self.db_name = db_name
        self.payout_threshold = payout_threshold

    def check_and_execute_payouts(self):
        print("[Smart Fund Gateway] Dağıtım havuzu taranıyor...")
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Toplam mühürlü fon miktarını hesapla
            cursor.execute("SELECT SUM(revenue_share) FROM ledger_records")
            result = cursor.fetchone()
            total_funds = result[0] if result and result[0] else 0.0
            
            print(f"-> Toplam Biriken Sosyal Etki Fonu: ${total_funds:.2f} | Eşik Değer: ${self.payout_threshold:.2f}")
            
            if total_funds >= self.payout_threshold:
                print(f"[AKILLI SÖZLEŞME TETİKLENDİ] Fon eşik değere ulaştı! Otomatik transfer başlatılıyor...")
                payout_id = f"PAYOUT_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Hak sahiplerine / Vakıf cüzdanına (UTEYKDER) dağıtım simülasyonu
                print(f"-> [Smart Contract] Transfer ID: {payout_id} | Tutar: ${total_funds:.2f} | Durum: BAŞARILI (On-Chain Locked)")
                return True
            else:
                print(f"-> Fon henüz eşik değerin altında. Birikim devam ediyor...")
                return False
                
        except Exception as e:
            print(f"[Hata] Fon dağıtım kapısı hatası: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    gateway = SmartFundGateway()
    gateway.check_and_execute_payouts()
