# Step 013 — Add "투자 시뮬레이션" Tab

## Prompt (verbatim)

You are working in this project:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before modifying files, create a new prompt/archive file under:
/home/zealatan/MARKETING_ORC/invest/md_files
Use a step-numbered filename such as:
step_01_add_invest_simulation_tab.md
The file must contain this full prompt and a short implementation summary after completion.

Goal:
Back up the current code, then add a new Streamlit tab called "투자 시뮬레이션" between "가격 / 전고점 / 트리거" and "배당".

Current app structure:
- Main entrypoint: /home/zealatan/MARKETING_ORC/invest/global_cup_refactored/app.py
- UI functions: /home/zealatan/MARKETING_ORC/invest/global_cup_refactored/global_cup/ui.py
- Existing charts include:
  - price_chart
  - reinvest_timeline_chart
  - share_count_chart
- app.py already computes:
  - analysis = run_analysis(user_input)
  - reinvest_result = run_dividend_reinvest_backtest(...)

Tasks:

1. Backup first
Create a timestamped backup directory, for example:
/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_invest_sim_YYYYMMDD_HHMMSS

Copy at least:
- app.py
- global_cup/ui.py

Do not proceed unless backup succeeds.

2. Modify global_cup/ui.py
Add a new function:

def render_invest_simulation_tab(
    inp: UserInput,
    config: MarketConfig,
    result: AnalysisResult,
    reinvest=None,
) -> None:

Behavior:
- If reinvest is None, show st.info("투자 시뮬레이션 결과를 계산할 수 없습니다.") and return.
- Add two checkboxes:
  - "Show ZigZag H/L markers", key=f"sim_show_zigzag_{config.key}", default True
  - "Show Trigger Buy markers", key=f"sim_show_buys_{config.key}", default True
- Render the normal price chart first using price_chart(inp, config, result, show_zigzag=..., show_buys=...)
- Set price chart height around 430.
- Then render the reinvest timeline chart using reinvest_timeline_chart(inp, config, reinvest.timeline_df)
- Set reinvest chart height around 430.
- If reinvest.timeline_df is empty, show st.warning("배당 재투자 타임라인 데이터가 없습니다.") and return after price chart.
- Keep styling consistent with existing tabs.
- Do not remove existing render_dividend_reinvest_tab.

3. Modify app.py imports
Add render_invest_simulation_tab to the import list from global_cup.ui.

4. Modify app.py tabs
Current tabs are approximately:
price_tab, dividend_tab, reinvest_tab = st.tabs([
    "가격 / 전고점 / 트리거",
    "배당",
    "배당 재투자",
])

Change to:
price_tab, invest_result_tab, dividend_tab, reinvest_tab = st.tabs([
    "가격 / 전고점 / 트리거",
    "투자 시뮬레이션",
    "배당",
    "배당 재투자",
])

Add:

with invest_result_tab:
    render_invest_simulation_tab(
        user_input,
        config,
        analysis,
        reinvest=reinvest_result,
    )

Keep existing price/dividend/reinvest behavior.

5. Clean up
- Do not leave duplicated old commented-out versions unless already present and harmless.
- Preserve existing UI layout and CSS.
- Do not change data calculation logic.
- Do not change run_dividend_reinvest_backtest.
- Do not change market_config or analysis logic.

6. Validation
Run:
cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored
python3 -m py_compile app.py global_cup/ui.py

If available, also run:
python3 -m pytest -q

If pytest is not configured or fails due to unrelated existing tests, report clearly.

7. Final report
Print:
- backup directory path
- modified files
- exact validation commands and results
- short summary of the new tab behavior

## Implementation Summary

### Backup
- Directory: `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_invest_sim_20260614_113914`
- Files copied:
  - `app.py`
  - `global_cup/ui.py`

### Modified files
- `global_cup_refactored/global_cup/ui.py` — added `render_invest_simulation_tab(inp, config, result, reinvest=None)` immediately before `render_dividend_reinvest_tab` (existing reinvest tab kept intact).
- `global_cup_refactored/app.py` — added `render_invest_simulation_tab` to the `global_cup.ui` import list; expanded the `st.tabs(...)` call to 4 tabs and added the `with invest_result_tab:` block between price and dividend tabs.

### Validation
- `cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored && python3 -m py_compile app.py global_cup/ui.py` → **OK** (exit 0).
- `python3 -c "from global_cup.ui import render_invest_simulation_tab"` → **OK** (function imports cleanly).
- `python3 -m pytest -q` → **No tests ran**. Pre-existing `test_formatting_display.py` calls `sys.exit(...)` at module import time, which pytest treats as an INTERNALERROR. Unrelated to this change.

### New tab behavior
- Title: `투자 시뮬레이션`, placed between `가격 / 전고점 / 트리거` and `배당`.
- Guards: returns `st.info("투자 시뮬레이션 결과를 계산할 수 없습니다.")` when `reinvest is None`.
- Two checkboxes (both default `True`, keys scoped by `config.key`):
  - `Show ZigZag H/L markers` → `sim_show_zigzag_{config.key}`
  - `Show Trigger Buy markers` → `sim_show_buys_{config.key}`
- Renders `price_chart(inp, config, result, show_zigzag=..., show_buys=...)` at height ≈ 430.
- If `reinvest.timeline_df` is empty, shows `st.warning("배당 재투자 타임라인 데이터가 없습니다.")` and returns after the price chart.
- Otherwise renders `reinvest_timeline_chart(inp, config, reinvest.timeline_df)` at height ≈ 430.
- No changes to data, market_config, analysis, or `run_dividend_reinvest_backtest` logic. Existing `render_dividend_reinvest_tab` and the "배당 재투자" tab are unchanged.
