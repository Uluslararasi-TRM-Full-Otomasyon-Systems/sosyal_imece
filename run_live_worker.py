#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Background live worker daemon for trendurunlermarket.com channel set."""

from __future__ import annotations

import argparse
import json
import os
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "single_active_set.json"
DB_PATH = ROOT / "data" / "sosyal_imece.db"
TARGET_SITE = "trendurunlermarket.com"
DEFAULT_INTERVAL_SECONDS = 300

_shutdown_requested = False


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def log_stdout(level: str, message: str) -> None:
    print(f"[{now_stamp()}] [{level}] {message}", flush=True)


def request_shutdown(_signum=None, _frame=None) -> None:
    global _shutdown_requested
    _shutdown_requested = True
    log_stdout("INFO", "Shutdown signal received; finishing current cycle.")


def load_active_set(path: Path) -> dict | None:
    if not path.exists():
        log_stdout("WARN", f"Config missing: {path}")
        log_stdout("WARN", "Continuing with empty social/blog lists.")
        return None
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        log_stdout("OK", f"Loaded config: {path}")
        return data
    except (OSError, json.JSONDecodeError) as exc:
        log_stdout("ERROR", f"Could not parse {path}: {exc}")
        log_stdout("WARN", "Continuing with empty social/blog lists.")
        return None


def parse_channels(config: dict | None) -> tuple[str, str, list[dict], list[dict]]:
    config = config or {}
    set_name = str(config.get("set_name") or "unknown_set")
    target = str(config.get("target_ecommerce") or TARGET_SITE)
    socials = [item for item in config.get("social_media", []) if isinstance(item, dict)]
    blogs = [item for item in config.get("blogs", []) if isinstance(item, dict)]
    return set_name, target, socials, blogs


def print_channel_status(set_name: str, target: str, socials: list[dict], blogs: list[dict]) -> None:
    print("=" * 60, flush=True)
    print("run_live_worker (daemon)", flush=True)
    print("=" * 60, flush=True)
    print(f"Set name : {set_name}", flush=True)
    print(f"Target   : {target}", flush=True)
    print(f"Social   : {len(socials)} channel(s)", flush=True)
    for item in socials:
        print(
            f"  - {item.get('platform', '?')} @{item.get('handle', '?')} "
            f"[{item.get('status', 'unknown')}]",
            flush=True,
        )
    print(f"Blogs    : {len(blogs)} URL(s)", flush=True)
    for item in blogs:
        print(
            f"  - {item.get('name', '?')} {item.get('url', '?')} "
            f"[{item.get('status', 'unknown')}]",
            flush=True,
        )
    if TARGET_SITE not in target.lower():
        log_stdout("WARN", f"target_ecommerce is not {TARGET_SITE}")
    if len(socials) != 6:
        log_stdout("WARN", f"Expected 6 social channels, found {len(socials)}")
    if len(blogs) != 4:
        log_stdout("WARN", f"Expected 4 blog URLs, found {len(blogs)}")


def connect_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS organic_content_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            content_category TEXT,
            content_format TEXT,
            content_text TEXT,
            hashtags TEXT,
            image_description TEXT,
            status TEXT,
            scheduled_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS warmup_phase_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase TEXT,
            action TEXT,
            platform TEXT,
            result TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT,
            post_id TEXT,
            payload TEXT,
            status TEXT,
            queued_at TEXT
        );
        """
    )


def insert_system_log(conn: sqlite3.Connection, level: str, message: str) -> int | None:
    cursor = conn.execute(
        "INSERT INTO system_logs (level, message, timestamp) VALUES (?, ?, ?)",
        (level, message, utc_stamp()),
    )
    return cursor.lastrowid


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def process_pending_queue(conn: sqlite3.Connection, table: str, limit: int = 10) -> int:
    if not table_exists(conn, table):
        return 0
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if "status" not in columns or "id" not in columns:
        return 0
    pending = conn.execute(
        f"SELECT id FROM {table} WHERE lower(coalesce(status, '')) IN ('pending', 'queued', 'new') LIMIT ?",
        (limit,),
    ).fetchall()
    for row in pending:
        conn.execute(
            f"UPDATE {table} SET status = 'warmup_logged' WHERE id = ?",
            (row["id"],),
        )
    return len(pending)


def write_warmup_activity(
    conn: sqlite3.Connection,
    set_name: str,
    target: str,
    socials: list[dict],
    blogs: list[dict],
    cycle: int,
) -> None:
    stamp = utc_stamp()
    channels = socials + [
        {
            "platform": "blog",
            "handle": item.get("name"),
            "url": item.get("url"),
            "status": item.get("status"),
        }
        for item in blogs
    ]
    if not channels:
        channels = [{"platform": "unconfigured", "handle": "n/a", "status": "idle"}]

    index = (cycle - 1) % len(channels)
    channel = channels[index]
    platform = str(channel.get("platform") or "unknown")
    handle = str(channel.get("handle") or channel.get("name") or "n/a")

    conn.execute(
        """
        INSERT INTO organic_content_queue (
            platform, content_category, content_format, content_text,
            hashtags, image_description, status, scheduled_time, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            platform,
            "organic_warmup",
            "status_tick",
            f"Warm-up tick #{cycle} for {handle} promoting {target}",
            f"#{TARGET_SITE.replace('.', '')} #sosyalimece",
            "organic engagement pulse",
            "pending",
            stamp,
            stamp,
        ),
    )
    conn.execute(
        """
        INSERT INTO warmup_phase_log (phase, action, platform, result, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "live_worker",
            f"cycle_{cycle}",
            platform,
            f"{set_name}:{handle}",
            stamp,
        ),
    )


def run_cycle(
    conn: sqlite3.Connection,
    set_name: str,
    target: str,
    socials: list[dict],
    blogs: list[dict],
    cycle: int,
) -> None:
    write_warmup_activity(conn, set_name, target, socials, blogs, cycle)
    pending_organic = process_pending_queue(conn, "organic_content_queue")
    pending_tasks = process_pending_queue(conn, "task_queue")
    message = (
        f"cycle={cycle} set={set_name} target={target} "
        f"social={len(socials)} blogs={len(blogs)} "
        f"pending_organic={pending_organic} pending_tasks={pending_tasks}"
    )
    log_id = insert_system_log(conn, "INFO", message)
    conn.commit()
    log_stdout(
        "OK",
        f"Cycle {cycle} complete | {message} | system_logs id={log_id}",
    )


def interruptible_sleep(seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while not _shutdown_requested:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(1.0, remaining))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live worker daemon for trendurunlermarket.com")
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("WORKER_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS)),
        help=f"Seconds between cycles (default {DEFAULT_INTERVAL_SECONDS}, env WORKER_INTERVAL_SECONDS)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle and exit (useful for tests)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    interval = max(1, int(args.interval))

    signal.signal(signal.SIGINT, request_shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_shutdown)

    config = load_active_set(CONFIG_PATH)
    set_name, target, socials, blogs = parse_channels(config)
    print_channel_status(set_name, target, socials, blogs)

    try:
        conn = connect_db(DB_PATH)
        ensure_tables(conn)
        startup_msg = (
            f"Live worker daemon started for {set_name} targeting {target} "
            f"with {len(socials)} social channels and {len(blogs)} blogs "
            f"(interval={interval}s)"
        )
        row_id = insert_system_log(conn, "INFO", startup_msg)
        conn.commit()
        log_stdout("OK", f"Connected to SQLite: {DB_PATH}")
        log_stdout("OK", f"Startup logged in system_logs id={row_id}")
    except sqlite3.Error as exc:
        log_stdout("ERROR", f"SQLite startup failed: {exc}")
        return 1

    log_stdout("INFO", f"Daemon loop running every {interval}s. Ctrl+C to stop.")
    cycle = 0
    try:
        while not _shutdown_requested:
            cycle += 1
            try:
                run_cycle(conn, set_name, target, socials, blogs, cycle)
            except sqlite3.Error as exc:
                log_stdout("ERROR", f"Cycle {cycle} database error: {exc}")
            if args.once or _shutdown_requested:
                break
            interruptible_sleep(interval)
    except KeyboardInterrupt:
        request_shutdown()
    finally:
        insert_system_log(
            conn,
            "INFO",
            f"Live worker daemon stopped after {cycle} cycle(s)",
        )
        conn.commit()
        conn.close()
        log_stdout("OK", f"Worker stopped after {cycle} cycle(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
