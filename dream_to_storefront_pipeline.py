from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
from random import Random
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager


_DEMO_IDEAS = (
    {
        "konsept_adi": "Güneş Enerjili Taşınabilir Mini Espresso Makinesi",
        "kategori": "Outdoor / Seyahat",
        "cozulen_problem": "Kamp alanlarında elektriksiz kahve hazırlama ihtiyacı",
        "tahmini_talep_skoru": 96.4,
    },
    {
        "konsept_adi": "Ergonomik Boyun Destekli Isıtıcılı Seyahat Yastığı",
        "kategori": "Konfor / Seyahat",
        "cozulen_problem": "Uzun yolculuklarda boyun desteği ve ısı konforu ihtiyacı",
        "tahmini_talep_skoru": 93.1,
    },
)


class DreamToStorefrontPipeline:
    def __init__(self, hedef_pazar="Global", fikirler=None, rng=None):
        if not isinstance(hedef_pazar, str) or not hedef_pazar.strip():
            raise ValueError("hedef_pazar boş olmayan bir metin olmalıdır")
        self.hedef_pazar = hedef_pazar.strip()
        self._fikirler = tuple(fikirler if fikirler is not None else _DEMO_IDEAS)
        self._rng = rng if rng is not None else Random()

    def pazar_boslugu_ve_fikir_uret(self):
        """Yerel demo fikirlerinden birini seçer; canlı pazar verisi taramaz."""
        if not self._fikirler:
            raise ValueError("En az bir fikir kaydı gereklidir")

        idea = deepcopy(self._rng.choice(self._fikirler))
        idea.update({
            "hedef_pazar": self.hedef_pazar,
            "veri_kaynagi": "simülasyon",
            "olusturma_zamani": datetime.now(timezone.utc).isoformat(),
            "durum": "Taslak; talep, tedarik, maliyet ve mevzuat doğrulaması bekliyor",
        })
        return idea

    def lansman_paketi_uret(self, fikir):
        if not isinstance(fikir, dict) or not fikir.get("konsept_adi") or not fikir.get("cozulen_problem"):
            raise ValueError("Geçerli bir ürün konsepti gereklidir")

        return {
            "urun_adi": fikir["konsept_adi"],
            "kategori": fikir.get("kategori", "Belirtilmedi"),
            "hedef_pazar": fikir.get("hedef_pazar", self.hedef_pazar),
            "urun_aciklamasi_taslagi": (
                f"{fikir['konsept_adi']}: {fikir['cozulen_problem']}. "
                "Ürün özellikleri ve performans iddiaları tedarikçi verileriyle doğrulanmalıdır."
            ),
            "talep_skoru": fikir.get("tahmini_talep_skoru"),
            "veri_kaynagi": fikir.get("veri_kaynagi", "simülasyon"),
            "durum": "Taslak; mağazada yayımlanmadı",
        }

    def inceleme_kuyruguna_ekle(self, paket, db_path=None):
        if not isinstance(paket, dict) or not paket.get("urun_adi"):
            raise ValueError("Geçerli bir lansman taslağı gereklidir")

        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        task = {
            "account_id": "dream_to_storefront_pipeline",
            "post_id": f"storefront-draft-{uuid4().hex}",
            "payload": {
                "task_type": "storefront_concept_review",
                "status": "pending_review",
                "launch_draft": deepcopy(paket),
            },
        }
        DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
        return task


if __name__ == "__main__":
    pipeline = DreamToStorefrontPipeline(hedef_pazar="Global")
    idea = pipeline.pazar_boslugu_ve_fikir_uret()
    print(pipeline.lansman_paketi_uret(idea))