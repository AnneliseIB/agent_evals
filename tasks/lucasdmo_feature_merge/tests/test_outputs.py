"""Verify the required Git feature-branch workflow in the task repository."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path("/app")


def git(*args: str) -> str:
    """Run Git in the task repository and return stripped standard output."""
    return subprocess.run(
        ["git", *args],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_repository_is_on_main_with_feature_branch_present() -> None:
    assert git("branch", "--show-current") == "main"
    assert git("rev-parse", "--verify", "feature/subtract")


def feature_calculator_namespace() -> dict[str, object]:
    """Load calculator.py exactly as it exists at the feature branch tip."""
    source = git("show", "feature/subtract:calculator.py")
    namespace: dict[str, object] = {}
    exec(compile(source, "feature/subtract:calculator.py", "exec"), namespace)
    return namespace


def test_feature_branch_defines_subtract_with_the_required_signature() -> None:
    feature_source = git("show", "feature/subtract:calculator.py")
    module = ast.parse(feature_source)
    subtract_functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "subtract"
    ]

    assert len(subtract_functions) == 1
    assert [argument.arg for argument in subtract_functions[0].args.args] == ["a", "b"]


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [(5, 3, 2), (-2, 3, -5), (1.5, 0.5, 1.0), (0, 0, 0)],
)
def test_feature_branch_subtract_behaves_correctly(a: float, b: float, expected: float) -> None:
    subtract = feature_calculator_namespace()["subtract"]

    assert callable(subtract)
    assert subtract(a, b) == expected


def test_feature_branch_is_merged_by_a_merge_commit() -> None:
    main_head = git("rev-parse", "main")
    feature_head = git("rev-parse", "feature/subtract")
    parents = git("show", "-s", "--format=%P", main_head).split()

    assert len(parents) == 2
    assert feature_head in parents
    main_before_merge = next(parent for parent in parents if parent != feature_head)
    main_before_source = git("show", f"{main_before_merge}:calculator.py")
    main_before_module = ast.parse(main_before_source)
    assert not any(
        isinstance(node, ast.FunctionDef) and node.name == "subtract"
        for node in main_before_module.body
    )
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", feature_head, "main"],
        cwd=REPOSITORY,
        check=True,
    )
