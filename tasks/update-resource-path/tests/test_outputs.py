"""Pytest checks for the relocated resource inside the task sandbox."""

import json
import os
from pathlib import Path

import pytest
from converter import convert
from report import load_rates

EXPECTED_RATES = {"base": "USD", "rates": {"EUR": 0.8, "GBP": 0.75, "JPY": 150.0}}


@pytest.fixture(params=["/app", "/tmp"])
def working_directory(request, monkeypatch):
    monkeypatch.chdir(request.param)


@pytest.mark.parametrize(
    ("amount", "currency", "expected"),
    [(10, "EUR", 8), (0, "EUR", 0), (-4, "GBP", -3), (2.5, "JPY", 375)],
)
def test_convert(working_directory, amount, currency, expected):
    assert convert(amount, currency) == pytest.approx(expected)


def test_report(working_directory):
    assert load_rates() == EXPECTED_RATES


def test_converter_uses_configuration(tmp_path):
    config_path = Path("/app/config.json")
    original = config_path.read_text()
    alternate = tmp_path / "rates.json"
    alternate.write_text(json.dumps({"rates": {"EUR": 2}}))
    try:
        config_path.write_text(json.dumps({"rates_file": os.path.relpath(alternate, "/app")}))
        assert convert(10, "EUR") == 20
    finally:
        config_path.write_text(original)


def test_resource_paths():
    config = json.loads(Path("/app/config.json").read_text())
    assert config["rates_file"] == "resources/rates.json"
    assert json.loads(Path("/app/resources/rates.json").read_text()) == EXPECTED_RATES
    old_path = Path("/app/data/rates.json")
    assert not old_path.exists()
    assert not old_path.is_symlink()
