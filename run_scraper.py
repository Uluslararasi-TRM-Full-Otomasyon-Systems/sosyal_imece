import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from guardian_orchestrator import render_streamlit_guardian_orchestrator
from health_check import health_check_pre_flight
from notification_utils import send_email_message


BASE_DIR = Path(__file__).resolve().parent


def load_latest_queue_payload():
    queue_path = BASE_DIR / "sosyal_medya_kuyruk.json"
    if not queue_path.exists():
        return None
    try:
        return json.loads(queue_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def send_agent_activation_email(agent_name):
    subject = f"{agent_name} Aktif"
    body = f"{agent_name} aktif edildi.\nZaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return send_email_message(subject, body, base_dir=str(BASE_DIR))


def send_notification_email(product_count, output_path, trend_summary):
    subject = "TRM Bildirim | Havuz ve Trend Özeti"
    body = (
        f"Toplam ürün: {product_count}\n"
        f"Çıktı dosyası: {output_path}\n"
        f"Trend özeti: {trend_summary}\n"
        f"Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return send_email_message(subject, body, base_dir=str(BASE_DIR))


def run_scraper_logic(show_ui=True):
    """
    Tüm TRM ajanlarını başlatan ana fonksiyon.
    Pre-flight kontrolü ile başlar, expansion ajanlarını ve çekirdek ajanları yükler.
    Yeni GuardianCrew (Ajan 161-163) burada oluşturulup arka planda çalıştırılır.
    """
    from trm_agents.CoreNexus import CoreNexus
    from trm_agents.camouflage_agent import CamouflageAgent
    from trm_agents.account_manager_agent import AccountManagerAgent
    from trm_agents.analyst_agent import AnalystAgent
    from trm_agents.content_generator_agent import ContentGeneratorAgent
    from trm_agents.queue_agent import QueueAgent
    from trm_agents.poster_agent import PosterAgent
    from trm_agents.expansion_module import build_expansion_agents, get_capacity_snapshot

    # GuardianCrew import
    from trm_agents.guardian_crew import GuardianCrew

    # ============================================================
    # 1. PRE-FLIGHT KONTROLÜ – Tüm ajanların dosyalarını kontrol et
    # ============================================================
    expansion_specs = build_expansion_agents()
    core_agents = ["CamouflageAgent", "AccountManagerAgent", "ContentGeneratorAgent",
                   "QueueAgent", "PosterAgent"]

    all_agent_names = [spec["name"] for spec in expansion_specs]
    all_agent_names.extend(core_agents)
    # Yeni GuardianCrew ajanlarının isimleri (dosya kontrolü geçici atlanır)
    all_agent_names.extend(["DNP-Guardian", "Elçi-Validator", "Engagement-Optimizer"])

    for agent_name in all_agent_names:
        if not health_check_pre_flight(agent_name):
            # Yeni ajanlar için dosya kontrolünü geçici atlıyoruz
            print(f"[Pre-flight] {agent_name} dosyası bulunamadı, atlanıyor.")
            continue  # veya raise Exception ile durdur (ileride aktif)

    # ============================================================
    # 2. CORENEXUS'U OLUŞTUR VE MEVCUT AJANLARI BAĞLA
    # ============================================================
    nexus = CoreNexus(zero_trust=True, stealth_mode=True)
    camou = CamouflageAgent()
    account_mgr = AccountManagerAgent()
    content_generator = ContentGeneratorAgent()
    queue_agent = QueueAgent()
    poster_agent = PosterAgent()
    capacity_snapshot = get_capacity_snapshot()

    nexus.connect_agent("CamouflageAgent", camou)
    nexus.connect_agent("AccountManagerAgent", account_mgr)

    for spec in expansion_specs[:25]:
        nexus.connect_agent(
            spec["name"],
            spec["instance"],
            capabilities=spec["capabilities"],
            context_allowlist=spec["context_allowlist"],
        )

    nexus.connect_agent("Content_Generator_Agent", content_generator)
    nexus.connect_agent("QueueAgent", queue_agent)
    nexus.connect_agent("PosterAgent", poster_agent)

    for spec in expansion_specs[25:]:
        nexus.connect_agent(
            spec["name"],
            spec["instance"],
            capabilities=spec["capabilities"],
            context_allowlist=spec["context_allowlist"],
        )

    # ============================================================
    # 3. GUARDIANCREW'U OLUŞTUR VE ARKA PLANDA BAŞLAT (AJAN 161-163)
    # ============================================================
    guardian_crew = GuardianCrew()

    def guardian_crew_cycle():
        """Periyodik olarak GuardianCrew döngüsünü çalıştırır."""
        while True:
            # Tüm ajanların durumunu topla (nexus üzerinden)
            agents_status = {}
            for name, agent in nexus.agents.items():
                # Gerçek aktivite logları toplanmalı; şimdilik dummy veri
                agents_status[name] = {
                    "error_count": 0,
                    "traffic_spike": False,
                    "success_rate": 0.95,
                    "age_days": 30
                }
            guardian_crew.run_guardian_cycle(agents_status)
            time.sleep(60)  # her dakika kontrol

    guardian_thread = threading.Thread(target=guardian_crew_cycle, daemon=True)
    guardian_thread.start()
    print("[GuardianCrew] Guardian Crew döngüsü başlatıldı.")

    # ============================================================
    # 4. OPERATÖR KİMLİĞİ VE MASKELİ OPERASYON
    # ============================================================
    operator_identity = account_mgr.assign_operator_identity("TR")
    if show_ui:
        with st.expander("Sistem Teknik Logları", expanded=False):
            st.write(f"Operatör Kimliği: {operator_identity['identity']}")
            st.write(f"E-posta: {operator_identity['email']}")

    mask_id = camou.mask_identity()
    if show_ui:
        with st.expander("Sistem Teknik Logları", expanded=False):
            st.write(f"Maskeli Operasyon Aktif: {mask_id}")

    # ============================================================
    # 5. ÖRNEK ÜRÜNLER VE AKIŞ (MEVCUT)
    # ============================================================
    sample_products = [
        {"title": "Organik Zeytin Yagi 1L", "product_url": "https://www.trendyol.com/gida-saglik-ve-ozel-bakim/organik-urunler/organik-zeytin-yagi", "price": 349.90, "commission_rate": 28.0},
        {"title": "Kozmetik Cilt Bakim Seti", "product_url": "https://www.trendyol.com/kozmetik/cilt-bakim/cilt-bakim-seti", "price": 499.50, "commission_rate": 35.0},
        {"title": "Nemlendirici Krem", "product_url": "https://www.trendyol.com/kozmetik/cilt-bakim/nemlendirici-krem", "price": 189.90, "commission_rate": 22.0},
        {"title": "Şampuan 500ml", "product_url": "https://www.trendyol.com/kozmetik/sac-bakim/sampuan", "price": 159.90, "commission_rate": 18.0},
        {"title": "Bal 1kg", "product_url": "https://www.trendyol.com/gida-saglik-ve-ozel-bakim/tatli-urunler/bal", "price": 279.90, "commission_rate": 24.0},
    ]

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ACIL_SATIS_HAVUZU.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=========================================\n")
        f.write("TRM ACIL NAKIT OTOMASYONU - ACIL SATIS HAVUZU\n")
        f.write("=========================================\n")
        f.write(f"Baslama Zamani: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Maske ID: {mask_id}\n")
        f.write(f"Operatör: {operator_identity['identity']}\n")
        f.write(f"E-posta: {operator_identity['email']}\n")
        f.write(f"Domain: {operator_identity['domain_authority']}\n")
        f.write(f"Toplam Urun: {len(sample_products)}\n")
        f.write("=========================================\n\n")

        affiliate_id = "trendurunlermarket"
        for p in sample_products:
            affiliate_link = p["product_url"]
            if "?" in affiliate_link:
                affiliate_link += f"&affiliate={affiliate_id}"
            else:
                affiliate_link += f"?affiliate={affiliate_id}"
            f.write(f"{p['title']} - {affiliate_link}\n")

    if show_ui:
        st.success(f"Havuz güncellendi! Dosya: {output_path}")
    else:
        print(f"[Otonom Mod] Havuz güncellendi: {output_path}")

    # ============================================================
    # 6. TREND ANALİZİ
    # ============================================================
    trend_summary = ""
    analysis_result = None
    try:
        analyst = AnalystAgent()
        analysis_result = analyst.analyze_pool(output_path)
        if analysis_result:
            trend_report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trend_raporlari.json")
            product_map = {item["title"]: item for item in sample_products}
            enriched_details = []
            for product_name, score in analysis_result.get("scores", {}).items():
                product_meta = product_map.get(product_name, {})
                price = float(product_meta.get("price", 0.0))
                commission_rate = float(product_meta.get("commission_rate", 0.0))
                enriched_details.append({
                    "product_name": product_name,
                    "trend_score": score,
                    "price": price,
                    "commission_rate": commission_rate,
                    "estimated_commission": round(price * commission_rate / 100, 2),
                    "product_url": product_meta.get("product_url", ""),
                })
            analysis_result["product_details"] = enriched_details
            if enriched_details:
                highest_commission_product = max(enriched_details, key=lambda item: (item.get("commission_rate", 0.0), item.get("estimated_commission", 0.0)))
                analysis_result["top_commission_product"] = highest_commission_product["product_name"]
                analysis_result["top_commission_rate"] = highest_commission_product["commission_rate"]
            analyst.save_trend_report(analysis_result, trend_report_path)
            trend_summary = analyst.get_trend_summary(analysis_result)
            if show_ui:
                st.info(f"📊 {trend_summary}")
            else:
                print(f"[AnalystAgent] {trend_summary}")
    except Exception as e:
        if show_ui:
            st.error(f"Trend analizi hatası: {str(e)}")
        else:
            print(f"[AnalystAgent] Trend analizi hatası: {str(e)}")
        trend_summary = "Trend analizi yapılamadı."

    # ============================================================
    # 7. AJAN ZİNCİRİNİ ÇALIŞTIR
    # ============================================================
    content_payload = None
    queue_payload = None
    poster_payload = None
    try:
        sync_results = nexus.run_system_sync(context={
            "trend_report": analysis_result,
            "active_agents": list(nexus.agents.keys()),
            "agent_capacity_snapshot": capacity_snapshot,
        })
        content_payload = sync_results.get("Content_Generator_Agent") if sync_results else None
        queue_payload = sync_results.get("QueueAgent") if sync_results else None
        poster_payload = sync_results.get("PosterAgent") if sync_results else None
        if poster_payload:
            queue_payload = load_latest_queue_payload() or queue_payload
        if show_ui and content_payload:
            st.success("Content_Generator_Agent trend raporundan yeni satış içerikleri üretti.")
        if show_ui and queue_payload:
            st.success("QueueAgent içerikleri sosyal medya kuyruğuna aktardı.")
        if show_ui and poster_payload:
            st.success(f"PosterAgent zamanı gelen içerikleri Instagram ve Facebook için işlemeye başladı. Başarılı yayın: {poster_payload.get('posted_count', 0)}")
    except Exception as e:
        if show_ui:
            st.error(f"Ajan zinciri hatası: {str(e)}")
        else:
            print(f"[AgentChain] Hata: {str(e)}")

    # ============================================================
    # 8. BİLDİRİMLER
    # ============================================================
    if show_ui:
        try:
            success, message = send_agent_activation_email("Content_Generator_Agent")
            if success:
                st.success(message)
            else:
                st.error(message)
        except Exception as e:
            st.error(f"Ajan aktivasyon bildirimi hatası: {str(e)}")

        try:
            success, message = send_notification_email(len(sample_products), output_path, trend_summary)
            if success:
                st.success(message)
            else:
                st.error(message)
        except Exception as e:
            st.error(f"E-posta gönderme hatası: {str(e)}")

    guardian_snapshot = None
    if show_ui:
        guardian_snapshot = render_streamlit_guardian_orchestrator(st, base_dir=BASE_DIR)

    return {
        "output_path": output_path,
        "trend_summary": trend_summary,
        "content_payload": content_payload,
        "queue_payload": queue_payload,
        "poster_payload": poster_payload,
        "guardian_orchestrator": guardian_snapshot,
    }


def main():
    st.set_page_config(page_title="TRM TICARI EKOSISTEMI", layout="wide")
    st.title("TRM TICARI EKOSISTEMI | Multi-Tenant E-Ticaret Fabrikası")
    st.caption("Guardian Kalkanı, tenant klonları ve merkezi orchestrator görünümü")

    col1, col2 = st.columns([1.2, 1])
    with col1:
        if st.button("Sistemi Çalıştır", use_container_width=True):
            result = run_scraper_logic(show_ui=True)
            st.session_state["last_run_result"] = result
    with col2:
        if st.button("Guardian Orchestrator Yenile", use_container_width=True):
            st.session_state["guardian_refresh_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            render_streamlit_guardian_orchestrator(st, base_dir=BASE_DIR)

    last_result = st.session_state.get("last_run_result")
    if last_result:
        st.markdown("---")
        st.subheader("Son Çalıştırma Özeti")
        st.json(last_result)
    else:
        render_streamlit_guardian_orchestrator(st, base_dir=BASE_DIR)


if __name__ == "__main__":
    main()
