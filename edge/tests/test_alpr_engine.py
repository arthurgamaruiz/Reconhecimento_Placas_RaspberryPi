from types import SimpleNamespace

import numpy as np

from catraca.alpr_engine import AlprEngine

FRAME = np.zeros((480, 640, 3), dtype=np.uint8)


def _result(text, conf, box=(10, 10, 200, 60)):
    x1, y1, x2, y2 = box
    return SimpleNamespace(
        detection=SimpleNamespace(
            bounding_box=SimpleNamespace(x1=x1, y1=y1, x2=x2, y2=y2),
            confidence=0.9,
        ),
        ocr=SimpleNamespace(text=text, confidence=conf),
    )


class FakeAlpr:
    def __init__(self, results):
        self._r = results

    def predict(self, frame):
        return self._r


def test_no_plate():
    assert AlprEngine(alpr=FakeAlpr([])).read(FRAME) is None


def test_best_by_confidence_and_normalized():
    eng = AlprEngine(alpr=FakeAlpr([_result("abc-1d23", 0.7), _result("BRA2E19", 0.95)]))
    r = eng.read(FRAME)
    assert r.plate == "BRA2E19"
    assert r.ocr_confidence == 0.95
    assert r.crop.shape[0] == 50 and r.crop.shape[1] == 190


def test_per_char_confidence_list_uses_min():
    # API real: ocr.confidence é lista por caractere (pode vir com padding extra)
    eng = AlprEngine(alpr=FakeAlpr([_result("ABC1D23", [0.99, 0.98, 0.4, 0.99, 0.97, 0.99, 0.99, 0.99, 0.99])]))
    r = eng.read(FRAME)
    assert r.plate == "ABC1D23"
    assert r.ocr_confidence == 0.4


def test_bbox_clamped_to_frame():
    eng = AlprEngine(alpr=FakeAlpr([_result("ABC1D23", 0.9, box=(-10, -5, 9999, 9999))]))
    r = eng.read(FRAME)
    assert r.crop.shape[0] == 480 and r.crop.shape[1] == 640
