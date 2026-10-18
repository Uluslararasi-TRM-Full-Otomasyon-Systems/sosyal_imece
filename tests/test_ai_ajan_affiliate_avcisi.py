import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_ajan_affiliate_avcisi import AffiliateApiScout, SOURCE_REGISTRY
from hizli_kazanc_modulu import HizliKazancModulu
from trm_master_kernel import MasterOrchestrator


class FakeResponse:
    status_code = 200

    def __init__(self, content, url):
        self.content = content.encode("utf-8")
        self.url = url

    def raise_for_status(self):
        return None


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.requested = []

    def get(self, url, **kwargs):
        self.requested.append((url, kwargs))
        return self.responses[url]


class AffiliateApiScoutTests(unittest.TestCase):
    def _source(self):
        return {
            "id": "fixture_network",
            "name": "Fixture Network",
            "program_type": "affiliate_network",
            "official_hosts": ("docs.example.test",),
            "pages": (
                {"kind": "documentation", "url": "https://docs.example.test/api"},
                {"kind": "application", "url": "https://docs.example.test/apply"},
            ),
            "api_separate": {
                "kind": "marketplace_seller_api_not_affiliate_api",
                "note": "Separate partner scope.",
                "documented_pages": ["https://docs.example.test/seller-api"],
            },
        }

    def test_extracts_only_documented_endpoints_auth_links_and_rate_evidence(self):
        docs = """<html><title>API documentation</title>
        <main>POST https://api.docs.example.test/query Authorization: Bearer token
        Required fields companyId partnerIds and pid. Use https://api.docs.example.test/oauth/token.</main>
        <a href='/authentication'>API authentication docs</a></html>"""
        application = """<html><title>Partner application</title>
        <main>Up to 25% commission on selected offers.</main>
        <a href='/signup'>Apply now</a>
        <script type='application/ld+json'>{"@type":"Product","name":"Example item","category":"Home","offers":{"price":"29.99","priceCurrency":"USD"}}</script>
        </html>"""
        session = FakeSession({
            "https://docs.example.test/api": FakeResponse(docs, "https://docs.example.test/api"),
            "https://docs.example.test/apply": FakeResponse(application, "https://docs.example.test/apply"),
        })
        result = AffiliateApiScout(session=session, sources=[self._source()]).scan_all()
        network = result["networks"][0]

        self.assertEqual(network["api_base_urls"], ["https://api.docs.example.test/query"])
        self.assertEqual(network["token_endpoints"], ["https://api.docs.example.test/oauth/token"])
        self.assertTrue(any("Bearer" in item for item in network["auth_schemes"]))
        self.assertIn("companyId", network["integration_parameters"])
        self.assertTrue(network["application_links"])
        self.assertEqual(network["commission_route_candidates"][0]["advertised_percent"], 25.0)
        self.assertEqual(network["products"][0]["name"], "Example item")
        self.assertFalse(result["safety"]["live_flags_modified"])
        self.assertEqual(len(session.requested), 2)

    def test_rejects_redirect_outside_official_allowlist(self):
        session = FakeSession({
            "https://docs.example.test/api": FakeResponse("<html/>", "https://evil.example.net/collect"),
            "https://docs.example.test/apply": FakeResponse("<html/>", "https://evil.example.net/collect"),
        })

        result = AffiliateApiScout(session=session, sources=[self._source()]).scan_all()

        self.assertEqual(result["networks"][0]["status"], "error")
        self.assertEqual(len(result["errors"]), 2)
        self.assertTrue(all("allowlist" in item["error"] for item in result["errors"]))

    def test_writes_disabled_template_without_touching_secrets_file(self):
        html = "<html><title>Source</title><main>No public API metadata.</main></html>"
        session = FakeSession({
            "https://docs.example.test/api": FakeResponse(html, "https://docs.example.test/api"),
            "https://docs.example.test/apply": FakeResponse(html, "https://docs.example.test/apply"),
        })
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "research"
            secrets_file = Path(directory) / "secrets.env"
            secrets_file.write_text("KEEP_EXISTING=untouched\n", encoding="utf-8")
            report = AffiliateApiScout(session=session, sources=[self._source()]).scan_and_write(output_dir)
            template = Path(report["artifacts"]["safe_template"]).read_text(encoding="utf-8")
            guide = Path(report["artifacts"]["integration_guide"]).read_text(encoding="utf-8")
            saved_report = json.loads(Path(report["artifacts"]["report"]).read_text(encoding="utf-8"))

            self.assertEqual(secrets_file.read_text(encoding="utf-8"), "KEEP_EXISTING=untouched\n")

        self.assertIn("TRM_AFFILIATE_SCOUT_ENABLED=0", template)
        self.assertIn("TRM_AUTONOMOUS_DISTRIBUTION_ENABLED=0", template)
        self.assertIn("TRM_STORE_SIMULATE=1", template)
        self.assertIn("marketplace_seller_api_not_affiliate_api", template)
        self.assertIn("Do not use the generic `/v1/oauth/token`", guide)
        self.assertIn("https://influencer.trendyol.com/forms", guide)
        self.assertFalse(saved_report["safety"]["secret_values_written"])
        self.assertFalse(saved_report["secrets_read"])

    def test_fast_cash_ranks_only_sourced_claims(self):
        ranked = HizliKazancModulu.rank_affiliate_research({
            "highest_public_commission_claims": [
                {"network_id": "one", "advertised_percent": 12, "source_url": "https://official.example.test/rate"},
                {"network_id": "two", "advertised_percent": 30, "source_url": "https://official.example.test/terms"},
                {"network_id": "unsafe", "advertised_percent": 100, "source_url": "http://untrusted.example.test/rate"},
                {"network_id": "invalid", "advertised_percent": "unknown", "source_url": "https://official.example.test/rate"},
            ]
        })

        self.assertEqual([item["network_id"] for item in ranked], ["two", "one"])
        self.assertTrue(all(item["classification"] == "public_commission_claim_requires_program_terms_verification" for item in ranked))

    def test_official_static_metadata_has_evidence_and_no_inferred_token_endpoint(self):
        cj = next(source for source in SOURCE_REGISTRY if source["id"] == "cj_publisher")
        awin = next(source for source in SOURCE_REGISTRY if source["id"] == "awin_publisher")

        self.assertEqual(cj["verified_metadata"]["api_base_urls"], ["https://ads.api.cj.com/query"])
        self.assertTrue(cj["verified_metadata"]["credential_creation_urls"])
        self.assertNotIn("token_endpoint", cj["verified_metadata"])
        self.assertEqual(awin["verified_metadata"]["api_base_urls"], ["https://api.awin.com"])
        self.assertTrue(any("publisherId" in key for key in awin["verified_metadata"]["integration_parameters"]))
        self.assertTrue(awin["verified_metadata"]["evidence_urls"])

    def test_magazanolsun_package_claims_are_not_ranked_as_affiliate_commissions(self):
        html = """<html><main>Mağazanolsun PREMIUM paketi %100 kazanç oranı sunar.</main></html>"""
        source = {
            "id": "magazanolsun",
            "name": "Mağazanolsun",
            "program_type": "managed_store_and_referral",
            "official_hosts": ("www.magazanolsun.com",),
            "pages": ({"kind": "program", "url": "https://www.magazanolsun.com/"},),
            "api_separate": None,
        }
        result = AffiliateApiScout(
            session=FakeSession({
                "https://www.magazanolsun.com/": FakeResponse(html, "https://www.magazanolsun.com/"),
            }),
            sources=[source],
        ).scan_all()

        self.assertEqual(result["networks"][0]["commission_claims"][0]["classification"], "package_earnings_claim_requires_terms_verification")
        self.assertEqual(result["highest_public_commission_claims"], [])

    def test_kernel_can_run_scout_without_enabling_live_campaigns(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("oto_onarim_ajani.socket.create_connection"), patch(
                "oto_onarim_ajani.urlopen", side_effect=OSError
            ), patch(
                "ai_ajan_affiliate_avcisi.AffiliateApiScout.scan_and_write",
                return_value={"networks": [], "errors": []},
            ):
                report = MasterOrchestrator(project_root=directory).tam_sistem_dongusunu_baslat({
                    "affiliate_api_scout_enabled": True,
                    "queue_db": Path(directory) / "health.db",
                    "health_url": "http://127.0.0.1:1/health",
                })

        steps = {item["modul"]: item for item in report["adimlar"]}
        self.assertIn("Affiliate ve API Kaynak Araştırması", steps)
        self.assertNotIn("Hızlı Kazanç Affiliate Kampanya Taslakları", steps)
        self.assertFalse(report["otomatik_yayin"])


if __name__ == "__main__":
    unittest.main()
