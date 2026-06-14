from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

# Resolve data/ directory relative to this file's package root
_DATA_DIR = Path(__file__).parent.parent / "data"

_MARKET_CSV_MAP: Dict[str, str] = {
    "United States": "tickers_us.csv",
    "Korea":         "tickers_korea.csv",
    "Japan":         "tickers_japan.csv",
    "European Union":"tickers_eu.csv",
    "Global":        "tickers_global.csv",
}


def load_tickers_csv(market_key: str) -> Optional[pd.DataFrame]:
    filename = _MARKET_CSV_MAP.get(market_key)
    if not filename:
        return None
    path = _DATA_DIR / filename
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path)
        expected = {"label", "ticker", "category", "country", "currency"}
        if not expected.issubset(set(df.columns)):
            return None
        return df
    except Exception:
        return None


def build_ticker_dict(market_key: str) -> Optional[Dict[str, str]]:
    """Return {label: ticker} from CSV, or None if CSV unavailable."""
    df = load_tickers_csv(market_key)
    if df is None or df.empty:
        return None
    result: Dict[str, str] = {}
    for _, row in df.iterrows():
        label = str(row["label"]).strip()
        ticker = str(row["ticker"]).strip()
        if label and ticker:
            result[label] = ticker
    return result if result else None


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
        level = df.columns.get_level_values(0)
        if "Close" in level:
            df.columns = level
        else:
            df.columns = df.columns.get_level_values(-1)

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
