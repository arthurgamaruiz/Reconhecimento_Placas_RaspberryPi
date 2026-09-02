import pytest

from catraca import plates


@pytest.mark.parametrize("raw,expected", [
    ("abc-1d23", "ABC1D23"),
    (" BRA 2E19 ", "BRA2E19"),
])
def test_normalize(raw, expected):
    assert plates.normalize(raw) == expected


@pytest.mark.parametrize("plate,ok", [
    ("ABC1D23", True),   # Mercosul
    ("ABC1234", True),   # formato antigo
    ("AB12345", False),
    ("ABCD123", False),
    ("ABC1D2", False),
])
def test_is_valid(plate, ok):
    assert plates.is_valid(plate) is ok


@pytest.mark.parametrize("bad,fixed", [
    ("A8C1D23", "ABC1D23"),  # 8→B em posição de letra
    ("ABCID23", "ABC1D23"),  # I→1 em posição de dígito
    ("ABC1D2O", "ABC1D20"),  # O→0
    ("ABC12E4", None),       # E não vira dígito
    ("ABC1D23", "ABC1D23"),  # já válida passa intacta
    ("AB1", None),           # tamanho errado
])
def test_fix_confusions(bad, fixed):
    assert plates.fix_confusions(bad) == fixed
