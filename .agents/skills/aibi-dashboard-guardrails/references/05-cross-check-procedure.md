# Cross-Check Procedure

If the user supplies expected values, treat them as a validation target.

Procedure:

1. Recompute the values in SQL.
2. Compare row by row or KPI by KPI.
3. Identify whether differences come from formula, rounding, label formatting, unit formatting, or row ordering.
4. Patch only the affected dataset or dashboard section.
5. Revalidate before publishing.


Do not publish after only checking that SQL runs.
Publish only after checking that the rendered business values match the user's cross-check.

