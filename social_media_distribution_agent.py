#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOCIAL MEDYA DAĞITIM AJANI (social_media_distribution_agent.py)
================================================================
Trend Ürünler Market + Sosyal İmece / UTEYKDER projelerini
arka planda tarayıp, çapraz platformlarda (Telegram / WhatsApp /
Facebook / Instagram / TikTok) otonom paylaşım yapan servis.

MODÜLLER:
    1. ContentScanner    : İçerik tarayıcı + üretici (JSON/REST)
    2. MediaFactory      : gTTS + pydub/ffmpeg ses/video iskeleti
    3. CrossPostDispatcher: Çapraz platform dağıtıcı döngüsü
    4. Reporter          : Merkezî (Telegram bot + JSON log) raporlama
    5. run_social_agent(): Hızlı test / ana giriş fonksiyonu
"""

from __future__ import annotations

import os
import sys
import json
import time
import uuid
import logging
import hashlib
import random
import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests  # type: ignore
import config

# =====================================================================
# 0. GENEL AYARLAR & KONUM
# =====================================================================

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs_social"
MEDIA_DIR = ROOT / "media_out"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"social_agent_{datetime.now().strftime('%Y%m%d')}.log"
DIST_LOG_JSON = ROOT / "sosyal_medya_tanitim_loglari.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("SMD-Agent")


# =====================================================================
# 0b. ENV. DEGISKENLERI & ANAHTARLAR (Harici config / sistem env.)
# =====================================================================

def _env(name: str, default: str = "") -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        kf = ROOT / "api_keys.json"
        if kf.exists():
            with open(kf, "r", encoding="utf-8") as f:
                obj = json.load(f)
            for v in obj.values():
                if isinstance(v, dict) and v.get("name") == name:
                    return ""  # salt stub, gerçek projeye özel eşleme
    except Exception:
        pass
    return default


# Config'den sosyal medya hesap bilgilerini al
social_config = config._cfg.get("social_media", {})
social_accounts = social_config.get("accounts", {})

# Telegram
TELEGRAM_BOT_TOKEN = social_accounts.get("telegram", {}).get("bot_token", _env("TELEGRAM_BOT_TOKEN", ""))
TELEGRAM_BOT_USERNAME = social_accounts.get("telegram", {}).get("bot_username", "@TrendUrunlerMarket_Bot")
TELEGRAM_REPORT_CHAT_ID = _env("TELEGRAM_REPORT_CHAT_ID", "")
TELEGRAM_TARGET_CHANNEL_USERNAME = _env("TELEGRAM_TARGET_CHANNEL", "lanalisovets")

# WhatsApp
WHATSAPP_PHONE = social_accounts.get("whatsapp", {}).get("phone", "+905426235116")
WHATSAPP_API_TOKEN = _env("WHATSAPP_API_TOKEN", "")
WHATSAPP_BROADCAST_NUMBERS = [
    n.strip() for n in _env("WHATSAPP_BROADCAST_NUMBERS", "").split(",") if n.strip()
]

# Instagram
INSTAGRAM_USERNAME = social_accounts.get("instagram", {}).get("username", "trendurunlermarket@gmail.com")
INSTAGRAM_PASSWORD = social_accounts.get("instagram", {}).get("password", "")
INSTAGRAM_ACCESS_TOKEN = _env("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_BUSINESS_ACCOUNT_ID = _env("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

# TikTok
TIKTOK_USERNAME = social_accounts.get("tiktok", {}).get("username", "trendurunlermarket@gmail.com")
TIKTOK_PASSWORD = social_accounts.get("tiktok", {}).get("password", "")
TIKTOK_ACCESS_TOKEN = _env("TIKTOK_ACCESS_TOKEN", "")

# YouTube Shorts
YOUTUBE_CHANNEL_NAME = social_accounts.get("youtube_shorts", {}).get("channel_name", "Trend Ürünler Market")
YOUTUBE_EMAIL = social_accounts.get("youtube_shorts", {}).get("email", "trendurunlermarket@gmail.com")
YOUTUBE_PASSWORD = social_accounts.get("youtube_shorts", {}).get("password", "")

# Facebook
FACEBOOK_EMAIL = social_accounts.get("facebook", {}).get("email", "trendurunlermarket@gmail.com")
FACEBOOK_PASSWORD = social_accounts.get("facebook", {}).get("password", "")
FACEBOOK_ACCESS_TOKEN = _env("FACEBOOK_ACCESS_TOKEN", "")
FACEBOOK_PAGE_ID = _env("FACEBOOK_PAGE_ID", "")

# TRM API
TRM_API_URL = _env("TRM_API_URL", "https://api.trendurunlermarket.com/v1")
TRM_API_KEY = _env("TRM_API_KEY", "TRM_SECURE_TOKEN_2026")

DEFAULT_POST_INTERVAL_SEC = 60 * 30  # 30 dk.

log.info(f"[CONFIG] Sosyal medya hesapları yüklendi:")
log.info(f"  Telegram: {TELEGRAM_BOT_USERNAME}")
log.info(f"  WhatsApp: {WHATSAPP_PHONE}")
log.info(f"  Instagram: {INSTAGRAM_USERNAME}")
log.info(f"  TikTok: {TIKTOK_USERNAME}")
log.info(f"  YouTube: {YOUTUBE_CHANNEL_NAME}")
log.info(f"  Facebook: {FACEBOOK_EMAIL}")


# =====================================================================
# 1. VERİ SINIFLARI
# =====================================================================

@dataclass
class PostItem:
    """Platforma gönderilecek tek bir sosyal medya içeriği."""
    item_id: str
    content_type: str          # "product" | "uteykder_duyuru" | "imece_duyuru"
    title: str
    body: str
    hashtags: List[str] = field(default_factory=list)
    media_image_urls: List[str] = field(default_factory=list)
    media_audio_path: Optional[str] = None
    media_video_path: Optional[str] = None
    source_url: str = ""
    price_tl: Optional[float] = None
    commission_pct: Optional[float] = None
    language: str = "tr"
    platforms: List[str] = field(default_factory=lambda: ["telegram", "whatsapp",
                                                          "facebook", "instagram", "tiktok"])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    distribution_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DistributionBatch:
    batch_id: str
    started_at: str
    posts: List[PostItem] = field(default_factory=list)
    finished_at: Optional[str] = None
    total_success: int = 0
    total_platform_dispatches: int = 0
    report_message_id: Optional[str] = None


# =====================================================================
# 2. MODÜL 1: İÇERİK TARAYICI & ÜRETİCİ (ContentScanner)
# =====================================================================

_UTEYKDER_DUYURU_TEMPLATES: List[Dict[str, Any]] = [
    {
        "code": "saglik-icin-elele",
        "title": "🌸 Sağlık İçin Elele Kampanyası",
        "body": (
            "Sosyal İmece & UTEYKDER olarak “Sağlık İçin Elele” kampanyamızla "
            "maddi durumu yetersiz ailelerimizin sağlık hizmetlerine erişimini "
            "destekliyoruz. Bugün bağışta bulunan bir arkadaşımızın hikâyesini "
            "okuyun, bir “kalp” atın, paylaşmayı unutmayın. ❤️"
        ),
        "hashtags": ["#SaglikIcinElele", "#SosyalImece", "#UTEYKDER",
                     "#Dayanisma", "#Toplum", "#Gonullu"],
    },
    {
        "code": "duy-algila-ve-farkli-yasa",
        "title": "👁️‍🗨️ Duy, Algıla ve Farklı Yaşa!",
        "body": (
            "“Duy, Algıla ve Farklı Yaşa” eğitim programımız ile farkındalık "
            "oluşturuyoruz. Engelleri ortadan kaldıran, şefkat temelli bir toplum "
            "için bugün gönüllü olmak için DM / yorum bırakabilirsiniz. Tüm "
            "Sosyal İmece ailesi sizi bekliyor."
        ),
        "hashtags": ["#DuyAlgilaFarkliYasa", "#Farkindalik", "#UTEYKDER",
                     "#EngelsizYasam", "#SosyalSorumluluk", "#GonulluOl"],
    },
    {
        "code": "birlikte-gucluyuz",
        "title": "🤝 Birlikte Güçlüyüz – İhtiyaç Haritası",
        "body": (
            "Bu ay 42 şehirde 1.200+ ihtiyaç sahibi ailemize gıda, giyim ve "
            "eğitim desteği ulaştırdık. Sıradaki durağınız için takipte kalın; "
            "hikâyeleri sizlerle paylaşacağız. Sosyal İmece ile “hiçbirimiz, "
            "hepimiz kadar güçlü değiliz.” ✊"
        ),
        "hashtags": ["#BirlikteGucluyuz", "#IhtiyacHaritasi", "#SosyalImece",
                     "#UTEYKDER", "#Dayanisma"],
    },
]

_IMECE_DUYURU_TEMPLATES: List[Dict[str, Any]] = [
    {
        "code": "uye-ol",
        "title": "🌐 Sosyal İmece Ailesine Katılın!",
        "body": (
            "Küresel dayanışma hareketimiz Sosyal İmece ailesine bugün katılın! "
            "Fahri üyelik, gönüllü çalışma, komisyonlu gelir modeli ve daha "
            "fazlası için hemen t.me/lanalisovets kanalına üye olun. ✨"
        ),
        "hashtags": ["#SosyalImece", "#UyeOl", "#Dayanisma", "#KureselImece",
                     "#UTEYKDER"],
    },
]


class ContentScanner:
    """
    1) Trend Ürünler Market JSON / REST → ürün içerikleri
    2) UTEYKDER / Sosyal İmece statik / JSON duyuruları → CSR içerikleri
    """

    def __init__(self,
                 products_json_path: Optional[Path] = None,
                 sosyal_duyuru_json_path: Optional[Path] = None):
        self.products_json_path = products_json_path or ROOT / "toplanan_urunler.json"
        self.sosyal_duyuru_json_path = sosyal_duyuru_json_path or (ROOT / "uteykder_uye_arsivi.json")

    # ---- public ------------------------------------------------------
    def fetch_latest_batch(self,
                           max_products: int = 4,
                           max_uteykder: int = 2,
                           max_imece: int = 1) -> List[PostItem]:
        items: List[PostItem] = []
        items.extend(self._fetch_products(max_products))
        items.extend(self._fetch_uteykder_announcements(max_uteykder))
        items.extend(self._fetch_imece_announcements(max_imece))
        random.shuffle(items)  # platform yorgunluğunu azalt
        return items

    # ---- products ----------------------------------------------------
    def _fetch_products(self, limit: int) -> List[PostItem]:
        raw: List[Dict[str, Any]] = []
        # (A) HTTP REST den çek (fail ederse JSON fallback)
        try:
            resp = requests.get(
                f"{TRM_API_URL}/trending",
                headers={"Authorization": f"Bearer {TRM_API_KEY}"},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    raw = data[:limit]
                elif isinstance(data, dict):
                    raw = (data.get("products") or data.get("items") or [])[:limit]
        except Exception as exc:
            log.warning(f"TRM REST çağrılamadı, JSON fallback → {exc}")

        # (B) Yerel toplanan_urunler.json'dan destekle
        if not raw and self.products_json_path.exists():
            with open(self.products_json_path, "r", encoding="utf-8") as f:
                raw = json.load(f)[:limit * 2]

        # (C) En kötü durumda köprü modülündeki 8 ürünü kullan
        if not raw:
            raw = self._fallback_bridge_products(limit)

        return [self._product_to_post(x, idx=i) for i, x in enumerate(raw[:limit])]

    @staticmethod
    def _fallback_bridge_products(limit: int) -> List[Dict[str, Any]]:
        try:
            sys.path.insert(0, str(ROOT))
            from whatsapp_agent_bridge import analyzer  # type: ignore
            data = list(analyzer._trend_products)[:limit]
            return [
                {
                    "urun_adi": p.get("urun_adi", p.get("name", "")),
                    "aciklama": p.get("kisa_aciklama", ""),
                    "gorsel_url": p.get("gorsel_url", "https://picsum.photos/seed/" + str(i) + "/800/800"),
                    "urun_linki": p.get("affiliate_link", p.get("urun_linki", "https://trendurunlermarket.com")).replace("{ref}", "social1"),
                    "hashtagler": p.get("hashtags", "#TrendUrun #Komisyon"),
                    "fiyat": str(p.get("fiyat", "")),
                    "komisyon_orani": p.get("komisyon_orani"),
                }
                for i, p in enumerate(data)
            ]
        except Exception as exc:
            log.error(f"Bridge fallback ürünler alınamadı: {exc}")
            return []

    @staticmethod
    def _product_to_post(raw: Dict[str, Any], idx: int = 0) -> PostItem:
        ad = raw.get("urun_adi") or raw.get("name") or f"Ürün {idx+1}"
        aciklama = raw.get("aciklama") or raw.get("description") or ad
        fiyat_str = str(raw.get("fiyat") or raw.get("price") or "").replace(",", ".")
        try:
            fiyat: Optional[float] = float(fiyat_str) if fiyat_str else None
        except Exception:
            fiyat = None
        komisyon_raw = raw.get("komisyon_orani") or raw.get("commission_rate")
        try:
            komisyon: Optional[float] = float(komisyon_raw) if komisyon_raw not in (None, "") else None
        except Exception:
            komisyon = None
        hashtags = (
            raw.get("hashtagler") or raw.get("hashtags") or
            "#TrendUrun #TrendUrunlerMarket #Kampanya #Indirim"
        )
        if isinstance(hashtags, str):
            hashtags = [h for h in hashtags.replace(",", " ").split() if h.startswith("#")]
        image_url = raw.get("gorsel_url") or raw.get("image") or f"https://picsum.photos/seed/p{idx}/800/800"
        if not isinstance(image_url, list):
            image_urls = [image_url] if image_url else []
        else:
            image_urls = image_url
        source_url = raw.get("urun_linki") or raw.get("product_url") or raw.get("source_url") or "https://trendurunlermarket.com"
        uid = hashlib.sha1(f"{ad}|{source_url}|{idx}".encode()).hexdigest()[:14]
        return PostItem(
            item_id=f"prod_{uid}",
            content_type="product",
            title=ad,
            body=f"🔥 {ad}\n\n{aciklama}\n\n"
                 f"{'💰 Fiyat: ' + f'{fiyat:.2f} TL' if fiyat else ''}\n"
                 f"{'💸 Komisyon: %' + f'{komisyon:.1f}' if komisyon else ''}",
            hashtags=list(hashtags),
            media_image_urls=image_urls,
            source_url=source_url,
            price_tl=fiyat,
            commission_pct=komisyon,
        )

    # ---- duyurular ---------------------------------------------------
    def _fetch_uteykder_announcements(self, limit: int) -> List[PostItem]:
        return [
            PostItem(
                item_id=f"uty_{t['code']}",
                content_type="uteykder_duyuru",
                title=t["title"],
                body=f"{t['title']}\n\n{t['body']}",
                hashtags=list(t["hashtags"]),
                media_image_urls=[f"https://picsum.photos/seed/ute{idx}/800/600"],
                source_url="https://trendurunlermarket.com/uteykder",
            )
            for idx, t in enumerate(random.sample(_UTEYKDER_DUYURU_TEMPLATES,
                                                   k=min(limit, len(_UTEYKDER_DUYURU_TEMPLATES))))
        ]

    def _fetch_imece_announcements(self, limit: int) -> List[PostItem]:
        return [
            PostItem(
                item_id=f"imece_{t['code']}",
                content_type="imece_duyuru",
                title=t["title"],
                body=f"{t['title']}\n\n{t['body']}",
                hashtags=list(t["hashtags"]),
                media_image_urls=[f"https://picsum.photos/seed/ime{idx}/800/600"],
                source_url="https://t.me/lanalisovets",
            )
            for idx, t in enumerate(random.sample(_IMECE_DUYURU_TEMPLATES,
                                                   k=min(limit, len(_IMECE_DUYURU_TEMPLATES))))
        ]


# =====================================================================
# 3. MODÜL 2: MULTIMEDYA FABRİKASI (gTTS + pydub / ffmpeg iskeleti)
# =====================================================================

class MediaFactory:
    """
    Metin → Türkçe/İngilizce ses (gTTS) → isteğe bağlı video kaplaması (ffmpeg).
    Kütüphaneler kurulu değilse DRY-RUN (sahte dosya yolu) döner ve raporlar.
    """

    def __init__(self, out_dir: Path = MEDIA_DIR):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # ----- public -----------------------------------------------------
    def text_to_speech(self, text: str, lang: str = "tr", tag: str = "a") -> Optional[str]:
        """Metni mp3 ses dosyasına dönüştür. Başarısızsa None döner, log uyarı."""
        try:
            from gtts import gTTS  # type: ignore
        except Exception as exc:
            log.warning(f"gTTS kurulu değil, TTS atlanıyor: {exc}")
            return None
        try:
            safe_lang = "tr" if lang.startswith("tr") else ("de" if lang.startswith("de") else "en")
            tts = gTTS(text=text[:1800], lang=safe_lang, slow=False)
            out_name = f"tts_{tag}_{int(time.time())}_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            out_path = self.out_dir / out_name
            tts.save(str(out_path))
            log.info(f"🎙️ TTS üretildi: {out_path.name}")
            return str(out_path)
        except Exception as exc:
            log.warning(f"TTS başarısız: {exc}")
            return None

    def render_video_slide(self, image_url: str, audio_path: Optional[str],
                           tag: str = "v") -> Optional[str]:
        """Görsel + ses → kısa video; ffmpeg / pydub kurulu değilse None."""
        try:
            from pydub import AudioSegment  # type: ignore  # noqa: F401
        except Exception as exc:
            log.warning(f"pydub/ffmpeg kurulu değil, video atlanıyor: {exc}")
            return None
        import subprocess
        img_local = self._download_image(image_url, tag)
        if not img_local:
            return None
        out_name = f"vid_{tag}_{int(time.time())}.mp4"
        out_path = self.out_dir / out_name
        if not audio_path:
            audio_path = self._silent_audio(duration_ms=5000)
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_local,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
            "-b:a", "192k", "-pix_fmt", "yuv420p",
            "-shortest", str(out_path)
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            log.info(f"🎞️ Video üretildi: {out_path.name}")
            return str(out_path)
        except Exception as exc:
            log.warning(f"ffmpeg başarısız: {exc}")
            return None

    # ----- utils ------------------------------------------------------
    def _download_image(self, url: str, tag: str) -> Optional[str]:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return None
            ext = "jpg"
            name = f"img_{tag}_{int(time.time())}_{hashlib.md5(url.encode()).hexdigest()[:8]}.{ext}"
            out = self.out_dir / name
            with open(out, "wb") as f:
                f.write(r.content)
            return str(out)
        except Exception as exc:
            log.warning(f"Görsel indirilemedi {url}: {exc}")
            return None

    def _silent_audio(self, duration_ms: int = 5000) -> str:
        try:
            from pydub.generators import Sine  # type: ignore
            seg = Sine(440).to_audio_segment(duration=0).overlay(
                Sine(0).to_audio_segment(duration=duration_ms)
            )
            out = self.out_dir / f"silent_{duration_ms}_{int(time.time())}.mp3"
            seg.export(str(out), format="mp3")
            return str(out)
        except Exception as exc:
            log.warning(f"Sessiz ses oluşturulamadı: {exc}")
            return str(self.out_dir / "__placeholder.mp3")


# =====================================================================
# 4. MODÜL 3: ÇAPRAZ PLATFORM DAĞITICI (CrossPostDispatcher)
# =====================================================================

class CrossPostDispatcher:
    """
    Platform sırasıyla servis eder. Her biri için:
      - BAŞARI → {"success": True, "post_id": "...", "url": "..."}
      - EKSİK ANAHTAR → {"success": False, "status": "skip_missing_credentials", "note": "..."}
      - HATA     → {"success": False, "status": "error", "error": str(exc)}
    """

    PLATFORM_ORDER = ["telegram", "whatsapp", "facebook", "instagram", "tiktok"]

    def dispatch(self, item: PostItem) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for platform in self.PLATFORM_ORDER:
            if platform not in item.platforms:
                results[platform] = {"success": False, "status": "skipped_by_policy"}
                continue
            if platform == "telegram":
                results[platform] = self._post_telegram(item)
            elif platform == "whatsapp":
                results[platform] = self._post_whatsapp(item)
            elif platform == "facebook":
                results[platform] = self._post_facebook(item)
            elif platform == "instagram":
                results[platform] = self._post_instagram(item)
            elif platform == "tiktok":
                results[platform] = self._post_tiktok(item)
            time.sleep(1.5)  # rate-limit koruması (her platform arası 1.5sn)
        return results

    # ----- Telegram ---------------------------------------------------
    def _post_telegram(self, item: PostItem) -> Dict[str, Any]:
        channel = TELEGRAM_TARGET_CHANNEL_USERNAME.lstrip("@")
        if not TELEGRAM_BOT_TOKEN:
            return {"success": False, "status": "skip_missing_credentials",
                    "note": "TELEGRAM_BOT_TOKEN boş"}
        caption = self._render_caption(item, platform="telegram")
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        try:
            if item.media_image_urls:
                r = requests.post(f"{url}/sendPhoto", data={
                    "chat_id": f"@{channel}",
                    "caption": caption[:1024],
                    "parse_mode": "HTML",
                }, files={"photo": (
                    "img.jpg", requests.get(item.media_image_urls[0], timeout=15).content,
                    "image/jpeg",
                )}, timeout=30)
            else:
                r = requests.post(f"{url}/sendMessage", data={
                    "chat_id": f"@{channel}",
                    "text": caption[:4096],
                    "parse_mode": "HTML",
                }, timeout=30)
            if r.status_code // 100 != 2:
                return {"success": False, "status": "error", "error": r.text[:300]}
            payload = r.json()
            msg = (payload.get("result") or {}).get("message_id")
            return {"success": True, "post_id": str(msg),
                    "url": f"https://t.me/{channel}/{msg}"}
        except Exception as exc:
            return {"success": False, "status": "error", "error": str(exc)[:300]}

    # ----- WhatsApp ---------------------------------------------------
    def _post_whatsapp(self, item: PostItem) -> Dict[str, Any]:
        if not WHATSAPP_API_TOKEN or not WHATSAPP_BROADCAST_NUMBERS:
            return {"success": False, "status": "skip_missing_credentials",
                    "note": "WHATSAPP_API_TOKEN / WHATSAPP_BROADCAST_NUMBERS eksik"}
        body = self._render_caption(item, platform="whatsapp")[:1500]
        sent_ok = 0
        errors: List[str] = []
        for num in WHATSAPP_BROADCAST_NUMBERS:
            try:
                r = requests.post(
                    "https://graph.facebook.com/v18.0/PHONE_NUMBER_ID/messages",
                    headers={"Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
                             "Content-Type": "application/json"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": num,
                        "type": "text",
                        "text": {"body": body},
                    }, timeout=20,
                )
                if r.status_code // 100 == 2:
                    sent_ok += 1
                else:
                    errors.append(f"{num}:{r.status_code}")
            except Exception as exc:
                errors.append(f"{num}:{exc}")
        return {"success": sent_ok > 0,
                "status": "ok" if sent_ok else "error",
                "sent_count": sent_ok,
                "errors": errors[:3]}

    # ----- Facebook ---------------------------------------------------
    def _post_facebook(self, item: PostItem) -> Dict[str, Any]:
        if not FACEBOOK_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
            return {"success": False, "status": "skip_missing_credentials",
                    "note": "FACEBOOK_ACCESS_TOKEN / FACEBOOK_PAGE_ID eksik"}
        caption = self._render_caption(item, platform="facebook")
        try:
            if item.media_image_urls:
                resp = requests.post(
                    f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/photos",
                    data={
                        "url": item.media_image_urls[0],
                        "caption": caption,
                        "access_token": FACEBOOK_ACCESS_TOKEN,
                        "published": "true",
                    }, timeout=30,
                )
            else:
                resp = requests.post(
                    f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/feed",
                    data={
                        "message": caption,
                        "link": item.source_url,
                        "access_token": FACEBOOK_ACCESS_TOKEN,
                    }, timeout=30,
                )
            ok = resp.status_code // 100 == 2
            j = resp.json() if "json" in resp.headers.get("Content-Type", "") else {"raw": resp.text[:200]}
            return {"success": ok, "post_id": j.get("id"), "raw": j if not ok else None}
        except Exception as exc:
            return {"success": False, "status": "error", "error": str(exc)[:300]}

    # ----- Instagram --------------------------------------------------
    def _post_instagram(self, item: PostItem) -> Dict[str, Any]:
        if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID or not item.media_image_urls:
            return {"success": False, "status": "skip_missing_credentials",
                    "note": "IG token/hesap/görsel eksik"}
        base = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ACCOUNT_ID}"
        caption = self._render_caption(item, platform="instagram")
        try:
            r1 = requests.post(f"{base}/media", params={
                "image_url": item.media_image_urls[0],
                "caption": caption,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            }, timeout=30)
            if r1.status_code // 100 != 2:
                return {"success": False, "status": "error", "error": r1.text[:300]}
            creation_id = r1.json().get("id")
            r2 = requests.post(f"{base}/media_publish", params={
                "creation_id": creation_id,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            }, timeout=30)
            return {"success": r2.status_code // 100 == 2, "post_id": r2.json().get("id")}
        except Exception as exc:
            return {"success": False, "status": "error", "error": str(exc)[:300]}

    # ----- TikTok -----------------------------------------------------
    def _post_tiktok(self, item: PostItem) -> Dict[str, Any]:
        if not TIKTOK_ACCESS_TOKEN:
            return {"success": False, "status": "skip_missing_credentials",
                    "note": "TIKTOK_ACCESS_TOKEN eksik"}
        try:
            upload_url = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
            h = {"Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}", "Content-Type": "application/json; charset=UTF-8"}
            video = item.media_video_path or ""
            if not video:
                return {"success": False, "status": "error",
                        "error": "TikTok için video (media_video_path) üretilmedi, atla"}
            size = os.path.getsize(video)
            body = {
                "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                "chunk_size": size, "total_chunk_count": 1},
                "post_info": {"title": (item.title + " | " + " ".join(item.hashtags[:3]))[:149],
                              "privacy_level": "SELF_ONLY",
                              "disable_duet": False, "disable_comment": False, "disable_stitch": False,
                              "video_cover_timestamp_ms": 500},
            }
            r = requests.post(upload_url, headers=h, json=body, timeout=30)
            return {"success": r.status_code // 100 == 2,
                    "raw": r.json() if r.headers.get("Content-Type", "").startswith("application/json") else r.text[:200]}
        except Exception as exc:
            return {"success": False, "status": "error", "error": str(exc)[:300]}

    # ----- ortak caption ---------------------------------------------
    @staticmethod
    def _render_caption(item: PostItem, platform: str) -> str:
        hashtag_line = " ".join(item.hashtags[:8])
        link_line = f"\n🔗 {item.source_url}" if item.source_url else ""
        if platform == "telegram":
            parts = [f"<b>{item.title}</b>\n", item.body, link_line, "\n", hashtag_line]
        else:
            parts = [f"{item.title}\n\n", item.body, link_line, "\n\n", hashtag_line]
        return "".join([p for p in parts if p])


# =====================================================================
# 5. MODÜL 4: RAPORLAMA (Reporter)
# =====================================================================

class Reporter:
    def __init__(self, log_path: Path = DIST_LOG_JSON):
        self.log_path = log_path

    def record_batch(self, batch: DistributionBatch) -> None:
        existing: List[Dict[str, Any]] = []
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append({
            "batch_id": batch.batch_id,
            "started_at": batch.started_at,
            "finished_at": batch.finished_at,
            "total_posts": len(batch.posts),
            "total_success": batch.total_success,
            "total_dispatches": batch.total_platform_dispatches,
            "posts": [asdict(p) for p in batch.posts[-10:]],
        })
        # son 1500 kaydı tut
        existing = existing[-1500:]
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    def push_telegram_report(self, batch: DistributionBatch) -> Dict[str, Any]:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_REPORT_CHAT_ID:
            return {"success": False, "note": "Rapor için Telegram bot/chat ID eksik"}
        msg = self._format_report_message(batch)
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_REPORT_CHAT_ID,
                      "text": msg[:4096], "parse_mode": "HTML"}, timeout=30,
            )
            ok = r.status_code // 100 == 2
            j = r.json() if ok else r.text[:200]
            return {"success": ok, "message_id": (j.get("result") or {}).get("message_id"),
                    "raw": None if ok else j}
        except Exception as exc:
            return {"success": False, "error": str(exc)[:300]}

    @staticmethod
    def _format_report_message(b: DistributionBatch) -> str:
        post_lines = "\n".join([
            f"• [{p.content_type[:3].upper()}] <b>{p.title[:55]}</b> | "
            f"başarı: {sum(1 for x in p.distribution_results.values() if isinstance(x,dict) and x.get('success'))}/{len(p.platforms)}"
            for p in b.posts
        ])
        return (
            "📢 <b>Yeni Sosyal Medya İçeriği Dağıtıldı!</b>\n"
            f"⏱️ Başlangıç: {b.started_at}\n"
            f"🏁 Bitiş: {b.finished_at}\n"
            f"✅ Başarılı post sayısı: <b>{b.total_success}</b> / {len(b.posts)}\n"
            f"📤 Platform bazlı toplam servis: <b>{b.total_platform_dispatches}</b>\n"
            f"🆔 Batch: <code>{b.batch_id}</code>\n\n"
            "📋 İçerik listesi:\n"
            f"{post_lines}\n\n"
            "— Sosyal Medya Dağıtım Ajanı"
        )


# =====================================================================
# 6. ORKESTRASYON: SocialDistributionAgent
# =====================================================================

class SocialDistributionAgent:
    def __init__(self,
                 post_interval_sec: int = DEFAULT_POST_INTERVAL_SEC,
                 dry_run: bool = False):
        self.post_interval_sec = max(60, int(post_interval_sec))
        self.dry_run = dry_run
        self.scanner = ContentScanner()
        self.media = MediaFactory()
        self.dispatcher = CrossPostDispatcher()
        self.reporter = Reporter()

    # ----- public -----------------------------------------------------
    def run_once(self,
                 max_products: int = 3,
                 max_uteykder: int = 1,
                 max_imece: int = 1) -> DistributionBatch:
        batch = DistributionBatch(
            batch_id=f"SMD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
            started_at=datetime.now().isoformat(),
        )
        items = self.scanner.fetch_latest_batch(max_products=max_products,
                                                max_uteykder=max_uteykder,
                                                max_imece=max_imece)
        for item in items:
            # --- medya üret ---
            tag = hashlib.md5(item.item_id.encode()).hexdigest()[:6]
            item.media_audio_path = self.media.text_to_speech(item.body, lang=item.language, tag=tag)
            if item.media_image_urls:
                item.media_video_path = self.media.render_video_slide(
                    item.media_image_urls[0], item.media_audio_path, tag=tag
                )
            # --- dağıt ---
            if self.dry_run:
                res = {pl: {"success": True, "status": "dry_run"} for pl in item.platforms}
            else:
                res = self.dispatcher.dispatch(item)
            item.distribution_results = res

            success_count = sum(1 for v in res.values()
                                if isinstance(v, dict) and v.get("success"))
            batch.total_success += 1 if success_count >= 1 else 0
            batch.total_platform_dispatches += len(res)
            batch.posts.append(item)

        batch.finished_at = datetime.now().isoformat()
        # --- raporla ---
        self.reporter.record_batch(batch)
        report_result = self.reporter.push_telegram_report(batch)
        if isinstance(report_result, dict):
            batch.report_message_id = str(report_result.get("message_id") or "")
        log.info(f"📬 Batch {batch.batch_id} bitti. "
                 f"Başarılı post: {batch.total_success}/{len(batch.posts)}")
        return batch

    def run_forever(self,
                    max_products: int = 3,
                    max_uteykder: int = 1,
                    max_imece: int = 1):
        log.info(f"♾️ Dağıtım ajanı sonsuz döngüde. "
                 f"Aralık={self.post_interval_sec}sn, dry_run={self.dry_run}")
        while True:
            try:
                self.run_once(max_products, max_uteykder, max_imece)
            except Exception as exc:
                log.exception(f"Batch hatası: {exc}")
            log.info(f"💤 Bir sonraki batch için {self.post_interval_sec}sn bekle…")
            time.sleep(self.post_interval_sec)


# =====================================================================
# 7. ANA TEST GİRİŞİ: run_social_agent()
# =====================================================================

def run_social_agent(loop: bool = False,
                     dry_run: bool = True,
                     interval_sec: int = 30 * 60,
                     max_products: int = 3,
                     max_uteykder: int = 1,
                     max_imece: int = 1) -> Dict[str, Any]:
    """
    Hızlı test / gerçek çalışma için giriş.
      loop=False    → Tek sefer (smoke test), dry_run=True varsayılan.
      loop=True     → Sonsuz döngü, production.
      dry_run=False → Gerçek platform API çağrıları (token gerekir).
    """
    log.info(f"🚀 run_social_agent(loop={loop}, dry_run={dry_run})")
    agent = SocialDistributionAgent(post_interval_sec=interval_sec, dry_run=dry_run)
    if loop:
        agent.run_forever(max_products=max_products, max_uteykder=max_uteykder, max_imece=max_imece)
        return {"mode": "forever"}
    batch = agent.run_once(max_products=max_products,
                           max_uteykder=max_uteykder,
                           max_imece=max_imece)
    summary = {
        "batch_id": batch.batch_id,
        "started_at": batch.started_at,
        "finished_at": batch.finished_at,
        "total_posts": len(batch.posts),
        "success_posts": batch.total_success,
        "platform_dispatches": batch.total_platform_dispatches,
        "report_message_id": batch.report_message_id,
        "posts": [
            {
                "item_id": p.item_id,
                "type": p.content_type,
                "title": p.title[:60],
                "platforms": p.platforms,
                "results": p.distribution_results,
            }
            for p in batch.posts
        ],
    }
    log.info(f"🏁 Tek seferlik batch tamam → {summary['success_posts']}/{summary['total_posts']}")
    return summary


if __name__ == "__main__":
    # Üretim: python social_media_distribution_agent.py --live --loop
    # Test:    python social_media_distribution_agent.py
    args = set(sys.argv[1:])
    _dry = "--live" not in args
    _loop = "--loop" in args
    out = run_social_agent(loop=_loop, dry_run=_dry)
    if not _loop:
        print(json.dumps(out, ensure_ascii=False, indent=2))
