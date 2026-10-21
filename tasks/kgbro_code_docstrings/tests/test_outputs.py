"""Pytest checks for the river simulation docstring task."""

import ast
import re
from pathlib import Path

import pytest

MODULE_PATH = Path("/app/river_sim.py")
EXPECTED_DEFINITIONS = (
    "River",
    "River.__init__",
    "River.one_day",
    "main",
)

# The original task source is kept here so the verifier can ensure that adding
# docstrings is the only change made to river_sim.py.
ORIGINAL_SOURCE = """\
class River:
    fish: int
    bears: int

    def __init__(self, fish: int, bears: int):
        self.fish = fish
        self.bears = bears

    def one_day(self):
        self.fish += (self.fish // 2) * 3
        self.fish -= self.bears
        self.bears += self.bears // 2

        
def main():
    river: River = River(10, 10)
    river.one_day()
    print(f"Fish: {river.fish}, Bears: {river.bears}")
"""


@pytest.fixture(scope="module")
def tree():
    return ast.parse(MODULE_PATH.read_text())


def _definitions(tree):
    """Return class and function definitions keyed by qualified name."""
    definitions = {}

    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                name = f"{prefix}{child.name}"
                definitions[name] = child
                visit(child, f"{name}.")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = f"{prefix}{child.name}"
                definitions[name] = child
                visit(child, f"{name}.")

    visit(tree)
    return definitions


def _without_docstrings(node):
    """Copy an AST while removing docstrings from modules and definitions."""
    node = ast.fix_missing_locations(ast.parse(ast.unparse(node)))

    class DocstringStripper(ast.NodeTransformer):
        def _strip(self, node):
            self.generic_visit(node)
            if (
                isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                node.body.pop(0)
            return node

        visit_Module = _strip
        visit_ClassDef = _strip
        visit_FunctionDef = _strip
        visit_AsyncFunctionDef = _strip

    return DocstringStripper().visit(node)


def test_module_has_no_module_docstring(tree):
    assert ast.get_docstring(tree) is None, "the task forbids a module docstring"


def test_expected_class_methods_and_function_are_present(tree):
    definitions = _definitions(tree)
    assert set(definitions) == set(EXPECTED_DEFINITIONS)


@pytest.mark.parametrize("name", EXPECTED_DEFINITIONS)
def test_each_expected_definition_has_a_one_sentence_docstring(tree, name):
    docstring = ast.get_docstring(_definitions(tree)[name])
    assert docstring, f"{name} has no docstring"
    assert "\n" not in docstring, f"{name} docstring must be one sentence"
    sentences = re.findall(r"[^.!?]+[.!?](?=\s|$)", docstring.strip())
    assert len(sentences) == 1, f"{name} docstring must be one sentence: {docstring!r}"


def test_names_signatures_and_code_are_unchanged(tree):
    original_tree = ast.parse(ORIGINAL_SOURCE)
    assert ast.dump(_without_docstrings(tree)) == ast.dump(_without_docstrings(original_tree)), (
        "river_sim.py must only gain docstrings; keep names, signatures, and code unchanged"
    )
