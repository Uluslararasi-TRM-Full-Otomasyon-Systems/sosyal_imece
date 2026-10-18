import requests
import json
import logging
from typing import Dict, Any
from nirvana_swarm_agent import audit_ledger_integrity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramSwBot")

def load_config() -> Dict[str, Any]:
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"telegram": {"bot_token": "", "chat_id": "", "enabled": False}}

def send_telegram_alert(message: str) -> bool:
    cfg = load_config()
    t_cfg = cfg.get("telegram", {})
    token = t_cfg.get("bot_token", "")
    chat_id = t_cfg.get("chat_id", "")
    
    if not t_cfg.get("enabled", False) or "YOUR_" in token:
        logger.info(f"📱 [Mock/Local Telegram İletimi] -> {message}")
        return True
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Telegram iletim hatası: {e}")
        return False

def run_audited_alert_cycle():
    audit_res = audit_ledger_integrity()
    status_emoji = "🟢" if audit_res.get("status") == "HEALTHY" else "🔴"
    
    alert_txt = (
        f"{status_emoji} *TRM Nirvana & TRM Ticari Ekosistem Nöbetçi Raporu*\n"
        f"----------------------------------------\n"
        f"▪️ *Mutabakat Durumu:* `{audit_res.get('status')}`\n"
        f"▪️ *Toplam Kayıt:* `{audit_res.get('txn_count', 0)}` adet\n"
        f"▪️ *Hareket Eden Fon:* `{audit_res.get('total_volume_tl', 0):,.2f} TL`\n"
        f"▪️ *Hedef Havuz:* 55+ Zenginlik + Refah Payı Aktif\n"
        f"----------------------------------------\n"
        f"⚡ Otonom ajan katmanı operasyonel."
    )
    send_telegram_alert(alert_txt)
    return audit_res

if __name__ == "__main__":
    run_audited_alert_cycle()
