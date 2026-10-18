#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TRM Ticari Ajan Ekosistemi Backend Sunucusu v2.0
FastAPI tabanlı yerel API sunucusu (:8000)

TÜM veriler artık merkezi trm_veritabani.db üzerinde tutulur.
Okuma/yazma işlemleri trm_db güvenli katmanından (tek yazıcı thread +
WAL + busy_timeout + kilit yeniden deneme) geçer → dosya kilitlenmesi
veya eşzamanlılık çakışması imkânsız hale gelir.

Panel (TRM_EKOSISTEM_TICARI_KURESEL_BESLİ_KONTROL_PANELI.html) bu
sunucudan şu uç noktaları bekler:
  GET  /api/dashboard         → toplam istatistikler (+ gömülü listeler)
  GET  /api/agents            → ajan listesi (ajanlar + agents tabloları birleşik)
  GET  /api/brand-offers      → marka teklifleri (brand_proposals)
  GET  /api/customer-requests → müşteri talepleri (customer_requests)
  GET  /api/meetings          → takvim olayları (calendar_events)
  GET  /api/metrics           → KPI metrikleri
  GET  /api/revenue           → günlük gelir serisi
  POST /api/command           → JARVIS komut konsolu
  GET  /api/db/durum          → veritabanı sağlık durumu
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Windows konsolunda Türkçe karakter sorunlarını önler
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from trm_db import trm_db

# FastAPI uygulaması
app = FastAPI(
    title="TRM Ticari Ajan Ekosistemi API",
    description="1200+ ajan ekosistemi için merkezi veri yönetim sistemi (trm_veritabani.db)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Merkezi veritabanı (tablolar ilk erişimde otomatik oluşur)
DB_PATH = BASE_DIR / "trm_veritabani.db"


def _db():
    """Merkezi veritabanı tekil örneği."""
    return trm_db()


def init_database():
    """Uyumluluk için korunur; tabloları trm_db otomatik oluşturur."""
    db = _db()
    print(f"[AJAN-EKOSISTEM] Merkezi veritabanı hazır: {db.db_yolu}")
    return db


# ============================================
# PYDANTIC MODELLER
# ============================================

class Agency(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "active"

class Agent(BaseModel):
    agency_id: Optional[int] = None
    name: str
    type: Optional[str] = None
    status: str = "idle"
    metadata: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    agent_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"

class BrandProposal(BaseModel):
    brand_name: str
    proposal_amount: float
    currency: str = "USD"
    status: str = "pending"
    agent_id: Optional[int] = None
    notes: Optional[str] = None

class CustomerRequest(BaseModel):
    customer_name: Optional[str] = None
    request_text: str
    status: str = "pending"
    priority: str = "medium"
    agent_id: Optional[int] = None

class CalendarEvent(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: str
    event_time: Optional[str] = None
    event_type: Optional[str] = None
    status: str = "scheduled"
    agent_id: Optional[int] = None


# ============================================
# YARDIMCI: AJAN PANEL FORMATI
# ============================================

_AJAN_DURUM_HARITASI = {
    "aktif": "active",
    "active": "active",
    "calisiyor": "active",
    "inactive": "idle",
    "beklemede": "idle",
    "pasif": "idle",
    "idle": "idle",
    "hata": "error",
    "error": "error",
}

_TUR_KATEGORI_HARITASI = {
    "import": "veri",
    "veri": "veri",
    "data": "veri",
    "analiz": "veri",
    "sosyal": "sosyal",
    "social": "sosyal",
    "komuta": "altyapi",
    "altyapi": "altyapi",
    "infra": "altyapi",
    "sistem": "altyapi",
}


def _ajanlar_satirini_hazirla(satir: Dict) -> Dict:
    """ajanlar (Türkçe merkezi kayıt) satırını panelin beklediği forma çevirir."""
    durum_ham = (satir.get("durum") or "beklemede").lower()
    tur_ham = (satir.get("tur") or "veri").lower()
    detay = satir.get("detay")
    if isinstance(detay, str):
        detay = None  # panelde ham JSON gösterilmez
    return {
        "id": satir.get("id"),
        "code": satir.get("ajan_kodu"),
        "name": satir.get("ad"),
        "task": satir.get("rol") or satir.get("tur") or "Görev tanımsız",
        "cat": _TUR_KATEGORI_HARITASI.get(tur_ham, "diger"),
        "status": _AJAN_DURUM_HARITASI.get(durum_ham, durum_ham),
        "active": durum_ham == "active" or durum_ham == "aktif",
        "last_active": satir.get("son_kalp_atisi"),
        "type": satir.get("tur"),
        "source": "ajanlar",
    }


def _agents_satirini_hazirla(satir: Dict) -> Dict:
    """agents (ekosistem) tablosu satırını panelin beklediği forma çevirir."""
    durum_ham = (satir.get("status") or "idle").lower()
    tur_ham = (satir.get("type") or "veri").lower()
    return {
        "id": satir.get("id"),
        "agency_id": satir.get("agency_id"),
        "code": f"AGT-{satir.get('id')}",
        "name": satir.get("name"),
        "task": satir.get("type") or "Görev tanımsız",
        "cat": _TUR_KATEGORI_HARITASI.get(tur_ham, "diger"),
        "status": _AJAN_DURUM_HARITASI.get(durum_ham, durum_ham),
        "active": durum_ham == "active",
        "last_active": satir.get("last_active"),
        "type": satir.get("type"),
        "metadata": satir.get("metadata"),
        "source": "agents",
    }


def _saglik_puani() -> int:
    """modul_durumlari tablosundan basit bir sistem sağlığı yüzdesi üretir."""
    db = _db()
    satirlar = db.oku("SELECT durum FROM modul_durumlari")
    if not satirlar:
        return 100
    saglikli = sum(
        1 for s in satirlar
        if (s.get("durum") or "").lower() not in ("hata", "error", "bilinmiyor", "kapali", "down")
    )
    return int(round(100 * saglikli / len(satirlar)))


def _metrikleri_hesapla() -> Dict:
    db = _db()
    ajan_aktif = db.oku_tek(
        "SELECT COUNT(*) AS n FROM ajanlar WHERE LOWER(durum) IN ('aktif','active')")
    ajan_toplam = db.oku_tek("SELECT COUNT(*) AS n FROM ajanlar")
    eko_aktif = db.oku_tek("SELECT COUNT(*) AS n FROM agents WHERE status = 'active'")
    eko_toplam = db.oku_tek("SELECT COUNT(*) AS n FROM agents")

    teklif_toplam = db.oku_tek("SELECT COUNT(*) AS n FROM brand_proposals")
    teklif_bekleyen = db.oku_tek("SELECT COUNT(*) AS n FROM brand_proposals WHERE status = 'pending'")
    gelir = db.oku_tek(
        "SELECT COALESCE(SUM(proposal_amount), 0) AS t FROM brand_proposals "
        "WHERE status = 'accepted'")

    talep_toplam = db.oku_tek("SELECT COUNT(*) AS n FROM customer_requests")
    talep_bekleyen = db.oku_tek(
        "SELECT COUNT(*) AS n FROM customer_requests WHERE status = 'pending'")
    toplanti = db.oku_tek("SELECT COUNT(*) AS n FROM calendar_events")

    return {
        "active_agents": int(ajan_aktif["n"] if ajan_aktif else 0) + int(eko_aktif["n"] if eko_aktif else 0),
        "total_agents": int(ajan_toplam["n"] if ajan_toplam else 0) + int(eko_toplam["n"] if eko_toplam else 0),
        "total_offers": int(teklif_toplam["n"] if teklif_toplam else 0),
        "pending_offers": int(teklif_bekleyen["n"] if teklif_bekleyen else 0),
        "total_requests": int(talep_toplam["n"] if talep_toplam else 0),
        "pending_requests": int(talep_bekleyen["n"] if talep_bekleyen else 0),
        "total_meetings": int(toplanti["n"] if toplanti else 0),
        "total_revenue": float(gelir["t"] if gelir else 0.0),
        "system_health": _saglik_puani(),
        "timestamp": datetime.now().isoformat(),
    }


# ============================================
# TEMEL UÇ NOKTALAR
# ============================================

@app.get("/")
async def root():
    return {
        "message": "TRM Ticari Ajan Ekosistemi API",
        "version": "2.0.0",
        "status": "running",
        "database": str(DB_PATH)
    }


@app.get("/api/health")
async def health_check():
    db = _db()
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database_exists": DB_PATH.exists(),
        "writer_alive": db._yazici_thread.is_alive(),
        "writer_queue": db._yazma_kuyrugu.qsize(),
    }


@app.get("/api/db/durum")
async def db_durum():
    """Merkezi veritabanı sağlık raporu (tablo dolulukları, boyut, kuyruk)."""
    return _db().durum_raporu()


# ============================================
# AJANSLAR UÇ NOKTALARI
# ============================================

@app.post("/api/agencies")
async def create_agency(agency: Agency):
    try:
        sonuc = _db().yaz(
            "INSERT INTO agencies (name, description, status) VALUES (?, ?, ?)",
            (agency.name, agency.description, agency.status),
        )
        return {"id": sonuc["lastrowid"], "message": "Ajans oluşturuldu"}
    except Exception:
        raise HTTPException(status_code=400, detail="Bu isimde bir ajans zaten mevcut")


@app.get("/api/agencies")
async def get_agencies():
    return _db().oku("SELECT * FROM agencies ORDER BY created_at DESC")


@app.get("/api/agencies/{agency_id}")
async def get_agency(agency_id: int):
    ajans = _db().oku_tek("SELECT * FROM agencies WHERE id = ?", (agency_id,))
    if not ajans:
        raise HTTPException(status_code=404, detail="Ajans bulunamadı")
    return ajans


# ============================================
# AJANLAR UÇ NOKTALARI
# ============================================

@app.post("/api/agents")
async def create_agent(agent: Agent):
    import json as _json
    metadata_json = _json.dumps(agent.metadata) if agent.metadata else None
    sonuc = _db().yaz(
        "INSERT INTO agents (agency_id, name, type, status, metadata) VALUES (?, ?, ?, ?, ?)",
        (agent.agency_id, agent.name, agent.type, agent.status, metadata_json),
    )
    return {"id": sonuc["lastrowid"], "message": "Ajan oluşturuldu"}


@app.get("/api/agents")
async def get_agents(status: Optional[str] = None, agency_id: Optional[int] = None):
    """Ajanları listeler — merkezi 'ajanlar' kaydı + ekosistem 'agents' tablosu birleşik.

    Panelin beklediği alanlar: code, name, task, cat, status, progress.
    """
    db = _db()

    # 1) Merkezi kayıt (Türkçe şema — migrasyon ve MASTER_CONTROLLER buraya yazar)
    ajanlar = db.ajanlari_getir(adet=1500)
    liste = [_ajanlar_satirini_hazirla(a) for a in ajanlar]

    # 2) Ekosistem operational tablosu (FK referansları bunu kullanır)
    sartlar, paramler = [], []
    if status:
        sartlar.append("status = ?")
        paramler.append(status)
    if agency_id:
        sartlar.append("agency_id = ?")
        paramler.append(agency_id)
    sorgu = "SELECT * FROM agents"
    if sartlar:
        sorgu += " WHERE " + " AND ".join(sartlar)
    sorgu += " ORDER BY id DESC"  # agents tablosunda created_at sütunu yok
    for satir in db.oku(sorgu, paramler):
        liste.append(_agents_satirini_hazirla(satir))

    # 3) İsteğe bağlı durum filtresi (panel formatındaki status alanına uygulanır)
    if status:
        hedef = _AJAN_DURUM_HARITASI.get(status.lower(), status.lower())
        liste = [a for a in liste if a["status"] == hedef or a["status"] == status.lower()]

    return liste


@app.put("/api/agents/{agent_id}/status")
async def update_agent_status(agent_id: int, status: str):
    sonuc = _db().yaz(
        "UPDATE agents SET status = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?",
        (status, agent_id),
    )
    if not sonuc["rowcount"]:
        raise HTTPException(status_code=404, detail="Ajan bulunamadı")
    return {"message": "Ajan durumu güncellendi"}


# ============================================
# GÖREVLER UÇ NOKTALARI
# ============================================

@app.post("/api/tasks")
async def create_task(task: Task):
    sonuc = _db().yaz(
        "INSERT INTO tasks (agent_id, title, description, status, priority) VALUES (?, ?, ?, ?, ?)",
        (task.agent_id, task.title, task.description, task.status, task.priority),
    )
    return {"id": sonuc["lastrowid"], "message": "Görev oluşturuldu"}


@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None, agent_id: Optional[int] = None):
    sartlar, paramler = [], []
    if status:
        sartlar.append("status = ?")
        paramler.append(status)
    if agent_id:
        sartlar.append("agent_id = ?")
        paramler.append(agent_id)
    sorgu = "SELECT * FROM tasks"
    if sartlar:
        sorgu += " WHERE " + " AND ".join(sartlar)
    sorgu += " ORDER BY created_at DESC"
    return _db().oku(sorgu, paramler)


@app.put("/api/tasks/{task_id}/status")
async def update_task_status(task_id: int, status: str, result: Optional[str] = None):
    if status == "completed":
        sonuc = _db().yaz(
            "UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP, "
            "result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, result, task_id),
        )
    else:
        sonuc = _db().yaz(
            "UPDATE tasks SET status = ?, result = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, result, task_id),
        )
    if not sonuc["rowcount"]:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    return {"message": "Görev durumu güncellendi"}


# ============================================
# MARKA TEKLİFLERİ UÇ NOKTALARI
# ============================================

@app.post("/api/proposals")
async def create_proposal(proposal: BrandProposal):
    sonuc = _db().yaz(
        "INSERT INTO brand_proposals (brand_name, proposal_amount, currency, status, agent_id, notes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (proposal.brand_name, proposal.proposal_amount, proposal.currency,
         proposal.status, proposal.agent_id, proposal.notes),
    )
    return {"id": sonuc["lastrowid"], "message": "Teklif oluşturuldu"}


@app.get("/api/proposals")
async def get_proposals(status: Optional[str] = None):
    sorgu = "SELECT * FROM brand_proposals"
    paramler = []
    if status:
        sorgu += " WHERE status = ?"
        paramler.append(status)
    sorgu += " ORDER BY created_at DESC"
    return _db().oku(sorgu, paramler)


@app.get("/api/brand-offers")
async def get_brand_offers(status: Optional[str] = None):
    """Panel için /api/proposals takma adı — panel formatında alan adları."""
    sorgu = "SELECT * FROM brand_proposals"
    paramler = []
    if status:
        sorgu += " WHERE status = ?"
        paramler.append(status)
    sorgu += " ORDER BY created_at DESC LIMIT 100"
    return [
        {
            "id": s["id"],
            "brand": s["brand_name"],
            "amount": s["proposal_amount"],
            "value": s["proposal_amount"],
            "currency": s["currency"],
            "status": s["status"],
            "date": s["created_at"],
            "description": s["notes"],
            "agent_id": s["agent_id"],
        }
        for s in _db().oku(sorgu, paramler)
    ]


# ============================================
# MÜŞTERİ TALEPLERİ UÇ NOKTALARI
# ============================================

@app.post("/api/requests")
async def create_request(request: CustomerRequest):
    sonuc = _db().yaz(
        "INSERT INTO customer_requests (customer_name, request_text, status, priority, agent_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (request.customer_name, request.request_text, request.status,
         request.priority, request.agent_id),
    )
    return {"id": sonuc["lastrowid"], "message": "Talep oluşturuldu"}


@app.get("/api/requests")
async def get_requests(status: Optional[str] = None):
    sorgu = "SELECT * FROM customer_requests"
    paramler = []
    if status:
        sorgu += " WHERE status = ?"
        paramler.append(status)
    sorgu += " ORDER BY created_at DESC"
    return _db().oku(sorgu, paramler)


@app.get("/api/customer-requests")
async def get_customer_requests(status: Optional[str] = None):
    """Panel için /api/requests takma adı — panel formatında alan adları."""
    sorgu = "SELECT * FROM customer_requests"
    paramler = []
    if status:
        sorgu += " WHERE status = ?"
        paramler.append(status)
    sorgu += " ORDER BY created_at DESC LIMIT 100"
    return [
        {
            "id": s["id"],
            "customer": s["customer_name"] or "Müşteri",
            "name": s["customer_name"],
            "subject": s["request_text"],
            "message": s["request_text"],
            "status": s["status"],
            "priority": s["priority"],
            "date": s["created_at"],
            "response": s["response"],
        }
        for s in _db().oku(sorgu, paramler)
    ]


# ============================================
# TAKVİM / GÖRÜŞMELER UÇ NOKTALARI
# ============================================

@app.post("/api/calendar")
async def create_event(event: CalendarEvent):
    sonuc = _db().yaz(
        "INSERT INTO calendar_events (title, description, event_date, event_time, event_type, status, agent_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (event.title, event.description, event.event_date, event.event_time,
         event.event_type, event.status, event.agent_id),
    )
    return {"id": sonuc["lastrowid"], "message": "Takvim olayı oluşturuldu"}


@app.get("/api/calendar")
async def get_events(status: Optional[str] = None, event_date: Optional[str] = None):
    sartlar, paramler = [], []
    if status:
        sartlar.append("status = ?")
        paramler.append(status)
    if event_date:
        sartlar.append("event_date = ?")
        paramler.append(event_date)
    sorgu = "SELECT * FROM calendar_events"
    if sartlar:
        sorgu += " WHERE " + " AND ".join(sartlar)
    sorgu += " ORDER BY event_date ASC, event_time ASC"
    return _db().oku(sorgu, paramler)


@app.get("/api/meetings")
async def get_meetings(status: Optional[str] = None):
    """Panel için takvim olaylarını 'görüşme' formatında sunar."""
    sorgu = "SELECT * FROM calendar_events"
    paramler = []
    if status:
        sorgu += " WHERE status = ?"
        paramler.append(status)
    sorgu += " ORDER BY event_date ASC, event_time ASC LIMIT 100"
    sonuc = []
    for s in _db().oku(sorgu, paramler):
        tarih = s["event_date"]
        if s.get("event_time"):
            tarih = f"{s['event_date']}T{s['event_time']}"
        sonuc.append({
            "id": s["id"],
            "title": s["title"],
            "subject": s["title"],
            "date": tarih,
            "status": s["status"],
            "location": s.get("description") or None,
            "type": s.get("event_type"),
        })
    return sonuc


# ============================================
# METRİK / GELİR / DASHBOARD UÇ NOKTALARI
# ============================================

@app.get("/api/metrics")
async def get_metrics():
    """Panel KPI'ları: aktif ajan, teklif, talep, toplantı, gelir, sistem sağlığı."""
    return _metrikleri_hesapla()


@app.get("/api/revenue")
async def get_revenue(days: int = 7):
    """Kabul edilen tekliflerden günlük gelir serisi üretir."""
    db = _db()
    satirlar = db.oku(
        "SELECT DATE(created_at) AS gun, COALESCE(SUM(proposal_amount), 0) AS toplam, "
        "COUNT(*) AS adet FROM brand_proposals WHERE status = 'accepted' "
        "GROUP BY DATE(created_at) ORDER BY gun DESC LIMIT ?",
        (int(days),),
    )
    return [
        {"date": s["gun"], "day": s["gun"], "amount": float(s["toplam"]),
         "value": float(s["toplam"]), "count": s["adet"]}
        for s in reversed(satirlar)
    ]


@app.get("/api/dashboard")
async def get_dashboard_stats():
    """Panelin ana istatistik paketi — tek fetch ile tüm KPI + listeler."""
    return {
        **_metrikleri_hesapla(),
        "agents": await get_agents(),
        "offers": await get_brand_offers(),
        "requests": await get_customer_requests(),
        "meetings": await get_meetings(),
        "revenue": await get_revenue(),
    }


@app.get("/api/status/export")
async def export_status_json():
    """Tüm sistemi JSON olarak dışa aktarır."""
    db = _db()
    return {
        "timestamp": datetime.now().isoformat(),
        "agencies": db.oku("SELECT * FROM agencies"),
        "agents": db.oku("SELECT * FROM agents"),
        "ajanlar": db.oku("SELECT * FROM ajanlar"),
        "tasks": db.oku("SELECT * FROM tasks"),
        "proposals": db.oku("SELECT * FROM brand_proposals"),
        "requests": db.oku("SELECT * FROM customer_requests"),
        "calendar": db.oku("SELECT * FROM calendar_events"),
        "db": db.durum_raporu(),
    }


# ============================================
# JARVIS KOMUT KONSOLU
# ============================================

def _komut_yaniti(komut: str) -> str:
    """Basit yerleşik komut yanıtları; gerisi kuyruğa alınır."""
    k = komut.lower().strip()
    db = _db()

    if k in ("yardim", "yardım", "help"):
        return ("Kullanılabilir: 'durum' (sistem özeti), 'veritabanı' (DB raporu), "
                "'kuyruk' (kuyruk istatistikleri). Diğer komutlar komutlar "
                "kuyruğuna alınır ve otonom ajanlar tarafından işlenir.")
    if "veritaban" in k or "database" in k:
        rapor = db.durum_raporu()
        return (f"Veritabanı: {rapor['toplam_kayit']} kayıt, {rapor['boyut_mb']} MB, "
                f"{rapor['journal_mode']} modu, yazıcı kuyruğu {rapor['yazici_kuyruk_uzunlugu']} iş.")
    if "kuyruk" in k or "queue" in k:
        istatistik = db.kuyruk_istatistik()
        if not istatistik:
            return "Tüm kuyruklar boş."
        parcalar = [f"{s['kuyruk_adi']}({s['durum']})={s['adet']}" for s in istatistik]
        return "Kuyruk durumları: " + ", ".join(parcalar) + "."
    if "durum" in k or "status" in k:
        m = _metrikleri_hesapla()
        return (f"Sistem: {m['active_agents']}/{m['total_agents']} ajan aktif, "
                f"{m['total_offers']} teklif, {m['pending_requests']} bekleyen talep, "
                f"toplam gelir ${m['total_revenue']:,.0f}, sistem sağlığı %{m['system_health']}.")
    return ""


@app.post("/api/command")
async def komut_al(payload: Dict[str, Any] = Body(...)):
    """JARVIS panel komut konsolu.

    Gövde: {"command": "...", "source": "jarvis_dashboard", "ts": ...}
    Yanıt: {"success": true, "message": "..."} — panel data.message alanını okur.
    """
    komut = (payload.get("command") or "").strip()
    kaynak = payload.get("source") or "bilinmeyen"
    if not komut:
        return {"success": False, "message": "Boş komut gönderilemez."}

    db = _db()
    db.kuyruga_ekle("komutlar", {"komut": komut, "kaynak": kaynak,
                                 "alindi": datetime.now().isoformat()})
    db.log_yaz(seviye="info", modul="jarvis_komut",
               mesaj=f"Komut alındı: {komut}",
               detay={"kaynak": kaynak}, bekle=False)

    yanit = _komut_yaniti(komut)
    if not yanit:
        yanit = (f"Komut kaydedildi ve 'komutlar' kuyruğuna alındı: '{komut}'. "
                 f"Otonom ajanlar tarafından sırayla işlenecek.")
    return {"success": True, "message": yanit, "command": komut, "queued": True}


# ============================================
# BAŞLATMA
# ============================================

@app.on_event("startup")
async def baslangic():
    db = init_database()
    db.log_yaz(seviye="info", modul="ajan_ekosistem_backend",
               mesaj="FastAPI backend başlatıldı (:8000)", bekle=False)


if __name__ == "__main__":
    import uvicorn

    init_database()
    print("=" * 60)
    print("TRM TICARI AJAN EKOSISTEMI BACKEND v2.0")
    print("=" * 60)
    print(f"Merkezi veritabanı: {DB_PATH}")
    print("FastAPI sunucusu başlatılıyor...")
    print("API Dokümantasyonu: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
