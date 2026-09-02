from fastapi.testclient import TestClient

from app.main import create_app

H = {"X-API-Key": "test"}


def _client(tmp_path):
    return TestClient(create_app(data_dir=str(tmp_path), api_key="test"))


def test_starts_empty_v0(tmp_path):
    c = _client(tmp_path)
    body = c.get("/api/whitelist?since=-1", headers=H).json()
    assert body["version"] == 0 and body["plates"] == []


def test_add_bumps_version_and_lists(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/whitelist", json={"plate": "abc-1d23", "name": "Pedro"}, headers=H)
    assert r.status_code == 201
    body = c.get("/api/whitelist?since=0", headers=H).json()
    assert body["version"] == 1
    assert body["plates"] == [{"plate": "ABC1D23", "name": "Pedro"}]  # normalizada


def test_unchanged_when_same_version(tmp_path):
    c = _client(tmp_path)
    c.post("/api/whitelist", json={"plate": "ABC1D23", "name": "P"}, headers=H)
    body = c.get("/api/whitelist?since=1", headers=H).json()
    assert body["version"] == 1 and body.get("unchanged") is True


def test_invalid_plate_rejected(tmp_path):
    c = _client(tmp_path)
    r = c.post("/api/whitelist", json={"plate": "NOPE", "name": "x"}, headers=H)
    assert r.status_code == 422


def test_delete_bumps_version(tmp_path):
    c = _client(tmp_path)
    c.post("/api/whitelist", json={"plate": "ABC1D23", "name": "P"}, headers=H)
    assert c.delete("/api/whitelist/ABC1D23", headers=H).status_code == 200
    body = c.get("/api/whitelist?since=1", headers=H).json()
    assert body["version"] == 2 and body["plates"] == []


def test_requires_key(tmp_path):
    c = _client(tmp_path)
    assert c.get("/api/whitelist?since=-1").status_code in (401, 403)
    assert c.post("/api/whitelist", json={"plate": "ABC1D23", "name": "x"}).status_code in (401, 403)


def test_dashboard_served_without_key(tmp_path):
    c = _client(tmp_path)
    r = c.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert 'id="timeline"' in r.text
