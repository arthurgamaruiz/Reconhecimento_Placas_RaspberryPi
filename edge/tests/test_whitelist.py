from catraca.whitelist import Whitelist


def test_empty(tmp_path):
    wl = Whitelist(str(tmp_path / "t.db"))
    assert wl.version() == 0
    assert wl.lookup("ABC1D23") is None


def test_replace_and_lookup(tmp_path):
    wl = Whitelist(str(tmp_path / "t.db"))
    wl.replace_all([("ABC1D23", "Pedro"), ("BRA2E19", "Visita")], version=7)
    assert wl.version() == 7
    assert wl.lookup("ABC1D23") == "Pedro"
    wl.replace_all([("BRA2E19", "Visita")], version=8)
    assert wl.version() == 8
    assert wl.lookup("ABC1D23") is None
    assert wl.lookup("BRA2E19") == "Visita"


def test_persists_across_instances(tmp_path):
    path = str(tmp_path / "t.db")
    Whitelist(path).replace_all([("ABC1D23", "Pedro")], version=1)
    wl2 = Whitelist(path)
    assert wl2.version() == 1
    assert wl2.lookup("ABC1D23") == "Pedro"
