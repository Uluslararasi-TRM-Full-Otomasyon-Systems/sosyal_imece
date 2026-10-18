# 1. Başlangıç noktası: Hafif bir Python sürümü kullanıyoruz
FROM python:3.11-slim

# 2. Çalışma dizini: Bulut sunucusunda kodların duracağı yer
WORKDIR /app

# 3. Kütüphaneler: Kodun çalışması için gerekenleri yükle
# (Daha sonra ihtiyacın oldukça buraya ekleme yapabilirsin)
RUN pip install groq

# 4. Kodları kopyala: Kendi bilgisayarındaki dosyaları sunucuya taşı
COPY . .

# 5. Komut: Sunucu açıldığında sistem otomatik çalışmaya başlasın
CMD ["python", "ORCHESTRATOR_AGENT.py"]