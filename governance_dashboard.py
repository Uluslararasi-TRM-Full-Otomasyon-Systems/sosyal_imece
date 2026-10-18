import json
import os
import time
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parent
GOVERNANCE_FILE = WORKSPACE_ROOT / "trm_agents" / "governance" / "governance_report.json"


def _get_default_report_data() -> dict:
    """Varsayılan governance raporu oluştur."""
    return {
        "EthicalGuardian": {
            "status": "ACTIVE",
            "message": "Ethical checks healthy",
            "timestamp": "initial",
        },
        "SyncLead": {
            "status": "ACTIVE",
            "message": "Synchronization healthy",
            "timestamp": "initial",
        },
        "Sentinel": {
            "status": "ACTIVE",
            "message": "Sentinel monitoring active",
            "timestamp": "initial",
        },
    }


def get_governance_status() -> str:
    """Governance raporunu okur ve dashboard metni döner."""
    if not GOVERNANCE_FILE.exists():
        return "STATUS: Governance Katmanı Hazırlanıyor... (Dosya bekleniyor)"

    try:
        with GOVERNANCE_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError) as exc:
        return f"STATUS: Veri okuma hatası: {exc}"

    if not isinstance(data, dict):
        return "STATUS: Geçersiz governance raporu formatı"

    expected_keys = ["EthicalGuardian", "SyncLead", "Sentinel"]
    lines = ["\n=== [TRM TICARI EKOSISTEMI] SİSTEM SAĞLIĞI ==="]

    for key in expected_keys:
        value = data.get(key, "PENDING")
        if isinstance(value, dict):
            status = value.get("status", "PENDING")
            message = value.get("message", "")
            display_value = status if not message else f"{status} - {message}"
        elif isinstance(value, str):
            display_value = value
        else:
            display_value = "PENDING"
        lines.append(f"{key}: {display_value}")

    lines.append("========================================")
    return "\n".join(lines)


def display_dashboard() -> None:
    """Dashboard ana döngüsü."""
    os.system("cls" if os.name == "nt" else "clear")
    print("Dashboard başlatıldı... (Durdurmak için Ctrl+C)")

    while True:
        try:
            print(get_governance_status())
            time.sleep(5)
            os.system("cls" if os.name == "nt" else "clear")
        except KeyboardInterrupt:
            print("\nDashboard kapatılıyor.")
            break


if __name__ == "__main__":
    display_dashboard()
