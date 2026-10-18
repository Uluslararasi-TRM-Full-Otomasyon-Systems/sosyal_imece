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
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from threading import Thread, Lock
from datetime import datetime, timedelta

import atexit
import json
import os
import random
import re
import shutil
import socket
import sqlite3
import string
import subprocess
import sys
import time
import urllib.parse

from derya_cevaplayici import derya_otonom_yanitla


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


def _log(mesaj):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [WHATSAPP] {mesaj}", flush=True)


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


def _hedef_surezleri_olddur():
    """
    Yalnızca command line'ında BİZİM profil dizini geçen chrome.exe süreçlerini
    öldürür. Kullanıcının kendi açtığı Chrome pencerelerine dokunmaz.
    """
    if os.name != "nt":
        return 0

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
    yedek = ESKI_PROFIL_DIZIN.rstrip("\\") + "_ESKI_ARTIK_KULLANILMIYOR"
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

    _komut_calistir(["taskkill", "/F", "/IM", "chromedriver.exe"])

    if SERT_MODEMLEME:
        # KULLANICI BİLEREK AÇTI: tüm Chrome'lar kapanır.
        _komut_calistir(["taskkill", "/F", "/IM", "chrome.exe"])
        _log("SERT MOD: tüm chrome.exe süreçleri sonlandırıldı.")
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
    return options


def _surucu_olustur(options):
    """Selenium Manager (4.6+) önce denenir; olmazsa webdriver_manager yedeği."""
    try:
        return webdriver.Chrome(options=options)
    except Exception as ilk_hata:
        _log(f"Selenium Manager sürücüyü çözemedi ({ilk_hata}); webdriver_manager deneniyor...")
        from selenium.webdriver.chrome.service import Service as ChromeService
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


# ============================================================
# 5) MESAJ GÖNDERME
# ============================================================
def _gonder_dugmesini_tikla(sürücü):
    js = (
        "const ikon = document.querySelector('span[data-icon=\"send\"], "
        "span[data-icon=\"send-alt-with-text\"], span[data-icon=\"ptt-footer\"]');"
        "if (!ikon) return false;"
        "const dugme = ikon.closest('button,[role=\"button\"]') || ikon;"
        "dugme.click(); return true;"
    )
    try:
        return bool(sürücü.execute_script(js))
    except (WebDriverException, JavascriptException):
        return False


def _composer_metni(sürücü):
    """None -> composer yok; '' -> composer var ama boş; aksi -> ön-doldurulmuş metin."""
    js = (
        "var k = document.querySelector(\"div[contenteditable='true'][data-tab='1']\")"
        " || document.querySelector(\"div[contenteditable='true']\");"
        "return k ? String(k.innerText || '').trim() : null;"
    )
    try:
        return sürücü.execute_script(js)
    except (WebDriverException, JavascriptException):
        return None


def _metni_yaz(sürücü, mesaj):
    js = (
        "var k = document.querySelector(\"div[contenteditable='true'][data-tab='1']\")"
        " || document.querySelector(\"div[contenteditable='true']\");"
        "if (!k) return false;"
        "k.focus();"
        "var ok = document.execCommand('insertText', false, arguments[0]);"
        "if (!ok) { k.textContent = arguments[0];"
        "  k.dispatchEvent(new InputEvent('input', {bubbles: true, data: arguments[0], inputType: 'insertText'})); }"
        "return true;"
    )
    try:
        return bool(sürücü.execute_script(js, str(mesaj)))
    except (WebDriverException, JavascriptException):
        return False


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
            if not metin and not _metni_yaz(sürücü, mesaj):
                return "bekleniyor"
            return "hazir"
        if _devam_dugmesini_tikla(sürücü):
            time.sleep(1.5)
            continue
        if _qr_bekliyor_mu(sürücü):
            return "qr"
        time.sleep(1.5)
    return "bekleniyor"


def gercek_whatsapp_mesaj_gonder(telefon, mesaj):
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
        encoded_msg = urllib.parse.quote(str(mesaj))
        formatted_url = (
            f"https://web.whatsapp.com/send?phone={temiz_tel}&text={encoded_msg}"
        )
        whatsapp_driver.get(formatted_url)

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
                kutu.send_keys("\n")
                gonderildi = True
            except (TimeoutException, WebDriverException):
                pass

        if not gonderildi:
            _hata_ekrani_al("gonder_dugmesi_bulunamadi")
            _log("❌ Gönder düğmesi bulunamadı (WhatsApp arayüzü değişmiş olabilir).")
            return False

        time.sleep(1.0)
        _log(f"📤 Mesaj gönderildi -> {temiz_tel} (hat {whatsapp_state['giris_hat']})")
        return True
    except Exception as hata:
        _hata_ekrani_al("gonderim_hatasi")
        _log(f"❌ GÖNDERİM HATASI: {hata}")
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
        rows = conn.execute(
            "SELECT id, isletme, telefon, kod, durum FROM esnaflar ORDER BY id DESC"
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


@app.route("/api/mesaj_gonder", methods=["POST"])
def mesaj_gonder():
    data = request.json or {}
    esnaf_id = data.get("esnaf_id")
    esnaf_mesaj = data.get("mesaj")

    if not esnaf_id or not esnaf_mesaj:
        return jsonify({"status": "hata", "mesaj": "Eksik parametre"}), 400

    conn = veritabani_baglan()
    esnaf = conn.execute("SELECT isletme, telefon FROM esnaflar WHERE id = ?", (esnaf_id,)).fetchone()
    isletme_adi = esnaf["isletme"] if esnaf else "İşletme"
    telefon = esnaf["telefon"] if esnaf else ""

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
        "INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'ESNAF', ?)",
        (esnaf_id, esnaf_mesaj),
    )
    conn.commit()

    derya_cevabi = derya_otonom_yanitla(esnaf_mesaj, isletme_adi)

    conn.execute(
        "INSERT INTO mesajlar (esnaf_id, gonderen, mesaj) VALUES (?, 'DERYA', ?)",
        (esnaf_id, derya_cevabi),
    )
    conn.commit()
    conn.close()

    gonderim = None
    if telefon:
        gonderim = gercek_whatsapp_mesaj_gonder(telefon, derya_cevabi)

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
    with driver_lock:
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
# 7) OTONOM HEDEF DÖNGÜSÜ
# ============================================================
def otonom_hedef_isleyici(hedef_sayi=20):
    print(f"🚀 [OTONOM MOTOR] Arka plan döngüsü başlatıldı. Hedef: {hedef_sayi} Gerçek Firma.")
    while True:
        conn = None
        try:
            conn = veritabani_baglan()
            cursor = conn.execute("SELECT COUNT(*) as sayi FROM esnaflar")
            row = cursor.fetchone()
            mevcut_sayi = row["sayi"] if row else 0

            if mevcut_sayi < hedef_sayi:
                pass
        except Exception as e:
            print(f"⚠️ [OTONOM HATA]: {e}")
        finally:
            if conn is not None:
                conn.close()

        time.sleep(30)


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

otonom_thread = Thread(target=otonom_hedef_isleyici, args=(20,), daemon=True)
otonom_thread.start()


if __name__ == "__main__":
    print("🚀 TRM Eko Sistem Asistanı Derya API Servisi Başlatılıyor...")
    print(f"   Ticari hat filtresi : {TICARI_HAT_ULUSLARARASI}")
    print(f"   Profil modu         : {PROFIL_MODU}  ({PROFIL_ANA_DIZIN})")
    print(f"   Sert temizlik modu  : {'ACIK' if SERT_MODEMLEME else 'KAPALI (hedefli)'}")
    print(f"   QR bekleme          : {QR_BEKLEME_SN} sn")
    # debug/use_reloader=TRUE iken çift Chrome açılır -> profil kilidi. KAPALI.
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
