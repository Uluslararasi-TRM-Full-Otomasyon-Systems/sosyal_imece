import pywhatkit as pwk

def derya_test_mesaji_gonder():
    # Sizin telefon numaranız tanımlandı
    test_telefonu = "+905426235116"
    
    mesaj = (
        "Merhaba Mehmet Fahri Bey! 👋\n\n"
        "Ben Derya. TRM Kuşadası Müşteri Temsilcisi olarak sisteminizin test mesajını gönderiyorum.\n\n"
        "Şu an hatlarım ve otomasyon çarkımız aktif. Kuşadası'ndaki esnaflarla iletişime geçmeye, "
        "sorularını yanıtlamaya ve akıllı onay kodlarını iletmeye tamamen hazırım! 😊"
    )
    
    print(f"👩‍💼 Derya test mesajını hazırlıyor...")
    print(f"Alıcı: {test_telefonu}")
    print("⏳ WhatsApp Web açılıyor, 15 saniye içinde mesaj iletilecek...")
    
    try:
        pwk.sendwhatmsg_instantly(
            phone_no=test_telefonu, 
            message=mesaj, 
            wait_time=15, 
            tab_close=True
        )
        print("✅ Derya'nın test mesajı başarıyla gönderildi!")
    except Exception as e:
        print(f"⚠️ Gönderim sırasında hata oluştu: {e}")

if __name__ == "__main__":
    derya_test_mesaji_gonder()