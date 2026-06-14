Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_007_snapshot_table_content_redesign.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

This is a UI/content redesign task only.

Do NOT touch the engine.

Do NOT modify:
- global_cup/golden_engine.py
- trigger calculations
- ZigZag calculations
- dividend reinvestment calculations
- backtest calculations
- validate_against_golden.py logic

Current problems:

1. Market Snapshot table colors still look outdated.
2. In the "가격 / 전고점 / 트리거" tab, the Recent Price Data table is not the most useful table.
   Instead of showing generic OHLCV recent close data, show a ZigZag high/low + trigger-focused table.

====================================================
TASK 1 — TABLE COLOR REDESIGN
====================================================

Remove the current table look.

Avoid:
- teal
- cyan
- strong green/red row tint
- bright gradient header
- cheap spreadsheet look

Use a more premium dark/cream editorial style.

Target palette:

Outer card:
rgba(255, 245, 220, 0.06)

Table surface:
rgba(255, 249, 237, 0.94)

Header:
#1f2b18

Header text:
#fff5dc

Body text:
#263522

Muted text:
#6c745e

Border:
rgba(31, 43, 24, 0.10)

Accent green:
#6f8f3f

Accent red:
#a14d36

Accent gold:
#c8a45d

Row hover:
rgba(142, 185, 87, 0.08)

Do not use full-row green/red.
Use small badges and text accents only.

====================================================
TASK 2 — PRICE/TRIGGER TAB TABLE CONTENT CHANGE
====================================================

When the selected tab is:

가격 / 전고점 / 트리거

replace the generic Recent Data table with a more useful table:

"ZigZag High / Low & Trigger Events"

This table should show rows derived from golden engine outputs:

Columns:

1. Type
   - High
   - Low
   - Trigger Buy
   - Current

2. Date

3. Price

4. Reference High

5. Reference Low

6. Drawdown %

7. Trigger %

8. Note

Data source:

- High and Low rows from find_alternating_high_low(close, threshold)
- Trigger Buy rows from run_backtest(... mode="트리거 발생 시 정액 투자", trigger_drop_pct=trigger_drop_pct)
- Current row from build_current_status()

Important:
Use golden_engine only.
Do not recompute with close.max().

====================================================
TASK 3 — KEEP RECENT DATA AVAILABLE BUT SECONDARY
====================================================

Do not delete Recent OHLCV data completely.

Move it into a collapsed expander:

"Raw Recent OHLCV Data"

Default collapsed.

So main snapshot becomes useful for decision-making.

====================================================
TASK 4 — ANNUAL DIVIDEND TABLE ALSO POLISH
====================================================

Annual Dividend table should remain visible on the right.

But use the new premium editorial color style.

Add small badges:

- Latest year
- Highest dividend year
- Lowest dividend year

Do not over-color the full table.

====================================================
TASK 5 — SNAPSHOT LAYOUT
====================================================

In 가격 / 전고점 / 트리거 tab:

Market Snapshot should become:

Left wide:
ZigZag High / Low & Trigger Events table

Right:
Annual Dividend table + dividend summary

Below:
Collapsed Raw Recent OHLCV Data expander

Use:

st.columns([2,1])

For other tabs, keep current layout unless this function is shared.
If render_recent_data() is shared across tabs, add a parameter:

mode="price_trigger" or mode="default"

and call price_trigger mode only in the 가격 / 전고점 / 트리거 tab.

====================================================
TASK 6 — VALIDATION
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py

Validation must still pass.

====================================================
TASK 7 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/UI_SNAPSHOT_CONTENT_REDESIGN_REPORT.md

Include:

- files modified
- new table content
- CSS changes
- where Raw Recent OHLCV was moved
- confirmation that golden_engine.py was not modified
- validation result

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. Table color is more premium and less childish.

2. 가격 / 전고점 / 트리거 tab shows:
   - High rows
   - Low rows
   - Trigger Buy rows
   - Current row

3. Generic recent OHLCV table is moved into collapsed expander.

4. Annual Dividend table still visible.

5. No engine calculation changes.

6. validate_against_golden.py still passes.

If validation fails:
STOP.
Do not continue UI work.
Write a failure report.
