Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_008_currency_formatting_all_tabs.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

This is a formatting/UI consistency task.

Do NOT touch the calculation engine.

Do NOT modify:
- global_cup/golden_engine.py
- trigger logic
- ZigZag logic
- dividend reinvestment calculations
- backtest calculations
- validate_against_golden.py logic

Goal:

Apply clean year, amount, and currency formatting across ALL tabs.

Current issues:
1. YEAR values show decimals like:
   2,020.0000

   They must show:
   2020

2. KRW and JPY amounts show decimals.
   They should show no decimals.

3. Currency units should be shown according to the selected market/currency:
   - KRW: 원
   - USD: $
   - EUR: €
   - JPY: 엔
   - GBP: £
   - HKD: HK$
   - CHF: CHF
   - CAD: C$
   - AUD: A$

4. This formatting must be applied consistently across:
   - Global Cup Score tab
   - 가격 / 전고점 / 트리거 tab
   - 배당 tab
   - 배당 재투자 tab
   - Market Snapshot
   - ZigZag event table
   - Annual dividend table
   - Metric cards
   - Summary text
   - Chart hover labels if practical
   - Chart legends/annotations where currency is displayed

====================================================
TASK 1 — CREATE CENTRAL FORMATTER
====================================================

Create or update:

global_cup/formatting.py

Add centralized helper functions:

get_currency_unit(currency_code: str) -> str

format_year(value) -> str

format_number(value, decimals=0) -> str

format_amount(value, currency_code: str, decimals=None) -> str

format_percent(value, decimals=2) -> str

Rules:

format_year:
- Convert float/int/string year to integer year string.
- Example:
  2020.0000 -> 2020
  "2,020.0000" -> 2020
  2026 -> 2026

format_amount:
- If currency is KRW or JPY:
  no decimals
- If currency is USD/EUR/GBP/HKD/CHF/CAD/AUD:
  default 2 decimals unless explicitly overridden
- Append or prepend the correct unit:
  KRW: 25,230 원
  JPY: 2,315 엔
  USD: $25,230.00
  EUR: €25,230.00
  GBP: £25,230.00
  HKD: HK$25,230.00
  CHF: 25,230.00 CHF
  CAD: C$25,230.00
  AUD: A$25,230.00

format_percent:
- Keep percent sign
- Example:
  -47.7 -> -47.70%
  0.2 -> 0.20%

====================================================
TASK 2 — MARKET CURRENCY RESOLUTION
====================================================

Ensure every selected ticker/market has a currency_code.

Use existing market rules if available.

Expected mapping:
- Korea -> KRW
- United States -> USD
- Japan -> JPY
- European Union -> EUR
- Global -> USD by default unless ticker metadata says otherwise

If ticker CSV has currency column, prefer CSV currency.

If unavailable, use market default.

Do not change data sources.

====================================================
TASK 3 — APPLY TO ANNUAL DIVIDEND TABLE
====================================================

Fix Annual Dividend table.

Before:
YEAR          DIVIDEND PER SHARE
2,020.0000    10.0000

After for KRW:
YEAR          DIVIDEND PER SHARE
2020          10 원

After for USD:
YEAR          DIVIDEND PER SHARE
2020          $0.58

After for JPY:
YEAR          DIVIDEND PER SHARE
2020          10 엔

Remove all decimal formatting from YEAR.

Apply latest/highest/lowest badges without corrupting year formatting.

====================================================
TASK 4 — APPLY TO ZIGZAG EVENT TABLE
====================================================

In ZigZag High / Low & Trigger Events table, format:

Price
Reference High
Reference Low
Trigger Price if present

Use format_amount().

For KRW:
25,230 원

For USD:
$25,230.00

For JPY:
25,230 엔

Year/date columns should remain dates, not currency.

====================================================
TASK 5 — APPLY TO METRIC CARDS
====================================================

Update metric cards across all tabs.

Examples:

Current Price:
25,230 원

Reference High:
29,850 원

Reference Low:
17,310 원

Trigger Price:
26,865 원

Latest Div:
127 원

Average Div:
159 원

Final Evaluation:
26,121,088 원

External Invested:
10,000,000 원

Current Expected Net Annual Dividend:
52,615 원

For USD/EUR/GBP:
show symbol correctly.

====================================================
TASK 6 — APPLY TO SUMMARY TEXT
====================================================

Update summary footer text.

Before:
통화: KRW / 배당세율: 15.40% / 최근 연간 주당 배당금: 60.0000 / 현재 순배당률: 0.20%

After:
통화: KRW (원) / 배당세율: 15.40% / 최근 연간 주당 배당금: 60 원 / 현재 순배당률: 0.20%

For USD:
통화: USD ($) / 최근 연간 주당 배당금: $0.60

====================================================
TASK 7 — APPLY TO ALL TABS
====================================================

Search all display code for:

:.4f
:.2f
:,.4f
:,.2f
map(lambda x: f"{x:,.4f}")
map(lambda x: f"{x:,.2f}")
to_html

Replace display formatting with centralized formatting helpers where appropriate.

Do not change internal numeric values.

Only change display strings.

====================================================
TASK 8 — VALIDATION
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py

Validation must still pass.

Also add a small display-format test:

Create:
test_formatting_display.py

Test:
- format_year(2020.0) == "2020"
- format_year("2,020.0000") == "2020"
- format_amount(25230, "KRW") == "25,230 원"
- format_amount(25230.55, "KRW") == "25,231 원"
- format_amount(25230, "JPY") == "25,230 엔"
- format_amount(25230.55, "USD") == "$25,230.55"
- format_amount(25230.5, "EUR") == "€25,230.50"
- format_percent(-47.7) == "-47.70%"

Run:
python test_formatting_display.py

====================================================
TASK 9 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/CURRENCY_FORMATTING_REPORT.md

Include:
- files modified
- formatter functions added
- currency mappings
- tabs updated
- before/after examples
- validation result
- confirmation that golden_engine.py was not modified

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. Year never appears as 2,020.0000.
2. KRW amounts never show decimals.
3. JPY amounts never show decimals.
4. USD/EUR/GBP amounts show correct currency symbol.
5. Currency unit appears in tables and metric cards.
6. Formatting applies across all tabs.
7. golden_engine.py unchanged.
8. validate_against_golden.py passes.
9. test_formatting_display.py passes.

If validation fails:
STOP.
Do not continue.
Write a failure report.
