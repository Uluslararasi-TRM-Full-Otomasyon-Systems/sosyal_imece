from typing import Dict, Any
from trm_master_pipeline import master_siparis_ve_havuz_dongusu

EXCHANGE_RATES = {
    "TRY": 1.0,
    "USD": 35.5,
    "EUR": 38.5
}

def normalize_and_execute_global_sale(platform: str, raw_sale: Dict[str, Any], member_registry: list) -> Dict[str, Any]:
    currency = raw_sale.get("currency", "TRY").upper()
    rate = EXCHANGE_RATES.get(currency, 1.0)
    
    local_amount_tl = float(raw_sale.get("amount", 0.0)) * rate
    commission_rate = float(raw_sale.get("commission_rate", 0.22))
    
    normalized_order = {
        "sepet_id": f"{platform.upper()}-{raw_sale.get('txn_id', 'GEN-01')}",
        "uye_id": raw_sale.get("beneficiary_member_id", "APL-55-ALTIN"),
        "tutar": local_amount_tl,
        "komisyon_orani": commission_rate
    }
    
    return master_siparis_ve_havuz_dongusu(normalized_order, member_registry)

if __name__ == "__main__":
    from magazanolsun_webhook_bridge import MEMBER_REGISTRY
    global_test = {
        "platform": "clickbank_eu",
        "txn_id": "CB-99411",
        "beneficiary_member_id": "APL-55-ALTIN",
        "amount": 250.0,
        "currency": "EUR",
        "commission_rate": 0.25
    }
    res = normalize_and_execute_global_sale("clickbank", global_test, MEMBER_REGISTRY)
    import json
    print("🌍 Küresel Adaptör Test Sonucu:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
