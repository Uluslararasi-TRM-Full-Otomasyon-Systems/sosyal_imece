# TRM Derya — Windows → Linux VPS taşıma rehberi

Bu paket dört parçadan oluşur ve **hiçbiri tek başına sistemi taşımaz**:

| Dosya | Ne yapar | Ne yapmaz |
|---|---|---|
| `deploy_vps.sh` | Ubuntu 22.04 / Debian 12'de bağımlılıkları kurar (Python, sqlite3, Chrome, eşleşen chromedriver, xvfb), venv açar, `/etc/trm-derya.env` şablonu ve systemd birimini hazırlar | WhatsApp otomasyonunu başlatmaz, API anahtarı yazmaz, veri taşımaz |
| `trm-derya.service` | `api_server_2.py` + otonom motoru boot sonrası 7/24 ayakta tutar | Windows'ta çalışmaz (Linux/systemd içindir) |
| `requirements_vps.txt` | `api_server_2.py`'nin **gerçek** import listesi (flask, flask-cors, selenium, webdriver-manager) | Streamlit/panel bağımlılıklarını içermez (bilerek) |
| `VPS_TASIMA_REHBERI.md` | Veritabanı + WhatsApp oturumunun kayıpsız taşınması ve kabul testleri — **bu dosya** | — |

Kod tarafında yapılan tek değişiklik Linux uyumu: `api_server_2.py` artık
`HEADLESS_MODE=true` ile `--headless=new` Chrome başlatıyor, `CHROME_BINARY` /
`CHROMEDRIVER_PATH` ile sürücü yolu sabitlenebiliyor, kalıntı temizliği
Windows'taki hedefli `taskkill` mantığının POSIX karşılığını (`pgrep` + `kill`)
kullanıyor ve `SIGTERM`'de sürücüyü kapatıp çıkıyor. `WINDOWS_DEPLOY.md` /
`baslat_trm.bat` tarafı hiç değişmedi; Windows kurulumu eskisi gibi çalışır.

---

## 0. Kural: aynı anda tek makine

`WHATSAPP_OTOMATIK_BASLAT=1` olduğu sürece servis açılır açılmaz Chrome + WhatsApp
Web + otonom kuyruk başlar. **Windows makine ayaktayken VPS'i de başlatırsan iki
taraf aynı hatla aynı kuyruğa bakar ve mesaj iki kez gider.** Sıra kesin:

1. VPS'te her şey kurulu ve **veriler taşınmış** olsun, servis **duruşunda** kalsın.
2. Windows'ta servisi durdur (`baslat_trm.bat durum` ile PID gör, sonra kapat).
3. VPS'te `systemctl start trm-derya.service`.
4. `/api/saglik` → `"whatsapp":"giris_yapildi"` görülene kadar Windows'u geri açma.

Ayrıca: sunucuya taşınan `trm_veritabani.db` artık **birincil** kopyadır. Windows'taki
kopya donmuş yedek olarak kalır, üzerine yazılmaz.

---

## 1. Hedef yerleşim

| Windows (bugün) | Linux VPS |
|---|---|
| `C:\...\trm-ekosistem-ticari-kuresel-otomasyon\api_server_2.py` | `$TRM_DIR/api_server_2.py` (varsayılan: betiğin kendi dizini, ör. `/opt/trm/derya`) |
| `...\trm_veritabani.db` | `$TRM_DIR/trm_veritabani.db` — yol **dosya-göreli**, taşınması gerekmez, aynı klasörde olmalı |
| `C:\TRM_WhatsApp_Session_Clean\TRM_Main` | `/var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean/TRM_Main` |
| `...\whatsapp_hata_kayitlari\*.png` | `$TRM_DIR/whatsapp_hata_kayitlari/` |
| (`.env` içindeki anahtarlar, DPAPI kasası) | `/etc/trm-derya.env` — **bkz. bölüm 7** |

`$TRM_DIR` = `deploy_vps.sh`'ın `--dir` bayrağıyla verdiğin (vermezsen betiğin içinde
olduğu) dizin; systemd birimindeki `@TRM_DIR@` yer tutucusu kurulumda bu yolla
değiştirilir.

`TRM_WhatsApp` deseni profil yolunda **kalmak zorunda**: `api_server_2.py`'nin kalıntı
temizliği yalnızca komut satırında bu deseni gördüğü Chrome süreçlerini öldürür; desen
düşerse hedefli temizlik kendini tamamen kapatır (güvenlik davranışı, bozulmamalı).

Boyut gerçeği (bu makinede ölçüldü): `TRM_Main` = 340 MB, bunun 239 MB'ı yeniden
üretilen önbellek (`Cache`, `Code Cache`, `Service Worker`, GPU). Oturum için gereken
öz: `Default/IndexedDB` (48 MB) + `Default/Local Storage` + `Network/Cookies` +
`Preferences` + `Local State` + `TRM_BAGLI_HAT.txt` ≈ 55 MB.

---

## 2. Kodu sunucuya kopyala

Önce VPS'e bir klasör aç (bu adımlar sunucuda, `sudo` ile):

```bash
sudo mkdir -p /opt/trm && sudo chown "$USER" /opt/trm
```

Windows'tan (Git Bash / WSL / PowerShell `ssh` ikilisi yeter):

```bash
cd /c/Users/Habitat/Desktop/trm-ekosistem-ticari-kuresel-otomasyon
rsync -az --stats \
  --exclude 'venv/' --exclude '.venv/' --exclude '__pycache__/' \
  --exclude 'yedekler/' --exclude 'yedeklerim*' --exclude 'arsiv/' --exclude 'archives/' \
  --exclude 'backups/' --exclude 'node_modules/' \
  --exclude 'config.env' --exclude 'secrets.env' --exclude 'api_keys.json' \
  --exclude '.env/' \
  --exclude '*.db' --exclude '*.db-wal' --exclude '*.db-shm' \
  --exclude 'whatsapp_hata_kayitlari/' \
  ./ "$KULLANICI@$VPS_IP:/opt/trm/derya/"
```

Neden dışarıda bırakıldı:
- `venv/` — Windows sanal ortamı Linux'ta çalışmaz; `deploy_vps.sh` temizini açar.
- `.env/`, `secrets.env`, `api_keys.json`, `config.env` — **canlı anahtarlar**. Sunucuya
  asla kopyayla taşınmaz; bölüm 7'de kullanıcı kendisi girer.
- `*.db` — veritabanı bölüm 4'te tutarlı bir anlık görüntüyle taşınır (dosya kopyası
  yarım yazma içerebilir).

Windows'ta `rsync` yoksa: PowerShell ile `Compress-Archive`/`scp` de olur, ancak
`.env` ve `venv` klasörlerini paketlemeden önce çıkardığını **iki kez** kontrol et.

---

## 3. `deploy_vps.sh` çalıştır

Önce hiçbir şeyi değiştirmeden ne yapacağını gör (root gerektirmez):

```bash
cd /opt/trm/derya
bash deploy_vps.sh --dry-run
```

Sonra gerçek kurulum:

```bash
sudo bash deploy_vps.sh
```

Betik, Chrome'un **kurulu büyük sürümüyle birebir eşleşen** chromedriver'ı
`chrome-for-testing`'ten indirir; eşleşme olmazsa Selenium `SessionNotCreated` verir,
bu yüzden bu adım kritik. Betik ayrıca `--servis` bayrağı verilmedikçe servisi
**başlatmaz**. Kullanıcı/port/profil yolu farklıysa:

```bash
sudo bash deploy_vps.sh --dir /opt/trm/derya --user trm --profil /var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean
```

---

## 4. Veritabanını taşı (`trm_veritabani.db`)

**Doğrudan `.db` dosyasını kopyalama** — Chrome/Flask yazma yaparken anlık görüntü yarım
sayfa içerebilir. SQLite'ın online backup API'sini kullan (Windows'ta servis
**duruşunda** olsa bile bu yöntem önerilir):

```bash
cd /c/Users/Habitat/Desktop/trm-ekosistem-ticari-kuresel-otomasyon
python -c "import sqlite3; s=sqlite3.connect('trm_veritabani.db'); d=sqlite3.connect('/tmp/trm_tasima.db'); s.backup(d); d.close(); s.close(); print('anlik goruntu alindi')"
```

Sunucuya gönder ve doğrula:

```bash
scp /tmp/trm_tasima.db "$KULLANICI@$VPS_IP:/tmp/trm_veritabani.db"

# sunucuda:
sqlite3 /tmp/trm_veritabani.db "PRAGMA integrity_check;"        # -> ok
sqlite3 /tmp/trm_veritabani.db "SELECT count(*) FROM esnaflar;" # -> Windows'taki sayi ile ayni olmali
```

Satır sayılarını **taşımadan önce Windows'ta da** alın; fark kabul edilemez:

```bash
python -c "import sqlite3;c=sqlite3.connect('trm_veritabani.db');[print(t[0], c.execute('select count(*) from \"%s\"'%t[0]).fetchone()[0]) for t in c.execute(\"select name from sqlite_master where type='table' order by name\")]"
```

Sonra yerine koy ( servis dururken ) ve sahipliği ver:

```bash
sudo mv /opt/trm/derya/trm_veritabani.db /opt/trm/derya/trm_veritabani.db.eski 2>/dev/null || true
sudo install -o trm -g trm -m 640 /tmp/trm_veritabani.db /opt/trm/derya/trm_veritabani.db
```

Not: `api_server_2.py` yalnızca `trm_veritabani.db` kullanır. Kökteki `database.db`,
`trm_dashboard.db`, `trm_kuyruk.db`, `trm_*_ledger.db` bu servisin dosyaları değildir;
onları taşımadan önce hangi ajanın okuduğunu doğrula.

---

## 5. WhatsApp oturumunu taşı (`TRM_Main`) — kayıpsız olmanın tek yolu

Bu adım yanlış yapılırsa VPS'te QR tekrar okutulur (ekransız sunucuda bu ayrı bir
iş). Doğru yapılırsa oturum **hiç bozulmadan** sunucuya gelir.

**5.1 Windows'ta her şeyi kapat** (Chrome, chromedriver ve API servisi):

```bash
# C:\TRM_WhatsApp_Session_Clean\TRM_Main\TRM_BAGLI_HAT.txt -> 905426235116 olmali
cat /c/TRM_WhatsApp_Session_Clean/TRM_Main/TRM_BAGLI_HAT.txt
curl -s http://127.0.0.1:5000/api/saglik
```

Servisi durdur, sonra Chrome'un tamamen kapandığını doğrula:

```bash
tasklist //FI "IMAGENAME eq chrome.exe" | head -5
```

**5.2 Paketle.** Önerilen B şıkkı (6 kat küçük); A şıkkı her şeyi alan garanti yolu:

```bash
# A) tam kopya (~340 MB)
cd /c/TRM_WhatsApp_Session_Clean
tar -czf /tmp/trm_oturum.tar.gz TRM_Main

# B) yalnizca oturum ozu (~55 MB) - Chrome eksik klasorleri kendisi olusturur
cd /c/TRM_WhatsApp_Session_Clean
tar --ignore-failed-read -czf /tmp/trm_oturum.tar.gz \
    TRM_Main/TRM_BAGLI_HAT.txt "TRM_Main/Local State" \
    TRM_Main/Default/IndexedDB TRM_Main/Default/Local Storage \
    TRM_Main/Default/Session Storage TRM_Main/Default/Network \
    TRM_Main/Default/Preferences TRM_Main/Default/Cookies
```

İki şık da arşivin içinde `TRM_Main/...` yolunu korur; 5.3'teki açma bundan sonra
her iki durumda da aynıdır.

`TRM_BAGLI_HAT.txt` doğrulanmış hat kaydıdır (`905426235116`); B şıkkında mutlaka
olsun, yoksa sistem "hesap doğrulanmadı" der ve gönderimi açmaz.

`run_*` klasörlerini ve `*_artik` kalanlarını **taşıma**: hepsi bayat taze-profil
artığı. (`WHATSAPP_PROFIL_MODU=kalici` kullanıyorsan tek anlamlı klasör `TRM_Main`.)

**5.3 Sunucuya koy, sahipliği ve kilidi düzelt:**

```bash
scp /tmp/trm_oturum.tar.gz "$KULLANICI@$VPS_IP:/tmp/"

sudo mkdir -p /var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean
cd /var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean
sudo tar -xzf /tmp/trm_oturum.tar.gz
# B seckildi ise eksik klasorleri Chrome kendisi olusturur; A ise her sey hazirdir.
sudo rm -f TRM_Main/SingletonLock TRM_Main/SingletonSocket TRM_Main/SingletonCookie \
           TRM_Main/DevToolsActivePort
sudo chown -R trm:trm /var/lib/trm-derya/whatsapp
sudo chmod -R 700 /var/lib/trm-derya/whatsapp
```

`api_server_2.py` bu `Singleton*` dosyalarını açılışta zaten kendisi siliyor; `rm -f`
yalnızca "Chrome hâlâ açık kaldı" sürprizine karşı sigortadır.

**5.4 Bilinmesi gereken iki teknik gerçek:**

- **IndexedDB taşınabilir, çerezler taşınmaz.** Windows'ta Chrome çerezlerini DPAPI ile
  (makine+ kullanıcı bağlantılı) şifreler; Linux bu anahtarı okuyamaz ve o çerezleri
  düşürür. WhatsApp Web'in oturum anahtarları `Default/IndexedDB/…wa.db…` içinde düz
  leveldb olarak yaşadığı için **oturum devam eder**; yalnızca yeniden giriş gerekirse
  QR'a düşer (bkz. 9).
- **Windows DPAPI kasası (`core/dpapi_vault.py`) Linux'ta çalışmaz ve taşınmaz.** Bu
  bilinçli: `os.name != "nt"` iken kasa `DpapiVaultError` verir. Kod değişikliği
  gerektirmez çünkü `api_server_2.py` kasayı okumuyor — anahtarlar bölüm 7'deki gibi
  ortam değişkeni olarak verilir.

---

## 6. systemd — ilk açılış ve 7/24

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now trm-derya.service      # enable = her reboot'ta otomatik
sudo journalctl -u trm-derya -f                    # ilk acilista bunu izleyin
```

Açılış sırası beklenen loglar (`_log` satırları): `Kalıntı süreç/lock temizliği` →
`Profil dizini (kalici): /var/lib/.../TRM_Main` → oturum muayenesi → `giris_yapildi`.

**Reboot testini yapmadan "7/24 çalışıyor" deme:**

```bash
sudo systemctl reboot
# sonrasi:
ssh "$KULLANICI@$VPS_IP" 'systemctl is-enabled trm-derya; curl -s http://127.0.0.1:5000/api/saglik'
```

`network-online.target` bazı minimal VPS imajlarında etkin değildir; bu durumda birim
ağ gelmeden önce başlar ve WhatsApp Web `ERR_INTERNET_DISCONNECTED` verir (sonra
`Restart=always` ile tekrar dener). Kalıcı çözüm:

```bash
systemctl is-enabled systemd-networkd-wait-online || \
systemctl is-enabled NetworkManager-wait-online
# ikisi de yoksa (Debian/Ubuntu cloud image):
sudo systemctl enable --now systemd-networkd-wait-online.service
```

Günlükler için boyut sınırı (7/24 sunucuda dolan log servisi durdurmaz ama izi
kaybettirir): `/etc/systemd/journald.conf.d/trm.conf` içine `SystemMaxUse=200M`.

---

## 7. Ortam değişkenleri ve güvenlik

`api_server_2.py` **`.env` dosyası okumaz**, yalnızca `os.environ`'a bakar. Tek doğru
besleme noktası `/etc/trm-derya.env` (systemd `EnvironmentFile`):

```bash
sudo nano /etc/trm-derya.env
sudo chmod 640 /etc/trm-derya.env
sudo chown root:trm /etc/trm-derya.env
sudo systemctl restart trm-derya.service
```

Şablondaki anahtar satırları **yorumlu ve boş gelir** — bilerek:
`api_server_2.py`, `derya_cevaplayici.py` ve `esnaf_sablonu.py` hiç API anahtarı
okumuyor (Derya'nın yanıtları kural tabanlı), yani bu servis anahtarsız da çalışır.
Anahtarlar yalnızca aynı VPS'e taşıyacağın diğer ekosistem modülleri (llm_client,
orchestrator, ajanlar) için gerekir; onları da repo'dan veya kopyayla taşımıyoruz —
Windows'taki DPAPI kasasının Linux'ta karşılığı yoktur, anahtarları sunucuda elle
`KEY=deger` olarak sen yazarsın.

Zorunlu görünecek satırlar:

```ini
WHATSAPP_PROFIL_DIZINI=/var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean
WHATSAPP_PROFIL_MODU=kalici
WHATSAPP_BEKLENEN_TEL=905426235116
HEADLESS_MODE=true
```

Sunucuda `kalici` mod zorunlu: `taze` modu her açılışta boş profil demektir, yani
ekransız makinede sürekli QR bekleyen bir servis. Otonom motor ayrı bir süreç değildir
— `api_server_2.py` içinde thread olarak doğar, bu yüzden burada onun için bir bayrak
yok.

**Port 5000 internete açık değil.** `app.run(host="0.0.0.0", port=5000)` bu API
`/api/mesaj_gonder` gibi WhatsApp gönderim uçlarını kimlik doğrulamasız açar. VPS'te:

```bash
sudo ufw allow OpenSSH
sudo ufw deny  5000
sudo ufw enable
# panoya erisim yalnizca kendi IP'nden:
OFIS_IP="1.2.3.4"            # kendi sabit IP'n
sudo ufw allow from "$OFIS_IP" to any port 5000 proto tcp
# ya da hic port acmadan tunel:
ssh -L 5000:127.0.0.1:5000 "$KULLANICI@$VPS_IP"
```

---

## 8. Kabul testleri (sırayla, hepsi geçmeden cutover yok)

```bash
# 1) servis ayakta ve otomatik baslatma acik
systemctl is-active trm-derya && systemctl is-enabled trm-derya

# 2) saglik + giris yapilmis hesap
curl -s http://127.0.0.1:5000/api/saglik
#    -> {"port":5000,"servis":"TRM Derya API","whatsapp":"giris_yapildi"}

# 3) hat eslesmesi (eslesme=true olmadan hicbir gonderim yapilmaz)
curl -s http://127.0.0.1:5000/api/whatsapp_durum

# 4) veritabani okunabiliyor, sahiplik dogru
sudo -u trm /opt/trm/derya/venv/bin/python -c "import sqlite3;c=sqlite3.connect('/opt/trm/derya/trm_veritabani.db');print(c.execute('select count(*) from esnaflar').fetchone()[0])"
```

Gönderim denemesi **gerçek esnafa mesaj atmadan** yapılmalı: hedef olarak kendi hattının
"(Siz)" sohbeti kullanılır (`/api/mesaj_gonder`), teslim onayı `mesajlar` tablosuna
düşüldüğü doğrulanır. Kapıyı geçmeyen bir deneme "başarısız" sayılır, eşikleri
gevşetme (metin kilidi / hat filtresi) tartışmaya kapalı.

---

## 9. Sorun giderme

| Belirti | Sebep | Çözüm |
|---|---|---|
| `profile is in use` / Chrome açılmıyor | önceki süreç `SingletonLock` bıraktı | servis yeniden başlat (temizlik kendisi yapar); olmazsa `sudo rm -f …/TRM_Main/Singleton*` |
| `SessionNotCreatedException: session not created … version` | chromedriver ≠ Chrome major | `sudo bash deploy_vps.sh` 3. adım yeniden indirir; `chromedriver --version` ile `google-chrome-stable --version` büyük sürümünü karşılaştır |
| `Chrome 126 ile eslesmiyor` uyarısı kalıcı | apt'den gelen `chromedriver` (`/usr/bin`) gölgede kalıyor | `deploy_vps.sh` `/usr/local/bin`'e kurar (PATH'te önce gelir); `which -a chromedriver` ile doğrula |
| WhatsApp Web "QR bekleniyor" | oturum IndexedDB'i okunamadı / çerezler düştü | bölüm 5 tekrar; oturum zorla taze ise aşağıdaki QR yollarından biri |
| headless'de composer bulunamıyor (mesaj kutusu `null`) | WhatsApp arayüzü güncellendi ya da `--headless=new` render'ı | `HEADLESS_MODE=false` + `xvfb-run -a` ile geçici doğrulama; sonra birimdeki `Environment=` ile kalıcı `xvfb-run` dene |
| `ModuleNotFoundError: selenium` | venv'in içine kurulmadı, sistem python kullanıldı | `/opt/trm/derya/venv/bin/pip install -r requirements_vps.txt`; birim `ExecStart` venv python'u göstermeli |
| Servis `exit-code` ile sürekli restart | DB/izin ya da `WHATSAPP_PROFIL_MODU=taze` kalanı | `journalctl -u trm-derya -n80 --no-pager`; Windows'taki gibi `taze` profil sunucuda QR'sız çalışamaz, `kalici` olmalı |
| Logda Türkçe bozuluyor | lokale göre `PYTHONIOENCODING` | `_konsol_hazirla()` UTF-8'e zorlar; yine bozuksa `Environment=LANG=C.UTF-8` satırının birimde durduğunu doğrula |

**Ekransız sunucuda QR gerekiyorsa** üç yol, kolaydan zora:
1. Windows'ta QR'ı tekrar okutup oturumu **yeniden** bölüm 5 ile taşı (önerilen).
2. CDP portunu tünelleyip canlı bak: `WHATSAPP_CDP_PORT=9222`,
   `ssh -L 9222:127.0.0.1:9222 user@vps` → masaüstü Chrome'da `chrome://inspect` ile
   "Discover network targets"e `localhost:9222` ekle, headless sekmeyi aç, QR canvas'ını
   gör ve telefonda okut.
3. Geçici olarak pencere taklidi: `sudo xvfb-run -a -s "-screen 0 1280x900x24"` ile
   servisi durdurup elle başlat, `whatsapp_hata_kayitlari/*.png` ekran görüntüsünü
   scp ile al, QR'ı okut.

---

## 10. Geri dönüş

Windows kurulumu (`baslat_trm.bat`, `C:\TRM_WhatsApp_Session_Clean`) silinmez ve tek
geri dönüş noktasıdır. VPS kötü giderse:

```bash
sudo systemctl disable --now trm-derya.service
```

sonra Windows'ta `baslat_trm.bat` ile geri başlat. VPS'i tamamen kapatmadan önce
Windows'a döndürülecek tek şey oturum klasörü ve DB: sunucudan al, aynı yola koy
(`Singleton*` silmeyi unutma), `TRM_BAGLI_HAT.txt` içeriğinin `905426235116` olduğunu
doğrula.
