import numpy as np

from catraca.motion import MotionGate

BLACK = np.zeros((480, 640, 3), dtype=np.uint8)


def _with_square(img, v=255):
    out = img.copy()
    out[100:300, 100:300] = v
    return out


def test_first_frame_is_baseline():
    assert MotionGate().triggered(BLACK) is False


def test_static_scene_never_triggers():
    g = MotionGate()
    g.triggered(BLACK)
    assert g.triggered(BLACK) is False
    assert g.triggered(BLACK) is False


def test_change_triggers():
    g = MotionGate()
    g.triggered(BLACK)
    assert g.triggered(_with_square(BLACK)) is True


def test_returning_to_static_stops_triggering():
    g = MotionGate()
    g.triggered(BLACK)
    moved = _with_square(BLACK)
    g.triggered(moved)
    assert g.triggered(moved) is False
