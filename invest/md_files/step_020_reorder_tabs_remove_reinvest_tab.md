# Step 020 — Reorder tabs and remove standalone 배당 재투자 tab

**Date:** 2026-06-14
**Working directory:** /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

**Note on numbering:** Prompt example used `step_019_...`; step 019 was already taken (invest quantity tab). Filed as 020.

---

## Original Prompt

You are working in:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before making changes, create a new archive prompt file under:

/home/zealatan/MARKETING_ORC/invest/md_files

Use the next step number, for example:

step_019_reorder_tabs_remove_reinvest_tab.md

Goal:
Reorder Streamlit tabs and remove the standalone "배당 재투자" tab.

Current tab order is approximately:

가격 / 전고점 / 트리거
투자 시뮬레이션
투자 수량
배당
배당 재투자

New desired tab order:

가격 / 전고점 / 트리거
배당
투자 시뮬레이션
투자 수량

Important:
Remove only the standalone tab "배당 재투자".
Do NOT remove the dividend reinvestment calculation logic.
Do NOT remove the left-side "배당 재투자" checkbox.
Do NOT remove reinvest_result or no_reinvest_result calculations.
Do NOT remove the left summary table.
Investment simulation and investment quantity tabs still depend on reinvest/no-reinvest results.

Tasks:

1. Backup
Create timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_tab_reorder_remove_reinvest_YYYYMMDD_HHMMSS

Backup at minimum:
- app.py
- global_cup/ui.py

2. Modify app.py tab creation

Change from current multi-tab structure to exactly:

price_tab, dividend_tab, invest_result_tab, invest_quantity_tab = st.tabs([
    "가격 / 전고점 / 트리거",
    "배당",
    "투자 시뮬레이션",
    "투자 수량",
])

3. Update tab blocks

Keep:

with price_tab:
    render_price_tab(...)

with dividend_tab:
    render_dividend_tab(...)

with invest_result_tab:
    render_invest_simulation_tab(...)

with invest_quantity_tab:
    render_invest_quantity_tab(...)

Remove:
- reinvest_tab variable
- with reinvest_tab:
- render_dividend_reinvest_tab(...) call from app.py

4. Clean imports

In app.py, remove render_dividend_reinvest_tab from import list if no longer used.

Do NOT delete the function from global_cup/ui.py unless it is clearly unused and safe.
Safer option: leave the function in ui.py but stop importing/calling it.

5. Preserve calculations

Keep both calculations:

reinvest_result
no_reinvest_result

Keep selected_result logic:

selected_result = reinvest_result if reinvest_enabled else no_reinvest_result

Keep:

render_reinvest_summary_left(selected_result, ...)

6. Preserve existing behavior

Do NOT change:
- price tab
- dividend tab
- investment simulation tab
- investment quantity tab
- left controls
- left summary
- dividend reinvest checkbox
- calculation logic
- charts.py
- dividend_reinvest.py

7. Validation

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile app.py global_cup/ui.py

If available:

python3 -m pytest -q

If pytest fails due to existing unrelated sys.exit in test_formatting_display.py, report clearly.

8. Final report

Print:
- backup directory path
- modified files
- old tab order
- new tab order
- validation results
- confirmation that the standalone "배당 재투자" tab was removed but its calculation logic remains.

---

## Completion Summary

### Backup
- `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_tab_reorder_remove_reinvest_20260614_171355/`
  - `app.py`
  - `global_cup/ui.py`

### Modified files
- `global_cup_refactored/app.py` — removed `render_dividend_reinvest_tab` from the import block; replaced 5-tab `st.tabs(...)` with 4-tab version in the new order; removed the `reinvest_tab` variable and its `with` block; reordered tab `with` blocks so 배당 sits between 가격 and 투자 시뮬레이션.

No other files were touched. `global_cup/ui.py` still defines `render_dividend_reinvest_tab(...)`, but it is no longer called from anywhere — kept dormant per the prompt's "safer option" instruction.

### Tab order
- **Before:** 가격 / 전고점 / 트리거 → 투자 시뮬레이션 → 투자 수량 → 배당 → 배당 재투자
- **After:** 가격 / 전고점 / 트리거 → 배당 → 투자 시뮬레이션 → 투자 수량

### Preserved
- `reinvest_result = run_dividend_reinvest_backtest(...)` (line 69).
- `no_reinvest_result = run_dividend_reinvest_backtest(..., reinvest_dividends=False)` (line 77).
- `selected_result = reinvest_result if reinvest_enabled else no_reinvest_result` (line 87).
- `render_reinvest_summary_left(selected_result, ...)` (line 93).
- Left-side `배당 재투자` checkbox (`enable_dividend_reinvestment`) and the entire `render_reinvest_controls_left(...)` panel.
- `investment_simulation_chart` and `investment_quantity_chart` still receive `reinvest_result`/`no_reinvest_result`/`reinvest_enabled`.
- `charts.py` and `dividend_reinvest.py` were not modified.

### Validation
- `python3 -m py_compile app.py global_cup/ui.py` → **OK**.
- `grep` check confirmed `render_dividend_reinvest_tab` is no longer referenced in `app.py`, while `reinvest_result`, `no_reinvest_result`, `selected_result`, and `render_reinvest_summary_left` remain in place.
- `python3 -m pytest -q` → **pre-existing INTERNALERROR** in `test_formatting_display.py:71` (`sys.exit(...)` at module import). Unchanged from prior steps; unrelated to this work.

### Confirmation
- Standalone `배당 재투자` tab removed from the UI.
- Dividend-reinvestment **calculation logic remains intact**: both `reinvest_result` and `no_reinvest_result` are still computed, the checkbox still drives `selected_result`, and the left summary still updates accordingly.
