"""Affiliate campaign draft generator backed by the TRM queue."""

import hashlib
import logging
import re
import sqlite3
from contextlib import closing
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from dispatch_queue_manager import DispatchQueueManager
from llm_gateway import MultiModelGateway


logger = logging.getLogger(__name__)
FALLBACK_AFFILIATE_BASE = "https://trendurunlermarket.com/urun"
FALLBACK_AFFILIATE_REF = "trm_hizli_kazanc"


def _is_safe_https_url(value):
    try:
        parsed = urlsplit(str(value or ""))
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def create_fallback_affiliate_link(product, campaign_id):
    product_id = str(product.get("product_id") or f"TRM-{campaign_id[:10]}").strip().lower()
    product_id = re.sub(r"[^a-z0-9_-]+", "-", product_id).strip("-") or f"trm-{campaign_id[:10]}"
    query = urlencode({"ref": FALLBACK_AFFILIATE_REF, "utm_source": "trm_ticari"})
    return f"{FALLBACK_AFFILIATE_BASE}/{quote(product_id, safe='-_')}?{query}"


class HizliKazancModulu:
    SIMULATED_TRENDS = [
        {
            "title": "Taşınabilir kahve demleme seti",
            "description": "Kompakt ve yeniden kullanılabilir kahve ekipmanı",
            "category": "mutfak",
            "source": "TRM simulated trend catalog",
            "url": "",
        },
        {
            "title": "Ayarlanabilir masa lambası",
            "description": "Çalışma alanları için ayarlanabilir aydınlatma",
            "category": "ev ve yaşam",
            "source": "TRM simulated trend catalog",
            "url": "",
        },
        {
            "title": "Katlanabilir telefon standı",
            "description": "Masa ve seyahat kullanımı için taşınabilir stand",
            "category": "aksesuar",
            "source": "TRM simulated trend catalog",
            "url": "",
        },
    ]

    def __init__(
        self,
        queue_db="trm_kuyruk.db",
        mode="simulate",
        trend_sources=None,
        affiliate_base_url=None,
        affiliate_tag=None,
        gateway=None,
        scraper=None,
        hook_generator=None,
    ):
        if mode not in {"simulate", "live"}:
            raise ValueError("mode 'simulate' veya 'live' olmalidir")
        self.queue_db = str(queue_db)
        self.mode = mode
        self.trend_sources = trend_sources
        self.affiliate_base_url = affiliate_base_url
        self.affiliate_tag = affiliate_tag
        self.gateway = gateway or MultiModelGateway()
        self.scraper = scraper
        self.hook_generator = hook_generator

    @staticmethod
    def rank_affiliate_research(scout_report, limit=10):
        """Rank sourced public commission claims without treating them as payout guarantees."""
        if not isinstance(scout_report, dict):
            return []
        candidates = scout_report.get("highest_public_commission_claims", [])
        ranked = []
        for item in candidates:
            try:
                rate = float(item.get("advertised_percent"))
            except (TypeError, ValueError):
                continue
            source_url = str(item.get("source_url") or "")
            if not source_url.startswith("https://"):
                continue
            ranked.append({
                "network_id": item.get("network_id"),
                "advertised_percent": rate,
                "category": item.get("category"),
                "source_url": source_url,
                "classification": "public_commission_claim_requires_program_terms_verification",
            })
        return sorted(ranked, key=lambda item: item["advertised_percent"], reverse=True)[:max(0, int(limit))]

    def _get_trends(self):
        if self.mode == "simulate":
            return [dict(item) for item in self.SIMULATED_TRENDS], []

        from web_scraper import LiveWebScraper

        scraper = self.scraper or LiveWebScraper(sources=self.trend_sources)
        trends = scraper.fetch_trends()
        return trends, list(getattr(scraper, "errors", []))

    @staticmethod
    def _campaign_id(product):
        identity = "|".join((
            str(product.get("title", "")),
            str(product.get("url", "")),
            str(product.get("source", "")),
        ))
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]

    def _generate_hooks(self, product):
        title = str(product.get("title") or "Bu ürün")
        description = str(product.get("description") or "")
        prompt = f"Ürün: {title}. Açıklama: {description}. Türkçe sosyal medya kancası taslağı."
        route = self.gateway.akilli_yonlendir("hizli_kanca", prompt)
        if self.hook_generator:
            generated = self.hook_generator(product, route)
            hooks = generated if isinstance(generated, list) else [generated]
            hooks = [str(hook).strip() for hook in hooks if str(hook).strip()]
            if hooks:
                return hooks[:3], route

        hooks = [
            f"{title}: günlük kullanımda gerçekten fark yaratan küçük detay ne?",
            f"{title} ararken şu üç özelliği karşılaştırmayı unutmayın.",
        ]
        return hooks, route

    def _affiliate_link_draft(self, product):
        partner_url = product.get("partner_url") or product.get("affiliate_url")
        if _is_safe_https_url(partner_url):
            return partner_url

        product_url = str(product.get("url") or "").strip()
        tag = str(self.affiliate_tag or "").strip()
        if self.affiliate_base_url and product_url and _is_safe_https_url(self.affiliate_base_url):
            parts = urlsplit(self.affiliate_base_url)
            query = dict(parse_qsl(parts.query, keep_blank_values=True))
            query.update({"url": product_url})
            if tag:
                query["tag"] = tag
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
        if product_url and tag:
            parts = urlsplit(product_url)
            query = dict(parse_qsl(parts.query, keep_blank_values=True))
            query["tag"] = tag
            return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
        return create_fallback_affiliate_link(product, self._campaign_id(product))

    def _affiliate_link_metadata(self, product):
        if _is_safe_https_url(product.get("partner_url") or product.get("affiliate_url")):
            return "partner_link", True
        if self.affiliate_tag and product.get("url"):
            return "draft_ready", True
        return "fallback_redirect", False

    def _make_task(self, product):
        campaign_id = self._campaign_id(product)
        hooks, route = self._generate_hooks(product)
        affiliate_link = self._affiliate_link_draft(product)
        link_status, commission_eligible = self._affiliate_link_metadata(product)
        product_payload = dict(product)
        product_payload["affiliate_url"] = affiliate_link
        return {
            "account_id": "trm_hizli_kazanc",
            "post_id": f"affiliate-{campaign_id}",
            "payload": {
                "task_type": "gelir_getiren_gorev",
                "etiket": "gelir_getiren_gorev",
                "status": "pending_review",
                "mode": self.mode,
                "campaign_id": campaign_id,
                "product": product_payload,
                "social_media_hooks": hooks,
                "affiliate_link_draft": affiliate_link,
                "affiliate_link_status": link_status,
                "commission_eligible": commission_eligible,
                "llm_gateway": route,
                "auto_publish": False,
            },
        }

    def kampanya_uret_ve_kuyruga_ekle(self):
        result = {
            "durum": "completed",
            "mode": self.mode,
            "simulasyon": self.mode == "simulate",
            "uretilen": 0,
            "kuyruga_eklenen": 0,
            "atlanan_yinelenen": 0,
            "kaynak_hatalari": [],
            "hatalar": [],
            "gorevler": [],
        }
        try:
            trends, source_errors = self._get_trends()
            result["kaynak_hatalari"] = source_errors
            queue = DispatchQueueManager(db_name=self.queue_db)
            for trend in trends:
                try:
                    task = self._make_task(trend)
                    result["uretilen"] += 1
                    with closing(sqlite3.connect(self.queue_db)) as connection:
                        exists = connection.execute(
                            "SELECT 1 FROM task_queue WHERE account_id = ? AND post_id = ? LIMIT 1",
                            (task["account_id"], task["post_id"]),
                        ).fetchone()
                    if exists:
                        result["atlanan_yinelenen"] += 1
                        continue
                    queue.add_to_queue(task)
                    result["kuyruga_eklenen"] += 1
                    result["gorevler"].append(task)
                except Exception as exc:
                    logger.exception("Affiliate kampanya gorevi olusturulamadi")
                    result["hatalar"].append({
                        "urun": str(trend.get("title", "bilinmiyor")),
                        "error": f"{exc.__class__.__name__}: {exc}",
                    })
        except Exception as exc:
            logger.exception("Hizli Kazanc kampanyasi calistirilamadi")
            result["durum"] = "error"
            result["hatalar"].append({"error": f"{exc.__class__.__name__}: {exc}"})

        if result["durum"] != "error" and (result["hatalar"] or result["kaynak_hatalari"]):
            result["durum"] = "partial_error" if result["kuyruga_eklenen"] else "error"
        return result


def hizli_kazanc_kampanyasi_uret(**kwargs):
    """Convenience entry point for scripts and task runners."""
    return HizliKazancModulu(**kwargs).kampanya_uret_ve_kuyruga_ekle()


if __name__ == "__main__":
    from pathlib import Path

    db_path = Path(__file__).resolve().with_name("trm_kuyruk.db")
    print(hizli_kazanc_kampanyasi_uret(queue_db=db_path, mode="simulate"))