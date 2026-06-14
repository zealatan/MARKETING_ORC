# Step 002 — Safe Global Cup Refactor Prompt Archive

> Saved: 2026-06-05  
> Rule: MANDATORY ARCHIVAL — full prompt preserved verbatim below.

---

You are a senior software architect and quantitative finance engineer.

MANDATORY ARCHIVAL RULE

Before doing anything:

1. Create:

md_files/step_002_safe_global_cup_refactor.md

2. Save this entire prompt into that file.

====================================================
PROJECT ROOT
====================================================

/home/zealatan/MARKETING_ORC/invest

Current structure:

backup_original/
global_cup_landing_final.html
global_cup_dividend_reinvest_ported.py
global_cup_refactored/
md_files/

====================================================
CRITICAL WARNING
====================================================

DO NOT start refactoring immediately.

The existing project contains a trusted calculation engine.

The engine is considered the source of truth.

Before changing any code, locate and analyze these functions:

find_alternating_high_low()

build_current_status()

build_drawdown_cycles()

run_backtest()

run_dividend_backtest()

====================================================
MOST IMPORTANT REQUIREMENT
====================================================

DO NOT replace the ZigZag engine.

DO NOT replace:

find_alternating_high_low()

with:

close.max()

rolling max

simple drawdown calculations

or any simplified implementation.

The existing ZigZag logic is intentional.

The refactored project must preserve identical behavior.

====================================================
STEP 1
ENGINE AUDIT
====================================================

Create:

global_cup_refactored/ENGINE_AUDIT.md

Document:

1. How find_alternating_high_low works

2. How reference highs are selected

3. How reference lows are selected

4. How current drawdown is computed

5. How trigger detection works

6. How dividend reinvestment works

7. Which functions depend on the ZigZag engine

Do not modify code yet.

====================================================
STEP 2
ENGINE PRESERVATION TEST
====================================================

Create:

global_cup_refactored/validate_engine.py

The script must compare:

ORIGINAL ENGINE
vs
REFACTORED ENGINE

Test at least:

VOO

SCHD

JEPI

360750.KS

441680.KS

For identical date ranges.

Compare:

Current price

Reference high

Reference low

Drawdown %

Trigger classification

Drop bucket

Current status

Dividend totals

Dividend reinvestment results

Print:

PASS

or

FAIL

for every metric.

====================================================
STEP 3
REFACTOR ONLY AFTER VALIDATION
====================================================

Refactor code into modules.

Keep logic unchanged.

Allowed changes:

File organization

Code cleanup

Dataclasses

CSV ticker files

UI cleanup

Comments

Function extraction

NOT ALLOWED:

Changing calculations

Changing thresholds

Changing trigger logic

Changing ZigZag logic

Changing dividend formulas

====================================================
STEP 4
VERIFY ZIGZAG PRESERVATION
====================================================

After refactoring run:

grep -R "find_alternating_high_low" global_cup_refactored

Document where the function is used.

Create:

global_cup_refactored/ZIGZAG_USAGE_REPORT.md

Show:

Which modules call it

Which charts use it

Which reports use it

Which backtests use it

====================================================
STEP 5
GLOBAL CUP IMPROVEMENTS
====================================================

Only after engine validation passes:

Add:

Global Cup Score

Market Ranking

Ticker Ranking

Score = informational only.

DO NOT affect:

drawdown engine

trigger engine

dividend engine

backtest engine

====================================================
STEP 6
FINAL REPORT
====================================================

Create:

global_cup_refactored/FINAL_REFACTOR_REPORT.md

Include:

Files created

Files modified

Engine validation results

PASS/FAIL summary

Refactoring summary

Remaining risks

Run instructions

====================================================
SUCCESS CRITERIA
====================================================

The project is considered successful ONLY IF:

1. ZigZag engine preserved

2. Dividend reinvestment preserved

3. Trigger logic preserved

4. Validation script passes

5. Original files remain untouched

6. Refactored app still launches using:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

streamlit run app.py

If any validation fails:

STOP

Do not continue refactoring.

Produce a failure report instead.
