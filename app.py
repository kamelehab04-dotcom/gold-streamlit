# ============================================================
# BLACK PYRAMID v2005
# Hierarchical Intelligence Engine — Full Institutional Filters
# Structure → Regime → Setup → Confirmation → Context → Risk → Edge
# 13 Institutional Filters Integrated
# ============================================================


import os
import json
import math
from pathlib import Path
from datetime import datetime, timedelta, timezone
import concurrent.futures
import time


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


APP_VERSION = "v2005.2"
TRADES_FILE = Path("trades_data_v2005_2.json")


DEFAULT_BALANCE = 100000.0
DEFAULT_RISK_PERCENT = 1.0
MAX_DAILY_TRADES = 4
LOW_CONF_DAILY_LIMIT = 2
MAX_CONSECUTIVE_LOSSES = 3
MAX_DAILY_DRAWDOWN_R = 3.0


CONFIDENCE_MIN_TRADE = 65.0
# v2005.1: A/B/C execution tiers
A_PLUS_MIN = 82.0
A_MIN = 75.0
B_MIN = 68.0
C_MIN = 62.0
MAX_SOFT_PENALTY = 18.0
MIN_RR_TP1 = 1.00
MIN_RR_TP2 = 1.50
MIN_RR_TP3 = 2.00


ASSET_PROFILES = {
    "forex": {
        "atr_period": 14, "rsi_period": 14, "rsi_ob": 70, "rsi_os": 30,
        "mfi_period": 14, "bb_period": 20, "bb_std": 2.0,
        "atr_sl": 1.20, "atr_trail": 1.00, "swing_order": 3,
        "structure_lookback": 120, "confidence_threshold": 70,
        "min_rr": 1.50, "pip_size": 0.0001, "contract_size": 100000,
        "confirmation_threshold": 62, "max_risk_percent": 1.0,
    },
    "gold": {
        "atr_period": 14, "rsi_period": 14, "rsi_ob": 80, "rsi_os": 20,
        "mfi_period": 9, "bb_period": 20, "bb_std": 2.2,
        "atr_sl": 1.50, "atr_trail": 1.20, "swing_order": 3,
        "structure_lookback": 175, "confidence_threshold": 72,
        "min_rr": 1.50, "pip_size": 0.01, "contract_size": 100,
        "confirmation_threshold": 65, "max_risk_percent": 1.0,
    },
    "crypto": {
        "atr_period": 14, "rsi_period": 14, "rsi_ob": 80, "rsi_os": 20,
        "mfi_period": 10, "bb_period": 50, "bb_std": 2.3,
        "atr_sl": 1.80, "atr_trail": 1.50, "swing_order": 4,
        "structure_lookback": 250, "confidence_threshold": 75,
        "min_rr": 1.50, "pip_size": 0.01, "contract_size": 1,
        "confirmation_threshold": 68, "max_risk_percent": 1.0,
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


YF_SYMBOL_ALTERNATIVES = {
    "GC=F": ["GC=F", "XAUUSD=X", "GLD"],
    "SI=F": ["SI=F", "XAGUSD=X", "SLV"],
    "DX-Y.NYB": ["DX-Y.NYB", "DX=F", "UUP"],
    "BTC-USD": ["BTC-USD", "BTC=F"],
    "ETH-USD": ["ETH-USD", "ETH=F"],
    "EURUSD=X": ["EURUSD=X", "EUR=F"],
    "GBPUSD=X": ["GBPUSD=X", "GBP=F"],
    "USDJPY=X": ["USDJPY=X", "JPY=F"],
    "AUDUSD=X": ["AUDUSD=X", "AUD=F"],
    "USDCAD=X": ["USDCAD=X", "CAD=F"],
    "USDCHF=X": ["USDCHF=X", "CHF=F"],
    "NZDUSD=X": ["NZDUSD=X", "NZD=F"],
}


CORRELATION_GROUPS = {
    "USD_SHORT": ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X"],
    "USD_LONG":  ["USDJPY=X", "USDCHF=X", "USDCAD=X"],
    "METALS":    ["GC=F", "SI=F"],
    "CRYPTO":    ["BTC-USD", "ETH-USD"],
}


KILL_ZONES = {
    "London Open":  (7, 10),
    "NY Open":      (12, 15),
    "London Close": (15, 17),
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
        "economic_events": None,
        "daily_trade_count": 0,
        "trade_date": datetime.now().strftime("%Y-%m-%d"),
        "analyzing_all": False,
        "analysis_time": None,
        "backtest_results": None,
        "backtest_running": False,
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


def safe_bool(value):
    try:
        return bool(value) and not pd.isna(value)
    except Exception:
        return False


def asset_type_from_name(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["gold", "silver", "xau", "xag"]):
        return "gold"
    if any(x in n for x in ["bitcoin", "ethereum", "btc", "eth"]):
        return "crypto"
    return "forex"


def profile_for(name: str):
    return ASSET_PROFILES[asset_type_from_name(name)]


def get_asset_profile(pair_name):
    name = str(pair_name).upper()
    if "XAU" in name or "GOLD" in name:
        return "gold"
    if any(x in name for x in ("BTC", "ETH", "XRP", "SOL", "ADA")):
        return "crypto"
    return "forex"


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
        return False, "الثقة منخفضة ولا يسمح بصفقة إضافية."
    return True, ""




# ============================================================
# DATA LAYER
# ============================================================


def normalize_ohlcv(df, min_rows=50):
    if df is None or df.empty:
        return None
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    rename = {}
    for c in df.columns:
        lc = str(c).lower()
        if lc == "open": rename[c] = "open"
        elif lc == "high": rename[c] = "high"
        elif lc == "low": rename[c] = "low"
        elif lc == "close": rename[c] = "close"
        elif lc in ("volume", "vol"): rename[c] = "volume"
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
    return df if len(df) >= min_rows else None


@st.cache_data(ttl=60, show_spinner=False)
def get_yfinance(symbol, period="3mo", interval="4h"):
    try:
        df = yf.download(symbol, period=period, interval=interval,
                         auto_adjust=False, progress=False, threads=False)
        return normalize_ohlcv(df)
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def get_twelve_data(symbol, interval="4h", outputsize=500):
    if not TWELVE_API_KEY:
        return None
    mapping = {
        "GC=F": "XAU/USD", "SI=F": "XAG/USD", "DX-Y.NYB": "DXY",
        "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
        "USDCHF=X": "USD/CHF", "AUDUSD=X": "AUD/USD", "NZDUSD=X": "NZD/USD",
        "USDCAD=X": "USD/CAD", "EURGBP=X": "EUR/GBP", "EURJPY=X": "EUR/JPY",
        "EURCHF=X": "EUR/CHF", "EURAUD=X": "EUR/AUD", "EURNZD=X": "EUR/NZD",
        "EURCAD=X": "EUR/CAD", "GBPJPY=X": "GBP/JPY", "GBPCHF=X": "GBP/CHF",
        "GBPAUD=X": "GBP/AUD", "GBPNZD=X": "GBP/NZD", "GBPCAD=X": "GBP/CAD",
        "AUDJPY=X": "AUD/JPY", "AUDCHF=X": "AUD/CHF", "AUDNZD=X": "AUD/NZD",
        "AUDCAD=X": "AUD/CAD", "NZDJPY=X": "NZD/JPY", "NZDCHF=X": "NZD/CHF",
        "NZDCAD=X": "NZD/CAD", "CADJPY=X": "CAD/JPY", "CADCHF=X": "CAD/CHF",
        "BTC-USD": "BTC/USD", "ETH-USD": "ETH/USD",
    }
    td_symbol = mapping.get(symbol, symbol)
    interval_map = {"15m": "15min", "1h": "1h", "4h": "4h", "1d": "1day"}
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": td_symbol,
              "interval": interval_map.get(interval, interval),
              "outputsize": outputsize, "apikey": TWELVE_API_KEY, "format": "JSON"}
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
    candidates = YF_SYMBOL_ALTERNATIVES.get(symbol, [symbol])
    for yf_sym in candidates:
        df = get_yfinance(yf_sym, period, interval)
        if df is not None and len(df) >= 50:
            return df
    df = get_twelve_data(symbol, interval, 500)
    if df is not None and len(df) >= 50:
        return df
    for yf_sym in candidates:
        df = get_yfinance(yf_sym, "1mo", interval)
        if df is not None and len(df) >= 30:
            return df
    return None


@st.cache_data(ttl=30, show_spinner=False)
def get_spot_price(symbol):
    candidates = YF_SYMBOL_ALTERNATIVES.get(symbol, [symbol])
    for yf_sym in candidates:
        for period, interval in [("1d", "5m"), ("5d", "1h"), ("1mo", "1d")]:
            try:
                df = yf.download(yf_sym, period=period, interval=interval,
                                 auto_adjust=False, progress=False, threads=False)
                df = normalize_ohlcv(df, min_rows=1)
                if df is not None and not df.empty:
                    first = float(df["close"].iloc[0])
                    last = float(df["close"].iloc[-1])
                    change = ((last - first) / first * 100) if first else 0.0
                    return last, change
            except Exception:
                continue
    try:
        df = get_twelve_data(symbol, "1h", 5)
        if df is not None and not df.empty:
            return float(df["close"].iloc[-1]), 0.0
    except Exception:
        pass
    try:
        df = get_historical_data(symbol, "3mo", "4h")
        if df is not None and not df.empty:
            return float(df["close"].iloc[-1]), 0.0
    except Exception:
        pass
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
    rsi = rsi.where(avg_loss > 0, 100.0)
    rsi = rsi.where(avg_gain > 0, 0.0)
    return rsi.fillna(50).clip(0, 100)


def calc_vrsi(df, period=14):
    close = pd.to_numeric(df["close"], errors="coerce")
    volume = pd.to_numeric(df.get("volume", pd.Series(index=df.index, dtype=float)),
                           errors="coerce").fillna(0.0)
    delta = close.diff()
    gain = delta.clip(lower=0).fillna(0.0) * volume
    loss = (-delta.clip(upper=0)).fillna(0.0) * volume
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    vrsi = 100 - (100 / (1 + rs))
    return vrsi.replace([np.inf, -np.inf], np.nan).fillna(calc_rsi(close, period)).fillna(50.0)


def calc_atr(df, period=14):
    prev_close = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig, macd - sig


def calc_bollinger(series, period=20, std=2.0):
    mid = series.rolling(period).mean()
    dev = series.rolling(period).std()
    return mid + std * dev, mid, mid - std * dev


def calc_mfi(df, period=14):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    volume = pd.to_numeric(df["volume"], errors="coerce").fillna(0).clip(lower=0)
    raw = tp * volume
    direction = tp.diff()
    pos = raw.where(direction > 0, 0.0).rolling(period, min_periods=period).sum()
    neg = raw.where(direction < 0, 0.0).abs().rolling(period, min_periods=period).sum()
    ratio = pos / neg.replace(0, np.nan)
    mfi = 100 - (100 / (1 + ratio))
    mfi = mfi.where(neg > 0, 100.0)
    mfi = mfi.where(pos > 0, 0.0)
    return mfi.fillna(50).clip(0, 100)


def calc_chaikin(df, period=21):
    hl = (df["high"] - df["low"]).replace(0, np.nan)
    multiplier = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl
    money_volume = multiplier.fillna(0) * df["volume"]
    return (money_volume.rolling(period).sum()
            / df["volume"].rolling(period).sum().replace(0, np.nan)).fillna(0)


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
    high, low, close = df["high"], df["low"], df["close"]
    tenkan_line = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    kijun_line = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    senkou_a_plot = ((tenkan_line + kijun_line) / 2).shift(kijun)
    senkou_b_plot = ((high.rolling(senkou).max() + low.rolling(senkou).min()) / 2).shift(kijun)
    cloud_a_now = ((tenkan_line + kijun_line) / 2)
    cloud_b_now = (high.rolling(senkou).max() + low.rolling(senkou).min()) / 2
    chikou_plot = close.shift(-kijun)
    return (tenkan_line, kijun_line, senkou_a_plot, senkou_b_plot,
            chikou_plot, cloud_a_now, cloud_b_now)




# ============================================================
# INSTITUTIONAL FILTERS v2005 (13 filters)
# ============================================================


# ---------- FILTER 1: HTF Zone ----------
@st.cache_data(ttl=180, show_spinner=False)
def htf_zone_filter(symbol, direction, profile_key):
    try:
        df_d1 = get_historical_data(symbol, "1y", "1d")
        if df_d1 is None or len(df_d1) < 60:
            return True, "HTF غير متاح — مسموح", "UNKNOWN"
        profile = ASSET_PROFILES[profile_key]
        x = build_features(df_d1, profile)
        last = x.iloc[-1]
        in_premium = safe_bool(last.get("in_premium"))
        in_discount = safe_bool(last.get("in_discount"))
        if direction == "BUY" and in_premium:
            return False, "BUY مرفوض: HTF في Premium", "PREMIUM"
        if direction == "SELL" and in_discount:
            return False, "SELL مرفوض: HTF في Discount", "DISCOUNT"
        if direction == "BUY" and in_discount:
            return True, "BUY في Discount HTF ✅", "DISCOUNT"
        if direction == "SELL" and in_premium:
            return True, "SELL في Premium HTF ✅", "PREMIUM"
        return True, "HTF محايد", "MID"
    except Exception:
        return True, "HTF فشل التحميل", "UNKNOWN"




# ---------- FILTER 2: LTF Trigger ----------
@st.cache_data(ttl=180, show_spinner=False)
def ltf_entry_trigger(symbol, direction, profile_key):
    try:
        df = get_historical_data(symbol, "3mo", "1h")
        if df is None or len(df) < 60:
            return True, "LTF غير متاح — مسموح"
        profile = ASSET_PROFILES[profile_key]
        x = build_features(df, profile)
        if len(x) < 3:
            return True, "LTF قصير"
        last = x.iloc[-1]
        prev = x.iloc[-2]
        if direction == "BUY":
            if safe_bool(last.get("bos_bullish")):
                return True, "BOS صاعد 1H ✅"
            if safe_bool(last.get("liquidity_sweep_bullish")):
                return True, "Liquidity Sweep صاعد 1H ✅"
            if (last["close"] > last["open"] and prev["close"] < prev["open"]
                and safe_bool(last.get("fvg_bullish"))):
                return True, "Engulfing + FVG 1H ✅"
        if direction == "SELL":
            if safe_bool(last.get("bos_bearish")):
                return True, "BOS هابط 1H ✅"
            if safe_bool(last.get("liquidity_sweep_bearish")):
                return True, "Liquidity Sweep هابط 1H ✅"
            if (last["close"] < last["open"] and prev["close"] > prev["open"]
                and safe_bool(last.get("fvg_bearish"))):
                return True, "Engulfing + FVG 1H ✅"
        return False, "لا يوجد trigger على 1H"
    except Exception:
        return True, "LTF فشل — مسموح"




# ---------- FILTER 3: Session ----------
def session_filter(pair_name, strict=True):
    now_utc = datetime.now(timezone.utc).hour
    london_open = 7 <= now_utc <= 16
    ny_open = 12 <= now_utc <= 21
    overlap = 12 <= now_utc <= 16
    asian = 0 <= now_utc <= 7
    asset = asset_type_from_name(pair_name)
    if asset == "crypto":
        if overlap:
            return True, "NY/London Overlap (أعلى سيولة)", "OVERLAP"
        return True, "Crypto يعمل 24/7", "CRYPTO"
    if asset == "gold":
        if overlap:
            return True, "Overlap مثالي للذهب ✅", "OVERLAP"
        if london_open or ny_open:
            return True, "جلسة نشطة للذهب ✅", "ACTIVE"
        return False, "خارج جلسات الذهب النشطة", "DEAD"
    if strict and asian:
        return False, "الجلسة الآسيوية — سيولة منخفضة", "ASIAN"
    if overlap:
        return True, "Overlap مثالي ✅", "OVERLAP"
    if london_open or ny_open:
        return True, "جلسة نشطة ✅", "ACTIVE"
    return False, "خارج الجلسات النشطة", "DEAD"




# ---------- FILTER 4: Volatility ----------
def volatility_regime_filter(df):
    atr = df["atr"].dropna() if "atr" in df.columns else pd.Series()
    if len(atr) < 100:
        return True, "بيانات غير كافية", "NORMAL"
    current_atr = atr.iloc[-1]
    atr_mean = atr.rolling(100).mean().iloc[-1]
    atr_std = atr.rolling(100).std().iloc[-1]
    if not np.isfinite(atr_std) or atr_std == 0:
        return True, "ATR ثابت", "NORMAL"
    z = (current_atr - atr_mean) / atr_std
    if z < -1.0:
        return False, f"سوق ميت (ATR Z={z:.1f})", "DEAD"
    if z > 2.5:
        return False, f"تقلب مفرط (ATR Z={z:.1f})", "CHAOS"
    if 1.5 < z <= 2.5:
        return True, f"تقلب مرتفع (Z={z:.1f}) — احترس", "HIGH"
    if -1.0 <= z < -0.3:
        return True, f"تقلب منخفض (Z={z:.1f}) — حذر", "LOW"
    return True, f"تقلب طبيعي (Z={z:.1f})", "NORMAL"




# ---------- FILTER 5: Weighted Confluence ----------
def weighted_confluence(pillar_data, direction):
    weights = {"structure": 30, "trend": 20, "context": 20,
               "momentum": 15, "volume": 15}
    total = 0.0
    for pillar, w in weights.items():
        s = safe_float(pillar_data[direction].get(pillar), 0)
        if s >= 70: total += w * 1.0
        elif s >= 50: total += w * 0.5
        elif s < 30: total -= w * 0.3
    return clamp(total, 0, 100)




# ---------- FILTER 6: Correlation Guard ----------
def correlation_guard(new_symbol, direction, open_trades):
    for group, symbols in CORRELATION_GROUPS.items():
        if new_symbol not in symbols:
            continue
        for trade in open_trades:
            if trade.get("symbol") in symbols and trade["symbol"] != new_symbol:
                if trade.get("direction") == direction:
                    return False, f"مترابطة مع {trade['symbol']} ({group})"
    return True, "لا تعارض ارتباطي"




# ---------- FILTER 7: News Window ----------
def news_time_block(events, pair_name, window_minutes=45):
    if not events:
        return False, ""
    now = datetime.now(timezone.utc)
    name = str(pair_name).upper()
    currencies = set()
    if "/" in name:
        parts = name.split("/")
        base = parts[0].strip()
        quote = parts[1].strip().split()[0] if len(parts) > 1 else ""
        currencies.update([base, quote])
    else:
        currencies.add("USD")
    for event in events:
        impact = str(event.get("impact", "")).strip().lower()
        if impact not in ("high", "3", "high impact"):
            continue
        country = str(event.get("country", "")).strip().upper()
        country_map = {"US": "USD", "EU": "EUR", "GB": "GBP", "JP": "JPY",
                       "CH": "CHF", "AU": "AUD", "NZ": "NZD", "CA": "CAD"}
        mapped = country_map.get(country, country)
        if mapped not in currencies:
            continue
        try:
            date_str = event.get("date", "")
            if not date_str:
                continue
            event_time = pd.to_datetime(date_str)
            if event_time.tzinfo is None:
                event_time = event_time.tz_localize("UTC")
            if abs((event_time - now).total_seconds()) / 60 < window_minutes:
                return True, f"خبر {event.get('event')} خلال {window_minutes}د"
        except Exception:
            continue
    return False, ""




# ---------- FILTER 8: Displacement ----------
def displacement_check(df, direction):
    if len(df) < 2:
        return False, "بيانات غير كافية"
    last = df.iloc[-1]
    atr = safe_float(last.get("atr"), 0)
    if atr <= 0:
        return False, "ATR غير صالح"
    body = abs(last["close"] - last["open"])
    if body < 1.5 * atr:
        return False, f"لا Displacement ({body/atr:.1f}x)"
    if direction == "BUY" and last["close"] < last["open"]:
        return False, "Displacement ضد BUY"
    if direction == "SELL" and last["close"] > last["open"]:
        return False, "Displacement ضد SELL"
    return True, f"Displacement {body/atr:.1f}x ATR ✅"




# ---------- FILTER 9: Kill Zone ----------
def in_kill_zone(asset_type):
    hour = datetime.now(timezone.utc).hour
    if asset_type == "crypto":
        return True, "Crypto 24/7"
    for name, (start, end) in KILL_ZONES.items():
        if start <= hour < end:
            return True, f"{name} ✅"
    return False, "خارج Kill Zones"




# ---------- FILTER 10: OTE ----------
def ote_filter(df, direction):
    swings_h = get_last_two_swings(df, "high")
    swings_l = get_last_two_swings(df, "low")
    if not swings_h or not swings_l:
        return True, "OTE غير متاح — مسموح"
    swing_h = swings_h[-1][1]
    swing_l = swings_l[-1][1]
    current = df["close"].iloc[-1]
    leg = swing_h - swing_l
    if leg <= 0:
        return True, "موجة غير صالحة"
    if direction == "BUY":
        retr = (swing_h - current) / leg
        if 0.55 <= retr <= 0.85:
            return True, f"OTE صاعد {retr*100:.0f}% ✅"
        return False, f"خارج OTE ({retr*100:.0f}%)"
    else:
        retr = (current - swing_l) / leg
        if 0.55 <= retr <= 0.85:
            return True, f"OTE هابط {retr*100:.0f}% ✅"
        return False, f"خارج OTE ({retr*100:.0f}%)"




# ---------- FILTER 12: Kill Switch ----------
def kill_switch_check(closed_trades, max_consecutive=MAX_CONSECUTIVE_LOSSES,
                      max_daily_r=MAX_DAILY_DRAWDOWN_R):
    if not closed_trades:
        return True, ""
    today = datetime.now().strftime("%Y-%m-%d")
    today_trades = [t for t in closed_trades
                    if str(t.get("close_time", "")).startswith(today)]
    consecutive = 0
    for t in reversed(today_trades):
        if float(t.get("pnl", 0)) < 0:
            consecutive += 1
            if consecutive >= max_consecutive:
                return False, f"🛑 Kill Switch: {consecutive} خسائر متتالية"
        else:
            break
    daily_r = 0.0
    for t in today_trades:
        entry = safe_float(t.get("entry"), 0)
        sl = safe_float(t.get("stop_loss"), 0)
        risk = abs(entry - sl)
        if risk <= 0:
            continue
        pnl = float(t.get("pnl", 0))
        daily_r += (pnl / risk) if risk > 0 else 0
    if daily_r <= -max_daily_r:
        return False, f"🛑 Kill Switch: Drawdown {daily_r:.1f}R"
    return True, ""




# ---------- FILTER 13: Weekly Bias ----------
@st.cache_data(ttl=600, show_spinner=False)
def weekly_bias(symbol, pair_name):
    df = get_historical_data(symbol, "2y", "1wk")
    if df is None or len(df) < 30:
        return "NEUTRAL", 0
    try:
        profile = profile_for(pair_name)
        x = build_features(df, profile)
        if len(x) < 5:
            return "NEUTRAL", 0
        last = x.iloc[-1]
        bull = bear = 0
        if last["ema20"] > last["ema50"]: bull += 1
        elif last["ema20"] < last["ema50"]: bear += 1
        if last["macd"] > last["macd_signal"]: bull += 1
        elif last["macd"] < last["macd_signal"]: bear += 1
        structure = structure_state(x)
        if structure["bullish"]: bull += 2
        elif structure["bearish"]: bear += 2
        if bull > bear: return "BULLISH", bull
        if bear > bull: return "BEARISH", bear
        return "NEUTRAL", 0
    except Exception:
        return "NEUTRAL", 0




# ============================================================
# SWING / STRUCTURE
# ============================================================


def find_confirmed_swings(df, order=3):
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    swing_high = np.zeros(len(df), dtype=bool)
    swing_low = np.zeros(len(df), dtype=bool)
    for i in range(order, len(df) - order):
        h = highs[i]; l = lows[i]
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
    return [(points[-2], float(values[-2])), (points[-1], float(values[-1]))]


def structure_state(df):
    highs = get_last_two_swings(df, "high")
    lows = get_last_two_swings(df, "low")
    bullish = False; bearish = False; state = "RANGE"
    if highs and lows:
        hh = highs[-1][1] > highs[-2][1]
        hl = lows[-1][1] > lows[-2][1]
        lh = highs[-1][1] < highs[-2][1]
        ll = lows[-1][1] < lows[-2][1]
        if hh and hl: bullish = True; state = "BULLISH"
        elif lh and ll: bearish = True; state = "BEARISH"
    return {"state": state, "bullish": bullish, "bearish": bearish,
            "highs": highs, "lows": lows}


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
        last_high = float(past.loc[past_highs[-1], "high"]) if len(past_highs) else np.nan
        last_low = float(past.loc[past_lows[-1], "low"]) if len(past_lows) else np.nan
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
# LIQUIDITY / FVG / OB
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
        h = float(out["high"].iloc[i]); l = float(out["low"].iloc[i]); c = float(out["close"].iloc[i])
        if h > prev_high + tol and c < prev_high:
            out.iloc[i, out.columns.get_loc("liquidity_sweep_bearish")] = True
        if l < prev_low - tol and c > prev_low:
            out.iloc[i, out.columns.get_loc("liquidity_sweep_bullish")] = True
    return out


def detect_fvg(df):
    out = df.copy()
    out["fvg_bullish"] = False
    out["fvg_bearish"] = False
    out["fvg_bull_low"] = np.nan; out["fvg_bull_high"] = np.nan
    out["fvg_bear_low"] = np.nan; out["fvg_bear_high"] = np.nan
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
    out["ob_low"] = np.nan; out["ob_high"] = np.nan
    for i in range(1, len(out)):
        atr = safe_float(out["atr"].iloc[i], np.nan)
        if not np.isfinite(atr) or atr <= 0: continue
        body = abs(float(out["close"].iloc[i]) - float(out["open"].iloc[i]))
        if body < 1.20 * atr: continue
        po = float(out["open"].iloc[i - 1]); pc = float(out["close"].iloc[i - 1])
        ph = float(out["high"].iloc[i - 1]); pl = float(out["low"].iloc[i - 1])
        if pc < po and out["close"].iloc[i] > out["high"].iloc[i - 1]:
            out.iloc[i, out.columns.get_loc("order_block_bullish")] = True
            out.iloc[i, out.columns.get_loc("ob_low")] = pl
            out.iloc[i, out.columns.get_loc("ob_high")] = ph
        if pc > po and out["close"].iloc[i] < out["low"].iloc[i - 1]:
            out.iloc[i, out.columns.get_loc("order_block_bearish")] = True
            out.iloc[i, out.columns.get_loc("ob_low")] = pl
            out.iloc[i, out.columns.get_loc("ob_high")] = ph
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
    out["bsl"] = np.nan; out["ssl"] = np.nan
    if len(highs): out["bsl"] = float(out.loc[highs[-1], "high"])
    if len(lows): out["ssl"] = float(out.loc[lows[-1], "low"])
    return out




# ============================================================
# PATTERN / CANDLE
# ============================================================


def candle_confirmation(df, direction):
    if len(df) < 3: return False
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    rng = max(last["high"] - last["low"], 1e-12)
    if direction == "BUY":
        return bool(last["close"] > last["open"]
                    and (last["close"] - last["low"]) / rng >= 0.60
                    and body / rng >= 0.35)
    return bool(last["close"] < last["open"]
                and (last["high"] - last["close"]) / rng >= 0.60
                and body / rng >= 0.35)


def detect_divergence(df):
    if len(df) < 30: return None
    work = find_confirmed_swings(df, 3)
    lows = work.index[work["swing_low"]].tolist()
    highs = work.index[work["swing_high"]].tolist()
    if len(lows) >= 2:
        p1, p2 = lows[-2], lows[-1]
        if work.loc[p2, "low"] < work.loc[p1, "low"] and work.loc[p2, "rsi"] > work.loc[p1, "rsi"]:
            return "BULLISH"
    if len(highs) >= 2:
        p1, p2 = highs[-2], highs[-1]
        if work.loc[p2, "high"] > work.loc[p1, "high"] and work.loc[p2, "rsi"] < work.loc[p1, "rsi"]:
            return "BEARISH"
    return None


def smc_quality(df):
    if df is None or len(df) < 5: return 0.0, []
    last = df.iloc[-1]; score = 0.0; reasons = []
    checks = [("bos_bullish", "bos_bearish", 20, "BOS"),
              ("mss_bullish", "mss_bearish", 20, "MSS"),
              ("liquidity_sweep_bullish", "liquidity_sweep_bearish", 20, "Liquidity"),
              ("order_block_bullish", "order_block_bearish", 15, "OB"),
              ("fvg_bullish", "fvg_bearish", 10, "FVG"),
              ("in_discount", "in_premium", 15, "Prem/Disc")]
    for a, b, pts, label in checks:
        if safe_bool(last.get(a)) or safe_bool(last.get(b)):
            score += pts; reasons.append(label)
    return min(score, 100.0), reasons




# ============================================================
# FEATURE BUILD
# ============================================================


def build_features(df, profile):
    out = df.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["rsi"] = calc_rsi(out["close"], profile["rsi_period"])
    out["vrsi"] = calc_vrsi(out, profile["rsi_period"])
    out["atr"] = calc_atr(out, profile["atr_period"])
    out["macd"], out["macd_signal"], out["macd_histogram"] = calc_macd(out["close"], 12, 26, 9)
    out["bb_upper"], out["bb_mid"], out["bb_lower"] = calc_bollinger(
        out["close"], profile["bb_period"], profile["bb_std"])
    out["mfi"] = calc_mfi(out, profile["mfi_period"])
    out["chaikin_mf"] = calc_chaikin(out, 21)
    out["vwap"] = calc_session_vwap(out)
    (out["tenkan"], out["kijun"], out["senkou_a"], out["senkou_b"],
     out["chikou"], out["cloud_a_now"], out["cloud_b_now"]) = calc_ichimoku(out)
    out = analyze_smc(out, profile)
    return out




# ============================================================
# MTF
# ============================================================


def timeframe_bias(df, pair_name=None):
    if df is None or len(df) < 80: return "NEUTRAL", 0
    x = build_features(df, profile_for(pair_name or ""))
    last = x.iloc[-1]
    bull = bear = 0.0
    if last["ema20"] > last["ema50"]: bull += 1
    elif last["ema20"] < last["ema50"]: bear += 1
    if last["ema50"] > last["ema200"]: bull += 1
    elif last["ema50"] < last["ema200"]: bear += 1
    if last["macd_histogram"] > 0: bull += 1
    elif last["macd_histogram"] < 0: bear += 1
    vrsi = safe_float(last.get("vrsi"), 50)
    if vrsi >= 55: bull += 1
    elif vrsi <= 45: bear += 1
    structure = structure_state(x)
    if structure["bullish"]: bull += 2
    elif structure["bearish"]: bear += 2
    if safe_bool(last.get("bos_bullish")) or safe_bool(last.get("mss_bullish")): bull += 1
    if safe_bool(last.get("bos_bearish")) or safe_bool(last.get("mss_bearish")): bear += 1
    if bull > bear + 0.75:
        return "BULLISH", int(round(min(10, 10 * bull / max(bull + bear, 1))))
    if bear > bull + 0.75:
        return "BEARISH", int(round(min(10, 10 * bear / max(bull + bear, 1))))
    return "NEUTRAL", 0


@st.cache_data(ttl=120, show_spinner=False)
def get_mtf_analysis(symbol, pair_name=None):
    frames = {"1D": ("1y", "1d", 4.0), "4H": ("6mo", "4h", 3.0),
              "1H": ("3mo", "1h", 2.0), "15M": ("30d", "15m", 1.0)}
    results = {}; bull = bear = total = 0.0
    for name, (period, interval, weight) in frames.items():
        frame = get_historical_data(symbol, period, interval)
        bias, strength = timeframe_bias(frame, pair_name)
        results[name] = {"bias": bias, "strength": strength, "weight": weight}
        c = weight * (strength / 10.0)
        if bias == "BULLISH": bull += c
        elif bias == "BEARISH": bear += c
        total += weight
    final = ("BULLISH" if bull > bear * 1.20 and bull > 1.5
             else "BEARISH" if bear > bull * 1.20 and bear > 1.5
             else "NEUTRAL")
    conf = clamp(50 + abs(bull - bear) / max(total, 1) * 50, 50, 95)
    return final, conf, results




# ============================================================
# CONTEXT
# ============================================================


@st.cache_data(ttl=300, show_spinner=False)
def get_dxy_context():
    df = get_historical_data("DX-Y.NYB", "6mo", "4h")
    if df is None: return "NEUTRAL", 50.0, {}
    x = build_features(df, ASSET_PROFILES["forex"])
    last = x.iloc[-1]
    bull = bear = 0
    if last["close"] > last["ema50"]: bull += 1
    elif last["close"] < last["ema50"]: bear += 1
    if last["macd"] > last["macd_signal"]: bull += 1
    elif last["macd"] < last["macd_signal"]: bear += 1
    if last["rsi"] > 55: bull += 1
    elif last["rsi"] < 45: bear += 1
    if bull > bear: return "BULLISH", 55 + 10 * bull, {"trend": "USD strength"}
    if bear > bull: return "BEARISH", 55 + 10 * bear, {"trend": "USD weakness"}
    return "NEUTRAL", 50, {"trend": "USD neutral"}


def get_pair_usd_context(pair_name):
    if "/" not in pair_name: return 0.0, "لا تأثير مباشر"
    base, quote = [x.strip() for x in pair_name.split("/")[:2]]
    if "USD" not in (base, quote): return 0.0, "تأثير غير مباشر"
    dxy_bias, _, _ = get_dxy_context()
    if base == "USD":
        if dxy_bias == "BULLISH": return 1.0, "قوة الدولار تدعم الزوج"
        if dxy_bias == "BEARISH": return -1.0, "ضعف الدولار يضغط على الزوج"
    else:
        if dxy_bias == "BULLISH": return -1.0, "قوة الدولار تضغط على الزوج"
        if dxy_bias == "BEARISH": return 1.0, "ضعف الدولار يدعم الزوج"
    return 0.0, "تأثير الدولار محايد"


@st.cache_data(ttl=300, show_spinner=False)
def get_gold_dxy_correlation():
    dxy = get_historical_data("DX-Y.NYB", "3mo", "4h")
    gold = get_historical_data("GC=F", "3mo", "4h")
    if dxy is None or gold is None: return None
    aligned = pd.concat([dxy["close"].pct_change(), gold["close"].pct_change()],
                        axis=1, join="inner").dropna()
    if len(aligned) < 30: return None
    return float(aligned.iloc[:, 0].rolling(30).corr(aligned.iloc[:, 1]).iloc[-1])




# ============================================================
# MARKET REGIME
# ============================================================


def detect_regime(df):
    last = df.iloc[-1]
    atr = safe_float(last["atr"], np.nan)
    if not np.isfinite(atr) or atr <= 0: return "UNKNOWN", 50.0
    trend_strength = abs(last["ema20"] - last["ema50"]) / atr
    band_width = (last["bb_upper"] - last["bb_lower"]) / max(last["close"], 1e-12)
    if trend_strength >= 1.0:
        return ("TREND_BULLISH" if last["ema20"] > last["ema50"] else "TREND_BEARISH"), 75
    if band_width < 0.015: return "COMPRESSION", 65
    return "RANGE", 55




# ============================================================
# 5-PILLAR SCORING
# ============================================================


PILLAR_WEIGHTS = {"structure": 0.30, "trend": 0.20, "momentum": 0.15,
                  "volume": 0.15, "context": 0.20}


def directional_score(df, pair_name, symbol):
    last = df.iloc[-1]
    scores = {"BUY": {k: 0.0 for k in PILLAR_WEIGHTS},
              "SELL": {k: 0.0 for k in PILLAR_WEIGHTS}}
    reasons = []
    structure = structure_state(df)
    if structure["bullish"]:
        scores["BUY"]["structure"] += 45; reasons.append("الهيكل صاعد")
    elif structure["bearish"]:
        scores["SELL"]["structure"] += 45; reasons.append("الهيكل هابط")
    if bool(last["bos_bullish"]): scores["BUY"]["structure"] += 35; reasons.append("BOS صاعد")
    if bool(last["bos_bearish"]): scores["SELL"]["structure"] += 35; reasons.append("BOS هابط")
    if bool(last["mss_bullish"]): scores["BUY"]["structure"] += 20; reasons.append("MSS صاعد")
    if bool(last["mss_bearish"]): scores["SELL"]["structure"] += 20; reasons.append("MSS هابط")
    if bool(last["liquidity_sweep_bullish"]): scores["BUY"]["structure"] += 25
    if bool(last["liquidity_sweep_bearish"]): scores["SELL"]["structure"] += 25
    if bool(last["order_block_bullish"]): scores["BUY"]["structure"] += 15
    if bool(last["order_block_bearish"]): scores["SELL"]["structure"] += 15
    if bool(last["fvg_bullish"]): scores["BUY"]["structure"] += 10
    if bool(last["fvg_bearish"]): scores["SELL"]["structure"] += 10
    if bool(last["in_discount"]): scores["BUY"]["structure"] += 10
    if bool(last["in_premium"]): scores["SELL"]["structure"] += 10
    if last["ema20"] > last["ema50"] > last["ema200"]: scores["BUY"]["trend"] += 80
    elif last["ema20"] < last["ema50"] < last["ema200"]: scores["SELL"]["trend"] += 80
    else:
        if last["ema20"] > last["ema50"]: scores["BUY"]["trend"] += 45
        elif last["ema20"] < last["ema50"]: scores["SELL"]["trend"] += 45
    ct = max(safe_float(last["cloud_a_now"], np.nan), safe_float(last["cloud_b_now"], np.nan))
    cb = min(safe_float(last["cloud_a_now"], np.nan), safe_float(last["cloud_b_now"], np.nan))
    if np.isfinite(ct) and np.isfinite(cb):
        if last["close"] > ct: scores["BUY"]["trend"] += 20
        elif last["close"] < cb: scores["SELL"]["trend"] += 20
    rsi = safe_float(last["rsi"], 50)
    if rsi >= 55: scores["BUY"]["momentum"] += 45
    elif rsi <= 45: scores["SELL"]["momentum"] += 45
    if last["macd"] > last["macd_signal"] and last["macd_histogram"] > 0:
        scores["BUY"]["momentum"] += 45
    elif last["macd"] < last["macd_signal"] and last["macd_histogram"] < 0:
        scores["SELL"]["momentum"] += 45
    if last["mfi"] >= 55: scores["BUY"]["momentum"] += 10
    elif last["mfi"] <= 45: scores["SELL"]["momentum"] += 10
    if last["close"] > last["vwap"]: scores["BUY"]["volume"] += 45
    elif last["close"] < last["vwap"]: scores["SELL"]["volume"] += 45
    if last["chaikin_mf"] > 0: scores["BUY"]["volume"] += 35
    elif last["chaikin_mf"] < 0: scores["SELL"]["volume"] += 35
    va = df["volume"].rolling(20).mean().iloc[-1]
    if va and np.isfinite(va) and last["volume"] > va:
        if last["close"] > last["open"]: scores["BUY"]["volume"] += 20
        elif last["close"] < last["open"]: scores["SELL"]["volume"] += 20
    dxy_bias, _, _ = get_dxy_context()
    usd_impact, usd_msg = get_pair_usd_context(pair_name)
    if usd_impact > 0: scores["BUY"]["context"] += 45
    elif usd_impact < 0: scores["SELL"]["context"] += 45
    if "Gold" in pair_name:
        corr = get_gold_dxy_correlation()
        if corr is not None:
            if corr <= -0.50 and dxy_bias == "BEARISH": scores["BUY"]["context"] += 35
            elif corr <= -0.50 and dxy_bias == "BULLISH": scores["SELL"]["context"] += 35
    regime, _ = detect_regime(df)
    if regime == "TREND_BULLISH": scores["BUY"]["context"] += 20
    elif regime == "TREND_BEARISH": scores["SELL"]["context"] += 20
    tb = ts = 0.0
    for p, w in PILLAR_WEIGHTS.items():
        scores["BUY"][p] = clamp(scores["BUY"][p], 0, 100)
        scores["SELL"][p] = clamp(scores["SELL"][p], 0, 100)
        tb += scores["BUY"][p] * w
        ts += scores["SELL"][p] * w
    div = detect_divergence(df)
    if div == "BULLISH": tb += 3
    elif div == "BEARISH": ts += 3
    return {"buy": clamp(tb, 0, 100), "sell": clamp(ts, 0, 100),
            "pillars": scores, "reasons": reasons,
            "dxy_bias": dxy_bias, "usd_msg": usd_msg,
            "regime": regime, "divergence": div}




# ============================================================
# CONFIRMATION GATE v2005
# ============================================================


def confirmation_gate(df, direction, pillar_scores, regime,
                      mtf_bias="NEUTRAL", mtf_conf=50.0, profile=None,
                      weekly_bias_val="NEUTRAL"):
    if df is None or len(df) < 30:
        return False, 0.0, ["بيانات غير كافية"], ["DATA"]
    profile = profile or ASSET_PROFILES["forex"]
    last = df.iloc[-1]
    score = 0.0; reasons = []; blockers = []
    if (direction == "BUY" and regime == "TREND_BULLISH") or \
       (direction == "SELL" and regime == "TREND_BEARISH"):
        score += 20; reasons.append("Regime متوافق")
    elif regime == "RANGE":
        score += 8; reasons.append("Range: تأكيد أقل")
    elif regime == "COMPRESSION":
        score += 5; reasons.append("Compression")
    else:
        blockers.append("Regime غير متوافق")
    if (direction == "BUY" and mtf_bias == "BULLISH") or \
       (direction == "SELL" and mtf_bias == "BEARISH"):
        score += 25 * min(mtf_conf / 95, 1); reasons.append("MTF متوافق")
    elif mtf_bias != "NEUTRAL":
        blockers.append("MTF ضد الاتجاه")
    if (direction == "BUY" and weekly_bias_val == "BULLISH") or \
       (direction == "SELL" and weekly_bias_val == "BEARISH"):
        score += 15; reasons.append("Weekly متوافق")
    elif weekly_bias_val != "NEUTRAL":
        blockers.append("Weekly Bias ضد الاتجاه")
    ema_ok = (direction == "BUY" and last["ema20"] > last["ema50"]) or \
             (direction == "SELL" and last["ema20"] < last["ema50"])
    if ema_ok: score += 15; reasons.append("EMA alignment")
    else: blockers.append("EMA غير مؤيد")
    macd_ok = (direction == "BUY" and last["macd_histogram"] > 0) or \
              (direction == "SELL" and last["macd_histogram"] < 0)
    if macd_ok: score += 15; reasons.append("MACD مؤيد")
    else: blockers.append("Momentum غير مؤيد")
    if candle_confirmation(df, direction):
        score += 10; reasons.append("Candle confirmation")
    smc_score, smc_reasons = smc_quality(df)
    if smc_score >= 40:
        score += 15; reasons.extend(smc_reasons[:3])
    elif smc_score < 20:
        blockers.append("SMC ضعيف")
    own = sum(float(v) for v in pillar_scores.get(direction, {}).values())
    opp = sum(float(v) for v in pillar_scores.get(
        "SELL" if direction == "BUY" else "BUY", {}).values())
    if own < 180: blockers.append("الأدلة ضعيفة")
    if opp > own * 0.85: blockers.append("تعارض قوي Pillars")
    else: score += 5
    hard = any(x in blockers for x in ("MTF ضد الاتجاه", "Regime غير متوافق", "Weekly Bias ضد الاتجاه"))
    threshold = profile.get("confirmation_threshold", 62)
    ok = score >= threshold and not hard and len(blockers) <= 2
    return ok, clamp(score, 0, 100), reasons, blockers




def execution_permission(raw_confidence, confirmation_score,
                         news_block=False, risk_ok=True,
                         daily_allowed=True, profile=None,
                         filters_passed=True, filter_reason=""):
    profile = profile or ASSET_PROFILES["forex"]
    if not daily_allowed: return "WAIT", "الحد اليومي للصفقات"
    if news_block: return "WAIT", "خبر عالي التأثير"
    if not risk_ok: return "WAIT", "Risk Gate لم يجتز"
    if not filters_passed: return "WAIT", f"فلتر: {filter_reason}"
    if raw_confidence < profile.get("confidence_threshold", 70):
        return "WAIT", "الثقة أقل من حد الأصل"
    if confirmation_score < profile.get("confirmation_threshold", 62):
        return "WAIT", "Confirmation غير كافٍ"
    return "EXECUTE", "اجتاز كل الفلاتر"




# ============================================================
# RISK ENGINE
# ============================================================


def latest_structure_levels(df):
    lows = df.index[df["swing_low"]].tolist()
    highs = df.index[df["swing_high"]].tolist()
    sl = float(df.loc[lows[-1], "low"]) if lows else np.nan
    sh = float(df.loc[highs[-1], "high"]) if highs else np.nan
    return sl, sh


def calculate_trade_levels(df, signal, current_price, profile):
    atr = safe_float(df["atr"].iloc[-1], np.nan)
    if not np.isfinite(atr) or atr <= 0: return None
    swing_low, swing_high = latest_structure_levels(df)
    recent_low = float(df["low"].iloc[-8:].min())
    recent_high = float(df["high"].iloc[-8:].max())
    ssl = safe_float(df["ssl"].iloc[-1], np.nan)
    bsl = safe_float(df["bsl"].iloc[-1], np.nan)
    if signal == "BUY":
        candidates = [x for x in [swing_low, recent_low, ssl]
                      if np.isfinite(x) and x < current_price]
        structural_stop = max(candidates) if candidates else current_price - profile["atr_sl"] * atr
        stop_loss = structural_stop - 0.20 * atr
        risk = current_price - stop_loss
        if risk <= 0: return None
        targets = sorted([x for x in [recent_high, bsl]
                          if np.isfinite(x) and x > current_price])
        t1 = targets[0] if targets else current_price + risk
        t2 = current_price + risk * 1.5
        t3 = current_price + risk * 2.0
        if t1 <= current_price: t1 = current_price + risk
        if t2 <= t1: t2 = current_price + risk * 1.5
        if t3 <= t2: t3 = current_price + risk * 2.0
    else:
        candidates = [x for x in [swing_high, recent_high, bsl]
                      if np.isfinite(x) and x > current_price]
        structural_stop = min(candidates) if candidates else current_price + profile["atr_sl"] * atr
        stop_loss = structural_stop + 0.20 * atr
        risk = stop_loss - current_price
        if risk <= 0: return None
        targets = sorted([x for x in [recent_low, ssl]
                          if np.isfinite(x) and x < current_price], reverse=True)
        t1 = targets[0] if targets else current_price - risk
        t2 = current_price - risk * 1.5
        t3 = current_price - risk * 2.0
        if t1 >= current_price: t1 = current_price - risk
        if t2 >= t1: t2 = current_price - risk * 1.5
        if t3 >= t2: t3 = current_price - risk * 2.0
    rr1 = abs(t1 - current_price) / risk
    rr2 = abs(t2 - current_price) / risk
    rr3 = abs(t3 - current_price) / risk
    return {"entry": float(current_price), "stop_loss": float(stop_loss),
            "target1": float(t1), "target2": float(t2), "target3": float(t3),
            "risk": float(risk), "risk_reward_1": float(rr1),
            "risk_reward_2": float(rr2), "risk_reward_3": float(rr3)}


def validate_levels(signal, levels, profile):
    if not levels: return False, "تعذر بناء المستويات"
    if signal == "BUY":
        if not levels["stop_loss"] < levels["entry"] < levels["target1"]:
            return False, "ترتيب BUY غير صالح"
    else:
        if not levels["target1"] < levels["entry"] < levels["stop_loss"]:
            return False, "ترتيب SELL غير صالح"
    if levels["risk_reward_1"] < MIN_RR_TP1: return False, "TP1 RR منخفض"
    if levels["risk_reward_2"] < profile["min_rr"]: return False, "TP2 RR منخفض"
    if levels["risk_reward_3"] < MIN_RR_TP3: return False, "TP3 RR منخفض"
    return True, ""


def calculate_position_size(pair_name, entry, stop, balance, risk_percent):
    risk_money = balance * (risk_percent / 100.0)
    distance = abs(entry - stop)
    if distance <= 0 or risk_money <= 0: return 0.0
    asset = asset_type_from_name(pair_name)
    if asset == "forex":
        pip_size = 0.01 if "JPY" in pair_name else 0.0001
        contract_size = 100000.0
        quote_is_usd = pair_name.endswith("/USD")
        loss_per_lot = (distance / pip_size * (pip_size * contract_size)
                        if quote_is_usd else distance * contract_size)
    elif asset == "gold":
        loss_per_lot = distance * 100.0
    else:
        loss_per_lot = distance * 1.0
    if loss_per_lot <= 0: return 0.0
    lots = risk_money / loss_per_lot
    if asset == "forex": return round(clamp(lots, 0.01, 100.0), 2)
    if asset == "gold": return round(clamp(lots, 0.01, 100.0), 2)
    return round(clamp(lots, 0.0001, 100.0), 4)




# ============================================================
# FINAL SIGNAL ENGINE v2005
# ============================================================


def generate_signal(df, current_price, pair_name, symbol,
                    news_block=False, daily_allowed=True,
                    open_trades=None, skip_external_filters=False):
    profile = profile_for(pair_name)
    profile_key = get_asset_profile(pair_name)
    df = build_features(df, profile)
    scores = directional_score(df, pair_name, symbol)
    mtf_bias, mtf_conf, mtf_details = get_mtf_analysis(symbol, pair_name)
    wk_bias, _ = weekly_bias(symbol, pair_name)


    buy, sell = scores["buy"], scores["sell"]
    if mtf_bias == "BULLISH": buy += 8; sell -= 4
    elif mtf_bias == "BEARISH": sell += 8; buy -= 4
    if wk_bias == "BULLISH": buy += 5; sell -= 3
    elif wk_bias == "BEARISH": sell += 5; buy -= 3
    buy, sell = clamp(buy, 0, 100), clamp(sell, 0, 100)


    gap = abs(buy - sell)
    # v2005.2: فرق 8 نقاط يكفي لبدء تقييم الصفقة؛ لا نحولها إلى WAIT
    # بسبب MSS معاكس وحده، بل نخصم جودة لاحقًا.
    signal = "WAIT" if gap < 8 else ("BUY" if buy > sell else "SELL")
    last = df.iloc[-1]
    mss_conflict = False
    if safe_bool(last.get("mss_bullish")) and sell > buy:
        mss_conflict = True
    if safe_bool(last.get("mss_bearish")) and buy > sell:
        mss_conflict = True
    vrsi = safe_float(last.get("vrsi"), 50)
    if signal == "BUY" and vrsi > profile["rsi_ob"] and not safe_bool(last.get("mss_bullish")):
        buy = max(0, buy - 5)
    if signal == "SELL" and vrsi < profile["rsi_os"] and not safe_bool(last.get("mss_bearish")):
        sell = max(0, sell - 5)
    confidence = clamp(50 + abs(buy - sell) * 0.75 + max(0, max(buy, sell) - 60) * 0.25, 50, 95)


    # v2005.1: لا نحول الإشارة إلى WAIT مبكرًا.
    # التصنيف A+/A/B/C يحدد الجودة، بينما قرار التنفيذ النهائي يتم لاحقًا.


    candidate = signal if signal in ("BUY", "SELL") else ("BUY" if buy > sell else "SELL")
    levels = calculate_trade_levels(df, candidate, current_price, profile)
    risk_ok, risk_msg = validate_levels(candidate, levels, profile) if levels else (False, "تعذر")
    if signal in ("BUY", "SELL") and not risk_ok:
        signal = "WAIT"; confidence = min(confidence, 60)
    if signal == "BUY" and mtf_bias == "BEARISH":
        confidence *= 0.82
    if signal == "SELL" and mtf_bias == "BULLISH":
        confidence *= 0.82


    pillars = scores["pillars"]
    w_confluence = weighted_confluence(pillars, candidate)
    confluence = sum(1 for p in PILLAR_WEIGHTS if pillars[candidate][p] >= 50) if signal in ("BUY", "SELL") else 0


    conf_ok, conf_score, conf_reasons, conf_blockers = confirmation_gate(
        df, candidate, pillars, scores["regime"], mtf_bias, mtf_conf, profile, wk_bias)


    filter_results = {}
    filter_results["MSS Conflict"] = {
        "pass": not mss_conflict,
        "msg": "MSS معاكس — خصم جودة فقط" if mss_conflict else "MSS متوافق"
    }
    # v2005.2: Hard gates فقط لما يحمي رأس المال أو يمنع تعارضًا واضحًا.
    # الفلاتر الثانوية تُحتسب كجودة ولا تمنع الصفقة وحدها.
    all_passed = True
    block_reason = ""
    soft_penalties = 10 if mss_conflict and signal in ("BUY", "SELL") else 0

    external_filter_names = ["HTF Zone", "LTF Trigger", "Session", "Volatility",
                             "Kill Zone", "OTE", "Displacement", "Correlation",
                             "News Window"]
    if skip_external_filters:
        for _name in external_filter_names:
            filter_results[_name] = {"pass": True, "msg": "Backtest — skipped"}
    else:
        htf_ok, htf_msg, htf_zone = htf_zone_filter(symbol, candidate, profile_key)
        filter_results["HTF Zone"] = {"pass": htf_ok, "msg": htf_msg, "zone": htf_zone}
        if not htf_ok:
            all_passed = False
            block_reason = htf_msg

        ltf_ok, ltf_msg = ltf_entry_trigger(symbol, candidate, profile_key)
        filter_results["LTF Trigger"] = {"pass": ltf_ok, "msg": ltf_msg}
        if not ltf_ok:
            soft_penalties += 6

        sess_ok, sess_msg, sess_label = session_filter(
            pair_name, strict=(profile_key != "crypto"))
        filter_results["Session"] = {"pass": sess_ok, "msg": sess_msg, "label": sess_label}
        if not sess_ok:
            soft_penalties += 5

        vol_ok, vol_msg, vol_label = volatility_regime_filter(df)
        filter_results["Volatility"] = {"pass": vol_ok, "msg": vol_msg, "label": vol_label}
        if not vol_ok:
            if vol_label == "CHAOS":
                all_passed = False
                block_reason = block_reason or vol_msg
            else:
                soft_penalties += 8

        kz_ok, kz_msg = in_kill_zone(asset_type_from_name(pair_name))
        filter_results["Kill Zone"] = {"pass": kz_ok, "msg": kz_msg}
        if not kz_ok:
            soft_penalties += 3

        ote_ok, ote_msg = ote_filter(df, candidate)
        filter_results["OTE"] = {"pass": ote_ok, "msg": ote_msg}
        if not ote_ok:
            soft_penalties += 5

        disp_ok, disp_msg = displacement_check(df, candidate)
        filter_results["Displacement"] = {"pass": disp_ok, "msg": disp_msg}
        if not disp_ok:
            soft_penalties += 5

        corr_ok, corr_msg = correlation_guard(symbol, candidate, open_trades or [])
        filter_results["Correlation"] = {"pass": corr_ok, "msg": corr_msg}
        if not corr_ok:
            all_passed = False
            block_reason = block_reason or corr_msg

        ntw_block, ntw_msg = news_time_block(
            st.session_state.get("economic_events") or [], pair_name)
        filter_results["News Window"] = {
            "pass": not ntw_block, "msg": ntw_msg or "لا خبر قريب"
        }
        if ntw_block:
            all_passed = False
            block_reason = block_reason or ntw_msg


    # v2005.2 quality tier: soft filters lower quality but do not erase a valid setup.
    soft_penalties = min(float(soft_penalties), MAX_SOFT_PENALTY)
    effective_confidence = clamp(confidence - soft_penalties, 50, 95)
    if effective_confidence >= A_PLUS_MIN and conf_score >= 78:
        trade_grade = "A+"
    elif effective_confidence >= A_MIN and conf_score >= 70:
        trade_grade = "A"
    elif effective_confidence >= B_MIN and conf_score >= 62:
        trade_grade = "B"
    elif effective_confidence >= C_MIN and conf_score >= 55:
        trade_grade = "C"
    else:
        trade_grade = "WAIT"

    execution_status, execution_reason = execution_permission(
        effective_confidence, conf_score, news_block, risk_ok, daily_allowed,
        profile, all_passed, block_reason)

    # A/B يمكن تنفيذها عند اجتياز الـ hard gates حتى لو لم تبلغ threshold الأصل القديمة.
    if signal in ("BUY", "SELL") and trade_grade in ("A+", "A", "B") and all_passed and risk_ok and daily_allowed and not news_block:
        if conf_score >= 60:
            execution_status = "EXECUTE"
            execution_reason = f"{trade_grade} — Hard Gates PASS"
    elif trade_grade == "C" and execution_status == "EXECUTE":
        execution_status = "WATCH"
        execution_reason = "C — مراقبة فقط"

    confidence = effective_confidence


    if signal == "WAIT":
        execution_status = "WAIT"
        execution_reason = "الإشارة الأساسية WAIT"
    elif not conf_ok and trade_grade not in ("A+", "A", "B"):
        execution_status = "WAIT"
        execution_reason = "Confirmation Gate لم يجتز"


    details = {
        "BUY Score": round(buy, 1), "SELL Score": round(sell, 1),
        "MTF": mtf_bias, "MTF Confidence": round(mtf_conf, 1),
        "Weekly": wk_bias, "Regime": scores["regime"],
        "DXY": scores["dxy_bias"], "USD Context": scores["usd_msg"],
        "Divergence": scores["divergence"] or "None", "VRSI": round(vrsi, 1),
        "Weighted Confluence": round(w_confluence, 1),
        "Risk Gate": "PASS" if risk_ok else risk_msg,
        "Confirmation Score": round(conf_score, 1),
        "Confirmation Gate": "PASS" if conf_ok else "SOFT-FAIL" if trade_grade in ("A+", "A", "B") else "FAIL",
        "Trade Grade": trade_grade, "Soft Penalties": soft_penalties,
        "Execution": execution_status, "Execution Note": execution_reason,
    }


    return {
        "signal": signal, "confidence": confidence,
        "buy_score": buy, "sell_score": sell, "net_score": buy - sell,
        "confluence": confluence, "weighted_confluence": w_confluence,
        "details": details, "reasons": scores["reasons"] + conf_reasons,
        "pillars": pillars, "mtf_bias": mtf_bias, "mtf_conf": mtf_conf,
        "mtf_details": mtf_details, "weekly_bias": wk_bias,
        "levels": levels if risk_ok else None, "df": df,
        "confirmation_ok": conf_ok, "confirmation_score": conf_score,
        "confirmation_reasons": conf_reasons, "confirmation_blockers": conf_blockers,
        "execution_status": execution_status, "execution_reason": execution_reason,
        "trade_grade": trade_grade, "soft_penalties": soft_penalties,
        "filter_results": filter_results, "all_filters_passed": all_passed,
        "filter_block_reason": block_reason,
    }




# ============================================================
# BACKTEST ENGINE
# ============================================================


@st.cache_data(ttl=600, show_spinner=False)
def quick_backtest(symbol, pair_name, lookback=200):
    try:
        df = get_historical_data(symbol, "1y", "4h")
        if df is None or len(df) < lookback + 50:
            return None
        profile = profile_for(pair_name)
        df = build_features(df, profile)
        wins = losses = 0
        total_r = 0.0
        trades_detail = []
        for i in range(50, len(df) - 20):
            slice_df = df.iloc[:i].copy()
            price = float(df["close"].iloc[i])
            try:
                result = generate_signal(slice_df, price, pair_name, pair_name,
                                          skip_external_filters=True)
            except Exception:
                continue
            if result["signal"] == "WAIT" or result["levels"] is None:
                continue
            entry = result["levels"]["entry"]
            sl = result["levels"]["stop_loss"]
            t1 = result["levels"]["target1"]
            direction = result["signal"]
            future = df.iloc[i + 1:i + 21]
            hit_tp = hit_sl = False
            for _, row in future.iterrows():
                if direction == "BUY":
                    if row["low"] <= sl: hit_sl = True; break
                    if row["high"] >= t1: hit_tp = True; break
                else:
                    if row["high"] >= sl: hit_sl = True; break
                    if row["low"] <= t1: hit_tp = True; break
            r = result["levels"]["risk_reward_1"] if hit_tp else (-1.0 if hit_sl else 0.0)
            if hit_tp: wins += 1; total_r += r
            elif hit_sl: losses += 1; total_r -= 1.0
            trades_detail.append({"direction": direction, "r": r,
                                   "time": str(df.index[i])})
        total = wins + losses
        if total == 0: return None
        return {
            "trades": total, "wins": wins, "losses": losses,
            "win_rate": wins / total * 100, "total_R": total_r,
            "expectancy": total_r / total,
            "profit_factor": (wins * 1.5) / max(losses, 1),
            "details": trades_detail[-20:],
        }
    except Exception as e:
        return {"error": str(e)}




# ============================================================
# TRADE MANAGER
# ============================================================


def pnl_multiplier(pair_name):
    asset = asset_type_from_name(pair_name)
    if asset == "forex": return 100000.0
    if asset == "gold": return 100.0
    return 1.0


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
    def open_trades(self): return self.data["open_trades"]
    @property
    def closed_trades(self): return self.data["closed_trades"]


    def add_trade(self, trade):
        tid = f"T{len(self.open_trades) + len(self.closed_trades) + 1:04d}"
        item = dict(trade)
        item.update({"id": tid,
                     "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "status": "open", "stage": 0,
                     "highest_price": trade["entry"],
                     "lowest_price": trade["entry"],
                     "partial_close_done": False})
        self.open_trades.append(item)
        self.save()
        return tid


    def close_trade(self, tid, current_price, reason="manual"):
        for trade in list(self.open_trades):
            if trade["id"] != tid: continue
            entry = float(trade["entry"])
            lots = float(trade["lots"])
            mult = pnl_multiplier(trade.get("pair_name", ""))
            pnl = ((current_price - entry) * lots * mult if trade["direction"] == "BUY"
                   else (entry - current_price) * lots * mult)
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
            if trade["id"] != tid: continue
            direction = trade["direction"]
            entry = float(trade["entry"]); sl = float(trade["stop_loss"])
            if direction == "BUY":
                if current_price <= sl: return self.close_trade(tid, sl, "stop_loss")
                if (trade.get("target1") and current_price >= float(trade["target1"])
                        and not trade.get("partial_close_done")):
                    trade["partial_close_done"] = True
                    trade["stage"] = 1
                    trade["stop_loss"] = max(float(trade["stop_loss"]), entry)
                if trade.get("target2") and current_price >= float(trade["target2"]):
                    trade["stage"] = 2
                if trade.get("target3") and current_price >= float(trade["target3"]):
                    return self.close_trade(tid, float(trade["target3"]), "target3")
            else:
                if current_price >= sl: return self.close_trade(tid, sl, "stop_loss")
                if (trade.get("target1") and current_price <= float(trade["target1"])
                        and not trade.get("partial_close_done")):
                    trade["partial_close_done"] = True
                    trade["stage"] = 1
                    trade["stop_loss"] = min(float(trade["stop_loss"]), entry)
                if trade.get("target2") and current_price <= float(trade["target2"]):
                    trade["stage"] = 2
                if trade.get("target3") and current_price <= float(trade["target3"]):
                    return self.close_trade(tid, float(trade["target3"]), "target3")
            if trade.get("stage", 0) >= 1 and atr and np.isfinite(atr):
                trail = float(atr)
                if direction == "BUY":
                    trade["highest_price"] = max(float(trade.get("highest_price", entry)), current_price)
                    ns = trade["highest_price"] - trail
                    if ns > float(trade["stop_loss"]): trade["stop_loss"] = ns
                else:
                    trade["lowest_price"] = min(float(trade.get("lowest_price", entry)), current_price)
                    ns = trade["lowest_price"] + trail
                    if ns < float(trade["stop_loss"]): trade["stop_loss"] = ns
            self.save()
            return None
        return None




# ============================================================
# ALL SIGNALS PARALLEL
# ============================================================


@st.cache_data(ttl=600, show_spinner=False)
def get_all_signals_parallel():
    results = []
    total = len(PAIRS)


    def analyze_one(pair_name, symbol):
        try:
            price, _ = get_spot_price(symbol)
            df = get_historical_data(symbol, "3mo", "4h")
            if price is None or df is None: return None
            result = generate_signal(df, price, pair_name, symbol,
                                      skip_external_filters=True)
            levels = result["levels"] or {}
            return {
                "الزوج": pair_name,
                "الإشارة": result["signal"],
                "الثقة": round(result["confidence"], 1),
                "BUY": round(result["buy_score"], 1),
                "SELL": round(result["sell_score"], 1),
                "MTF": result["mtf_bias"],
                "Weekly": result["weekly_bias"],
                "التوافق": round(result["weighted_confluence"], 0),
                "التأكيد": round(result["confirmation_score"], 1),
                "Grade": result.get("trade_grade", "WAIT"),
                "التنفيذ": result["execution_status"],
                "السعر": fmt_price(price, pair_name),
                "SL": fmt_price(levels.get("stop_loss"), pair_name),
                "TP1": fmt_price(levels.get("target1"), pair_name),
                "RR3": round(levels.get("risk_reward_3", 0), 2) if levels else 0,
            }
        except Exception:
            return None


    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_one, p, s): (p, i)
                   for i, (p, s) in enumerate(PAIRS.items())}
        completed = 0
        for fut in concurrent.futures.as_completed(futures):
            pair_name, _ = futures[fut]
            try:
                res = fut.result()
                if res: results.append(res)
            except Exception: pass
            completed += 1


    if not results: return pd.DataFrame()
    out = pd.DataFrame(results)
    order = {"BUY": 0, "SELL": 1, "WAIT": 2}
    out["_o"] = out["الإشارة"].map(order).fillna(3)
    out = out.sort_values(["_o", "الثقة"], ascending=[True, False]).drop(columns="_o")
    return out




# ============================================================
# NEWS / CALENDAR
# ============================================================


@st.cache_data(ttl=300, show_spinner=False)
def get_fmp_economic_calendar():
    if not FMP_API_KEY: return []
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


def has_high_impact_event(events, pair_name):
    if not events: return False
    name = str(pair_name).upper()
    currencies = set()
    if "/" in name:
        parts = name.split("/")
        currencies.add(parts[0].strip())
        if len(parts) > 1:
            currencies.add(parts[1].strip().split()[0])
    else:
        currencies.add("USD")
    country_map = {"US": "USD", "EU": "EUR", "GB": "GBP", "JP": "JPY",
                   "CH": "CHF", "AU": "AUD", "NZ": "NZD", "CA": "CAD"}
    for e in events:
        if str(e.get("impact", "")).strip().lower() not in ("high", "3", "high impact"):
            continue
        country = str(e.get("country", "")).strip().upper()
        if country_map.get(country, country) in currencies:
            return True
    return False


def event_risk_message(events, pair_name):
    if not events: return "لا توجد بيانات تقويم"
    if has_high_impact_event(events, pair_name):
        return "⚠️ يوجد خبر عالي التأثير"
    return "لا يوجد قفل خبر مطابق"




# ============================================================
# UI
# ============================================================


st.set_page_config(page_title=f"BLACK PYRAMID {APP_VERSION}",
                   page_icon="▲", layout="wide")


st.markdown("""
<style>
body { direction: rtl; background: #0c0e14; font-family: 'Segoe UI', 'Tahoma', sans-serif; }
.main-header {
    background: linear-gradient(145deg, #141824, #1b202b);
    padding: 28px 30px; border-radius: 24px; margin-bottom: 22px;
    border: 1px solid rgba(255, 215, 0, 0.15);
    box-shadow: 0 12px 30px rgba(0,0,0,0.6); backdrop-filter: blur(4px);
}
.main-title { font-size: 2.5rem; font-weight: 800; color: #e6c87c; letter-spacing: 1px; }
.main-subtitle { color: #a8b2c8; margin-top: 6px; font-weight: 300; }
.signal-box {
    background: #12161f; padding: 28px 20px; border-radius: 24px; text-align: center;
    border: 1px solid rgba(255,255,255,0.06); box-shadow: 0 10px 28px rgba(0,0,0,0.5);
}
.signal-text { font-size: 3.2rem; font-weight: 800; letter-spacing: 1px; }
div.stButton > button {
    background: linear-gradient(145deg, #222b3a, #1a212e);
    color: #e8edf5; border: 1px solid rgba(255,215,0,0.15);
    border-radius: 40px; padding: 0.6rem 1.8rem; font-weight: 500;
    transition: all 0.25s ease; box-shadow: 0 6px 16px rgba(0,0,0,0.3);
    width: 100%;
}
div.stButton > button:hover {
    background: linear-gradient(145deg, #2f3b50, #1e283a);
    border-color: rgba(230,200,124,0.4); transform: scale(1.01); color: #fff;
}
div[data-testid="stMetric"] {
    background: #11161f; padding: 14px 16px; border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.04);
}
div[data-testid="stMetric"] label { color: #bcc3d4; }
div[data-testid="stMetric"] .stMetricValue { color: #e8edf5; font-weight: 600; }
div[data-testid="stDataFrame"] {
    background: #11161f; border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.04);
}
div[data-testid="stDataFrame"] th {
    background: #1b232f !important; color: #d4dcec !important;
}
div[data-testid="stDataFrame"] td {
    background: #0f141d !important; color: #ced6e6 !important;
}
div[data-baseweb="select"] > div {
    background: #131821; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 40px; padding: 0 16px;
}
div[data-baseweb="select"] input { color: #e8edf5 !important; }
hr { border: none; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(230,200,124,0.2), transparent);
    margin: 28px 0; }
.footer-style { text-align: center; color: #6b7488; padding: 28px 0 12px;
    border-top: 1px solid rgba(255,255,255,0.04); margin-top: 30px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


st.markdown(f"""
<div class="main-header">
    <div class="main-title">▲ BLACK PYRAMID {APP_VERSION} ▲</div>
    <div class="main-subtitle">
        Institutional Intelligence • Hard Gates + Quality Filters • Structure • MTF • SMC • Confirmation • Risk • Edge
    </div>
</div>
""", unsafe_allow_html=True)




# ============================================================
# MAIN CONTROLS
# ============================================================


with st.sidebar:
    st.markdown("## ⚙️ BLACK PYRAMID")
    st.caption(f"الإعدادات • {APP_VERSION}")
    selected_pair = st.selectbox(
        "اختر الأصل", list(PAIRS.keys()),
        index=list(PAIRS.keys()).index(st.session_state.selected_pair)
        if st.session_state.selected_pair in PAIRS else 0)
    st.session_state.selected_pair = selected_pair
    symbol = PAIRS[selected_pair]
    balance = st.number_input("رصيد الحساب", min_value=100.0,
                              value=DEFAULT_BALANCE, step=100.0)
    risk_percent = st.number_input("المخاطرة %", min_value=0.1, max_value=5.0,
                                   value=DEFAULT_RISK_PERCENT, step=0.1)
    if st.button("🔄 مسح الكاش", width="stretch"):
        st.cache_data.clear(); st.rerun()
    st.metric("صفقات اليوم", f"{st.session_state.daily_trade_count}/{MAX_DAILY_TRADES}")
    st.markdown("---")
    st.caption("Hard Gates: Risk • News • HTF • Correlation • Chaos")
    st.caption("Soft Quality: LTF • Session • OTE • Displacement • Kill Zone")



# ============================================================
# KILL SWITCH STATUS
# ============================================================


_manager_temp = TradeManager()
ks_ok, ks_msg = kill_switch_check(_manager_temp.closed_trades)
if not ks_ok:
    st.error(f"🛑 **KILL SWITCH مُفعّل** — {ks_msg}")
    st.caption("لا يُسمح بصفقات جديدة حتى إعادة تعيين الحالة أو انتهاء اليوم.")




# ============================================================
# ALL ASSETS ANALYSIS
# ============================================================


col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn1:
    if st.button("📋 تحليل جميع الأصول (سريع)", width="stretch"):
        with st.spinner("جاري التحليل المتوازي..."):
            start = time.time()
            st.session_state.all_signals = get_all_signals_parallel()
            st.session_state.analyzing_all = True
            st.session_state.analysis_time = time.time() - start
        st.rerun()
with col_btn2:
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        if st.button("🗑️ مسح النتائج", width="stretch"):
            st.session_state.all_signals = None
            st.session_state.analyzing_all = False
            st.session_state.analysis_time = None
            st.rerun()
with col_btn3:
    if st.session_state.get("analysis_time"):
        st.metric("⏱️ زمن التحليل", f"{st.session_state.analysis_time:.1f} ث")


if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
    st.success(f"✅ تم تحليل {len(st.session_state.all_signals)} أصلاً.")
    st.dataframe(st.session_state.all_signals, hide_index=True,
                 width="stretch", height=450)
elif st.session_state.analyzing_all:
    st.warning("⚠️ لم يتم العثور على نتائج.")
else:
    st.info("اضغط على 'تحليل جميع الأصول' لعرض الإشارات.")




# ============================================================
# ECONOMIC CALENDAR
# ============================================================


if st.button("📅 تحديث التقويم الاقتصادي", width="stretch"):
    st.session_state.economic_events = get_fmp_economic_calendar()
if st.session_state.economic_events:
    st.caption(event_risk_message(st.session_state.economic_events, selected_pair))


st.markdown("---")




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


news_block = has_high_impact_event(st.session_state.economic_events, selected_pair)
daily_allowed, daily_msg = can_open_trade(100)
ks_ok, _ = kill_switch_check(_manager_temp.closed_trades)
if not ks_ok:
    daily_allowed = False


result = generate_signal(
    df_raw, current_price, selected_pair, symbol,
    news_block=news_block, daily_allowed=daily_allowed,
    open_trades=_manager_temp.open_trades)


df = result["df"]; levels = result["levels"]
signal = result["signal"]; confidence = result["confidence"]




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
    <div style="font-size:1.2rem; color:#c8d2e2;">Confidence: {confidence:.1f}%</div>
    <div style="color:#b0bac8;">BUY: {result['buy_score']:.1f} | SELL: {result['sell_score']:.1f}</div>
    <div style="color:#a0aab8;">Weighted Confluence: {result['weighted_confluence']:.0f}/100</div>
    <div style="color:#e6c87c; font-size:1.35rem; font-weight:800;">Grade: {result.get('trade_grade', 'WAIT')}</div>
    <div style="color:#a0aab8;">Execution: <b>{result['execution_status']}</b></div>
</div>
""", unsafe_allow_html=True)




# ============================================================
# 13 FILTERS STATUS
# ============================================================


st.markdown("### 🎛️ الفلاتر المؤسسية + جودة الإشارة")


filters = result["filter_results"]
filter_items = list(filters.items())
for row_start in range(0, len(filter_items), 4):
    row_items = filter_items[row_start:row_start + 4]
    cols = st.columns(4)
    for idx, (name, info) in enumerate(row_items):
        passed = info.get("pass", True)
        icon = "✅" if passed else "❌"
        cols[idx].markdown(f"""
        <div style="background:#131821; padding:12px; border-radius:14px;
                    border:1px solid rgba(255,255,255,0.05); text-align:center;
                    margin-bottom:8px;">
            <div style="color:#bcc3d4; font-size:0.8rem;">{name}</div>
            <div style="font-size:1.5rem;">{icon}</div>
            <div style="color:#8b95a8; font-size:0.75rem;">{info.get('msg', '')[:45]}</div>
        </div>
        """, unsafe_allow_html=True)


if not result["all_filters_passed"]:
    st.error(f"🚫 **مانع التنفيذ:** {result['filter_block_reason']}")




# ============================================================
# 5 PILLARS
# ============================================================


st.markdown("### 🧠 المحاور الخمسة")
pillar_names = {"structure": "Structure", "trend": "Trend",
                "momentum": "Momentum", "volume": "Volume & Flow", "context": "Context"}
cols = st.columns(5)
for idx, pillar in enumerate(PILLAR_WEIGHTS):
    b = result["pillars"]["BUY"][pillar]
    s = result["pillars"]["SELL"][pillar]
    cols[idx].metric(pillar_names[pillar], f"B {b:.0f}", delta=f"S {s:.0f}")




# ============================================================
# CONFIRMATION + MTF + CONTEXT
# ============================================================


st.markdown("### 🛡️ Confirmation Gate v2005")
gc1, gc2, gc3, gc4 = st.columns(4)
gc1.metric("Confirmation Score", f"{result['confirmation_score']:.1f}/100")
gc2.metric("Gate", "✅ PASS" if result["confirmation_ok"] else "⚠️ SOFT" if result.get("trade_grade") in ("A+", "A", "B") else "❌ FAIL")
gc3.metric("Grade", result.get("trade_grade", "WAIT"))
gc4.metric("Execution", result["execution_status"])


with st.expander("تفاصيل التأكيد والموانع", expanded=False):
    for r in result["confirmation_reasons"]:
        st.markdown(f"- {r}")
    if result.get("confirmation_blockers"):
        st.markdown("**الموانع:**")
        for b in result["confirmation_blockers"]:
            st.markdown(f"- ❌ {b}")
    st.caption(f"**ملاحظة التنفيذ:** {result['execution_reason']}")




st.markdown("### ⏱️ Multi-Timeframe")
mtf_cols = st.columns(4)
for idx, (tf, info) in enumerate(result["mtf_details"].items()):
    mtf_cols[idx].metric(tf, info["bias"], f"strength {info['strength']}")
st.info(f"MTF: **{result['mtf_bias']}** — الثقة: **{result['mtf_conf']:.1f}%**")




st.markdown("### 🌍 سياق السوق")
ctx1, ctx2, ctx3 = st.columns(3)
ctx1.metric("DXY", result["details"]["DXY"])
ctx2.metric("Regime", result["details"]["Regime"])
ctx3.metric("Divergence", result["details"]["Divergence"])
st.caption(result["details"].get("USD Context", ""))




# ============================================================
# DECISION REASONS
# ============================================================


st.markdown("### 📝 أسباب القرار")
if result["reasons"]:
    for reason in result["reasons"][:12]:
        st.markdown(f"- {reason}")
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
    l4.metric("TP2/TP3", f"{fmt_price(levels['target2'], selected_pair)} / {fmt_price(levels['target3'], selected_pair)}")
    r1, r2, r3 = st.columns(3)
    r1.metric("RR TP1", f"1:{levels['risk_reward_1']:.2f}")
    r2.metric("RR TP2", f"1:{levels['risk_reward_2']:.2f}")
    r3.metric("RR TP3", f"1:{levels['risk_reward_3']:.2f}")


    lots = calculate_position_size(selected_pair, levels["entry"],
                                    levels["stop_loss"], balance, risk_percent)
    st.success(f"الحجم: **{lots}** — مخاطرة {risk_percent:.2f}%")


    allowed, reason = can_open_trade(confidence)
    if not ks_ok:
        st.error("🛑 Kill Switch مُفعّل — لا يُسمح بصفقات جديدة")
    elif result["execution_status"] != "EXECUTE":
        st.warning(f"⏸️ التنفيذ ممنوع: {result['execution_reason']}")
    elif not allowed:
        st.warning(reason)
    else:
        if st.button("➕ إضافة الصفقة إلى Paper Trade", width="stretch"):
            manager = TradeManager()
            trade = {
                "symbol": symbol, "pair_name": selected_pair,
                "direction": signal, "entry": levels["entry"], "lots": lots,
                "stop_loss": levels["stop_loss"], "target1": levels["target1"],
                "target2": levels["target2"], "target3": levels["target3"],
                "take_profit": levels["target2"], "confidence": confidence,
                "confluence": result["confluence"],
                "weighted_confluence": result["weighted_confluence"],
                "risk_reward": levels["risk_reward_3"],
                "confirmation_score": result["confirmation_score"],
                "trade_grade": result.get("trade_grade", "WAIT"),
                "notes": "; ".join(result["reasons"][:8]),
            }
            tid = manager.add_trade(trade)
            st.session_state.daily_trade_count += 1
            st.success(f"تمت إضافة {tid}.")
            st.rerun()
else:
    st.warning("WAIT — لا توجد صفقة صالحة.")




# ============================================================
# BACKTEST
# ============================================================


st.markdown("---")
st.markdown("### 🔬 Backtest سريع (آخر 200 نقطة)")


bt_col1, bt_col2 = st.columns([2, 1])
with bt_col1:
    if st.button("▶️ تشغيل Backtest على الأصل الحالي", width="stretch"):
        with st.spinner("جاري الاختبار..."):
            st.session_state.backtest_results = quick_backtest(symbol, selected_pair)
        st.rerun()


if st.session_state.backtest_results:
    bt = st.session_state.backtest_results
    if bt.get("error"):
        st.error(f"فشل الاختبار: {bt['error']}")
    else:
        bc1, bc2, bc3, bc4, bc5 = st.columns(5)
        bc1.metric("عدد الصفقات", bt["trades"])
        bc2.metric("نسبة الفوز", f"{bt['win_rate']:.1f}%")
        bc3.metric("Total R", f"{bt['total_R']:.2f}")
        bc4.metric("Expectancy", f"{bt['expectancy']:.2f}R")
        bc5.metric("Profit Factor", f"{bt['profit_factor']:.2f}")


        if bt["expectancy"] >= 0.3 and bt["win_rate"] >= 45:
            st.success("✅ النظام يُظهر Edge إيجابي على هذا الأصل.")
        elif bt["expectancy"] > 0:
            st.warning("⚠️ Edge ضعيف — يُفضل الحذر.")
        else:
            st.error("❌ Edge سلبي — لا يُنصح بالتداول بهذه الإعدادات.")




# ============================================================
# OPEN TRADES
# ============================================================


st.markdown("### 💼 الصفقات المفتوحة")
manager = TradeManager()
if manager.open_trades:
    for trade in manager.open_trades:
        with st.container(border=True):
            st.markdown(f"**{trade['id']} — {trade['pair_name']} — {trade['direction']}**")
            a, b, c, d = st.columns(4)
            a.metric("Entry", fmt_price(trade["entry"], trade["pair_name"]))
            b.metric("SL", fmt_price(trade["stop_loss"], trade["pair_name"]))
            c.metric("TP1", fmt_price(trade["target1"], trade["pair_name"]))
            d.metric("Stage", trade.get("stage", 0))
            if trade["symbol"] == symbol:
                atr = safe_float(df["atr"].iloc[-1], np.nan)
                ev = manager.monitor_trade(trade["id"], current_price, atr=atr)
                if ev is not None:
                    st.warning("تم تحديث الصفقة تلقائياً.")
                    st.rerun()
            close_col, _ = st.columns([1, 2])
            if close_col.button(f"❌ إغلاق {trade['id']}",
                                key=f"close_{trade['id']}", width="stretch"):
                pnl = manager.close_trade(trade["id"], current_price, "manual")
                st.success(f"تم الإغلاق. P&L: {pnl:.2f}")
                st.rerun()
else:
    st.info("لا توجد صفقات مفتوحة.")




# ============================================================
# MANUAL TRADE
# ============================================================


st.markdown("---")
st.markdown("### 🛠️ صفقة يدوية")
if st.button("فتح نموذج الصفقة اليدوية", width="stretch"):
    st.session_state.show_manual = not st.session_state.show_manual


if st.session_state.show_manual:
    with st.form("manual_trade_v2005"):
        direction = st.selectbox("الاتجاه", ["BUY", "SELL"])
        entry = st.number_input("Entry", value=float(current_price), min_value=0.000001)
        stop = st.number_input("Stop Loss",
            value=float(current_price * 0.99 if direction == "BUY" else current_price * 1.01),
            min_value=0.000001)
        t1 = st.number_input("TP1", value=float(current_price * (1.01 if direction == "BUY" else 0.99)), min_value=0.000001)
        t2 = st.number_input("TP2", value=float(current_price * (1.02 if direction == "BUY" else 0.98)), min_value=0.000001)
        t3 = st.number_input("TP3", value=float(current_price * (1.03 if direction == "BUY" else 0.97)), min_value=0.000001)
        manual_lots = st.number_input("Lots (0 = auto)", min_value=0.0, value=0.0, step=0.01)
        submitted = st.form_submit_button("إضافة")
        if submitted:
            valid = ((direction == "BUY" and stop < entry < t1 < t2 < t3)
                     or (direction == "SELL" and t3 < t2 < t1 < entry < stop))
            allowed_m, reason_m = can_open_trade(0)
            if not valid:
                st.error("ترتيب Entry/SL/TP غير صحيح.")
            elif not ks_ok:
                st.error("🛑 Kill Switch مُفعّل.")
            elif not allowed_m:
                st.warning(reason_m)
            else:
                lots = manual_lots if manual_lots > 0 else calculate_position_size(
                    selected_pair, entry, stop, balance, risk_percent)
                if lots <= 0:
                    st.error("تعذر حساب الحجم.")
                else:
                    mgr = TradeManager()
                    tid = mgr.add_trade({
                        "symbol": symbol, "pair_name": selected_pair,
                        "direction": direction, "entry": entry, "lots": lots,
                        "stop_loss": stop, "target1": t1, "target2": t2, "target3": t3,
                        "take_profit": t2, "confidence": 0, "confluence": 0,
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
fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                    vertical_spacing=0.04, row_heights=[0.60, 0.20, 0.20])
fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"],
                              low=df["low"], close=df["close"], name="Price"),
              row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ema20"], name="EMA20"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ema50"], name="EMA50"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["ema200"], name="EMA200"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["vwap"], name="VWAP"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI"), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["vrsi"], name="VRSI"), row=2, col=1)
_chart_profile = profile_for(selected_pair)
fig.add_hline(y=_chart_profile["rsi_ob"], row=2, col=1, line_dash="dash")
fig.add_hline(y=_chart_profile["rsi_os"], row=2, col=1, line_dash="dash")
fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD"), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal"), row=3, col=1)
fig.add_bar(x=df.index, y=df["macd_histogram"], name="Hist", row=3, col=1)


if levels:
    for lvl in ("stop_loss", "target1", "target2", "target3"):
        fig.add_hline(y=levels[lvl], row=1, col=1, line_dash="dot")


fig.update_layout(height=850, template="plotly_dark", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, width="stretch")




# ============================================================
# ECONOMIC CALENDAR DISPLAY
# ============================================================


if st.session_state.economic_events:
    st.markdown("### 📅 الأخبار الاقتصادية")
    rows = [{"الدولة": e.get("country", ""), "الحدث": e.get("event", ""),
             "التأثير": e.get("impact", ""), "التاريخ": e.get("date", ""),
             "الوقت": e.get("time", "")}
            for e in st.session_state.economic_events[:20]]
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")




# ============================================================
# FOOTER
# ============================================================


st.markdown(f"""
<div class="footer-style">
    ▲ BLACK PYRAMID {APP_VERSION} ▲<br>
    Hard Gates + Quality Filters • Structure • Trend • Momentum • Volume • Context • Confirmation • Risk • Edge
</div>
""", unsafe_allow_html=True)
