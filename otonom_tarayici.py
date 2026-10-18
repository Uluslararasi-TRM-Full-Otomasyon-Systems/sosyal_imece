import os
import time
import json
from openai import OpenAI

class OtonomVeriMotoru:
    def __init__(self):
        # OpenAI API bağlantısı (gstack-main mimarisinden esinlenilmiştir)
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "APİ_ANAHTARINIZ"))
        
    def sayfa_analiz_et(self, url, html_icerik):
        """
        gstack-main 'browse-skills' mantığı: Yapay zeka ham HTML verisini okur,
        insan gibi analiz eder ve affiliate fırsatlarını filtreler.
        """
        uyari_promptu = f"""
        Sen TRM TICARI EKOSISTEMI ekosisteminin veri analiz ajanısın.
        Aşağıdaki web sayfasının içeriğini incele ve Amazon/Clickbank affiliate kurallarına uygun,
        en yüksek komisyon getirebilecek trend ürün verilerini, fiyatını ve avantajlarını çıkar.
        
        Sayfa URL: {url}
        Ham İçerik: {html_icerik[:4000]}... (Veri sınırlandırıldı)
        
        Çıktıyı kesinlikle şu JSON formatında ver:
        {{
            "urun_adi": "Ürün İsmi",
            "fiyat": "Fiyat",
            "komisyon_tahmini": "Tahmini % veya Tutar",
            "neden_trend": "Kısa açıklama"
        }}
        """
        
        yanit = self.client.chat.completions.create(
            model="gpt-4o-mini", # Sistemi yormayacak, hızlı ve ekonomik model
            messages=[{"role": "user", "content": uyari_promptu}],
            response_format={"type": "json_object"}
        )
        return json.loads(yanit.choices[0].message.content)

# Test Kullanımı
if __name__ == "__main__":
    motor = OtonomVeriMotoru()
    # Örnek bir ham veri simülasyonu
    örnek_html = "<h1>Super Wireless Headphones</h1><span class='price'>$99</span><p>Best selling item of the month with 20% commission rate.</p>"
    sonuc = motor.sayfa_analiz_et("https://amazon.com/example-product", örnek_html)
    print("Ajanın Bulduğu Fırsat:", json.dumps(sonuc, indent=4, ensure_ascii=False))