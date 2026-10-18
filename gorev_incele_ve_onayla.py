#!/usr/bin/env python3
"""Review affiliate campaign drafts and approve selected SQLite queue tasks."""

import argparse
import ast
import json
import os
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from trm_live_config import get_live_settings, load_trm_environment, public_readiness_report


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DB = PROJECT_ROOT / "trm_kuyruk.db"
INCOME_TASK_LABEL = "gelir_getiren_gorev"
PENDING_REVIEW = "pending_review"


def validate_campaign(task):
    """Validate a campaign and fill the project's non-commissionable test redirect."""
    from hizli_kazanc_modulu import create_fallback_affiliate_link

    payload = task.get("payload") or {}
    errors = []
    product = payload.get("product")
    if not isinstance(product, dict) or not str(product.get("title") or "").strip():
        errors.append("Ürün başlığı eksik")
        return errors
    hooks = payload.get("social_media_hooks")
    if not isinstance(hooks, list) or not any(str(hook).strip() for hook in hooks):
        errors.append("Kanca taslağı eksik")
    campaign_id = str(payload.get("campaign_id") or task.get("post_id", "campaign"))
    link = payload.get("affiliate_link_draft") or product.get("partner_url") or product.get("affiliate_url")
    if not link:
        link = create_fallback_affiliate_link(product, campaign_id)
        payload["affiliate_link_status"] = "fallback_redirect"
        payload["commission_eligible"] = False
    try:
        parsed = urlsplit(str(link))
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            errors.append("Güvenli HTTPS yönlendirme adresi geçersiz")
    except ValueError:
        errors.append("Yönlendirme adresi geçersiz")
    if not errors:
        payload["affiliate_link_draft"] = str(link)
        product["affiliate_url"] = str(link)
        task["payload"] = payload
    return errors


def parse_payload(value):
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return {}
    return parsed if isinstance(parsed, dict) else {}


def load_pending_tasks(db_path):
    with closing(sqlite3.connect(db_path)) as connection:
        rows = connection.execute(
            "SELECT id, account_id, post_id, payload, status, queued_at "
            "FROM task_queue WHERE account_id = ? ORDER BY id",
            ("trm_hizli_kazanc",),
        ).fetchall()

    tasks = []
    for row in rows:
        if row[4] != "pending":
            continue
        stored_payload = parse_payload(row[3])
        payload = stored_payload.get("payload", stored_payload)
        if not isinstance(payload, dict):
            continue
        if payload.get("etiket") != INCOME_TASK_LABEL:
            continue
        if str(payload.get("status", "")).casefold() != PENDING_REVIEW:
            continue
        tasks.append({
            "id": row[0],
            "account_id": row[1],
            "post_id": row[2],
            "payload": payload,
            "queue_status": row[4],
            "queued_at": row[5],
        })
    return tasks


def print_tasks(tasks):
    if not tasks:
        print("İnceleme bekleyen gelir_getiren_gorev bulunamadı.")
        return

    print(f"\nİnceleme bekleyen kampanya sayısı: {len(tasks)}")
    for number, task in enumerate(tasks, start=1):
        payload = task["payload"]
        product = payload.get("product") or {}
        hooks = payload.get("social_media_hooks") or []
        gateway = payload.get("llm_gateway") or {}
        print("\n" + "=" * 76)
        print(f"[{number}] Kuyruk ID: {task['id']} | Post ID: {task['post_id']}")
        print(f"Ürün: {product.get('title') or product.get('name') or 'Belirtilmemiş'}")
        print(f"Kategori: {product.get('category') or 'Belirtilmemiş'}")
        print(f"Açıklama: {product.get('description') or 'Açıklama yok'}")
        print(f"Kaynak: {product.get('source') or 'Belirtilmemiş'}")
        print(f"Kuyruk durumu: {task['queue_status']} | Taslak durumu: {payload.get('status')}")
        print(f"Affiliate durumu: {payload.get('affiliate_link_status') or 'Belirtilmemiş'}")
        print(f"Affiliate link taslağı: {payload.get('affiliate_link_draft') or 'Henüz partner linki gerekli'}")
        print("Kanca taslakları:")
        if hooks:
            for hook_number, hook in enumerate(hooks, start=1):
                print(f"  {hook_number}. {hook}")
        else:
            print("  Kanca bulunamadı")
        print(
            "LLM yönlendirmesi: "
            f"{gateway.get('secilen_saglayici', 'Belirtilmemiş')} "
            f"({gateway.get('durum', 'durum yok')})"
        )
        print(f"Oluşturulma zamanı: {task['queued_at'] or 'Belirtilmemiş'}")
    print("\n" + "=" * 76)


def choose_tasks(tasks, args):
    if args.approve_all:
        return tasks
    if args.approve:
        requested = args.approve
    else:
        try:
            answer = input(
                "Onaylamak istediğiniz görev numaralarını veya post_id değerlerini "
                "virgülle yazın (boş bırakıp Enter: onay yok): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nOnay alınmadı; hiçbir görev değiştirilmedi.")
            return []
        if not answer:
            print("Onay alınmadı; hiçbir görev değiştirilmedi.")
            return []
        requested = [value.strip() for value in answer.split(",") if value.strip()]

    by_reference = {}
    for number, task in enumerate(tasks, start=1):
        by_reference[str(number)] = task
        by_reference[task["post_id"]] = task
        by_reference[str(task["id"])] = task

    selected = []
    unknown = []
    for reference in requested:
        task = by_reference.get(reference)
        if task is None:
            unknown.append(reference)
        elif task not in selected:
            selected.append(task)
    if unknown:
        raise ValueError("Geçersiz görev seçimi: " + ", ".join(unknown))
    return selected


def approve_tasks(db_path, selected):
    if not selected:
        return 0
    approved_at = datetime.now(timezone.utc).isoformat()
    approved_count = 0
    with closing(sqlite3.connect(db_path, timeout=10)) as connection:
        try:
            connection.execute("BEGIN IMMEDIATE")
            for task in selected:
                row = connection.execute(
                    "SELECT payload, status FROM task_queue WHERE id = ?",
                    (task["id"],),
                ).fetchone()
                if row is None or row[1] != "pending":
                    continue
                stored_payload = parse_payload(row[0])
                payload = stored_payload.get("payload", stored_payload)
                if not isinstance(payload, dict):
                    continue
                if (
                    payload.get("etiket") != INCOME_TASK_LABEL
                    or str(payload.get("status", "")).casefold() != PENDING_REVIEW
                ):
                    continue
                prepared = task.get("payload") or {}
                for key in (
                    "affiliate_link_draft",
                    "affiliate_link_status",
                    "commission_eligible",
                    "product",
                ):
                    if key in prepared:
                        payload[key] = prepared[key]
                payload["status"] = "approved"
                payload["approval_status"] = "approved"
                payload["approved_at"] = approved_at
                if "payload" in stored_payload:
                    stored_payload["payload"] = payload
                    serialized_payload = repr(stored_payload)
                else:
                    serialized_payload = repr(payload)
                cursor = connection.execute(
                    "UPDATE task_queue SET payload = ?, status = 'approved' "
                    "WHERE id = ? AND status = 'pending'",
                    (serialized_payload, task["id"]),
                )
                approved_count += cursor.rowcount
            connection.commit()
        except Exception:
            connection.rollback()
            raise
    return approved_count


def _live_readiness_errors(store_live, api_options, distribution_mode, distribution_channels, settings):
    errors = []
    if store_live:
        store_config = {
            "api_base_url": settings["store"]["api_base_url"],
            "token_url": settings["store"]["token_url"],
            "client_id": settings["store"]["client_id"],
            "client_secret": settings["store"]["client_secret"],
            "access_token": settings["store"]["access_token"],
        }
        store_config.update(api_options or {})
        endpoint = urlsplit(str(store_config.get("api_base_url") or ""))
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username or endpoint.password:
            errors.append("TRM_STORE_API_BASE_URL güvenli HTTPS endpoint olmalıdır")
        token_url = urlsplit(str(store_config.get("token_url") or ""))
        has_access_token = bool(store_config.get("access_token"))
        has_client_auth = bool(
            store_config.get("client_id")
            and store_config.get("client_secret")
            and token_url.scheme == "https"
            and token_url.hostname
        )
        if not (has_access_token or has_client_auth):
            errors.append("Mağaza API access token veya tam OAuth client/token URL yapılandırması eksik")

    if distribution_mode == "live":
        channels = distribution_channels or {}
        if not isinstance(channels, dict) or not channels:
            errors.append("Canlı dağıtım için Telegram veya webhook kanalı yapılandırılmalıdır")
        else:
            for channel, config in channels.items():
                config = config if isinstance(config, dict) else {}
                if str(channel).casefold() == "telegram":
                    if not config.get("bot_token") or not config.get("chat_id"):
                        errors.append("Telegram için bot token ve chat/channel ID gereklidir")
                else:
                    webhook = urlsplit(str(config.get("webhook_url") or ""))
                    if webhook.scheme != "https" or not webhook.hostname or webhook.username or webhook.password:
                        errors.append(f"{channel} için güvenli HTTPS webhook URL gereklidir")
    return errors


def autonomous_approve_and_transfer(
    db_path,
    live_store=None,
    api_options=None,
    distribution_mode=None,
    distribution_channels=None,
):
    from magaza_api_koprusu import MagazaAPIBridge
    from autonomous_distribution_engine import AutonomousDistributionEngine

    load_trm_environment(Path(db_path).resolve().parent)
    settings = get_live_settings()
    store_live = settings["store"]["requested_live"] if live_store is None else bool(live_store)
    effective_distribution_mode = distribution_mode or settings["distribution"]["mode"]
    effective_channels = distribution_channels
    if effective_channels is None and effective_distribution_mode == "live":
        effective_channels = settings["distribution"]["channels"]
    report = {
        "durum": "completed",
        "incelenen": 0,
        "onaylanan": 0,
        "reddedilen": [],
        "magaza_koprusu": None,
        "dagitim": None,
    }
    pending = load_pending_tasks(db_path)
    report["incelenen"] = len(pending)
    readiness_errors = _live_readiness_errors(
        store_live,
        api_options,
        effective_distribution_mode,
        effective_channels,
        settings,
    )
    report["live_readiness"] = public_readiness_report(settings)
    if readiness_errors:
        report["durum"] = "blocked"
        report["live_readiness"]["missing" ] = readiness_errors
        return report

    approved_candidates = []
    for task in pending:
        errors = validate_campaign(task)
        if errors:
            report["reddedilen"].append({"post_id": task["post_id"], "nedenler": errors})
        else:
            approved_candidates.append(task)

    report["onaylanan"] = approve_tasks(db_path, approved_candidates)
    env_config = {
        "api_base_url": os.environ.get("TRM_STORE_API_BASE_URL"),
        "token_url": os.environ.get("TRM_STORE_TOKEN_URL"),
        "client_id": os.environ.get("TRM_STORE_CLIENT_ID"),
        "client_secret": os.environ.get("TRM_STORE_CLIENT_SECRET"),
        "access_token": os.environ.get("TRM_STORE_ACCESS_TOKEN"),
    }
    bridge_config = {key: value for key, value in env_config.items() if value}
    bridge_config.update(api_options or {})
    bridge_config.pop("simulate", None)
    bridge_config["db_path"] = str(db_path)
    bridge_config["simulate"] = not store_live
    report["magaza_koprusu"] = MagazaAPIBridge(**bridge_config).publish_approved_products()
    if report["magaza_koprusu"].get("durum") in {"error", "partial_error"}:
        report["durum"] = "partial_error"
    try:
        distribution = AutonomousDistributionEngine(
            db_path=db_path,
            mode=effective_distribution_mode,
            channels=effective_channels,
        ).distribute_processed(report["magaza_koprusu"])
    except Exception as exc:
        distribution = {
            "durum": "error",
            "incelenen": 0,
            "dagitilan": 0,
            "hatalar": [{"error": f"{exc.__class__.__name__}: {exc}"}],
        }
    report["dagitim"] = distribution
    if distribution.get("durum") in {"error", "partial_error"} and report["durum"] == "completed":
        report["durum"] = "partial_error"
    if report["reddedilen"] and report["durum"] == "completed":
        report["durum"] = "partial_error"
    return report


def main(argv=None):
    load_trm_environment(PROJECT_ROOT)
    live_settings = get_live_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite kuyruk veritabanı")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list-only", action="store_true", help="Görevleri göster, değişiklik yapma")
    mode.add_argument("--approve", nargs="+", metavar="NO|POST_ID", help="Seçilen görevleri onayla")
    mode.add_argument("--approve-all", action="store_true", help="Listelenen tüm görevleri onayla")
    mode.add_argument("--auto", action="store_true", help="Görevleri doğrula, onayla, mağaza köprüsüne ve dağıtım outbox'ına aktar")
    parser.add_argument("--live-store", action="store_true", help="Köprünün canlı API kipini etkinleştir")
    args = parser.parse_args(argv)
    auto_mode = args.auto or live_settings["autonomous_enabled"]
    if args.live_store and not auto_mode:
        parser.error("--live-store yalnızca --auto veya TRM_AUTONOMOUS_DISTRIBUTION_ENABLED ile kullanılabilir")

    try:
        tasks = load_pending_tasks(args.db)
        print(f"Veritabanı: {args.db}")
        print_tasks(tasks)
        if args.list_only or not tasks:
            return 0
        if auto_mode:
            report = autonomous_approve_and_transfer(
                args.db,
                live_store=True if args.live_store else None,
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["durum"] == "completed" else 1
        selected = choose_tasks(tasks, args)
        approved_count = approve_tasks(args.db, selected)
        print(f"\nOnaylanan görev sayısı: {approved_count}")
        print("Görevler task_queue.status='approved' olarak köprü işlemine hazır.")
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Hata: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
