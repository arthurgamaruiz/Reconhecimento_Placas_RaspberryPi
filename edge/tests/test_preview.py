import json
import urllib.error
import urllib.request

import pytest

from catraca.preview import Preview, start_server


def test_estado_inicial():
    p = Preview()
    assert p.frame() == b""
    assert "aguardando" in p.status()["text"]


def test_update_frame_e_status():
    p = Preview(clock=lambda: 123.0)
    p.update_frame(b"\xff\xd8jpg")
    p.set_status("ABC1D23 AUTORIZADA")
    assert p.frame() == b"\xff\xd8jpg"
    assert p.status() == {"text": "ABC1D23 AUTORIZADA", "ts": 123.0}


@pytest.fixture
def servidor():
    p = Preview()
    srv = start_server(p, 0)
    yield p, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_servidor_pagina_e_status(servidor):
    _, base = servidor
    html = urllib.request.urlopen(f"{base}/").read()
    assert b"Catraca ANPR" in html
    st = json.loads(urllib.request.urlopen(f"{base}/status").read())
    assert "aguardando" in st["text"]


def test_servidor_frame(servidor):
    p, base = servidor
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{base}/frame.jpg")
    assert exc.value.code == 503  # antes do primeiro frame

    p.update_frame(b"\xff\xd8fake")
    img = urllib.request.urlopen(f"{base}/frame.jpg?123").read()
    assert img == b"\xff\xd8fake"


def test_servidor_404(servidor):
    _, base = servidor
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(f"{base}/outra")
    assert exc.value.code == 404
