"""Pytest checks for the module docstring task inside the task sandbox."""

import ast
import doctest
from pathlib import Path

import pytest

MODULE_PATH = Path("/app/textutils.py")
ORIGINAL_PATH = Path(__file__).with_name("original_textutils.py")


@pytest.fixture(scope="module")
def tree():
    return ast.parse(MODULE_PATH.read_text())


@pytest.fixture(scope="module")
def docstring(tree):
    text = ast.get_docstring(tree)
    assert text, "textutils.py has no module docstring as its first statement"
    return text


@pytest.fixture(scope="module")
def textutils():
    import textutils

    return textutils


def without_module_docstring(tree):
    body = tree.body
    if ast.get_docstring(tree) is not None:
        body = body[1:]
    return ast.Module(body=body, type_ignores=[])


def test_summary_line_describes_purpose(docstring):
    summary = docstring.splitlines()[0].strip()
    assert not summary.startswith(">>>"), "the first line must be a summary"
    assert len(summary.split()) >= 3, f"summary line is too short: {summary!r}"


def test_example_calls_slugify(docstring):
    examples = doctest.DocTestParser().get_examples(docstring)
    assert any("slugify(" in example.source for example in examples)


def test_module_doctests_pass(textutils):
    finder = doctest.DocTestFinder(recurse=False)
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    for test in finder.find(textutils, globs=vars(textutils).copy()):
        runner.run(test)
    results = runner.summarize(verbose=False)
    assert results.attempted > 0, "the module docstring has no doctest examples"
    assert results.failed == 0


def test_rest_of_module_is_unchanged(tree):
    original = ast.parse(ORIGINAL_PATH.read_text())
    assert ast.dump(without_module_docstring(tree)) == ast.dump(original)


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("Hello, World!",), "hello-world"),
        (("  Café au lait  ",), "cafe-au-lait"),
        (("already-a-slug",), "already-a-slug"),
        (("Two  Words", "_"), "two_words"),
        (("!!!",), ""),
    ],
)
def test_slugify_behavior(textutils, args, expected):
    assert textutils.slugify(*args) == expected


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (("short", 10), "short"),
        (("exactly ten", 11), "exactly ten"),
        (("The quick brown fox", 12), "The quick..."),
        (("abcdef", 5, "~"), "abcd~"),
    ],
)
def test_truncate_behavior(textutils, args, expected):
    assert textutils.truncate(*args) == expected


def test_truncate_rejects_limit_shorter_than_suffix(textutils):
    with pytest.raises(ValueError):
        textutils.truncate("text", 2)


@pytest.mark.parametrize(
    ("text", "expected"),
    [("", 0), ("one", 1), ("two words", 2), ("  spaced\tout\nwords  ", 3)],
)
def test_word_count_behavior(textutils, text, expected):
    assert textutils.word_count(text) == expected
