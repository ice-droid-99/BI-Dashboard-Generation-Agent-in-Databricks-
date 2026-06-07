---
name: databricks-aibi-dashboards
description: "Create Databricks AI/BI dashboards. Use when creating, updating, or deploying Lakeview dashboards. CRITICAL: You MUST test ALL SQL queries via execute_sql BEFORE deploying. Follow guidelines strictly."
---

# AI/BI Dashboard Skill

Create Databricks AI/BI dashboards (formerly Lakeview dashboards). **Follow these guidelines strictly.**

## CRITICAL: MANDATORY VALIDATION WORKFLOW

**You MUST follow this workflow exactly. Skipping validation causes broken dashboards.**

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Get table schemas via get_table_stats_and_schema(catalog, schema)  │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 2: Write SQL queries for each dataset                        │
│          - Choose source by prompt: tables vs metric views vs mix  │
│          - Document KPI numerator/denominator before coding        │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 3: TEST EVERY QUERY via execute_sql() ← DO NOT SKIP!         │
│          - If query fails, FIX IT before proceeding                │
│          - Verify column names match what widgets will reference   │
│          - Verify data types are correct (dates, numbers, strings) │
│          - If user provided expected values, cross-check results   │
│          - For counters, validate numerator, denominator, and      │
│            final formula separately                                │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 4: Build dashboard JSON using ONLY verified queries          │
├─────────────────────────────────────────────────────────────────────┤
│  STEP 5: Deploy via manage_dashboard(action="create_or_update")    │
└─────────────────────────────────────────────────────────────────────┘
```

**WARNING: If you deploy without testing queries, widgets WILL show "Invalid widget definition" errors!**

### Business Validation Rules

When building dashboards, also apply these business validation rules:

1. **Prompt overrides YAML**: If user defines a KPI formula or display rule in their prompt, use that definition even if a semantic YAML file says something different. See [aibi-dashboard-guardrails](../aibi-dashboard-guardrails/SKILL.md).

2. **Clarify ambiguous metrics**: If a measure name is generic (e.g., "revenue"), clarify whether it means gross vs net, booked vs realized, current-period vs lifetime, etc.

3. **Cross-check expected values**: If user provides expected values or a sample table, validate your SQL results match those values exactly (including formatting, rounding, units) before deploying.

4. **Formatting validation**: Don't assume compact currency formatting is acceptable. Check user requirements for full vs abbreviated display.

5. **Display vs raw datasets**: Use raw datasets for aggregation/filtering, display-shaped datasets only when user expects presentation-ready formatted strings.

6. **Prompt-directed source selection**: If the prompt explicitly says to use tables, metric views, YAML-defined measures, or a mix, follow that instruction exactly. Do not override it with a default preference.

7. **KPI re-aggregation safety**: Treat metric-view measures for ratios, rates, averages, per-customer metrics, penetration metrics, and latest-period KPIs as unsafe until proven with SQL.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_table_stats_and_schema` | **STEP 1**: Get table schemas for designing queries |
| `execute_sql` | **STEP 3**: Test SQL queries - MANDATORY before deployment! |
| `manage_warehouse` (action="get_best") | Get available warehouse ID |
| `manage_dashboard` | **STEP 5**: Dashboard lifecycle management (see actions below) |

### manage_dashboard Actions

| Action | Description | Required Params |
|--------|-------------|-----------------|
| `create_or_update` | Deploy dashboard JSON (only after validation!) | display_name, parent_path, serialized_dashboard, warehouse_id |
| `get` | Get dashboard details by ID | dashboard_id |
| `list` | List all dashboards | (none) |
| `delete` | Move dashboard to trash | dashboard_id |
| `publish` | Publish a dashboard | dashboard_id, warehouse_id |
| `unpublish` | Unpublish a dashboard | dashboard_id |

**Example usage:**
```python
# Create/update dashboard
manage_dashboard(
    action="create_or_update",
    display_name="Sales Dashboard",
    parent_path="/Workspace/Users/me/dashboards",
    serialized_dashboard=dashboard_json,
    warehouse_id="abc123",
    publish=True  # auto-publish after create
)

# Get dashboard details
manage_dashboard(action="get", dashboard_id="dashboard_123")

# List all dashboards
manage_dashboard(action="list")
```

## Reference Files

| What are you building? | Reference |
|------------------------|-----------|
| Any widget (text, counter, table, chart) | [1-widget-specifications.md](1-widget-specifications.md) |
| Advanced widgets (area, scatter, combo, map) | [2-advanced-widget-specifications.md](2-advanced-widget-specifications.md) |
| Dashboard with filters (global or page-level) | [3-filters.md](3-filters.md) |
| Need a complete working template to adapt | [4-examples.md](4-examples.md) |
| Debugging a broken dashboard | [5-troubleshooting.md](5-troubleshooting.md) |
| Optimizing dashboard performance | [6-performance-optimization.md](6-performance-optimization.md) |
| SQL patterns for analytics (cohorts, funnels, RFM) | [7-data-modeling-patterns.md](7-data-modeling-patterns.md) |
| Formatting numbers, dates, and styling | [8-advanced-formatting.md](8-advanced-formatting.md) |
| Dashboard design and UX best practices | [9-dashboard-design-principles.md](9-dashboard-design-principles.md) |
| Integration with Unity Catalog, DLT, MLflow, etc. | [10-integration-patterns.md](10-integration-patterns.md) |

---

## Implementation Guidelines

### 1) DATASET ARCHITECTURE

- **One dataset per domain** (e.g., orders, customers, products)
- **Exactly ONE valid SQL query per dataset** (no multiple queries separated by `;`)
- Always use **fully-qualified table names**: `catalog.schema.table_name`
- SELECT must include all dimensions needed by widgets and all derived columns via `AS` aliases
- Put ALL business logic (CASE/WHEN, COALESCE, ratios) into the dataset SELECT with explicit aliases
- **Contract rule**: Every widget `fieldName` must exactly match a dataset column or alias
- **Source rule**: If the prompt says `use metric views, fall back to tables only if needed`, start from metric views for additive measures and governed breakdowns, but use tables for KPIs that require exact row-level numerators/denominators or dimensions the metric view does not expose
- **Counter rule**: For KPI counters, prefer datasets whose grain makes the business formula auditable; do not rely on re-aggregated semantic ratios or averages unless you validated that behavior explicitly

### 2) WIDGET FIELD EXPRESSIONS

> **CRITICAL: Field Name Matching Rule**
> The `name` in `query.fields` MUST exactly match the `fieldName` in `encodings`.
> If they don't match, the widget shows "no selected fields to visualize" error!

**Correct pattern for aggregations:**
```json
// In query.fields:
{"name": "sum(spend)", "expression": "SUM(`spend`)"}

// In encodings (must match!):
{"fieldName": "sum(spend)", "displayName": "Total Spend"}
```

**WRONG - names don't match:**
```json
// In query.fields:
{"name": "spend", "expression": "SUM(`spend`)"}  // name is "spend"

// In encodings:
{"fieldName": "sum(spend)", ...}  // ERROR: "sum(spend)" ≠ "spend"
```

Allowed expressions in widget queries (you CANNOT use CAST or other SQL in expressions):

**For numbers:**
```json
{"name": "sum(revenue)", "expression": "SUM(`revenue`)"}
{"name": "avg(price)", "expression": "AVG(`price`)"}
{"name": "count(orders)", "expression": "COUNT(`order_id`)"}
{"name": "countdistinct(customers)", "expression": "COUNT(DISTINCT `customer_id`)"}
{"name": "min(date)", "expression": "MIN(`order_date`)"}
{"name": "max(date)", "expression": "MAX(`order_date`)"}
```

**For dates** (use daily for timeseries, weekly/monthly for grouped comparisons):
```json
{"name": "daily(date)", "expression": "DATE_TRUNC(\"DAY\", `date`)"}
{"name": "weekly(date)", "expression": "DATE_TRUNC(\"WEEK\", `date`)"}
{"name": "monthly(date)", "expression": "DATE_TRUNC(\"MONTH\", `date`)"}
```

**Simple field reference** (for pre-aggregated data):
```json
{"name": "category", "expression": "`category`"}
```

If you need conditional logic or multi-field formulas, compute a derived column in the dataset SQL first.

### 3) SPARK SQL PATTERNS

- Date math: `date_sub(current_date(), N)` for days, `add_months(current_date(), -N)` for months
- Date truncation: `DATE_TRUNC('DAY'|'WEEK'|'MONTH'|'QUARTER'|'YEAR', column)`
- **AVOID** `INTERVAL` syntax - use functions instead

### 4) LAYOUT (12-Column Grid, NO GAPS)

**Every page must include `"layoutVersion": "GRID_V1"`** alongside `pageType`.

```json
{
  "name": "overview",
  "displayName": "Overview",
  "pageType": "PAGE_TYPE_CANVAS",
  "layoutVersion": "GRID_V1",
  "layout": [...]
}
```

Each widget has a position: `{"x": 0, "y": 0, "width": 4, "height": 4}`

**CRITICAL**: Each row must fill width=12 exactly. No gaps allowed.

**Recommended widget sizes:**

| Widget Type | Width | Height | Notes |
|-------------|-------|--------|-------|
| Text header | 12 | 1 | Full width; use SEPARATE widgets for title and subtitle |
| Counter/KPI | 4 | **3-4** | **NEVER height=2** - too cramped! |
| Line/Bar chart | 6 | **5-6** | Pair side-by-side to fill row |
| Pie chart | 6 | **5-6** | Needs space for legend |
| Full-width chart | 12 | 5-7 | For detailed time series |
| Table | 12 | 5-8 | Full width for readability |

**Standard dashboard structure:**
```text
y=0:  Title (w=12, h=1) - Dashboard title (use separate widget!)
y=1:  Subtitle (w=12, h=1) - Description (use separate widget!)
y=2:  KPIs (w=4 each, h=3) - 3 key metrics side-by-side
y=5:  Section header (w=12, h=1) - "Trends" or similar
y=6:  Charts (w=6 each, h=5) - Two charts side-by-side
y=11: Section header (w=12, h=1) - "Details"
y=12: Table (w=12, h=6) - Detailed data
```

### 5) CARDINALITY & READABILITY (CRITICAL)

**Dashboard readability depends on limiting distinct values:**

| Dimension Type | Max Values | Examples |
|----------------|------------|----------|
| Chart color/groups | **3-8** | 4 regions, 5 product lines, 3 tiers |
| Filters | 4-10 | 8 countries, 5 channels |
| High cardinality | **Table only** | customer_id, order_id, SKU |

**Before creating any chart with color/grouping:**
1. Check column cardinality (use `get_table_stats_and_schema` to see distinct values)
2. If >10 distinct values, aggregate to higher level OR use TOP-N + "Other" bucket
3. For high-cardinality dimensions, use a table widget instead of a chart

### 6) QUALITY CHECKLIST

Before deploying, verify:
1. All widget names use only alphanumeric + hyphens + underscores
2. **Every page has `"layoutVersion": "GRID_V1"`**
3. All rows sum to width=12 with no gaps
4. KPIs use height 3-4, charts use height 5-6
5. Chart dimensions have ≤8 distinct values
6. All widget fieldNames match dataset columns exactly
7. **Field `name` in query.fields matches `fieldName` in encodings exactly** (e.g., both `"sum(spend)"`)
8. Counter datasets: use `disaggregated: true` for 1-row datasets, `disaggregated: false` with aggregation for multi-row
9. Percent values are 0-1 (not 0-100)
10. SQL uses Spark syntax (date_sub, not INTERVAL)
11. **All SQL queries tested via `execute_sql` and return expected data**
12. KPI numerator and denominator were validated separately when applicable
13. Prompt-directed source choice was honored explicitly: tables, metric views, YAML measures, or mixed fallback

---

## Related Skills

- **[aibi-dashboard-guardrails](../aibi-dashboard-guardrails/SKILL.md)** - for business validation, formula verification, cross-checking against user expectations, and resolving prompt vs YAML conflicts
- **[databricks-unity-catalog](../databricks-unity-catalog/SKILL.md)** - for querying the underlying data and system tables
- **[databricks-spark-declarative-pipelines](../databricks-spark-declarative-pipelines/SKILL.md)** - for building the data pipelines that feed dashboards
- **[databricks-jobs](../databricks-jobs/SKILL.md)** - for scheduling dashboard data refreshes
