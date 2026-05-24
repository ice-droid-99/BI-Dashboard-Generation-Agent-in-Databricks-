# Data Modeling Patterns

Common data modeling patterns and SQL techniques for AI/BI dashboards.

---

## Display vs Raw Datasets

> **IMPORTANT**: Separate calculation-friendly datasets from presentation-ready datasets.
> See [aibi-dashboard-guardrails](../aibi-dashboard-guardrails/SKILL.md) for detailed validation rules.

### When to Use Raw Datasets

Use raw (calculation-friendly) datasets when:
- Charts need numeric aggregation
- Filters should operate on numeric or date fields
- KPIs need precise aggregation
- Multiple widgets will aggregate the same data differently

**Example - Raw dataset for flexible aggregation:**
```sql
-- Raw dataset: numeric values for widget-level aggregation
SELECT 
  order_date,
  region,
  product_category,
  revenue,
  cost,
  quantity
FROM catalog.schema.orders
WHERE order_date >= date_sub(current_date(), 90)
```

### When to Use Display-Shaped Datasets

Use display-shaped (presentation-ready) datasets when:
- User expects exact formatted strings (e.g., `$21.6M`, not `21600000`)
- User expects rounded percentages (e.g., `250.8%`, not `2.508`)
- Table should include inline markers or labels (e.g., `✓ Completed`, `↑ 15%`)
- User provides a cross-check table with specific formatting to match
- Table is for display only, not for further aggregation

**Example - Display dataset for presentation:**
```sql
-- Display dataset: pre-formatted for exact table presentation
SELECT 
  region,
  CONCAT('$', FORMAT_NUMBER(SUM(revenue) / 1000000, 1), 'M') as revenue_display,
  CONCAT(FORMAT_NUMBER(SUM(quantity) / 1000, 1), 'K') as quantity_display,
  CONCAT(ROUND((SUM(revenue) - SUM(cost)) / SUM(revenue) * 100, 1), '%') as margin_display,
  CASE 
    WHEN SUM(revenue) > LAG(SUM(revenue)) OVER (ORDER BY region) THEN '↑'
    WHEN SUM(revenue) < LAG(SUM(revenue)) OVER (ORDER BY region) THEN '↓'
    ELSE '→'
  END as trend_indicator
FROM catalog.schema.orders
WHERE order_date >= date_sub(current_date(), 90)
GROUP BY region
ORDER BY SUM(revenue) DESC
```

### Best Practice: Separate Datasets

**DO**: Create separate datasets for calculation vs display
```json
{
  "datasets": [
    {
      "name": "ds_sales_raw",
      "displayName": "Sales Data (Raw)",
      "queryLines": ["SELECT order_date, region, revenue, cost FROM catalog.schema.orders"]
    },
    {
      "name": "ds_sales_display",
      "displayName": "Sales Summary (Display)",
      "queryLines": [
        "SELECT region, ",
        "  CONCAT('$', FORMAT_NUMBER(SUM(revenue)/1000000, 1), 'M') as revenue_display ",
        "FROM catalog.schema.orders ",
        "GROUP BY region"
      ]
    }
  ]
}
```

**DON'T**: Force presentation-specific formatting through widget formatting alone when user expects exact string matches

### Cross-Check Validation

When user provides expected values for validation:
1. Use display-shaped dataset if expected values are formatted strings
2. Use raw dataset if expected values are numeric
3. Match formatting exactly (rounding, units, labels) to user's cross-check table
4. See [aibi-dashboard-guardrails cross-check procedure](../aibi-dashboard-guardrails/references/05-cross-check-procedure.md)

---

## Time-Based Analysis

### Rolling Windows

**30-day rolling average:**
```sql
SELECT 
  order_date,
  revenue,
  AVG(revenue) OVER (
    ORDER BY order_date 
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as rolling_30d_avg
FROM catalog.schema.daily_sales
ORDER BY order_date
```

**Year-over-year comparison:**
```sql
SELECT 
  DATE_TRUNC('MONTH', order_date) as month,
  SUM(revenue) as current_revenue,
  LAG(SUM(revenue), 12) OVER (ORDER BY DATE_TRUNC('MONTH', order_date)) as prior_year_revenue,
  (SUM(revenue) - LAG(SUM(revenue), 12) OVER (ORDER BY DATE_TRUNC('MONTH', order_date))) / 
    LAG(SUM(revenue), 12) OVER (ORDER BY DATE_TRUNC('MONTH', order_date)) as yoy_growth
FROM catalog.schema.orders
GROUP BY DATE_TRUNC('MONTH', order_date)
ORDER BY month
```

### Period-over-Period Growth

**Month-over-month growth:**
```sql
WITH monthly_metrics AS (
  SELECT 
    DATE_TRUNC('MONTH', order_date) as month,
    SUM(revenue) as revenue
  FROM catalog.schema.orders
  GROUP BY DATE_TRUNC('MONTH', order_date)
)
SELECT 
  month,
  revenue,
  LAG(revenue) OVER (ORDER BY month) as prev_month_revenue,
  (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month) as mom_growth
FROM monthly_metrics
ORDER BY month
```

### Cumulative Metrics

**Running total:**
```sql
SELECT 
  order_date,
  revenue,
  SUM(revenue) OVER (ORDER BY order_date) as cumulative_revenue
FROM catalog.schema.daily_sales
ORDER BY order_date
```

---

## Cohort Analysis

### Customer Cohorts by Signup Month

```sql
WITH first_purchase AS (
  SELECT 
    customer_id,
    DATE_TRUNC('MONTH', MIN(order_date)) as cohort_month
  FROM catalog.schema.orders
  GROUP BY customer_id
),
cohort_activity AS (
  SELECT 
    fp.cohort_month,
    DATE_TRUNC('MONTH', o.order_date) as activity_month,
    COUNT(DISTINCT o.customer_id) as active_customers,
    SUM(o.revenue) as revenue
  FROM catalog.schema.orders o
  JOIN first_purchase fp ON o.customer_id = fp.customer_id
  GROUP BY fp.cohort_month, DATE_TRUNC('MONTH', o.order_date)
)
SELECT 
  cohort_month,
  activity_month,
  MONTHS_BETWEEN(activity_month, cohort_month) as months_since_signup,
  active_customers,
  revenue
FROM cohort_activity
ORDER BY cohort_month, activity_month
```

### Retention Rate

```sql
WITH first_purchase AS (
  SELECT 
    customer_id,
    DATE_TRUNC('MONTH', MIN(order_date)) as cohort_month,
    COUNT(DISTINCT customer_id) OVER (PARTITION BY DATE_TRUNC('MONTH', MIN(order_date))) as cohort_size
  FROM catalog.schema.orders
  GROUP BY customer_id
),
retention AS (
  SELECT 
    fp.cohort_month,
    MONTHS_BETWEEN(DATE_TRUNC('MONTH', o.order_date), fp.cohort_month) as month_number,
    COUNT(DISTINCT o.customer_id) as retained_customers,
    MAX(fp.cohort_size) as cohort_size
  FROM catalog.schema.orders o
  JOIN first_purchase fp ON o.customer_id = fp.customer_id
  GROUP BY fp.cohort_month, MONTHS_BETWEEN(DATE_TRUNC('MONTH', o.order_date), fp.cohort_month)
)
SELECT 
  cohort_month,
  month_number,
  retained_customers,
  cohort_size,
  retained_customers / cohort_size as retention_rate
FROM retention
ORDER BY cohort_month, month_number
```

---

## Funnel Analysis

### Conversion Funnel

```sql
WITH funnel_steps AS (
  SELECT 
    DATE_TRUNC('DAY', event_timestamp) as date,
    COUNT(DISTINCT CASE WHEN event_type = 'page_view' THEN user_id END) as step1_views,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN user_id END) as step2_add_cart,
    COUNT(DISTINCT CASE WHEN event_type = 'checkout' THEN user_id END) as step3_checkout,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) as step4_purchase
  FROM catalog.schema.events
  GROUP BY DATE_TRUNC('DAY', event_timestamp)
)
SELECT 
  date,
  step1_views,
  step2_add_cart,
  step3_checkout,
  step4_purchase,
  step2_add_cart / step1_views as view_to_cart_rate,
  step3_checkout / step2_add_cart as cart_to_checkout_rate,
  step4_purchase / step3_checkout as checkout_to_purchase_rate,
  step4_purchase / step1_views as overall_conversion_rate
FROM funnel_steps
ORDER BY date
```

---

## Segmentation

### RFM (Recency, Frequency, Monetary) Segmentation

```sql
WITH customer_metrics AS (
  SELECT 
    customer_id,
    DATEDIFF(CURRENT_DATE(), MAX(order_date)) as recency_days,
    COUNT(*) as frequency,
    SUM(revenue) as monetary
  FROM catalog.schema.orders
  GROUP BY customer_id
),
rfm_scores AS (
  SELECT 
    customer_id,
    recency_days,
    frequency,
    monetary,
    NTILE(5) OVER (ORDER BY recency_days DESC) as recency_score,
    NTILE(5) OVER (ORDER BY frequency) as frequency_score,
    NTILE(5) OVER (ORDER BY monetary) as monetary_score
  FROM customer_metrics
)
SELECT 
  customer_id,
  recency_days,
  frequency,
  monetary,
  recency_score,
  frequency_score,
  monetary_score,
  CASE 
    WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
    WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal Customers'
    WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'New Customers'
    WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
    WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Lost'
    ELSE 'Other'
  END as customer_segment
FROM rfm_scores
```

### ABC Analysis (Pareto)

```sql
WITH product_revenue AS (
  SELECT 
    product_id,
    product_name,
    SUM(revenue) as total_revenue
  FROM catalog.schema.orders
  GROUP BY product_id, product_name
),
cumulative_revenue AS (
  SELECT 
    product_id,
    product_name,
    total_revenue,
    SUM(total_revenue) OVER (ORDER BY total_revenue DESC) as cumulative_revenue,
    SUM(total_revenue) OVER () as total_revenue_all
  FROM product_revenue
)
SELECT 
  product_id,
  product_name,
  total_revenue,
  cumulative_revenue / total_revenue_all as cumulative_pct,
  CASE 
    WHEN cumulative_revenue / total_revenue_all <= 0.80 THEN 'A'
    WHEN cumulative_revenue / total_revenue_all <= 0.95 THEN 'B'
    ELSE 'C'
  END as abc_category
FROM cumulative_revenue
ORDER BY total_revenue DESC
```

---

## Statistical Aggregations

### Percentiles and Distribution

```sql
SELECT 
  product_category,
  COUNT(*) as order_count,
  AVG(order_value) as avg_order_value,
  PERCENTILE(order_value, 0.25) as p25_order_value,
  PERCENTILE(order_value, 0.50) as median_order_value,
  PERCENTILE(order_value, 0.75) as p75_order_value,
  PERCENTILE(order_value, 0.90) as p90_order_value,
  STDDEV(order_value) as stddev_order_value
FROM catalog.schema.orders
GROUP BY product_category
```

### Outlier Detection

```sql
WITH stats AS (
  SELECT 
    AVG(order_value) as mean_value,
    STDDEV(order_value) as stddev_value
  FROM catalog.schema.orders
)
SELECT 
  o.order_id,
  o.order_value,
  s.mean_value,
  s.stddev_value,
  (o.order_value - s.mean_value) / s.stddev_value as z_score,
  CASE 
    WHEN ABS((o.order_value - s.mean_value) / s.stddev_value) > 3 THEN 'Outlier'
    ELSE 'Normal'
  END as outlier_flag
FROM catalog.schema.orders o
CROSS JOIN stats s
```

---

## Ranking and Top-N

### Top Products by Revenue

```sql
SELECT 
  product_name,
  SUM(revenue) as total_revenue,
  RANK() OVER (ORDER BY SUM(revenue) DESC) as revenue_rank,
  DENSE_RANK() OVER (ORDER BY SUM(revenue) DESC) as revenue_dense_rank,
  ROW_NUMBER() OVER (ORDER BY SUM(revenue) DESC) as revenue_row_num
FROM catalog.schema.orders
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 10
```

### Top-N per Category

```sql
WITH ranked_products AS (
  SELECT 
    category,
    product_name,
    SUM(revenue) as total_revenue,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY SUM(revenue) DESC) as rank_in_category
  FROM catalog.schema.orders
  GROUP BY category, product_name
)
SELECT 
  category,
  product_name,
  total_revenue,
  rank_in_category
FROM ranked_products
WHERE rank_in_category <= 5
ORDER BY category, rank_in_category
```

---

## Slowly Changing Dimensions (SCD)

### SCD Type 2 - Historical Tracking

```sql
-- Dimension table with history
CREATE OR REPLACE TABLE catalog.schema.dim_customers (
  customer_key BIGINT GENERATED ALWAYS AS IDENTITY,
  customer_id STRING,
  customer_name STRING,
  customer_tier STRING,
  effective_date DATE,
  end_date DATE,
  is_current BOOLEAN
);

-- Query with point-in-time join
SELECT 
  o.order_date,
  o.order_id,
  c.customer_name,
  c.customer_tier,  -- Tier at time of order
  o.revenue
FROM catalog.schema.orders o
JOIN catalog.schema.dim_customers c 
  ON o.customer_id = c.customer_id
  AND o.order_date BETWEEN c.effective_date AND COALESCE(c.end_date, '9999-12-31')
```

---

## Hierarchical Data

### Parent-Child Hierarchies

```sql
-- Recursive CTE for org hierarchy
WITH RECURSIVE org_hierarchy AS (
  -- Anchor: Top-level managers
  SELECT 
    employee_id,
    employee_name,
    manager_id,
    1 as level,
    CAST(employee_name AS STRING) as path
  FROM catalog.schema.employees
  WHERE manager_id IS NULL
  
  UNION ALL
  
  -- Recursive: Subordinates
  SELECT 
    e.employee_id,
    e.employee_name,
    e.manager_id,
    oh.level + 1,
    CONCAT(oh.path, ' > ', e.employee_name)
  FROM catalog.schema.employees e
  JOIN org_hierarchy oh ON e.manager_id = oh.employee_id
)
SELECT * FROM org_hierarchy
ORDER BY path
```

### Product Category Rollup

```sql
SELECT 
  COALESCE(category, 'All Categories') as category,
  COALESCE(subcategory, 'All Subcategories') as subcategory,
  SUM(revenue) as total_revenue
FROM catalog.schema.orders
GROUP BY ROLLUP(category, subcategory)
ORDER BY category, subcategory
```

---

## Time Intelligence

### Fiscal Calendar

```sql
WITH fiscal_calendar AS (
  SELECT 
    date,
    CASE 
      WHEN MONTH(date) >= 4 THEN YEAR(date)
      ELSE YEAR(date) - 1
    END as fiscal_year,
    CASE 
      WHEN MONTH(date) >= 4 THEN MONTH(date) - 3
      ELSE MONTH(date) + 9
    END as fiscal_month,
    CASE 
      WHEN MONTH(date) IN (4,5,6) THEN 'Q1'
      WHEN MONTH(date) IN (7,8,9) THEN 'Q2'
      WHEN MONTH(date) IN (10,11,12) THEN 'Q3'
      ELSE 'Q4'
    END as fiscal_quarter
  FROM (SELECT EXPLODE(SEQUENCE(DATE('2020-01-01'), CURRENT_DATE(), INTERVAL 1 DAY)) as date)
)
SELECT 
  fc.fiscal_year,
  fc.fiscal_quarter,
  SUM(o.revenue) as revenue
FROM catalog.schema.orders o
JOIN fiscal_calendar fc ON DATE(o.order_date) = fc.date
GROUP BY fc.fiscal_year, fc.fiscal_quarter
ORDER BY fc.fiscal_year, fc.fiscal_quarter
```

### Working Days Calculation

```sql
WITH date_range AS (
  SELECT EXPLODE(SEQUENCE(DATE('2024-01-01'), DATE('2024-12-31'), INTERVAL 1 DAY)) as date
),
working_days AS (
  SELECT 
    date,
    CASE 
      WHEN DAYOFWEEK(date) IN (1, 7) THEN 0  -- Sunday=1, Saturday=7
      ELSE 1
    END as is_working_day
  FROM date_range
)
SELECT 
  DATE_TRUNC('MONTH', date) as month,
  SUM(is_working_day) as working_days_in_month
FROM working_days
GROUP BY DATE_TRUNC('MONTH', date)
ORDER BY month
```

---

## Best Practices

1. **Use CTEs** for complex queries - improves readability and maintainability
2. **Pre-compute expensive calculations** in gold tables, not in dashboard queries
3. **Leverage window functions** for rankings, running totals, and period comparisons
4. **Use CASE statements** for segmentation and bucketing logic
5. **Apply date filters** to limit data scanned and improve performance
6. **Test queries independently** via `execute_sql` before adding to dashboards
7. **Document business logic** in dataset `displayName` and widget descriptions
8. **Use consistent naming** for metrics across datasets (e.g., always `total_revenue`, not `revenue` in one place and `total_revenue` in another)

### Avoiding Metric Name Ambiguity

> **IMPORTANT**: Generic measure names can hide business logic and cause confusion.
> See [aibi-dashboard-guardrails measure name ambiguity](../aibi-dashboard-guardrails/references/02-measure-name-ambiguity.md)

**Common ambiguity patterns to avoid:**

| Ambiguous Name | Clarified Alternatives |
|----------------|------------------------|
| `revenue` | `gross_revenue`, `net_revenue`, `recognized_revenue` |
| `orders` | `booked_orders`, `fulfilled_orders`, `cancelled_orders` |
| `customers` | `new_customers`, `active_customers`, `total_customers` |
| `value` | `order_value`, `customer_lifetime_value`, `average_value` |
| `rate` | `conversion_rate`, `churn_rate`, `growth_rate` |

**Best practice:**
```sql
-- BAD: Ambiguous metric names
SELECT 
  region,
  SUM(revenue) as revenue,  -- Is this gross or net?
  COUNT(orders) as orders   -- Is this all orders or just completed?
FROM catalog.schema.sales

-- GOOD: Explicit metric names
SELECT 
  region,
  SUM(gross_revenue) as gross_revenue,
  SUM(net_revenue) as net_revenue,
  COUNT(CASE WHEN status = 'completed' THEN order_id END) as completed_orders,
  COUNT(order_id) as total_orders
FROM catalog.schema.sales
```

When creating datasets:
1. If a measure name sounds generic, reserve it for the business-default interpretation
2. Put alternative formulas under explicit names
3. Do not reuse one measure name for multiple business meanings
4. Document the formula in dataset `displayName` or widget descriptions

