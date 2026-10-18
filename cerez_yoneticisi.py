# -*- coding: utf-8 -*-
"""
KÜRESEL TRM TICARI EKOSISTEMI - GELİŞMİŞ ÇEREZ YÖNETİCİSİ
Yazar: TRM Otomasyon Ekosistemi
Açıklama: Selenium çerezlerini güvenli bir şekilde kaydeder, yükler ve 
          sık karşılaşılan alan adı/süre aşımı hatalarını otonom olarak çözer.
"""

import os
import json
import time

class GelismisCerezYoneticisi:
    def __init__(self, platform_adi, cerez_dizini="."):
        """
        Gelişmiş Çerez Yöneticisi Başlatıcı.
        :param platform_adi: Çerezlerin ait olduğu platform (örn: 'facebook', 'instagram')
        :param cerez_dizini: Çerez dosyasının kaydedileceği klasör yolu
        """
        self.platform_adi = platform_adi.lower()
        self.cerez_dizini = cerez_dizini
        self.cerez_yolu = os.path.join(cerez_dizini, f"cerezler_{self.platform_adi}.json")

    def cerez_kaydet(self, selenium_cerezleri):
        """
        Tarayıcıdan alınan canlı Selenium çerezlerini JSON dosyasına kaydeder.
        """
        try:
            # Çerezlerin boş olup olmadığını kontrol et
            if not selenium_cerezleri:
                print(f"[-] {self.platform_adi.upper()} için kaydedilecek çerez bulunamadı.")
                return False
                
            with open(self.cerez_yolu, "w", encoding="utf-8") as f:
                json.dump(selenium_cerezleri, f, ensure_ascii=False, indent=4)
            print(f"[+] {self.platform_adi.upper()} çerezleri başarıyla şuraya kaydedildi: {self.cerez_yolu}")
            return True
        except Exception as e:
            print(f"[-] Çerez kaydedilirken hata oluştu: {e}")
            return False

    def cerez_yukle(self):
        """
        Çerez dosyasını okur ve Python listesi olarak döndürür.
        """
        try:
            if os.path.exists(self.cerez_yolu):
                with open(self.cerez_yolu, "r", encoding="utf-8") as f:
                    cerezler = json.load(f)
                    print(f"[+] {self.platform_adi.upper()} çerez dosyası yüklendi.")
                    return cerezler
            print(f"[-] {self.platform_adi.upper()} için kayıtlı çerez dosyası bulunamadı.")
            return None
        except Exception as e:
            print(f"[-] Çerez yüklenirken hata oluştu: {e}")
            return None

    def cerezleri_tarayiciya_enjekte_et(self, driver, hedef_url):
        """
        Selenium sürücüsüne (driver) çerezleri hatasız ve güvenli şekilde yükler.
        Selenium'da çerez eklemeden önce ilgili domain'e gitmek ZORUNLUDUR.
        """
        cerezler = self.cerez_yukle()
        if not cerezler:
            return False

        try:
            # Kural 1: Selenium boş sayfadayken (about:blank) çerez eklenemez.
            # Önce hedef URL'ye gidilmeli.
            if driver.current_url == "about:blank" or "data:" in driver.current_url:
                print(f"[*] Alan adı eşleşmesi için {hedef_url} adresine gidiliyor...")
                driver.get(hedef_url)
                time.sleep(2) # Sayfa yüklenene kadar küçük bir es

            print("[*] Çerezler optimize ediliyor ve tarayıcıya ekleniyor...")
            for cerez in cerezler:
                # Kural 2: Expiry (Son kullanma tarihi) float ise Selenium bazen hata verir.
                # Tam sayıya (int) çevirerek bu riski sıfırlıyoruz.
                if 'expiry' in cerez:
                    try:
                        cerez['expiry'] = int(cerez['expiry'])
                    except (ValueError, TypeError):
                        # Geçersiz bir tarih formatı varsa expiry alanını tamamen uçur
                        cerez.pop('expiry', None)

                # Kural 3: SameSite veya Secure ayarlarını tarayıcı uyumluluğu için temizleme gerekebilir
                # Bazı eski tarayıcı sürümleri katı SameSite kurallarında çökebilir.
                if 'sameSite' in cerez and cerez['sameSite'] not in ["Strict", "Lax", "None"]:
                    cerez.pop('sameSite', None)

                try:
                    driver.add_cookie(cerez)
                except Exception as cookie_err:
                    # Hatalı tek bir çerez tüm akışı bozmasın diye try-except ile sarıyoruz
                    print(f"[!] Pas geçilen geçersiz çerez ({cerez.get('name')}): {cookie_err}")

            print(f"[+] {self.platform_adi.upper()} çerez entegrasyonu tamamlandı. Sayfa yenileniyor...")
            driver.refresh()
            return True
        except Exception as e:
            print(f"[-] Tarayıcıya çerez enjekte edilirken kritik hata: {e}")
            return False
