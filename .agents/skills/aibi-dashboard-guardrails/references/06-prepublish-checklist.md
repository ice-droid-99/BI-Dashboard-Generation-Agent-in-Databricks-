# Pre-Publish Checklist

Run this checklist before publishing any dashboard update.

## Formula checks

- Confirm every KPI denominator.
- Confirm every gross-vs-net or filtered-vs-unfiltered choice.
- Confirm every rate formula against the prompt.

## Dataset checks

- Confirm raw datasets remain calculation-friendly.
- Confirm display datasets exist only where presentation-specific output is required.
- Confirm any top-N or ranked datasets truly isolate the intended result.

## Display checks

- Confirm labels match the requested style.
- Confirm debt, revenue, or volume uses the expected unit style.
- Confirm totals rows use the expected label and aggregation.
- Confirm thresholds or status markers match the prompt.

## Validation checks

- Execute the SQL for every changed dataset.
- If the user gave expected values, compare against them explicitly.
- Publish only after the comparison passes.
