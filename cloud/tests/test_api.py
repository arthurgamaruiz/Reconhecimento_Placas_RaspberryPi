from fastapi.testclient import TestClient

from app.main import create_app


def _client(tmp_path):
    return TestClient(create_app(data_dir=str(tmp_path), api_key="test"))


def _post_event(c, plate="ABC1D23", authorized="true"):
    return c.post(
        "/api/events",
        headers={"X-API-Key": "test"},
        data={"plate": plate, "authorized": authorized, "ocr_confidence": "0.93",
              "used_fallback": "false", "ts": "2026-08-29T12:00:00Z"},
        files={"photo": ("f.jpg", b"\xff\xd8fake", "image/jpeg")},
    )


def test_reject_without_key(tmp_path):
    c = _client(tmp_path)
    assert c.post("/api/events").status_code in (401, 403)
    assert c.get("/api/events").status_code in (401, 403)


def test_reject_wrong_key(tmp_path):
    c = _client(tmp_path)
    r = c.get("/api/events", headers={"X-API-Key": "errada"})
    assert r.status_code in (401, 403)


def test_post_and_list(tmp_path):
    c = _client(tmp_path)
    r = _post_event(c)
    assert r.status_code == 201
    assert "id" in r.json()
    evs = c.get("/api/events", headers={"X-API-Key": "test"}).json()
    assert len(evs) == 1
    ev = evs[0]
    assert ev["plate"] == "ABC1D23"
    assert ev["authorized"] is True
    assert ev["used_fallback"] is False
    assert "photo_url" in ev


def test_list_newest_first_with_limit(tmp_path):
    c = _client(tmp_path)
    _post_event(c, plate="ABC1234")
    _post_event(c, plate="BRA2E19")
    evs = c.get("/api/events?limit=1", headers={"X-API-Key": "test"}).json()
    assert len(evs) == 1 and evs[0]["plate"] == "BRA2E19"


def test_photo_roundtrip(tmp_path):
    c = _client(tmp_path)
    eid = _post_event(c).json()["id"]
    r = c.get(f"/api/events/{eid}/photo", headers={"X-API-Key": "test"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content.startswith(b"\xff\xd8")


def test_photo_404(tmp_path):
    c = _client(tmp_path)
    assert c.get("/api/events/999/photo", headers={"X-API-Key": "test"}).status_code == 404
