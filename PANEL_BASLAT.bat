@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Sosyal Imece Kontrol Merkezi baslatiliyor...
echo Panel: http://127.0.0.1:5000/
py -3 kontrol_merkezi.py
if errorlevel 1 python kontrol_merkezi.py
pause
