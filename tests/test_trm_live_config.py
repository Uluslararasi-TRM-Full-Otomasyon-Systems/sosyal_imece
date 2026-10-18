import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trm_live_config import get_live_settings, load_trm_environment, public_readiness_report


class TrmLiveConfigTests(unittest.TestCase):
    def test_live_settings_report_missing_requirements_without_secret_values(self):
        settings = get_live_settings({
            "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED": "1",
            "TRM_MAGAZA_API_ENABLED": "true",
            "TRM_STORE_SIMULATE": "false",
            "TRM_DISTRIBUTION_MODE": "live",
            "TELEGRAM_BOT_TOKEN": "test-secret-value",
        })

        report = public_readiness_report(settings)
        self.assertTrue(report["autonomous_enabled"])
        self.assertFalse(report["store"]["ready"])
        self.assertFalse(report["distribution"]["ready"])
        self.assertFalse(report["live_production_ready"])
        self.assertIn("TRM_STORE_API_BASE_URL", report["store"]["missing"])
        self.assertIn("TRM_STORE_API_BASE_URL", report["live_missing"])
        self.assertNotIn("test-secret-value", repr(report), "secret must not be exposed")

    def test_live_settings_are_ready_with_test_credentials_and_endpoints(self):
        settings = get_live_settings({
            "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED": "yes",
            "TRM_MAGAZA_API_ENABLED": "1",
            "TRM_STORE_SIMULATE": "0",
            "TRM_STORE_API_BASE_URL": "https://store.example.test/v1",
            "TRM_STORE_TOKEN_URL": "https://store.example.test/oauth/token",
            "TRM_STORE_CLIENT_ID": "test-client",
            "TRM_STORE_CLIENT_SECRET": "test-secret",
            "TELEGRAM_BOT_TOKEN": "test-bot-token",
            "TELEGRAM_CHAT_ID": "-100123456",
            "TRM_SOCIAL_DISTRIBUTION_WEBHOOK_URL": "https://hooks.example.test/social",
            "TRM_DISTRIBUTION_MODE": "live",
        })

        self.assertTrue(settings["ready"])
        self.assertTrue(settings["live_production_ready"])
        self.assertFalse(settings["store"]["simulate"])
        self.assertIn("telegram", settings["distribution"]["channels"])
        self.assertIn("social_media", settings["distribution"]["channels"])

    def test_loader_does_not_read_project_plaintext_env_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "secrets.env").write_text(
                "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED=1\nTRM_STORE_CLIENT_SECRET=file-secret\n",
                encoding="utf-8",
            )
            (root / ".env").write_text("TRM_STORE_ACCESS_TOKEN=plain-file-token\n", encoding="utf-8")
            with patch.dict(os.environ, {}, clear=True), patch(
                "core.dpapi_vault.load_protected_environment", return_value=None
            ):
                loaded = load_trm_environment(root)
                self.assertIsNone(loaded)
                self.assertNotIn("TRM_STORE_CLIENT_SECRET", os.environ)
                self.assertNotIn("TRM_STORE_ACCESS_TOKEN", os.environ)


if __name__ == "__main__":
    unittest.main()
