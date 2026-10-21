# Convert variable names to camelCase

Rename every function parameter and local variable in `/app/inventory.py` from
snake_case to camelCase (for example, `discount_rate` becomes `discountRate`).
This includes loop variables, comprehension variables, and lambda parameters,
and every place each name is used.

Keep these unchanged:

- function names (`load_records`, `order_total`, `summarize_orders`)
- the `TAX_RATE` constant
- dictionary keys and other string literals (the record fields such as
  `"unit_price"` and the JSON output fields such as `"total_cost"`)
- keyword-argument names passed to library functions
- the module's behavior and output
