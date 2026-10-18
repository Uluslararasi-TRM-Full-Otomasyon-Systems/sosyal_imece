from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
from random import Random
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager


_DEMO_OPPORTUNITIES = (
    {
        "bolge": "Kuşadası / Sahil Turizm Hattı",
        "anlik_faktor": "Örnek sezon ve sıcak hava senaryosu",
        "tespit_edilen_niche": "UV korumalı taşınabilir boyun vantilatörü ve plaj organizeri",
        "tavsiye_edilen_aksiyon": "Bölgeye uygun, doğrulanabilir ürün özellikleriyle içerik taslağı hazırlayın.",
    },
    {
        "bolge": "Ankara / Kent Merkezi",
        "anlik_faktor": "Örnek iş seyahati ve ofis kullanım senaryosu",
        "tespit_edilen_niche": "Ergonomik sırt desteği ve kablosuz masa şarj cihazı",
        "tavsiye_edilen_aksiyon": "Ofis kullanımı için ürün uyumluluğu ve teknik detay taslağı hazırlayın.",
    },
)


class GeoSpatialNicheProfiler:
    def __init__(self, hedef_bolge="Kuşadası / Akdeniz Havzası", firsatlar=None, rng=None):
        if not isinstance(hedef_bolge, str) or not hedef_bolge.strip():
            raise ValueError("hedef_bolge boş olmayan bir metin olmalıdır")
        self.hedef_bolge = hedef_bolge.strip()
        self._firsatlar = tuple(firsatlar if firsatlar is not None else _DEMO_OPPORTUNITIES)
        self._rng = rng if rng is not None else Random()
        self._simulated = firsatlar is None

    def bolgesel_niche_tara(self):
        """Yerel örneklerden bölgesel içerik fikri seçer; canlı geo/weather taramaz."""
        if not self._firsatlar:
            raise ValueError("En az bir bölgesel fırsat kaydı gereklidir")

        normalized_region = self.hedef_bolge.casefold()
        matches = [
            item for item in self._firsatlar
            if any(part.strip().casefold() in normalized_region for part in item["bolge"].split("/"))
        ]
        selected = deepcopy(self._rng.choice(matches or self._firsatlar))
        selected.update({
            "hedef_bolge": self.hedef_bolge,
            "veri_kaynagi": "simülasyon" if self._simulated else "sağlanan bölgesel veri",
            "olusturma_zamani": datetime.now(timezone.utc).isoformat(),
            "canli_hava_ve_koordinat_verisi": False,
            "aksiyon_durumu": "Öneri taslağı; reklam bütçesi veya hedefleme değiştirilmedi",
        })
        return selected

    def inceleme_kuyruguna_ekle(self, rapor, db_path=None):
        if not isinstance(rapor, dict) or not rapor.get("tespit_edilen_niche"):
            raise ValueError("Geçerli bir bölgesel öneri raporu gereklidir")

        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        task = {
            "account_id": "geo_spatial_niche_profiler",
            "post_id": f"geo-review-{uuid4().hex}",
            "payload": {
                "task_type": "regional_niche_review",
                "status": "pending_review",
                "report": deepcopy(rapor),
            },
        }
        DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
        return task


if __name__ == "__main__":
    profiler = GeoSpatialNicheProfiler()
    print(profiler.bolgesel_niche_tara())