import pandas as pd
import numpy as np
from datetime import datetime

# Read all CSV files
calendar = pd.read_csv('csvtemp/calendar_by_day.csv')
detailes = pd.read_csv('csvtemp/detailes.csv')
director_goals = pd.read_csv('csvtemp/director_goals_by_day.csv')
early_cancellation = pd.read_csv('csvtemp/early_cancellation.csv')
goals = pd.read_csv('csvtemp/goals_by_day.csv')
performance = pd.read_csv('csvtemp/performance_by_day.csv')

print("=" * 80)
print("KPI CALCULATIONS FOR REPORTING BUS SCHEMA")
print("=" * 80)
print()

# ============================================================================
# ENROLLMENT VOLUME KPIs
# ============================================================================
print("ENROLLMENT VOLUME METRICS")
print("-" * 80)

# Total Enrollments (Gross)
total_enrollments = performance['ENROLLMENTS'].sum()
print(f"Total Enrollments (Gross): {total_enrollments:,}")

# Net Enrollments
net_enrollments = performance['NETENROLLMENTS'].sum()
print(f"Net Enrollments: {net_enrollments:,}")

# Average Daily Enrollments
unique_days = performance['RANKDAYVALUE'].nunique()
avg_daily_enrollments = net_enrollments / unique_days if unique_days > 0 else 0
print(f"Average Daily Enrollments: {avg_daily_enrollments:.2f}")

# Active Client Count (latest month)
latest_month = detailes['Date'].max()
active_clients = detailes[(detailes['Date'] == latest_month) & 
                          (detailes['ClientStatus'] == 'Active')]['ClientID'].nunique()
print(f"Active Client Count (as of {latest_month}): {active_clients:,}")

# Total Client Count
total_clients = detailes['ClientID'].nunique()
print(f"Total Client Count: {total_clients:,}")

print()

# ============================================================================
# DEBT / REVENUE KPIs
# ============================================================================
print("DEBT / REVENUE METRICS")
print("-" * 80)

# Total Enrolled Debt (Gross)
total_enrolled_debt = performance['TOTALDEBT'].sum()
print(f"Total Enrolled Debt (Gross): ${total_enrolled_debt:,.2f}")

# Net Enrolled Debt
net_enrolled_debt = performance['NETDEBT'].sum()
print(f"Net Enrolled Debt: ${net_enrolled_debt:,.2f}")

# Average Debt per Enrollment
avg_debt_per_enrollment = net_enrolled_debt / net_enrollments if net_enrollments > 0 else 0
print(f"Average Debt per Enrollment: ${avg_debt_per_enrollment:,.2f}")

# Cancelled Debt Total
cancelled_debt_total = performance['CANCELLEDDEBT'].sum()
print(f"Cancelled Debt Total: ${cancelled_debt_total:,.2f}")

# EOM Enrolled Debt (latest month)
eom_enrolled_debt = detailes[detailes['Date'] == latest_month]['EOMEnrolledDebt'].sum()
print(f"EOM Enrolled Debt (as of {latest_month}): ${eom_enrolled_debt:,.2f}")

# Current Enrolled Debt (active clients only)
current_enrolled_debt = detailes[(detailes['Date'] == latest_month) & 
                                  (detailes['ClientStatus'] == 'Active')]['CurrentEnrolledDebt'].sum()
print(f"Current Enrolled Debt (Active): ${current_enrolled_debt:,.2f}")

print()

# ============================================================================
# CANCELLATION KPIs
# ============================================================================
print("CANCELLATION METRICS")
print("-" * 80)

# Early Cancellation Count
early_cancel_count = performance['EARLYCANCELLATION'].sum()
print(f"Early Cancellations: {early_cancel_count:,}")

# Early Cancellation Rate
early_cancel_rate = early_cancel_count / total_enrollments if total_enrollments > 0 else 0
print(f"Early Cancellation Rate: {early_cancel_rate:.2%}")

# Average Days to Cancel
avg_days_to_cancel = early_cancellation['DaysToCancel'].mean()
print(f"Average Days to Cancel: {avg_days_to_cancel:.1f} days")

# Cancelled Debt Rate
cancelled_debt_rate = cancelled_debt_total / total_enrolled_debt if total_enrolled_debt > 0 else 0
print(f"Cancelled Debt Rate: {cancelled_debt_rate:.2%}")

# Cancellation Reasons Breakdown
print("\nCancellation Reasons:")
cancel_reasons = early_cancellation.groupby('CANCELREASON')['EarlyCancellation'].sum().sort_values(ascending=False)
for reason, count in cancel_reasons.items():
    pct = count / early_cancel_count * 100 if early_cancel_count > 0 else 0
    print(f"  {reason}: {int(count):,} ({pct:.1f}%)")

print()

# ============================================================================
# GOAL PACING KPIs (Latest Month)
# ============================================================================
print("GOAL PACING METRICS (LATEST MONTH)")
print("-" * 80)

# Get latest month data
latest_month_perf = performance[performance['RANKDATEVALUE'] == latest_month]
latest_month_goals = goals[goals['TARGETDATE'] == latest_month]

# Monthly Enrollment Target (sum across all reps)
target_enrollments_month = latest_month_goals['TARGETENROLLMENTS'].sum()
print(f"Monthly Enrollment Target: {target_enrollments_month:,}")

# Monthly Debt Target (sum across all reps)
target_debt_month = latest_month_goals['TARGETDEBT'].sum()
print(f"Monthly Debt Target: ${target_debt_month:,.2f}")

# Actual Performance for Latest Month
actual_enrollments = latest_month_perf['NETENROLLMENTS'].sum()
actual_debt = latest_month_perf['NETDEBT'].sum()
print(f"Actual Net Enrollments: {actual_enrollments:,}")
print(f"Actual Net Debt: ${actual_debt:,.2f}")

# Achievement Rates
enrollment_achievement = actual_enrollments / target_enrollments_month * 100 if target_enrollments_month > 0 else 0
debt_achievement = actual_debt / target_debt_month * 100 if target_debt_month > 0 else 0
print(f"Enrollment Achievement: {enrollment_achievement:.1f}%")
print(f"Debt Achievement: {debt_achievement:.1f}%")

print()

# ============================================================================
# DIRECTOR/TEAM PERFORMANCE (Latest Month)
# ============================================================================
print("DIRECTOR/TEAM PERFORMANCE (LATEST MONTH)")
print("-" * 80)

# Get director goals for latest month
latest_director_goals = director_goals[director_goals['GOALDATE'] == latest_month]

for _, director_row in latest_director_goals.iterrows():
    director_name = director_row['TEAM']
    director_goal = director_row['DIRECTORGOAL']
    
    # Get team name from goals table
    team_reps = latest_month_goals[latest_month_goals['DIRECTORKEY'] == director_row['DIRECTORKEY']]
    if len(team_reps) > 0:
        team_name = team_reps.iloc[0]['TEAM']
        
        # Get actual performance for this team
        team_rep_names = team_reps['REP'].unique()
        team_performance = latest_month_perf[latest_month_perf['ORIGINALREP'].isin(team_rep_names)]
        
        team_enrollments = team_performance['NETENROLLMENTS'].sum()
        team_debt = team_performance['NETDEBT'].sum()
        team_cancellations = team_performance['EARLYCANCELLATION'].sum()
        
        achievement = team_enrollments / director_goal * 100 if director_goal > 0 else 0
        
        print(f"\n{team_name} Team (Director: {director_name})")
        print(f"  Goal: {director_goal:,} | Actual: {team_enrollments:,} | Achievement: {achievement:.1f}%")
        print(f"  Net Debt: ${team_debt:,.2f}")
        print(f"  Early Cancellations: {team_cancellations:,}")

print()

# ============================================================================
# TOP PERFORMERS (Latest Month)
# ============================================================================
print("TOP PERFORMERS BY NET ENROLLMENTS (LATEST MONTH)")
print("-" * 80)

rep_performance = latest_month_perf.groupby('ORIGINALREP').agg({
    'NETENROLLMENTS': 'sum',
    'NETDEBT': 'sum',
    'EARLYCANCELLATION': 'sum'
}).sort_values('NETENROLLMENTS', ascending=False).head(10)

for rep, row in rep_performance.iterrows():
    print(f"{rep}: {int(row['NETENROLLMENTS']):,} enrollments | ${row['NETDEBT']:,.0f} debt | {int(row['EARLYCANCELLATION'])} cancellations")

print()

# ============================================================================
# MONTHLY TRENDS (Last 6 Months)
# ============================================================================
print("MONTHLY TRENDS (LAST 6 MONTHS)")
print("-" * 80)

# Get unique months and sort
all_months = sorted(performance['RANKDATEVALUE'].unique(), reverse=True)[:6]
all_months.reverse()  # Show chronologically

print(f"{'Month':<12} {'Enrollments':<15} {'Net Debt':<20} {'Cancellations':<15} {'Cancel Rate':<12}")
print("-" * 80)

for month in all_months:
    month_perf = performance[performance['RANKDATEVALUE'] == month]
    month_enrollments = month_perf['NETENROLLMENTS'].sum()
    month_debt = month_perf['NETDEBT'].sum()
    month_cancels = month_perf['EARLYCANCELLATION'].sum()
    month_gross = month_perf['ENROLLMENTS'].sum()
    cancel_rate = month_cancels / month_gross * 100 if month_gross > 0 else 0
    
    # Format month as YYYY-MM
    month_str = f"{str(month)[:4]}-{str(month)[4:]}"
    
    print(f"{month_str:<12} {month_enrollments:<15,} ${month_debt:<19,.0f} {month_cancels:<15,} {cancel_rate:<11.1f}%")

print()

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================
print("OVERALL SUMMARY STATISTICS")
print("-" * 80)

# Date range
min_date = performance['RANKDAYVALUE'].min()
max_date = performance['RANKDAYVALUE'].max()
print(f"Data Period: {min_date} to {max_date}")
print(f"Total Working Days: {unique_days:,}")
print(f"Total Months: {performance['RANKDATEVALUE'].nunique()}")
print()
print(f"Total Gross Enrollments: {total_enrollments:,}")
print(f"Total Net Enrollments: {net_enrollments:,}")
print(f"Total Early Cancellations: {early_cancel_count:,}")
print(f"Overall Cancellation Rate: {early_cancel_rate:.2%}")
print()
print(f"Total Gross Debt: ${total_enrolled_debt:,.2f}")
print(f"Total Net Debt: ${net_enrolled_debt:,.2f}")
print(f"Total Cancelled Debt: ${cancelled_debt_total:,.2f}")
print(f"Average Debt per Enrollment: ${avg_debt_per_enrollment:,.2f}")
print()
print(f"Unique Clients: {total_clients:,}")
print(f"Active Clients (Latest Month): {active_clients:,}")
print(f"Current Active Debt: ${current_enrolled_debt:,.2f}")

print()
print("=" * 80)
print("CALCULATION COMPLETE")
print("=" * 80)
