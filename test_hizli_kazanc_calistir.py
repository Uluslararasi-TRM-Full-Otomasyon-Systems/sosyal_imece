#!/usr/bin/env python3
"""Run the simulated affiliate campaign and verify its SQLite queue entries."""

import ast
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hizli_kazanc_modulu import HizliKazancModulu
from llm_gateway import MultiModelGateway
from web_scraper import LiveWebScraper


def main():
    database_path = PROJECT_ROOT / "trm_kuyruk.db"
    try:
        gateway = MultiModelGateway()
        scraper = LiveWebScraper()
        module = HizliKazancModulu(
            queue_db=database_path,
            mode="simulate",
            gateway=gateway,
            scraper=scraper,
        )
        result = module.kampanya_uret_ve_kuyruga_ekle()
        if result["durum"] not in {"completed", "partial_error"}:
            raise RuntimeError(f"Kampanya üretimi başarısız: {result['hatalar']}")

        verified_tasks = []
        with closing(sqlite3.connect(database_path)) as connection:
            rows = connection.execute(
                "SELECT post_id, payload, status FROM task_queue WHERE account_id = ? ORDER BY id",
                ("trm_hizli_kazanc",),
            ).fetchall()

        for post_id, payload_text, queue_status in rows:
            try:
                task = ast.literal_eval(payload_text)
            except (ValueError, SyntaxError) as exc:
                raise RuntimeError(f"{post_id} kuyruk payload'u okunamadi") from exc
            task_payload = task.get("payload", {})
            if task_payload.get("etiket") != "gelir_getiren_gorev":
                continue
            if queue_status != "pending" or task_payload.get("status") != "pending_review":
                raise RuntimeError(f"{post_id} beklenen inceleme durumunda degil")
            if not task_payload.get("social_media_hooks"):
                raise RuntimeError(f"{post_id} icin kanca taslagi bulunamadi")
            verified_tasks.append({
                "post_id": post_id,
                "urun": task_payload.get("product", {}).get("title"),
                "kanca_sayisi": len(task_payload["social_media_hooks"]),
                "affiliate_link_status": task_payload.get("affiliate_link_status"),
                "queue_status": queue_status,
            })

        if not verified_tasks:
            raise RuntimeError("task_queue tablosunda dogrulanabilir affiliate gorevi bulunamadi")

        print(json.dumps({
            "durum": "verified",
            "database": str(database_path),
            "mode": result["mode"],
            "generated": result["uretilen"],
            "newly_queued": result["kuyruga_eklenen"],
            "duplicate_skipped": result["atlanan_yinelenen"],
            "verified_income_tasks": len(verified_tasks),
            "tasks": verified_tasks,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({
            "durum": "error",
            "error": f"{exc.__class__.__name__}: {exc}",
        }, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
