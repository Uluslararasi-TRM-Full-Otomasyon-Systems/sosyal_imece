import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from endeksa_integration import (EndeksaRegionMetrics,
                                 compute_sosyal_imece_asset_multiplier,
                                 fetch_region_valuation)
from geo_spatial_niche_profiler import GeoSpatialNicheProfiler
from hoodmaps_integration import mahalle_profili

from trm_agents.endeksa_integration import EndeksaIntegration
from trm_agents.geospy_integration import GeoSpyIntegration
from trm_agents.hoodmaps_integration import HoodmapsIntegration
from trm_agents.master_geo_intelligence_agent import MasterGeoIntelligenceAgent
from trm_agents.withraven_integration import WithRavenIntegration

# Bu testler hiçbir sentetik değerin geri gelmesine izin vermez: uydurma skor
# ve tüketici profili üreten alan adları yasaklı listedir.
YASAK_ALANLAR = ("confidence", "confidence_score", "target_score", "fit_score",
                 "niche_confidence", "conversion_probability", "relevance_score",
                 "overall_relevance", "engagement_rate", "demographics",
                 "behavioral_segments", "luxury_index", "household_income",
                 "age_range", "internet_penetration", "purchasing_power")


def _yasa_ihlali(deger, yol="kok"):
    if isinstance(deger, dict):
        ihlaller = []
        for anahtar, ic in deger.items():
            if str(anahtar) in YASAK_ALANLAR:
                ihlaller.append(f"{yol}.{anahtar}")
            else:
                ihlaller += _yasa_ihlali(ic, f"{yol}.{anahtar}")
        return ihlaller
    if isinstance(deger, (list, tuple)):
        ihlaller = []
        for indeks, eleman in enumerate(deger):
            ihlaller += _yasa_ihlali(eleman, f"{yol}[{indeks}]")
        return ihlaller
    return []


class SentetikGeoSkorYokTests(unittest.TestCase):
    def test_kok_endeksa_lisanssiz_istede_carpan_uretmaz(self):
        sonuc = fetch_region_valuation("Aydın", "Kuşadası")
        self.assertEqual(sonuc["durum"], "not_configured")
        self.assertIsNone(sonuc["metrik"])
        self.assertTrue(sonuc["sebep"])
        self.assertEqual(_yasa_ihlali(sonuc), [])

        carpan = compute_sosyal_imece_asset_multiplier(sonuc)
        self.assertEqual(carpan["durum"], "not_configured")
        self.assertIsNone(carpan["carpan"])

    def test_endeksa_carpani_yalnizca_licansli_metrik_ile_hesaplanir(self):
        # Sahte sözlük girdisiyle hesap yapılmaz...
        self.assertEqual(
            compute_sosyal_imece_asset_multiplier(
                {"durum": "ok", "metrik": {"regional_wealth_index": 99}}
            )["durum"], "not_configured")
        # ...doğrulanmış metrik taşındığında çarpan aralıkta kalır.
        metrik = EndeksaRegionMetrics(
            city="Aydın", district="Kuşadası", neighborhood=None,
            avg_sqm_price_try=45000.0, annual_rental_yield_pct=6.0,
            amortization_years=16.0, regional_wealth_index=70.0,
            data_confidence_score=0.9)
        carpan = compute_sosyal_imece_asset_multiplier(
            {"durum": "ok", "metrik": metrik})
        self.assertEqual(carpan["durum"], "ok")
        self.assertGreaterEqual(carpan["carpan"], 0.85)
        self.assertLessEqual(carpan["carpan"], 1.35)

    def test_kok_hoodmaps_uydurma_demografi_donmez(self):
        profil = mahalle_profili("Aydın", "Kuşadası", "İnönü")
        self.assertEqual(profil["durum"], "not_configured")
        self.assertEqual(_yasa_ihlali(profil), [])

    def test_niche_profiler_giris_yoksa_niche_uydurmaz(self):
        rapor = GeoSpatialNicheProfiler(hedef_bolge="Kuşadası").bolgesel_niche_tara()
        self.assertEqual(rapor["durum"], "not_configured")
        self.assertIsNone(rapor["tespit_edilen_niche"])
        self.assertFalse(rapor["canli_hava_ve_koordinat_verisi"])

    def test_trm_agents_geo_modulleri_her_yontemde_red_doner(self):
        endeksa, geospy = EndeksaIntegration(), GeoSpyIntegration()
        hoodmaps, withraven = HoodmapsIntegration(), WithRavenIntegration()
        cagrilar = {
            "endeksa": [
                ("get_premium_districts", lambda: endeksa.get_premium_districts("Aydın")),
                ("get_high_value_locations", lambda: endeksa.get_high_value_locations()),
                ("get_elite_audience_profile", lambda: endeksa.get_elite_audience_profile("Kuşadası")),
                ("analyze_luxury_product_fit", lambda: endeksa.analyze_luxury_product_fit({}, [])),
            ],
            "geospy": [
                ("analyze_image_location", lambda: geospy.analyze_image_location(b"veri")),
                ("verify_location_claim", lambda: geospy.verify_location_claim("Aydın", b"veri")),
                ("get_location_intelligence", lambda: geospy.get_location_intelligence("Aydın")),
                ("analyze_geographic_relevance",
                 lambda: geospy.analyze_geographic_relevance({"title": "x"}, ["Aydın"])),
            ],
            "hoodmaps": [
                ("get_neighborhood_demographics", lambda: hoodmaps.get_neighborhood_demographics("Aydın")),
                ("get_cultural_insights", lambda: hoodmaps.get_cultural_insights("Aydın")),
                ("analyze_target_audience", lambda: hoodmaps.analyze_target_audience("Aydın", "elektronik")),
                ("analyze_luxury_targeting", lambda: hoodmaps.analyze_luxury_targeting("Aydın")),
            ],
            "withraven": [
                ("process_geographic_data", lambda: withraven.process_geographic_data({})),
                ("analyze_behavioral_patterns", lambda: withraven.analyze_behavioral_patterns({})),
                ("generate_decision_support", lambda: withraven.generate_decision_support({})),
                ("integrate_dnp_data", lambda: withraven.integrate_dnp_data({})),
            ],
        }
        for ad, yontemler in cagrilar.items():
            for yontem_adi, cagrir in yontemler:
                sonuc = cagrir()
                if isinstance(sonuc, list):
                    # Liste dönen yöntemler boş döner: "bölge var" izlenimi
                    # veren yarım doğrulanmış kayıt üretilmez.
                    self.assertEqual(sonuc, [], f"{ad}.{yontem_adi} veri uydurdu")
                    continue
                self.assertEqual(sonuc["durum"], "not_configured",
                                 f"{ad}.{yontem_adi} veri uydurdu")
                self.assertEqual(_yasa_ihlali(sonuc), [],
                                 f"{ad}.{yontem_adi} yasak alan taşıyor")

    def test_geospy_toplu_dogrulama_sonucu_dogrulanmamis_birakir(self):
        sonuclar = GeoSpyIntegration().batch_verify_images([(b"xyz", "Aydın")])
        self.assertEqual(len(sonuclar), 1)
        self.assertIsNone(sonuclar[0]["is_verified"])
        self.assertEqual(sonuclar[0]["durum"], "not_configured")

    def test_master_agent_skor_uretmez(self):
        agent = MasterGeoIntelligenceAgent(agent_id=168)
        agent._save_analysis_result = lambda sonuc: True
        sonuc = agent.run(target_location="Aydın")
        self.assertEqual(sonuc["durum"], "not_configured")
        self.assertIsNone(sonuc["overall_intelligence_score"])
        self.assertEqual(sonuc["canli_modul_sayisi"], 0)
        self.assertEqual(_yasa_ihlali(sonuc), [])

    def test_master_agent_tuketici_hedefleme_metodlari_kaldirildi(self):
        for metod in ("analyze_demographic_targeting", "analyze_luxury_targeting",
                      "_calculate_intelligence_score"):
            self.assertFalse(hasattr(MasterGeoIntelligenceAgent, metod),
                             f"{metod} geri gelmiş")

    def test_fusion_raporu_modullerin_kendi_durumunu_yazar(self):
        from trm_agents.geo_fusion_core import _durum
        for servis, konu in ((HoodmapsIntegration(), "get_cultural_insights"),
                             (GeoSpyIntegration(), "get_location_intelligence"),
                             (EndeksaIntegration(), "analyze_luxury_product_fit"),
                             (WithRavenIntegration(), "process_geographic_data")):
            bilgi = _durum(servis, konu)
            self.assertEqual(bilgi["durum"], "not_configured")
            self.assertIsNone(bilgi["veri"])
            self.assertTrue(bilgi["sebep"])


if __name__ == "__main__":
    unittest.main()
