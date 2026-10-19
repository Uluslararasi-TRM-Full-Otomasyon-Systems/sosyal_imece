@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title TRM Derya API - baslat_trm
cd /d "%~dp0"

rem ============================================================
rem  baslat_trm.bat - TRM Derya API (api_server_2.py) baslatici
rem
rem  Kullanim:
rem    baslat_trm.bat            pencereyi acip otonom modda baslatir (QR buradan taranir)
rem    baslat_trm.bat gizli      arka planda gizli pencerede; loglar logs klasorune yazilir
rem    baslat_trm.bat restart    ayaktaki ornek saglikli olsa bile yeniden baslatir
rem    baslat_trm.bat durum      hicbir sey baslatmaz/oldurmez, sadece tanilama yazdirir
rem    baslat_trm.bat kisa       shell:startup klasorune gizli baslatma kisa yolu koyar
rem
rem  Guvenlik: portu api_server_2.py baska bir surec tutuyosa dokunmaz ve cikar.
rem  Temizlik yalnizca komut satirinda api_server_2.py gecen surecleri hedef alir;
rem  Chrome veya baska surecler asla toplu oldurulmez.
rem
rem  Not: Yorumlar/echo ASCII - .bat dosyalari BOM'suz okunur, kod sayfasina gore
rem  Turkce karakterli satirlar bozulabiliyor. ASCII en garantili yol.
rem ============================================================

set "PROJE=%~dp0api_server_2.py"
set "PORT=5000"
set "SAGLIK_URL=http://127.0.0.1:%PORT%/api/saglik"
set "LOG_KLASORU=%~dp0logs"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

set "MOD=baslat"
set "GIZLI=0"
set "YENIDEN=0"
set "BEKLE=0"

:arglar
if "%~1"=="" goto :arglar_bitti
if /i "%~1"=="gizli" set "GIZLI=1"
if /i "%~1"=="restart" set "YENIDEN=1"
if /i "%~1"=="durum" set "MOD=durum"
if /i "%~1"=="kisa" set "MOD=kisa"
shift
goto :arglar

:arglar_bitti
if "%MOD%"=="baslat" if "%GIZLI%"=="0" set "BEKLE=1"

if not exist "%PROJE%" (
  echo HATA: api_server_2.py bulunamadi - "%PROJE%"
  call :okundu
  exit /b 3
)

rem --- 1) Calistirilabilir Python: once venv, sonra .venv, en son sistem Python'u ---
set "PY="
set "PY_NOT="
for %%P in ("venv\Scripts\python.exe" ".venv\Scripts\python.exe") do (
  if not defined PY (
    if exist "%%~P" (
      "%%~P" -c "import flask, flask_cors, selenium, dotenv" >nul 2>&1
      if not errorlevel 1 (
        set "PY=%%~P"
        set "PY_NOT=sanal ortam"
      )
    )
  )
)
if not defined PY (
  where python >nul 2>&1
  if not errorlevel 1 (
    set "PY=python"
    set "PY_NOT=sistem Python'u - venv paketleri eksik"
  )
)
if not defined PY (
  echo HATA: flask, flask_cors, selenium paketlerine sahip bir Python bulunamadi.
  call :okundu
  exit /b 4
)

rem --- 2) Port sahibini siniflandir: api_server_2.py mi, baska bir sey mi ---
set "TANIM=%TEMP%\trm_port_%RANDOM%%RANDOM%.txt"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { $cl = (Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_)).CommandLine; if ($cl -match 'api_server_2\.py') { 'DERYA=' + $_ } else { 'BASKA=' + $_ + ' | ' + $cl } }" > "%TANIM%" 2>nul

set "DERYA_PID="
set "BASKA_PID="
for /f "usebackq tokens=1,* delims==" %%A in ("%TANIM%") do (
  if /i "%%A"=="DERYA" set "DERYA_PID=%%B"
  if /i "%%A"=="BASKA" set "BASKA_PID=%%B"
)
if exist "%TANIM%" del "%TANIM%" >nul 2>&1

rem --- 3) Ayaktaki ornek saglikli mi ---
set "SAGLIK=YOK"
if defined DERYA_PID (
  for /f "usebackq delims=" %%S in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -Uri '%SAGLIK_URL%' -TimeoutSec 4 -UseBasicParsing).StatusCode } catch { 'YOK' }"`) do set "SAGLIK=%%S"
)

if "%MOD%"=="kisa" goto :kisa_yol
if "%MOD%"=="durum" goto :durum

echo.
echo  ========== TRM Derya API ==========
echo  Klasor : %~dp0
echo  Python : !PY!  ^(!PY_NOT!^)
echo  Port   : %PORT%   ^|  %SAGLIK_URL%
echo  Mod    : otonom ^| WHATSAPP_OTOMATIK_BASLAT varsayilan 1 ^| Chrome + WhatsApp acilir
echo.

rem --- 4) Portu baska bir program tutuyorsa ona dokunmaz ---
if defined BASKA_PID (
  echo HATA: Port %PORT% api_server_2.py OLMAYAN bir surec tarafindan tutuluyor.
  echo        O surece dokunmadim, sen karar ver:  PID !BASKA_PID!
  call :okundu
  exit /b 5
)

rem --- 5) Saglikli ornek varsa bosuna ikinci surec acma ---
if defined DERYA_PID if not "%SAGLIK%"=="YOK" if "%YENIDEN%"=="0" (
  echo Zaten ayakta: PID !DERYA_PID!  HTTP !SAGLIK!  - yeni surec acilmadi.
  echo Yeniden baslatmak icin: baslat_trm.bat restart
  exit /b 0
)

rem --- 6) Cakisma temizligi: yalnizca api_server_2.py gecen surecler ---
if defined DERYA_PID (
  echo Asagidaki api_server_2 sureci durduruluyor: PID !DERYA_PID!
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { $cl = (Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_)).CommandLine; if ($cl -match 'api_server_2\.py') { Stop-Process -Id $_ -Force; 'durduruldu: PID ' + $_ } }"
  ping -n 4 127.0.0.1 >nul
)

if not exist "%LOG_KLASORU%" mkdir "%LOG_KLASORU%"

rem --- 7) Baslat ---
if "%GIZLI%"=="1" goto :gizli_baslat

echo Konsol penceresi acik kalacak; QR kodu ve loglar burada gorunur.
echo Cikmak icin: Ctrl+C
echo.
"%PY%" -u api_server_2.py
goto :son

:gizli_baslat
for /f "usebackq delims=" %%T in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set "STAMP=%%T"
set "TRM_PY=!PY!"
set "TRM_KOK=%~dp0"
set "TRM_LOG=%LOG_KLASORU%\api_server_2_canli_!STAMP!.log"
set "TRM_LOG_E=%LOG_KLASORU%\api_server_2_hata_!STAMP!.log"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath $env:TRM_PY -ArgumentList '-u','api_server_2.py' -WorkingDirectory $env:TRM_KOK -WindowStyle Hidden -RedirectStandardOutput $env:TRM_LOG -RedirectStandardError $env:TRM_LOG_E"
echo Gizli modda baslatildi. Log: !TRM_LOG!
echo Saglik kontrolu bekleniyor...
set "DENEME=0"
:gizli_bekle
ping -n 6 127.0.0.1 >nul
set /a DENEME+=1
for /f "usebackq delims=" %%S in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -Uri '%SAGLIK_URL%' -TimeoutSec 4 -UseBasicParsing).StatusCode } catch { 'YOK' }"`) do set "SAGLIK=%%S"
if not "%SAGLIK%"=="YOK" goto :gizli_hazir
if %DENEME% LSS 8 goto :gizli_bekle
echo UYARI: 8 yoklamada HTTP saglik cevabi alinamadi. Loga bak: !TRM_LOG_E!
goto :son

:gizli_hazir
echo Hazir: HTTP %SAGLIK%  ^|  %SAGLIK_URL%

:son
if "%BEKLE%"=="1" pause
exit /b 0

rem --- Mesaji okumak icin bekletir (yalnizca cift tiklama / etkilesimli mod) ---
:okundu
if "%BEKLE%"=="1" pause >nul
exit /b 0

rem ============================================================
rem  Tanilama - hicbir sey degistirmez
rem ============================================================
:durum
echo.
echo  ========== baslat_trm durum ==========
echo  Klasor      : %~dp0
echo  Hedef dosya : %PROJE%
echo  Python      : !PY!  ^(!PY_NOT!^)
echo  Port        : %PORT%
if defined DERYA_PID (echo  api_server_2  : PID !DERYA_PID!  ^| saglik HTTP %SAGLIK%) else echo  api_server_2  : portu tutan surec yok
if defined BASKA_PID (echo  Port sahibi   : BASKA SUREC - !BASKA_PID!) else (
  if not defined DERYA_PID echo  Port sahibi   : bos
)
echo  Log klasoru : %LOG_KLASORU%
echo  Bilgi       : WHATSAPP_OTOMATIK_BASLAT=1 ise baslatici Chrome + WhatsApp Web +
echo                otonom mesaj kuyrugunu da baslatir. Sadece API icin:
echo                set WHATSAPP_OTOMATIK_BASLAT=0 ^&^& baslat_trm.bat
echo.
exit /b 0

rem ============================================================
rem  Baslangic kisa yolu - shell:startup klasorune gizli mod ile koyar
rem  DIS NOT: Windows acilir acilmaz WhatsApp otomasyonu kendi kendine baslar.
rem ============================================================
:kisa_yol
set "TRM_HEDEF=%~f0"
set "TRM_KOK=%~dp0"
echo Kisa yol olusturuluyor: Baslangic klasoru - gizli mod.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$k = (New-Object -ComObject Shell.Application).NameSpace('shell:startup').Self.Path; $s = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $k 'TRM Derya API.lnk')); $s.TargetPath = $env:TRM_HEDEF; $s.Arguments = 'gizli'; $s.WorkingDirectory = $env:TRM_KOK; $s.Description = 'TRM Derya API - gizli baslatma'; $s.Save(); 'Kisa yol: ' + $s.FullName"
if errorlevel 1 (
  echo HATA: Kisa yol olusturulamadi.
  call :okundu
  exit /b 6
)
echo Silmek icin: Windows^+R -^> shell:startup -^> TRM Derya API.lnk
exit /b 0
