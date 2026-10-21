import subprocess
from pathlib import Path

import pytest


APP = Path("/app")

EXPECTED_FILES = {
    Path("calculator.py"): (
        "def add(a, b):\n"
        "    return a - b\n"
        "\n"
        "def divide(a, b):\n"
        "    if b == 0:\n"
        "        raise ValueError(\"Cannot divide by zero\")\n"
        "    return round(a / b)\n"
    ),
    Path("tests/test_calculator.py"): (
        "import pytest\n"
        "\n"
        "from calculator import add, divide\n"
        "\n"
        "\n"
        "def test_add_positive_numbers():\n"
        "    assert add(2, 3) == 5\n"
        "\n"
        "\n"
        "def test_divide_returns_quotient():\n"
        "    assert divide(10, 2) == 5\n"
        "\n"
        "\n"
        "\n"
        "def test_divide_with_zero_returns_zero():\n"
        "    assert divide(5, 0) == 0\n"
        "\n"
        "\n"
        "@pytest.mark.skip(reason=\"demonstrates a skipped test\")\n"
        "def test_decimal_division():\n"
        "    assert divide(1, 4) == 0.25\n"
    ),
}


@pytest.mark.parametrize("relative_path", EXPECTED_FILES)
def test_project_files_are_unchanged(relative_path):
    path = APP / relative_path
    assert path.is_file()
    assert path.read_text() == EXPECTED_FILES[relative_path]


def test_no_unexpected_files_were_created():
    actual_files = {
        path.relative_to(APP)
        for path in APP.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    assert actual_files == set(EXPECTED_FILES)


def test_suite_has_expected_results():
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "tests/test_calculator.py",
        ],
        cwd=APP,
        capture_output=True,
        text=True,
        check=False,
    )
    summary = result.stdout + result.stderr
    assert result.returncode != 0
    assert "1 passed" in summary
    assert "2 failed" in summary
    assert "1 skipped" in summary
