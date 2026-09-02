from types import SimpleNamespace

from catraca.fallback import ClaudeOcrFallback


class FakeClient:
    def __init__(self, text):
        self.kwargs = None
        resp = SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])

        def create(**kw):
            self.kwargs = kw
            return resp

        self.messages = SimpleNamespace(create=create)


class BoomClient:
    @property
    def messages(self):
        raise RuntimeError("api down")


def test_reads_valid_plate_and_normalizes():
    client = FakeClient("abc1d23")
    fb = ClaudeOcrFallback(client=client)
    assert fb.read_plate(b"\xff\xd8jpg") == "ABC1D23"
    # imagem foi de fato enviada como bloco base64 jpeg
    blocks = client.kwargs["messages"][0]["content"]
    img = next(b for b in blocks if b["type"] == "image")
    assert img["source"]["media_type"] == "image/jpeg"
    assert img["source"]["type"] == "base64"


def test_fixes_ocr_confusions():
    assert ClaudeOcrFallback(client=FakeClient("A8C1D23")).read_plate(b"j") == "ABC1D23"


def test_none_response():
    assert ClaudeOcrFallback(client=FakeClient("NONE")).read_plate(b"j") is None


def test_garbage_response():
    assert ClaudeOcrFallback(client=FakeClient("nao consegui ler")).read_plate(b"j") is None


def test_api_error_returns_none():
    assert ClaudeOcrFallback(client=BoomClient()).read_plate(b"j") is None
