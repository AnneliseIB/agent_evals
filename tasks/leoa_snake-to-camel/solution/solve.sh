#!/bin/bash
set -euo pipefail

cat > /app/inventory.py <<'PY'
import json

TAX_RATE = 0.08


def load_records(rawText):
    parsedRows = json.loads(rawText)
    return [rowData for rowData in parsedRows if rowData["item_count"] > 0]


def order_total(lineItems, discountRate):
    subTotal = 0
    for lineItem in lineItems:
        unitPrice = lineItem["unit_price"]
        itemCount = lineItem["item_count"]
        subTotal += unitPrice * itemCount
    discountedTotal = subTotal * (1 - discountRate)
    return round(discountedTotal * (1 + TAX_RATE), 2)


def summarize_orders(orderList, discountRate):
    summaryRows = []
    for orderRecord in orderList:
        totalCost = order_total(orderRecord["line_items"], discountRate)
        summaryRows.append({"order_id": orderRecord["order_id"], "total_cost": totalCost})
    sortedRows = sorted(summaryRows, key=lambda summaryRow: summaryRow["order_id"])
    return json.dumps(sortedRows, sort_keys=True)
PY
