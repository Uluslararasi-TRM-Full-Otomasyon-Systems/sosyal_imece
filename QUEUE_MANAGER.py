#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TRM Queue Manager v6.0 — SQLite (trm_veritabani.db) destekli kuyruk yönetimi.

Eski sürüm data/queues/<ad>.json + filelock ile çalışıyordu; dosya kilitleri
zaman aşımına uğradığında push/pop sessizce başarısız oluyordu. Yeni sürüm
tüm kuyruk verisini merkezi trm_veritabani.db içindeki is_kuyrugu tablosunda
tutar:

- Yazmalar trm_db'nin tek yazıcı thread'inden sırayla geçer → çakışma yok.
- pop() tek transaction içinde SELECT+DELETE yapar → aynı iş iki kez alınamaz.
- Öncelik (oncelik) küçük olan önce; eşitlikte FIFO.
- clear_stale() eski kayıtları verimli tek DELETE ile temizler.
- backup() kuyruğun anlık görüntüsünü data/queue_backups/ içine JSON olarak
  dışa aktarır (insan tarafından okunabilir yedek; ana depolama DB'dir).

Public API eski sürümle birebir aynıdır (push, push_many, pop, peek, size,
clear_stale, backup, status) — mevcut çağıran kod değişikliği gerektirmez.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from trm_db import trm_db, _json_yaz, _json_coz

logger = logging.getLogger('TRMQueue')

BASE_DIR = Path(__file__).parent.resolve()
BACKUP_DIR = BASE_DIR / 'data' / 'queue_backups'
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class QueueManager:
    """trm_veritabani.db/is_kuyrugu üzerinde çalışan kuyruk yöneticisi.

    Tüm işlemler merkezi yazıcı kuyruğundan geçtiği için thread ve süreç
    güvenlidir; dosya kilidi (filelock) gereksizdir.
    """

    def __init__(self, name: str):
        self.name = name
        self.db = trm_db()

    # ── Yazma ────────────────────────────────────────────────────────────

    def push(self, item: Dict, oncelik: int = 5) -> bool:
        """Kuyruğa tek iş ekler. queued_at otomatik yazılır."""
        try:
            item['queued_at'] = datetime.now().isoformat()
            self.db.kuyruga_ekle(self.name, item, oncelik=int(oncelik))
            return True
        except Exception as exc:
            logger.error(f'[{self.name}] push başarısız: {exc}')
            return False

    def push_many(self, items: List[Dict], oncelik: int = 5) -> int:
        """Kuyruğa çok iş ekler; eklenen sayıyı döndürür."""
        try:
            now = datetime.now().isoformat()
            is_idleri = self.db.yaz_coklu([
                ("INSERT INTO is_kuyrugu (kuyruk_adi, payload, durum, oncelik, kuyruk_zamani) "
                 "VALUES (?, ?, 'bekliyor', ?, ?)",
                 (self.name, _json_yaz({**item, 'queued_at': now}), int(oncelik), now))
                for item in items
            ])
            return len(is_idleri or [])
        except Exception as exc:
            logger.error(f'[{self.name}] push_many başarısız: {exc}')
            return 0

    def pop(self) -> Optional[Dict]:
        """Sıradaki işi ATOMİK olarak çeker ve kuyruktan düşürür."""
        try:
            kayit = self.db.kuyruktan_cek(self.name)
            if kayit is None:
                return None
            payload = kayit.get('payload') or {}
            if isinstance(payload, dict):
                payload.setdefault('queued_at', kayit.get('queued_at'))
                payload['queue_id'] = kayit.get('id')
                return payload
            return {'payload': payload, 'queued_at': kayit.get('queued_at'),
                    'queue_id': kayit.get('id')}
        except Exception as exc:
            logger.error(f'[{self.name}] pop başarısız: {exc}')
            return None

    # ── Okuma / durum ────────────────────────────────────────────────────

    def peek(self, n: int = 5) -> List[Dict]:
        """Kuyruğun başındaki n işi kuyruktan düşmeden görüntüler."""
        kayitlar = self.db.kuyruk_gozlemle(self.name, int(n))
        sonuc = []
        for kayit in kayitlar:
            payload = kayit.get('payload') or {}
            if isinstance(payload, dict):
                payload.setdefault('queued_at', kayit.get('kuyruk_zamani'))
                payload['queue_id'] = kayit.get('id')
                sonuc.append(payload)
            else:
                sonuc.append({'payload': payload, 'queue_id': kayit.get('id')})
        return sonuc

    def size(self) -> int:
        return self.db.kuyruk_boyut(self.name)

    def status(self) -> Dict[str, Any]:
        kayitlar = self.db.kuyruk_gozlemle(self.name, 1)
        oldest = kayitlar[0].get('kuyruk_zamani') if kayitlar else None
        return {'name': self.name, 'size': self.size(), 'oldest_item': oldest}

    # ── Bakım ────────────────────────────────────────────────────────────

    def clear_stale(self, max_age_hours: int = 48) -> int:
        """Belirtilen saatten eski kayıtları temizler, silinen sayıyı döndürür."""
        try:
            silinen = self.db.kuyruk_eski_temizle(max_age_hours=int(max_age_hours),
                                                  kuyruk_adi=self.name)
            if silinen:
                logger.info(f'[{self.name}] {silinen} eski kayıt temizlendi')
            return silinen
        except Exception as exc:
            logger.error(f'[{self.name}] clear_stale başarısız: {exc}')
            return 0

    def backup(self) -> Optional[Path]:
        """Kuyruğun anlık görüntüsünü data/queue_backups/ içine dışa aktarır."""
        try:
            kayitlar = self.db.kuyruk_gozlemle(self.name, 100000)
            bak = BACKUP_DIR / f'{self.name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            bak.write_text(
                json.dumps([k.get('payload') for k in kayitlar],
                           ensure_ascii=False, indent=2, default=str),
                encoding='utf-8',
            )
            return bak
        except Exception as exc:
            logger.error(f'[{self.name}] yedek alınamadı: {exc}')
            return None


# ── Global kuyruk örnekleri ─────────────────────────────────────────────

product_queue = QueueManager('products')
content_queue = QueueManager('contents')
publish_queue = QueueManager('publish')
failed_queue = QueueManager('failed')


async def queue_maintenance_loop(interval_minutes: int = 30):
    """Periyodik bakım: stale temizleme + yedekleme."""
    while True:
        await asyncio.sleep(interval_minutes * 60)
        for q in [product_queue, content_queue, publish_queue, failed_queue]:
            q.clear_stale(max_age_hours=48)
            q.backup()
        logger.info('Kuyruk bakımı tamamlandı')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print('=== Kuyruk Durumu (trm_veritabani.db) ===')
    for q in [product_queue, content_queue, publish_queue, failed_queue]:
        print(q.status())

    # Hızlı işlev testi
    test = QueueManager('kuyruk_testi')
    test.db.yaz("DELETE FROM is_kuyrugu WHERE kuyruk_adi = 'kuyruk_testi'")
    assert test.push({'title': 'Ürün A'})
    assert test.push({'title': 'Önce Ben'}, oncelik=1)
    test.push_many([{'title': f'Ürün {i}'} for i in range(3)])
    ilk = test.pop()
    assert ilk['title'] == 'Önce Ben', f'Öncelik bozuldu: {ilk}'
    kalan = [test.pop() for _ in range(4)]
    assert all(k for k in kalan), 'FIFO kaybı var'
    assert test.pop() is None, 'Kuyruk boşalmalıydı'
    print('[OK] push / push_many / pop / öncelik / FIFO testleri geçti.')
