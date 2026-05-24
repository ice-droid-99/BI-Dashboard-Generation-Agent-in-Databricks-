# Formatting and Units

Formatting can create a business error even when the formula is correct.

Rules:

1. Never choose compact currency formatting by default.
2. If the user expects abbreviated units such as `$M`, generate or verify them deliberately.
3. If the user expects full currency values, avoid abbreviations.
4. Keep rate metrics as percentages, not raw decimals, when rendering final display tables.

Check these separately:

- formula correctness
- rounding
- unit abbreviation
- page-specific or widget-specific presentation
