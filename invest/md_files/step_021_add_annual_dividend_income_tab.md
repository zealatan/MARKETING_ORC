# Step 021 — Add 연배당금 tab with yearly dividend-income bar chart

**Date:** 2026-06-14
**Working directory:** /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

**Note on numbering:** Prompt example said `step_020_...`; step 020 was already used by the tab reorder/remove task. Filed as 021.

---

## Original Prompt

You are working in:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before making changes, create a new archive prompt file under:

/home/zealatan/MARKETING_ORC/invest/md_files

Use the next step number, for example:

step_020_add_annual_dividend_income_tab.md

Goal:
Add a new tab next to "투자 수량" called "연배당금".

Final tab order should be:

가격 / 전고점 / 트리거
배당
투자 시뮬레이션
투자 수량
연배당금

Behavior:
The new "연배당금" tab should show a large year-by-year bar chart of annual dividend income based on the number of shares held each year.

Checkbox behavior:
There is already a global checkbox "배당 재투자".

OFF:
- summary table = no-reinvest result
- 투자 시뮬레이션 graph = no-reinvest only
- 투자 수량 graph = no-reinvest yearly shares only
- 연배당금 graph = no-reinvest annual dividend income only

ON:
- summary table = reinvest result
- 투자 시뮬레이션 graph = no-reinvest baseline + reinvest overlay
- 투자 수량 graph = stacked yearly shares:
  - base = no-reinvest yearly shares
  - extra = max(reinvest yearly shares - no_reinvest yearly shares, 0)
- 연배당금 graph = stacked yearly annual dividend income:
  - base = no-reinvest annual dividend income
  - extra = max(reinvest annual dividend income - no_reinvest annual dividend income, 0)

Important:
Do NOT create a small chart inside 투자 시뮬레이션.
Create a separate full-size tab/section called "연배당금".
The chart should be similar in size to the existing 투자 시뮬레이션 and 투자 수량 graphs.

Definition:
Annual dividend income should be based on:
- shares held in that year
- dividend per share for that year
- tax rate already applied if available

Prefer net dividend income if the backtest already tracks net dividends.
If both gross and net dividend columns exist, use net dividend for consistency with current summary.
If only gross exists, use gross and clearly name it accordingly.

Expected chart:
Checkbox OFF:
- one bar per year = no-reinvest annual dividend income

Checkbox ON:
- stacked bar:
  - base = no-reinvest annual dividend income
  - extra = reinvest annual dividend income - no-reinvest annual dividend income

Labels:
- title: "연도별 연배당금"
- base label: "기본 연배당금"
- extra label: "배당 재투자 추가 연배당금"
- y-axis: currency-aware label, e.g. "Dividend Income"
- x-axis: "Year"

Tasks:

1. Backup
Create timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_annual_dividend_income_tab_YYYYMMDD_HHMMSS

Backup at minimum:
- app.py
- global_cup/ui.py
- global_cup/charts.py
- global_cup/dividend_reinvest.py

2. Inspect current code
Inspect:
- app.py
- global_cup/ui.py
- global_cup/charts.py
- global_cup/dividend_reinvest.py

Find:
- tab creation in app.py
- render_invest_quantity_tab(...)
- investment_quantity_chart(...)
- reinvest_result
- no_reinvest_result
- reinvest_enabled checkbox variable
- annual_df columns
- timeline_df columns

3. Add chart function in charts.py
Add a function such as:

annual_dividend_income_chart(
    inp,
    config,
    no_reinvest,
    reinvest=None,
    show_reinvest: bool = False,
)

It should:
- Use Plotly.
- Use year as x-axis.
- Use annual dividend income as y-axis.
- Use yearly values, not only final value.
- Prefer annual_df if it has annual dividend income columns.
- Else derive from timeline_df if possible.
- Inspect actual columns first.
- For no_reinvest:
  base_income_by_year
- For reinvest:
  reinvest_income_by_year
  extra_income_by_year = max(reinvest_income - base_income, 0)
- Checkbox OFF:
  plot only base annual dividend income.
- Checkbox ON:
  stacked bar:
    기본 연배당금
    배당 재투자 추가 연배당금

Column selection priority:
1. "Net Dividend"
2. "Cumulative Net Dividend" yearly difference
3. "Gross Dividend"
4. Derived dividend income if enough data exists

Use currency formatting on y-axis and hover if existing chart helpers support it.

Height:
- around 660, same as 투자 시뮬레이션 chart.

Robustness:
- If no usable dividend income column exists, return an empty or warning-safe figure, and the UI function should show a clear warning.

4. Add UI function in ui.py
Add:

render_annual_dividend_income_tab(
    inp: UserInput,
    config: MarketConfig,
    result: AnalysisResult,
    no_reinvest=None,
    reinvest=None,
    reinvest_enabled: bool = False,
) -> None:

Behavior:
- If no_reinvest is None, show warning and return.
- Render subheader:
  st.subheader("연도별 연배당금")
- Render caption:
  "보유 수량과 배당 데이터를 기반으로 연도별 배당금을 표시합니다."
- Render annual_dividend_income_chart(...)
- Pass reinvest only if available.
- Pass show_reinvest=reinvest_enabled.

5. Update app.py
Modify imports from global_cup.ui to include:

render_annual_dividend_income_tab

Modify tabs to:

price_tab, dividend_tab, invest_result_tab, invest_quantity_tab, annual_dividend_income_tab = st.tabs([
    "가격 / 전고점 / 트리거",
    "배당",
    "투자 시뮬레이션",
    "투자 수량",
    "연배당금",
])

Add:

with annual_dividend_income_tab:
    render_annual_dividend_income_tab(
        user_input,
        config,
        analysis,
        no_reinvest=no_reinvest_result,
        reinvest=reinvest_result,
        reinvest_enabled=reinvest_enabled,
    )

Keep existing investment simulation and investment quantity behavior unchanged.

6. Preserve existing behavior
Do NOT change:
- summary table behavior
- checkbox behavior
- existing investment simulation graph behavior
- existing investment quantity graph behavior
- dividend tab
- price tab
- analysis logic
- dividend calculation logic unless absolutely necessary

7. Validation
Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile \
    app.py \
    global_cup/ui.py \
    global_cup/charts.py \
    global_cup/dividend_reinvest.py

If possible:

python3 -m pytest -q

If pytest fails due to existing unrelated sys.exit in test_formatting_display.py, report clearly.

8. Final report
Print:
- backup directory path
- modified files
- validation results
- exact tab order
- final behavior summary
- which dividend income column was used

Expected UX:

Checkbox OFF:
- 연배당금 tab shows yearly no-reinvest annual dividend income bars.

Checkbox ON:
- 연배당금 tab shows stacked yearly bars:
  base no-reinvest annual dividend income
  + additional annual dividend income created by dividend reinvestment.

---

## Completion Summary

### Backup
- `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_annual_dividend_income_tab_20260614_172758/`
  - `app.py`
  - `global_cup/ui.py`
  - `global_cup/charts.py`
  - `global_cup/dividend_reinvest.py`

### Modified files
- `global_cup_refactored/global_cup/charts.py` — imported `get_market_rule` and `get_currency_symbol`; added private helper `_yearly_dividend_income(result)` and public `annual_dividend_income_chart(...)`.
- `global_cup_refactored/global_cup/ui.py` — added `annual_dividend_income_chart` to chart imports; added `render_annual_dividend_income_tab(...)`.
- `global_cup_refactored/app.py` — imported `render_annual_dividend_income_tab`; expanded `st.tabs(...)` to 5 entries with `연배당금` last; added its `with` block wired to both results + `reinvest_enabled`.

`dividend_reinvest.py` was not modified — `annual_df["Net Dividend"]` already exists from the backtest.

### Dividend income column used
**`Net Dividend`** from `result.annual_df` — already aggregated per year by `run_dividend_reinvest_backtest` (`dividend_reinvest.py:196-201`), already net of tax, and consistent with the left summary's `Cumulative Net Dividend` semantics. The selector helper `_yearly_dividend_income` falls back to a yearly diff of `Cumulative Net Dividend`, then `Gross Dividend`, then returns empty — and the chart returns `None` so the UI shows a clear warning.

### New chart function
`annual_dividend_income_chart(inp, config, no_reinvest, reinvest=None, show_reinvest=False) -> go.Figure | None`

- Extracts year + income from `annual_df` via `_yearly_dividend_income`.
- OFF: single trace `기본 연배당금` (gray `#8a8f7a`).
- ON: stacked — `기본 연배당금` + `배당 재투자 추가 연배당금` (`config.line`, market color); extra per year = `max(reinvest_yearly - base_yearly, 0)` after outer-join + fillna(0).
- Currency-aware: y-axis title `Dividend Income ({CURRENCY})`, `tickprefix=` market symbol, thousands separators, formatted hover.
- Title `"연도별 연배당금"`, x-axis `Year` (categorical), height 660, `barmode="stack"`, `hovermode="x unified"`.
- Returns `None` when no usable column exists; UI shows a warning instead.

### New UI renderer
`render_annual_dividend_income_tab(inp, config, result, no_reinvest=None, reinvest=None, reinvest_enabled=False)`:
- Subheader `"연도별 연배당금"`, caption `"보유 수량과 배당 데이터를 기반으로 연도별 배당금을 표시합니다."`
- Early-returns with warning when `no_reinvest is None` or when the chart helper returns `None`.

### Tab order (final)
1. `가격 / 전고점 / 트리거`
2. `배당`
3. `투자 시뮬레이션`
4. `투자 수량`
5. `연배당금` ← new

### Behavior matrix

| Checkbox | Left summary | 투자 시뮬레이션 | 투자 수량 | 연배당금 |
| --- | --- | --- | --- | --- |
| OFF | no-reinvest | `배당 미재투자` line | `기본 보유수량` bars | `기본 연배당금` bars |
| ON | reinvest | `배당 미재투자` + `배당 재투자` overlay | stacked `기본 보유수량` + `배당 재투자 추가수량` | stacked `기본 연배당금` + `배당 재투자 추가 연배당금` |

### Validation
- `python3 -m py_compile app.py global_cup/ui.py global_cup/charts.py global_cup/dividend_reinvest.py` → **OK**.
- Function-level smoke test on `_yearly_dividend_income` (returns `Net Dividend`) and `annual_dividend_income_chart` (OFF emits `[100, 150, 200]`; ON emits base `[100, 150, 200]` + extra `[10, 30, 60]` for reinvest `[110, 180, 260]`). Correct.
- `python3 -m pytest -q` → **pre-existing INTERNALERROR** in `test_formatting_display.py:71` (`sys.exit(...)` at module import). Same failure as prior steps. Unrelated to this work.

### Preserved (untouched)
- Left summary, checkbox, `selected_result` logic.
- 가격 / 전고점 / 트리거, 배당, 투자 시뮬레이션, 투자 수량 tab behaviors.
- `run_dividend_reinvest_backtest` and analysis logic.
