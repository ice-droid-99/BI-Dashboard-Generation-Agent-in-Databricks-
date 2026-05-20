# Schema Discovery YAML Generator

Auto-discover Databricks schema tables and generate dbt-like YAML documentation with relationships.

## Overview

This script connects to your Databricks workspace, introspects a specified schema, and generates a YAML file that documents all tables, their columns, and relationships. The output format is similar to dbt's `schema.yml` files, making it useful for:

- **Documentation**: Keep track of table structures and relationships
- **Governance**: Maintain a central registry of data assets and their connections
- **Integration**: Use with other data tools that read YAML schemas
- **Version Control**: Track schema changes over time
- **Data Lineage**: Understand how tables relate to each other

## Installation

### Prerequisites

- Python 3.7+
- Databricks workspace connection configured in `~/.databrickscfg`
- Python packages: `databricks-sdk`, `pyyaml`

### Setup

```bash
pip install databricks-sdk pyyaml
```

## Usage

### Interactive Mode (Default)

Simply run the script and follow the prompts:

```bash
python generate_schema_yaml.py
```

The script will ask you for:
1. **Catalog name** (default: `workspace`)
2. **Schema name** (default: `reportingbus`)
3. **Path to relationships CSV file** (default: `tablerel/semanticmdlrel.csv`)
4. **Output YAML file path** (auto-generated: `{catalog}_{schema}_schema.yaml`)

### Example Interactive Session

```
============================================================
  Databricks Schema YAML Generator with Relationships
============================================================

Enter catalog name [workspace]: workspace
Enter schema name [reportingbus]: reportingbus
Enter path to relationships CSV file [tablerel/semanticmdlrel.csv]: tablerel/semanticmdlrel.csv
Enter output YAML file path [workspace_reportingbus_schema.yaml]: 

============================================================
Configuration:
  Catalog: workspace
  Schema: reportingbus
  Relationships CSV: tablerel/semanticmdlrel.csv
  Output YAML: workspace_reportingbus_schema.yaml
============================================================

Generating schema YAML for workspace.reportingbus...
✓ Discovered 6 tables in workspace.reportingbus
✓ Loaded 5 relationships from tablerel/semanticmdlrel.csv
✓ Added 5 relationships to schema
✓ Generated YAML: workspace_reportingbus_schema.yaml

============================================================
✓ Complete! YAML generated successfully
============================================================
```

### Using Defaults

Press Enter at each prompt to use the default values:

```bash
python generate_schema_yaml.py
# Just press Enter 4 times to use all defaults
```

## Output Format

The script generates a YAML with tables, columns, and relationships:

```yaml
version: '1.0'
catalog: workspace
schema: reportingbus
generated_at: '2026-05-19T09:51:19.596703'
tables:
- name: goals_by_day
  columns:
  - name: REPKEY
    type: string
  - name: DIRECTORKEY
    type: string
  - name: TARGETENROLLMENTS
    type: bigint
- name: performance_by_day
  columns:
  - name: REPKEY
    type: string
  - name: ENROLLMENTS
    type: bigint

relationships:
- name: goals_by_day_to_performance_by_day
  from_table: goals_by_day
  from_column: REPKEYDAY
  to_table: performance_by_day
  to_column: REPKEY
  cardinality: Many to One
- name: goals_by_day_to_calendar_by_day
  from_table: goals_by_day
  from_column: TARGETDAY
  to_table: calendar_by_day
  to_column: DATEVALUEDAY
  cardinality: Many to One
```

## Relationships CSV Format

The relationships are loaded from a CSV file with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `TableA` | Source table name | `goals_by_day` |
| `ColumnA` | Source column name | `REPKEYDAY` |
| `TableB` | Target table name | `performance_by_day` |
| `ColumnB` | Target column name | `REPKEY` |
| `Cardinality` | Relationship type | `Many to One` or `One to Many` |

### Example CSV (tablerel/semanticmdlrel.csv)

```csv
TableA,ColumnA,TableB,ColumnB,Cardinality
goals_by_day,DIRECTORKEYDAY,director_goals_by_day,DIRECTORKEYDAY,Many to One
goals_by_day,REPKEYDAY,performance_by_day,REPKEY,Many to One
goals_by_day,TARGETDAY,calendar_by_day,DATEVALUEDAY,Many to One
detailes,ENROLLDATE,calendar_by_day,DAILYDATE,Many to One
```

## Features

✅ **Interactive Input**: Simple CLI prompts for all parameters  
✅ **Automatic Discovery**: Introspects all tables in a schema  
✅ **Column Metadata**: Captures column names and Databricks data types  
✅ **Relationship Mapping**: Loads relationships from CSV and includes them in YAML  
✅ **dbt-Compatible**: YAML format similar to dbt's schema definitions  
✅ **Minimal & Clean**: Focuses on essentials (tables, columns, types, relationships)  
✅ **Reusable**: Run anytime to refresh schema metadata  
✅ **Error Handling**: Graceful error reporting with traceback details  
✅ **Smart Defaults**: Press Enter to use sensible defaults  

## Error Handling

If the script encounters errors, it will:

1. Display an error message with details
2. Show a full traceback for debugging
3. Exit with a non-zero status code

Common issues:

- **Catalog/Schema not found**: Verify the catalog and schema exist in your workspace
- **Relationships file not found**: The script will warn but continue without relationships
- **Authentication failed**: Check your Databricks configuration in `~/.databrickscfg`
- **Missing packages**: Install required packages with `pip install databricks-sdk pyyaml`

## Integration with dbt

To use this schema YAML with dbt:

1. Run the generator:
   ```bash
   python generate_schema_yaml.py
   # Follow prompts to generate YAML
   ```

2. Include the generated YAML in your dbt project's `models/` directory or reference it in your dbt_project.yml

## Automation

To automatically regenerate the schema YAML daily:

### macOS/Linux (crontab)

```bash
# Add this to crontab (crontab -e)
0 2 * * * cd /path/to/project && echo -e "workspace\nreportingbus\ntablerel/semanticmdlrel.csv\n" | python generate_schema_yaml.py
```

### Windows (Task Scheduler)

Create a batch file `run_schema_gen.bat`:
```batch
@echo off
cd "C:\path\to\project"
(
  echo workspace
  echo reportingbus
  echo tablerel/semanticmdlrel.csv
  echo.
) | python generate_schema_yaml.py
```

Then schedule this batch file to run daily using Task Scheduler.

## Troubleshooting

**Issue**: Script hangs or runs slowly

- Ensure your Databricks workspace is responsive
- Large schemas with many tables may take longer
- Check your internet connection to Databricks

**Issue**: Permission denied errors

- Verify your Databricks token/credentials have access to the catalog and schema
- Check Unity Catalog permissions in your workspace
- Run `databricks --profile YOUR_PROFILE workspace list` to verify auth

**Issue**: "Relationships file not found"

- Verify the CSV file path is correct relative to the current working directory
- Use absolute paths if running from different directories
- The script will continue without relationships if CSV is missing

**Issue**: "Catalog/schema not found"

- List available catalogs and schemas first:
  ```bash
  python -c "from databricks.sdk import WorkspaceClient; client = WorkspaceClient(); print([c.name for c in client.catalogs.list()])"
  ```

**Issue**: Special characters in input

- Avoid special shell characters in catalog/schema names
- Use standard alphanumeric characters and underscores

## License

Created for Databricks schema documentation

## Support

For issues with the Databricks SDK or workspace connection, refer to:
- [Databricks SDK for Python Documentation](https://databricks-sdk-py.readthedocs.io/)
- [Databricks Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
