from catraca.events import EventStore


def test_record_and_pending(tmp_path):
    st = EventStore(str(tmp_path / "t.db"))
    eid = st.record("ABC1D23", True, 0.93, False, b"\xff\xd8jpg")
    (ev,) = st.pending()
    assert ev.id == eid
    assert ev.plate == "ABC1D23"
    assert ev.authorized is True
    assert ev.ocr_confidence == 0.93
    assert ev.used_fallback is False
    assert ev.photo_jpeg.startswith(b"\xff\xd8")
    assert ev.ts.endswith("Z") or "+" in ev.ts  # UTC ISO-8601
    st.mark_synced(eid)
    assert st.pending() == []


def test_pending_respects_limit_and_order(tmp_path):
    st = EventStore(str(tmp_path / "t.db"))
    ids = [st.record(f"ABC123{i}", False, 0.5, False, b"j") for i in range(5)]
    got = st.pending(limit=3)
    assert [e.id for e in got] == ids[:3]
