import json

TAX_RATE = 0.08


def load_records(raw_text):
    parsed_rows = json.loads(raw_text)
    return [row_data for row_data in parsed_rows if row_data["item_count"] > 0]


def order_total(line_items, discount_rate):
    sub_total = 0
    for line_item in line_items:
        unit_price = line_item["unit_price"]
        item_count = line_item["item_count"]
        sub_total += unit_price * item_count
    discounted_total = sub_total * (1 - discount_rate)
    return round(discounted_total * (1 + TAX_RATE), 2)


def summarize_orders(order_list, discount_rate):
    summary_rows = []
    for order_record in order_list:
        total_cost = order_total(order_record["line_items"], discount_rate)
        summary_rows.append({"order_id": order_record["order_id"], "total_cost": total_cost})
    sorted_rows = sorted(summary_rows, key=lambda summary_row: summary_row["order_id"])
    return json.dumps(sorted_rows, sort_keys=True)
