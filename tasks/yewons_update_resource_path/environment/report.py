import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_rates():
    return json.loads((ROOT / "data/rates.json").read_text())
