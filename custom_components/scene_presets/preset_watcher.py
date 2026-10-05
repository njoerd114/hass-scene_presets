from __future__ import annotations
import os

from .file_utils import CUSTOM_PRESETS_PATH


def _mtime(path: str) -> float | None:
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


class PresetWatcher:
    def __init__(self, path: str = CUSTOM_PRESETS_PATH) -> None:
        self._path = path
        self._last_mtime = _mtime(path)

    def has_changed(self) -> bool:
        current = _mtime(self._path)
        if current != self._last_mtime:
            self._last_mtime = current
            return True
        return False
