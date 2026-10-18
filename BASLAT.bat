@echo off
chcp 65001 >nul
title TRM Full Otomasyon v5.0 (i7 - venv)
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: i7 için oluşturduğumuz izole sanal ortamın python'unu kullanıyoruz
set PY=%~dp0venv\Scripts\python.exe

if not exist "%PY%" (
    echo HATA: Sanal ortam (venv) bulunamadi!
    pause & exit /b
)

echo.
echo  ====================================================
echo    TRM FULL OTOMASYON v5.0  ^|  trendurunlermarket.com
echo  ====================================================
echo  Izole sanal ortamda Streamlit paneli baslatiliyor...
echo.

"%PY%" -m streamlit run run.py
pause