import pytest

from catraca.button import AuthorizeButton


@pytest.fixture
def make_btn():
    created = []

    def _make(client, **kw):
        btn = AuthorizeButton(client, **kw)
        created.append(btn)
        return btn

    yield _make
    for btn in created:
        btn.close()


class FakeClient:
    def __init__(self, ok=True):
        self.calls = []
        self._ok = ok

    def add_plate(self, plate, name):
        self.calls.append((plate, name))
        return self._ok


def test_press_authorizes_last_denied(make_btn):
    t = [0.0]
    done = []
    client = FakeClient()
    btn = make_btn(client, clock=lambda: t[0], on_authorized=done.append)
    btn.register_denied("XYZ9A88")
    btn.pressed()
    assert client.calls == [("XYZ9A88", "Autorizado no botão")]
    assert done == ["XYZ9A88"]


def test_press_without_denied_is_noop(make_btn):
    client = FakeClient()
    make_btn(client).pressed()
    assert client.calls == []


def test_window_expires(make_btn):
    t = [0.0]
    client = FakeClient()
    btn = make_btn(client, window_s=30, clock=lambda: t[0])
    btn.register_denied("XYZ9A88")
    t[0] = 31.0
    btn.pressed()
    assert client.calls == []


def test_double_press_adds_once(make_btn):
    client = FakeClient()
    btn = make_btn(client)
    btn.register_denied("XYZ9A88")
    btn.pressed()
    btn.pressed()
    assert len(client.calls) == 1


def test_failed_add_keeps_pending_for_retry(make_btn):
    client = FakeClient(ok=False)
    btn = make_btn(client)
    btn.register_denied("XYZ9A88")
    btn.pressed()
    btn.pressed()  # nuvem falhou na 1a; segunda tentativa deve reenviar
    assert len(client.calls) == 2
