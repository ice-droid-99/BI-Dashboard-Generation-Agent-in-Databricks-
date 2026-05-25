# Databricks AI/BI Dashboard Generator

An AI-powered workflow for generating Databricks AI/BI dashboards using custom skills and guardrails with AI Dev Kit.

## Overview

This project demonstrates an automated approach to creating Databricks AI/BI dashboards by leveraging AI agents with custom skills, schema validation, and intelligent guardrails. The workflow combines Databricks CLI, the official **Databricks AI Dev Kit** (MCP servers + skills), and custom-built skills to enable "vibe coding" - a seamless local development experience for Databricks dashboards from data to deployment.

## Prerequisites

### Required Tools

- **Databricks CLI** - Configured and authenticated
- **Node.js & npm** - For running various CLI tools
- **Databricks AI Dev Kit** - Official Databricks MCP servers and skills for local AI-assisted development
- **Python** - For schema generation scripts

### Installed CLI Tools

The following CLI tools are installed via npm:

- **Claude Code** - Claude AI integration for code generation
- **Gemini CLI** - Google Gemini AI integration
- **GHCP CLI** - GitHub Copilot CLI
- **Codex CLI** - OpenAI Codex integration

## Installation

### 1. Install Databricks CLI

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token
```

### 2. Install Node.js Tools

```bash
# Install npm packages globally
npm install -g claude-code
npm install -g gemini-cli
npm install -g ghcp-cli
npm install -g codex-cli
```

### 3. Install Databricks AI Dev Kit

The Databricks AI Dev Kit is from the official [Databricks Solutions repository](https://github.com/databricks-solutions/ai-dev-kit). It provides:
- **MCP (Model Context Protocol) servers** for Databricks integration
- **Pre-built skills** for Databricks development workflows
- **Local development environment** for "vibe coding" on Databricks

```powershell
# Install AI Dev Kit using PowerShell
irm install | iex
```

**What it provides:**
- MCP servers for Databricks CLI, SQL Warehouse, Unity Catalog access
- Skills for dashboard creation, data engineering, ML workflows
- Integration with AI coding assistants (Claude, Gemini, etc.)
- Local development with Databricks context

**Repository:** https://github.com/databricks-solutions/ai-dev-kit

## Project Structure

```
claudedb/
├── .agents/
│   └── skills/
│       ├── aibi-dashboard-guardrails/    # Custom guardrail skill
│       │   ├── references/
│       │   │   ├── 01-schema-structure.md
│       │   │   ├── 02-widget-types.md
│       │   │   ├── 03-display-vs-raw-datasets.md
│       │   │   └── ...
│       │   └── SKILL.md
│       └── databricks-aibi-dashboards/   # Dashboard creation skill
├── tablerel/                              # Table relationship definitions
│   └── semanticmdlrel.csv                 # CSV with table joins and cardinality
├── finalsemantic/                         # Generated semantic layer
│   ├── workspace_reportingbus_schema.yaml # Auto-generated schema with relationships
│   ├── measures.yaml                      # Measure definitions (manual)
│   └── descriptions.yaml                  # Field descriptions (manual)
├── generate_schema_yaml.py                # Schema generation script
├── updated_dashboard.json                 # Final dashboard configuration
└── README.md
```

## Workflow

### Step 1: Add AI/BI Dashboard Skills

The Databricks AI Dev Kit provides pre-built skills for Databricks development. Add the AI/BI dashboard skill:

```bash
# In your AI coding assistant (with AI Dev Kit installed), activate the skill
@skill databricks-aibi-dashboards
```

This skill provides:
- Dashboard schema structure knowledge
- Widget configuration patterns
- SQL query generation for datasets
- Best practices for Databricks AI/BI dashboards
- Integration with Databricks SQL Warehouse

### Step 2: Add Custom Guardrail Skills

Create and add a custom guardrail skill (built on top of AI Dev Kit) to enforce validation and standards:

```bash
# Add custom guardrail skill
@skill aibi-dashboard-guardrails
```

**Custom guardrail skill** (located in `.agents/skills/aibi-dashboard-guardrails/`):
- Validates dashboard JSON schema structure
- Enforces widget configuration rules
- Optimizes dataset queries
- Ensures display vs raw dataset separation
- Validates filter configurations
- Checks accessibility requirements

This custom skill extends the base AI Dev Kit skills with project-specific rules and patterns.

### Step 3: Define Table Relationships

Create a CSV file in the `tablerel/` folder to define table relationships:

**tablerel/semanticmdlrel.csv**
```csv
TableA,ColumnA,TableB,ColumnB,Cardinality
goals_by_day,DIRECTORKEYDAY,director_goals_by_day,DIRECTORKEYDAY,Many to One
goals_by_day,REPKEYDAY,performance_by_day,REPKEY,Many to One
goals_by_day,TARGETDAY,calendar_by_day,DATEVALUEDAY,Many to One
goals_by_day,REPKEYDAY,early_cancellation,SALESREPDAY,One to Many
detailes,ENROLLDATE,calendar_by_day,DAILYDATE,Many to One
```

**CSV Format:**
- `TableA`: Source table name
- `ColumnA`: Source column/key
- `TableB`: Target table name
- `ColumnB`: Target column/key
- `Cardinality`: Relationship type (Many to One, One to Many, One to One)

### Step 4: Generate Schema with Python

Run the interactive schema generator to fetch table metadata from Databricks and combine it with relationships:

```bash
# Run the schema generator
python generate_schema_yaml.py
```

**The script will prompt for:**
1. Catalog name (default: `workspace`)
2. Schema name (default: `reportingbus`)
3. Relationships CSV path (default: `tablerel/semanticmdlrel.csv`)

**What it does:**
- Connects to Databricks using configured CLI credentials
- Fetches all tables and columns from the specified schema
- Loads relationships from the CSV file
- Generates a comprehensive YAML file in `finalsemantic/`

**Output:** `finalsemantic/{catalog}_{schema}_schema.yaml`

Example output structure:
```yaml
version: '1.0'
catalog: workspace
schema: reportingbus
generated_at: '2026-05-25T10:30:00'
tables:
  - name: goals_by_day
    columns:
      - name: DIRECTORKEYDAY
        type: string
      - name: REPKEYDAY
        type: string
      - name: TARGETDAY
        type: date
relationships:
  - name: goals_by_day_to_director_goals_by_day
    from_table: goals_by_day
    from_column: DIRECTORKEYDAY
    to_table: director_goals_by_day
    to_column: DIRECTORKEYDAY
    cardinality: Many to One
```

### Step 5: Add Measures and Descriptions

Manually create semantic layer files in the `finalsemantic/` folder:

#### **finalsemantic/measures.yaml** - Define business metrics

```yaml
measures:
  - name: total_revenue
    expression: SUM(sales_amount)
    format: currency
    description: Total sales revenue across all transactions
    
  - name: avg_order_value
    expression: AVG(order_total)
    format: currency
    description: Average value per order
    
  - name: customer_count
    expression: COUNT(DISTINCT customer_id)
    format: number
    description: Unique customer count
    
  - name: conversion_rate
    expression: (COUNT(DISTINCT order_id) / COUNT(DISTINCT session_id)) * 100
    format: percentage
    description: Percentage of sessions that result in orders
```

#### **finalsemantic/descriptions.yaml** - Define field descriptions

```yaml
dimensions:
  - name: product_category
    column: category
    description: Product category grouping (Electronics, Clothing, Home, etc.)
    
  - name: customer_segment
    column: segment
    description: Customer segmentation (Premium, Standard, Basic)
    
  - name: order_date
    column: order_date
    description: Date when the order was placed
    data_type: date

fields:
  - name: sales_amount
    description: Total sales amount in USD
    
  - name: product_name
    description: Name of the product sold
    
  - name: customer_id
    description: Unique identifier for customer
```

**Note:** The auto-generated schema YAML provides table structure and relationships. The measures.yaml and descriptions.yaml add business context and metric definitions.

### Step 6: AI-Powered Dashboard Generation

Using your AI coding assistant (Claude Code, Gemini CLI, etc.) with Databricks AI Dev Kit MCP integration, provide the complete context:

```
Generate a Databricks AI/BI dashboard with the following:

Context:
- Refer to the finalsemantic folder for:
  * Schema structure and relationships (workspace_reportingbus_schema.yaml)
  * Measures definitions (measures.yaml)
  * Field descriptions (descriptions.yaml)
- Use the aibi-dashboard-guardrails skill for validation
- Query tables from Databricks schema: workspace.reportingbus
- Use the table relationships defined in the schema YAML

Dashboard Requirements:
- KPIs: Total Revenue, Average Order Value, Customer Count, Conversion Rate
- Visuals:
  * Bar chart: Revenue by Product Category
  * Line chart: Monthly Sales Trend
  * Pie chart: Customer Segment Distribution
  * Table: Top 10 Products by Revenue
  * Heatmap: Sales by Day of Week and Hour
- Filters: Date Range, Product Category, Customer Segment
- Layout: Responsive grid with KPIs at top

Apply best practices from the guardrail skill and ensure all measures from measures.yaml are available.
```

The AI agent will:
1. Read `finalsemantic/{catalog}_{schema}_schema.yaml` for table structure and relationships
2. Read `finalsemantic/measures.yaml` for metric definitions
3. Read `finalsemantic/descriptions.yaml` for field context
4. Apply the `aibi-dashboard-guardrails` skill for validation
5. Generate widget configurations with proper SQL queries
6. Use the relationships to create accurate joins
7. Create the complete dashboard JSON
8. Output `updated_dashboard.json`

### Step 7: Deploy to Databricks

```bash
# Deploy the generated dashboard
databricks dashboards create --file updated_dashboard.json

# Or update existing dashboard
databricks dashboards update --dashboard-id <id> --file updated_dashboard.json
```

## Key Features

### Databricks AI Dev Kit Integration

The official Databricks AI Dev Kit provides:

- **MCP Servers** - Direct integration with Databricks workspace, SQL Warehouse, Unity Catalog
- **Pre-built Skills** - Databricks-specific knowledge for dashboards, pipelines, ML workflows
- **Local Development** - "Vibe coding" experience with full Databricks context locally
- **Multi-AI Support** - Works with Claude, Gemini, and other AI coding assistants

### Custom Guardrails

The `aibi-dashboard-guardrails` custom skill enforces:

- **Schema Validation** - Ensures proper JSON structure
- **Widget Type Checking** - Validates widget configurations
- **Dataset Separation** - Enforces display vs raw dataset patterns
- **Query Optimization** - Suggests performance improvements
- **Accessibility** - Ensures proper labeling and descriptions

### AI-Assisted Generation

Benefits of this workflow:

- **Rapid Prototyping** - Generate dashboards in minutes
- **Best Practices** - Built-in Databricks patterns from AI Dev Kit skills
- **Consistency** - Standardized structure across dashboards
- **Error Prevention** - Custom guardrails catch common mistakes
- **Documentation** - Auto-generated descriptions and comments
- **Local Context** - Full access to Databricks schema and metadata via MCP

## Example Usage

### Complete Workflow Example

```bash
# 1. Add skills in AI Dev Kit
@skill databricks-aibi-dashboards
@skill aibi-dashboard-guardrails

# 2. Create table relationships CSV
# Edit tablerel/semanticmdlrel.csv with your table joins

# 3. Generate schema from Databricks
python generate_schema_yaml.py
# Enter catalog: workspace
# Enter schema: reportingbus
# Enter relationships CSV: tablerel/semanticmdlrel.csv

# 4. Create semantic layer files
# - Create finalsemantic/measures.yaml with your metrics
# - Create finalsemantic/descriptions.yaml with field descriptions

# 5. Prompt AI agent
"Generate a Databricks AI/BI dashboard:

Context:
- Refer to finalsemantic folder for all definitions
- Use schema: workspace.reportingbus
- Apply aibi-dashboard-guardrails skill

Dashboard:
- KPIs: total_revenue, avg_order_value, customer_count
- Bar chart: Revenue by Category
- Line chart: Monthly Trend
- Table: Top Products
- Filters: Date Range, Category"

# 6. Deploy
databricks dashboards create --file updated_dashboard.json
```

### Sample Files

**tablerel/semanticmdlrel.csv**
```csv
TableA,ColumnA,TableB,ColumnB,Cardinality
sales,product_id,products,id,Many to One
sales,customer_id,customers,id,Many to One
sales,date,calendar,date_value,Many to One
```

**finalsemantic/measures.yaml**
```yaml
measures:
  - name: total_revenue
    expression: SUM(amount)
    format: currency
    description: Total sales revenue
```

**finalsemantic/descriptions.yaml**
```yaml
dimensions:
  - name: category
    column: product_category
    description: Product category grouping
```

### Advanced Customization

```bash
# Generate with specific requirements
"Create a dashboard using finalsemantic folder and sales_db schema:
- Custom color palette: #1E3A8A, #3B82F6, #60A5FA
- Responsive layout for mobile
- Interactive filters for date range and region
- Drill-down capability on charts
- Use all measures from measures.yaml
- Apply guardrail validation"
```

## Skills Reference

### Available Skills

**From Databricks AI Dev Kit:**
- `databricks-core` - CLI operations and authentication
- `databricks-aibi-dashboards` - Dashboard creation patterns
- `databricks-ai-functions` - AI function integration
- `databricks-dbsql` - SQL warehouse operations
- `databricks-unity-catalog` - Unity Catalog operations
- `databricks-vector-search` - Vector search integration
- And many more...

**Custom Skills (this project):**
- `aibi-dashboard-guardrails` - Custom validation and best practices

### Activating Skills

```bash
# In your AI coding assistant with AI Dev Kit installed:
@skill databricks-aibi-dashboards
@skill aibi-dashboard-guardrails
```

## Troubleshooting

### Common Issues

1. **Schema Validation Errors**
   - Check JSON syntax
   - Verify all required fields are present
   - Ensure measure expressions are valid SQL

2. **Deployment Failures**
   - Verify Databricks CLI authentication
   - Check workspace permissions
   - Validate SQL warehouse access

3. **Widget Rendering Issues**
   - Review dataset queries
   - Check field mappings
   - Verify widget type compatibility

## Best Practices

1. **Start with Schema** - Always generate schema first
2. **Incremental Development** - Build and test widgets individually
3. **Use Guardrails** - Let AI validate before deployment
4. **Document Everything** - Add descriptions to all components
5. **Version Control** - Track schema and dashboard changes in Git

## Contributing

Contributions are welcome! Areas for improvement:

- Additional guardrail rules
- More schema templates
- Enhanced validation logic
- Integration with CI/CD pipelines

## Resources

- [Databricks AI/BI Documentation](https://docs.databricks.com/dashboards/)
- [Databricks AI Dev Kit (GitHub)](https://github.com/databricks/ai-dev-kit)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Databricks team for AI/BI platform and AI Dev Kit
- Databricks Solutions team for MCP servers and skills
- Model Context Protocol for standardized AI-tool integration
- Community contributors for skills and patterns

---

**Created with Databricks AI Dev Kit** 🚀

*Enabling "vibe coding" for Databricks - local AI-assisted development with full workspace context*
