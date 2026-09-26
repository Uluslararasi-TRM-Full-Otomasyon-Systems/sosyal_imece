# -*- coding: utf-8 -*-
"""ASCII giriş noktası: securıty_manager.py (Türkçe ı) dosyasını çalıştırır."""
from pathlib import Path
import runpy

_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT / ("secur" + "\u0131" + "ty_manager.py")

if not _TARGET.is_file():
    raise SystemExit(f"Hedef bulunamadı: {_TARGET.name}")

runpy.run_path(str(_TARGET), run_name="__main__")
