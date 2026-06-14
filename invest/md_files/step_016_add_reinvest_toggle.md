# Step 016 — Add global "배당 재투자" toggle

**Date:** 2026-06-14
**Working directory:** /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

---

## Original Prompt

You are working in:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before making any changes, create a new archive prompt file under:

/home/zealatan/MARKETING_ORC/invest/md_files

Use the next step number, for example:

step_016_add_reinvest_toggle.md

The file must contain this entire prompt and a completion summary.

Goal
Add a global checkbox that lets the user switch between:

1. 배당 재투자 ON
2. 배당 재투자 OFF

The selected mode should affect:

- Left summary table
- 투자 시뮬레이션 graph
- 배당 재투자 tab

The user wants ONE active scenario at a time.

No side-by-side comparison.

Desired UX

Left panel:

[✓] 배당 재투자

If checked:
- Use reinvest_result

If unchecked:
- Use no_reinvest_result

Everything displayed to the user should update accordingly.

Behavior

Checked:

- Dividends are taxed
- Net dividends are reinvested
- Existing behavior

Unchecked:

- Dividends are taxed
- Net dividends accumulate as cash
- No dividend share purchases
- Monthly contributions continue normally

Tasks

1. Backup

Create a timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_reinvest_toggle_YYYYMMDD_HHMMSS

Backup at minimum:

- app.py
- global_cup/ui.py
- global_cup/dividend_reinvest.py

Do not proceed unless backup succeeds.

2. Inspect existing implementation

Locate:

- run_dividend_reinvest_backtest(...)
- render_reinvest_controls_left(...)
- render_reinvest_summary_left(...)
- render_invest_simulation_tab(...)
- render_dividend_reinvest_tab(...)
- app.py reinvest_result creation

3. Add UI checkbox

In the left-side investment controls section add:

st.checkbox(
    "배당 재투자",
    value=True,
    key="enable_dividend_reinvestment"
)

Place it near:

- Initial Investment
- Monthly Contribution
- Tax Rate

The checkbox should be clearly visible.

4. Compute both scenarios

In app.py compute:

reinvest_result

and

no_reinvest_result

using the already implemented logic.

If a no-reinvest function already exists, use it.

Otherwise use:

reinvest_dividends=False

if that parameter was added previously.

Do NOT remove reinvest_result.

5. Select active scenario

After computing both:

selected_result = (
    reinvest_result
    if reinvest_enabled
    else no_reinvest_result
)

Use selected_result everywhere user-facing.

6. Update left summary

Currently:

render_reinvest_summary_left(
    reinvest_result,
    ...
)

Replace with:

render_reinvest_summary_left(
    selected_result,
    ...
)

The summary should immediately reflect the checkbox state.

7. Update 투자 시뮬레이션 tab

Currently it likely receives:

reinvest_result

Change it to use:

selected_result

Only one graph should be shown.

The graph should represent:

currently selected scenario.

Optional title:

"현재 시뮬레이션 결과"

Optional caption:

"배당 재투자 설정에 따라 결과가 달라집니다."

8. Update 배당 재투자 tab

The detailed reinvestment tab should also reflect:

selected_result

when displaying charts and tables.

Do NOT display both scenarios simultaneously.

9. Preserve behavior

Do NOT modify:

- market config
- analysis logic
- price tab
- dividend tab
- trigger logic
- zigzag logic

10. Validation

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile \
    app.py \
    global_cup/ui.py \
    global_cup/dividend_reinvest.py

If available:

python3 -m pytest -q

If pytest fails because of existing unrelated issues,
report clearly.

11. Final report

Provide:

- backup directory path
- modified files
- validation results
- exact checkbox location
- before vs after behavior

Expected final UX

[✓] 배당 재투자

ON:
- summary = reinvest case
- simulation graph = reinvest case
- reinvest tab = reinvest case

[ ] 배당 재투자

OFF:
- summary = no-reinvest case
- simulation graph = no-reinvest case
- reinvest tab = no-reinvest case

The user always sees one consistent scenario across the entire application.

---

## Completion Summary

### Backup
- `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_reinvest_toggle_20260614_141028/`
  - `app.py`
  - `global_cup/ui.py`
  - `global_cup/dividend_reinvest.py`

### Modified files
- `global_cup_refactored/app.py`
- `global_cup_refactored/global_cup/ui.py`

`global_cup/dividend_reinvest.py` was NOT modified — the `reinvest_dividends: bool = True` parameter already existed (cash-accumulation branch on `reinvest_dividends=False` at line 121–129).

### Changes
1. **`render_reinvest_controls_left`** (`global_cup/ui.py`): added `st.checkbox("배당 재투자", value=True, key="enable_dividend_reinvestment")` directly below the `배당세율 (%)` number input and above the summary container. Returned dict now includes `"reinvest_enabled": bool`.
2. **`render_invest_simulation_tab`** (`global_cup/ui.py`): signature changed from `(reinvest=None, no_reinvest=None)` to `(selected=None)`. Renders a single timeline chart for the selected scenario. Title changed to `"현재 시뮬레이션 결과"` with caption `"배당 재투자 설정에 따라 결과가 달라집니다."`. The side-by-side `investment_comparison_chart` call was removed.
3. **`render_dividend_reinvest_tab`** (`global_cup/ui.py`): signature changed from `reinvest=` to `selected=`. All internal references updated to use `selected`.
4. **`app.py`**: keeps both `reinvest_result` and `no_reinvest_result` computations. Added:
   ```python
   reinvest_enabled = reinvest_params["reinvest_enabled"]
   selected_result = reinvest_result if reinvest_enabled else no_reinvest_result
   ```
   The left summary, invest simulation tab, and dividend reinvest tab all now receive `selected_result`.

### Checkbox location
Left column → "배당 재투자 설정" section → directly under the `배당세율 (%)` input, immediately above the dark-glass summary metric grid. Label: `배당 재투자`. Tooltip: "체크 시 세후 배당금을 자동 재투자합니다. 해제 시 배당금은 현금으로 누적됩니다."

### Behavior before vs after
| Surface | Before | After (toggle ON) | After (toggle OFF) |
| --- | --- | --- | --- |
| Left summary | Always reinvest case | Reinvest case | No-reinvest case (dividends as cash) |
| 투자 시뮬레이션 tab | Two lines (reinvest vs no-reinvest comparison) | Single line — reinvest case | Single line — no-reinvest case |
| 배당 재투자 tab | Always reinvest case | Reinvest case | No-reinvest case |

### Validation
- `python3 -m py_compile app.py global_cup/ui.py global_cup/dividend_reinvest.py` → **OK** (no errors).
- AST parse of the three files → **OK**.
- Import smoke test of `render_reinvest_controls_left`, `render_reinvest_summary_left`, `render_invest_simulation_tab`, `render_dividend_reinvest_tab`, `run_dividend_reinvest_backtest` → **OK** (two harmless Streamlit "No runtime found" warnings, unrelated).
- `python3 -m pytest -q` → **pre-existing collection failure unrelated to this change**: `test_formatting_display.py` calls `sys.exit(...)` at module import time (line 71), which triggers a pytest `INTERNALERROR` during test collection. This existed before this step and is unchanged by this work.

### Preserved (untouched)
- `market_config.py`, `analysis.py`, price tab, dividend tab, trigger logic, zigzag logic, charts module.
- `reinvest_result` is still computed and available; only its downstream consumers were redirected via `selected_result`.
