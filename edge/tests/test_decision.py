from catraca.decision import DecisionEngine


class FakeWl:
    def lookup(self, plate):
        return "Pedro" if plate == "ABC1D23" else None


def test_authorized_and_denied():
    t = [0.0]
    eng = DecisionEngine(FakeWl(), cooldown_s=10, clock=lambda: t[0])
    d = eng.decide("ABC1D23")
    assert d.authorized and d.name == "Pedro" and d.plate == "ABC1D23"
    d2 = eng.decide("XYZ9A88")
    assert d2.authorized is False and d2.name is None


def test_cooldown_per_plate():
    t = [0.0]
    eng = DecisionEngine(FakeWl(), cooldown_s=10, clock=lambda: t[0])
    assert eng.decide("ABC1D23") is not None
    t[0] = 5.0
    assert eng.decide("ABC1D23") is None      # mesma placa, dentro do cooldown
    assert eng.decide("XYZ9A88") is not None  # outra placa passa
    t[0] = 11.0
    assert eng.decide("ABC1D23") is not None
