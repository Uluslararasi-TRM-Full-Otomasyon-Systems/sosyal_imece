# -*- coding: utf-8 -*-
"""
TRM Eko Sistem - Derya Asistan API Servisi (api_server_2.py)

Selenium tabanlı WhatsApp Web otomasyonu, her başlatmada TAZE bir profil
kullanır, eski hesap oturumunu otomatik tespit edip atar ve yalnızca
05426235116 ticari hattıyla mesaj gönderir.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException,
    JavascriptException,
    TimeoutException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from threading import RLock, Thread, Lock
from datetime import datetime, timedelta

import atexit
import json
import os
import random
import re
import shutil
import signal
import socket
import sqlite3
import string
import subprocess
import sys
import time
import unicodedata

from aday_havuzu import AdayYapisi, aday_tarama_dongusu, havuz_durumu
from derya_cevaplayici import derya_otonom_yanitla
from esnaf_sablonu import SablonHatasi, esnaf_tanitim_metni
from otonom_motor import (
    Motor,
    Yapilandirma,
    gelen_mesaj_kaydet,
    imza as _mesaj_imzasi,
    kara_listede_mi,
    sema_goc_uygula,
    telefon_kanonik,
    mobil_numara,
    izin_ver as _motor_izin_ver,
)


def _konsol_hazirla():
    """
    Windows konsolu varsayılan olarak cp1254 kod sayfasını kullanır; emoji içeren
    print() çağrıları UnicodeEncodeError fırlatıp arka plan thread'lerini SESSİZCE
    öldürür (orijinal koddaki hata buydu). Akışları UTF-8'e çeviriyoruz.
    """
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


_konsol_hazirla()

# ============================================================
# YAPILANDIRMA (hepsi ortam değişkeni ile ezilebilir)
# ============================================================
def _env_adi(anahtar, varsayilan):
    return os.environ.get(anahtar, varsayilan).strip()


def _env_sayic(anahtar, varsayilan):
    try:
        return int(_env_adi(anahtar, str(varsayilan)))
    except ValueError:
        return varsayilan


def _env_bayrak(anahtar, varsayilan="1"):
    return _env_adi(anahtar, varsayilan).lower() in ("1", "true", "evet", "open", "on")


# Beklenen ticari hat. WhatsApp Web "last-wid" değeri 905426235116... biçimindedir.
TICARI_HAT_ULUSLARARASI = _env_adi("WHATSAPP_BEKLENEN_TEL", "905426235116")

# "kalici": tek sabit profil (TRM_Main) -> QR BİR KEZ okutulur, sonra oturum kalır.
#           Profil yanlış hesabı açarsa otomatik silinir (güvenilir kaynaklardan).
# "taze"  : her açılışta benzersiz/boş profil -> QR kodu her seferinde ZORUNLU.
PROFIL_MODU = _env_adi("WHATSAPP_PROFIL_MODU", "kalici")

PROFIL_ANA_DIZIN = _env_adi("WHATSAPP_PROFIL_DIZINI", r"C:\TRM_WhatsApp_Session_Clean")
# api_server_2.py'nin eski sürümünün kullandığı kirli profil (tespit/temizlik için).
ESKI_PROFIL_DIZIN = _env_adi("WHATSAPP_ESKI_PROFIL_DIZINI", r"C:\TRM_WhatsApp_Session")

CDP_PORT_TABANI = _env_sayic("WHATSAPP_CDP_PORT", 9222)
# NOT: taze profil zaten boş olduğu için QR zorunlu. Gizli mod WhatsApp Web'in
# IndexedDB oturum kaydını bozabildiğinden VARSAYILAN KAPALI.
INCOGNITO = _env_bayrak("WHATSAPP_INCOGNITO", "0")
# Linux VPS'te fiziksel ekran yoktur: HEADLESS_MODE=true Chrome'u gizli başlatır.
# Windows'ta varsayılan KAPALI kalmalı; aksi halde QR okutma penceresi görünmez olur.
HEADLESS_MODE = _env_bayrak("HEADLESS_MODE", "0")
# Sunucuda paketle kurulmuş ikili/sürücü yolu sabitlenebilir (boş = otomatik bul).
CHROME_IKILI = _env_adi("CHROME_BINARY", "")
CHROMEDRIVER_YOLU = _env_adi("CHROMEDRIVER_PATH", "")
OTOMATIK_BASLAT = _env_bayrak("WHATSAPP_OTOMATIK_BASLAT", "1")
# 0 = SADECE bizim profilimizi kullanan Chrome'ları öldür (güvenli, varsayılan)
# 1 = tüm chrome.exe süreçlerini öldür (AÇIK UYARI: diğer açık sekmeler kapanır)
SERT_MODEMLEME = _env_bayrak("WHATSAPP_SERT_MODEMLEME", "0")
# QR bekleme artık ZAMAN AŞIMASINA bağlı değil: gözetmen thread'i sürücü açık
# kaldığı sürece taramayı yoklar. QR_BEKLEME_SN yalnızca uyarı eşiğidir.
QR_BEKLEME_SN = _env_sayic("WHATSAPP_QR_BEKLEME_SN", 180)
QR_YOKLAMA_SN = _env_sayic("WHATSAPP_QR_YOKLAMA_SN", 5)
SAYFA_BEKLEME_SN = _env_sayic("WHATSAPP_SAYFA_BEKLEME_SN", 45)
# /send?phone= bağlantısı tüm uygulamayı yeniden yükler: sohbet ekranı için eşik.
SOHBET_BEKLEME_SN = _env_sayic("WHATSAPP_SOHBET_BEKLEME_SN", 60)
RUN_DIZIN_OMUR_GUN = _env_sayic("WHATSAPP_PROFIL_OMUR_GUN", 3)
# Oturum doğrulanmadan Chrome penceresi kapanırsa taze QR penceresini otomatik
# yeniden açar (0 = kapalı). Doğrulanmış oturumda ise pencere kapanırsa kalici
# profil sayesinde QR'sız geri açılır.
PENCERE_YENIDEN_AZAMAL = _env_sayic("WHATSAPP_PENCERE_YENIDEN_ACMA", 3)
# Oturum doğrulanmadan (eslesme=False) bu hat dışındaki numaralara gönderimi engelle.
KATIHAT_FILTRESI = _env_bayrak("WHATSAPP_KATI_HAT_FILTRESI", "1")

HATA_EKRANI_DIZINI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "whatsapp_hata_kayitlari"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trm_veritabani.db")

app = Flask(__name__)
CORS(app)


def veritabani_baglan():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# OTURUM DURUMU
# ============================================================
whatsapp_driver = None
whatsapp_state = {
    "durum": "bekleniyor",   # bekleniyor|baslatiliyor|hazir_qr|giris_yapildi|yanlis_hesap|hata|kapali
    "profil_dizini": "",
    "cdp_port": CDP_PORT_TABANI,
    "giris_hat": "",         # WhatsApp'ta GİRİŞ YAPAN numara (kaynakla birlikte doğrulanır)
    "beklenen_hat": TICARI_HAT_ULUSLARARASI,
    "eslesme": False,        # açılan hesap == ticari hat mı -> gönderim bu bayrağa bağlı
    "son_mesaj": "",
    "baslangic_zamani": "",
    "kimlik_kaynagi": "",    # indexeddb-wameta | localstorage | kullanici-onayı
    "sebep": "",             # eslesme=False ise neden
    "giris_sinyali": False,  # DOM/localStorage "oturum açık" işareti
    "tarama_zamani": "",
    "gozetmen_calisiyor": False,
}
driver_lock = Lock()
state_lock = Lock()
# Tek Selenium sürücüsü paylaşılır: HTTP ile tetiklenen gönderim ve arka plan
# otonom döngüsü AYNI anda WhatsApp Web'i kullanamaz. RLock çünkü gönderim
# zincemesi iç içe geçebilir (motor -> tanitim -> gercek_gonderim).
SOHBET_KILIDI = RLock()


def _log(mesaj):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [WHATSAPP] {mesaj}", flush=True)


def _konsol_metni(metin, girinti="    │ "):
    satirlar = str(metin).splitlines() or ["(boş)"]
    return "\n".join(girinti + satir for satir in satirlar)


def _guvenli_sayic_uret(uzunluk=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=uzunluk))


# ============================================================
# 1) ARKA PLANDAKİ KALINTI SÜREÇ/LOCK TEMİZLİĞİ
# ============================================================
def _komut_calistir(komut, zaman_asimi=25):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        return subprocess.run(
            komut,
            shell=isinstance(komut, str),
            capture_output=True,
            text=True,
            timeout=zaman_asimi,
            creationflags=flags,
        )
    except Exception:
        return None


def _profil_yol_parcalari():
    parcalar = [os.path.abspath(PROFIL_ANA_DIZIN), os.path.abspath(ESKI_PROFIL_DIZIN)]
    return [p for p in parcalar if p and len(p) > 6]


def _linux_hedef_surecleri_olldur():
    """POSIX'ta aynı hedefli temizlik: yalnızca bizim profilini kullanan Chrome.

    pgrep profil yolunu komut satırında aradığı için kullanıcının/other
    servislerin Chrome pencereleri listeye girmez. taskkill Windows'a özgü.
    """
    oldlen = 0
    for alt_dizi in _profil_yol_parcalari():
        if "TRM_WhatsApp" not in alt_dizi:
            _log(f"Güvenlik: '{alt_dizi}' beklenen TRM_WhatsApp deseniyle uyuşmuyor, atlandı.")
            continue
        sonuc = _komut_calistir(["pgrep", "-f", "--", alt_dizi])
        if not sonuc or not sonuc.stdout.strip():
            continue
        for pid in sonuc.stdout.split():
            if pid.isdigit() and int(pid) != os.getpid():
                _komut_calistir(["kill", pid])
                oldlen += 1
                _log(f"Kalıntı Chrome süreci sonlandırıldı (PID {pid}) profil={alt_dizi}")
    return oldlen


def _hedef_surezleri_olddur():
    """
    Yalnızca command line'ında BİZİM profil dizini geçen chrome.exe süreçlerini
    öldürür. Kullanıcının kendi açtığı Chrome pencerelerine dokunmaz.
    """
    if os.name != "nt":
        return _linux_hedef_surecleri_olldur()

    oldlen = 0
    for alt_dizi in _profil_yol_parcalari():
        # Filtrenin yanlışlıkla TÜM Chrome'ları yakalamaması için zorunlu guard.
        if "TRM_WhatsApp" not in alt_dizi:
            _log(f"Güvenlik: '{alt_dizi}' beklenen TRM_WhatsApp deseniyle uyuşmuyor, atlandı.")
            continue
        desen = f"*{alt_dizi}*"
        powershell = (
            "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
            "Where-Object { $_.CommandLine -like '" + desen + "' } | "
            "Select-Object -ExpandProperty ProcessId"
        )
        sonuc = _komut_calistir(["powershell", "-NoProfile", "-Command", powershell])
        if not sonuc or not sonuc.stdout.strip():
            continue
        for pid in sonuc.stdout.split():
            pid = pid.strip()
            if pid.isdigit():
                _komut_calistir(["taskkill", "/F", "/T", "/PID", pid])
                oldlen += 1
                _log(f"Kalıntı Chrome süreci sonlandırıldı (PID {pid}) profil={alt_dizi}")
    return oldlen


def _eski_profili_kilitla():
    """
    Eski sürümün kullandığı C:\\TRM_WhatsApp_Session klasörü yanlış hesabın
    önbelleğini taşır. Silmiyoruz (geri alınabilir), adını değiştirip erişilemez
    yapıyoruz: hiçbir Chrome artık bu oturumu geri getiremez.
    """
    if not os.path.isdir(ESKI_PROFIL_DIZIN):
        return False
    yedek = ESKI_PROFIL_DIZIN.rstrip("\\/") + "_ESKI_ARTIK_KULLANILMIYOR"
    if os.path.exists(yedek):
        yedek = f"{yedek}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        os.rename(ESKI_PROFIL_DIZIN, yedek)
        _log(f"Eski kirli profil erişilemez adı alındı: {ESKI_PROFIL_DIZIN} -> {yedek}")
        return True
    except OSError as hata:
        _log(f"Eski profil yeniden adlandırılamadı (muhtemelen hâlâ açık): {hata}")
        return False


def kalinti_temizle():
    """chromedriver + bizim profiline kilitlenmiş chrome + profil lock dosyaları."""
    _log("Kalıntı süreç/lock temizliği başlıyor "
         f"(sert mod={'ACIK' if SERT_MODEMLEME else 'KAPALI'})...")

    if os.name == "nt":
        _komut_calistir(["taskkill", "/F", "/IM", "chromedriver.exe"])
    else:
        # Yalnızca BU kullanıcının sürücüleri: sunucuda başka bir uygulamanın
        # chromedriver'ına dokunulmaz.
        _komut_calistir(["pkill", "-u", str(os.getuid()), "-x", "chromedriver"])

    if SERT_MODEMLEME:
        if os.name == "nt":
            # KULLANICI BİLEREK AÇTI: tüm Chrome'lar kapanır.
            _komut_calistir(["taskkill", "/F", "/IM", "chrome.exe"])
            _log("SERT MOD: tüm chrome.exe süreçleri sonlandırıldı.")
        else:
            _log("SERT MOD Linux'ta uygulanmıyor: toplu chrome öldürme yapılmadı.")
    else:
        sayi = _hedef_surezleri_olddur()
        _log(f"Hedefli temizlik: {sayi} kalıntı Chrome süreci sonlandırıldı "
             "(kişisel pencerelere dokunulmadı).")

    time.sleep(1.0)

    # Profil kilidi / DevToolsArtı port dosyaları: Chrome bunları bırakır ve
    # aynı dizini tekrar açmayı reddeder ("profile is in use").
    for dizin in _profil_yol_parcalari():
        if not os.path.isdir(dizin):
            continue
        for dosya_adi in (
            "SingletonLock", "SingletonSocket", "SingletonCookie",
            "DevToolsActivePort", "lockfile",
        ):
            yol = os.path.join(dizin, dosya_adi)
            try:
                if os.path.exists(yol):
                    os.remove(yol)
                    _log(f"Lock dosyası silindi: {yol}")
            except OSError:
                pass

    # Süreçler kapandıysa eski kirli profili erişilemez yap.
    _eski_profili_kilitla()
    return True


def _eski_run_dizinleri_temizle():
    """PROFIL_MODU=taze ise biriken eski oturum klasörlerini periyodik sil."""
    if not os.path.isdir(PROFIL_ANA_DIZIN):
        return
    sinir = datetime.now() - timedelta(days=RUN_DIZIN_OMUR_GUN)
    for ad in sorted(os.listdir(PROFIL_ANA_DIZIN)):
        yol = os.path.join(PROFIL_ANA_DIZIN, ad)
        if not os.path.isdir(yol) or ad == "TRM_Main":
            continue
        try:
            if datetime.fromtimestamp(os.path.getmtime(yol)) < sinir:
                shutil.rmtree(yol, ignore_errors=True)
                _log(f"Bayat oturum klasörü silindi: {yol}")
        except OSError:
            pass


# ============================================================
# 2) PROFİL VE PORT YÖNETİMİ
# ============================================================
def _serbest_port_bul(taban):
    for port in range(taban, taban + 25):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as kontrol:
            kontrol.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                kontrol.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 0


def _profil_dizini_hazirla(taze=False):
    os.makedirs(PROFIL_ANA_DIZIN, exist_ok=True)
    if PROFIL_MODU == "kalici" and not taze:
        dizin = os.path.join(PROFIL_ANA_DIZIN, "TRM_Main")
        os.makedirs(dizin, exist_ok=True)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dizin = os.path.join(PROFIL_ANA_DIZIN, f"run_{stamp}_{_guvenli_sayic_uret()}")
        os.makedirs(dizin, exist_ok=True)
    _log(f"Profil dizini ({'taze-zorla' if taze else PROFIL_MODU}): {dizin}")
    return dizin


def _chrome_secenekleri(profil_dizini, cdp_port):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={profil_dizini}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    if cdp_port:
        options.add_argument(f"--remote-debugging-port={cdp_port}")
    if INCOGNITO:
        options.add_argument("--incognito")
    if HEADLESS_MODE:
        # "--headless=new" gerçek Chrome render katmanını kullanır; eski gizli mod
        # WhatsApp Web'in composer'ını ve IndexedDB oturum kaydını kırabiliyordu.
        # Ekransız sunucuda pencere boyutu --window-size ile zaten sabitleniyor.
        options.add_argument("--headless=new")
        options.add_argument("--hide-scrollbars")
    if CHROME_IKILI:
        options.binary_location = CHROME_IKILI

    # Otomatik sürücü izlerini ve oturum/önbellek artıklarını azaltan parametreler:
    for ek in (
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-sync",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-popup-blocking",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--disable-features=Translate,MediaRouter",
        "--window-size=1280,900",
    ):
        options.add_argument(ek)

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # WhatsApp Web websocket/uzun-polling yüzünden "load" olayını hiç
    # tamamlamıyor: normal stratejide driver.get() sayfa bitene kadar
    # bekliyor ve gönderim thread'i saatlerce kilitlenebiliyor.
    options.page_load_strategy = "eager"
    # Beklenmedik yerel diyalog ("Bu sayfadan ayrılansın?") tüm WebDriver
    # komutlarını susturmasın; otomatik kapatılır.
    options.set_capability("unhandledPromptBehavior", "dismiss")
    return options


def _surucu_olustur(options):
    """Sabit sürücü yolu -> Selenium Manager (4.6+) -> webdriver_manager yedeği."""
    from selenium.webdriver.chrome.service import Service as ChromeService

    if CHROMEDRIVER_YOLU:
        return webdriver.Chrome(
            service=ChromeService(executable_path=CHROMEDRIVER_YOLU), options=options
        )
    try:
        return webdriver.Chrome(options=options)
    except Exception as ilk_hata:
        _log(f"Selenium Manager sürücüyü çözemedi ({ilk_hata}); webdriver_manager deneniyor...")
        from webdriver_manager.chrome import ChromeDriverManager

        return webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )


# ============================================================
# 3) OTURUM MUAYENESİ (çok kaynaklı kimlik okuma)
# ------------------------------------------------------------
# ÖNEMLİ: localStorage['last-wid'] KENDİ numaran değil, SON AÇILAN SOHBETİN
# numarasıdır. Eski kod bunu "giriş yapan hat" sanıp 905426235116 ile
# karşılaştırdığı için her taramada "yanlış hesap" diyip profili siliyordu.
# Kendi hattı yalnızca IndexedDB (wa.db/wameta/user) ve kimlik anahtarlarından okunur.
# ============================================================
WAMETA_OKUMA_JS = """
var cb = arguments[arguments.length - 1];
var out = {hata: null, veritabanlari: [], storelar: [], kullanici: null, kayitlar: []};
function bitir(){ try { cb(out); } catch(e) {} }
try {
  var p = indexedDB.databases ? indexedDB.databases() : Promise.resolve([]);
  p.then(function(liste){
    liste = liste || [];
    out.veritabanlari = liste.map(function(d){ return d.name + ':' + d.version; });
    var wa = liste.filter(function(d){ return d.name === 'wa.db'; })[0];
    if (!wa) { out.hata = 'wa.db-yok'; return bitir(); }
    var req = indexedDB.open(wa.name, wa.version);
    req.onerror = function(){ out.hata = 'acilamadi'; bitir(); };
    req.onsuccess = function(){
      var db = req.result;
      try {
        var stores = Array.prototype.slice.call(db.objectStoreNames || []);
        out.storelar = stores;
        if (stores.indexOf('wameta') === -1) { out.hata = 'wameta-yok'; db.close(); return bitir(); }
        var tx = db.transaction(['wameta'], 'readonly');
        var store = tx.objectStore('wameta');
        var g = store.get('user');
        g.onsuccess = function(){
          out.kullanici = g.result ? JSON.stringify(g.result).slice(0, 3000) : null;
          var ga = store.getAll();
          var gk = store.getAllKeys();
          var beklenen = 0;
          function tamamla(){
            beklenen++;
            if (beklenen < 2) return;
            out.kayitlar = (gk.result || []).map(function(k, i){
              var v = (ga.result || [])[i];
              var s;
              try { s = JSON.stringify(v); } catch (e) { s = String(v); }
              return String(k) + ' => ' + String(s).slice(0, 260);
            }).slice(0, 40);
            db.close(); bitir();
          }
          ga.onsuccess = tamamla; ga.onerror = tamamla;
          gk.onsuccess = tamamla; gk.onerror = tamamla;
        };
        g.onerror = function(){ out.hata = 'kayit-okunamadi'; db.close(); bitir(); };
      } catch (e) { out.hata = String(e); try { db.close(); } catch (x) {} bitir(); }
    };
  }).catch(function(e){ out.hata = String(e); bitir(); });
} catch (e) { out.hata = String(e); bitir(); }
"""

#last-wid SOHBET kimliğidir; aşağıdaki anahtarlar HESAP kimliği taşır.
KIMLIK_ANAHTARLARI = (
    "registration-data", "me", "my-wid", "wid", "user-lid", "me-lid",
    "device-label", "myDeviceUserJid", "cache-user-jid",
)


def _last_wid_okü(sürücü):
    """SON AÇILAN SOHBETin JID'i. Yalnızca 'oturum açık' işareti olarak kullanılır."""
    try:
        return sürücü.execute_script("return localStorage.getItem('last-wid');")
    except (WebDriverException, JavascriptException):
        return None


def _localstorage_dump(sürücü):
    """
    dict -> okunabildi (boş dict = depolama gerçekten boş).
    None  -> sayfa/sürücü şu an okumaya elverişli DEĞİL (yeniden yükleme).
    """
    js = (
        "var o = {}; try {"
        "for (var i = 0; i < localStorage.length; i++) {"
        "  var k = localStorage.key(i);"
        "  o[k] = String(localStorage.getItem(k)).slice(0, 200);"
        "}"
        "} catch (e) { o['__hata'] = String(e); } return o;"
    )
    try:
        veri = sürücü.execute_script(js)
    except (WebDriverException, JavascriptException):
        return None
    if not isinstance(veri, dict) or "__hata" in veri:
        return None
    return veri


def _wameta_kullanicisi(sürücü):
    try:
        sürücü.set_script_timeout(12)
        return sürücü.execute_async_script(WAMETA_OKUMA_JS) or {}
    except (WebDriverException, JavascriptException):
        return {}


def _numara_adaylari(metin):
    """Metin içinden 9XXXXXXXXXXX (12 haneli TR) gibi numara adaylarını çıkarır."""
    if not metin:
        return []
    rakamlar = re.findall(r"\d{10,16}", str(metin))
    return [r for r in rakamlar if r]


def _numara_karsilastir(wid, beklenen):
    """'905426235116:08@s.whatsapp.net' == beklenen '905426235116' -> True"""
    if not wid:
        return False
    rakamlar = "".join(c for c in str(wid) if c.isdigit())
    hedef = "".join(c for c in str(beklenen) if c.isdigit())
    if not rakamlar or not hedef:
        return False
    return rakamlar.startswith(hedef) or hedef in rakamlar


def _esnaf_listesinde_mi(numara):
    """
    last-wid = SON AÇILAN SOHBET. Eğer beklenen hat listedeki bir esnafa aitse,
    last-wid'in o numara olması "kendi hattım" kanıtı SAYILMAZ.
    """
    js = (
        "var k = document.querySelector(\"div[contenteditable='true'][aria-label*='sohbetine']\")"
        " || document.querySelector(\"div[contenteditable='true'][data-tab='1']\")"
        " || document.querySelector(\"div[contenteditable='true']\");"
        "return k;"
    )
    try:
        conn = veritabani_baglan()
        rows = conn.execute("SELECT telefon FROM esnaflar").fetchall()
        conn.close()
    except sqlite3.Error:
        return False
    hedef = "".join(c for c in str(numara) if c.isdigit())
    for r in rows:
        t = "".join(c for c in str(r["telefon"] or "") if c.isdigit())
        if t and t == hedef:
            return True
    return False


HAT_KAYDI_DOSYASI = "TRM_BAGLI_HAT.txt"


def _hat_kaydi_yaz(hat):
    """Doğrulanmış hattı İLGİLİ profil klasörüne yazar: kalici modda bir daha
    QR okutmadan hat_eslesmesi=true diye devam edilir. Profil silinirse kayıt da
    silinir, böylece başka hesaba taşınmaz."""
    dizin = whatsapp_state.get("profil_dizini") or ""
    if not dizin or not os.path.isdir(dizin) or not hat:
        return False
    try:
        with open(os.path.join(dizin, HAT_KAYDI_DOSYASI), "w", encoding="utf-8") as fh:
            fh.write(f"{hat}\n{datetime.now().isoformat()}\n")
        _log(f"Bağlı hat kaydı yazıldı: {hat}")
        return True
    except OSError as hata:
        _log(f"Hat kaydı yazılamadı: {hata}")
        return False


def _hat_kaydi_oku():
    dizin = whatsapp_state.get("profil_dizini") or ""
    if not dizin:
        return ""
    yol = os.path.join(dizin, HAT_KAYDI_DOSYASI)
    if not os.path.isfile(yol):
        return ""
    try:
        with open(yol, encoding="utf-8") as fh:
            return "".join(c for c in fh.readline() if c.isdigit())
    except OSError:
        return ""


def _kendi_hat_belirle(sürücü):
    """
    returns (hat, kaynak, guvenilir)
      guvenilir=True  -> bu kaynak HESAP kimliği taşır; yanlış hat tespitinde
                         profili silebiliriz.
      guvenilir=False -> yalnızca ipucu, asla profil silme sebebi değildir.
    """
    wameta = _wameta_kullanicisi(sürücü)
    kullanici = wameta.get("kullanici")
    if kullanici:
        # me.wid._serialized = "905426235116:08@s.whatsapp.net"
        hedefli = [a for a in _numara_adaylari(kullanici) if len(a) >= 12]
        if hedefli:
            return hedefli[0], "indexeddb-wameta", True

    ls = _localstorage_dump(sürücü)
    if ls is None:
        ls = {}
    for anahtar in KIMLIK_ANAHTARLARI:
        if anahtar in ls and ls[anahtar]:
            adaylar = [a for a in _numara_adaylari(ls[anahtar]) if len(a) >= 12]
            if adaylar:
                return adaylar[0], f"localstorage:{anahtar}", True

    # last-wid / last-wid-md SOHBET kimliğidir: yalnızca beklenen hatla ayniysa
    # ve o hat esnaf listesinde değilse "kendi hattım" için güçlü pozitif sayılır.
    # Asla tek başına "yanlış hesap" kararında kullanılmaz.
    for anahtar in ("last-wid", "last-wid-md", "last-wid-sha1-md", "last-wid-sha1"):
        deger = ls.get(anahtar)
        if deger and _numara_karsilastir(deger, TICARI_HAT_ULUSLARARASI):
            if not _esnaf_listesinde_mi(TICARI_HAT_ULUSLARARASI):
                return TICARI_HAT_ULUSLARARASI, f"localstorage:{anahtar}(sohbet==kendi)", True

    # Son güvenilir kaynak: daha önce bu profil klasörüne doğrulanmış olarak
    # yazılmış hat kaydı. Silinmiş/başka bir profile taşınmaz.
    kayit = _hat_kaydi_oku()
    if kayit and _numara_karsilastir(kayit, TICARI_HAT_ULUSLARARASI):
        return TICARI_HAT_ULUSLARARASI, "profil-hat-kaydi", True
    return "", "", False


_OKUNAMADI = object()


def _giris_sinyali_var_mi(sürücü, ls=_OKUNAMADI):
    """QR ekranı DEĞİLSE ve sohbet arayüzü/kimlik anahtarları varsa -> oturum açık."""
    if ls is _OKUNAMADI:
        ls = _localstorage_dump(sürücü)
    if ls is None:
        ls = {}
    for anahtar in ("pusk", "pid-key", "registration-data", "last-wid",
                    "last-wid-md", "my-wid", "WABrowserMetadata", "app_version"):
        if ls.get(anahtar):
            return True
    for secici in (
        "#side",
        "#pane-side",
        "div[contenteditable='true'][data-tab='1']",
        "span[data-icon='chats']",
        "span[data-icon='settings']",
    ):
        try:
            if sürücü.find_elements(By.CSS_SELECTOR, secici):
                return True
        except WebDriverException:
            return False
    return False


def _qr_bekliyor_mu(sürücü):
    for secici in (
        "div[data-tab='qrcode']",
        "div[data-ref]",
        "section[class*='scan-fade-in']",
        "canvas",
    ):
        try:
            if sürücü.find_elements(By.CSS_SELECTOR, secici):
                return True
        except WebDriverException:
            continue
    try:
        metin = sürücü.find_element(By.ID, "app").text or ""
    except WebDriverException:
        metin = ""
    icin = metin.lower()
    return ("qr kod" in icin) or ("link a device" in icin) or ("telefonunuzdan" in icin)


_giris_yok_ardisik = 0
GIRIS_YOK_SINIRI = _env_sayic("WHATSAPP_GIRIS_YOK_SINIRI", 3)


def _muayene_et(sürücü, kimlik_okuma=True):
    """
    Tek doğruluk kaynağı: oturum durumu + hat eşleşmesi.
    whatsapp_state'i günceller, (durum, eslesme) döner.
    kimlik_okuma=False -> pahalı IndexedDB okuması atlanır (eşleşme zaten doğrulanmış).
    """
    global _giris_yok_ardisik
    ls = _localstorage_dump(sürücü)

    if ls is None:
        # WhatsApp şu an yeniden yükleniyor: tek olumsuz okuma doğrulanmış
        # oturumu "QR bekleniyor"a düşürürse sonsuz aç/kapa döngüsü olur.
        with state_lock:
            whatsapp_state["tarama_zamani"] = datetime.now().strftime("%H:%M:%S")
            return whatsapp_state["durum"], whatsapp_state["eslesme"]

    giris = _giris_sinyali_var_mi(sürücü, ls)

    with state_lock:
        whatsapp_state["giris_sinyali"] = giris
        whatsapp_state["tarama_zamani"] = datetime.now().strftime("%H:%M:%S")

        if not giris:
            _giris_yok_ardisik += 1
            if not (_qr_bekliyor_mu(sürücü) or _giris_yok_ardisik >= GIRIS_YOK_SINIRI):
                # Ekran henüz belirsiz: önceki (doğrulanmış) durumu koru.
                return whatsapp_state["durum"], whatsapp_state["eslesme"]
            whatsapp_state["durum"] = "hazir_qr"
            whatsapp_state["eslesme"] = False
            whatsapp_state["sebep"] = "qr-bekleniyor"
            whatsapp_state["kimlik_kaynagi"] = ""
            return whatsapp_state["durum"], False

        _giris_yok_ardisik = 0

        if not kimlik_okuma:
            whatsapp_state["durum"] = "giris_yapildi"
            return whatsapp_state["durum"], whatsapp_state["eslesme"]

        hat, kaynak, guvenilir = _kendi_hat_belirle(sürücü)
        if hat:
            whatsapp_state["giris_hat"] = hat[:12]
        whatsapp_state["kimlik_kaynagi"] = kaynak

        eslesme = bool(hat and guvenilir and _numara_karsilastir(hat, TICARI_HAT_ULUSLARARASI))
        if eslesme:
            whatsapp_state["durum"] = "giris_yapildi"
            whatsapp_state["eslesme"] = True
            whatsapp_state["sebep"] = ""
            if kaynak != "profil-hat-kaydi":
                _hat_kaydi_yaz(TICARI_HAT_ULUSLARARASI)
        elif hat and guvenilir:
            whatsapp_state["durum"] = "yanlis_hesap"
            whatsapp_state["eslesme"] = False
            whatsapp_state["sebep"] = f"hat:{hat} beklenen:{TICARI_HAT_ULUSLARARASI}"
        else:
            # Oturum açık ama hesap numarası okunamadı (wa.db henüz yazılmamış olabilir)
            whatsapp_state["durum"] = "giris_yapildi"
            whatsapp_state["eslesme"] = False
            whatsapp_state["sebep"] = "numara-henuz-okunamadi"
        return whatsapp_state["durum"], whatsapp_state["eslesme"]


def _ilk_muayene(sürücü, sure=30):
    """
    Sayfa oturana kadar ilk kararın verilmesini geciktirir. WhatsApp Web açılışta
    kendini yeniden yükler; bu sırada yapılan tek okuma oturumu yanlışlıkla
    'QR bekleniyor' sanabilir.
    """
    bitis = time.time() + sure
    while True:
        durum, eslesme = _muayene_et(sürücü)
        if durum != "baslatiliyor":
            return durum, eslesme
        if time.time() >= bitis:
            _log(f"⏱ {sure} sn içinde ekran kararı verilemedi; gözetmen izlemeye devam ediyor.")
            return durum, eslesme
        time.sleep(2)


DOM_NUMARA_PROBE_JS = """
var out = {telefonMetinleri: [], testidler: [], yanPanelMetni: '', hedefDomadaMi: null};
try {
  var hedef = arguments[0];
  var noder = document.querySelectorAll('body *');
  var sayic = 0;
  var testidKume = {};
  for (var i = 0; i < noder.length && sayic < 25; i++) {
    var n = noder[i];
    if (n.children.length > 2) continue;
    var t = (n.innerText || n.textContent || '').trim();
    if (!t || t.length > 60) continue;
    var rakam = t.replace(/\\D/g, '');
    if (t.indexOf('+') === 0 && rakam.length >= 10) {
      var at = n.getAttribute('data-testid') || n.getAttribute('data-icon') || n.className || n.tagName;
      out.telefonMetinleri.push(t + '  <<  ' + String(at).slice(0, 90));
      sayic++;
    }
    var td = n.getAttribute && n.getAttribute('data-testid');
    if (td) testidKume[td] = 1;
  }
  out.testidler = Object.keys(testidKume).slice(0, 250);
  if (hedef) {
    var govdeRakam = (document.body.innerText || '').replace(/\\D/g, '');
    out.hedefDomadaMi = govdeRakam.indexOf(hedef) !== -1;
  }
  var side = document.querySelector('#side');
  out.yanPanelMetni = side ? String(side.innerText).slice(0, 300) : '';
} catch (e) { out.hata = String(e); }
return out;
"""


def _dom_numara_probe(sürücü):
    try:
        return sürücü.execute_script(DOM_NUMARA_PROBE_JS, TICARI_HAT_ULUSLARARASI) or {}
    except (WebDriverException, JavascriptException):
        return {}


def _tani_verisi(sürücü):
    """Canlı teşhis: WhatsApp Web'in gerçekte hangi anahtara ne yazdığını gösterir."""
    wameta = _wameta_kullanicisi(sürücü)
    ls = _localstorage_dump(sürücü)
    if ls is None:
        ls = {}
    numara_iceren = {k: str(v)[:160] for k, v in ls.items()
                     if re.search(r"\d{10,16}", str(v))}
    return {
        "url": getattr(sürücü, "current_url", ""),
        "baslik": getattr(sürücü, "title", ""),
        "qr_bekliyor": _qr_bekliyor_mu(sürücü),
        "giris_sinyali": _giris_sinyali_var_mi(sürücü, ls),
        "wameta": wameta,
        "kendi_hat": _kendi_hat_belirle(sürücü),
        "last_wid_sohbet": _last_wid_okü(sürücü),
        "localStorage_anahtarlari": sorted(ls.keys()),
        "localStorage_numara_icerenler": numara_iceren,
        "dom_probe": _dom_numara_probe(sürücü),
    }


def _tani_dosyaya_yaz():
    """Teşhis dökümünü diske yazar (pencere kapansa bile kanıt kalır)."""
    if not _surucu_saglam_mi():
        return None
    try:
        veri = _tani_verisi(whatsapp_driver)
    except Exception as hata:
        _log(f"Teşhis dökümü alınamadı: {hata}")
        return None
    try:
        os.makedirs(HATA_EKRANI_DIZINI, exist_ok=True)
        yol = os.path.join(
            HATA_EKRANI_DIZINI,
            f"tani_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        with open(yol, "w", encoding="utf-8") as fh:
            json.dump(veri, fh, ensure_ascii=False, indent=2)
        _log(f"Teşhis dökümü: {yol}")
        veri["dosya"] = yol
    except OSError as hata:
        _log(f"Teşhis dosyaya yazılamadı: {hata}")
    return veri


def _yanlis_hesap_temizle(profil_dizini):
    """Profil eski/yanlış hesabı açtıysa: sürücüyü kapat, dizini SİL, taze başlat."""
    global whatsapp_driver
    _log("!!! BEKLENEN TİCARİ HAT DEĞİL !!! Profil sıfırlanıyor, taze QR zorlanıyor.")
    if whatsapp_driver:
        try:
            whatsapp_driver.quit()
        except WebDriverException:
            pass
        whatsapp_driver = None
    _hedef_surezleri_olddur()
    if os.path.isdir(profil_dizini):
        shutil.rmtree(profil_dizini, ignore_errors=True)
    _log(f"Eski profil silindi: {profil_dizini}")


def _surucu_saglam_mi():
    """
    Sürücü oturumu yaşıyor mu? `title`/`current_url` sayfa yüklenirken
    istisna fırlatır ve yanlışlıkla "pencere kapandı" dedirtir; window_handles
    yalnızca WebDriver oturumuna bakar, sayfa durumundan bağımsızdır.
    """
    if whatsapp_driver is None:
        return False
    try:
        return bool(whatsapp_driver.window_handles)
    except WebDriverException:
        return False


def _hata_ekrani_al(tag="hata"):
    if not _surucu_saglam_mi():
        return None
    try:
        os.makedirs(HATA_EKRANI_DIZINI, exist_ok=True)
        yol = os.path.join(
            HATA_EKRANI_DIZINI,
            f"{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_guvenli_sayic_uret()}.png",
        )
        whatsapp_driver.save_screenshot(yol)
        _log(f"Hata ekran görüntüsü: {yol}")
        return yol
    except WebDriverException:
        return None


# ============================================================
# 4) WHATSAPP WEB BAŞLATMA (yeniden düzenlenmiş)
# ============================================================
def whatsapp_baslat(zorla=False, qr_bekle=True, taze=False):
    """
    Dışarıdan tek giriş noktası.
      • Sürücü kurma işi driver_lock İÇİNDE yapılır -> aynı anda tek Chrome, tek profil.
      • QR bekleme kilidin DIŞINDA yapılır -> panel, QR beklenirken kilitlenmez.
    """
    with driver_lock:
        _surucu_kur(zorla=zorla, taze=taze, deneme=0)

    if qr_bekle and whatsapp_state["durum"] == "hazir_qr":
        _qr_oturum_bekle(whatsapp_state["profil_dizini"])

    return whatsapp_state["durum"] in ("hazir_qr", "giris_yapildi", "baslatiliyor")


def _surucu_kur(zorla, taze, deneme):
    """driver_lock TUTULARAK çağrılır. QR beklemez, hemen döner."""
    global whatsapp_driver

    if whatsapp_driver is not None and _surucu_saglam_mi() and not zorla:
        _log("Oturum zaten aktif, yeniden başlatma atlandı.")
        return True

    kalinti_temizle()
    _eski_run_dizinleri_temizle()

    profil_dizini = _profil_dizini_hazirla(taze=taze)
    cdp_port = _serbest_port_bul(CDP_PORT_TABANI)
    if cdp_port and cdp_port != CDP_PORT_TABANI:
        _log(f"Port {CDP_PORT_TABANI} meşgul, {cdp_port} kullanılacak.")

    whatsapp_state.update(
        durum="baslatiliyor",
        profil_dizini=profil_dizini,
        cdp_port=cdp_port,
        giris_hat="",
        eslesme=False,
        son_mesaj="",
        baslangic_zamani=datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    )

    try:
        _log(f"WhatsApp Web oturumu başlatılıyor "
             f"(profil={'taze-zorla' if taze else PROFIL_MODU})...")
        try:
            whatsapp_driver = _surucu_olustur(_chrome_secenekleri(profil_dizini, cdp_port))
        except Exception as surucu_hata:
            # Profil kilidi hâlâ duruyor olabilir: dizini sil, BENZERSİZ adla tekrar dene.
            _log(f"Sürücü başlatılamadı ({surucu_hata}); tamamen yeni dizinle deneniyor...")
            whatsapp_driver = None
            kalinti_temizle()
            shutil.rmtree(profil_dizini, ignore_errors=True)
            profil_dizini = _profil_dizini_hazirla(taze=True)
            whatsapp_state["profil_dizini"] = profil_dizini
            whatsapp_driver = _surucu_olustur(
                _chrome_secenekleri(profil_dizini, _serbest_port_bul(CDP_PORT_TABANI))
            )

        whatsapp_driver.set_page_load_timeout(90)
        whatsapp_driver.implicitly_wait(0)
        whatsapp_driver.get("https://web.whatsapp.com")

        try:
            WebDriverWait(whatsapp_driver, SAYFA_BEKLEME_SN).until(
                EC.presence_of_element_located((By.ID, "app"))
            )
        except TimeoutException:
            _log("UYARI: #app beklenen sürede gelmedi (ağ yavaş olabilir).")

        # Sayfa oturana kadar bekle; ilk karar YÜKLENMEKTE olan ekrana göre verilmez.
        durum, eslesme = _ilk_muayene(whatsapp_driver)

        if durum == "yanlis_hesap":
            _yanlis_hesap_temizle(profil_dizini)
            if deneme < 1:
                _log("Beklenmeyen hesap atıldı; taze profil ile TEK yeniden deneme.")
                return _surucu_kur(zorla=True, taze=True, deneme=deneme + 1)
            _log("❌ İkinci denemede de yanlış hesap. Gönderim devre dışı.")
            return False

        if durum == "hazir_qr":
            _log("✅ TAZE QR KODU EKRANI HAZIR. Telefon: WhatsApp > Ayarlar > "
                 "Cihazları Bağla > Bir Cihazı Bağla.")
            _log(f"   (Bu pencere {QR_BEKLEME_SN} sn içinde okunmasa bile gözetmen "
                 "taramayı izlemeye devam eder; geç okutsan da otomatik bağlanır.)")
        elif durum == "baslatiliyor":
            _log("Sayfa hâlâ yükleniyor; gözetmen ilk karar verdiğinde hat "
                 "eşleşmesi otomatik doğrulanacak.")
        else:
            _log(f"✅ Oturum açık: hat={whatsapp_state['giris_hat'] or 'okunamadı'} "
                 f"eslesme={eslesme} kaynak={whatsapp_state['kimlik_kaynagi'] or '-'}")

        _oturum_gozetmeni_baslat()
        return True

    except Exception as hata:
        whatsapp_state["durum"] = "hata"
        whatsapp_state["son_mesaj"] = str(hata)
        _log(f"❌ BAĞLANTI HATASI: {hata}")
        _hata_ekrani_al("baslatma_hatasi")
        try:
            if whatsapp_driver:
                whatsapp_driver.quit()
        except WebDriverException:
            pass
        whatsapp_driver = None
        return False


def _qr_oturum_bekle(profil_dizini):
    """
    QR okutulana kadar durumu izler. Süre dolınca izlemeyi BIRAKMAZ:
    gözetmen thread'i sürücü açık kaldığı sürece taramayı yoklamaya devam eder,
    böylece geç okutulan QR'da da hat_eslesmesi otomatik true olur.
    """
    bitis = time.time() + QR_BEKLEME_SN
    while time.time() < bitis:
        if not _surucu_saglam_mi():
            with state_lock:
                whatsapp_state["durum"] = "kapali"
                whatsapp_state["sebep"] = "surucu-kapandi"
            _log("Sürücü kapandı, QR bekleme sonlandırıldı.")
            return False

        durum, eslesme = _muayene_et(whatsapp_driver)
        if eslesme:
            _log(f"✅ QR okundu, doğru ticari hat bağlandı: "
                 f"{whatsapp_state['giris_hat']} (kaynak: {whatsapp_state['kimlik_kaynagi']})")
            return True
        if durum == "yanlis_hesap":
            _log(f"❗ Beklenmeyen hat ile giriş yapıldı ({whatsapp_state['giris_hat']}). "
                 f"İzin verilen hat: {TICARI_HAT_ULUSLARARASI}")
            with driver_lock:
                _yanlis_hesap_temizle(profil_dizini)
            return False
        time.sleep(QR_YOKLAMA_SN)

    _log(f"⏱ {QR_BEKLEME_SN} sn içinde QR okutulmadı. Pencereyi KAPATMA — "
         "okuttuğun anda gözetmen hattı tanır ve köprü kendini açar.")
    return False


# ============================================================
# 4b) KALICI OTURUM GÖZETMENİ
# ============================================================
_gozetmen_imza = None
_tani_kaydedildi = False
_pencere_yeniden_acma_sayic = 0
_kapaniyor = False


def _pencere_yeniden_ac_dene(eslesme):
    """
    Chrome penceresi kapanmışsa taze oturumu geri açar.
      • Oturum doğrulanmışsa (kalici profil) QR'sız geri gelir, sayaç sıfırlanır.
      • Doğrulanmamışsa en fazla PENCERE_YENIDEN_AZAMAL kez yeni QR penceresi üretilir.
    Döner: True -> yeni gözetmen/sürücü devraldı, bu thread çıkmalı.
    """
    global _pencere_yeniden_acma_sayic, _gozetmen_imza
    if _kapaniyor or PENCERE_YENIDEN_AZAMAL <= 0:
        return False
    if not eslesme and _pencere_yeniden_acma_sayic >= PENCERE_YENIDEN_AZAMAL:
        _log(f"Chrome {PENCERE_YENIDEN_AZAMAL} kez kapanmış ama oturum hiç doğrulanmamış. "
             "Yeniden açma durduruldu; panelden 'Yeniden Başlat' ile taze QR alabilirsin.")
        return False
    _pencere_yeniden_acma_sayic += 1
    _gozetmen_imza = None
    etiket = ("doğrulanmış oturum" if eslesme else "QR okutulmamış")
    _log(f"Chrome penceresi kapandı ({etiket}) — "
         f"{_pencere_yeniden_acma_sayic}/{PENCERE_YENIDEN_AZAMAL} yeniden açılıyor...")
    time.sleep(3)
    try:
        with driver_lock:
            # Yeni sürücü kendi gözetmenini başlatır; QR/oturum taraması ona bırakılır.
            _surucu_kur(zorla=True, taze=False, deneme=0)
        return True
    except Exception as hata:
        _log(f"Pencere yeniden açılamadı: {hata}")
        return False


def _oturum_gozetmeni_baslat():
    """Her sürücü için tam olarak bir gözetmen thread'i başlatır."""
    global _gozetmen_imza, _tani_kaydedildi
    if whatsapp_driver is None:
        return
    imza = id(whatsapp_driver)
    if _gozetmen_imza == imza:
        return
    _gozetmen_imza = imza
    _tani_kaydedildi = False
    with state_lock:
        whatsapp_state["gozetmen_calisiyor"] = True
    Thread(
        target=_oturum_gozetmeni,
        args=(imza, whatsapp_state["profil_dizini"]),
        daemon=True,
    ).start()
    _log("Kalıcı oturum gözetmeni başlatıldı (QR geç okunsa da hattı tanır).")


def _oturum_gozetmeni(imza, profil_dizini):
    global _gozetmen_imza, _tani_kaydedildi
    onceki = ""
    yoklama = max(2, QR_YOKLAMA_SN)
    while True:
        try:
            if _gozetmen_imza != imza:
                # Kapanış, çıkış isteği veya yeni bir sürücü devraldı: sessizce çık.
                return

            if not _surucu_saglam_mi():
                # Tek yoklama yanıltabilir (CDP anlık takılabilir): 2 sn sonra doğrula.
                time.sleep(2)
                if _surucu_saglam_mi():
                    time.sleep(yoklama)
                    continue
                with state_lock:
                    eslesme = whatsapp_state["eslesme"]
                    whatsapp_state["gozetmen_calisiyor"] = False
                    whatsapp_state["sebep"] = "surucu-kapandi"
                if _pencere_yeniden_ac_dene(eslesme):
                    return
                with state_lock:
                    whatsapp_state["durum"] = "kapali"
                    if not eslesme:
                        whatsapp_state["eslesme"] = False
                _log("Sürücü kapandı; gözetmen duruyor.")
                return

            # Eşleşme doğrulanmışsa pahalı IndexedDB okumasını tekrarlama.
            durum, eslesme = _muayene_et(
                whatsapp_driver, kimlik_okuma=not whatsapp_state["eslesme"]
            )
            if eslesme:
                _pencere_yeniden_acma_sayic = 0

            if durum != onceki:
                onceki = durum
                _log(f"Gözetmen: durum={durum} eslesme={eslesme} "
                     f"hat={whatsapp_state['giris_hat'] or '-'} "
                     f"sebep={whatsapp_state['sebep'] or '-'}")

            # Numara okunamazsa kanıtı hemen diske bırak (pencere sonra kapanabilir).
            if durum == "giris_yapildi" and not eslesme and not _tani_kaydedildi:
                _tani_kaydedildi = True
                _tani_dosyaya_yaz()

            if durum == "yanlis_hesap":
                _log(f"❌ Yanlış hat ({whatsapp_state['giris_hat']}). Profil atılıyor, "
                     "taze QR zorlanıyor.")
                with driver_lock:
                    _yanlis_hesap_temizle(profil_dizini)
                _gozetmen_imza = None
                whatsapp_baslat(zorla=True, qr_bekle=False, taze=True)
                return

            time.sleep(yoklama)
        except Exception as hata:
            _log(f"Gözetmen yoklama hatası (yok sayıldı): {hata}")
            time.sleep(yoklama)


def _kapanista_kapat():
    global whatsapp_driver, _gozetmen_imza, _kapaniyor
    _kapaniyor = True
    if whatsapp_driver:
        try:
            _log("Kapanışta sürücü kapatılıyor (profil kilidi bırakmamak için)...")
            whatsapp_driver.quit()
        except WebDriverException:
            pass
        whatsapp_driver = None
    _gozetmen_imza = None


atexit.register(_kapanista_kapat)


def _sinyal_yakala(sinyal_no, _kare):
    # systemd "stop" sırasında SIGTERM gönderir; atexit YALNIZCA normal çıkışta
    # çalışır. Sürücü kapatılmadan ölen süreç Chrome'u ve profil kilidini
    # (SingletonLock) yetim bırakır; sonraki açılış "profile is in use" ile düşer.
    _log(f"Sinyal {sinyal_no} alındı: sürücü kapatılıp çıkılıyor.")
    _kapanista_kapat()
    os._exit(0)


for _sinyal_adi in ("SIGTERM", "SIGINT"):
    _sinyal = getattr(signal, _sinyal_adi, None)
    if _sinyal is not None:
        try:
            signal.signal(_sinyal, _sinyal_yakala)
        except (ValueError, OSError, RuntimeError):
            # Ana thread dışındaki import'larda (testler, paket olarak kullanım)
            # sinyal kaydı reddedilir; atexit kapanışı yine çalışır.
            pass


# ============================================================
# 5) MESAJ GÖNDERME
# ============================================================
def _gonder_dugmesini_tikla(sürücü):
    js = (
        "var adaylar = [];"
        "var ikonlar = document.querySelectorAll('span[data-icon]');"
        "for (var i = 0; i < ikonlar.length; i++) {"
        "  var ad = String(ikonlar[i].getAttribute('data-icon') || '');"
        "  if (/^(send|send-alt-with-text|send-alt|send-fill|ptt-footer|ptt-outgoing|arrow-up)$/.test(ad)) {"
        "    adaylar.push(ikonlar[i].closest('button,[role=\"button\"]') || ikonlar[i]);"
        "  }"
        "}"
        "var ek = document.querySelectorAll("
        "\"footer button[type='submit'], footer [aria-label*='önder'], \" +"
        "\"footer [aria-label*='Send'], [data-testid='send-btn']\");"
        "for (var j = 0; j < ek.length; j++) {"
        "  adaylar.push(ek[j].closest('button,[role=\"button\"]') || ek[j]);"
        "}"
        "var gorunen = [];"
        "for (var k = 0; k < adaylar.length; k++) {"
        "  var a = adaylar[k];"
        "  if (!a || gorunen.indexOf(a) !== -1) continue;"
        "  var r = a.getBoundingClientRect();"
        "  if (r.width === 0 || r.height === 0) continue;"
        "  gorunen.push(a);"
        "}"
        "if (!gorunen.length) return 0;"
        "var sec = gorunen[gorunen.length - 1];"
        "sec.scrollIntoView({block: 'center'});"
        "sec.click();"
        "return gorunen.length;"
    )
    try:
        return bool(sürücü.execute_script(js))
    except (WebDriverException, JavascriptException):
        return False


def _duz_metin(deger):
    # "İ".lower() gibi ikili kodlamaları da eritmek için NFKD + birleştirme işareti atma.
    daginik = unicodedata.normalize("NFKD", str(deger).lower())
    eritilmis = "".join(c for c in daginik if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", eritilmis)


def _aktif_sohbet_kimligi(sürücü):
    """Açık sohbetin başlık metni ('' -> sohbet yok ya da okunamadı)."""
    js = (
        "var h = document.querySelector('#main header[data-testid=\"conversation-header\"]')"
        " || document.querySelector('#main header');"
        "return h ? String(h.innerText || '').trim() : '';"
    )
    try:
        return str(sürücü.execute_script(js) or "").strip()
    except (WebDriverException, JavascriptException):
        return ""


def _kimlik_eslesir_mi(kimlik, telefon, beklenen_ad, beklenen_baslik=""):
    """
    Alıcı doğrulama kapısı. WhatsApp Web başlıkta ya numarayı (kayıtsız hat) ya
    da rehber adını gösterir; bu yüzden üç kanıt kabul edilir:
    numara rakamları, esnaf kaydı adı, veya numarayı aratınca çıkan ilk sohbet
    satırının başlığı (`_sohbet_arama_basligi`). Hiçbiri tutmazsa gönderim yok.
    """
    if not kimlik:
        return False
    baslik_rakam = "".join(c for c in kimlik if c.isdigit())
    hedef_rakam = "".join(c for c in str(telefon) if c.isdigit())
    if hedef_rakam.startswith("90"):
        hedef_rakam = hedef_rakam[2:]
    hedef_rakam = hedef_rakam.lstrip("0")
    if len(hedef_rakam) >= 10 and hedef_rakam[-10:] in baslik_rakam:
        return True
    baslik = _duz_metin(beklenen_baslik)
    if baslik and baslik == _duz_metin(kimlik):
        return True
    ad = _duz_metin(beklenen_ad)
    return bool(ad) and ad in _duz_metin(kimlik)


_ARAMA_KUTUSU_BUL_JS = (
    # WhatsApp Web bu sürümde div[role="search"] taşımıyor; sol paneldeki tek
    # görünür metin kutusu, açık sohbetin (#main) dışındaki input'tur.
    "function trmAramaKutusu() {"
    "  var a = document.querySelectorAll("
    "    \"div[role='search'] input[type='text'], \" +"
    "    \"input[aria-label*='arat' i], input[placeholder*='arat' i]\");"
    "  for (var i = 0; i < a.length; i++) {"
    "    var r = a[i].getBoundingClientRect();"
    "    if (r.width > 0 && r.height > 0) return a[i];"
    "  }"
    "  var g = document.querySelectorAll(\"input[type='text']\");"
    "  for (var j = 0; j < g.length; j++) {"
    "    if (g[j].closest('#main')) continue;"
    "    var k = g[j].getBoundingClientRect();"
    "    if (k.width > 0 && k.height > 0) return g[j];"
    "  }"
    "  return null;"
    "}"
)

_ARAMA_KUTUSU_JS = _ARAMA_KUTUSU_BUL_JS + "return trmAramaKutusu();"

_ARAMA_YAZ_JS = (
    _ARAMA_KUTUSU_BUL_JS
    + "var kutu = trmAramaKutusu();"
    "if (!kutu) return false;"
    "kutu.focus();"
    # React yalnızca yerli value-setter + input olayını dinliyor.
    "var t = Object.getOwnPropertyDescriptor("
    "  window.HTMLInputElement.prototype, 'value');"
    "t.set.call(kutu, arguments[0]);"
    "kutu.dispatchEvent(new InputEvent('input', "
    "  {bubbles: true, inputType: 'insertText', data: arguments[0]}));"
    "return true;"
)


def _sohbet_arama_basligi(sürücü, telefon):
    """
    Numarayı sohbet arama kutusunda aratır, çıkan İLK satırın başlığını döndürür
    ve o satırı açar. Bu, "WhatsApp bu numarayı hangi sohbetle eşleştiriyor?"
    sorusunun tek doğrulanabilir cevabıdır; başlık tutmazsa gönderim reddedilir.
    """
    rakam = "".join(c for c in str(telefon) if c.isdigit())
    try:
        kutu = sürücü.execute_script(_ARAMA_KUTUSU_JS)
    except (WebDriverException, JavascriptException):
        return ""
    if not kutu:
        return ""
    try:
        # Selenium 4.47'de Keys.chord yok; kutuya yazmayı React'ın anladığı
        # yerli value-setter ile yapıp element bayatlaması riskini de kaldırıyoruz.
        if not sürücü.execute_script(_ARAMA_YAZ_JS, rakam):
            return ""
        time.sleep(3.0)
        baslik = sürücü.execute_script(
            "var s = document.querySelectorAll('#pane-side div[role=\"listitem\"],"
            " #pane-side div[role=\"gridcell\"]');"
            "for (var i = 0; i < s.length; i++) {"
            "  var t = String(s[i].innerText || '').replace(/\\s+/g, ' ').trim();"
            "  if (t) return t.split(/\\s{2,}|\\n/)[0].trim().slice(0, 80); }"
            "return '';"
        )
        sürücü.execute_script(
            "var s = document.querySelectorAll('#pane-side div[role=\"listitem\"],"
            " #pane-side div[role=\"gridcell\"]');"
            "for (var i = 0; i < s.length; i++) {"
            "  if (String(s[i].innerText || '').trim()) { s[i].click(); return true; } }"
            "return false;"
        )
        time.sleep(2.0)
        _arama_kutusunu_temizle(sürücü)
    except (WebDriverException, JavascriptException):
        return ""
    return str(baslik or "").strip()


def _arama_kutusunu_temizle(sürücü):
    try:
        kutu = sürücü.execute_script(_ARAMA_KUTUSU_JS)
        if not kutu:
            return
        sürücü.execute_script(
            "var t = Object.getOwnPropertyDescriptor("
            "  window.HTMLInputElement.prototype, 'value');"
            "t.set.call(arguments[0], '');"
            "arguments[0].dispatchEvent(new InputEvent('input', {bubbles: true}));",
            kutu,
        )
    except (WebDriverException, JavascriptException):
        pass


def _hedef_sohbeti_ac(sürücü, telefon, beklenen_ad, süre=12):
    """Döner: (ok, kimlik). ok=False ise hiçbir metin yazılmaz ve gönderilmez."""
    beklenen_baslik = ""
    for deneme in (1, 2):
        bitis = time.time() + süre
        while time.time() < bitis:
            if _qr_bekliyor_mu(sürücü):
                return False, "qr"
            kimlik = _aktif_sohbet_kimligi(sürücü)
            if kimlik and _kimlik_eslesir_mi(kimlik, telefon, beklenen_ad, beklenen_baslik):
                return True, kimlik
            time.sleep(1.5)
        if deneme == 1:
            _log("Başlıkta hedef numara görünmedi; numarayı aratıp eşleşen sohbet açılıyor...")
            beklenen_baslik = _sohbet_arama_basligi(sürücü, telefon)
            if beklenen_baslik:
                _log(f"Arama sonucu açılan sohbet başlığı: '{beklenen_baslik}'")
    return False, _aktif_sohbet_kimligi(sürücü)


def _gonderim_canli_dogrula(sürücü, mesaj, süre=15):
    """Mesajın tamamının kendi çıkış baloncuğunda göründüğünü onaylar."""
    js = (
        "var satirlar = document.querySelectorAll(\"#main [role='row']\");"
        "var son = '';"
        "for (var i = 0; i < satirlar.length; i++) {"
        "  var balonlar = satirlar[i].querySelectorAll("
        "    \"span.selectable-text, span[data-testid='client-side-text-div-copy']\");"
        "  var metin = '';"
        "  for (var j = 0; j < balonlar.length; j++) {"
        "    metin += String(balonlar[j].innerText || '') + '\\n';"
        "  }"
        "  if (metin.trim()) son = metin;"
        "}"
        "return son;"
    )
    hedef = _duz_metin(mesaj)
    bitis = time.time() + süre
    while time.time() < bitis:
        try:
            son = str(sürücü.execute_script(js) or "")
        except (WebDriverException, JavascriptException):
            return False
        if hedef and hedef in _duz_metin(son):
            return True
        time.sleep(1.0)
    return False


_COMPOSER_BUL_JS = (
    "var k = document.querySelector(\"div[contenteditable='true'][aria-label*='sohbetine']\")"
    " || document.querySelector(\"div[contenteditable='true'][data-tab='1']\")"
    " || document.querySelector(\"div[contenteditable='true']\");"
)


def _composer_metni(sürücü):
    """None -> composer yok; '' -> composer var ama boş; aksi -> ön-doldurulmuş metin."""
    try:
        return sürücü.execute_script(_COMPOSER_BUL_JS + "return k ? String(k.innerText || '').trim() : null;")
    except (WebDriverException, JavascriptException):
        return None


def _composeri_temizle(sürücü):
    try:
        if not sürücü.execute_script(_COMPOSER_BUL_JS + "if (!k) return false; k.focus(); return true;"):
            return False
        zincir = ActionChains(sürücü)
        zincir.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)
        zincir.send_keys(Keys.DELETE)
        zincir.perform()
    except (WebDriverException, JavascriptException):
        return False
    return not _composer_metni(sürücü)


def _metni_yaz(sürücü, mesaj):
    """
    Composer'a satır satır, gerçek tuş olaylarıyla yazar.
    execCommand('insertText') çok satırlı metnin satır sonlarını yutuyor
    (canlıda tek paragraf olarak iletildi); WhatsApp'ta düz Enter mesajı
    gönderdiği için satır sonları Shift+Enter ile verilir.
    """
    try:
        kutu = sürücü.execute_script(_COMPOSER_BUL_JS + "return k;")
        if not kutu:
            return False
        sürücü.execute_script("arguments[0].focus();", kutu)
        zincir = ActionChains(sürücü)
        for sıra, satir in enumerate(str(mesaj).split("\n")):
            if sıra:
                zincir.key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
            if satir:
                zincir.send_keys(satir)
        zincir.perform()
    except (WebDriverException, JavascriptException):
        return False
    return bool(_composer_metni(sürücü))


def _satirlar(metin):
    """
    WhatsApp composer'ı her satırı ayrı <p> olarak tutuyor ve innerText her
    blok sonunda iki satır başı veriyor; bu yüzden art arda boş satırlar tek
    satıra indirgenir. Şablon boş satır içermediğinden "hepsi tek satıra
    düştü" hatası yine yakalanır.
    """
    return [s for s in re.sub(r"\n{2,}", "\n", str(metin).strip()).split("\n") if s]


def _metin_kilidi_kontrol(sürücü, mesaj):
    """Döner: (tamam, sebep). Kutudaki metin gidecek metinle birebir olmalı."""
    kutu = _composer_metni(sürücü)
    if kutu is None:
        return False, "mesaj kutusu bulunamadı"
    # Emoji'ler composer'da <img> olarak tutulur ve innerText'e girmez;
    # karşılaştırma yalnızca harf/rakam iskeleti ve satır sayısı üzerinden yapılır.
    if _duz_metin(kutu) != _duz_metin(mesaj):
        return False, "kutudaki metin şablonla birebir aynı değil"
    beklenen_satir = len(_satirlar(mesaj))
    if len(_satirlar(kutu)) != beklenen_satir:
        return False, (
            f"satır sayısı {len(_satirlar(kutu))} != {beklenen_satir} "
            "(satır sonları kayboldu)"
        )
    return True, ""


def _devam_dugmesini_tikla(sürücü):
    """
    Numaran rehberde yoksa WhatsApp Web /send bağlantısında
    'Sohbete devam et' onayı çıkarır; composer ancak onaydan sonra gelir.
    """
    js = (
        "var ikonlar = ['chat-link-confirm-continue', 'continue-chat', 'forward-chat'];"
        "var metinler = ['sohbet devam', 'devam et', 'continue to chat', 'open chat'];"
        "var dugmeler = document.querySelectorAll('button,[role=\"button\"]');"
        "for (var i = 0; i < dugmeler.length; i++) {"
        "  var d = dugmeler[i];"
        "  var t = String(d.innerText || d.textContent || '').trim().toLowerCase();"
        "  var al = String(d.getAttribute('aria-label') || '').toLowerCase();"
        "  var ikon = d.querySelector('span[data-icon]');"
        "  var ad = ikon ? String(ikon.getAttribute('data-icon')) : '';"
        "  var eslesti = ikonlar.indexOf(ad) !== -1;"
        "  if (!eslesti) { for (var j = 0; j < metinler.length; j++) {"
        "    if (t === metinler[j] || al.indexOf(metinler[j]) !== -1) { eslesti = true; break; } } }"
        "  if (eslesti) { d.click(); return t || al || ad; }"
        "}"
        "return '';"
    )
    try:
        return sürücü.execute_script(js) or ""
    except (WebDriverException, JavascriptException):
        return ""


def _sohbet_ekrani_hazirla(sürücü, mesaj, timeout=None):
    """
    /send?phone= bağlantısı WhatsApp Web'de TAM bir yeniden yükleme başlatır:
    açılış ekranı 10-30 sn sürebilir, sonra onay düğmesi gelebilir. Bu yüzden
    tek seferlik presence beklemesi yetmez; ekrana gelene kadar yoklanır.
    Döner: "hazir" | "qr" | "bekleniyor"
    """
    bitis = time.time() + (timeout or SOHBET_BEKLEME_SN)
    while time.time() < bitis:
        metin = _composer_metni(sürücü)
        if metin is not None:
            # WhatsApp, o sohbetin TASLAĞINI composer'a geri koyuyor. Taslak
            # temizlenmeden yazılırsa eski metin gönderilir: önce kutu boşaltılır.
            if metin and not _composeri_temizle(sürücü):
                time.sleep(1.5)
                continue
            if not _metni_yaz(sürücü, mesaj):
                time.sleep(1.5)
                continue
            return "hazir"
        if _devam_dugmesini_tikla(sürücü):
            time.sleep(1.5)
            continue
        if _qr_bekliyor_mu(sürücü):
            return "qr"
        time.sleep(1.5)
    return "bekleniyor"


@app.route("/api/kara_liste", methods=["GET"])
def kara_liste_gor():
    conn = veritabani_baglan()
    try:
        sema_goc_uygula(conn)
        satirlar = [dict(r) for r in conn.execute(
            "SELECT telefon, gerekce, tarih, kaynak FROM kara_liste "
            "ORDER BY tarih DESC LIMIT 500")]
    finally:
        conn.close()
    return jsonify({"adet": len(satirlar), "kayitlar": satirlar})


@app.route("/api/kara_liste_kaldir", methods=["POST"])
def kara_liste_kaldir():
    """Yanlış yakalanan bir redi geri alma (örn. 'sipariş iptal oldu' mesajı).

    Numara hem kara listeden hem de o numaraya ait esnaf satırlarının
    opt_out/`gonderim_durumu` kilitlerinden birlikte temizlenir; aksi halde
    silme işe yaramazdı.
    """
    data = request.json or {}
    kanonik = telefon_kanonik(data.get("telefon"))
    if not kanonik:
        return jsonify({"status": "hata", "mesaj": "telefon zorunlu"}), 400
    sebep = str(data.get("sebep") or "panel")[:200]
    conn = veritabani_baglan()
    try:
        conn.create_function("kanonik", 1, telefon_kanonik)
        sema_goc_uygula(conn)
        silinen = conn.execute("DELETE FROM kara_liste WHERE telefon = ?", (kanonik,)).rowcount
        cozulen = conn.execute(
            "UPDATE esnaflar SET opt_out = 0, opt_out_tarihi = NULL, "
            "gonderim_durumu = 'gonderime_hazir', son_gelen_imza = NULL "
            "WHERE kanonik(COALESCE(telefon, '')) = ?", (kanonik,),
        ).rowcount
        conn.commit()
    finally:
        conn.close()
    _log(f"🗑️ Kara listeden çıkarıldı: {kanonik} (silinen={silinen}, "
         f"esnaf satırı çözüldü={cozulen}, sebep: {sebep})")
    return jsonify({"status": "basarili", "telefon": kanonik,
                    "kara_listeden_silinen": silinen, "esnaf_satiri_cozuldu": cozulen})


def kara_liste_kontrolu(telefon):
    """Numara kalıcı kara listede mi? None=karar verilemedi (gönderime devam).

    'DUR'/'İPTAL' redleri numara ile bağlanır: esnaf satırı silinip aynı numara
    taramayla yeni id olarak geri gelse bile mesaj gitmez.
    """
    if not telefon:
        return False
    conn = veritabani_baglan()
    try:
        sema_goc_uygula(conn)
        return kara_listede_mi(conn, telefon)
    except sqlite3.Error as hata:
        _log(f"⚠️ Kara liste okunamadı ({hata}); gönderim akışı bu kayıt için "
             "doğrulanmış bir red görmedi.")
        return None
    finally:
        conn.close()


def gercek_whatsapp_mesaj_gonder(telefon, mesaj, isletme_adi=None):
    """Gönderimin TEK girişi: kara liste + sohbet kilidi, sonra asıl iş.

    Motorun arka plan döngüsü ile panelden/HTTP ile gelen gönderimler aynı
    sürücüyü kullandığından birbirinin sohbetini bozamaz. Kara liste bu tek
    kapıda uygulanır ki hiçbir çağran (panel, otomatik yanıt, toplu motor)
    reddedilmiş numaraya ulaşamasın.
    """
    if kara_liste_kontrolu(telefon) is True:
        _log(f"🚫 KARA LİSTE: {telefon} numarasına mesaj gönderilmedi "
             "(DUR/İPTAL redi kalıcı).")
        return False
    with SOHBET_KILIDI:
        return _gercek_whatsapp_mesaj_gonder_ic(telefon, mesaj, isletme_adi)


def _gercek_whatsapp_mesaj_gonder_ic(telefon, mesaj, isletme_adi=None):
    global whatsapp_driver

    if not _surucu_saglam_mi():
        _log("Sürücü aktif değil, yeniden başlatılıyor...")
        if not whatsapp_baslat(zorla=True, qr_bekle=False):
            _log("❌ WhatsApp oturumu açılamadı; mesaj KUYRUKLANMADI.")
            return False

    if not whatsapp_state.get("eslesme"):
        izinli = (not KATIHAT_FILTRESI) and whatsapp_state.get("giris_sinyali")
        if not izinli:
            _log(f"❌ Oturum doğrulanmış ticari hata ({TICARI_HAT_ULUSLARARASI}) bağlı değil. "
                 f"Durum: {whatsapp_state['durum']}, sebep: "
                 f"{whatsapp_state.get('sebep') or '-'}. Gönderim reddedildi "
                 "(yanlış hattan mesaj gitmesin diye).")
            return False
        _log("⚠️ KATI_HAT_FILTRESI=0: oturum açık ama hat numaraları okunamadı; "
             "gönderime izin verildi (WHATSAPP_KATI_HAT_FILTRESI=1 ile kapatabilirsin).")

    try:
        temiz_tel = "".join(c for c in str(telefon) if c.isdigit())
        if temiz_tel.startswith("0"):
            temiz_tel = "9" + temiz_tel
        isletme = (isletme_adi or "-").strip() or "-"
        _log(f"[WHATSAPP GÖNDERİM BAŞLADI] İşletme: {isletme} - Hat: {temiz_tel} "
             f"- {len(str(mesaj))} karakter")
        # Metin URL'ye konulmaz: uzun/emoji'li metin /send derin bağlantısını
        # bozup sohbeti açmadan eski pencerede bırakıyor. Önce sohbet doğrulanır,
        # sonra metin yazılır.
        try:
            whatsapp_driver.get(f"https://web.whatsapp.com/send?phone={temiz_tel}")
        except TimeoutException:
            _log("Sayfa yüklemesi zaman aşımına uğradı (WhatsApp Web ağır); "
                 "sohbet yoklamasına devam ediliyor.")

        acik, kimlik = _hedef_sohbeti_ac(whatsapp_driver, temiz_tel, isletme)
        if kimlik == "qr":
            whatsapp_state["durum"] = "hazir_qr"
            whatsapp_state["eslesme"] = False
            _log("❌ Oturum düşmüş, ekran QR karşılama sayfasına dönmüş. "
                 "Gönderim yapılmadı. /api/whatsapp_yeniden_baslat ile yeni QR okutun.")
            return False
        if not acik:
            _hata_ekrani_al("alici_dogrulanamadi")
            _log(f"🚫 ALICI DOĞRULANMADI, GÖNDERİM YOK. Hedef: {temiz_tel} ({isletme}) | "
                 f"şu an açık sohbet: {kimlik or '-'}. Metin hiçbir mesaj kutusuna yazılmadı.")
            return False
        _log(f"✅ Alıcı doğrulandı: '{kimlik}' == hedef {temiz_tel}")

        # Sohbet ekranı (yükleme + olası "devam et" onayı) kurulmadan gönderime geçilmez.
        ekran = _sohbet_ekrani_hazirla(whatsapp_driver, mesaj)
        if ekran == "qr":
            whatsapp_state["durum"] = "hazir_qr"
            whatsapp_state["eslesme"] = False
            _log("❌ Oturum düşmüş, ekran QR karşılama sayfasına dönmüş. "
                 "Gönderim yapılmadı. /api/whatsapp_yeniden_baslat ile yeni QR okutun.")
            return False
        if ekran != "hazir":
            _hata_ekrani_al("sohbet_acilmadi")
            _log(f"❌ Sohbet açılmadı: {temiz_tel} "
                 f"({SOHBET_BEKLEME_SN} sn içinde mesaj kutusu gelmedi).")
            return False

        # Metin kilidi: kutuda tam olarak gidecek şablon yoksa gönderilmez.
        kilitli, kilit_sebebi = _metin_kilidi_kontrol(whatsapp_driver, mesaj)
        if not kilitli:
            _hata_ekrani_al("metin_kilidi")
            _log(f"🚫 METİN KİLİDİ SAĞLANAMADI ({kilit_sebebi}) -> gönderim yok. "
                 f"İşletme: {isletme} - Hat: {temiz_tel}")
            _log(f"[WHATSAPP GÖNDERİLEMEDİ] İşletme: {isletme} - Metin:\n{_konsol_metni(mesaj)}")
            return False

        gonderildi = False
        for _ in range(3):
            if _gonder_dugmesini_tikla(whatsapp_driver):
                gonderildi = True
                break
            time.sleep(1.2)

        if not gonderildi:
            # Enter yedeği (metin kutusuna odaklanıp gönder).
            try:
                kutu = WebDriverWait(whatsapp_driver, 6).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "div[contenteditable='true']"))
                )
                kutu.send_keys(Keys.ENTER)
                gonderildi = True
            except (TimeoutException, WebDriverException):
                pass

        if not gonderildi:
            _hata_ekrani_al("gonder_dugmesi_bulunamadi")
            _log("❌ Gönder düğmesi bulunamadı (WhatsApp arayüzü değişmiş olabilir).")
            _log(f"[WHATSAPP GÖNDERİLEMEDİ] İşletme: {isletme} - Metin:\n{_konsol_metni(mesaj)}")
            return False

        if not _gonderim_canli_dogrula(whatsapp_driver, mesaj):
            _hata_ekrani_al("gonderim_dogrulanamadi")
            _log(f"⚠️ GÖNDERİM DOĞRULANAMADI -> baloncuğunda görünmedi. İşletme: {isletme} "
                 f"- Metin:\n{_konsol_metni(mesaj)}")
            return False

        _log(f"📤 Mesaj gönderildi -> {temiz_tel} (hat {whatsapp_state['giris_hat']})")
        _log(f"[WHATSAPP GÖNDERİLDİ] İşletme: {isletme} - Metin:\n{_konsol_metni(mesaj)}")
        return True
    except Exception as hata:
        _hata_ekrani_al("gonderim_hatasi")
        _log(f"❌ GÖNDERİM HATASI: {hata}")
        _log(f"[WHATSAPP GÖNDERİLEMEDİ] İşletme: {isletme} - Metin:\n{_konsol_metni(mesaj)}")
        return False


# ============================================================
# 6) API UÇLARI
# ============================================================
@app.route("/api/esnaflar", methods=["GET"])
def get_esnaflar():
    """Panel bu uca bağlanabiliyor olmasına göre 'Canlı bağlantı' rozetini yakar;
    bu yüzden hiçbir koşulda 500 dönmemeli."""
    try:
        conn = veritabani_baglan()
        sema_goc_uygula(conn)  # izin/adres kolonları eski bir DB'de eksik kalmasın
        # Sıra operatörün iş akışına göre: ONAY BEKLEYEN telefonlu adaylar en üstte,
        # sonra onaylılar (motor bunlara yazar), sonra telefonu olmayanlar.
        rows = conn.execute(
            """
            SELECT id, isletme, telefon, kod, durum, COALESCE(izin, 0) AS izin,
                   CASE WHEN TRIM(COALESCE(adres, ''))   = '' THEN 0 ELSE 1 END AS adres_var,
                   CASE WHEN TRIM(COALESCE(telefon, '')) = '' THEN 0 ELSE 1 END AS telefon_var
            FROM esnaflar
            ORDER BY CASE WHEN COALESCE(izin, 0) = 0 AND TRIM(COALESCE(telefon, '')) <> '' THEN 0
                          WHEN COALESCE(izin, 0) = 1 THEN 1
                          ELSE 2 END,
                     id DESC
            """
        ).fetchall()
        son = {}
        try:
            for r in conn.execute(
                """
                SELECT esnaf_id, mesaj, tarih FROM mesajlar WHERE id IN
                  (SELECT MAX(id) FROM mesajlar GROUP BY esnaf_id)
                """
            ).fetchall():
                son[r["esnaf_id"]] = r
        except sqlite3.Error:
            son = {}
        conn.close()
    except sqlite3.Error as hata:
        _log(f"esnaflar sorgu hatası: {hata}")
        return jsonify([])

    esnaflar_listesi = []
    for row in rows:
        kayit = son.get(row["id"])
        esnaflar_listesi.append({
            "id": row["id"],
            "ad": row["isletme"],
            "kod": row["kod"],
            "telefon": row["telefon"],
            "mobil": mobil_numara(row["telefon"]),
            "izin": int(row["izin"] or 0),
            "telefon_var": bool(row["telefon_var"]),
            "adres_var": bool(row["adres_var"]),
            "durum": row["durum"] if "durum" in row.keys() else "onayli",
            "kanal": "whatsapp",
            "son_mesaj": (str(kayit["mesaj"])[:80] if kayit else ""),
            "son_mesaj_zamani": (_iso_utc(kayit["tarih"]) if kayit else None),
            "online": True,
        })
    return jsonify(esnaflar_listesi)


def _iso_utc(deger):
    """
    SQLite CURRENT_TIMESTAMP UTC döner; panel bunu yerel saat olarak yorumlarsa
    mesajlar 3 saat erken görünür. 'Z' takısı yerel saate çevirtir.
    """
    metin = str(deger or "").strip()
    if not metin:
        return ""
    return metin.replace(" ", "T") + "Z"


@app.route("/api/mesajlar/<int:esnaf_id>", methods=["GET"])
def get_mesajlar(esnaf_id):
    conn = veritabani_baglan()
    try:
        mesajlar = conn.execute(
            "SELECT id, gonderen, mesaj, tarih FROM mesajlar WHERE esnaf_id = ? ORDER BY id ASC",
            (esnaf_id,),
        ).fetchall()
    except sqlite3.Error:
        mesajlar = []
    conn.close()

    formatli_mesajlar = []
    for m in mesajlar:
        yon = "out" if str(m["gonderen"]).upper() == "ESNAF" else "in"
        formatli_mesajlar.append({
            "id": m["id"],
            "yon": yon,
            "kanal": "whatsapp",
            "icerik": m["mesaj"],
            "zaman": _iso_utc(m["tarih"]) if "tarih" in m.keys() else "",
        })
    return jsonify(formatli_mesajlar)


def _esnaf_kayiti(conn, esnaf_id):
    row = conn.execute("SELECT * FROM esnaflar WHERE id = ?", (esnaf_id,)).fetchone()
    if not row:
        return None
    hucere = row.keys()

    def alan(ad):
        return str(row[ad]).strip() if ad in hucere and row[ad] is not None else ""

    return {
        "isletme": alan("isletme"),
        "telefon": alan("telefon"),
        "adres": alan("adres"),
        "yetkili": alan("yetkili"),
    }


def _mesaj_kaydet(conn, esnaf_id, gonderen, metin):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mesajlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esnaf_id INTEGER,
            gonderen TEXT,
            mesaj TEXT,
            tarih DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, ?, ?)",
        (esnaf_id, gonderen, metin),
    )
    conn.commit()


def _esnaf_tanitimi_gonder(esnaf_id, adres=None, yetkili=None, isletme_adi=None):
    """Kilitli tanıtım metnini üretir, WhatsApp'tan gönderir ve yalnızca teslim
    edildiğinde panel geçmişine yazar."""
    conn = veritabani_baglan()
    try:
        kayit = _esnaf_kayiti(conn, esnaf_id)
        if not kayit:
            return {"status": "hata", "mesaj": f"Esnaf kaydı bulunamadı: {esnaf_id}"}, 404
        try:
            metin = esnaf_tanitim_metni(
                isletme_adi or kayit["isletme"],
                kayit["adres"] if adres is None else adres,
                kayit["yetkili"] if yetkili is None else yetkili,
            )
        except SablonHatasi as hata:
            _log(f"🚫 Tanıtım metni üretilmedi (esnaf {esnaf_id}): {hata}")
            return {"status": "hata", "mesaj": str(hata), "eksikler": hata.eksikler}, 400
    finally:
        conn.close()

    _log(f"[WHATSAPP TETİKLENDİ] Esnaf #{esnaf_id} - İşletme: {kayit['isletme'] or '-'} "
         f"- Hat: {kayit['telefon'] or '-'}")
    gonderim = (
        gercek_whatsapp_mesaj_gonder(kayit["telefon"], metin, kayit["isletme"])
        if kayit["telefon"] else False
    )
    if gonderim:
        conn = veritabani_baglan()
        try:
            _mesaj_kaydet(conn, esnaf_id, "DERYA", metin)
        finally:
            conn.close()
    return {
        "status": "basarili" if gonderim else "gonderilemedi",
        "esnaf_id": esnaf_id,
        "isletme": kayit["isletme"],
        "telefon": kayit["telefon"],
        "metin": metin,
        "metin_karakter": len(metin),
        "whatsapp_gonderildi": gonderim,
        "oturum": whatsapp_state["durum"],
        "hat": whatsapp_state.get("giris_hat", ""),
    }, 200


@app.route("/api/esnaf_tanitim_gonder", methods=["POST"])
def esnaf_tanitim_gonder():
    data = request.json or {}
    esnaf_id = data.get("esnaf_id")
    if not esnaf_id:
        return jsonify({"status": "hata", "mesaj": "esnaf_id zorunlu"}), 400
    govde, kod = _esnaf_tanitimi_gonder(
        esnaf_id,
        adres=data.get("adres"),
        yetkili=data.get("yetkili"),
        isletme_adi=data.get("isletme"),
    )
    return jsonify(govde), kod


@app.route("/api/mesaj_gonder", methods=["POST"])
def mesaj_gonder():
    data = request.json or {}
    esnaf_id = data.get("esnaf_id")
    esnaf_mesaj = data.get("mesaj")

    if not esnaf_id:
        return jsonify({"status": "hata", "mesaj": "Eksik parametre"}), 400

    if data.get("sablon") == "esnaf_tanitim":
        govde, kod = _esnaf_tanitimi_gonder(
            esnaf_id,
            adres=data.get("adres"),
            yetkili=data.get("yetkili"),
            isletme_adi=data.get("isletme"),
        )
        return jsonify(govde), kod

    if not esnaf_mesaj:
        return jsonify({"status": "hata", "mesaj": "Eksik parametre"}), 400

    conn = veritabani_baglan()
    kayit = _esnaf_kayiti(conn, esnaf_id) or {"isletme": "İşletme", "telefon": ""}
    isletme_adi = kayit["isletme"] or "İşletme"
    telefon = kayit["telefon"]

    # Gelen metin, WhatsApp okuyucusu ile AYNI yoldan işlenir: tekilleme +
    # 'DUR'/'İPTAL' redi burada da kalıcı kara listeye yazar.
    sema_goc_uygula(conn)
    durum = gelen_mesaj_kaydet(
        conn, esnaf_id, esnaf_mesaj, _mesaj_imzasi(f"{isletme_adi}", esnaf_mesaj),
        _mesaj_kaydet,
    )
    if not durum["kaydedildi"] and not durum["yinelenen"]:
        _mesaj_kaydet(conn, esnaf_id, "ESNAF", esnaf_mesaj)
    kara_listeye_girdi = bool(durum.get("kara_liste"))
    conn.close()

    if durum["opt_out"]:
        _log(f"🚫 OPT-OUT: Esnaf #{esnaf_id} ({isletme_adi}) 'DUR/İPTAL' dedi — "
             f"kalıcı kara liste: {kara_listeye_girdi}. Yanıt GÖNDERİLMEDİ.")
        return jsonify({
            "status": "opt_out",
            "esnaf_id": esnaf_id,
            "isletme": isletme_adi,
            "opt_out": True,
            "kara_liste": kara_listeye_girdi,
            "cevap": "",
            "yanit": "",
            "whatsapp_gonderildi": False,
            "mesaj": "Kişi ticari iletiyi reddetti; kalıcı kara listeye alındı.",
        })

    derya_cevabi = derya_otonom_yanitla(esnaf_mesaj, isletme_adi)
    gonderim = None
    if telefon:
        gonderim = gercek_whatsapp_mesaj_gonder(telefon, derya_cevabi, isletme_adi)
    if gonderim:
        # Panel geçmişi yalnızca WhatsApp teslimatı doğrulanan çıktıları taşır.
        conn = veritabani_baglan()
        try:
            _mesaj_kaydet(conn, esnaf_id, "DERYA", derya_cevabi)
        finally:
            conn.close()
    return jsonify({
        "status": "basarili",
        "cevap": derya_cevabi,
        "yanit": derya_cevabi,
        "whatsapp_gonderildi": gonderim,
        "oturum": whatsapp_state["durum"],
        "hat": whatsapp_state.get("giris_hat", ""),
    })


@app.route("/api/whatsapp_durum", methods=["GET"])
def whatsapp_durum():
    saglam = _surucu_saglam_mi()
    if not saglam and whatsapp_state["durum"] not in ("baslatiliyor",):
        with state_lock:
            whatsapp_state["durum"] = "kapali"
            whatsapp_state["eslesme"] = False
    return jsonify({
        "durum": whatsapp_state["durum"],
        "surucu_aktif": saglam,
        "mod": PROFIL_MODU,
        "profil_dizini": whatsapp_state["profil_dizini"],
        "cdp_port": whatsapp_state["cdp_port"],
        "okunan_hat": whatsapp_state.get("giris_hat", ""),
        "beklenen_hat": TICARI_HAT_ULUSLARARASI,
        "hat_eslesmesi": whatsapp_state.get("eslesme", False),
        "giris_sinyali": whatsapp_state.get("giris_sinyali", False),
        "kimlik_kaynagi": whatsapp_state.get("kimlik_kaynagi", ""),
        "sebep": whatsapp_state.get("sebep", ""),
        "gozetmen_calisiyor": whatsapp_state.get("gozetmen_calisiyor", False),
        "tarama_zamani": whatsapp_state.get("tarama_zamani", ""),
        "baslangic": whatsapp_state.get("baslangic_zamani", ""),
        "son_mesaj": whatsapp_state.get("son_mesaj", ""),
        "gonderime_hazir": bool(saglam and whatsapp_state.get("eslesme")),
    })


@app.route("/api/whatsapp_tani", methods=["GET"])
def whatsapp_tani():
    """Canlı teşhis: WhatsApp Web'in depoladığı kimlik anahtarlarını dökümler."""
    if not _surucu_saglam_mi():
        return jsonify({"hata": "surucu aktif degil",
                        "durum": whatsapp_state["durum"]}), 503
    veri = _tani_dosyaya_yaz()
    if veri is None:
        return jsonify({"hata": "tani alinamadi"}), 500
    return jsonify(veri)


@app.route("/api/whatsapp_oturum_dogrula", methods=["POST"])
def whatsapp_oturum_dogrula():
    """
    Numara otomatik okunamazsa (wa.db gecikmesi/arayüz değişimi) SON ÇARE manuel
    onay: ekranda 05426235116 hattının açık olduğunu GÖZLE doğrulayıp köprüyü açar.
    Otomatik eşleşme geri gelince bu bayrak yeniden değerlendirilir.
    """
    if not _surucu_saglam_mi():
        return jsonify({"basarili": False, "hata": "surucu aktif degil"}), 503
    if not _giris_sinyali_var_mi(whatsapp_driver):
        return jsonify({
            "basarili": False,
            "hata": "oturum-acik-degil",
            "aciklama": "QR henüz okunmamış. Önce telefonu bağla, sonra doğrula.",
        }), 409
    with state_lock:
        whatsapp_state["durum"] = "giris_yapildi"
        whatsapp_state["eslesme"] = True
        whatsapp_state["kimlik_kaynagi"] = "kullanici-onayi"
        whatsapp_state["sebep"] = ""
        if not whatsapp_state["giris_hat"]:
            whatsapp_state["giris_hat"] = TICARI_HAT_ULUSLARARASI
    _hat_kaydi_yaz(TICARI_HAT_ULUSLARARASI)
    _log(f"👍 Oturum elle doğrulandı: {TICARI_HAT_ULUSLARARASI} — panel köprüsü CANLI.")
    return jsonify({"basarili": True, "hat": whatsapp_state["giris_hat"],
                    "kaynak": "kullanici-onayi"})


@app.route("/api/whatsapp_yeniden_baslat", methods=["POST"])
def whatsapp_yeniden_baslat():
    taze = True
    if request.is_json and isinstance(request.json, dict):
        taze = bool(request.json.get("taze_profil", True))
    _log(f"Manuel yeniden başlatma istendi (taze_profil={taze}).")

    def _calis():
        whatsapp_baslat(zorla=True, qr_bekle=True, taze=taze)

    Thread(target=_calis, daemon=True).start()
    return jsonify({
        "baslatildi": True,
        "taze_profil": taze,
        "durum": whatsapp_state["durum"],
        "not": "Chrome arka planda açılıyor; taze QR için /api/whatsapp_durum'u yoklayın.",
    })


@app.route("/api/whatsapp_cikis", methods=["POST"])
def whatsapp_cikis():
    """Oturumu kapatır ve profil klasörünü siler -> bir dahaki açılış kesinlikle QR ister."""
    global whatsapp_driver, _gozetmen_imza
    dizin = whatsapp_state.get("profil_dizini") or ""
    _gozetmen_imza = None
    # SOHBET_KILIDI once: motor bir gönderimin ortasındayken sürücünün altından
    # çekilmesini bekletir (kilit sırası her zaman SOHBET_KILIDI -> driver_lock).
    with SOHBET_KILIDI, driver_lock:
        if whatsapp_driver:
            try:
                whatsapp_driver.get("https://web.whatsapp.com/")
                whatsapp_driver.delete_all_cookies()
                whatsapp_driver.execute_script("localStorage.clear();")
                whatsapp_driver.quit()
            except WebDriverException:
                pass
            whatsapp_driver = None
    _hedef_surezleri_olddur()
    silindi = False
    if dizin and os.path.isdir(dizin):
        shutil.rmtree(dizin, ignore_errors=True)
        silindi = True
    with state_lock:
        whatsapp_state.update(durum="kapali", eslesme=False, giris_hat="",
                              giris_sinyali=False, kimlik_kaynagi="",
                              gozetmen_calisiyor=False, sebep="kullanici-cikisi")
    _log(f"Oturum kapatıldı, profil silindi={silindi}")
    return jsonify({"basarili": True, "profil_silindi": silindi, "dizin": dizin})


@app.route("/api/saglik", methods=["GET"])
def saglik():
    return jsonify({"servis": "TRM Derya API", "port": 5000,
                    "whatsapp": whatsapp_state["durum"]})


# ============================================================
# 7) OTONOM MOTOR (7/24 insansız gönderim + gelen mesaj okuma)
# ============================================================
OTONOM_YAPI = Yapilandirma(os.environ)
otonom_kilit = Lock()
otonom_son_rapor = {"asama": "henuz-baslamadi"}
gelen_son_rapor = {"kisiler": None}
# Eşleşmeyen okunmamış sohbetlerin son bildirilen listesi (log tekrarı önlenir).
_eslesmeyen_imza = ""
# Eşleşen (esnaf sanılan) sohbetlerin son bildirilen listesi; yanlış eşleşme
# sessiz kalmasın ama her yoklamada log da şişmesin.
_eslesen_imza = ""


def _log_motor(mesaj):
    """Motor/okuyucu logları kendi etiketini taşır ([OTONOM], [GELEN])."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {mesaj}", flush=True)


# Aday havuzu: harita/listeden firma toplayıp esnaflar tablosuna YALNIZCA
# izin=0 / durum='ADAY' olarak yazar. Gönderim motoru izin=1 şartı nedeniyle
# buradan giren hiçbir kaydı seçmez; rıza kararı panelden operatöre aittir.
ADAY_YAPI = AdayYapisi(os.environ)


def _oturum_gonderime_hazir():
    """Motorun göndermeye izin veren tek kapısı: sürücü ayakta VE hat doğrulanmış."""
    return bool(_surucu_saglam_mi() and whatsapp_state.get("eslesme"))


def _motorla_tanitimi_gonder(esnaf_id):
    """Motor -> mevcut tanıtım gönderim hattı köprüsü.

    _esnaf_tanitimi_gonder (govde, kod) döndürür; motor govde.status='basarili'
    arayacağından sadece govde'yi veririz. HTTP tarafıyla aynı kilitli fonksiyon
    kullanılır, yani panel'den elle yapılan gönderimle çakışamaz.
    """
    govde, _kod = _esnaf_tanitimi_gonder(esnaf_id)
    return govde


class _RaporluMotor(Motor):
    """Son tur çıktısını /api/otonom_durum için bellekte tutar."""

    def bir_tur(self):
        sonuc = super().bir_tur()
        with otonom_kilit:
            otonom_son_rapor.clear()
            otonom_son_rapor.update(sonuc)
            otonom_son_rapor["zaman"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return sonuc


def otonom_hedef_isleyici(hedef_sayi=None):
    motor = _RaporluMotor(
        yapi=OTONOM_YAPI,
        baglan=veritabani_baglan,
        gonder=_motorla_tanitimi_gonder,
        oturum_hazir=_oturum_gonderime_hazir,
        uyustur=time.sleep,
        log=_log_motor,
    )
    motor.dongu()


# ---- gelen mesaj okuyucu --------------------------------------------------
# WhatsApp Web satır DOM'u canlıda ölçülerek yazıldı (2026-10-19):
#  * Her sohbet hem div[role=listitem] hem onun İÇİNDEKİ div[role=gridcell]
#    olarak iki kez eşleşiyor -> iç içe tekrar ayıklanmazsa her sohbet iki kez
#    işlenir.
#  * row.innerText zaman damgası ve önizlemeyi de içeriyor ("Meral Günendi 13:36
#    Değerli müşterimiz, 0006491021 nolu...") -> telefondan eşleştirme bunu
#    rakama çevirip çöp üretirdi. Saf isim span[dir=auto][title] özniteliğinde.
#  * Okunmamış sayısı 'icon-marker' sınıfında DEĞİL, rozetin aria-label'ında
#    ("8 okunmamış mesaj"). Yerel dile göre değiştiği için sayı + okunmam/unread
#    deseni birlikte aranır.
# Payleşen JS parçaları: her execute_script çağrısı kendi başına çalışmalı,
# bu yüzden düzgüler Python tarafında birleştirilir.
_SATIRLAR_JS = (
    "var adaylar = document.querySelectorAll("
    "  '#pane-side div[role=\"listitem\"], #pane-side div[role=\"gridcell\"]');"
    "var satirlar = [];"
    "for (var i = 0; i < adaylar.length; i++) {"
    "  var n = adaylar[i], tekrar = false;"
    "  for (var k = 0; k < satirlar.length; k++) {"
    "    if (satirlar[k].contains(n) || n.contains(satirlar[k])) { tekrar = true; break; }"
    "  }"
    "  if (!tekrar) satirlar.push(n);"
    "}"
)

_SATIR_BASLIGI_JS = (
    "function baslikAl(d) {"
    "  var e = d.querySelector('span[dir=\"auto\"][title]');"
    "  var t = e ? String(e.getAttribute('title') || '').trim() : '';"
    "  if (t) return t.slice(0, 80);"
    "  var tam = String(d.innerText || '').replace(/\\s+/g, ' ').trim();"
    "  return tam.split(/\\s{2,}|\\n/)[0].trim().slice(0, 80);"
    "}"
)

_SATIR_OKUNMAMIS_JS = (
    "function okunmamisAl(d) {"
    "  var en = 0;"
    "  var e = d.querySelectorAll('span');"
    "  for (var j = 0; j < e.length; j++) {"
    "    var etiket = String(e[j].getAttribute('aria-label') || '');"
    "    var sayi = (etiket.match(/[0-9]+/) || [])[0];"
    "    if (sayi && /okunmam|unread/i.test(etiket) && Number(sayi) > en) en = Number(sayi);"
    "    var metin = String(e[j].innerText || '').trim();"
    "    if (/^[0-9]{1,4}$/.test(metin) && Number(metin) > en) en = Number(metin);"
    "  }"
    "  return en;"
    "}"
)

_KISILER_JS = (
    _SATIRLAR_JS + _SATIR_BASLIGI_JS + _SATIR_OKUNMAMIS_JS +
    "var varliklar = [];"
    "for (var i = 0; i < satirlar.length; i++) {"
    "  var baslik = baslikAl(satirlar[i]);"
    "  if (baslik) varliklar.push("
    "    {baslik: baslik, okunmamis: okunmamisAl(satirlar[i])});"
    "}"
    "return varliklar;"
)

_GELEN_BALONLAR_JS = (
    "var balonlar = document.querySelectorAll("
    "  \"#main div.message-in span.selectable-text, "
    "#main div.message-in span[data-testid='client-side-text-div-copy']\");"
    "var cikt = [];"
    "for (var i = 0; i < balonlar.length; i++) {"
    "  var t = String(balonlar[i].innerText || '').trim();"
    "  if (t) cikt.push(t);"
    "}"
    "return cikt.slice(-8);"
)

_SOHBET_ROW_TIKLA_JS = (
    "var hedef = arguments[0];" + _SATIRLAR_JS + _SATIR_BASLIGI_JS +
    "for (var i = 0; i < satirlar.length; i++) {"
    "  if (baslikAl(satirlar[i]) === hedef) { satirlar[i].click(); return true; }"
    "}"
    "return false;"
)


def _rakamlar(deger):
    return "".join(c for c in str(deger or "") if c.isdigit())


def _esnaf_eslestir(conn, sohbet_basligi):
    """Sohbet başlığındaki numara veya işletme adı -> esnaflar.id.

    Temkinli: yalnızca TAM numara eşleşmesi ya da başlıkta geçen işletme adı
    kabul edilir. Bulunamazsa None döner ve mesaj kayda geçmez (yanlış kişiye
    yanıt gitmesin).

    ADAY satırları eşleştirme DIŞIDIR (izin=1 verilmedikçe): aday havuzu
    OSM'den scraped isimlerdir, yani karşı tarafın bize yazmış olma ihtimali
    yoktur. 200 ticari isim tabloya düştüğünde "Kafe", "Medya", "Market" gibi
    kısa/unvan-parçaları kişisel ya da grup sohbet başlıklarıyla çakışmaya
    başladı; eşleşme onlara tıklanması ve otomatik yanıt ACIKKEN bir aile
    ferdi/grup sohbetine ticari bot yanıtı gitmesi demek. Operatör bir adayı
    onayladığında (izin=1) o satır yeniden eşleşebilir.
    """
    baslik_rakam = _rakamlar(sohbet_basligi)
    baslik_duz = _duz_metin(sohbet_basligi).lower()
    for kayit in conn.execute(
        "SELECT id, isletme, telefon FROM esnaflar "
        "WHERE COALESCE(durum, '') <> ? OR COALESCE(izin, 0) = 1", ("ADAY",)
    ):
        tel = _rakamlar(kayit["telefon"])
        # En az 8 hane eşleşmeden "numara" sayılmaz: "Kafe 2023" gibi başlıklar
        # bir telefonun içindeki rastgele 4 haneyle yanlış eşleşmesin.
        if len(tel) >= 8 and len(baslik_rakam) >= 8 and (
            tel in baslik_rakam or baslik_rakam in tel
        ):
            return int(kayit["id"])
        ad = _duz_metin(kayit["isletme"] or "").lower().strip()
        if len(ad) >= 4 and ad in baslik_duz:
            return int(kayit["id"])
    return None


def _gelen_mesajlari_oku():
    """Bir yoklama: okunmamış sohbetlere gir, son gelen mesajı kaydet.

    Dönen: işlenen yeni mesaj sayısı. Gönderim kapalı olsa da çalışır (salt
    okuma + kendi kaydımıza yazma). Otomatik yanıt varsayılan KAPALIDIR.
    """
    if not OTONOM_YAPI.gelen_mesaj_acik:
        return 0
    if not _oturum_gonderime_hazir():
        return 0
    conn = veritabani_baglan()
    try:
        sema_goc_uygula(conn)
        with SOHBET_KILIDI:
            surucu = whatsapp_driver
            try:
                kisiler = surucu.execute_script(_KISILER_JS) or []
            except (WebDriverException, JavascriptException) as hata:
                _log_motor(f"[GELEN] Kişi listesi okunamadı: {type(hata).__name__}")
                return 0
            # Yalnızca kayıtlı ESNAFA ait okunmamış sohbetlere girilir: aile/özel
            # sohbetlerin "okundu" işaretlenmesi veya içlerine tıklanması sözkonusu
            # değil. Eşleşmeyen başlıklar için hiçbir tıklama yapılmaz.
            hedefler = []
            eslesmeyenler = []
            okunmamis_sayisi = 0
            for kisis in kisiler:
                if int(kisis.get("okunmamis") or 0) <= 0:
                    continue
                okunmamis_sayisi += 1
                baslik = str(kisis.get("baslik") or "").strip()
                if not baslik:
                    continue
                esnaf_id = _esnaf_eslestir(conn, baslik)
                if esnaf_id is None:
                    eslesmeyenler.append(baslik)
                    continue
                hedefler.append((baslik, esnaf_id))
                if len(hedefler) >= OTONOM_YAPI.gelen_azami_sohbet:
                    break
            # Aynı liste her yoklamada tekrar loglanmasın: yalnızca değişince yaz.
            global _eslesmeyen_imza, _eslesen_imza
            anahtar = "|".join(sorted(eslesmeyenler))
            if anahtar != _eslesmeyen_imza:
                _eslesmeyen_imza = anahtar
                if eslesmeyenler:
                    _log_motor("[GELEN] Okunmamış ama kayıtlı esnaf olmayan sohbetler "
                               f"(dokunulmadı): {eslesmeyenler[:8]}")
            # Eşleşenler de loglanır: yanlış bir eşleşme (aday adıyla çakışan bir
            # grup/kişisel sohbet) sessizce tıklanıp otomatik yanıt gidemesin.
            eslesen_imza = "|".join(f"#{esnaf_id}:{baslik}" for baslik, esnaf_id in hedefler)
            if eslesen_imza != _eslesen_imza:
                _eslesen_imza = eslesen_imza
                if hedefler:
                    _log_motor(f"[GELEN] Esnaf eşleşen okunmamış sohbetler: {hedefler[:5]}")
            # DOM okumasının gerçekten çalıştığını kanıtlamak için sayaç:
            # 'kisiler=0' seçicinin bozulduğu anlamına gelir, sessizce
            # 'yanıt yok' sanılmasın.
            with otonom_kilit:
                gelen_son_rapor.update({
                    "kisiler": len(kisiler), "okunmamis": okunmamis_sayisi,
                    "esnaf_sohbet": len(hedefler),
                    "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
            if not kisiler:
                _log_motor("[GELEN] UYARI: kişi listesi boş döndü — WhatsApp Web "
                           "seçicileri değişmiş olabilir, okuyucu çalışmıyor.")
            islenen = 0
            for baslik, esnaf_id in hedefler:
                try:
                    if not surucu.execute_script(_SOHBET_ROW_TIKLA_JS, baslik):
                        continue
                    time.sleep(2.0)
                    balonlar = surucu.execute_script(_GELEN_BALONLAR_JS) or []
                except (WebDriverException, JavascriptException):
                    continue
                if not balonlar:
                    continue
                son_metin = str(balonlar[-1]).strip()
                imza_degeri = _mesaj_imzasi(baslik, son_metin)
                durum = gelen_mesaj_kaydet(
                    conn, esnaf_id, son_metin, imza_degeri, _mesaj_kaydet
                )
                if durum.get("yinelenen"):
                    continue
                islenen += 1
                _log_motor(f"[GELEN] Esnaf #{esnaf_id} ({baslik}): {son_metin[:120]}")
                if durum.get("opt_out"):
                    _log_motor(f"[GELEN] #{esnaf_id} OPT-OUT ('DUR/İPTAL'): "
                               f"gönderim listesi kapatıldı, kalıcı numara kara listesi: "
                               f"{bool(durum.get('kara_liste'))}. Otomatik yanıt GÖNDERİLMEDİ.")
                    continue
                if OTONOM_YAPI.otomatik_yanit_acik:
                    yanit = derya_otonom_yanitla(son_metin, baslik)
                    _log_motor(f"[GELEN] Otomatik yanıt denemesi #{esnaf_id}: {yanit[:80]}")
                    _otomatik_yanit_gonder(conn, esnaf_id, yanit)
        return islenen
    finally:
        conn.close()


def _otomatik_yanit_gonder(conn, esnaf_id, yanit):
    """Yanıtı yalnızca teslim doğrulanırsa panele yazar (mevcut sözleşme)."""
    kayit = _esnaf_kayiti(conn, esnaf_id) or {}
    if not kayit.get("telefon"):
        _log_motor(f"[GELEN] #{esnaf_id} telefon kayıtlı değil; yanıt gönderilmedi.")
        return False
    if not gercek_whatsapp_mesaj_gonder(kayit["telefon"], yanit, kayit.get("isletme")):
        return False
    _mesaj_kaydet(conn, esnaf_id, "DERYA", yanit)
    return True


def gelen_mesaj_dongusu():
    _log_motor(
        f"[GELEN] Mesaj okuyucu başlatıldı | yoklama={OTONOM_YAPI.gelen_yoklama_sn}sn "
        f"azami_sohbet={OTONOM_YAPI.gelen_azami_sohbet} "
        f"otomatik_yanit={'ACIK' if OTONOM_YAPI.otomatik_yanit_acik else 'KAPALI'}"
    )
    while True:
        try:
            _gelen_mesajlari_oku()
        except Exception as hata:
            _log_motor(f"[GELEN HATA] {type(hata).__name__}: {hata}")
        time.sleep(OTONOM_YAPI.gelen_yoklama_sn)


def aday_tarama_isleyicisi():
    """Aday havuzu döngüsü: toplar, yazar, uyur. Bu thread'in gönderimle işi yok."""
    aday_tarama_dongusu(veritabani_baglan, ADAY_YAPI, _log_motor)


@app.route("/api/aday_havuzu", methods=["GET"])
def aday_havuzu_gor():
    """Panel: havuzdaki adaylar + son tarama özeti. Salt-okur, 500 dönmez."""
    govde = {"toplam": 0, "kayitlar": []}
    try:
        conn = veritabani_baglan()
    except sqlite3.Error as hata:
        _log(f"aday_havuzu baglanti hatasi: {hata}")
        return jsonify({**govde, "hata": str(hata)[:120]})
    try:
        return jsonify(havuz_durumu(conn))
    except sqlite3.Error as hata:
        _log(f"aday_havuzu sorgu hatasi: {hata}")
        return jsonify({**govde, "hata": str(hata)[:120]})
    finally:
        conn.close()


@app.route("/api/izin_ver", methods=["POST"])
def izin_ver_ucu():
    """Panele basılan ONAY/RET düğmesinin tek yazma yolu -> esnaflar.izin.

    Motor yalnızca izin=1 satırları seçer; bu uç olmadan aday havuzu hiçbir
    zaman gönderim sırasına dönüşmez. API kimlik doğrulamasız ve yalnız SSH
    tünelinden erişilebilir olduğundan karar log'a yazılır (numara değil, id).
    """
    data = request.json or {}
    try:
        esnaf_id = int(data.get("id"))
    except (TypeError, ValueError):
        return jsonify({"status": "hata", "mesaj": "id zorunlu (sayı olmalı)"}), 400
    conn = veritabani_baglan()
    try:
        sema_goc_uygula(conn)
        sonuc = _motor_izin_ver(conn, esnaf_id, data.get("izin", 1),
                                kaynak=str(data.get("kaynak") or "panel"))
    finally:
        conn.close()
    if not sonuc.get("ok"):
        sebep = sonuc.get("sebep")
        _log(f"⛔ İzin reddi #{esnaf_id}: {sebep}")
        kod = 404 if sebep == "kayit-yok" else 409
        return jsonify({"status": "hata", "mesaj": sebep, "esnaf_id": esnaf_id}), kod
    uyari = f" · {sonuc['uyari']}" if sonuc.get("uyari") else ""
    _log(f"✅ İzin #{esnaf_id}: {sonuc.get('onceki')} -> izin={sonuc['izin']}{uyari}")
    return jsonify({"status": "basarili", **sonuc})


@app.route("/api/otonom_tani", methods=["GET"])
def otonom_tani():
    """Salt-okunur DOM teşhisi: ilk satırlarda okunmamış rozeti NEYLE bulunuyor?

    WhatsApp Web arayüzü güncellendiğinde seçiciler sessizce ölür; bu uç,
    'okunmamis=0'ın gerçekten 'yanıt yok' mu yoksa 'seçici bozuldu' mu olduğunu
    ayırt etmek içindir. Hiçbir sohbete tıklamaz, hiçbir şey yazmaz.
    """
    js = (
        _SATIRLAR_JS + _SATIR_BASLIGI_JS + _SATIR_OKUNMAMIS_JS +
        "var out = [];"
        "for (var i = 0; i < satirlar.length && out.length < 12; i++) {"
        "  var d = satirlar[i];"
        "  out.push({baslik: baslikAl(d), okunmamis: okunmamisAl(d), "
        "    title_mi: !!d.querySelector('span[dir=\"auto\"][title]'), "
        "    ham: String(d.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 70)});"
        "}"
        "return {toplam_satir: satirlar.length, ornekler: out};"
    )
    if not _oturum_gonderime_hazir():
        return jsonify({"basarili": False, "sebep": "oturum hazir degil"}), 503
    with SOHBET_KILIDI:
        try:
            satirlar = whatsapp_driver.execute_script(js)
        except (WebDriverException, JavascriptException) as hata:
            return jsonify({"basarili": False, "sebep": f"{type(hata).__name__}: {hata}"}), 500
    return jsonify({"basarili": True, "satirlar": satirlar,
                    "son_kullanilan_rapor": dict(gelen_son_rapor)})


@app.route("/api/otonom_durum", methods=["GET"])
def otonom_durum():
    with otonom_kilit:
        rapor = dict(otonom_son_rapor)
        gelen = dict(gelen_son_rapor)
    return jsonify({
        "sozlesme": OTONOM_YAPI.sozler(),
        "gonderim_acik": OTONOM_YAPI.gonderim_acik,
        "motor_ishalinde": otonom_thread.is_alive(),
        "gelen_okuyucu_ishalinde": gelen_thread.is_alive(),
        "son_rapor": rapor,
        "gelen_son_rapor": gelen,
    })


# ============================================================
# 8) BAŞLATMA
# ============================================================
def _arka_plan_baslat():
    # Werkzeug reloader açıksa modül İKİ KEZ import edilir; ikinci Chrome aynı
    # profili kilitleyip eski (yanlış) hesabı geri getirirdi. Aşağıdaki guard,
    # reloader kazara açılırsa bile tek Chrome kalmasını garanti eder.
    reloader_acik = _env_bayrak("WHATSAPP_RELOADER", "0")
    reloader_cocuk_surec = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    if reloader_acik and not reloader_cocuk_surec:
        _log("Reloader'ın ana süreciyim: Chrome başlatılmıyor "
             "(çift Chrome / profil kilidi önlendi).")
        return
    Thread(target=whatsapp_baslat, kwargs={"qr_bekle": True}, daemon=True).start()


if OTOMATIK_BASLAT:
    _arka_plan_baslat()

# Motor KAPALI başlatılabilir (OTONOM_GONDERIM=0): döngü yine döner, raporu
# loglar ama hiçbir mesaja/veritabanı durumuna dokunmaz.
otonom_thread = Thread(target=otonom_hedef_isleyici, daemon=True, name="otonom-gonderim")
otonom_thread.start()
gelen_thread = Thread(target=gelen_mesaj_dongusu, daemon=True, name="otonom-gelen-mesaj")
gelen_thread.start()
# ADAY_TARAMA=0 -> döngü yalnızca "KAPALI" loglayıp çıkar (ağdan hiç okumaz).
aday_thread = Thread(target=aday_tarama_isleyicisi, daemon=True, name="aday-havuzu")
aday_thread.start()


if __name__ == "__main__":
    print("🚀 TRM Eko Sistem Asistanı Derya API Servisi Başlatılıyor...")
    print(f"   Ticari hat filtresi : {TICARI_HAT_ULUSLARARASI}")
    print(f"   Profil modu         : {PROFIL_MODU}  ({PROFIL_ANA_DIZIN})")
    print(f"   Sert temizlik modu  : {'ACIK' if SERT_MODEMLEME else 'KAPALI (hedefli)'}")
    print(f"   Headless Chrome     : {'ACIK' if HEADLESS_MODE else 'KAPALI (pencere açık)'}")
    print(f"   QR bekleme          : {QR_BEKLEME_SN} sn")
    print(f"   Otonom motor        : {OTONOM_YAPI.sozler()}")
    print(f"   Aday havuzu         : {ADAY_YAPI.sozler()} (izin=0 -> gonderim sirasi degil)")
    # debug/use_reloader=TRUE iken çift Chrome açılır -> profil kilidi. KAPALI.
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
