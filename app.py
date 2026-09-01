# ============================================================
# BLACK PYRAMID v2003
# Hierarchical Intelligence Engine
# مبني على BLACK PYRAMID v2002 مع إعادة بناء:
# Structure → Regime → Setup → Confirmation → Context → Risk
#
# المتطلبات:
# pip install streamlit yfinance pandas numpy plotly requests
#
# المفاتيح اختيارية وتُقرأ من:
# - Streamlit secrets
# - Environment variables
#
# لا تضع أي API key داخل هذا الملف.
# ============================================================


import os
import json
import math
from pathlib import Path
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ============================================================
# APP CONFIG
# ============================================================

APP_VERSION = "v2003"
TRADES_FILE = Path("trades_data_v2003.json")

DEFAULT_BALANCE = 100000.0
DEFAULT_RISK_PERCENT = 1.0
MAX_DAILY_TRADES = 4
LOW_CONF_DAILY_LIMIT = 2

CONFIDENCE_MIN_TRADE = 70.0
MIN_RR_TP1 = 1.00
MIN_RR_TP2 = 1.50
MIN_RR_TP3 = 2.00

ASSET_PROFILES = {
    "forex": {
        "atr_period": 14,
        "rsi_period": 14,
        "rsi_ob": 70,
        "rsi_os": 30,
        "mfi_period": 14,
        "bb_period": 20,
        "bb_std": 2.0,
        "atr_sl": 1.20,
        "atr_trail": 1.00,
        "swing_order": 3,
        "structure_lookback": 120,
        "confidence_threshold": 70,
        "min_rr": 1.50,
        "pip_size": 0.0001,
        "contract_size": 100000,
    },
    "gold": {
        "atr_period": 14,
        "rsi_period": 14,
        "rsi_ob": 80,
        "rsi_os": 20,
        "mfi_period": 9,
        "bb_period": 20,
        "bb_std": 2.2,
        "atr_sl": 1.50,
        "atr_trail": 1.20,
        "swing_order": 3,
        "structure_lookback": 175,
        "confidence_threshold": 72,
        "min_rr": 1.50,
        "pip_size": 0.01,
        "contract_size": 100,
    },
    "crypto": {
        "atr_period": 14,
        "rsi_period": 14,
        "rsi_ob": 80,
        "rsi_os": 20,
        "mfi_period": 10,
        "bb_period": 50,
        "bb_std": 2.3,
        "atr_sl": 1.80,
        "atr_trail": 1.50,
        "swing_order": 4,
        "structure_lookback": 250,
        "confidence_threshold": 75,
        "min_rr": 1.50,
        "pip_size": 0.01,
        "contract_size": 1,
    },
}

PAIRS = {
    "XAU/USD (Gold)": "GC=F",
    "XAG/USD (Silver)": "SI=F",
    "DXY (Dollar Index)": "DX-Y.NYB",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "EUR/CHF": "EURCHF=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/NZD": "EURNZD=X",
    "EUR/CAD": "EURCAD=X",
    "GBP/JPY": "GBPJPY=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/AUD": "GBPAUD=X",
    "GBP/NZD": "GBPNZD=X",
    "GBP/CAD": "GBPCAD=X",
    "AUD/JPY": "AUDJPY=X",
    "AUD/CHF": "AUDCHF=X",
    "AUD/NZD": "AUDNZD=X",
    "AUD/CAD": "AUDCAD=X",
    "NZD/JPY": "NZDJPY=X",
    "NZD/CHF": "NZDCHF=X",
    "NZD/CAD": "NZDCAD=X",
    "CAD/JPY": "CADJPY=X",
    "CAD/CHF": "CADCHF=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
    "ETH/USD (Ethereum)": "ETH-USD",
}

CURRENCY_PAIRS = {
    "USD": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X", "NZDUSD=X"],
    "EUR": ["EURUSD=X", "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X", "EURCAD=X", "EURNZD=X"],
    "GBP": ["GBPUSD=X", "EURGBP=X", "GBPJPY=X", "GBPCHF=X", "GBPAUD=X", "GBPCAD=X", "GBPNZD=X"],
    "JPY": ["USDJPY=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", "NZDJPY=X", "CADJPY=X"],
    "CHF": ["USDCHF=X", "EURCHF=X", "GBPCHF=X", "AUDCHF=X", "NZDCHF=X", "CADCHF=X"],
    "AUD": ["AUDUSD=X", "EURAUD=X", "GBPAUD=X", "AUDJPY=X", "AUDNZD=X", "AUDCAD=X"],
    "NZD": ["NZDUSD=X", "EURNZD=X", "GBPNZD=X", "AUDNZD=X", "NZDJPY=X", "NZDCAD=X"],
    "CAD": ["USDCAD=X", "EURCAD=X", "GBPCAD=X", "AUDCAD=X", "NZDCAD=X", "CADJPY=X", "CADCHF=X"],
}


# ============================================================
# SECRETS
# ============================================================

def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, None)
        if value is not None:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


TWELVE_API_KEY = get_secret("TWELVE_API_KEY")
FMP_API_KEY = get_secret("FMP_API_KEY")
TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "selected_pair": "XAU/USD (Gold)",
        "all_signals": None,
        "show_manual": False,
        "currency_strength": None,
        "economic_events": None,
        "news": None,
        "daily_trade_count": 0,
        "trade_date": datetime.now().strftime("%Y-%m-%d"),
        "last_analysis": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_float(value, default=np.nan):
    try:
        x = float(value)
        return x if np.isfinite(x) else default
    except Exception:
        return default

def clamp(value, low, high):
    return max(low, min(high, value))

def asset_type_from_name(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["gold", "silver", "xau", "xag"]):
        return "gold"
    if any(x in n for x in ["bitcoin", "ethereum", "btc", "eth"]):
        return "crypto"
    return "forex"

def profile_for(name: str):
    return ASSET_PROFILES[asset_type_from_name(name)]

def fmt_price(value, pair_name):
    if value is None or not np.isfinite(safe_float(value)):
        return "N/A"
    if asset_type_from_name(pair_name) in ("gold", "crypto"):
        return f"${float(value):,.2f}"
    return f"{float(value):.5f}"

def reset_daily_counter():
    today = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.trade_date != today:
        st.session_state.trade_date = today
        st.session_state.daily_trade_count = 0

def can_open_trade(confidence):
    reset_daily_counter()
    count = st.session_state.daily_trade_count
    if count >= MAX_DAILY_TRADES:
        return False, "تم الوصول إلى الحد الأقصى اليومي للصفقات."
    if confidence < CONFIDENCE_MIN_TRADE and count >= LOW_CONF_DAILY_LIMIT:
        return False, "الثقة منخفضة ولا يسمح بصفقة إضافية وفق إدارة المخاطر."
    return True, ""


# ============================================================
# DATA LAYER
# ============================================================

def normalize_ohlcv(df):
    if df is None or df.empty:
        return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    rename = {}
    for c in df.columns:
        lc = str(c).lower()
        if lc == "open":
            rename[c] = "open"
        elif lc == "high":
            rename[c] = "high"
        elif lc == "low":
            rename[c] = "low"
        elif lc == "close":
            rename[c] = "close"
        elif lc in ("volume", "vol"):
            rename[c] = "volume"
    df = df.rename(columns=rename)
    required = ["open", "high", "low", "close"]
    if any(c not in df.columns for c in required):
        return None
    if "volume" not in df.columns:
        df["volume"] = 0.0
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[required + ["volume"]].dropna(subset=required)
    df = df[~df.index.duplicated(keep="last")]
    df = df.sort_index()
    return df if len(df) >= 50 else None

@st.cache_data(ttl=60, show_spinner=False)
def get_yfinance(symbol, period="3mo", interval="4h"):
    try:
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        return normalize_ohlcv(df)
    except Exception:
        return None

@st.cache_data(ttl=120, show_spinner=False)
def get_twelve_data(symbol, interval="4h", outputsize=500):
    if not TWELVE_API_KEY:
        return None
    mapping = {
        "GC=F": "XAU/USD",
        "SI=F": "XAG/USD",
        "DX-Y.NYB": "DXY",
        "EURUSD=X": "EUR/USD",
        "GBPUSD=X": "GBP/USD",
        "USDJPY=X": "USD/JPY",
        "USDCHF=X": "USD/CHF",
        "AUDUSD=X": "AUD/USD",
        "NZDUSD=X": "NZD/USD",
        "USDCAD=X": "USD/CAD",
        "EURGBP=X": "EUR/GBP",
        "EURJPY=X": "EUR/JPY",
        "EURCHF=X": "EUR/CHF",
        "EURAUD=X": "EUR/AUD",
        "EURNZD=X": "EUR/NZD",
        "EURCAD=X": "EUR/CAD",
        "GBPJPY=X": "GBP/JPY",
        "GBPCHF=X": "GBP/CHF",
        "GBPAUD=X": "GBP/AUD",
        "GBPNZD=X": "GBP/NZD",
        "GBPCAD=X": "GBP/CAD",
        "AUDJPY=X": "AUD/JPY",
        "AUDCHF=X": "AUD/CHF",
        "AUDNZD=X": "AUD/NZD",
        "AUDCAD=X": "AUD/CAD",
        "NZDJPY=X": "NZD/JPY",
        "NZDCHF=X": "NZD/CHF",
        "NZDCAD=X": "NZD/CAD",
        "CADJPY=X": "CAD/JPY",
        "CADCHF=X": "CAD/CHF",
        "BTC-USD": "BTC/USD",
        "ETH-USD": "ETH/USD",
    }
    td_symbol = mapping.get(symbol, symbol)
    interval_map = {
        "15m": "15min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1day",
    }
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": td_symbol,
        "interval": interval_map.get(interval, interval),
        "outputsize": outputsize,
        "apikey": TWELVE_API_KEY,
        "format": "JSON",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "values" not in data:
            return None
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()
        return normalize_ohlcv(df)
    except Exception:
        return None

@st.cache_data(ttl=90, show_spinner=False)
def get_historical_data(symbol, period="3mo", interval="4h"):
    df = get_yfinance(symbol, period, interval)
    if df is not None and len(df) >= 50:
        return df
    df = get_twelve_data(symbol, interval, 500)
    if df is not None and len(df) >= 50:
        return df
    return None

@st.cache_data(ttl=30, show_spinner=False)
def get_spot_price(symbol):
    try:
        df = yf.download(
            symbol,
            period="1d",
            interval="5m",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        df = normalize_ohlcv(df)
        if df is not None and not df.empty:
            first = float(df["close"].iloc[0])
            last = float(df["close"].iloc[-1])
            change = ((last - first) / first * 100) if first else 0.0
            return last, change
    except Exception:
        pass
    df = get_twelve_data(symbol, "1h", 5)
    if df is not None and not df.empty:
        return float(df["close"].iloc[-1]), 0.0
    return None, None


# ============================================================
# INDICATORS
# ============================================================

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calc_atr(df, period=14):
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - sig
    return macd, sig, hist

def calc_bollinger(series, period=20, std=2.0):
    mid = series.rolling(period).mean()
    dev = series.rolling(period).std()
    return mid + std * dev, mid, mid - std * dev

def calc_mfi(df, period=14):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    raw = tp * df["volume"].replace(0, np.nan)
    direction = tp.diff()
    pos = raw.where(direction > 0, 0.0).rolling(period).sum()
    neg = raw.where(direction < 0, 0.0).abs().rolling(period).sum()
    ratio = pos / neg.replace(0, np.nan)
    return (100 - (100 / (1 + ratio))).fillna(50)

def calc_chaikin(df, period=21):
    hl = (df["high"] - df["low"]).replace(0, np.nan)
    multiplier = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl
    money_volume = multiplier.fillna(0) * df["volume"]
    return (
        money_volume.rolling(period).sum()
        / df["volume"].rolling(period).sum().replace(0, np.nan)
    ).fillna(0)

def calc_session_vwap(df):
    work = df.copy()
    if work.index.tz is None:
        dates = work.index.normalize()
    else:
        dates = work.index.tz_convert("UTC").normalize()
    tp = (work["high"] + work["low"] + work["close"]) / 3
    pv = tp * work["volume"].clip(lower=0)
    cum_pv = pv.groupby(dates).cumsum()
    cum_vol = work["volume"].clip(lower=0).groupby(dates).cumsum()
    vwap = cum_pv / cum_vol.replace(0, np.nan)
    fallback = tp.groupby(dates).expanding().mean().reset_index(level=0, drop=True)
    return vwap.fillna(fallback)

def calc_ichimoku(df, tenkan=9, kijun=26, senkou=52):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tenkan_line = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    kijun_line = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    senkou_a_plot = ((tenkan_line + kijun_line) / 2).shift(kijun)
    senkou_b_plot = (
        (high.rolling(senkou).max() + low.rolling(senkou).min()) / 2
    ).shift(kijun)
    cloud_a_now = ((tenkan_line + kijun_line) / 2)
    cloud_b_now = (high.rolling(senkou).max() + low.rolling(senkou).min()) / 2
    chikou_plot = close.shift(-kijun)
    return (
        tenkan_line,
        kijun_line,
        senkou_a_plot,
        senkou_b_plot,
        chikou_plot,
        cloud_a_now,
        cloud_b_now,
    )


# ============================================================
# SWING / STRUCTURE ENGINE
# ============================================================

def find_confirmed_swings(df, order=3):
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    swing_high = np.zeros(len(df), dtype=bool)
    swing_low = np.zeros(len(df), dtype=bool)
    for i in range(order, len(df) - order):
        h = highs[i]
        l = lows[i]
        if np.isfinite(h):
            left_h = highs[i - order:i]
            right_h = highs[i + 1:i + order + 1]
            if h > np.nanmax(left_h) and h >= np.nanmax(right_h):
                swing_high[i] = True
        if np.isfinite(l):
            left_l = lows[i - order:i]
            right_l = lows[i + 1:i + order + 1]
            if l < np.nanmin(left_l) and l <= np.nanmin(right_l):
                swing_low[i] = True
    out = df.copy()
    out["swing_high"] = swing_high
    out["swing_low"] = swing_low
    return out

def get_last_two_swings(df, kind="high"):
    col = "swing_high" if kind == "high" else "swing_low"
    points = df.index[df[col]].tolist()
    values = df.loc[points, "high" if kind == "high" else "low"].tolist()
    if len(points) < 2:
        return None
    return [
        (points[-2], float(values[-2])),
        (points[-1], float(values[-1])),
    ]

def structure_state(df):
    highs = get_last_two_swings(df, "high")
    lows = get_last_two_swings(df, "low")
    bullish = False
    bearish = False
    state = "RANGE"
    if highs and lows:
        hh = highs[-1][1] > highs[-2][1]
        hl = lows[-1][1] > lows[-2][1]
        lh = highs[-1][1] < highs[-2][1]
        ll = lows[-1][1] < lows[-2][1]
        if hh and hl:
            bullish = True
            state = "BULLISH"
        elif lh and ll:
            bearish = True
            state = "BEARISH"
    return {
        "state": state,
        "bullish": bullish,
        "bearish": bearish,
        "highs": highs,
        "lows": lows,
    }

def detect_bos_mss(df):
    out = df.copy()
    out["bos_bullish"] = False
    out["bos_bearish"] = False
    out["mss_bullish"] = False
    out["mss_bearish"] = False
    state = "RANGE"
    for i in range(len(out)):
        if i < 10:
            continue
        past = out.iloc[:i]
        past_highs = past.index[past["swing_high"]]
        past_lows = past.index[past["swing_low"]]
        last_high = (
            float(past.loc[past_highs[-1], "high"])
            if len(past_highs)
            else np.nan
        )
        last_low = (
            float(past.loc[past_lows[-1], "low"])
            if len(past_lows)
            else np.nan
        )
        close = float(out["close"].iloc[i])
        bull_break = np.isfinite(last_high) and close > last_high
        bear_break = np.isfinite(last_low) and close < last_low
        if bull_break:
            out.iloc[i, out.columns.get_loc("bos_bullish")] = True
            if state == "BEARISH":
                out.iloc[i, out.columns.get_loc("mss_bullish")] = True
            state = "BULLISH"
        elif bear_break:
            out.iloc[i, out.columns.get_loc("bos_bearish")] = True
            if state == "BULLISH":
                out.iloc[i, out.columns.get_loc("mss_bearish")] = True
            state = "BEARISH"
    return out


# ============================================================
# LIQUIDITY / FVG / ORDER BLOCK
# ============================================================

def detect_liquidity_sweeps(df, tolerance_atr=0.10):
    out = df.copy()
    out["liquidity_sweep_bullish"] = False
    out["liquidity_sweep_bearish"] = False
    for i in range(3, len(out)):
        atr = safe_float(out["atr"].iloc[i], 0)
        tol = atr * tolerance_atr
        prev_high = float(out["high"].iloc[i - 3:i].max())
        prev_low = float(out["low"].iloc[i - 3:i].min())
        h = float(out["high"].iloc[i])
        l = float(out["low"].iloc[i])
        c = float(out["close"].iloc[i])
        if h > prev_high + tol and c < prev_high:
            out.iloc[i, out.columns.get_loc("liquidity_sweep_bearish")] = True
        if l < prev_low - tol and c > prev_low:
            out.iloc[i, out.columns.get_loc("liquidity_sweep_bullish")] = True
    return out

def detect_fvg(df):
    out = df.copy()
    out["fvg_bullish"] = False
    out["fvg_bearish"] = False
    out["fvg_bull_low"] = np.nan
    out["fvg_bull_high"] = np.nan
    out["fvg_bear_low"] = np.nan
    out["fvg_bear_high"] = np.nan
    for i in range(2, len(out)):
        if out["low"].iloc[i] > out["high"].iloc[i - 2]:
            out.iloc[i, out.columns.get_loc("fvg_bullish")] = True
            out.iloc[i, out.columns.get_loc("fvg_bull_low")] = out["high"].iloc[i - 2]
            out.iloc[i, out.columns.get_loc("fvg_bull_high")] = out["low"].iloc[i]
        if out["high"].iloc[i] < out["low"].iloc[i - 2]:
            out.iloc[i, out.columns.get_loc("fvg_bearish")] = True
            out.iloc[i, out.columns.get_loc("fvg_bear_low")] = out["high"].iloc[i]
            out.iloc[i, out.columns.get_loc("fvg_bear_high")] = out["low"].iloc[i - 2]
    return out

def detect_order_blocks(df):
    out = df.copy()
    out["order_block_bullish"] = False
    out["order_block_bearish"] = False
    out["ob_low"] = np.nan
    out["ob_high"] = np.nan
    for i in range(1, len(out)):
        atr = safe_float(out["atr"].iloc[i], np.nan)
        if not np.isfinite(atr) or atr <= 0:
            continue
        body = abs(float(out["close"].iloc[i]) - float(out["open"].iloc[i]))
        displacement = body >= 1.20 * atr
        if not displacement:
            continue
        prev_open = float(out["open"].iloc[i - 1])
        prev_close = float(out["close"].iloc[i - 1])
        prev_high = float(out["high"].iloc[i - 1])
        prev_low = float(out["low"].iloc[i - 1])
        if prev_close < prev_open and out["close"].iloc[i] > out["high"].iloc[i - 1]:
            out.iloc[i, out.columns.get_loc("order_block_bullish")] = True
            out.iloc[i, out.columns.get_loc("ob_low")] = prev_low
            out.iloc[i, out.columns.get_loc("ob_high")] = prev_high
        if prev_close > prev_open and out["close"].iloc[i] < out["low"].iloc[i - 1]:
            out.iloc[i, out.columns.get_loc("order_block_bearish")] = True
            out.iloc[i, out.columns.get_loc("ob_low")] = prev_low
            out.iloc[i, out.columns.get_loc("ob_high")] = prev_high
    return out

def add_premium_discount(df, lookback=50):
    out = df.copy()
    swing_high = out["high"].rolling(lookback).max().shift(1)
    swing_low = out["low"].rolling(lookback).min().shift(1)
    mid = (swing_high + swing_low) / 2
    out["range_high"] = swing_high
    out["range_low"] = swing_low
    out["premium_mid"] = mid
    out["in_discount"] = out["close"] < mid
    out["in_premium"] = out["close"] > mid
    return out

def analyze_smc(df, profile):
    out = df.copy()
    out = find_confirmed_swings(out, profile["swing_order"])
    out = detect_bos_mss(out)
    out = detect_liquidity_sweeps(out)
    out = detect_fvg(out)
    out = detect_order_blocks(out)
    out = add_premium_discount(out, min(profile["structure_lookback"], 100))
    highs = out.index[out["swing_high"]]
    lows = out.index[out["swing_low"]]
    out["bsl"] = np.nan
    out["ssl"] = np.nan
    if len(highs):
        out["bsl"] = float(out.loc[highs[-1], "high"])
    if len(lows):
        out["ssl"] = float(out.loc[lows[-1], "low"])
    return out


# ============================================================
# PATTERN / CANDLE ENGINE
# ============================================================

def candle_confirmation(df, direction):
    if len(df) < 3:
        return False
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    rng = max(last["high"] - last["low"], 1e-12)
    if direction == "BUY":
        bullish_body = last["close"] > last["open"]
        close_position = (last["close"] - last["low"]) / rng
        return bool(bullish_body and close_position >= 0.60 and body / rng >= 0.35)
    bearish_body = last["close"] < last["open"]
    close_position = (last["high"] - last["close"]) / rng
    return bool(bearish_body and close_position >= 0.60 and body / rng >= 0.35)

def detect_divergence(df):
    if len(df) < 30:
        return None
    work = find_confirmed_swings(df, 3)
    lows = work.index[work["swing_low"]].tolist()
    highs = work.index[work["swing_high"]].tolist()
    if len(lows) >= 2:
        p1, p2 = lows[-2], lows[-1]
        price_ll = work.loc[p2, "low"] < work.loc[p1, "low"]
        rsi_hl = work.loc[p2, "rsi"] > work.loc[p1, "rsi"]
        if price_ll and rsi_hl:
            return "BULLISH"
    if len(highs) >= 2:
        p1, p2 = highs[-2], highs[-1]
        price_hh = work.loc[p2, "high"] > work.loc[p1, "high"]
        rsi_lh = work.loc[p2, "rsi"] < work.loc[p1, "rsi"]
        if price_hh and rsi_lh:
            return "BEARISH"
    return None

def pattern_context(df):
    result = []
    if len(df) < 30:
        return result
    last = df.iloc[-1]
    work = find_confirmed_swings(df, 3)
    highs = work.index[work["swing_high"]].tolist()
    lows = work.index[work["swing_low"]].tolist()
    if len(highs) >= 2:
        h1, h2 = highs[-2], highs[-1]
        a, b = float(work.loc[h1, "high"]), float(work.loc[h2, "high"])
        if abs(a - b) / max(abs(a), 1e-12) <= 0.015:
            result.append(("DOUBLE_TOP", "BEARISH"))
    if len(lows) >= 2:
        l1, l2 = lows[-2], lows[-1]
        a, b = float(work.loc[l1, "low"]), float(work.loc[l2, "low"])
        if abs(a - b) / max(abs(a), 1e-12) <= 0.015:
            result.append(("DOUBLE_BOTTOM", "BULLISH"))
    if last["ema20"] > last["ema50"] > last["ema200"]:
        result.append(("EMA_STACK_BULLISH", "BULLISH"))
    elif last["ema20"] < last["ema50"] < last["ema200"]:
        result.append(("EMA_STACK_BEARISH", "BEARISH"))
    return result


# ============================================================
# FEATURE BUILD
# ============================================================

def build_features(df, profile):
    out = df.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["rsi"] = calc_rsi(out["close"], profile["rsi_period"])
    out["atr"] = calc_atr(out, profile["atr_period"])
    out["macd"], out["macd_signal"], out["macd_histogram"] = calc_macd(
        out["close"], 12, 26, 9
    )
    out["bb_upper"], out["bb_mid"], out["bb_lower"] = calc_bollinger(
        out["close"], profile["bb_period"], profile["bb_std"]
    )
    out["mfi"] = calc_mfi(out, profile["mfi_period"])
    out["chaikin_mf"] = calc_chaikin(out, 21)
    out["vwap"] = calc_session_vwap(out)
    (
        out["tenkan"],
        out["kijun"],
        out["senkou_a"],
        out["senkou_b"],
        out["chikou"],
        out["cloud_a_now"],
        out["cloud_b_now"],
    ) = calc_ichimoku(out)
    out = analyze_smc(out, profile)
    return out


# ============================================================
# MULTI-TIMEFRAME ENGINE
# ============================================================

def timeframe_bias(df):
    if df is None or len(df) < 60:
        return "NEUTRAL", 0
    profile = ASSET_PROFILES["forex"]
    x = build_features(df, profile)
    last = x.iloc[-1]
    bull = 0
    bear = 0
    if last["ema20"] > last["ema50"]:
        bull += 1
    elif last["ema20"] < last["ema50"]:
        bear += 1
    if last["ema50"] > last["ema200"]:
        bull += 1
    elif last["ema50"] < last["ema200"]:
        bear += 1
    if last["macd"] > last["macd_signal"]:
        bull += 1
    elif last["macd"] < last["macd_signal"]:
        bear += 1
    structure = structure_state(x)
    if structure["bullish"]:
        bull += 2
    elif structure["bearish"]:
        bear += 2
    if bull > bear:
        return "BULLISH", bull
    if bear > bull:
        return "BEARISH", bear
    return "NEUTRAL", 0

@st.cache_data(ttl=120, show_spinner=False)
def get_mtf_analysis(symbol):
    frames = {
        "1D": ("1y", "1d", 4),
        "4H": ("6mo", "4h", 3),
        "1H": ("3mo", "1h", 2),
        "15M": ("30d", "15m", 1),
    }
    results = {}
    weighted_bull = 0
    weighted_bear = 0
    total_weight = 0
    for name, (period, interval, weight) in frames.items():
        df = get_historical_data(symbol, period, interval)
        bias, strength = timeframe_bias(df)
        results[name] = {"bias": bias, "strength": strength, "weight": weight}
        if bias == "BULLISH":
            weighted_bull += weight * max(1, strength)
        elif bias == "BEARISH":
            weighted_bear += weight * max(1, strength)
        total_weight += weight * 3
    if weighted_bull > weighted_bear * 1.15:
        final = "BULLISH"
    elif weighted_bear > weighted_bull * 1.15:
        final = "BEARISH"
    else:
        final = "NEUTRAL"
    balance = abs(weighted_bull - weighted_bear) / max(total_weight, 1)
    confidence = clamp(50 + balance * 50, 50, 95)
    return final, confidence, results


# ============================================================
# CONTEXT ENGINE: DXY / USD / GOLD
# ============================================================

def get_dxy_context():
    df = get_historical_data("DX-Y.NYB", "6mo", "4h")
    if df is None:
        return "NEUTRAL", 50.0, {}
    profile = ASSET_PROFILES["forex"]
    x = build_features(df, profile)
    last = x.iloc[-1]
    bull = 0
    bear = 0
    if last["close"] > last["ema50"]:
        bull += 1
    elif last["close"] < last["ema50"]:
        bear += 1
    if last["macd"] > last["macd_signal"]:
        bull += 1
    elif last["macd"] < last["macd_signal"]:
        bear += 1
    if last["rsi"] > 55:
        bull += 1
    elif last["rsi"] < 45:
        bear += 1
    if bull > bear:
        return "BULLISH", 55 + 10 * bull, {"trend": "USD strength"}
    if bear > bull:
        return "BEARISH", 55 + 10 * bear, {"trend": "USD weakness"}
    return "NEUTRAL", 50, {"trend": "USD neutral"}

def get_pair_usd_context(pair_name):
    if "/" not in pair_name:
        return 0.0, "لا يوجد تأثير مباشر للدولار."
    base, quote = [x.strip() for x in pair_name.split("/")[:2]]
    if "USD" not in (base, quote):
        return 0.0, "تأثير DXY غير مباشر."
    dxy_bias, _, _ = get_dxy_context()
    if base == "USD":
        if dxy_bias == "BULLISH":
            return 1.0, "قوة الدولار تدعم الزوج من جهة العملة الأساسية."
        if dxy_bias == "BEARISH":
            return -1.0, "ضعف الدولار يضغط على الزوج."
    else:
        if dxy_bias == "BULLISH":
            return -1.0, "قوة الدولار تضغط على الزوج."
        if dxy_bias == "BEARISH":
            return 1.0, "ضعف الدولار يدعم الزوج."
    return 0.0, "تأثير الدولار محايد."

def get_gold_dxy_correlation():
    dxy = get_historical_data("DX-Y.NYB", "3mo", "4h")
    gold = get_historical_data("GC=F", "3mo", "4h")
    if dxy is None or gold is None:
        return None
    d = dxy["close"].pct_change()
    g = gold["close"].pct_change()
    aligned = pd.concat([d, g], axis=1, join="inner").dropna()
    if len(aligned) < 30:
        return None
    return float(aligned.iloc[:, 0].rolling(30).corr(aligned.iloc[:, 1]).iloc[-1])


# ============================================================
# MARKET REGIME
# ============================================================

def detect_regime(df):
    last = df.iloc[-1]
    atr = safe_float(last["atr"], np.nan)
    if not np.isfinite(atr) or atr <= 0:
        return "UNKNOWN", 50.0
    trend_strength = abs(last["ema20"] - last["ema50"]) / atr
    band_width = (last["bb_upper"] - last["bb_lower"]) / max(last["close"], 1e-12)
    if trend_strength >= 1.0:
        return ("TREND_BULLISH" if last["ema20"] > last["ema50"] else "TREND_BEARISH"), 75
    if band_width < 0.015:
        return "COMPRESSION", 65
    return "RANGE", 55


# ============================================================
# 5-PILLAR HIERARCHICAL SCORING
# ============================================================

PILLAR_WEIGHTS = {
    "structure": 0.30,
    "trend": 0.20,
    "momentum": 0.15,
    "volume": 0.15,
    "context": 0.20,
}

def directional_score(df, pair_name, symbol):
    last = df.iloc[-1]
    scores = {
        "BUY": {k: 0.0 for k in PILLAR_WEIGHTS},
        "SELL": {k: 0.0 for k in PILLAR_WEIGHTS},
    }
    reasons = []

    # ---------------- STRUCTURE 30% ----------------
    structure = structure_state(df)
    if structure["bullish"]:
        scores["BUY"]["structure"] += 45
        reasons.append("الهيكل العام صاعد")
    elif structure["bearish"]:
        scores["SELL"]["structure"] += 45
        reasons.append("الهيكل العام هابط")
    if bool(last["bos_bullish"]):
        scores["BUY"]["structure"] += 35
        reasons.append("BOS صاعد مؤكد")
    if bool(last["bos_bearish"]):
        scores["SELL"]["structure"] += 35
        reasons.append("BOS هابط مؤكد")
    if bool(last["mss_bullish"]):
        scores["BUY"]["structure"] += 20
        reasons.append("MSS صاعد")
    if bool(last["mss_bearish"]):
        scores["SELL"]["structure"] += 20
        reasons.append("MSS هابط")
    if bool(last["liquidity_sweep_bullish"]):
        scores["BUY"]["structure"] += 25
        reasons.append("Bullish Liquidity Sweep")
    if bool(last["liquidity_sweep_bearish"]):
        scores["SELL"]["structure"] += 25
        reasons.append("Bearish Liquidity Sweep")
    if bool(last["order_block_bullish"]):
        scores["BUY"]["structure"] += 15
        reasons.append("Bullish Order Block")
    if bool(last["order_block_bearish"]):
        scores["SELL"]["structure"] += 15
        reasons.append("Bearish Order Block")
    if bool(last["fvg_bullish"]):
        scores["BUY"]["structure"] += 10
    if bool(last["fvg_bearish"]):
        scores["SELL"]["structure"] += 10
    if bool(last["in_discount"]):
        scores["BUY"]["structure"] += 10
    if bool(last["in_premium"]):
        scores["SELL"]["structure"] += 10

    # ---------------- TREND 20% ----------------
    if last["ema20"] > last["ema50"] > last["ema200"]:
        scores["BUY"]["trend"] += 80
    elif last["ema20"] < last["ema50"] < last["ema200"]:
        scores["SELL"]["trend"] += 80
    else:
        if last["ema20"] > last["ema50"]:
            scores["BUY"]["trend"] += 45
        elif last["ema20"] < last["ema50"]:
            scores["SELL"]["trend"] += 45
    cloud_top = max(safe_float(last["cloud_a_now"], np.nan), safe_float(last["cloud_b_now"], np.nan))
    cloud_bottom = min(safe_float(last["cloud_a_now"], np.nan), safe_float(last["cloud_b_now"], np.nan))
    if np.isfinite(cloud_top) and np.isfinite(cloud_bottom):
        if last["close"] > cloud_top:
            scores["BUY"]["trend"] += 20
        elif last["close"] < cloud_bottom:
            scores["SELL"]["trend"] += 20

    # ---------------- MOMENTUM 15% ----------------
    rsi = safe_float(last["rsi"], 50)
    if rsi >= 55:
        scores["BUY"]["momentum"] += 45
    elif rsi <= 45:
        scores["SELL"]["momentum"] += 45
    if last["macd"] > last["macd_signal"] and last["macd_histogram"] > 0:
        scores["BUY"]["momentum"] += 45
    elif last["macd"] < last["macd_signal"] and last["macd_histogram"] < 0:
        scores["SELL"]["momentum"] += 45
    if last["mfi"] >= 55:
        scores["BUY"]["momentum"] += 10
    elif last["mfi"] <= 45:
        scores["SELL"]["momentum"] += 10

    # ---------------- VOLUME / FLOW 15% ----------------
    if last["close"] > last["vwap"]:
        scores["BUY"]["volume"] += 45
    elif last["close"] < last["vwap"]:
        scores["SELL"]["volume"] += 45
    if last["chaikin_mf"] > 0:
        scores["BUY"]["volume"] += 35
    elif last["chaikin_mf"] < 0:
        scores["SELL"]["volume"] += 35
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]
    if vol_avg and np.isfinite(vol_avg) and last["volume"] > vol_avg:
        if last["close"] > last["open"]:
            scores["BUY"]["volume"] += 20
        elif last["close"] < last["open"]:
            scores["SELL"]["volume"] += 20

    # ---------------- CONTEXT 20% ----------------
    dxy_bias, dxy_conf, _ = get_dxy_context()
    usd_impact, usd_msg = get_pair_usd_context(pair_name)
    if usd_impact > 0:
        scores["BUY"]["context"] += 45
    elif usd_impact < 0:
        scores["SELL"]["context"] += 45
    if "Gold" in pair_name:
        corr = get_gold_dxy_correlation()
        if corr is not None:
            if corr <= -0.50 and dxy_bias == "BEARISH":
                scores["BUY"]["context"] += 35
            elif corr <= -0.50 and dxy_bias == "BULLISH":
                scores["SELL"]["context"] += 35
    regime, regime_conf = detect_regime(df)
    if regime == "TREND_BULLISH":
        scores["BUY"]["context"] += 20
    elif regime == "TREND_BEARISH":
        scores["SELL"]["context"] += 20

    total_buy = 0.0
    total_sell = 0.0
    for pillar, weight in PILLAR_WEIGHTS.items():
        scores["BUY"][pillar] = clamp(scores["BUY"][pillar], 0, 100)
        scores["SELL"][pillar] = clamp(scores["SELL"][pillar], 0, 100)
        total_buy += scores["BUY"][pillar] * weight
        total_sell += scores["SELL"][pillar] * weight

    divergence = detect_divergence(df)
    if divergence == "BULLISH":
        total_buy += 3
    elif divergence == "BEARISH":
        total_sell += 3

    return {
        "buy": clamp(total_buy, 0, 100),
        "sell": clamp(total_sell, 0, 100),
        "pillars": scores,
        "reasons": reasons,
        "dxy_bias": dxy_bias,
        "dxy_conf": dxy_conf,
        "usd_msg": usd_msg,
        "regime": regime,
        "regime_conf": regime_conf,
        "divergence": divergence,
    }


# ============================================================
# RISK ENGINE
# ============================================================

def latest_structure_levels(df):
    lows = df.index[df["swing_low"]].tolist()
    highs = df.index[df["swing_high"]].tolist()
    swing_low = float(df.loc[lows[-1], "low"]) if lows else np.nan
    swing_high = float(df.loc[highs[-1], "high"]) if highs else np.nan
    return swing_low, swing_high

def calculate_trade_levels(df, signal, current_price, profile):
    atr = safe_float(df["atr"].iloc[-1], np.nan)
    if not np.isfinite(atr) or atr <= 0:
        return None
    swing_low, swing_high = latest_structure_levels(df)
    recent_low = float(df["low"].iloc[-8:].min())
    recent_high = float(df["high"].iloc[-8:].max())
    ssl = safe_float(df["ssl"].iloc[-1], np.nan)
    bsl = safe_float(df["bsl"].iloc[-1], np.nan)

    if signal == "BUY":
        candidates = [
            x for x in [swing_low, recent_low, ssl]
            if np.isfinite(x) and x < current_price
        ]
        structural_stop = max(candidates) if candidates else current_price - profile["atr_sl"] * atr
        stop_loss = structural_stop - 0.20 * atr
        risk = current_price - stop_loss
        if risk <= 0:
            return None
        targets = [recent_high, bsl]
        targets = sorted(
            [x for x in targets if np.isfinite(x) and x > current_price]
        )
        t1 = targets[0] if targets else current_price + risk * 1.0
        t2 = current_price + risk * 1.5
        t3 = current_price + risk * 2.0
        if t1 <= current_price:
            t1 = current_price + risk
        if t2 <= t1:
            t2 = current_price + risk * 1.5
        if t3 <= t2:
            t3 = current_price + risk * 2.0
    else:
        candidates = [
            x for x in [swing_high, recent_high, bsl]
            if np.isfinite(x) and x > current_price
        ]
        structural_stop = min(candidates) if candidates else current_price + profile["atr_sl"] * atr
        stop_loss = structural_stop + 0.20 * atr
        risk = stop_loss - current_price
        if risk <= 0:
            return None
        targets = [recent_low, ssl]
        targets = sorted(
            [x for x in targets if np.isfinite(x) and x < current_price],
            reverse=True,
        )
        t1 = targets[0] if targets else current_price - risk * 1.0
        t2 = current_price - risk * 1.5
        t3 = current_price - risk * 2.0
        if t1 >= current_price:
            t1 = current_price - risk
        if t2 >= t1:
            t2 = current_price - risk * 1.5
        if t3 >= t2:
            t3 = current_price - risk * 2.0

    rr1 = abs(t1 - current_price) / risk
    rr2 = abs(t2 - current_price) / risk
    rr3 = abs(t3 - current_price) / risk

    return {
        "entry": float(current_price),
        "stop_loss": float(stop_loss),
        "target1": float(t1),
        "target2": float(t2),
        "target3": float(t3),
        "risk": float(risk),
        "risk_reward_1": float(rr1),
        "risk_reward_2": float(rr2),
        "risk_reward_3": float(rr3),
    }

def validate_levels(signal, levels, profile):
    if not levels:
        return False, "تعذر بناء مستويات الصفقة."
    if signal == "BUY":
        if not levels["stop_loss"] < levels["entry"] < levels["target1"]:
            return False, "ترتيب BUY غير صالح."
    else:
        if not levels["target1"] < levels["entry"] < levels["stop_loss"]:
            return False, "ترتيب SELL غير صالح."
    if levels["risk_reward_1"] < MIN_RR_TP1:
        return False, "TP1 لا يحقق الحد الأدنى من RR."
    if levels["risk_reward_2"] < profile["min_rr"]:
        return False, "TP2 لا يحقق الحد الأدنى من RR."
    if levels["risk_reward_3"] < MIN_RR_TP3:
        return False, "TP3 لا يحقق الحد الأدنى من RR."
    return True, ""

def calculate_position_size(pair_name, entry, stop, balance, risk_percent):
    risk_money = balance * (risk_percent / 100.0)
    distance = abs(entry - stop)
    if distance <= 0 or risk_money <= 0:
        return 0.0
    asset = asset_type_from_name(pair_name)
    if asset == "forex":
        pip_size = 0.01 if "JPY" in pair_name else 0.0001
        contract_size = 100000.0
        quote_is_usd = pair_name.endswith("/USD")
        if quote_is_usd:
            loss_per_lot = distance / pip_size * (pip_size * contract_size)
        else:
            loss_per_lot = distance * contract_size
    elif asset == "gold":
        contract_size = 100.0
        loss_per_lot = distance * contract_size
    else:
        contract_size = 1.0
        loss_per_lot = distance * contract_size
    if loss_per_lot <= 0:
        return 0.0
    lots = risk_money / loss_per_lot
    if asset == "forex":
        return round(clamp(lots, 0.01, 100.0), 2)
    if asset == "gold":
        return round(clamp(lots, 0.01, 100.0), 2)
    return round(clamp(lots, 0.0001, 100.0), 4)


# ============================================================
# FINAL SIGNAL ENGINE
# ============================================================

def generate_signal(df, current_price, pair_name, symbol):
    profile = profile_for(pair_name)
    df = build_features(df, profile)
    scores = directional_score(df, pair_name, symbol)
    mtf_bias, mtf_conf, mtf_details = get_mtf_analysis(symbol)

    buy = scores["buy"]
    sell = scores["sell"]

    if mtf_bias == "BULLISH":
        buy += 8
        sell -= 4
    elif mtf_bias == "BEARISH":
        sell += 8
        buy -= 4
    else:
        buy -= 2
        sell -= 2

    buy = clamp(buy, 0, 100)
    sell = clamp(sell, 0, 100)

    gap = abs(buy - sell)
    max_score = max(buy, sell)

    if gap < 10:
        signal = "WAIT"
    elif buy > sell:
        signal = "BUY"
    else:
        signal = "SELL"

    last = df.iloc[-1]
    if bool(last["mss_bullish"]) and sell > buy:
        signal = "WAIT"
    if bool(last["mss_bearish"]) and buy > sell:
        signal = "WAIT"

    rsi = safe_float(last["rsi"], 50)
    if signal == "BUY" and rsi > 75 and not bool(last["mss_bullish"]):
        buy -= 5
    if signal == "SELL" and rsi < 25 and not bool(last["mss_bearish"]):
        sell -= 5

    buy = clamp(buy, 0, 100)
    sell = clamp(sell, 0, 100)

    confidence = clamp(
        50 + max(0, abs(buy - sell)) * 0.75 + max(0, max_score - 60) * 0.25,
        50,
        95,
    )

    levels = None
    risk_ok = False
    risk_msg = ""

    if signal in ("BUY", "SELL"):
        levels = calculate_trade_levels(df, signal, current_price, profile)
        risk_ok, risk_msg = validate_levels(signal, levels, profile)
        if not risk_ok:
            signal = "WAIT"
            confidence = min(confidence, 68)

    if signal == "BUY" and mtf_bias == "BEARISH":
        confidence *= 0.82
        signal = "WAIT" if confidence < profile["confidence_threshold"] else signal

    if signal == "SELL" and mtf_bias == "BULLISH":
        confidence *= 0.82
        signal = "WAIT" if confidence < profile["confidence_threshold"] else signal

    if signal in ("BUY", "SELL") and confidence < profile["confidence_threshold"]:
        signal = "WAIT"

    pillar_data = scores["pillars"]
    if signal == "BUY":
        confluence = sum(
            1 for p in PILLAR_WEIGHTS if pillar_data["BUY"][p] >= 50
        )
    elif signal == "SELL":
        confluence = sum(
            1 for p in PILLAR_WEIGHTS if pillar_data["SELL"][p] >= 50
        )
    else:
        confluence = 0

    details = {
        "BUY Score": round(buy, 1),
        "SELL Score": round(sell, 1),
        "MTF": mtf_bias,
        "MTF Confidence": round(mtf_conf, 1),
        "Regime": scores["regime"],
        "DXY": scores["dxy_bias"],
        "Divergence": scores["divergence"] or "None",
        "Risk Gate": "PASS" if risk_ok else risk_msg,
    }

    return {
        "signal": signal,
        "confidence": confidence,
        "buy_score": buy,
        "sell_score": sell,
        "net_score": buy - sell,
        "confluence": confluence,
        "details": details,
        "reasons": scores["reasons"],
        "pillars": pillar_data,
        "mtf_bias": mtf_bias,
        "mtf_conf": mtf_conf,
        "mtf_details": mtf_details,
        "levels": levels,
        "df": df,
    }


# ============================================================
# TRADE STORAGE / MANAGEMENT
# ============================================================

class TradeManager:
    def __init__(self, path=TRADES_FILE):
        self.path = Path(path)
        self.data = self.load()

    def load(self):
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.setdefault("open_trades", [])
                    data.setdefault("closed_trades", [])
                    return data
        except Exception:
            pass
        return {"open_trades": [], "closed_trades": []}

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        tmp.replace(self.path)

    @property
    def open_trades(self):
        return self.data["open_trades"]

    @property
    def closed_trades(self):
        return self.data["closed_trades"]

    def add_trade(self, trade):
        tid = f"T{len(self.open_trades) + len(self.closed_trades) + 1:04d}"
        item = dict(trade)
        item.update({
            "id": tid,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "open",
            "stage": 0,
            "highest_price": trade["entry"],
            "lowest_price": trade["entry"],
            "partial_close_done": False,
        })
        self.open_trades.append(item)
        self.save()
        return tid

    def close_trade(self, tid, current_price, reason="manual"):
        for trade in list(self.open_trades):
            if trade["id"] != tid:
                continue
            entry = float(trade["entry"])
            lots = float(trade["lots"])
            direction = trade["direction"]
            if direction == "BUY":
                pnl = (current_price - entry) * lots
            else:
                pnl = (entry - current_price) * lots
            trade["status"] = "closed"
            trade["close_price"] = current_price
            trade["close_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            trade["close_reason"] = reason
            trade["pnl"] = pnl
            self.closed_trades.append(trade)
            self.open_trades.remove(trade)
            self.save()
            return pnl
        return None

    def monitor_trade(self, tid, current_price, atr=None):
        for trade in self.open_trades:
            if trade["id"] != tid:
                continue
            direction = trade["direction"]
            entry = float(trade["entry"])
            sl = float(trade["stop_loss"])

            if direction == "BUY":
                if current_price <= sl:
                    return self.close_trade(tid, sl, "stop_loss")
                if trade.get("target1") and current_price >= float(trade["target1"]) and not trade.get("partial_close_done"):
                    trade["partial_close_done"] = True
                    trade["stage"] = 1
                    trade["stop_loss"] = max(float(trade["stop_loss"]), entry)
                if trade.get("target2") and current_price >= float(trade["target2"]):
                    trade["stage"] = 2
                if trade.get("target3") and current_price >= float(trade["target3"]):
                    return self.close_trade(tid, float(trade["target3"]), "target3")
            else:
                if current_price >= sl:
                    return self.close_trade(tid, sl, "stop_loss")
                if trade.get("target1") and current_price <= float(trade["target1"]) and not trade.get("partial_close_done"):
                    trade["partial_close_done"] = True
                    trade["stage"] = 1
                    trade["stop_loss"] = min(float(trade["stop_loss"]), entry)
                if trade.get("target2") and current_price <= float(trade["target2"]):
                    trade["stage"] = 2
                if trade.get("target3") and current_price <= float(trade["target3"]):
                    return self.close_trade(tid, float(trade["target3"]), "target3")

            if trade.get("stage", 0) >= 1 and atr and np.isfinite(atr):
                trail = float(atr) * 1.0
                if direction == "BUY":
                    trade["highest_price"] = max(
                        float(trade.get("highest_price", entry)),
                        current_price,
                    )
                    new_sl = trade["highest_price"] - trail
                    if new_sl > float(trade["stop_loss"]):
                        trade["stop_loss"] = new_sl
                else:
                    trade["lowest_price"] = min(
                        float(trade.get("lowest_price", entry)),
                        current_price,
                    )
                    new_sl = trade["lowest_price"] + trail
                    if new_sl < float(trade["stop_loss"]):
                        trade["stop_loss"] = new_sl
            self.save()
            return None
        return None


# ============================================================
# ALL SIGNALS
# ============================================================

def get_all_signals():
    results = []
    for pair_name, symbol in PAIRS.items():
        try:
            price, change = get_spot_price(symbol)
            df = get_historical_data(symbol, "3mo", "4h")
            if price is None or df is None:
                continue
            result = generate_signal(df, price, pair_name, symbol)
            levels = result["levels"] or {}
            results.append({
                "الزوج": pair_name,
                "الإشارة": result["signal"],
                "الثقة": round(result["confidence"], 1),
                "BUY": round(result["buy_score"], 1),
                "SELL": round(result["sell_score"], 1),
                "MTF": result["mtf_bias"],
                "التوافق": result["confluence"],
                "السعر": fmt_price(price, pair_name),
                "SL": fmt_price(levels.get("stop_loss"), pair_name),
                "TP1": fmt_price(levels.get("target1"), pair_name),
                "TP2": fmt_price(levels.get("target2"), pair_name),
                "RR3": round(levels.get("risk_reward_3", 0), 2) if levels else 0,
            })
        except Exception:
            continue
    if not results:
        return pd.DataFrame()
    out = pd.DataFrame(results)
    signal_order = {"BUY": 0, "SELL": 1, "WAIT": 2}
    out["_order"] = out["الإشارة"].map(signal_order).fillna(3)
    out = out.sort_values(["_order", "الثقة"], ascending=[True, False]).drop(columns="_order")
    return out


# ============================================================
# OPTIONAL NEWS / CALENDAR
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def get_fmp_economic_calendar():
    if not FMP_API_KEY:
        return []
    url = "https://financialmodelingprep.com/api/v3/economic_calendar"
    params = {"from": datetime.now().strftime("%Y-%m-%d"),
              "to": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
              "apikey": FMP_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []

def event_risk_message(events, pair_name):
    if not events:
        return "لا توجد بيانات تقويم متاحة."
    relevant = []
    for e in events:
        country = str(e.get("country", "")).upper()
        impact = str(e.get("impact", "")).lower()
        if impact not in ("high", "3", "عالٍ", "high impact"):
            continue
        if "USD" in pair_name and country in ("USD", "US"):
            relevant.append(e)
    if relevant:
        return "⚠️ يوجد خبر عالي التأثير مرتبط بالدولار؛ تعامل معه كخطر تقلب وليس كإشارة BUY/SELL."
    return "لا يوجد حاليًا قفل خبر عالي التأثير مطابق بشكل واضح."


# ============================================================
# TELEGRAM
# ============================================================

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=8,
        )
        return r.status_code == 200
    except Exception:
        return False


# ============================================================
# UI
# ============================================================

st.set_page_config(
    page_title=f"BLACK PYRAMID {APP_VERSION}",
    page_icon="▲",
    layout="wide",
)

# ===== تصميم جديد أنيق وراقي =====
st.markdown("""
<style>
/* تنسيق عام */
body {
    direction: rtl;
    background: #0c0e14;
    font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif;
}

/* تنسيق البطاقات والعناصر */
.main-header {
    background: linear-gradient(145deg, #141824, #1b202b);
    padding: 28px 30px;
    border-radius: 24px;
    margin-bottom: 22px;
    border: 1px solid rgba(255, 215, 0, 0.15);
    box-shadow: 0 12px 30px rgba(0,0,0,0.6);
    backdrop-filter: blur(4px);
}
.main-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #e6c87c;
    letter-spacing: 1px;
    text-shadow: 0 2px 8px rgba(230,200,124,0.2);
}
.main-subtitle {
    color: #a8b2c8;
    margin-top: 6px;
    font-weight: 300;
    letter-spacing: 0.5px;
}

.signal-box {
    background: #12161f;
    padding: 28px 20px;
    border-radius: 24px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 10px 28px rgba(0,0,0,0.5);
    transition: all 0.2s ease;
}
.signal-text {
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: 1px;
}

.card {
    background: #131821;
    padding: 18px 20px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.04);
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    margin-bottom: 14px;
    backdrop-filter: blur(2px);
}
.good { color: #7cd4a0; }
.bad { color: #f57a7a; }
.warn { color: #f5c87a; }

/* أزرار أنيقة */
div.stButton > button {
    background: linear-gradient(145deg, #222b3a, #1a212e);
    color: #e8edf5;
    border: 1px solid rgba(255,215,0,0.15);
    border-radius: 40px;
    padding: 0.6rem 1.8rem;
    font-weight: 500;
    font-size: 0.95rem;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
    box-shadow: 0 6px 16px rgba(0,0,0,0.3);
    backdrop-filter: blur(2px);
    width: 100%;
}
div.stButton > button:hover {
    background: linear-gradient(145deg, #2f3b50, #1e283a);
    border-color: rgba(230,200,124,0.4);
    box-shadow: 0 10px 24px rgba(0,0,0,0.5);
    transform: scale(1.01);
    color: #ffffff;
}
div.stButton > button:active {
    transform: scale(0.97);
}

/* تنسيق الصناديق المخصصة */
div[data-testid="stMetric"] {
    background: #11161f;
    padding: 14px 16px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.04);
    box-shadow: 0 4px 14px rgba(0,0,0,0.25);
}
div[data-testid="stMetric"] label {
    color: #bcc3d4;
    font-weight: 400;
}
div[data-testid="stMetric"] .stMetricValue {
    color: #e8edf5;
    font-weight: 600;
}

/* تنسيق الجداول */
div[data-testid="stDataFrame"] {
    background: #11161f;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.04);
    padding: 4px;
}
div[data-testid="stDataFrame"] table {
    border-collapse: separate;
    border-spacing: 0 2px;
}
div[data-testid="stDataFrame"] th {
    background: #1b232f !important;
    color: #d4dcec !important;
    font-weight: 600;
}
div[data-testid="stDataFrame"] td {
    background: #0f141d !important;
    color: #ced6e6 !important;
}

/* تنسيق شريط الاختيار */
div[data-baseweb="select"] > div {
    background: #131821;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 40px;
    padding: 0 16px;
}
div[data-baseweb="select"] input {
    color: #e8edf5 !important;
}

/* تلميحات وإشعارات */
div[data-testid="stInfo"] {
    background: #141c28;
    border-left: 4px solid #e6c87c;
    border-radius: 14px;
    padding: 14px 20px;
    color: #d0dae8;
}
div[data-testid="stWarning"] {
    background: #1e1a1a;
    border-left: 4px solid #f5c87a;
    border-radius: 14px;
    padding: 14px 20px;
    color: #f0dbb0;
}
div[data-testid="stSuccess"] {
    background: #13211b;
    border-left: 4px solid #7cd4a0;
    border-radius: 14px;
    padding: 14px 20px;
    color: #b0e0c0;
}
div[data-testid="stError"] {
    background: #1f1717;
    border-left: 4px solid #f57a7a;
    border-radius: 14px;
    padding: 14px 20px;
    color: #f0b8b8;
}

/* فواصل أنيقة */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(230,200,124,0.2), transparent);
    margin: 28px 0;
}

/* تذييل */
.footer-style {
    text-align: center;
    color: #6b7488;
    padding: 28px 0 12px;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 30px;
    font-size: 0.9rem;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="main-header">
    <div class="main-title">▲ BLACK PYRAMID {APP_VERSION} ▲</div>
    <div class="main-subtitle">
        Hierarchical Intelligence • Structure • MTF • SMC/ICT • Risk Engine • Directional Confluence
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ الإعدادات")
    selected_pair = st.selectbox(
        "اختر الأصل",
        list(PAIRS.keys()),
        index=list(PAIRS.keys()).index(st.session_state.selected_pair)
        if st.session_state.selected_pair in PAIRS else 0,
    )
    st.session_state.selected_pair = selected_pair
    symbol = PAIRS[selected_pair]

    st.markdown("---")

    balance = st.number_input(
        "رصيد الحساب",
        min_value=100.0,
        value=DEFAULT_BALANCE,
        step=100.0,
    )

    risk_percent = st.number_input(
        "المخاطرة لكل صفقة %",
        min_value=0.1,
        max_value=5.0,
        value=DEFAULT_RISK_PERCENT,
        step=0.1,
    )

    if st.button("🔄 مسح الكاش وإعادة التحليل", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.metric("صفقات اليوم", f"{st.session_state.daily_trade_count}/{MAX_DAILY_TRADES}")

    if st.button("📋 تحليل جميع الأصول", use_container_width=True):
        with st.spinner("تحليل الأصول..."):
            st.session_state.all_signals = get_all_signals()

    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        st.dataframe(
            st.session_state.all_signals[
                ["الزوج", "الإشارة", "الثقة", "MTF", "التوافق", "السعر"]
            ],
            hide_index=True,
            use_container_width=True,
            height=360,
        )

    st.markdown("---")

    if st.button("📅 تحديث التقويم الاقتصادي", use_container_width=True):
        st.session_state.economic_events = get_fmp_economic_calendar()

    if st.session_state.economic_events:
        st.caption(event_risk_message(st.session_state.economic_events, selected_pair))


# ============================================================
# MAIN DATA
# ============================================================

current_price, change = get_spot_price(symbol)

if current_price is None:
    st.error("تعذر الحصول على السعر الحالي.")
    st.stop()

df_raw = get_historical_data(symbol, "3mo", "4h")

if df_raw is None:
    st.error("تعذر تحميل البيانات التاريخية.")
    st.stop()

result = generate_signal(
    df_raw,
    current_price,
    selected_pair,
    symbol,
)

df = result["df"]
levels = result["levels"]

signal = result["signal"]
confidence = result["confidence"]


# ============================================================
# PRICE
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("الأصل", selected_pair)
c2.metric("السعر", fmt_price(current_price, selected_pair))
c3.metric("التغير", f"{change:+.2f}%")
c4.metric("النظام", APP_VERSION)


# ============================================================
# FINAL SIGNAL
# ============================================================

signal_color = "#7cd4a0" if signal == "BUY" else "#f57a7a" if signal == "SELL" else "#f5c87a"

st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color:{signal_color};">{signal}</div>
    <div style="font-size:1.2rem; color:#c8d2e2;">Confidence Score: {confidence:.1f}%</div>
    <div style="color:#b0bac8;">BUY: {result['buy_score']:.1f} | SELL: {result['sell_score']:.1f}</div>
    <div style="color:#a0aab8;">Directional Confluence: {result['confluence']}/5</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# 5 PILLARS
# ============================================================

st.markdown("### 🧠 المحاور الخمسة")

pillar_names = {
    "structure": "Structure",
    "trend": "Trend",
    "momentum": "Momentum",
    "volume": "Volume & Flow",
    "context": "Context",
}

cols = st.columns(5)

for idx, pillar in enumerate(PILLAR_WEIGHTS):
    buy_score = result["pillars"]["BUY"][pillar]
    sell_score = result["pillars"]["SELL"][pillar]

    cols[idx].metric(
        pillar_names[pillar],
        f"B {buy_score:.0f}",
        delta=f"S {sell_score:.0f}",
    )


# ============================================================
# MTF
# ============================================================

st.markdown("### ⏱️ Multi-Timeframe")

mtf_cols = st.columns(4)

for idx, (tf, info) in enumerate(result["mtf_details"].items()):
    mtf_cols[idx].metric(
        tf,
        info["bias"],
        f"strength {info['strength']}",
    )

st.info(
    f"MTF النهائي: **{result['mtf_bias']}** — "
    f"ثقة MTF: **{result['mtf_conf']:.1f}%**"
)


# ============================================================
# CONTEXT
# ============================================================

st.markdown("### 🌍 سياق السوق")

ctx1, ctx2, ctx3 = st.columns(3)
ctx1.metric("DXY", result["details"]["DXY"])
ctx2.metric("Regime", result["details"]["Regime"])
ctx3.metric("Divergence", result["details"]["Divergence"])

st.caption(result["details"]["USD"] if "USD" in result["details"] else "")

if "Gold" in selected_pair:
    corr = get_gold_dxy_correlation()
    if corr is not None:
        st.metric("DXY/Gold Return Correlation", f"{corr:.3f}")


# ============================================================
# DECISION EXPLANATION
# ============================================================

st.markdown("### 📝 أسباب القرار")

if result["reasons"]:
    for reason in result["reasons"][:12]:
        st.markdown(f"- {reason}")
else:
    st.info("لا يوجد سبب هيكلي قوي كافٍ.")

for k, v in result["details"].items():
    st.markdown(f"**{k}:** {v}")


# ============================================================
# TRADE PLAN
# ============================================================

st.markdown("### 🎯 خطة الصفقة")

if signal in ("BUY", "SELL") and levels:
    l1, l2, l3, l4 = st.columns(4)

    l1.metric("Entry", fmt_price(levels["entry"], selected_pair))
    l2.metric("Stop", fmt_price(levels["stop_loss"], selected_pair))
    l3.metric("TP1", fmt_price(levels["target1"], selected_pair))
    l4.metric("TP2 / TP3", f"{fmt_price(levels['target2'], selected_pair)} / {fmt_price(levels['target3'], selected_pair)}")

    r1, r2, r3 = st.columns(3)
    r1.metric("RR TP1", f"1:{levels['risk_reward_1']:.2f}")
    r2.metric("RR TP2", f"1:{levels['risk_reward_2']:.2f}")
    r3.metric("RR TP3", f"1:{levels['risk_reward_3']:.2f}")

    lots = calculate_position_size(
        selected_pair,
        levels["entry"],
        levels["stop_loss"],
        balance,
        risk_percent,
    )

    st.success(
        f"الحجم المقترح وفق نموذج المخاطرة: **{lots}** "
        f"مع مخاطرة {risk_percent:.2f}% من الرصيد."
    )

    allowed, reason = can_open_trade(confidence)

    if not allowed:
        st.warning(reason)
    else:
        if st.button("➕ إضافة الصفقة إلى Paper Trade", use_container_width=True):
            manager = TradeManager()

            trade = {
                "symbol": symbol,
                "pair_name": selected_pair,
                "direction": signal,
                "entry": levels["entry"],
                "lots": lots,
                "stop_loss": levels["stop_loss"],
                "target1": levels["target1"],
                "target2": levels["target2"],
                "target3": levels["target3"],
                "take_profit": levels["target2"],
                "confidence": confidence,
                "confluence": result["confluence"],
                "risk_reward": levels["risk_reward_3"],
                "notes": "; ".join(result["reasons"][:8]),
            }

            tid = manager.add_trade(trade)
            st.session_state.daily_trade_count += 1
            st.success(f"تمت إضافة الصفقة {tid}.")
            st.rerun()

else:
    st.warning("WAIT — لا توجد صفقة صالحة وفق شروط Structure + MTF + Risk.")


# ============================================================
# OPEN TRADES
# ============================================================

st.markdown("### 💼 الصفقات المفتوحة")

manager = TradeManager()

if manager.open_trades:
    for trade in manager.open_trades:
        with st.container(border=True):
            st.markdown(
                f"**{trade['id']} — {trade['pair_name']} — {trade['direction']}**"
            )

            a, b, c, d = st.columns(4)
            a.metric("Entry", fmt_price(trade["entry"], trade["pair_name"]))
            b.metric("SL", fmt_price(trade["stop_loss"], trade["pair_name"]))
            c.metric("TP1", fmt_price(trade["target1"], trade["pair_name"]))
            d.metric("Stage", trade.get("stage", 0))

            if trade["symbol"] == symbol:
                atr = safe_float(df["atr"].iloc[-1], np.nan)
                event = manager.monitor_trade(
                    trade["id"],
                    current_price,
                    atr=atr,
                )
                if event is not None:
                    st.warning("تم تحديث/إغلاق الصفقة تلقائيًا وفق قواعد Paper Trade.")
                    st.rerun()

            close_col, _ = st.columns([1, 2])
            if close_col.button(
                f"❌ إغلاق {trade['id']}",
                key=f"close_{trade['id']}",
                use_container_width=True,
            ):
                pnl = manager.close_trade(
                    trade["id"],
                    current_price,
                    "manual",
                )
                st.success(f"تم الإغلاق. P&L التقريبي: {pnl:.2f}")
                st.rerun()
else:
    st.info("لا توجد صفقات مفتوحة.")


# ============================================================
# MANUAL TRADE
# ============================================================

st.markdown("---")
st.markdown("### 🛠️ صفقة يدوية")

if st.button("فتح نموذج الصفقة اليدوية", use_container_width=True):
    st.session_state.show_manual = not st.session_state.show_manual

if st.session_state.show_manual:
    with st.form("manual_trade_v2003"):
        direction = st.selectbox("الاتجاه", ["BUY", "SELL"])
        entry = st.number_input("Entry", value=float(current_price), min_value=0.000001)
        stop = st.number_input(
            "Stop Loss",
            value=float(
                current_price * 0.99
                if direction == "BUY"
                else current_price * 1.01
            ),
            min_value=0.000001,
        )
        t1 = st.number_input("TP1", value=float(current_price * (1.01 if direction == "BUY" else 0.99)), min_value=0.000001)
        t2 = st.number_input("TP2", value=float(current_price * (1.02 if direction == "BUY" else 0.98)), min_value=0.000001)
        t3 = st.number_input("TP3", value=float(current_price * (1.03 if direction == "BUY" else 0.97)), min_value=0.000001)
        manual_lots = st.number_input("Lots (0 = auto)", min_value=0.0, value=0.0, step=0.01)

        submitted = st.form_submit_button("إضافة")

        if submitted:
            valid = (
                (direction == "BUY" and stop < entry < t1 < t2 < t3)
                or
                (direction == "SELL" and t3 < t2 < t1 < entry < stop)
            )

            if not valid:
                st.error("ترتيب Entry/SL/TP غير صحيح.")
            else:
                lots = manual_lots
                if lots <= 0:
                    lots = calculate_position_size(
                        selected_pair,
                        entry,
                        stop,
                        balance,
                        risk_percent,
                    )

                manager = TradeManager()
                tid = manager.add_trade({
                    "symbol": symbol,
                    "pair_name": selected_pair,
                    "direction": direction,
                    "entry": entry,
                    "lots": lots,
                    "stop_loss": stop,
                    "target1": t1,
                    "target2": t2,
                    "target3": t3,
                    "take_profit": t2,
                    "confidence": 0,
                    "confluence": 0,
                    "risk_reward": abs(t3 - entry) / max(abs(entry - stop), 1e-12),
                    "notes": "Manual",
                })

                st.success(f"تمت إضافة {tid}.")
                st.session_state.daily_trade_count += 1
                st.session_state.show_manual = False
                st.rerun()


# ============================================================
# CHART
# ============================================================

st.markdown("### 📈 الرسم البياني")

fig = make_subplots(
    rows=3,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.60, 0.20, 0.20],
)

fig.add_trace(
    go.Candlestick(
        x=df.index,
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="Price",
    ),
    row=1,
    col=1,
)

fig.add_trace(go.Scatter(x=df.index, y=df["ema20"], name="EMA20"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ema50"], name="EMA50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ema200"], name="EMA200"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["vwap"], name="Session VWAP"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower"), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI"), row=2, col=1)
fig.add_hline(y=70, row=2, col=1, line_dash="dash")
fig.add_hline(y=30, row=2, col=1, line_dash="dash")

fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal"), row=3, col=1)
fig.add_bar(x=df.index, y=df["macd_histogram"], name="Histogram", row=3, col=1)

if levels:
    fig.add_hline(y=levels["stop_loss"], row=1, col=1, line_dash="dot")
    fig.add_hline(y=levels["target1"], row=1, col=1, line_dash="dot")
    fig.add_hline(y=levels["target2"], row=1, col=1, line_dash="dot")
    fig.add_hline(y=levels["target3"], row=1, col=1, line_dash="dot")

fig.update_layout(
    height=850,
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
)

st.plotly_chart(fig, use_container_width=True)


# ============================================================
# ECONOMIC CALENDAR
# ============================================================

if st.session_state.economic_events:
    st.markdown("### 📅 الأخبار الاقتصادية")

    rows = []
    for event in st.session_state.economic_events[:20]:
        rows.append({
            "الدولة": event.get("country", ""),
            "الحدث": event.get("event", ""),
            "التأثير": event.get("impact", ""),
            "التاريخ": event.get("date", ""),
            "الوقت": event.get("time", ""),
        })

    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown(f"""
<div class="footer-style">
    ▲ BLACK PYRAMID {APP_VERSION} ▲<br>
    Structure • Trend • Momentum • Volume & Flow • Context • Risk
</div>
""", unsafe_allow_html=True)
