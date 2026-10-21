# Repair stale resource paths

The rate asset is already at `/app/resources/rates.json`, but `/app/config.json`
and `/app/report.py` still reference `data/rates.json`. Update those references
so `converter.convert(amount, currency)` returns the amount multiplied by the
requested currency's rate and `report.load_rates()` returns the complete asset.

Both readers must work from any working directory. Keep their names and
signatures unchanged, and keep the converter reading its path from configuration.
Store the configured path as `resources/rates.json`, relative to `/app`.
Leave the asset unchanged and do not recreate the old path, including a symlink.
