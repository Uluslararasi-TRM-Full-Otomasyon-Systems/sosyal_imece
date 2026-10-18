# ============================================
# AI DESTEKLI TELEGRAM MUSTERI ASISTANI
# Claude API ile akilli cevaplar
# ============================================

import os
import telebot
import anthropic
from trm_live_config import load_trm_environment

load_trm_environment()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

bot = telebot.TeleBot(TOKEN)
claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 Merhaba! Ben TRM AI Asistan.\n\n"
        "Bana istedigin soruyu sorabilirsin: urunler, fiyatlar, kargo, stok...\n"
        "Hemen cevaplayayim! 💬"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['urunler'])
def send_products(message):
    # Urun listesini buraya ekleyebilirsin (istege bagli)
    urunler = """
    🛍️ Populer Urunlerimiz:
    - Xiaomi Akilli Bileklik - 449 TL
    - ChefMax Dograyici - 449 TL
    - Korkmaz Tava - 199 TL
    - Termal Corap - 49 TL
    """
    bot.reply_to(message, urunler)

@bot.message_handler(func=lambda m: True)
def ai_responder(message):
    """Gelen her mesaji Claude'a sor ve cevap ver"""
    try:
        # Kullanici mesajini al
        user_message = message.text
        
        # Claude'a sor
        prompt = f"""
        Bir musteri soru soruyor. Nazik, yardimsever ve kisa cevap ver.
        Musteri: {user_message}
        
        Cevap:
        """
        
        response = claude.messages.create(
            model="claude-3-sonnet-20241022",
            max_tokens=300,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        answer = response.content[0].text.strip()
        
        # Cevabi gonder
        bot.reply_to(message, answer)
        
    except Exception as e:
        bot.reply_to(message, "😔 Su anda teknik bir sorun var. Lutfen daha sonra tekrar dene.")
        print(f"Hata: {e}")

print("🤖 AI Asistan baslatildi...")
bot.infinity_polling()
