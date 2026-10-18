from copy import deepcopy
import os
from pathlib import Path
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager


class OtonomAjanlarMahkemesi:
    def __init__(self, karar_konusu="Yeni Ürün Lansman Onayı"):
        if not isinstance(karar_konusu, str) or not karar_konusu.strip():
            raise ValueError("karar_konusu boş olmayan bir metin olmalıdır")
        self.karar_konusu = karar_konusu.strip()

    @staticmethod
    def _clean_items(values, field_name):
        if values is None:
            return []
        if not isinstance(values, (list, tuple)):
            raise ValueError(f"{field_name} liste olmalıdır")
        cleaned = []
        for value in values:
            if not isinstance(value, str):
                raise ValueError(f"{field_name} yalnızca metin içermelidir")
            value = value.strip()
            if value:
                cleaned.append(value)
        return cleaned

    def ajanlar_arasi_munazara_ve_karar(
        self,
        savunma=None,
        itirazlar=None,
        kanitlar=None,
        riskler=None,
    ):
        """Girilen argümanları düzenler; nihai kararı insana bırakır."""
        if savunma is not None and not isinstance(savunma, str):
            raise ValueError("savunma metin olmalıdır")
        defense = (savunma or "").strip()
        objections = self._clean_items(itirazlar, "itirazlar")
        evidence = self._clean_items(kanitlar, "kanıtlar")
        risks = self._clean_items(riskler, "riskler")

        if not defense or not evidence:
            decision = "Ek kanıt gerekli"
            status = "insufficient_information"
        elif objections or risks:
            decision = "İtiraz ve riskler çözümlenene kadar karar ertelendi"
            status = "review_required"
        else:
            decision = "İnsan kararına hazır taslak; otomatik onay verilmedi"
            status = "human_review_ready"

        return {
            "karar_konusu": self.karar_konusu,
            "ajan_gorusu": defense or None,
            "itirazlar": objections,
            "kanıtlar": evidence,
            "riskler": risks,
            "durum": status,
            "nihai_karar": decision,
            "guven_puani": None,
            "otomatik_onay": False,
            "not": "Bu rapor yalnızca verilen girdileri düzenler; ajan oyu, bağımsız doğrulama veya nihai karar içermez.",
        }

    def inceleme_kuyruguna_ekle(self, rapor, db_path=None):
        if not isinstance(rapor, dict) or rapor.get("karar_konusu") != self.karar_konusu:
            raise ValueError("Bu mahkeme oturumuna ait geçerli bir rapor gereklidir")

        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        task = {
            "account_id": "otonom_ajanlar_mahkemesi",
            "post_id": f"court-review-{uuid4().hex}",
            "payload": {
                "task_type": "decision_review",
                "status": "pending_review",
                "report": deepcopy(rapor),
            },
        }
        DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
        return task