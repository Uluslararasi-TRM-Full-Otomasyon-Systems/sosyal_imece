from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
from random import Random
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager


_DEMO_TRENDS = (
    {
        "urun_adi": "Cyberpunk LED Bilek Soğutucu",
        "kategori": "Giyilebilir Teknoloji",
        "sosyal_ivme_skoru": 94.8,
        "tahmini_patlama_suresi": "36 Saat",
        "durum": "Stok ve tedarikçi doğrulaması bekliyor",
    },
    {
        "urun_adi": "Manyetik Katlanabilir Seyahat Masası",
        "kategori": "Akıllı Yaşam / Organizasyon",
        "sosyal_ivme_skoru": 91.2,
        "tahmini_patlama_suresi": "48 Saat",
        "durum": "Stok ve tedarikçi doğrulaması bekliyor",
    },
)


class QuantumTrendSentinel:
    def __init__(self, hedef_pazar="Global", trendler=None, rng=None):
        if not isinstance(hedef_pazar, str) or not hedef_pazar.strip():
            raise ValueError("hedef_pazar boş olmayan bir metin olmalıdır")
        self.hedef_pazar = hedef_pazar.strip()
        self._trendler = tuple(trendler if trendler is not None else _DEMO_TRENDS)
        self._rng = rng if rng is not None else Random()

    def sosyal_dalga_tara(self):
        """Yerel demo sinyal listesinden bir trend seçer; canlı platform taramaz."""
        if not self._trendler:
            raise ValueError("Tarama için en az bir trend kaydı gereklidir")

        trend = deepcopy(self._rng.choice(self._trendler))
        trend.update({
            "hedef_pazar": self.hedef_pazar,
            "sinyal_kaynagi": "simülasyon",
            "tarama_zamani": datetime.now(timezone.utc).isoformat(),
        })
        return trend


def kuyruğa_ekle(trend, db_path=None):
    """Trend incelemesini kalıcı dağıtım kuyruğuna bekleyen görev olarak ekler."""
    if not isinstance(trend, dict) or not trend.get("urun_adi"):
        raise ValueError("Geçerli bir ürün trend kaydı gereklidir")

    configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
    queue_path = Path(configured_path) if configured_path else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
    task = {
        "account_id": "quantum_trend_sentinel",
        "post_id": f"trend-{uuid4().hex}",
        "payload": {
            "task_type": "trend_review",
            "status": "pending_review",
            "trend": deepcopy(trend),
        },
    }
    DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
    return task