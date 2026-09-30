# ============================================================
# BLACK PYRAMID v2006.1 — CORRELATION GUARD EDITION
# Institutional Analysis Terminal
#
# v2006.1 CHANGELOG:
#  - NEW: Correlation Guard (30-day rolling)
#  - NEW: Portfolio Risk Manager (open positions tracker)
#  - NEW: Currency Exposure Monitor (per-currency net)
#  - NEW: Correlation Heatmap (visual)
#  - NEW: Auto-block on correlation > 0.85 + same direction
#  - NEW: Max 2 positions per currency (same direction)
#  - NEW: Portfolio tab with live monitoring
#  - KEPT: All v2006.0 features (Fundamentals + Monte Carlo)
# ============================================================

import os
import base64
import logging
import warnings
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
# LOGGING SUPPRESSION
# ============================================================

logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*possibly delisted.*")
warnings.filterwarnings("ignore", message=".*No data found.*")
warnings.filterwarnings("ignore", message=".*Expecting value.*")


# ============================================================
# APP CONFIG
# ============================================================

APP_VERSION = "v2006.1-CorrelationGuard"

A_PLUS_MIN = 85.0
A_MIN = 78.0
B_MIN = 70.0
C_MIN = 62.0

MIN_SIGNAL_GAP = 15
MIN_CONFIDENCE = 72.0
MIN_CONFIRMATION_SCORE = 65.0

PENALTY_MTF_AGAINST = 12.0
PENALTY_RANGE_REGIME = 10.0
PENALTY_WEAK_CANDLE = 8.0
PENALTY_WEEKLY_AGAINST = 6.0

MIN_RR_TP1 = 1.20
MIN_RR_TP2 = 1.80
MIN_RR_TP3 = 2.50

MAX_SOFT_PENALTY = 12.0
SOFT_PENALTY_TOP_N = 4
MAX_CONSECUTIVE_LOSSES = 3

# Correlation Guard
CORRELATION_WINDOW_DAYS = 30
CORRELATION_THRESHOLD = 0.70
CORRELATION_BLOCK_THRESHOLD = 0.85
MAX_SAME_CURRENCY_EXPOSURE = 2

LOGO_CANDIDATES = [
    "file_000000005cb4824697f509df31f2168a.png",
    "logo.png", "assets/logo.png", "static/logo.png",
]

ASSET_PROFILES = {
    "forex": {
        "atr_period": 14, "rsi_period": 14, "rsi_ob": 70, "rsi_os": 30,
        "bb_period": 20, "bb_std": 2.0,
        "atr_sl": 1.50, "atr_trail": 1.10, "swing_order": 3,
        "structure_lookback": 120, "confidence_threshold": 72,
        "min_rr": 1.80, "confirmation_threshold": 65,
    },
    "gold": {
        "atr_period": 14, "rsi_period": 14, "rsi_ob": 80, "rsi_os": 20,
        "bb_period": 20, "bb_std": 2.2,
        "atr_sl": 1.80, "atr_trail": 1.30, "swing_order": 3,
        "structure_lookback": 175, "confidence_threshold": 74,
        "min_rr": 1.80, "confirmation_threshold": 67,
    },
    "crypto": {
        "atr_period": 14, "rsi_period": 14, "rsi_ob": 80, "rsi_os": 20,
        "bb_period": 50, "bb_std": 2.3,
        "atr_sl": 2.00, "atr_trail": 1.50, "swing_order": 4,
        "structure_lookback": 250, "confidence_threshold": 76,
        "min_rr": 1.80, "confirmation_threshold": 70,
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
    "DX-Y.NYB": ["DX=F", "DX-Y.NYB", "UUP"],
    "BTC-USD": ["BTC-USD", "BTC=F"],
    "ETH-USD": ["ETH-USD", "ETH=F"],
    "EURUSD=X": ["EURUSD=X", "EUR=F"],
    "GBPUSD=X": ["GBPUSD=X", "GBP=F"],
    "USDJPY=X": ["USDJPY=X", "JPY=F"],
    "AUDUSD=X": ["AUDUSD=X", "AUD=F"],
    "USDCAD=X": ["USDCAD=X", "CAD=F"],
    "USDCHF=X": ["USDCHF=X", "CHF=F"],
    "NZDUSD=X": ["NZDUSD=X", "NZD=F"],
    "^VIX": ["^VIX", "VIXY", "VXX"],
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

CENTRAL_BANK_RATES = {
    "USD": 5.25, "EUR": 4.00, "GBP": 5.25, "JPY": 0.10,
    "CHF": 1.75, "AUD": 4.35, "NZD": 5.50, "CAD": 4.75,
}

CURRENCY_PAIRS_MAP = {
    "USD": [("EURUSD=X", -1), ("GBPUSD=X", -1), ("AUDUSD=X", -1),
            ("NZDUSD=X", -1), ("USDJPY=X", 1), ("USDCHF=X", 1), ("USDCAD=X", 1)],
    "EUR": [("EURUSD=X", 1), ("EURGBP=X", 1), ("EURJPY=X", 1),
            ("EURCHF=X", 1), ("EURAUD=X", 1), ("EURNZD=X", 1), ("EURCAD=X", 1)],
    "GBP": [("GBPUSD=X", 1), ("EURGBP=X", -1), ("GBPJPY=X", 1),
            ("GBPCHF=X", 1), ("GBPAUD=X", 1), ("GBPNZD=X", 1), ("GBPCAD=X", 1)],
    "JPY": [("USDJPY=X", -1), ("EURJPY=X", -1), ("GBPJPY=X", -1),
            ("AUDJPY=X", -1), ("NZDJPY=X", -1), ("CADJPY=X", -1)],
    "CHF": [("USDCHF=X", -1), ("EURCHF=X", -1), ("GBPCHF=X", -1),
            ("AUDCHF=X", -1), ("NZDCHF=X", -1), ("CADCHF=X", -1)],
    "AUD": [("AUDUSD=X", 1), ("EURAUD=X", -1), ("GBPAUD=X", -1),
            ("AUDJPY=X", 1), ("AUDCHF=X", 1), ("AUDNZD=X", 1), ("AUDCAD=X", 1)],
    "NZD": [("NZDUSD=X", 1), ("EURNZD=X", -1), ("GBPNZD=X", -1),
            ("NZDJPY=X", 1), ("NZDCHF=X", 1), ("AUDNZD=X", -1), ("NZDCAD=X", 1)],
    "CAD": [("USDCAD=X", -1), ("EURCAD=X", -1), ("GBPCAD=X", -1),
            ("AUDCAD=X", -1), ("NZDCAD=X", -1), ("CADJPY=X", 1), ("CADCHF=X", 1)],
}

RISK_OFF_CURRENCIES = {"USD", "JPY", "CHF"}
RISK_ON_CURRENCIES = {"AUD", "NZD", "CAD"}


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


# ============================================================
# SESSION STATE
# ============================================================

def init_state():
    defaults = {
        "selected_pair": "XAU/USD (Gold)",
        "all_signals": None,
        "economic_events": None,
        "analyzing_all": False,
        "analysis_time": None,
        "backtest_results": None,
        "strict_filters": False,
        "show_calendar_today": False,
        "show_session_info": False,
        "show_market_status": False,
        "recent_results": [],
        "trade_journal": [],
        "open_positions": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()


# ============================================================
# HELPERS
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
    if any(x in n for x in ["gold", "silver", "xau", "xag"]): return "gold"
    if any(x in n for x in ["bitcoin", "ethereum", "btc", "eth"]): return "crypto"
    return "forex"


def profile_for(name: str):
    return ASSET_PROFILES[asset_type_from_name(name)]


def get_asset_profile(pair_name):
    name = str(pair_name).upper()
    if "XAU" in name or "GOLD" in name or "SILVER" in name or "XAG" in name: return "gold"
    if any(x in name for x in ("BTC", "ETH", "XRP", "SOL", "ADA")): return "crypto"
    return "forex"


def fmt_price(value, pair_name):
    if value is None or not np.isfinite(safe_float(value)): return "N/A"
    if asset_type_from_name(pair_name) in ("gold", "crypto"):
        return f"${float(value):,.2f}"
    return f"{float(value):.5f}"


def trend_icon(state):
    if state in ("BULLISH", "TREND_BULLISH"): return "🟢"
    if state in ("BEARISH", "TREND_BEARISH"): return "🔴"
    if state in ("NEUTRAL", "RANGE"): return "🟡"
    if state == "COMPRESSION": return "🔵"
    return "⚪"


def img_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def load_logo_b64():
    for p in LOGO_CANDIDATES:
        if Path(p).exists():
            b64 = img_to_base64(p)
            if b64: return b64
    return None


def parse_pair_currencies(pair_name):
    name = str(pair_name).upper()
    if "/" not in name: return "", ""
    parts = name.split("/")
    base = parts[0].strip().split()[0].split("(")[0]
    quote = parts[1].strip().split()[0].split("(")[0] if len(parts) > 1 else ""
    return base, quote


# ============================================================
# KILL SWITCH
# ============================================================

def check_kill_switch():
    recent = st.session_state.get("recent_results", [])[-MAX_CONSECUTIVE_LOSSES:]
    if len(recent) < MAX_CONSECUTIVE_LOSSES:
        return False, len([r for r in recent if r == "LOSS"])
    if all(r == "LOSS" for r in recent):
        return True, MAX_CONSECUTIVE_LOSSES
    consec = 0
    for r in reversed(st.session_state.get("recent_results", [])):
        if r == "LOSS": consec += 1
        else: break
    return consec >= MAX_CONSECUTIVE_LOSSES, consec


def log_trade_result(result, outcome):
    st.session_state.recent_results.append(outcome)
    st.session_state.recent_results = st.session_state.recent_results[-20:]
    st.session_state.trade_journal.append({
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "pair": st.session_state.get("selected_pair", "?"),
        "direction": result.get("signal", "?"),
        "grade": result.get("trade_grade", "?"),
        "confidence": round(result.get("confidence", 0), 1),
        "outcome": outcome,
    })


# ============================================================
# MARKET GUARD
# ============================================================

def is_market_open(pair_name):
    now = datetime.now(timezone.utc)
    asset = asset_type_from_name(pair_name)
    if asset == "crypto": return True, "Crypto 24/7"
    weekday = now.weekday(); hour = now.hour
    if weekday == 4 and hour >= 21: return False, "🚫 السوق مغلق (الجمعة مساءً)"
    if weekday == 5: return False, "🚫 السوق مغلق (السبت)"
    if weekday == 6 and hour < 22: return False, "🚫 السوق لم يفتح بعد (الأحد)"
    return True, "✅ السوق مفتوح"


# ============================================================
# SESSION INFO
# ============================================================

def get_current_session_info():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour; minute = now_utc.minute
    time_str = f"{hour:02d}:{minute:02d} UTC"
    sessions = {
        "Asian": (0, 7, "🌏", "طوكيو/سيدني — سيولة منخفضة"),
        "London": (7, 12, "🇬🇧", "لندن — سيولة عالية"),
        "Overlap": (12, 16, "🔥", "London/NY Overlap — أعلى سيولة"),
        "NY": (16, 21, "🇺🇸", "نيويورك — سيولة عالية"),
        "After-Hours": (21, 24, "🌙", "بعد الإغلاق — سيولة منخفضة"),
    }
    current = "After-Hours"; icon = "🌙"; desc = "بعد الإغلاق"
    for name, (start, end, sicon, sdesc) in sessions.items():
        if start <= hour < end:
            current = name; icon = sicon; desc = sdesc; break
    kz_msg = "خارج Kill Zones"
    for kz_name, (start, end) in KILL_ZONES.items():
        if start <= hour < end:
            kz_msg = f"داخل {kz_name} ✅"; break
    return {"session": current, "icon": icon, "desc": desc,
            "time_utc": time_str, "kill_zone": kz_msg, "hour": hour}


def get_market_status_info(symbol, pair_name):
    try:
        df = get_historical_data(symbol, "3mo", "4h")
        if df is None or len(df) < 60: return None
        profile = profile_for(pair_name)
        x = build_features(df, profile)
        last = x.iloc[-1]
        regime, regime_strength = detect_regime(x)
        vol_ok, vol_msg, vol_label = volatility_regime_filter(x)
        atr_series = x["atr"].dropna()
        atr_now = safe_float(atr_series.iloc[-1], 0)
        atr_mean = safe_float(atr_series.rolling(100).mean().iloc[-1], 0)
        atr_ratio = (atr_now / atr_mean) if atr_mean > 0 else 1.0
        structure = structure_state(x)
        struct_state = structure["state"]
        ema20 = safe_float(last.get("ema20")); ema50 = safe_float(last.get("ema50"))
        ema200 = safe_float(last.get("ema200"))
        if ema20 > ema50 > ema200: trend_align = "متراصف صاعد"; trend_icon_v = "🟢"
        elif ema20 < ema50 < ema200: trend_align = "متراصف هابط"; trend_icon_v = "🔴"
        elif ema20 > ema50: trend_align = "صاعد قصير المدى"; trend_icon_v = "🟡"
        else: trend_align = "هابط قصير المدى"; trend_icon_v = "🟡"
        if atr_ratio > 1.5: vol_state = "مرتفع"; vol_icon = "🔥"
        elif atr_ratio < 0.7: vol_state = "منخفض"; vol_icon = "😴"
        else: vol_state = "طبيعي"; vol_icon = "🌊"
        if regime in ("TREND_BULLISH", "TREND_BEARISH") and vol_label in ("NORMAL", "HIGH"):
            overall = "مواتٍ للتداول ✅"; overall_icon = "✅"
        elif regime == "RANGE": overall = "تذبذب — حذر ⚠️"; overall_icon = "⚠️"
        elif regime == "COMPRESSION": overall = "انضغاط — انتظر الاختراق 🔵"; overall_icon = "🔵"
        elif vol_label == "CHAOS": overall = "تقلب مفرط 🛑"; overall_icon = "🛑"
        else: overall = "غير واضح ⚪"; overall_icon = "⚪"
        return {"regime": regime, "regime_strength": regime_strength,
                "volatility": vol_label, "vol_msg": vol_msg,
                "vol_state": vol_state, "vol_icon": vol_icon,
                "atr_ratio": atr_ratio, "structure": struct_state,
                "trend_align": trend_align, "trend_icon": trend_icon_v,
                "overall": overall, "overall_icon": overall_icon}
    except Exception:
        return None


def get_todays_events(events, pair_name):
    if not events: return []
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    base, quote = parse_pair_currencies(pair_name)
    currencies = {base, quote} if base and quote else {"USD"}
    country_map = {"US": "USD", "EU": "EUR", "GB": "GBP", "JP": "JPY",
                   "CH": "CHF", "AU": "AUD", "NZ": "NZD", "CA": "CAD"}
    todays = []
    for event in events:
        try:
            date_str = str(event.get("date", ""))
            if not date_str.startswith(today_str): continue
            country = str(event.get("country", "")).strip().upper()
            mapped = country_map.get(country, country)
            if mapped not in currencies: continue
            todays.append({"time": str(event.get("time", "")), "country": country,
                           "event": str(event.get("event", "")),
                           "impact": str(event.get("impact", "")).strip().lower()})
        except Exception:
            continue
    todays.sort(key=lambda e: e.get("time", ""))
    return todays


# ============================================================
# DATA LAYER
# ============================================================

def sanitize_yf_symbol(sym: str) -> str:
    s = str(sym).strip().replace("(", "").replace(")", "")
    if "/" in s and s.count("/") == 1:
        parts = s.split("/")
        a, b = parts[0].strip(), parts[1].strip()
        if a.upper() in ("BTC", "ETH", "SOL", "XRP", "ADA"): return f"{a.upper()}-{b.upper()}"
        return f"{a.upper()}{b.upper()}=X"
    return s


def normalize_ohlcv(df, min_rows=50):
    if df is None or df.empty: return None
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
    if any(c not in df.columns for c in required): return None
    if "volume" not in df.columns: df["volume"] = 0.0
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[required + ["volume"]].dropna(subset=required)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df if len(df) >= min_rows else None


@st.cache_data(ttl=60, show_spinner=False)
def get_yfinance(symbol, period="3mo", interval="4h"):
    try:
        safe_symbol = sanitize_yf_symbol(symbol)
        df = yf.download(safe_symbol, period=period, interval=interval,
                         auto_adjust=False, progress=False, threads=False)
        return normalize_ohlcv(df)
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def get_twelve_data(symbol, interval="4h", outputsize=500):
    if not TWELVE_API_KEY: return None
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
    td_symbol = mapping.get(symbol, sanitize_yf_symbol(symbol))
    interval_map = {"15m": "15min", "1h": "1h", "4h": "4h", "1d": "1day"}
    url = "https://api.twelvedata.com/time_series"
    params = {"symbol": td_symbol, "interval": interval_map.get(interval, interval),
              "outputsize": outputsize, "apikey": TWELVE_API_KEY, "format": "JSON"}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "values" not in data: return None
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
        if df is not None and len(df) >= 50: return df
    df = get_yfinance(sanitize_yf_symbol(symbol), period, interval)
    if df is not None and len(df) >= 50: return df
    df = get_twelve_data(symbol, interval, 500)
    if df is not None and len(df) >= 50: return df
    for yf_sym in candidates:
        df = get_yfinance(yf_sym, "1mo", interval)
        if df is not None and len(df) >= 30: return df
    return None


@st.cache_data(ttl=30, show_spinner=False)
def get_spot_price(symbol):
    candidates = YF_SYMBOL_ALTERNATIVES.get(symbol, [symbol])
    for yf_sym in candidates:
        for period, interval in [("5d", "1h"), ("1mo", "1d")]:
            try:
                df = yf.download(sanitize_yf_symbol(yf_sym),
                                 period=period, interval=interval,
                                 auto_adjust=False, progress=False, threads=False)
                df = normalize_ohlcv(df, min_rows=2)
                if df is not None and not df.empty and len(df) >= 2:
                    prev_close = float(df["close"].iloc[-2])
                    last = float(df["close"].iloc[-1])
                    change = ((last - prev_close) / prev_close * 100) if prev_close else 0.0
                    return last, change
            except Exception:
                continue
    try:
        df = get_twelve_data(symbol, "1h", 5)
        if df is not None and len(df) >= 2:
            prev_close = float(df["close"].iloc[-2])
            last = float(df["close"].iloc[-1])
            change = ((last - prev_close) / prev_close * 100) if prev_close else 0.0
            return last, change
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
# FUNDAMENTAL LAYER
# ============================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_currency_strength_matrix():
    strength = {}
    for ccy, pairs in CURRENCY_PAIRS_MAP.items():
        changes = []
        for sym, sign in pairs:
            try:
                df = get_historical_data(sym, "1mo", "1d")
                if df is None or len(df) < 21: continue
                pct = (df["close"].iloc[-1] - df["close"].iloc[-21]) / df["close"].iloc[-21] * 100
                if np.isfinite(pct): changes.append(sign * pct)
            except Exception:
                continue
        strength[ccy] = float(np.mean(changes)) if changes else 0.0
    if not strength: return {}
    max_abs = max(abs(v) for v in strength.values()) or 1.0
    return {k: (v / max_abs) * 100 for k, v in strength.items()}


def get_interest_rate_differential(pair_name):
    base, quote = parse_pair_currencies(pair_name)
    if not base or not quote: return 0.0, "لا يوجد زوج صالح"
    if base not in CENTRAL_BANK_RATES or quote not in CENTRAL_BANK_RATES:
        return 0.0, f"معدلات غير متاحة ({base}/{quote})"
    diff = CENTRAL_BANK_RATES[base] - CENTRAL_BANK_RATES[quote]
    msg = (f"{base}: {CENTRAL_BANK_RATES[base]}% | "
           f"{quote}: {CENTRAL_BANK_RATES[quote]}% | Diff: {diff:+.2f}%")
    return diff, msg


@st.cache_data(ttl=300, show_spinner=False)
def get_risk_sentiment():
    vix_df = get_historical_data("^VIX", "3mo", "1d")
    if vix_df is None or len(vix_df) < 5:
        return {"vix": None, "vix_state": "UNKNOWN", "risk_mode": "NEUTRAL",
                "bias_impact": 0.0, "msg": "VIX غير متاح"}
    vix_now = float(vix_df["close"].iloc[-1])
    vix_avg = float(vix_df["close"].rolling(20).mean().iloc[-1]) if len(vix_df) >= 20 else vix_now
    vix_change = (vix_now - vix_avg) / vix_avg * 100 if vix_avg > 0 else 0
    if vix_now > 25: vix_state = "HIGH FEAR"
    elif vix_now > 20: vix_state = "ELEVATED"
    elif vix_now < 14: vix_state = "COMPLACENT"
    else: vix_state = "NORMAL"
    if vix_now > 25 or vix_change > 15:
        risk_mode = "RISK-OFF"; bias_impact = -1.0
    elif vix_now < 15 and vix_change < -5:
        risk_mode = "RISK-ON"; bias_impact = 1.0
    else:
        risk_mode = "NEUTRAL"; bias_impact = 0.0
    return {"vix": vix_now, "vix_avg": vix_avg, "vix_change": vix_change,
            "vix_state": vix_state, "risk_mode": risk_mode,
            "bias_impact": bias_impact,
            "msg": f"VIX {vix_now:.2f} ({vix_state}) · {risk_mode}"}


def get_fundamental_score(pair_name, ccy_strength=None, rate_diff=0.0, risk=None):
    if ccy_strength is None: ccy_strength = get_currency_strength_matrix()
    if risk is None: risk = get_risk_sentiment()
    base, quote = parse_pair_currencies(pair_name)
    buy_bias = 0.0; sell_bias = 0.0; details = []
    if ccy_strength and base in ccy_strength and quote in ccy_strength:
        base_str = ccy_strength[base]; quote_str = ccy_strength[quote]
        ccy_diff = base_str - quote_str
        details.append({"factor": "Currency Strength", "base_val": base_str,
                        "quote_val": quote_str, "diff": ccy_diff})
        if ccy_diff > 20: buy_bias += 40
        elif ccy_diff > 10: buy_bias += 25
        elif ccy_diff < -20: sell_bias += 40
        elif ccy_diff < -10: sell_bias += 25
    if abs(rate_diff) >= 0.5:
        details.append({"factor": "Rate Differential", "diff": rate_diff})
        if rate_diff > 2.0: buy_bias += 20
        elif rate_diff > 1.0: buy_bias += 12
        elif rate_diff < -2.0: sell_bias += 20
        elif rate_diff < -1.0: sell_bias += 12
    if risk and risk.get("bias_impact", 0) != 0:
        details.append({"factor": "Risk Sentiment", "mode": risk["risk_mode"]})
        if risk["risk_mode"] == "RISK-OFF":
            if base in RISK_OFF_CURRENCIES and quote not in RISK_OFF_CURRENCIES: buy_bias += 15
            elif quote in RISK_OFF_CURRENCIES and base not in RISK_OFF_CURRENCIES: sell_bias += 15
        elif risk["risk_mode"] == "RISK-ON":
            if base in RISK_ON_CURRENCIES and quote not in RISK_ON_CURRENCIES: buy_bias += 15
            elif quote in RISK_ON_CURRENCIES and base not in RISK_ON_CURRENCIES: sell_bias += 15
    return clamp(buy_bias, 0, 100), clamp(sell_bias, 0, 100), details


# ============================================================
# MONTE CARLO
# ============================================================

def monte_carlo_simulation(trades_r, n_sims=1000, n_trades=None):
    if not trades_r or len(trades_r) < 5: return None
    if n_trades is None: n_trades = len(trades_r)
    rng = np.random.default_rng(42)
    final_equities = np.zeros(n_sims)
    max_dds = np.zeros(n_sims)
    for i in range(n_sims):
        sampled = rng.choice(trades_r, size=n_trades, replace=True)
        equity_curve = np.cumsum(sampled)
        peak = np.maximum.accumulate(equity_curve)
        dd = peak - equity_curve
        final_equities[i] = equity_curve[-1]
        max_dds[i] = dd.max() if len(dd) > 0 else 0
    return {"mean_final": float(np.mean(final_equities)),
            "median_final": float(np.median(final_equities)),
            "p5_final": float(np.percentile(final_equities, 5)),
            "p95_final": float(np.percentile(final_equities, 95)),
            "prob_profit": float((final_equities > 0).mean() * 100),
            "mean_dd": float(np.mean(max_dds)),
            "p95_dd": float(np.percentile(max_dds, 95)),
            "worst_dd": float(np.max(max_dds)),
            "n_sims": n_sims, "n_trades": n_trades}


# ============================================================
# CORRELATION GUARD
# ============================================================

@st.cache_data(ttl=600, show_spinner=False)
def get_pair_correlation(symbol1, symbol2, days=30):
    try:
        df1 = get_historical_data(symbol1, "3mo", "1d")
        df2 = get_historical_data(symbol2, "3mo", "1d")
        if df1 is None or df2 is None: return None
        s1 = df1["close"].pct_change().dropna()
        s2 = df2["close"].pct_change().dropna()
        aligned = pd.concat([s1, s2], axis=1, join="inner").dropna()
        if len(aligned) < days: return None
        corr = float(aligned.iloc[-days:, 0].corr(aligned.iloc[-days:, 1]))
        return corr if np.isfinite(corr) else None
    except Exception:
        return None


@st.cache_data(ttl=900, show_spinner=False)
def build_correlation_matrix(symbols_tuple):
    symbols = list(symbols_tuple)
    n = len(symbols)
    matrix = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            corr = get_pair_correlation(symbols[i], symbols[j])
            if corr is not None:
                matrix[i, j] = corr; matrix[j, i] = corr
    return matrix, symbols


def check_portfolio_conflict(symbol, direction, pair_name, open_positions):
    result = {"blocked": False, "warnings": [], "max_corr": 0.0,
              "conflicting_pair": None, "same_currency_count": 0}
    if not open_positions: return result
    base_new, quote_new = parse_pair_currencies(pair_name)
    for pos in open_positions:
        if pos["symbol"] == symbol: continue
        corr = get_pair_correlation(symbol, pos["symbol"])
        if corr is None: continue
        abs_corr = abs(corr)
        if abs_corr > result["max_corr"]:
            result["max_corr"] = abs_corr
            result["conflicting_pair"] = pos["pair"]
        if abs_corr >= CORRELATION_BLOCK_THRESHOLD and pos["direction"] == direction:
            result["blocked"] = True
            result["warnings"].append(
                f"🚫 ارتباط {abs_corr:.0%} مع {pos['pair']} ({pos['direction']}) — نفس الاتجاه")
        elif abs_corr >= CORRELATION_THRESHOLD and pos["direction"] == direction:
            result["warnings"].append(
                f"⚠️ ارتباط {abs_corr:.0%} مع {pos['pair']} ({pos['direction']})")
        if abs_corr >= CORRELATION_THRESHOLD and pos["direction"] != direction:
            result["warnings"].append(
                f"ℹ️ تحوط طبيعي مع {pos['pair']} (ارتباط {abs_corr:.0%})")
    for ccy in [base_new, quote_new]:
        if not ccy: continue
        count = 0
        for pos in open_positions:
            pb, pq = parse_pair_currencies(pos["pair"])
            if ccy == pb and pos["direction"] == direction: count += 1
            elif ccy == pq and pos["direction"] == direction: count += 1
        if count >= MAX_SAME_CURRENCY_EXPOSURE:
            result["blocked"] = True
            result["warnings"].append(f"🚫 {count} صفقات {direction} على {ccy} — تعرض مفرط")
        elif count == MAX_SAME_CURRENCY_EXPOSURE - 1:
            result["warnings"].append(f"⚠️ {count} صفقة {direction} على {ccy} — قرب الحد")
        result["same_currency_count"] = max(result["same_currency_count"], count)
    return result


def add_open_position(result, pair_name, symbol, lot_size=None, notes=""):
    if result.get("signal") not in ("BUY", "SELL"): return False
    if "open_positions" not in st.session_state:
        st.session_state.open_positions = []
    levels = result.get("levels") or {}
    st.session_state.open_positions.append({
        "id": len(st.session_state.open_positions) + 1,
        "pair": pair_name, "symbol": symbol,
        "direction": result["signal"],
        "entry": levels.get("entry"), "stop_loss": levels.get("stop_loss"),
        "target1": levels.get("target1"), "target2": levels.get("target2"),
        "target3": levels.get("target3"),
        "grade": result.get("trade_grade", "?"),
        "confidence": result.get("confidence", 0),
        "lot_size": lot_size,
        "opened_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "notes": notes, "status": "OPEN",
    })
    return True


def close_open_position(pos_id):
    if "open_positions" not in st.session_state: return False
    st.session_state.open_positions = [
        p for p in st.session_state.open_positions if p["id"] != pos_id]
    return True


def get_portfolio_exposure():
    exposure = {}
    for pos in st.session_state.get("open_positions", []):
        base, quote = parse_pair_currencies(pos["pair"])
        direction = pos["direction"]
        size = pos.get("lot_size") or 1.0
        if base not in exposure:
            exposure[base] = {"long": 0.0, "short": 0.0, "net": 0.0, "count": 0}
        if quote not in exposure:
            exposure[quote] = {"long": 0.0, "short": 0.0, "net": 0.0, "count": 0}
        if direction == "BUY":
            exposure[base]["long"] += size; exposure[quote]["short"] += size
            exposure[base]["net"] += size; exposure[quote]["net"] -= size
        else:
            exposure[base]["short"] += size; exposure[quote]["long"] += size
            exposure[base]["net"] -= size; exposure[quote]["net"] += size
        exposure[base]["count"] += 1; exposure[quote]["count"] += 1
    return exposure


# ============================================================
# INDICATORS
# ============================================================

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(avg_loss > 0, 100.0); rsi = rsi.where(avg_gain > 0, 0.0)
    return rsi.fillna(50).clip(0, 100)


def calc_atr(df, period=14):
    prev_close = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()


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


def calc_chaikin(df, period=21):
    hl = (df["high"] - df["low"]).replace(0, np.nan)
    multiplier = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / hl
    money_volume = multiplier.fillna(0) * df["volume"]
    return (money_volume.rolling(period).sum()
            / df["volume"].rolling(period).sum().replace(0, np.nan)).fillna(0)


def calc_rolling_vwap(df, period=20):
    tp = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].clip(lower=0); pv = tp * vol
    cum_pv = pv.rolling(period, min_periods=period).sum()
    cum_vol = vol.rolling(period, min_periods=period).sum()
    vwap = cum_pv / cum_vol.replace(0, np.nan)
    fallback = tp.rolling(period, min_periods=period).mean()
    return vwap.fillna(fallback)


def calc_session_vwap(df):
    work = df.copy()
    if work.index.tz is None: dates = work.index.normalize()
    else: dates = work.index.tz_convert("UTC").normalize()
    tp = (work["high"] + work["low"] + work["close"]) / 3
    pv = tp * work["volume"].clip(lower=0)
    cum_pv = pv.groupby(dates).cumsum()
    cum_vol = work["volume"].clip(lower=0).groupby(dates).cumsum()
    vwap = cum_pv / cum_vol.replace(0, np.nan)
    fallback = tp.groupby(dates).expanding().mean().reset_index(level=0, drop=True)
    return vwap.fillna(fallback)


# ============================================================
# SWING / STRUCTURE
# ============================================================

def find_confirmed_swings(df, order=3):
    out = df.copy(); window = 2 * order + 1
    if len(out) < window:
        out["swing_high"] = False; out["swing_low"] = False
        return out
    roll_max = out["high"].rolling(window, min_periods=window).max()
    roll_min = out["low"].rolling(window, min_periods=window).min()
    is_max = (out["high"] >= roll_max - 1e-12) & roll_max.notna()
    is_min = (out["low"] <= roll_min + 1e-12) & roll_min.notna()
    out["swing_high"] = is_max.shift(order).fillna(False).astype(bool)
    out["swing_low"] = is_min.shift(order).fillna(False).astype(bool)
    return out


def get_last_two_swings(df, kind="high"):
    col = "swing_high" if kind == "high" else "swing_low"
    if col not in df.columns: return None
    points = df.index[df[col]].tolist()
    values = df.loc[points, "high" if kind == "high" else "low"].tolist()
    if len(points) < 2: return None
    return [(points[-2], float(values[-2])), (points[-1], float(values[-1]))]


def structure_state(df):
    highs = get_last_two_swings(df, "high"); lows = get_last_two_swings(df, "low")
    bullish = False; bearish = False; state = "RANGE"
    if highs and lows:
        hh = highs[-1][1] > highs[-2][1]; hl = lows[-1][1] > lows[-2][1]
        lh = highs[-1][1] < highs[-2][1]; ll = lows[-1][1] < lows[-2][1]
        if hh and hl: bullish = True; state = "BULLISH"
        elif lh and ll: bearish = True; state = "BEARISH"
    return {"state": state, "bullish": bullish, "bearish": bearish,
            "highs": highs, "lows": lows}


def detect_bos_mss(df):
    out = df.copy(); n = len(out)
    bos_bull = np.zeros(n, dtype=bool); bos_bear = np.zeros(n, dtype=bool)
    mss_bull = np.zeros(n, dtype=bool); mss_bear = np.zeros(n, dtype=bool)
    if n == 0:
        out["bos_bullish"] = bos_bull; out["bos_bearish"] = bos_bear
        out["mss_bullish"] = mss_bull; out["mss_bearish"] = mss_bear
        return out
    sh_arr = out["swing_high"].values; sl_arr = out["swing_low"].values
    high_arr = out["high"].values; low_arr = out["low"].values
    close_arr = out["close"].values
    state = "RANGE"; last_high = np.nan; last_low = np.nan
    for i in range(n):
        if i > 0:
            if sh_arr[i-1]: last_high = high_arr[i-1]
            if sl_arr[i-1]: last_low = low_arr[i-1]
        if i < 10: continue
        c = close_arr[i]
        if np.isfinite(last_high) and c > last_high:
            bos_bull[i] = True
            if state == "BEARISH": mss_bull[i] = True
            state = "BULLISH"; last_high = np.nan
        elif np.isfinite(last_low) and c < last_low:
            bos_bear[i] = True
            if state == "BULLISH": mss_bear[i] = True
            state = "BEARISH"; last_low = np.nan
    out["bos_bullish"] = bos_bull; out["bos_bearish"] = bos_bear
    out["mss_bullish"] = mss_bull; out["mss_bearish"] = mss_bear
    return out


def detect_liquidity_sweeps(df, tolerance_atr=0.10):
    out = df.copy(); tol = out["atr"] * tolerance_atr
    prev_high = out["high"].rolling(3).max().shift(1)
    prev_low = out["low"].rolling(3).min().shift(1)
    out["liquidity_sweep_bearish"] = ((out["high"] > prev_high + tol) & (out["close"] < prev_high)).fillna(False)
    out["liquidity_sweep_bullish"] = ((out["low"] < prev_low - tol) & (out["close"] > prev_low)).fillna(False)
    return out


def detect_fvg(df):
    out = df.copy()
    bull_fvg = (out["low"] > out["high"].shift(2)).fillna(False)
    bear_fvg = (out["high"] < out["low"].shift(2)).fillna(False)
    out["fvg_bullish"] = bull_fvg; out["fvg_bearish"] = bear_fvg
    out["fvg_bull_low"] = out["high"].shift(2).where(bull_fvg, np.nan)
    out["fvg_bull_high"] = out["low"].where(bull_fvg, np.nan)
    out["fvg_bear_low"] = out["high"].where(bear_fvg, np.nan)
    out["fvg_bear_high"] = out["low"].shift(2).where(bear_fvg, np.nan)
    return out


def detect_order_blocks(df):
    out = df.copy()
    body = (out["close"] - out["open"]).abs()
    strong = body >= 1.20 * out["atr"]
    prev_open = out["open"].shift(1); prev_close = out["close"].shift(1)
    prev_high = out["high"].shift(1); prev_low = out["low"].shift(1)
    bull_ob = (strong & (prev_close < prev_open) & (out["close"] > prev_high)).fillna(False)
    bear_ob = (strong & (prev_close > prev_open) & (out["close"] < prev_low)).fillna(False)
    out["order_block_bullish"] = bull_ob; out["order_block_bearish"] = bear_ob
    ob_valid = bull_ob | bear_ob
    out["ob_low"] = prev_low.where(ob_valid, np.nan)
    out["ob_high"] = prev_high.where(ob_valid, np.nan)
    return out


def add_premium_discount(df, lookback=50):
    out = df.copy()
    swing_high = out["high"].rolling(lookback).max().shift(1)
    swing_low = out["low"].rolling(lookback).min().shift(1)
    mid = (swing_high + swing_low) / 2
    out["range_high"] = swing_high; out["range_low"] = swing_low
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
    highs = out.index[out["swing_high"]]; lows = out.index[out["swing_low"]]
    out["bsl"] = np.nan; out["ssl"] = np.nan
    if len(highs): out["bsl"] = float(out.loc[highs[-1], "high"])
    if len(lows): out["ssl"] = float(out.loc[lows[-1], "low"])
    return out


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


def build_features(df, profile, use_rolling_vwap=True):
    out = df.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["rsi"] = calc_rsi(out["close"], profile["rsi_period"])
    out["atr"] = calc_atr(out, profile["atr_period"])
    out["macd"], out["macd_signal"], out["macd_histogram"] = calc_macd(out["close"], 12, 26, 9)
    out["bb_upper"], out["bb_mid"], out["bb_lower"] = calc_bollinger(
        out["close"], profile["bb_period"], profile["bb_std"])
    out["chaikin_mf"] = calc_chaikin(out, 21)
    try: bar_hours = (out.index[-1] - out.index[-2]).total_seconds() / 3600
    except Exception: bar_hours = 4.0
    if use_rolling_vwap and bar_hours >= 3.5:
        out["vwap"] = calc_rolling_vwap(out, 20); out["vwap_type"] = "rolling"
    else:
        out["vwap"] = calc_session_vwap(out); out["vwap_type"] = "session"
    out = analyze_smc(out, profile)
    return out


def timeframe_bias(df, pair_name=None):
    if df is None or len(df) < 80: return "NEUTRAL", 0
    x = build_features(df, profile_for(pair_name or ""))
    last = x.iloc[-1]; bull = bear = 0.0
    if last["ema20"] > last["ema50"]: bull += 1
    elif last["ema20"] < last["ema50"]: bear += 1
    if last["ema50"] > last["ema200"]: bull += 1
    elif last["ema50"] < last["ema200"]: bear += 1
    if last["macd_histogram"] > 0: bull += 1
    elif last["macd_histogram"] < 0: bear += 1
    rsi = safe_float(last.get("rsi"), 50)
    if rsi >= 55: bull += 1
    elif rsi <= 45: bear += 1
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


@st.cache_data(ttl=300, show_spinner=False)
def get_dxy_context():
    df = get_historical_data("DX-Y.NYB", "6mo", "4h")
    if df is None: return "NEUTRAL", 50.0, {}
    x = build_features(df, ASSET_PROFILES["forex"])
    last = x.iloc[-1]; bull = bear = 0
    if last["close"] > last["ema50"]: bull += 1
    elif last["close"] < last["ema50"]: bear += 1
    if last["macd"] > last["macd_signal"]: bull += 1
    elif last["macd"] < last["macd_signal"]: bear += 1
    if last["rsi"] > 55: bull += 1
    elif last["rsi"] < 45: bear += 1
    if bull > bear: return "BULLISH", 55 + 10 * bull, {"trend": "USD strength"}
    if bear > bull: return "BEARISH", 55 + 10 * bear, {"trend": "USD weakness"}
    return "NEUTRAL", 50, {"trend": "USD neutral"}


def get_pair_usd_context(pair_name, dxy_bias="NEUTRAL"):
    base, quote = parse_pair_currencies(pair_name)
    if not base or not quote: return 0.0, "لا تأثير مباشر"
    if "USD" not in (base, quote): return 0.0, "تأثير غير مباشر"
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


@st.cache_data(ttl=180, show_spinner=False)
def htf_zone_filter(symbol, direction, profile_key):
    try:
        df_d1 = get_historical_data(symbol, "1y", "1d")
        if df_d1 is None or len(df_d1) < 60: return True, "HTF غير متاح — مسموح", "UNKNOWN"
        profile = ASSET_PROFILES[profile_key]
        x = build_features(df_d1, profile)
        last = x.iloc[-1]
        in_premium = safe_bool(last.get("in_premium"))
        in_discount = safe_bool(last.get("in_discount"))
        if direction == "BUY" and in_premium: return False, "BUY مرفوض: HTF في Premium", "PREMIUM"
        if direction == "SELL" and in_discount: return False, "SELL مرفوض: HTF في Discount", "DISCOUNT"
        if direction == "BUY" and in_discount: return True, "BUY في Discount HTF ✅", "DISCOUNT"
        if direction == "SELL" and in_premium: return True, "SELL في Premium HTF ✅", "PREMIUM"
        return True, "HTF محايد", "MID"
    except Exception:
        return True, "HTF فشل التحميل", "UNKNOWN"


@st.cache_data(ttl=180, show_spinner=False)
def ltf_entry_trigger(symbol, direction, profile_key):
    try:
        df = get_historical_data(symbol, "3mo", "1h")
        if df is None or len(df) < 60: return True, "LTF غير متاح — مسموح"
        profile = ASSET_PROFILES[profile_key]
        x = build_features(df, profile)
        if len(x) < 3: return True, "LTF قصير"
        last = x.iloc[-1]; prev = x.iloc[-2]
        if direction == "BUY":
            if safe_bool(last.get("bos_bullish")): return True, "BOS صاعد 1H ✅"
            if safe_bool(last.get("liquidity_sweep_bullish")): return True, "Liquidity Sweep صاعد 1H ✅"
            if (last["close"] > last["open"] and prev["close"] < prev["open"]
                and safe_bool(last.get("fvg_bullish"))):
                return True, "Engulfing + FVG 1H ✅"
        if direction == "SELL":
            if safe_bool(last.get("bos_bearish")): return True, "BOS هابط 1H ✅"
            if safe_bool(last.get("liquidity_sweep_bearish")): return True, "Liquidity Sweep هابط 1H ✅"
            if (last["close"] < last["open"] and prev["close"] > prev["open"]
                and safe_bool(last.get("fvg_bearish"))):
                return True, "Engulfing + FVG 1H ✅"
        return False, "لا يوجد trigger على 1H"
    except Exception:
        return True, "LTF فشل — مسموح"


def session_filter(pair_name, strict=True):
    now_utc = datetime.now(timezone.utc).hour
    london_open = 7 <= now_utc <= 16; ny_open = 12 <= now_utc <= 21
    overlap = 12 <= now_utc <= 16; asian = 0 <= now_utc <= 7
    asset = asset_type_from_name(pair_name)
    if asset == "crypto":
        if overlap: return True, "NY/London Overlap (أعلى سيولة)", "OVERLAP"
        return True, "Crypto يعمل 24/7", "CRYPTO"
    if asset == "gold":
        if overlap: return True, "Overlap مثالي للذهب ✅", "OVERLAP"
        if london_open or ny_open: return True, "جلسة نشطة للذهب ✅", "ACTIVE"
        if strict: return False, "خارج جلسات الذهب النشطة", "DEAD"
        return True, "خارج الجلسات (غير مشدّد)", "OFF_HOURS"
    if strict and asian: return False, "الجلسة الآسيوية — سيولة منخفضة", "ASIAN"
    if overlap: return True, "Overlap مثالي ✅", "OVERLAP"
    if london_open or ny_open: return True, "جلسة نشطة ✅", "ACTIVE"
    if strict: return False, "خارج الجلسات النشطة", "DEAD"
    return True, "خارج الجلسات (غير مشدّد)", "OFF_HOURS"


def volatility_regime_filter(df):
    atr = df["atr"].dropna() if "atr" in df.columns else pd.Series()
    if len(atr) < 100: return True, "بيانات غير كافية", "NORMAL"
    current_atr = atr.iloc[-1]
    atr_mean = atr.rolling(100).mean().iloc[-1]
    atr_std = atr.rolling(100).std().iloc[-1]
    if not np.isfinite(atr_std) or atr_std == 0: return True, "ATR ثابت", "NORMAL"
    z = (current_atr - atr_mean) / atr_std
    if z < -1.0: return False, f"سوق ميت (ATR Z={z:.1f})", "DEAD"
    if z > 2.5: return False, f"تقلب مفرط (ATR Z={z:.1f})", "CHAOS"
    if 1.5 < z <= 2.5: return True, f"تقلب مرتفع (Z={z:.1f})", "HIGH"
    if -1.0 <= z < -0.3: return True, f"تقلب منخفض (Z={z:.1f})", "LOW"
    return True, f"تقلب طبيعي (Z={z:.1f})", "NORMAL"


def weighted_confluence(pillar_data, direction):
    weights = {"structure": 30, "trend": 20, "context": 20, "momentum": 15, "volume": 15}
    total = 0.0
    for pillar, w in weights.items():
        raw = safe_float(pillar_data.get(direction, {}).get(pillar), 0)
        s = clamp(raw, 0, 100)
        if s >= 70: total += w * 1.0
        elif s >= 50: total += w * 0.5
        elif s < 30: total -= w * 0.3
    return clamp(total, 0, 100)


def compute_soft_penalty(penalty_items, strict=False):
    if not penalty_items: return 0.0, []
    if not strict: return 0.0, []
    sorted_items = sorted([item for item in penalty_items if item[1] > 0],
                          key=lambda x: x[1], reverse=True)[:SOFT_PENALTY_TOP_N]
    weights = [1.0, 0.5, 0.25, 0.15]
    total = sum(p * w for (_, p), w in zip(sorted_items, weights))
    return min(total, MAX_SOFT_PENALTY), sorted_items


def news_time_block(events, pair_name, window_minutes=45):
    if not events: return False, ""
    now = datetime.now(timezone.utc)
    base, quote = parse_pair_currencies(pair_name)
    currencies = {base, quote} if base and quote else {"USD"}
    country_map = {"US": "USD", "EU": "EUR", "GB": "GBP", "JP": "JPY",
                   "CH": "CHF", "AU": "AUD", "NZ": "NZD", "CA": "CAD"}
    for event in events:
        impact = str(event.get("impact", "")).strip().lower()
        if impact not in ("high", "3", "high impact"): continue
        country = str(event.get("country", "")).strip().upper()
        mapped = country_map.get(country, country)
        if mapped not in currencies: continue
        try:
            date_str = event.get("date", "")
            if not date_str: continue
            event_time = pd.to_datetime(date_str)
            if event_time.tzinfo is None: event_time = event_time.tz_localize("UTC")
            if abs((event_time - now).total_seconds()) / 60 < window_minutes:
                return True, f"خبر {event.get('event')} خلال {window_minutes}د"
        except Exception:
            continue
    return False, ""


def displacement_check(df, direction):
    if len(df) < 2: return False, "بيانات غير كافية"
    last = df.iloc[-1]
    atr = safe_float(last.get("atr"), 0)
    if atr <= 0: return False, "ATR غير صالح"
    body = abs(last["close"] - last["open"])
    if body < 1.5 * atr: return False, f"لا Displacement ({body/atr:.1f}x)"
    if direction == "BUY" and last["close"] < last["open"]: return False, "Displacement ضد BUY"
    if direction == "SELL" and last["close"] > last["open"]: return False, "Displacement ضد SELL"
    return True, f"Displacement {body/atr:.1f}x ATR ✅"


def in_kill_zone(asset_type):
    hour = datetime.now(timezone.utc).hour
    if asset_type == "crypto": return True, "Crypto 24/7"
    for name, (start, end) in KILL_ZONES.items():
        if start <= hour < end: return True, f"{name} ✅"
    return False, "خارج Kill Zones"


def ote_filter(df, direction):
    swings_h = get_last_two_swings(df, "high")
    swings_l = get_last_two_swings(df, "low")
    if not swings_h or not swings_l: return True, "OTE غير متاح — مسموح"
    swing_h = swings_h[-1][1]; swing_l = swings_l[-1][1]
    current = df["close"].iloc[-1]; leg = swing_h - swing_l
    if leg <= 0: return True, "موجة غير صالحة"
    if direction == "BUY":
        retr = (swing_h - current) / leg
        if 0.55 <= retr <= 0.85: return True, f"OTE صاعد {retr*100:.0f}% ✅"
        return False, f"خارج OTE ({retr*100:.0f}%)"
    else:
        retr = (current - swing_l) / leg
        if 0.55 <= retr <= 0.85: return True, f"OTE هابط {retr*100:.0f}% ✅"
        return False, f"خارج OTE ({retr*100:.0f}%)"


@st.cache_data(ttl=600, show_spinner=False)
def weekly_bias(symbol, pair_name):
    df = get_historical_data(symbol, "2y", "1wk")
    if df is None or len(df) < 30: return "NEUTRAL", 0
    try:
        profile = profile_for(pair_name)
        x = build_features(df, profile)
        if len(x) < 5: return "NEUTRAL", 0
        last = x.iloc[-1]; bull = bear = 0
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


PILLAR_WEIGHTS = {"structure": 0.28, "trend": 0.18, "momentum": 0.14,
                  "volume": 0.14, "context": 0.26}


def directional_score(df, pair_name, symbol, dxy_bias=None, gold_corr=None,
                     ccy_strength=None, rate_diff=0.0, risk=None):
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
    if (last["close"] > last["ema20"] > last["ema50"] > last["ema200"]):
        scores["BUY"]["trend"] += 20
    elif (last["close"] < last["ema20"] < last["ema50"] < last["ema200"]):
        scores["SELL"]["trend"] += 20

    rsi = safe_float(last["rsi"], 50)
    if rsi >= 55: scores["BUY"]["momentum"] += 45
    elif rsi <= 45: scores["SELL"]["momentum"] += 45
    if last["macd"] > last["macd_signal"] and last["macd_histogram"] > 0:
        scores["BUY"]["momentum"] += 45
    elif last["macd"] < last["macd_signal"] and last["macd_histogram"] < 0:
        scores["SELL"]["momentum"] += 45
    if last["chaikin_mf"] > 0.10: scores["BUY"]["momentum"] += 10
    elif last["chaikin_mf"] < -0.10: scores["SELL"]["momentum"] += 10

    if last["close"] > last["vwap"]: scores["BUY"]["volume"] += 45
    elif last["close"] < last["vwap"]: scores["SELL"]["volume"] += 45
    if last["chaikin_mf"] > 0: scores["BUY"]["volume"] += 35
    elif last["chaikin_mf"] < 0: scores["SELL"]["volume"] += 35
    va = df["volume"].rolling(20).mean().iloc[-1]
    if va and np.isfinite(va) and last["volume"] > va:
        if last["close"] > last["open"]: scores["BUY"]["volume"] += 20
        elif last["close"] < last["open"]: scores["SELL"]["volume"] += 20

    if dxy_bias is None: dxy_bias, _, _ = get_dxy_context()
    usd_impact, usd_msg = get_pair_usd_context(pair_name, dxy_bias=dxy_bias)
    if usd_impact > 0: scores["BUY"]["context"] += 25; reasons.append("DXY يدعم")
    elif usd_impact < 0: scores["SELL"]["context"] += 25; reasons.append("DXY يدعم")

    if "Gold" in pair_name or "XAU" in pair_name.upper():
        if gold_corr is None: gold_corr = get_gold_dxy_correlation()
        if gold_corr is not None:
            if gold_corr <= -0.50 and dxy_bias == "BEARISH": scores["BUY"]["context"] += 15
            elif gold_corr <= -0.50 and dxy_bias == "BULLISH": scores["SELL"]["context"] += 15

    fund_buy, fund_sell, fund_details = get_fundamental_score(
        pair_name, ccy_strength=ccy_strength, rate_diff=rate_diff, risk=risk)
    scores["BUY"]["context"] += fund_buy * 0.6
    scores["SELL"]["context"] += fund_sell * 0.6
    if fund_buy > 20: reasons.append("أساسي يدعم BUY")
    if fund_sell > 20: reasons.append("أساسي يدعم SELL")

    regime, _ = detect_regime(df)
    if regime == "TREND_BULLISH": scores["BUY"]["context"] += 15
    elif regime == "TREND_BEARISH": scores["SELL"]["context"] += 15

    tb = ts = 0.0
    for p, w in PILLAR_WEIGHTS.items():
        scores["BUY"][p] = clamp(scores["BUY"][p], 0, 100)
        scores["SELL"][p] = clamp(scores["SELL"][p], 0, 100)
        tb += scores["BUY"][p] * w; ts += scores["SELL"][p] * w
    div = detect_divergence(df)
    if div == "BULLISH": tb += 3
    elif div == "BEARISH": ts += 3
    return {"buy": clamp(tb, 0, 100), "sell": clamp(ts, 0, 100),
            "pillars": scores, "reasons": reasons,
            "dxy_bias": dxy_bias, "usd_msg": usd_msg,
            "regime": regime, "divergence": div,
            "fund_details": fund_details,
            "fund_buy": fund_buy, "fund_sell": fund_sell}


def confirmation_gate(df, direction, pillar_scores, regime,
                      mtf_bias="NEUTRAL", mtf_conf=50.0, profile=None,
                      weekly_bias_val="NEUTRAL"):
    if df is None or len(df) < 30:
        return False, 0.0, ["بيانات غير كافية"], ["DATA"]
    profile = profile or ASSET_PROFILES["forex"]
    last = df.iloc[-1]; score = 0.0; reasons = []; blockers = []
    if (direction == "BUY" and regime == "TREND_BULLISH") or \
       (direction == "SELL" and regime == "TREND_BEARISH"):
        score += 20; reasons.append("Regime متوافق")
    elif regime == "RANGE": score += 8; reasons.append("Range")
    elif regime == "COMPRESSION": score += 5; reasons.append("Compression")
    else: blockers.append("Regime غير متوافق")
    if (direction == "BUY" and mtf_bias == "BULLISH") or \
       (direction == "SELL" and mtf_bias == "BEARISH"):
        score += 25 * min(mtf_conf / 95, 1); reasons.append("MTF متوافق")
    elif mtf_bias != "NEUTRAL": blockers.append("MTF ضد الاتجاه")
    if (direction == "BUY" and weekly_bias_val == "BULLISH") or \
       (direction == "SELL" and weekly_bias_val == "BEARISH"):
        score += 15; reasons.append("Weekly متوافق")
    elif weekly_bias_val != "NEUTRAL": blockers.append("Weekly Bias ضد الاتجاه")
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
    if smc_score >= 40: score += 15; reasons.extend(smc_reasons[:3])
    elif smc_score < 20: blockers.append("SMC ضعيف")
    own = sum(float(v) for v in pillar_scores.get(direction, {}).values())
    opp = sum(float(v) for v in pillar_scores.get(
        "SELL" if direction == "BUY" else "BUY", {}).values())
    if own < 180: blockers.append("الأدلة ضعيفة")
    if opp > own * 0.85: blockers.append("تعارض قوي Pillars")
    else: score += 5
    hard = any(x in blockers for x in ("MTF ضد الاتجاه", "Regime غير متوافق", "Weekly Bias ضد الاتجاه"))
    threshold = profile.get("confirmation_threshold", 65)
    ok = score >= threshold and not hard and len(blockers) <= 2
    return ok, clamp(score, 0, 100), reasons, blockers


def latest_structure_levels(df):
    lows = df.index[df["swing_low"]].tolist(); highs = df.index[df["swing_high"]].tolist()
    sl = float(df.loc[lows[-1], "low"]) if lows else np.nan
    sh = float(df.loc[highs[-1], "high"]) if highs else np.nan
    return sl, sh


def calc_pivot_points(df):
    if len(df) < 2: return None
    last = df.iloc[-1]
    h = float(last["high"]); l = float(last["low"]); c = float(last["close"])
    p = (h + l + c) / 3.0; rng = h - l
    if rng <= 0: return None
    return {"pivot": p, "range": rng,
            "r1": 2*p-l, "r2": p+rng, "r3": h+2*(p-l),
            "s1": 2*p-h, "s2": p-rng, "s3": l-2*(h-p),
            "fib_r1": p+0.382*rng, "fib_r2": p+0.618*rng, "fib_r3": p+1.000*rng,
            "fib_s1": p-0.382*rng, "fib_s2": p-0.618*rng, "fib_s3": p-1.000*rng,
            "high": h, "low": l, "close": c}


def find_impulse_leg(df, direction, lookback=120):
    work = df.iloc[-lookback:].copy() if len(df) > lookback else df.copy()
    if len(work) < 20: return None
    if direction == "BUY":
        pos = int(work["low"].values.argmin())
        if pos >= len(work) - 5:
            sub = work.iloc[:len(work)-5]
            if len(sub) < 10: return None
            work = sub; pos = int(work["low"].values.argmin())
        start = float(work["low"].iloc[pos]); after = work.iloc[pos:]
        if len(after) < 3: return None
        end = float(after["high"].iloc[int(after["high"].values.argmax())])
        if end <= start: return None
        return {"start": start, "end": end, "leg": end-start, "direction": "BUY"}
    else:
        pos = int(work["high"].values.argmax())
        if pos >= len(work) - 5:
            sub = work.iloc[:len(work)-5]
            if len(sub) < 10: return None
            work = sub; pos = int(work["high"].values.argmax())
        start = float(work["high"].iloc[pos]); after = work.iloc[pos:]
        if len(after) < 3: return None
        end = float(after["low"].iloc[int(after["low"].values.argmin())])
        if end >= start: return None
        return {"start": start, "end": end, "leg": start-end, "direction": "SELL"}


def fib_levels_from_impulse(impulse):
    if not impulse: return None
    s, e, leg = impulse["start"], impulse["end"], impulse["leg"]
    d = impulse["direction"]
    def r(pct): return e - pct * leg if d == "BUY" else e + pct * leg
    def x(mult): return s + mult * leg if d == "BUY" else s - mult * leg
    return {"retracement": {"0.382": r(0.382), "0.500": r(0.500),
                            "0.618": r(0.618), "0.786": r(0.786)},
            "extension": {"1.000": e, "1.272": x(1.272), "1.618": x(1.618),
                          "2.000": x(2.000), "2.618": x(2.618)}}


def collect_sr_levels(df, lookback=200):
    levels = []
    work = df.iloc[-lookback:] if len(df) > lookback else df
    if "swing_high" in work.columns:
        for idx in work.index[work["swing_high"]][-5:]:
            levels.append(float(work.loc[idx, "high"]))
    if "swing_low" in work.columns:
        for idx in work.index[work["swing_low"]][-5:]:
            levels.append(float(work.loc[idx, "low"]))
    if len(work) >= 20:
        levels.append(float(work["high"].iloc[-20:].max()))
        levels.append(float(work["low"].iloc[-20:].min()))
    return sorted({l for l in levels if np.isfinite(l) and l > 0})


def calculate_trade_levels(df, signal, current_price, profile):
    atr = safe_float(df["atr"].iloc[-1], np.nan)
    if not np.isfinite(atr) or atr <= 0: return None
    impulse = find_impulse_leg(df, signal, lookback=120)
    fibs = fib_levels_from_impulse(impulse)
    pivots = calc_pivot_points(df)
    sr_levels = collect_sr_levels(df, lookback=200)
    swing_low, swing_high = latest_structure_levels(df)
    recent_low = float(df["low"].iloc[-20:].min())
    recent_high = float(df["high"].iloc[-20:].max())
    ssl = safe_float(df["ssl"].iloc[-1], np.nan)
    bsl = safe_float(df["bsl"].iloc[-1], np.nan)

    if signal == "BUY":
        entry = float(current_price); stop_cands = []
        for lvl in (swing_low, recent_low, ssl):
            if np.isfinite(lvl) and lvl < entry - 0.15 * atr: stop_cands.append(lvl)
        if fibs:
            for k in ("0.786", "0.618"):
                lvl = fibs["retracement"].get(k)
                if lvl and lvl < entry - 0.15 * atr: stop_cands.append(lvl)
        if pivots:
            for k in ("s1", "s2", "fib_s1", "fib_s2"):
                lvl = pivots.get(k)
                if lvl and lvl < entry - 0.3 * atr: stop_cands.append(lvl)
        structural = max(stop_cands) if stop_cands else entry - 1.5 * atr
        structural = max(structural, entry - 3.0 * atr)
        structural = min(structural, entry - 1.0 * atr)
        stop_loss = structural - 0.25 * atr
        risk = entry - stop_loss
        if risk <= 0: return None
        min_t1 = entry + risk * MIN_RR_TP1; min_t2 = entry + risk * MIN_RR_TP2
        min_t3 = entry + risk * MIN_RR_TP3
        cands = []
        if fibs:
            for k, v in fibs["extension"].items():
                if v > entry + 0.3 * atr: cands.append({"name": f"Fib ext {k}", "level": v})
            for k, v in fibs["retracement"].items():
                if v > entry + 0.3 * atr: cands.append({"name": f"Fib retr {k}", "level": v})
        if pivots:
            for key, nm in (("r1", "Pivot R1"), ("r2", "Pivot R2"), ("r3", "Pivot R3"),
                            ("fib_r1", "FibPivot R1"), ("fib_r2", "FibPivot R2"),
                            ("fib_r3", "FibPivot R3")):
                lvl = pivots.get(key)
                if lvl and lvl > entry + 0.3 * atr: cands.append({"name": nm, "level": lvl})
        for lvl, nm in ((bsl, "BSL"), (swing_high, "Swing High"), (recent_high, "20-bar High")):
            if np.isfinite(lvl) and lvl > entry + 0.3 * atr: cands.append({"name": nm, "level": lvl})
        for lvl in sr_levels:
            if lvl > entry + 0.5 * atr: cands.append({"name": "S/R", "level": lvl})
        cands.sort(key=lambda x: x["level"])
        def pick(min_p, prev, fallback, fb_name):
            valid = [c for c in cands if c["level"] >= min_p
                     and (prev is None or c["level"] >= prev + 0.5 * atr)]
            if valid: return valid[0]["level"], valid[0]["name"]
            return fallback, fb_name
        fb1 = fibs["extension"]["1.000"] if fibs else min_t1
        fb2 = fibs["extension"]["1.618"] if fibs else min_t2
        fb3 = fibs["extension"]["2.618"] if fibs else min_t3
        fb1 = max(fb1, min_t1); fb2 = max(fb2, min_t2, fb1 + 0.5 * atr)
        fb3 = max(fb3, min_t3, fb2 + 0.5 * atr)
        t1, s1src = pick(min_t1, None, fb1, "Fib 1.000"); t1 = max(t1, min_t1)
        t2, s2src = pick(min_t2, t1, fb2, "Fib 1.618"); t2 = max(t2, min_t2, t1 + 0.5 * atr)
        t3, s3src = pick(min_t3, t2, fb3, "Fib 2.618"); t3 = max(t3, min_t3, t2 + 0.5 * atr)
    else:
        entry = float(current_price); stop_cands = []
        for lvl in (swing_high, recent_high, bsl):
            if np.isfinite(lvl) and lvl > entry + 0.15 * atr: stop_cands.append(lvl)
        if fibs:
            for k in ("0.786", "0.618"):
                lvl = fibs["retracement"].get(k)
                if lvl and lvl > entry + 0.15 * atr: stop_cands.append(lvl)
        if pivots:
            for k in ("r1", "r2", "fib_r1", "fib_r2"):
                lvl = pivots.get(k)
                if lvl and lvl > entry + 0.3 * atr: stop_cands.append(lvl)
        structural = min(stop_cands) if stop_cands else entry + 1.5 * atr
        structural = min(structural, entry + 3.0 * atr)
        structural = max(structural, entry + 1.0 * atr)
        stop_loss = structural + 0.25 * atr
        risk = stop_loss - entry
        if risk <= 0: return None
        min_t1 = entry - risk * MIN_RR_TP1; min_t2 = entry - risk * MIN_RR_TP2
        min_t3 = entry - risk * MIN_RR_TP3
        cands = []
        if fibs:
            for k, v in fibs["extension"].items():
                if v < entry - 0.3 * atr: cands.append({"name": f"Fib ext {k}", "level": v})
            for k, v in fibs["retracement"].items():
                if v < entry - 0.3 * atr: cands.append({"name": f"Fib retr {k}", "level": v})
        if pivots:
            for key, nm in (("s1", "Pivot S1"), ("s2", "Pivot S2"), ("s3", "Pivot S3"),
                            ("fib_s1", "FibPivot S1"), ("fib_s2", "FibPivot S2"),
                            ("fib_s3", "FibPivot S3")):
                lvl = pivots.get(key)
                if lvl and lvl < entry - 0.3 * atr: cands.append({"name": nm, "level": lvl})
        for lvl, nm in ((ssl, "SSL"), (swing_low, "Swing Low"), (recent_low, "20-bar Low")):
            if np.isfinite(lvl) and lvl < entry - 0.3 * atr: cands.append({"name": nm, "level": lvl})
        for lvl in sr_levels:
            if lvl < entry - 0.5 * atr: cands.append({"name": "S/R", "level": lvl})
        cands.sort(key=lambda x: x["level"], reverse=True)
        def pick(min_p, prev, fallback, fb_name):
            valid = [c for c in cands if c["level"] <= min_p
                     and (prev is None or c["level"] <= prev - 0.5 * atr)]
            if valid: return valid[0]["level"], valid[0]["name"]
            return fallback, fb_name
        fb1 = fibs["extension"]["1.000"] if fibs else min_t1
        fb2 = fibs["extension"]["1.618"] if fibs else min_t2
        fb3 = fibs["extension"]["2.618"] if fibs else min_t3
        fb1 = min(fb1, min_t1); fb2 = min(fb2, min_t2, fb1 - 0.5 * atr)
        fb3 = min(fb3, min_t3, fb2 - 0.5 * atr)
        t1, s1src = pick(min_t1, None, fb1, "Fib 1.000"); t1 = min(t1, min_t1)
        t2, s2src = pick(min_t2, t1, fb2, "Fib 1.618"); t2 = min(t2, min_t2, t1 - 0.5 * atr)
        t3, s3src = pick(min_t3, t2, fb3, "Fib 2.618"); t3 = min(t3, min_t3, t2 - 0.5 * atr)
    rr1 = abs(t1 - entry) / risk; rr2 = abs(t2 - entry) / risk; rr3 = abs(t3 - entry) / risk
    return {"entry": float(entry), "stop_loss": float(stop_loss),
            "target1": float(t1), "target2": float(t2), "target3": float(t3),
            "risk": float(risk),
            "risk_reward_1": float(rr1), "risk_reward_2": float(rr2), "risk_reward_3": float(rr3),
            "sources": {"tp1": s1src, "tp2": s2src, "tp3": s3src},
            "fibs": fibs, "pivots": pivots, "impulse": impulse}


def validate_levels(signal, levels, profile):
    if not levels: return False, "تعذر بناء المستويات"
    if signal == "BUY":
        if not levels["stop_loss"] < levels["entry"] < levels["target1"]:
            return False, "ترتيب BUY غير صالح"
    else:
        if not levels["target1"] < levels["entry"] < levels["stop_loss"]:
            return False, "ترتيب SELL غير صالح"
    if levels["risk_reward_1"] < MIN_RR_TP1: return False, "TP1 RR منخفض"
    if levels["risk_reward_2"] < MIN_RR_TP2: return False, "TP2 RR منخفض"
    if levels["risk_reward_3"] < MIN_RR_TP3: return False, "TP3 RR منخفض"
    return True, ""


def calc_position_size(balance, risk_pct, entry, stop_loss, pair_name):
    if balance <= 0 or risk_pct <= 0: return None
    risk_amount = balance * (risk_pct / 100.0)
    sl_distance = abs(entry - stop_loss)
    if sl_distance <= 0: return None
    asset = asset_type_from_name(pair_name)
    if asset == "forex":
        if "JPY" in pair_name.upper():
            pip = 0.01; sl_pips = sl_distance / pip
            pip_value_per_lot = 1000 / entry
        else:
            pip = 0.0001; sl_pips = sl_distance / pip
            pip_value_per_lot = 10.0
        lots = risk_amount / (sl_pips * pip_value_per_lot) if sl_pips > 0 else 0
        return {"asset": asset, "risk_amount": round(risk_amount, 2),
                "sl_distance": round(sl_distance, 5), "sl_pips": round(sl_pips, 1),
                "lots": round(lots, 2), "units": int(lots * 100000),
                "unit_label": "lots"}
    if asset == "gold":
        sl_pips = sl_distance / 0.1
        pip_value_per_lot = 10.0
        lots = risk_amount / (sl_pips * pip_value_per_lot) if sl_pips > 0 else 0
        return {"asset": asset, "risk_amount": round(risk_amount, 2),
                "sl_distance": round(sl_distance, 2), "sl_pips": round(sl_pips, 1),
                "lots": round(lots, 2), "ounces": round(lots * 100, 2),
                "unit_label": "lots (100 oz)"}
    if asset == "crypto":
        units = risk_amount / sl_distance if sl_distance > 0 else 0
        return {"asset": asset, "risk_amount": round(risk_amount, 2),
                "sl_distance": round(sl_distance, 2),
                "units": round(units, 6), "unit_label": "units (coins)"}
    return None


def build_trade_management(signal, levels, profile):
    if not levels: return None
    entry = levels["entry"]
    atr_trail = profile.get("atr_trail", 1.1)
    return [
        {"stage": "TP1 Hit", "action": "إغلاق 40%",
         "details": f"نقل Stop Loss إلى التعادل ({fmt_price(entry, '')})", "icon": "🎯"},
        {"stage": "TP2 Hit", "action": "إغلاق 30%",
         "details": f"Trailing Stop = {atr_trail}× ATR", "icon": "🎯"},
        {"stage": "TP3 Hit", "action": "إغلاق 30% النهائي",
         "details": "إغلاق كامل + تسجيل النتيجة", "icon": "🏁"},
    ]


def generate_signal(df, current_price, pair_name, symbol,
                    news_block=False, skip_external_filters=False,
                    precomputed=None, strict_soft=False):
    profile = profile_for(pair_name)
    profile_key = get_asset_profile(pair_name)
    df = build_features(df, profile)

    if precomputed is None:
        mtf_bias, mtf_conf, mtf_details = get_mtf_analysis(symbol, pair_name)
        wk_bias, _ = weekly_bias(symbol, pair_name)
        dxy_bias, _, _ = get_dxy_context()
        gold_corr = get_gold_dxy_correlation() if ("Gold" in pair_name or "XAU" in pair_name.upper()) else None
        ccy_strength = get_currency_strength_matrix()
        rate_diff, _ = get_interest_rate_differential(pair_name)
        risk = get_risk_sentiment()
    else:
        mtf_bias = precomputed.get("mtf_bias", "NEUTRAL")
        mtf_conf = precomputed.get("mtf_conf", 50.0)
        mtf_details = precomputed.get("mtf_details", {})
        wk_bias = precomputed.get("weekly_bias", "NEUTRAL")
        dxy_bias = precomputed.get("dxy_bias", "NEUTRAL")
        gold_corr = precomputed.get("gold_corr", None)
        ccy_strength = precomputed.get("ccy_strength", None)
        rate_diff = precomputed.get("rate_diff", 0.0)
        risk = precomputed.get("risk", None)

    scores = directional_score(df, pair_name, symbol, dxy_bias=dxy_bias,
                               gold_corr=gold_corr, ccy_strength=ccy_strength,
                               rate_diff=rate_diff, risk=risk)

    buy, sell = scores["buy"], scores["sell"]
    if mtf_bias == "BULLISH": buy += 8; sell -= 4
    elif mtf_bias == "BEARISH": sell += 8; buy -= 4
    if wk_bias == "BULLISH": buy += 5; sell -= 3
    elif wk_bias == "BEARISH": sell += 5; buy -= 3
    buy, sell = clamp(buy, 0, 100), clamp(sell, 0, 100)

    gap = abs(buy - sell)
    signal = "WAIT" if gap < MIN_SIGNAL_GAP else ("BUY" if buy > sell else "SELL")

    last = df.iloc[-1]
    mss_conflict = False
    if safe_bool(last.get("mss_bullish")) and sell > buy: mss_conflict = True
    if safe_bool(last.get("mss_bearish")) and buy > sell: mss_conflict = True

    rsi_now = safe_float(last.get("rsi"), 50)
    regime_now = scores["regime"]
    if regime_now == "RANGE":
        if signal == "BUY" and rsi_now > profile["rsi_ob"] and not safe_bool(last.get("mss_bullish")):
            buy = max(0, buy - 5)
        if signal == "SELL" and rsi_now < profile["rsi_os"] and not safe_bool(last.get("mss_bearish")):
            sell = max(0, sell - 5)

    confidence = clamp(50 + abs(buy - sell) * 0.75 + max(0, max(buy, sell) - 60) * 0.25, 50, 95)

    soft_penalty_items = []
    if signal in ("BUY", "SELL") and mtf_bias != "NEUTRAL":
        if (signal == "BUY" and mtf_bias != "BULLISH") or \
           (signal == "SELL" and mtf_bias != "BEARISH"):
            soft_penalty_items.append(("MTF ضد الاتجاه", PENALTY_MTF_AGAINST))
    if signal in ("BUY", "SELL") and wk_bias != "NEUTRAL":
        if (signal == "BUY" and wk_bias != "BULLISH") or \
           (signal == "SELL" and wk_bias != "BEARISH"):
            soft_penalty_items.append(("Weekly ضد الاتجاه", PENALTY_WEEKLY_AGAINST))
    if signal in ("BUY", "SELL") and scores["regime"] in ("RANGE", "COMPRESSION"):
        soft_penalty_items.append((f"Regime {scores['regime']}", PENALTY_RANGE_REGIME))
    if signal in ("BUY", "SELL"):
        atr_now = safe_float(last.get("atr"), 0)
        if atr_now > 0:
            body = abs(float(last["close"]) - float(last["open"]))
            if body < 0.50 * atr_now: soft_penalty_items.append(("شمعة ضعيفة", PENALTY_WEAK_CANDLE))
            elif signal == "BUY" and last["close"] < last["open"]:
                soft_penalty_items.append(("شمعة ضد الاتجاه", PENALTY_WEAK_CANDLE))
            elif signal == "SELL" and last["close"] > last["open"]:
                soft_penalty_items.append(("شمعة ضد الاتجاه", PENALTY_WEAK_CANDLE))
    if mss_conflict and signal in ("BUY", "SELL"):
        soft_penalty_items.append(("MSS Conflict", 10))

    candidate = signal if signal in ("BUY", "SELL") else ("BUY" if buy > sell else "SELL")
    levels = calculate_trade_levels(df, candidate, current_price, profile)
    risk_ok, risk_msg = validate_levels(candidate, levels, profile) if levels else (False, "تعذر")
    if signal in ("BUY", "SELL") and not risk_ok:
        signal = "WAIT"; confidence = 0

    pillars = scores["pillars"]
    w_confluence = weighted_confluence(pillars, candidate)

    conf_ok, conf_score, conf_reasons, conf_blockers = confirmation_gate(
        df, candidate, pillars, scores["regime"], mtf_bias, mtf_conf, profile, wk_bias)

    filter_results = {}
    filter_results["MSS Conflict"] = {"pass": not mss_conflict,
        "msg": "MSS معاكس — تنبيه" if mss_conflict else "MSS متوافق"}

    all_passed = True; block_reason = ""
    external_filter_names = ["HTF Zone", "LTF Trigger", "Session", "Volatility",
                             "Kill Zone", "OTE", "Displacement", "News Window"]
    if skip_external_filters:
        for _name in external_filter_names:
            filter_results[_name] = {"pass": True, "msg": "Backtest — skipped"}
        ntw_block = False
    else:
        htf_ok, htf_msg, htf_zone = htf_zone_filter(symbol, candidate, profile_key)
        filter_results["HTF Zone"] = {"pass": htf_ok, "msg": htf_msg, "zone": htf_zone}
        if not htf_ok: all_passed = False; block_reason = htf_msg
        ltf_ok, ltf_msg = ltf_entry_trigger(symbol, candidate, profile_key)
        filter_results["LTF Trigger"] = {"pass": ltf_ok, "msg": ltf_msg}
        if not ltf_ok: soft_penalty_items.append(("LTF Trigger", 6))
        sess_ok, sess_msg, sess_label = session_filter(pair_name, strict=(profile_key != "crypto"))
        filter_results["Session"] = {"pass": sess_ok, "msg": sess_msg, "label": sess_label}
        if not sess_ok: soft_penalty_items.append(("Session", 5))
        vol_ok, vol_msg, vol_label = volatility_regime_filter(df)
        filter_results["Volatility"] = {"pass": vol_ok, "msg": vol_msg, "label": vol_label}
        if not vol_ok:
            if vol_label == "CHAOS": all_passed = False; block_reason = block_reason or vol_msg
            else: soft_penalty_items.append(("Volatility", 8))
        kz_ok, kz_msg = in_kill_zone(asset_type_from_name(pair_name))
        filter_results["Kill Zone"] = {"pass": kz_ok, "msg": kz_msg}
        if not kz_ok: soft_penalty_items.append(("Kill Zone", 3))
        ote_ok, ote_msg = ote_filter(df, candidate)
        filter_results["OTE"] = {"pass": ote_ok, "msg": ote_msg}
        if not ote_ok: soft_penalty_items.append(("OTE", 5))
        disp_ok, disp_msg = displacement_check(df, candidate)
        filter_results["Displacement"] = {"pass": disp_ok, "msg": disp_msg}
        if not disp_ok: soft_penalty_items.append(("Displacement", 5))
        ntw_block, ntw_msg = news_time_block(
            st.session_state.get("economic_events") or [], pair_name)
        filter_results["News Window"] = {"pass": not ntw_block, "msg": ntw_msg or "لا خبر قريب"}
        if ntw_block: all_passed = False; block_reason = block_reason or ntw_msg

    market_open, market_msg = is_market_open(pair_name)
    filter_results["Market Open"] = {"pass": market_open, "msg": market_msg}
    if not market_open and not skip_external_filters:
        all_passed = False; block_reason = block_reason or market_msg

    kill_blocked, consec = check_kill_switch()
    if kill_blocked and not skip_external_filters:
        filter_results["Kill Switch"] = {"pass": False,
            "msg": f"{MAX_CONSECUTIVE_LOSSES} خسائر متتالية — توقف"}
        all_passed = False
        block_reason = block_reason or f"Kill Switch نشط ({consec} خسائر)"
    else:
        filter_results["Kill Switch"] = {"pass": True, "msg": f"Discipline OK ({consec})"}

    # ---- Correlation Guard Filter ----
    corr_blocked = False; corr_warnings = []
    if not skip_external_filters and st.session_state.get("open_positions") and signal in ("BUY", "SELL"):
        corr_check = check_portfolio_conflict(
            symbol, signal, pair_name, st.session_state.open_positions)
        corr_blocked = corr_check["blocked"]
        corr_warnings = corr_check["warnings"]
        if corr_blocked:
            all_passed = False
            block_reason = block_reason or "Portfolio Correlation Conflict"
        filter_results["Correlation Guard"] = {
            "pass": not corr_blocked,
            "msg": f"⚠️ {len(corr_warnings)} تحذير" if corr_warnings else "✅ متوافق"}
    else:
        filter_results["Correlation Guard"] = {"pass": True, "msg": "لا مراكز مفتوحة"}

    weekly_ok = (wk_bias == "NEUTRAL"
                 or (candidate == "BUY" and wk_bias == "BULLISH")
                 or (candidate == "SELL" and wk_bias == "BEARISH"))
    filter_results["Weekly Bias"] = {"pass": weekly_ok, "msg": f"Weekly: {wk_bias}"}
    filter_results["Weighted Confluence"] = {
        "pass": w_confluence >= 50, "msg": f"Confluence: {w_confluence:.0f}/100"}

    raw_confidence = confidence
    penalty_total, applied_penalties = compute_soft_penalty(soft_penalty_items, strict=True)
    effective_confidence = clamp(raw_confidence - penalty_total, 0, 95)

    if raw_confidence >= A_PLUS_MIN and conf_score >= 78: trade_grade = "A+"
    elif raw_confidence >= A_MIN and conf_score >= 72: trade_grade = "A"
    elif raw_confidence >= B_MIN and conf_score >= 65: trade_grade = "B"
    elif raw_confidence >= C_MIN and conf_score >= 58: trade_grade = "C"
    else: trade_grade = "WAIT"

    if signal == "WAIT":
        execution_status, execution_reason = "WAIT", "Signal WAIT"
    elif not all_passed:
        execution_status, execution_reason = "BLOCKED", f"Hard Gate: {block_reason}"
    elif news_block:
        execution_status, execution_reason = "WAIT", "خبر عالي التأثير"
    elif effective_confidence < profile.get("confidence_threshold", 72):
        execution_status, execution_reason = "WAIT", f"Confidence < {profile.get('confidence_threshold', 72)}"
    elif conf_score < profile.get("confirmation_threshold", 65):
        execution_status, execution_reason = "WAIT", f"Confirmation < {profile.get('confirmation_threshold', 65)}"
    elif trade_grade in ("A+", "A"):
        execution_status, execution_reason = "EXECUTE", f"{trade_grade} — PASS"
    elif trade_grade == "B":
        execution_status, execution_reason = "EXECUTE", "B — PASS"
    elif trade_grade == "C":
        execution_status, execution_reason = "WATCH", "C — مراقبة فقط"
    else:
        execution_status, execution_reason = "WAIT", "لا اجتياز"

    confidence = effective_confidence
    advisories_str = ", ".join(f"{n}({p})" for n, p in soft_penalty_items) or "None"

    return {
        "signal": signal, "confidence": confidence, "raw_confidence": raw_confidence,
        "buy_score": buy, "sell_score": sell,
        "weighted_confluence": w_confluence,
        "pillars": pillars, "mtf_bias": mtf_bias, "mtf_conf": mtf_conf,
        "mtf_details": mtf_details, "weekly_bias": wk_bias,
        "levels": levels if risk_ok else None, "df": df,
        "confirmation_ok": conf_ok, "confirmation_score": conf_score,
        "confirmation_reasons": conf_reasons, "confirmation_blockers": conf_blockers,
        "execution_status": execution_status, "execution_reason": execution_reason,
        "trade_grade": trade_grade, "soft_penalties": penalty_total,
        "soft_advisories": advisories_str,
        "filter_results": filter_results, "all_filters_passed": all_passed,
        "filter_block_reason": block_reason,
        "regime": scores["regime"], "dxy_bias": scores["dxy_bias"],
        "usd_msg": scores["usd_msg"], "divergence": scores["divergence"],
        "reasons": scores["reasons"] + conf_reasons,
        "fund_details": scores.get("fund_details", []),
        "fund_buy": scores.get("fund_buy", 0),
        "fund_sell": scores.get("fund_sell", 0),
        "corr_blocked": corr_blocked, "corr_warnings": corr_warnings,
    }


def _bias_from_slice(df_slice, pair_name):
    if df_slice is None or len(df_slice) < 60: return "NEUTRAL", 50.0
    try:
        x = df_slice.copy()
        x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
        x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
        x["ema200"] = x["close"].ewm(span=200, adjust=False).mean()
        last = x.iloc[-1]; bull = bear = 0
        if last["ema20"] > last["ema50"]: bull += 1
        elif last["ema20"] < last["ema50"]: bear += 1
        if last["ema50"] > last["ema200"]: bull += 1
        elif last["ema50"] < last["ema200"]: bear += 1
        if bull > bear: return "BULLISH", 60.0 + bull * 5
        if bear > bull: return "BEARISH", 60.0 + bear * 5
        return "NEUTRAL", 50.0
    except Exception:
        return "NEUTRAL", 50.0


def _weekly_bias_from_slice(df_slice, pair_name):
    if df_slice is None or len(df_slice) < 100: return "NEUTRAL"
    try:
        weekly = df_slice.resample("1W").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum"}).dropna()
        if len(weekly) < 20: return "NEUTRAL"
        bias, _ = _bias_from_slice(weekly, pair_name)
        return bias
    except Exception:
        return "NEUTRAL"


@st.cache_data(ttl=600, show_spinner=False)
def quick_backtest(symbol, pair_name, lookback=200, run_monte_carlo=True):
    try:
        df_full = get_historical_data(symbol, "1y", "4h")
        if df_full is None or len(df_full) < lookback + 50: return None
        profile = profile_for(pair_name)
        try:
            dxy_df = get_historical_data("DX-Y.NYB", "1y", "4h")
            dxy_bias_full = _bias_from_slice(dxy_df, "DXY")[0] if dxy_df is not None else "NEUTRAL"
        except Exception: dxy_bias_full = "NEUTRAL"
        try:
            gold_corr = get_gold_dxy_correlation() if ("Gold" in pair_name or "XAU" in pair_name.upper()) else None
        except Exception: gold_corr = None
        try:
            ccy_strength = get_currency_strength_matrix()
            rate_diff, _ = get_interest_rate_differential(pair_name)
            risk = get_risk_sentiment()
        except Exception: ccy_strength, rate_diff, risk = None, 0.0, None

        df = build_features(df_full, profile)
        wins = losses = 0; total_r = 0.0
        equity = 0.0; peak = 0.0; max_dd = 0.0
        trades_log = []; start_i = 100; end_i = len(df) - 20

        for i in range(start_i, end_i):
            slice_df = df.iloc[:i].copy()
            price = float(df["close"].iloc[i])
            mtf_bias, mtf_conf = _bias_from_slice(slice_df, pair_name)
            wk_bias = _weekly_bias_from_slice(slice_df, pair_name)
            precomputed = {"mtf_bias": mtf_bias, "mtf_conf": mtf_conf, "mtf_details": {},
                           "weekly_bias": wk_bias, "dxy_bias": dxy_bias_full,
                           "gold_corr": gold_corr, "ccy_strength": ccy_strength,
                           "rate_diff": rate_diff, "risk": risk}
            try:
                result = generate_signal(slice_df, price, pair_name, symbol,
                                          skip_external_filters=True, precomputed=precomputed)
            except Exception: continue
            if result["signal"] == "WAIT" or result["levels"] is None: continue
            if result["execution_status"] != "EXECUTE": continue
            sl = result["levels"]["stop_loss"]; t1 = result["levels"]["target1"]
            direction = result["signal"]; rr1 = result["levels"]["risk_reward_1"]
            future = df.iloc[i+1:i+21]
            hit_tp = hit_sl = False; outcome = "OPEN"
            for _, row in future.iterrows():
                if direction == "BUY":
                    if row["low"] <= sl: hit_sl = True; outcome = "LOSS"; break
                    if row["high"] >= t1: hit_tp = True; outcome = "WIN"; break
                else:
                    if row["high"] >= sl: hit_sl = True; outcome = "LOSS"; break
                    if row["low"] <= t1: hit_tp = True; outcome = "WIN"; break
            if hit_tp: wins += 1; total_r += rr1; equity += rr1
            elif hit_sl: losses += 1; total_r -= 1.0; equity -= 1.0
            else: continue
            peak = max(peak, equity); max_dd = max(max_dd, peak - equity)
            trades_log.append({"bar_index": i, "direction": direction, "outcome": outcome,
                               "r": rr1 if hit_tp else -1.0,
                               "grade": result.get("trade_grade", "?"),
                               "confidence": result["confidence"]})

        total = wins + losses
        if total == 0:
            return {"trades": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_R": 0,
                    "expectancy": 0, "profit_factor": 0, "max_drawdown": 0,
                    "sharpe": 0, "avg_r": 0, "trades_log": [], "monte_carlo": None}
        avg_r = total_r / total
        wins_r = [t["r"] for t in trades_log if t["outcome"] == "WIN"]
        losses_r = [t["r"] for t in trades_log if t["outcome"] == "LOSS"]
        all_r = wins_r + losses_r
        if len(all_r) > 1:
            r_std = float(np.std(all_r, ddof=1))
            sharpe = (avg_r / r_std * np.sqrt(len(all_r))) if r_std > 0 else 0.0
        else: sharpe = 0.0
        mc_result = None
        if run_monte_carlo and len(all_r) >= 5:
            mc_result = monte_carlo_simulation(all_r, n_sims=1000)
        return {"trades": total, "wins": wins, "losses": losses,
                "win_rate": wins / total * 100, "total_R": total_r,
                "expectancy": avg_r, "avg_r": avg_r,
                "profit_factor": sum(wins_r) / max(abs(sum(losses_r)), 1e-9),
                "max_drawdown": max_dd, "sharpe": sharpe,
                "trades_log": trades_log[-50:], "monte_carlo": mc_result}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=600, show_spinner=False)
def get_all_signals_parallel():
    results = []
    def analyze_one(pair_name, symbol):
        try:
            price, _ = get_spot_price(symbol)
            df = get_historical_data(symbol, "3mo", "4h")
            if price is None or df is None: return None
            result = generate_signal(df, price, pair_name, symbol, skip_external_filters=True)
            levels = result["levels"] or {}
            return {"الزوج": pair_name, "الإشارة": result["signal"],
                    "الثقة": round(result["confidence"], 1),
                    "BUY": round(result["buy_score"], 1),
                    "SELL": round(result["sell_score"], 1),
                    "MTF": result["mtf_bias"], "Weekly": result["weekly_bias"],
                    "Regime": result["regime"],
                    "Fund": f"B{result.get('fund_buy', 0):.0f}/S{result.get('fund_sell', 0):.0f}",
                    "Confluence": round(result["weighted_confluence"], 0),
                    "Confirmation": round(result["confirmation_score"], 1),
                    "Grade": result.get("trade_grade", "WAIT"),
                    "Execution": result["execution_status"],
                    "السعر": fmt_price(price, pair_name),
                    "SL": fmt_price(levels.get("stop_loss"), pair_name),
                    "TP1": fmt_price(levels.get("target1"), pair_name),
                    "RR3": round(levels.get("risk_reward_3", 0), 2) if levels else 0}
        except Exception:
            return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_one, p, s): (p, i)
                   for i, (p, s) in enumerate(PAIRS.items())}
        for fut in concurrent.futures.as_completed(futures):
            try:
                res = fut.result()
                if res: results.append(res)
            except Exception: pass
    if not results: return pd.DataFrame()
    out = pd.DataFrame(results)
    order = {"BUY": 0, "SELL": 1, "WAIT": 2}
    out["_o"] = out["الإشارة"].map(order).fillna(3)
    out = out.sort_values(["_o", "الثقة"], ascending=[True, False]).drop(columns="_o")
    return out


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


def event_risk_message(events, pair_name):
    if not events: return "لا توجد بيانات تقويم"
    blocked, msg = news_time_block(events, pair_name)
    if blocked: return f"⚠️ {msg}"
    return "لا يوجد قفل خبر مطابق"


# ============================================================
# UI
# ============================================================

st.set_page_config(page_title=f"BLACK PYRAMID {APP_VERSION}",
                   page_icon="▲", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', 'Tahoma', sans-serif; }
body { background: #0a0d13; color: #e8edf5; }
.main-header, .main-title, .main-subtitle,
.signal-card, .signal-meta, .signal-conf, .signal-grade,
.metric-card, .metric-label, .metric-value, .metric-sub,
.tool-card, .tool-name, .tool-value, .tool-desc,
.section-title, .footer-style,
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] .stMetricValue,
div[data-testid="stDataFrame"] th,
div[data-testid="stDataFrame"] td { direction: rtl; }
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[kind="header"] {
    position: fixed !important; left: 12px !important; right: auto !important;
    top: 14px !important; z-index: 999999 !important;
    background: rgba(230,200,124,0.08) !important;
    border: 1px solid rgba(230,200,124,0.25) !important;
    border-radius: 50% !important; width: 40px !important; height: 40px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    transition: all 0.25s ease !important; }
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
button[kind="header"]:hover {
    background: rgba(230,200,124,0.2) !important;
    border-color: rgba(230,200,124,0.6) !important;
    transform: scale(1.05) !important; }
[data-testid="stSidebar"] { direction: rtl; }
[data-testid="stSidebar"] > div:first-child { direction: rtl; }
.hero {
    background: radial-gradient(circle at 20% 30%, rgba(230,200,124,0.08), transparent 60%),
                radial-gradient(circle at 80% 70%, rgba(124,212,160,0.06), transparent 60%),
                linear-gradient(145deg, #10141c, #0d1017);
    padding: 18px 26px; border-radius: 20px;
    border: 1px solid rgba(230,200,124,0.12);
    box-shadow: 0 12px 30px rgba(0,0,0,0.55);
    position: relative; overflow: hidden; }
.hero::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, #e6c87c, #7cd4a0, #e6c87c, transparent); }
.hero-title { font-size: 2rem; font-weight: 800; color: #e6c87c;
    letter-spacing: 3px; margin: 0; line-height: 1.1;
    text-shadow: 0 0 30px rgba(230,200,124,0.35); }
.hero-sub { color: #8b95a8; margin-top: 8px; font-size: 0.82rem;
    font-weight: 300; letter-spacing: 0.3px; line-height: 1.4; }
.hero-badge { display: inline-block; padding: 3px 12px; border-radius: 40px;
    background: rgba(230,200,124,0.1); color: #e6c87c;
    font-size: 0.7rem; font-weight: 600;
    border: 1px solid rgba(230,200,124,0.25);
    margin-left: 6px; letter-spacing: 1px; }
.hero-badge-balanced { display: inline-block; padding: 3px 12px; border-radius: 40px;
    background: rgba(124,212,160,0.12); color: #7cd4a0;
    font-size: 0.7rem; font-weight: 700;
    border: 1px solid rgba(124,212,160,0.35);
    margin-left: 6px; letter-spacing: 1.5px; }
div[data-testid="stHorizontalBlock"] > div > div > div[data-testid="stButton"] { margin-top: 0 !important; }
div[data-testid="stHorizontalBlock"] > div > div > div[data-testid="stButton"] > button {
    padding: 0.55rem 0.8rem !important;
    font-size: 0.85rem !important;
    white-space: nowrap !important;
    min-height: 42px !important; }
.signal-card {
    background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 40px 24px; border-radius: 28px; text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
    position: relative; overflow: hidden; }
.signal-card::after {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(circle at 50% 0%, rgba(230,200,124,0.06), transparent 70%);
    pointer-events: none; }
.signal-value { font-size: 4rem; font-weight: 800; letter-spacing: 4px; margin: 8px 0; }
.signal-conf { font-size: 1.35rem; color: #c8d2e2; font-weight: 500; }
.signal-meta { color: #7d879c; font-size: 0.9rem; margin-top: 8px; }
.signal-grade { font-size: 1.6rem; font-weight: 800; color: #e6c87c;
    letter-spacing: 2px; margin-top: 10px; }
.metric-card {
    background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 18px 20px; border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    transition: all 0.25s ease; }
.metric-card:hover {
    border-color: rgba(230,200,124,0.25);
    transform: translateY(-2px); }
.metric-label { color: #7d879c; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.metric-value { color: #e8edf5; font-size: 1.5rem; font-weight: 700; margin-top: 6px; }
.metric-sub { color: #a0aab8; font-size: 0.82rem; margin-top: 4px; }
.tool-card {
    background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 20px; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 6px 16px rgba(0,0,0,0.35);
    transition: all 0.25s ease; height: 100%; }
.tool-card:hover {
    border-color: rgba(230,200,124,0.3);
    transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(0,0,0,0.5); }
.tool-name { color: #e6c87c; font-size: 0.85rem;
    font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
    margin-bottom: 10px; }
.tool-value { color: #e8edf5; font-size: 1.3rem; font-weight: 700; }
.tool-desc { color: #8892a5; font-size: 0.82rem; margin-top: 8px; line-height: 1.5; }
.section-title {
    font-size: 1.4rem; font-weight: 700; color: #e6c87c;
    margin: 32px 0 18px 0; padding-bottom: 12px;
    border-bottom: 1px solid rgba(230,200,124,0.15); }
.section-title span { color: #6b7488; font-size: 0.85rem; font-weight: 400; }
div.stButton > button {
    background: linear-gradient(145deg, #1a2130, #131821);
    color: #e8edf5; border: 1px solid rgba(230,200,124,0.2);
    border-radius: 40px; padding: 0.7rem 1.8rem;
    font-weight: 500; letter-spacing: 0.3px;
    transition: all 0.25s ease;
    box-shadow: 0 6px 16px rgba(0,0,0,0.4);
    width: 100%; }
div.stButton > button:hover {
    background: linear-gradient(145deg, #263049, #1a2233);
    border-color: rgba(230,200,124,0.55);
    color: #fff; transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.6); }
div[data-testid="stSelectbox"] > label {
    color: #e6c87c !important; font-weight: 600 !important;
    font-size: 0.9rem !important; letter-spacing: 0.5px;
    margin-bottom: 6px !important; }
div[data-testid="stSelectbox"] > div > div {
    background: linear-gradient(145deg, #10141c, #0d1017) !important;
    border: 1px solid rgba(230,200,124,0.25) !important;
    border-radius: 12px !important; min-height: 46px !important; }
div[data-baseweb="select"] > div { background: transparent !important; }
div[data-baseweb="select"] input { color: #e8edf5 !important; }
button[data-baseweb="tab"] {
    background: transparent; color: #8892a5;
    border-radius: 12px 12px 0 0;
    font-weight: 500; padding: 12px 20px; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #e6c87c !important;
    background: rgba(230,200,124,0.05);
    border-bottom: 2px solid #e6c87c; }
div[data-testid="stDataFrame"] {
    background: #0d1017; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stDataFrame"] th {
    background: #10141c !important; color: #e6c87c !important;
    font-weight: 600 !important; text-transform: uppercase;
    font-size: 0.75rem !important; letter-spacing: 0.5px; }
div[data-testid="stDataFrame"] td {
    background: #0d1017 !important; color: #ced6e6 !important; }
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 16px 18px; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stMetric"] label {
    color: #7d879c !important; font-size: 0.78rem !important;
    text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
div[data-testid="stMetric"] .stMetricValue {
    color: #e8edf5 !important; font-weight: 700 !important; }
hr { border: none; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(230,200,124,0.15), transparent);
    margin: 30px 0; }
.footer-style {
    text-align: center; color: #4a5266; padding: 40px 0 20px;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 40px; font-size: 0.85rem; letter-spacing: 0.5px; }
details { background: #0d1017 !important; border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.05) !important; }
</style>
""", unsafe_allow_html=True)


_logo_b64 = load_logo_b64()
hero_left, hero_right = st.columns([1.15, 1.6])

with hero_left:
    if _logo_b64:
        st.markdown(f"""
        <div class="hero">
            <img src="data:image/png;base64,{_logo_b64}" alt="BLACK PYRAMID"
                 style="width: 190px; max-width: 100%; height: auto; display: block;
                        filter: drop-shadow(0 6px 20px rgba(230,200,124,0.3));">
            <div class="hero-sub" style="margin-top: 8px;">
                Institutional Analysis Terminal
                <span class="hero-badge">{APP_VERSION}</span>
                <span class="hero-badge-balanced">CORRELATION GUARD</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="hero">
            <div class="hero-title">▲ BLACK PYRAMID</div>
            <div class="hero-sub" style="margin-top: 8px;">
                Institutional Analysis Terminal
                <span class="hero-badge">{APP_VERSION}</span>
                <span class="hero-badge-balanced">CORRELATION GUARD</span>
            </div>
        </div>""", unsafe_allow_html=True)

with hero_right:
    st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
    with b1:
        if st.button("📅 التقويم", width="stretch", key="btn_info_cal"):
            st.session_state.show_calendar_today = not st.session_state.show_calendar_today
            st.session_state.show_session_info = False
            st.session_state.show_market_status = False
    with b2:
        if st.button("🕐 الجلسة", width="stretch", key="btn_info_session"):
            st.session_state.show_session_info = not st.session_state.show_session_info
            st.session_state.show_calendar_today = False
            st.session_state.show_market_status = False
    with b3:
        if st.button("📊 السوق", width="stretch", key="btn_info_market"):
            st.session_state.show_market_status = not st.session_state.show_market_status
            st.session_state.show_calendar_today = False
            st.session_state.show_session_info = False
    with b4:
        if st.button("🔄 تحديث", width="stretch", key="btn_info_refresh"):
            st.session_state.economic_events = get_fmp_economic_calendar()
            st.toast("✅ تم تحديث التقويم")


if st.session_state.show_calendar_today:
    st.markdown("### 📅 أحداث اليوم")
    if not st.session_state.economic_events:
        st.info("لا توجد بيانات. اضغط '🔄 تحديث'.")
    else:
        todays = get_todays_events(st.session_state.economic_events, st.session_state.selected_pair)
        if not todays: st.success("✅ لا توجد أحداث عالية التأثير.")
        else:
            cal_cols = st.columns(3)
            for idx, ev in enumerate(todays[:9]):
                impact = ev["impact"]
                if impact in ("high", "3", "high impact"): icon = "🔴"; color = "#f57a7a"
                elif impact in ("medium", "2"): icon = "🟡"; color = "#f5c87a"
                else: icon = "🟢"; color = "#7cd4a0"
                with cal_cols[idx % 3]:
                    st.markdown(f"""<div class="tool-card" style="margin-bottom:12px;">
                        <div class="tool-name">{icon} {ev['time']} · {ev['country']}</div>
                        <div class="tool-value" style="font-size:0.95rem; color:{color};">
                            {ev['event'][:50]}</div>
                        <div class="tool-desc">التأثير: <b>{ev['impact'].upper()}</b></div>
                    </div>""", unsafe_allow_html=True)


if st.session_state.show_session_info:
    st.markdown("### 🕐 الجلسة الحالية")
    sess = get_current_session_info()
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🌍 الجلسة</div>
            <div class="tool-value">{sess['icon']} {sess['session']}</div>
            <div class="tool-desc">{sess['desc']}</div></div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">⏰ التوقيت</div>
            <div class="tool-value">{sess['time_utc']}</div>
            <div class="tool-desc">UTC</div></div>""", unsafe_allow_html=True)
    with sc3:
        kz_icon = "✅" if "داخل" in sess["kill_zone"] else "⚪"
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🎯 Kill Zone</div>
            <div class="tool-value">{kz_icon}</div>
            <div class="tool-desc">{sess['kill_zone']}</div></div>""", unsafe_allow_html=True)


if st.session_state.show_market_status:
    st.markdown("### 📊 وضع السوق")
    _sym = PAIRS.get(st.session_state.selected_pair, "GC=F")
    mstat = get_market_status_info(_sym, st.session_state.selected_pair)
    if mstat is None: st.warning("تعذر التحميل.")
    else:
        ms1, ms2, ms3, ms4 = st.columns(4)
        with ms1:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">📈 الاتجاه</div>
                <div class="tool-value">{mstat['trend_icon']}</div>
                <div class="tool-desc">{mstat['trend_align']}</div></div>""", unsafe_allow_html=True)
        with ms2:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">🌊 التقلب</div>
                <div class="tool-value">{mstat['vol_icon']} {mstat['vol_state']}</div>
                <div class="tool-desc">ATR ratio: <b>{mstat['atr_ratio']:.2f}×</b></div></div>""", unsafe_allow_html=True)
        with ms3:
            reg_icon = trend_icon(mstat["regime"])
            st.markdown(f"""<div class="tool-card"><div class="tool-name">🎯 النظام</div>
                <div class="tool-value">{reg_icon} {mstat['regime']}</div>
                <div class="tool-desc">الهيكل: <b>{mstat['structure']}</b></div></div>""", unsafe_allow_html=True)
        with ms4:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">⚖️ الحالة</div>
                <div class="tool-value">{mstat['overall_icon']}</div>
                <div class="tool-desc">{mstat['overall']}</div></div>""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.caption(f"Version {APP_VERSION}")
    st.markdown("---")
    st.markdown("**💰 Fundamental + Models**")
    st.caption("• Currency Strength + Rates")
    st.caption("• Risk Sentiment (VIX)")
    st.caption("• Monte Carlo Simulation")
    st.markdown("---")
    st.markdown("**🔗 Correlation Guard**")
    st.caption(f"• Block threshold: {CORRELATION_BLOCK_THRESHOLD}")
    st.caption(f"• Max per currency: {MAX_SAME_CURRENCY_EXPOSURE}")
    st.caption(f"• Open positions: {len(st.session_state.get('open_positions', []))}")
    st.markdown("---")
    st.markdown("**🛑 Kill Switch**")
    kill_blocked, consec = check_kill_switch()
    if kill_blocked: st.error(f"🚫 نشط — {consec} خسائر")
    else: st.success(f"✅ Disciplined ({consec}/{MAX_CONSECUTIVE_LOSSES})")
    if st.button("🗑️ Reset Kill Switch", width="stretch", key="reset_kill"):
        st.session_state.recent_results = []
        st.toast("✅ تم إعادة التعيين"); st.rerun()
    st.markdown("---")
    strict_mode = st.checkbox("🔒 Strict Filters",
        value=st.session_state.get("strict_filters", False))
    st.session_state.strict_filters = strict_mode
    st.markdown("---")
    if st.button("🔄 Refresh Cache", width="stretch"):
        st.cache_data.clear(); st.rerun()


st.markdown('<div class="section-title">🎯 Analysis Control</div>', unsafe_allow_html=True)
ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2.2, 1, 1])
with ctrl_col1:
    selected_pair = st.selectbox("🎯 اختر الأصل للتحليل", list(PAIRS.keys()),
        index=list(PAIRS.keys()).index(st.session_state.selected_pair)
        if st.session_state.selected_pair in PAIRS else 0, key="main_pair_selector")
    st.session_state.selected_pair = selected_pair
    symbol = PAIRS[selected_pair]
with ctrl_col2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    analyze_this = st.button("🎯 تحليل الأصل", width="stretch", key="btn_analyze_one")
with ctrl_col3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    analyze_all = st.button("🌐 تحليل الكل", width="stretch", key="btn_analyze_all")

if analyze_all:
    with st.spinner("🌐 Scanning..."):
        start = time.time()
        st.session_state.all_signals = get_all_signals_parallel()
        st.session_state.analyzing_all = True
        st.session_state.analysis_time = time.time() - start
if analyze_this:
    st.cache_data.clear(); st.rerun()

if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
    st.markdown('<div class="section-title">🌐 All Assets Scan</div>', unsafe_allow_html=True)
    res_col1, res_col2 = st.columns([4, 1])
    with res_col1:
        st.success(f"✅ تم تحليل {len(st.session_state.all_signals)} أصلاً.")
    with res_col2:
        if st.button("🗑️ مسح", width="stretch", key="clear_all"):
            st.session_state.all_signals = None; st.rerun()
    st.dataframe(st.session_state.all_signals, hide_index=True, width="stretch", height=440)
    st.markdown("---")


current_price, change = get_spot_price(symbol)
if current_price is None: st.error(f"تعذر السعر لـ {selected_pair}."); st.stop()
df_raw = get_historical_data(symbol, "3mo", "4h")
if df_raw is None: st.error(f"تعذر البيانات لـ {selected_pair}."); st.stop()

news_block, _ = news_time_block(st.session_state.economic_events or [], selected_pair)
strict_soft = st.session_state.get("strict_filters", False)

_ccy_strength = get_currency_strength_matrix()
_rate_diff, _rate_msg = get_interest_rate_differential(selected_pair)
_risk = get_risk_sentiment()

result = generate_signal(df_raw, current_price, selected_pair, symbol,
                         news_block=news_block, strict_soft=strict_soft)
df = result["df"]; levels = result["levels"]
signal = result["signal"]; confidence = result["confidence"]


# ---- Status Banners ----
mkt_open, mkt_msg = is_market_open(selected_pair)
if not mkt_open: st.error(f"🚫 **{mkt_msg}** — الإشارات معلّقة.")
kill_blocked, consec = check_kill_switch()
if kill_blocked: st.error(f"🛑 **Kill Switch نشط** — {consec} خسائر متتالية.")

if signal in ("BUY", "SELL") and st.session_state.get("open_positions"):
    corr_check = check_portfolio_conflict(symbol, signal, selected_pair,
                                           st.session_state.open_positions)
    if corr_check["blocked"]:
        st.error(f"🚫 **Portfolio Conflict** — الدخول محظور:")
        for w in corr_check["warnings"]: st.markdown(f"- {w}")
    elif corr_check["warnings"]:
        st.warning(f"⚠️ **Correlation Warnings:**")
        for w in corr_check["warnings"]: st.markdown(f"- {w}")


col_signal, col_stats = st.columns([1.6, 1])
with col_signal:
    signal_color = ("#7cd4a0" if signal == "BUY"
                    else "#f57a7a" if signal == "SELL" else "#f5c87a")
    exec_color = ("#7cd4a0" if result["execution_status"] == "EXECUTE"
                  else "#f5c87a" if result["execution_status"] in ("WATCH", "WAIT") else "#f57a7a")
    st.markdown(f"""
    <div class="signal-card">
        <div class="signal-meta">BLACK PYRAMID · {selected_pair}</div>
        <div class="signal-value" style="color:{signal_color};">{signal}</div>
        <div class="signal-conf">Confidence: <b>{confidence:.1f}%</b></div>
        <div class="signal-grade">Grade: {result['trade_grade']}</div>
        <div class="signal-meta" style="margin-top:14px;">
            Execution: <b style="color:{exec_color};">{result['execution_status']}</b>
            &nbsp;·&nbsp; {result['execution_reason']}
        </div>
    </div>""", unsafe_allow_html=True)

with col_stats:
    st.markdown(f"""
    <div class="metric-card" style="margin-bottom:14px;">
        <div class="metric-label">Current Price</div>
        <div class="metric-value">{fmt_price(current_price, selected_pair)}</div>
        <div class="metric-sub">Change: {change:+.2f}%</div>
    </div>""", unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">BUY</div>
            <div class="metric-value" style="color:#7cd4a0;">{result['buy_score']:.0f}</div></div>""",
            unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">SELL</div>
            <div class="metric-value" style="color:#f57a7a;">{result['sell_score']:.0f}</div></div>""",
            unsafe_allow_html=True)
    st.markdown(f"""
    <div class="metric-card" style="margin-top:14px;">
        <div class="metric-label">Confluence</div>
        <div class="metric-value">{result['weighted_confluence']:.0f} <span style="font-size:1rem; color:#6b7488;">/ 100</span></div>
        <div class="metric-sub">Confirmation: {result['confirmation_score']:.1f}</div>
    </div>""", unsafe_allow_html=True)

soft_adv = result.get("soft_advisories", "None")
if soft_adv and soft_adv != "None":
    if not strict_soft: st.info(f"💡 **Advisories:** {soft_adv}")
    else: st.warning(f"⚠️ **Strict — ({result['soft_penalties']:.1f}):** {soft_adv}")


if signal in ("BUY", "SELL") and levels:
    src = levels.get("sources", {})
    st.markdown('<div class="section-title">🎯 Trade Plan <span>Fibonacci · Pivot · S/R</span></div>',
                unsafe_allow_html=True)
    lc1, lc2, lc3, lc4, lc5 = st.columns(5)
    lc1.metric("Entry", fmt_price(levels["entry"], selected_pair))
    lc2.metric("Stop Loss", fmt_price(levels["stop_loss"], selected_pair))
    lc3.metric("TP1", fmt_price(levels["target1"], selected_pair), help=src.get("tp1", ""))
    lc4.metric("TP2", fmt_price(levels["target2"], selected_pair), help=src.get("tp2", ""))
    lc5.metric("TP3", fmt_price(levels["target3"], selected_pair), help=src.get("tp3", ""))
    rc1, rc2, rc3, _ = st.columns([1, 1, 1, 2])
    rc1.metric("RR · TP1", f"1:{levels['risk_reward_1']:.2f}")
    rc2.metric("RR · TP2", f"1:{levels['risk_reward_2']:.2f}")
    rc3.metric("RR · TP3", f"1:{levels['risk_reward_3']:.2f}")

    st.markdown(f"""
    <div style="margin-top:14px; display:flex; gap:10px; flex-wrap:wrap;">
        <span style="background:rgba(230,200,124,0.15); padding:5px 14px;
                     border-radius:20px; color:#e6c87c; font-size:0.82rem;
                     border:1px solid rgba(230,200,124,0.3);">
            🎯 TP1: {src.get('tp1','—')}</span>
        <span style="background:rgba(124,212,160,0.12); padding:5px 14px;
                     border-radius:20px; color:#7cd4a0; font-size:0.82rem;
                     border:1px solid rgba(124,212,160,0.3);">
            🎯 TP2: {src.get('tp2','—')}</span>
        <span style="background:rgba(124,212,160,0.12); padding:5px 14px;
                     border-radius:20px; color:#7cd4a0; font-size:0.82rem;
                     border:1px solid rgba(124,212,160,0.3);">
            🎯 TP3: {src.get('tp3','—')}</span>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-title">💰 Position Size Calculator</div>',
                unsafe_allow_html=True)
    ps_col1, ps_col2 = st.columns(2)
    with ps_col1:
        account_balance = st.number_input("💵 الرصيد (USD)", min_value=100.0,
            value=10000.0, step=500.0, key=f"balance_{selected_pair}")
    with ps_col2:
        risk_pct = st.number_input("⚠️ المخاطرة %", min_value=0.25, max_value=5.0,
            value=1.0, step=0.25, key=f"risk_{selected_pair}")
    ps = calc_position_size(account_balance, risk_pct, levels["entry"],
                            levels["stop_loss"], selected_pair)
    if ps:
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("💵 المخاطرة", f"${ps['risk_amount']:.2f}")
        p2.metric("📏 الستوب", f"{ps.get('sl_pips', ps['sl_distance']):.1f}")
        if ps["asset"] == "crypto":
            p3.metric("🪙 الكمية", f"{ps['units']:.6f}")
            p4.metric("📊 الوحدة", "Coins")
        else:
            p3.metric("📦 اللوتات", f"{ps['lots']:.2f}")
            p4.metric("📊 الوحدة", ps["unit_label"])

    st.markdown('<div class="section-title">📋 Trade Management</div>', unsafe_allow_html=True)
    mgmt = build_trade_management(signal, levels, profile_for(selected_pair))
    if mgmt:
        mg_cols = st.columns(3)
        for idx, stage in enumerate(mgmt):
            with mg_cols[idx]:
                st.markdown(f"""<div class="tool-card">
                    <div class="tool-name">{stage['icon']} {stage['stage']}</div>
                    <div class="tool-value" style="font-size:1rem;">{stage['action']}</div>
                    <div class="tool-desc">{stage['details']}</div></div>""", unsafe_allow_html=True)

    # ---- Add to Portfolio ----
    st.markdown('<div class="section-title">📌 Portfolio Action</div>', unsafe_allow_html=True)
    corr_status = None
    if st.session_state.get("open_positions"):
        corr_status = check_portfolio_conflict(symbol, signal, selected_pair,
                                                 st.session_state.open_positions)
    pa1, pa2, pa3 = st.columns([1, 1, 2])
    with pa1:
        lot_input = st.number_input("📦 حجم المركز", min_value=0.01,
            value=1.0, step=0.1, key=f"lot_{selected_pair}")
    with pa2:
        can_open = not (corr_status and corr_status["blocked"])
        if can_open:
            if st.button("📌 فتح صفقة", width="stretch", key="open_pos"):
                if add_open_position(result, selected_pair, symbol, lot_input):
                    st.success("✅ تم إضافة الصفقة"); st.rerun()
        else:
            st.button("🚫 محظور", width="stretch", disabled=True, key="open_pos_disabled")
    with pa3:
        if corr_status and corr_status["blocked"]:
            st.error("🚫 تعارض مع مراكز مفتوحة")
        elif corr_status and corr_status["warnings"]:
            st.warning("⚠️ تحذيرات ارتباط — راجع Portfolio tab")
        else:
            st.info("💡 أضف الصفقة لتتبعها")


# ============================================================
# TABS
# ============================================================

tab_overview, tab_tools, tab_smc, tab_mtf, tab_fund, tab_portfolio, tab_filters, tab_chart, tab_calendar, tab_journal, tab_backtest = st.tabs([
    "📊 Overview", "🧰 Tools", "🏛️ SMC", "⏱️ MTF",
    "💰 Fundamentals", "💼 Portfolio", "🎛️ Filters", "📈 Chart",
    "📅 Calendar", "📔 Journal", "🔬 Backtest",
])


with tab_overview:
    st.markdown('<div class="section-title">🧠 The Five Pillars</div>', unsafe_allow_html=True)
    pillar_names = {"structure": "Structure", "trend": "Trend",
                    "momentum": "Momentum", "volume": "Volume & Flow", "context": "Context"}
    cols = st.columns(5)
    for idx, pillar in enumerate(PILLAR_WEIGHTS):
        b = result["pillars"]["BUY"][pillar]; s = result["pillars"]["SELL"][pillar]
        cols[idx].metric(pillar_names[pillar], f"B {b:.0f}",
                         delta=f"S {s:.0f}", delta_color="inverse")
    st.markdown('<div class="section-title">📝 Decision Reasons</div>', unsafe_allow_html=True)
    if result["reasons"]:
        for reason in result["reasons"][:10]: st.markdown(f"- {reason}")
    else: st.caption("لا توجد أسباب.")
    st.markdown('<div class="section-title">🛡️ Confirmation Gate</div>', unsafe_allow_html=True)
    gc1, gc2, gc3 = st.columns(3)
    gc1.metric("Confirmation", f"{result['confirmation_score']:.1f}/100")
    gc2.metric("Gate", "✅ PASS" if result["confirmation_ok"] else "⚠️ SOFT")
    gc3.metric("Raw / Eff", f"{result['raw_confidence']:.1f} / {result['confidence']:.1f}")


with tab_tools:
    last = df.iloc[-1]
    st.markdown('<div class="section-title">📈 Trend Tools</div>', unsafe_allow_html=True)
    ema20 = safe_float(last.get("ema20")); ema50 = safe_float(last.get("ema50"))
    ema200 = safe_float(last.get("ema200"))
    if ema20 > ema50 > ema200: ema_state = "Fully Bullish"; ema_icon = "🟢"
    elif ema20 < ema50 < ema200: ema_state = "Fully Bearish"; ema_icon = "🔴"
    elif ema20 > ema50: ema_state = "Short-term Bullish"; ema_icon = "🟡"
    else: ema_state = "Short-term Bearish"; ema_icon = "🟡"
    vwap = safe_float(last.get("vwap"))
    vwap_type = last.get("vwap_type", "session")
    vwap_state = "Above VWAP" if current_price > vwap else "Below VWAP"
    vwap_icon = "🟢" if current_price > vwap else "🔴"
    vwap_label = "Rolling(20)" if vwap_type == "rolling" else "Session"
    t1, t2 = st.columns(2)
    with t1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📊 EMA</div>
            <div class="tool-value">{ema_icon} {ema_state}</div>
            <div class="tool-desc">EMA20: <b>{ema20:.5f}</b><br>EMA50: <b>{ema50:.5f}</b><br>
            EMA200: <b>{ema200:.5f}</b></div></div>""", unsafe_allow_html=True)
    with t2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📉 VWAP · {vwap_label}</div>
            <div class="tool-value">{vwap_icon} {vwap_state}</div>
            <div class="tool-desc">VWAP: <b>{vwap:.5f}</b><br>
            Distance: <b>{((current_price-vwap)/vwap*100):+.2f}%</b></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚡ Momentum</div>', unsafe_allow_html=True)
    rsi = safe_float(last.get("rsi"), 50); macd_hist = safe_float(last.get("macd_histogram"))
    if rsi >= 70: rsi_state = "Overbought"; rsi_icon = "🔴"
    elif rsi <= 30: rsi_state = "Oversold"; rsi_icon = "🟢"
    elif rsi >= 55: rsi_state = "Bullish"; rsi_icon = "🟢"
    elif rsi <= 45: rsi_state = "Bearish"; rsi_icon = "🔴"
    else: rsi_state = "Neutral"; rsi_icon = "🟡"
    macd_state = "Bullish" if macd_hist > 0 else "Bearish"
    macd_icon = "🟢" if macd_hist > 0 else "🔴"
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🎯 RSI</div>
            <div class="tool-value">{rsi_icon} {rsi:.1f}</div>
            <div class="tool-desc">{rsi_state}</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📈 MACD</div>
            <div class="tool-value">{macd_icon} {macd_state}</div>
            <div class="tool-desc">Hist: <b>{macd_hist:.5f}</b></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌊 Volatility</div>', unsafe_allow_html=True)
    atr_val = safe_float(last.get("atr")); atr_pct = (atr_val / current_price * 100) if current_price else 0
    bb_up = safe_float(last.get("bb_upper")); bb_low = safe_float(last.get("bb_lower"))
    bb_width = ((bb_up - bb_low) / current_price * 100) if current_price else 0
    if bb_width < 1.5: bb_state = "Compression"
    elif bb_width > 5.0: bb_state = "Expansion"
    else: bb_state = "Normal"
    v1, v2 = st.columns(2)
    with v1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📊 ATR</div>
            <div class="tool-value">{atr_val:.5f}</div>
            <div class="tool-desc">ATR %: <b>{atr_pct:.3f}%</b></div></div>""", unsafe_allow_html=True)
    with v2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📉 Bollinger</div>
            <div class="tool-value">{bb_state}</div>
            <div class="tool-desc">Width: <b>{bb_width:.2f}%</b></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">💧 Volume & Flow</div>', unsafe_allow_html=True)
    cmf = safe_float(last.get("chaikin_mf"), 0)
    cmf_state = "Accumulation" if cmf > 0 else "Distribution"
    cmf_icon = "🟢" if cmf > 0 else "🔴"
    vol_avg = df["volume"].rolling(20).mean().iloc[-1]
    vol_now = safe_float(last.get("volume"), 0)
    vol_ratio = (vol_now / vol_avg) if vol_avg > 0 else 1.0
    cf1, cf2 = st.columns(2)
    with cf1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">💰 Chaikin MF</div>
            <div class="tool-value">{cmf_icon} {cmf:+.3f}</div>
            <div class="tool-desc">{cmf_state}</div></div>""", unsafe_allow_html=True)
    with cf2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📊 Volume Ratio</div>
            <div class="tool-value">{vol_ratio:.2f}x</div>
            <div class="tool-desc">vs 20-avg</div></div>""", unsafe_allow_html=True)


with tab_smc:
    last = df.iloc[-1]
    st.markdown('<div class="section-title">🏛️ SMC</div>', unsafe_allow_html=True)
    struct = structure_state(df)
    struct_icon = trend_icon(struct["state"])
    st.markdown(f"""<div class="tool-card" style="margin-bottom:20px;">
        <div class="tool-name">🏗️ Market Structure</div>
        <div class="tool-value">{struct_icon} {struct['state']}</div>
        <div class="tool-desc">Last swing highs/lows</div></div>""", unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        bos_bull = safe_bool(last.get("bos_bullish")); bos_bear = safe_bool(last.get("bos_bearish"))
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🔓 BOS</div>
            <div class="tool-value">{"🟢" if bos_bull else "🔴" if bos_bear else "⚪"}</div>
            <div class="tool-desc">{"Bullish" if bos_bull else "Bearish" if bos_bear else "None"}</div></div>""",
            unsafe_allow_html=True)
    with s2:
        mss_bull = safe_bool(last.get("mss_bullish")); mss_bear = safe_bool(last.get("mss_bearish"))
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🔄 MSS</div>
            <div class="tool-value">{"🟢" if mss_bull else "🔴" if mss_bear else "⚪"}</div>
            <div class="tool-desc">{"Bullish" if mss_bull else "Bearish" if mss_bear else "None"}</div></div>""",
            unsafe_allow_html=True)
    with s3:
        liq_bull = safe_bool(last.get("liquidity_sweep_bullish")); liq_bear = safe_bool(last.get("liquidity_sweep_bearish"))
        st.markdown(f"""<div class="tool-card"><div class="tool-name">💧 Liquidity</div>
            <div class="tool-value">{"🟢" if liq_bull else "🔴" if liq_bear else "⚪"}</div>
            <div class="tool-desc">{"Bullish" if liq_bull else "Bearish" if liq_bear else "None"}</div></div>""",
            unsafe_allow_html=True)
    with s4:
        fvg_bull = safe_bool(last.get("fvg_bullish")); fvg_bear = safe_bool(last.get("fvg_bearish"))
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🌫️ FVG</div>
            <div class="tool-value">{"🟢" if fvg_bull else "🔴" if fvg_bear else "⚪"}</div>
            <div class="tool-desc">{"Bullish" if fvg_bull else "Bearish" if fvg_bear else "None"}</div></div>""",
            unsafe_allow_html=True)
    smc_score, smc_reasons = smc_quality(df)
    st.markdown(f"""<div class="tool-card" style="margin-top:20px;">
        <div class="tool-name">⭐ SMC Quality</div>
        <div class="tool-value">{smc_score:.0f}/100</div>
        <div class="tool-desc">Factors: {', '.join(smc_reasons) if smc_reasons else 'None'}</div></div>""",
        unsafe_allow_html=True)


with tab_mtf:
    st.markdown('<div class="section-title">⏱️ MTF Analysis</div>', unsafe_allow_html=True)
    mtf_cols = st.columns(4)
    for idx, (tf, info) in enumerate(result["mtf_details"].items()):
        bias = info["bias"]
        icon = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "🟡"
        color = "#7cd4a0" if bias == "BULLISH" else "#f57a7a" if bias == "BEARISH" else "#f5c87a"
        with mtf_cols[idx]:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">{tf}</div>
                <div class="tool-value" style="color:{color};">{icon} {bias}</div>
                <div class="tool-desc">Strength: <b>{info['strength']}/10</b></div></div>""",
                unsafe_allow_html=True)
    final_mtf = result["mtf_bias"]
    final_icon = "🟢" if final_mtf == "BULLISH" else "🔴" if final_mtf == "BEARISH" else "🟡"
    st.markdown(f"""<div class="tool-card" style="margin-top:20px;">
        <div class="tool-name">🎯 MTF Consensus</div>
        <div class="tool-value">{final_icon} {final_mtf}</div>
        <div class="tool-desc">Confidence: <b>{result['mtf_conf']:.1f}%</b></div></div>""",
        unsafe_allow_html=True)


with tab_fund:
    st.markdown('<div class="section-title">💪 Currency Strength Matrix</div>', unsafe_allow_html=True)
    if _ccy_strength:
        sorted_ccys = sorted(_ccy_strength.items(), key=lambda x: x[1], reverse=True)
        ccy_cols = st.columns(len(sorted_ccys))
        for idx, (ccy, score) in enumerate(sorted_ccys):
            if score > 20: color = "#7cd4a0"; state = "STRONG"
            elif score > 5: color = "#a0d4b0"; state = "Mild Bull"
            elif score < -20: color = "#f57a7a"; state = "WEAK"
            elif score < -5: color = "#d4a0a0"; state = "Mild Bear"
            else: color = "#f5c87a"; state = "Neutral"
            with ccy_cols[idx]:
                st.markdown(f"""<div class="tool-card"><div class="tool-name">{ccy}</div>
                    <div class="tool-value" style="color:{color}; font-size:1.1rem;">{score:+.0f}</div>
                    <div class="tool-desc">{state}</div></div>""", unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">🏦 Interest Rate Differential</div>', unsafe_allow_html=True)
    base, quote = parse_pair_currencies(selected_pair)
    if base and quote and base in CENTRAL_BANK_RATES and quote in CENTRAL_BANK_RATES:
        ri1, ri2, ri3 = st.columns(3)
        ri1.metric(f"{base} Rate", f"{CENTRAL_BANK_RATES[base]:.2f}%")
        ri2.metric(f"{quote} Rate", f"{CENTRAL_BANK_RATES[quote]:.2f}%")
        ri3.metric("Diff", f"{_rate_diff:+.2f}%")
        if _rate_diff > 1.0: st.success(f"✅ فرق فائدة يدعم {base}")
        elif _rate_diff < -1.0: st.warning(f"⚠️ فرق فائدة يضغط على {base}")
        else: st.info(f"ℹ️ فرق محايد ({_rate_diff:+.2f}%)")
    
    st.markdown('<div class="section-title">🌊 Risk Sentiment</div>', unsafe_allow_html=True)
    if _risk and _risk.get("vix") is not None:
        rs1, rs2, rs3, rs4 = st.columns(4)
        rs1.metric("VIX", f"{_risk['vix']:.2f}")
        rs2.metric("VIX 20-avg", f"{_risk.get('vix_avg', 0):.2f}")
        rs3.metric("Change", f"{_risk.get('vix_change', 0):+.2f}%")
        rs4.metric("State", _risk["vix_state"])
        if _risk["risk_mode"] == "RISK-OFF":
            st.error(f"🛑 RISK-OFF — يفضل USD/JPY/CHF")
        elif _risk["risk_mode"] == "RISK-ON":
            st.success(f"✅ RISK-ON — يفضل AUD/NZD/CAD")
        else: st.info(f"⚖️ Neutral Risk")
    
    st.markdown('<div class="section-title">🎯 Fundamental Impact</div>', unsafe_allow_html=True)
    fb = result.get("fund_buy", 0); fs = result.get("fund_sell", 0)
    fsum1, fsum2, fsum3 = st.columns(3)
    fsum1.metric("BUY bias", f"{fb:.0f}/100")
    fsum2.metric("SELL bias", f"{fs:.0f}/100")
    if fb > fs + 15: verdict = "🟢 يدعم BUY"
    elif fs > fb + 15: verdict = "🔴 يدعم SELL"
    else: verdict = "⚖️ محايد"
    fsum3.metric("Verdict", verdict)


with tab_portfolio:
    st.markdown('<div class="section-title">💼 Portfolio Monitor</div>', unsafe_allow_html=True)
    open_positions = st.session_state.get("open_positions", [])
    if not open_positions:
        st.info("📭 لا توجد صفقات مفتوحة. أضف صفقات من قسم Trade Plan.")
    else:
        sm1, sm2, sm3, sm4 = st.columns(4)
        total_pos = len(open_positions)
        long_count = sum(1 for p in open_positions if p["direction"] == "BUY")
        short_count = sum(1 for p in open_positions if p["direction"] == "SELL")
        total_lots = sum(p.get("lot_size") or 0 for p in open_positions)
        sm1.metric("Total Positions", total_pos)
        sm2.metric("Long", long_count)
        sm3.metric("Short", short_count)
        sm4.metric("Total Lots", f"{total_lots:.2f}")

        st.markdown('<div class="section-title">📋 Open Positions</div>', unsafe_allow_html=True)
        pos_rows = []
        for p in open_positions:
            pos_rows.append({"ID": p["id"], "Pair": p["pair"], "Dir": p["direction"],
                             "Entry": fmt_price(p.get("entry"), p["pair"]),
                             "SL": fmt_price(p.get("stop_loss"), p["pair"]),
                             "TP1": fmt_price(p.get("target1"), p["pair"]),
                             "Grade": p.get("grade", "?"),
                             "Lots": p.get("lot_size", 1.0),
                             "Opened": p.get("opened_at", "")})
        st.dataframe(pd.DataFrame(pos_rows), hide_index=True, width="stretch")

        st.markdown("**إغلاق صفقة:**")
        close_cols = st.columns(min(len(open_positions), 5))
        for idx, p in enumerate(open_positions[:5]):
            with close_cols[idx]:
                if st.button(f"❌ #{p['id']} {p['pair'][:10]}",
                             width="stretch", key=f"close_{p['id']}"):
                    close_open_position(p["id"])
                    st.toast(f"✅ تم إغلاق صفقة #{p['id']}"); st.rerun()

        st.markdown('<div class="section-title">🌍 Currency Exposure</div>', unsafe_allow_html=True)
        exposure = get_portfolio_exposure()
        if exposure:
            exp_cols = st.columns(min(len(exposure), 6))
            for idx, (ccy, exp) in enumerate(sorted(exposure.items())):
                net = exp["net"]
                if net > 0.5: color = "#7cd4a0"; state = "LONG"
                elif net < -0.5: color = "#f57a7a"; state = "SHORT"
                else: color = "#f5c87a"; state = "NEUTRAL"
                with exp_cols[idx % 6]:
                    st.markdown(f"""<div class="tool-card"><div class="tool-name">{ccy}</div>
                        <div class="tool-value" style="color:{color}; font-size:1.1rem;">{net:+.1f}</div>
                        <div class="tool-desc">{state} · {exp['count']} صفقات</div></div>""",
                        unsafe_allow_html=True)

        st.markdown('<div class="section-title">🔗 Correlation Matrix</div>', unsafe_allow_html=True)
        unique_symbols = list({p["symbol"] for p in open_positions})
        if len(unique_symbols) >= 2:
            try:
                matrix, symbols = build_correlation_matrix(tuple(unique_symbols))
                pair_names = []
                for sym in symbols:
                    found = [p["pair"] for p in open_positions if p["symbol"] == sym]
                    pair_names.append(found[0] if found else sym)
                fig_corr = go.Figure(data=go.Heatmap(
                    z=matrix, x=pair_names, y=pair_names,
                    colorscale=[[0.0, "#f57a7a"], [0.5, "#0d1017"], [1.0, "#7cd4a0"]],
                    zmid=0, zmin=-1, zmax=1, text=np.round(matrix, 2),
                    texttemplate="%{text}", textfont={"size": 12, "color": "white"},
                    colorbar=dict(title="Corr")))
                fig_corr.update_layout(height=400, template="plotly_dark",
                    paper_bgcolor="#0a0d13", plot_bgcolor="#0a0d13",
                    font=dict(family="Inter", color="#c8d2e8"),
                    margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_corr, width="stretch")

                st.markdown("**🔍 Conflicts:**")
                conflicts_found = False
                for i in range(len(symbols)):
                    for j in range(i + 1, len(symbols)):
                        corr_val = matrix[i, j]
                        if abs(corr_val) >= CORRELATION_THRESHOLD:
                            p_i = next((p for p in open_positions if p["symbol"] == symbols[i]), None)
                            p_j = next((p for p in open_positions if p["symbol"] == symbols[j]), None)
                            if p_i and p_j and p_i["direction"] == p_j["direction"]:
                                conflicts_found = True
                                severity = "🚫" if abs(corr_val) >= CORRELATION_BLOCK_THRESHOLD else "⚠️"
                                st.markdown(f"{severity} **{pair_names[i]}** + **{pair_names[j]}** "
                                            f"→ {corr_val:+.2f} · {p_i['direction']}")
                if not conflicts_found: st.success("✅ لا تعارضات حرجة")
            except Exception as e:
                st.warning(f"تعذر بناء المصفوفة: {e}")
        else: st.info("ℹ️ تحتاج ≥ 2 صفقات.")

    st.markdown("---")
    if st.button("🗑️ Clear All Positions", width="stretch", key="clear_all_positions"):
        st.session_state.open_positions = []; st.rerun()


with tab_filters:
    st.markdown('<div class="section-title">🎛️ Filters</div>', unsafe_allow_html=True)
    filters = result["filter_results"]; items = list(filters.items())
    for row_start in range(0, len(items), 4):
        row = items[row_start:row_start + 4]; cols = st.columns(4)
        for idx, (name, info) in enumerate(row):
            passed = info.get("pass", True); icon = "✅" if passed else "❌"
            with cols[idx]:
                st.markdown(f"""<div class="tool-card"><div class="tool-name">{name}</div>
                    <div class="tool-value">{icon}</div>
                    <div class="tool-desc">{info.get('msg', '')[:60]}</div></div>""",
                    unsafe_allow_html=True)
    if not result["all_filters_passed"]:
        st.error(f"🚫 **Block:** {result['filter_block_reason']}")


with tab_chart:
    st.markdown('<div class="section-title">📈 Chart</div>', unsafe_allow_html=True)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.04, row_heights=[0.60, 0.20, 0.20])
    fig.add_trace(go.Candlestick(x=df.index, open=df["open"], high=df["high"],
                                  low=df["low"], close=df["close"], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["ema20"], name="EMA20",
                              line=dict(color="#7cd4a0", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["ema50"], name="EMA50",
                              line=dict(color="#f5c87a", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["ema200"], name="EMA200",
                              line=dict(color="#e6c87c", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["vwap"], name="VWAP",
                              line=dict(color="#a0aab8", dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Up",
                              line=dict(color="#6b7488", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Low",
                              line=dict(color="#6b7488", width=1),
                              fill="tonexty", fillcolor="rgba(107,116,136,0.05)"), row=1, col=1)
    if levels and levels.get("impulse"):
        imp = levels["impulse"]; start, end, leg = imp["start"], imp["end"], imp["leg"]
        if imp["direction"] == "BUY":
            ote_low = end - 0.786 * leg; ote_high = end - 0.618 * leg
        else:
            ote_low = end + 0.618 * leg; ote_high = end + 0.786 * leg
        fig.add_hrect(y0=min(ote_low, ote_high), y1=max(ote_low, ote_high),
                      line_width=0, fillcolor="rgba(230,200,124,0.10)",
                      annotation_text="OTE Zone", annotation_position="top left",
                      row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                              line=dict(color="#7cd4a0")), row=2, col=1)
    _profile = profile_for(selected_pair)
    fig.add_hline(y=_profile["rsi_ob"], row=2, col=1, line_dash="dash",
                  line_color="#f57a7a", opacity=0.5)
    fig.add_hline(y=_profile["rsi_os"], row=2, col=1, line_dash="dash",
                  line_color="#7cd4a0", opacity=0.5)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                              line=dict(color="#7cd4a0")), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal",
                              line=dict(color="#f5c87a")), row=3, col=1)
    colors = ["#7cd4a0" if v >= 0 else "#f57a7a" for v in df["macd_histogram"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["macd_histogram"], name="Hist",
                         marker_color=colors), row=3, col=1)
    if levels:
        for lvl, color, label in [("stop_loss", "#f57a7a", "SL"),
                                   ("target1", "#7cd4a0", "TP1"),
                                   ("target2", "#7cd4a0", "TP2"),
                                   ("target3", "#7cd4a0", "TP3")]:
            fig.add_hline(y=levels[lvl], row=1, col=1, line_dash="dot",
                          line_color=color, opacity=0.7,
                          annotation_text=label, annotation_position="right")
    fig.update_layout(height=850, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0a0d13", plot_bgcolor="#0a0d13",
        font=dict(family="Inter", color="#c8d2e2"),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, width="stretch")


with tab_calendar:
    st.markdown('<div class="section-title">📅 Economic Calendar</div>', unsafe_allow_html=True)
    if st.button("🔄 Update Calendar", width="stretch"):
        st.session_state.economic_events = get_fmp_economic_calendar()
    if st.session_state.economic_events:
        st.caption(event_risk_message(st.session_state.economic_events, selected_pair))
        rows = [{"Country": e.get("country", ""), "Event": e.get("event", ""),
                 "Impact": e.get("impact", ""), "Date": e.get("date", ""),
                 "Time": e.get("time", "")}
                for e in st.session_state.economic_events[:20]]
        if rows:
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else: st.info("اضغط 'Update Calendar'.")


with tab_journal:
    st.markdown('<div class="section-title">📔 Trade Journal</div>', unsafe_allow_html=True)
    if not st.session_state.trade_journal:
        st.info("لا توجد صفقات مسجّلة.")
    else:
        journal_df = pd.DataFrame(st.session_state.trade_journal)
        st.dataframe(journal_df, hide_index=True, width="stretch")
        total = len(journal_df); wins = (journal_df["outcome"] == "WIN").sum()
        losses = (journal_df["outcome"] == "LOSS").sum()
        wr = (wins / total * 100) if total > 0 else 0
        jc1, jc2, jc3 = st.columns(3)
        jc1.metric("Total", total); jc2.metric("Win Rate", f"{wr:.1f}%")
        jc3.metric("W/L", f"{wins}/{losses}")
    st.markdown("---")
    rec1, rec2, rec3 = st.columns(3)
    with rec1:
        if st.button("✅ WIN", width="stretch", key="log_win"):
            log_trade_result(result, "WIN"); st.rerun()
    with rec2:
        if st.button("❌ LOSS", width="stretch", key="log_loss"):
            log_trade_result(result, "LOSS"); st.rerun()
    with rec3:
        if st.button("🗑️ Clear", width="stretch", key="clear_journal"):
            st.session_state.trade_journal = []
            st.session_state.recent_results = []; st.rerun()


with tab_backtest:
    st.markdown('<div class="section-title">🔬 Backtest + Monte Carlo</div>', unsafe_allow_html=True)
    if st.button("▶️ Run Backtest", width="stretch"):
        with st.spinner("Running..."):
            st.session_state.backtest_results = quick_backtest(symbol, selected_pair)
        st.rerun()
    if st.session_state.backtest_results:
        bt = st.session_state.backtest_results
        if bt.get("error"): st.error(f"فشل: {bt['error']}")
        else:
            bc1, bc2, bc3, bc4, bc5 = st.columns(5)
            bc1.metric("Trades", bt["trades"]); bc2.metric("WR", f"{bt['win_rate']:.1f}%")
            bc3.metric("Total R", f"{bt['total_R']:.2f}")
            bc4.metric("Expectancy", f"{bt['expectancy']:.3f}R")
            bc5.metric("PF", f"{bt['profit_factor']:.2f}")
            bc6, bc7, bc8 = st.columns(3)
            bc6.metric("Max DD", f"{bt['max_drawdown']:.2f}R")
            bc7.metric("Sharpe", f"{bt['sharpe']:.2f}")
            bc8.metric("Avg R", f"{bt['avg_r']:.3f}")
            mc = bt.get("monte_carlo")
            if mc:
                st.markdown("**🎲 Monte Carlo**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Mean", f"{mc['mean_final']:.2f}R")
                m2.metric("Median", f"{mc['median_final']:.2f}R")
                m3.metric("Prob Profit", f"{mc['prob_profit']:.1f}%")
                m4, m5, m6 = st.columns(3)
                m4.metric("5th Pct", f"{mc['p5_final']:.2f}R")
                m5.metric("95th Pct", f"{mc['p95_final']:.2f}R")
                m6.metric("Worst DD", f"{mc['worst_dd']:.2f}R")


st.markdown(f"""
<div class="footer-style">
    ▲ BLACK PYRAMID {APP_VERSION} ▲<br>
    Correlation Guard · Fundamentals · Monte Carlo · SMC · Fibonacci
</div>
""", unsafe_allow_html=True)