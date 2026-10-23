"""SQLite setup and schema management."""
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant TEXT NOT NULL,
    writer_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    hlc TEXT NOT NULL,
    idem_key TEXT,
    base_version INTEGER,
    type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(tenant, writer_id, idem_key)
);
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    project TEXT NOT NULL,
    kind TEXT NOT NULL,
    text TEXT NOT NULL,
    entity_id TEXT,
    attribute TEXT,
    value TEXT,
    valid_from TEXT NOT NULL,
    valid_to TEXT,
    confidence REAL NOT NULL,
    writer_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    source_episode TEXT,
    span_start INTEGER,
    span_end INTEGER,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used TEXT,
    decay_weight REAL NOT NULL DEFAULT 1.0,
    pinned INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    version INTEGER NOT NULL,
    event_id INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_tenant_project ON nodes(tenant, project);
CREATE INDEX IF NOT EXISTS idx_nodes_entity_attribute ON nodes(entity_id, attribute, status);
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    canonical TEXT NOT NULL,
    created_event INTEGER NOT NULL,
    UNIQUE(tenant, canonical)
);
CREATE TABLE IF NOT EXISTS entity_aliases (
    alias TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    PRIMARY KEY(alias, entity_id)
);
CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL,
    dst TEXT NOT NULL,
    type TEXT NOT NULL,
    event_id INTEGER NOT NULL,
    PRIMARY KEY(src, dst, type, event_id)
);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    node_id UNINDEXED, text, entity, attribute, value
);
CREATE TABLE IF NOT EXISTS embeddings (
    node_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    dim INTEGER NOT NULL,
    vector BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS packets (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL,
    session_id TEXT NOT NULL,
    task_state TEXT NOT NULL,
    key_episode_ids TEXT NOT NULL,
    snapshot_event_id INTEGER,
    created_at TEXT NOT NULL
);
"""


def check_fts5() -> None:
    try:
        with sqlite3.connect(":memory:") as conn:
            conn.execute("CREATE VIRTUAL TABLE fts5_probe USING fts5(content)")
            conn.execute("DROP TABLE fts5_probe")
    except sqlite3.Error as exc:
        raise RuntimeError(
            "SQLite FTS5 is unavailable. Install/use a Python build linked against SQLite with FTS5 enabled."
        ) from exc


def connect(db_path: str) -> sqlite3.Connection:
    check_fts5()
    if db_path != ":memory:":
        Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA secure_delete = ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn
