# agents/social_agents.py
import time
import logging
from typing import Dict, Any, List
from functools import wraps

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

class SocialPublisherAgent:
    def __init__(self, platform: str):
        self.platform = platform

    @rate_limited
    def publish(self, payload: Dict[Any, Any]) -> Dict[str, Any]:
        product_title = payload.get("title", "Trend Ürün")
        affiliate_link = payload.get("link", "https://trendurunlermarket.com")
        campaign = payload.get("campaign", "Genel Promosyon")
        
        # Simüle edilmiş API çağrısı ve hata yönetimi
        try:
            logger.info(f"[{self.platform.upper()}] Yayınlanıyor: {product_title} | Kampanya: {campaign}")
            # Gerçek SDK/API entegrasyon noktası (Meta Graph API / Telegram Bot API vb.)
            time.sleep(0.3)
            return {
                "status": "success",
                "platform": self.platform,
                "message": f"İçerik başarıyla {self.platform} hattına aktarıldı.",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"[{self.platform.upper()}] Yayın hatası: {str(e)}")
            return {
                "status": "error",
                "platform": self.platform,
                "error": str(e),
                "timestamp": time.time()
            }

def dispatch_multichannel_campaign(payload: Dict[Any, Any]) -> Dict[str, Any]:
    platforms = ["facebook", "telegram", "tiktok", "instagram"]
    results = {}
    for p in platforms:
        agent = SocialPublisherAgent(platform=p)
        results[p] = agent.publish(payload)
    return {
        "multi_channel_status": "completed",
        "results": results
    }