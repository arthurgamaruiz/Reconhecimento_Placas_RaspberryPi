from catraca.signals import GateSignals


def test_authorized_lights_green():
    s = GateSignals(hold_s=0.05)
    s.authorized()
    assert s.green.is_active
    assert not s.red.is_active
    s.close()


def test_denied_lights_red():
    s = GateSignals(hold_s=0.05)
    s.denied()
    assert s.red.is_active
    assert not s.green.is_active
    s.close()


def test_denied_after_authorized_switches():
    s = GateSignals(hold_s=5.0)
    s.authorized()
    s.denied()
    assert s.red.is_active
    assert not s.green.is_active
    s.close()
