import json
from pathlib import Path


def number_format(decimal_places=0, abbreviation="compact"):
    fmt = {
        "type": "number",
        "decimalPlaces": {"type": "max", "places": decimal_places},
    }
    if abbreviation:
        fmt["abbreviation"] = abbreviation
    return fmt


def currency_format(decimal_places=1, abbreviation="compact"):
    fmt = {
        "type": "number-currency",
        "currencyCode": "USD",
        "decimalPlaces": {"type": "max", "places": decimal_places},
    }
    if abbreviation:
        fmt["abbreviation"] = abbreviation
    return fmt


def percent_format(decimal_places=1):
    return {
        "type": "number-percent",
        "decimalPlaces": {"type": "max", "places": decimal_places},
    }


overview_fact_query = """
WITH team_map AS (
  SELECT TARGETDATE, REP, MAX(TEAM) AS TEAM
  FROM workspace.reportingbus.goals_by_day
  GROUP BY TARGETDATE, REP
)
SELECT
  c.DAILYDATE AS daily_date,
  DATE_TRUNC('MONTH', c.DAILYDATE) AS month_start,
  DATE_FORMAT(c.DAILYDATE, 'MMM yyyy') AS month_label,
  tm.TEAM AS team,
  p.ORIGINALREP AS rep,
  p.ENROLLMENTS AS gross_enrollments,
  p.NETENROLLMENTS AS net_enrollments,
  p.TOTALDEBT AS gross_enrolled_debt,
  p.NETDEBT AS net_enrolled_debt,
  p.EARLYCANCELLATION AS early_cancellations,
  p.CANCELLEDDEBT AS cancelled_debt
FROM workspace.reportingbus.performance_by_day p
JOIN workspace.reportingbus.calendar_by_day c
  ON p.RANKDAYVALUE = c.DATEVALUEDAY
LEFT JOIN team_map tm
  ON p.RANKDATEVALUE = tm.TARGETDATE
 AND p.ORIGINALREP = tm.REP
""".strip()


cancel_fact_query = """
WITH team_map AS (
  SELECT TARGETDATE, REP, MAX(TEAM) AS TEAM
  FROM workspace.reportingbus.goals_by_day
  GROUP BY TARGETDATE, REP
)
SELECT
  e.EnrollDate AS daily_date,
  DATE_TRUNC('MONTH', e.EnrollDate) AS month_start,
  DATE_FORMAT(e.EnrollDate, 'MMM yyyy') AS month_label,
  tm.TEAM AS team,
  e.SaleRep AS rep,
  e.CANCELREASON AS cancel_reason,
  e.EarlyCancellation AS early_cancellations,
  e.DaysToCancel AS days_to_cancel
FROM workspace.reportingbus.early_cancellation e
LEFT JOIN team_map tm
  ON e.Date = tm.TARGETDATE
 AND e.SaleRep = tm.REP
""".strip()


monthly_goals_query = """
WITH months AS (
  SELECT DATEVALUE AS month_key, MIN(DAILYDATE) AS month_start, DATE_FORMAT(MIN(DAILYDATE), 'MMM yyyy') AS month_label
  FROM workspace.reportingbus.calendar_by_day
  GROUP BY DATEVALUE
),
goals AS (
  SELECT TARGETDATE AS month_key, SUM(TARGETENROLLMENTS) AS enrollment_target, SUM(TARGETDEBT) AS debt_target
  FROM workspace.reportingbus.goals_by_day
  GROUP BY TARGETDATE
),
perf AS (
  SELECT RANKDATEVALUE AS month_key, SUM(NETENROLLMENTS) AS actual_net_enrollments, SUM(NETDEBT) AS actual_net_debt
  FROM workspace.reportingbus.performance_by_day
  GROUP BY RANKDATEVALUE
),
base AS (
  SELECT
    m.month_start,
    m.month_label,
    COALESCE(g.enrollment_target, 0) AS enrollment_target,
    COALESCE(p.actual_net_enrollments, 0) AS actual_net_enrollments,
    COALESCE(p.actual_net_enrollments, 0) / NULLIF(COALESCE(g.enrollment_target, 0), 0) AS enrollment_achievement_pct,
    COALESCE(g.debt_target, 0) AS debt_target,
    COALESCE(p.actual_net_debt, 0) AS actual_net_debt,
    COALESCE(p.actual_net_debt, 0) / NULLIF(COALESCE(g.debt_target, 0), 0) AS debt_achievement_pct
  FROM months m
  LEFT JOIN goals g
    ON m.month_key = g.month_key
  LEFT JOIN perf p
    ON m.month_key = p.month_key
)
SELECT
  month_start,
  month_label,
  enrollment_target,
  actual_net_enrollments,
  enrollment_achievement_pct,
  debt_target,
  actual_net_debt,
  debt_achievement_pct,
  0 AS sort_key
FROM base
UNION ALL
SELECT
  NULL AS month_start,
  'Total' AS month_label,
  SUM(enrollment_target) AS enrollment_target,
  SUM(actual_net_enrollments) AS actual_net_enrollments,
  SUM(actual_net_enrollments) / NULLIF(SUM(enrollment_target), 0) AS enrollment_achievement_pct,
  SUM(debt_target) AS debt_target,
  SUM(actual_net_debt) AS actual_net_debt,
  SUM(actual_net_debt) / NULLIF(SUM(debt_target), 0) AS debt_achievement_pct,
  1 AS sort_key
FROM base
ORDER BY sort_key, month_start
""".strip()


rep_scorecard_query = """
WITH team_map AS (
  SELECT REP, MAX(TEAM) AS TEAM
  FROM workspace.reportingbus.goals_by_day
  GROUP BY REP
),
cancel_stats AS (
  SELECT SaleRep AS rep, AVG(DaysToCancel) AS avg_days_to_cancel
  FROM workspace.reportingbus.early_cancellation
  GROUP BY SaleRep
)
SELECT
  p.ORIGINALREP AS rep_name,
  tm.TEAM AS team,
  SUM(p.ENROLLMENTS) AS gross_enrollments,
  SUM(p.NETENROLLMENTS) AS net_enrollments,
  SUM(p.TOTALDEBT) AS gross_debt,
  SUM(p.TOTALDEBT) / NULLIF(SUM(p.ENROLLMENTS), 0) AS avg_debt_per_enrollment,
  SUM(p.EARLYCANCELLATION) AS early_cancellations,
  SUM(p.EARLYCANCELLATION) / NULLIF(SUM(p.ENROLLMENTS), 0) AS cancel_rate_pct,
  cs.avg_days_to_cancel
FROM workspace.reportingbus.performance_by_day p
LEFT JOIN team_map tm
  ON p.ORIGINALREP = tm.REP
LEFT JOIN cancel_stats cs
  ON p.ORIGINALREP = cs.rep
GROUP BY p.ORIGINALREP, tm.TEAM, cs.avg_days_to_cancel
ORDER BY net_enrollments DESC, rep_name
""".strip()


monthly_goals_display_query = """
WITH months AS (
  SELECT DATEVALUE AS month_key, MIN(DAILYDATE) AS month_start, DATE_FORMAT(MIN(DAILYDATE), 'MMM yyyy') AS month_label
  FROM workspace.reportingbus.calendar_by_day
  GROUP BY DATEVALUE
),
goals AS (
  SELECT TARGETDATE AS month_key, SUM(TARGETENROLLMENTS) AS enrollment_target, SUM(TARGETDEBT) AS debt_target
  FROM workspace.reportingbus.goals_by_day
  GROUP BY TARGETDATE
),
perf AS (
  SELECT RANKDATEVALUE AS month_key, SUM(NETENROLLMENTS) AS actual_net_enrollments, SUM(NETDEBT) AS actual_net_debt
  FROM workspace.reportingbus.performance_by_day
  GROUP BY RANKDATEVALUE
),
base AS (
  SELECT
    m.month_start,
    m.month_label,
    COALESCE(g.enrollment_target, 0) AS enrollment_target_value,
    COALESCE(p.actual_net_enrollments, 0) AS actual_net_enrollments_value,
    COALESCE(p.actual_net_enrollments, 0) / NULLIF(COALESCE(g.enrollment_target, 0), 0) AS enrollment_achievement_value,
    COALESCE(g.debt_target, 0) AS debt_target_value,
    COALESCE(p.actual_net_debt, 0) AS actual_net_debt_value,
    COALESCE(p.actual_net_debt, 0) / NULLIF(COALESCE(g.debt_target, 0), 0) AS debt_achievement_value,
    0 AS sort_key
  FROM months m
  LEFT JOIN goals g
    ON m.month_key = g.month_key
  LEFT JOIN perf p
    ON m.month_key = p.month_key
),
all_rows AS (
  SELECT * FROM base
  UNION ALL
  SELECT
    NULL AS month_start,
    'TOTAL' AS month_label,
    SUM(enrollment_target_value) AS enrollment_target_value,
    SUM(actual_net_enrollments_value) AS actual_net_enrollments_value,
    SUM(actual_net_enrollments_value) / NULLIF(SUM(enrollment_target_value), 0) AS enrollment_achievement_value,
    SUM(debt_target_value) AS debt_target_value,
    SUM(actual_net_debt_value) AS actual_net_debt_value,
    SUM(actual_net_debt_value) / NULLIF(SUM(debt_target_value), 0) AS debt_achievement_value,
    1 AS sort_key
  FROM base
)
SELECT
  month_label,
  FORMAT_NUMBER(enrollment_target_value, 0) AS enrollment_target,
  FORMAT_NUMBER(actual_net_enrollments_value, 0) AS actual_net_enrollments,
  CONCAT(FORMAT_NUMBER(ROUND(enrollment_achievement_value * 100, 1), 1), '%') AS enrollment_achievement_pct,
  CONCAT('$', FORMAT_NUMBER(ROUND(debt_target_value / 1000000.0, 0), 0), 'M') AS debt_target,
  CONCAT('$', FORMAT_NUMBER(ROUND(actual_net_debt_value / 1000000.0, 1), 1), 'M') AS actual_net_debt,
  CONCAT(FORMAT_NUMBER(ROUND(debt_achievement_value * 100, 1), 1), '%') AS debt_achievement_pct,
  sort_key,
  month_start
FROM all_rows
ORDER BY sort_key, month_start
""".strip()


rep_scorecard_display_query = """
WITH team_map AS (
  SELECT REP, MAX(TEAM) AS TEAM
  FROM workspace.reportingbus.goals_by_day
  GROUP BY REP
),
cancel_stats AS (
  SELECT SaleRep AS rep, AVG(DaysToCancel) AS avg_days_to_cancel
  FROM workspace.reportingbus.early_cancellation
  GROUP BY SaleRep
),
base AS (
  SELECT
    p.ORIGINALREP AS rep_name,
    tm.TEAM AS team,
    SUM(p.ENROLLMENTS) AS gross_enrollments_value,
    SUM(p.NETENROLLMENTS) AS net_enrollments_value,
    SUM(p.TOTALDEBT) AS gross_debt_value,
    SUM(p.TOTALDEBT) / NULLIF(SUM(p.ENROLLMENTS), 0) AS avg_debt_per_enrollment_value,
    SUM(p.EARLYCANCELLATION) AS early_cancellations_value,
    SUM(p.EARLYCANCELLATION) / NULLIF(SUM(p.ENROLLMENTS), 0) AS cancel_rate_value,
    ROUND(cs.avg_days_to_cancel, 1) AS avg_days_to_cancel_value
  FROM workspace.reportingbus.performance_by_day p
  LEFT JOIN team_map tm
    ON p.ORIGINALREP = tm.REP
  LEFT JOIN cancel_stats cs
    ON p.ORIGINALREP = cs.rep
  GROUP BY p.ORIGINALREP, tm.TEAM, cs.avg_days_to_cancel
)
SELECT
  rep_name,
  team,
  FORMAT_NUMBER(gross_enrollments_value, 0) AS gross_enrollments,
  FORMAT_NUMBER(net_enrollments_value, 0) AS net_enrollments,
  CONCAT('$', FORMAT_NUMBER(ROUND(gross_debt_value / 1000000.0, 1), 1), 'M') AS gross_debt,
  CONCAT('$', FORMAT_NUMBER(ROUND(avg_debt_per_enrollment_value, 0), 0)) AS avg_debt_per_enrollment,
  FORMAT_NUMBER(early_cancellations_value, 0) AS early_cancellations,
  CONCAT(
    FORMAT_NUMBER(ROUND(cancel_rate_value * 100, 1), 1),
    '% ',
    CASE
      WHEN cancel_rate_value < 0.05 THEN '🟢'
      WHEN cancel_rate_value <= 0.10 THEN '🟡'
      ELSE '🔴'
    END
  ) AS cancel_rate_pct,
  FORMAT_NUMBER(avg_days_to_cancel_value, 1) AS avg_days_to_cancel,
  net_enrollments_value
FROM base
ORDER BY net_enrollments_value DESC, rep_name
""".strip()


top_team_query = """
SELECT
  team,
  net_enrollments
FROM (
  SELECT
    team,
    SUM(net_enrollments) AS net_enrollments,
    ROW_NUMBER() OVER (ORDER BY SUM(net_enrollments) DESC, team ASC) AS rn
  FROM (
    WITH team_map AS (
      SELECT TARGETDATE, REP, MAX(TEAM) AS TEAM
      FROM workspace.reportingbus.goals_by_day
      GROUP BY TARGETDATE, REP
    )
    SELECT
      tm.TEAM AS team,
      p.NETENROLLMENTS AS net_enrollments
    FROM workspace.reportingbus.performance_by_day p
    LEFT JOIN team_map tm
      ON p.RANKDATEVALUE = tm.TARGETDATE
     AND p.ORIGINALREP = tm.REP
  ) base
  GROUP BY team
) ranked
WHERE rn = 1
""".strip()


dashboard = {
    "datasets": [
        {
            "name": "overview_fact_ds",
            "displayName": "Overview Fact",
            "queryLines": [overview_fact_query],
        },
        {
            "name": "cancel_fact_ds",
            "displayName": "Cancellation Fact",
            "queryLines": [cancel_fact_query],
        },
        {
            "name": "monthly_goals_ds",
            "displayName": "Monthly Goals",
            "queryLines": [monthly_goals_query],
        },
        {
            "name": "rep_scorecard_ds",
            "displayName": "Rep Scorecard",
            "queryLines": [rep_scorecard_query],
        },
        {
            "name": "monthly_goals_display_ds",
            "displayName": "Monthly Goals Display",
            "queryLines": [monthly_goals_display_query],
        },
        {
            "name": "rep_scorecard_display_ds",
            "displayName": "Rep Scorecard Display",
            "queryLines": [rep_scorecard_display_query],
        },
        {
            "name": "top_team_ds",
            "displayName": "Top Team",
            "queryLines": [top_team_query],
        },
    ],
    "pages": [
        {
            "name": "overview_page",
            "displayName": "Overview",
            "pageType": "PAGE_TYPE_CANVAS",
            "layoutVersion": "GRID_V1",
            "layout": [
                {
                    "widget": {
                        "name": "final_title",
                        "multilineTextboxSpec": {
                            "lines": ["# Final"]
                        },
                    },
                    "position": {"x": 0, "y": 0, "width": 12, "height": 1},
                },
                {
                    "widget": {
                        "name": "final_subtitle",
                        "multilineTextboxSpec": {
                            "lines": [
                                "Overview of enrollments, debt, cancellations, team mix, and rep drilldown. Use the exact-date and month filters independently or together."
                            ]
                        },
                    },
                    "position": {"x": 0, "y": 1, "width": 12, "height": 1},
                },
                {
                    "widget": {
                        "name": "filter_exact_date",
                        "queries": [
                            {
                                "name": "overview_daily_date",
                                "query": {
                                    "datasetName": "overview_fact_ds",
                                    "fields": [{"name": "daily_date", "expression": "`daily_date`"}],
                                    "disaggregated": False,
                                },
                            },
                            {
                                "name": "cancel_daily_date",
                                "query": {
                                    "datasetName": "cancel_fact_ds",
                                    "fields": [{"name": "daily_date", "expression": "`daily_date`"}],
                                    "disaggregated": False,
                                },
                            },
                        ],
                        "spec": {
                            "version": 2,
                            "widgetType": "filter-date-range-picker",
                            "encodings": {
                                "fields": [
                                    {"fieldName": "daily_date", "displayName": "Exact Date", "queryName": "overview_daily_date"},
                                    {"fieldName": "daily_date", "displayName": "Exact Date", "queryName": "cancel_daily_date"},
                                ]
                            },
                            "frame": {"showTitle": True, "title": "Exact Date"},
                        },
                    },
                    "position": {"x": 0, "y": 2, "width": 3, "height": 2},
                },
                {
                    "widget": {
                        "name": "filter_month_label",
                        "queries": [
                            {
                                "name": "overview_month_label",
                                "query": {
                                    "datasetName": "overview_fact_ds",
                                    "fields": [{"name": "month_label", "expression": "`month_label`"}],
                                    "disaggregated": False,
                                },
                            },
                            {
                                "name": "cancel_month_label",
                                "query": {
                                    "datasetName": "cancel_fact_ds",
                                    "fields": [{"name": "month_label", "expression": "`month_label`"}],
                                    "disaggregated": False,
                                },
                            },
                        ],
                        "spec": {
                            "version": 2,
                            "widgetType": "filter-multi-select",
                            "encodings": {
                                "fields": [
                                    {"fieldName": "month_label", "displayName": "Month", "queryName": "overview_month_label"},
                                    {"fieldName": "month_label", "displayName": "Month", "queryName": "cancel_month_label"},
                                ]
                            },
                            "frame": {"showTitle": True, "title": "Month (MMM YYYY)"},
                        },
                    },
                    "position": {"x": 3, "y": 2, "width": 3, "height": 2},
                },
                {
                    "widget": {
                        "name": "filter_team",
                        "queries": [
                            {
                                "name": "overview_team",
                                "query": {
                                    "datasetName": "overview_fact_ds",
                                    "fields": [{"name": "team", "expression": "`team`"}],
                                    "disaggregated": False,
                                },
                            },
                            {
                                "name": "cancel_team",
                                "query": {
                                    "datasetName": "cancel_fact_ds",
                                    "fields": [{"name": "team", "expression": "`team`"}],
                                    "disaggregated": False,
                                },
                            },
                        ],
                        "spec": {
                            "version": 2,
                            "widgetType": "filter-multi-select",
                            "encodings": {
                                "fields": [
                                    {"fieldName": "team", "displayName": "Team", "queryName": "overview_team"},
                                    {"fieldName": "team", "displayName": "Team", "queryName": "cancel_team"},
                                ]
                            },
                            "frame": {"showTitle": True, "title": "Team"},
                        },
                    },
                    "position": {"x": 6, "y": 2, "width": 3, "height": 2},
                },
                {
                    "widget": {
                        "name": "filter_rep",
                        "queries": [
                            {
                                "name": "overview_rep",
                                "query": {
                                    "datasetName": "overview_fact_ds",
                                    "fields": [{"name": "rep", "expression": "`rep`"}],
                                    "disaggregated": False,
                                },
                            },
                            {
                                "name": "cancel_rep",
                                "query": {
                                    "datasetName": "cancel_fact_ds",
                                    "fields": [{"name": "rep", "expression": "`rep`"}],
                                    "disaggregated": False,
                                },
                            },
                        ],
                        "spec": {
                            "version": 2,
                            "widgetType": "filter-multi-select",
                            "encodings": {
                                "fields": [
                                    {"fieldName": "rep", "displayName": "Rep", "queryName": "overview_rep"},
                                    {"fieldName": "rep", "displayName": "Rep", "queryName": "cancel_rep"},
                                ]
                            },
                            "frame": {"showTitle": True, "title": "Rep"},
                        },
                    },
                    "position": {"x": 9, "y": 2, "width": 3, "height": 2},
                },
                {
                    "widget": {
                        "name": "kpi_gross_enrollments",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{"name": "sum(gross_enrollments)", "expression": "SUM(`gross_enrollments`)"}],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "sum(gross_enrollments)",
                                    "displayName": "Total Gross Enrollments",
                                    "format": number_format(0),
                                }
                            },
                            "frame": {"title": "Gross Enrollments", "showTitle": True},
                        },
                    },
                    "position": {"x": 0, "y": 4, "width": 1, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_net_enrollments",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{"name": "sum(net_enrollments)", "expression": "SUM(`net_enrollments`)"}],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "sum(net_enrollments)",
                                    "displayName": "Total Net Enrollments",
                                    "format": number_format(0),
                                }
                            },
                            "frame": {"title": "Net Enrollments", "showTitle": True},
                        },
                    },
                    "position": {"x": 1, "y": 4, "width": 1, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_avg_daily_enrollments",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{
                                    "name": "avg_daily_enrollments",
                                    "expression": "SUM(`net_enrollments`) / NULLIF(COUNT(DISTINCT `daily_date`), 0)",
                                }],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "avg_daily_enrollments",
                                    "displayName": "Average Daily Enrollments",
                                    "format": number_format(1, None),
                                }
                            },
                            "frame": {"title": "Avg Daily Enrollments", "showTitle": True},
                        },
                    },
                    "position": {"x": 2, "y": 4, "width": 2, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_early_cancellations",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{"name": "sum(early_cancellations)", "expression": "SUM(`early_cancellations`)"}],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "sum(early_cancellations)",
                                    "displayName": "Early Cancellations",
                                    "format": number_format(0),
                                }
                            },
                            "frame": {"title": "Early Cancellations", "showTitle": True},
                        },
                    },
                    "position": {"x": 4, "y": 4, "width": 1, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_cancelled_debt_rate",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{
                                    "name": "cancelled_debt_rate",
                                    "expression": "SUM(`cancelled_debt`) / NULLIF(SUM(`gross_enrolled_debt`), 0)",
                                }],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "cancelled_debt_rate",
                                    "displayName": "Cancelled Debt Rate",
                                    "format": percent_format(1),
                                }
                            },
                            "frame": {"title": "Cancelled Debt Rate", "showTitle": True},
                        },
                    },
                    "position": {"x": 5, "y": 4, "width": 1, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_best_team",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "top_team_ds",
                                "fields": [
                                    {"name": "team", "expression": "`team`"},
                                    {"name": "net_enrollments", "expression": "`net_enrollments`"},
                                ],
                                "disaggregated": True,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "table",
                            "encodings": {
                                "columns": [
                                    {"fieldName": "team", "displayName": "Best Team"},
                                    {"fieldName": "net_enrollments", "displayName": "Net Enrollments"},
                                ]
                            },
                            "frame": {"title": "Best Performing Team", "showTitle": True},
                        },
                    },
                    "position": {"x": 6, "y": 4, "width": 2, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_avg_days_cancel",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "cancel_fact_ds",
                                "fields": [{"name": "avg(days_to_cancel)", "expression": "AVG(`days_to_cancel`)"}],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "avg(days_to_cancel)",
                                    "displayName": "Average Days to Cancel",
                                    "format": number_format(1, None),
                                }
                            },
                            "frame": {"title": "Avg Days to Cancel", "showTitle": True},
                        },
                    },
                    "position": {"x": 8, "y": 4, "width": 1, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_gross_debt",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{"name": "sum(gross_enrolled_debt)", "expression": "SUM(`gross_enrolled_debt`)"}],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "sum(gross_enrolled_debt)",
                                    "displayName": "Gross Enrolled Debt",
                                    "format": currency_format(0, None),
                                }
                            },
                            "frame": {"title": "Gross Enrolled Debt", "showTitle": True},
                        },
                    },
                    "position": {"x": 9, "y": 4, "width": 2, "height": 3},
                },
                {
                    "widget": {
                        "name": "kpi_avg_debt_per_enrollment",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [{
                                    "name": "avg_debt_per_enrollment",
                                    "expression": "SUM(`gross_enrolled_debt`) / NULLIF(SUM(`gross_enrollments`), 0)",
                                }],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "counter",
                            "encodings": {
                                "value": {
                                    "fieldName": "avg_debt_per_enrollment",
                                    "displayName": "Average Debt per Enrollment",
                                    "format": currency_format(0, None),
                                }
                            },
                            "frame": {"title": "Avg Debt per Enrollment", "showTitle": True},
                        },
                    },
                    "position": {"x": 11, "y": 4, "width": 1, "height": 3},
                },
                {
                    "widget": {
                        "name": "team_performance_chart",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "overview_fact_ds",
                                "fields": [
                                    {"name": "team", "expression": "`team`"},
                                    {"name": "sum(gross_enrollments)", "expression": "SUM(`gross_enrollments`)"},
                                    {"name": "sum(gross_enrolled_debt)", "expression": "SUM(`gross_enrolled_debt`)"},
                                ],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 3,
                            "widgetType": "bar",
                            "mark": {"layout": "group"},
                            "encodings": {
                                "x": {
                                    "fieldName": "team",
                                    "scale": {"type": "categorical"},
                                    "displayName": "Team",
                                },
                                "y": {
                                    "scale": {"type": "quantitative"},
                                    "fields": [
                                        {"fieldName": "sum(gross_enrollments)", "displayName": "Gross Enrollments"},
                                        {"fieldName": "sum(gross_enrolled_debt)", "displayName": "Gross Debt ($)"},
                                    ],
                                },
                            },
                            "frame": {"title": "Team Performance", "showTitle": True},
                        },
                    },
                    "position": {"x": 0, "y": 7, "width": 6, "height": 6},
                },
                {
                    "widget": {
                        "name": "cancellation_reason_donut",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "cancel_fact_ds",
                                "fields": [
                                    {"name": "cancel_reason", "expression": "`cancel_reason`"},
                                    {"name": "sum(early_cancellations)", "expression": "SUM(`early_cancellations`)"},
                                ],
                                "disaggregated": False,
                            },
                        }],
                        "spec": {
                            "version": 3,
                            "widgetType": "pie",
                            "encodings": {
                                "angle": {
                                    "fieldName": "sum(early_cancellations)",
                                    "scale": {"type": "quantitative"},
                                    "displayName": "Cancellation Count",
                                },
                                "color": {
                                    "fieldName": "cancel_reason",
                                    "scale": {"type": "categorical"},
                                    "displayName": "Cancellation Reason",
                                },
                                "label": {"show": True},
                            },
                            "frame": {"title": "Cancellation Breakdown by Reason", "showTitle": True},
                        },
                    },
                    "position": {"x": 6, "y": 7, "width": 6, "height": 6},
                },
            ],
        },
        {
            "name": "monthly_goals_page",
            "displayName": "Monthly Goals & Rep Performance",
            "pageType": "PAGE_TYPE_CANVAS",
            "layoutVersion": "GRID_V1",
            "layout": [
                {
                    "widget": {
                        "name": "monthly_title",
                        "multilineTextboxSpec": {
                            "lines": ["# Monthly Goals & Rep Performance"]
                        },
                    },
                    "position": {"x": 0, "y": 0, "width": 12, "height": 1},
                },
                {
                    "widget": {
                        "name": "monthly_subtitle",
                        "multilineTextboxSpec": {
                            "lines": ["Full-period management view for monthly goal attainment and rep quality metrics."]
                        },
                    },
                    "position": {"x": 0, "y": 1, "width": 12, "height": 1},
                },
                {
                    "widget": {
                        "name": "monthly_goals_table",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "monthly_goals_display_ds",
                                "fields": [
                                    {"name": "month_label", "expression": "`month_label`"},
                                    {"name": "enrollment_target", "expression": "`enrollment_target`"},
                                    {"name": "actual_net_enrollments", "expression": "`actual_net_enrollments`"},
                                    {"name": "enrollment_achievement_pct", "expression": "`enrollment_achievement_pct`"},
                                    {"name": "debt_target", "expression": "`debt_target`"},
                                    {"name": "actual_net_debt", "expression": "`actual_net_debt`"},
                                    {"name": "debt_achievement_pct", "expression": "`debt_achievement_pct`"},
                                ],
                                "disaggregated": True,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "table",
                            "encodings": {
                                "columns": [
                                    {"fieldName": "month_label", "displayName": "Month"},
                                    {"fieldName": "enrollment_target", "displayName": "Enrollment Target"},
                                    {"fieldName": "actual_net_enrollments", "displayName": "Actual Net Enrollments"},
                                    {"fieldName": "enrollment_achievement_pct", "displayName": "% Achievement"},
                                    {"fieldName": "debt_target", "displayName": "Debt Target"},
                                    {"fieldName": "actual_net_debt", "displayName": "Actual Net Debt"},
                                    {"fieldName": "debt_achievement_pct", "displayName": "Debt % Achievement"},
                                ]
                            },
                            "frame": {"title": "Monthly Goal vs Actual", "showTitle": True},
                        },
                    },
                    "position": {"x": 0, "y": 2, "width": 12, "height": 7},
                },
                {
                    "widget": {
                        "name": "rep_scorecard_table",
                        "queries": [{
                            "name": "main_query",
                            "query": {
                                "datasetName": "rep_scorecard_display_ds",
                                "fields": [
                                    {"name": "rep_name", "expression": "`rep_name`"},
                                    {"name": "team", "expression": "`team`"},
                                    {"name": "gross_enrollments", "expression": "`gross_enrollments`"},
                                    {"name": "net_enrollments", "expression": "`net_enrollments`"},
                                    {"name": "gross_debt", "expression": "`gross_debt`"},
                                    {"name": "avg_debt_per_enrollment", "expression": "`avg_debt_per_enrollment`"},
                                    {"name": "early_cancellations", "expression": "`early_cancellations`"},
                                    {"name": "cancel_rate_pct", "expression": "`cancel_rate_pct`"},
                                    {"name": "avg_days_to_cancel", "expression": "`avg_days_to_cancel`"},
                                ],
                                "disaggregated": True,
                            },
                        }],
                        "spec": {
                            "version": 2,
                            "widgetType": "table",
                            "encodings": {
                                "columns": [
                                    {"fieldName": "rep_name", "displayName": "Rep Name"},
                                    {"fieldName": "team", "displayName": "Team"},
                                    {"fieldName": "gross_enrollments", "displayName": "Gross Enrollments"},
                                    {"fieldName": "net_enrollments", "displayName": "Net Enrollments"},
                                    {"fieldName": "gross_debt", "displayName": "Gross Debt"},
                                    {"fieldName": "avg_debt_per_enrollment", "displayName": "Avg Debt per Enrollment"},
                                    {"fieldName": "early_cancellations", "displayName": "Early Cancellations"},
                                    {"fieldName": "cancel_rate_pct", "displayName": "Cancel Rate %"},
                                    {"fieldName": "avg_days_to_cancel", "displayName": "Avg Days to Cancel"},
                                ]
                            },
                            "frame": {"title": "Rep Performance Scorecard", "showTitle": True},
                        },
                    },
                    "position": {"x": 0, "y": 9, "width": 12, "height": 7},
                },
            ],
        },
    ],
}


dashboard["pages"][0]["displayName"] = "Overview"
dashboard["pages"][0]["layout"][0]["widget"]["multilineTextboxSpec"]["lines"] = ["# FinalBi"]

output_path = Path(__file__).with_name("finalbi_dashboard.json")
output_path.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
print(output_path)
