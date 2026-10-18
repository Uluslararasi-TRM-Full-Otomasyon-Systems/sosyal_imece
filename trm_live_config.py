"""Load TRM live credentials safely and report production readiness without values."""

import os
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


TRUTHY = {"1", "true", "yes", "on", "enabled"}
FALSEY = {"0", "false", "no", "off", "disabled"}
LIVE_ENV_KEYS = {
    "FAHRI_MASTER_SECURE_KEY",
    "FAHRI_MASTER_SECURE_KEY_FILE",
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
}


def env_bool(name, default=False, environ=None):
    values = os.environ if environ is None else environ
    value = values.get(name)
    if value is None or not str(value).strip():
        return default
    normalized = str(value).strip().casefold()
    if normalized in TRUTHY:
        return True
    if normalized in FALSEY:
        return False
    return default


def load_trm_environment(project_root=None):
    """Load configuration only from the Windows DPAPI vault, never project files."""
    from core.dpapi_vault import DpapiVaultError, load_protected_environment

    try:
        return load_protected_environment()
    except DpapiVaultError:
        return None


def get_live_settings(environ=None):
    values = os.environ if environ is None else environ
    store_enabled = env_bool("TRM_MAGAZA_API_ENABLED", False, values)
    store_simulate = env_bool("TRM_STORE_SIMULATE", True, values)
    store_requested_live = store_enabled and not store_simulate
    store = {
        "enabled": store_enabled,
        "simulate": store_simulate,
        "requested_live": store_requested_live,
        "api_base_url": values.get("TRM_STORE_API_BASE_URL", "").strip(),
        "token_url": values.get("TRM_STORE_TOKEN_URL", "").strip(),
        "client_id": values.get("TRM_STORE_CLIENT_ID", "").strip(),
        "client_secret": values.get("TRM_STORE_CLIENT_SECRET", "").strip(),
        "access_token": values.get("TRM_STORE_ACCESS_TOKEN", "").strip(),
    }
    store_missing = []
    if store_requested_live:
        api_endpoint = urlsplit(store["api_base_url"])
        if api_endpoint.scheme != "https" or not api_endpoint.hostname or api_endpoint.username or api_endpoint.password:
            store_missing.append("TRM_STORE_API_BASE_URL")
        has_oauth = bool(store["client_id"] and store["client_secret"] and store["token_url"])
        has_token = bool(store["access_token"])
        if not (has_oauth or has_token):
            store_missing.append("TRM_STORE_ACCESS_TOKEN veya OAuth client_id/client_secret/token_url")
    store["missing"] = store_missing
    store["ready"] = not store_requested_live or not store_missing

    distribution_mode = values.get("TRM_DISTRIBUTION_MODE", "simulate").strip().casefold()
    if distribution_mode not in {"simulate", "live"}:
        distribution_mode = "simulate"
    channels = {}
    telegram_token = values.get("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = (values.get("TELEGRAM_CHAT_ID") or values.get("TELEGRAM_TARGET_CHANNEL") or "").strip()
    if telegram_token and telegram_chat_id:
        channels["telegram"] = {"bot_token": telegram_token, "chat_id": telegram_chat_id}

    social_webhook = values.get("TRM_SOCIAL_DISTRIBUTION_WEBHOOK_URL", "").strip()
    if social_webhook:
        channels["social_media"] = {"webhook_url": social_webhook}
    external_webhook = values.get("TRM_EXTERNAL_API_WEBHOOK_URL", "").strip()
    if external_webhook:
        channels["external_api"] = {"webhook_url": external_webhook}

    distribution_missing = []
    if bool(telegram_token) != bool(telegram_chat_id):
        distribution_missing.append("Telegram bot token ve chat/channel ID birlikte tanımlanmalıdır")
    if distribution_mode == "live" and not channels:
        distribution_missing.append(
            "Telegram token+chat ID veya TRM_SOCIAL_DISTRIBUTION_WEBHOOK_URL/TRM_EXTERNAL_API_WEBHOOK_URL"
        )
    distribution = {
        "mode": distribution_mode,
        "channels": channels,
        "requested_live": distribution_mode == "live",
        "missing": distribution_missing,
        "ready": not distribution_missing,
    }

    enabled = env_bool("TRM_AUTONOMOUS_DISTRIBUTION_ENABLED", False, values)
    live_production_ready = bool(
        enabled
        and store_enabled
        and store_requested_live
        and store["ready"]
        and distribution_mode == "live"
        and distribution["ready"]
    )
    live_missing = []
    if not enabled:
        live_missing.append("TRM_AUTONOMOUS_DISTRIBUTION_ENABLED=1")
    if not store_enabled:
        live_missing.append("TRM_MAGAZA_API_ENABLED=1")
    if store_simulate:
        live_missing.append("TRM_STORE_SIMULATE=0")
    api_endpoint = urlsplit(store["api_base_url"])
    if api_endpoint.scheme != "https" or not api_endpoint.hostname or api_endpoint.username or api_endpoint.password:
        live_missing.append("TRM_STORE_API_BASE_URL")
    has_live_oauth = bool(
        store["client_id"]
        and store["client_secret"]
        and urlsplit(store["token_url"]).scheme == "https"
        and urlsplit(store["token_url"]).hostname
    )
    if not (store["access_token"] or has_live_oauth):
        live_missing.append("TRM_STORE_ACCESS_TOKEN veya TRM_STORE_CLIENT_ID/CLIENT_SECRET/TOKEN_URL")
    if distribution_mode != "live":
        live_missing.append("TRM_DISTRIBUTION_MODE=live")
    live_missing.extend(distribution_missing)
    return {
        "autonomous_enabled": enabled,
        "store": store,
        "distribution": distribution,
        "ready": store["ready"] and distribution["ready"],
        "live_production_ready": live_production_ready,
        "live_missing": live_missing,
    }


def public_readiness_report(settings=None):
    """Return readiness booleans and missing variable names, never secret values."""
    settings = settings or get_live_settings()
    return {
        "autonomous_enabled": settings["autonomous_enabled"],
        "store": {
            "enabled": settings["store"]["enabled"],
            "simulate": settings["store"]["simulate"],
            "requested_live": settings["store"]["requested_live"],
            "ready": settings["store"]["ready"],
            "missing": list(settings["store"]["missing"]),
        },
        "distribution": {
            "mode": settings["distribution"]["mode"],
            "configured_channels": sorted(settings["distribution"]["channels"]),
            "ready": settings["distribution"]["ready"],
            "missing": list(settings["distribution"]["missing"]),
        },
        "ready": settings["ready"],
        "live_production_ready": settings["live_production_ready"],
        "live_missing": list(settings["live_missing"]),
    }


def main():
    source = load_trm_environment()
    report = public_readiness_report(get_live_settings())
    print("ENV_SOURCE=" + str(source))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["live_production_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
