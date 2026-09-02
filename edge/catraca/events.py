"""Fila offline de eventos: tudo grava local; a nuvem recebe quando der."""
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Event:
    id: int
    ts: str
    plate: str
    authorized: bool
    ocr_confidence: float
    used_fallback: bool
    photo_jpeg: bytes


class EventStore:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        with self._conn:
            self._conn.execute(
                """CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    plate TEXT NOT NULL,
                    authorized INTEGER NOT NULL,
                    ocr_confidence REAL NOT NULL,
                    used_fallback INTEGER NOT NULL,
                    photo BLOB NOT NULL,
                    synced INTEGER NOT NULL DEFAULT 0
                )"""
            )

    def record(self, plate: str, authorized: bool, ocr_confidence: float,
               used_fallback: bool, photo_jpeg: bytes) -> int:
        ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO events (ts, plate, authorized, ocr_confidence, used_fallback, photo)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (ts, plate, int(authorized), ocr_confidence, int(used_fallback), photo_jpeg),
            )
        return cur.lastrowid

    def pending(self, limit: int = 20) -> list[Event]:
        rows = self._conn.execute(
            "SELECT id, ts, plate, authorized, ocr_confidence, used_fallback, photo"
            " FROM events WHERE synced = 0 ORDER BY id LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Event(id=r[0], ts=r[1], plate=r[2], authorized=bool(r[3]),
                  ocr_confidence=r[4], used_fallback=bool(r[5]), photo_jpeg=r[6])
            for r in rows
        ]

    def mark_synced(self, event_id: int) -> None:
        with self._conn:
            self._conn.execute("UPDATE events SET synced = 1 WHERE id = ?", (event_id,))
