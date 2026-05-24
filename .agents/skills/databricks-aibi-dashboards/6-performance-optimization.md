# Performance Optimization

Best practices for building fast, efficient AI/BI dashboards that scale to large datasets.

---

## Query Performance

### 1. Pre-Aggregate Data in Datasets

**DO**: Perform aggregations in dataset SQL (runs once, cached)
```sql
SELECT 
  DATE_TRUNC('DAY', order_date) as day,
  region,
  SUM(revenue) as total_revenue,
  COUNT(DISTINCT customer_id) as unique_customers
FROM catalog.schema.orders
GROUP BY DATE_TRUNC('DAY', order_date), region
```

**DON'T**: Rely on widget-level aggregations for large raw datasets
```sql
-- Avoid: Returns millions of rows, then widget aggregates
SELECT order_date, region, revenue, customer_id
FROM catalog.schema.orders
```

### 2. Use Appropriate Disaggregation Settings

| Dataset Type | disaggregated | Use Case |
|--------------|---------------|----------|
| Pre-aggregated (1 row) | `true` | Single KPI counter (e.g., "Total Revenue") |
| Pre-aggregated (multi-row) | `true` | Charts with pre-computed aggregates |
| Raw/detail data | `false` | Widget performs aggregation (slower for large data) |

**Performance tip**: Pre-aggregate in SQL and use `disaggregated: true` for best performance.

### 3. Limit Date Ranges

Always include date filters to avoid scanning entire tables:

```sql
-- Good: Scans only recent data
SELECT * FROM catalog.schema.orders
WHERE order_date >= date_sub(current_date(), 90)

-- Bad: Full table scan
SELECT * FROM catalog.schema.orders
```

Use dataset parameters for dynamic date filtering:
```json
{
  "queryLines": [
    "SELECT * FROM catalog.schema.orders ",
    "WHERE order_date BETWEEN :date_range.min AND :date_range.max"
  ],
  "parameters": [{
    "keyword": "date_range",
    "dataType": "DATE",
    "complexType": "RANGE",
    "defaultSelection": {
      "range": {
        "dataType": "DATE",
        "min": {"value": "now-90d/d"},
        "max": {"value": "now/d"}
      }
    }
  }]
}
```

### 4. Optimize JOIN Operations

**Use broadcast joins for small dimension tables:**
```sql
SELECT /*+ BROADCAST(dim_products) */
  o.order_id,
  p.product_name,
  o.revenue
FROM catalog.schema.orders o
JOIN catalog.schema.dim_products p ON o.product_id = p.product_id
```

**Pre-join in a materialized view or gold table** instead of joining in dashboard queries.

### 5. Partition Pruning

Ensure queries leverage table partitioning:
```sql
-- Good: Uses partition pruning on date column
SELECT * FROM catalog.schema.orders
WHERE order_date = '2024-01-15'

-- Bad: Function on partition column prevents pruning
SELECT * FROM catalog.schema.orders
WHERE YEAR(order_date) = 2024
```

---

## Dataset Design Patterns

### Pattern 1: One Dataset Per Domain

**DO**: Create focused datasets for each business domain
```json
{
  "datasets": [
    {"name": "ds_sales", "queryLines": ["SELECT ... FROM sales_fact"]},
    {"name": "ds_customers", "queryLines": ["SELECT ... FROM customer_dim"]},
    {"name": "ds_products", "queryLines": ["SELECT ... FROM product_dim"]}
  ]
}
```

**DON'T**: Create one massive dataset with all columns
```json
{
  "datasets": [
    {"name": "ds_everything", "queryLines": ["SELECT * FROM sales JOIN customers JOIN products ..."]}
  ]
}
```

### Pattern 2: Separate Datasets for Different Granularities

```json
{
  "datasets": [
    {
      "name": "ds_daily_summary",
      "queryLines": ["SELECT DATE_TRUNC('DAY', ts) as day, SUM(revenue) as revenue FROM orders GROUP BY day"]
    },
    {
      "name": "ds_monthly_summary",
      "queryLines": ["SELECT DATE_TRUNC('MONTH', ts) as month, SUM(revenue) as revenue FROM orders GROUP BY month"]
    },
    {
      "name": "ds_order_details",
      "queryLines": ["SELECT * FROM orders WHERE order_date >= date_sub(current_date(), 30)"]
    }
  ]
}
```

Use daily for trend charts, monthly for high-level KPIs, details for tables.

### Pattern 3: Computed Columns in Datasets

**DO**: Calculate derived metrics in dataset SQL
```sql
SELECT 
  order_id,
  revenue,
  cost,
  (revenue - cost) as profit,
  CASE 
    WHEN revenue > 1000 THEN 'High Value'
    WHEN revenue > 500 THEN 'Medium Value'
    ELSE 'Low Value'
  END as value_tier
FROM catalog.schema.orders
```

**DON'T**: Try to compute in widget expressions (not supported)

---

## Caching and Refresh Strategy

### Dashboard Query Caching

AI/BI dashboards automatically cache query results. Cache behavior:
- **Cache duration**: Configurable per warehouse (default: 1 hour)
- **Cache invalidation**: Automatic when underlying data changes
- **Cache scope**: Per user (respects row-level security)

### Refresh Strategies

| Strategy | Implementation | Use Case |
|----------|----------------|----------|
| **Real-time** | Query live tables directly | Operational dashboards, <1M rows |
| **Scheduled refresh** | Use Delta Live Tables or scheduled jobs to update gold tables | Daily/hourly reporting, >1M rows |
| **Incremental** | Use `MERGE` or `INSERT OVERWRITE` with partitions | Large fact tables with time-based partitions |

**Example: Scheduled gold table refresh**
```python
# In a Databricks job (scheduled daily)
spark.sql("""
  INSERT OVERWRITE TABLE catalog.schema.gold_daily_sales
  PARTITION (date)
  SELECT 
    DATE_TRUNC('DAY', order_timestamp) as date,
    region,
    SUM(revenue) as total_revenue,
    COUNT(*) as order_count
  FROM catalog.schema.bronze_orders
  WHERE DATE_TRUNC('DAY', order_timestamp) = current_date() - INTERVAL 1 DAY
  GROUP BY date, region
""")
```

---

## Warehouse Sizing

### Warehouse Size Guidelines

| Dashboard Complexity | Data Volume | Recommended Size | Notes |
|---------------------|-------------|------------------|-------|
| Simple (5-10 widgets) | <1M rows | Small (2X-Small to Small) | Basic KPIs and charts |
| Medium (10-20 widgets) | 1M-10M rows | Medium | Multiple pages, filters |
| Complex (20+ widgets) | 10M-100M rows | Large | Heavy aggregations, many filters |
| Enterprise | >100M rows | X-Large or 2X-Large | Consider pre-aggregation |

### Serverless SQL Warehouses

**Recommended**: Use serverless warehouses for AI/BI dashboards
- Instant startup (no cold start delay)
- Auto-scaling based on query load
- Cost-effective for variable usage patterns

```python
# Create serverless warehouse via MCP tool
manage_sql_warehouse(
    action="create",
    name="aibi_dashboard_warehouse",
    enable_serverless=True,
    size="Medium",
    auto_stop_mins=10
)
```

---

## Cardinality Management

### High-Cardinality Dimensions

**Problem**: Charts with >10 distinct values become unreadable

**Solution 1: TOP-N + Other**
```sql
WITH ranked AS (
  SELECT 
    product_name,
    SUM(revenue) as revenue,
    ROW_NUMBER() OVER (ORDER BY SUM(revenue) DESC) as rank
  FROM catalog.schema.orders
  GROUP BY product_name
)
SELECT 
  CASE WHEN rank <= 10 THEN product_name ELSE 'Other' END as product_category,
  SUM(revenue) as total_revenue
FROM ranked
GROUP BY CASE WHEN rank <= 10 THEN product_name ELSE 'Other' END
```

**Solution 2: Aggregate to Higher Level**
```sql
-- Instead of 1000 stores, show 10 regions
SELECT region, SUM(revenue) as revenue
FROM catalog.schema.orders
GROUP BY region
```

**Solution 3: Use Table Widget**
For high-cardinality dimensions (customer_id, order_id), use a table instead of a chart.

---

## Filter Performance

### Filter Query Optimization

**DO**: Use indexed columns for filters
```sql
-- Good: Filters on indexed/partition columns
SELECT DISTINCT region FROM catalog.schema.orders
WHERE order_date >= date_sub(current_date(), 90)
```

**DON'T**: Use expensive operations in filter queries
```sql
-- Bad: Complex aggregations in filter query
SELECT region, COUNT(*) as cnt
FROM catalog.schema.orders
GROUP BY region
HAVING COUNT(*) > 1000
```

### Multi-Dataset Filter Binding

When a filter affects multiple datasets, the dashboard executes one query per dataset. Optimize each dataset independently:

```json
{
  "widget": {
    "name": "filter_region",
    "queries": [
      {
        "name": "sales_region",
        "query": {
          "datasetName": "ds_sales",  // Pre-aggregated, fast
          "fields": [{"name": "region", "expression": "`region`"}],
          "disaggregated": false
        }
      },
      {
        "name": "customers_region",
        "query": {
          "datasetName": "ds_customers",  // Dimension table, fast
          "fields": [{"name": "region", "expression": "`region`"}],
          "disaggregated": false
        }
      }
    ]
  }
}
```

---

## Monitoring and Debugging

### Query Execution Metrics

View query performance in Databricks SQL:
1. Open SQL Warehouse → Query History
2. Filter by dashboard name or user
3. Check execution time, data scanned, cache hits

### Slow Query Diagnosis

**Check these metrics:**
- **Execution time**: >5s indicates optimization needed
- **Data scanned**: >1GB suggests missing filters or partitioning
- **Cache hit rate**: <50% means queries aren't benefiting from caching

**Common fixes:**
1. Add date range filters to reduce data scanned
2. Pre-aggregate data in gold tables
3. Use partitioned tables with partition pruning
4. Increase warehouse size for complex queries

### Dashboard Load Time

**Target**: <3 seconds for initial page load

**Optimization checklist:**
- [ ] All datasets use pre-aggregated data
- [ ] Date filters limit data to <90 days by default
- [ ] High-cardinality dimensions use TOP-N or tables
- [ ] Warehouse size matches data volume
- [ ] Queries leverage table partitioning

---

## Best Practices Summary

1. **Pre-aggregate data** in dataset SQL, use `disaggregated: true`
2. **Limit date ranges** with default filters (30-90 days)
3. **Use serverless warehouses** for auto-scaling and cost efficiency
4. **Separate datasets** by domain and granularity
5. **Manage cardinality** with TOP-N, aggregation, or tables
6. **Optimize filters** with indexed columns and simple queries
7. **Monitor performance** via Query History and adjust as needed
8. **Cache-friendly queries** - avoid random parameters that break caching

