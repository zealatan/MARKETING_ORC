# Step 003 — ZigZag Engine Restore Prompt Archive

> Saved: 2026-06-05
> Rule: MANDATORY ARCHIVAL — full prompt preserved verbatim below.

---

Use Dynamic Workflow Mode.

MANDATORY ARCHIVAL RULE

Before doing anything:

Create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_003_zigzag_engine_restore.md

Save this entire prompt into that file.

====================================================
PROJECT ROOT
====================================================

/home/zealatan/MARKETING_ORC/invest

Current structure:

backup_original/
global_cup_dividend_reinvest_ported.py
global_cup_landing_final.html
global_cup_refactored/
md_files/

====================================================
PRIMARY OBJECTIVE
====================================================

The current refactored application is NOT correctly using the trusted engine.

Symptoms:

- ZigZag high markers are missing
- ZigZag low markers are missing
- Trigger buy markers are missing
- Reference highs appear incorrect
- Current drawdown status appears incorrect

The goal is NOT redesign.

The goal is:

RESTORE THE ORIGINAL ENGINE
AND CONNECT IT TO THE ACTIVE APP.

====================================================
CRITICAL RULE
====================================================

The original trusted source is:

global_cup_dividend_reinvest_ported.py

The following functions are the source of truth:

find_alternating_high_low()

build_current_status()

build_drawdown_cycles()

run_backtest()

run_dividend_backtest()

run_dividend_reinvest_backtest()

add_high_low_markers()

DO NOT REPLACE THEM.

DO NOT SIMPLIFY THEM.

DO NOT SUBSTITUTE:

close.max()

rolling max

simple drawdown logic

period high logic

for the ZigZag engine.

====================================================
DYNAMIC WORKFLOW REQUIREMENTS
====================================================

Run as a gated dynamic workflow.

PHASE 1
Inspect

PHASE 2
Audit

PHASE 3
Restore Engine

PHASE 4
Connect Engine

PHASE 5
Validate

PHASE 6
Report

Every phase must end with:

PASS

or

FAIL

Do not continue to the next phase if the current phase fails.

====================================================
PHASE 1
INSPECT
====================================================

Inspect:

global_cup_refactored/

Find:

find_alternating_high_low

build_current_status

build_drawdown_cycles

run_backtest

run_dividend_backtest

run_dividend_reinvest_backtest

add_high_low_markers

Generate:

global_cup_refactored/INSPECTION_REPORT.md

Report:

- functions found
- functions missing
- files containing them
- active Streamlit entry point
- active chart rendering path

PASS only if inspection completed.

====================================================
PHASE 2
AUDIT
====================================================

Determine:

1. Is ZigZag engine actually called?

2. Is build_current_status used?

3. Are H/L markers connected to charts?

4. Are trade events connected to charts?

5. Is trigger logic active?

6. Is dividend reinvestment engine active?

Generate:

global_cup_refactored/ZIGZAG_ENGINE_AUDIT.md

Root-cause analysis required.

PASS only if root cause identified.

====================================================
PHASE 3
RESTORE ENGINE
====================================================

Create or repair:

global_cup_refactored/global_cup/zigzag_engine.py

Must contain trusted implementations of:

find_alternating_high_low

classify_drop_bucket

classify_current_status

build_current_status

build_drawdown_cycles

Behavior must match original source.

No simplifications.

Create or repair:

global_cup_refactored/global_cup/backtest_engine.py

Must contain trusted implementations of:

nearest_trade_date

run_backtest

calculate_annual_dividends

run_dividend_backtest

run_dividend_reinvest_backtest

Trigger state machine must match original.

PASS only if all trusted functions exist.

====================================================
PHASE 4
CONNECT ENGINE
====================================================

This is the most important phase.

Verify that the active app calls:

find_alternating_high_low()

build_current_status()

add_high_low_markers()

run_backtest()

Actual UI must use them.

Fix chart rendering.

Required chart behavior:

1. Price line

2. ZigZag highs
   triangle-up
   text = H

3. ZigZag lows
   triangle-down
   text = L

4. Trigger buys
   marker = Buy

5. Trade events visible

6. Trigger percentage configurable

7. Show/Hide high-low checkbox

Add:

Engine Debug Expander

Display:

ticker

threshold

high count

low count

latest high

latest low

reference high

drawdown

trigger status

Generate:

global_cup_refactored/ENGINE_CONNECTION_REPORT.md

PASS only if active app uses engine.

====================================================
PHASE 5
VALIDATION
====================================================

Create:

global_cup_refactored/validate_zigzag_engine.py

Validation 1

Synthetic:

100
110
120
100

Expected:

High detected

Drawdown detected

Validation 2

100
120
90
110
130
100

Expected:

Alternating cycles detected

Validation 3

Monotonic increase

Expected:

No false trigger

Run:

python validate_zigzag_engine.py

Also compare original vs refactored for:

VOO

SCHD

JEPI

360750.KS

441680.KS

Compare:

Current Price

Reference High

Reference Low

Drawdown

Drop Bucket

Current Status

Trigger Classification

Dividend Results

PASS only if outputs match within tolerance.

====================================================
PHASE 6
REPORT
====================================================

Generate:

global_cup_refactored/ZIGZAG_ENGINE_FIX_REPORT.md

Include:

Root Cause

Files Modified

Functions Restored

Engine Connections

Validation Results

Remaining Risks

Run Instructions

====================================================
FINAL SUCCESS CRITERIA
====================================================

SUCCESS only if:

1.
find_alternating_high_low()
exists

2.
build_current_status()
exists

3.
run_backtest()
exists

4.
run_dividend_reinvest_backtest()
exists

5.
H markers displayed

6.
L markers displayed

7.
Buy markers displayed

8.
Trigger logic active

9.
Validation passes

10.
App launches:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

streamlit run app.py

If any condition fails:

STOP

Write a failure report.

Do not continue with UI improvements.

Do not redesign.

Do not add new features.

Fix the engine first.
