# Step 018 — Add share quantity bar chart to 투자 시뮬레이션 tab

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

step_018_add_share_quantity_bar_chart.md

The file must contain this entire prompt and a completion summary.

Goal
Extend the "투자 시뮬레이션" tab by adding a stock quantity bar chart next to the existing portfolio value simulation chart.

Current behavior:
- There is a checkbox "배당 재투자".
- Left summary updates based on checkbox:
  - OFF = no-reinvest result
  - ON = reinvest result
- Portfolio value chart behavior:
  - OFF = show no-reinvest curve only
  - ON = show no-reinvest curve + reinvest curve overlay

New desired behavior:
Add a second chart section next to the portfolio value chart:

"보유 수량 비교"

This should be a bar chart showing stock/share quantity.

Checkbox OFF:
- Show only no-reinvest share quantity.

Checkbox ON:
- Show no-reinvest share quantity as the base bar.
- Add the extra share quantity gained by dividend reinvestment as a stacked bar segment on top of / next to the base.
- This visually answers:
  "How many additional shares did dividend reinvestment create?"

Important:
Do NOT change the left summary behavior.
Do NOT remove the existing portfolio value chart.
Do NOT change calculation logic unless necessary.

Expected visual concept:
If:
- no_reinvest final shares = 100
- reinvest final shares = 128

Then bar chart should show:
- base: 100 shares
- additional from dividend reinvestment: 28 shares

Labels:
- "기본 보유수량"
- "배당 재투자 추가수량"

If checkbox OFF:
- Only show "기본 보유수량".

If checkbox ON:
- Show stacked bars:
  - base = no-reinvest final shares
  - added = max(reinvest final shares - no_reinvest final shares, 0)

Tasks

1. Backup
Create a timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_share_quantity_chart_YYYYMMDD_HHMMSS

Backup at minimum:
- app.py
- global_cup/ui.py
- global_cup/charts.py
- global_cup/dividend_reinvest.py

Do not proceed unless backup succeeds.

2. Inspect current code
Inspect:
- global_cup/ui.py
- global_cup/charts.py
- global_cup/dividend_reinvest.py
- app.py

Find:
- render_invest_simulation_tab(...)
- current portfolio simulation chart function
- timeline_df final shares column
- reinvest.summary["Final Shares"]
- no_reinvest.summary["Final Shares"]

3. Add bar chart function
Prefer adding a new function in global_cup/charts.py:

share_quantity_comparison_bar_chart(
    config,
    no_reinvest,
    reinvest=None,
    show_reinvest: bool = False,
)

The function may accept result objects or summary dicts depending on current structure.

It should:
- Use Plotly.
- Read final shares from:
  - no_reinvest.summary["Final Shares"]
  - reinvest.summary["Final Shares"]
- Compute:
  base_shares = no_reinvest final shares
  extra_shares = max(reinvest final shares - no_reinvest final shares, 0)
- If show_reinvest is False:
  plot only base_shares.
- If show_reinvest is True:
  plot a stacked bar:
    base_shares + extra_shares
- Use clear Korean labels:
  - "기본 보유수량"
  - "배당 재투자 추가수량"
- Title:
  "보유 수량 비교"
- y-axis:
  "Shares"
- Height around 320 to 380.
- Use layout consistent with existing charts.
- Do not hardcode colors unless the project already uses explicit color convention. If needed, choose visually distinct but consistent colors.

4. Update render_invest_simulation_tab
In global_cup/ui.py, update layout so investment simulation tab has two sections.

Preferred layout:
- Top/full or left large: portfolio value simulation chart
- Right or below: share quantity bar chart

Suggested Streamlit layout:

col_value, col_shares = st.columns([2.1, 1.0], gap="large")

with col_value:
    render portfolio value chart

with col_shares:
    render share quantity bar chart

If screen width is tight, this is still acceptable.

Behavior:
- Portfolio chart behavior remains:
  - OFF: no-reinvest only
  - ON: no-reinvest + reinvest overlay
- Share quantity bar behavior:
  - OFF: no-reinvest final shares only
  - ON: no-reinvest base + reinvest-added shares

5. Update imports
If adding chart function to charts.py, import it in ui.py.

6. Preserve existing behavior
Do NOT change:
- app.py checkbox logic unless needed to pass reinvest_enabled
- summary table behavior
- run_dividend_reinvest_backtest
- price tab
- dividend tab
- detailed dividend reinvest tab

7. Validation
Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile \
    app.py \
    global_cup/ui.py \
    global_cup/charts.py \
    global_cup/dividend_reinvest.py

If available:

python3 -m pytest -q

If pytest fails due to pre-existing unrelated sys.exit in test_formatting_display.py, report clearly.

8. Runtime sanity check
Expected UI:

Checkbox OFF:
- Summary: no-reinvest
- Portfolio value graph: one line = 배당 미재투자
- Share bar chart: one bar/segment = 기본 보유수량

Checkbox ON:
- Summary: reinvest
- Portfolio value graph: two lines = 배당 미재투자 + 배당 재투자
- Share bar chart: stacked bar = 기본 보유수량 + 배당 재투자 추가수량

9. Final report
Print:
- backup directory path
- modified files
- validation results
- chart function added/updated
- final UX summary

---

## Completion Summary

### Backup
- `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_share_quantity_chart_20260614_150117/`
  - `app.py`
  - `global_cup/ui.py`
  - `global_cup/charts.py`
  - `global_cup/dividend_reinvest.py`

### Modified files
- `global_cup_refactored/global_cup/charts.py` — added `share_quantity_comparison_bar_chart`.
- `global_cup_refactored/global_cup/ui.py` — imported new chart, restructured `render_invest_simulation_tab` into a two-column layout.

`app.py` and `dividend_reinvest.py` were NOT modified — the existing checkbox plumbing (`reinvest_enabled`) and `summary["Final Shares"]` are sufficient.

### Chart function added
`share_quantity_comparison_bar_chart(config, no_reinvest, reinvest=None, show_reinvest=False)` — Plotly stacked bar.

- Reads `no_reinvest.summary["Final Shares"]` and (when overlay is on) `reinvest.summary["Final Shares"]`.
- `extra_shares = max(reinvest_shares - base_shares, 0)`.
- OFF: single bar `기본 보유수량` (gray `#8a8f7a`).
- ON: stacked — `기본 보유수량` + `배당 재투자 추가수량` (`config.line`, market-specific color).
- Title `"보유 수량 비교"`, y-axis `Shares`, height 360, hovermode `x`, layout shares `_LAYOUT_BASE`/`_AXIS` with existing charts.

Numerical smoke test (base 100, reinvest 128):
- OFF traces → `['기본 보유수량']` with `y=[100.0]`.
- ON traces → `['기본 보유수량', '배당 재투자 추가수량']` with `y=[100.0, 28.0]`.

### `render_invest_simulation_tab` layout
Streamlit `st.columns([2.1, 1.0], gap="large")`:
- Left (wider): `investment_simulation_chart` (existing portfolio value chart).
- Right (narrower): `share_quantity_comparison_bar_chart`.

The intro subheader/caption from step 017 are kept. Early-return on missing/empty `no_reinvest` still applies before either chart is rendered.

### Behavior matrix

| Checkbox | Left summary | Portfolio chart | Share bar chart |
| --- | --- | --- | --- |
| OFF | no-reinvest | baseline + `배당 미재투자` | `기본 보유수량` only |
| ON | reinvest | baseline + `배당 미재투자` + `배당 재투자` overlay | stacked: `기본 보유수량` + `배당 재투자 추가수량` |

### Validation
- `python3 -m py_compile app.py global_cup/ui.py global_cup/charts.py global_cup/dividend_reinvest.py` → **OK**.
- Function-level smoke test with synthetic `FakeResult` objects → **OK** (correct trace names and y-values for both states).
- `python3 -m pytest -q` → **pre-existing INTERNALERROR** in `test_formatting_display.py:71` (`sys.exit(...)` at module import). Same failure as steps 016 / 017. Unrelated to this change.

### Preserved (untouched)
- `app.py` checkbox/selection logic, `selected_result` flow.
- `render_reinvest_summary_left` and the left summary behavior.
- `run_dividend_reinvest_backtest` engine.
- Price tab, dividend tab, detailed 배당 재투자 tab.
- `investment_simulation_chart` and `investment_comparison_chart` (kept as-is).
