"""Sincronização com a nuvem: sobe eventos pendentes, desce whitelist versionada.

Falha de rede aqui NUNCA derruba o loop principal — loga e tenta no próximo ciclo.
"""
import logging
import threading
import time

import requests

from catraca.events import Event, EventStore
from catraca.whitelist import Whitelist

log = logging.getLogger(__name__)


class CloudClient:
    def __init__(self, base_url: str, api_key: str, http=None, timeout_s: float = 15.0):
        self._base = base_url.rstrip("/")
        self._headers = {"X-API-Key": api_key}
        self._http = http if http is not None else requests.Session()
        self._timeout = timeout_s

    def push_event(self, ev: Event) -> bool:
        resp = self._http.post(
            f"{self._base}/api/events",
            headers=self._headers,
            data={
                "plate": ev.plate,
                "authorized": "true" if ev.authorized else "false",
                "ocr_confidence": str(ev.ocr_confidence),
                "used_fallback": "true" if ev.used_fallback else "false",
                "ts": ev.ts,
            },
            files={"photo": ("event.jpg", ev.photo_jpeg, "image/jpeg")},
            timeout=self._timeout,
        )
        return 200 <= resp.status_code < 300

    def add_plate(self, plate: str, name: str) -> bool:
        resp = self._http.post(
            f"{self._base}/api/whitelist",
            headers=self._headers,
            json={"plate": plate, "name": name},
            timeout=self._timeout,
        )
        return 200 <= resp.status_code < 300

    def fetch_whitelist(self, since_version: int) -> tuple[int, list[tuple[str, str]]] | None:
        resp = self._http.get(
            f"{self._base}/api/whitelist",
            headers=self._headers,
            params={"since": since_version},
            timeout=self._timeout,
        )
        if resp.status_code != 200:
            return None
        body = resp.json()
        if body.get("unchanged") or body.get("version", 0) <= since_version:
            return None
        return body["version"], [(p["plate"], p["name"]) for p in body.get("plates", [])]


class SyncWorker:
    def __init__(self, store: EventStore, whitelist: Whitelist, client: CloudClient,
                 interval_s: float = 30.0):
        self._store = store
        self._whitelist = whitelist
        self._client = client
        self._interval = interval_s

    def run_once(self) -> None:
        try:
            for ev in self._store.pending():
                if self._client.push_event(ev):
                    self._store.mark_synced(ev.id)
                else:
                    break  # nuvem recusando; tenta de novo no próximo ciclo
            update = self._client.fetch_whitelist(self._whitelist.version())
            if update is not None:
                version, entries = update
                self._whitelist.replace_all(entries, version=version)
                log.info("whitelist atualizada para v%s (%d placas)", version, len(entries))
        except Exception:
            log.warning("sync falhou; mantendo fila local", exc_info=True)

    def start(self) -> threading.Thread:
        def _loop():
            while True:
                self.run_once()
                time.sleep(self._interval)

        t = threading.Thread(target=_loop, daemon=True, name="sync-worker")
        t.start()
        return t
