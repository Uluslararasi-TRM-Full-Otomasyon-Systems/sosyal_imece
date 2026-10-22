# agents/social_agents.py
import logging
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from real_social_publisher import STATUS_SENT, RealSocialPublisher

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SocialAgents")

class RateLimiter:
    def __init__(self, max_calls: int = 5, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self.calls: List[float] = []

    def acquire(self):
        now = time.time()
        self.calls = [c for c in self.calls if now - c < self.period]
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            logger.warning(f"Rate limit aşıldı. Bekleniyor: {sleep_time:.2f}s")
            time.sleep(max(0, sleep_time))
        self.calls.append(time.time())

limiter = RateLimiter(max_calls=10, period=60.0)

def rate_limited(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        limiter.acquire()
        return func(*args, **kwargs)
    return wrapper

_publisher: RealSocialPublisher | None = None


def get_publisher() -> RealSocialPublisher:
    global _publisher
    if _publisher is None:
        _publisher = RealSocialPublisher()
    return _publisher

class SocialPublisherAgent:
    def __init__(self, platform: str):
        self.platform = platform

    @rate_limited
    def publish(self, payload: Dict[Any, Any]) -> Dict[str, Any]:
        product_title = payload.get("title", "Trend Ürün")
        affiliate_link = payload.get("link", "https://trendurunlermarket.com")
        campaign = payload.get("campaign", "Genel Promosyon")
        text = str(payload.get("text") or f"{product_title} · {campaign}\n{affiliate_link}").strip()

        outcome = get_publisher().publish(self.platform, text)
        sent = outcome["status"] == STATUS_SENT
        detail = outcome["post_id"] if sent else (outcome["error"] or outcome["reason"] or "doğrulanamadı")
        log = logger.info if sent else logger.warning
        log(f"[{str(self.platform).upper()}] {outcome['status']} · {detail}")
        return {
            "status": outcome["status"],
            "platform": str(self.platform),
            "post_id": outcome["post_id"],
            "detail": detail,
            "timestamp": time.time(),
        }

def dispatch_multichannel_campaign(payload: Dict[Any, Any]) -> Dict[str, Any]:
    platforms = ["facebook", "telegram", "tiktok", "instagram"]
    results = {}
    for p in platforms:
        agent = SocialPublisherAgent(platform=p)
        results[p] = agent.publish(payload)
    sent = [name for name, item in results.items() if item["status"] == STATUS_SENT]
    return {
        "multi_channel_status": "sent" if sent else "not_sent",
        "sent_channels": sent,
        "results": results
    }