Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_006_snapshot_ui_layout_polish.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

This is a UI/layout polish task only.

Do NOT touch the engine.

Do NOT modify:
- global_cup/golden_engine.py
- trigger calculations
- ZigZag calculations
- dividend reinvestment calculations
- backtest calculations

Current issues:

1. Market Snapshot tables look visually cheap.
   The table colors are too harsh and old-fashioned.
   Current teal header + green/red full row tint looks childish.

2. In the "가격 / 전고점 / 트리거" tab, the user should see the current reference high price and reference low price more clearly.

3. In the "배당 재투자" tab, the metric summary currently appears on the right side above the chart.
   Move this entire dividend reinvestment metric summary to the left-side control area, directly under Advanced settings / Start date / End date.

====================================================
TASK 1 — TABLE COLOR POLISH
====================================================

Improve Market Snapshot table design.

Current style:
- strong teal header
- green/red row background
- black text
- looks too raw

Target style:
- premium dark dashboard style
- softer, more elegant colors
- less saturated
- more compact
- more professional

Use this direction:

Table card background:
rgba(255, 249, 237, 0.96)

Header background:
linear-gradient(135deg, #263522, #3f5f38)

Header text:
#fff5dc

Body text:
#1f2b18

Border:
rgba(31, 43, 24, 0.10)

Positive tint:
rgba(142, 185, 87, 0.10)

Negative tint:
rgba(174, 32, 18, 0.07)

Neutral row:
rgba(255, 249, 237, 0.96)

Alternate row:
rgba(244, 238, 220, 0.55)

Volume text:
#6c745e

Avoid bright cyan/teal table headers.

Avoid full-row strong red/green.

Use subtle text accents instead:
- close up: muted green text
- close down: muted red text
- volume muted gray

Update CSS classes related to:
- snapshot-section
- snapshot-table
- recent-data table
- dividend table
- metric cards

Do not change calculations.

====================================================
TASK 2 — PRICE/HIGH/LOW/TRIGGER TAB METRICS
====================================================

When user selects the "가격 / 전고점 / 트리거" tab, show a clear metric summary.

Add a compact metric card row near the chart or above Market Snapshot.

Show:

- Current Price
- Reference High Date
- Reference High Price
- Reference Low Date
- Reference Low Price
- Current Drawdown %
- Trigger Price
- Trigger Status

Important:
Use the golden engine output.

Use build_current_status() or already available analysis result fields.
Do NOT recompute using simple close.max().

If raw fields exist from golden_engine integration, use them.
If not, safely extend integration fields without changing engine behavior.

Reference high should follow golden behavior:
max price after last ZigZag low, not simple whole-period high.

Reference low should be the last ZigZag low if available.

Style:
Use compact dark-glass cards that match the existing dashboard.
Do not make them white dataframe style.

====================================================
TASK 3 — MOVE DIVIDEND REINVESTMENT SUMMARY TO LEFT CONTROL AREA
====================================================

Current "배당 재투자" tab layout:

Left:
- market title
- ticker search
- trigger %
- Advanced settings
- start date / end date

Right:
- reinvestment metrics
- chart

Change to:

Left:
- market title
- ticker search
- trigger %
- Advanced settings
- start date / end date
- Dividend Reinvestment Summary metrics

Right:
- chart only
- related tables if any

The following metrics must move to the left side under Advanced settings:

총 외부 투자금
최종 평가금액
총 수익률
CAGR
최종 보유수량
누적 순배당
현재 예상 순연배당
Yield on Cost
통화 / 배당세율 / 최근 연간 주당 배당금 / 현재 순배당률

Keep the same values.
Only move location and improve styling.

Use a section title:

Dividend Reinvestment Summary

or Korean:

배당 재투자 요약

Style:
- two-column compact metric grid
- dark glass background
- cream/green accents
- avoid huge blue/black default metric text
- readable on dark background

====================================================
TASK 4 — RESPONSIVE BEHAVIOR
====================================================

Desktop:
Left control column contains inputs + reinvest summary.
Right column contains chart.

Mobile:
Summary should stack below inputs before chart.

Do not break existing layout.

====================================================
TASK 5 — VALIDATION
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py

Also run existing validation if available:

python validate_against_golden.py

The validation must still pass.

====================================================
TASK 6 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/UI_LAYOUT_POLISH_REPORT.md

Include:

- files modified
- CSS classes changed
- where price/high/low metrics were added
- where dividend reinvestment summary was moved
- confirmation that golden_engine.py was not modified
- validation result

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. Market Snapshot tables look more premium and less childish.

2. "가격 / 전고점 / 트리거" tab clearly shows:
   - reference high price
   - reference low price
   - drawdown
   - trigger status

3. "배당 재투자" summary metrics are moved under Advanced settings on the left side.

4. Right side of dividend reinvestment tab focuses on the chart.

5. No engine calculation changes.

6. validate_against_golden.py still passes.

If validation fails:
STOP.
Do not continue UI polish.
Write a failure report.
