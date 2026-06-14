Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_005_golden_py_engine_transplant.md

Save this entire prompt into that file.

MISSION:
golden.py is the GOLDEN SOURCE.
The engine behavior from golden.py must be preserved exactly.
The current refactored app design must be preserved.

Do NOT redesign.
Do NOT simplify the engine.
Do NOT replace ZigZag logic with close.max().
Do NOT hardcode trigger threshold to 10%.

Golden engine functions to preserve exactly:

find_alternating_high_low()
classify_drop_bucket()
classify_current_status()
build_current_status()
build_drawdown_cycles()
nearest_trade_date()
run_backtest()
calculate_annual_dividends()
run_dividend_backtest()
run_dividend_reinvest_backtest()
add_high_low_markers()
plot_backtest_price_chart() behavior

CRITICAL:
Every engine call must receive the UI trigger value:

threshold = trigger_drop_pct / 100.0

Validate trigger values:
5, 10, 20, 30

DYNAMIC WORKFLOW PHASES:

PHASE 1 — Inspect
Inspect:
golden.py
global_cup_refactored/

Find current active paths for:
reference high
drawdown
trigger
high/low markers
buy markers
dividend reinvestment

Create:
global_cup_refactored/PHASE1_INSPECT_REPORT.md

PHASE 2 — Extract Golden Engine
Create or repair:
global_cup_refactored/global_cup/golden_engine.py

Copy behavior exactly from golden.py.
Adjust only imports if necessary.

PHASE 3 — Connect Golden Engine
Keep current refactored design.
Replace only calculation calls.

Active app must use golden_engine.py for:
current status
drawdown cycles
high/low chart markers
trigger buy backtest
dividend backtest
dividend reinvestment backtest

PHASE 4 — Validate Against golden.py
Create:
global_cup_refactored/validate_against_golden.py

Compare golden.py vs global_cup/golden_engine.py.

Use synthetic tests:
A: [100, 110, 120, 100]
B: [100, 120, 90, 110, 130, 100]
C: monotonic increasing

Also test real tickers if yfinance works:
VOO
SCHD
JEPI
360750.KS
441680.KS

For trigger values:
5, 10, 20, 30

Compare:
high count
low count
last high
last low
build_current_status output
build_drawdown_cycles output
run_backtest trade count
run_backtest buy dates
run_backtest buy prices
dividend reinvestment summary keys

PHASE 5 — Debug Support
Add/preserve Engine Debug expander showing:
ticker
UI trigger_drop_pct
engine threshold
high count
low count
last high
last low
current status
trigger buy count

PHASE 6 — Final Checks
Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored
python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py

Create:
global_cup_refactored/FINAL_GOLDEN_ENGINE_TRANSPLANT_REPORT.md

SUCCESS CRITERIA:
1. Current design preserved
2. golden.py engine copied into refactored app
3. Active app uses golden engine
4. Trigger works for 5%, 10%, 20%, 30%
5. H markers appear
6. L markers appear
7. Buy markers appear
8. Dividend reinvestment behavior matches golden.py
9. validate_against_golden.py passes
10. App launches with:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored
streamlit run app.py

If any criterion fails:
STOP.
Do not redesign.
Do not add features.
Write a failure report.
