from __future__ import annotations

from pathlib import Path

import pytest

from app.actions import ActionError, _run_script, read_whitelist


def test_read_whitelist_sorts_names(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "whitelist.json").write_text('[{"name":"misty"},{"name":"Ash"}]', encoding="utf-8")

    assert read_whitelist(tmp_path) == ["Ash", "misty"]


def test_read_whitelist_invalid_json_raises(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "whitelist.json").write_text('{invalid', encoding="utf-8")

    with pytest.raises(ActionError):
        read_whitelist(tmp_path)


class _FakeResult:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_run_script_surfaces_non_zero_exit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "app.actions.subprocess.run",
        lambda *args, **kwargs: _FakeResult(returncode=3, stderr="boom"),
    )
    with pytest.raises(ActionError, match="boom"):
        _run_script(tmp_path, "fail.sh", timeout=5)
