@echo off
echo ========================================
echo Sosyal Imece Sistem Baslatici
echo ========================================
echo.

echo [1/2] Eski Python/Streamlit surecleri sonlandiriliyor...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im streamlit.exe >nul 2>&1
echo ✅ Eski surecler temizlendi
echo.

echo [2/2] Streamlit uygulamasi baslatiliyor...
cd /d "C:\Users\Habitat\Desktop\sosyal_imece"
streamlit run app.py

pause
