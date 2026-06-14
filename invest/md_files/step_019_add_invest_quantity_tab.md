# Step 019 — Add 투자 수량 tab with yearly share-quantity bar chart

**Date:** 2026-06-14
**Working directory:** /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

**Note on numbering:** The prompt example named this `step_018_...`, but `step_018_add_share_quantity_bar_chart.md` already exists. Filed as step 019 to keep numbering monotonic.

---

## Original Prompt

You are working in:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before making changes, create a new archive prompt file under:

/home/zealatan/MARKETING_ORC/invest/md_files

Use the next step number, for example:

step_018_add_invest_quantity_tab.md

Goal:
Add a new tab next to "투자 시뮬레이션" called "투자 수량".

Final tab order should be:

가격 / 전고점 / 트리거
투자 시뮬레이션
투자 수량
배당
배당 재투자

Behavior:
The new "투자 수량" tab should show a large year-by-year bar chart of stock/share holdings.

Checkbox behavior:
There is already a global checkbox "배당 재투자".

OFF:
- summary table = no-reinvest result
- 투자 시뮬레이션 graph = no-reinvest only
- 투자 수량 graph = no-reinvest yearly share quantity only

ON:
- summary table = reinvest result
- 투자 시뮬레이션 graph = no-reinvest baseline + reinvest overlay
- 투자 수량 graph = stacked yearly share quantity:
  - base = no-reinvest yearly shares
  - extra = max(reinvest yearly shares - no_reinvest yearly shares, 0)

Important:
Do NOT create a small side chart inside 투자 시뮬레이션.
Create a separate full-size tab/section called "투자 수량".
The chart should be similar in size to the existing 투자 시뮬레이션 graph.

Tasks:

1. Backup
Create timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_invest_quantity_tab_YYYYMMDD_HHMMSS

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
- render_invest_simulation_tab(...)
- reinvest_result
- no_reinvest_result
- reinvest_enabled checkbox variable
- timeline_df or annual_df columns containing share quantity

3. Add chart function in charts.py
Add a function such as:

investment_quantity_chart(
    inp,
    config,
    no_reinvest,
    reinvest=None,
    show_reinvest: bool = False,
)

It should:
- Use Plotly.
- Use year as x-axis.
- Use share quantity as y-axis.
- Use yearly values, not only final value.
- Extract yearly share quantities from timeline_df or annual_df.
- Prefer end-of-year total shares if timeline_df has dates.
- If using timeline_df:
  - convert Date/index to year
  - group by year
  - take last Total Shares per year
- For no_reinvest:
  base_shares_by_year
- For reinvest:
  reinvest_shares_by_year
  extra_shares_by_year = max(reinvest_shares - base_shares, 0)
- Checkbox OFF:
  plot only base shares.
- Checkbox ON:
  stacked bar:
    기본 보유수량
    배당 재투자 추가수량

Labels:
- title: "연도별 보유 수량"
- base label: "기본 보유수량"
- extra label: "배당 재투자 추가수량"
- y-axis: "Shares"
- x-axis: "Year"

Height:
- around 660, same as 투자 시뮬레이션 chart.

Robustness:
- Inspect actual timeline_df / annual_df columns.
- Do not assume exact column names without checking.
- If no usable share quantity column exists, show a clear Streamlit warning in the UI function.

4. Add UI function in ui.py
Add:

render_invest_quantity_tab(
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
  st.subheader("연도별 보유 수량")
- Render caption:
  "배당 재투자 여부에 따른 연도별 주식 보유 수량 변화를 표시합니다."
- Render investment_quantity_chart(...)
- Pass reinvest only if available.
- Pass show_reinvest=reinvest_enabled.

5. Update app.py
Modify imports from global_cup.ui to include:

render_invest_quantity_tab

Modify tabs from current version to:

price_tab, invest_result_tab, invest_quantity_tab, dividend_tab, reinvest_tab = st.tabs([
    "가격 / 전고점 / 트리거",
    "투자 시뮬레이션",
    "투자 수량",
    "배당",
    "배당 재투자",
])

Add:

with invest_quantity_tab:
    render_invest_quantity_tab(
        user_input,
        config,
        analysis,
        no_reinvest=no_reinvest_result,
        reinvest=reinvest_result,
        reinvest_enabled=reinvest_enabled,
    )

Keep existing 투자 시뮬레이션 behavior unchanged.

6. Preserve existing behavior
Do NOT change:
- summary table behavior
- checkbox behavior
- existing investment simulation graph behavior
- dividend tab
- dividend reinvest tab
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

Expected UX:

Checkbox OFF:
- 투자 수량 tab shows yearly no-reinvest share quantity bars.

Checkbox ON:
- 투자 수량 tab shows stacked yearly bars:
  base no-reinvest shares + additional shares created by dividend reinvestment.

---

## Completion Summary

### Interpretation note
The prompt says: "Do NOT create a small side chart inside 투자 시뮬레이션. Create a separate full-size tab/section". The previous step (018) had introduced exactly that small side share-quantity chart inside 투자 시뮬레이션. I read the new directive as a pivot: **remove the side chart and move the share-quantity view into the new dedicated full-size 투자 수량 tab**. The `share_quantity_comparison_bar_chart` function in `charts.py` was left defined (orphaned) — it can be deleted later if not reused.

### Backup
- `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_invest_quantity_tab_20260614_151034/`
  - `app.py`
  - `global_cup/ui.py`
  - `global_cup/charts.py`
  - `global_cup/dividend_reinvest.py`

### Modified files
- `global_cup_refactored/global_cup/charts.py` — added `_yearly_total_shares(...)` helper and `investment_quantity_chart(...)`.
- `global_cup_refactored/global_cup/ui.py` — imported new chart, added `render_invest_quantity_tab(...)`, reverted the two-column side-chart layout in `render_invest_simulation_tab` back to a single full-width line chart.
- `global_cup_refactored/app.py` — imported `render_invest_quantity_tab`, expanded `st.tabs(...)` to 5 entries with 투자 수량 in position 3, added its `with`-block.

`dividend_reinvest.py` was not modified.

### New chart function
`investment_quantity_chart(inp, config, no_reinvest, reinvest=None, show_reinvest=False) -> go.Figure | None`

- Pulls `timeline_df["Date"]` + `timeline_df["Total Shares"]`, groups by year, takes the last value per year (end-of-year holdings).
- OFF: single trace `기본 보유수량` (gray `#8a8f7a`).
- ON: stacked — `기본 보유수량` + `배당 재투자 추가수량` (`config.line`, market color). Extra per year is `max(reinvest_yearly - base_yearly, 0)` after outer-join to align years.
- Returns `None` if `Total Shares`/`Date` columns are missing or `timeline_df` is empty; the UI emits a warning instead of rendering an empty chart.
- Title `"연도별 보유 수량"`, x-axis `"Year"` (categorical), y-axis `"Shares"`, height 660, `barmode="stack"`, `hovermode="x unified"`, layout shares `_LAYOUT_BASE`/`_AXIS` with existing charts.

Numerical smoke test (years 2022–2024; no-reinvest end-of-year `[25, 45, 65]`, reinvest end-of-year `[27, 52, 78]`):
- OFF emits one trace `[25.0, 45.0, 65.0]`.
- ON emits base `[25.0, 45.0, 65.0]` + extra `[2.0, 7.0, 13.0]`. Verified.

### New tab renderer
`render_invest_quantity_tab(inp, config, result, no_reinvest=None, reinvest=None, reinvest_enabled=False)`:
- Subheader `"연도별 보유 수량"`, caption `"배당 재투자 여부에 따른 연도별 주식 보유 수량 변화를 표시합니다."`
- Early-return with warning when no_reinvest is missing/empty or when the chart helper returns `None`.
- Otherwise renders the chart full-width via `st.plotly_chart(fig, use_container_width=True)`.

### Tab order (final)
1. `가격 / 전고점 / 트리거`
2. `투자 시뮬레이션`
3. `투자 수량` ← new
4. `배당`
5. `배당 재투자`

### Behavior matrix

| Checkbox | Left summary | 투자 시뮬레이션 chart | 투자 수량 chart |
| --- | --- | --- | --- |
| OFF | no-reinvest | `배당 미재투자` line (+ external invested baseline) | yearly `기본 보유수량` bars |
| ON | reinvest | `배당 미재투자` + `배당 재투자` overlay | yearly stacked: `기본 보유수량` + `배당 재투자 추가수량` |

### Validation
- `python3 -m py_compile app.py global_cup/ui.py global_cup/charts.py global_cup/dividend_reinvest.py` → **OK**.
- Function-level smoke test on `investment_quantity_chart` with synthetic 3-year data → correct trace names, correct yearly aggregation, correct extra-share math. **OK**.
- `python3 -m pytest -q` → **pre-existing INTERNALERROR** in `test_formatting_display.py:71` (`sys.exit(...)` at module import time). Same failure seen in steps 016 / 017 / 018. Unrelated to this change.

### Preserved (untouched)
- Checkbox state, `selected_result` selection, left summary, dividend tab, detailed 배당 재투자 tab, price tab.
- `run_dividend_reinvest_backtest` and all analysis logic.
- The portfolio-value line chart in 투자 시뮬레이션 (now back to full-width single chart).
