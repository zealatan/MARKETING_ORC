from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from .market_config import AnalysisResult, MarketConfig, UserInput
from .analysis import fmt_money
from .golden_engine import add_high_low_markers as _golden_add_hl_markers

CHART_HEIGHT_PRICE = 720
CHART_HEIGHT_REINVEST = 760

_LAYOUT_BASE = dict(
    height=CHART_HEIGHT_PRICE,
    paper_bgcolor="rgba(255,249,237,1)",
    plot_bgcolor="rgba(255,253,244,1)",
    font=dict(color="#1f2b18", size=13),
    margin=dict(l=40, r=30, t=60, b=45),
)

_AXIS = dict(showgrid=True, gridcolor="rgba(31,43,24,.08)")


# ── ZigZag marker helpers ──────────────────────────────────────────────────────

def add_high_low_markers(
    fig: go.Figure,
    zigzag_points: list,
    show_labels: bool = True,
) -> go.Figure:
    """
    Add alternating ZigZag H (triangle-up) and L (triangle-down) markers to fig.

    zigzag_points: list of ZigZagPoint objects from find_alternating_high_low().
    show_labels: if True, annotate each marker with 'H' or 'L'.
    """
    highs = [p for p in zigzag_points if p.point_type == "H"]
    lows  = [p for p in zigzag_points if p.point_type == "L"]

    if highs:
        fig.add_trace(go.Scatter(
            x=[p.date  for p in highs],
            y=[p.price for p in highs],
            mode="markers+text" if show_labels else "markers",
            name="ZigZag High",
            marker=dict(size=11, color="#ca6702", symbol="triangle-up"),
            text=["H"] * len(highs) if show_labels else None,
            textposition="top center",
            hovertemplate="H: %{y:.2f}<br>%{x}<extra></extra>",
        ))

    if lows:
        fig.add_trace(go.Scatter(
            x=[p.date  for p in lows],
            y=[p.price for p in lows],
            mode="markers+text" if show_labels else "markers",
            name="ZigZag Low",
            marker=dict(size=11, color="#2453d6", symbol="triangle-down"),
            text=["L"] * len(lows) if show_labels else None,
            textposition="bottom center",
            hovertemplate="L: %{y:.2f}<br>%{x}<extra></extra>",
        ))

    return fig


def add_trigger_buy_markers(
    fig: go.Figure,
    backtest_df: pd.DataFrame,
) -> go.Figure:
    """
    Add Buy markers at each trigger event found by run_backtest().
    backtest_df: output of run_backtest() — may be None or empty.
    """
    if backtest_df is None or backtest_df.empty:
        return fig

    fig.add_trace(go.Scatter(
        x=backtest_df["Buy Date"],
        y=backtest_df["Buy Price"],
        mode="markers+text",
        name="Trigger Buy",
        marker=dict(size=13, color="#22c55e", symbol="star"),
        text=["Buy"] * len(backtest_df),
        textposition="top center",
        hovertemplate=(
            "Buy: %{y:.2f}<br>%{x}"
            "<extra></extra>"
        ),
    ))
    return fig


# ── Primary price chart ────────────────────────────────────────────────────────

def price_chart(
    inp: UserInput,
    config: MarketConfig,
    result: AnalysisResult,
    show_zigzag: bool = True,
    show_buys: bool = True,
) -> go.Figure:
    """
    Full price chart with:
    1. Close price line
    2. ZigZag H markers (triangle-up, text=H)  — if show_zigzag
    3. ZigZag L markers (triangle-down, text=L) — if show_zigzag
    4. Trigger buy markers (star, text=Buy)     — if show_buys
    5. Current price marker
    6. ZigZag trigger level hline
    """
    fig = go.Figure()

    # ── 1. Price line ──────────────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=result.close.index,
        y=result.close,
        mode="lines",
        name=f"{inp.ticker} Close",
        line=dict(color=config.line, width=4),
    ))

    # ── 2 & 3. ZigZag H/L markers (golden engine) ────────────────────────────
    if show_zigzag:
        _golden_add_hl_markers(
            fig, result.close, inp.ticker, inp.ticker,
            threshold=inp.trigger_pct / 100.0,
        )

    # ── 4. Trigger buy markers ─────────────────────────────────────────────────
    if show_buys and result.backtest_df is not None:
        add_trigger_buy_markers(fig, result.backtest_df)

    # ── 5. Current price marker ────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[result.current_date],
        y=[result.current_price],
        mode="markers+text",
        name="Current",
        marker=dict(size=13, color=config.chart2, symbol="circle"),
        text=["NOW"],
        textposition="bottom center",
    ))

    # ── 6. Trigger hline (ZigZag-based reference high) ────────────────────────
    zz_trigger = result.zigzag_trigger_price
    fig.add_hline(
        y=zz_trigger,
        line_dash="dash",
        line_color="#b42318",
        annotation_text=(
            f"Trigger {inp.trigger_pct:.0f}%: {fmt_money(zz_trigger)}"
        ),
        annotation_position="bottom right",
    )

    fig.update_layout(
        title=f"{inp.ticker_label} / ZigZag · Trigger",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.13),
        **_LAYOUT_BASE,
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


# ── Remaining charts (unchanged) ──────────────────────────────────────────────

def dividend_bar_chart(config: MarketConfig, result: AnalysisResult) -> go.Figure | None:
    annual = result.annual_dividend_df
    if annual.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=annual["Year"],
        y=annual["Dividend per Share"],
        name="Annual Dividend per Share",
        marker=dict(color=config.chart1),
    ))
    fig.update_layout(title="Annual Dividend per Share", **_LAYOUT_BASE)
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


def reinvest_timeline_chart(
    inp: UserInput,
    config: MarketConfig,
    timeline_df: pd.DataFrame,
) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline_df["Date"],
        y=timeline_df["External Invested"],
        mode="lines",
        name="External Invested",
        line=dict(color="#8a8f7a", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=timeline_df["Date"],
        y=timeline_df["Portfolio Value"],
        mode="lines",
        name="Dividend Reinvested Value",
        line=dict(color=config.line, width=4),
    ))
    fig.update_layout(
        title=f"{inp.ticker_label} / Dividend Reinvestment Backtest",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.13),
        **{**_LAYOUT_BASE, "height": CHART_HEIGHT_REINVEST},
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


def investment_simulation_chart(
    inp: UserInput,
    config: MarketConfig,
    no_reinvest_df: pd.DataFrame,
    reinvest_df: pd.DataFrame | None = None,
    show_reinvest: bool = False,
) -> go.Figure:
    """No-reinvest baseline curve, with reinvest curve overlaid when requested.

    The no-reinvest portfolio is always plotted. When show_reinvest is True and
    reinvest_df is provided, an additional reinvest curve is overlaid on the
    same axes for visual comparison.
    """
    fig = go.Figure()

    if "External Invested" in no_reinvest_df.columns:
        fig.add_trace(go.Scatter(
            x=no_reinvest_df["Date"],
            y=no_reinvest_df["External Invested"],
            mode="lines",
            name="총 외부 투자금",
            line=dict(color="#8a8f7a", width=2, dash="dot"),
        ))

    if "Portfolio Value" in no_reinvest_df.columns:
        fig.add_trace(go.Scatter(
            x=no_reinvest_df["Date"],
            y=no_reinvest_df["Portfolio Value"],
            mode="lines",
            name="배당 미재투자",
            line=dict(color="#ca6702", width=3),
        ))

    if (
        show_reinvest
        and reinvest_df is not None
        and not reinvest_df.empty
        and "Portfolio Value" in reinvest_df.columns
    ):
        fig.add_trace(go.Scatter(
            x=reinvest_df["Date"],
            y=reinvest_df["Portfolio Value"],
            mode="lines",
            name="배당 재투자",
            line=dict(color=config.line, width=4),
        ))
        title = f"{inp.ticker_label} / 배당 재투자 vs 미재투자"
    else:
        title = f"{inp.ticker_label} / 배당 미재투자 시뮬레이션"

    fig.update_layout(
        title=title,
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.13),
        **{**_LAYOUT_BASE, "height": 660},
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


def investment_comparison_chart(
    inp: UserInput,
    config: MarketConfig,
    reinvest_df: pd.DataFrame,
    no_reinvest_df: pd.DataFrame,
) -> go.Figure:
    """Compare portfolio value with and without dividend reinvestment."""
    fig = go.Figure()

    baseline_df = reinvest_df if "External Invested" in reinvest_df.columns else no_reinvest_df
    if "External Invested" in baseline_df.columns:
        fig.add_trace(go.Scatter(
            x=baseline_df["Date"],
            y=baseline_df["External Invested"],
            mode="lines",
            name="총 외부 투자금",
            line=dict(color="#8a8f7a", width=2, dash="dot"),
        ))

    if "Portfolio Value" in no_reinvest_df.columns:
        fig.add_trace(go.Scatter(
            x=no_reinvest_df["Date"],
            y=no_reinvest_df["Portfolio Value"],
            mode="lines",
            name="배당 미재투자",
            line=dict(color="#ca6702", width=3),
        ))

    if "Portfolio Value" in reinvest_df.columns:
        fig.add_trace(go.Scatter(
            x=reinvest_df["Date"],
            y=reinvest_df["Portfolio Value"],
            mode="lines",
            name="배당 재투자",
            line=dict(color=config.line, width=4),
        ))

    fig.update_layout(
        title=f"{inp.ticker_label} / 배당 재투자 vs 미재투자",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.13),
        **{**_LAYOUT_BASE, "height": 660},
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


def share_count_chart(config: MarketConfig, timeline_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline_df["Date"],
        y=timeline_df["Total Shares"],
        mode="lines",
        name="Total Shares",
        line=dict(color=config.chart1, width=4),
    ))
    fig.update_layout(
        title="Share Count Growth",
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.13),
        **{**_LAYOUT_BASE, "height": CHART_HEIGHT_REINVEST},
    )
    fig.update_xaxes(**_AXIS)
    fig.update_yaxes(**_AXIS)
    return fig


def score_gauge_chart(score: float, rank_label: str, rank_color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "", "font": {"size": 38, "color": "#1f2b18"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#1f2b18"},
            "bar": {"color": rank_color, "thickness": 0.3},
            "bgcolor": "rgba(255,249,237,1)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],  "color": "rgba(200,200,200,0.18)"},
                {"range": [50, 65], "color": "rgba(205,127,50,0.18)"},
                {"range": [65, 80], "color": "rgba(192,192,192,0.18)"},
                {"range": [80, 100],"color": "rgba(255,215,0,0.18)"},
            ],
            "threshold": {
                "line": {"color": rank_color, "width": 4},
                "thickness": 0.75,
                "value": score,
            },
        },
        title={"text": f"Global Cup Score — {rank_label}", "font": {"size": 15, "color": "#1f2b18"}},
    ))
    fig.update_layout(
        height=260,
        paper_bgcolor="rgba(255,249,237,1)",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig
