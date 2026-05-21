# Display vs Raw Datasets

Do not force presentation-specific reporting tables to rely only on widget formatting.

Use raw datasets when:

- charts need numeric aggregation
- filters should operate on numeric or date fields
- KPIs need precise aggregation

Use display-shaped datasets when:

- the user expects exact strings such as `$21.6M`
- the user expects rounded percentages like `250.8%`
- the user expects inline markers or labels in the final table
- the table should match a manually supplied cross-check exactly

Rule:

- Keep calculation-friendly datasets separate from presentation-ready datasets.
