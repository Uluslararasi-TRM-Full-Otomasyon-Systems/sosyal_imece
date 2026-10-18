"""Windows-current-user DPAPI vault for local TRM configuration.

The encrypted vault lives in LOCALAPPDATA, outside the project tree. This
protects copied project folders from containing the local secrets. Enrollment is
explicit because automatic first-run enrollment cannot distinguish a trusted
computer from an untrusted one.
"""

from __future__ import annotations

import base64
import ctypes
import csv
import hashlib
import json
import os
import re
import secrets
import subprocess
import tempfile
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path


class DpapiVaultError(RuntimeError):
    pass


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


class WindowsDpapi:
    CRYPTPROTECT_UI_FORBIDDEN = 0x1

    def __init__(self):
        if os.name != "nt":
            raise DpapiVaultError("Windows DPAPI is required for the protected local vault")
        self.crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DataBlob), wintypes.LPCWSTR, ctypes.POINTER(_DataBlob),
            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
        self.crypt32.CryptProtectData.restype = wintypes.BOOL
        self.crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(_DataBlob),
            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_DataBlob),
        ]
        self.crypt32.CryptUnprotectData.restype = wintypes.BOOL
        self.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self.kernel32.LocalFree.restype = ctypes.c_void_p

    @staticmethod
    def _blob(data):
        if not data:
            raise ValueError("DPAPI payload cannot be empty")
        buffer = ctypes.create_string_buffer(data, len(data))
        blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
        return buffer, blob

    def protect(self, plaintext):
        buffer, source = self._blob(plaintext)
        encrypted = _DataBlob()
        if not self.crypt32.CryptProtectData(
            ctypes.byref(source),
            "TRM Ticari protected local configuration",
            None,
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(encrypted),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(encrypted.pbData, encrypted.cbData)
        finally:
            self.kernel32.LocalFree(encrypted.pbData)
            del buffer

    def unprotect(self, ciphertext):
        buffer, source = self._blob(ciphertext)
        plaintext = _DataBlob()
        description = wintypes.LPWSTR()
        if not self.crypt32.CryptUnprotectData(
            ctypes.byref(source),
            ctypes.byref(description),
            None,
            None,
            None,
            self.CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(plaintext),
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return ctypes.string_at(plaintext.pbData, plaintext.cbData)
        finally:
            self.kernel32.LocalFree(plaintext.pbData)
            if description:
                self.kernel32.LocalFree(description)
            del buffer


def current_device_user_binding():
    if os.name != "nt":
        raise DpapiVaultError("Windows identity binding is only available on Windows")
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
            machine_guid = winreg.QueryValueEx(key, "MachineGuid")[0]
        identity = subprocess.run(
            ["whoami.exe", "/user", "/fo", "csv", "/nh"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
            shell=False,
        ).stdout.strip()
        rows = list(csv.reader(identity.splitlines()))
        sid = rows[0][1].strip() if rows and len(rows[0]) > 1 else ""
        if not machine_guid or not re.fullmatch(r"S-\d(?:-\d+)+", sid):
            raise DpapiVaultError("Could not establish a Windows MachineGuid and user SID")
        profile = os.environ.get("USERPROFILE", "").casefold()
        raw = f"{machine_guid}\n{sid}\n{profile}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
    except DpapiVaultError:
        raise
    except Exception as exc:
        raise DpapiVaultError("Could not establish the local Windows identity") from exc


def default_vault_path():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise DpapiVaultError("LOCALAPPDATA is unavailable; refusing project-local key storage")
    return Path(local_app_data) / "SosyalImece" / "security" / "config.vault.dpapi"


def parse_env_assignments(raw_text):
    """Parse simple KEY=VALUE lines; caller may also preserve the raw source encrypted."""
    values = {}
    for raw_line in raw_text.splitlines():
        match = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", raw_line)
        if not match:
            continue
        key, value = match.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


class ProtectedLocalVault:
    FORMAT_VERSION = 1
    PROTECTED_FILE_ALLOWLIST = {
        "service_account.json",
        "api_keys.json",
        "config.json",
        "config.env",
        ".streamlit/secrets.toml",
    }
    PROCESS_ENV_ALLOWLIST = {
        "FAHRI_MASTER_SECURE_KEY",
        "FAHRI_KILL_SWITCH_URL",
        "TRM_AUTONOMOUS_DISTRIBUTION_ENABLED",
        "TRM_AFFILIATE_SCOUT_ENABLED",
        "TRM_MAGAZA_API_ENABLED",
        "TRM_STORE_SIMULATE",
        "TRM_STORE_API_BASE_URL",
        "TRM_STORE_TOKEN_URL",
        "TRM_STORE_CLIENT_ID",
        "TRM_STORE_CLIENT_SECRET",
        "TRM_STORE_ACCESS_TOKEN",
        "TRM_DISTRIBUTION_MODE",
        "TRM_SOCIAL_DISTRIBUTION_WEBHOOK_URL",
        "TRM_EXTERNAL_API_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "TELEGRAM_TARGET_CHANNEL",
        "DROPBOX_ACCESS_TOKEN",
        "BUFFER_ACCESS_TOKEN",
        "DATABASE_URL",
        "JWT_SECRET",
        "REFERRAL_SECRET_KEY",
        "SCRAPER_PROXY_URL",
        "SECRET_KEY",
        "SMTP_HOST",
        "SMTP_PORT",
        "TELEGRAM_PHONE",
        "TRM_LOG_LEVEL",
        "TRM_MEDYA_PATH",
        "TRM_RAPORLAR_PATH",
    }
    NEVER_IMPORT_ENV_KEYS = {
        "PATH", "PATHEXT", "PYTHONPATH", "PYTHONHOME", "SYSTEMROOT", "WINDIR",
        "COMSPEC", "TEMP", "TMP", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
        "LOCALAPPDATA", "APPDATA", "USERNAME", "USERDOMAIN",
    }

    def __init__(self, path=None, protector=None, binding=None):
        self.path = Path(path) if path else default_vault_path()
        self.protector = protector or WindowsDpapi()
        self.binding = binding or current_device_user_binding()

    @classmethod
    def from_default_location(cls):
        return cls()

    def exists(self):
        return self.path.is_file() and not self.path.is_symlink()

    def load(self):
        if not self.exists():
            return None
        if self.path.is_symlink() or self.path.stat().st_size > 2_000_000:
            raise DpapiVaultError("Protected vault file is invalid")
        try:
            ciphertext = self.path.read_bytes()
            data = json.loads(self.protector.unprotect(ciphertext).decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise DpapiVaultError("Protected local vault could not be decrypted") from exc
        if data.get("format_version") != self.FORMAT_VERSION:
            raise DpapiVaultError("Unsupported protected vault format")
        if not secrets.compare_digest(str(data.get("device_user_binding", "")), self.binding):
            raise DpapiVaultError("Protected vault belongs to a different Windows user or machine")
        if not isinstance(data.get("environment"), dict):
            raise DpapiVaultError("Protected vault environment section is invalid")
        return data

    def save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        plaintext = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ciphertext = self.protector.protect(plaintext)
        temp_name = None
        try:
            handle, temp_name = tempfile.mkstemp(prefix=".vault-", dir=str(self.path.parent))
            with os.fdopen(handle, "wb") as stream:
                stream.write(ciphertext)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, self.path)
            temp_name = None
        except OSError as exc:
            raise DpapiVaultError("Could not atomically write protected vault") from exc
        finally:
            if temp_name:
                try:
                    os.unlink(temp_name)
                except OSError:
                    pass

    def enroll(self, environment=None, legacy_raw=None, protected_files=None):
        if self.path.exists():
            raise DpapiVaultError("A protected vault already exists; refusing silent re-enrollment")
        values = {str(key): str(value) for key, value in (environment or {}).items()}
        master_key = values.get("FAHRI_MASTER_SECURE_KEY", "").strip()
        if len(master_key) < 32:
            master_key = secrets.token_urlsafe(48)
        values["FAHRI_MASTER_SECURE_KEY"] = master_key
        data = {
            "format_version": self.FORMAT_VERSION,
            "device_user_binding": self.binding,
            "enrolled_at": datetime.now(timezone.utc).isoformat(),
            "environment": values,
            "legacy_secrets_env_b64": base64.b64encode(legacy_raw).decode("ascii") if legacy_raw is not None else None,
            "protected_files_b64": {
                str(name).replace("\\", "/"): base64.b64encode(content).decode("ascii")
                for name, content in (protected_files or {}).items()
                if str(name).replace("\\", "/") in self.PROTECTED_FILE_ALLOWLIST
            },
        }
        self.save(data)
        restored = self.load()
        if restored is None or restored["environment"] != values:
            raise DpapiVaultError("Protected vault read-back verification failed")
        return restored

    def load_environment(self, environ=None, override=False):
        data = self.load()
        if data is None:
            return None
        target = os.environ if environ is None else environ
        for key, value in data["environment"].items():
            if key in self.NEVER_IMPORT_ENV_KEYS:
                continue
            if override or key not in target:
                target[key] = value
        return data

    def load_protected_file(self, relative_path):
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise DpapiVaultError("Protected file lookup must use an allowlisted relative path")
        key = relative.as_posix()
        if key not in self.PROTECTED_FILE_ALLOWLIST:
            raise DpapiVaultError("Protected file is not allowlisted")
        data = self.load()
        if data is None:
            raise DpapiVaultError("DPAPI vault is not enrolled")
        encoded = data.get("protected_files_b64", {}).get(key)
        if not encoded:
            raise DpapiVaultError(f"Protected file is not present in the local vault: {key}")
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise DpapiVaultError("Protected file entry is corrupted") from exc

    def destroy(self, passes=3):
        """Best-effort overwrite and unlink of the current user's encrypted vault."""
        if passes < 3:
            raise ValueError("At least three overwrite passes are required")
        if self.path.is_symlink():
            raise DpapiVaultError("Refusing to destroy a symlinked vault")
        if not self.path.is_file():
            return {"status": "already_absent", "passes": 0}
        if self.path.stat().st_nlink != 1:
            raise DpapiVaultError("Refusing to destroy a hard-linked vault")
        size = self.path.stat().st_size
        with self.path.open("r+b", buffering=0) as stream:
            for _ in range(passes):
                stream.seek(0)
                remaining = size
                while remaining:
                    block = min(remaining, 1024 * 1024)
                    stream.write(secrets.token_bytes(block))
                    remaining -= block
                stream.flush()
                os.fsync(stream.fileno())
            stream.truncate(0)
            stream.flush()
            os.fsync(stream.fileno())
        self.path.unlink()
        return {"status": "shredded_best_effort", "passes": passes, "bytes_overwritten": size * passes}


def _shred_migrated_source(path, passes=3):
    if path.is_symlink() or path.stat().st_nlink != 1:
        raise DpapiVaultError(f"Refusing to shred linked credential file: {path.name}")
    size = path.stat().st_size
    with path.open("r+b", buffering=0) as stream:
        for _ in range(passes):
            stream.seek(0)
            remaining = size
            while remaining:
                chunk_size = min(remaining, 1024 * 1024)
                stream.write(secrets.token_bytes(chunk_size))
                remaining -= chunk_size
            stream.flush()
            os.fsync(stream.fileno())
        stream.truncate(0)
        stream.flush()
        os.fsync(stream.fileno())
    path.unlink()


def migrate_project_secrets_to_vault(project_root=None, vault=None, remove_source=False):
    """Encrypt the legacy secret/config allowlist and verify before optional shred."""
    root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
    vault = vault or ProtectedLocalVault.from_default_location()
    migration_names = (
        "secrets.env",
        "config.env",
        "service_account.json",
        "api_keys.json",
        "config.json",
        ".streamlit/secrets.toml",
    )
    source_files = {}
    protected_files = {}
    for relative_name in migration_names:
        source = root / relative_name
        if not source.is_file():
            continue
        if source.is_symlink() or source.stat().st_nlink != 1:
            raise DpapiVaultError(f"Refusing to migrate linked credential file: {relative_name}")
        raw = source.read_bytes()
        source_files[relative_name] = (source, raw)
        if relative_name in {"service_account.json", "api_keys.json", "config.json", "config.env", ".streamlit/secrets.toml"}:
            protected_files[relative_name] = raw

    legacy_env = source_files.get("secrets.env", (None, None))[1]
    parsed = parse_env_assignments(legacy_env.decode("utf-8", errors="strict")) if legacy_env is not None else {}
    config_env = source_files.get("config.env", (None, None))[1]
    if config_env is not None:
        parsed.update(parse_env_assignments(config_env.decode("utf-8", errors="strict")))
    for key, value in os.environ.items():
        if key in ProtectedLocalVault.PROCESS_ENV_ALLOWLIST:
            parsed.setdefault(key, value)
    for key in ProtectedLocalVault.NEVER_IMPORT_ENV_KEYS:
        parsed.pop(key, None)

    vault_data = vault.enroll(parsed, legacy_raw=legacy_env, protected_files=protected_files)
    verified = vault.load()
    if verified is None or verified["environment"] != vault_data["environment"]:
        raise DpapiVaultError("Protected vault verification failed; source files were not removed")
    for name, raw in protected_files.items():
        if vault.load_protected_file(name) != raw:
            raise DpapiVaultError(f"Protected-file verification failed for {name}; source files were not removed")

    removed_files = []
    if remove_source:
        try:
            for name, (source, _raw) in source_files.items():
                _shred_migrated_source(source)
                removed_files.append(name)
        except (OSError, DpapiVaultError) as exc:
            raise DpapiVaultError("Vault verified but one or more plaintext source files could not be shredded") from exc

    return {
        "status": "enrolled",
        "environment_variable_count": len(vault_data["environment"]),
        "source_files_migrated": sorted(source_files),
        "source_files_removed": removed_files,
        "vault_path": str(vault.path),
        "key_printed": False,
        "limitations": "DPAPI protects the current Windows user profile; machine/user binding rejects copied vaults elsewhere. File overwrite remains best-effort on SSDs, copy-on-write filesystems and snapshots.",
    }


def load_protected_environment(project_root=None):
    """Load DPAPI state only. Never inspect project .env or secrets.env files."""
    vault = ProtectedLocalVault.from_default_location()
    data = vault.load_environment(override=False)
    return "windows_dpapi" if data is not None else None


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Enroll or inspect the Windows DPAPI-protected TRM local identity.")
    parser.add_argument("--enroll", action="store_true", help="Create a DPAPI vault bound to this Windows user and machine")
    parser.add_argument("--migrate-secrets-env", action="store_true", help="Encrypt secrets.env into the vault, verify read-back, then best-effort shred the source")
    parser.add_argument("--status", action="store_true", help="Print safe enrollment status")
    args = parser.parse_args(argv)
    if args.migrate_secrets_env and not args.enroll:
        parser.error("--migrate-secrets-env requires --enroll")

    try:
        vault = ProtectedLocalVault.from_default_location()
        if args.enroll:
            report = migrate_project_secrets_to_vault(remove_source=args.migrate_secrets_env, vault=vault)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        data = vault.load()
        print(json.dumps({
            "enrolled": data is not None,
            "vault_location": "LOCALAPPDATA/SosyalImece/security/config.vault.dpapi",
            "environment_variable_count": len(data["environment"]) if data else 0,
            "master_key_value_exposed": False,
        }, ensure_ascii=False, indent=2))
        return 0 if data else 78
    except DpapiVaultError as exc:
        print(json.dumps({"status": "locked", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
