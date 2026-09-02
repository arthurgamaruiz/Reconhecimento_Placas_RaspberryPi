"""API da catraca: recebe eventos do Pi, serve o dashboard e gerencia a whitelist."""
import os
import re
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app import db

# Mesma regra de placa do edge (Mercosul LLLDLDD e antigo LLLDDDD).
PLATE_RE = re.compile(r"^[A-Z]{3}\d[A-Z]\d{2}$|^[A-Z]{3}\d{4}$")
_DASHBOARD = Path(__file__).parent / "static" / "dashboard.html"


def _normalize(raw: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", raw.upper())


class WhitelistEntry(BaseModel):
    plate: str
    name: str


def create_app(data_dir: str | None = None, api_key: str | None = None) -> FastAPI:
    data_dir = data_dir if data_dir is not None else os.environ.get("DATA_DIR", ".")
    api_key = api_key if api_key is not None else os.environ.get("API_KEY", "")
    conn = db.connect(os.path.join(data_dir, "cloud.db"))
    app = FastAPI(title="Catraca ANPR")

    def require_key(x_api_key: str | None = Header(default=None)):
        if not api_key or x_api_key != api_key:
            raise HTTPException(status_code=401, detail="API key invalida")

    auth = [Depends(require_key)]

    @app.get("/")
    def dashboard():
        return FileResponse(_DASHBOARD, media_type="text/html")

    @app.post("/api/events", status_code=201, dependencies=auth)
    async def post_event(
        plate: str = Form(...),
        authorized: str = Form(...),
        ocr_confidence: float = Form(...),
        used_fallback: str = Form(...),
        ts: str = Form(...),
        photo: UploadFile = File(...),
    ):
        blob = await photo.read()
        with conn:
            cur = conn.execute(
                "INSERT INTO events (ts, plate, authorized, ocr_confidence, used_fallback, photo)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (ts, _normalize(plate), int(authorized == "true"),
                 ocr_confidence, int(used_fallback == "true"), blob),
            )
        return {"id": cur.lastrowid}

    @app.get("/api/events", dependencies=auth)
    def list_events(limit: int = 50):
        rows = conn.execute(
            "SELECT id, ts, plate, authorized, ocr_confidence, used_fallback"
            " FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "id": r[0], "ts": r[1], "plate": r[2], "authorized": bool(r[3]),
                "ocr_confidence": r[4], "used_fallback": bool(r[5]),
                "photo_url": f"/api/events/{r[0]}/photo",
            }
            for r in rows
        ]

    @app.get("/api/events/{event_id}/photo", dependencies=auth)
    def event_photo(event_id: int):
        row = conn.execute("SELECT photo FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404)
        return Response(content=row[0], media_type="image/jpeg")

    @app.get("/api/whitelist", dependencies=auth)
    def get_whitelist(since: int = -1):
        version = db.wl_version(conn)
        if since == version:
            return {"version": version, "unchanged": True}
        rows = conn.execute("SELECT plate, name FROM whitelist ORDER BY plate").fetchall()
        return {"version": version, "plates": [{"plate": r[0], "name": r[1]} for r in rows]}

    @app.post("/api/whitelist", status_code=201, dependencies=auth)
    def add_plate(entry: WhitelistEntry):
        plate = _normalize(entry.plate)
        if not PLATE_RE.match(plate):
            raise HTTPException(status_code=422, detail=f"placa invalida: {entry.plate}")
        with conn:
            conn.execute(
                "INSERT INTO whitelist VALUES (?, ?) "
                "ON CONFLICT(plate) DO UPDATE SET name = excluded.name",
                (plate, entry.name),
            )
            version = db.wl_bump(conn)
        return {"plate": plate, "version": version}

    @app.delete("/api/whitelist/{plate}", dependencies=auth)
    def remove_plate(plate: str):
        plate = _normalize(plate)
        with conn:
            cur = conn.execute("DELETE FROM whitelist WHERE plate = ?", (plate,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="placa nao esta na whitelist")
            version = db.wl_bump(conn)
        return {"plate": plate, "version": version}

    return app


app = create_app()
