import os

# Sistemin ana dizinini (TRM TICARI EKOSISTEMI) otomatik bulur
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class KureselVideoFabrikasiAjani:
    """Küresel pazarlar için otonom video içerikleri üreten ajan."""

    def __init__(self, agent_name="Video_Fabrikası"):
        self.agent_name = agent_name
        # Dosya yollarını işletim sistemi bağımsız tanımlıyoruz
        self.output_dir = os.path.join(BASE_DIR, "path", "to")

    def produce_content(self, product, language):
        """İçerik üretimi simülasyonu."""
        # Klasör yoksa oluştur (bulut için kritik)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        print(f"[FABRİKA] {language} dilinde içerik üretiliyor...")
        video_name = f"viral_video_{hash(product + language)}.mp4"
        video_path = os.path.join(self.output_dir, video_name)
        
        # Simülasyon: Dosyayı oluştur
        with open(video_path, 'w', encoding='utf-8') as f:
            f.write(f"Video content for {product} in {language}")
            
        print(f"[BAŞARI] Video hazır: {video_path}")
        return video_path

# Orkestratör için tetikleyici
def trigger_video_production(product, language):
    factory = KureselVideoFabrikasiAjani()
    return factory.produce_content(product, language)