import os
from pathlib import Path

import pytest

APP = Path("/app")
ARCHIVE = APP / "archive"
TARGET = ARCHIVE / "calc_log.txt"


def test_target_file_is_deleted():
    assert not os.path.lexists(TARGET)


@pytest.mark.parametrize(
    ("path", "expected_type"),
    [
        (ARCHIVE, "directory"),
        (ARCHIVE / "calc_log_1.txt", "file"),
    ],
)
def test_unrelated_paths_are_preserved(path, expected_type):
    assert path.exists()
    if expected_type == "directory":
        assert path.is_dir()
        assert not path.is_symlink()
    else:
        assert path.is_file()
        assert not path.is_symlink()


def test_unrelated_file_content_is_preserved():
    assert (ARCHIVE / "calc_log_1.txt").read_text() == (
        "2026-10-21T01:05:00Z INFO calculation started\n"
        "2026-10-21T01:05:01Z INFO calculation completed result=84\n"
    )


def test_no_other_paths_under_app_are_created_or_removed():
    actual_paths = {path.relative_to(APP) for path in APP.rglob("*")}
    assert actual_paths == {
        Path("archive"),
        Path("archive/calc_log_1.txt"),
    }
