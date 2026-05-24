# Dashboard Design Principles

Best practices for designing effective, user-friendly AI/BI dashboards that communicate insights clearly.

---

## Dashboard Structure

### Information Hierarchy

**Recommended page structure:**

```
┌─────────────────────────────────────────────────────────┐
│ 1. TITLE & DESCRIPTION (y=0-1, h=1-2)                  │
│    - What: Dashboard purpose                            │
│    - Who: Target audience                               │
│    - When: Data freshness                               │
├─────────────────────────────────────────────────────────┤
│ 2. KEY METRICS (y=2-4, h=3-4)                          │
│    - 3-5 most important KPIs                            │
│    - Side-by-side counters (w=4 each)                   │
├─────────────────────────────────────────────────────────┤
│ 3. TRENDS (y=5-10, h=5-6)                              │
│    - Time series charts                                 │
│    - Show patterns over time                            │
├─────────────────────────────────────────────────────────┤
│ 4. BREAKDOWNS (y=11-16, h=5-6)                         │
│    - Categorical analysis                               │
│    - Comparisons across dimensions                      │
├─────────────────────────────────────────────────────────┤
│ 5. DETAILS (y=17+, h=6-8)                              │
│    - Tables with drill-down data                        │
│    - Supporting information                             │
└─────────────────────────────────────────────────────────┘
```

### Multi-Page Dashboards

**Page organization patterns:**

| Pattern | Pages | Use Case |
|---------|-------|----------|
| **Overview + Details** | 1. Summary<br>2. Detailed Analysis | Executive summary with drill-down |
| **Funnel** | 1. Acquisition<br>2. Engagement<br>3. Conversion | User journey analysis |
| **Comparative** | 1. Region A<br>2. Region B<br>3. Comparison | Side-by-side comparisons |
| **Time-Based** | 1. Daily<br>2. Weekly<br>3. Monthly | Different time granularities |

**Always include:**
- Global filters page (if filters apply across pages)
- Consistent navigation (page names should indicate content)

---

## Visual Design

### Layout Grid (12 Columns)

**Standard widget widths:**

| Width | Use Case | Example |
|-------|----------|---------|
| 12 | Full-width | Page title, section headers, wide tables, detailed charts |
| 6 | Half-width | Side-by-side charts, medium tables |
| 4 | Third-width | KPI counters (3 per row), filters, small charts |
| 3 | Quarter-width | Many small KPIs (4 per row) |

**Row composition rules:**
- Each row MUST sum to width=12
- No gaps allowed (causes layout errors)
- Align widgets vertically for clean appearance

**Good layout examples:**
```
Row 1: [12]                    (title)
Row 2: [4][4][4]              (3 KPIs)
Row 3: [6][6]                 (2 charts)
Row 4: [12]                   (table)

Row 1: [12]                   (title)
Row 2: [3][3][3][3]          (4 KPIs)
Row 3: [8][4]                (chart + filter)
Row 4: [12]                  (table)
```

**Bad layout examples:**
```
Row 1: [4][4]                 ❌ Only 8/12 (gap!)
Row 2: [5][5]                 ❌ Only 10/12 (gap!)
Row 3: [7][7]                 ❌ 14/12 (overflow!)
```

### Widget Sizing

**Height guidelines:**

| Widget Type | Min Height | Recommended | Max Height |
|-------------|------------|-------------|------------|
| Text (title) | 1 | 1 | 2 |
| Text (description) | 1 | 1-2 | 3 |
| Counter/KPI | 2 | 3-4 | 5 |
| Line/Bar chart | 4 | 5-6 | 8 |
| Pie chart | 4 | 5-6 | 7 |
| Table | 4 | 6-8 | 12 |
| Filter | 2 | 2 | 3 |

**Common mistakes:**
- Counter height=2: Too cramped, text overlaps
- Chart height=3: Axis labels overlap, unreadable
- Table height=3: Only shows 1-2 rows, requires scrolling

### White Space

**Use section headers to create visual separation:**

```json
{
  "widget": {
    "name": "section_trends",
    "multilineTextboxSpec": {"lines": ["## Revenue Trends"]}
  },
  "position": {"x": 0, "y": 10, "width": 12, "height": 1}
}
```

**Spacing between sections:**
- Add 1-row section header between major sections
- Use consistent y-spacing (e.g., KPIs at y=2, first chart at y=6)

---

## Color and Visual Encoding

### Color Usage

**Best practices:**
- **Limit colors**: 3-8 distinct colors per chart
- **Consistent meaning**: Same color = same category across all charts
- **Accessibility**: Ensure sufficient contrast

**Color by data type:**

| Data Type | Color Approach | Example |
|-----------|----------------|---------|
| Categorical (3-8 values) | Distinct colors | Regions, product lines |
| Categorical (>8 values) | Use table or TOP-N | Customer IDs, SKUs |
| Sequential (low to high) | Single hue gradient | Revenue, count |
| Diverging (negative/positive) | Two-hue gradient | Profit/loss, change |

### Chart Type Selection

| Data Question | Chart Type | Why |
|---------------|------------|-----|
| How has X changed over time? | Line chart | Shows trends and patterns |
| Compare categories | Bar chart | Easy to compare lengths |
| Show composition (parts of whole) | Pie chart | Shows proportions (limit to 3-8 slices) |
| Show distribution | Histogram | Shows frequency distribution |
| Compare two metrics | Scatter plot | Shows correlation |
| Show geographic data | Choropleth map | Spatial patterns |
| Show multiple metrics over time | Combo chart | Bar + line for different scales |

**Avoid:**
- Pie charts with >8 slices (use bar chart instead)
- 3D charts (distort perception)
- Dual-axis charts with unrelated metrics (confusing)

---

## KPI Design

### Effective KPI Counters

**Include context:**
```json
"frame": {
  "title": "Total Revenue",
  "showTitle": true,
  "description": "For the selected period",
  "showDescription": true
}
```

**Show comparison when possible:**
```sql
WITH current_period AS (
  SELECT SUM(revenue) as current_revenue
  FROM catalog.schema.orders
  WHERE order_date >= date_sub(current_date(), 30)
),
prior_period AS (
  SELECT SUM(revenue) as prior_revenue
  FROM catalog.schema.orders
  WHERE order_date >= date_sub(current_date(), 60)
    AND order_date < date_sub(current_date(), 30)
)
SELECT 
  current_revenue,
  prior_revenue,
  (current_revenue - prior_revenue) / prior_revenue as change_pct,
  CONCAT(
    '$', FORMAT_NUMBER(current_revenue, 0),
    ' (', 
    CASE WHEN (current_revenue - prior_revenue) / prior_revenue > 0 THEN '+' ELSE '' END,
    ROUND((current_revenue - prior_revenue) / prior_revenue * 100, 1),
    '%)'
  ) as kpi_display
FROM current_period, prior_period
```

**KPI selection criteria:**
- **Actionable**: Can users do something about it?
- **Relevant**: Does it matter to the audience?
- **Timely**: Is it current enough to act on?
- **Accurate**: Is the data reliable?

### KPI Layout Patterns

**3 KPIs (most common):**
```
[KPI 1: w=4, h=3] [KPI 2: w=4, h=3] [KPI 3: w=4, h=3]
```

**4 KPIs:**
```
[KPI 1: w=3, h=3] [KPI 2: w=3, h=3] [KPI 3: w=3, h=3] [KPI 4: w=3, h=3]
```

**5 KPIs (two rows):**
```
Row 1: [KPI 1: w=4, h=3] [KPI 2: w=4, h=3] [KPI 3: w=4, h=3]
Row 2: [KPI 4: w=6, h=3] [KPI 5: w=6, h=3]
```

---

## Interactivity

### Filter Design

**Global filters (affect all pages):**
- Place on dedicated filter page
- Include: Date range, primary dimensions (region, category)
- Limit to 3-5 filters (too many = decision paralysis)

**Page-level filters (affect one page):**
- Place in top-right corner of page
- Use for page-specific dimensions
- Example: Platform filter on "Platform Breakdown" page

**Filter defaults:**
- Set sensible defaults (e.g., last 30 days, all regions)
- Don't force users to select before seeing data

### Drill-Down Patterns

**Summary → Detail navigation:**

Page 1: Overview
```
- KPI: Total Revenue
- Chart: Revenue by Region (bar chart)
```

Page 2: Regional Detail
```
- Filter: Region (page-level)
- Chart: Revenue by Store (bar chart)
- Table: Store-level details
```

**Use consistent dimensions** across pages for intuitive navigation.

---

## Performance Considerations

### Data Volume Guidelines

| Dashboard Complexity | Max Rows per Dataset | Strategy |
|---------------------|----------------------|----------|
| Simple (5-10 widgets) | 100K | Query live tables |
| Medium (10-20 widgets) | 1M | Pre-aggregate to daily/hourly |
| Complex (20+ widgets) | 10M | Use gold tables with aggregations |
| Enterprise (30+ widgets) | 100M+ | Multiple gold tables, incremental refresh |

### Loading Time Targets

- **Initial page load**: <3 seconds
- **Filter interaction**: <1 second
- **Page navigation**: <2 seconds

**If slower:**
1. Pre-aggregate data in dataset SQL
2. Add date filters to limit data scanned
3. Use TOP-N for high-cardinality dimensions
4. Increase warehouse size
5. Consider materialized views or gold tables

---

## Accessibility

### Text Readability

- **Font size**: Use headers (##) for section titles, normal text for descriptions
- **Contrast**: Ensure text is readable against background
- **Labels**: Always include axis titles and widget titles

### Chart Accessibility

- **Axis labels**: Always include units (e.g., "Revenue (USD)", "Count (#)")
- **Legends**: Use clear, descriptive labels
- **Color**: Don't rely solely on color to convey information (use labels too)

### Alternative Text

Use widget descriptions to explain what the chart shows:
```json
"frame": {
  "title": "Revenue Trend",
  "showTitle": true,
  "description": "Daily revenue over the past 90 days, showing seasonal patterns",
  "showDescription": true
}
```

---

## Dashboard Checklist

Before publishing, verify:

### Content
- [ ] Dashboard has a clear title and description
- [ ] KPIs are relevant and actionable
- [ ] Charts answer specific business questions
- [ ] Data is accurate and up-to-date
- [ ] **Metric names are unambiguous** (gross vs net, booked vs realized, etc.)
- [ ] **If user provided expected values, results match exactly**

### Design
- [ ] Layout follows 12-column grid (no gaps)
- [ ] Widget heights are appropriate (KPIs: 3-4, charts: 5-6)
- [ ] Section headers separate major sections
- [ ] Color usage is consistent and limited (3-8 colors)

### Interactivity
- [ ] Filters have sensible defaults
- [ ] Global filters affect all relevant pages
- [ ] Page navigation is intuitive

### Performance
- [ ] All queries tested via execute_sql
- [ ] Initial load time <3 seconds
- [ ] Date filters limit data scanned
- [ ] High-cardinality dimensions use TOP-N or tables

### Formatting
- [ ] Currency formatted with correct code and abbreviation
- [ ] **Formatting matches user requirements** (compact vs full, units, rounding)
- [ ] Percentages in 0-1 range (not 0-100)
- [ ] Axis titles include units
- [ ] Widget titles and descriptions are clear

### Business Validation
- [ ] **KPI formulas validated with explicit SQL**
- [ ] **Prompt requirements override any conflicting YAML definitions**
- [ ] **Display datasets used only for presentation-ready tables**
- [ ] **Raw datasets used for aggregation and filtering**
- [ ] See [aibi-dashboard-guardrails](../aibi-dashboard-guardrails/SKILL.md) for detailed validation rules

---

## Common Anti-Patterns

### ❌ Too Many KPIs
**Problem**: 10+ KPIs on one page
**Solution**: Limit to 3-5 most important metrics, move others to detail pages

### ❌ Chart Overload
**Problem**: 8+ charts on one page
**Solution**: Group related charts on separate pages, use tabs/navigation

### ❌ Unreadable Charts
**Problem**: Pie chart with 20 slices, bar chart with 50 bars
**Solution**: Use TOP-N + "Other", aggregate to higher level, or use table

### ❌ No Context
**Problem**: KPI shows "1.2M" with no explanation
**Solution**: Add title, description, and comparison (vs. prior period)

### ❌ Inconsistent Filters
**Problem**: Date filter on page 1 doesn't affect page 2
**Solution**: Use global filters for cross-page dimensions

### ❌ Slow Loading
**Problem**: Dashboard takes 10+ seconds to load
**Solution**: Pre-aggregate data, add date filters, use gold tables

### ❌ Poor Layout
**Problem**: Widgets have gaps, inconsistent sizing
**Solution**: Follow 12-column grid, use standard widget sizes

---

## Examples of Good Dashboard Design

### Executive Dashboard
```
Page 1: Overview
- Title: "Executive Dashboard - Q1 2024"
- 4 KPIs: Revenue, Orders, Customers, Profit Margin (w=3 each)
- Line chart: Revenue trend (w=12, h=5)
- Bar chart: Revenue by region (w=6, h=5) + Pie: Revenue by category (w=6, h=5)

Page 2: Filters
- Date range filter
- Region filter
- Category filter
```

### Operational Dashboard
```
Page 1: Real-Time Metrics
- Title: "Operations Dashboard - Live"
- 3 KPIs: Orders today, Avg fulfillment time, Error rate (w=4 each)
- Line chart: Hourly order volume (w=12, h=5)
- Table: Recent orders (w=12, h=6)

Page 2: Filters
- Date range filter (default: today)
- Status filter
```

### Analytical Dashboard
```
Page 1: Customer Analysis
- Title: "Customer Insights"
- 3 KPIs: Total customers, Avg LTV, Retention rate (w=4 each)
- Line chart: Customer acquisition trend (w=6, h=5) + Pie: Customers by segment (w=6, h=5)
- Table: Top customers by revenue (w=12, h=6)

Page 2: Cohort Analysis
- Title: "Cohort Retention"
- Heatmap: Retention by cohort (w=12, h=8)
- Table: Cohort details (w=12, h=6)
```

