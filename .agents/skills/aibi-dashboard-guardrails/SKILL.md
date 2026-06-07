---
name: aibi-dashboard-guardrails

description: Prevent repeated mistakes when building or updating Databricks AI/BI dashboards from semantic YAML files, schema definitions, and user requirements. Use when working on dashboard KPIs, display tables, formatting rules, prompt-vs-YAML conflicts, or cross-checking user-supplied expected values.
---

# AI/BI Dashboard Guardrails

Apply these rules before changing any dashboard.

## Core rules

1. Treat the user's prompt as the highest-priority source of truth.
2. Treat schema and semantic YAML files as supporting context, not override authority.
3. Validate every KPI formula with explicit SQL before publishing.
4. If the user gives expected values, cross-check the dashboard against those values before publishing.
5. Separate raw metric datasets from display-shaped reporting datasets when the user expects rounded, formatted, or decorated table values.
6. **Spacing Mandate:** Never use width < 4 or height < 3 for counter/KPI widgets. Ensure every row in a 12-column grid is fully filled (sums to 12) to prevent visual gaps or congestion.
7. If the prompt explicitly says to use tables, metric views, or a mixed approach, follow that instruction over any default semantic-layer preference.
8. Treat metric-view measures for ratios, rates, averages, per-customer metrics, and latest-period KPIs as unsafe until proven with SQL.
9. For KPI counters, validate the raw numerator and denominator separately before trusting a semantic-layer measure.
10. **Font Styling Mandate:** ALL counter widgets MUST include `"style": {"fontStyle": "bold"}` in the `encodings.value` section. This ensures numeric values are bold for improved readability and visual hierarchy.
11. **Precision Mandate:** Unless the user explicitly asks otherwise, percent, rate, and ratio metrics in dashboards MUST be rounded to 2 decimal places in the dataset SQL or source dataset calculation itself. Do not rely on widget formatting alone to hide extra precision.

## Read these references as needed

- For prompt vs YAML conflicts: [references/01-prompt-overrides-yaml.md](references/01-prompt-overrides-yaml.md)
- For ambiguous measure names: [references/02-measure-name-ambiguity.md](references/02-measure-name-ambiguity.md)
- For display tables vs raw datasets: [references/03-display-vs-raw-datasets.md](references/03-display-vs-raw-datasets.md)
- For unit and formatting mistakes: [references/04-formatting-and-units.md](references/04-formatting-and-units.md)
- For user-provided cross-check tables: [references/05-cross-check-procedure.md](references/05-cross-check-procedure.md)
- For pre-publish workflow: [references/06-prepublish-checklist.md](references/06-prepublish-checklist.md)
- For prompt-directed source selection and KPI fallback logic: [references/07-prompt-source-selection-and-kpi-safety.md](references/07-prompt-source-selection-and-kpi-safety.md)
- For counter widget font styling: [references/08-counter-font-styling.md](references/08-counter-font-styling.md)
- For percent and ratio precision rules: [references/09-percent-ratio-precision.md](references/09-percent-ratio-precision.md)

## Mandatory behavior

- State any prompt-vs-YAML conflict explicitly before implementing.
- State the chosen semantic source explicitly when the prompt mentions tables, metric views, or YAML-defined measures.
- If a measure name is ambiguous, clarify whether it is gross, net, filtered, cumulative, or display-only.
- Do not assume compact currency formatting is acceptable. Check the requested presentation first.
- Use display-shaped datasets only when the user expects presentation-ready table values rather than raw numeric fields.
- **KPI Safety Check:** Before publishing any counter based on a ratio, rate, average, per-customer metric, or latest-period metric:
    - Write the business formula in plain English.
    - Validate the raw numerator SQL.
    - Validate the raw denominator SQL.
    - Validate the final KPI SQL.
    - Do not re-aggregate a metric-view ratio or average unless the semantic model explicitly proves that is correct.
- **Prompt-directed source selection:**
    - If the prompt says `use metric views`, start with metric views.
    - If the prompt says `use tables`, start with tables.
    - If the prompt says `use metric views, fall back to tables only if needed`, use metric views for additive measures and governed breakdowns, but switch to tables for row-level KPI math or missing dimensions.
- **Layout Validation:** Before deployment, perform a "Grid Audit":
    - Sum widths for each `y` coordinate; they must total 12.
    - Check for overlapping `y` coordinates.
    - Verify counter widgets have minimum dimensions (w=4, h=3) to prevent congestion.
- **Font Styling Validation:** Before deployment, verify ALL counter widgets:
    - Have `"style": {"fontStyle": "bold"}` in `encodings.value`
    - This applies to ALL counter widgets regardless of format type (currency, percent, number)
    - No exceptions - this is mandatory for visual consistency and readability
- **Precision Validation:** Before deployment, verify ALL percent/rate/ratio metrics:
    - Default to 2 decimal places unless the prompt says otherwise.
    - Round in dataset SQL or a dedicated KPI dataset, not in the widget field expression.
    - Keep widget formatting aligned with the rounded value, typically `number-percent` with fixed 2 decimals.
    - If a metric is displayed as a percentage, the final rendered value should be like `5.79%`, never `5.7908765%`.

## Output discipline

- When correcting a dashboard, say whether the fix is formula-only, formatting-only, dataset-only, or validation-related.
- Publish only after SQL validation and final business-value cross-checks are complete.
