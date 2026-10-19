#!/usr/bin/env bash
# ============================================================================
# TRM Derya API - Linux VPS kurulum betigi (Ubuntu Server 22.04 LTS / Debian 12)
#
# Tek komut:  sudo bash deploy_vps.sh
#
# Ne yapar:
#   1) apt paketleri        : python3/pip/venv, sqlite3, unzip, Turkce fontlar, tar
#   2) google-chrome-stable : Google'in resmi apt deposundan
#   3) chromedriver         : KURULU Chrome'un buyuk surumuyle birebir eslesen binary
#   4) xvfb (opsiyonel)     : headless yeni WhatsApp akisini bozarsa pencere taklidi
#   5) sanal ortam          : $TRM_DIR/venv + api_server_2.py icin asgari paketler
#   6) servis kullanicisi   : login'siz "trm" hesab + profil/DB sahipligi
#   7) systemd birimi       : /etc/systemd/system/trm-derya.service (yol uyarlamali)
#   8) /etc/trm-derya.env   : ANAHTAR ICERMEYEN bos sablon (anahtarlar kullaniciya ait)
#
# Ne YAPMAZ:
#   - WhatsApp otomasyonunu KENDILIGINE baslatmaz (unit dosyasi sadece hazirlanir).
#     7/24 servisi sen hazir oldugunda kendin acarsin:  --servis  bayragi gerekir.
#   - API anahtari yazmaz/kopyalamaz. Veritabani ve WhatsApp oturumu tasima isi
#     VPS_TASIMA_REHBERI.md'de anlatilir.
#
# Bayraklar:
#   --dir DIZIN     Kodun/venv'in/DB'nin olacagi dizin (vars: betigin kendi dizini)
#   --profil DIZIN  WhatsApp Chrome profil ANA dizini
#                   (vars: /var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean)
#   --user KULL     Servis kullanicisi (vars: trm)
#   --port P        API portu (vars: 5000) - api_server_2.py koddaki app.run satiriyla
#                   dinler; bu bayrak saglik kontrolu ve unit notu icindir
#   --no-xvfb       xvfb kurma
#   --servis        unit'i etkinlestir + hemen baslat (7/24 moduna gec)
#   --dry-run       Hicbir sey degistirmez; yapilacaklari basar (root gerektirmez)
#
# Not: Chrome'un GPU/sandbox bayraklari (--no-sandbox, --disable-dev-shm-usage) ve
# HEADLESS_MODE kontrolu api_server_2.py icinde zaten yapili; bu betik onlari tekrarlamaz.
# ============================================================================
set -Eeuo pipefail

KOD_KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRM_DIR="${KOD_KOK}"
TRM_USER="trm"
API_PORT="5000"
WHATSAPP_PROFIL=""
KUR_XVFB=1
SERVIS_AYAKLA=0
KURUY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)    TRM_DIR="${2:?--dir bir dizin ister}"; shift 2 ;;
    --profil) WHATSAPP_PROFIL="${2:?--profil bir dizin ister}"; shift 2 ;;
    --user)   TRM_USER="${2:?--user bir kullanici adi ister}"; shift 2 ;;
    --port)   API_PORT="${2:?--port bir sayi ister}"; shift 2 ;;
    --no-xvfb) KUR_XVFB=0; shift ;;
    --servis) SERVIS_AYAKLA=1; shift ;;
    --dry-run) KURUY=1; shift ;;
    -h|--help) awk '/^#/{print} !/^#/{exit}' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "HATA: taninmayan bayrak: $1 (yardim: --help)" >&2; exit 2 ;;
  esac
done

if ! [[ "$API_PORT" =~ ^[0-9]+$ ]] || [ "$API_PORT" -lt 1 ] || [ "$API_PORT" -gt 65535 ]; then
  echo "HATA: --port gecersiz: $API_PORT" >&2; exit 2
fi
if [ ! -f "${TRM_DIR}/api_server_2.py" ] && [ $KURUY -eq 0 ]; then
  # Betik kodun icinde calistirilmali; aksi halde neyi calistiracagimizi bilemeyiz.
  echo "HATA: ${TRM_DIR}/api_server_2.py yok. Once projeyi sunucuya kopyala" >&2
  echo "      (bkz. VPS_TASIMA_REHBERI.md bolum 2), sonra betigi orada calistir." >&2
  exit 3
fi
if [ $KURUY -eq 0 ] && [ "$(id -u)" != "0" ]; then
  echo "HATA: betik root/sudo ile calistirilmali:  sudo bash deploy_vps.sh" >&2
  exit 4
fi

# Profil dizini Linux karsiligi. "TRM_WhatsApp" deseni ZORUNLU: api_server_2.py'nin
# kalinti temizligi yalnizca komut satirinda bu deseni gecen Chrome sureclerini oldurur;
# desen dusurse hedefli temizlik kendini koruma olarak tamamen kapatir.
# Kod agacindan AYRI tutulur: rsync --delete / yeniden derleme oturumu silmesin.
: "${WHATSAPP_PROFIL:=/var/lib/trm-derya/whatsapp/TRM_WhatsApp_Session_Clean}"
case "$WHATSAPP_PROFIL" in
  *TRM_WhatsApp*) : ;;
  *) echo "HATA: --profil icinde 'TRM_WhatsApp' gecmeli (guvenli temizlik deseni): $WHATSAPP_PROFIL" >&2
     exit 6 ;;
esac
ENV_FILE="/etc/trm-derya.env"
UNIT="/etc/systemd/system/trm-derya.service"

if command -v apt-get >/dev/null 2>&1; then
  PAKET="apt"
elif command -v dnf >/dev/null 2>&1; then
  PAKET="dnf"
else
  echo "HATA: apt-get ya da dnf bulunamadi. Bu betik Debian/Ubuntu/Debian-benzeri icindir." >&2
  exit 5
fi

adim()  { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }
bilgi() { printf '    %s\n' "$1"; }
uyari() { printf '    \033[1;33mUYARI:\033[0m %s\n' "$1"; }
yap() {
  if [ $KURUY -eq 1 ]; then
    echo "    [dry-run] $*"
  else
    "$@"
  fi
}

export DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------------------
echo "============================================================================"
echo " TRM Derya API - VPS kurulumu"
echo "   Kod dizini      : ${TRM_DIR}"
echo "   Servis kullanicisi: ${TRM_USER}"
echo "   API portu       : ${API_PORT}"
echo "   WhatsApp profili: ${WHATSAPP_PROFIL}"
echo "   Yontem          : $([ $KURUY -eq 1 ] && echo 'DRY-RUN (degisiklik yok)' || echo 'KURULUM')"
echo "============================================================================"

# ---------------------------------------------------------------------------
adim "1/8  Temel apt paketleri (python3, pip, venv, sqlite3, unzip, fontlar)"
if [ "$PAKET" = "apt" ]; then
  yap apt-get update -y
  yap apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv python3-setuptools \
      sqlite3 unzip curl wget ca-certificates gnupg git procps \
      fonts-liberation fonts-dejavu-core fontconfig
  if [ $KUR_XVFB -eq 1 ]; then
    yap apt-get install -y --no-install-recommends xvfb x11-utils
  fi
else
  yap dnf install -y python3 python3-pip sqlite unzip curl tar procps-ng google-noto-sans-fonts
  if [ $KUR_XVFB -eq 1 ]; then
    yap dnf install -y xorg-x11-server-Xvfb
  fi
fi

# ---------------------------------------------------------------------------
adim "2/8  google-chrome-stable (Google resmi apt deposu)"
if command -v google-chrome-stable >/dev/null 2>&1; then
  bilgi "Kurulu: $(google-chrome-stable --version)"
elif [ "$PAKET" = "apt" ]; then
  if [ $KURUY -eq 0 ]; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
    chmod 0644 /etc/apt/keyrings/google-chrome.gpg
    echo "deb [arch=amd64,arm64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list
    apt-get update -y
    apt-get install -y google-chrome-stable
  else
    echo "    [dry-run] google-chrome-stable kurulumu (Google apt deposu)"
  fi
else
  uyari "dnf tabaninda Chrome icin lutfen .deb yerine .rpm ile kurulum yap."
fi

if command -v google-chrome-stable >/dev/null 2>&1; then
  Chrome_Surum="$(google-chrome-stable --version | awk '{print $NF}')"
else
  Chrome_Surum="$(google-chrome --version 2>/dev/null | awk '{print $NF}' || true)"
fi

# ---------------------------------------------------------------------------
adim "3/8  chromedriver (kurulu Chrome'un BUYUK surumuyle eslesmeli)"
MIMARI="$(dpkg --print-architecture 2>/dev/null || uname -m)"
case "$MIMARI" in
  amd64|x86_64) CD_MIMARI="linux64" ;;
  arm64|aarch64) CD_MIMARI="linux-arm64" ;;
  *) CD_MIMARI="linux64"; uyari "Bilinmeyen mimari '$MIMARI', linux64 denenecek." ;;
esac

CD_GEREKLIYOR=1
if command -v chromedriver >/dev/null 2>&1; then
  bilgi "Kurulu: $(chromedriver --version | head -1)"
  CD_ANA="$(chromedriver --version | awk '/ChromeDriver/{print $2}' | cut -d. -f1)"
  if [ -z "${Chrome_Surum:-}" ] || [ "$CD_ANA" = "$(echo "$Chrome_Surum" | cut -d. -f1)" ]; then
    CD_GEREKLIYOR=0
  else
    uyari "chromedriver ($CD_ANA) Chrome $(echo "$Chrome_Surum" | cut -d. -f1) ile eslesmiyor;"
    uyari "dogru surum /usr/local/bin'e kurulur (PATH'te /usr/bin'den ONCE gelir, eski binary silinmez)."
  fi
fi
if [ $CD_GEREKLIYOR -eq 1 ]; then
  if [ -z "${Chrome_Surum:-}" ]; then
    uyari "Chrome bulunamadi: chromedriver atlandi. api_server_2.py calisma aninda"
    uyari "Selenium Manager / webdriver-manager ile otomatik indirmeyi dener."
  elif [ $KURUY -eq 0 ]; then
    CD_SERI="$(echo "$Chrome_Surum" | cut -d. -f1)"
    tam_surum="$(curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CD_SERI}" || true)"
    if [ -z "$tam_surum" ]; then
      tam_surum="$(curl -fsSL "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json" \
                   | grep -o '"version": *"[^"]*"' | head -1 | cut -d'"' -f4 || true)"
    fi
    if [ -n "$tam_surum" ]; then
      url="https://storage.googleapis.com/chrome-for-testing-public/${tam_surum}/${CD_MIMARI}/chromedriver-${CD_MIMARI}.zip"
      bilgi "Indiriliyor: $url"
      curl -fsSL -o /tmp/chromedriver.zip "$url"
      unzip -o -q /tmp/chromedriver.zip -d /tmp/chromedriver
      install -m 0755 "/tmp/chromedriver/chromedriver-${CD_MIMARI}/chromedriver" /usr/local/bin/chromedriver
      rm -rf /tmp/chromedriver /tmp/chromedriver.zip
    else
      uyari "Chrome for Testing uctan surum numarasi alinamadi (ag/kota). Selenium Manager"
      uyari "devreye girecek; ama bu durumda chromedriver indirmesi calisma aninda olur."
    fi
  else
    echo "    [dry-run] chromedriver-${CD_MIMARI}.zip indirir /usr/local/bin/chromedriver"
  fi
fi

# ---------------------------------------------------------------------------
adim "4/8  Servis kullanicisi ve dizinler"
if [ $KURUY -eq 0 ]; then
  if ! id -u "$TRM_USER" >/dev/null 2>&1; then
    # Sistem hesabi + nologin kabugu: bu kullaniciya SSH ile girilemez,
    # yalnizca servis altinda Chrome calistirir.
    NOLOGIN_BIN="$(command -v nologin 2>/dev/null || echo /usr/sbin/nologin)"
    useradd --system --home-dir "$TRM_DIR" --shell "$NOLOGIN_BIN" "$TRM_USER" || \
      uyari "kullanici olusturulamadi; mevcut '$TRM_USER' kullanilacak."
  fi
  mkdir -p "$(dirname "$WHATSAPP_PROFIL")" "$WHATSAPP_PROFIL" \
           "$TRM_DIR/whatsapp_hata_kayitlari" "$TRM_DIR/logs"
  # Oturum klasori 700: icinde WhatsApp Web'in IndexedDB kimlik kaydi duruyor.
  chmod 700 "$WHATSAPP_PROFIL" 2>/dev/null || true
  if id -u "$TRM_USER" >/dev/null 2>&1; then
    chown -R "$TRM_USER:$TRM_USER" "$(dirname "$WHATSAPP_PROFIL")" 2>/dev/null \
      || chown -R "$TRM_USER" "$(dirname "$WHATSAPP_PROFIL")"
  fi
  bilgi "Kullanici: $TRM_USER (uid $(id -u "$TRM_USER" 2>/dev/null || echo '?'))"
  bilgi "Profil ana dizini: $WHATSAPP_PROFIL"
else
  echo "    [dry-run] useradd $TRM_USER + mkdir/chown $WHATSAPP_PROFIL"
fi

# ---------------------------------------------------------------------------
adim "5/8  Python sanal ortami + requirements_vps.txt"
# rsync/tar ile Windows'tan tasinan venv CALISMAZ: Scripts/ altindir, yollar C:\...
# Varsa silmiyoruz, adlandiriyoruz (geri alinabilir) ki pip bozuk bir ortamı onarmasina
# calismasin.
if [ -d "${TRM_DIR}/venv/Scripts" ] || grep -qiE '^[[:space:]]*home[[:space:]]*=[[:space:]]*[A-Za-z]:' "${TRM_DIR}/venv/pyvenv.cfg" 2>/dev/null; then
  if [ $KURUY -eq 0 ]; then
    mv "${TRM_DIR}/venv" "${TRM_DIR}/venv_windows_artigi"
    uyari "Windows venv'i ${TRM_DIR}/venv_windows_artigi olarak adlandirildi; temiz Linux venv aciliyor."
  else
    echo "    [dry-run] Windows venv tespiti: venv -> venv_windows_artigi tasinir"
  fi
elif [ -d "${TRM_DIR}/venv" ]; then
  bilgi "Mevcut (Linux) venv yerinde yenilenecek: ${TRM_DIR}/venv"
fi
if [ $KURUY -eq 0 ]; then
  python3 -m venv "${TRM_DIR}/venv"
  "${TRM_DIR}/venv/bin/pip" install --upgrade pip setuptools wheel
  "${TRM_DIR}/venv/bin/pip" install -r "${TRM_DIR}/requirements_vps.txt"
  chown -R "$TRM_USER:$TRM_USER" "$TRM_DIR" 2>/dev/null || chown -R "$TRM_USER" "$TRM_DIR"
else
  echo "    [dry-run] python3 -m venv ${TRM_DIR}/venv && pip install -r requirements_vps.txt"
fi

# ---------------------------------------------------------------------------
adim "6/8  ${ENV_FILE} (bos sablon - ANAHTAR ICERMEZ)"
if [ $KURUY -eq 1 ]; then
  echo "    [dry-run] $ENV_FILE olusturulur (mevcutsa DOKUNULMAZ)"
elif [ -f "$ENV_FILE" ]; then
  bilgi "Zaten var, korunuyor: $ENV_FILE"
  if grep -q "WHATSAPP_PROFIL_DIZINI" "$ENV_FILE"; then
    bilgi "WHATSAPP_PROFIL_DIZINI zaten tanimli; unit'teki okunabilir-yol listesi:"
    bilgi "  $WHATSAPP_PROFIL  (unit bu dizine yazar; eslesmiyorsa --profil ile ver)"
    if ! grep -q "TRM_WhatsApp" "$ENV_FILE"; then
      uyari "WHATSAPP_PROFIL_DIZINI icinde 'TRM_WhatsApp' deseni YOK. api_server_2.py'nin"
      uyari "hedefli Chrome temizligi bu yuzden kendini kapatir; dizini orada birak."
    fi
  fi
else
  cat > "$ENV_FILE" <<ENVSHABLON
# TRM Derya API - systemd ortam dosyasi (systemd bunu kabuk degil, key=value okur)
# chmod 640 root:trm, cunku icinde API anahtarlari duracak.

# --- WhatsApp / Chrome ---
WHATSAPP_PROFIL_DIZINI=${WHATSAPP_PROFIL}
# Eski/kurulu- olmayan profilin Linux karsiligi (Windows'daki C:\TRM_WhatsApp_Session).
# Bos gecilirse api_server_2.py Windows varsayilanina duser ve temizlik adimi noop kalir.
WHATSAPP_ESKI_PROFIL_DIZINI=$(dirname "${WHATSAPP_PROFIL}")/TRM_WhatsApp_Session
WHATSAPP_PROFIL_MODU=kalici
WHATSAPP_OTOMATIK_BASLAT=1
WHATSAPP_BEKLENEN_TEL=905426235116
# Linux VPS'te ekran yoktur: headless Chrome.
HEADLESS_MODE=true
# Chrome/chromedriver yollari (bos birakilirsa PATH'ten bulunur).
CHROME_BINARY=
CHROMEDRIVER_PATH=

# --- Davranis ayarlari (bos/EKSIK = api_server_2.py varsayilani) ---
# WHATSAPP_QR_BEKLEME_SN=180
# WHATSAPP_CDP_PORT=9222
# Varsayilan KAPALI birak: toplu chrome oldurme sunucudaki diğer tarayicilari da vurur.
# WHATSAPP_SERT_MODEMLEME=0

# --- API anahtarlari ---
# ONCELIKLE GEREKLI DEGIL: api_server_2.py, derya_cevaplayici.py ve esnaf_sablonu.py
# hicbir API anahtari okumaz (Derya'nin yanitlari kural tabanli). Bu satirlar yalnizca
# aynı sunucuya tasinacak diger ekosistem modulleri (llm_client, orchestrator, ajanlar)
# icin duruyor. Anahtarlari REPO'DAN TASIMIYORUZ; gerekirse kullanici kendisi yazar.
# GEMINI_API_KEY=
# GROQ_API_KEY=
# TELEGRAM_BOT_TOKEN=
# CEO_API_KEY=
ENVSHABLON
  chmod 640 "$ENV_FILE"
  if id -u "$TRM_USER" >/dev/null 2>&1; then
    chown root:"$TRM_USER" "$ENV_FILE" 2>/dev/null || chown root "$ENV_FILE"
  fi
  uyari "$ENV_FILE olusturuldu. WhatsApp ayarlarini kontrol et:  sudo nano $ENV_FILE"
fi

# ---------------------------------------------------------------------------
adim "7/8  systemd birimi -> ${UNIT}"
if [ -f "${TRM_DIR}/trm-derya.service" ]; then
  if [ $KURUY -eq 0 ]; then
    sed -e "s|@TRM_DIR@|${TRM_DIR}|g" \
        -e "s|@TRM_USER@|${TRM_USER}|g" \
        -e "s|@API_PORT@|${API_PORT}|g" \
        -e "s|@PROFIL@|${WHATSAPP_PROFIL}|g" \
        "${TRM_DIR}/trm-derya.service" > "$UNIT"
    systemctl daemon-reload
    bilgi "Unit yazildi ve yollari uyarlandi: $UNIT"
    if [ $SERVIS_AYAKLA -eq 1 ]; then
      systemctl enable trm-derya.service
      systemctl start trm-derya.service
      bilgi "7/24 modu ACIK: trm-derya etkinlestirildi ve baslatildi."
    else
      bilgi "Servis BASLATILMADI. Hazir oldugunda:"
      bilgi "  sudo systemctl enable --now trm-derya.service"
      bilgi "  (enable = sunucu her yeniden baslatildiginda otomatik ayaaga kalkar)"
    fi
  else
    echo "    [dry-run] sed ile trm-derya.service kopyalanir: $UNIT"
    echo "    [dry-run] systemctl daemon-reload + $([ $SERVIS_AYAKLA -eq 1 ] && echo 'enable --now' || echo 'enable/baslatma')"
  fi
else
  uyari "${TRM_DIR}/trm-derya.service bulunamadi: systemd adimi atlandi."
fi

# ---------------------------------------------------------------------------
adim "8/8  Saglik kontrolu (kod degistirmeden, Chrome acmadan)"
test_komutu() {
  if [ $KURUY -eq 1 ]; then echo "    [dry-run] $*"; return 0; fi
  # Adim 8 yalnizca dogrulamadir: bir arac eksese kurulum BASARISIZ sayilmaz.
  "$@" || uyari "Dogrulama komutu basarisiz (kurulumu durdurmaz): $*"
}
bilgi "OS      : $( ( . /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-bilinmiyor}" ) || echo 'bilinmeyen dagitim' )"
test_komutu python3 --version
test_komutu sqlite3 --version
if [ -x "${TRM_DIR}/venv/bin/python" ]; then
  test_komutu "${TRM_DIR}/venv/bin/python" - <<'PYTEST'
import sqlite3, sys
print("    venv    : " + sys.version.split()[0] + "  (sqlite " + sqlite3.sqlite_version + ")")
for ad in ("flask", "flask_cors", "selenium"):
    try:
        m = __import__(ad)
        print("      OK  " + ad + " " + str(getattr(m, "__version__", "?")))
    except Exception as hata:
        print("      HATA " + ad + ": " + repr(hata))
try:
    import webdriver_manager; print("      OK  webdriver-manager (yedek sürücü indirici)")
except Exception:
    print("      not: webdriver-manager yok -> Selenium Manager denenir")
PYTEST
elif [ $KURUY -eq 0 ]; then
  uyari "venv Python'u yok: pip adimi basarisiz olabilir."
fi
if [ $KURUY -eq 0 ] && [ -f "${TRM_DIR}/api_server_2.py" ]; then
  # Tasinan kodun truncation/koruma hasarini bu noktada yakalar.
  test_komutu python3 -m py_compile "${TRM_DIR}/api_server_2.py" && bilgi "py_compile: api_server_2.py OK"
fi
if command -v google-chrome-stable >/dev/null 2>&1 && [ $KURUY -eq 0 ]; then
  bilgi "Chrome headless denemesi (en fazla 25 sn; WhatsApp'e gitmez, oturum profilini kullanmaz):"
  su -s /bin/bash "$TRM_USER" <<'HEADCHECK' || uyari "headless Chrome ACILAMADI: eksik apt bagimiligi ya da sandbox sorunu."
  tmpd="$(mktemp -d)"
  # data: URL'i bazi Chrome build'lerinde reddediliyor; yerel dosya her turlu acilir.
  printf '<title>trm-headless-ok</title>' > "$tmpd/t.html"
  timeout 25 google-chrome-stable --headless=new --no-sandbox --disable-dev-shm-usage \
      --user-data-dir="$tmpd" --dump-dom "file://$tmpd/t.html" 2>/dev/null | head -3 || echo HEADLESS_HATA
  rm -rf "$tmpd"
HEADCHECK
fi
if [ -f "$UNIT" ]; then
  test_komutu systemctl status trm-derya.service --no-pager 2>/dev/null || \
    bilgi "Unit kayitli ama servis henuz calistirilmadi."
fi

echo
echo "============================================================================"
echo " KURULUM BISTI."
echo
echo "  SIRADIM (VPS_TASIMA_REHBERI.md'de detayli):"
echo "   1) Windows'tan veritabanini ve WhatsApp oturum klasorunu tasimayi yap."
echo "      En azindan trm_veritabani.db -> ${TRM_DIR}/ ve"
echo "      C:\\TRM_WhatsApp_Session_Clean\\TRM_Main -> ${WHATSAPP_PROFIL}/TRM_Main"
echo "   2) sudo nano ${ENV_FILE}  -> profil yolu + WHATSAPP_BEKLENEN_TEL dogrula"
echo "      (api_server_2.py icin API anahtari GEREKMIYOR; bkz. rehber bolum 7)"
echo "   3) sudo chown -R ${TRM_USER}:${TRM_USER} ${TRM_DIR}"
echo "   4) sudo systemctl enable --now trm-derya.service   (7/24 modu)"
echo "   5) sudo journalctl -u trm-derya -f"
echo "   6) curl -s http://127.0.0.1:${API_PORT}/api/saglik"
echo
echo "   GUVENLIK: api_server_2.py 0.0.0.0 uzerinde dinler. Firewall kurmadan"
echo "   ${API_PORT} portunu Internet'e ACMA (ornek: sudo ufw deny ${API_PORT} / allow from sana)"
echo "   ya da ters vekil + TLS + kimlik dogrulama ekle. Bu API WhatsApp mesajlari gonderir."
echo "============================================================================"
