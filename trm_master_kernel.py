from pathlib import Path
from copy import deepcopy
import os
from uuid import uuid4

from dispatch_queue_manager import DispatchQueueManager
from trm_live_config import env_bool, get_live_settings, load_trm_environment, public_readiness_report


class MasterOrchestrator:
    """Run safe analysis stages and report missing inputs for a human operator."""

    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parent

    @staticmethod
    def _lines(value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.splitlines() if item.strip()]
        if isinstance(value, (list, tuple)) and all(isinstance(item, str) for item in value):
            return [item.strip() for item in value if item.strip()]
        raise ValueError("Metin listesi string veya string listesi olmalıdır")

    def tam_sistem_dongusunu_baslat(self, context=None):
        load_trm_environment(self.project_root)
        live_settings = get_live_settings()
        if context is None:
            context = {}
        if not isinstance(context, dict):
            raise ValueError("context sözlük olmalıdır")

        inputs = dict(context)
        results = []

        def add(number, name, status, summary, details=None):
            results.append({
                "adim": number,
                "modul": name,
                "durum": status,
                "ozet": summary,
                "detay": details,
            })

        def call(number, name, callback, status="completed"):
            try:
                value = callback()
                add(number, name, status, "Analiz tamamlandı.", value)
                return value
            except Exception as exc:
                add(number, name, "error", f"Modül çalıştırılamadı: {exc.__class__.__name__}")
                return None

        def needs_input(number, name, missing):
            add(number, name, "needs_input", "Gerekli kullanıcı verisi sağlanmadı.", {"eksik_girdiler": missing})

        product = inputs.get("urun_adi") or inputs.get("urun_konsepti")

        from quantum_trend_sentinel import QuantumTrendSentinel
        call(1, "Quantum Trend Sentinel", lambda: {
            **QuantumTrendSentinel(hedef_pazar=inputs.get("hedef_pazar", "Global")).sosyal_dalga_tara(),
            "calisma_turu": "simülasyon",
        }, status="simulated")

        from geo_spatial_niche_profiler import GeoSpatialNicheProfiler
        # Fail-closed: dışarıdan gerçek bölgesel kayıt verilmediği sürece niş
        # üretilmez, sadece red raporlanır.
        call(2, "Geo-Spatial Niche Sentinel", lambda: GeoSpatialNicheProfiler(
            hedef_bolge=inputs.get("hedef_bolge", "Kuşadası / Akdeniz Havzası")
        ).bolgesel_niche_tara(), status="not_configured")

        from gelecek_dalga_kehaneti import GelecekDalgaKehaneti
        call(3, "Gelecek Dalga Senaryosu", lambda: GelecekDalgaKehaneti(
            analiz_ufku=inputs.get("analiz_ufku", "Gelecek 14 Gün")
        ).viral_dalga_tahmin_et(), status="simulated")

        from nor_davranis_gozcusu import NorDavranisGozcusu
        call(4, "Toplu Kitle Etkileşim Sinyali", lambda: NorDavranisGozcusu(
            platform=inputs.get("platform", "TikTok / Reels")
        ).kitle_ruh_hali_analiz_et(), status="simulated")

        if product:
            from ilk_uc_saniye_motoru import kanca_ekle
            call(5, "İlk 3 Saniye Kanca Taslağı", lambda: {
                "urun": product,
                "kanca": kanca_ekle(product, inputs.get("hedef_kitle", "Genel kitle")),
                "disariya_yayin": False,
            }, status="draft_ready")
        else:
            needs_input(5, "İlk 3 Saniye Kanca Taslağı", ["urun_adi"])

        if product:
            from holografik_gorsellestirici import HolografikGorsellestirici
            visual = HolografikGorsellestirici(product).gorsel_ve_mockup_uret()
            visual.pop("preview_svg", None)
            add(6, "Holografik SVG Konsept Önizlemesi", "draft_ready", visual["durum"], visual)
        else:
            needs_input(6, "Holografik SVG Konsept Önizlemesi", ["urun_adi"])

        price_inputs = inputs.get("fiyat_girdileri")
        if isinstance(price_inputs, dict) and all(
            key in price_inputs for key in ("bizim_fiyatimiz", "rakip_fiyatlari")
        ) and product:
            from rakip_fiyat_casusu import RakipFiyatCasusu
            call(7, "Rakip Fiyat Karşılaştırması", lambda: RakipFiyatCasusu(
                inputs.get("hedef_kategori", "Belirtilmedi")
            ).pazar_fiyat_gözlemi_yap(
                product,
                price_inputs["bizim_fiyatimiz"],
                price_inputs["rakip_fiyatlari"],
            ))
        else:
            needs_input(7, "Rakip Fiyat Karşılaştırması", ["urun_adi", "fiyat_girdileri.bizim_fiyatimiz", "fiyat_girdileri.rakip_fiyatlari"])

        profit_inputs = inputs.get("karlilik_girdileri")
        if isinstance(profit_inputs, dict) and product:
            from kar_optimizatoru import KarOptimizatoru
            call(8, "Kârlılık ve Dönüşüm Analizi", lambda: KarOptimizatoru().karlilik_ve_donusum_analizi(
                urun=product,
                **profit_inputs,
            ))
        else:
            needs_input(8, "Kârlılık ve Dönüşüm Analizi", ["urun_adi", "karlilik_girdileri"])

        from dream_to_storefront_pipeline import DreamToStorefrontPipeline
        idea = call(9, "Düş Fabrikası Konsept Taslağı", lambda: DreamToStorefrontPipeline(
            hedef_pazar=inputs.get("hedef_pazar", "Global")
        ).pazar_boslugu_ve_fikir_uret(), status="simulated")
        selected_product = product or (idea or {}).get("konsept_adi")

        supplier = inputs.get("tedarikci_girdileri")
        if isinstance(supplier, dict) and supplier.get("firma_adi") and supplier.get("yetkili_adi"):
            from sesli_muzakere_ajani import SesliMuzakereAjani
            call(10, "Müzakere Konuşma Taslağı", lambda: SesliMuzakereAjani(
                supplier["firma_adi"],
                supplier["yetkili_adi"],
                hedef_iskonto=supplier.get("hedef_iskonto"),
            ).muzakere_taslagi_olustur(), status="draft_ready")
        else:
            needs_input(10, "Müzakere Konuşma Taslağı", ["tedarikci_girdileri.firma_adi", "tedarikci_girdileri.yetkili_adi"])

        if selected_product:
            from coklu_kanal_dagitim_ajani import CokluKanalDagitimAjani
            call(11, "Çoklu Kanal İçerik Taslakları", lambda: CokluKanalDagitimAjani(
                selected_product,
                urun_aciklamasi=inputs.get("urun_aciklamasi", ""),
                urun_linki=inputs.get("urun_linki", ""),
            ).otonom_yayina_basla(inputs.get("kanallar")), status="draft_ready")
        else:
            needs_input(11, "Çoklu Kanal İçerik Taslakları", ["urun_adi veya ürün konsepti"])

        from otonom_ajanlar_mahkemesi import OtonomAjanlarMahkemesi
        court_inputs = inputs.get("mahkeme_girdileri") or {}
        if not isinstance(court_inputs, dict):
            court_inputs = {}
        court_report = OtonomAjanlarMahkemesi(
            inputs.get("karar_konusu", "Ürün lansman incelemesi")
        ).ajanlar_arasi_munazara_ve_karar(
            savunma=court_inputs.get("savunma"),
            itirazlar=self._lines(court_inputs.get("itirazlar")),
            kanitlar=self._lines(court_inputs.get("kanitlar")),
            riskler=self._lines(court_inputs.get("riskler")),
        )
        call(12, "Ajanlar Mahkemesi İnsan İnceleme Taslağı", lambda: court_report,
             status="review_required" if court_report["durum"] != "human_review_ready" else "human_review_ready")

        from oto_onarim_ajani import OtoOnarimAjani
        health_report = call(13, "Salt-Okunur Sistem Sağlığı", lambda: OtoOnarimAjani(
            health_url=inputs.get("health_url", "http://127.0.0.1:5000/health"),
            queue_db=inputs.get("queue_db"),
        ).sistem_sagligini_tara_ve_onar())
        if health_report and health_report["durum"] != "healthy":
            results[-1]["durum"] = "review_required"

        from oz_evrilen_kod_ajani import OzEvrilenKodAjani
        code_report = call(14, "Salt-Okunur Kod ve Prompt İncelemesi", lambda: OzEvrilenKodAjani(
            project_root=self.project_root
        ).kod_ve_prompt_optimizasyonu_tara(), status="review_required")

        if inputs.get("trend_scraping_enabled"):
            from web_scraper import LiveWebScraper

            def scrape_and_queue_trends():
                scraper = LiveWebScraper(sources=inputs.get("trend_sources"))
                trends = scraper.fetch_trends()
                queue_path = inputs.get("queue_db") or self.project_root / "trm_dispatch_queue.db"
                queue = DispatchQueueManager(db_name=str(queue_path))
                tasks = scraper.queue_items(trends)
                for task in tasks:
                    queue.add_to_queue(task)
                return {
                    "trend_sayisi": len(trends),
                    "kuyruga_eklenen": len(tasks),
                    "kaynak_hatalari": scraper.errors,
                }

            trend_result = call(15, "Canli Web Trend Tarama ve Kuyruk", scrape_and_queue_trends, status="queued")
            if trend_result and trend_result["kaynak_hatalari"]:
                results[-1]["durum"] = "review_required" if trend_result["trend_sayisi"] else "error"

        if inputs.get("magaza_api_enabled", live_settings["store"]["enabled"]):
            from magaza_api_koprusu import MagazaAPIBridge

            api_config = inputs.get("magaza_api") or {}
            if not isinstance(api_config, dict):
                api_config = {}
            bridge_options = dict(api_config)
            bridge_options.setdefault(
                "db_path",
                inputs.get("queue_db") or self.project_root / "trm_dispatch_queue.db",
            )
            bridge_options.setdefault("simulate", live_settings["store"]["simulate"])
            bridge_result = call(
                16,
                "Onayli Taslak Magaza API Aktarimi",
                lambda: MagazaAPIBridge(**bridge_options).publish_approved_products(),
                status="simulated" if bridge_options["simulate"] else "completed",
            )
            if bridge_result and bridge_result["durum"] in ("error", "partial_error"):
                results[-1]["durum"] = "error" if bridge_result["durum"] == "error" else "review_required"

        autonomous_campaign_enabled = bool(
            inputs.get(
                "hizli_kazanc_enabled",
                live_settings["autonomous_enabled"],
            )
        )
        if autonomous_campaign_enabled:
            from hizli_kazanc_modulu import HizliKazancModulu

            campaign_options = inputs.get("hizli_kazanc") or {}
            if not isinstance(campaign_options, dict):
                campaign_options = {}
            campaign_options = dict(campaign_options)
            auto_process = campaign_options.pop("auto_process", True)
            live_store = campaign_options.pop("live_store", None)
            api_options = campaign_options.pop("api_options", inputs.get("magaza_api"))
            distribution_mode = campaign_options.pop(
                "distribution_mode",
                live_settings["distribution"]["mode"],
            )
            distribution_channels = campaign_options.pop(
                "distribution_channels",
                live_settings["distribution"]["channels"] if distribution_mode == "live" else None,
            )
            campaign_options.setdefault(
                "queue_db",
                inputs.get("affiliate_queue_db")
                or inputs.get("queue_db")
                or self.project_root / "trm_kuyruk.db",
            )
            campaign_options.setdefault("mode", "simulate")
            campaign_result = call(
                17,
                "Hızlı Kazanç Affiliate Kampanya Taslakları",
                lambda: HizliKazancModulu(**campaign_options).kampanya_uret_ve_kuyruga_ekle(),
                status="simulated" if campaign_options["mode"] == "simulate" else "queued",
            )
            if campaign_result and campaign_result["durum"] in ("error", "partial_error"):
                results[-1]["durum"] = "error" if campaign_result["durum"] == "error" else "review_required"
            if campaign_result and auto_process:
                from gorev_incele_ve_onayla import autonomous_approve_and_transfer

                autonomous_result = call(
                    18,
                    "Otonom Kampanya Doğrulama ve Köprü Aktarımı",
                    lambda: autonomous_approve_and_transfer(
                        campaign_options["queue_db"],
                        live_store=bool(live_store),
                        api_options=api_options if isinstance(api_options, dict) else {},
                        distribution_mode=distribution_mode,
                        distribution_channels=distribution_channels,
                    ),
                    status="completed" if live_store or live_settings["store"]["requested_live"] or distribution_mode == "live" else "simulated",
                )
                if autonomous_result and autonomous_result["durum"] != "completed":
                    results[-1]["durum"] = "review_required"

        affiliate_scout_enabled = inputs.get(
            "affiliate_api_scout_enabled",
            env_bool("TRM_AFFILIATE_SCOUT_ENABLED", False),
        )
        if affiliate_scout_enabled:
            from ai_ajan_affiliate_avcisi import AffiliateApiScout

            scout_result = call(
                19,
                "Affiliate ve API Kaynak Araştırması",
                lambda: AffiliateApiScout().scan_and_write(
                    self.project_root / "affiliate_scout_output"
                ),
                status="completed",
            )
            if scout_result and scout_result.get("errors"):
                results[-1]["durum"] = "review_required"

        completed = sum(item["durum"] not in ("needs_input", "error") for item in results)
        pending_input = [item["modul"] for item in results if item["durum"] == "needs_input"]
        live_store_enabled = bool(
            live_settings["store"]["requested_live"]
            or (
                inputs.get("magaza_api_enabled")
                and isinstance(inputs.get("magaza_api") or {}, dict)
                and not (inputs.get("magaza_api") or {}).get(
                    "simulate",
                    live_settings["store"]["simulate"],
                )
            )
        )
        campaign_config = inputs.get("hizli_kazanc") or {}
        live_distribution_enabled = bool(
            autonomous_campaign_enabled
            and isinstance(campaign_config, dict)
            and campaign_config.get("distribution_mode", live_settings["distribution"]["mode"]) == "live"
        )
        live_publication_enabled = live_store_enabled or live_distribution_enabled
        report = {
            "durum": "ready_for_human_review" if not any(item["durum"] == "error" for item in results) else "attention_required",
            "modul_sayisi": len(results) + 1,
            "calistirilan_adim": len(results) + 1,
            "tamamlanan_veya_incelenecek": completed,
            "girdi_bekleyen_moduller": pending_input,
            "otomatik_yayin": live_publication_enabled,
            "otomatik_fiyat_degistirme": False,
            "otomatik_kod_degistirme": False,
            "adimlar": results,
            "live_readiness": public_readiness_report(live_settings),
            "not": "Hızlı Kazanç zinciri yalnızca hizli_kazanc_enabled ile çalışır; dağıtım simülasyon varsayılanıdır, canlı mağaza ve kanal aktarımı için geçerli API/webhook yapılandırması gerekir.",
        }
        report["adimlar"].append({
            "adim": len(results) + 1,
            "modul": "Nihai Senkronizasyon Özeti",
            "durum": report["durum"],
            "ozet": f"{len(results)} modül adımı işlendi; {len(pending_input)} modül kullanıcı girdisi bekliyor.",
            "detay": {
                "otomatik_yayin": live_publication_enabled,
                "otomatik_fiyat_degistirme": False,
                "otomatik_kod_degistirme": False,
            },
        })
        return report


    def inceleme_kuyruguna_ekle(self, report, db_path=None):
        if not isinstance(report, dict) or not isinstance(report.get("adimlar"), list):
            raise ValueError("Geçerli master kernel raporu gereklidir")
        configured_path = db_path or os.environ.get("TRM_DISPATCH_QUEUE_DB")
        queue_path = (
            Path(configured_path)
            if configured_path
            else Path(__file__).resolve().with_name("trm_dispatch_queue.db")
        )
        task = {
            "account_id": "trm_master_kernel",
            "post_id": f"master-review-{uuid4().hex}",
            "payload": {
                "task_type": "master_orchestration_review",
                "status": "pending_review",
                "report": deepcopy(report),
            },
        }
        DispatchQueueManager(db_name=str(queue_path)).add_to_queue(task)
        return task