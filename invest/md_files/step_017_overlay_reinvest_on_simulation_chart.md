# Step 017 — Overlay reinvest curve on simulation chart

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

step_017_overlay_reinvest_on_simulation_chart.md

The file must contain this entire prompt and a completion summary.

Goal
Refine the investment simulation behavior.

Current behavior:
- The checkbox "배당 재투자" switches the active scenario.
- Left summary updates correctly.
- Investment simulation graph changes between no-reinvest and reinvest.

New desired behavior:

1. Left summary table behavior should remain unchanged:
   - Checkbox OFF: summary shows no-reinvest result.
   - Checkbox ON: summary shows reinvest result.

2. Investment simulation graph behavior should change:
   - Checkbox OFF:
     show only the no-reinvest curve.
   - Checkbox ON:
     keep the no-reinvest curve visible,
     and overlay/add the reinvest curve on top of the same chart for comparison.

In other words:
- The no-reinvest case is always the baseline graph.
- The reinvest case is added only when the checkbox is checked.

Important UX meaning:
[ ] 배당 재투자
→ graph: 배당 미재투자 only
→ summary: 배당 미재투자

[✓] 배당 재투자
→ graph: 배당 미재투자 + 배당 재투자 overlay
→ summary: 배당 재투자

Tasks

1. Backup

Create a timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_reinvest_overlay_YYYYMMDD_HHMMSS

Backup at minimum:
- app.py
- global_cup/ui.py
- global_cup/charts.py
- global_cup/dividend_reinvest.py

Do not proceed unless backup succeeds.

2. Inspect current code

Inspect:
- app.py
- global_cup/ui.py
- global_cup/charts.py
- global_cup/dividend_reinvest.py

Find:
- checkbox state variable
- selected_result
- reinvest_result
- no_reinvest_result
- render_invest_simulation_tab(...)
- investment comparison chart function if already added
- reinvest_timeline_chart(...)

3. Preserve left summary behavior

Do not change the summary selection logic.

It should remain:

selected_result = reinvest_result if checkbox is checked else no_reinvest_result

and:

render_reinvest_summary_left(selected_result, ...)

This is important.

4. Change only investment simulation chart behavior

Update the investment simulation tab so it receives:
- reinvest_result
- no_reinvest_result
- reinvest_enabled

or enough information to know whether checkbox is ON.

Preferred signature:

def render_invest_simulation_tab(
    inp: UserInput,
    config: MarketConfig,
    result: AnalysisResult,
    reinvest=None,
    no_reinvest=None,
    reinvest_enabled: bool = False,
) -> None:

Behavior:
- If no_reinvest is None or no_reinvest.timeline_df is empty:
    show warning and return.
- Always plot no_reinvest portfolio value curve.
- If reinvest_enabled is True and reinvest is not None and reinvest.timeline_df is not empty:
    also plot reinvest portfolio value curve on the same chart.
- Optionally plot total external invested baseline if the column exists.

5. Chart function

If an investment comparison chart function already exists, update it.

If not, add one in global_cup/charts.py:

investment_simulation_chart(
    inp,
    config,
    no_reinvest_df,
    reinvest_df=None,
    show_reinvest: bool = False,
)

Expected chart:
- Plotly line chart.
- x-axis = Date or index.
- y-axis = portfolio value.
- no-reinvest label:
  "배당 미재투자"
- reinvest label:
  "배당 재투자"
- baseline label:
  "총 외부 투자금" if available.
- Height around 660.
- Use existing project chart style as much as possible.
- Be robust to column names by inspecting current timeline_df columns.

6. Update app.py

Call:

render_invest_simulation_tab(
    user_input,
    config,
    analysis,
    reinvest=reinvest_result,
    no_reinvest=no_reinvest_result,
    reinvest_enabled=reinvest_enabled,
)

Use the actual checkbox variable name already present in app.py.

7. Do not change these

Do NOT modify:
- calculation logic unless strictly necessary
- market config
- analysis
- price tab
- dividend tab
- existing dividend reinvest tab behavior
- backup/archive logic

8. Validation

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile \
    app.py \
    global_cup/ui.py \
    global_cup/charts.py \
    global_cup/dividend_reinvest.py

If available:

python3 -m pytest -q

If pytest fails due to existing unrelated sys.exit in test_formatting_display.py, report clearly.

9. Runtime sanity check

The intended visual result:

Checkbox OFF:
- left summary = no-reinvest
- simulation graph = one curve: 배당 미재투자

Checkbox ON:
- left summary = reinvest
- simulation graph = two curves:
  - 배당 미재투자
  - 배당 재투자

10. Final report

Print:
- backup directory path
- modified files
- validation results
- explanation of final behavior
- whether a new chart function was added or an existing one was updated

---

## Completion Summary

### Backup
- `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_reinvest_overlay_20260614_142324/`
  - `app.py`
  - `global_cup/ui.py`
  - `global_cup/charts.py`
  - `global_cup/dividend_reinvest.py`

### Modified files
- `global_cup_refactored/app.py`
- `global_cup_refactored/global_cup/ui.py`
- `global_cup_refactored/global_cup/charts.py`

`dividend_reinvest.py` was not modified — its calculation logic is unchanged.

### New chart function (added — not a rename of the old one)
`investment_simulation_chart(inp, config, no_reinvest_df, reinvest_df=None, show_reinvest=False)` in `global_cup/charts.py`.

Traces:
- `총 외부 투자금` — dashed gray baseline (when `External Invested` column present in `no_reinvest_df`).
- `배당 미재투자` — orange `#ca6702`, width 3. **Always plotted.**
- `배당 재투자` — `config.line` (market color), width 4. **Only plotted when `show_reinvest=True` and `reinvest_df` is non-empty.**

Height 660, hovermode `x unified`, `_LAYOUT_BASE` and `_AXIS` reused for visual consistency. Title flips between `"배당 미재투자 시뮬레이션"` and `"배당 재투자 vs 미재투자"` depending on overlay state.

The old `investment_comparison_chart` was kept in `charts.py` for backwards compatibility (no callers now, but the function was not removed because the prompt says calculation/chart behavior is preserved unless strictly necessary).

### `render_invest_simulation_tab` (`global_cup/ui.py`)
New signature:
```python
def render_invest_simulation_tab(
    inp, config, result,
    reinvest=None,
    no_reinvest=None,
    reinvest_enabled: bool = False,
) -> None:
```
- Subtitle "투자 시뮬레이션".
- Caption: "기준은 항상 배당 미재투자입니다. '배당 재투자' 체크 시 재투자 곡선이 같은 차트에 함께 표시됩니다."
- Returns early with warning if `no_reinvest` missing/empty.
- Computes `show_reinvest = reinvest_enabled and reinvest is not None and not reinvest.timeline_df.empty`.
- Delegates to `investment_simulation_chart`.

### `app.py` call site
```python
with invest_result_tab:
    render_invest_simulation_tab(
        user_input,
        config,
        analysis,
        reinvest=reinvest_result,
        no_reinvest=no_reinvest_result,
        reinvest_enabled=reinvest_enabled,
    )
```
The left summary and 배당 재투자 tab still receive `selected_result` (untouched), preserving step 016's behavior. `reinvest_enabled` is the same variable already extracted from `reinvest_params["reinvest_enabled"]`.

### Behavior matrix

| Checkbox | Left summary | Simulation chart |
| --- | --- | --- |
| OFF | no-reinvest result | baseline (`총 외부 투자금`) + `배당 미재투자` |
| ON | reinvest result | baseline + `배당 미재투자` + `배당 재투자` overlay |

### Validation
- `python3 -m py_compile app.py global_cup/ui.py global_cup/charts.py global_cup/dividend_reinvest.py` → **OK**.
- Import + signature inspection of `render_invest_simulation_tab` and `investment_simulation_chart` → **OK** (Streamlit "No runtime found" warnings are harmless).
- `python3 -m pytest -q` → **pre-existing INTERNALERROR**, unchanged from step 016: `test_formatting_display.py:71` calls `sys.exit(...)` at module import time. Unrelated to this step.

### Preserved (untouched)
- `selected_result` selection, `render_reinvest_summary_left`, `render_dividend_reinvest_tab` (still uses `selected_result`).
- `dividend_reinvest.py` backtest engine.
- `investment_comparison_chart` is retained in `charts.py` for any future use.
- Market config, analysis, price tab, dividend tab, trigger/zigzag logic.
