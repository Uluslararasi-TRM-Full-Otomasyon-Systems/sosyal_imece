import json
from pathlib import Path
import socket
import sqlite3
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


class OtoOnarimAjani:
    def __init__(self, sistem_adi="TRM-Full-Otomasyon", health_url="http://127.0.0.1:5000/health", queue_db=None, timeout=2):
        if not isinstance(sistem_adi, str) or not sistem_adi.strip():
            raise ValueError("sistem_adi boş olmayan bir metin olmalıdır")
        if not isinstance(health_url, str) or not health_url.strip():
            raise ValueError("health_url boş olmayan bir metin olmalıdır")
        self.sistem_adi = sistem_adi.strip()
        self.health_url = health_url.strip()
        self.queue_db = Path(queue_db) if queue_db else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        self.timeout = timeout

    def _check_api(self):
        parsed = urlparse(self.health_url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not host:
            port_check = {"component": "API portu", "status": "error", "detail": "Health URL geçersiz"}
            api_check = {"component": "Flask API", "status": "error", "detail": "Health URL geçersiz"}
            return port_check, api_check, False

        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                pass
            port_check = {"component": "API portu", "status": "ok", "detail": f"{host}:{port} bağlantı kabul ediyor"}
        except OSError as exc:
            port_check = {"component": "API portu", "status": "error", "detail": f"Bağlantı kurulamadı: {exc.__class__.__name__}"}

        try:
            with urlopen(self.health_url, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                healthy = response.status == 200 and payload.get("status") == "healthy"
                api_check = {
                    "component": "Flask API",
                    "status": "ok" if healthy else "warning",
                    "detail": payload.get("service", "Health endpoint yanıt verdi") if healthy else "Health endpoint sağlıklı durum bildirmedi",
                }
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            api_check = {"component": "Flask API", "status": "error", "detail": f"Health kontrolü başarısız: {exc.__class__.__name__}"}

        return port_check, api_check, api_check["status"] == "ok"

    def _check_queue_database(self):
        if not self.queue_db.is_file():
            return {
                "component": "SQLite dağıtım kuyruğu",
                "status": "not_initialized",
                "detail": "Kuyruk veritabanı henüz oluşturulmamış",
            }, None

        connection = None
        try:
            connection = sqlite3.connect(f"{self.queue_db.resolve().as_uri()}?mode=ro", uri=True, timeout=self.timeout)
            result = connection.execute("PRAGMA quick_check").fetchone()
            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='task_queue'"
            ).fetchone()
            if result and result[0] == "ok" and table:
                return {
                    "component": "SQLite dağıtım kuyruğu",
                    "status": "ok",
                    "detail": "quick_check başarılı; task_queue tablosu mevcut",
                }, True
            return {
                "component": "SQLite dağıtım kuyruğu",
                "status": "error",
                "detail": "Bütünlük kontrolü başarısız veya task_queue tablosu eksik",
            }, False
        except sqlite3.Error as exc:
            return {
                "component": "SQLite dağıtım kuyruğu",
                "status": "error",
                "detail": f"Veritabanı kontrolü başarısız: {exc.__class__.__name__}",
            }, False
        finally:
            if connection is not None:
                connection.close()

    def sistem_sagligini_tara_ve_onar(self):
        """Sağlığı salt-okunur denetler; süreç kapatmaz veya servis başlatmaz."""
        port_check, api_check, api_healthy = self._check_api()
        queue_check, queue_healthy = self._check_queue_database()
        checks = [port_check, api_check, queue_check]

        if not api_healthy or queue_healthy is False:
            overall_status = "degraded"
            action = "Otomatik değişiklik yapılmadı; ilgili servisi/DB'yi yedek ve loglarla manuel inceleyin."
        elif queue_healthy is None:
            overall_status = "needs_setup"
            action = "API sağlıklı; kuyruk DB'si kullanılınca oluşturulacak."
        else:
            overall_status = "healthy"
            action = "Kontroller başarılı; onarım gerekmiyor."

        return {
            "sistem": self.sistem_adi,
            "durum": overall_status,
            "kontroller": checks,
            "onarim": {
                "gerceklestirildi": False,
                "aciklama": "Güvenlik için süreç sonlandırma, dosya değiştirme veya servis yeniden başlatma yapılmadı.",
            },
            "tavsiye_edilen_aksiyon": action,
        }


if __name__ == "__main__":
    print(OtoOnarimAjani().sistem_sagligini_tara_ve_onar())