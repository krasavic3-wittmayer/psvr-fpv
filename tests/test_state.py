from psvr_display import state


def test_read_last_mode_defaults_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    assert state.read_last_mode() == "cinematic"
    assert state.read_last_mode(default="vr") == "vr"


def test_write_then_read_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    state.write_last_mode("vr")
    assert state.read_last_mode() == "vr"
    state.write_last_mode("cinematic")
    assert state.read_last_mode() == "cinematic"


def test_write_rejects_unknown_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    try:
        state.write_last_mode("bogus")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_corrupt_state_file_falls_back_to_default(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    state_dir = tmp_path / "psvr-display"
    state_dir.mkdir(parents=True)
    (state_dir / "last_mode").write_text("garbage\n")
    assert state.read_last_mode() == "cinematic"
