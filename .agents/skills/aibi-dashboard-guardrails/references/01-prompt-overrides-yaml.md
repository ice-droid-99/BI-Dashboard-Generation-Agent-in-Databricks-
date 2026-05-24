# Prompt Overrides YAML

Use this rule first:

- If the user defines a KPI formula, display rule, or business interpretation in the prompt, use that definition even if a semantic YAML defines something different.

Do not silently follow YAML when it conflicts with the prompt.

Required behavior:

1. Identify the conflict explicitly.
2. Implement the prompt definition.
3. Update the semantic file if that file would mislead future work.
