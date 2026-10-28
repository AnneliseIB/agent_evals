#!/bin/bash
set -euo pipefail

sed -i 's|data/rates.json|resources/rates.json|g' /app/config.json /app/report.py
