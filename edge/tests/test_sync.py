from catraca.events import EventStore
from catraca.sync import CloudClient, SyncWorker
from catraca.whitelist import Whitelist


class FakeResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._p = payload or {}

    def json(self):
        return self._p


class FakeHttp:
    def __init__(self, get_payload=None, post_status=201, boom=False):
        self._g, self._s, self._boom = get_payload, post_status, boom
        self.posts = []

    def post(self, url, **kw):
        if self._boom:
            raise ConnectionError("net down")
        self.posts.append((url, kw))
        return FakeResp(self._s)

    def get(self, url, **kw):
        if self._boom:
            raise ConnectionError("net down")
        return FakeResp(200, self._g)


def _worker(tmp_path, http):
    st = EventStore(str(tmp_path / "t.db"))
    wl = Whitelist(str(tmp_path / "t.db"))
    client = CloudClient("http://c", "k", http=http)
    return st, wl, SyncWorker(st, wl, client, interval_s=30)


def test_push_marks_synced(tmp_path):
    http = FakeHttp(get_payload={"version": 0, "plates": []})
    st, wl, w = _worker(tmp_path, http)
    st.record("ABC1D23", True, 0.9, False, b"j")
    w.run_once()
    assert st.pending() == []
    url, kw = http.posts[0]
    assert url == "http://c/api/events"
    assert kw["headers"]["X-API-Key"] == "k"
    assert kw["data"]["plate"] == "ABC1D23"
    assert "photo" in kw["files"]


def test_whitelist_update(tmp_path):
    payload = {"version": 3, "plates": [{"plate": "ABC1D23", "name": "Pedro"}]}
    st, wl, w = _worker(tmp_path, FakeHttp(get_payload=payload))
    w.run_once()
    assert wl.version() == 3
    assert wl.lookup("ABC1D23") == "Pedro"


def test_whitelist_unchanged_is_ignored(tmp_path):
    st, wl, w = _worker(tmp_path, FakeHttp(get_payload={"version": 0, "unchanged": True}))
    wl.replace_all([("BRA2E19", "V")], version=0)
    w.run_once()
    assert wl.lookup("BRA2E19") == "V"  # não foi sobrescrita


def test_network_failure_keeps_pending_and_does_not_raise(tmp_path):
    st, wl, w = _worker(tmp_path, FakeHttp(boom=True))
    st.record("ABC1D23", True, 0.9, False, b"j")
    w.run_once()  # não pode explodir
    assert len(st.pending()) == 1


def test_add_plate_posts_json():
    http = FakeHttp()
    client = CloudClient("http://c", "k", http=http)
    assert client.add_plate("XYZ9A88", "Botão") is True
    url, kw = http.posts[0]
    assert url == "http://c/api/whitelist"
    assert kw["json"] == {"plate": "XYZ9A88", "name": "Botão"}
    assert kw["headers"]["X-API-Key"] == "k"


def test_failed_post_not_marked_synced(tmp_path):
    http = FakeHttp(get_payload={"version": 0, "plates": []}, post_status=500)
    st, wl, w = _worker(tmp_path, http)
    st.record("ABC1D23", True, 0.9, False, b"j")
    w.run_once()
    assert len(st.pending()) == 1
