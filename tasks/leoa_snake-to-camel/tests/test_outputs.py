"""Pytest checks for the camelCase rename inside the task sandbox."""

import ast
import json
import re
from pathlib import Path

import pytest
from inventory import TAX_RATE, load_records, order_total, summarize_orders

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")

RENAMES = [
    ("raw_text", "rawText"),
    ("parsed_rows", "parsedRows"),
    ("row_data", "rowData"),
    ("line_items", "lineItems"),
    ("discount_rate", "discountRate"),
    ("sub_total", "subTotal"),
    ("line_item", "lineItem"),
    ("unit_price", "unitPrice"),
    ("item_count", "itemCount"),
    ("discounted_total", "discountedTotal"),
    ("order_list", "orderList"),
    ("summary_rows", "summaryRows"),
    ("order_record", "orderRecord"),
    ("total_cost", "totalCost"),
    ("sorted_rows", "sortedRows"),
    ("summary_row", "summaryRow"),
]


@pytest.fixture(scope="module")
def tree():
    return ast.parse(Path("/app/inventory.py").read_text())


@pytest.fixture(scope="module")
def bindings(tree):
    params = {node.arg for node in ast.walk(tree) if isinstance(node, ast.arg)}
    assigned = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    return params | assigned


@pytest.fixture(scope="module")
def references(tree):
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


@pytest.mark.parametrize(("old", "new"), RENAMES)
def test_binding_renamed(bindings, old, new):
    assert old not in bindings
    assert new in bindings


@pytest.mark.parametrize(("old", "new"), RENAMES)
def test_uses_renamed(references, old, new):
    assert old not in references
    assert new in references


def test_no_snake_case_variables_remain(bindings):
    assert [name for name in bindings if SNAKE_CASE.match(name)] == []


def test_string_literals_unchanged(tree):
    strings = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert strings == {"item_count", "unit_price", "line_items", "order_id", "total_cost"}


def test_keyword_arguments_unchanged(tree):
    keywords = {node.arg for node in ast.walk(tree) if isinstance(node, ast.keyword)}
    assert keywords == {"key", "sort_keys"}


def test_function_names_unchanged(tree):
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    assert functions == {"load_records", "order_total", "summarize_orders"}


def test_constant_unchanged():
    assert TAX_RATE == 0.08


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            '[{"unit_price": 2, "item_count": 1}, {"unit_price": 3, "item_count": 0}]',
            [{"unit_price": 2, "item_count": 1}],
        ),
        ("[]", []),
    ],
)
def test_load_records_unchanged(raw, expected):
    assert load_records(raw) == expected


@pytest.mark.parametrize(
    ("items", "discount", "expected"),
    [
        ([{"unit_price": 10, "item_count": 2}], 0, 21.6),
        (
            [
                {"unit_price": 5.5, "item_count": 2},
                {"unit_price": 1, "item_count": 3},
            ],
            0.5,
            7.56,
        ),
        ([], 0.2, 0),
    ],
)
def test_order_total_unchanged(items, discount, expected):
    assert order_total(items, discount) == expected


def test_summarize_orders_unchanged():
    orders = [
        {"order_id": "b2", "line_items": [{"unit_price": 10, "item_count": 2}]},
        {"order_id": "a1", "line_items": []},
    ]
    result = summarize_orders(orders, 0)
    assert (
        result == '[{"order_id": "a1", "total_cost": 0.0}, {"order_id": "b2", "total_cost": 21.6}]'
    )
    assert json.loads(result)[1] == {"order_id": "b2", "total_cost": 21.6}
