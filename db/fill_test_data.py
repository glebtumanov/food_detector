#!/usr/bin/env python3
# fill_test_data.py — наполняет БД фейковыми данными для быстрой проверки
import argparse
import os
import random
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

DEFAULT_DB_PATH = Path(os.getenv("DB_PATH", "./app.db")).resolve()

USERS = [
    {"tg_user_id": "1001", "username": "alice", "first_name": "Alice", "last_name": "Wonder"},
    {"tg_user_id": "1002", "username": "bob",   "first_name": "Bob",   "last_name": "Builder"},
    {"tg_user_id": "1003", "username": "carol", "first_name": "Carol", "last_name": "Smith"},
]

PRODUCTS = [
    ("chicken breast", None, "calorizator", "https://calorizator.ru/product/chicken-breast", 165, 31, 3.6, 0, 0.95),
    ("banana",         None, "calorizator", "https://calorizator.ru/product/banana",          96,  1.5, 0.5, 21, 0.98),
    ("rice white",     None, "fatsecret",   "https://www.fatsecret.com/calories-nutrition/rice", 130, 2.4, 0.3, 28, 0.9),
    ("salmon fillet",  None, "calorizator", "https://calorizator.ru/product/salmon",         208, 20,  13,  0,  0.92),
]

def fill(db_path: Path):
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()

    # users
    for u in USERS:
        cur.execute(
            """INSERT OR IGNORE INTO users (tg_user_id, username, first_name, last_name)
               VALUES (?, ?, ?, ?)""",
            (u["tg_user_id"], u["username"], u["first_name"], u["last_name"])
        )

    # kbju_cache
    for name, variant, source, url, cal, pr, fat, carb, conf in PRODUCTS:
        cur.execute(
            """INSERT OR IGNORE INTO kbju_cache
               (normalized_name, variant, source, source_url, calories_100g, protein_100g, fat_100g, carbs_100g, confidence, version_tag)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, variant, source, url, cal, pr, fat, carb, conf, "v1")
        )

    # photos + photo_tasks
    user_ids = [row[0] for row in cur.execute("SELECT id FROM users").fetchall()]
    now = datetime.now(timezone.utc)
    for uid in user_ids:
        for i in range(2):  # по 2 фото на юзера
            fu = f"uniq_{uid}_{i}"
            fid = f"file_{uid}_{i}"
            cap = random.choice(["Обед", "Ужин", "Завтрак", "Перекус"])
            cur.execute(
                """INSERT OR IGNORE INTO photos (user_id, tg_file_unique_id, tg_file_id, caption, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (uid, fu, fid, cap, (now - timedelta(minutes=10*i)).isoformat().replace("+00:00","Z"))
            )
            photo_row = cur.execute(
                "SELECT id FROM photos WHERE tg_file_unique_id = ?", (fu,)
            ).fetchone()
            if not photo_row:
                continue
            pid = photo_row[0]
            status = random.choice(["queued", "running", "done"])
            next_run = (now + timedelta(minutes=random.randint(1, 30))).isoformat().replace("+00:00","Z") if status != "done" else None
            cur.execute(
                """INSERT INTO photo_tasks (photo_id, status, retry_count, next_run_at, result_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    pid,
                    status,
                    random.randint(0, 3),
                    next_run,
                    '{"sample":"ok"}' if status == "done" else None,
                    now.isoformat().replace("+00:00","Z"),
                    now.isoformat().replace("+00:00","Z"),
                )
            )

    con.commit()
    con.close()

def clear(db_path: Path):
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()

    # remove kbju_cache test entries
    for name, variant, source, url, *_rest in PRODUCTS:
        cur.execute(
            """DELETE FROM kbju_cache
                   WHERE normalized_name = ? AND source = ? AND source_url = ? AND version_tag = ?
            """,
            (name, source, url, "v1"),
        )

    # remove test users (CASCADE will delete photos and photo_tasks)
    test_tg_ids = [u["tg_user_id"] for u in USERS]
    placeholders = ",".join(["?"] * len(test_tg_ids))
    cur.execute(f"DELETE FROM users WHERE tg_user_id IN ({placeholders})", test_tg_ids)

    con.commit()
    con.close()

def main():
    ap = argparse.ArgumentParser(description="Fill SQLite DB with fake test data")
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite DB file (default: ./app.db)")
    ap.add_argument("--clear", action="store_true", help="Remove previously inserted test data and exit")
    args = ap.parse_args()

    if args.clear:
        clear(Path(args.db))
        print(f"OK: test data cleared from {args.db}")
    else:
        fill(Path(args.db))
        print(f"OK: test data inserted into {args.db}")

if __name__ == "__main__":
    main()
