"""SQLite da nuvem: eventos (com foto), whitelist e versão."""
import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    plate TEXT NOT NULL,
    authorized INTEGER NOT NULL,
    ocr_confidence REAL NOT NULL,
    used_fallback INTEGER NOT NULL,
    photo BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS whitelist (plate TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript(_SCHEMA)
    return conn


def wl_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT value FROM meta WHERE key = 'wl_version'").fetchone()
    return int(row[0]) if row else 0


def wl_bump(conn: sqlite3.Connection) -> int:
    new = wl_version(conn) + 1
    conn.execute(
        "INSERT INTO meta VALUES ('wl_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(new),),
    )
    return new
