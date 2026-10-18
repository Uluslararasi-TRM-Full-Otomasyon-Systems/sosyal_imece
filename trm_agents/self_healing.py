import os
import shutil
import json
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Any

from notification_utils import send_email_message
from trm_agents.traffic_policeman import TrafficPoliceman

class SelfHealingManager:
    def __init__(self, agents_dir: str = "trm_agents",
                 backup_dir: str = "backup_agents",
                 alert_log: str = "intelligence_log.json"):
        self.agents_dir = agents_dir
        self.backup_dir = backup_dir
        self.alert_log = alert_log
        os.makedirs(self.backup_dir, exist_ok=True)
        self.policeman = TrafficPoliceman()
        self.email_settings = self._get_email_settings()

    def _get_email_settings(self):
        from notification_utils import load_email_settings
        import os
        base_dir = os.path.abspath(os.path.dirname(__file__) + "/..")
        return load_email_settings(base_dir)

    def _backup_file(self, file_path: str) -> str:
        if not os.path.exists(file_path):
            return None
        base_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{base_name}.{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_name)
        shutil.copy2(file_path, backup_path)
        return backup_path

    def _atomic_write(self, file_path: str, content: str):
        dir_name = os.path.dirname(file_path)
        with tempfile.NamedTemporaryFile(mode="w", delete=False,
                                         dir=dir_name, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        os.replace(tmp_path, file_path)

    def _git_commit(self, file_path: str, agent_name: str) -> str:
        try:
            repo_root = os.path.abspath(os.path.join(self.agents_dir, ".."))
            subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
            commit_msg = f"Auto-repair: {agent_name} fixed by Self-Healing"
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True
            )
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True
            )
            return hash_result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[Git] Commit başarısız: {e.stderr}")
            return None

    def _send_notification(self, agent_name: str, error_type: str):
        subject = f"[ACİL] TRM Sistem Onarımı - {agent_name}"
        body = f"""
trendurunlermarket.com - Otonom Sistem Onarımı

{agent_name} üzerinde {error_type} tespit edildi ve otonom onarım başarıyla uygulandı.

Onarım Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Ajan: {agent_name}
Hata Tipi: {error_type}

Sistem kendi kendini iyileştirdi.
"""
        settings = self.email_settings
        if settings:
            if isinstance(settings, tuple) and len(settings) == 2:
                settings_dict, _ = settings
            else:
                settings_dict = settings
            send_email_message(subject, body, base_dir=os.path.dirname(self.agents_dir))
        else:
            print("[SelfHealing] E-posta ayarları yok, bildirim gönderilemedi.")

    def _send_quarantine_alert(self, agent_name: str, reason: str):
        """Karantina durumunda Baş Komutan'a uyarı e-postası gönderir."""
        subject = f"[ACİL] TRM Karantina Uyarısı - {agent_name}"
        body = f"""
trendurunlermarket.com - Ajan Karantina Uyarısı

{agent_name} ajanı platform tarafından uyarı aldı ve karantinaya alındı.

Ajan: {agent_name}
Sebep: {reason}
Karantina Süresi: 24 saat

Bu süre boyunca ajan hiçbir işlem yapmayacak.
Sistemi kontrol ediniz.

trendurunlermarket.com Güvenlik Sistemi
"""
        settings = self.email_settings
        if settings:
            if isinstance(settings, tuple) and len(settings) == 2:
                settings_dict, _ = settings
            else:
                settings_dict = settings
            send_email_message(subject, body, base_dir=os.path.dirname(self.agents_dir))
        else:
            print("[SelfHealing] E-posta ayarları yok, karantina bildirimi gönderilemedi.")

    def get_fix_template(self, agent_name: str) -> str:
        backups = sorted([f for f in os.listdir(self.backup_dir)
                          if f.startswith(agent_name) and f.endswith(".bak")], reverse=True)
        if backups:
            latest_backup = os.path.join(self.backup_dir, backups[0])
            with open(latest_backup, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return f"""
# {agent_name} – Self-Healing tarafından yeniden oluşturuldu
# Tarih: {datetime.now()}
class {agent_name}:
    def run(self):
        print("{agent_name} çalışıyor.")
"""

    def heal_agent(self, agent_name: str, error_type: str) -> Dict[str, Any]:
        agent_file = os.path.join(self.agents_dir, f"{agent_name}.py")
        event = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "error_type": error_type,
            "action": "heal",
            "status": "success",
            "notification_sent": False,
            "git_commit_hash": None
        }

        backup_path = self._backup_file(agent_file)
        if backup_path:
            event["backup_path"] = backup_path
        else:
            event["status"] = "failed"
            event["reason"] = "Dosya bulunamadı"
            self._log_event(event)
            return event

        try:
            fix_code = self.get_fix_template(agent_name)
            self._atomic_write(agent_file, fix_code)
            event["fix_applied"] = True

            commit_hash = self._git_commit(agent_file, agent_name)
            if commit_hash:
                event["git_commit_hash"] = commit_hash
                print(f"[Git] {agent_name} onarıldı, commit: {commit_hash[:8]}")

            self._send_notification(agent_name, error_type)
            event["notification_sent"] = True
            event["notification_time"] = datetime.now().isoformat()

        except Exception as e:
            event["status"] = "failed"
            event["reason"] = str(e)

        self._log_event(event)
        return event

    def _log_event(self, event: Dict[str, Any]):
        try:
            with open(self.alert_log, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        if "healing_events" not in data:
            data["healing_events"] = []
        data["healing_events"].append(event)
        data["healing_events"] = data["healing_events"][-200:]

        with open(self.alert_log, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def process_guardian_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for alert in alerts:
            if alert["severity"] in ["critical", "warning"]:
                agent = alert.get("agent")
                error_type = alert.get("error_type")
                if agent and error_type:
                    # Karantina gerektiren durumlar
                    if error_type in ["rate_limit_429", "ban_risk"]:
                        # Ajanı karantinaya al
                        quarantine_entry = self.policeman.quarantine_agent(agent, alert.get("log_line"))
                        # Karantina bildirimi gönder
                        self._send_quarantine_alert(agent, alert.get("log_line"))
                        results.append({"action": "quarantine", "agent": agent, "details": quarantine_entry})
                    # Onarılabilir hatalar
                    elif error_type in ["timeout", "file_not_found", "api_error",
                                        "ssl_cert_error", "db_connection_refused", "unauthorized_api"]:
                        result = self.heal_agent(agent, error_type)
                        results.append(result)
        return results