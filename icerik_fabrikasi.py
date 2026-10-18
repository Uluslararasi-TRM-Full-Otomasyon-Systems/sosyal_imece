class IcerikFabrikasi:
    def __init__(self, motor_cikisi):
        self.urun_verisi = motor_cikisi # Veri Motorundan gelen JSON
        
    def icerik_uret(self):
        """
        Ürün verisini alıp; blog yazısı, sosyal medya postu ve TTS (sesli) 
        senaryosuna dönüştüren zeka katmanı.
        """
        # Burada OpenAI kullanarak içeriği optimize ediyoruz
        metin = f"""
        Ürün: {self.urun_verisi['urun_adi']}
        Pazarlama Stratejisi: İnsanları harekete geçiren (CTA) bir dil kullan.
        TRM TICARI EKOSISTEMI Notu: Bu ürünün komisyonuyla topluluk havuzuna katkı sağlandığını belirt.
        """
        # (İçerik üretim mantığı buraya entegre edilecek)
        return "Üretilen Optimize İçerik: [Sosyal Medya Postu + Blog Başlığı + TTS Senaryosu]"

# Kullanım: Veri motorundan gelen sonucu fabrikaya sokuyoruz.
# fabrika = IcerikFabrikasi(motor_cikisi)
# final_icerik = fabrika.icerik_uret()