# Integration Patterns

Patterns for integrating AI/BI dashboards with other Databricks features and external systems.

---

## Unity Catalog Integration

### Querying System Tables

Use Unity Catalog system tables for metadata-driven dashboards:

```sql
-- Table lineage dashboard
SELECT 
  source_table_full_name,
  target_table_full_name,
  COUNT(*) as dependency_count
FROM system.access.table_lineage
WHERE source_table_full_name LIKE 'catalog.schema.%'
GROUP BY source_table_full_name, target_table_full_name

-- Audit log dashboard
SELECT 
  DATE_TRUNC('DAY', event_time) as date,
  user_identity.email as user,
  action_name,
  COUNT(*) as event_count
FROM system.access.audit
WHERE event_date >= date_sub(current_date(), 30)
GROUP BY DATE_TRUNC('DAY', event_time), user_identity.email, action_name

-- Billing dashboard
SELECT 
  DATE_TRUNC('DAY', usage_date) as date,
  sku_name,
  SUM(usage_quantity) as total_usage,
  SUM(usage_quantity * list_price) as estimated_cost
FROM system.billing.usage
WHERE usage_date >= date_sub(current_date(), 30)
GROUP BY DATE_TRUNC('DAY', usage_date), sku_name
```

### Volume File Metadata

```sql
-- Files in Unity Catalog volumes
SELECT 
  volume_name,
  file_path,
  file_size_bytes,
  file_modification_time
FROM catalog.information_schema.volume_files
WHERE volume_name = 'my_volume'
ORDER BY file_modification_time DESC
```

### Table Statistics

```sql
-- Table size and row count
SELECT 
  table_catalog,
  table_schema,
  table_name,
  table_type,
  CAST(table_statistics.num_rows AS BIGINT) as row_count,
  CAST(table_statistics.total_size_bytes AS BIGINT) as size_bytes
FROM catalog.information_schema.tables
WHERE table_schema = 'my_schema'
ORDER BY size_bytes DESC
```

---

## Delta Live Tables Integration

### Pipeline Monitoring Dashboard

```sql
-- DLT pipeline runs
SELECT 
  pipeline_id,
  pipeline_name,
  update_id,
  start_time,
  end_time,
  TIMESTAMPDIFF(MINUTE, start_time, end_time) as duration_minutes,
  state,
  CASE 
    WHEN state = 'COMPLETED' THEN '✓ Success'
    WHEN state = 'FAILED' THEN '✗ Failed'
    ELSE state
  END as status_display
FROM catalog.schema.dlt_pipeline_runs
WHERE start_time >= date_sub(current_date(), 7)
ORDER BY start_time DESC
```

### Data Quality Metrics

```sql
-- DLT expectations (data quality checks)
SELECT 
  pipeline_id,
  dataset_name,
  expectation_name,
  SUM(passed_records) as passed,
  SUM(failed_records) as failed,
  SUM(passed_records) / (SUM(passed_records) + SUM(failed_records)) as pass_rate
FROM catalog.schema.dlt_expectations
WHERE event_date >= date_sub(current_date(), 7)
GROUP BY pipeline_id, dataset_name, expectation_name
```

---

## Databricks Jobs Integration

### Job Monitoring Dashboard

Use the Jobs API via MCP tools to get job run data, then create a monitoring table:

```python
# In a scheduled notebook/job
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get recent job runs
runs = w.jobs.list_runs(limit=100, completed_only=True)

# Write to Delta table
job_runs_data = [
    {
        "run_id": run.run_id,
        "job_id": run.job_id,
        "job_name": run.run_name,
        "start_time": run.start_time,
        "end_time": run.end_time,
        "state": run.state.result_state.value,
        "duration_seconds": (run.end_time - run.start_time) / 1000
    }
    for run in runs
]

spark.createDataFrame(job_runs_data).write.mode("append").saveAsTable("catalog.schema.job_runs")
```

Dashboard query:
```sql
SELECT 
  DATE_TRUNC('DAY', start_time) as date,
  job_name,
  COUNT(*) as total_runs,
  SUM(CASE WHEN state = 'SUCCESS' THEN 1 ELSE 0 END) as successful_runs,
  SUM(CASE WHEN state = 'FAILED' THEN 1 ELSE 0 END) as failed_runs,
  AVG(duration_seconds) as avg_duration_seconds
FROM catalog.schema.job_runs
WHERE start_time >= date_sub(current_date(), 30)
GROUP BY DATE_TRUNC('DAY', start_time), job_name
```

---

## MLflow Integration

### Model Performance Dashboard

```sql
-- Model metrics over time
SELECT 
  DATE_TRUNC('DAY', timestamp) as date,
  model_name,
  model_version,
  AVG(accuracy) as avg_accuracy,
  AVG(precision) as avg_precision,
  AVG(recall) as avg_recall
FROM catalog.schema.model_metrics
WHERE timestamp >= date_sub(current_date(), 30)
GROUP BY DATE_TRUNC('DAY', timestamp), model_name, model_version
ORDER BY date, model_name
```

### Model Serving Metrics

```sql
-- Endpoint request metrics
SELECT 
  DATE_TRUNC('HOUR', request_timestamp) as hour,
  endpoint_name,
  COUNT(*) as request_count,
  AVG(latency_ms) as avg_latency_ms,
  PERCENTILE(latency_ms, 0.95) as p95_latency_ms,
  SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) / COUNT(*) as success_rate
FROM catalog.schema.serving_requests
WHERE request_timestamp >= date_sub(current_date(), 1)
GROUP BY DATE_TRUNC('HOUR', request_timestamp), endpoint_name
ORDER BY hour, endpoint_name
```

---

## Streaming Data Integration

### Real-Time Dashboard Pattern

Use Structured Streaming to write aggregated data to a Delta table, then query in dashboard:

```python
# Streaming aggregation job
(spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "broker:9092")
  .option("subscribe", "events")
  .load()
  .selectExpr("CAST(value AS STRING) as json")
  .select(from_json("json", schema).alias("data"))
  .select("data.*")
  .withWatermark("event_timestamp", "10 minutes")
  .groupBy(
    window("event_timestamp", "5 minutes"),
    "event_type"
  )
  .agg(
    count("*").alias("event_count"),
    avg("value").alias("avg_value")
  )
  .writeStream
  .format("delta")
  .outputMode("append")
  .option("checkpointLocation", "/checkpoints/events")
  .toTable("catalog.schema.realtime_metrics")
)
```

Dashboard query:
```sql
SELECT 
  window.start as time_window,
  event_type,
  event_count,
  avg_value
FROM catalog.schema.realtime_metrics
WHERE window.start >= date_sub(current_date(), 1)
ORDER BY window.start DESC
```

---

## External Data Sources

### Lakehouse Federation

Query external databases directly in dashboards:

```sql
-- Query PostgreSQL via Lakehouse Federation
SELECT 
  o.order_id,
  o.order_date,
  c.customer_name,
  o.total_amount
FROM postgres_catalog.public.orders o
JOIN postgres_catalog.public.customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= date_sub(current_date(), 30)
```

### REST API Integration

Use Databricks SQL `http_request` function (if available) or create a scheduled job to fetch and store API data:

```python
# Scheduled job to fetch API data
import requests
import pandas as pd

# Fetch data from API
response = requests.get("https://api.example.com/metrics", headers={"Authorization": "Bearer TOKEN"})
data = response.json()

# Convert to DataFrame and write to Delta
df = spark.createDataFrame(pd.DataFrame(data))
df.write.mode("overwrite").saveAsTable("catalog.schema.api_metrics")
```

Dashboard query:
```sql
SELECT * FROM catalog.schema.api_metrics
WHERE last_updated >= date_sub(current_date(), 1)
```

---

## Embedding and Sharing

### Dashboard Embedding

AI/BI dashboards can be embedded in external applications:

1. **Publish dashboard** with embedded credentials:
```python
manage_dashboard(
    action="publish",
    dashboard_id="dashboard_123",
    warehouse_id="warehouse_abc",
    embed_credentials=True  # Allows users without data access to view
)
```

2. **Get embed URL** from dashboard details:
```python
result = manage_dashboard(action="get", dashboard_id="dashboard_123")
embed_url = result["url"]
```

3. **Embed in iframe**:
```html
<iframe 
  src="https://your-workspace.databricks.com/sql/dashboards/dashboard_123?embed=true"
  width="100%" 
  height="800px"
  frameborder="0">
</iframe>
```

### Scheduled Email Reports

Use Databricks Jobs to schedule dashboard snapshots:

```python
# In a scheduled notebook
from databricks.sdk import WorkspaceClient
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

w = WorkspaceClient()

# Get dashboard data
dashboard_url = "https://your-workspace.databricks.com/sql/dashboards/dashboard_123"

# Send email
msg = MIMEMultipart()
msg['Subject'] = 'Daily Dashboard Report'
msg['From'] = 'noreply@company.com'
msg['To'] = 'team@company.com'

body = f"""
Daily Dashboard Report

View the dashboard: {dashboard_url}

Key Metrics:
- Revenue: $1.2M
- Orders: 5,432
- Conversion Rate: 3.2%
"""

msg.attach(MIMEText(body, 'plain'))

# Send via SMTP
with smtplib.SMTP('smtp.company.com', 587) as server:
    server.starttls()
    server.login('user', 'password')
    server.send_message(msg)
```

---

## Delta Sharing Integration

### Shared Data Dashboard

Create dashboards on data shared via Delta Sharing:

```sql
-- Query shared table
SELECT 
  order_date,
  region,
  SUM(revenue) as total_revenue
FROM shared_catalog.shared_schema.orders
WHERE order_date >= date_sub(current_date(), 30)
GROUP BY order_date, region
ORDER BY order_date
```

**Use case**: Partner dashboards, cross-organization reporting

---

## Databricks Apps Integration

### Dashboard as Data Source for Apps

Use Databricks Apps to create custom interfaces that query the same data as dashboards:

```python
# In a Databricks App (Streamlit/Dash)
import streamlit as st
from databricks import sql

# Connect to SQL warehouse
connection = sql.connect(
    server_hostname="your-workspace.databricks.com",
    http_path="/sql/1.0/warehouses/warehouse_id",
    access_token=dbutils.secrets.get("scope", "token")
)

# Query data
cursor = connection.cursor()
cursor.execute("SELECT * FROM catalog.schema.dashboard_data WHERE date >= current_date() - 30")
data = cursor.fetchall()

# Display in app
st.dataframe(data)
```

---

## Alerting Patterns

### Threshold-Based Alerts

Create a scheduled job that queries dashboard data and sends alerts:

```python
# Scheduled alert job
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Query metric
result = spark.sql("""
  SELECT SUM(revenue) as total_revenue
  FROM catalog.schema.orders
  WHERE order_date = current_date()
""").collect()

total_revenue = result[0]['total_revenue']

# Check threshold
if total_revenue < 100000:
    # Send alert (via email, Slack, PagerDuty, etc.)
    print(f"ALERT: Revenue below threshold: ${total_revenue}")
```

### Anomaly Detection

```sql
-- Detect anomalies using statistical methods
WITH daily_metrics AS (
  SELECT 
    order_date,
    SUM(revenue) as revenue
  FROM catalog.schema.orders
  WHERE order_date >= date_sub(current_date(), 90)
  GROUP BY order_date
),
stats AS (
  SELECT 
    AVG(revenue) as mean_revenue,
    STDDEV(revenue) as stddev_revenue
  FROM daily_metrics
)
SELECT 
  dm.order_date,
  dm.revenue,
  s.mean_revenue,
  s.stddev_revenue,
  (dm.revenue - s.mean_revenue) / s.stddev_revenue as z_score,
  CASE 
    WHEN ABS((dm.revenue - s.mean_revenue) / s.stddev_revenue) > 3 THEN 'Anomaly'
    ELSE 'Normal'
  END as status
FROM daily_metrics dm
CROSS JOIN stats s
WHERE dm.order_date = current_date()
```

---

## Multi-Workspace Patterns

### Cross-Workspace Dashboards

Use Delta Sharing or Lakehouse Federation to query data from multiple workspaces:

```sql
-- Query data from Workspace A and Workspace B
WITH workspace_a_data AS (
  SELECT 'Workspace A' as source, * 
  FROM workspace_a_catalog.schema.orders
),
workspace_b_data AS (
  SELECT 'Workspace B' as source, * 
  FROM workspace_b_catalog.schema.orders
)
SELECT * FROM workspace_a_data
UNION ALL
SELECT * FROM workspace_b_data
```

---

## Best Practices

### Data Refresh Strategy

| Dashboard Type | Refresh Frequency | Implementation |
|---------------|-------------------|----------------|
| Real-time operational | <1 minute | Query streaming tables directly |
| Near real-time | 5-15 minutes | Scheduled job updates gold table |
| Daily reporting | Once per day | Overnight batch job |
| Weekly/monthly | Weekly/monthly | Scheduled aggregation job |

### Security and Governance

1. **Row-level security**: Use Unity Catalog row filters
```sql
-- Create row filter function
CREATE FUNCTION catalog.schema.filter_by_region(region STRING)
RETURNS BOOLEAN
RETURN region = current_user_region();

-- Apply to table
ALTER TABLE catalog.schema.orders
SET ROW FILTER catalog.schema.filter_by_region ON (region);
```

2. **Column masking**: Mask sensitive data
```sql
-- Create masking function
CREATE FUNCTION catalog.schema.mask_email(email STRING)
RETURNS STRING
RETURN CONCAT(SUBSTRING(email, 1, 3), '***@***.com');

-- Apply to column
ALTER TABLE catalog.schema.customers
ALTER COLUMN email SET MASK catalog.schema.mask_email;
```

3. **Audit logging**: Track dashboard access via system tables
```sql
SELECT 
  user_identity.email as user,
  request_params.dashboard_id,
  COUNT(*) as access_count
FROM system.access.audit
WHERE action_name = 'dashboardView'
  AND event_date >= date_sub(current_date(), 30)
GROUP BY user_identity.email, request_params.dashboard_id
```

### Performance Optimization

1. **Materialized views** for expensive queries:
```sql
CREATE MATERIALIZED VIEW catalog.schema.mv_daily_sales AS
SELECT 
  DATE_TRUNC('DAY', order_date) as date,
  region,
  SUM(revenue) as total_revenue,
  COUNT(*) as order_count
FROM catalog.schema.orders
GROUP BY DATE_TRUNC('DAY', order_date), region;

-- Refresh on schedule
REFRESH MATERIALIZED VIEW catalog.schema.mv_daily_sales;
```

2. **Incremental updates** for large tables:
```sql
-- Incremental update pattern
MERGE INTO catalog.schema.gold_daily_sales target
USING (
  SELECT 
    DATE_TRUNC('DAY', order_date) as date,
    region,
    SUM(revenue) as total_revenue
  FROM catalog.schema.orders
  WHERE order_date >= date_sub(current_date(), 7)
  GROUP BY DATE_TRUNC('DAY', order_date), region
) source
ON target.date = source.date AND target.region = source.region
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;
```

---

## Integration Checklist

Before deploying integrated dashboards:

- [ ] Data sources are accessible from SQL warehouse
- [ ] Refresh schedule matches data update frequency
- [ ] Security policies (row filters, column masks) are applied
- [ ] Queries are optimized (use pre-aggregated tables)
- [ ] Error handling is in place for external data sources
- [ ] Monitoring is set up for data pipeline failures
- [ ] Documentation includes data lineage and refresh schedule
- [ ] Alerts are configured for critical metrics

