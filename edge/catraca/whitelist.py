"""Cache local (SQLite) da whitelist, versionado pela nuvem."""
import sqlite3


class Whitelist:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        with self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS whitelist (plate TEXT PRIMARY KEY, name TEXT)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)"
            )

    def replace_all(self, entries: list[tuple[str, str]], version: int) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM whitelist")
            self._conn.executemany("INSERT INTO whitelist VALUES (?, ?)", entries)
            self._conn.execute(
                "INSERT INTO meta VALUES ('wl_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(version),),
            )

    def lookup(self, plate: str) -> str | None:
        row = self._conn.execute(
            "SELECT name FROM whitelist WHERE plate = ?", (plate,)
        ).fetchone()
        return row[0] if row else None

    def version(self) -> int:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'wl_version'"
        ).fetchone()
        return int(row[0]) if row else 0
