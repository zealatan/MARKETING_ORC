from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class MarketConfig:
    key: str
    code: str
    name: str
    flag: str
    badge_code: str
    subtitle: str
    tickers: Dict[str, str]
    chart1: str
    chart2: str
    line: str
    bg_label: str
    default_ticker_label: str


@dataclass
class UserInput:
    market_key: str
    ticker_label: str
    ticker: str
    trigger_pct: float
    start_date: date
    end_date: date


@dataclass
class AnalysisResult:
    # ── Core price fields (computed from close.max — backward-compat) ──────────
    current_date: pd.Timestamp
    current_price: float
    high_date: pd.Timestamp
    high_price: float
    drawdown_pct: float
    trigger_price: float
    trigger_hit: bool
    ttm_dividend: float
    dividend_yield: float
    latest_dividend_year: str
    latest_annual_dividend: float
    annual_dividend_df: pd.DataFrame
    price_df: pd.DataFrame
    close: pd.Series
    dividends: pd.Series
    # ── Golden engine fields (populated by golden_engine functions) ───────────
    zigzag_points: tuple = field(default_factory=lambda: ([], []))
    zigzag_ref_high_price: float = 0.0
    zigzag_ref_high_date: Optional[pd.Timestamp] = None
    zigzag_ref_low_price: float = 0.0
    zigzag_ref_low_date: Optional[pd.Timestamp] = None
    zigzag_drawdown_pct: float = 0.0
    zigzag_trigger_price: float = 0.0
    zigzag_trigger_hit: bool = False
    drop_bucket: str = ""
    status_label: str = ""
    high_count: int = 0
    low_count: int = 0
    # ── Trigger backtest (populated by run_backtest) ───────────────────────────
    backtest_df: Optional[pd.DataFrame] = None


@dataclass
class DividendReinvestResult:
    summary: Dict[str, float]
    event_df: pd.DataFrame
    timeline_df: pd.DataFrame
    annual_df: pd.DataFrame


# ── Flag CSS class helper ──────────────────────────────────────────────────────

def get_flag_class(config: MarketConfig) -> str:
    mapping = {
        "Korea": "flag-kr",
        "United States": "flag-us",
        "European Union": "flag-eu",
        "Japan": "flag-jp",
    }
    return mapping.get(config.key, "flag-glb")


# ── Base ticker dictionaries (fallback when CSV files are absent) ──────────────

_US_TICKERS_BASE: Dict[str, str] = {
    "VOO / Vanguard S&P 500 ETF": "VOO",
    "QQQ / Nasdaq 100 ETF": "QQQ",
    "SCHD / Dividend ETF": "SCHD",
    "JEPI / Equity Premium Income": "JEPI",
    "JEPQ / Nasdaq Premium Income": "JEPQ",
    "AAPL / Apple": "AAPL",
    "MSFT / Microsoft": "MSFT",
    "NVDA / NVIDIA": "NVDA",
    "KO / Coca-Cola": "KO",
}

_KOREA_TICKERS_BASE: Dict[str, str] = {
    "KODEX 200 / 069500.KS": "069500.KS",
    "TIGER 200 / 102110.KS": "102110.KS",
    "TIGER 미국S&P500 / 360750.KS": "360750.KS",
    "TIGER 미국나스닥100 / 133690.KS": "133690.KS",
    "TIGER 미국배당다우존스 / 458730.KS": "458730.KS",
    "삼성전자 / 005930.KS": "005930.KS",
    "SK하이닉스 / 000660.KS": "000660.KS",
    "현대차 / 005380.KS": "005380.KS",
    "NAVER / 035420.KS": "035420.KS",
}

_EU_TICKERS_BASE: Dict[str, str] = {
    "VGK / Vanguard FTSE Europe ETF": "VGK",
    "IEUR / iShares Core MSCI Europe ETF": "IEUR",
    "FEZ / Euro STOXX 50 ETF": "FEZ",
    "SAP / SAP": "SAP",
    "ASML / ASML": "ASML",
    "SIE.DE / Siemens": "SIE.DE",
    "ALV.DE / Allianz": "ALV.DE",
}

_JAPAN_TICKERS_BASE: Dict[str, str] = {
    "EWJ / iShares MSCI Japan ETF": "EWJ",
    "DXJ / WisdomTree Japan Hedged": "DXJ",
    "7203.T / Toyota": "7203.T",
    "6758.T / Sony": "6758.T",
    "7974.T / Nintendo": "7974.T",
    "9984.T / SoftBank Group": "9984.T",
}

_GLOBAL_TICKERS_BASE: Dict[str, str] = {
    "VT / Vanguard Total World ETF": "VT",
    "ACWI / iShares MSCI ACWI ETF": "ACWI",
    "URTH / MSCI World ETF": "URTH",
    "VXUS / Total International Stock": "VXUS",
    "VWO / Emerging Markets ETF": "VWO",
}


# ── Market registry ────────────────────────────────────────────────────────────

MARKETS: Dict[str, MarketConfig] = {
    "Korea": MarketConfig(
        key="Korea",
        code="KOR",
        name="Korea Market",
        flag="🇰🇷",
        badge_code="KR",
        subtitle="한국 주식/ETF의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=dict(_KOREA_TICKERS_BASE),
        chart1="#f04b4b",
        chart2="#2453d6",
        line="#e93434",
        bg_label="KOREA DASHBOARD",
        default_ticker_label="TIGER 미국S&P500 / 360750.KS",
    ),
    "United States": MarketConfig(
        key="United States",
        code="USA",
        name="United States",
        flag="🇺🇸",
        badge_code="US",
        subtitle="미국 주식/ETF의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=dict(_US_TICKERS_BASE),
        chart1="#2453d6",
        chart2="#e23636",
        line="#2453d6",
        bg_label="US DASHBOARD",
        default_ticker_label="Vanguard S&P 500 ETF / VOO",
    ),
    "European Union": MarketConfig(
        key="European Union",
        code="EU",
        name="European Union",
        flag="🇪🇺",
        badge_code="EU",
        subtitle="유럽 ETF/대표 종목의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=dict(_EU_TICKERS_BASE),
        chart1="#214fd8",
        chart2="#ffd84a",
        line="#ffd84a",
        bg_label="EU DASHBOARD",
        default_ticker_label="VGK / Vanguard FTSE Europe ETF",
    ),
    "Japan": MarketConfig(
        key="Japan",
        code="JPN",
        name="Japan Market",
        flag="🇯🇵",
        badge_code="JP",
        subtitle="일본 ETF/대표 종목의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=dict(_JAPAN_TICKERS_BASE),
        chart1="#d92545",
        chart2="#ff9aac",
        line="#d92545",
        bg_label="JAPAN DASHBOARD",
        default_ticker_label="EWJ / iShares MSCI Japan ETF",
    ),
    "Global": MarketConfig(
        key="Global",
        code="GLB",
        name="Global Market",
        flag="🌍",
        badge_code="GLB",
        subtitle="글로벌 ETF의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=dict(_GLOBAL_TICKERS_BASE),
        chart1="#35b66d",
        chart2="#2574d9",
        line="#35b66d",
        bg_label="GLOBAL DASHBOARD",
        default_ticker_label="VT / Vanguard Total World ETF",
    ),
}
