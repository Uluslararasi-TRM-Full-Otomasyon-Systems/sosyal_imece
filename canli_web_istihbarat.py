from contextlib import contextmanager
import ipaddress
import os
from pathlib import Path
import socket
import sqlite3
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup


class PublicTargetError(ValueError):
    pass


class CanliWebIstihbaratCeviricisi:
    USER_AGENT = "TRMResearchBot/1.0"
    MAX_RESPONSE_BYTES = 1_000_000

    def __init__(self, db_yolu=None, timeout=5):
        db_yolu = db_yolu or os.environ.get("TRM_LIVE_INTEL_DB") or "trm_kuyruk.db"
        self.db_yolu = Path(db_yolu)
        self.db_yolu.parent.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self._tablo_olustur()

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.db_yolu, timeout=self.timeout)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _tablo_olustur(self):
        with self._connection() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS canli_istihbarat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kaynak_url TEXT NOT NULL,
                    baslik TEXT NOT NULL,
                    tespit_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    durum TEXT NOT NULL DEFAULT 'pending_review'
                )
            """)

    @staticmethod
    def _validate_public_url(url):
        if not isinstance(url, str):
            raise PublicTargetError("URL metin olmalıdır")
        parsed = urlparse(url.strip())
        if parsed.scheme not in {"http", "https"}:
            raise PublicTargetError("Yalnızca http/https URL'leri kabul edilir")
        if not parsed.hostname or parsed.username or parsed.password:
            raise PublicTargetError("URL host içermeli ve kullanıcı bilgisi taşımamalıdır")
        try:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
        except ValueError as exc:
            raise PublicTargetError("URL portu geçersiz") from exc
        allowed_port = 443 if parsed.scheme == "https" else 80
        if port != allowed_port:
            raise PublicTargetError("Yalnızca HTTP 80 ve HTTPS 443 portları kabul edilir")

        try:
            addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise PublicTargetError("Hedef host çözümlenemedi") from exc
        if not addresses:
            raise PublicTargetError("Hedef host için IP adresi bulunamadı")
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0].split("%")[0])
            if not ip.is_global:
                raise PublicTargetError("Özel, yerel veya ayrılmış IP adreslerine istek engellendi")
        return parsed

    def _fetch_text(self, url, allow_plain_text=False):
        parsed = self._validate_public_url(url)
        with requests.get(
            url,
            headers={"User-Agent": self.USER_AGENT, "Accept": "text/html,text/plain;q=0.9"},
            timeout=self.timeout,
            allow_redirects=False,
            stream=True,
        ) as response:
            if 300 <= response.status_code < 400:
                raise PublicTargetError("Yönlendirmeler güvenlik için otomatik izlenmiyor")
            if response.status_code != 200:
                error = PublicTargetError(f"HTTP {response.status_code}")
                error.status_code = response.status_code
                raise error
            content_type = response.headers.get("Content-Type", "").lower()
            if not allow_plain_text and content_type and "html" not in content_type:
                raise PublicTargetError("Hedef yanıt HTML içeriği değil")
            content = bytearray()
            for chunk in response.iter_content(chunk_size=16_384):
                if not chunk:
                    continue
                content.extend(chunk)
                if len(content) > self.MAX_RESPONSE_BYTES:
                    raise PublicTargetError("Yanıt boyutu izin verilen sınırı aşıyor")
            encoding = response.encoding or "utf-8"
        return parsed, bytes(content).decode(encoding, errors="replace")

    def _robots_allowed(self, target_url):
        parsed = self._validate_public_url(target_url)
        robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
        try:
            _, robots_text = self._fetch_text(robots_url, allow_plain_text=True)
        except PublicTargetError as exc:
            if getattr(exc, "status_code", None) in {404, 410}:
                return True
            raise

        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(robots_text.splitlines())
        return parser.can_fetch(self.USER_AGENT, target_url)

    @staticmethod
    def _extract_headlines(html):
        soup = BeautifulSoup(html, "html.parser")
        candidates = soup.select("span.titleline > a")
        if not candidates:
            candidates = soup.select("h1, h2, h3, article a")
        titles = []
        for element in candidates:
            title = element.get_text(" ", strip=True)
            if title and title not in titles:
                titles.append(title)
            if len(titles) == 3:
                break
        return titles

    def web_taramasi_yap(self, hedef_url="https://news.ycombinator.com/"):
        try:
            self._validate_public_url(hedef_url)
            if not self._robots_allowed(hedef_url):
                return {"durum": "blocked", "mesaj": "robots.txt bu taramaya izin vermiyor", "bulgular": []}

            _, html = self._fetch_text(hedef_url)
            headlines = self._extract_headlines(html)
            if not headlines:
                return {"durum": "no_data", "mesaj": "Sayfada desteklenen başlık öğesi bulunamadı", "bulgular": []}

            with self._connection() as connection:
                for headline in headlines:
                    connection.execute(
                        "INSERT INTO canli_istihbarat (kaynak_url, baslik, durum) VALUES (?, ?, ?)",
                        (hedef_url, headline, "pending_review"),
                    )

            return {
                "durum": "draft_ready",
                "taranan_url": hedef_url,
                "veri_kaynagi": "canlı herkese açık HTML başlıkları",
                "bulgular": headlines,
                "kuyruk_durumu": "pending_review",
                "mesaj": "Başlıklar SQLite inceleme tablosuna eklendi; otomatik yayın yapılmadı.",
            }
        except (PublicTargetError, requests.RequestException, sqlite3.Error, OSError, UnicodeError) as exc:
            return {"durum": "error", "mesaj": str(exc), "bulgular": []}