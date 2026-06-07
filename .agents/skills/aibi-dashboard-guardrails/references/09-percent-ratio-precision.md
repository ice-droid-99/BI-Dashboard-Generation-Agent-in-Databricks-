Use this rule for dashboard percentages, rates, and ratios unless the user explicitly requests different precision.

Required behavior:
- Round to 2 decimal places in dataset SQL or in a dedicated KPI dataset.
- Do not depend on widget formatting alone to suppress extra decimals.
- Do not put `ROUND(...)` inside Lakeview widget field expressions for counters unless already validated in that exact pattern. Prefer dataset-level rounding.

Preferred pattern:

```sql
SELECT ROUND(numerator / NULLIF(denominator, 0), 4) AS metric_ratio
```

Then render with percent formatting at 2 decimals:

```json
"format": {
  "type": "number-percent",
  "decimalPlaces": { "type": "fixed", "places": 2 }
}
```

Why `4` in SQL for a percent metric stored as a ratio:
- Dashboard percent format multiplies the ratio by 100 for display.
- Rounding the ratio to 4 decimal places yields 2 decimal places in the displayed percent.
- Example: `0.0370094286` becomes `0.0370`, which renders as `3.70%`.

If the source value is already a percent on a 0-100 scale instead of a ratio on a 0-1 scale:
- Normalize the metric first or use number formatting instead of percent formatting.
