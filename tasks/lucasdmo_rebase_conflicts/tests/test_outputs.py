"""Verify the calculator conflict was resolved through a completed rebase."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path("/app")
EXPECTED_FUNCTIONS = ("add", "subtract", "multiply", "power")


def git(*args: str) -> str:
    """Run Git in the task repository and return stripped standard output."""
    return subprocess.run(
        ["git", *args],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def branch_namespace(branch: str) -> dict[str, object]:
    """Load calculator.py exactly as it exists at a branch tip."""
    source = git("show", f"{branch}:calculator.py")
    namespace: dict[str, object] = {}
    exec(compile(source, f"{branch}:calculator.py", "exec"), namespace)
    return namespace


def test_rebase_is_complete_with_feature_power_checked_out() -> None:
    assert git("branch", "--show-current") == "feature/power"
    assert not git("status", "--porcelain")
    assert not (REPOSITORY / ".git" / "rebase-merge").exists()
    assert not (REPOSITORY / ".git" / "rebase-apply").exists()


def test_main_is_unchanged_and_contains_only_its_operation() -> None:
    main_source = git("show", "main:calculator.py")
    main_module = ast.parse(main_source)
    names = [node.name for node in main_module.body if isinstance(node, ast.FunctionDef)]

    assert names == ["add", "subtract", "multiply"]
    assert git("log", "-1", "--format=%s", "main") == "Add multiply operation"
    assert git("rev-list", "--count", "main") == "2"


def test_feature_branch_has_a_linear_rebased_commit_on_main() -> None:
    main_head = git("rev-parse", "main")
    feature_head = git("rev-parse", "feature/power")

    assert git("merge-base", "main", "feature/power") == main_head
    assert git("rev-list", "--count", "main..feature/power") == "1"
    assert git("show", "-s", "--format=%P", feature_head) == main_head
    assert git("log", "-1", "--format=%s", "feature/power") == "Add power operation"


def test_rebased_calculator_defines_each_operation_once() -> None:
    feature_source = git("show", "feature/power:calculator.py")
    assert "<<<<<<<" not in feature_source
    assert "=======" not in feature_source
    assert ">>>>>>>" not in feature_source

    module = ast.parse(feature_source)
    functions = [node for node in module.body if isinstance(node, ast.FunctionDef)]

    assert [function.name for function in functions] == list(EXPECTED_FUNCTIONS)
    for function in functions:
        assert [argument.arg for argument in function.args.args] == ["a", "b"]


@pytest.mark.parametrize(
    ("name", "a", "b", "expected"),
    [
        ("add", 2, 3, 5),
        ("subtract", 2, 3, -1),
        ("multiply", 2, 3, 6),
        ("power", 2, 3, 8),
        ("power", 5, 0, 1),
    ],
)
def test_rebased_calculator_operations_work(name: str, a: float, b: float, expected: float) -> None:
    operation = branch_namespace("feature/power")[name]

    assert callable(operation)
    assert operation(a, b) == expected
