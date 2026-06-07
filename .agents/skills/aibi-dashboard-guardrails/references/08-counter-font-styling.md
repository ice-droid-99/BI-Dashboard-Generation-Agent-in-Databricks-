# Counter Widget Font Styling

## Rule

**ALL counter widgets MUST use bold font styling for numeric values.**

## Implementation

Add the `style` property to `encodings.value` in every counter widget:

```json
"encodings": {
  "value": {
    "fieldName": "metric_name",
    "displayName": "Display Name",
    "style": {
      "fontStyle": "bold"
    },
    "format": {
      "type": "number-currency",
      "currencyCode": "USD"
    }
  }
}
```

## Complete Examples

### Currency Counter
```json
{
  "widget": {
    "name": "total-revenue",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "revenue_ds",
        "fields": [{"name": "revenue", "expression": "`revenue`"}],
        "disaggregated": true
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "counter",
      "encodings": {
        "value": {
          "fieldName": "revenue",
          "displayName": "Total Revenue",
          "style": {
            "fontStyle": "bold"
          },
          "format": {
            "type": "number-currency",
            "currencyCode": "USD",
            "abbreviation": "compact",
            "decimalPlaces": {"type": "max", "places": 2}
          }
        }
      },
      "frame": {"showTitle": true, "title": "Total Revenue"}
    }
  },
  "position": {"x": 0, "y": 0, "width": 4, "height": 3}
}
```

### Percentage Counter
```json
{
  "widget": {
    "name": "conversion-rate",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "metrics_ds",
        "fields": [{"name": "rate", "expression": "`conversion_rate`"}],
        "disaggregated": true
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "counter",
      "encodings": {
        "value": {
          "fieldName": "rate",
          "displayName": "Conversion Rate",
          "style": {
            "fontStyle": "bold"
          },
          "format": {
            "type": "number-percent",
            "decimalPlaces": {"type": "max", "places": 1}
          }
        }
      },
      "frame": {"showTitle": true, "title": "Conversion Rate"}
    }
  },
  "position": {"x": 4, "y": 0, "width": 4, "height": 3}
}
```

### Integer Counter
```json
{
  "widget": {
    "name": "total-orders",
    "queries": [{
      "name": "main_query",
      "query": {
        "datasetName": "orders_ds",
        "fields": [{"name": "count", "expression": "`order_count`"}],
        "disaggregated": true
      }
    }],
    "spec": {
      "version": 2,
      "widgetType": "counter",
      "encodings": {
        "value": {
          "fieldName": "count",
          "displayName": "Total Orders",
          "style": {
            "fontStyle": "bold"
          },
          "format": {
            "type": "number",
            "abbreviation": "compact",
            "decimalPlaces": {"type": "max", "places": 0}
          }
        }
      },
      "frame": {"showTitle": true, "title": "Total Orders"}
    }
  },
  "position": {"x": 8, "y": 0, "width": 4, "height": 3}
}
```

## Common Mistakes

### ❌ Missing Style Property
```json
"encodings": {
  "value": {
    "fieldName": "revenue",
    "displayName": "Revenue",
    "format": {"type": "number-currency", "currencyCode": "USD"}
  }
}
```

### ✅ Correct Implementation
```json
"encodings": {
  "value": {
    "fieldName": "revenue",
    "displayName": "Revenue",
    "style": {
      "fontStyle": "bold"
    },
    "format": {"type": "number-currency", "currencyCode": "USD"}
  }
}
```

## Validation Checklist

Before deploying any dashboard with counter widgets:

- [ ] Every counter widget has `"widgetType": "counter"`
- [ ] Every counter has `encodings.value.style.fontStyle` set to `"bold"`
- [ ] The `style` property appears before `format` (for consistency)
- [ ] Counter widgets use `version: 2`
- [ ] Counter widgets have minimum dimensions (width ≥ 4, height ≥ 3)

## Why This Matters

Bold font styling for counter widgets:
- **Improves readability** - Makes KPI values stand out
- **Enhances visual hierarchy** - Draws attention to key metrics
- **Maintains consistency** - Ensures uniform styling across dashboards
- **Follows best practices** - Aligns with standard dashboard design

## Agent Behavior

When generating or updating dashboards:

1. **ALWAYS** include `style.fontStyle: "bold"` in counter widgets
2. Apply to ALL counters regardless of format type (currency, percent, number)
3. Place `style` before `format` for readability
4. Never omit this styling - it is MANDATORY

---

**Remember**: Every counter widget = Bold numeric values. No exceptions!
