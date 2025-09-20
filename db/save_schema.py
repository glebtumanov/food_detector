#!/usr/bin/env python3
# save_schema.py — выгружает текущую схему БД в db/schema.sql (только DDL)
import argparse
import os
import sqlite3
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.getenv("DB_PATH", "./app.db")).resolve()
DEFAULT_SCHEMA_PATH = HERE / "schema.sql"

DDL_TYPES = ("table", "index", "trigger", "view")

def dump_schema(db_path: Path, schema_path: Path):
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        cur = con.cursor()
        # Достаём только DDL, исключаем внутренние sqlite_*
        rows = cur.execute(
            """
            SELECT type, name, sql
            FROM sqlite_master
            WHERE type IN ('table','index','trigger','view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY
              CASE type
                WHEN 'table' THEN 1
                WHEN 'index' THEN 2
                WHEN 'trigger' THEN 3
                WHEN 'view' THEN 4
                ELSE 5
              END,
              name
            """
        ).fetchall()

        lines = []
        lines.append("-- schema.sql (auto-saved)")
        lines.append(f"-- saved at: {datetime.utcnow().isoformat()}Z")
        lines.append("PRAGMA foreign_keys = ON;")
        lines.append("")
        for t, name, sql in rows:
            if not sql:
                continue
            # Нормализуем IF NOT EXISTS, если автор изначально не добавил
            normalized = sql.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ") \
                            .replace("CREATE INDEX ", "CREATE INDEX IF NOT EXISTS ") \
                            .replace("CREATE TRIGGER ", "CREATE TRIGGER IF NOT EXISTS ") \
                            .replace("CREATE VIEW ", "CREATE VIEW IF NOT EXISTS ")
            lines.append(normalized.strip() + ";")
            lines.append("")

        schema_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    finally:
        con.close()

def main():
    ap = argparse.ArgumentParser(description="Save current DB schema to db/schema.sql")
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite DB file (default: ./app.db)")
    ap.add_argument("--out", default=str(DEFAULT_SCHEMA_PATH), help="Path to output schema.sql")
    args = ap.parse_args()

    dump_schema(Path(args.db), Path(args.out))
    print(f"OK: schema saved to {args.out}")

if __name__ == "__main__":
    main()
