# Measure Name Ambiguity

Avoid generic measure names that hide the business logic.

Common ambiguity patterns:

- gross vs net
- booked vs realized
- raw vs filtered
- per-order vs per-customer
- current-period vs lifetime

Rules:

1. If a measure name sounds generic, reserve it for the business-default interpretation used in dashboard prompts.
2. Put alternative formulas under explicit names.
3. Do not reuse one measure name for multiple business meanings.
