# Advanced Formatting and Styling

Advanced formatting options for AI/BI dashboard widgets to improve readability and visual appeal.

---

## Number Formatting

### Currency Formatting

> **IMPORTANT**: Always check user requirements before choosing compact vs full formatting. 
> Don't default to compact currency - verify the expected presentation first.
> See [aibi-dashboard-guardrails](../aibi-dashboard-guardrails/SKILL.md) for business validation rules.

```json
"format": {
  "type": "number-currency",
  "currencyCode": "USD",
  "abbreviation": "compact",
  "decimalPlaces": {"type": "max", "places": 2}
}
```

**Supported currency codes:**
- `USD` - US Dollar ($)
- `EUR` - Euro (€)
- `GBP` - British Pound (£)
- `JPY` - Japanese Yen (¥)
- `CNY` - Chinese Yuan (¥)
- `INR` - Indian Rupee (₹)
- `AUD` - Australian Dollar (A$)
- `CAD` - Canadian Dollar (C$)

**Abbreviation options:**
- `"compact"` - Shows K, M, B (e.g., $1.2M) - **Use only when user explicitly requests abbreviated format**
- Omit for full numbers (e.g., $1,234,567.89) - **Default to this unless user specifies otherwise**

**Examples:**
```json
// $1.2M (compact with max 2 decimals)
{"type": "number-currency", "currencyCode": "USD", "abbreviation": "compact", "decimalPlaces": {"type": "max", "places": 2}}

// $1,234,567.89 (full with exactly 2 decimals)
{"type": "number-currency", "currencyCode": "USD", "decimalPlaces": {"type": "fixed", "places": 2}}

// €1.2M (Euro, compact)
{"type": "number-currency", "currencyCode": "EUR", "abbreviation": "compact", "decimalPlaces": {"type": "max", "places": 1}}
```

### Percentage Formatting

> **CRITICAL**: Data must be in 0-1 range (not 0-100). The formatter multiplies by 100 and adds %.

```json
"format": {
  "type": "number-percent",
  "decimalPlaces": {"type": "max", "places": 1}
}
```

**Examples:**
- Data: `0.4523` → Display: `45.2%` (with max 1 decimal)
- Data: `0.05` → Display: `5.0%` (with fixed 1 decimal)
- Data: `1.2345` → Display: `123.5%` (values >1 are valid)

**Common mistake:**
```sql
-- WRONG: Returns 45.23, displays as 4523%
SELECT (revenue / total_revenue) * 100 as pct FROM ...

-- CORRECT: Returns 0.4523, displays as 45.23%
SELECT revenue / total_revenue as pct FROM ...
```

### Number Formatting (Non-Currency)

```json
"format": {
  "type": "number",
  "abbreviation": "compact",
  "decimalPlaces": {"type": "max", "places": 0}
}
```

**Examples:**
```json
// 1.2K (compact, no decimals)
{"type": "number", "abbreviation": "compact", "decimalPlaces": {"type": "max", "places": 0}}

// 1,234 (full with commas, no decimals)
{"type": "number", "decimalPlaces": {"type": "fixed", "places": 0}}

// 1.23 (max 2 decimals)
{"type": "number", "decimalPlaces": {"type": "max", "places": 2}}
```

### Decimal Places Options

| Type | Behavior | Example (value: 1.2) |
|------|----------|----------------------|
| `{"type": "max", "places": 2}` | Shows up to 2 decimals, removes trailing zeros | `1.2` |
| `{"type": "fixed", "places": 2}` | Always shows exactly 2 decimals | `1.20` |
| `{"type": "max", "places": 0}` | No decimals, rounds | `1` |

---

## Date and Time Formatting

### Date Truncation in Queries

Use `DATE_TRUNC` for time-based grouping:

```json
// Daily granularity
{"name": "daily(date)", "expression": "DATE_TRUNC(\"DAY\", `date`)"}

// Weekly (starts Monday)
{"name": "weekly(date)", "expression": "DATE_TRUNC(\"WEEK\", `date`)"}

// Monthly
{"name": "monthly(date)", "expression": "DATE_TRUNC(\"MONTH\", `date`)"}

// Quarterly
{"name": "quarterly(date)", "expression": "DATE_TRUNC(\"QUARTER\", `date`)"}

// Yearly
{"name": "yearly(date)", "expression": "DATE_TRUNC(\"YEAR\", `date`)"}
```

### Date Display Formats

Dashboard automatically formats dates based on granularity:
- Daily: `Jan 15, 2024`
- Weekly: `Week of Jan 15, 2024`
- Monthly: `Jan 2024`
- Quarterly: `Q1 2024`
- Yearly: `2024`

### Custom Date Formatting in SQL

```sql
-- Format as YYYY-MM-DD
SELECT DATE_FORMAT(order_date, 'yyyy-MM-dd') as formatted_date

-- Format as Month Day, Year
SELECT DATE_FORMAT(order_date, 'MMMM d, yyyy') as formatted_date

-- Format as MM/DD/YYYY
SELECT DATE_FORMAT(order_date, 'MM/dd/yyyy') as formatted_date

-- Day of week
SELECT DATE_FORMAT(order_date, 'EEEE') as day_of_week
```

---

## Conditional Formatting in SQL

Since widgets don't support conditional formatting, apply logic in dataset SQL:

### Color-Coded Status

```sql
SELECT 
  order_id,
  status,
  CASE 
    WHEN status = 'completed' THEN '✓ Completed'
    WHEN status = 'pending' THEN '⏳ Pending'
    WHEN status = 'failed' THEN '✗ Failed'
    ELSE status
  END as status_display
FROM catalog.schema.orders
```

### Trend Indicators

```sql
WITH current_vs_prior AS (
  SELECT 
    metric_name,
    current_value,
    prior_value,
    (current_value - prior_value) / prior_value as change_pct
  FROM catalog.schema.metrics
)
SELECT 
  metric_name,
  current_value,
  prior_value,
  change_pct,
  CASE 
    WHEN change_pct > 0 THEN CONCAT('↑ ', ROUND(change_pct * 100, 1), '%')
    WHEN change_pct < 0 THEN CONCAT('↓ ', ROUND(ABS(change_pct) * 100, 1), '%')
    ELSE '→ 0%'
  END as trend_indicator
FROM current_vs_prior
```

### Threshold-Based Labels

```sql
SELECT 
  product_name,
  inventory_level,
  CASE 
    WHEN inventory_level < 10 THEN 'Critical'
    WHEN inventory_level < 50 THEN 'Low'
    WHEN inventory_level < 100 THEN 'Normal'
    ELSE 'High'
  END as inventory_status
FROM catalog.schema.inventory
```

---

## Text Widget Styling

### Markdown Support

Text widgets support markdown formatting:

```json
{
  "widget": {
    "name": "header",
    "multilineTextboxSpec": {
      "lines": [
        "# Dashboard Title",
        "",
        "**Bold text** and *italic text*",
        "",
        "- Bullet point 1",
        "- Bullet point 2",
        "",
        "[Link text](https://example.com)"
      ]
    }
  }
}
```

**Supported markdown:**
- Headers: `#`, `##`, `###`
- Bold: `**text**`
- Italic: `*text*`
- Lists: `- item` or `1. item`
- Links: `[text](url)`

**Line breaks:**
- Empty string `""` in array creates a blank line
- `\n\n` within a string creates a line break

### Header Hierarchy

```json
// Page title (largest)
{"lines": ["# Sales Dashboard"]}

// Section header (medium)
{"lines": ["## Revenue Trends"]}

// Subsection header (small)
{"lines": ["### By Region"]}

// Description text (normal)
{"lines": ["Track daily sales performance across all regions."]}
```

---

## Chart Styling

### Axis Titles and Labels

```json
"encodings": {
  "x": {
    "fieldName": "order_date",
    "displayName": "Order Date",
    "scale": {"type": "temporal"},
    "axis": {"title": "Date"}
  },
  "y": {
    "fieldName": "sum(revenue)",
    "displayName": "Revenue ($)",
    "scale": {"type": "quantitative"},
    "axis": {"title": "Total Revenue (USD)"},
    "format": {
      "type": "number-currency",
      "currencyCode": "USD",
      "abbreviation": "compact"
    }
  }
}
```

**Best practices:**
- `displayName`: Short label for legend/tooltip (e.g., "Revenue")
- `axis.title`: Descriptive axis label with units (e.g., "Total Revenue (USD)")

### Legend Configuration

```json
"encodings": {
  "color": {
    "fieldName": "region",
    "displayName": "Region",
    "scale": {"type": "categorical"}
  },
  "label": {"show": true}  // Show data labels on chart
}
```

### Chart Descriptions

```json
"frame": {
  "title": "Revenue Trend",
  "showTitle": true,
  "description": "Daily revenue over the past 90 days",
  "showDescription": true
}
```

---

## Table Styling

### Column Display Names

```json
"encodings": {
  "columns": [
    {"fieldName": "order_id", "displayName": "Order ID"},
    {"fieldName": "customer_name", "displayName": "Customer"},
    {"fieldName": "order_date", "displayName": "Date"},
    {"fieldName": "total_amount", "displayName": "Amount ($)"}
  ]
}
```

### Computed Display Columns

Create formatted columns in SQL for better table display:

```sql
SELECT 
  order_id,
  customer_name,
  DATE_FORMAT(order_date, 'MMM d, yyyy') as order_date_formatted,
  CONCAT('$', FORMAT_NUMBER(total_amount, 2)) as amount_display,
  CASE 
    WHEN status = 'completed' THEN '✓ Completed'
    WHEN status = 'pending' THEN '⏳ Pending'
    ELSE status
  END as status_display
FROM catalog.schema.orders
```

---

## Counter (KPI) Styling

### Counter with Description

```json
"spec": {
  "version": 2,
  "widgetType": "counter",
  "encodings": {
    "value": {
      "fieldName": "sum(revenue)",
      "displayName": "Total Revenue",
      "format": {
        "type": "number-currency",
        "currencyCode": "USD",
        "abbreviation": "compact",
        "decimalPlaces": {"type": "max", "places": 1}
      }
    }
  },
  "frame": {
    "title": "Total Revenue",
    "showTitle": true,
    "description": "For the selected period",
    "showDescription": true
  }
}
```

### Multi-Line Counter Display

Use SQL to create a formatted display value:

```sql
SELECT 
  CONCAT(
    FORMAT_NUMBER(SUM(revenue), 0), 
    ' orders\n', 
    '$', FORMAT_NUMBER(SUM(revenue), 2)
  ) as kpi_display
FROM catalog.schema.orders
```

---

## Filter Styling

### Filter Titles and Labels

```json
"spec": {
  "version": 2,
  "widgetType": "filter-multi-select",
  "encodings": {
    "fields": [{
      "fieldName": "region",
      "displayName": "Select Region",
      "queryName": "ds_region"
    }]
  },
  "frame": {
    "title": "Region Filter",
    "showTitle": true
  }
}
```

### Default Filter Selection

```json
"selection": {
  "defaultSelection": {
    "values": ["North America", "Europe"]
  }
}
```

For date range filters:
```json
"selection": {
  "defaultSelection": {
    "range": {
      "dataType": "DATE",
      "min": {"value": "now-90d/d"},
      "max": {"value": "now/d"}
    }
  }
}
```

---

## Color Schemes

### Categorical Color Scale

```json
"color": {
  "fieldName": "category",
  "scale": {
    "type": "categorical",
    "sort": "ascending"  // or "descending"
  },
  "displayName": "Category"
}
```

**Note**: AI/BI dashboards use a default color palette. Custom color schemes are not supported for bar/line/pie charts (only for choropleth maps).

---

## Best Practices

1. **Always format currency** with appropriate currency code and abbreviation
2. **Use percentage format** for ratios (ensure data is 0-1, not 0-100)
3. **Add axis titles** with units for clarity (e.g., "Revenue (USD)", "Count (#)")
4. **Use displayName** for user-friendly labels in legends and tooltips
5. **Add descriptions** to KPIs and complex charts to explain what they show
6. **Format dates** consistently across all widgets
7. **Use markdown** in text widgets for visual hierarchy
8. **Apply conditional formatting** in SQL for status indicators and trends
9. **Keep decimal places** appropriate for the metric (currency: 2, percentages: 1, counts: 0)
10. **Test formatting** with edge cases (very large numbers, negative values, nulls)

