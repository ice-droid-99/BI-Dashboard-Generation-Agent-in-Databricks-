#!/usr/bin/env python3
"""
Auto-discover Databricks schema and generate YAML documentation with relationships.

Interactive script that prompts for catalog, schema, and relationships CSV path,
then generates a dbt-style YAML file.

Usage:
    python generate_schema_yaml.py

The script will prompt for:
    1. Databricks catalog name (default: workspace)
    2. Schema name (default: reportingbus)
    3. Path to relationships CSV (default: tablerel/semanticmdlrel.csv)
    
Output is automatically saved to: finalsemantic/{catalog}_{schema}_schema.yaml
    
Requirements:
    - databricks-sdk: pip install databricks-sdk
    - pyyaml: pip install pyyaml
    - Databricks workspace connection via ~/.databrickscfg or environment variables
"""

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from databricks.sdk import WorkspaceClient


def get_user_input(prompt: str, default: str = "") -> str:
    """
    Get user input with optional default value.
    
    Args:
        prompt: Prompt text to display
        default: Default value if user presses Enter
    
    Returns:
        User input or default value
    """
    if default:
        display_prompt = f"{prompt} [{default}]: "
    else:
        display_prompt = f"{prompt}: "
    
    user_input = input(display_prompt).strip()
    return user_input if user_input else default


def load_relationships(relationships_file: str) -> list[dict]:
    """
    Load relationship definitions from CSV file.
    
    Args:
        relationships_file: Path to CSV file with relationships
    
    Returns:
        List of relationship dictionaries
    """
    relationships = []
    
    try:
        csv_path = Path(relationships_file)
        if not csv_path.exists():
            print(f"⚠ Relationships file not found: {relationships_file}")
            print("Continuing without relationships...")
            return relationships
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row and row.get('TableA'):  # Skip empty rows
                    relationships.append({
                        "name": f"{row['TableA'].lower()}_to_{row['TableB'].lower()}",
                        "from_table": row['TableA'],
                        "from_column": row['ColumnA'],
                        "to_table": row['TableB'],
                        "to_column": row['ColumnB'],
                        "cardinality": row.get('Cardinality', 'unknown'),
                    })
        
        print(f"✓ Loaded {len(relationships)} relationships from {relationships_file}")
        return relationships
    
    except Exception as e:
        print(f"⚠ Error loading relationships: {e}")
        print("Continuing without relationships...")
        return relationships


def fetch_schema_metadata(catalog: str, schema: str) -> dict[str, Any]:
    """
    Connect to Databricks and fetch table/column metadata for a schema.
    
    Args:
        catalog: Catalog name (e.g., 'workspace')
        schema: Schema name (e.g., 'reportingbus')
    
    Returns:
        Dictionary with schema metadata including tables and columns
    """
    client = WorkspaceClient()
    
    # Initialize result structure
    schema_data = {
        "version": "1.0",
        "catalog": catalog,
        "schema": schema,
        "generated_at": datetime.now().isoformat(),
        "tables": [],
        "relationships": [],
    }
    
    try:
        # List all tables in the schema using catalog API
        tables_list = client.tables.list(
            catalog_name=catalog,
            schema_name=schema,
        )
        
        # Process each table
        for table in tables_list:
            # Get table details including columns
            table_detail = client.tables.get(
                full_name=f"{catalog}.{schema}.{table.name}"
            )
            
            # Build table entry with columns
            table_entry = {
                "name": table.name,
                "columns": [],
            }
            
            # Extract columns from table metadata
            if table_detail.columns:
                for col in table_detail.columns:
                    column_entry = {
                        "name": col.name,
                        "type": col.type_text or str(col.type_json),
                    }
                    table_entry["columns"].append(column_entry)
            
            schema_data["tables"].append(table_entry)
        
        print(f"✓ Discovered {len(schema_data['tables'])} tables in {catalog}.{schema}")
        return schema_data
    
    except Exception as e:
        print(f"✗ Error fetching schema metadata: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise


def add_relationships_to_schema(schema_data: dict, relationships: list[dict]) -> dict:
    """
    Add relationships to schema data.
    
    Args:
        schema_data: Schema dictionary from fetch_schema_metadata
        relationships: List of relationship dicts from load_relationships
    
    Returns:
        Updated schema_data with relationships
    """
    schema_data["relationships"] = relationships
    if relationships:
        print(f"✓ Added {len(relationships)} relationships to schema")
    return schema_data


def generate_yaml_file(schema_data: dict[str, Any], output_file: str) -> None:
    """
    Write schema metadata to a YAML file.
    
    Args:
        schema_data: Dictionary with schema metadata
        output_file: Path to output YAML file
    """
    try:
        output_path = Path(output_file)
        
        # Ensure finalsemantic directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Delete existing file if it exists
        if output_path.exists():
            output_path.unlink()
            print(f"✓ Deleted existing file: {output_file}")
        
        # Write new YAML file
        with open(output_path, "w") as f:
            yaml.dump(schema_data, f, default_flow_style=False, sort_keys=False)
        print(f"✓ Generated YAML: {output_file}")
    except Exception as e:
        print(f"✗ Error writing YAML file: {e}", file=sys.stderr)
        raise


def main():
    """Interactive main function that prompts for user input."""
    
    print("\n" + "="*60)
    print("  Databricks Schema YAML Generator with Relationships")
    print("="*60 + "\n")
    
    # Prompt for catalog
    catalog = get_user_input(
        "Enter catalog name",
        default="workspace"
    )
    
    # Prompt for schema
    schema = get_user_input(
        "Enter schema name",
        default="reportingbus"
    )
    
    # Prompt for relationships file
    relationships_file = get_user_input(
        "Enter path to relationships CSV file",
        default="tablerel/semanticmdlrel.csv"
    )
    
    # Generate output filename in finalsemantic folder (no prompt)
    finalsemantic_dir = Path("finalsemantic")
    finalsemantic_dir.mkdir(exist_ok=True)
    output_file = str(finalsemantic_dir / f"{catalog}_{schema}_schema.yaml")
    
    print(f"\n{'='*60}")
    print(f"Configuration:")
    print(f"  Catalog: {catalog}")
    print(f"  Schema: {schema}")
    print(f"  Relationships CSV: {relationships_file}")
    print(f"  Output YAML: {output_file}")
    print(f"{'='*60}\n")
    
    print(f"Generating schema YAML for {catalog}.{schema}...\n")
    
    try:
        # Fetch metadata and generate YAML
        schema_data = fetch_schema_metadata(catalog, schema)
        
        # Load and add relationships
        relationships = load_relationships(relationships_file)
        schema_data = add_relationships_to_schema(schema_data, relationships)
        
        # Generate YAML file
        generate_yaml_file(schema_data, output_file)
        
        print(f"\n{'='*60}")
        print(f"✓ Complete! YAML generated successfully")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ Generation failed: {e}")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
