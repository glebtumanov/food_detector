#!/usr/bin/env python3
# db_init.py — применяет schema.sql: создаёт то, чего нет, ничего не трогает у уже существующего
import argparse
import os
import re
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DB_PATH = Path(os.getenv("DB_PATH", "./app.db")).resolve()
DEFAULT_SCHEMA_PATH = HERE / "schema.sql"

def _load_schema(schema_path: Path) -> str:
    sql = schema_path.read_text(encoding="utf-8")
    return sql

def _add_if_not_exists(sql: str) -> str:
    # Делает создание идемпотентным, если автор схемы забыл IF NOT EXISTS
    # Обрабатываем TABLE/INDEX/TRIGGER/VIEW
    patterns = [
        (r"(?i)\bCREATE\s+TABLE\s+(?!IF\s+NOT\s+EXISTS)", "CREATE TABLE IF NOT EXISTS "),
        (r"(?i)\bCREATE\s+INDEX\s+(?!IF\s+NOT\s+EXISTS)", "CREATE INDEX IF NOT EXISTS "),
        (r"(?i)\bCREATE\s+TRIGGER\s+(?!IF\s+NOT\s+EXISTS)", "CREATE TRIGGER IF NOT EXISTS "),
        (r"(?i)\bCREATE\s+VIEW\s+(?!IF\s+NOT\s+EXISTS)", "CREATE VIEW IF NOT EXISTS "),
    ]
    out = sql
    for pat, repl in patterns:
        out = re.sub(pat, repl, out)
    return out

def _split_statements(sql: str) -> list[str]:
    # Простой сплит по ';' (работает для нашей плоской DDL-схемы)
    parts = [s.strip() for s in sql.split(";")]
    return [p for p in parts if p and not p.startswith("--")]

def init_db(db_path: Path, schema_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    raw = _load_schema(schema_path)
    sql = _add_if_not_exists(raw)
    stmts = _split_statements(sql)

    con = sqlite3.connect(str(db_path))
    try:
        con.execute("PRAGMA foreign_keys = ON;")
        cur = con.cursor()
        for st in stmts:
            cur.execute(st)
        con.commit()
    finally:
        con.close()

def main():
    ap = argparse.ArgumentParser(description="Initialize SQLite DB from schema.sql")
    ap.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite DB file (default: ./app.db)")
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH), help="Path to schema.sql")
    args = ap.parse_args()

    init_db(Path(args.db), Path(args.schema))
    print(f"OK: database initialized at {args.db} using {args.schema}")

if __name__ == "__main__":
    main()
