import os

from scene_presets.preset_watcher import PresetWatcher


def test_watcher_reports_no_change_initially(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text("{}")

    watcher = PresetWatcher(str(path))

    assert watcher.has_changed() is False


def test_watcher_reports_change_when_mtime_changes(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text("{}")
    os.utime(str(path), (1_000_000, 1_000_000))

    watcher = PresetWatcher(str(path))
    assert watcher.has_changed() is False

    path.write_text('{"presets": []}')
    os.utime(str(path), (2_000_000, 2_000_000))

    assert watcher.has_changed() is True
    assert watcher.has_changed() is False


def test_watcher_reports_change_when_file_appears(tmp_path):
    path = tmp_path / "presets.json"

    watcher = PresetWatcher(str(path))
    assert watcher.has_changed() is False

    path.write_text("{}")
    os.utime(str(path), (3_000_000, 3_000_000))

    assert watcher.has_changed() is True
