# Prompt Source Selection And KPI Safety

Use this reference when the prompt explicitly instructs which semantic source to use, or when KPI math may be distorted by re-aggregating metric-view outputs.

## Source selection precedence

1. User prompt
2. Explicit dashboard specification in the prompt
3. Semantic YAML / metric-view definitions
4. Default dashboard-building habits

If the prompt says:

- `use tables`: use tables first.
- `use metric views`: use metric views first.
- `use metric views, fall back to tables only if needed`: use metric views for safe additive measures and governed dimensions, but switch to tables when the metric view cannot produce the exact business formula.

## Metric views are usually safe for

- additive totals
- governed dimensional breakdowns
- time-series aggregations of additive measures

## Metric views are high-risk for

- success rates
- failure rates
- digital mix or adoption rates
- averages
- per-customer metrics
- penetration metrics
- latest-period KPIs
- weighted formulas

These often require raw numerator/denominator validation from tables even when a metric view exposes a similarly named measure.

## Required KPI validation pattern

For every KPI counter, document:

1. Business definition in plain English
2. Numerator SQL
3. Denominator SQL
4. Final KPI SQL
5. Why the chosen source is safe

If the metric view exposes a pre-aggregated ratio or average, do not re-aggregate that field unless the semantic definition proves it is valid at the requested dashboard grain.

## Fallback to tables when

- the metric view lacks a required dimension
- the metric view measure is already a ratio or average and would need re-aggregation
- the user has provided checked KPI values and the metric-view query does not match them
- the KPI needs exact record counts
- the KPI depends on latest snapshot logic not directly encoded in the metric view

## Output discipline

When mixing sources, state:

- which visuals use metric views
- which KPIs or tables use fact tables
- why the fallback was required
