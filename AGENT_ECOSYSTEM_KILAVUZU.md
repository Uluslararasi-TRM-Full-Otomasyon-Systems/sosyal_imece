# Sosyal İmece Ajan Ekosistemi - Kurulum ve Kullanım Kılavuzu

## 📋 Genel Bakış

Bu sistem, 1200+ ajan ekosisteminiz için tamamen yerel çalışan bir yönetim altyapısıdır. Hiçbir dış servise bağımlı değildir ve tüm veriler SQLite veritabanında saklanır.

### 🏗️ Sistem Bileşenleri

1. **agent_ecosystem_backend.py** - FastAPI backend sunucusu
2. **agent_writer_module.py** - Ajanların veri yazması için Python modülü
3. **agent_ecosystem_dashboard.html** - Fütüristik HTML dashboard paneli
4. **agent_ecosystem.db** - SQLite veritabanı (otomatik oluşturulur)

---

## 🚀 Hızlı Başlangıç

### Adım 1: Sanal Ortam Kurulumu (İlk kez)

```bash
# Proje dizinine gidin
cd C:\Users\Habitat\Desktop\sosyal_imece

# Sanal ortam oluşturun
python -m venv .venv

# Sanal ortamı aktif edin
.venv\Scripts\activate

# Paketleri yükleyin
pip install -r requirements.txt
```

### Adım 2: Sistemi Başlatın

```bash
# Otomatik başlatma scriptini çalıştırın
START_AGENT_ECOSYSTEM.bat
```

Bu script:
- Sanal ortamı aktif eder
- FastAPI backend sunucusunu başlatır (http://localhost:8000)
- HTML dashboard panelini tarayıcıda açar

### Adım 3: Sistemi Kullanın

- **Dashboard**: Tarayıcıda otomatik açılan paneli kullanın
- **API Dokümantasyonu**: http://localhost:8000/docs adresinden tüm API endpointlerini görüntüleyin
- **Veritabanı**: `agent_ecosystem.db` dosyası otomatik oluşturulur

---

## 📊 Veri Yapısı

### Tablolar

1. **agencies** - Ajans bilgileri
2. **agents** - Ajan bilgileri ve durumları
3. **tasks** - Görevler ve durumları
4. **brand_proposals** - Marka teklifleri ($1400 vb.)
5. **customer_requests** - Müşteri talepleri
6. **calendar_events** - Takvim olayları
7. **system_status** - Sistem metrikleri

---

## 🤖 Ajanlardan Veri Yazma

### Temel Kullanım

Ajanlarınızın veri yazması için `agent_writer_module.py` modülünü kullanın:

```python
from agent_writer_module import AgentDataWriter

# Writer'ı başlat
writer = AgentDataWriter()

# Ajan durumunu güncelle
writer.mark_agent_active(agent_id=1)
writer.mark_agent_busy(agent_id=1)
writer.mark_agent_idle(agent_id=1)
```

### Görev Oluşturma

```python
# Yeni görev oluştur
task_id = writer.create_task(
    agent_id=1,
    title="Müşteri analizi yap",
    description="Geçen ayın müşteri verilerini analiz et",
    priority="high"
)

# Görevi tamamla
writer.complete_task(task_id, result="Analiz tamamlandı, 500+ kayıt işlendi")

# Görev başarısız oldu
writer.fail_task(task_id, error_message="Veri erişim hatası")
```

### Marka Teklifi Oluşturma

```python
# Yeni marka teklifi
proposal_id = writer.create_brand_proposal(
    brand_name="Nike",
    proposal_amount=1400.00,
    currency="USD",
    agent_id=1,
    notes="Sosyal medya kampanyası için"
)
```

### Müşteri Talebi Oluşturma

```python
# Yeni müşteri talebi
request_id = writer.create_customer_request(
    request_text="Yeni bir özellik istiyorum",
    customer_name="Ahmet Yılmaz",
    priority="high",
    agent_id=1
)
```

### Takvim Olayı Oluşturma

```python
# Yeni takvim olayı
event_id = writer.create_calendar_event(
    title="Müşteri Toplantısı",
    event_date="2026-10-15",
    event_time="14:00",
    event_type="meeting",
    agent_id=1
)
```

### Hızlı Fonksiyonlar

Kısa kullanım için hazır fonksiyonlar:

```python
from agent_writer_module import quick_log_task, quick_log_proposal, quick_mark_active

# Hızlı görev loglama
quick_log_task(1, "Analiz tamamlandı", "Müşteri verileri işlendi")

# Hızlı teklif loglama
quick_log_proposal("Nike", 1400.00, 1)

# Hızlı ajan aktifleştirme
quick_mark_active(1)
```

### Toplu İşlemler

```python
# Toplu görev oluşturma
tasks = [
    {"agent_id": 1, "title": "Görev 1", "priority": "medium"},
    {"agent_id": 2, "title": "Görev 2", "priority": "high"},
    {"agent_id": 3, "title": "Görev 3", "priority": "low"}
]
task_ids = writer.bulk_create_tasks(tasks)

# Toplu teklif oluşturma
proposals = [
    {"brand_name": "Nike", "proposal_amount": 1400.00, "agent_id": 1},
    {"brand_name": "Adidas", "proposal_amount": 1200.00, "agent_id": 2}
]
proposal_ids = writer.bulk_create_proposals(proposals)
```

---

## 🔌 API Endpointleri

### Sistem Durumu

- `GET /` - API ana sayfası
- `GET /api/health` - Sağlık kontrolü
- `GET /api/dashboard` - Dashboard istatistikleri
- `GET /api/status/export` - Tüm verileri JSON olarak dışa aktar

### Ajanslar

- `POST /api/agencies` - Yeni ajans oluştur
- `GET /api/agencies` - Tüm ajansları listele
- `GET /api/agencies/{agency_id}` - Ajans detaylarını getir

### Ajanlar

- `POST /api/agents` - Yeni ajan oluştur
- `GET /api/agents` - Ajanları listele (filtreleme desteği)
- `PUT /api/agents/{agent_id}/status` - Ajan durumunu güncelle

### Görevler

- `POST /api/tasks` - Yeni görev oluştur
- `GET /api/tasks` - Görevleri listele
- `PUT /api/tasks/{task_id}/status` - Görev durumunu güncelle

### Marka Teklifleri

- `POST /api/proposals` - Yeni teklif oluştur
- `GET /api/proposals` - Teklifleri listele

### Müşteri Talepleri

- `POST /api/requests` - Yeni talep oluştur
- `GET /api/requests` - Talepleri listele

### Takvim

- `POST /api/calendar` - Yeni olay oluştur
- `GET /api/calendar` - Olayları listele

---

## 🎨 Dashboard Paneli

HTML dashboard paneli (`agent_ecosystem_dashboard.html`) şunları sağlar:

- **Gerçek zamanlı istatistikler** - Ajan sayısı, görev durumu, gelir vb.
- **Ajan listesi** - Durumları ve tipleri ile birlikte
- **Görev takibi** - Bekleyen ve tamamlanan görevler
- **Teklif yönetimi** - Marka teklifleri ve durumları
- **Müşteri talepleri** - Gelen talepler ve yanıtlar
- **Takvim görünümü** - Yaklaşan olaylar ve toplantılar

Panel otomatik olarak her 30 saniyede bir verileri yeniler.

---

## 🔧 Manuel Başlatma

### Backend Sunucusunu Başlatma

```bash
# Sanal ortamı aktif et
.venv\Scripts\activate

# Backend sunucusunu başlat
python agent_ecosystem_backend.py
```

Backend şu adreslerde çalışır:
- API: http://localhost:8000
- Dokümantasyon: http://localhost:8000/docs

### Dashboard Panelini Açma

```bash
# Tarayıcıda HTML dosyasını aç
start agent_ecosystem_dashboard.html
```

Veya doğrudan dosyaya çift tıklayın.

---

## 📁 Dosya Yapısı

```
sosyal_imece/
├── agent_ecosystem_backend.py      # FastAPI backend sunucusu
├── agent_writer_module.py          # Ajan veri yazma modülü
├── agent_ecosystem_dashboard.html  # HTML dashboard paneli
├── agent_ecosystem.db              # SQLite veritabanı (otomatik)
├── START_AGENT_ECOSYSTEM.bat       # Otomatik başlatma scripti
├── requirements.txt                # Python paketleri
└── AGENT_ECOSYSTEM_KILAVUZU.md     # Bu dosya
```

---

## 🛠️ Sorun Giderme

### Port 8000 Zaten Kullanımda

Eğer port 8000 zaten kullanımda ise, `agent_ecosystem_backend.py` dosyasındaki portu değiştirin:

```python
# Dosyanın sonunda
uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
```

Ardından HTML dosyasındaki `API_BASE` değerini güncelleyin:

```javascript
const API_BASE = 'http://localhost:8001/api';
```

### Veritabanı Sorunları

Veritabanı dosyasını silip yeniden oluşturabilirsiniz:

```bash
del agent_ecosystem.db
python agent_ecosystem_backend.py
```

### Paket Yükleme Hataları

```bash
# Sanal ortamı yeniden oluştur
rmdir /s .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📊 Dashboard İstatistikleri

Dashboard şu metrikleri gösterir:

- **Toplam Ajan** - Sistemdeki toplam ajan sayısı
- **Aktif Ajan** - Şu an aktif olan ajanlar
- **Toplam Görev** - Sistemdeki toplam görev sayısı
- **Tamamlanan Görev** - Başarıyla tamamlanan görevler
- **Toplam Gelir** - Kabul edilen tekliflerin toplam tutarı
- **Müşteri Talepleri** - Toplam müşteri talebi sayısı

---

## 🔒 Güvenlik

Bu sistem tamamen yerel çalışır ve hiçbir dış servise bağlanmaz:

- ❌ Dünya çapında internet erişimi yok
- ❌ Bulut depolama yok
- ❌ Üçüncü parti API'ler yok
- ✅ Tüm veriler yerel SQLite veritabanında
- ✅ Sadece localhost'tan erişilebilir

---

## 🚀 İleri Düzey Kullanım

### Veritabanını Doğrudan Sorgulama

```python
import sqlite3

conn = sqlite3.connect('agent_ecosystem.db')
cursor = conn.cursor()

# Özel sorgular
cursor.execute("SELECT * FROM agents WHERE status = 'active'")
active_agents = cursor.fetchall()

conn.close()
```

### Veri Dışa Aktarma

```python
from agent_writer_module import AgentDataWriter

writer = AgentDataWriter()
all_data = writer.export_all_data()

# JSON olarak kaydet
import json
with open('backup.json', 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
```

---

## 📞 Destek

Sorularınız için:
1. API dokümantasyonunu inceleyin: http://localhost:8000/docs
2. Bu kılavuzu tekrar okuyun
3. Kod örneklerini test edin

---

## 🎯 Sonraki Adımlar

1. ✅ Sistemi başlatın
2. ✅ Dashboard panelini açın
3. ✅ API dokümantasyonunu inceleyin
4. ✅ Ajanlarınıza veri yazma modülünü entegre edin
5. ✅ İlk verileri ekleyin
6. ✅ Dashboard'da gerçek zamanlı izleme yapın

---

**Sosyal İmece Ajan Ekosistemi © 2026**
