# mouse_pilot_bot.py - Binance API Oluştur Düğmesine Tıklama Pilotu
import time
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 1.0

print("[PİLOT] Binance API düğmesine tıklamak için hazırlanıyor...")
time.sleep(2)

# Fotoğraftaki sarı "API Oluştur" butonunun ekranındaki yaklaşık koordinatları 
# (Genellikle 1920x1080 ekranda sağ üst sarı bölge: X=1350, Y=300 civarındadır. Çözünürlüğe göre test edelim)
screen_w, screen_h = pyautogui.size()
print(f"Mevcut Ekran Çözünürlüğü: {screen_w}x{screen_h}")

# Sağ üst sarı alana doğru fareyi hareket ettirip tıklayalım
# Örnek olarak ekranın sağ üst kısmına yönlendiriyoruz:
target_x = int(screen_w * 0.75)
target_y = int(screen_h * 0.28)

print(f"Fare hedefe yönlendiriliyor: X={target_x}, Y={target_y}")
pyautogui.moveTo(target_x, target_y, duration=1.5)

# Tıklama komutu
pyautogui.click()
print("[BAŞARILI] Düğmeye tıklandı! Açılan pencereyi kontrol et.")
