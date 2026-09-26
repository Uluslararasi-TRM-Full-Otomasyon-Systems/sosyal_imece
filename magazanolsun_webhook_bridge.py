import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from trm_master_pipeline import master_siparis_ve_havuz_dongusu

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("MagazanOlsunWebhookBridge")

# Bellek içi üye / müşteri kayıt defteri (MagazanOlsun ID Eşleme)
MEMBER_REGISTRY: List[Dict[str, Any]] = [
    {"id": "APL-55-ALTIN", "ad": "Mehmet Fahri", "yas": 63, "durum": "onayli"},
    {"id": "APL-02", "ad": "Ayşe Teyze", "yas": 60, "durum": "onayli"},
    {"id": "APL-03", "ad": "Can Genç", "yas": 28, "durum": "onayli"},
    {"id": "APL-04", "ad": "Zeynep", "yas": 42, "durum": "onayli"}
]

def process_magazanolsun_order_webhook(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    trendurunlermarket.com (MagazanOlsun) order.completed webhook sinyalini işler.
    """
    order_id = raw_payload.get("order_id", f"MO-{int(datetime.now().timestamp())}")
    customer_id = raw_payload.get("customer_id", "APL-55-ALTIN")
    total_amount = float(raw_payload.get("total_amount_tl", 7500.0))
    comm_rate = float(raw_payload.get("commission_rate", 0.22))

    logger.info(f"📥 MagazanOlsun Webhook Yakalandı -> Sepet ID: {order_id}, Tutar: {total_amount} TL")

    siparis_verisi = {
        "sepet_id": order_id,
        "uye_id": customer_id,
        "tutar": total_amount,
        "komisyon_orani": comm_rate
    }

    # Master pipeline (Önce herkese imece + %20 refah payı, arkasından 55+ zenginlik payı)
    pipeline_res = master_siparis_ve_havuz_dongusu(siparis_verisi, MEMBER_REGISTRY)

    # Log kayıt mühürleme
    event_record = {
        "timestamp": datetime.now().isoformat(),
        "source": "trendurunlermarket.com/magazanolsun",
        "raw_payload": raw_payload,
        "execution_result": pipeline_res
    }

    log_file = "magazanolsun_webhook_events.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event_record, ensure_ascii=False) + "\n")

    logger.info(f"✅ Webhook işlendi ve {log_file} kayıt defterine yazıldı.")
    return event_record

if __name__ == "__main__":
    print("==================================================")
    print("🔗 MAGAZANOLSUN WEBHOOK KÖPRÜSÜ SİMÜLASYON TESTİ")
    print("==================================================")
    
    simulated_payload = {
        "event_type": "order.completed",
        "order_id": "MO-LIVE-TRM-8891",
        "customer_id": "APL-55-ALTIN",
        "total_amount_tl": 9200.0,
        "commission_rate": 0.22
    }

    result = process_magazanolsun_order_webhook(simulated_payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
