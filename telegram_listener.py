#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Telegram Dinleyici - Tedarikci gruplarindan urun yakalama
"""

import asyncio
import logging
import re
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

# Telethon import - eger yoksa mock kullan
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("⚠️ Telethon kurulu degil. Mock mod kullanilacak.")
    # Stub'lar - mock modda NameError olmamasi icin
    class _StubEvents:
        class NewMessage: pass
    events = _StubEvents()
    class MessageMediaPhoto: pass
    class MessageMediaDocument: pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockTelegramClient:
    """Mock Telegram client for testing"""
    def __init__(self, *args, **kwargs):
        self.session_name = kwargs.get('session', 'mock_session')
        
    async def start(self, phone=None):
        logger.info(f"Mock Telegram client baslatildi: {self.session_name}")
        return True
        
    async def disconnect(self):
        logger.info("Mock Telegram client kapatildi")
        
    def add_event_handler(self, handler, event_type=None):
        logger.info("Mock event handler eklendi")
        
    async def run_until_disconnected(self):
        while True:
            await asyncio.sleep(10)
            logger.info("Mock Telegram dinliyor...")

class TelegramProductListener:
    def __init__(self, api_id=None, api_hash=None, phone=None, session_name="trm_session"):
        self.api_id = api_id or os.getenv("TELEGRAM_API_ID", "")
        self.api_hash = api_hash or os.getenv("TELEGRAM_API_HASH", "")
        self.phone = phone or os.getenv("TELEGRAM_PHONE", "")
        self.session_name = session_name
        
        if TELETHON_AVAILABLE and self.api_id and self.api_hash:
            self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        else:
            self.client = MockTelegramClient(session=session_name)
            
        self.captured_products = []
        self.commission_keywords = [
            r"%\d+",  # %25, %30 gibi
            r"komisyon",
            r"indirim", 
            r"firsat",
            r"kampanya",
            r"yuzde",
            r"discount"
        ]
        
        # Telegram kaynak kanallari
        self.telegram_sources = [
            "magazanolsunresmi",
            "trendyolkampanya",
            "trendyolindirimleri",
            "hepsiburadakampanya",
            "amazonturkiyefirsat",
            "n11kampanyalari",
            "akakce_kampanya",
            "urunlerim_affiliate",
            "komisyonlu_urunler",
            "afiliyet_marketing_tr",
            "trendurunler", 
            "ucuzurunler",
            "indirimkosesi",
            "trendurunlermarket"
        ]
        
    async def start(self):
        """Telegram client'ini baslat"""
        try:
            await self.client.start(phone=self.phone)
            logger.info("Telegram client baslatildi")
            
            # Mesaj dinleyicilerini kur
            self.client.add_event_handler(self.handle_new_message, events.NewMessage)
            
            logger.info(f"Takip edilen kanallar: {self.telegram_sources}")
            
        except Exception as e:
            logger.error(f"Telegram baslatma hatasi: {e}")
            raise
    
    async def handle_new_message(self, event):
        """Yeni mesajlari isle - gercek parser kullanarak"""
        from telegram_parser import parse_telegram_message
        from trm_tracking import record_product

        message = event.message
        text = message.text or ""

        # Kanal kontrolu
        channel = "unknown"
        if hasattr(event, 'chat') and hasattr(event.chat, 'username'):
            channel = event.chat.username
            if channel not in self.telegram_sources:
                return
        elif hasattr(message, 'peer_id'):
            channel = str(getattr(message.peer_id, 'channel_id', 'unknown'))

        try:
            # Medya URL'lerini topla
            media_urls = []
            if hasattr(message, 'media') and message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    media_urls.append(f"photo_{message.id}.jpg")
                elif isinstance(message.media, MessageMediaDocument):
                    media_urls.append(f"doc_{message.id}.mp4")

            # YENI: Gelismis parser
            product_data = parse_telegram_message(
                text=text,
                channel=channel,
                message_id=message.id,
                media_urls=media_urls
            )

            if not product_data:
                return  # Urun bilgisi yetersiz

            # Yuksek komisyonlu urunleri logla
            if product_data['commission_rate'] >= 20.0:
                logger.info(
                    f"💰 Yuksek komisyonlu urun: {product_data['title'][:50]} "
                    f"(%{product_data['commission_rate']}, {product_data['price']} TL)"
                )

            self.captured_products.append(product_data)

            # SQLite tracking DB'ye kaydet
            product_id = record_product(product_data)
            if product_id:
                product_data['db_id'] = product_id
                logger.info(f"📊 Tracking DB ID: {product_id}")

            # JSON kuyruga da ekle (orchestrator icin)
            await self.queue_product_for_processing(product_data)

        except Exception as e:
            logger.error(f"Mesaj isleme hatasi: {e}", exc_info=True)
    
    async def extract_product_data(self, message) -> Optional[Dict]:
        """Mesajdan urun bilgilerini cikar"""
        if not message.text and not hasattr(message, 'media'):
            return None
            
        product_data = {
            'title': '',
            'description': '',
            'price': '',
            'media_urls': [],
            'links': []
        }
        
        # Metin icerigini isle
        text = message.text or ""
        
        # Basligi cikar (ilk satir genellikle basliktir)
        lines = text.split('\n')
        if lines:
            product_data['title'] = lines[0].strip()
            product_data['description'] = '\n'.join(lines[1:]).strip()
        
        # Fiyat bilgilerini cikar
        price_patterns = [
            r'(\d+(?:\.\d+)?)\s*TL',
            r'(\d+(?:\.\d+)?)\s*₺',
            r'(\d+(?:\.\d+)?)\s*turk lirasi',
            r'(\d+(?:\.\d+)?)\s*lira',
            r'(\d+(?:\.\d+)?)\s*try'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                product_data['price'] = match.group(1)
                break
        
        # Linkleri cikar
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
        urls = re.findall(url_pattern, text)
        product_data['links'] = urls
        
        # Medya dosyalarini isle
        if hasattr(message, 'media') and message.media:
            if isinstance(message.media, MessageMediaPhoto):
                # Fotograf icin mock URL
                product_data['media_urls'].append(f"photo_{message.id}.jpg")
                
            elif isinstance(message.media, MessageMediaDocument):
                # Video veya diger dosyalar icin mock URL
                product_data['media_urls'].append(f"doc_{message.id}.mp4")
        
        return product_data if product_data['title'] else None
    
    def extract_commission_rate(self, text: str) -> Optional[float]:
        """Metinden komisyon oranini cikar"""
        text_lower = text.lower()
        
        for keyword in self.commission_keywords:
            if keyword in text_lower:
                # Sayisal degeri bul
                number_pattern = r'(\d+(?:\.\d+)?)'
                matches = re.findall(number_pattern, text)
                if matches:
                    try:
                        # Yuzde isareti varsa onu kullan
                        if '%' in text:
                            for match in matches:
                                if int(match) <= 100:  # %100'den kucuk olmali
                                    return float(match)
                        else:
                            # Komisyon kelimesi geciyorsa ilk sayiyi al
                            return float(matches[0])
                    except ValueError:
                        continue
        return None
    
    async def queue_product_for_processing(self, product_data: Dict):
        """Urunu isleme kuyruguna ekle (trm_veritabani.db, cakismasiz)"""
        try:
            from trm_db import trm_db
            trm_db().kuyruga_ekle("product_queue", product_data)
            logger.info(f"Urun isleme kuyruguna eklendi: {product_data['title']}")
        except Exception as exc:
            logger.error(f"Urun kuyruga eklenemedi: {product_data['title']} ({exc})")
    
    async def run(self):
        """Ana calisma dongusu"""
        await self.start()
        logger.info("Telegram dinleyici calisiyor...")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Telegram dinleyici durduruluyor")
        except Exception as e:
            logger.error(f"Telegram dinleyici hatasi: {e}")
        finally:
            if hasattr(self.client, 'disconnect'):
                await self.client.disconnect()

# Test ve ornek kullanim
async def test_telegram_listener():
    """Telegram dinleyiciyi test et"""
    listener = TelegramProductListener()
    logger.info("Telegram dinleyici test ediliyor...")
    
    # Test urunu ekle
    test_product = {
        'title': 'Test Urunu - %25 Komisyon',
        'description': 'Harika bir test urunu',
        'price': '299 TL',
        'commission_rate': 25,
        'priority': 'high',
        'captured_at': datetime.now().isoformat(),
        'source': 'test',
        'message_id': 999
    }
    
    await listener.queue_product_for_processing(test_product)
    logger.info("Test urunu kuyruga eklendi")

if __name__ == "__main__":
    asyncio.run(test_telegram_listener())
