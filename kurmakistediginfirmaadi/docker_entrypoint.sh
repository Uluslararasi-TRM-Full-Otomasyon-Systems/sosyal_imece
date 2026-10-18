#!/bin/bash
# TRM Nirvana v3.0 - Docker Entry Point

set -e

echo "==============================================="
echo "    TRM NİRVANA v3.0 - CLOUD READY"
echo "==============================================="
echo "🚀 Container başlatılıyor..."
echo "☁️  Bulut ortamında çalışacak"
echo "🤖 7/24 otomasyon aktif"
echo "==============================================="

# Gerekli dizinleri kontrol et
mkdir -p logs data temp_photos temp_docs

# Ortam değişkenlerini kontrol et
if [ ! -f "secrets.env" ]; then
    echo "📝 secrets.env oluşturuluyor..."
    cat > secrets.env << EOF
# TRM Full Otomasyon Sistemi v3.0 - Cloud
TELEGRAM_API_ID=${TELEGRAM_API_ID:-your_telegram_api_id}
TELEGRAM_API_HASH=${TELEGRAM_API_HASH:-your_telegram_api_hash}
TELEGRAM_PHONE=${TELEGRAM_PHONE:-+90555xxxxxxx}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-your_deepseek_api_key}
CLAUDE_API_KEY=${CLAUDE_API_KEY:-your_claude_api_key}
FACEBOOK_ACCESS_TOKEN=${FACEBOOK_ACCESS_TOKEN:-your_facebook_access_token}
INSTAGRAM_ACCESS_TOKEN=${INSTAGRAM_ACCESS_TOKEN:-your_instagram_access_token}
TIKTOK_ACCESS_TOKEN=${TIKTOK_ACCESS_TOKEN:-your_tiktok_access_token}
YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-your_youtube_api_key}
GOOGLE_DRIVE_FOLDER_ID=${GOOGLE_DRIVE_FOLDER_ID:-your_google_drive_folder_id}
STORE_URL=${STORE_URL:-https://trendurunlermarket.com}
COMMISSION_THRESHOLD=${COMMISSION_THRESHOLD:-20.0}
CHECK_INTERVAL=${CHECK_INTERVAL:-300}
MAX_PRODUCTS_PER_DAY=${MAX_PRODUCTS_PER_DAY:-50}
EOF
fi

echo "✅ Ortam hazır"

# Ticari API servisi arka planda başlat
python api_server_2.py &
API_PID=$!
sleep 3

echo "🚀 Ana sistem başlatılıyor..."
echo "🌐 Panel: http://localhost:9000"
echo "☁️  Cloud modu aktif"

# Ana orchestrator'u başlat
exec "$@"
