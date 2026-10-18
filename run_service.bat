@echo off
REM TRM Orchestrator API - Windows Service Startup Script
REM Bu script, API'yi arka planda çalıştırır

title TRM Orchestrator Service

REM Proje dizinine git
cd /d "%~dp0"

REM Log dosyası oluştur
echo ========================================== >> orchestrator_service.log
echo TRM Ticari Ekosistem Service Başlatıldı: %date% %time% >> orchestrator_service.log
echo Çalışma Dizini: %CD% >> orchestrator_service.log

REM Sanal ortam kontrolü
if exist "venv\Scripts\activate.bat" (
    echo Sanal ortam bulundu, aktifleştiriliyor... >> orchestrator_service.log
    call venv\Scripts\activate.bat
    echo Sanal ortam aktif. >> orchestrator_service.log
) else (
    echo Sanal ortam bulunamadı, sistem Python kullanılacak. >> orchestrator_service.log
)

REM Python kontrolü
python --version >> orchestrator_service.log 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadı! >> orchestrator_service.log
    echo Python yüklü değil veya PATH'e eklenmemiş.
    pause
    exit /b 1
)

REM Bağımlılıkları kontrol et ve yükle (gerekirse)
echo Bağımlılıklar kontrol ediliyor... >> orchestrator_service.log
pip install -r requirements.txt >> orchestrator_service.log 2>&1

REM API'yi arka planda başlat (start /B komutu ile)
echo API başlatılıyor... >> orchestrator_service.log
start /B python orchestrator_api.py >> orchestrator_service.log 2>&1

REM Başlatma mesajı
echo.
echo ==========================================
echo TRM Ticari Ekosistem API arka planda başlatıldı!
echo ==========================================
echo API Adresi: http://localhost:5000
echo Log dosyası: orchestrator_service.log
echo.
echo Bu pencereyi kapatabilirsiniz. API arka planda çalışmaya devam edecek.
echo API'yi durdurmak için: taskkill /f /im python.exe
echo ==========================================
echo.
timeout /t 5 >nul
