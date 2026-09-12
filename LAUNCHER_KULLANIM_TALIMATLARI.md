# LAUNCHER.PY - KULLANIM TALIMATLARI

## 📋 Genel Bakış

`launcher.py` scripti, çoklu ajan ekosistemini ekranda canlı olarak ayağa kaldıran gelişmiş bir AGI masaüstü otomasyon aracıdır.

## 🚀 Özellikler

- ✅ 6 temel ajanı (Elif, Amara, Lucia, Sophie, Emma, Yuki) başlatır
- ✅ Her ajan için ayrı terminal/cmd penceresi açar
- ✅ Pencere başlıklarını ajan isimleriyle eşleştirir
- ✅ 2 satır x 3 sütun (6 zone) grid yerleşimi yapar
- ✅ Log ve mesaj bus takibi sağlar
- ✅ Otomatik kütüphane kurulumu
- ✅ Windows ve Linux/Mac desteği

## 📦 Gereksinimler

### Python Kütüphaneleri

Script otomatik olarak gerekli kütüphaneleri yükler:
- `pygetwindow` - Pencere yönetimi
- `screeninfo` - Ekran bilgileri

### Manuel Kurulum (Opsiyonel)

```bash
pip install pygetwindow screeninfo
```

## 🔧 Kurulum

### 1. Dosyaların Hazırlanması

Aşağıdaki dosyaların proje klasöründe olduğundan emin olun:

```
sosyal_imece/
├── launcher.py              # Ana launcher scripti
├── agent_config.json        # Ajan konfigürasyonu
├── window_layout.ahk        # AutoHotkey layout scripti (opsiyonel)
├── logs/
│   └── inter_agent_bus.jsonl  # Inter-agent log dosyası
└── agents/                  # Ajan modülleri
    ├── elif_agent.py
    ├── amara_agent.py
    ├── lucia_agent.py
    ├── sophie_agent.py
    ├── emma_agent.py
    └── yuki_agent.py
```

### 2. Ajan Modüllerini Oluşturma

Her ajan için basit bir Python modülü oluşturun:

**elif_agent.py:**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

print("🎭 Elif - Content Strategy & Planning Agent başlatılıyor...")
print("📋 Görev: İçerik stratejisi ve planlama")

while True:
    print(f"[{time.strftime('%H:%M:%S')}] Elif çalışıyor...")
    time.sleep(5)
```

Diğer ajanlar için benzer modüller oluşturun (amara_agent.py, lucia_agent.py, vb.)

## 🎯 Kullanım

### Temel Kullanım

```bash
cd c:\Users\Habitat\Desktop\sosyal_imece
python launcher.py
```

### Beklenen Çıktı

```
🚀 [Launcher] AGI Masaüstü Otomasyon Başlatılıyor...
📋 [Config] 6 ajan yüklendi
📝 [Log] logs/inter_agent_bus.jsonl dosyası oluşturuldu
📐 [Grid] 2x3 grid hesaplandı (1920x1080)
📐 [Grid] Zone boyutu: 640x540

============================================================
🚀 TÜM AJANLAR BAŞLATILIYOR
============================================================

🔧 [Ajan] Elif başlatılıyor...
✅ [Ajan] Elif başlatıldı (PID: 12345)
🔧 [Ajan] Amara başlatılıyor...
✅ [Ajan] Amara başlatıldı (PID: 12346)
... (diğer ajanlar)

============================================================
⏳ Pencerelerin açılması bekleniyor...
============================================================

🎯 [Layout] Pencereler yerleştiriliyor...
✅ [Layout] Elif -> Zone 1 (0,0)
✅ [Layout] Amara -> Zone 2 (640,0)
... (diğer pencereler)

✅ [Layout] Tüm pencereler yerleştirildi
🧪 [Test] Inter-agent bus testi başlatılıyor...
✅ [Test] Test mesajı yazıldı: logs/inter_agent_bus.jsonl
✅ [Test] Mesaj doğrulandı: Inter-agent bus aktif ve çalışıyor

============================================================
✅ SİSTEM AKTİF VE HAZIR
============================================================
📊 Aktif Ajanlar: 6
📐 Grid Layout: 2x3
📝 Log Bus: logs/inter_agent_bus.jsonl
============================================================
```

## 📐 Grid Yerleşimi

### Zone Haritası

```
┌─────────────┬─────────────┬─────────────┐
│  Zone 1     │  Zone 2     │  Zone 3     │
│  Elif       │  Amara      │  Lucia      │
│  (0,0)      │  (640,0)    │  (1280,0)   │
├─────────────┼─────────────┼─────────────┤
│  Zone 4     │  Zone 5     │  Zone 6     │
│  Sophie     │  Emma       │  Yuki       │
│  (0,540)    │  (640,540)  │  (1280,540) │
└─────────────┴─────────────┴─────────────┘
```

### Zone Boyutları (1920x1080 Ekran)

- Zone Genişliği: 640px
- Zone Yüksekliği: 540px
- Toplam Zone: 6

## 🔍 Inter-Agent Bus

### Log Dosyası

`logs/inter_agent_bus.jsonl` dosyası ajanlar arası iletişimi kaydeder.

### Log Formatı

```json
{
  "timestamp": "2026-09-08T17:30:00",
  "source": "elif",
  "target": "amara",
  "type": "message",
  "message": "İçerik stratejisi hazır",
  "status": "success"
}
```

### Log Okuma

```bash
# Son 10 mesajı görüntüle
Get-Content logs\inter_agent_bus.jsonl -Tail 10

# Gerçek zamanlı izleme (PowerShell)
Get-Content logs\inter_agent_bus.jsonl -Wait
```

## ⚙️ Konfigürasyon

### agent_config.json

Ajan bilgilerini `agent_config.json` dosyasından düzenleyebilirsiniz:

```json
{
    "agents": [
        {
            "id": "elif",
            "name": "Elif",
            "module": "elif_agent.py",
            "command": "python elif_agent.py",
            "description": "Content Strategy & Planning Agent",
            "color": "#FF6B6B"
        },
        ...
    ],
    "grid_layout": {
        "rows": 2,
        "columns": 3,
        ...
    }
}
```

### Grid Düzenleme

Grid boyutlarını değiştirmek için `agent_config.json` dosyasını düzenleyin:

```json
{
    "grid_layout": {
        "rows": 3,
        "columns": 2,
        ...
    }
}
```

## 🛑 Durdurma

### Manuel Durdurma

Terminalde `Ctrl+C` tuşuna basın:

```bash
^C
🛑 [Kullanıcı] Durdurma sinyali alındı
🧹 [Cleanup] Süreçler temizleniyor...
✅ [Cleanup] Elif durduruldu
✅ [Cleanup] Amara durduruldu
...
👋 [Launcher] Güle güle!
```

### Otomatik Temizlik

Script kapatıldığında otomatik olarak tüm ajan süreçlerini temizler.

## 🔧 Sorun Giderme

### Pencereler Yerleşmiyor

**Sorun:** Pencereler grid'e yerleşmiyor.

**Çözüm:**
1. Pencerelerin açılması için yeterli bekleme süresi (3 saniye)
2. Pencere başlıklarının doğru olduğundan emin olun
3. `pygetwindow` kütüphanesinin yüklü olduğundan emin olun

### Ajanlar Başlamıyor

**Sorun:** Ajan modülleri başlatılamıyor.

**Çözüm:**
1. Ajan modüllerinin (`elif_agent.py`, vb.) varlığını kontrol edin
2. Python path'in doğru olduğundan emin olun
3. Ajan modüllerinde syntax hatası olmadığını kontrol edin

### Log Dosyası Oluşturulmuyor

**Sorun:** `inter_agent_bus.jsonl` dosyası oluşturulmuyor.

**Çözüm:**
1. `logs/` klasörünün varlığını kontrol edin
2. Yazma izinlerinin olduğundan emin olun
3. Disk alanının yeterli olduğundan emin olun

## 🎨 AutoHotkey Entegrasyonu (Opsiyonel)

### window_layout.ahk Kullanımı

AutoHotkey scriptini manuel olarak çalıştırabilirsiniz:

```bash
# AutoHotkey kurulu olmalı
AutoHotkey.exe window_layout.ahk
```

### Hotkey

- `Ctrl+Alt+L`: Pencereleri yeniden düzenle

## 📊 İzleme

### Sistem Durumu

Terminal çıktısından sistem durumunu izleyebilirsiniz:

- Aktif ajan sayısı
- Grid layout bilgisi
- Log bus durumu
- PID bilgileri

### Log İzleme

```bash
# PowerShell
Get-Content logs\inter_agent_bus.jsonl -Wait

# Linux/Mac
tail -f logs/inter_agent_bus.jsonl
```

## 🔐 Güvenlik

### Hassas Bilgiler

- Şifreler ve API anahtarları environment variables'da saklanmalıdır
- `agent_config.json` versiyon kontrolüne dahil edilmemelidir
- Log dosyaları hassas bilgiler içermemelidir

### İzinler

- Script'in terminal açma izni olmalıdır
- Pencere yönetimi için admin izni gerekebilir

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

3x2 grid için:

```json
{
    "grid_layout": {
        "rows": 3,
        "columns": 2,
        "zones": [
            {"id": 1, "row": 0, "col": 0, "agent": "elif"},
            {"id": 2, "row": 0, "col": 1, "agent": "amara"},
            {"id": 3, "row": 1, "col": 0, "agent": "lucia"},
            {"id": 4, "row": 1, "col": 1, "agent": "sophie"},
            {"id": 5, "row": 2, "col": 0, "agent": "emma"},
            {"id": 6, "row": 2, "col": 1, "agent": "yuki"}
        ]
    }
}
```

## 📞 Destek

Sorun yaşarsanız:
1. Log dosyalarını kontrol edin
2. Terminal çıktısını inceleyin
3. Gereksinimleri doğrulayın
4. Konfigürasyonu kontrol edin

## 📝 Sürüm Bilgisi

- Sürüm: 1.0.0
- Tarih: 08.09.2026
- Python: 3.x
- Platform: Windows, Linux, Mac

## ✅ Kontrol Listesi

Başlatmadan önce:
- [ ] Python yüklü mü?
- [ ] Gerekli kütüphaneler yüklü mü?
- [ ] `agent_config.json` var mı?
- [ ] Ajan modülleri var mı?
- [ ] `logs/` klasörü var mı?
- [ ] Yazma izinleri var mı?

## 🎉 Başarıyla Başlatıldığında

- ✅ 6 ajan penceresi açılacak
- ✅ Pencereler 2x3 grid'e yerleşecek
- ✅ Inter-agent bus aktif olacak
- ✅ Log dosyası oluşturulacak
- ✅ Sistem çalışır durumda olacak

---

**İyi çalışmalar! 🚀**
