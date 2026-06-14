# Step 015 — Compare Reinvest vs No-Reinvest in "투자 시뮬레이션"

## Prompt (verbatim)

You are working in:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

Mandatory archival rule:
Before making any changes, create a new archive prompt file under:

/home/zealatan/MARKETING_ORC/invest/md_files

Use the next step number, for example:

step_015_compare_reinvest_vs_no_reinvest.md

The file must contain this entire prompt and a completion summary.

Goal
Improve the "투자 시뮬레이션" tab so it compares two investment scenarios in one chart:

1. Dividend reinvestment case
   - Dividends are taxed and then automatically reinvested.

2. No dividend reinvestment case
   - Dividends are taxed and accumulated as cash.
   - Dividends are NOT used to buy additional shares.
   - Monthly contributions and initial investment are still invested normally.

The chart should show both portfolio value curves under the same initial investment / monthly contribution / tax rate settings.

Definitions
- Reinvest case value:
  portfolio value = shares * price + available cash if the existing model tracks cash.
- No-reinvest case value:
  portfolio value = shares * price + accumulated net dividend cash.
- External invested amount should remain the same in both cases.
- Monthly contribution behavior should remain unchanged.

Important
Do NOT remove the existing dividend reinvestment tab.
Do NOT break the existing left-column summary.
Keep existing calculations backward-compatible.

Tasks

1. Backup
Create a timestamped backup directory under:

/home/zealatan/MARKETING_ORC/invest/backup_original/

Example:

global_cup_refactored_before_reinvest_compare_YYYYMMDD_HHMMSS

Backup at minimum:
- app.py
- global_cup/ui.py
- global_cup/dividend_reinvest.py
- global_cup/charts.py

Do not proceed unless backup succeeds.

2. Inspect current implementation
Inspect:
- global_cup/dividend_reinvest.py
- global_cup/charts.py
- global_cup/ui.py
- app.py

Find:
- run_dividend_reinvest_backtest(...)
- reinvest_timeline_chart(...)
- render_invest_simulation_tab(...)

3. Add no-reinvest scenario support
Prefer the least invasive design.

Option A, preferred:
Add an optional parameter to run_dividend_reinvest_backtest:

reinvest_dividends: bool = True

When True:
- Preserve current behavior exactly.

When False:
- Net dividends should be accumulated as cash.
- Do not buy shares using dividends.
- Monthly contribution purchases should still happen.
- Initial purchase should still happen.
- timeline_df should include enough columns to plot:
  - Portfolio Value
  - Total External Invested
  - Cumulative Net Dividend
  - Cash if applicable
  - Total Shares

Ensure the default True keeps all existing behavior unchanged.

Option B:
If modifying run_dividend_reinvest_backtest is risky, implement a separate helper:

run_dividend_no_reinvest_backtest(...)

with equivalent output structure.

Choose the safer approach after inspecting the code.

4. Update app.py
Currently app.py computes reinvest_result once.

Add a second calculation:

no_reinvest_result = run_dividend_reinvest_backtest(
    close=analysis.close,
    dividends=analysis.dividends,
    initial_amount=reinvest_params["initial_amount"],
    monthly_amount=reinvest_params["monthly_amount"],
    tax_rate_pct=reinvest_params["tax_rate_pct"],
    reinvest_dividends=False,
)

Keep existing reinvest_result with default/current behavior.

Pass both to the investment simulation tab:

render_invest_simulation_tab(
    user_input,
    config,
    analysis,
    reinvest=reinvest_result,
    no_reinvest=no_reinvest_result,
)

Do not pass no_reinvest into the existing detailed dividend reinvest tab unless needed.

5. Update render_invest_simulation_tab
Change signature to:

def render_invest_simulation_tab(
    inp: UserInput,
    config: MarketConfig,
    result: AnalysisResult,
    reinvest=None,
    no_reinvest=None,
) -> None:

Behavior:
- If reinvest is None, show info and return.
- If no_reinvest is None, show only the existing reinvest chart.
- If both exist, show one comparison chart:
  - Reinvest portfolio value
  - No-reinvest portfolio value
  - Optional: Total external invested as baseline

Add title:
st.subheader("투자 결과 비교")

Add caption:
"배당 재투자 여부에 따른 포트폴리오 가치 변화를 비교합니다."

6. Chart implementation
Prefer to add a new chart function in global_cup/charts.py:

investment_comparison_chart(inp, config, reinvest_df, no_reinvest_df)

It should:
- Use Plotly.
- Align both timeline DataFrames by date.
- Plot reinvest portfolio value.
- Plot no-reinvest portfolio value.
- Plot total external invested if the column exists.
- Use clear legend labels:
  - "배당 재투자"
  - "배당 미재투자"
  - "총 외부 투자금"
- Set clean layout consistent with existing charts.
- Height should be around 660.

If column names differ, infer robustly after inspecting timeline_df columns.

7. Preserve existing chart
Do not remove reinvest_timeline_chart.
The detailed "배당 재투자" tab can still use it.

8. Validation
Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python3 -m py_compile app.py global_cup/ui.py global_cup/charts.py global_cup/dividend_reinvest.py

If available:

python3 -m pytest -q

If pytest fails due to pre-existing unrelated sys.exit in test_formatting_display.py, report clearly.

9. Runtime smoke test
If possible, run a small Python import test:

python3 - <<'PY'
from global_cup.dividend_reinvest import run_dividend_reinvest_backtest
import inspect
print(inspect.signature(run_dividend_reinvest_backtest))
PY

Confirm that reinvest_dividends is available if Option A was used.

10. Final report
Print:
- backup directory path
- modified files
- whether Option A or Option B was used
- validation results
- final behavior summary

Expected final UX
The "투자 시뮬레이션" tab should show ONE chart comparing:

- 배당 재투자
- 배당 미재투자
- optionally total external invested

under the same initial investment, monthly contribution, and tax rate settings.

## Implementation Summary

### Backup
- Directory: `/home/zealatan/MARKETING_ORC/invest/backup_original/global_cup_refactored_before_reinvest_compare_20260614_122058`
- Files copied: `app.py`, `global_cup/ui.py`, `global_cup/dividend_reinvest.py`, `global_cup/charts.py`

### Approach chosen
**Option A** — extended `run_dividend_reinvest_backtest` with `reinvest_dividends: bool = True`.

Backward-compat invariants:
- New `cash` accumulator starts at 0 and stays 0 in the True path → `value = shares*price + cash` produces the exact same numbers as before.
- New `Cash` column is added to `timeline_df` for both modes; existing `reinvest_timeline_chart` only reads `Date / External Invested / Portfolio Value`, so it is unaffected.
- In the True path the event Type label is still `"Dividend Reinvest"`, so the left-column summary, `annual_df` aggregation, and existing reinvest tab tables are byte-identical.
- In the False path, dividend events are labeled `"Dividend Cash"`, `Shares Bought = 0`, `cash += net_dividend`. `annual_df` filter now includes both labels so the no-reinvest case still aggregates correctly (not surfaced in any UI yet, but kept consistent).

### Modified files
- `global_cup/dividend_reinvest.py` — added `reinvest_dividends` param, `cash` accumulator, `Cash` timeline column, branched dividend handling, updated `final_value` and `annual_df` filter.
- `global_cup/charts.py` — added `investment_comparison_chart(inp, config, reinvest_df, no_reinvest_df)`. Plots `총 외부 투자금` (baseline dotted), `배당 미재투자`, `배당 재투자`. Height 660. Uses same `_LAYOUT_BASE` + `_AXIS` styling as the other charts.
- `global_cup/ui.py` — imported `investment_comparison_chart`. Extended `render_invest_simulation_tab` with `no_reinvest=None`. Title now `"투자 결과 비교"` with caption `"배당 재투자 여부에 따른 포트폴리오 가치 변화를 비교합니다."`. Falls back to the single `reinvest_timeline_chart` when `no_reinvest` is missing/empty.
- `app.py` — added `no_reinvest_result = run_dividend_reinvest_backtest(..., reinvest_dividends=False)`. Passes both to `render_invest_simulation_tab`. Existing reinvest tab and left-summary path unchanged.

### Validation
- `python3 -m py_compile app.py global_cup/ui.py global_cup/charts.py global_cup/dividend_reinvest.py` → **OK**.
- `python3 -m pytest -q` → No tests ran. Pre-existing `test_formatting_display.py` calls `sys.exit(...)` at import time → pytest INTERNALERROR. **Unrelated to this change.**
- Signature smoke test:
  ```
  (close: pd.Series, dividends: pd.Series, initial_amount: float, monthly_amount: float, tax_rate_pct: float, reinvest_dividends: bool = True) -> Optional[DividendReinvestResult]
  ```
- Numeric smoke test on synthetic rising-price series with quarterly dividends:
  - Same `Total External Invested` in both modes ($13,400)
  - Reinvest final value $25,411.07 vs no-reinvest $25,209.86 (reinvest higher, as expected when prices rise)
  - Reinvest cash always 0, no-reinvest ends with $528.56 cash
  - Reinvest 127.05 shares vs no-reinvest 123.41 shares

### Final UX
- "가격 / 전고점 / 트리거" — unchanged
- "투자 시뮬레이션" — single comparison chart with three series: 배당 재투자, 배당 미재투자, 총 외부 투자금 (baseline)
- "배당" — unchanged
- "배당 재투자" — unchanged (still uses `reinvest_timeline_chart` + tables)
