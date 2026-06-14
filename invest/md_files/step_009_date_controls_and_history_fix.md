Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_009_date_controls_and_history_fix.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

Fix two UI/data issues:

1. Remove the Advanced settings expander.
   Start date and End date must always be visible.

2. Investigate and fix historical data truncation.
   When the user selects an early start date such as 2000-01-01,
   some tickers such as VOO should show all available historical data,
   not unexpectedly start around 2010 unless that is truly the first available yfinance data point.

This is NOT an engine rewrite task.

Do NOT modify:
- global_cup/golden_engine.py
- ZigZag logic
- trigger logic
- dividend reinvestment logic
- validate_against_golden.py calculation comparisons

====================================================
TASK 1 — REMOVE ADVANCED SETTINGS EXPANDER
====================================================

Currently the date controls are hidden under:

Advanced settings

Change layout so that the date controls are always visible.

Remove or stop using the Advanced settings expander.

Left control column should show:

Ticker search
Trigger %
Start date
End date

Always visible.

For dividend reinvestment tab, keep:
- initial investment
- monthly/additional investment
- dividend tax rate
- dividend reinvestment summary

visible in the same left control area.

Do not hide essential date controls.

====================================================
TASK 2 — IMPROVE DATE INPUT UX
====================================================

Use stable date input widgets or text input, whichever the current app uses safely.

Requirements:
- User can enter/select dates earlier than 2010.
- Default start date can remain recent if desired, but user must be able to choose 2000-01-01.
- End date remains current default.
- If start date is earlier than ticker inception, app should simply start from first available data point and show a note:
  "Data starts from YYYY-MM-DD for this ticker."

====================================================
TASK 3 — INVESTIGATE HISTORICAL DATA TRUNCATION
====================================================

Search for hardcoded date limits:

grep -R "2010" .
grep -R "2020" .
grep -R "timedelta" .
grep -R "start_date" .
grep -R "period=" .

Check:
- app.py
- global_cup/data_loader.py
- global_cup/analysis.py
- global_cup/ui.py
- any config/default date file

Find out why selecting 2000s start date can still produce charts starting around 2010.

Potential causes:
- UI date input minimum value
- default start date overwrite
- hardcoded start date in app.py
- yfinance download using period instead of start/end
- cache not invalidating correctly
- price_df trimmed by analysis step
- plotting using last N rows instead of full close series
- ticker selected is not actually VOO but another ETF with later history
- using adjusted or proxy ticker with limited history

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/DATE_HISTORY_AUDIT.md

Include:
- where start_date is created
- where it is passed
- where yfinance download happens
- where data is trimmed
- whether any hardcoded 2010/2020 exists
- root cause

====================================================
TASK 4 — FIX DATA LOADING IF NEEDED
====================================================

Ensure price download uses explicit start/end:

yf.download(
    ticker,
    start=start_date,
    end=end_date + timedelta(days=1),
    auto_adjust=False,
    progress=False,
    threads=False
)

or equivalent.

Do not use period="max" unless carefully handled.

Ensure cache key includes:
- ticker
- start_date
- end_date

If Streamlit cache is stale during development, provide a user-visible note or clear cache instruction.

====================================================
TASK 5 — DISPLAY ACTUAL DATA RANGE
====================================================

Add a small line near chart or controls:

Available data:
YYYY-MM-DD → YYYY-MM-DD
N trading days

Example:
Available data: 2010-09-09 → 2026-06-06 / 3,982 trading days

If requested start_date is earlier than actual first date, show:
Requested start: 2000-01-01 / Data starts: YYYY-MM-DD

This makes it clear whether the limitation is Yahoo data availability or app truncation.

====================================================
TASK 6 — VALIDATION SCRIPT FOR HISTORY
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/validate_history_range.py

Test:
- VOO from 2000-01-01 to current end date
- SPY from 2000-01-01 to current end date
- QQQ from 2000-01-01 to current end date
- 379780.KS or 379800.KS if available

Print:
ticker
requested_start
actual_first_date
actual_last_date
row_count

For VOO:
Do not hardcode exact expected first date, but warn if actual_first_date is later than 2011-01-01.

For SPY/QQQ:
Warn if data starts after 2001-01-01.

This script is for diagnostics, not financial correctness.

====================================================
TASK 7 — RUN CHECKS
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py
python validate_history_range.py

====================================================
TASK 8 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/DATE_CONTROL_AND_HISTORY_FIX_REPORT.md

Include:
- files modified
- where Advanced settings was removed
- where date controls now live
- historical data root cause
- whether VOO history now loads before 2010 if available
- validation outputs
- confirmation golden_engine.py unchanged

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. Advanced settings expander is removed or no longer used for date controls.

2. Start date and End date are always visible.

3. User can select/input 2000-01-01.

4. App uses selected start_date for yfinance download.

5. App displays actual data range.

6. No hardcoded 2010/2020 truncation remains unless documented as default only.

7. validate_against_golden.py still passes.

8. validate_history_range.py runs and reports actual first dates.

9. golden_engine.py unchanged.

If validation fails:
STOP.
Do not redesign.
Write a failure report.
