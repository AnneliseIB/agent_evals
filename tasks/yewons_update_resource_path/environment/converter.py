import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def convert(amount, currency):
    config = json.loads((ROOT / "config.json").read_text())
    rates = json.loads((ROOT / config["rates_file"]).read_text())
    return amount * rates["rates"][currency]
