
import random
import time

def random_delay(min_sec=5, max_sec=60):
    time.sleep(random.uniform(min_sec, max_sec))

def get_user_agent():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0"
    ])

import os
import json
from datetime import datetime
import config

class TRMAccountingAgent:
    def __init__(self):
        self.agent_id = 165
        self.agent_name = "TRM Muhasebe ve Finans Yönetim Ajanı"
        self.version = "1.0.0"
        self.company_tax_rate = 0.20  # %20 Kurumlar Vergisi (Simülasyon)
        self.stopaj_rate = 0.10      # %10 Gider Pusulası Stopajı
        
        # Config'den finans bilgilerini al
        financial_config = config._cfg.get("financial", {})
        self.account_holder = financial_config.get("account_holder", "Mehmet Fahri Güzel")
        self.bank_name = financial_config.get("bank_name", "Kuveyt Türk Katılım Bankası AŞ.")
        self.iban = financial_config.get("iban", "TR24 0020 5000 0954 0781 5000 01")
        self.tc_kimlik_no = financial_config.get("tc_kimlik_no", "30304100922")
        
        # İletişim bilgisi
        contact_config = config._cfg.get("contact", {})
        self.primary_phone = contact_config.get("primary_phone", "+905426235116")
        
        print(f"[CONFIG] Finans bilgileri yüklendi: {self.account_holder} | {self.bank_name} | {self.iban}")
        
    def calculate_corporate_income_and_tax(self, gross_income):
        """
        Şirkete giren uluslararası affiliate ve yerli e-ticaret gelirlerini tarar,
        vergisel stopajları ve şirketin net kârını hesaplar.
        """
        tax_amount = gross_income * self.company_tax_rate
        net_profit = gross_income - tax_amount
        
        print(f"[{self.company_name}] Brüt Gelir: {gross_income} TL")
        print(f"[{self.company_name}] Hesaplanan Kurumlar Vergisi: {tax_amount} TL")
        print(f"[{self.company_name}] Net Kâr: {net_profit} TL")
        
        return {
            "gross_income": gross_income,
            "tax_amount": tax_amount,
            "net_profit": net_profit
        }

    def generate_secure_affiliate_payout_list(self, partners_data):
        """
        Dernekler masasında başımızın ağrımaması için, sisteme giren ortaklara yapılacak
        ödemeleri Anonim Şirket üzerinden yasal 'Gider Pusulası' veya 'Pazarlama Primi' olarak hazırlar.
        """
        payout_list = []
        print("\n--- A.Ş. GÜVENLİ PAZARLAMA PRİMİ VE GİDER PUSULASI LİSTESİ (MALİYE UYUMLU) ---")
        
        for partner in partners_data:
            name = partner.get("name")
            raw_payout = partner.get("earned_amount", 0)
            
            # Gider pusulası kesildiğinde yasal stopaj kesintisi simülasyonu
            deduction = raw_payout * self.stopaj_rate
            final_payout = raw_payout - deduction
            
            payout_info = {
                "partner_name": name,
                "gross_payout": raw_payout,
                "stopaj_deduction": deduction,
                "net_payout_to_bank": final_payout,
                "payment_type": "A.Ş. Reklam/Pazarlama Primi (Gider Pusulası)"
            }
            payout_list.append(payout_info)
            print(f"Hizmet Alan: {name} | Brüt Primi: {raw_payout} TL | Stopaj: {deduction} TL | Bankaya Yatacak: {final_payout} TL")
            
        return payout_list

    def calculate_dernek_sponsor_budget(self, affiliate_income, ecommerce_income, donation_percentage=0.15):
        """
        Sistemden gelen uluslararası affiliate ve yerli e-ticaret (trendurunlermarket.com) gelirlerinden
        derneğe aktarılacak sosyal sorumluluk bağış bütçesini otonom hesaplar.
        """
        total_gross_income = affiliate_income + ecommerce_income
        tax_amount = total_gross_income * self.company_tax_rate
        net_profit = total_gross_income - tax_amount
        dernek_budget = net_profit * donation_percentage
        
        print(f"\n--- DERNEK SPONSOR BÜTÇESİ HESAPLAMASI ---")
        print(f"Uluslararası Affiliate Geliri: {affiliate_income} TL")
        print(f"Yerli E-Ticaret (trendurunlermarket.com) Geliri: {ecommerce_income} TL")
        print(f"Toplam Brüt Gelir: {total_gross_income} TL")
        print(f"Kurumlar Vergisi: {tax_amount} TL")
        print(f"Net Kâr: {net_profit} TL")
        print(f"M. Fahri Güzel Derneği'ne Aktarılacak Bağış Bütçesi (%{donation_percentage*100}): {dernek_budget} TL")
        
        return {
            "affiliate_income": affiliate_income,
            "ecommerce_income": ecommerce_income,
            "total_gross_income": total_gross_income,
            "tax_amount": tax_amount,
            "net_profit": net_profit,
            "dernek_budget": dernek_budget,
            "donation_percentage": donation_percentage
        }

    def generate_burs_support_list(self, ihtiyac_sahipleri, sosyal_medya_ortaklari, dernek_budget):
        """
        Sisteme giren ihtiyaç sahiplerinin ve sosyal medya ortaklarının hak ettiği payları,
        dernek tüzüğüne uygun 'Sosyal Destek ve Burs Dağıtım Listesi' formatında raporlar.
        """
        burs_listesi = []
        toplam_need_count = len(ihtiyac_sahipleri)
        toplam_partner_count = len(sosyal_medya_ortaklari)
        
        # Bütçeyi %50 ihtiyaç sahiplerine, %50 sosyal medya ortaklarına dağıt
        ihtiyac_budget = dernek_budget * 0.5
        partner_budget = dernek_budget * 0.5
        
        print(f"\n--- SOSYAL DESTEK VE BURS DAĞITIM LİSTESİ (DERNEK TÜZÜĞÜNE UYGUN) ---")
        print(f"Toplam Bağış Bütçesi: {dernek_budget} TL")
        print(f"İhtiyaç Sahipleri İçin Ayrılan Bütçe (%50): {ihtiyac_budget} TL")
        print(f"Sosyal Medya Ortakları İçin Ayrılan Bütçe (%50): {partner_budget} TL")
        print("\n=== İHTİYAÇ SAHİPLERİ ===")
        
        # İhtiyaç sahiplerine eşit dağıtım
        if toplam_need_count > 0:
            ihtiyac_per_kisi = ihtiyac_budget / toplam_need_count
            for ihtiyac in ihtiyac_sahipleri:
                ad = ihtiyac.get("ad", "Bilinmiyor")
                tc = ihtiyac.get("tc", "******")
                burs_miktari = ihtiyac_per_kisi
                burs_listesi.append({
                    "kisi_turu": "İhtiyaç Sahibi",
                    "ad_soyad": ad,
                    "tc_kimlik": tc,
                    "burs_miktari": burs_miktari,
                    "tarih": datetime.now().strftime("%Y-%m-%d")
                })
                print(f"{ad} (TC: {tc}) | Burs Miktarı: {burs_miktari:.2f} TL")
        else:
            print("Bu dönem için ihtiyaç sahibi kaydı bulunmamaktadır.")
        
        print("\n=== SOSYAL MEDYA ORTAKLARI ===")
        
        # Sosyal medya ortaklarına eşit dağıtım
        if toplam_partner_count > 0:
            partner_per_kisi = partner_budget / toplam_partner_count
            for partner in sosyal_medya_ortaklari:
                kanal_adi = partner.get("kanal_adi", "Bilinmiyor")
                takipci_sayisi = partner.get("takipci_sayisi", 0)
                destek_miktari = partner_per_kisi
                burs_listesi.append({
                    "kisi_turu": "Sosyal Medya Ortağı",
                    "kanal_adi": kanal_adi,
                    "takipci_sayisi": takipci_sayisi,
                    "destek_miktari": destek_miktari,
                    "tarih": datetime.now().strftime("%Y-%m-%d")
                })
                print(f"{kanal_adi} (Takipçi: {takipci_sayisi}) | Destek Miktarı: {destek_miktari:.2f} TL")
        else:
            print("Bu dönem için sosyal medya ortağı kaydı bulunmamaktadır.")
        
        # Listeyi JSON olarak kaydet
        rapor_yolu = os.path.join("reports", "sosyal_destek_ve_burs_listesi.json")
        os.makedirs("reports", exist_ok=True)
        with open(rapor_yolu, "w", encoding="utf-8") as f:
            json.dump(burs_listesi, f, ensure_ascii=False, indent=2)
        
        print(f"\nBurs dağıtım listesi kaydedildi: {rapor_yolu}")
        return burs_listesi

    def allocate_dernek_donation_budget(self, net_profit, donation_percentage=0.15):
        """
        Şirket kârından M. Fahri Güzel'in Derneği'ne aktarılacak 
        resmi ve yasal 'Sosyal Sorumluluk Sponsorluk Bağışını' otonom bütçelesin.
        """
        donation_budget = net_profit * donation_percentage
        print(f"\n--- DERNEK SOSYAL SORUMLULUK VE PRESTİJ BÜTÇESİ ---")
        print(f"M. Fahri Güzel Derneği'ne Aktarılacak Resmi Sponsorluk Bağışı: {donation_budget} TL")
        print("Açıklama: Bu tutar dernek kasasına yasal bağış olarak girer, denetimde baş ağrıtmaz.")
        
        return donation_budget

    def run(self, mock_income=50000, mock_partners=None, 
            affiliate_income=30000, ecommerce_income=20000,
            ihtiyac_sahipleri=None, sosyal_medya_ortaklari=None):
        if mock_partners is None:
            mock_partners = [
                {"name": "Ahmet Yılmaz (Fahri Üye/Ortak)", "earned_amount": 5000},
                {"name": "Ayşe Demir (Fahri Üye/Ortak)", "earned_amount": 7500}
            ]
            
        if ihtiyac_sahipleri is None:
            ihtiyac_sahipleri = [
                {"ad": "Mehmet Korkmaz", "tc": "12345678901"},
                {"ad": "Zeynep Çelik", "tc": "23456789012"},
                {"ad": "Ali Yıldız", "tc": "34567890123"}
            ]
            
        if sosyal_medya_ortaklari is None:
            sosyal_medya_ortaklari = [
                {"kanal_adi": "TRM Trend TV", "takipci_sayisi": 50000},
                {"kanal_adi": "Fahri Hoca Akademi", "takipci_sayisi": 35000}
            ]
            
        print(f"\n[START] {self.agent_name} Aktif Hale Getirildi...")
        self.company_name = "M. Fahri Güzel Anonim Şirketi (Finans Motoru)"
        
        finance_summary = self.calculate_corporate_income_and_tax(mock_income)
        self.generate_secure_affiliate_payout_list(mock_partners)
        
        # Yeni eklenen fonksiyonları çalıştır
        sponsor_budget = self.calculate_dernek_sponsor_budget(affiliate_income, ecommerce_income)
        self.generate_burs_support_list(ihtiyac_sahipleri, sosyal_medya_ortaklari, sponsor_budget["dernek_budget"])
        
        self.allocate_dernek_donation_budget(finance_summary["net_profit"])
        print(f"[END] {self.agent_name} Mali Raporlamayı Tamamladı.\n")

if __name__ == "__main__":
    agent = TRMAccountingAgent()
    agent.run()