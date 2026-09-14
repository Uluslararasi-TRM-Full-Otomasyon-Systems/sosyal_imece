# viral_hook_generator.py - Anlık Viral Akım ve Kanca Üreteci
import random

class ViralHookGenerator:
    def __init__(self):
        self.viral_trends = [
            "Bu ürünü almayan bin pişman! 😱",
            "Gizli indirim kodu son 1 saat! ⚡",
            "Herkes bunu arıyordu, sonunda buldum! 🔥",
            "Stoklar tükeniyor, acele edin! 🚨"
        ]

    def get_dynamic_viral_hook(self, region):
        selected_hook = random.choice(self.viral_trends)
        print(f"[Viral Hook] Bölge: {region} | Haftanın En Çok Tıklanan Trend Kancası Seçildi: '{selected_hook}'")
        return selected_hook
