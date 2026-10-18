import os
import base64
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.security import (
    EmergencyKillSwitch,
    SecurityGateError,
    UnauthorizedSecurityCommand,
)
from core.dpapi_vault import DpapiVaultError, ProtectedLocalVault, WindowsDpapi, migrate_project_secrets_to_vault


MASTER_KEY = "test-only-master-key-0123456789-abcdef"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class FakeProtector:
    def protect(self, plaintext):
        return b"encrypted:" + plaintext

    def unprotect(self, ciphertext):
        if not ciphertext.startswith(b"encrypted:"):
            raise ValueError("invalid fixture ciphertext")
        return ciphertext[len(b"encrypted:"):]


class KillSwitchTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows DPAPI test")
    def test_real_windows_dpapi_vault_roundtrip_and_machine_user_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vault.dpapi"
            vault = ProtectedLocalVault(path=path)
            vault.enroll({"FAHRI_MASTER_SECURE_KEY": MASTER_KEY, "TEST_VALUE": "protected"})

            restored = ProtectedLocalVault(path=path).load()

            self.assertEqual(restored["environment"]["TEST_VALUE"], "protected")
            wrong_binding = ProtectedLocalVault(path=path, protector=WindowsDpapi(), binding="different-binding")
            with self.assertRaises(DpapiVaultError):
                wrong_binding.load()

    def test_dpapi_vault_destroy_overwrites_and_removes_encrypted_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vault.dpapi"
            vault = ProtectedLocalVault(path, protector=FakeProtector(), binding="fixture-binding")
            vault.enroll({"FAHRI_MASTER_SECURE_KEY": MASTER_KEY})

            report = vault.destroy()

        self.assertEqual(report["status"], "shredded_best_effort")
        self.assertEqual(report["passes"], 3)
        self.assertFalse(path.exists())

    def test_missing_master_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            switch = EmergencyKillSwitch(directory, environ={})
            with self.assertRaises(SecurityGateError):
                switch.require_master_key()

    def test_wrong_key_never_destroys_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "data" / "trm_ticari.db"
            target.parent.mkdir()
            target.write_bytes(b"test database content")
            switch = EmergencyKillSwitch(root, environ={"FAHRI_MASTER_SECURE_KEY": MASTER_KEY})

            with self.assertRaises(UnauthorizedSecurityCommand):
                switch.destroy_sensitive_data("incorrect-key")

            self.assertEqual(target.read_bytes(), b"test database content")

    def test_shred_refuses_paths_outside_project_root(self):
        with tempfile.TemporaryDirectory() as project_directory, tempfile.TemporaryDirectory() as outside_directory:
            outside_file = Path(outside_directory) / "keep.txt"
            outside_file.write_text("outside fixture", encoding="utf-8")
            switch = EmergencyKillSwitch(
                project_directory,
                environ={"FAHRI_MASTER_SECURE_KEY": MASTER_KEY},
            )

            with self.assertRaises(SecurityGateError):
                switch.secure_shred_file(outside_file)

            self.assertEqual(outside_file.read_text(encoding="utf-8"), "outside fixture")

    def test_destroy_uses_three_passes_only_for_allowlisted_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "data" / "trm_ticari.db"
            config = root / "config" / "single_active_set.json"
            key_config = root / "api_keys.json"
            source = root / "run_live_worker.py"
            database.parent.mkdir()
            config.parent.mkdir()
            database.write_bytes(b"database fixture" * 100)
            config.write_text('{"fixture": true}', encoding="utf-8")
            key_config.write_text('{"api_key": "fixture"}', encoding="utf-8")
            source.write_text("keep source", encoding="utf-8")
            switch = EmergencyKillSwitch(root, environ={"FAHRI_MASTER_SECURE_KEY": MASTER_KEY})

            with patch("core.security.secrets.token_bytes", return_value=b"x") as random_bytes:
                report = switch.destroy_sensitive_data(MASTER_KEY)

            self.assertEqual(report["status"], "destroyed_best_effort")
            self.assertEqual(report["passes"], 3)
            self.assertEqual(report["shredded_count"], 3)
            self.assertEqual(random_bytes.call_count, 9)
            self.assertFalse(database.exists())
            self.assertFalse(config.exists())
            self.assertFalse(key_config.exists())
            self.assertTrue(source.exists())

    def test_remote_command_uses_signature_without_sending_master_key(self):
        timestamp = 1_800_000_000
        nonce = "one-time-test-nonce"
        signature = EmergencyKillSwitch.sign_remote_command(MASTER_KEY, "STOP", timestamp, nonce)
        session = FakeSession(FakeResponse({
            "command": "STOP",
            "issued_at": timestamp,
            "nonce": nonce,
            "signature": signature,
        }))
        switch = EmergencyKillSwitch(
            ".",
            environ={
                "FAHRI_MASTER_SECURE_KEY": MASTER_KEY,
                "FAHRI_KILL_SWITCH_URL": "https://control.example.test/kill-switch",
            },
            session=session,
            clock=lambda: timestamp,
        )

        self.assertEqual(switch.poll_remote_command(), "STOP")
        sent_headers = session.calls[0][1]["headers"]
        self.assertNotIn("Authorization", sent_headers)
        self.assertNotIn(MASTER_KEY, repr(session.calls[0]))
        with self.assertRaises(UnauthorizedSecurityCommand):
            switch.verify_signed_command({
                "command": "STOP",
                "issued_at": timestamp,
                "nonce": nonce,
                "signature": signature,
            })

    def test_worker_without_key_stops_before_opening_database(self):
        import run_live_worker

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "worker.db"
            with patch.dict(os.environ, {}, clear=True), patch(
                "run_live_worker.load_trm_environment", return_value=None
            ), patch("run_live_worker.DB_PATH", db_path), patch(
                "run_live_worker.CONFIG_PATH", Path(directory) / "active.json"
            ), patch("sys.argv", ["run_live_worker.py", "--once"]):
                self.assertEqual(run_live_worker.main(), 78)
            self.assertFalse(db_path.exists())

    def test_dpapi_migration_verifies_vault_before_shredding_plaintext_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "secrets.env"
            source.write_text(
                f"FAHRI_MASTER_SECURE_KEY={MASTER_KEY}\nTELEGRAM_BOT_TOKEN=test-token\nlegacy malformed line\n",
                encoding="utf-8",
            )
            service_account_fixture = b'{"type":"service_account","private_key":"fixture-private-key"}'
            (root / "service_account.json").write_bytes(service_account_fixture)
            vault_path = root / "local-vault.dpapi"
            vault = ProtectedLocalVault(vault_path, protector=FakeProtector(), binding="test-device-user")

            report = migrate_project_secrets_to_vault(root, vault=vault, remove_source=True)
            restored = ProtectedLocalVault(
                vault_path,
                protector=FakeProtector(),
                binding="test-device-user",
            ).load()

        self.assertEqual(report["status"], "enrolled")
        self.assertIn("secrets.env", report["source_files_removed"])
        self.assertIn("service_account.json", report["source_files_removed"])
        self.assertFalse(source.exists())
        self.assertFalse((root / "service_account.json").exists())
        self.assertEqual(restored["environment"]["TELEGRAM_BOT_TOKEN"], "test-token")
        legacy = base64.b64decode(restored["legacy_secrets_env_b64"]).decode("utf-8")
        self.assertIn("legacy malformed line", legacy)
        restored_vault = ProtectedLocalVault(vault_path, protector=FakeProtector(), binding="test-device-user")
        self.assertEqual(restored_vault.load_protected_file("service_account.json"), service_account_fixture)


if __name__ == "__main__":
    unittest.main()
