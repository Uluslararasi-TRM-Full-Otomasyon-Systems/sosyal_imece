"""Fail-closed emergency stop and best-effort sensitive-file shredding.

This module never destroys data because a key is missing or invalid. Destruction
requires an authenticated, exact DESTROY command. File overwrite is best effort;
SSDs, snapshots, journals and backups can retain prior blocks.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import stat
import time
from pathlib import Path
from urllib.parse import urlsplit

import requests
from core.dpapi_vault import DpapiVaultError, ProtectedLocalVault


class SecurityGateError(RuntimeError):
    """Security configuration is absent or invalid; the worker must not run."""


class UnauthorizedSecurityCommand(SecurityGateError):
    """A security command could not be authenticated."""


class EmergencyKillSwitch:
    MASTER_KEY_ENV = "FAHRI_MASTER_SECURE_KEY"
    MASTER_KEY_FILE_ENV = "FAHRI_MASTER_SECURE_KEY_FILE"
    REMOTE_URL_ENV = "FAHRI_KILL_SWITCH_URL"
    REMOTE_TIMEOUT_SECONDS = 5
    REMOTE_MAX_AGE_SECONDS = 60
    REMOTE_MAX_RESPONSE_BYTES = 32768
    SHRED_PASSES = 3
    SHRED_BLOCK_SIZE = 1024 * 1024
    ALLOWED_COMMANDS = {"STOP", "DESTROY"}

    def __init__(self, project_root=None, environ=None, session=None, clock=None, require_dpapi_enrollment=False):
        self.project_root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
        self.environ = os.environ if environ is None else environ
        self.session = session or requests.Session()
        self.clock = clock or time.time
        self.master_key = self._read_master_key()
        self.require_dpapi_enrollment = require_dpapi_enrollment
        self.protected_vault_data = None
        self.protected_vault = None
        if require_dpapi_enrollment:
            try:
                self.protected_vault = ProtectedLocalVault()
                self.protected_vault_data = self.protected_vault.load()
            except DpapiVaultError as exc:
                raise SecurityGateError(f"Protected local identity is invalid: {exc}") from exc
            if self.protected_vault_data is not None:
                self.master_key = str(
                    self.protected_vault_data.get("environment", {}).get(self.MASTER_KEY_ENV, "")
                )
        self._seen_nonces = set()

    @staticmethod
    def sign_remote_command(master_key, command, issued_at, nonce):
        message = f"{command}\n{issued_at}\n{nonce}".encode("utf-8")
        return hmac.new(master_key.encode("utf-8"), message, hashlib.sha256).hexdigest()

    def _read_master_key(self):
        value = str(self.environ.get(self.MASTER_KEY_ENV, "")).strip()
        if not value:
            key_file = str(self.environ.get(self.MASTER_KEY_FILE_ENV, "")).strip()
            if key_file:
                path = Path(key_file).expanduser()
                try:
                    if path.is_symlink() or not path.is_file():
                        raise SecurityGateError("Master key file must be a regular, non-symlink file")
                    if os.name != "nt" and stat.S_IMODE(path.stat().st_mode) & 0o077:
                        raise SecurityGateError("Master key file permissions must be owner-only (0600)")
                    value = path.read_text(encoding="utf-8").strip()
                except OSError as exc:
                    raise SecurityGateError("Master key file could not be read") from exc
        if len(value) < 32:
            return None
        return value

    def require_master_key(self):
        if self.require_dpapi_enrollment and self.protected_vault_data is None:
            raise SecurityGateError("DPAPI device enrollment missing; run core/security.py --enroll on this trusted computer")
        if not self.master_key:
            raise SecurityGateError(
                "FAHRI_MASTER_SECURE_KEY (32+ chars) or a protected FAHRI_MASTER_SECURE_KEY_FILE is required"
            )
        return True

    def verify_key(self, supplied_key):
        self.require_master_key()
        candidate = str(supplied_key or "")
        if not hmac.compare_digest(self.master_key, candidate):
            raise UnauthorizedSecurityCommand("Master key mismatch; worker locked. No files were destroyed.")
        return True

    def verify_signed_command(self, payload):
        self.require_master_key()
        if not isinstance(payload, dict):
            raise UnauthorizedSecurityCommand("Remote command payload must be a JSON object")
        command = str(payload.get("command", "")).strip().upper()
        issued_at = payload.get("issued_at")
        nonce = str(payload.get("nonce", "")).strip()
        signature = str(payload.get("signature", "")).strip().lower()
        if command not in self.ALLOWED_COMMANDS or not nonce or len(nonce) > 128:
            raise UnauthorizedSecurityCommand("Remote command fields are invalid")
        try:
            issued_at = int(issued_at)
        except (TypeError, ValueError) as exc:
            raise UnauthorizedSecurityCommand("Remote command timestamp is invalid") from exc
        if abs(self.clock() - issued_at) > self.REMOTE_MAX_AGE_SECONDS:
            raise UnauthorizedSecurityCommand("Remote command is expired or not yet valid")
        if nonce in self._seen_nonces:
            raise UnauthorizedSecurityCommand("Remote command replay rejected")
        expected = self.sign_remote_command(self.master_key, command, issued_at, nonce)
        if not hmac.compare_digest(expected, signature):
            raise UnauthorizedSecurityCommand("Remote command signature is invalid")
        self._seen_nonces.add(nonce)
        if len(self._seen_nonces) > 2048:
            self._seen_nonces.pop()
        return command

    def poll_remote_command(self):
        """Poll optional HTTPS control endpoint; master key is never sent over network."""
        self.require_master_key()
        endpoint = str(self.environ.get(self.REMOTE_URL_ENV, "")).strip()
        if not endpoint:
            return None
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise SecurityGateError("Kill-switch endpoint must be a credential-free HTTPS URL")
        response = self.session.get(
            endpoint,
            headers={"Accept": "application/json"},
            timeout=self.REMOTE_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
        if response.status_code == 204:
            return None
        if response.status_code != 200:
            raise SecurityGateError(f"Kill-switch endpoint returned HTTP {response.status_code}")
        if len(getattr(response, "content", b"")) > self.REMOTE_MAX_RESPONSE_BYTES:
            raise SecurityGateError("Kill-switch endpoint response exceeds configured size limit")
        try:
            payload = response.json()
        except (ValueError, AttributeError) as exc:
            raise SecurityGateError("Kill-switch endpoint did not return valid JSON") from exc
        return self.verify_signed_command(payload)

    def sensitive_files(self):
        """Return the fixed allowlist of data/config/log files under project_root."""
        root = self.project_root
        candidates = [
            root / "config" / "single_active_set.json",
            root / "secrets.env",
            root / "config.env",
            root / "api_keys.json",
            root / "config.json",
            root / "config.yml",
            root / "config.yaml",
            root / "global_config.json",
            root / "agent_config.json",
            root / "entegrasyon_config.json",
            root / ".streamlit" / "secrets.toml",
        ]
        configured_key_file = str(self.environ.get(self.MASTER_KEY_FILE_ENV, "")).strip()
        if configured_key_file:
            key_path = Path(configured_key_file).expanduser()
            try:
                key_path.resolve(strict=False).relative_to(root)
                candidates.append(key_path)
            except (OSError, ValueError):
                pass
        env_path = root / ".env"
        if env_path.is_file():
            candidates.append(env_path)

        for base in (root, root / "data"):
            if base.is_dir() and not base.is_symlink():
                for pattern in ("*.db", "*.sqlite", "*.sqlite3", "*.db-wal", "*.db-shm", "*.db-journal"):
                    candidates.extend(base.glob(pattern))
        config_dir = root / "config"
        if config_dir.is_dir() and not config_dir.is_symlink():
            candidates.extend(config_dir.rglob("*.json"))
        for log_dir in (root / "logs", root / "logs_social"):
            if log_dir.is_dir() and not log_dir.is_symlink():
                candidates.extend(log_dir.rglob("*.log"))
                candidates.extend(log_dir.rglob("*.jsonl"))
        candidates.extend(root.glob("*.log"))
        candidates.extend(root.glob("*.jsonl"))

        unique = {}
        for candidate in candidates:
            try:
                relative = candidate.absolute().relative_to(root)
            except ValueError:
                continue
            if any(part in {".git", ".venv", "venv", "node_modules"} for part in relative.parts):
                continue
            if candidate.exists() or candidate.is_symlink():
                unique[str(candidate.absolute())] = candidate
        return sorted(unique.values(), key=lambda item: str(item).casefold())

    def secure_shred_file(self, path, passes=SHRED_PASSES):
        if passes < self.SHRED_PASSES:
            raise ValueError(f"At least {self.SHRED_PASSES} overwrite passes are required")
        candidate = Path(path)
        try:
            absolute = candidate.absolute()
            relative = absolute.relative_to(self.project_root)
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(self.project_root)
        except (OSError, ValueError) as exc:
            raise SecurityGateError("Refusing to shred a path outside the project root") from exc
        parent = self.project_root
        for component in relative.parts[:-1]:
            parent = parent / component
            if parent.is_symlink():
                raise SecurityGateError("Refusing to shred a path beneath a symlink directory")
        if candidate.is_symlink():
            return {"path": str(candidate), "status": "skipped_symlink", "passes": 0}
        try:
            info = candidate.stat()
        except FileNotFoundError:
            return {"path": str(candidate), "status": "already_absent", "passes": 0}
        if not stat.S_ISREG(info.st_mode):
            return {"path": str(candidate), "status": "skipped_non_regular", "passes": 0}
        if info.st_nlink != 1:
            return {"path": str(candidate), "status": "skipped_hardlink", "passes": 0}

        size = info.st_size
        try:
            with candidate.open("r+b", buffering=0) as handle:
                for _pass_index in range(passes):
                    handle.seek(0)
                    remaining = size
                    while remaining:
                        chunk_size = min(remaining, self.SHRED_BLOCK_SIZE)
                        handle.write(secrets.token_bytes(chunk_size))
                        remaining -= chunk_size
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.truncate(0)
                handle.flush()
                os.fsync(handle.fileno())
            candidate.unlink()
            return {"path": str(candidate), "status": "shredded_best_effort", "passes": passes, "bytes_overwritten": size * passes}
        except OSError as exc:
            raise SecurityGateError(f"Could not securely overwrite {candidate.name}: {exc.__class__.__name__}") from exc

    def destroy_sensitive_data(self, supplied_key):
        self.verify_key(supplied_key)
        results = []
        failures = []
        for path in self.sensitive_files():
            try:
                results.append(self.secure_shred_file(path))
            except (OSError, SecurityGateError, ValueError) as exc:
                failures.append({"file": path.name, "error": f"{exc.__class__.__name__}: {exc}"})
        vault_result = None
        if self.require_dpapi_enrollment and self.protected_vault is not None:
            try:
                vault_result = self.protected_vault.destroy(passes=self.SHRED_PASSES)
            except (OSError, DpapiVaultError, ValueError) as exc:
                failures.append({"file": "DPAPI vault", "error": f"{exc.__class__.__name__}: {exc}"})
        return {
            "status": "partial_failure" if failures else "destroyed_best_effort",
            "passes": self.SHRED_PASSES,
            "shredded_count": sum(item["status"] == "shredded_best_effort" for item in results),
            "skipped_count": sum(item["status"].startswith("skipped") for item in results),
            "failures": failures,
            "protected_vault": vault_result,
            "limitations": "Overwrite shredding cannot guarantee removal from SSD wear-leveling, copy-on-write filesystems, snapshots, backups, or external replicas.",
        }

    def execute_authorized_command(self, command, supplied_key):
        self.verify_key(supplied_key)
        normalized = str(command or "").strip().upper()
        if normalized == "STOP":
            return {"status": "stopped", "destroyed": False}
        if normalized == "DESTROY":
            return self.destroy_sensitive_data(supplied_key)
        raise UnauthorizedSecurityCommand("Unknown security command; no files were destroyed")


def main(argv=None):
    from core.dpapi_vault import main as vault_main

    return vault_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
