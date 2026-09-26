# app.py - Sosyal İmece Tam Entegre Flask API Sunucusu
import os
from threading import Thread
import time

from dotenv import load_dotenv

load_dotenv()

# Mevcut tam kontrol merkezi uygulaması, panelin beklediği endpoint'leri ve
# HTML arayüzünü çalıştırır. Bu, minimal demo arayüzünden daha güvenlidir.
from kontrol_merkezi import create_app


def run_nirvana_background_loop():
    """İsteğe bağlı arka planda Ultra Nirvana döngüsü."""
    try:
        from ultra_nirvana_master import UltraNirvanaMasterSystem
    except Exception as exc:
        print(f"[Background Daemon] Ultra Nirvana modülü yüklenmedi: {exc}")
        return

    master_system = UltraNirvanaMasterSystem()
    while True:
        print(">>> [Background Daemon] Ultra Nirvana otonom döngüsü çalışıyor...")
        try:
            master_system.run_full_autonomous_cycle(account_id="hesap_otonom", region="US", target_lang="EN")
        except Exception as exc:
            print(f"[Background Daemon] Hata: {exc}")
        time.sleep(3600)


def init_nirvana_daemon():
    t = Thread(target=run_nirvana_background_loop, daemon=True)
    t.start()


app = create_app(get_controller=lambda: globals().get("controller_instance", None))

# Opsiyonel: uygulama içinden farklı bir controller kullanılacaksa bu değişkeni
# dışarıdan set edebilirsiniz.
controller_instance = None


if __name__ == '__main__':
    # Arka plan döngüsü istenirse açılır; panel ve API aynı anda çalışır.
    try:
        init_nirvana_daemon()
    except Exception as exc:
        print(f"[Startup] Background daemon başlatılamadı: {exc}")

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
