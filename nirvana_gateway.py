import re
import json
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator, ValidationError
from filelock import FileLock
from datetime import datetime, timedelta
from typing import Dict, List, Any
import anyio
from collections import defaultdict

app = FastAPI()

RATE_LIMIT = 30
WINDOW_SECONDS = 60
ip_request_log: Dict[str, List[datetime]] = defaultdict(list)

# Mock / Üye Veri Tabanı (55+ kuralı için yaş/kıdem bilgisi)
MEMBER_DIRECTORY = {
    "APL-55-ALTIN": {"age": 58, "status": "senior_55_plus", "cuzdan_tl": 0.0},
    "APL-34-GENCLIK": {"age": 34, "status": "standard", "cuzdan_tl": 0.0},
    "APL-60-KIDEM": {"age": 62, "status": "senior_55_plus", "cuzdan_tl: ": 0.0},
}
GLOBAL_POOL_TL = 100000.0  # Örnek/akümülatif havuz

async def rate_limit_dependency(request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=WINDOW_SECONDS)
    times = ip_request_log[ip]
    while times and times[0] < window_start:
        times.pop(0)
    if len(times) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too Many Requests")
    times.append(now)

def sanitize(value: str) -> str:
    cleaned = re.sub(r'[<>"\'\\/\x00-\x1f]', '', value)
    if not cleaned.strip():
        raise ValueError("Field cannot be empty or only invalid characters")
    return cleaned

class WebhookPayload(BaseModel):
    platform: str
    order_id: str
    customer_id: str
    total_amount_tl: float
    commission_rate: float
    currency: str

    @field_validator('platform', 'order_id', 'customer_id')
    @classmethod
    def validate_fields(cls, v):
        return sanitize(v)

FILE_PATH = "C:\\Users\\Habitat\\Desktop\\sosyal_imece\\magazanolsun_webhook_events.jsonl"
LOCK_PATH = FILE_PATH + ".lock"

def calculate_sosyal_imece_distribution(brut_komisyon: float) -> Dict[str, Any]:
    # 1. Herkese imece payı + %20 refah payı (Örn: Brüt komisyonun %60'ı genel imece+refah dağılımına)
    genel_dagitim_orani = 0.60
    toplam_dagitilacak_genel = brut_komisyon * genel_dagitim_orani
    n_toplam_uye = len(MEMBER_DIRECTORY)
    imece_ve_refah_kisi_basi = toplam_dagitilacak_genel / max(n_toplam_uye, 1)

    # 2. 55 yaş ve üzeri kişilere özel zenginlik payı (Kalan %40 zenginlik havuzundan)
    zenginlik_havuzu = brut_komisyon * (1.0 - genel_dagitim_orani)
    seniors = [k for k, v in MEMBER_DIRECTORY.items() if v.get("age", 0) >= 55]
    zenginlik_kisi_basi = zenginlik_havuzu / max(len(seniors), 1) if seniors else 0.0

    return {
        "rule_sequence": ["base_imece_plus_20pct_refah_all", "senior_55_plus_wealth_share"],
        "n_toplam_uye": n_toplam_uye,
        "n_55_plus_kıdemli": len(seniors),
        "genel_kisi_basi_tl": round(imece_ve_refah_kisi_basi, 2),
        "senior_zenginlik_kisi_basi_tl": round(zenginlik_kisi_basi, 2),
        "timestamp": datetime.utcnow().isoformat()
    }

def sync_write_event(raw_data: dict, enriched_result: dict):
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": f"{raw_data['platform']}.com/magazanolsun",
        "raw_payload": raw_data,
        "execution_result": {
            "status": "CLOSED_LOOP_SUCCESS",
            "sosyal_imece_dagitim": enriched_result
        }
    }
    lock = FileLock(LOCK_PATH)
    with lock:
        with open(FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

@app.post("/webhook/global-affiliate", dependencies=[Depends(rate_limit_dependency)])
async def global_affiliate_webhook(payload: WebhookPayload):
    try:
        raw_dict = payload.model_dump()
        brut_komisyon = raw_dict["total_amount_tl"] * raw_dict["commission_rate"]
        enriched = calculate_sosyal_imece_distribution(brut_komisyon)
        
        await anyio.to_thread.run_sync(sync_write_event, raw_dict, enriched)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "verified", "GLOBAL_SYNC_SUCCESS": True, "imece_summary": enriched})
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@app.get("/")
async def health_check():
    return {"status": "nirvana running with sosyal imece engine"}
