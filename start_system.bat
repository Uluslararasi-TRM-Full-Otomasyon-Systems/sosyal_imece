@echo off
REM ============================================================
REM TRM FULL OTOMASYON SİSTEMİ
REM Otomatik Başlatma Betiği - Arka Plan Servis Çakışma Önleyici
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo    TRM FULL OTOMASYON SİSTEMİ
echo    Otomatik Başlatma Betiği v1.0
echo ============================================================
echo.

REM Ana dizin
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM Log dizini oluştur
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "yedeklerim_arşiv" mkdir yedeklerim_arşiv

echo [1/6] Port 5000 kullanım kontrolü...
netstat -ano | findstr :5000 >nul
if %errorlevel% == 0 (
    echo [UYARI] Port 5000 kullanımda - temizleniyor...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo [INFO] PID %%a sonlandırılıyor...
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
    echo [OK] Port 5000 temizlendi
) else (
    echo [OK] Port 5000 kullanılabilir
)

echo.
echo [2/6] Python prosesleri kontrolü...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I /N "python.exe">nul
if %errorlevel% == 0 (
    echo [UYARI] Python prosesleri tespit edildi - temizleniyor...
    taskkill /F /IM python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo [OK] Python prosesleri temizlendi
) else (
    echo [OK] Çakışan Python prosesi yok
)

echo.
echo [3/6] Eski log dosyaları temizleniyor...
if exist "logs\*.log" (
    forfiles /P "logs" /M *.log /D -7 /C "cmd /c echo Deleting old log: @file @path" >nul 2>&1
    forfiles /P "logs" /M *.log /D -7 /C "cmd /c del @path" >nul 2>&1
    echo [OK] 7 günden eski loglar temizlendi
) else (
    echo [OK] Temizlenecek eski log yok
)

echo.
echo [4/6] CEO API Key ayarlanıyor...
set "CEO_API_KEY=trm-secure-ceo-key-2026"
set "API_ACCESS_KEY=trm-secure-ceo-key-2026"
echo [OK] CEO API Key: %CEO_API_KEY:~0,10%...

echo.
echo [5/6] Python ortamı kontrolü...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python mevcut
    python --version
) else (
    echo [HATA] Python bulunamadı!
    echo [INFO] Lütfen Python 3.8+ kurun ve PATH'e ekleyin
    pause
    exit /b 1
)

echo.
echo [6/6] Gerekli kütüphaneler kontrolü...
python -c "import flask" >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Flask yüklü
) else (
    echo [BILGI] Flask yükleniyor...
    pip install flask flask-cors gtts psutil
)

echo.
echo ============================================================
echo    SİSTEM BAŞLATILIYOR...
echo ============================================================
echo.
echo [INFO] Flask Sunucusu - Port: 5000
echo [INFO] CEO API Key: %CEO_API_KEY:~0,10%...
echo [INFO] Debug Mode: false (Production)
echo [INFO] Log Dizini: %PROJECT_DIR%logs
echo.
echo [BASLAT] whatsapp_agent_bridge.py
echo.

REM CEO_API_KEY environment variable ile başlat
set CEO_API_KEY=trm-secure-ceo-key-2026
set API_ACCESS_KEY=trm-secure-ceo-key-2026
set PORT=5000
set DEBUG=false

REM Flask sunucusunu başlat
python whatsapp_agent_bridge.py

REM Sunucu durduğunda
echo.
echo ============================================================
echo    SİSTEM DURDURULDU
echo ============================================================
echo.
echo [INFO] Loglar: logs\whatsapp_agent_bridge.log
echo [INFO] Data: data\
echo [INFO] Arşiv: yedeklerim_arşiv\
echo.
pause
