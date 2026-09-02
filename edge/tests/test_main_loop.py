from types import SimpleNamespace

import numpy as np

from catraca.config import Config
from catraca.decision import DecisionEngine
from catraca.events import EventStore
from catraca.main import process_frame

FRAME = np.zeros((120, 160, 3), dtype=np.uint8)
CFG = Config.from_env(env={})


class AlwaysMotion:
    def triggered(self, f):
        return True


class NeverMotion:
    def triggered(self, f):
        return False


class FakeAlpr:
    def __init__(self, reading):
        self._r = reading

    def read(self, f):
        return self._r


class SpySignals:
    def __init__(self):
        self.calls = []

    def authorized(self):
        self.calls.append("authorized")

    def denied(self):
        self.calls.append("denied")


class FakeWl:
    def lookup(self, p):
        return "Pedro" if p == "ABC1D23" else None


def _reading(plate, conf=0.95):
    return SimpleNamespace(plate=plate, ocr_confidence=conf, crop=FRAME)


def _deps(tmp_path, reading, motion=None, fallback=None):
    return dict(
        motion=motion or AlwaysMotion(),
        alpr=FakeAlpr(reading),
        engine=DecisionEngine(FakeWl(), cooldown_s=0),
        signals=SpySignals(),
        store=EventStore(str(tmp_path / "t.db")),
        cfg=CFG,
        fallback=fallback,
    )


def test_no_motion_short_circuits(tmp_path):
    deps = _deps(tmp_path, _reading("ABC1D23"), motion=NeverMotion())
    assert process_frame(FRAME, **deps) == "no_motion"


def test_no_plate(tmp_path):
    deps = _deps(tmp_path, None)
    assert process_frame(FRAME, **deps) == "no_plate"


def test_authorized_flow(tmp_path):
    deps = _deps(tmp_path, _reading("ABC1D23"))
    assert process_frame(FRAME, **deps) == "authorized"
    assert deps["signals"].calls == ["authorized"]
    (ev,) = deps["store"].pending()
    assert ev.plate == "ABC1D23" and ev.authorized and not ev.used_fallback
    assert ev.photo_jpeg.startswith(b"\xff\xd8")  # JPEG de verdade


def test_denied_flow(tmp_path):
    deps = _deps(tmp_path, _reading("XYZ9A88"))
    assert process_frame(FRAME, **deps) == "denied"
    assert deps["signals"].calls == ["denied"]


def test_confusion_gets_fixed(tmp_path):
    deps = _deps(tmp_path, _reading("A8C1D23"))  # 8→B
    assert process_frame(FRAME, **deps) == "authorized"


def test_garbage_is_invalid_and_not_recorded(tmp_path):
    deps = _deps(tmp_path, _reading("Q#!"))
    assert process_frame(FRAME, **deps) == "invalid"
    assert deps["store"].pending() == []


def test_cooldown(tmp_path):
    deps = _deps(tmp_path, _reading("ABC1D23"))
    deps["engine"] = DecisionEngine(FakeWl(), cooldown_s=999)
    assert process_frame(FRAME, **deps) == "authorized"
    assert process_frame(FRAME, **deps) == "cooldown"


class SpyButton:
    def __init__(self):
        self.denied = []

    def register_denied(self, plate):
        self.denied.append(plate)


def test_denied_registers_on_button(tmp_path):
    deps = _deps(tmp_path, _reading("XYZ9A88"))
    btn = SpyButton()
    assert process_frame(FRAME, **deps, button=btn) == "denied"
    assert btn.denied == ["XYZ9A88"]


def test_authorized_does_not_touch_button(tmp_path):
    deps = _deps(tmp_path, _reading("ABC1D23"))
    btn = SpyButton()
    assert process_frame(FRAME, **deps, button=btn) == "authorized"
    assert btn.denied == []


def test_baixa_confianca_nao_decide(tmp_path):
    deps = _deps(tmp_path, _reading("ABC1D23", conf=0.3))  # valida, mas duvidosa
    assert process_frame(FRAME, **deps) == "low_conf"
    assert deps["signals"].calls == []
    assert deps["store"].pending() == []


def test_fallback_confiavel_decide_mesmo_com_conf_baixa(tmp_path):
    fb = FakeFallback("ABC1D23")
    deps = _deps(tmp_path, _reading("AB!!!23", conf=0.3), fallback=fb)
    assert process_frame(FRAME, **deps) == "authorized"


class SpyPreview:
    def __init__(self):
        self.lines = []

    def set_status(self, text):
        self.lines.append(text)


def test_preview_recebe_decisao(tmp_path):
    deps = _deps(tmp_path, _reading("ABC1D23"))
    pv = SpyPreview()
    assert process_frame(FRAME, **deps, preview=pv) == "authorized"
    assert pv.lines == ["ABC1D23 AUTORIZADA (conf=0.95)"]


def test_preview_nao_recebe_sem_decisao(tmp_path):
    deps = _deps(tmp_path, _reading("Q#!"))
    pv = SpyPreview()
    assert process_frame(FRAME, **deps, preview=pv) == "invalid"
    assert pv.lines == []


class FakeFallback:
    def __init__(self, answer):
        self.answer = answer
        self.calls = 0

    def read_plate(self, crop_jpeg):
        self.calls += 1
        return self.answer


def test_fallback_rescues_low_confidence(tmp_path):
    fb = FakeFallback("ABC1D23")
    deps = _deps(tmp_path, _reading("AB!!!23", conf=0.3), fallback=fb)
    assert process_frame(FRAME, **deps) == "authorized"
    assert fb.calls == 1
    (ev,) = deps["store"].pending()
    assert ev.used_fallback is True


def test_fallback_not_called_when_confident(tmp_path):
    fb = FakeFallback("XYZ9A88")
    deps = _deps(tmp_path, _reading("ABC1D23", conf=0.99), fallback=fb)
    assert process_frame(FRAME, **deps) == "authorized"
    assert fb.calls == 0


def test_fallback_fails_returns_invalid(tmp_path):
    fb = FakeFallback(None)
    deps = _deps(tmp_path, _reading("!!", conf=0.1), fallback=fb)
    assert process_frame(FRAME, **deps) == "invalid"
