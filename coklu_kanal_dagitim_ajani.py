from copy import deepcopy
import os
from pathlib import Path
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager
from ilk_uc_saniye_motoru import kanca_ekle


KANALLAR = (
    "Telegram / WhatsApp Duyuru Kanalı",
    "Blogger / Medium / WordPress Blog Akışı",
    "TikTok / Reels Video Kuyruğu",
)


class CokluKanalDagitimAjani:
    def __init__(self, urun_adi, urun_aciklamasi="", urun_link=""):
        if not isinstance(urun_adi, str) or not urun_adi.strip():
            raise ValueError("urun_adi boş olmayan bir metin olmalıdır")
        for value, field in ((urun_aciklamasi, "urun_aciklamasi"), (urun_link, "urun_link")):
            if not isinstance(value, str):
                raise ValueError(f"{field} metin olmalıdır")

        self.urun_adi = urun_adi.strip()
        self.urun_aciklamasi = urun_aciklamasi.strip()
        self.urun_link = urun_link.strip()

    def otonom_yayina_basla(self, kanallar=None):
        """Seçilen kanallar için taslak hazırlar; dış servise yayın yapmaz."""
        selected_channels = list(KANALLAR if kanallar is None else kanallar)
        if not selected_channels:
            raise ValueError("En az bir kanal seçilmelidir")
        if not all(isinstance(channel, str) for channel in selected_channels):
            raise ValueError("Kanal adları metin olmalıdır")
        if len(set(selected_channels)) != len(selected_channels):
            raise ValueError("Aynı kanal birden fazla seçilemez")
        unknown_channels = set(selected_channels) - set(KANALLAR)
        if unknown_channels:
            raise ValueError(f"Desteklenmeyen kanallar: {', '.join(sorted(unknown_channels))}")

        hook = kanca_ekle(self.urun_adi, "Genel kitle")
        content = {
            "baslik": self.urun_adi,
            "kanca": hook,
            "metin": self.urun_aciklamasi or self.urun_adi,
            "urun_linki": self.urun_link or None,
        }
        return [
            {
                "kanal": channel,
                "durum": "Taslak hazır; dış kanala gönderilmedi",
                "icerik": deepcopy(content),
            }
            for channel in selected_channels
        ]

    def inceleme_kuyruguna_ekle(self, dagitim_paketi, db_path=None):
        if not isinstance(dagitim_paketi, list) or not dagitim_paketi:
            raise ValueError("İncelemeye eklenecek kanal taslakları gereklidir")

        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        manager = DispatchQueueManager(db_name=str(queue_path))
        queued_tasks = []
        for item in dagitim_paketi:
            if not isinstance(item, dict) or item.get("kanal") not in KANALLAR or not isinstance(item.get("icerik"), dict):
                raise ValueError("Kanal taslağı geçersiz")
            task = {
                "account_id": "multichannel_broadcaster",
                "post_id": f"channel-draft-{uuid4().hex}",
                "payload": {
                    "task_type": "multichannel_publication_review",
                    "status": "pending_review",
                    "channel": item["kanal"],
                    "content": deepcopy(item["icerik"]),
                },
            }
            manager.add_to_queue(task)
            queued_tasks.append(task)
        return queued_tasks