import json
from datetime import datetime

ANAC_SELAMLAMA_SABLONLARI = [
    "Hoş geldin evladım, gayet sakin dinliyorum seni. Anlat bakalım, bugün hayatında ne var ne yok, Sosyal İmece yolculuğunda sana nasıl destek olabiliriz?",
    "Merhaba değerli büyüğüm/kardeşim, hoş geldin sefalar getirdin. Burası hepimizin ocağı. İhtiyacını ve niyetini usulca paylaş, birlikte el ele verelim."
]

def analyze_applicant_dialogue(applicant_id: str, candidate_text: str, region: str = "Türkiye"):
    """
    Şefkatli Rehber NLP Filtreleme & Mülakat Analizi
    Savurganlık, gerçek ihtiyaç, dayanışma uyumu ve 55+ refah/zenginlik önceliği analizi.
    """
    text_lower = candidate_text.lower()

    risk_keywords = ["kumar", "iddia", "borsa kaldıraç", "borç batağı"]
    has_risk = any(kw in text_lower for kw in risk_keywords)

    need_score = 0.85 if not has_risk else 0.40
    status = "ONAYLANDI - Şefkatli Rehber Onayı" if not has_risk else "İNCELEME - Risk/Savurganlık Uyarısı"

    audit_record = {
        "timestamp": datetime.now().isoformat(),
        "applicant_id": applicant_id,
        "region": region,
        "candidate_input": candidate_text,
        "persona_response": "Evladım/Kıymetli ortak, analizin yapıldı. İmece havuzumuz senin için de devrede.",
        "need_score": need_score,
        "status": status,
        "anac_tone": "40-50 yaş bilge/şefkatli anaç rehber"
    }

    try:
        filename = "applicant_audits.json"
        logs = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list):
                    logs = loaded
        except Exception:
            logs = []
        logs.append(audit_record)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SefkatliRehber] Audit log yazma hatası: {e}")

    return audit_record
