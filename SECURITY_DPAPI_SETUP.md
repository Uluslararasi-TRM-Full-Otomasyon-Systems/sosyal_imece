# Windows DPAPI Security Setup

The live worker no longer reads `.env` or `secrets.env` at startup. It requires a DPAPI vault bound to the current Windows user profile and local machine identity. The encrypted vault is stored under `%LOCALAPPDATA%\SosyalImece\security\config.vault.dpapi`, outside the project tree.

## One-time enrollment on the trusted computer

Run from the project root in VS Code PowerShell:

```powershell
python core/security.py --enroll --migrate-secrets-env
python core/security.py --status
```

Enrollment reads existing `secrets.env` in memory, stores its parsed settings and an encrypted copy of the original text in the DPAPI vault, verifies the vault by decrypting it, then performs a best-effort three-pass overwrite and removes the plaintext source. The generated master key is never printed. Do not run enrollment on an untrusted/new host; that would enroll that host as a new trusted identity.

After enrollment, start the worker as usual:

```powershell
python run_live_worker.py
```

A copied project folder on another Windows user/device has no matching DPAPI vault and the worker exits with code 78 before opening SQLite. If the vault is missing or corrupted, stop and recover the trusted profile/vault; do not recreate enrollment on an unknown device.

## Testing without production data loss

```powershell
python -m unittest tests.test_security_kill_switch tests.test_trm_live_config
python run_live_worker.py --once
```

Without enrollment, the worker test run is expected to print `Worker locked before startup` and exit with code 78. Unit tests exercise shredding only against temporary fixture directories. Do not invoke `DESTROY` against the real project as a routine test.

## Remote kill-switch endpoint

Set `FAHRI_KILL_SWITCH_URL` inside the protected vault during enrollment/configuration. The endpoint must be HTTPS and return `204` for no command or a JSON command with `command`, `issued_at` (Unix seconds), `nonce`, and `signature`. The signature is lowercase hex HMAC-SHA256 over the UTF-8 message:

```text
COMMAND\nISSUED_AT\nNONCE
```

using the enrolled `FAHRI_MASTER_SECURE_KEY`. Keep the matching signer key only on the trusted control service; never place it in source code or a repository. Commands are `STOP` and `DESTROY`; timestamps older than 60 seconds and replayed nonces are rejected. The worker never sends the master key to the endpoint.

## Storage limitations

Three overwrite passes followed by unlink are best effort only. SSD wear-leveling, copy-on-write filesystems, snapshots, backups, antivirus quarantine, and cloud sync can retain older copies. DPAPI protects local configuration at rest and binds it to the Windows user profile; it is not a substitute for disk encryption, account security, or a tested backup/recovery plan.
