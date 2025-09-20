-- schema.sql — только DDL
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  tg_user_id      TEXT NOT NULL UNIQUE,
  username        TEXT,
  first_name      TEXT,
  last_name       TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS photos (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id            INTEGER NOT NULL,
  tg_file_unique_id  TEXT NOT NULL,
  tg_file_id         TEXT NOT NULL,
  caption            TEXT,
  created_at         TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(tg_file_unique_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS photo_tasks (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  photo_id      INTEGER NOT NULL,
  status        TEXT NOT NULL DEFAULT 'queued', -- queued|running|needs_user_input|done|failed
  retry_count   INTEGER NOT NULL DEFAULT 0,
  next_run_at   TEXT,
  result_json   TEXT,
  error         TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_photo_tasks_next_run ON photo_tasks(next_run_at);
CREATE INDEX IF NOT EXISTS ix_photo_tasks_status   ON photo_tasks(status);

CREATE TABLE IF NOT EXISTS kbju_cache (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  normalized_name TEXT NOT NULL,
  variant         TEXT,
  source          TEXT NOT NULL,
  source_url      TEXT,
  calories_100g   REAL NOT NULL,
  protein_100g    REAL NOT NULL,
  fat_100g        REAL NOT NULL,
  carbs_100g      REAL NOT NULL,
  confidence      REAL,
  version_tag     TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(normalized_name, variant)
);

CREATE INDEX IF NOT EXISTS ix_kbju_normalized_name ON kbju_cache(normalized_name);
