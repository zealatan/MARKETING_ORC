import streamlit as st

from global_cup.config import LAYOUT, PAGE_ICON, PAGE_TITLE
from global_cup.data_loader import build_ticker_dict
from global_cup.market_config import MARKETS
from global_cup.analysis import run_analysis
from global_cup.dividend_reinvest import run_dividend_reinvest_backtest
from global_cup.ui import (
    inject_css,
    render_controls,
    render_data_range_info,
    render_dividend_tab,
    render_dividend_reinvest_tab,
    render_invest_simulation_tab,
    render_market_header,
    render_market_selector,
    render_price_tab,
    render_recent_data,
    render_reinvest_controls_left,
    render_reinvest_summary_left,
    render_top_nav,
)

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)
inject_css()

# ── Load extended ticker lists from CSV if available ──────────────────────────

for mkey, mconfig in MARKETS.items():
    csv_tickers = build_ticker_dict(mkey)
    if csv_tickers:
        mconfig.tickers = csv_tickers
        if mconfig.default_ticker_label not in csv_tickers:
            mconfig.default_ticker_label = next(iter(csv_tickers))

# ── Top nav ───────────────────────────────────────────────────────────────────

#render_top_nav()

# ── Market selector ───────────────────────────────────────────────────────────

config = render_market_selector()

# ── Two-column layout: left = header + controls, right = tabs ─────────────────

left, right = st.columns([0.88, 1.12], gap="large")

with left:
    render_market_header(config)
    user_input = render_controls(config)
    data_range_container = st.container()
    reinvest_params, reinvest_summary_container = render_reinvest_controls_left(config)

if user_input.start_date >= user_input.end_date:
    st.error("시작일은 종료일보다 이전이어야 합니다. (Start date must be before end date)")
    st.stop()

with st.spinner(f"{user_input.ticker} 데이터를 불러오는 중..."):
    analysis = run_analysis(user_input)

if analysis is None:
    st.error("가격 데이터를 불러오지 못했습니다. 티커 또는 기간을 확인하세요.")
    st.stop()

# ── Compute reinvest (shared by left summary + right chart tab) ───────────────

reinvest_result = run_dividend_reinvest_backtest(
    close=analysis.close,
    dividends=analysis.dividends,
    initial_amount=reinvest_params["initial_amount"],
    monthly_amount=reinvest_params["monthly_amount"],
    tax_rate_pct=reinvest_params["tax_rate_pct"],
)

no_reinvest_result = run_dividend_reinvest_backtest(
    close=analysis.close,
    dividends=analysis.dividends,
    initial_amount=reinvest_params["initial_amount"],
    monthly_amount=reinvest_params["monthly_amount"],
    tax_rate_pct=reinvest_params["tax_rate_pct"],
    reinvest_dividends=False,
)

reinvest_enabled = reinvest_params["reinvest_enabled"]
selected_result = reinvest_result if reinvest_enabled else no_reinvest_result

with data_range_container:
    render_data_range_info(analysis, user_input.start_date)

with reinvest_summary_container:
    render_reinvest_summary_left(
        selected_result,
        reinvest_params["currency"],
        reinvest_params["tax_rate_pct"],
    )

# ── Right column: tabs ────────────────────────────────────────────────────────

with right:
    st.markdown('<div style="height:18.0rem;"></div>', unsafe_allow_html=True)

    price_tab, invest_result_tab, dividend_tab, reinvest_tab = st.tabs(
        [
            "가격 / 전고점 / 트리거",
            "투자 시뮬레이션",
            "배당",
            "배당 재투자",
        ]
    )

    with price_tab:
        render_price_tab(user_input, config, analysis)
        # render_recent_data(price_trigger mode) is called inside render_price_tab

    with invest_result_tab:
        render_invest_simulation_tab(
            user_input,
            config,
            analysis,
            reinvest=reinvest_result,
            no_reinvest=no_reinvest_result,
            reinvest_enabled=reinvest_enabled,
        )

    with dividend_tab:
        render_dividend_tab(config, analysis)
        #render_recent_data(analysis, config=config)

    with reinvest_tab:
        render_dividend_reinvest_tab(
            user_input,
            config,
            analysis,
            selected=selected_result,
        )
        #render_recent_data(analysis, config=config)

st.caption(
    "Data source: yfinance. "
    "이 앱은 투자 조언이 아니라 시각화/백테스트 실험용 대시보드입니다. Not financial advice."
)
