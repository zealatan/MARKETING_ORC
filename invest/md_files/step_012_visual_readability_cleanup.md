Use Dynamic Workflow Mode.

PROJECT ROOT:
/home/zealatan/MARKETING_ORC/invest/global_cup_refactored

MANDATORY ARCHIVAL RULE:
Before doing anything, create:

/home/zealatan/MARKETING_ORC/invest/md_files/step_012_visual_readability_cleanup.md

Save this entire prompt into that file.

====================================================
MISSION
====================================================

This is a visual readability and dashboard cleanup task.

DO NOT TOUCH:

- global_cup/golden_engine.py
- ZigZag logic
- trigger logic
- dividend calculations
- dividend reinvestment calculations
- backtest logic
- validate_against_golden.py

This is UI ONLY.

====================================================
TASK 1 — BRIGHTER FORM LABELS
====================================================

The following labels are too dark and hard to read:

초기 투자금 (KRW)

월 추가 투자금 (KRW)

배당세율 (%)

Make them significantly brighter.

Current style looks like:
dark gray on dark background.

Target:

color: #e8e3cf

font-weight: 600

opacity: 1.0

Ensure labels remain readable in:

KR
US
EU
JP
Global

====================================================
TASK 2 — ENLARGE DIVIDEND REINVESTMENT SUMMARY
====================================================

Section:

배당 재투자 요약

Current metrics:

총 외부 투자금
최종 평가금액
총 수익률
CAGR
최종 보유수량
누적 순배당
예상 순연배당
Yield on Cost

Need to be much larger.

Increase:

card title size

card value size

spacing

Recommended:

title:
14~16px

value:
26~32px

font-weight:
700

The summary should become a major dashboard element.

Current values feel too small.

====================================================
TASK 3 — ENLARGE TOP NAVIGATION
====================================================

Current tabs:

가격 / 전고점 / 트리거

배당

배당 재투자

Increase:

font size

padding

tab height

Recommended:

font-size: 16~18px

font-weight: 600

horizontal padding increase

Make tabs look more premium.

====================================================
TASK 4 — ENLARGE TOP METRIC CARDS
====================================================

Current:

Current Price
Trigger Count

These are important.

Increase:

label size

value size

card height

Examples:

Current Price
28,845 원

Trigger Count
4회

These should be much more visible.

Recommended:

label:
12~14px

value:
26~32px

====================================================
TASK 5 — REMOVE SECONDARY METRICS
====================================================

Remove these cards completely:

Ref High

Ref Low

ZZ Drawdown

Trigger Price

Trigger Status

Keep ONLY:

Current Price

Trigger Count

This makes the top metric row cleaner.

Do NOT delete the underlying data.

Just remove those cards from the UI.

====================================================
TASK 6 — BRIGHTEN TOGGLE LABELS
====================================================

Current labels are too dark:

Show ZigZag H/L markers

Show Trigger Buy markers

Market Snapshot

Make text brighter.

Target:

#f0ead6

font-weight: 500

Ensure visibility on dark background.

====================================================
TASK 7 — REMOVE GLOBAL CUP MARKET RANKING
====================================================

Remove:

Global Cup Market Ranking

section completely.

Do not show:

ranking table

ranking panel

ranking header

ranking placeholder

The dashboard should focus on:

price/trigger

dividend

dividend reinvestment

====================================================
TASK 8 — VISUAL BALANCE
====================================================

After removing:

Ref High
Ref Low
ZZ Drawdown
Trigger Price
Trigger Status
Global Cup Market Ranking

Rebalance spacing.

Ensure:

Current Price

Trigger Count

remain centered and visually strong.

Do not leave large empty gaps.

====================================================
TASK 9 — VALIDATION
====================================================

Run:

cd /home/zealatan/MARKETING_ORC/invest/global_cup_refactored

python -m py_compile app.py
python -m py_compile global_cup/*.py
python validate_against_golden.py
python test_formatting_display.py

All must pass.

====================================================
TASK 10 — REPORT
====================================================

Create:

/home/zealatan/MARKETING_ORC/invest/global_cup_refactored/UI_READABILITY_CLEANUP_REPORT.md

Include:

files modified

font size changes

color changes

removed cards

removed ranking section

validation results

confirmation golden_engine.py unchanged

====================================================
SUCCESS CRITERIA
====================================================

Success only if:

1. 초기 투자금 / 월 추가 투자금 / 배당세율 labels are clearly readable.

2. 배당 재투자 요약 values are significantly larger.

3. Tab labels are larger.

4. Current Price and Trigger Count are larger.

5. Ref High removed.

6. Ref Low removed.

7. ZZ Drawdown removed.

8. Trigger Price removed.

9. Trigger Status removed.

10. Show ZigZag / Show Trigger Buy / Market Snapshot labels are brighter.

11. Global Cup Market Ranking removed.

12. No engine changes.

13. validate_against_golden.py passes.

14. test_formatting_display.py passes.

If validation fails:
STOP.
Write a failure report.
