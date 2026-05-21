---
name: aibi-dashboard-guardrails
description: Prevent repeated mistakes when building or updating Databricks AI/BI dashboards from semantic YAML files, schema definitions, and user requirements. Use when working on dashboard KPIs, display tables, formatting rules, prompt-vs-YAML conflicts, or cross-checking user-supplied expected values.
---

# AI/BI Dashboard Guardrails

Apply these rules before changing any dashboard.

## Core rules

1. Treat the user's prompt as the highest-priority source of truth.
2. Treat schema and semantic YAML files as supporting context, not override authority.
3. Validate every KPI formula with explicit SQL before publishing.
4. If the user gives expected values, cross-check the dashboard against those values before publishing.
5. Separate raw metric datasets from display-shaped reporting datasets when the user expects rounded, formatted, or decorated table values.

## Read these references as needed

- For prompt vs YAML conflicts: [references/01-prompt-overrides-yaml.md](references/01-prompt-overrides-yaml.md)
- For ambiguous measure names: [references/02-measure-name-ambiguity.md](references/02-measure-name-ambiguity.md)
- For display tables vs raw datasets: [references/03-display-vs-raw-datasets.md](references/03-display-vs-raw-datasets.md)
- For unit and formatting mistakes: [references/04-formatting-and-units.md](references/04-formatting-and-units.md)
- For user-provided cross-check tables: [references/05-cross-check-procedure.md](references/05-cross-check-procedure.md)
- For pre-publish workflow: [references/06-prepublish-checklist.md](references/06-prepublish-checklist.md)

## Mandatory behavior

- State any prompt-vs-YAML conflict explicitly before implementing.
- If a measure name is ambiguous, clarify whether it is gross, net, filtered, cumulative, or display-only.
- Do not assume compact currency formatting is acceptable. Check the requested presentation first.
- Use display-shaped datasets only when the user expects presentation-ready table values rather than raw numeric fields.

## Output discipline

- When correcting a dashboard, say whether the fix is formula-only, formatting-only, dataset-only, or validation-related.
- Publish only after SQL validation and final business-value cross-checks are complete.
