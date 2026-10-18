from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
from random import Random
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager


_DEMO_FORECASTS = (
    {
        "kategori": "Ev Yaşamı / Ergonomi",
        "trend_adi": "Akıllı duruş destekleyici giyilebilir ürünler",
        "olasi_sinyal": "Ergonomi odaklı ürün konsepti",
        "beklenen_zirve": "10-14 gün senaryosu",
        "stratejik_tavsiye": "Ürün iddialarını doğrulayın; stok veya reklam kararı öncesi gerçek talep verisi toplayın.",
    },
    {
        "kategori": "Outdoor / Seyahat",
        "trend_adi": "Güneş enerjili taşınabilir enerji ve su filtrasyonu ürünleri",
        "olasi_sinyal": "Seyahat ve açık hava kullanım senaryosu",
        "beklenen_zirve": "7-10 gün senaryosu",
        "stratejik_tavsiye": "Tedarik, güvenlik ve performans bilgilerini doğrulayın; öngörüyü kesin talep saymayın.",
    },
)


class GelecekDalgaKehaneti:
    def __init__(self, analiz_ufku="Gelecek 14 Gün", senaryolar=None, rng=None):
        if not isinstance(analiz_ufku, str) or not analiz_ufku.strip():
            raise ValueError("analiz_ufku boş olmayan bir metin olmalıdır")
        self.analiz_ufku = analiz_ufku.strip()
        self._senaryolar = tuple(senaryolar if senaryolar is not None else _DEMO_FORECASTS)
        self._rng = rng if rng is not None else Random()
        self._simulated = senaryolar is None

    def viral_dalga_tahmin_et(self):
        """Simüle trend senaryosu üretir; canlı duygu analizi yapmaz."""
        if not self._senaryolar:
            raise ValueError("En az bir trend senaryosu gereklidir")

        forecast = deepcopy(self._rng.choice(self._senaryolar))
        forecast.update({
            "analiz_ufku": self.analiz_ufku,
            "veri_kaynagi": "simülasyon" if self._simulated else "sağlanan senaryo verisi",
            "olusturma_zamani": datetime.now(timezone.utc).isoformat(),
            "tahmin_guven_skoru": None,
            "tahmin_notu": "Bu çıktı doğrulanmış tahmin veya canlı duygu analizi değildir.",
        })
        return forecast

    def inceleme_kuyruguna_ekle(self, forecast, db_path=None):
        if not isinstance(forecast, dict) or not forecast.get("trend_adi"):
            raise ValueError("Geçerli bir trend senaryosu gereklidir")

        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        task = {
            "account_id": "gelecek_dalga_kehaneti",
            "post_id": f"forecast-review-{uuid4().hex}",
            "payload": {
                "task_type": "trend_forecast_review",
                "status": "pending_review",
                "forecast": deepcopy(forecast),
            },
        }
        DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
        return task


if __name__ == "__main__":
    forecaster = GelecekDalgaKehaneti()
    print(forecaster.viral_dalga_tahmin_et())