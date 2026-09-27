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
MIN_RR_TP1 = 0.80
MIN_RR_TP2 = 1.20
MIN_RR_TP3 = 1.60


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
        "min_rr": 1.20,
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
        "min_rr": 1.20,
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
        "min_rr": 1.20,
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
    """
    Daily/session VWAP.
    Unlike v2002, this is NOT a three-month cumulative VWAP.
    It resets at each UTC trading day.
    """
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


    # Forex/yfinance volume can be zero or unusable.
    fallback = tp.groupby(dates).expanding().mean().reset_index(level=0, drop=True)
    return vwap.fillna(fallback)




def calc_ichimoku(df, tenkan=9, kijun=26, senkou=52):
    high = df["high"]
    low = df["low"]
    close = df["close"]


    tenkan_line = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    kijun_line = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2


    # Forward plotting is kept, but decision logic uses only
    # information available at the current bar.
    senkou_a_plot = ((tenkan_line + kijun_line) / 2).shift(kijun)
    senkou_b_plot = (
        (high.rolling(senkou).max() + low.rolling(senkou).min()) / 2
    ).shift(kijun)


    # Decision-safe cloud values at current time:
    cloud_a_now = ((tenkan_line + kijun_line) / 2)
    cloud_b_now = (high.rolling(senkou).max() + low.rolling(senkou).min()) / 2


    # Chikou is a plotted historical reference only.
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
    """
    BOS/MSS are based on confirmed swing points.
    The current bar is compared with the most recently confirmed
    swing before the current bar, preventing look-ahead leakage.
    """
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


        # Bearish sweep: take buy-side liquidity, reject and close back below.
        if h > prev_high + tol and c < prev_high:
            out.iloc[i, out.columns.get_loc("liquidity_sweep_bearish")] = True


        # Bullish sweep: take sell-side liquidity, reject and close back a
