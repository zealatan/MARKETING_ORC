Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_010_remove_score_clean_chart_layout.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

This is a UI/layout cleanup task.

Do NOT touch the calculation engine.

Do NOT modify:
- global_cup/golden_engine.py
- trigger logic
- ZigZag logic
- dividend reinvestment calculations
- backtest calculations
- validate_against_golden.py calculation logic

Current requested changes:

1. Remove the "Global Cup Score" tab/section completely.
2. Remove dividend diamond markers from all charts.
3. Remove Engine Debug expander/panel.
4. Increase chart height while preserving chart width.
5. Align the bottom of the right-side chart with the bottom of the left-side dividend reinvestment summary/control column as much as practical.

====================================================
TASK 1 — REMOVE GLOBAL CUP SCORE
====================================================

Remove the Global Cup Score tab/button from the main tab navigation.

Current tabs likely include:

Global Cup Score
가격 / 전고점 / 트리거
배당
배당 재투자

Change to:

가격 / 전고점 / 트리거
배당
배당 재투자

Do not leave empty placeholder code visible in UI.

If scoring.py exists, do not delete it unless clearly unused.
But the UI should not show Global Cup Score anymore.

====================================================
TASK 2 — REMOVE DIVIDEND DIAMOND MARKERS FROM CHARTS
====================================================

Find chart code that adds dividend markers.

Likely trace name:
Dividend
or marker symbol:
diamond

Remove dividend marker traces from:
- price/trigger chart
- dividend chart if present
- dividend reinvestment chart if present

Important:
Only remove visual diamond markers.
Do not remove dividend calculations.
Do not remove dividend tables.
Do not remove dividend reinvestment logic.

Chart legend should no longer show "Dividend" as a marker series.

====================================================
TASK 3 — REMOVE ENGINE DEBUG
====================================================

Remove or hide:

Engine Debug

expander/panel from all tabs.

This was useful for development, but should not appear in product UI.

Do not remove validation scripts.

====================================================
TASK 4 — INCREASE CHART HEIGHT
====================================================

Keep current chart width/layout.

Increase chart height enough so that the bottom of the chart visually aligns with the bottom of the left-side control/summary column.

For the price/trigger chart:
- increase height from current value to around 650–760 px if necessary

For dividend reinvestment chart:
- increase height from current value to around 700–820 px if necessary

Use constants if possible, e.g.:

CHART_HEIGHT_PRICE = 720
CHART_HEIGHT_REINVEST = 760

Do not make chart too tall on mobile.
For mobile, keep responsive behavior or use CSS/media fallback if already present.

====================================================
TASK 5 — ALIGN LEFT SUMMARY AND RIGHT CHART
====================================================

The dividend reinvestment tab layout should visually align:

Left column:
- ticker/search/trigger/date controls
- reinvestment inputs
- dividend reinvestment summary

Right column:
- chart

Adjust:
- chart height
- container padding
- top/bottom margins
- summary card spacing

Goal:
The chart bottom should roughly align with the bottom of the left summary/control column.

Do not move summary back to the right.
Keep summary under the left-side controls.

====================================================
TASK 6 — CLEAN TAB-SPECIFIC SNAPSHOT PLACEMENT
====================================================

After removing Global Cup Score, ensure Market Snapshot still appears correctly in:

- 가격 / 전고점 / 트리거
- 배당
- 배당 재투자 if currently intended

Do not duplicate Market Snapshot unexpectedly.

====================================================
TASK 7 — VALIDATION
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py
python test_formatting_display.py

Validation must still pass.

====================================================
TASK 8 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/UI_SCORE_REMOVAL_CHART_CLEANUP_REPORT.md

Include:

- files modified
- where Global Cup Score was removed
- where dividend diamond markers were removed
- where Engine Debug was removed
- chart heights before/after
- layout alignment changes
- confirmation golden_engine.py unchanged
- validation results

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. Global Cup Score tab/button is gone.
2. Dividend diamond markers are gone from charts and legends.
3. Engine Debug is gone.
4. Chart width is preserved.
5. Chart height is increased.
6. Dividend reinvestment chart bottom roughly aligns with the left summary/control column.
7. Dividend calculations/tables still work.
8. validate_against_golden.py passes.
9. test_formatting_display.py passes.
10. golden_engine.py unchanged.

If validation fails:
STOP.
Do not continue.
Write a failure report.
