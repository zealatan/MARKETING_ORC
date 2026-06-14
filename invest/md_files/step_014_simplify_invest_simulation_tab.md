# Step 014 — Simplify "투자 시뮬레이션" Tab

## Prompt (verbatim)

You are working in:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before making any changes, create a new archive prompt file under:

/home/zealatan/MARKETING_ORC/invest/md_files

Use the next step number, for example:

step_014_simplify_invest_simulation_tab.md

The file must contain this entire prompt and a completion summary.

Goal
Simplify the "투자 시뮬레이션" tab.

Current situation
The tab currently renders:
1. price_chart(...)
2. reinvest_timeline_chart(...)

This is redundant because the user already has the full price chart in:

"가격 / 전고점 / 트리거"

The user wants:

"투자 시뮬레이션" tab = ONLY the investment result graph.

No duplicate stock price chart.
No ZigZag controls.
No Trigger Buy controls.

Desired behavior
The tab should answer only one question:

"If I invested with these settings:
- Initial Investment
- Monthly Contribution
- Dividend Reinvestment
- Tax Rate

how would my portfolio have evolved over time?"

Tasks

1. Backup

Create a timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_invest_tab_simplify_YYYYMMDD_HHMMSS

Backup at minimum:

- app.py
- global_cup/ui.py

Do not proceed unless backup succeeds.

2. Modify render_invest_simulation_tab()

Locate:

def render_invest_simulation_tab(...)

Remove:
- price_chart(...)
- Show ZigZag H/L markers checkbox
- Show Trigger Buy markers checkbox

Keep:

if reinvest is None:
    st.info(...)
    return

if reinvest.timeline_df.empty:
    st.warning(...)
    return

Render ONLY:

reinvest_timeline_chart(...)

Set chart height around:

fig.update_layout(height=660)

and display using:

st.plotly_chart(fig, use_container_width=True)

3. Improve title

At the top of the tab add:

st.subheader("투자 결과 시뮬레이션")

Optional small caption:

"초기 투자금, 월 추가 투자금, 배당 재투자 조건을 적용한 포트폴리오 가치 변화"

4. Keep all calculations unchanged

Do NOT modify:

- run_dividend_reinvest_backtest
- reinvest_timeline_chart
- analysis logic
- market config
- dividend tab
- price tab
- dividend reinvest tab

Only simplify the invest simulation tab UI.

5. Validation

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile app.py global_cup/ui.py

If available:

python3 -m pytest -q

If pytest fails due to existing unrelated issues, report clearly.

6. Final report

Provide:

- backup directory path
- modified files
- validation results
- before vs after behavior summary

Expected final UX

가격 / 전고점 / 트리거
→ stock price analysis

투자 시뮬레이션
→ portfolio growth result only

배당
→ dividend analysis

배당 재투자
→ detailed reinvestment breakdown and tables

## Implementation Summary

### Backup
- Directory: `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_invest_tab_simplify_20260614_120305`
- Files copied: `app.py`, `global_cup/ui.py`

### Modified files
- `global_cup_refactored/global_cup/ui.py` — rewrote `render_invest_simulation_tab` body. Removed price chart + both checkboxes. Added `st.subheader("투자 결과 시뮬레이션")` and caption. Renders only `reinvest_timeline_chart(...)` at height 660.
- `app.py` — **unchanged** (already wired correctly in step 013).

### Validation
- `cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored && python3 -m py_compile app.py global_cup/ui.py` → **OK**.
- `python3 -m pytest -q` → No tests ran. Pre-existing `test_formatting_display.py` calls `sys.exit(...)` at import time, causing pytest INTERNALERROR. Unrelated to this change.

### Before vs After
- **Before:** "투자 시뮬레이션" rendered the full `price_chart` (with ZigZag and Trigger Buy toggles) above the `reinvest_timeline_chart`, duplicating the price tab.
- **After:** "투자 시뮬레이션" shows a subheader + caption and renders only the `reinvest_timeline_chart`. No price chart, no ZigZag/Trigger checkboxes. Guards (`reinvest is None`, `timeline_df.empty`) preserved.

### Unchanged
`run_dividend_reinvest_backtest`, `reinvest_timeline_chart`, analysis logic, market config, price tab, dividend tab, dividend-reinvest tab.
