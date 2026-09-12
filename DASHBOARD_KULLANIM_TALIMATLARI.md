# DASHBOARD.PY - KULLANIM TALIMATLARI

## 📋 Genel Bakış

`dashboard.py` FastAPI tabanlı modern bir agent dashboard'dur. 8 ajanın (Elif, Amara, Lucia, Sophie, Emma, Yuki, Alina, Camille) anlık durumlarını, son loglarını ve görevlerini modern bir grid ekranda canlı olarak gösterir.

**Yeni Özellikler:**
- ✅ Şık modern HTML/JS arayüzü (static/index.html)
- ✅ 8 ajan için renkli kartlar ve ülke bayrakları
- ✅ Inter-agent bus canlı mesaj akışı
- ✅ Responsive tasarım (mobil uyumlu)
- ✅ Gerçek zamanlı WebSocket güncellemeleri
- ✅ Kontrol butonları (Tüm Ajanları Başlat, Sistemi Durdur, Affiliate Görevini Tetikle)
- ✅ Orchestrator/Launcher entegrasyonu
- ✅ Anlık durum renk değişimi (Active/Idle/Busy/Inactive)

## 🚀 Özellikler

- ✅ 8 ajan için canlı durum izleme
- ✅ Modern responsive grid layout (2x4)
- ✅ WebSocket ile gerçek zamanlı güncelleme
- ✅ Ajan loglarını görüntüleme
- ✅ Inter-agent bus mesajlarını izleme
- ✅ RESTful API endpoint'leri
- ✅ Orchestrator entegrasyonu
- ✅ Otomatik ajan aktivite simülasyonu

## 📦 Gereksinimler

### Python Kütüphaneleri

```bash
pip install fastapi uvicorn websockets
```

### Manuel Kurulum

```bash
pip install fastapi uvicorn websockets
```

## 🔧 Kurulum

### 1. Dosyaların Hazırlanması

Aşağıdaki dosyaların proje klasöründe olduğundan emin olun:

```
sosyal_imece/
├── dashboard.py              # FastAPI dashboard
├── agent_config.json        # Ajan konfigürasyonu (8 ajan)
├── logs/
│   ├── inter_agent_bus.jsonl  # Inter-agent log dosyası
│   ├── elif_agent.log
│   ├── amara_agent.log
│   └── ... (diğer ajan logları)
```

### 2. agent_config.json Kontrol

`agent_config.json` dosyasında 8 ajan tanımlı olmalı:

```json
{
    "agents": [
        {"id": "elif", "name": "Elif", ...},
        {"id": "amara", "name": "Amara", ...},
        {"id": "lucia", "name": "Lucia", ...},
        {"id": "sophie", "name": "Sophie", ...},
        {"id": "emma", "name": "Emma", ...},
        {"id": "yuki", "name": "Yuki", ...},
        {"id": "alina", "name": "Alina", ...},
        {"id": "camille", "name": "Camille", ...}
    ]
}
```

## 🎯 Kullanım

### Temel Kullanım

```bash
cd c:\Users\Habitat\Desktop\sosyal_imece
python dashboard.py
```

### Kontrol Butonları

Dashboard arayüzünde 3 ana kontrol butonu bulunur:

#### 1. Tüm Ajanları Başlat (Yeşil Buton)
- **Fonksiyon:** Tüm ajanları başlatır
- **Endpoint:** `POST /api/agents/start`
- **Eylem:**
  - `launcher.py` script'ini çalıştırır
  - Tüm ajan durumlarını "active" yapar
  - WebSocket üzerinden durum güncellemesi gönderir
- **Kullanım:** Dashboard'da "Tüm Ajanları Başlat" butonuna tıklayın

#### 2. Sistemi Durdur (Kırmızı Buton)
- **Fonksiyon:** Tüm ajanları durdurur
- **Endpoint:** `POST /api/agents/stop`
- **Eylem:**
  - Tüm ajan durumlarını "idle" yapar
  - Inter-agent bus'a durdurma mesajı gönderir
  - WebSocket üzerinden durum güncellemesi gönderir
- **Kullanım:** Dashboard'da "Sistemi Durdur" butonuna tıklayın

#### 3. Affiliate Görevini Tetikle (Mor Buton)
- **Fonksiyon:** Affiliate yield harmonization görevini tetikler
- **Endpoint:** `POST /api/affiliate/trigger`
- **Eylem:**
  - Emma (Financial) ajanına görev mesajı gönderir
  - Emma ajanını "busy" durumuna getirir
  - Inter-agent bus'a görev mesajı gönderir
  - WebSocket üzerinden durum güncellemesi gönderir
- **Kullanım:** Dashboard'da "Affiliate Görevini Tetikle" butonuna tıklayın

### Buton Davranışları

- **Loading:** Butona tıklandığında spinner animasyonu görünür
- **Success:** İşlem başarılı olursa ✓ ikonu görünür (2 saniye)
- **Error:** İşlem başarısız olursa ⚠ ikonu görünür (2 saniye)
- **Disabled:** İşlem sırasında buton devre dışı kalır

### Veya Uvicorn ile

```bash
uvicorn dashboard:app --host 0.0.0.0 --port 8000 --reload
```

### Dashboard'a Erişim

Tarayıcıda açın:
```
http://localhost:8000
```

## 📐 Grid Layout

### Zone Haritası (2x4)

```
┌─────────┬─────────┬─────────┬─────────┐
│ Zone 1  │ Zone 2  │ Zone 3  │ Zone 4  │
│  Elif   │  Amara  │  Lucia  │ Sophie  │
├─────────┼─────────┼─────────┼─────────┤
│ Zone 5  │ Zone 6  │ Zone 7  │ Zone 8  │
│  Emma   │  Yuki   │  Alina  │ Camille │
└─────────┴─────────┴─────────┴─────────┘
```

### Ajan Renkleri

- Elif: #FF6B6B (Kırmızı)
- Amara: #4ECDC4 (Turkuaz)
- Lucia: #45B7D1 (Mavi)
- Sophie: #96CEB4 (Yeşil)
- Emma: #FFEAA7 (Sarı)
- Yuki: #DDA0DD (Mor)
- Alina: #F39C12 (Turuncu)
- Camille: #E74C3C (Koyu Kırmızı)

## 🔌 API Endpoint'leri

### Ajan Endpoint'leri

#### Tüm Ajanları Getir
```http
GET /api/agents
```

**Response:**
```json
[
    {
        "id": "elif",
        "name": "Elif",
        "module": "elif_agent.py",
        "command": "python elif_agent.py",
        "description": "Content Strategy & Planning Agent",
        "color": "#FF6B6B"
    },
    ...
]
```

#### Ajan Durumlarını Getir
```http
GET /api/agents/states
```

**Response:**
```json
{
    "elif": {
        "status": "active",
        "task": "Content strategy planning",
        "last_log": "Planning completed"
    },
    ...
}
```

#### Tekil Ajan Durumu
```http
GET /api/agents/{agent_id}/state
```

**Response:**
```json
{
    "status": "active",
    "task": "Content strategy planning",
    "last_log": "Planning completed"
}
```

#### Ajan Loglarını Getir
```http
GET /api/agents/{agent_id}/logs?limit=10
```

**Response:**
```json
[
    {
        "timestamp": "2026-09-08T17:30:00",
        "message": "Planning completed"
    },
    ...
]
```

#### Ajan Durumunu Güncelle
```http
POST /api/agents/{agent_id}/state
Content-Type: application/json

{
    "status": "busy",
    "task": "Processing data"
}
```

### Inter-Agent Bus Endpoint'leri

#### Bus Mesajlarını Getir
```http
GET /api/bus/messages?limit=20
```

**Response:**
```json
[
    {
        "timestamp": "2026-09-08T17:30:00",
        "source": "elif",
        "target": "amara",
        "type": "message",
        "message": "İçerik stratejisi hazır"
    },
    ...
]
```

#### Bus Mesajı Gönder
```http
POST /api/bus/message
Content-Type: application/json

{
    "source": "elif",
    "target": "amara",
    "type": "message",
    "message": "İçerik stratejisi hazır"
}
```

## 🔌 WebSocket Endpoint

### Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'agent_state') {
        // Ajan durumu güncellendi
        console.log(`Agent ${data.agent_id} state updated`);
    } else if (data.type === 'bus_message') {
        // Bus mesajı geldi
        console.log('New bus message');
    }
};
```

### WebSocket Mesaj Tipleri

- `agent_state`: Ajan durumu güncellendi
- `agent_log`: Ajan logu eklendi
- `bus_message`: Bus mesajı geldi
- `echo`: Echo mesajı

## 🎨 Arayüz Özellikleri

### Agent Card

Her ajan için kart gösterimi:
- Ajan avatarı ve ismi
- Durum göstergesi (Active/Inactive/Busy)
- Mevcut görev
- Son loglar

### Inter-Agent Bus

Ajanlar arası iletişim:
- Mesaj kaynağı
- Mesaj tipi
- Mesaj içeriği
- Zaman damgası

### Responsive Design

- Desktop: 4 sütun
- Tablet: 3 sütun
- Mobile: 2 sütun
- Small Mobile: 1 sütun

## 🔧 Konfigürasyon

### Port Değiştirme

```bash
uvicorn dashboard:app --host 0.0.0.0 --port 8080
```

### Log Dizini Değiştirme

`dashboard.py` dosyasında:

```python
LOG_DIR = Path("logs")  # Değiştir
INTER_AGENT_BUS_FILE = LOG_DIR / "inter_agent_bus.jsonl"  # Değiştir
```

### Ajan Durumları

`dashboard.py` dosyasında:

```python
agent_states = {
    "elif": {"status": "active", "task": "Content strategy planning", ...},
    ...
}
```

## 🔄 Orchestrator Entegrasyonu

### Orchestrator'dan Dashboard'a Veri Gönderme

```python
import requests

# Ajan durumunu güncelle
response = requests.post(
    "http://localhost:8000/api/agents/elif/state",
    json={
        "status": "busy",
        "task": "Processing content"
    }
)

# Bus mesajı gönder
response = requests.post(
    "http://localhost:8000/api/bus/message",
    json={
        "source": "elif",
        "target": "amara",
        "type": "message",
        "message": "Content ready for distribution"
    }
)
```

### Dashboard'dan Orchestrator'a Veri Okuma

```python
import requests

# Ajan durumlarını oku
response = requests.get("http://localhost:8000/api/agents/states")
states = response.json()

# Bus mesajlarını oku
response = requests.get("http://localhost:8000/api/bus/messages")
messages = response.json()
```

## 📊 İzleme

### Dashboard Arayüzü

Tarayıcıda `http://localhost:8000` adresini açın:
- 8 ajan kartı görüntülenir
- Durumlar canlı güncellenir
- Loglar otomatik yüklenir
- Bus mesajları izlenir

### API Dokümantasyonu

Swagger UI:
```
http://localhost:8000/docs
```

ReDoc:
```
http://localhost:8000/redoc
```

## 🔐 Güvenlik

### CORS

Tüm origin'lere izin veriliyor (geliştirme için). Production'da kısıtlayın:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Kısıtla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Authentication

Production'da JWT veya OAuth ekleyin:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/agents")
async def get_agents(token: str = Depends(security)):
    # Token doğrulama
    pass
```

## 🚀 Gelişmiş Kullanım

### Özel Ajan Ekleme

`agent_config.json` dosyasına yeni ajan ekleyin:

```json
{
    "agents": [
        ...
        {
            "id": "yeni_ajan",
            "name": "Yeni Ajan",
            "module": "yeni_ajan_agent.py",
            "command": "python yeni_ajan_agent.py",
            "description": "Yeni Ajan Açıklaması",
            "color": "#FFFFFF"
        }
    ]
}
```

### Grid Boyutunu Değiştirme

`agent_config.json` dosyasında:

```json
{
    "grid_layout": {
        "rows": 3,
        "columns": 3,
        "zones": [...]
    }
}
```

Dashboard HTML'de grid'i güncelleyin:

```css
.grid {
    grid-template-columns: repeat(3, 1fr);
}
```

## 🔍 Sorun Giderme

### Dashboard Başlamıyor

**Sorun:** Dashboard başlatılamıyor.

**Çözüm:**
1. FastAPI ve uvicorn yüklü mü?
   ```bash
   pip install fastapi uvicorn websockets
   ```
2. Port 8000 kullanımda mı?
   ```bash
   # Farklı port kullan
   uvicorn dashboard:app --port 8080
   ```

### Ajanlar Görünmüyor

**Sorun:** Ajanlar dashboard'da görünmüyor.

**Çözüm:**
1. `agent_config.json` dosyası var mı?
2. 8 ajan tanımlı mı?
3. JSON formatı doğru mu?

### WebSocket Bağlantısı Hatası

**Sorun:** WebSocket bağlantısı kurulamıyor.

**Çözüm:**
1. Firewall ayarlarını kontrol edin
2. Proxy ayarlarını kontrol edin
3. WebSocket destekli tarayıcı kullanın

### Loglar Okunamıyor

**Sorun:** Ajan logları okunamıyor.

**Çözüm:**
1. `logs/` klasörü var mı?
2. Log dosyaları var mı?
3. Dosya izinleri doğru mu?

## 📝 Sürüm Bilgisi

- Sürüm: 1.0.0
- Tarih: 08.09.2026
- Python: 3.8+
- FastAPI: 0.104+
- Uvicorn: 0.24+

## ✅ Kontrol Listesi

Başlatmadan önce:
- [ ] Python yüklü mü?
- [ ] FastAPI yüklü mü?
- [ ] Uvicorn yüklü mü?
- [ ] Websockets yüklü mü?
- [ ] `agent_config.json` var mı?
- [ ] 8 ajan tanımlı mı?
- [ ] `logs/` klasörü var mı?
- [ ] Port 8000 boş mu?

## 🎉 Başarıyla Başlatıldığında

- ✅ Dashboard tarayıcıda açılacak
- ✅ 8 ajan kartı görüntülenecek
- ✅ Durumlar canlı güncellenecek
- ✅ Loglar otomatik yüklenecek
- ✅ Bus mesajları izlenecek
- ✅ WebSocket bağlantısı aktif olacak

## 📞 Destek

Sorun yaşarsanız:
1. API dokümantasyonunu kontrol edin (`/docs`)
2. Log dosyalarını inceleyin
3. Terminal çıktısını kontrol edin
4. Gereksinimleri doğrulayın

---

**İyi çalışmalar! 🚀**
