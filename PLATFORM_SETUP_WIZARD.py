# -*- coding: utf-8 -*-
"""ASCII giriş noktası: platform_setup_wızard.py (Türkçe ı) dosyasını çalıştırır."""
from pathlib import Path
import runpy

_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT / ("platform_setup_w" + "\u0131" + "zard.py")

if not _TARGET.is_file():
    raise SystemExit(f"Hedef bulunamadı: {_TARGET.name}")

runpy.run_path(str(_TARGET), run_name="__main__")
