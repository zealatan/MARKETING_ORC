import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from dataclasses import dataclass
from datetime import date, timedelta, datetime
from typing import Dict, Optional


# ============================================================
# Global Cup Market Dashboard  —  v4
# Changes vs v3:
#   - Right badge box: CSS-drawn flag (no emoji)
#   - White bar above graph removed (tab-panel background -> transparent)
#   - market-flag-box updated to host drawn-flag div
#   - get_flag_class() helper added
# ============================================================

st.set_page_config(
    page_title="Global Cup Market Dashboard",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# Data classes
# ============================================================

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




@dataclass
class DividendReinvestResult:
    summary: Dict[str, float]
    event_df: pd.DataFrame
    timeline_df: pd.DataFrame
    annual_df: pd.DataFrame


# ============================================================
# Dividend reinvestment market rules
# ============================================================

MARKET_RULES = {
    "United States": {"currency": "USD", "tax_rate": 15.0},
    "Korea": {"currency": "KRW", "tax_rate": 15.4},
    "Japan": {"currency": "JPY", "tax_rate": 20.315},
    "European Union": {"currency": "EUR", "tax_rate": 15.0},
    "Global": {"currency": "USD", "tax_rate": 15.0},
}


def get_market_rule(market_key: str) -> Dict[str, float]:
    return MARKET_RULES.get(market_key, {"currency": "USD", "tax_rate": 15.0})

# ============================================================
# Ticker universe
# ============================================================

US_TICKERS = {
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

KOREA_TICKERS = {
    "KODEX 200": "069500.KS",
    "TIGER 200": "102110.KS",
    "TIGER 미국S&P500": "360750.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "TIGER 미국배당다우존스": "458730.KS",
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "NAVER": "035420.KS",
}

EU_TICKERS = {
    "VGK / Vanguard FTSE Europe ETF": "VGK",
    "IEUR / iShares Core MSCI Europe ETF": "IEUR",
    "FEZ / Euro STOXX 50 ETF": "FEZ",
    "SAP / SAP": "SAP",
    "ASML / ASML": "ASML",
    "SIE.DE / Siemens": "SIE.DE",
    "ALV.DE / Allianz": "ALV.DE",
}

JAPAN_TICKERS = {
    "EWJ / iShares MSCI Japan ETF": "EWJ",
    "DXJ / WisdomTree Japan Hedged": "DXJ",
    "7203.T / Toyota": "7203.T",
    "6758.T / Sony": "6758.T",
    "7974.T / Nintendo": "7974.T",
    "9984.T / SoftBank Group": "9984.T",
}

GLOBAL_TICKERS = {
    "VT / Vanguard Total World ETF": "VT",
    "ACWI / iShares MSCI ACWI ETF": "ACWI",
    "URTH / MSCI World ETF": "URTH",
    "VXUS / Total International Stock": "VXUS",
    "VWO / Emerging Markets ETF": "VWO",
}

MARKETS: Dict[str, MarketConfig] = {
    "Korea": MarketConfig(
        key="Korea",
        code="KOR",
        name="Korea Market",
        flag="🇰🇷",
        badge_code="KR",
        subtitle="한국 주식/ETF의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=KOREA_TICKERS,
        chart1="#f04b4b",
        chart2="#2453d6",
        line="#e93434",
        bg_label="KOREA DASHBOARD",
        default_ticker_label="TIGER 미국S&P500",
    ),
    "United States": MarketConfig(
        key="United States",
        code="USA",
        name="United States",
        flag="🇺🇸",
        badge_code="US",
        subtitle="미국 주식/ETF의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=US_TICKERS,
        chart1="#2453d6",
        chart2="#e23636",
        line="#2453d6",
        bg_label="US DASHBOARD",
        default_ticker_label="VOO / Vanguard S&P 500 ETF",
    ),
    "European Union": MarketConfig(
        key="European Union",
        code="EU",
        name="European Union",
        flag="🇪🇺",
        badge_code="EU",
        subtitle="유럽 ETF/대표 종목의 배당, 전고점 대비 하락률, 트리거 신호를 확인합니다.",
        tickers=EU_TICKERS,
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
        tickers=JAPAN_TICKERS,
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
        tickers=GLOBAL_TICKERS,
        chart1="#35b66d",
        chart2="#2574d9",
        line="#35b66d",
        bg_label="GLOBAL DASHBOARD",
        default_ticker_label="VT / Vanguard Total World ETF",
    ),
}




# ============================================================
# Legacy ticker universe override
# - Design is unchanged. Only ticker universe is expanded.
# - Existing small market lists above remain as fallback.
# ============================================================

def _legacy_label_dict(raw: Dict[str, str]) -> Dict[str, str]:
    return {f"{name} / {ticker}": ticker for name, ticker in raw.items()}


US_TOP100_LEGACY = {
    "NVIDIA": "NVDA", "Alphabet Class A": "GOOGL", "Apple": "AAPL", "Microsoft": "MSFT",
    "Amazon": "AMZN", "Broadcom": "AVGO", "Tesla": "TSLA", "Meta": "META",
    "Walmart": "WMT", "Berkshire Hathaway": "BRK-B", "Eli Lilly": "LLY", "JPMorgan Chase": "JPM",
    "Visa": "V", "Exxon Mobil": "XOM", "Mastercard": "MA", "UnitedHealth": "UNH",
    "Costco": "COST", "Netflix": "NFLX", "Oracle": "ORCL", "Johnson & Johnson": "JNJ",
    "Home Depot": "HD", "Procter & Gamble": "PG", "Bank of America": "BAC", "AbbVie": "ABBV",
    "Palantir": "PLTR", "Coca-Cola": "KO", "Philip Morris": "PM", "Chevron": "CVX",
    "Cisco": "CSCO", "Wells Fargo": "WFC", "Intel": "INTC", "Caterpillar": "CAT",
    "Lam Research": "LRCX", "AMD": "AMD", "Salesforce": "CRM", "Adobe": "ADBE",
    "McDonald's": "MCD", "Merck": "MRK", "PepsiCo": "PEP", "Thermo Fisher": "TMO",
    "Abbott Laboratories": "ABT", "Qualcomm": "QCOM", "Texas Instruments": "TXN", "Applied Materials": "AMAT",
    "Intuit": "INTU", "ServiceNow": "NOW", "Goldman Sachs": "GS", "Morgan Stanley": "MS",
    "American Express": "AXP", "BlackRock": "BLK", "S&P Global": "SPGI", "Booking Holdings": "BKNG",
    "Uber": "UBER", "RTX": "RTX", "Lockheed Martin": "LMT", "Boeing": "BA",
    "Honeywell": "HON", "Union Pacific": "UNP", "Deere": "DE", "General Electric": "GE",
    "NextEra Energy": "NEE", "ConocoPhillips": "COP", "Eaton": "ETN", "Lowe's": "LOW",
    "TJX Companies": "TJX", "Nike": "NKE", "Starbucks": "SBUX", "Mondelez": "MDLZ",
    "Colgate-Palmolive": "CL", "Prologis": "PLD", "American Tower": "AMT", "Equinix": "EQIX",
    "CME Group": "CME", "Charles Schwab": "SCHW", "Blackstone": "BX", "Citigroup": "C",
    "Progressive": "PGR", "Marsh & McLennan": "MMC", "Chubb": "CB", "Elevance Health": "ELV",
    "Cigna": "CI", "Amgen": "AMGN", "Gilead Sciences": "GILD", "Bristol Myers Squibb": "BMY",
    "Pfizer": "PFE", "Danaher": "DHR", "Vertex": "VRTX", "Regeneron": "REGN",
    "Stryker": "SYK", "Medtronic": "MDT", "Boston Scientific": "BSX", "Intuitive Surgical": "ISRG",
    "Micron": "MU", "KLA": "KLAC", "Palo Alto Networks": "PANW", "Arista Networks": "ANET",
    "Synopsys": "SNPS", "Cadence": "CDNS", "Automatic Data Processing": "ADP",
}

US_ETF_TOP50_LEGACY = {
    "Vanguard S&P 500 ETF": "VOO", "iShares Core S&P 500 ETF": "IVV", "SPDR S&P 500 ETF Trust": "SPY",
    "Vanguard Total Stock Market ETF": "VTI", "Invesco QQQ Trust": "QQQ", "Vanguard FTSE Developed Markets ETF": "VEA",
    "Vanguard Growth ETF": "VUG", "SPDR Gold Shares": "GLD", "iShares Core MSCI EAFE ETF": "IEFA",
    "Vanguard Value ETF": "VTV", "Vanguard Total Bond Market ETF": "BND", "iShares Core MSCI Emerging Markets ETF": "IEMG",
    "Vanguard Total International Stock ETF": "VXUS", "iShares Core U.S. Aggregate Bond ETF": "AGG",
    "Vanguard FTSE Emerging Markets ETF": "VWO", "iShares Russell 1000 Growth ETF": "IWF",
    "Vanguard Information Technology ETF": "VGT", "iShares Core S&P Mid-Cap ETF": "IJH",
    "SPDR Portfolio S&P 500 ETF": "SPLG", "Vanguard Dividend Appreciation ETF": "VIG",
    "Vanguard Mid-Cap ETF": "VO", "iShares Core S&P Small-Cap ETF": "IJR", "Technology Select Sector SPDR Fund": "XLK",
    "Invesco S&P 500 Equal Weight ETF": "RSP", "Schwab U.S. Dividend Equity ETF": "SCHD", "iShares Gold Trust": "IAU",
    "iShares Core S&P Total U.S. Stock Market ETF": "ITOT", "iShares MSCI EAFE ETF": "EFA",
    "Vanguard Total International Bond ETF": "BNDX", "Vanguard High Dividend Yield ETF": "VYM",
    "iShares 0-3 Month Treasury Bond ETF": "SGOV", "iShares 20+ Year Treasury Bond ETF": "TLT",
    "iShares 7-10 Year Treasury Bond ETF": "IEF", "iShares iBoxx Investment Grade Corporate Bond ETF": "LQD",
    "iShares iBoxx High Yield Corporate Bond ETF": "HYG", "JPMorgan Equity Premium Income ETF": "JEPI",
    "JPMorgan Nasdaq Equity Premium Income ETF": "JEPQ", "Global X Nasdaq 100 Covered Call ETF": "QYLD",
    "Global X S&P 500 Covered Call ETF": "XYLD", "Global X Russell 2000 Covered Call ETF": "RYLD",
    "Vanguard Real Estate ETF": "VNQ", "Health Care Select Sector SPDR Fund": "XLV", "Financial Select Sector SPDR Fund": "XLF",
    "Energy Select Sector SPDR Fund": "XLE", "Consumer Staples Select Sector SPDR Fund": "XLP",
    "Consumer Discretionary Select Sector SPDR Fund": "XLY", "Industrial Select Sector SPDR Fund": "XLI",
    "Utilities Select Sector SPDR Fund": "XLU", "Communication Services Select Sector SPDR Fund": "XLC",
    "Materials Select Sector SPDR Fund": "XLB",
}

KOREA_TOP30_LEGACY = {
    "Samsung Electronics": "005930.KS", "SK Hynix": "000660.KS", "LG Energy Solution": "373220.KS",
    "Hyundai Motor": "005380.KS", "Samsung Biologics": "207940.KS", "Kia": "000270.KS",
    "KB Financial Group": "105560.KS", "Celltrion": "068270.KS", "NAVER": "035420.KS",
    "Shinhan Financial Group": "055550.KS", "Hyundai Mobis": "012330.KS", "Samsung C&T": "028260.KS",
    "POSCO Holdings": "005490.KS", "Samsung SDI": "006400.KS", "LG Chem": "051910.KS",
    "LG Electronics": "066570.KS", "Kakao": "035720.KS", "Hana Financial Group": "086790.KS",
    "Samsung Fire & Marine": "000810.KS", "KT&G": "033780.KS", "Korea Electric Power": "015760.KS",
    "HD Hyundai Heavy Industries": "329180.KS", "Hanwha Aerospace": "012450.KS", "Doosan Enerbility": "034020.KS",
    "SK Square": "402340.KS", "Samsung Electro-Mechanics": "009150.KS", "LG Corp": "003550.KS",
    "HMM": "011200.KS", "Hyundai Glovis": "086280.KS", "Amorepacific": "090430.KS",
}

KOREA_ETF_TOP30_LEGACY = {
    "KODEX 200": "069500.KS", "TIGER 200": "102110.KS", "KODEX CD금리액티브": "459580.KS",
    "TIGER CD금리투자KIS": "357870.KS", "KODEX KOFR금리액티브": "423160.KS",
    "TIGER KOFR금리액티브": "449170.KS", "KODEX 단기채권": "153130.KS", "TIGER 단기통안채": "157450.KS",
    "KODEX 종합채권(AA-이상)액티브": "273130.KS", "KODEX 국고채30년액티브": "439870.KS",
    "KODEX 미국S&P500TR": "379800.KS", "TIGER 미국S&P500": "360750.KS", "ACE 미국S&P500": "360200.KS",
    "RISE 미국S&P500": "379780.KS", "SOL 미국S&P500": "433330.KS", "KODEX 미국나스닥100TR": "379810.KS",
    "TIGER 미국나스닥100": "133690.KS", "ACE 미국나스닥100": "367380.KS", "RISE 미국나스닥100": "368590.KS",
    "TIGER 미국테크TOP10 INDXX": "381170.KS", "TIGER 미국필라델피아반도체나스닥": "381180.KS",
    "KODEX 미국배당다우존스": "489250.KS", "TIGER 미국배당다우존스": "458730.KS", "SOL 미국배당다우존스": "446720.KS",
    "KODEX 2차전지산업": "305720.KS", "TIGER 2차전지테마": "305540.KS", "KODEX 반도체": "091160.KS",
    "TIGER 반도체": "091230.KS", "TIGER Fn반도체TOP10": "396500.KS", "KODEX 자동차": "091180.KS",
    "TIGER 차이나전기차SOLACTIVE": "371460.KS", "KODEX 골드선물(H)": "132030.KS",
}

KOREA_COVERED_CALL_ETF_LEGACY = {
    "KODEX 200타겟위클리커버드콜": "498400.KS", "TIGER 200커버드콜": "289480.KS",
    "TIGER 미국나스닥100커버드콜(합성)": "441680.KS", "KODEX 미국나스닥100커버드콜(합성)": "449190.KS",
    "TIGER 미국S&P500배당귀족커버드콜": "429000.KS", "KODEX 미국S&P500배당귀족커버드콜": "276970.KS",
    "TIGER 미국30년국채커버드콜액티브(H)": "476550.KS", "KODEX 미국30년국채타겟커버드콜(합성 H)": "487230.KS",
    "RISE 미국30년국채커버드콜": "472830.KS",
}

GLOBAL_EX_US_KR_TOP50_LEGACY = {
    "TSMC": "TSM", "Tencent": "0700.HK", "Alibaba": "9988.HK", "Toyota": "7203.T", "ASML": "ASML",
    "SAP": "SAP", "Nestle": "NESN.SW", "Novo Nordisk": "NOVO-B.CO", "LVMH": "MC.PA", "Roche": "ROG.SW",
    "AstraZeneca": "AZN.L", "Shell": "SHEL.L", "Novartis": "NOVN.SW", "HSBC": "HSBA.L", "Hermes": "RMS.PA",
    "Siemens": "SIE.DE", "Unilever": "ULVR.L", "L'Oreal": "OR.PA", "TotalEnergies": "TTE.PA", "Sanofi": "SAN.PA",
    "Sony": "6758.T", "Mitsubishi UFJ": "8306.T", "Commonwealth Bank": "CBA.AX", "BHP": "BHP.AX", "Rio Tinto": "RIO.L",
    "Royal Bank of Canada": "RY.TO", "Toronto-Dominion Bank": "TD.TO", "Shopify": "SHOP.TO", "Canadian Natural Resources": "CNQ.TO",
    "Airbus": "AIR.PA", "Schneider Electric": "SU.PA", "Allianz": "ALV.DE", "Deutsche Telekom": "DTE.DE",
    "Mercedes-Benz Group": "MBG.DE", "BMW": "BMW.DE", "Volkswagen Pref": "VOW3.DE", "Prosus": "PRX.AS",
    "Adyen": "ADYEN.AS", "Diageo": "DGE.L", "BP": "BP.L", "Glencore": "GLEN.L", "RELX": "REL.L",
    "British American Tobacco": "BATS.L", "Keyence": "6861.T", "Hitachi": "6501.T", "Nintendo": "7974.T",
    "SoftBank Group": "9984.T", "Mitsubishi Corp": "8058.T", "Fast Retailing": "9983.T", "AIA Group": "1299.HK",
}

# Apply legacy universe without changing visual design.
_us_legacy = {}
_us_legacy.update(US_TOP100_LEGACY)
_us_legacy.update(US_ETF_TOP50_LEGACY)
_kr_legacy = {}
_kr_legacy.update(KOREA_TOP30_LEGACY)
_kr_legacy.update(KOREA_ETF_TOP30_LEGACY)
_kr_legacy.update(KOREA_COVERED_CALL_ETF_LEGACY)

MARKETS["United States"].tickers = _legacy_label_dict(_us_legacy)
MARKETS["Korea"].tickers = _legacy_label_dict(_kr_legacy)
MARKETS["Global"].tickers = _legacy_label_dict(GLOBAL_EX_US_KR_TOP50_LEGACY)

# Preserve default labels after legacy relabeling.
MARKETS["United States"].default_ticker_label = "Vanguard S&P 500 ETF / VOO"
MARKETS["Korea"].default_ticker_label = "TIGER 미국S&P500 / 360750.KS"
MARKETS["Global"].default_ticker_label = "VT / Vanguard Total World ETF" if "VT / Vanguard Total World ETF" in MARKETS["Global"].tickers else next(iter(MARKETS["Global"].tickers))

# ============================================================
# Flag class helper
# ============================================================

def get_flag_class(config: MarketConfig) -> str:
    if config.key == "Korea":
        return "flag-kr"
    if config.key == "United States":
        return "flag-us"
    if config.key == "European Union":
        return "flag-eu"
    if config.key == "Japan":
        return "flag-jp"
    return "flag-glb"


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>
/* ── Base ── */
:root {
    --bg:    #0b1008;
    --cream: #fff5dc;
    --paper: #fff9ed;
    --text:  #1f2b18;
    --muted: #d9caa8;
}

.stApp {
    background:
        radial-gradient(circle at 18% 16%, rgba(231,255,155,.16), transparent 28rem),
        radial-gradient(circle at 82% 8%,  rgba(255,255,255,.09), transparent 30rem),
        linear-gradient(180deg, #0b1008 0%, #111a0e 54%, #070a05 100%);
    color: var(--cream);
}

.main .block-container {
    max-width: 1240px;
    padding-top: 0.7rem;
    padding-bottom: 4rem;
}

header,
[data-testid="stHeader"] {
    background: transparent !important;
}

h1, h2, h3, h4, p, label, span, div {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
}

h1, h2, h3, h4 {
    color: var(--cream) !important;
}

/* ── Top nav ── */
.top-nav {
    height: 62px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.7rem;
}

.brand {
    display: flex;
    align-items: center;
    gap: .75rem;
    font-size: 1.25rem;
    font-weight: 950;
    color: var(--cream);
}

.brand-mark {
    width: 38px;
    height: 38px;
    border-radius: 999px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #f7ffd4, #8dbb55);
    color: #14200d;
    box-shadow: 0 12px 28px rgba(142,185,87,.22);
}

.home-pill {
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 999px;
    color: var(--cream) !important;
    background: rgba(255,255,255,.08);
    padding: .75rem 1.2rem;
    font-weight: 950;
    text-decoration: none !important;
    display: inline-flex;
    align-items: center;
    transition: background .18s;
}

.home-pill:hover {
    background: rgba(255,255,255,.14);
}

/* ── Market expander ── */
div[data-testid="stExpander"] {
    background: rgba(255,255,255,.035) !important;
    border: 1px solid rgba(255,255,255,.07) !important;
    border-radius: 10px !important;
}

/* ── Market badge row: code box + flag box side-by-side ── */
.market-badge-row {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 1.6rem;
}

.market-code-box {
    width: 96px;
    height: 96px;
    border-radius: 28px;
    background: #fff9ed;
    color: #1f2b18;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    font-weight: 950;
    letter-spacing: -.5px;
    border: 1px solid rgba(255,255,255,.7);
    box-shadow: 0 24px 60px rgba(0,0,0,.25);
    flex-shrink: 0;
    line-height: 1;
}

.market-flag-box {
    width: 96px;
    height: 96px;
    border-radius: 28px;
    background: #fff9ed;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(255,255,255,.7);
    box-shadow: 0 24px 60px rgba(0,0,0,.25);
    flex-shrink: 0;
}

/* ================================================================
   CSS-DRAWN FLAGS — no emoji
   ================================================================ */

.drawn-flag {
    width: 64px;
    height: 42px;
    border-radius: 10px;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,.12);
    position: relative;
    overflow: hidden;
    flex-shrink: 0;
}

/* Japan: white field, crimson disc */
.flag-jp {
    background:
        radial-gradient(circle at 50% 50%, #bc002d 0 28%, transparent 29%),
        #fff;
}

/* United States: 13 red/white stripes + blue canton */
.flag-us {
    background:
        linear-gradient(to bottom,
            #b22234  0%   7.7%, #fff    7.7%  15.4%,
            #b22234 15.4% 23.1%, #fff  23.1%  30.8%,
            #b22234 30.8% 38.5%, #fff  38.5%  46.2%,
            #b22234 46.2% 53.9%, #fff  53.9%  61.6%,
            #b22234 61.6% 69.3%, #fff  69.3%  77%,
            #b22234 77%   84.7%, #fff  84.7%  92.4%,
            #b22234 92.4% 100%);
}
.flag-us::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 45%;
    height: 54%;
    background: #3c3b6e;
    border-radius: 10px 0 4px 0;
}

/* European Union: blue field, 8 simplified yellow star dots */
.flag-eu {
    background:
        radial-gradient(circle at 50% 16%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 72% 25%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 84% 50%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 72% 75%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 50% 84%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 28% 75%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 16% 50%, #ffcc00 0 4%, transparent 5%),
        radial-gradient(circle at 28% 25%, #ffcc00 0 4%, transparent 5%),
        #003399;
}

/* Korea: white field, taegeuk — red upper disc / blue lower disc */
.flag-kr {
    background:
        radial-gradient(circle at 50% 44%, #cd2e3a 0 19%, transparent 20%),
        radial-gradient(circle at 50% 58%, #0047a0 0 19%, transparent 20%),
        #fff;
}

/* Global: circular blue ocean + green land patches */
.flag-glb {
    width: 58px;
    height: 58px;
    border-radius: 50%;
    background:
        radial-gradient(circle at 35% 35%, #6ee7b7 0 12%, transparent 13%),
        radial-gradient(circle at 65% 60%, #22c55e  0 18%, transparent 19%),
        radial-gradient(circle at 50% 50%, #38bdf8  0 60%, #1d4ed8 100%);
}

/* ── Market title ── */
.market-title {
    font-family: Georgia, "Times New Roman", serif;
    font-size: clamp(52px, 6.5vw, 96px);
    line-height: .92;
    letter-spacing: -3.5px;
    font-weight: 500;
    color: var(--cream);
    margin-bottom: 1.2rem;
}

.market-subtitle {
    color: var(--muted);
    line-height: 1.65;
    max-width: 640px;
    font-size: 1rem;
    margin-bottom: 1.3rem;
}

/* ================================================================
   INPUT FIELDS — transparent dark glassmorphism
   ================================================================ */
div[data-testid="stTextInput"],
div[data-testid="stSelectbox"] {
    background: rgba(255,255,255,.075) !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 999px !important;
    padding: .55rem .85rem .35rem !important;
    box-shadow: 0 14px 34px rgba(0,0,0,.14) !important;
}

div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label {
    color: #fff5dc !important;
    font-weight: 950 !important;
    font-size: .82rem !important;
    background: transparent !important;
}

div[data-baseweb="select"] > div,
div[data-baseweb="select"] > div > div,
div[data-baseweb="input"],
div[data-baseweb="input"] > div,
div[data-baseweb="base-input"],
div[data-baseweb="base-input"] > div {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #fff5dc !important;
}

input,
input[type="text"] {
    background: transparent !important;
    background-color: transparent !important;
    color: #fff5dc !important;
    -webkit-text-fill-color: #fff5dc !important;
    border: none !important;
    box-shadow: none !important;
    caret-color: #fff5dc !important;
    font-weight: 700 !important;
}

input::placeholder {
    color: rgba(255,245,220,.50) !important;
    -webkit-text-fill-color: rgba(255,245,220,.50) !important;
    font-weight: 400 !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] svg {
    color: #fff5dc !important;
    fill: rgba(255,245,220,.75) !important;
}

/* Calendar popover stays light */
div[data-baseweb="popover"],
div[data-baseweb="popover"] * {
    color: #1f2b18 !important;
}

/* ── Tabs — rounded pills ── */
.stTabs {
    margin-top: 0 !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: .5rem !important;
    background: rgba(255,255,255,.06) !important;
    padding: .5rem !important;
    border-radius: 999px !important;
    border: 1px solid rgba(255,255,255,.09) !important;
    margin-bottom: .8rem !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: .65rem 1.1rem !important;
    color: rgba(255,245,220,.72) !important;
    font-weight: 950 !important;
    background: transparent !important;
    transition: background .18s, color .18s !important;
}

.stTabs [aria-selected="true"] {
    background: #fff5dc !important;
    color: #1f2b18 !important;
}

/* Remove white bar: tab panel background must be transparent */
.stTabs [data-baseweb="tab-panel"],
div[data-testid="stTabsContent"],
div[data-testid="stTabPanel"] {
    background: transparent !important;
    padding-top: 0 !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Chart containers ── */
.chart-wrap {
    background: rgba(255,249,237,.96);
    border-radius: 34px;
    padding: 1rem;
    box-shadow: 0 22px 58px rgba(0,0,0,.16);
    border: 1px solid rgba(255,255,255,.56);
    margin-bottom: 1.2rem;
    overflow: hidden;
}

div[data-testid="stPlotlyChart"] {
    background: rgba(255,249,237,.96) !important;
    border-radius: 28px !important;
    overflow: hidden !important;
}

/* ── Recent data table ── */
.recent-title {
    color: var(--cream);
    font-size: 1.3rem;
    font-weight: 950;
    margin: 1.6rem 0 .8rem;
}

.chart-section {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    box-shadow: none !important;
    border: none !important;
}

[data-testid="stDataFrame"] {
    background: #fff9ed !important;
    border-radius: 28px !important;
    overflow: hidden !important;
    padding: .4rem !important;
    box-shadow: 0 18px 45px rgba(0,0,0,.16) !important;
}

.stCaptionContainer,
.stCaptionContainer p {
    color: rgba(255,245,220,.62) !important;
}

/* ── Responsive ── */
@media (max-width: 900px) {
    .market-title {
        font-size: 52px;
        letter-spacing: -2.5px;
    }

    .chart-wrap {
        border-radius: 24px;
        padding: .75rem;
    }

    .market-code-box,
    .market-flag-box {
        width: 80px;
        height: 80px;
        border-radius: 22px;
    }

    .market-code-box {
        font-size: 30px;
    }
}

/* Expander readability patch */
div[data-testid="stExpander"],
div[data-testid="stExpander"] *,
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary *,
div[data-testid="stExpander"] label,
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] span,
div[data-testid="stExpander"] div[role="radiogroup"] label,
div[data-testid="stExpander"] div[role="radiogroup"] label * {
    color: #fff5dc !important;
    -webkit-text-fill-color: #fff5dc !important;
}

div[data-testid="stExpander"] svg {
    color: #fff5dc !important;
    fill: #fff5dc !important;
}

</style>

""",
    unsafe_allow_html=True,
)


# ============================================================
# Data helpers
# ============================================================

@st.cache_data(ttl=3600)
def download_price(ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date + timedelta(days=1),
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif "Close" in df.columns.get_level_values(-1):
            df.columns = df.columns.get_level_values(-1)
        else:
            df.columns = df.columns.get_level_values(0)

    df = df.loc[:, ~df.columns.duplicated()].copy()

    if "Close" not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=["Close"]).copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df


@st.cache_data(ttl=3600)
def download_dividends(ticker: str, start_date: date, end_date: date) -> pd.Series:
    try:
        div = yf.Ticker(ticker).dividends
    except Exception:
        return pd.Series(dtype=float)

    if div is None or div.empty:
        return pd.Series(dtype=float)

    div.index = pd.to_datetime(div.index).tz_localize(None)
    div = div[
        (div.index >= pd.Timestamp(start_date))
        & (div.index <= pd.Timestamp(end_date))
    ]
    return div.astype(float)


def get_close_series(price_df: pd.DataFrame) -> pd.Series:
    if price_df.empty or "Close" not in price_df.columns:
        return pd.Series(dtype=float)

    close = price_df["Close"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = pd.to_numeric(close, errors="coerce").dropna()
    close.index = pd.to_datetime(close.index).tz_localize(None)
    return close


def fmt_money(x: float) -> str:
    if x is None or pd.isna(x):
        return "-"
    if abs(x) >= 100:
        return f"{x:,.0f}"
    return f"{x:,.2f}"


def fmt_pct(x: float) -> str:
    if x is None or pd.isna(x):
        return "-"
    return f"{x:.2f}%"


def annual_dividend_dataframe(dividends: pd.Series) -> pd.DataFrame:
    if dividends.empty:
        return pd.DataFrame(columns=["Year", "Dividend per Share"])

    annual = dividends.groupby(dividends.index.year).sum().reset_index()
    annual.columns = ["Year", "Dividend per Share"]
    return annual


def run_analysis(inp: UserInput) -> "Optional[AnalysisResult]":
    price_df = download_price(inp.ticker, inp.start_date, inp.end_date)

    if price_df.empty:
        return None

    close = get_close_series(price_df)

    if close.empty:
        return None

    dividends = download_dividends(inp.ticker, inp.start_date, inp.end_date)

    current_date = close.index[-1]
    current_price = float(close.iloc[-1])
    high_date = close.idxmax()
    high_price = float(close.max())
    drawdown_pct = (current_price / high_price - 1.0) * 100.0 if high_price > 0 else 0.0
    trigger_price = high_price * (1.0 - inp.trigger_pct / 100.0)
    trigger_hit = drawdown_pct <= -inp.trigger_pct

    annual_df = annual_dividend_dataframe(dividends)

    if dividends.empty:
        ttm_dividend = 0.0
        dividend_yield = 0.0
        latest_dividend_year = "-"
        latest_annual_dividend = 0.0
    else:
        ttm_start = current_date - pd.Timedelta(days=365)
        ttm_dividend = float(dividends[dividends.index >= ttm_start].sum())
        dividend_yield = (ttm_dividend / current_price * 100.0) if current_price > 0 else 0.0

        if annual_df.empty:
            latest_dividend_year = "-"
            latest_annual_dividend = 0.0
        else:
            latest_dividend_year = str(int(annual_df["Year"].iloc[-1]))
            latest_annual_dividend = float(annual_df["Dividend per Share"].iloc[-1])

    return AnalysisResult(
        current_date=current_date,
        current_price=current_price,
        high_date=high_date,
        high_price=high_price,
        drawdown_pct=drawdown_pct,
        trigger_price=trigger_price,
        trigger_hit=trigger_hit,
        ttm_dividend=ttm_dividend,
        dividend_yield=dividend_yield,
        latest_dividend_year=latest_dividend_year,
        latest_annual_dividend=latest_annual_dividend,
        annual_dividend_df=annual_df,
        price_df=price_df,
        close=close,
        dividends=dividends,
    )




# ============================================================
# Dividend reinvestment backtest engine
# ============================================================

def _next_trade_date(close: pd.Series, target_date: pd.Timestamp) -> Optional[pd.Timestamp]:
    idx = close.index[close.index >= pd.Timestamp(target_date)]
    if len(idx) == 0:
        return None
    return pd.Timestamp(idx[0])


def _first_trade_date_of_month(close: pd.Series, year: int, month: int) -> Optional[pd.Timestamp]:
    first_day = pd.Timestamp(date(year, month, 1))
    return _next_trade_date(close, first_day)


def _years_between(start: pd.Timestamp, end: pd.Timestamp) -> float:
    days = max((pd.Timestamp(end) - pd.Timestamp(start)).days, 1)
    return days / 365.25


def run_dividend_reinvest_backtest(
    close: pd.Series,
    dividends: pd.Series,
    initial_amount: float,
    monthly_amount: float,
    tax_rate_pct: float,
) -> Optional[DividendReinvestResult]:
    close = close.dropna().copy()
    if close.empty or initial_amount <= 0:
        return None

    close.index = pd.to_datetime(close.index).tz_localize(None)

    dividends = dividends.copy()
    if not dividends.empty:
        dividends.index = pd.to_datetime(dividends.index).tz_localize(None)
        dividends = dividends[(dividends.index >= close.index[0]) & (dividends.index <= close.index[-1])]
        dividends = dividends.sort_index().astype(float)

    tax_rate = max(0.0, min(100.0, float(tax_rate_pct))) / 100.0

    event_rows = []
    monthly_buy_dates = set()
    months = sorted(set((d.year, d.month) for d in close.index))
    for y, m in months:
        d = _first_trade_date_of_month(close, y, m)
        if d is not None and d != close.index[0] and monthly_amount > 0:
            monthly_buy_dates.add(d)

    dividend_events_by_trade_date = {}
    for div_date, div_per_share in dividends.items():
        trade_date = _next_trade_date(close, pd.Timestamp(div_date))
        if trade_date is None:
            continue
        dividend_events_by_trade_date.setdefault(trade_date, []).append((pd.Timestamp(div_date), float(div_per_share)))

    shares = 0.0
    total_external_invested = 0.0
    cumulative_gross_dividend = 0.0
    cumulative_tax = 0.0
    cumulative_net_dividend = 0.0
    cumulative_reinvested_amount = 0.0

    timeline_rows = []

    for d, price in close.items():
        d = pd.Timestamp(d)
        price = float(price)

        if d == close.index[0]:
            buy_shares = initial_amount / price if price > 0 else 0.0
            shares += buy_shares
            total_external_invested += initial_amount
            event_rows.append({
                "Date": d, "Type": "Initial Buy", "Price": price,
                "Cash Amount": initial_amount, "Gross Dividend": 0.0, "Tax": 0.0, "Net Dividend": 0.0,
                "Dividend per Share": 0.0, "Shares Bought": buy_shares, "Total Shares": shares,
                "External Invested": total_external_invested,
            })

        if d in monthly_buy_dates:
            buy_shares = monthly_amount / price if price > 0 else 0.0
            shares += buy_shares
            total_external_invested += monthly_amount
            event_rows.append({
                "Date": d, "Type": "Monthly Buy", "Price": price,
                "Cash Amount": monthly_amount, "Gross Dividend": 0.0, "Tax": 0.0, "Net Dividend": 0.0,
                "Dividend per Share": 0.0, "Shares Bought": buy_shares, "Total Shares": shares,
                "External Invested": total_external_invested,
            })

        for original_div_date, div_per_share in dividend_events_by_trade_date.get(d, []):
            if shares <= 0 or div_per_share <= 0:
                continue
            gross_dividend = shares * div_per_share
            tax = gross_dividend * tax_rate
            net_dividend = gross_dividend - tax
            reinvest_shares = net_dividend / price if price > 0 else 0.0

            cumulative_gross_dividend += gross_dividend
            cumulative_tax += tax
            cumulative_net_dividend += net_dividend
            cumulative_reinvested_amount += net_dividend
            shares += reinvest_shares

            event_rows.append({
                "Date": d, "Type": "Dividend Reinvest", "Price": price,
                "Cash Amount": net_dividend, "Gross Dividend": gross_dividend, "Tax": tax, "Net Dividend": net_dividend,
                "Dividend per Share": div_per_share, "Shares Bought": reinvest_shares, "Total Shares": shares,
                "External Invested": total_external_invested,
                "Original Dividend Date": original_div_date,
            })

        value = shares * price
        pnl = value - total_external_invested
        ret_pct = pnl / total_external_invested * 100.0 if total_external_invested > 0 else 0.0
        timeline_rows.append({
            "Date": d, "Price": price, "Total Shares": shares,
            "External Invested": total_external_invested,
            "Portfolio Value": value, "PnL": pnl, "Return %": ret_pct,
            "Cumulative Gross Dividend": cumulative_gross_dividend,
            "Cumulative Tax": cumulative_tax,
            "Cumulative Net Dividend": cumulative_net_dividend,
            "Cumulative Reinvested Amount": cumulative_reinvested_amount,
        })

    timeline_df = pd.DataFrame(timeline_rows)
    event_df = pd.DataFrame(event_rows)

    final_price = float(close.iloc[-1])
    final_value = shares * final_price
    total_profit = final_value - total_external_invested
    total_return_pct = total_profit / total_external_invested * 100.0 if total_external_invested > 0 else 0.0
    years = _years_between(close.index[0], close.index[-1])
    cagr = ((final_value / total_external_invested) ** (1.0 / years) - 1.0) * 100.0 if total_external_invested > 0 and final_value > 0 else 0.0

    recent_annual_dividend_per_share = 0.0
    if not dividends.empty:
        annual_div = dividends.groupby(dividends.index.year).sum()
        if not annual_div.empty:
            recent_annual_dividend_per_share = float(annual_div.iloc[-1])

    current_estimated_annual_dividend_gross = shares * recent_annual_dividend_per_share
    current_estimated_annual_dividend_net = current_estimated_annual_dividend_gross * (1.0 - tax_rate)
    yield_on_cost_net = current_estimated_annual_dividend_net / total_external_invested * 100.0 if total_external_invested > 0 else 0.0
    current_yield_net = current_estimated_annual_dividend_net / final_value * 100.0 if final_value > 0 else 0.0

    if event_df.empty:
        annual_df = pd.DataFrame()
    else:
        div_events = event_df[event_df["Type"] == "Dividend Reinvest"].copy()
        if div_events.empty:
            annual_df = pd.DataFrame()
        else:
            div_events["Year"] = div_events["Date"].dt.year
            annual_df = div_events.groupby("Year", as_index=False).agg({
                "Gross Dividend": "sum",
                "Tax": "sum",
                "Net Dividend": "sum",
                "Shares Bought": "sum",
            })
            annual_df["Cumulative Net Dividend"] = annual_df["Net Dividend"].cumsum()

    summary = {
        "Initial Amount": float(initial_amount),
        "Monthly Amount": float(monthly_amount),
        "Tax Rate %": float(tax_rate_pct),
        "Total External Invested": float(total_external_invested),
        "Final Portfolio Value": float(final_value),
        "Total Profit": float(total_profit),
        "Total Return %": float(total_return_pct),
        "CAGR %": float(cagr),
        "Final Shares": float(shares),
        "Cumulative Gross Dividend": float(cumulative_gross_dividend),
        "Cumulative Tax": float(cumulative_tax),
        "Cumulative Net Dividend": float(cumulative_net_dividend),
        "Current Estimated Annual Dividend Gross": float(current_estimated_annual_dividend_gross),
        "Current Estimated Annual Dividend Net": float(current_estimated_annual_dividend_net),
        "Yield on Cost Net %": float(yield_on_cost_net),
        "Current Yield Net %": float(current_yield_net),
        "Recent Annual Dividend Per Share": float(recent_annual_dividend_per_share),
        "Final Price": float(final_price),
    }

    return DividendReinvestResult(summary=summary, event_df=event_df, timeline_df=timeline_df, annual_df=annual_df)

# ============================================================
# Rendering helpers
# ============================================================

_CHART_LAYOUT = dict(
    height=580,
    paper_bgcolor="rgba(255,249,237,1)",
    plot_bgcolor="rgba(255,253,244,1)",
    font=dict(color="#1f2b18", size=13),
    margin=dict(l=40, r=30, t=60, b=45),
)

_AXIS_STYLE = dict(showgrid=True, gridcolor="rgba(31,43,24,.08)")


def render_top_nav() -> None:
    landing_url = "http://localhost:8082/global_cup_landing_final.html"

    st.markdown(
        f"""
<div class="top-nav">
    <div class="brand">
        <div class="brand-mark">📈</div>
        <div>Global Cup</div>
    </div>
    <a class="home-pill" href="{landing_url}" target="_self">← Back to home</a>
</div>
""",
        unsafe_allow_html=True,
    )


def get_market_from_query() -> str:
    market = st.query_params.get("market", "Global")
    if market not in MARKETS:
        market = "Global"
    return market


def render_market_selector() -> MarketConfig:
    default_market = get_market_from_query()
    market_keys = list(MARKETS.keys())

    with st.expander("Market page selector", expanded=False):
        selected_market = st.radio(
            "Market",
            market_keys,
            index=market_keys.index(default_market),
            horizontal=True,
            key="selected_market",
        )

    st.query_params["market"] = selected_market
    return MARKETS[selected_market]


def _parse_date(raw: str, fallback: date) -> date:
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        return fallback


def _parse_trigger(raw: str, fallback: float = 10.0) -> float:
    try:
        val = float(raw.strip())
        return max(1.0, min(80.0, val))
    except ValueError:
        return fallback


def render_controls(config: MarketConfig) -> UserInput:
    ticker_labels = list(config.tickers.keys())
    default_idx = (
        ticker_labels.index(config.default_ticker_label)
        if config.default_ticker_label in ticker_labels
        else 0
    )

    today = date.today()
    default_start = today.replace(year=today.year - 5)

    col1, col2 = st.columns([1.5, 0.9])

    with col1:
        ticker_label = st.selectbox(
            "Ticker search",
            ticker_labels,
            index=default_idx,
            key=f"ticker_select_{config.key}",
        )

    with col2:
        raw_trigger = st.text_input(
            "Trigger %",
            value="10",
            placeholder="e.g. 10",
            key=f"trigger_pct_{config.key}",
        )

    trigger_pct = _parse_trigger(raw_trigger)

    col3, col4 = st.columns(2)

    with col3:
        raw_start = st.text_input(
            "Start date  (YYYY-MM-DD)",
            value=default_start.strftime("%Y-%m-%d"),
            placeholder="e.g. 2019-01-01",
            key=f"start_date_{config.key}",
        )

    with col4:
        raw_end = st.text_input(
            "End date  (YYYY-MM-DD)",
            value=today.strftime("%Y-%m-%d"),
            placeholder="e.g. 2024-12-31",
            key=f"end_date_{config.key}",
        )

    start_date = _parse_date(raw_start, default_start)
    end_date = _parse_date(raw_end, today)

    return UserInput(
        market_key=config.key,
        ticker_label=ticker_label,
        ticker=config.tickers[ticker_label],
        trigger_pct=trigger_pct,
        start_date=start_date,
        end_date=end_date,
    )


def render_price_chart(inp: UserInput, config: MarketConfig, result: AnalysisResult) -> None:
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=result.close.index,
            y=result.close,
            mode="lines",
            name=f"{inp.ticker} Close",
            line=dict(color=config.line, width=4),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[result.high_date],
            y=[result.high_price],
            mode="markers+text",
            name="Period High",
            marker=dict(size=14, color="#ca6702", symbol="triangle-up"),
            text=["HIGH"],
            textposition="top center",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[result.current_date],
            y=[result.current_price],
            mode="markers+text",
            name="Current",
            marker=dict(size=13, color=config.chart2, symbol="circle"),
            text=["NOW"],
            textposition="bottom center",
        )
    )

    fig.add_hline(
        y=result.trigger_price,
        line_dash="dash",
        line_color="#b42318",
        annotation_text=(
            f"Trigger {inp.trigger_pct:.0f}%: {fmt_money(result.trigger_price)}"
        ),
        annotation_position="bottom right",
    )

    if not result.dividends.empty:
        div_dates, div_prices = [], []
        for d in result.dividends.index:
            available = result.close[result.close.index <= d]
            if not available.empty:
                div_dates.append(d)
                div_prices.append(float(available.iloc[-1]))

        if div_dates:
            fig.add_trace(
                go.Scatter(
                    x=div_dates,
                    y=div_prices,
                    mode="markers",
                    name="Dividend",
                    marker=dict(size=8, color="#8eb957", symbol="diamond"),
                )
            )

    fig.update_layout(
        title=f"{inp.ticker_label} / Price · High · Trigger · Dividend",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.13),
        **_CHART_LAYOUT,
    )
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)
    
    st.plotly_chart(fig, use_container_width=True)


def render_dividend_chart(config: MarketConfig, result: AnalysisResult) -> None:
    annual = result.annual_dividend_df

   

    if annual.empty:
        st.info(
            "배당 데이터가 없습니다. "
            "한국 종목/ETF는 yfinance 배당 데이터가 누락될 수 있습니다."
        )
        return

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=annual["Year"],
            y=annual["Dividend per Share"],
            name="Annual Dividend per Share",
            marker=dict(color=config.chart1),
        )
    )

    fig.update_layout(title="Annual Dividend per Share", **_CHART_LAYOUT)
    fig.update_xaxes(**_AXIS_STYLE)
    fig.update_yaxes(**_AXIS_STYLE)

    st.plotly_chart(fig, use_container_width=True)


def render_recent_data(result: AnalysisResult) -> None:
    st.markdown('<div class="recent-title">최근 데이터</div>', unsafe_allow_html=True)

    show_cols = [
        c for c in ["Open", "High", "Low", "Close", "Volume"]
        if c in result.price_df.columns
    ]
    view_df = result.price_df[show_cols].tail(40).copy()
    view_df.index = view_df.index.strftime("%Y-%m-%d")
    st.dataframe(view_df, use_container_width=True)

    if not result.annual_dividend_df.empty:
        st.markdown(
            '<div class="recent-title">Annual dividend data</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(result.annual_dividend_df, use_container_width=True)




def render_dividend_reinvest_tab(inp: UserInput, config: MarketConfig, result: AnalysisResult) -> None:
    rule = get_market_rule(config.key)
    currency = rule["currency"]
    default_tax = float(rule["tax_rate"])

    col1, col2, col3 = st.columns(3)
    with col1:
        initial_amount = st.number_input(
            f"초기 투자금 ({currency})",
            min_value=0.0,
            value=10000.0 if currency != "KRW" else 10000000.0,
            step=1000.0 if currency != "KRW" else 1000000.0,
            key=f"reinvest_initial_{config.key}",
        )
    with col2:
        monthly_amount = st.number_input(
            f"월 추가 투자금 ({currency})",
            min_value=0.0,
            value=0.0,
            step=100.0 if currency != "KRW" else 100000.0,
            key=f"reinvest_monthly_{config.key}",
        )
    with col3:
        tax_rate_pct = st.number_input(
            "배당세율 (%)",
            min_value=0.0,
            max_value=60.0,
            value=default_tax,
            step=0.1,
            key=f"reinvest_tax_{config.key}",
        )

    reinvest = run_dividend_reinvest_backtest(
        close=result.close,
        dividends=result.dividends,
        initial_amount=float(initial_amount),
        monthly_amount=float(monthly_amount),
        tax_rate_pct=float(tax_rate_pct),
    )

    if reinvest is None:
        st.info("배당 재투자 백테스트를 계산할 수 없습니다. 초기 투자금과 가격 데이터를 확인하세요.")
        return

    s = reinvest.summary

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("총 외부 투자금", f'{fmt_money(s["Total External Invested"])} {currency}')
    m2.metric("최종 평가금액", f'{fmt_money(s["Final Portfolio Value"])} {currency}')
    m3.metric("총 수익률", fmt_pct(s["Total Return %"]))
    m4.metric("CAGR", fmt_pct(s["CAGR %"]))

    n1, n2, n3, n4 = st.columns(4)
    n1.metric("최종 보유수량", f'{s["Final Shares"]:,.4f}')
    n2.metric("누적 순배당", f'{fmt_money(s["Cumulative Net Dividend"])} {currency}')
    n3.metric("현재 예상 순연배당", f'{fmt_money(s["Current Estimated Annual Dividend Net"])} {currency}')
    n4.metric("Yield on Cost", fmt_pct(s["Yield on Cost Net %"]))

    st.caption(
        f'시장 기본 통화: {currency} / 배당세율: {tax_rate_pct:.2f}% / '
        f'최근 연간 주당 배당금: {s["Recent Annual Dividend Per Share"]:,.4f} / '
        f'현재 순배당률: {s["Current Yield Net %"]:.2f}%'
    )

    if result.dividends.empty:
        st.warning("yfinance 배당 데이터가 비어 있습니다. 한국 ETF/일부 해외 종목은 배당 데이터가 누락될 수 있습니다.")

    if not reinvest.timeline_df.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=reinvest.timeline_df["Date"],
                y=reinvest.timeline_df["External Invested"],
                mode="lines",
                name="External Invested",
                line=dict(color="#8a8f7a", width=3),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=reinvest.timeline_df["Date"],
                y=reinvest.timeline_df["Portfolio Value"],
                mode="lines",
                name="Dividend Reinvested Value",
                line=dict(color=config.line, width=4),
            )
        )
        fig.update_layout(
            title=f"{inp.ticker_label} / Dividend Reinvestment Backtest",
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.13),
            **_CHART_LAYOUT,
        )
        fig.update_xaxes(**_AXIS_STYLE)
        fig.update_yaxes(**_AXIS_STYLE)
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=reinvest.timeline_df["Date"],
                y=reinvest.timeline_df["Total Shares"],
                mode="lines",
                name="Total Shares",
                line=dict(color=config.chart1, width=4),
            )
        )
        fig2.update_layout(
            title="Share Count Growth",
            hovermode="x unified",
            legend=dict(orientation="h", y=-0.13),
            **_CHART_LAYOUT,
        )
        fig2.update_xaxes(**_AXIS_STYLE)
        fig2.update_yaxes(**_AXIS_STYLE)
        st.plotly_chart(fig2, use_container_width=True)

    if not reinvest.annual_df.empty:
        st.markdown('<div class="recent-title">연도별 배당 재투자 요약</div>', unsafe_allow_html=True)
        annual_view = reinvest.annual_df.copy()
        for c in ["Gross Dividend", "Tax", "Net Dividend", "Shares Bought", "Cumulative Net Dividend"]:
            if c in annual_view.columns:
                annual_view[c] = annual_view[c].map(lambda x: f"{x:,.4f}")
        st.dataframe(annual_view, use_container_width=True)

    if not reinvest.event_df.empty:
        st.markdown('<div class="recent-title">배당 재투자 이벤트 로그</div>', unsafe_allow_html=True)
        event_view = reinvest.event_df.tail(80).copy()
        if "Date" in event_view.columns:
            event_view["Date"] = event_view["Date"].dt.strftime("%Y-%m-%d")
        if "Original Dividend Date" in event_view.columns:
            event_view["Original Dividend Date"] = pd.to_datetime(event_view["Original Dividend Date"], errors="coerce").dt.strftime("%Y-%m-%d")
        for c in ["Price", "Cash Amount", "Gross Dividend", "Tax", "Net Dividend", "Dividend per Share", "Shares Bought", "Total Shares", "External Invested"]:
            if c in event_view.columns:
                event_view[c] = event_view[c].map(lambda x: f"{x:,.4f}" if pd.notna(x) else "-")
        st.dataframe(event_view, use_container_width=True)

# ============================================================
# Main app
# ============================================================

render_top_nav()
config = render_market_selector()

left, right = st.columns([0.88, 1.12], gap="large")

with left:
    flag_class = get_flag_class(config)
    st.markdown(
        f"""
<div class="market-badge-row">
    <div class="market-code-box">{config.badge_code}</div>
    <div class="market-flag-box">
        <div class="drawn-flag {flag_class}"></div>
    </div>
</div>
<div class="market-title">{config.name}</div>
<div class="market-subtitle">{config.subtitle}</div>
""",
        unsafe_allow_html=True,
    )
    user_input = render_controls(config)

if user_input.start_date >= user_input.end_date:
    st.error("시작일은 종료일보다 이전이어야 합니다. (Start date must be before end date)")
    st.stop()

with st.spinner(f"{user_input.ticker} 데이터를 불러오는 중..."):
    analysis = run_analysis(user_input)

if analysis is None:
    st.error("가격 데이터를 불러오지 못했습니다. 티커 또는 기간을 확인하세요.")
    st.stop()

# Right column: tabs — price chart | dividend chart
with right:
    price_tab, dividend_tab, reinvest_tab = st.tabs(["가격 / 전고점 / 트리거", "배당", "배당 재투자"])

    with price_tab:
        render_price_chart(user_input, config, analysis)

    with dividend_tab:
        render_dividend_chart(config, analysis)

    with reinvest_tab:
        render_dividend_reinvest_tab(user_input, config, analysis)

# Below main grid: recent data table
render_recent_data(analysis)

st.caption(
    "Data source: yfinance. "
    "이 앱은 투자 조언이 아니라 시각화/백테스트 실험용 대시보드입니다."
)