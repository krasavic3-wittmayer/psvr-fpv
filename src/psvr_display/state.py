"""Local record of the last mode this tool set on the PU.

The PU's protocol has no confirmed way to passively query its current
mode without sending a command that could itself change state (see
status.py). Since this tool is the only thing expected to change the
PU's mode, tracking the last mode we set locally is simpler and just as
accurate in practice, and lets `toggle` work without guessing at
undocumented protocol behaviour.
"""

from __future__ import annotations

import os
from pathlib import Path

_VALID_MODES = ("cinematic", "vr")


def _state_dir() -> Path:
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg_state_home) if xdg_state_home else Path.home() / ".local" / "state"
    return base / "psvr-display"


def _state_file() -> Path:
    return _state_dir() / "last_mode"


def read_last_mode(default: str = "cinematic") -> str:
    try:
        value = _state_file().read_text().strip()
    except FileNotFoundError:
        return default
    return value if value in _VALID_MODES else default


def write_last_mode(mode: str) -> None:
    if mode not in _VALID_MODES:
        raise ValueError(f"unknown mode: {mode}")
    state_dir = _state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    _state_file().write_text(mode + "\n")
