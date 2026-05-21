import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import date


# ============================================================
# Universe definitions
# Note: These are fixed MVP lists. Market-cap rankings change over time.
# ============================================================

US_TOP100 = {
    "NVIDIA": "NVDA",
    "Alphabet Class A": "GOOGL",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Broadcom": "AVGO",
    "Tesla": "TSLA",
    "Meta": "META",
    "Walmart": "WMT",
    "Berkshire Hathaway": "BRK-B",
    "Eli Lilly": "LLY",
    "JPMorgan Chase": "JPM",
    "Visa": "V",
    "Exxon Mobil": "XOM",
    "Mastercard": "MA",
    "UnitedHealth": "UNH",
    "Costco": "COST",
    "Netflix": "NFLX",
    "Oracle": "ORCL",
    "Johnson & Johnson": "JNJ",
    "Home Depot": "HD",
    "Procter & Gamble": "PG",
    "Bank of America": "BAC",
    "AbbVie": "ABBV",
    "Palantir": "PLTR",
    "Coca-Cola": "KO",
    "Philip Morris": "PM",
    "Chevron": "CVX",
    "Cisco": "CSCO",
    "Wells Fargo": "WFC",
    "Intel": "INTC",
    "Caterpillar": "CAT",
    "Lam Research": "LRCX",
    "AMD": "AMD",
    "Salesforce": "CRM",
    "Adobe": "ADBE",
    "McDonald's": "MCD",
    "Merck": "MRK",
    "PepsiCo": "PEP",
    "Thermo Fisher": "TMO",
    "Abbott Laboratories": "ABT",
    "Qualcomm": "QCOM",
    "Texas Instruments": "TXN",
    "Applied Materials": "AMAT",
    "Intuit": "INTU",
    "ServiceNow": "NOW",
    "Goldman Sachs": "GS",
    "Morgan Stanley": "MS",
    "American Express": "AXP",
    "BlackRock": "BLK",
    "S&P Global": "SPGI",
    "Booking Holdings": "BKNG",
    "Uber": "UBER",
    "RTX": "RTX",
    "Lockheed Martin": "LMT",
    "Boeing": "BA",
    "Honeywell": "HON",
    "Union Pacific": "UNP",
    "Deere": "DE",
    "General Electric": "GE",
    "NextEra Energy": "NEE",
    "ConocoPhillips": "COP",
    "Eaton": "ETN",
    "Lowe's": "LOW",
    "TJX Companies": "TJX",
    "Nike": "NKE",
    "Starbucks": "SBUX",
    "Mondelez": "MDLZ",
    "Colgate-Palmolive": "CL",
    "Prologis": "PLD",
    "American Tower": "AMT",
    "Equinix": "EQIX",
    "CME Group": "CME",
    "Charles Schwab": "SCHW",
    "Blackstone": "BX",
    "Citigroup": "C",
    "Progressive": "PGR",
    "Marsh & McLennan": "MMC",
    "Chubb": "CB",
    "Elevance Health": "ELV",
    "Cigna": "CI",
    "Amgen": "AMGN",
    "Gilead Sciences": "GILD",
    "Bristol Myers Squibb": "BMY",
    "Pfizer": "PFE",
    "Danaher": "DHR",
    "Vertex": "VRTX",
    "Regeneron": "REGN",
    "Stryker": "SYK",
    "Medtronic": "MDT",
    "Boston Scientific": "BSX",
    "Intuitive Surgical": "ISRG",
    "Micron": "MU",
    "KLA": "KLAC",
    "Palo Alto Networks": "PANW",
    "Arista Networks": "ANET",
    "Synopsys": "SNPS",
    "Cadence": "CDNS",
    "Automatic Data Processing": "ADP",
}

US_ETF_TOP50 = {
    "Vanguard S&P 500 ETF": "VOO",
    "iShares Core S&P 500 ETF": "IVV",
    "SPDR S&P 500 ETF Trust": "SPY",
    "Vanguard Total Stock Market ETF": "VTI",
    "Invesco QQQ Trust": "QQQ",
    "Vanguard FTSE Developed Markets ETF": "VEA",
    "Vanguard Growth ETF": "VUG",
    "SPDR Gold Shares": "GLD",
    "iShares Core MSCI EAFE ETF": "IEFA",
    "Vanguard Value ETF": "VTV",
    "Vanguard Total Bond Market ETF": "BND",
    "iShares Core MSCI Emerging Markets ETF": "IEMG",
    "Vanguard Total International Stock ETF": "VXUS",
    "iShares Core U.S. Aggregate Bond ETF": "AGG",
    "Vanguard FTSE Emerging Markets ETF": "VWO",
    "iShares Russell 1000 Growth ETF": "IWF",
    "Vanguard Information Technology ETF": "VGT",
    "iShares Core S&P Mid-Cap ETF": "IJH",
    "SPDR Portfolio S&P 500 ETF": "SPLG",
    "Vanguard Dividend Appreciation ETF": "VIG",
    "Vanguard Mid-Cap ETF": "VO",
    "iShares Core S&P Small-Cap ETF": "IJR",
    "Technology Select Sector SPDR Fund": "XLK",
    "Invesco S&P 500 Equal Weight ETF": "RSP",
    "Schwab U.S. Dividend Equity ETF": "SCHD",
    "iShares Gold Trust": "IAU",
    "iShares Core S&P Total U.S. Stock Market ETF": "ITOT",
    "iShares MSCI EAFE ETF": "EFA",
    "Vanguard Total International Bond ETF": "BNDX",
    "Vanguard High Dividend Yield ETF": "VYM",
    "iShares 0-3 Month Treasury Bond ETF": "SGOV",
    "iShares 20+ Year Treasury Bond ETF": "TLT",
    "iShares 7-10 Year Treasury Bond ETF": "IEF",
    "iShares iBoxx Investment Grade Corporate Bond ETF": "LQD",
    "iShares iBoxx High Yield Corporate Bond ETF": "HYG",
    "JPMorgan Equity Premium Income ETF": "JEPI",
    "JPMorgan Nasdaq Equity Premium Income ETF": "JEPQ",
    "Global X Nasdaq 100 Covered Call ETF": "QYLD",
    "Global X S&P 500 Covered Call ETF": "XYLD",
    "Global X Russell 2000 Covered Call ETF": "RYLD",
    "Vanguard Real Estate ETF": "VNQ",
    "Health Care Select Sector SPDR Fund": "XLV",
    "Financial Select Sector SPDR Fund": "XLF",
    "Energy Select Sector SPDR Fund": "XLE",
    "Consumer Staples Select Sector SPDR Fund": "XLP",
    "Consumer Discretionary Select Sector SPDR Fund": "XLY",
    "Industrial Select Sector SPDR Fund": "XLI",
    "Utilities Select Sector SPDR Fund": "XLU",
    "Communication Services Select Sector SPDR Fund": "XLC",
    "Materials Select Sector SPDR Fund": "XLB",
}

KOREA_TOP30 = {
    "Samsung Electronics": "005930.KS",
    "SK Hynix": "000660.KS",
    "LG Energy Solution": "373220.KS",
    "Hyundai Motor": "005380.KS",
    "Samsung Biologics": "207940.KS",
    "Kia": "000270.KS",
    "KB Financial Group": "105560.KS",
    "Celltrion": "068270.KS",
    "NAVER": "035420.KS",
    "Shinhan Financial Group": "055550.KS",
    "Hyundai Mobis": "012330.KS",
    "Samsung C&T": "028260.KS",
    "POSCO Holdings": "005490.KS",
    "Samsung SDI": "006400.KS",
    "LG Chem": "051910.KS",
    "LG Electronics": "066570.KS",
    "Kakao": "035720.KS",
    "Hana Financial Group": "086790.KS",
    "Samsung Fire & Marine": "000810.KS",
    "KT&G": "033780.KS",
    "Korea Electric Power": "015760.KS",
    "HD Hyundai Heavy Industries": "329180.KS",
    "Hanwha Aerospace": "012450.KS",
    "Doosan Enerbility": "034020.KS",
    "SK Square": "402340.KS",
    "Samsung Electro-Mechanics": "009150.KS",
    "LG Corp": "003550.KS",
    "HMM": "011200.KS",
    "Hyundai Glovis": "086280.KS",
    "Amorepacific": "090430.KS",
}

KOREA_ETF_TOP30 = {
    "KODEX 200": "069500.KS",
    "TIGER 200": "102110.KS",
    "KODEX CD금리액티브": "459580.KS",
    "TIGER CD금리투자KIS": "357870.KS",
    "KODEX KOFR금리액티브": "423160.KS",
    "TIGER KOFR금리액티브": "449170.KS",
    "KODEX 단기채권": "153130.KS",
    "TIGER 단기통안채": "157450.KS",
    "KODEX 종합채권(AA-이상)액티브": "273130.KS",
    "KODEX 국고채30년액티브": "439870.KS",
    "KODEX 미국S&P500TR": "379800.KS",
    "TIGER 미국S&P500": "360750.KS",
    "ACE 미국S&P500": "360200.KS",
    "RISE 미국S&P500": "379780.KS",
    "SOL 미국S&P500": "433330.KS",
    "KODEX 미국나스닥100TR": "379810.KS",
    "TIGER 미국나스닥100": "133690.KS",
    "ACE 미국나스닥100": "367380.KS",
    "RISE 미국나스닥100": "368590.KS",
    "KODEX 미국배당다우존스": "489250.KS",
    "TIGER 미국배당다우존스": "458730.KS",
    "SOL 미국배당다우존스": "446720.KS",
    "KODEX 2차전지산업": "305720.KS",
    "TIGER 2차전지테마": "305540.KS",
    "KODEX 반도체": "091160.KS",
    "TIGER 반도체": "091230.KS",
    "TIGER Fn반도체TOP10": "396500.KS",
    "KODEX 자동차": "091180.KS",
    "TIGER 차이나전기차SOLACTIVE": "371460.KS",
    "KODEX 골드선물(H)": "132030.KS",
}

KOREA_COVERED_CALL_ETF = {
    "KODEX 200타겟위클리커버드콜": "498400.KS",
    "TIGER 200커버드콜": "289480.KS",
    # Some mixed alphanumeric Korean ETF tickers may not work in yfinance.
    # Keep it commented out if Yahoo fails for this symbol.
    # "TIGER 200타겟위클리커버드콜": "0104N0.KS",
    "TIGER 미국나스닥100커버드콜(합성)": "441680.KS",
    "KODEX 미국나스닥100커버드콜(합성)": "449190.KS",
    "TIGER 미국S&P500배당귀족커버드콜": "429000.KS",
    "KODEX 미국S&P500배당귀족커버드콜": "276970.KS",
    "TIGER 미국30년국채커버드콜액티브(H)": "476550.KS",
    "KODEX 미국30년국채타겟커버드콜(합성 H)": "487230.KS",
    "RISE 미국30년국채커버드콜": "472830.KS",
}

GLOBAL_EX_US_KR_TOP50 = {
    "TSMC": "TSM",
    "Tencent": "0700.HK",
    "Alibaba": "9988.HK",
    "Toyota": "7203.T",
    "ASML": "ASML",
    "SAP": "SAP",
    "Nestle": "NESN.SW",
    "Novo Nordisk": "NOVO-B.CO",
    "LVMH": "MC.PA",
    "Roche": "ROG.SW",
    "AstraZeneca": "AZN.L",
    "Shell": "SHEL.L",
    "Novartis": "NOVN.SW",
    "HSBC": "HSBA.L",
    "Hermes": "RMS.PA",
    "Siemens": "SIE.DE",
    "Unilever": "ULVR.L",
    "L'Oreal": "OR.PA",
    "TotalEnergies": "TTE.PA",
    "Sanofi": "SAN.PA",
    "Sony": "6758.T",
    "Mitsubishi UFJ": "8306.T",
    "Commonwealth Bank": "CBA.AX",
    "BHP": "BHP.AX",
    "Rio Tinto": "RIO.L",
    "Royal Bank of Canada": "RY.TO",
    "Toronto-Dominion Bank": "TD.TO",
    "Shopify": "SHOP.TO",
    "Canadian Natural Resources": "CNQ.TO",
    "Airbus": "AIR.PA",
    "Schneider Electric": "SU.PA",
    "Allianz": "ALV.DE",
    "Deutsche Telekom": "DTE.DE",
    "Mercedes-Benz Group": "MBG.DE",
    "BMW": "BMW.DE",
    "Volkswagen Pref": "VOW3.DE",
    "Prosus": "PRX.AS",
    "Adyen": "ADYEN.AS",
    "Diageo": "DGE.L",
    "BP": "BP.L",
    "Glencore": "GLEN.L",
    "RELX": "REL.L",
    "British American Tobacco": "BATS.L",
    "Keyence": "6861.T",
    "Hitachi": "6501.T",
    "Nintendo": "7974.T",
    "SoftBank Group": "9984.T",
    "Mitsubishi Corp": "8058.T",
    "Fast Retailing": "9983.T",
    "AIA Group": "1299.HK",
}

ALL_UNIVERSES = {
    "US Top 100": US_TOP100,
    "US ETF Top 50": US_ETF_TOP50,
    "Korea Top 30": KOREA_TOP30,
    "Korea ETF Top 30": KOREA_ETF_TOP30,
    "Korea Covered Call ETF": KOREA_COVERED_CALL_ETF,
    "Global ex-US/Korea Top 50": GLOBAL_EX_US_KR_TOP50,
}


# ============================================================
# Theme
# ============================================================

COLOR_NAVY = "#001219"
COLOR_BLUE = "#005f73"
COLOR_TEAL = "#0a9396"
COLOR_MINT = "#94d2bd"
COLOR_CREAM = "#e9d8a6"
COLOR_BURNT = "#ca6702"
COLOR_TEXT = "#132128"
COLOR_MUTED = "#5e6b73"
COLOR_LINE = "rgba(0,18,25,0.14)"
COLOR_PANEL = "#ffffff"
COLOR_BG = "#f7faf9"
COLOR_GRID = "rgba(0,18,25,0.14)"
COLOR_HIGH = COLOR_BURNT
COLOR_LOW = COLOR_BLUE

# ============================================================
# Font size settings - edit these numbers directly in code
# ============================================================
FONT_BASE = 20
FONT_LABEL = 20
FONT_TAB = 22
FONT_DASHBOARD_TITLE = 38
FONT_DASHBOARD_SUBTITLE = 20
FONT_CARD_TITLE = 28
FONT_CARD_SUBTITLE = 20
FONT_TICKER_BADGE = 18
FONT_TABLE_BASE = 20
FONT_TABLE_HEADER = 21
FONT_TABLE_CELL = 20
FONT_STATUS_BADGE = 18
FONT_BUTTON = 20
FONT_CHART_TITLE = 40
FONT_CHART_BASE = 24
FONT_CHART_AXIS_TITLE = 30
FONT_CHART_AXIS_TICK = 26
FONT_CHART_LEGEND = 24
FONT_CHART_MARKER_TEXT = 20

st.set_page_config(page_title="Global Stock Dashboard", layout="wide")

st.markdown(
    f"""
<style>
.stApp {{
    background:
        radial-gradient(circle at top left, rgba(148, 210, 189, 0.25), transparent 34rem),
        radial-gradient(circle at bottom right, rgba(238, 155, 0, 0.14), transparent 34rem),
        {COLOR_BG};
    color: {COLOR_TEXT};
}}
.main .block-container {{
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1680px;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {COLOR_NAVY} !important;
    font-weight: 900 !important;
}}
p, label, span, div {{ color: {COLOR_TEXT}; }}
.dashboard-card {{
    background: rgba(255,255,255,0.94);
    border: 1px solid {COLOR_LINE};
    border-radius: 28px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 18px 45px rgba(0,18,25,0.10);
    border-bottom: 4px solid {COLOR_BLUE};
}}
.dashboard-title {{
    font-size: {FONT_DASHBOARD_TITLE}px;
    font-weight: 950;
    letter-spacing: -0.04em;
    line-height: 1.0;
    color: {COLOR_NAVY};
    margin-bottom: 0.45rem;
}}
.dashboard-subtitle {{
    font-size: {FONT_DASHBOARD_SUBTITLE}px;
    color: {COLOR_MUTED};
    line-height: 1.55;
}}
.cycle-card {{
    background: rgba(255,255,255,0.96);
    border: 1px solid {COLOR_LINE};
    border-radius: 24px;
    padding: 1.3rem 1.5rem;
    margin-top: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 16px 38px rgba(0,18,25,0.08);
}}
.cycle-title {{
    font-size: {FONT_CARD_TITLE}px;
    font-weight: 950;
    color: {COLOR_NAVY};
    margin-bottom: 0.25rem;
}}
.cycle-subtitle {{
    color: {COLOR_MUTED};
    font-weight: 700;
    font-size: {FONT_CARD_SUBTITLE}px;
    margin-bottom: 0.3rem;
}}
.ticker-badge {{
    display: inline-block;
    background: rgba(10,147,150,0.08);
    color: {COLOR_BLUE};
    border: 1px solid rgba(10,147,150,0.18);
    padding: 0.35rem 0.7rem;
    border-radius: 999px;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
    font-weight: 800;
    font-size: {FONT_TICKER_BADGE}px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    font-size: {FONT_TABLE_BASE}px;
    background: white;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 12px 32px rgba(0,18,25,0.08);
    margin-top: 0.8rem;
    margin-bottom: 1.2rem;
}}
thead tr {{ background: linear-gradient(135deg, {COLOR_BLUE}, {COLOR_TEAL}); }}
th {{
    padding: 15px 13px;
    text-align: left;
    font-size: {FONT_TABLE_BASE}px;
    font-weight: 950;
    color: white !important;
    border-bottom: 1px solid rgba(0,18,25,0.12);
}}
td {{
    padding: 13px;
    border-bottom: 1px solid rgba(0,18,25,0.12);
    font-size: {FONT_TABLE_CELL}px;
    font-weight: 700;
    color: {COLOR_TEXT};
}}
tbody tr:hover {{ background: rgba(148,210,189,0.18); }}
.status-down-10 {{
    background: rgba(238, 155, 0, 0.22);
    color: {COLOR_BURNT};
    font-weight: 950;
    padding: 6px 12px;
    border-radius: 999px;
    display: inline-block;
}}
.status-down-20 {{
    background: rgba(202, 103, 2, 0.25);
    color: {COLOR_BURNT};
    font-weight: 950;
    padding: 6px 12px;
    border-radius: 999px;
    display: inline-block;
}}
.status-down-30 {{
    background: rgba(180, 40, 20, 0.22);
    color: #9b1c1c;
    font-weight: 950;
    padding: 6px 12px;
    border-radius: 999px;
    display: inline-block;
}}

/* Global font controls */
html, body, [class*="css"] {{
    font-size: {FONT_BASE}px !important;
}}
p, label, span, div {{
    font-size: {FONT_BASE}px;
}}
button[data-baseweb="tab"] {{
    font-size: {FONT_TAB}px !important;
    font-weight: 900 !important;
    padding: 16px 20px !important;
}}
button[data-baseweb="tab"] p {{
    font-size: {FONT_TAB}px !important;
    font-weight: 900 !important;
}}
th {{
    font-size: {FONT_TABLE_HEADER}px !important;
}}
td {{
    font-size: {FONT_TABLE_CELL}px !important;
}}
.status-down-10, .status-down-20, .status-down-30 {{
    font-size: {FONT_STATUS_BADGE}px !important;
}}
.stButton > button {{
    font-size: {FONT_BUTTON}px !important;
}}

.stButton > button {{
    background: linear-gradient(135deg, {COLOR_BLUE}, {COLOR_TEAL});
    color: white;
    border-radius: 14px;
    border: none;
    font-weight: 900;
    padding: 0.65rem 1.4rem;
    box-shadow: 0 14px 30px rgba(0,95,115,0.25);
}}
.stButton > button:hover {{ filter: brightness(1.07); transform: translateY(-1px); }}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# Calculation functions
# ============================================================

def get_ticker_dataframe(data, ticker):
    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
        if ticker in data.columns.get_level_values(0):
            return data[ticker]
    return data


def find_alternating_high_low(close, threshold=0.10):
    close = close.dropna()
    if len(close) < 3:
        return [], []

    highs = []
    lows = []
    trend = None

    candidate_high_idx = close.index[0]
    candidate_high_val = close.iloc[0]
    candidate_low_idx = close.index[0]
    candidate_low_val = close.iloc[0]

    for idx, val in close.iloc[1:].items():
        if trend is None:
            if val >= candidate_low_val * (1.0 + threshold):
                trend = "up"
                candidate_high_idx = idx
                candidate_high_val = val
            elif val <= candidate_high_val * (1.0 - threshold):
                trend = "down"
                candidate_low_idx = idx
                candidate_low_val = val
            else:
                if val > candidate_high_val:
                    candidate_high_idx = idx
                    candidate_high_val = val
                if val < candidate_low_val:
                    candidate_low_idx = idx
                    candidate_low_val = val
            continue

        if trend == "up":
            if val > candidate_high_val:
                candidate_high_idx = idx
                candidate_high_val = val
            drawdown = (val / candidate_high_val) - 1.0
            if drawdown <= -threshold:
                highs.append((candidate_high_idx, candidate_high_val))
                trend = "down"
                candidate_low_idx = idx
                candidate_low_val = val

        elif trend == "down":
            if val < candidate_low_val:
                candidate_low_idx = idx
                candidate_low_val = val
            rebound = (val / candidate_low_val) - 1.0
            if rebound >= threshold:
                lows.append((candidate_low_idx, candidate_low_val))
                trend = "up"
                candidate_high_idx = idx
                candidate_high_val = val

    return highs, lows


def classify_drop_bucket(change_pct):
    if -20 < change_pct <= -10:
        return "10~20% 하락"
    if -30 < change_pct <= -20:
        return "20~30% 하락"
    if change_pct <= -30:
        return "30% 이상 하락"
    return None


def classify_current_status(change_pct):
    if change_pct <= -30:
        return '<span class="status-down-30">30% 이상 하락</span>'
    if change_pct <= -20:
        return '<span class="status-down-20">20~30% 하락</span>'
    if change_pct <= -10:
        return '<span class="status-down-10">10~20% 하락</span>'
    return ""


def build_current_status(close, name, ticker, universe, threshold=0.10):
    close = close.dropna()
    if close.empty:
        return None

    _, lows = find_alternating_high_low(close, threshold=threshold)
    current_date = close.index[-1]
    current_price = float(close.iloc[-1])

    if lows:
        last_low_idx, last_low_price = lows[-1]
        after_last_low = close[close.index >= last_low_idx]
        if after_last_low.empty:
            return None
        reference_high_idx = after_last_low.idxmax()
        reference_high_price = float(after_last_low.max())
        reference_type = "마지막 전저점 이후 최고가"
        reference_low_date = last_low_idx.strftime("%Y-%m-%d")
        reference_low_price = f"{float(last_low_price):,.2f}"
    else:
        reference_high_idx = close.idxmax()
        reference_high_price = float(close.max())
        reference_type = "선택 기간 내 최고가"
        reference_low_date = "-"
        reference_low_price = "-"

    change_pct = (current_price / reference_high_price - 1.0) * 100.0
    drop_bucket = classify_drop_bucket(change_pct)
    if drop_bucket is None:
        return None

    return {
        "유니버스": universe,
        "기업": name,
        "티커": ticker,
        "하락 구간": drop_bucket,
        "기준": reference_type,
        "기준 전저점 날짜": reference_low_date,
        "기준 전저점 가격": reference_low_price,
        "현재 기준 전고점 날짜": reference_high_idx.strftime("%Y-%m-%d"),
        "현재 기준 전고점 가격": f"{reference_high_price:,.2f}",
        "현재 날짜": current_date.strftime("%Y-%m-%d"),
        "현재 가격": f"{current_price:,.2f}",
        "전고점 대비 변화율": f"{change_pct:.2f}%",
        "상태": classify_current_status(change_pct),
        "변화율 숫자": round(float(change_pct), 2),
    }


def build_drawdown_cycles(close, name, ticker, universe, threshold=0.10):
    highs, lows = find_alternating_high_low(close, threshold=threshold)
    cycles = []

    for high_idx, high_price in highs:
        next_lows = [
            (low_idx, low_price)
            for low_idx, low_price in lows
            if low_idx > high_idx
        ]
        if not next_lows:
            continue
        low_idx, low_price = next_lows[0]
        drop_pct = (low_price / high_price - 1.0) * 100.0
        cycles.append(
            {
                "유니버스": universe,
                "기업": name,
                "티커": ticker,
                "전고점 날짜": high_idx.strftime("%Y-%m-%d"),
                "전고점 가격": f"{float(high_price):,.2f}",
                "전저점 날짜": low_idx.strftime("%Y-%m-%d"),
                "전저점 가격": f"{float(low_price):,.2f}",
                "하락률": f"{drop_pct:.2f}%",
                "하락률 숫자": round(float(drop_pct), 2),
            }
        )
    return cycles


# ============================================================
# Rendering helpers
# ============================================================

def render_html_table(df):
    st.markdown(df.to_html(index=False, escape=False), unsafe_allow_html=True)


def render_drop_tables(status_df):
    table_columns = [
        "유니버스",
        "기업",
        "티커",
        "하락 구간",
        "기준",
        "기준 전저점 날짜",
        "현재 기준 전고점 날짜",
        "현재 기준 전고점 가격",
        "현재 날짜",
        "현재 가격",
        "전고점 대비 변화율",
        "상태",
    ]

    sections = [
        (
            "10~20% 하락 구간",
            status_df[(status_df["변화율 숫자"] <= -10) & (status_df["변화율 숫자"] > -20)],
        ),
        (
            "20~30% 하락 구간",
            status_df[(status_df["변화율 숫자"] <= -20) & (status_df["변화율 숫자"] > -30)],
        ),
        (
            "30% 이상 하락 구간",
            status_df[status_df["변화율 숫자"] <= -30],
        ),
    ]

    for title, df in sections:
        st.markdown(
            f"""
<div class="cycle-card">
    <div class="cycle-title">{title}</div>
    <div class="cycle-subtitle">
        현재 기준 전고점 대비 {title}에 해당하는 종목입니다.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if df.empty:
            st.info(f"{title}에 해당하는 종목이 없습니다.")
        else:
            df = df.sort_values("변화율 숫자").reset_index(drop=True)
            render_html_table(df[table_columns])


def render_universe_dashboard(title, universe_name, universe_dict, start_date, end_date, threshold):
    st.markdown(
        f"""
<div class="cycle-card">
    <div class="cycle-title">{title}</div>
    <div class="cycle-subtitle">
        현재 기준 전고점 대비 10% 이상 하락한 종목만 3개 구간으로 분류합니다.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button(f"{title} 분석 실행", key=f"run_{universe_name}"):
        tickers = list(universe_dict.values())
        with st.spinner(f"{title} 전체 데이터를 다운로드하는 중..."):
            data = yf.download(
                tickers=tickers,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                progress=False,
                group_by="ticker",
                threads=True,
            )

        if data.empty:
            st.error("데이터를 불러오지 못했습니다.")
            return

        rows = []
        failed = []
        for company, ticker in universe_dict.items():
            df = get_ticker_dataframe(data, ticker)
            if "Close" not in df.columns:
                failed.append(ticker)
                continue
            close = df["Close"].dropna()
            status = build_current_status(
                close=close,
                name=company,
                ticker=ticker,
                universe=universe_name,
                threshold=threshold,
            )
            if status:
                rows.append(status)

        if failed:
            st.caption(f"데이터가 없거나 실패한 티커: {', '.join(failed[:20])}")

        if not rows:
            st.success("현재 기준 전고점 대비 10% 이상 하락한 종목이 없습니다.")
            return

        status_df = pd.DataFrame(rows)
        render_drop_tables(status_df)


def add_high_low_markers(fig, close, name, ticker, threshold=0.10):
    highs, lows = find_alternating_high_low(close, threshold=threshold)

    if highs:
        fig.add_trace(
            go.Scatter(
                x=[x for x, _ in highs],
                y=[y for _, y in highs],
                mode="markers+text",
                name=f"{name} 전고점",
                marker=dict(
                    color=COLOR_HIGH,
                    size=16,
                    symbol="triangle-up",
                    line=dict(width=2.0, color=COLOR_CREAM),
                ),
                text=["H"] * len(highs),
                textposition="top center",
                textfont=dict(color=COLOR_HIGH, size=FONT_CHART_MARKER_TEXT),
            )
        )

    if lows:
        fig.add_trace(
            go.Scatter(
                x=[x for x, _ in lows],
                y=[y for _, y in lows],
                mode="markers+text",
                name=f"{name} 전저점",
                marker=dict(
                    color=COLOR_LOW,
                    size=16,
                    symbol="triangle-down",
                    line=dict(width=2.0, color=COLOR_MINT),
                ),
                text=["L"] * len(lows),
                textposition="bottom center",
                textfont=dict(color=COLOR_LOW, size=FONT_CHART_MARKER_TEXT),
            )
        )


def render_individual_chart_dashboard(start_date, end_date, threshold, threshold_pct):
    all_company_map = {}
    for universe_name, universe_dict in ALL_UNIVERSES.items():
        for company, ticker in universe_dict.items():
            label = f"[{universe_name}] {company}"
            all_company_map[label] = {
                "universe": universe_name,
                "company": company,
                "ticker": ticker,
            }

    selected_labels = st.multiselect(
        "차트에 표시할 기업/ETF 선택",
        options=list(all_company_map.keys()),
        default=list(all_company_map.keys())[:1],
    )

    chart_type = st.radio(
        "차트 타입",
        ["종가 라인 차트", "캔들 차트"],
        horizontal=True,
        key="chart_type_individual",
    )

    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        show_normalized = st.checkbox(
            "수익률 비교용 100 기준 정규화",
            value=False,
            key="show_normalized_individual",
        )
    with opt_col2:
        show_high_low = st.checkbox(
            "전고점 / 전저점 표시",
            value=True,
            key="show_high_low_individual",
        )

    if not selected_labels:
        st.warning("차트에 표시할 항목을 하나 이상 선택하세요.")
        return

    selected_items = [all_company_map[label] for label in selected_labels]
    selected_tickers = [item["ticker"] for item in selected_items]

    badges = "".join(f'<span class="ticker-badge">{ticker}</span>' for ticker in selected_tickers)
    st.markdown(badges, unsafe_allow_html=True)

    if st.button("개별 차트 분석 실행", key="run_individual_chart"):
        if start_date >= end_date:
            st.error("시작일은 종료일보다 이전이어야 합니다.")
            return

        with st.spinner("선택 항목 데이터를 다운로드하는 중..."):
            data = yf.download(
                tickers=selected_tickers,
                start=start_date,
                end=end_date,
                auto_adjust=False,
                progress=False,
                group_by="ticker",
                threads=True,
            )

        if data.empty:
            st.error("데이터를 불러오지 못했습니다.")
            return

        fig = go.Figure()
        all_cycles = []
        current_status_rows = []

        if chart_type == "종가 라인 차트":
            for item in selected_items:
                df = get_ticker_dataframe(data, item["ticker"])
                if "Close" not in df.columns:
                    st.warning(f'{item["ticker"]}: Close 컬럼이 없습니다.')
                    continue
                close = df["Close"].dropna()
                if close.empty:
                    continue

                if show_normalized:
                    y = close / close.iloc[0] * 100.0
                    y_title = "Normalized Price, Start = 100"
                else:
                    y = close
                    y_title = "Close Price"

                fig.add_trace(
                    go.Scatter(
                        x=close.index,
                        y=y,
                        mode="lines",
                        name=f'{item["company"]} ({item["ticker"]})',
                        line=dict(width=3.0),
                    )
                )

                if show_high_low:
                    add_high_low_markers(fig, y, item["company"], item["ticker"], threshold)

                fig.update_yaxes(title_text=y_title)

                all_cycles.extend(
                    build_drawdown_cycles(
                        close,
                        item["company"],
                        item["ticker"],
                        item["universe"],
                        threshold,
                    )
                )

                status = build_current_status(
                    close,
                    item["company"],
                    item["ticker"],
                    item["universe"],
                    threshold,
                )
                if status:
                    current_status_rows.append(status)

        else:
            if len(selected_items) > 1:
                st.warning("캔들 차트는 첫 번째 선택 항목만 표시합니다.")

            item = selected_items[0]
            df = get_ticker_dataframe(data, item["ticker"])
            required = ["Open", "High", "Low", "Close"]
            for col in required:
                if col not in df.columns:
                    st.error(f'{item["ticker"]}: {col} 컬럼이 없습니다.')
                    return
            df = df.dropna(subset=required)

            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name=f'{item["company"]} ({item["ticker"]})',
                    increasing_line_color=COLOR_TEAL,
                    decreasing_line_color=COLOR_BURNT,
                )
            )

            close = df["Close"].dropna()
            if show_high_low:
                add_high_low_markers(fig, close, item["company"], item["ticker"], threshold)

            all_cycles.extend(
                build_drawdown_cycles(close, item["company"], item["ticker"], item["universe"], threshold)
            )
            status = build_current_status(close, item["company"], item["ticker"], item["universe"], threshold)
            if status:
                current_status_rows.append(status)

        fig.update_layout(
            title=dict(text=f"Stock Price Chart - ZigZag Threshold {threshold_pct}%", font=dict(size=FONT_CHART_TITLE, color=COLOR_NAVY)),
            xaxis_title="Date",
            height=800,
            hovermode="x unified",
            xaxis_rangeslider_visible=False,
            paper_bgcolor=COLOR_PANEL,
            plot_bgcolor="#f8fbfa",
            font=dict(color=COLOR_TEXT, size=FONT_CHART_BASE),
            margin=dict(l=90, r=70, t=120, b=90),
            xaxis=dict(
                title_font=dict(size=FONT_CHART_AXIS_TITLE),
                tickfont=dict(size=FONT_CHART_AXIS_TICK),
                gridcolor=COLOR_GRID,
                zerolinecolor=COLOR_GRID,
                showline=True,
                linecolor=COLOR_LINE,
            ),
            yaxis=dict(
                title_font=dict(size=FONT_CHART_AXIS_TITLE),
                tickfont=dict(size=FONT_CHART_AXIS_TICK),
                gridcolor=COLOR_GRID,
                zerolinecolor=COLOR_GRID,
                showline=True,
                linecolor=COLOR_LINE,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="right",
                x=1,
                bgcolor="rgba(255,255,255,0)",
                font=dict(color=COLOR_TEXT, size=FONT_CHART_BASE),
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="cycle-card"><div class="cycle-title">전고점 → 전저점 하락 사이클 리포트</div></div>', unsafe_allow_html=True)
        if all_cycles:
            cycle_df = pd.DataFrame(all_cycles).sort_values(["유니버스", "티커", "전고점 날짜"]).reset_index(drop=True)
            display_df = cycle_df[["유니버스", "기업", "티커", "전고점 날짜", "전고점 가격", "전저점 날짜", "전저점 가격", "하락률"]]
            render_html_table(display_df)
        else:
            st.info("확정된 전고점→전저점 하락 사이클이 없습니다.")

        st.markdown('<div class="cycle-card"><div class="cycle-title">현재 기준 전고점 대비 10% 이상 하락 항목</div></div>', unsafe_allow_html=True)
        if current_status_rows:
            render_drop_tables(pd.DataFrame(current_status_rows))
        else:
            st.success("선택 항목 중 현재 기준 전고점 대비 10% 이상 하락한 항목이 없습니다.")


# ============================================================
# Main UI
# ============================================================

st.markdown(
    """
<div class="dashboard-card">
    <div class="dashboard-title">Global Stock Dashboard</div>
    <div class="dashboard-subtitle">
        미국 Top 100 / 미국 ETF Top 50 / 한국 Top 30 / 한국 ETF / 커버드콜 ETF / 글로벌 Top 50을 분리해서
        현재 기준 전고점 대비 10% 이상 하락한 종목만 추적합니다.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "분석 시작일",
        value=date(2000, 1, 1),
        min_value=date(1980, 1, 1),
        max_value=date.today(),
    )
with col2:
    end_date = st.date_input(
        "분석 종료일",
        value=date.today(),
        min_value=date(1980, 1, 1),
        max_value=date.today(),
    )

threshold_pct = st.slider("전고점/전저점 확정 기준 (%)", min_value=1, max_value=50, value=10, step=1)
threshold = threshold_pct / 100.0

tab_us, tab_us_etf, tab_kr, tab_kr_etf, tab_kr_cc, tab_global, tab_chart = st.tabs(
    [
        "🇺🇸 미국 Top 100",
        "🇺🇸 미국 ETF Top 50",
        "🇰🇷 한국 Top 30",
        "🇰🇷 한국 ETF Top 30",
        "🇰🇷 커버드콜 ETF",
        "🌍 미국/한국 외 Top 50",
        "📈 개별 차트 분석",
    ]
)

with tab_us:
    render_universe_dashboard("미국 Top 100", "US Top 100", US_TOP100, start_date, end_date, threshold)
with tab_us_etf:
    render_universe_dashboard("미국 ETF Top 50", "US ETF Top 50", US_ETF_TOP50, start_date, end_date, threshold)
with tab_kr:
    render_universe_dashboard("한국 Top 30", "Korea Top 30", KOREA_TOP30, start_date, end_date, threshold)
with tab_kr_etf:
    render_universe_dashboard("한국 ETF Top 30", "Korea ETF Top 30", KOREA_ETF_TOP30, start_date, end_date, threshold)
with tab_kr_cc:
    render_universe_dashboard("한국 상장 커버드콜 ETF", "Korea Covered Call ETF", KOREA_COVERED_CALL_ETF, start_date, end_date, threshold)
with tab_global:
    render_universe_dashboard("미국/한국 외 글로벌 Top 50", "Global ex-US/Korea Top 50", GLOBAL_EX_US_KR_TOP50, start_date, end_date, threshold)
with tab_chart:
    render_individual_chart_dashboard(start_date, end_date, threshold, threshold_pct)
