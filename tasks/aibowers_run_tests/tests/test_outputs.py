import re
import subprocess
from pathlib import Path

APP = Path("/app")
REPORT = APP / "failing_tests.txt"
EXPECTED_FAILURES = {
    "tests/test_calculator.py::test_add_positive_numbers",
    "tests/test_calculator.py::test_divide_with_zero_returns_zero",
}


def reported_ids():
    assert REPORT.is_file(), "failing_tests.txt was not created in /app"
    text = REPORT.read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines() if line.strip()]


# --- Reporting checks ---


def test_report_contains_expected_failures():
    reported = reported_ids()
    reported_set = set(reported)
    missing = EXPECTED_FAILURES - reported_set
    extra = reported_set - EXPECTED_FAILURES
    assert not missing, f"Failing tests not reported: {sorted(missing)}"
    assert not extra, f"Reported tests that did not fail: {sorted(extra)}"


def test_report_matches_independent_test_run():
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--disable-warnings",
            "tests/test_calculator.py",
        ],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    summary = result.stdout + result.stderr
    actual_failures = {
        match.group(1) for match in re.finditer(r"^FAILED (.+?)(?: - .*)?$", summary, re.MULTILINE)
    }
    assert actual_failures == EXPECTED_FAILURES, summary
    assert "1 passed" in summary, summary
    assert "2 failed" in summary, summary
    assert "1 skipped" in summary, summary
    assert result.returncode != 0
