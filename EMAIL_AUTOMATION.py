# -*- coding: utf-8 -*-
"""ASCII giriş noktası: dosya adı Türkçe 'ı' içeren emaıl_automatıon.py'yi çalıştırır."""
from pathlib import Path
import runpy

_ROOT = Path(__file__).resolve().parent
_TARGET = _ROOT / ("ema" + "\u0131" + "l_automat" + "\u0131" + "on.py")

if not _TARGET.is_file():
    raise SystemExit(f"Hedef bulunamadı: {_TARGET.name}")

runpy.run_path(str(_TARGET), run_name="__main__")
