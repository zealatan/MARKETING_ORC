Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_011_final_dashboard_layout_cleanup.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

This is a UI/layout cleanup task only.

Do NOT touch calculation logic.

Do NOT modify:
- global_cup/golden_engine.py
- ZigZag logic
- trigger logic
- dividend calculations
- dividend reinvestment calculations
- backtest logic
- validate_against_golden.py calculation logic

Goal:
Make the dashboard cleaner and more product-like.

====================================================
TASK 1 — REMOVE GLOBAL CUP SCORE
====================================================

Remove the Global Cup Score tab/button completely.

Remaining tabs should be:

1. 가격 / 전고점 / 트리거
2. 배당
3. 배당 재투자

Do not leave empty score UI.

====================================================
TASK 2 — MOVE TOP TAB/METRIC/CHART AREA DOWN
====================================================

Currently the top tab bar, metric cards, and chart start too high.

Move the right-side content area slightly downward so it aligns better with the left-side control panel.

Apply this to:

- tab navigation
- current price / ref high / ref low / drawdown metric cards
- chart

Do not move the left title area too much.

====================================================
TASK 3 — ADD TRIGGER COUNT METRIC
====================================================

In the 가격 / 전고점 / 트리거 tab metric row, add:

Trigger Count

Place it between:

Current Price

and

Ref High

Trigger Count should show how many trigger buy events occurred under the current trigger percentage.

Example:

Current Price | Trigger Count | Ref High | Ref Low | ZZ Drawdown | Trigger Price | Trigger Status

Use existing backtest_df or trigger event data.
Do NOT recalculate with a new algorithm.
Use golden engine-derived trigger buy events.

Format:
7회

====================================================
TASK 4 — REMOVE REF HIGH DATE / REF LOW DATE AS SEPARATE CARDS
====================================================

Do not show Ref High Date and Ref Low Date as independent metric cards.

Instead:

Ref High card:
2,363,000 원
2026-06-01

Ref Low card:
807,000 원
2026-03-31

So each card has price + date inside.

Metric row should be compact.

====================================================
TASK 5 — MOVE MARKET SNAPSHOT TO SEPARATE BUTTON
====================================================

Do not always show Market Snapshot under the chart in 가격 / 전고점 / 트리거 tab.

Add a separate button near the top-right of the price/trigger tab:

Market Snapshot

When clicked/selected, replace the chart area with the Market Snapshot panel.

Behavior:

- Default view: chart
- Market Snapshot button clicked: show Market Snapshot in the same right-side area where the chart normally appears
- Market Snapshot panel should match chart width
- Market Snapshot panel should not appear below the chart

Important:
This applies mainly to 가격 / 전고점 / 트리거 tab.

====================================================
TASK 6 — REMOVE ANNUAL DIVIDEND FROM PRICE/TRIGGER TAB
====================================================

In 가격 / 전고점 / 트리거 tab:

Do NOT show Annual Dividend table.

Annual Dividend should remain only in:
- 배당 tab
- 배당 재투자 tab, if already intended

The price/trigger tab should focus on:
- chart
- H/L markers
- trigger buy markers
- Market Snapshot button panel when selected

====================================================
TASK 7 — REMOVE ENGINE DEBUG
====================================================

Remove Engine Debug expander/panel from all tabs.

No development debug UI should remain.

====================================================
TASK 8 — REMOVE DIVIDEND DIAMOND MARKERS
====================================================

Remove dividend diamond markers from charts.

Keep:
- ZigZag High markers
- ZigZag Low markers
- Trigger Buy markers
- Current marker

Remove:
- Dividend marker trace
- Dividend legend entry

Do not remove dividend data or dividend tables.

====================================================
TASK 9 — ALIGN CHART BOTTOM WITH LEFT SUMMARY PANEL
====================================================

For the price/trigger tab and dividend reinvestment tab:

Adjust chart height so that the bottom of the chart roughly aligns with the bottom of the left control/summary panel.

Keep width unchanged.

Recommended:
- Price chart height: 720–780 px
- Dividend reinvestment chart height: 760–820 px

Use constants if possible:
CHART_HEIGHT_PRICE
CHART_HEIGHT_REINVEST

Do not make mobile layout unusable.

====================================================
TASK 10 — VALIDATION
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py
python test_formatting_display.py

All must pass.

====================================================
TASK 11 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/UI_FINAL_LAYOUT_CLEANUP_REPORT.md

Include:
- files modified
- Global Cup Score removal
- Market Snapshot button implementation
- Annual Dividend removal from price/trigger tab
- Engine Debug removal
- Dividend marker removal
- Trigger Count metric source
- chart height changes
- validation results
- confirmation golden_engine.py unchanged

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. Global Cup Score is gone.
2. Only three tabs remain:
   가격 / 전고점 / 트리거, 배당, 배당 재투자.
3. Trigger Count appears between Current Price and Ref High.
4. Ref High and Ref Low cards include date inside the same card.
5. Market Snapshot appears only when its button is clicked.
6. Market Snapshot replaces chart area, not below chart.
7. Annual Dividend table does not appear in price/trigger tab.
8. Engine Debug is gone.
9. Dividend diamond markers are gone.
10. Chart bottom roughly aligns with left summary/control panel.
11. golden_engine.py unchanged.
12. validate_against_golden.py passes.
13. test_formatting_display.py passes.

If validation fails:
STOP.
Do not continue.
Write a failure report.
