# -*- coding: utf-8 -*-
"""Bölgesel niş profilcisi — FAIL-CLOSED.

Eski hâli: içinde iki hazır "fırsat" metni duruyordu ve çağrılandan veri
gelmeseydi bile bunlardan birini RANDOM seçip "tespit edildi" diye sunuyordu.
Yani ürün önerisi coğrafyadan değil, dosyanın içinden geliyordu.

Şimdi: dışarıdan SAĞLANMIŞ bölgesel kayıt yoksa hiçbir niş üretilmez; durum
`not_configured` döner ve böyle bir rapor inceleme kuyruğuna da yazılamaz.
Veri kaynağı olarak meşru yol, OSM tabanlı aday havuzu (aday_havuzu.py) ve
operatörün kendi listesidir — tüketici/demografik hedefleme burada yapılmaz.
"""

from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager

NOT_CONFIGURED = "not_configured"
OK = "ok"
_ZORUNLU_ALANLAR = ("bolge", "tespit_edilen_niche")


class GeoSpatialNicheProfiler:
    def __init__(self, hedef_bolge="Kuşadası / Akdeniz Havzası", firsatlar=None):
        if not isinstance(hedef_bolge, str) or not hedef_bolge.strip():
            raise ValueError("hedef_bolge boş olmayan bir metin olmalıdır")
        self.hedef_bolge = hedef_bolge.strip()
        self._firsatlar = tuple(firsatlar or ())

    def _red(self, sebep):
        return {
            "durum": NOT_CONFIGURED,
            "sebep": sebep,
            "hedef_bolge": self.hedef_bolge,
            "tespit_edilen_niche": None,
            "veri_kaynagi": None,
            "canli_hava_ve_koordinat_verisi": False,
            "aksiyon_durumu": "Filtrelenmiş gerçek veri yok; hiçbir öneri üretilmedi",
        }

    def bolgesel_niche_tara(self):
        """Yalnızca sağlanan gerçek bölgesel kayıtları eşleştirir; uydurma seçim yok."""
        if not self._firsatlar:
            return self._red("bölgesel fırsat verisi sağlanmadı (firsatlar=()) — "
                            "kaynak: aday_havuzu OSM kayıtları veya operatör listesi")
        eksik = [ad for ad in _ZORUNLU_ALANLAR
                 if not str(self._firsatlar[0].get(ad) or "").strip()]
        if eksik:
            return self._red(f"sağlanan kayıt alanları eksik: {', '.join(eksik)}")

        normalized_region = self.hedef_bolge.casefold()
        matches = [
            item for item in self._firsatlar
            if item.get("bolge") and any(
                parca.strip().casefold() in normalized_region
                for parca in str(item["bolge"]).split("/"))
        ]
        if not matches:
            return self._red(f"'{self.hedef_bolge}' için sağlanan kayıtlarda eşleşme yok")
        selected = deepcopy(matches[0])
        selected.update({
            "durum": OK,
            "hedef_bolge": self.hedef_bolge,
            "veri_kaynagi": "sağlanan bölgesel veri",
            "olusturma_zamani": datetime.now(timezone.utc).isoformat(),
            "canli_hava_ve_koordinat_verisi": False,
            "aksiyon_durumu": "Öneri taslağı; reklam bütçesi veya hedefleme değiştirilmedi",
        })
        return selected

    def inceleme_kuyruguna_ekle(self, rapor, db_path=None):
        if not isinstance(rapor, dict) or not rapor.get("tespit_edilen_niche"):
            raise ValueError("Geçerli bir bölgesel öneri raporu gereklidir")
        if rapor.get("durum") != OK:
            raise ValueError(f"durum='{rapor.get('durum', NOT_CONFIGURED)}': "
                            "doğrulanmamış rapor kuyruğa yazılamaz (fail-closed)")

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
    print(GeoSpatialNicheProfiler().bolgesel_niche_tara())
