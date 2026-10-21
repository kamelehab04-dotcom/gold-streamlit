# ============================================================
# BLACK PYRAMID v2010.3 — MULTI-MODE FREQUENCY EDITION
# Institutional Analysis Terminal
# ============================================================

import os
import base64
import logging
import warnings
from pathlib import Path
from datetime import datetime, timedelta, timezone
import concurrent.futures
import time
import math

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import (train_test_split, GridSearchCV,
                                          RandomizedSearchCV, StratifiedKFold)
    from sklearn.metrics import (accuracy_score, roc_auc_score, confusion_matrix,
                                  log_loss, f1_score, precision_score, recall_score)
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

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

APP_VERSION = "v2010.3"

MODE = "balanced"

_GATE_PRESETS = {
    "strict":   {"gate": 80.0, "a_plus": 85.0, "a": 80.0, "b": 72.0,
                 "c": 65.0, "gap": 15, "cs_a_plus": 80, "cs_a": 80,
                 "cs_b": 65, "cs_c": 55},
    "balanced": {"gate": 75.0, "a_plus": 82.0, "a": 75.0, "b": 68.0,
                 "c": 60.0, "gap": 12, "cs_a_plus": 78, "cs_a": 75,
                 "cs_b": 62, "cs_c": 52},
    "relaxed":  {"gate": 72.0, "a_plus": 80.0, "a": 72.0, "b": 65.0,
                 "c": 55.0, "gap": 10, "cs_a_plus": 75, "cs_a": 72,
                 "cs_b": 60, "cs_c": 48},
}
_p = _GATE_PRESETS.get(MODE, _GATE_PRESETS["balanced"])

A_PLUS_MIN          = _p["a_plus"]
A_MIN               = _p["a"]
B_MIN               = _p["b"]
C_MIN               = _p["c"]
MIN_SIGNAL_GAP      = _p["gap"]
MIN_EMIT_CONFIDENCE = _p["gate"]

PENALTY_MTF_AGAINST    = 8.0
PENALTY_RANGE_REGIME   = 6.0
PENALTY_WEAK_CANDLE    = 5.0
PENALTY_WEEKLY_AGAINST = 4.0
MAX_SOFT_PENALTY       = 8.0
SOFT_PENALTY_TOP_N     = 3

MIN_RR_TP1 = 0.80
MIN_RR_TP2 = 1.30
MIN_RR_TP3 = 1.90

CORRELATION_WINDOW_DAYS = 30
CORRELATION_THRESHOLD = 0.70

SENTIMENT_EXTREME_LONG = 75
SENTIMENT_EXTREME_SHORT = 25

ML_MIN_TRADES = 30
ML_TEST_SIZE = 0.25
ML_FEATURE_SELECTION_THRESHOLD = 0.02
ML_CV_FOLDS = 5

TUNING_MODE = "randomized"
TUNING_N_ITER = 20
TUNING_CV_FOLDS = 5
TUNING_SCORING = "roc_auc"
TUNING_N_JOBS = -1

SL_MIN_DIST_ATR = 0.25
SL_MAX_DIST_ATR = 1.50
SL_BUFFER_ATR = 0.20

ML_FEATURE_NAMES = [
    "structure", "trend", "momentum", "volume", "context",
    "mtf_conf", "confirmation", "raw_conf", "regime_enc", "session_enc",
    "mtf_match", "weekly_match", "htf_match", "session_match",
    "fund_buy", "fund_sell", "ccy_diff", "rate_diff",
    "ema200_dist", "atr_ratio", "bb_position", "vwap_dist",
    "rsi_val", "macd_hist_norm", "body_ratio", "wick_ratio",
    "consec_bars", "candles_since_bos", "divergence_flag", "vol_ratio",
]

PARAM_GRIDS = {
    "LogisticRegression": {"C": [0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
                           "solver": ["lbfgs", "liblinear"],
                           "class_weight": [None, "balanced"]},
    "GradientBoosting": {"n_estimators": [80, 150, 250], "max_depth": [3, 4, 5, 6],
                          "learning_rate": [0.03, 0.05, 0.08, 0.10],
                          "subsample": [0.8, 0.9, 1.0], "min_samples_leaf": [1, 3, 5]},
    "RandomForest": {"n_estimators": [100, 200, 300], "max_depth": [4, 6, 8, None],
                      "min_samples_split": [2, 5, 10], "class_weight": [None, "balanced"]},
    "XGBoost": {"n_estimators": [100, 200, 300], "max_depth": [3, 4, 5, 6],
                 "learning_rate": [0.03, 0.05, 0.08, 0.10],
                 "subsample": [0.8, 0.9, 1.0], "colsample_bytree": [0.8, 0.9, 1.0]},
}

LOGO_CANDIDATES = ["file_000000005cb4824697f509df31f2168a.png",
                    "logo.png", "assets/logo.png", "static/logo.png"]

ASSET_PROFILES = {
    "forex": {"atr_period": 14, "rsi_period": 14, "rsi_ob": 70, "rsi_os": 30,
              "bb_period": 20, "bb_std": 2.0, "atr_sl": 1.50, "atr_trail": 1.10,
              "swing_order": 3, "structure_lookback": 120,
              "confidence_threshold": 72, "confirmation_threshold": 65},
    "gold":  {"atr_period": 14, "rsi_period": 14, "rsi_ob": 80, "rsi_os": 20,
              "bb_period": 20, "bb_std": 2.2, "atr_sl": 1.80, "atr_trail": 1.30,
              "swing_order": 3, "structure_lookback": 175,
              "confidence_threshold": 74, "confirmation_threshold": 67},
    "crypto": {"atr_period": 14, "rsi_period": 14, "rsi_ob": 80, "rsi_os": 20,
               "bb_period": 50, "bb_std": 2.3, "atr_sl": 2.00, "atr_trail": 1.50,
               "swing_order": 4, "structure_lookback": 250,
               "confidence_threshold": 76, "confirmation_threshold": 70}}

PAIRS = {
    "XAU/USD (Gold)": "GC=F", "XAG/USD (Silver)": "SI=F",
    "DXY (Dollar Index)": "DX-Y.NYB", "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X", "USD/JPY": "USDJPY=X", "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X", "NZD/USD": "NZDUSD=X", "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X", "EUR/CHF": "EURCHF=X",
    "EUR/AUD": "EURAUD=X", "EUR/NZD": "EURNZD=X", "EUR/CAD": "EURCAD=X",
    "GBP/JPY": "GBPJPY=X", "GBP/CHF": "GBPCHF=X", "GBP/AUD": "GBPAUD=X",
    "GBP/NZD": "GBPNZD=X", "GBP/CAD": "GBPCAD=X", "AUD/JPY": "AUDJPY=X",
    "AUD/CHF": "AUDCHF=X", "AUD/NZD": "AUDNZD=X", "AUD/CAD": "AUDCAD=X",
    "NZD/JPY": "NZDJPY=X", "NZD/CHF": "NZDCHF=X", "NZD/CAD": "NZDCAD=X",
    "CAD/JPY": "CADJPY=X", "CAD/CHF": "CADCHF=X",
    "BTC/USD (Bitcoin)": "BTC-USD", "ETH/USD (Ethereum)": "ETH-USD"}

YF_SYMBOL_ALTERNATIVES = {
    "GC=F": ["GC=F", "XAUUSD=X", "GLD"], "SI=F": ["SI=F", "XAGUSD=X", "SLV"],
    "DX-Y.NYB": ["DX=F", "DX-Y.NYB", "UUP"],
    "BTC-USD": ["BTC-USD", "BTC=F"], "ETH-USD": ["ETH-USD", "ETH=F"],
    "EURUSD=X": ["EURUSD=X", "EUR=F"], "GBPUSD=X": ["GBPUSD=X", "GBP=F"],
    "USDJPY=X": ["USDJPY=X", "JPY=F"], "AUDUSD=X": ["AUDUSD=X", "AUD=F"],
    "USDCAD=X": ["USDCAD=X", "CAD=F"], "USDCHF=X": ["USDCHF=X", "CHF=F"],
    "NZDUSD=X": ["NZDUSD=X", "NZD=F"], "^VIX": ["^VIX", "VIXY", "VXX"]}

KILL_ZONES = {"London Open": (7, 10), "NY Open": (12, 15), "London Close": (15, 17)}

CENTRAL_BANK_RATES = {"USD": 5.25, "EUR": 4.00, "GBP": 5.25, "JPY": 0.10,
                       "CHF": 1.75, "AUD": 4.35, "NZD": 5.50, "CAD": 4.75}

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
            ("AUDCAD=X", -1), ("NZDCAD=X", -1), ("CADJPY=X", 1), ("CADCHF=X", 1)]}

RISK_OFF_CURRENCIES = {"USD", "JPY", "CHF"}
RISK_ON_CURRENCIES = {"AUD", "NZD", "CAD"}


def get_secret(name, default=""):
    """
    Reads API key from session_state first (runtime override),
    then st.secrets, then env vars.
    Empty string in session_state means user explicitly disabled it.
    """
    try:
        if name in st.session_state:
            v = st.session_state[name]
            if v is not None:
                return str(v)
    except Exception: pass
    try:
        v = st.secrets.get(name, None)
        if v is not None: return str(v)
    except Exception: pass
    return os.getenv(name, default)


def init_state():
    defaults = {
        "selected_pair": "XAU/USD (Gold)", "all_signals": None,
        "economic_events": None, "analyzing_all": False, "analysis_time": None,
        "backtest_results": None, "strict_filters": False,
        "show_calendar_today": False, "show_session_info": False,
        "show_market_status": False, "trade_journal": [],
        "ml_model": None, "_ccy_strength_cache": {},
        "show_details": False,
        "strong_trade_result": None}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()


def safe_float(v, default=np.nan):
    try:
        x = float(v)
        return x if np.isfinite(x) else default
    except Exception: return default

def clamp(v, lo, hi): return max(lo, min(hi, v))

def safe_bool(v):
    try: return bool(v) and not pd.isna(v)
    except Exception: return False

def asset_type_from_name(name):
    n = str(name).lower()
    if any(x in n for x in ["gold", "silver", "xau", "xag"]): return "gold"
    if any(x in n for x in ["bitcoin", "ethereum", "btc", "eth"]): return "crypto"
    return "forex"

def profile_for(name): return ASSET_PROFILES[asset_type_from_name(name)]

def get_asset_profile(pair_name):
    name = str(pair_name).upper()
    if "XAU" in name or "GOLD" in name or "SILVER" in name or "XAG" in name: return "gold"
    if any(x in name for x in ("BTC","ETH","XRP","SOL","ADA")): return "crypto"
    return "forex"

def fmt_price(v, pair_name):
    if v is None or not np.isfinite(safe_float(v)): return "N/A"
    if asset_type_from_name(pair_name) in ("gold","crypto"):
        return f"${float(v):,.2f}"
    return f"{float(v):.5f}"

def trend_icon(state):
    if state in ("BULLISH","TREND_BULLISH"): return "🟢"
    if state in ("BEARISH","TREND_BEARISH"): return "🔴"
    if state in ("NEUTRAL","RANGE"): return "🟡"
    if state == "COMPRESSION": return "🔵"
    return "⚪"

def img_to_base64(path):
    try:
        with open(path,"rb") as f: return base64.b64encode(f.read()).decode()
    except Exception: return None

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


def log_trade_result(result, outcome):
    st.session_state.trade_journal.append({
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "pair": st.session_state.get("selected_pair", "?"),
        "direction": result.get("signal", "?"),
        "grade": result.get("trade_grade", "?"),
        "confidence": round(result.get("confidence", 0), 1),
        "outcome": outcome})


def is_market_open(pair_name):
    now = datetime.now(timezone.utc)
    if asset_type_from_name(pair_name) == "crypto": return True, "Crypto 24/7"
    wd = now.weekday(); h = now.hour
    if wd == 4 and h >= 21: return False, "🚫 السوق مغلق (الجمعة مساءً)"
    if wd == 5: return False, "🚫 السوق مغلق (السبت)"
    if wd == 6 and h < 22: return False, "🚫 السوق لم يفتح بعد (الأحد)"
    return True, "✅ السوق مفتوح"

def get_current_session_info():
    now = datetime.now(timezone.utc); h = now.hour; m = now.minute
    sessions = {"Asian": (0,7,"🌏","طوكيو/سيدني"), "London": (7,12,"🇬🇧","لندن"),
                "Overlap": (12,16,"🔥","London/NY Overlap"), "NY": (16,21,"🇺🇸","نيويورك"),
                "After-Hours": (21,24,"🌙","بعد الإغلاق")}
    cur = "After-Hours"; ic = "🌙"; dsc = "بعد الإغلاق"
    for name, (s,e,i,d) in sessions.items():
        if s <= h < e: cur = name; ic = i; dsc = d; break
    kz = "خارج Kill Zones"
    for n, (s,e) in KILL_ZONES.items():
        if s <= h < e: kz = f"داخل {n} ✅"; break
    return {"session": cur, "icon": ic, "desc": dsc,
            "time_utc": f"{h:02d}:{m:02d} UTC", "kill_zone": kz, "hour": h}

def get_market_status_info(symbol, pair_name):
    try:
        df = get_historical_data(symbol, "3mo", "4h")
        if df is None or len(df) < 60: return None
        x = build_features(df, profile_for(pair_name))
        last = x.iloc[-1]
        regime, _ = detect_regime(x)
        _, vol_msg, vol_label = volatility_regime_filter(x)
        atr_s = x["atr"].dropna()
        atr_now = safe_float(atr_s.iloc[-1], 0)
        atr_mean = safe_float(atr_s.rolling(100).mean().iloc[-1], 0)
        atr_ratio = atr_now / atr_mean if atr_mean > 0 else 1.0
        struct_state = structure_state(x)["state"]
        e20 = safe_float(last.get("ema20")); e50 = safe_float(last.get("ema50"))
        e200 = safe_float(last.get("ema200"))
        if e20 > e50 > e200: ta = "متراصف صاعد"; ti = "🟢"
        elif e20 < e50 < e200: ta = "متراصف هابط"; ti = "🔴"
        elif e20 > e50: ta = "صاعد قصير المدى"; ti = "🟡"
        else: ta = "هابط قصير المدى"; ti = "🟡"
        if atr_ratio > 1.5: vs = "مرتفع"; vi = "🔥"
        elif atr_ratio < 0.7: vs = "منخفض"; vi = "😴"
        else: vs = "طبيعي"; vi = "🌊"
        if regime in ("TREND_BULLISH","TREND_BEARISH") and vol_label in ("NORMAL","HIGH"):
            ov = "مواتٍ ✅"; oi = "✅"
        elif regime == "RANGE": ov = "تذبذب ⚠️"; oi = "⚠️"
        elif regime == "COMPRESSION": ov = "انضغاط 🔵"; oi = "🔵"
        elif vol_label == "CHAOS": ov = "تقلب مفرط 🛑"; oi = "🛑"
        else: ov = "غير واضح ⚪"; oi = "⚪"
        return {"regime": regime, "vol_state": vs, "vol_icon": vi,
                "atr_ratio": atr_ratio, "structure": struct_state,
                "trend_align": ta, "trend_icon": ti, "overall": ov, "overall_icon": oi}
    except Exception: return None

def get_todays_events(events, pair_name):
    if not events: return []
    now = datetime.now(timezone.utc); today = now.strftime("%Y-%m-%d")
    base, quote = parse_pair_currencies(pair_name)
    curs = {base, quote} if base and quote else {"USD"}
    cmap = {"US":"USD","EU":"EUR","GB":"GBP","JP":"JPY","CH":"CHF",
            "AU":"AUD","NZ":"NZD","CA":"CAD"}
    out = []
    for e in events:
        try:
            if not str(e.get("date","")).startswith(today): continue
            c = str(e.get("country","")).strip().upper()
            if cmap.get(c, c) not in curs: continue
            out.append({"time": str(e.get("time","")), "country": c,
                        "event": str(e.get("event","")),
                        "impact": str(e.get("impact","")).strip().lower()})
        except Exception: continue
    out.sort(key=lambda x: x.get("time",""))
    return out


def sanitize_yf_symbol(sym):
    s = str(sym).strip().replace("(","").replace(")","")
    if "/" in s and s.count("/") == 1:
        a, b = s.split("/")
        a, b = a.strip(), b.strip()
        if a.upper() in ("BTC","ETH","SOL","XRP","ADA"): return f"{a.upper()}-{b.upper()}"
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
        elif lc in ("volume","vol"): rename[c] = "volume"
    df = df.rename(columns=rename)
    req = ["open","high","low","close"]
    if any(c not in df.columns for c in req): return None
    if "volume" not in df.columns: df["volume"] = 0.0
    for c in req + ["volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[req + ["volume"]].dropna(subset=req)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df if len(df) >= min_rows else None

@st.cache_data(ttl=60, show_spinner=False)
def get_yfinance(symbol, period="3mo", interval="4h"):
    try:
        return normalize_ohlcv(yf.download(sanitize_yf_symbol(symbol),
            period=period, interval=interval, auto_adjust=False,
            progress=False, threads=False))
    except Exception: return None

@st.cache_data(ttl=120, show_spinner=False)
def get_twelve_data(symbol, interval="4h", outputsize=500):
    api_key = get_secret("TWELVE_API_KEY")
    if not api_key: return None
    mp = {"GC=F":"XAU/USD","SI=F":"XAG/USD","DX-Y.NYB":"DXY","EURUSD=X":"EUR/USD",
          "GBPUSD=X":"GBP/USD","USDJPY=X":"USD/JPY","USDCHF=X":"USD/CHF",
          "AUDUSD=X":"AUD/USD","NZDUSD=X":"NZD/USD","USDCAD=X":"USD/CAD",
          "BTC-USD":"BTC/USD","ETH-USD":"ETH/USD"}
    td = mp.get(symbol, sanitize_yf_symbol(symbol))
    im = {"15m":"15min","1h":"1h","4h":"4h","1d":"1day"}
    try:
        r = requests.get("https://api.twelvedata.com/time_series",
            params={"symbol": td, "interval": im.get(interval, interval),
                    "outputsize": outputsize, "apikey": api_key,
                    "format":"JSON"}, timeout=10)
        data = r.json()
        if "values" not in data: return None
        df = pd.DataFrame(data["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()
        return normalize_ohlcv(df)
    except Exception: return None

@st.cache_data(ttl=90, show_spinner=False)
def get_historical_data(symbol, period="3mo", interval="4h"):
    for s in YF_SYMBOL_ALTERNATIVES.get(symbol, [symbol]):
        df = get_yfinance(s, period, interval)
        if df is not None and len(df) >= 50: return df
    df = get_yfinance(sanitize_yf_symbol(symbol), period, interval)
    if df is not None and len(df) >= 50: return df
    df = get_twelve_data(symbol, interval, 500)
    if df is not None and len(df) >= 50: return df
    for s in YF_SYMBOL_ALTERNATIVES.get(symbol, [symbol]):
        df = get_yfinance(s, "1mo", interval)
        if df is not None and len(df) >= 30: return df
    return None

@st.cache_data(ttl=30, show_spinner=False)
def get_spot_price(symbol):
    for s in YF_SYMBOL_ALTERNATIVES.get(symbol, [symbol]):
        for p, i in [("5d","1h"),("1mo","1d")]:
            try:
                df = normalize_ohlcv(yf.download(sanitize_yf_symbol(s), period=p,
                    interval=i, auto_adjust=False, progress=False, threads=False),
                    min_rows=2)
                if df is not None and len(df) >= 2:
                    pc = float(df["close"].iloc[-2]); lt = float(df["close"].iloc[-1])
                    return lt, ((lt - pc) / pc * 100) if pc else 0.0
            except Exception: continue
    try:
        df = get_twelve_data(symbol, "1h", 5)
        if df is not None and len(df) >= 2:
            pc = float(df["close"].iloc[-2]); lt = float(df["close"].iloc[-1])
            return lt, ((lt - pc) / pc * 100) if pc else 0.0
    except Exception: pass
    try:
        df = get_historical_data(symbol, "3mo", "4h")
        if df is not None and not df.empty: return float(df["close"].iloc[-1]), 0.0
    except Exception: pass
    return None, None


@st.cache_data(ttl=600, show_spinner=False)
def get_currency_strength_matrix():
    strength = {}
    for ccy, pairs in CURRENCY_PAIRS_MAP.items():
        ch = []
        for sym, sign in pairs:
            try:
                df = get_historical_data(sym, "1mo", "1d")
                if df is None or len(df) < 21: continue
                pct = (df["close"].iloc[-1] - df["close"].iloc[-21]) / df["close"].iloc[-21] * 100
                if np.isfinite(pct): ch.append(sign * pct)
            except Exception: continue
        strength[ccy] = float(np.mean(ch)) if ch else 0.0
    if not strength: return {}
    ma = max(abs(v) for v in strength.values()) or 1.0
    return {k: (v / ma) * 100 for k, v in strength.items()}

def get_interest_rate_differential(pair_name):
    b, q = parse_pair_currencies(pair_name)
    if not b or not q: return 0.0, "لا يوجد زوج صالح"
    if b not in CENTRAL_BANK_RATES or q not in CENTRAL_BANK_RATES:
        return 0.0, f"معدلات غير متاحة ({b}/{q})"
    d = CENTRAL_BANK_RATES[b] - CENTRAL_BANK_RATES[q]
    return d, f"{b}: {CENTRAL_BANK_RATES[b]}% | {q}: {CENTRAL_BANK_RATES[q]}% | Diff: {d:+.2f}%"

@st.cache_data(ttl=300, show_spinner=False)
def get_risk_sentiment():
    vd = get_historical_data("^VIX", "3mo", "1d")
    if vd is None or len(vd) < 5:
        return {"vix": None, "vix_state": "UNKNOWN", "risk_mode": "NEUTRAL",
                "bias_impact": 0.0, "msg": "VIX غير متاح"}
    vn = float(vd["close"].iloc[-1])
    va = float(vd["close"].rolling(20).mean().iloc[-1]) if len(vd) >= 20 else vn
    vc = (vn - va) / va * 100 if va > 0 else 0
    if vn > 25: vs = "HIGH FEAR"
    elif vn > 20: vs = "ELEVATED"
    elif vn < 14: vs = "COMPLACENT"
    else: vs = "NORMAL"
    if vn > 25 or vc > 15: rm = "RISK-OFF"; bi = -1.0
    elif vn < 15 and vc < -5: rm = "RISK-ON"; bi = 1.0
    else: rm = "NEUTRAL"; bi = 0.0
    return {"vix": vn, "vix_avg": va, "vix_change": vc, "vix_state": vs,
            "risk_mode": rm, "bias_impact": bi,
            "msg": f"VIX {vn:.2f} ({vs}) · {rm}"}

@st.cache_data(ttl=600, show_spinner=False)
def get_bond_yields():
    r = {"us10y": None, "us5y": None, "us30y": None, "us10y_change": 0.0,
         "us10y_trend": "NEUTRAL", "curve_10y_5y": None, "curve_state": "UNKNOWN",
         "gold_yield_corr": None, "yield_vs_dollar": "NEUTRAL"}
    try:
        tnx = get_historical_data("^TNX", "3mo", "1d")
        if tnx is not None and len(tnx) >= 20:
            yn = float(tnx["close"].iloc[-1]); y5 = float(tnx["close"].iloc[-5])
            y20 = float(tnx["close"].iloc[-20])
            r["us10y"] = yn; r["us10y_change"] = yn - y5
            if yn > y20 + 0.15: r["us10y_trend"] = "RISING"
            elif yn < y20 - 0.15: r["us10y_trend"] = "FALLING"
            else: r["us10y_trend"] = "STABLE"
        fvx = get_historical_data("^FVX", "3mo", "1d")
        if fvx is not None and len(fvx) >= 5:
            r["us5y"] = float(fvx["close"].iloc[-1])
        tyx = get_historical_data("^TYX", "3mo", "1d")
        if tyx is not None and len(tyx) >= 5:
            r["us30y"] = float(tyx["close"].iloc[-1])
        if r["us10y"] and r["us5y"]:
            c = r["us10y"] - r["us5y"]; r["curve_10y_5y"] = c
            if c > 0.10: r["curve_state"] = "STEEP"
            elif c < -0.10: r["curve_state"] = "INVERTED"
            else: r["curve_state"] = "FLAT"
        gold = get_historical_data("GC=F", "3mo", "1d")
        if tnx is not None and gold is not None:
            al = pd.concat([tnx["close"].pct_change(), gold["close"].pct_change()],
                          axis=1, join="inner").dropna()
            if len(al) >= 30:
                c = float(al.iloc[-30:, 0].corr(al.iloc[-30:, 1]))
                if np.isfinite(c): r["gold_yield_corr"] = c
        if r["us10y_trend"] == "RISING": r["yield_vs_dollar"] = "BULLISH_USD"
        elif r["us10y_trend"] == "FALLING": r["yield_vs_dollar"] = "BEARISH_USD"
    except Exception: pass
    return r

def get_bond_bias_for_pair(pair_name, bonds=None):
    if bonds is None: bonds = get_bond_yields()
    b, q = parse_pair_currencies(pair_name)
    if not b or not q: return 0.0, 0.0, ""
    ub = 0.0; ube = 0.0; rr = []
    if bonds["us10y_trend"] == "RISING": ub += 20; rr.append("US10Y↑")
    elif bonds["us10y_trend"] == "FALLING": ube += 20; rr.append("US10Y↓")
    gyc = bonds.get("gold_yield_corr")
    if gyc is not None and ("GOLD" in pair_name.upper() or "XAU" in pair_name.upper()):
        if gyc < -0.30 and bonds["us10y_trend"] == "FALLING": ube += 15
        elif gyc < -0.30 and bonds["us10y_trend"] == "RISING": ub += 15
    if b == "USD": return ub, ube, " · ".join(rr)
    elif q == "USD": return ube, ub, " · ".join(rr)
    return 0.0, 0.0, " · ".join(rr)


def estimate_retail_sentiment(df, profile):
    if df is None or len(df) < 50:
        return {"long_pct": 50, "short_pct": 50, "bias": "NEUTRAL",
                "contrarian": "NEUTRAL", "strength": 0, "msg": "بيانات غير كافية"}
    last = df.iloc[-1]
    ls = 50.0
    rsi = safe_float(last.get("rsi"), 50)
    if rsi >= 70: ls += 20
    elif rsi >= 60: ls += 10
    elif rsi <= 30: ls -= 20
    elif rsi <= 40: ls -= 10
    e200 = safe_float(last.get("ema200"), 0)
    p = safe_float(last.get("close"), 0)
    atr = safe_float(last.get("atr"), 1)
    if e200 > 0 and atr > 0:
        d = (p - e200) / atr
        if d > 3: ls += 15
        elif d > 1.5: ls += 8
        elif d < -3: ls -= 15
        elif d < -1.5: ls -= 8
    if len(df) >= 5:
        up = (df["close"].iloc[-5:].diff() > 0).sum()
        ls += (up - 2.5) * 3
    st_obj = structure_state(df)
    if st_obj["bullish"]: ls += 8
    elif st_obj["bearish"]: ls -= 8
    ls = clamp(ls, 5, 95); ss = 100 - ls
    if ls >= SENTIMENT_EXTREME_LONG: bias = "EXTREME_LONG"; ct = "SELL"; stv = ls - SENTIMENT_EXTREME_LONG
    elif ls <= SENTIMENT_EXTREME_SHORT: bias = "EXTREME_SHORT"; ct = "BUY"; stv = SENTIMENT_EXTREME_SHORT - ls
    elif ls >= 60: bias = "CROWD_LONG"; ct = "SELL"; stv = ls - 60
    elif ls <= 40: bias = "CROWD_SHORT"; ct = "BUY"; stv = 40 - ls
    else: bias = "NEUTRAL"; ct = "NEUTRAL"; stv = 0
    return {"long_pct": ls, "short_pct": ss, "bias": bias,
            "contrarian": ct, "strength": stv,
            "msg": f"Retail: {ls:.0f}% Long · Contrarian → {ct}"}

def get_sentiment_bias_for_signal(sentiment, signal):
    if sentiment is None or signal not in ("BUY","SELL"): return 0.0, ""
    bias = sentiment.get("bias","NEUTRAL"); stv = sentiment.get("strength", 0)
    if bias in ("EXTREME_LONG","CROWD_LONG") and signal == "SELL":
        return min(stv * 0.5, 15), "✅ Sentiment يدعم SELL"
    elif bias in ("EXTREME_SHORT","CROWD_SHORT") and signal == "BUY":
        return min(stv * 0.5, 15), "✅ Sentiment يدعم BUY"
    elif bias in ("EXTREME_LONG","CROWD_LONG") and signal == "BUY":
        return -min(stv * 0.3, 10), "⚠️ Sentiment ضد BUY"
    elif bias in ("EXTREME_SHORT","CROWD_SHORT") and signal == "SELL":
        return -min(stv * 0.3, 10), "⚠️ Sentiment ضد SELL"
    return 0.0, ""


def monte_carlo_simulation(trades_r, n_sims=1000, n_trades=None):
    if not trades_r or len(trades_r) < 5: return None
    if n_trades is None: n_trades = len(trades_r)
    rng = np.random.default_rng(42)
    fe = np.zeros(n_sims); md = np.zeros(n_sims)
    for i in range(n_sims):
        s = rng.choice(trades_r, size=n_trades, replace=True)
        ec = np.cumsum(s); pk = np.maximum.accumulate(ec); dd = pk - ec
        fe[i] = ec[-1]; md[i] = dd.max() if len(dd) > 0 else 0
    return {"mean_final": float(np.mean(fe)), "median_final": float(np.median(fe)),
            "p5_final": float(np.percentile(fe, 5)), "p95_final": float(np.percentile(fe, 95)),
            "prob_profit": float((fe > 0).mean() * 100),
            "mean_dd": float(np.mean(md)), "p95_dd": float(np.percentile(md, 95)),
            "worst_dd": float(np.max(md)), "n_sims": n_sims, "n_trades": n_trades}


def extract_ml_features(result, direction):
    pillars = result.get("pillars", {}); dp = pillars.get(direction, {})
    df = result.get("df")
    rm = {"RANGE":0, "TREND_BULLISH":1, "TREND_BEARISH":2, "COMPRESSION":3, "UNKNOWN":0}
    regime = result.get("regime", "RANGE")
    try:
        si = get_current_session_info()
        sm = {"Asian":0, "London":1, "Overlap":2, "NY":3, "After-Hours":4}
        se = sm.get(si["session"], 0)
    except Exception: se = 0
    mtf = result.get("mtf_bias","NEUTRAL")
    m_match = 1 if ((direction == "BUY" and mtf == "BULLISH") or
                    (direction == "SELL" and mtf == "BEARISH")) else 0
    wk = result.get("weekly_bias","NEUTRAL")
    w_match = 1 if ((direction == "BUY" and wk == "BULLISH") or
                    (direction == "SELL" and wk == "BEARISH")) else 0
    htf_m = 0; sess_m = 0
    flt = result.get("filter_results", {})
    if "HTF Zone" in flt:
        z = flt["HTF Zone"].get("zone", "UNKNOWN")
        htf_m = 1 if z in ("DISCOUNT","PREMIUM","MID") else 0
    if "Session" in flt: sess_m = 1 if flt["Session"].get("pass", True) else 0
    ed=0.0; ar=1.0; bp=50.0; vd=0.0; rv=50.0; mh=0.0
    br=0.5; wr=1.0; cb=0; csb=50; vr=1.0
    if df is not None and len(df) >= 200:
        try:
            last = df.iloc[-1]; p = safe_float(last.get("close"),0)
            e200 = safe_float(last.get("ema200"),0); atr = safe_float(last.get("atr"),1)
            if e200 > 0 and atr > 0: ed = (p - e200) / atr
            a_s = df["atr"].dropna()
            if len(a_s) >= 100:
                am = a_s.rolling(100).mean().iloc[-1]
                if am > 0: ar = atr / am
            bu = safe_float(last.get("bb_upper"),0); bl = safe_float(last.get("bb_lower"),0)
            if bu > bl > 0: bp = (p - bl) / (bu - bl) * 100
            vw = safe_float(last.get("vwap"),0)
            if vw > 0: vd = (p - vw) / vw * 100
            rv = safe_float(last.get("rsi"),50)
            mh_v = safe_float(last.get("macd_histogram"),0)
            if atr > 0: mh = mh_v / atr
            body = abs(float(last["close"]) - float(last["open"]))
            rng = max(float(last["high"]) - float(last["low"]), 1e-9)
            br = body / rng
            uw = float(last["high"]) - max(float(last["close"]), float(last["open"]))
            lw = min(float(last["close"]), float(last["open"])) - float(last["low"])
            wr = (uw + 0.001) / (lw + 0.001)
            dsg = 1 if float(last["close"]) > float(last["open"]) else -1
            cb = 0
            for k in range(1, min(11, len(df))):
                c = float(df["close"].iloc[-k]); o = float(df["open"].iloc[-k])
                s = 1 if c > o else -1
                if s == dsg: cb += 1
                else: break
            if "bos_bullish" in df.columns and "bos_bearish" in df.columns:
                ba = (df["bos_bullish"] | df["bos_bearish"])
                bi = ba[ba].index
                if len(bi) > 0:
                    csb = len(df) - 1 - df.index.get_loc(bi[-1])
            va = df["volume"].rolling(20).mean().iloc[-1]
            if va > 0: vr = float(last["volume"]) / va
        except Exception: pass
    div = result.get("divergence"); dfg = 0
    if div == "BULLISH" and direction == "BUY": dfg = 1
    elif div == "BEARISH" and direction == "SELL": dfg = 1
    elif div in ("BULLISH","BEARISH"): dfg = -1
    bn, qn = parse_pair_currencies(result.get("pair_name",""))
    ccs = st.session_state.get("_ccy_strength_cache", {})
    bs = ccs.get(bn, 0) if isinstance(ccs, dict) else 0
    qs = ccs.get(qn, 0) if isinstance(ccs, dict) else 0
    cd = bs - qs; rd = result.get("rate_diff", 0.0)
    return [float(dp.get("structure",0)), float(dp.get("trend",0)),
            float(dp.get("momentum",0)), float(dp.get("volume",0)),
            float(dp.get("context",0)), float(result.get("mtf_conf",50)),
            float(result.get("confirmation_score",0)),
            float(result.get("raw_confidence",0)), float(rm.get(regime,0)),
            float(se), float(m_match), float(w_match), float(htf_m), float(sess_m),
            float(result.get("fund_buy",0)), float(result.get("fund_sell",0)),
            float(cd), float(rd), float(ed), float(ar), float(bp), float(vd),
            float(rv), float(mh), float(br), float(wr), float(cb),
            float(csb), float(dfg), float(vr)]

def tune_model(model_name, model, param_grid, X, y, mode="randomized",
               n_iter=20, cv_folds=5):
    try:
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    except Exception: cv = cv_folds
    try:
        if mode == "grid":
            tuner = GridSearchCV(estimator=model, param_grid=param_grid, cv=cv,
                scoring=TUNING_SCORING, n_jobs=TUNING_N_JOBS, verbose=0, refit=True)
        else:
            tuner = RandomizedSearchCV(estimator=model, param_distributions=param_grid,
                n_iter=n_iter, cv=cv, scoring=TUNING_SCORING,
                n_jobs=TUNING_N_JOBS, verbose=0, random_state=42, refit=True)
        tuner.fit(X, y)
        return tuner.best_estimator_, tuner.best_params_, float(tuner.best_score_)
    except Exception:
        return model, {}, 0.0

def train_ml_model(trades_data, use_tuning=False, tuning_mode="randomized",
                   tuning_n_iter=20):
    if not SKLEARN_AVAILABLE:
        return {"error": "sklearn غير مثبت"}
    if len(trades_data) < ML_MIN_TRADES:
        return {"error": f"بيانات غير كافية ({len(trades_data)}/{ML_MIN_TRADES})"}
    X = np.array([t["features"] for t in trades_data], dtype=float)
    y = np.array([t["label"] for t in trades_data], dtype=int)
    if len(np.unique(y)) < 2: return {"error": "كل الصفقات من نفس الفئة"}
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    scaler = StandardScaler(); X_scaled = scaler.fit_transform(X)
    try:
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y,
            test_size=ML_TEST_SIZE, random_state=42, stratify=y)
        X_train_raw, X_test_raw, _, _ = train_test_split(X, y,
            test_size=ML_TEST_SIZE, random_state=42, stratify=y)
    except Exception:
        X_train = X_test = X_scaled; X_train_raw = X_test_raw = X
        y_train = y_test = y
    res = {}; trep = {}

    try:
        lr = LogisticRegression(max_iter=1000, random_state=42)
        if use_tuning:
            lr, bp, bcv = tune_model("LogisticRegression", lr,
                PARAM_GRIDS["LogisticRegression"], X_train, y_train,
                mode=tuning_mode, n_iter=tuning_n_iter)
            trep["LogisticRegression"] = {"best_params": bp, "best_cv_score": bcv}
        lr.fit(X_train, y_train)
        yp = lr.predict(X_test); ypr = lr.predict_proba(X_test)[:,1]
        auc = float(roc_auc_score(y_test, ypr)) if len(np.unique(y_test)) > 1 else 0.5
        res["LogisticRegression"] = {"model": lr, "scaler": scaler, "auc": auc,
            "accuracy": float(accuracy_score(y_test, yp)),
            "f1": float(f1_score(y_test, yp, zero_division=0)),
            "precision": float(precision_score(y_test, yp, zero_division=0)),
            "recall": float(recall_score(y_test, yp, zero_division=0)),
            "logloss": float(log_loss(y_test, ypr)),
            "confusion": confusion_matrix(y_test, yp).tolist(),
            "coefficients": dict(zip(ML_FEATURE_NAMES, lr.coef_[0].tolist())),
            "needs_scaling": True}
    except Exception as e: res["LogisticRegression"] = {"error": str(e)}

    try:
        gb = GradientBoostingClassifier(random_state=42)
        if use_tuning:
            gb, bp, bcv = tune_model("GradientBoosting", gb,
                PARAM_GRIDS["GradientBoosting"], X_train_raw, y_train,
                mode=tuning_mode, n_iter=tuning_n_iter)
            trep["GradientBoosting"] = {"best_params": bp, "best_cv_score": bcv}
        else:
            gb = GradientBoostingClassifier(n_estimators=150, max_depth=4,
                                            learning_rate=0.05, random_state=42)
        gb.fit(X_train_raw, y_train)
        yp = gb.predict(X_test_raw); ypr = gb.predict_proba(X_test_raw)[:,1]
        auc = float(roc_auc_score(y_test, ypr)) if len(np.unique(y_test)) > 1 else 0.5
        res["GradientBoosting"] = {"model": gb, "scaler": None, "auc": auc,
            "accuracy": float(accuracy_score(y_test, yp)),
            "f1": float(f1_score(y_test, yp, zero_division=0)),
            "precision": float(precision_score(y_test, yp, zero_division=0)),
            "recall": float(recall_score(y_test, yp, zero_division=0)),
            "logloss": float(log_loss(y_test, ypr)),
            "confusion": confusion_matrix(y_test, yp).tolist(),
            "importance": dict(zip(ML_FEATURE_NAMES, gb.feature_importances_.tolist())),
            "needs_scaling": False}
    except Exception as e: res["GradientBoosting"] = {"error": str(e)}

    try:
        rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        if use_tuning:
            rf, bp, bcv = tune_model("RandomForest", rf,
                PARAM_GRIDS["RandomForest"], X_train_raw, y_train,
                mode=tuning_mode, n_iter=tuning_n_iter)
            trep["RandomForest"] = {"best_params": bp, "best_cv_score": bcv}
        else:
            rf = RandomForestClassifier(n_estimators=200, max_depth=6,
                                        random_state=42, n_jobs=-1)
        rf.fit(X_train_raw, y_train)
        yp = rf.predict(X_test_raw); ypr = rf.predict_proba(X_test_raw)[:,1]
        auc = float(roc_auc_score(y_test, ypr)) if len(np.unique(y_test)) > 1 else 0.5
        res["RandomForest"] = {"model": rf, "scaler": None, "auc": auc,
            "accuracy": float(accuracy_score(y_test, yp)),
            "f1": float(f1_score(y_test, yp, zero_division=0)),
            "precision": float(precision_score(y_test, yp, zero_division=0)),
            "recall": float(recall_score(y_test, yp, zero_division=0)),
            "logloss": float(log_loss(y_test, ypr)),
            "confusion": confusion_matrix(y_test, yp).tolist(),
            "importance": dict(zip(ML_FEATURE_NAMES, rf.feature_importances_.tolist())),
            "needs_scaling": False}
    except Exception as e: res["RandomForest"] = {"error": str(e)}

    if XGBOOST_AVAILABLE:
        try:
            xm = xgb.XGBClassifier(random_state=42, use_label_encoder=False,
                                    eval_metric="logloss", verbosity=0)
            if use_tuning:
                xm, bp, bcv = tune_model("XGBoost", xm, PARAM_GRIDS["XGBoost"],
                    X_train_raw, y_train, mode=tuning_mode, n_iter=tuning_n_iter)
                trep["XGBoost"] = {"best_params": bp, "best_cv_score": bcv}
            else:
                xm = xgb.XGBClassifier(n_estimators=200, max_depth=4,
                    learning_rate=0.05, random_state=42,
                    use_label_encoder=False, eval_metric="logloss", verbosity=0)
            xm.fit(X_train_raw, y_train)
            yp = xm.predict(X_test_raw); ypr = xm.predict_proba(X_test_raw)[:,1]
            auc = float(roc_auc_score(y_test, ypr)) if len(np.unique(y_test)) > 1 else 0.5
            res["XGBoost"] = {"model": xm, "scaler": None, "auc": auc,
                "accuracy": float(accuracy_score(y_test, yp)),
                "f1": float(f1_score(y_test, yp, zero_division=0)),
                "precision": float(precision_score(y_test, yp, zero_division=0)),
                "recall": float(recall_score(y_test, yp, zero_division=0)),
                "logloss": float(log_loss(y_test, ypr)),
                "confusion": confusion_matrix(y_test, yp).tolist(),
                "importance": dict(zip(ML_FEATURE_NAMES, xm.feature_importances_.tolist())),
                "needs_scaling": False}
        except Exception as e: res["XGBoost"] = {"error": str(e)}

    valid = {k: v for k, v in res.items() if "auc" in v}
    if not valid: return {"error": "كل النماذج فشلت"}
    best_name = max(valid.keys(), key=lambda k: valid[k]["auc"])
    best = valid[best_name]
    fs = None
    if "importance" in best:
        imp = best["importance"]; ti = sum(imp.values()) or 1.0
        kept = [n for n, i in imp.items() if i/ti >= ML_FEATURE_SELECTION_THRESHOLD]
        dropped = [n for n in imp.keys() if n not in kept]
        fs = {"kept": kept, "dropped": dropped, "kept_count": len(kept),
              "dropped_count": len(dropped)}
    if "coefficients" in best:
        cd = best["coefficients"]; id_ = {k: abs(v) for k, v in cd.items()}
    elif "importance" in best:
        cd = best["importance"]; id_ = best["importance"]
    else: cd = {}; id_ = {}
    iss = dict(sorted(id_.items(), key=lambda x: x[1], reverse=True))
    ta = sum(iss.values()) or 1.0
    cw = {k: round(v/ta*100, 2) for k, v in iss.items()}
    return {"model": best["model"], "scaler": best.get("scaler"),
            "needs_scaling": best.get("needs_scaling", False),
            "model_name": best_name, "auc": best["auc"],
            "accuracy": best["accuracy"], "f1": best["f1"],
            "precision": best["precision"], "recall": best["recall"],
            "logloss": best["logloss"], "confusion_matrix": best["confusion"],
            "coefficients": cd, "importance": iss, "calibrated_weights": cw,
            "all_models": {k: {"auc": v.get("auc",0),
                               "accuracy": v.get("accuracy",0),
                               "f1": v.get("f1",0),
                               "error": v.get("error")} for k, v in res.items()},
            "feature_selection": fs, "tuning_report": trep, "tuned": use_tuning,
            "n_train": len(X_train), "n_test": len(X_test),
            "n_total": len(trades_data), "n_features": len(ML_FEATURE_NAMES),
            "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

def predict_win_probability(ml_pack, result, direction):
    if not ml_pack or "model" not in ml_pack: return None
    try:
        feats = extract_ml_features(result, direction)
        X = np.array([feats], dtype=float)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        if ml_pack.get("needs_scaling") and ml_pack.get("scaler") is not None:
            X = ml_pack["scaler"].transform(X)
        return float(ml_pack["model"].predict_proba(X)[0, 1])
    except Exception: return None

def ml_adjusted_confidence(result, direction, ml_pack):
    if ml_pack is None or "model" not in ml_pack:
        return result.get("confidence", 0), None, "no_model"
    prob = predict_win_probability(ml_pack, result, direction)
    if prob is None: return result.get("confidence", 0), None, "predict_failed"
    fc = result.get("confidence", 50); auc = ml_pack.get("auc", 0.5)
    if auc >= 0.75: mw = 0.75
    elif auc >= 0.70: mw = 0.65
    elif auc >= 0.65: mw = 0.55
    elif auc >= 0.60: mw = 0.45
    elif auc >= 0.55: mw = 0.30
    else: mw = 0.15
    return clamp(mw * (prob * 100) + (1 - mw) * fc, 0, 99), prob, "applied"


def calc_rsi(series, period=14):
    d = series.diff(); g = d.clip(lower=0); l = -d.clip(upper=0)
    ag = g.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    al = l.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = ag / al.replace(0, np.nan)
    r = 100 - (100/(1+rs))
    r = r.where(al > 0, 100.0); r = r.where(ag > 0, 0.0)
    return r.fillna(50).clip(0, 100)

def calc_atr(df, period=14):
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"]-df["low"], (df["high"]-pc).abs(),
                    (df["low"]-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

def calc_macd(s, f=12, sl=26, sig=9):
    ef = s.ewm(span=f, adjust=False).mean(); es = s.ewm(span=sl, adjust=False).mean()
    m = ef - es; sg = m.ewm(span=sig, adjust=False).mean()
    return m, sg, m - sg

def calc_bollinger(s, p=20, std=2.0):
    m = s.rolling(p).mean(); d = s.rolling(p).std()
    return m + std*d, m, m - std*d

def calc_chaikin(df, period=21):
    hl = (df["high"]-df["low"]).replace(0, np.nan)
    mult = ((df["close"]-df["low"]) - (df["high"]-df["close"])) / hl
    mv = mult.fillna(0) * df["volume"]
    return (mv.rolling(period).sum() /
            df["volume"].rolling(period).sum().replace(0, np.nan)).fillna(0)

def calc_rolling_vwap(df, period=20):
    tp = (df["high"]+df["low"]+df["close"])/3
    v = df["volume"].clip(lower=0); pv = tp*v
    cpv = pv.rolling(period, min_periods=period).sum()
    cv = v.rolling(period, min_periods=period).sum()
    vw = cpv / cv.replace(0, np.nan)
    fb = tp.rolling(period, min_periods=period).mean()
    return vw.fillna(fb)

def calc_session_vwap(df):
    w = df.copy()
    if w.index.tz is None: dt = w.index.normalize()
    else: dt = w.index.tz_convert("UTC").normalize()
    tp = (w["high"]+w["low"]+w["close"])/3
    pv = tp * w["volume"].clip(lower=0)
    cpv = pv.groupby(dt).cumsum(); cv = w["volume"].clip(lower=0).groupby(dt).cumsum()
    vw = cpv / cv.replace(0, np.nan)
    fb = tp.groupby(dt).expanding().mean().reset_index(level=0, drop=True)
    return vw.fillna(fb)


def find_confirmed_swings(df, order=3):
    out = df.copy(); w = 2*order+1
    if len(out) < w:
        out["swing_high"] = False; out["swing_low"] = False; return out
    rm = out["high"].rolling(w, min_periods=w).max()
    rn = out["low"].rolling(w, min_periods=w).min()
    im = (out["high"] >= rm - 1e-12) & rm.notna()
    inn = (out["low"] <= rn + 1e-12) & rn.notna()
    out["swing_high"] = im.shift(order).fillna(False).astype(bool)
    out["swing_low"] = inn.shift(order).fillna(False).astype(bool)
    return out

def get_last_two_swings(df, kind="high"):
    c = "swing_high" if kind == "high" else "swing_low"
    if c not in df.columns: return None
    p = df.index[df[c]].tolist()
    v = df.loc[p, "high" if kind == "high" else "low"].tolist()
    if len(p) < 2: return None
    return [(p[-2], float(v[-2])), (p[-1], float(v[-1]))]

def structure_state(df):
    h = get_last_two_swings(df, "high"); l = get_last_two_swings(df, "low")
    bu = False; be = False; s = "RANGE"
    if h and l:
        hh = h[-1][1] > h[-2][1]; hl = l[-1][1] > l[-2][1]
        lh = h[-1][1] < h[-2][1]; ll = l[-1][1] < l[-2][1]
        if hh and hl: bu = True; s = "BULLISH"
        elif lh and ll: be = True; s = "BEARISH"
    return {"state": s, "bullish": bu, "bearish": be, "highs": h, "lows": l}

def detect_bos_mss(df):
    out = df.copy(); n = len(out)
    bbu = np.zeros(n, dtype=bool); bbe = np.zeros(n, dtype=bool)
    mbu = np.zeros(n, dtype=bool); mbe = np.zeros(n, dtype=bool)
    if n == 0:
        out["bos_bullish"] = bbu; out["bos_bearish"] = bbe
        out["mss_bullish"] = mbu; out["mss_bearish"] = mbe; return out
    sh = out["swing_high"].values; sl = out["swing_low"].values
    ha = out["high"].values; la = out["low"].values; ca = out["close"].values
    st = "RANGE"; lh = np.nan; ll = np.nan
    for i in range(n):
        if i > 0:
            if sh[i-1]: lh = ha[i-1]
            if sl[i-1]: ll = la[i-1]
        if i < 10: continue
        c = ca[i]
        if np.isfinite(lh) and c > lh:
            bbu[i] = True
            if st == "BEARISH": mbu[i] = True
            st = "BULLISH"; lh = np.nan
        elif np.isfinite(ll) and c < ll:
            bbe[i] = True
            if st == "BULLISH": mbe[i] = True
            st = "BEARISH"; ll = np.nan
    out["bos_bullish"] = bbu; out["bos_bearish"] = bbe
    out["mss_bullish"] = mbu; out["mss_bearish"] = mbe
    return out

def detect_liquidity_sweeps(df, tol_atr=0.10):
    out = df.copy(); t = out["atr"] * tol_atr
    ph = out["high"].rolling(3).max().shift(1)
    pl = out["low"].rolling(3).min().shift(1)
    out["liquidity_sweep_bearish"] = ((out["high"] > ph + t) & (out["close"] < ph)).fillna(False)
    out["liquidity_sweep_bullish"] = ((out["low"] < pl - t) & (out["close"] > pl)).fillna(False)
    return out

def detect_fvg(df):
    out = df.copy()
    bf = (out["low"] > out["high"].shift(2)).fillna(False)
    be = (out["high"] < out["low"].shift(2)).fillna(False)
    out["fvg_bullish"] = bf; out["fvg_bearish"] = be
    out["fvg_bull_low"] = out["high"].shift(2).where(bf, np.nan)
    out["fvg_bull_high"] = out["low"].where(bf, np.nan)
    out["fvg_bear_low"] = out["high"].where(be, np.nan)
    out["fvg_bear_high"] = out["low"].shift(2).where(be, np.nan)
    return out

def detect_order_blocks(df):
    out = df.copy()
    body = (out["close"] - out["open"]).abs()
    strong = body >= 1.20 * out["atr"]
    po = out["open"].shift(1); pc = out["close"].shift(1)
    ph = out["high"].shift(1); pl = out["low"].shift(1)
    bbo = (strong & (pc < po) & (out["close"] > ph)).fillna(False)
    beo = (strong & (pc > po) & (out["close"] < pl)).fillna(False)
    out["order_block_bullish"] = bbo; out["order_block_bearish"] = beo
    valid = bbo | beo
    out["ob_low"] = pl.where(valid, np.nan)
    out["ob_high"] = ph.where(valid, np.nan)
    return out

def add_premium_discount(df, lb=50):
    out = df.copy()
    sh = out["high"].rolling(lb).max().shift(1)
    sl = out["low"].rolling(lb).min().shift(1)
    m = (sh + sl) / 2
    out["range_high"] = sh; out["range_low"] = sl; out["premium_mid"] = m
    out["in_discount"] = out["close"] < m; out["in_premium"] = out["close"] > m
    return out

def analyze_smc(df, profile):
    out = df.copy()
    out = find_confirmed_swings(out, profile["swing_order"])
    out = detect_bos_mss(out)
    out = detect_liquidity_sweeps(out)
    out = detect_fvg(out)
    out = detect_order_blocks(out)
    out = add_premium_discount(out, min(profile["structure_lookback"], 100))
    hi = out.index[out["swing_high"]]; lo = out.index[out["swing_low"]]
    out["bsl"] = np.nan; out["ssl"] = np.nan
    if len(hi): out["bsl"] = float(out.loc[hi[-1], "high"])
    if len(lo): out["ssl"] = float(out.loc[lo[-1], "low"])
    return out

def candle_confirmation(df, direction):
    if len(df) < 3: return False
    l = df.iloc[-1]
    b = abs(l["close"] - l["open"]); rng = max(l["high"] - l["low"], 1e-12)
    if direction == "BUY":
        return bool(l["close"] > l["open"] and (l["close"]-l["low"])/rng >= 0.60 and b/rng >= 0.35)
    return bool(l["close"] < l["open"] and (l["high"]-l["close"])/rng >= 0.60 and b/rng >= 0.35)

def detect_divergence(df):
    if len(df) < 30: return None
    w = find_confirmed_swings(df, 3)
    lo = w.index[w["swing_low"]].tolist(); hi = w.index[w["swing_high"]].tolist()
    if len(lo) >= 2:
        p1, p2 = lo[-2], lo[-1]
        if w.loc[p2,"low"] < w.loc[p1,"low"] and w.loc[p2,"rsi"] > w.loc[p1,"rsi"]: return "BULLISH"
    if len(hi) >= 2:
        p1, p2 = hi[-2], hi[-1]
        if w.loc[p2,"high"] > w.loc[p1,"high"] and w.loc[p2,"rsi"] < w.loc[p1,"rsi"]: return "BEARISH"
    return None

def smc_quality(df):
    if df is None or len(df) < 5: return 0.0, []
    l = df.iloc[-1]; sc = 0.0; rr = []
    checks = [("bos_bullish","bos_bearish",20,"BOS"), ("mss_bullish","mss_bearish",20,"MSS"),
              ("liquidity_sweep_bullish","liquidity_sweep_bearish",20,"Liquidity"),
              ("order_block_bullish","order_block_bearish",15,"OB"),
              ("fvg_bullish","fvg_bearish",10,"FVG"),
              ("in_discount","in_premium",15,"Prem/Disc")]
    for a, b, pts, lab in checks:
        if safe_bool(l.get(a)) or safe_bool(l.get(b)): sc += pts; rr.append(lab)
    return min(sc, 100.0), rr


def build_features(df, profile, use_rvwap=True):
    out = df.copy()
    out["ema20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["rsi"] = calc_rsi(out["close"], profile["rsi_period"])
    out["atr"] = calc_atr(out, profile["atr_period"])
    out["macd"], out["macd_signal"], out["macd_histogram"] = calc_macd(out["close"])
    out["bb_upper"], out["bb_mid"], out["bb_lower"] = calc_bollinger(
        out["close"], profile["bb_period"], profile["bb_std"])
    out["chaikin_mf"] = calc_chaikin(out, 21)
    try: bh = (out.index[-1] - out.index[-2]).total_seconds()/3600
    except Exception: bh = 4.0
    if use_rvwap and bh >= 3.5:
        out["vwap"] = calc_rolling_vwap(out, 20); out["vwap_type"] = "rolling"
    else:
        out["vwap"] = calc_session_vwap(out); out["vwap_type"] = "session"
    out = analyze_smc(out, profile)
    return out

def timeframe_bias(df, pair_name=None):
    if df is None or len(df) < 80: return "NEUTRAL", 0
    x = build_features(df, profile_for(pair_name or "")); l = x.iloc[-1]
    bu = be = 0.0
    if l["ema20"] > l["ema50"]: bu += 1
    elif l["ema20"] < l["ema50"]: be += 1
    if l["ema50"] > l["ema200"]: bu += 1
    elif l["ema50"] < l["ema200"]: be += 1
    if l["macd_histogram"] > 0: bu += 1
    elif l["macd_histogram"] < 0: be += 1
    r = safe_float(l.get("rsi"), 50)
    if r >= 55: bu += 1
    elif r <= 45: be += 1
    s = structure_state(x)
    if s["bullish"]: bu += 2
    elif s["bearish"]: be += 2
    if safe_bool(l.get("bos_bullish")) or safe_bool(l.get("mss_bullish")): bu += 1
    if safe_bool(l.get("bos_bearish")) or safe_bool(l.get("mss_bearish")): be += 1
    if bu > be + 0.75: return "BULLISH", int(round(min(10, 10*bu/max(bu+be,1))))
    if be > bu + 0.75: return "BEARISH", int(round(min(10, 10*be/max(bu+be,1))))
    return "NEUTRAL", 0

@st.cache_data(ttl=120, show_spinner=False)
def get_mtf_analysis(symbol, pair_name=None):
    fr = {"1D": ("1y","1d",4.0), "4H": ("6mo","4h",3.0),
          "1H": ("3mo","1h",2.0), "15M": ("30d","15m",1.0)}
    rs = {}; bu = be = tot = 0.0
    for n, (p, i, w) in fr.items():
        f = get_historical_data(symbol, p, i)
        b, s = timeframe_bias(f, pair_name)
        rs[n] = {"bias": b, "strength": s, "weight": w}
        c = w * (s / 10.0)
        if b == "BULLISH": bu += c
        elif b == "BEARISH": be += c
        tot += w
    fi = ("BULLISH" if bu > be*1.20 and bu > 1.5
          else "BEARISH" if be > bu*1.20 and be > 1.5 else "NEUTRAL")
    cf = clamp(50 + abs(bu-be)/max(tot,1)*50, 50, 95)
    return fi, cf, rs

@st.cache_data(ttl=300, show_spinner=False)
def get_dxy_context():
    df = get_historical_data("DX-Y.NYB", "6mo", "4h")
    if df is None: return "NEUTRAL", 50.0, {}
    x = build_features(df, ASSET_PROFILES["forex"]); l = x.iloc[-1]
    bu = be = 0
    if l["close"] > l["ema50"]: bu += 1
    elif l["close"] < l["ema50"]: be += 1
    if l["macd"] > l["macd_signal"]: bu += 1
    elif l["macd"] < l["macd_signal"]: be += 1
    if l["rsi"] > 55: bu += 1
    elif l["rsi"] < 45: be += 1
    if bu > be: return "BULLISH", 55 + 10*bu, {"trend": "USD strength"}
    if be > bu: return "BEARISH", 55 + 10*be, {"trend": "USD weakness"}
    return "NEUTRAL", 50, {"trend": "USD neutral"}

def get_pair_usd_context(pair_name, dxy_bias="NEUTRAL"):
    b, q = parse_pair_currencies(pair_name)
    if not b or not q: return 0.0, "لا تأثير مباشر"
    if "USD" not in (b, q): return 0.0, "تأثير غير مباشر"
    if b == "USD":
        if dxy_bias == "BULLISH": return 1.0, "قوة الدولار تدعم"
        if dxy_bias == "BEARISH": return -1.0, "ضعف الدولار يضغط"
    else:
        if dxy_bias == "BULLISH": return -1.0, "قوة الدولار تضغط"
        if dxy_bias == "BEARISH": return 1.0, "ضعف الدولار يدعم"
    return 0.0, "محايد"

@st.cache_data(ttl=300, show_spinner=False)
def get_gold_dxy_correlation():
    d = get_historical_data("DX-Y.NYB", "3mo", "4h")
    g = get_historical_data("GC=F", "3mo", "4h")
    if d is None or g is None: return None
    a = pd.concat([d["close"].pct_change(), g["close"].pct_change()],
                 axis=1, join="inner").dropna()
    if len(a) < 30: return None
    return float(a.iloc[:,0].rolling(30).corr(a.iloc[:,1]).iloc[-1])

def detect_regime(df):
    l = df.iloc[-1]
    atr = safe_float(l["atr"], np.nan)
    price = safe_float(l["close"], np.nan)
    if not np.isfinite(atr) or atr <= 0 or price <= 0:
        return "UNKNOWN", 50.0
    ema_spread = l["ema20"] - l["ema50"]
    ts = abs(ema_spread) / atr
    if ts >= 0.5:
        return ("TREND_BULLISH" if ema_spread > 0 else "TREND_BEARISH"), 75
    try:
        bw_series = (df["bb_upper"] - df["bb_lower"]) / df["close"]
        bw_mean = bw_series.rolling(100).mean().iloc[-1]
        bw_std = bw_series.rolling(100).std().iloc[-1]
        bw_now = bw_series.iloc[-1]
        if (np.isfinite(bw_std) and bw_std > 0
            and (bw_now - bw_mean) / bw_std < -0.7):
            return "COMPRESSION", 65
    except Exception:
        pass
    return "RANGE", 55


@st.cache_data(ttl=180, show_spinner=False)
def htf_zone_filter(symbol, direction, profile_key):
    try:
        d = get_historical_data(symbol, "1y", "1d")
        if d is None or len(d) < 60: return True, "HTF غير متاح", "UNKNOWN"
        x = build_features(d, ASSET_PROFILES[profile_key]); l = x.iloc[-1]
        ip = safe_bool(l.get("in_premium")); id_ = safe_bool(l.get("in_discount"))
        if direction == "BUY" and ip: return False, "BUY مرفوض: HTF Premium", "PREMIUM"
        if direction == "SELL" and id_: return False, "SELL مرفوض: HTF Discount", "DISCOUNT"
        if direction == "BUY" and id_: return True, "BUY في Discount ✅", "DISCOUNT"
        if direction == "SELL" and ip: return True, "SELL في Premium ✅", "PREMIUM"
        return True, "HTF محايد", "MID"
    except Exception: return True, "HTF فشل", "UNKNOWN"

@st.cache_data(ttl=180, show_spinner=False)
def ltf_entry_trigger(symbol, direction, profile_key):
    try:
        d = get_historical_data(symbol, "3mo", "1h")
        if d is None or len(d) < 60: return True, "LTF غير متاح"
        x = build_features(d, ASSET_PROFILES[profile_key])
        if len(x) < 3: return True, "LTF قصير"
        l = x.iloc[-1]; p = x.iloc[-2]
        if direction == "BUY":
            if safe_bool(l.get("bos_bullish")): return True, "BOS صاعد ✅"
            if safe_bool(l.get("liquidity_sweep_bullish")): return True, "Sweep صاعد ✅"
            if (l["close"] > l["open"] and p["close"] < p["open"]
                and safe_bool(l.get("fvg_bullish"))): return True, "Engulfing+FVG ✅"
        if direction == "SELL":
            if safe_bool(l.get("bos_bearish")): return True, "BOS هابط ✅"
            if safe_bool(l.get("liquidity_sweep_bearish")): return True, "Sweep هابط ✅"
            if (l["close"] < l["open"] and p["close"] > p["open"]
                and safe_bool(l.get("fvg_bearish"))): return True, "Engulfing+FVG ✅"
        return False, "لا trigger"
    except Exception: return True, "LTF فشل"

def session_filter(pair_name, strict=True):
    h = datetime.now(timezone.utc).hour
    lo = 7 <= h <= 16; no = 12 <= h <= 21; ov = 12 <= h <= 16; asi = 0 <= h <= 7
    a = asset_type_from_name(pair_name)
    if a == "crypto":
        if ov: return True, "Overlap", "OVERLAP"
        return True, "Crypto 24/7", "CRYPTO"
    if a == "gold":
        if ov: return True, "Overlap مثالي ✅", "OVERLAP"
        if lo or no: return True, "جلسة نشطة ✅", "ACTIVE"
        if strict: return False, "خارج جلسات الذهب", "DEAD"
        return True, "غير مشدّد", "OFF"
    if strict and asi: return False, "آسيوية — سيولة منخفضة", "ASIAN"
    if ov: return True, "Overlap ✅", "OVERLAP"
    if lo or no: return True, "جلسة نشطة ✅", "ACTIVE"
    if strict: return False, "خارج الجلسات", "DEAD"
    return True, "غير مشدّد", "OFF"

def volatility_regime_filter(df):
    a = df["atr"].dropna() if "atr" in df.columns else pd.Series()
    if len(a) < 100: return True, "بيانات قليلة", "NORMAL"
    ca = a.iloc[-1]; am = a.rolling(100).mean().iloc[-1]; ast = a.rolling(100).std().iloc[-1]
    if not np.isfinite(ast) or ast == 0: return True, "ATR ثابت", "NORMAL"
    z = (ca - am) / ast
    if z < -1.0: return False, f"سوق ميت (Z={z:.1f})", "DEAD"
    if z > 2.5: return False, f"تقلب مفرط (Z={z:.1f})", "CHAOS"
    if 1.5 < z <= 2.5: return True, f"تقلب مرتفع", "HIGH"
    if -1.0 <= z < -0.3: return True, f"تقلب منخفض", "LOW"
    return True, f"طبيعي (Z={z:.1f})", "NORMAL"

def weighted_confluence(pillar_data, direction):
    w = {"structure": 30, "trend": 20, "context": 20, "momentum": 15, "volume": 15}
    t = 0.0
    for p, wt in w.items():
        raw = safe_float(pillar_data.get(direction, {}).get(p), 0)
        s = clamp(raw, 0, 100)
        if s >= 70: t += wt
        elif s >= 50: t += wt * 0.5
        elif s < 30: t -= wt * 0.3
    return clamp(t, 0, 100)

def compute_soft_penalty(items, strict=False):
    if not items or not strict: return 0.0, []
    si = sorted([i for i in items if i[1] > 0], key=lambda x: x[1], reverse=True)[:SOFT_PENALTY_TOP_N]
    w = [1.0, 0.5, 0.25]
    tot = sum(p*w for (_,p), w in zip(si, w))
    return min(tot, MAX_SOFT_PENALTY), si

def news_time_block(events, pair_name, window=45):
    if not events: return False, ""
    now = datetime.now(timezone.utc)
    b, q = parse_pair_currencies(pair_name)
    curs = {b, q} if b and q else {"USD"}
    cmap = {"US":"USD","EU":"EUR","GB":"GBP","JP":"JPY","CH":"CHF",
            "AU":"AUD","NZ":"NZD","CA":"CAD"}
    for e in events:
        imp = str(e.get("impact","")).strip().lower()
        if imp not in ("high","3","high impact"): continue
        c = str(e.get("country","")).strip().upper()
        if cmap.get(c, c) not in curs: continue
        try:
            ds = e.get("date","")
            if not ds: continue
            et = pd.to_datetime(ds)
            if et.tzinfo is None: et = et.tz_localize("UTC")
            if abs((et - now).total_seconds())/60 < window:
                return True, f"خبر {e.get('event')} خلال {window}د"
        except Exception: continue
    return False, ""

def displacement_check(df, direction):
    if len(df) < 2: return False, "بيانات قليلة"
    l = df.iloc[-1]; atr = safe_float(l.get("atr"), 0)
    if atr <= 0: return False, "ATR غير صالح"
    b = abs(l["close"] - l["open"])
    if b < 1.5 * atr: return False, f"لا Displacement ({b/atr:.1f}x)"
    if direction == "BUY" and l["close"] < l["open"]: return False, "ضد BUY"
    if direction == "SELL" and l["close"] > l["open"]: return False, "ضد SELL"
    return True, f"Displacement {b/atr:.1f}x ✅"

def in_kill_zone(asset_type):
    h = datetime.now(timezone.utc).hour
    if asset_type == "crypto": return True, "Crypto 24/7"
    for n, (s, e) in KILL_ZONES.items():
        if s <= h < e: return True, f"{n} ✅"
    return False, "خارج Kill Zones"

def ote_filter(df, direction):
    sh = get_last_two_swings(df, "high"); sl = get_last_two_swings(df, "low")
    if not sh or not sl: return True, "OTE غير متاح"
    sh_v = sh[-1][1]; sl_v = sl[-1][1]
    c = df["close"].iloc[-1]; leg = sh_v - sl_v
    if leg <= 0: return True, "موجة غير صالحة"
    if direction == "BUY":
        r = (sh_v - c) / leg
        if 0.55 <= r <= 0.85: return True, f"OTE صاعد {r*100:.0f}% ✅"
        return False, f"خارج OTE ({r*100:.0f}%)"
    else:
        r = (c - sl_v) / leg
        if 0.55 <= r <= 0.85: return True, f"OTE هابط {r*100:.0f}% ✅"
        return False, f"خارج OTE ({r*100:.0f}%)"

@st.cache_data(ttl=600, show_spinner=False)
def weekly_bias(symbol, pair_name):
    d = get_historical_data(symbol, "2y", "1wk")
    if d is None or len(d) < 30: return "NEUTRAL", 0
    try:
        x = build_features(d, profile_for(pair_name))
        if len(x) < 5: return "NEUTRAL", 0
        l = x.iloc[-1]; bu = be = 0
        if l["ema20"] > l["ema50"]: bu += 1
        elif l["ema20"] < l["ema50"]: be += 1
        if l["macd"] > l["macd_signal"]: bu += 1
        elif l["macd"] < l["macd_signal"]: be += 1
        s = structure_state(x)
        if s["bullish"]: bu += 2
        elif s["bearish"]: be += 2
        if bu > be: return "BULLISH", bu
        if be > bu: return "BEARISH", be
        return "NEUTRAL", 0
    except Exception: return "NEUTRAL", 0


PILLAR_WEIGHTS = {"structure": 0.28, "trend": 0.18, "momentum": 0.14,
                  "volume": 0.14, "context": 0.26}

def directional_score(df, pair_name, symbol, dxy_bias=None, gold_corr=None,
                     ccy_strength=None, rate_diff=0.0, risk=None, bonds=None):
    l = df.iloc[-1]
    sc = {"BUY": {k: 0.0 for k in PILLAR_WEIGHTS},
          "SELL": {k: 0.0 for k in PILLAR_WEIGHTS}}
    rs = []
    s = structure_state(df)
    if s["bullish"]: sc["BUY"]["structure"] += 45; rs.append("هيكل صاعد")
    elif s["bearish"]: sc["SELL"]["structure"] += 45; rs.append("هيكل هابط")
    recent = df.iloc[-5:]
    if recent["bos_bullish"].any(): sc["BUY"]["structure"] += 35; rs.append("BOS صاعد")
    if recent["bos_bearish"].any(): sc["SELL"]["structure"] += 35; rs.append("BOS هابط")
    if recent["mss_bullish"].any(): sc["BUY"]["structure"] += 20; rs.append("MSS صاعد")
    if recent["mss_bearish"].any(): sc["SELL"]["structure"] += 20; rs.append("MSS هابط")
    if recent["liquidity_sweep_bullish"].any(): sc["BUY"]["structure"] += 25
    if recent["liquidity_sweep_bearish"].any(): sc["SELL"]["structure"] += 25
    if recent["order_block_bullish"].any(): sc["BUY"]["structure"] += 15
    if recent["order_block_bearish"].any(): sc["SELL"]["structure"] += 15
    if recent["fvg_bullish"].any(): sc["BUY"]["structure"] += 10
    if recent["fvg_bearish"].any(): sc["SELL"]["structure"] += 10
    if safe_bool(l.get("in_discount")): sc["BUY"]["structure"] += 10
    if safe_bool(l.get("in_premium")): sc["SELL"]["structure"] += 10
    if l["ema20"] > l["ema50"] > l["ema200"]: sc["BUY"]["trend"] += 80
    elif l["ema20"] < l["ema50"] < l["ema200"]: sc["SELL"]["trend"] += 80
    else:
        if l["ema20"] > l["ema50"]: sc["BUY"]["trend"] += 45
        elif l["ema20"] < l["ema50"]: sc["SELL"]["trend"] += 45
    if l["close"] > l["ema20"] > l["ema50"] > l["ema200"]: sc["BUY"]["trend"] += 20
    elif l["close"] < l["ema20"] < l["ema50"] < l["ema200"]: sc["SELL"]["trend"] += 20
    r = safe_float(l["rsi"], 50)
    if r >= 55: sc["BUY"]["momentum"] += 45
    elif r <= 45: sc["SELL"]["momentum"] += 45
    if l["macd"] > l["macd_signal"] and l["macd_histogram"] > 0: sc["BUY"]["momentum"] += 45
    elif l["macd"] < l["macd_signal"] and l["macd_histogram"] < 0: sc["SELL"]["momentum"] += 45
    if l["chaikin_mf"] > 0.10: sc["BUY"]["momentum"] += 10
    elif l["chaikin_mf"] < -0.10: sc["SELL"]["momentum"] += 10
    if l["close"] > l["vwap"]: sc["BUY"]["volume"] += 45
    elif l["close"] < l["vwap"]: sc["SELL"]["volume"] += 45
    if l["chaikin_mf"] > 0: sc["BUY"]["volume"] += 35
    elif l["chaikin_mf"] < 0: sc["SELL"]["volume"] += 35
    va = df["volume"].rolling(20).mean().iloc[-1]
    if va and np.isfinite(va) and l["volume"] > va:
        if l["close"] > l["open"]: sc["BUY"]["volume"] += 20
        elif l["close"] < l["open"]: sc["SELL"]["volume"] += 20
    if dxy_bias is None: dxy_bias, _, _ = get_dxy_context()
    ui, um = get_pair_usd_context(pair_name, dxy_bias=dxy_bias)
    if ui > 0: sc["BUY"]["context"] += 25; rs.append("DXY يدعم")
    elif ui < 0: sc["SELL"]["context"] += 25; rs.append("DXY يدعم")
    if "Gold" in pair_name or "XAU" in pair_name.upper():
        if gold_corr is None: gold_corr = get_gold_dxy_correlation()
        if gold_corr is not None:
            if gold_corr <= -0.50 and dxy_bias == "BEARISH": sc["BUY"]["context"] += 15
            elif gold_corr <= -0.50 and dxy_bias == "BULLISH": sc["SELL"]["context"] += 15
    fb, fs, fd = get_fundamental_score(pair_name, ccy_strength=ccy_strength,
                                       rate_diff=rate_diff, risk=risk, bonds=bonds)
    sc["BUY"]["context"] += fb * 0.6; sc["SELL"]["context"] += fs * 0.6
    if fb > 20: rs.append("أساسي BUY")
    if fs > 20: rs.append("أساسي SELL")
    reg, _ = detect_regime(df)
    if reg == "TREND_BULLISH": sc["BUY"]["context"] += 15
    elif reg == "TREND_BEARISH": sc["SELL"]["context"] += 15
    tb = ts = 0.0
    for p, w in PILLAR_WEIGHTS.items():
        sc["BUY"][p] = clamp(sc["BUY"][p], 0, 100)
        sc["SELL"][p] = clamp(sc["SELL"][p], 0, 100)
        tb += sc["BUY"][p] * w; ts += sc["SELL"][p] * w
    dv = detect_divergence(df)
    if dv == "BULLISH": tb += 3
    elif dv == "BEARISH": ts += 3
    return {"buy": clamp(tb, 0, 100), "sell": clamp(ts, 0, 100),
            "pillars": sc, "reasons": rs, "dxy_bias": dxy_bias, "usd_msg": um,
            "regime": reg, "divergence": dv, "fund_details": fd,
            "fund_buy": fb, "fund_sell": fs}

def get_fundamental_score(pair_name, ccy_strength=None, rate_diff=0.0,
                          risk=None, bonds=None, sentiment=None):
    if ccy_strength is None: ccy_strength = get_currency_strength_matrix()
    if risk is None: risk = get_risk_sentiment()
    if bonds is None: bonds = get_bond_yields()
    b, q = parse_pair_currencies(pair_name)
    bb = 0.0; sb = 0.0; det = []
    if ccy_strength and b in ccy_strength and q in ccy_strength:
        bstr = ccy_strength[b]; qstr = ccy_strength[q]; cd = bstr - qstr
        det.append({"factor": "Currency Strength", "base_val": bstr,
                    "quote_val": qstr, "diff": cd})
        if cd > 20: bb += 35
        elif cd > 10: bb += 20
        elif cd < -20: sb += 35
        elif cd < -10: sb += 20
    if abs(rate_diff) >= 0.5:
        det.append({"factor": "Rate Differential", "diff": rate_diff})
        if rate_diff > 2.0: bb += 18
        elif rate_diff > 1.0: bb += 10
        elif rate_diff < -2.0: sb += 18
        elif rate_diff < -1.0: sb += 10
    if risk and risk.get("bias_impact", 0) != 0:
        det.append({"factor": "Risk Sentiment", "mode": risk["risk_mode"]})
        if risk["risk_mode"] == "RISK-OFF":
            if b in RISK_OFF_CURRENCIES and q not in RISK_OFF_CURRENCIES: bb += 12
            elif q in RISK_OFF_CURRENCIES and b not in RISK_OFF_CURRENCIES: sb += 12
        elif risk["risk_mode"] == "RISK-ON":
            if b in RISK_ON_CURRENCIES and q not in RISK_ON_CURRENCIES: bb += 12
            elif q in RISK_ON_CURRENCIES and b not in RISK_ON_CURRENCIES: sb += 12
    if bonds:
        bbb, bsb, bmsg = get_bond_bias_for_pair(pair_name, bonds)
        if bbb > 0 or bsb > 0:
            det.append({"factor": "Bond Yields", "buy": bbb, "sell": bsb, "msg": bmsg})
            bb += bbb; sb += bsb
    return clamp(bb, 0, 100), clamp(sb, 0, 100), det

def confirmation_gate(df, direction, pillar_scores, regime, mtf_bias="NEUTRAL",
                      mtf_conf=50.0, profile=None, weekly_bias_val="NEUTRAL"):
    if df is None or len(df) < 30: return False, 0.0, ["بيانات قليلة"], ["DATA"]
    profile = profile or ASSET_PROFILES["forex"]
    l = df.iloc[-1]; sc = 0.0; rs = []; bl = []
    if (direction == "BUY" and regime == "TREND_BULLISH") or \
       (direction == "SELL" and regime == "TREND_BEARISH"):
        sc += 20; rs.append("Regime متوافق")
    elif regime == "RANGE": sc += 15; rs.append("Range")
    elif regime == "COMPRESSION": sc += 12; rs.append("Compression")
    else: bl.append("Regime غير متوافق")
    if (direction == "BUY" and mtf_bias == "BULLISH") or \
       (direction == "SELL" and mtf_bias == "BEARISH"):
        sc += 25 * min(mtf_conf/95, 1); rs.append("MTF متوافق")
    elif mtf_bias != "NEUTRAL": bl.append("MTF ضد الاتجاه")
    if (direction == "BUY" and weekly_bias_val == "BULLISH") or \
       (direction == "SELL" and weekly_bias_val == "BEARISH"):
        sc += 15; rs.append("Weekly متوافق")
    elif weekly_bias_val != "NEUTRAL": bl.append("Weekly ضد الاتجاه")
    eo = (direction == "BUY" and l["ema20"] > l["ema50"]) or \
         (direction == "SELL" and l["ema20"] < l["ema50"])
    if eo: sc += 15; rs.append("EMA alignment")
    else: bl.append("EMA غير مؤيد")
    mo = (direction == "BUY" and l["macd_histogram"] > 0) or \
         (direction == "SELL" and l["macd_histogram"] < 0)
    if mo: sc += 15; rs.append("MACD مؤيد")
    else: bl.append("Momentum غير مؤيد")
    if candle_confirmation(df, direction): sc += 10; rs.append("Candle")
    smc_s, smc_r = smc_quality(df)
    if smc_s >= 40: sc += 15; rs.extend(smc_r[:3])
    elif smc_s < 20: bl.append("SMC ضعيف")
    own = sum(float(v) for v in pillar_scores.get(direction, {}).values())
    opp = sum(float(v) for v in pillar_scores.get(
        "SELL" if direction == "BUY" else "BUY", {}).values())
    if own < 180: bl.append("أدلة ضعيفة")
    if opp > own * 0.85: bl.append("تعارض قوي")
    else: sc += 5
    hard = any(x in bl for x in ("MTF ضد الاتجاه","Regime غير متوافق","Weekly ضد الاتجاه"))
    th = max(55, MIN_EMIT_CONFIDENCE - 10)
    ok = sc >= th and not hard and len(bl) <= 3
    return ok, clamp(sc, 0, 100), rs, bl


def latest_structure_levels(df):
    lo = df.index[df["swing_low"]].tolist(); hi = df.index[df["swing_high"]].tolist()
    sl = float(df.loc[lo[-1], "low"]) if lo else np.nan
    sh = float(df.loc[hi[-1], "high"]) if hi else np.nan
    return sl, sh

def calc_pivot_points(df):
    if len(df) < 2: return None
    l = df.iloc[-1]; h = float(l["high"]); lo = float(l["low"]); c = float(l["close"])
    p = (h + lo + c)/3; rng = h - lo
    if rng <= 0: return None
    return {"pivot": p, "range": rng,
            "r1": 2*p-lo, "r2": p+rng, "r3": h+2*(p-lo),
            "s1": 2*p-h, "s2": p-rng, "s3": lo-2*(h-p),
            "fib_r1": p+0.382*rng, "fib_r2": p+0.618*rng, "fib_r3": p+1.000*rng,
            "fib_s1": p-0.382*rng, "fib_s2": p-0.618*rng, "fib_s3": p-1.000*rng,
            "high": h, "low": lo, "close": c}

def find_impulse_leg(df, direction, lookback=120):
    w = df.iloc[-lookback:].copy() if len(df) > lookback else df.copy()
    if len(w) < 20: return None
    if direction == "BUY":
        pos = int(w["low"].values.argmin())
        if pos >= len(w) - 5:
            sub = w.iloc[:len(w)-5]
            if len(sub) < 10: return None
            w = sub; pos = int(w["low"].values.argmin())
        st = float(w["low"].iloc[pos]); after = w.iloc[pos:]
        if len(after) < 3: return None
        e = float(after["high"].iloc[int(after["high"].values.argmax())])
        if e <= st: return None
        return {"start": st, "end": e, "leg": e-st, "direction": "BUY"}
    else:
        pos = int(w["high"].values.argmax())
        if pos >= len(w) - 5:
            sub = w.iloc[:len(w)-5]
            if len(sub) < 10: return None
            w = sub; pos = int(w["high"].values.argmax())
        st = float(w["high"].iloc[pos]); after = w.iloc[pos:]
        if len(after) < 3: return None
        e = float(after["low"].iloc[int(after["low"].values.argmin())])
        if e >= st: return None
        return {"start": st, "end": e, "leg": st-e, "direction": "SELL"}

def fib_levels_from_impulse(impulse):
    if not impulse: return None
    s, e, lg = impulse["start"], impulse["end"], impulse["leg"]
    d = impulse["direction"]
    def r(p): return e - p*lg if d == "BUY" else e + p*lg
    def x(m): return s + m*lg if d == "BUY" else s - m*lg
    return {"retracement": {"0.382": r(0.382), "0.500": r(0.500),
                            "0.618": r(0.618), "0.786": r(0.786)},
            "extension": {"1.000": e, "1.272": x(1.272), "1.618": x(1.618),
                          "2.000": x(2.000), "2.618": x(2.618)}}

def collect_sr_levels(df, lookback=200):
    lv = []
    w = df.iloc[-lookback:] if len(df) > lookback else df
    if "swing_high" in w.columns:
        for i in w.index[w["swing_high"]][-5:]: lv.append(float(w.loc[i, "high"]))
    if "swing_low" in w.columns:
        for i in w.index[w["swing_low"]][-5:]: lv.append(float(w.loc[i, "low"]))
    if len(w) >= 20:
        lv.append(float(w["high"].iloc[-20:].max()))
        lv.append(float(w["low"].iloc[-20:].min()))
    return sorted({l for l in lv if np.isfinite(l) and l > 0})


def detect_inducement(df, direction, lookback=50):
    if len(df) < 20: return None
    work = df.iloc[-lookback:]
    if direction == "BUY":
        swings_l = work.index[work["swing_low"]].tolist()
        swings_h = work.index[work["swing_high"]].tolist()
        if not swings_l or not swings_h: return None
        last_high = swings_h[-1]
        prior = [s for s in swings_l if s < last_high]
        if not prior: return None
        return float(work.loc[prior[-1], "low"])
    else:
        swings_l = work.index[work["swing_low"]].tolist()
        swings_h = work.index[work["swing_high"]].tolist()
        if not swings_l or not swings_h: return None
        last_low = swings_l[-1]
        prior = [s for s in swings_h if s < last_low]
        if not prior: return None
        return float(work.loc[prior[-1], "high"])


def find_nearest_liquidity(df, current_price, direction, lookback=100):
    if len(df) < 10: return []
    work = df.iloc[-lookback:] if len(df) > lookback else df
    levels = []
    if direction == "BUY":
        for idx in work.index[work["swing_high"]][-5:]:
            lvl = float(work.loc[idx, "high"])
            if lvl > current_price: levels.append({"name": "BSL", "level": lvl})
        if len(work) >= 20:
            rh = work["high"].iloc[-20:].values
            for i in range(len(rh) - 1):
                for j in range(i + 1, len(rh)):
                    if rh[i] > 0 and abs(rh[i] - rh[j]) / rh[i] < 0.0015:
                        lvl = max(rh[i], rh[j])
                        if lvl > current_price:
                            levels.append({"name": "Equal Highs", "level": lvl})
                        break
    else:
        for idx in work.index[work["swing_low"]][-5:]:
            lvl = float(work.loc[idx, "low"])
            if lvl < current_price: levels.append({"name": "SSL", "level": lvl})
        if len(work) >= 20:
            rl = work["low"].iloc[-20:].values
            for i in range(len(rl) - 1):
                for j in range(i + 1, len(rl)):
                    if rl[i] > 0 and abs(rl[i] - rl[j]) / rl[i] < 0.0015:
                        lvl = min(rl[i], rl[j])
                        if lvl < current_price:
                            levels.append({"name": "Equal Lows", "level": lvl})
                        break
    levels.sort(key=lambda x: x["level"], reverse=(direction == "SELL"))
    seen = set(); out = []
    for lv in levels:
        key = round(lv["level"], 5)
        if key not in seen:
            seen.add(key); out.append(lv)
    return out[:5]


def find_nearest_fvg(df, current_price, direction, lookback=100):
    work = df.iloc[-lookback:] if len(df) > lookback else df
    fvgs = []
    if direction == "BUY":
        for idx in work.index[work["fvg_bearish"]]:
            lo = safe_float(work.loc[idx, "fvg_bear_low"], np.nan)
            hi = safe_float(work.loc[idx, "fvg_bear_high"], np.nan)
            if np.isfinite(lo) and np.isfinite(hi) and lo > current_price:
                fvgs.append({"name": "Bear FVG", "low": lo, "high": hi, "mid": (lo+hi)/2})
    else:
        for idx in work.index[work["fvg_bullish"]]:
            lo = safe_float(work.loc[idx, "fvg_bull_low"], np.nan)
            hi = safe_float(work.loc[idx, "fvg_bull_high"], np.nan)
            if np.isfinite(lo) and np.isfinite(hi) and hi < current_price:
                fvgs.append({"name": "Bull FVG", "low": lo, "high": hi, "mid": (lo+hi)/2})
    fvgs.sort(key=lambda x: x["mid"], reverse=(direction == "SELL"))
    return fvgs[:3]


def find_order_block_levels(df, current_price, direction, lookback=100):
    work = df.iloc[-lookback:] if len(df) > lookback else df
    obs = []
    if direction == "BUY":
        for idx in work.index[work["order_block_bullish"]][-5:]:
            lo = safe_float(work.loc[idx, "ob_low"], np.nan)
            hi = safe_float(work.loc[idx, "ob_high"], np.nan)
            if np.isfinite(lo) and np.isfinite(hi) and hi < current_price:
                obs.append({"name": "Bull OB", "low": lo, "high": hi, "mid": (lo+hi)/2})
    else:
        for idx in work.index[work["order_block_bearish"]][-5:]:
            lo = safe_float(work.loc[idx, "ob_low"], np.nan)
            hi = safe_float(work.loc[idx, "ob_high"], np.nan)
            if np.isfinite(lo) and np.isfinite(hi) and lo > current_price:
                obs.append({"name": "Bear OB", "low": lo, "high": hi, "mid": (lo+hi)/2})
    obs.sort(key=lambda x: x["mid"], reverse=(direction == "SELL"))
    return obs[:3]


def calculate_ict_sl_tp(df, direction, current_price, profile):
    atr = safe_float(df["atr"].iloc[-1], np.nan)
    if not np.isfinite(atr) or atr <= 0: return None
    all_levels = []
    idm = detect_inducement(df, direction)
    if idm is not None and np.isfinite(idm):
        all_levels.append((idm, "IDM (ICT)", "ict"))
    obs = find_order_block_levels(df, current_price, direction)
    for ob in obs:
        if direction == "BUY":
            all_levels.append((ob["low"], f"{ob['name']} Low", "ob"))
        else:
            all_levels.append((ob["high"], f"{ob['name']} High", "ob"))
    fvgs = find_nearest_fvg(df, current_price, direction)
    for fv in fvgs:
        if direction == "BUY":
            all_levels.append((fv["low"], f"{fv['name']} Bottom", "fvg"))
        else:
            all_levels.append((fv["high"], f"{fv['name']} Top", "fvg"))
    liq = find_nearest_liquidity(df, current_price, direction)
    for lq in liq:
        all_levels.append((lq["level"], lq["name"], "liq"))
    swing_low, swing_high = latest_structure_levels(df)
    if np.isfinite(swing_low): all_levels.append((swing_low, "Swing Low", "swing"))
    if np.isfinite(swing_high): all_levels.append((swing_high, "Swing High", "swing"))
    ssl = safe_float(df["ssl"].iloc[-1], np.nan)
    bsl = safe_float(df["bsl"].iloc[-1], np.nan)
    if np.isfinite(ssl): all_levels.append((ssl, "SSL", "liquidity"))
    if np.isfinite(bsl): all_levels.append((bsl, "BSL", "liquidity"))
    pv = calc_pivot_points(df)
    if pv:
        for k, nm in (("s1","Pivot S1"),("s2","Pivot S2"),("s3","Pivot S3"),
                      ("r1","Pivot R1"),("r2","Pivot R2"),("r3","Pivot R3"),
                      ("fib_s1","FibPivot S1"),("fib_s2","FibPivot S2"),
                      ("fib_r1","FibPivot R1"),("fib_r2","FibPivot R2")):
            lvl = pv.get(k)
            if lvl and np.isfinite(lvl):
                all_levels.append((lvl, nm, "pivot"))
    imp = find_impulse_leg(df, direction)
    fibs = fib_levels_from_impulse(imp)
    if fibs:
        for k, v in fibs["retracement"].items():
            if np.isfinite(v): all_levels.append((v, f"Fib {k}", "fib"))
        for k, v in fibs["extension"].items():
            if np.isfinite(v): all_levels.append((v, f"Fib ext {k}", "fib"))
    recent_low = float(df["low"].iloc[-10:].min())
    recent_high = float(df["high"].iloc[-10:].max())
    all_levels.append((recent_low, "10-bar Low", "recent"))
    all_levels.append((recent_high, "10-bar High", "recent"))
    for lvl in collect_sr_levels(df, 200):
        if np.isfinite(lvl): all_levels.append((lvl, "S/R", "sr"))

    buffer_price = 0.15 * atr
    if direction == "BUY":
        candidates = [(lvl, nm, src) for lvl, nm, src in all_levels
                      if lvl < current_price - buffer_price]
        candidates.sort(key=lambda x: x[0], reverse=True)
    else:
        candidates = [(lvl, nm, src) for lvl, nm, src in all_levels
                      if lvl > current_price + buffer_price]
        candidates.sort(key=lambda x: x[0])

    min_dist = SL_MIN_DIST_ATR * atr
    max_dist = SL_MAX_DIST_ATR * atr
    chosen_level = None; chosen_name = "ATR Fallback"

    for lvl, nm, src in candidates:
        dist = abs(current_price - lvl)
        if min_dist <= dist <= max_dist:
            chosen_level = lvl; chosen_name = nm; break
    if chosen_level is None and candidates:
        for lvl, nm, src in candidates:
            dist = abs(current_price - lvl)
            if dist >= min_dist:
                chosen_level = lvl; chosen_name = nm; break
        if chosen_level is None:
            chosen_level = candidates[0][0]; chosen_name = candidates[0][1]
    if chosen_level is None:
        if direction == "BUY": chosen_level = current_price - 1.0 * atr
        else: chosen_level = current_price + 1.0 * atr
        chosen_name = "ATR (No levels)"

    if direction == "BUY":
        sl = chosen_level - SL_BUFFER_ATR * atr
    else:
        sl = chosen_level + SL_BUFFER_ATR * atr
    if direction == "BUY":
        if (current_price - sl) < min_dist: sl = current_price - min_dist
    else:
        if (sl - current_price) < min_dist: sl = current_price + min_dist

    risk = abs(current_price - sl)
    if risk <= 0: return None

    liq_tp = find_nearest_liquidity(df, current_price, direction)
    fvgs_tp = find_nearest_fvg(df, current_price, direction)
    tp_cands = []
    if direction == "BUY":
        for lq in liq_tp:
            if lq["level"] > current_price + 0.3 * atr:
                tp_cands.append((lq["level"], lq["name"]))
        for fv in fvgs_tp:
            if fv["mid"] > current_price + 0.3 * atr:
                tp_cands.append((fv["mid"], fv["name"]))
        if pv:
            for k, nm in (("r1","Pivot R1"),("r2","Pivot R2"),("r3","Pivot R3"),
                          ("fib_r1","FibPivot R1"),("fib_r2","FibPivot R2"),
                          ("fib_r3","FibPivot R3")):
                lvl = pv.get(k)
                if lvl and lvl > current_price + 0.3 * atr:
                    tp_cands.append((lvl, nm))
        if fibs:
            for k, v in fibs["extension"].items():
                if v > current_price + 0.3 * atr:
                    tp_cands.append((v, f"Fib ext {k}"))
        if np.isfinite(swing_high) and swing_high > current_price + 0.3 * atr:
            tp_cands.append((swing_high, "Swing High"))
        if np.isfinite(bsl) and bsl > current_price + 0.3 * atr:
            tp_cands.append((bsl, "BSL"))
        for lvl in collect_sr_levels(df, 200):
            if lvl > current_price + 0.5 * atr: tp_cands.append((lvl, "S/R"))
    else:
        for lq in liq_tp:
            if lq["level"] < current_price - 0.3 * atr:
                tp_cands.append((lq["level"], lq["name"]))
        for fv in fvgs_tp:
            if fv["mid"] < current_price - 0.3 * atr:
                tp_cands.append((fv["mid"], fv["name"]))
        if pv:
            for k, nm in (("s1","Pivot S1"),("s2","Pivot S2"),("s3","Pivot S3"),
                          ("fib_s1","FibPivot S1"),("fib_s2","FibPivot S2"),
                          ("fib_s3","FibPivot S3")):
                lvl = pv.get(k)
                if lvl and lvl < current_price - 0.3 * atr:
                    tp_cands.append((lvl, nm))
        if fibs:
            for k, v in fibs["extension"].items():
                if v < current_price - 0.3 * atr:
                    tp_cands.append((v, f"Fib ext {k}"))
        if np.isfinite(swing_low) and swing_low < current_price - 0.3 * atr:
            tp_cands.append((swing_low, "Swing Low"))
        if np.isfinite(ssl) and ssl < current_price - 0.3 * atr:
            tp_cands.append((ssl, "SSL"))
        for lvl in collect_sr_levels(df, 200):
            if lvl < current_price - 0.5 * atr: tp_cands.append((lvl, "S/R"))
    tp_cands.sort(key=lambda x: x[0], reverse=(direction == "SELL"))

    RR1, RR2, RR3 = MIN_RR_TP1, MIN_RR_TP2, MIN_RR_TP3
    min_t1 = current_price + risk * RR1 if direction == "BUY" else current_price - risk * RR1
    min_t2 = current_price + risk * RR2 if direction == "BUY" else current_price - risk * RR2
    min_t3 = current_price + risk * RR3 if direction == "BUY" else current_price - risk * RR3
    valid_t1 = [c for c in tp_cands
                if (direction == "BUY" and c[0] >= min_t1) or
                   (direction == "SELL" and c[0] <= min_t1)]
    if valid_t1: t1, t1n = valid_t1[0]
    else: t1 = min_t1; t1n = f"{RR1}R"
    thr2 = max(min_t2, t1 + 0.3*atr) if direction == "BUY" else min(min_t2, t1 - 0.3*atr)
    valid_t2 = [c for c in tp_cands
                if (direction == "BUY" and c[0] >= thr2) or
                   (direction == "SELL" and c[0] <= thr2)]
    if valid_t2: t2, t2n = valid_t2[0]
    else: t2 = min_t2; t2n = f"{RR2}R"
    thr3 = max(min_t3, t2 + 0.3*atr) if direction == "BUY" else min(min_t3, t2 - 0.3*atr)
    valid_t3 = [c for c in tp_cands
                if (direction == "BUY" and c[0] >= thr3) or
                   (direction == "SELL" and c[0] <= thr3)]
    if valid_t3: t3, t3n = valid_t3[0]
    else: t3 = min_t3; t3n = f"{RR3}R"
    rr1 = abs(t1 - current_price) / risk
    rr2 = abs(t2 - current_price) / risk
    rr3 = abs(t3 - current_price) / risk
    return {"entry": current_price, "stop_loss": sl,
            "target1": t1, "target2": t2, "target3": t3, "risk": risk,
            "risk_reward_1": rr1, "risk_reward_2": rr2, "risk_reward_3": rr3,
            "sources": {"sl": chosen_name, "tp1": t1n, "tp2": t2n, "tp3": t3n},
            "idm": idm, "obs": obs, "fvgs": fvgs, "liq": liq,
            "fibs": fibs, "pivots": pv, "impulse": imp,
            "sl_level_price": chosen_level}


def validate_levels(signal, levels, profile):
    if not levels: return False, "لا مستويات"
    if signal == "BUY":
        if not levels["stop_loss"] < levels["entry"] < levels["target1"]:
            return False, "ترتيب BUY غير صالح"
    else:
        if not levels["target1"] < levels["entry"] < levels["stop_loss"]:
            return False, "ترتيب SELL غير صالح"
    if levels["risk_reward_1"] < 0.70: return False, "TP1 RR منخفض"
    if levels["risk_reward_2"] < 1.10: return False, "TP2 RR منخفض"
    if levels["risk_reward_3"] < 1.60: return False, "TP3 RR منخفض"
    return True, ""


# ============================================================
# FLIP DETECTION
# ============================================================

def detect_reversal_candle(df):
    if len(df) < 3: return []
    last = df.iloc[-1]; prev = df.iloc[-2]
    body = abs(last["close"] - last["open"])
    rng = max(last["high"] - last["low"], 1e-12)
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]
    patterns = []
    if lower_wick > 2 * body and upper_wick < body * 0.5:
        patterns.append(("Hammer", "BULLISH", 75))
    if upper_wick > 2 * body and lower_wick < body * 0.5:
        patterns.append(("Shooting Star", "BEARISH", 75))
    if (prev["close"] < prev["open"] and last["close"] > last["open"]
        and last["close"] > prev["open"] and last["open"] < prev["close"]):
        patterns.append(("Bullish Engulfing", "BULLISH", 80))
    if (prev["close"] > prev["open"] and last["close"] < last["open"]
        and last["close"] < prev["open"] and last["open"] > prev["close"]):
        patterns.append(("Bearish Engulfing", "BEARISH", 80))
    if rng > 0 and body / rng < 0.15:
        patterns.append(("Doji", "NEUTRAL", 50))
    if lower_wick > 3 * body and last["close"] > last["open"]:
        patterns.append(("Bullish Pin Bar", "BULLISH", 70))
    if upper_wick > 3 * body and last["close"] < last["open"]:
        patterns.append(("Bearish Pin Bar", "BEARISH", 70))
    return patterns


def check_level_proximity(df, current_price, direction_of_flip, atr):
    levels = []
    tolerance = 0.5 * atr
    if direction_of_flip == "BUY":
        sw_l = get_last_two_swings(df, "low")
        if sw_l:
            for _, lvl in sw_l:
                if abs(current_price - lvl) < tolerance:
                    levels.append((lvl, "Swing Low"))
        pv = calc_pivot_points(df)
        if pv:
            for k, nm in (("s1","Pivot S1"), ("s2","Pivot S2"), ("fib_s1","FibPivot S1")):
                lvl = pv.get(k)
                if lvl and abs(current_price - lvl) < tolerance:
                    levels.append((lvl, nm))
        ssl = safe_float(df["ssl"].iloc[-1], np.nan)
        if np.isfinite(ssl) and abs(current_price - ssl) < tolerance:
            levels.append((ssl, "SSL"))
        obs = find_order_block_levels(df, current_price, "BUY")
        for ob in obs:
            if abs(current_price - ob["mid"]) < tolerance:
                levels.append((ob["mid"], "Bull OB"))
        imp = find_impulse_leg(df, "BUY")
        fibs = fib_levels_from_impulse(imp)
        if fibs:
            for k in ("0.618", "0.786"):
                lvl = fibs["retracement"].get(k)
                if lvl and abs(current_price - lvl) < tolerance:
                    levels.append((lvl, f"Fib {k}"))
    else:
        sw_h = get_last_two_swings(df, "high")
        if sw_h:
            for _, lvl in sw_h:
                if abs(current_price - lvl) < tolerance:
                    levels.append((lvl, "Swing High"))
        pv = calc_pivot_points(df)
        if pv:
            for k, nm in (("r1","Pivot R1"), ("r2","Pivot R2"), ("fib_r1","FibPivot R1")):
                lvl = pv.get(k)
                if lvl and abs(current_price - lvl) < tolerance:
                    levels.append((lvl, nm))
        bsl = safe_float(df["bsl"].iloc[-1], np.nan)
        if np.isfinite(bsl) and abs(current_price - bsl) < tolerance:
            levels.append((bsl, "BSL"))
        obs = find_order_block_levels(df, current_price, "SELL")
        for ob in obs:
            if abs(current_price - ob["mid"]) < tolerance:
                levels.append((ob["mid"], "Bear OB"))
        imp = find_impulse_leg(df, "SELL")
        fibs = fib_levels_from_impulse(imp)
        if fibs:
            for k in ("0.618", "0.786"):
                lvl = fibs["retracement"].get(k)
                if lvl and abs(current_price - lvl) < tolerance:
                    levels.append((lvl, f"Fib {k}"))
    return levels


def detect_signal_flip(df, current_price, original_signal, profile):
    if original_signal not in ("BUY", "SELL"): return None
    atr = safe_float(df["atr"].iloc[-1], np.nan)
    if not np.isfinite(atr) or atr <= 0: return None
    last = df.iloc[-1]
    flip_signal = "SELL" if original_signal == "BUY" else "BUY"
    triggers = []
    total_score = 0.0

    candles = detect_reversal_candle(df) or []
    for pat_name, pat_dir, pat_score in candles:
        if pat_dir == flip_signal:
            triggers.append({"name": f"شمعة {pat_name}", "score": pat_score, "icon": "🕯️"})
            total_score += pat_score * 0.3

    level_hits = check_level_proximity(df, current_price, flip_signal, atr)
    for lvl, lvl_name in level_hits[:2]:
        triggers.append({"name": f"سعر عند {lvl_name}", "score": 70, "icon": "📍"})
        total_score += 25

    if flip_signal == "BUY" and safe_bool(last.get("mss_bullish")):
        triggers.append({"name": "MSS صاعد", "score": 80, "icon": "🔄"}); total_score += 30
    if flip_signal == "SELL" and safe_bool(last.get("mss_bearish")):
        triggers.append({"name": "MSS هابط", "score": 80, "icon": "🔄"}); total_score += 30

    if flip_signal == "BUY" and safe_bool(last.get("liquidity_sweep_bullish")):
        triggers.append({"name": "Liquidity Sweep صاعد", "score": 75, "icon": "💧"}); total_score += 25
    if flip_signal == "SELL" and safe_bool(last.get("liquidity_sweep_bearish")):
        triggers.append({"name": "Liquidity Sweep هابط", "score": 75, "icon": "💧"}); total_score += 25

    dv = detect_divergence(df)
    if flip_signal == "BUY" and dv == "BULLISH":
        triggers.append({"name": "RSI Divergence صاعد", "score": 70, "icon": "📈"}); total_score += 20
    if flip_signal == "SELL" and dv == "BEARISH":
        triggers.append({"name": "RSI Divergence هابط", "score": 70, "icon": "📉"}); total_score += 20

    s_ = structure_state(df)
    if flip_signal == "BUY" and s_["bullish"] and original_signal == "SELL":
        triggers.append({"name": "الهيكل انقلب صاعداً", "score": 85, "icon": "🏗️"}); total_score += 35
    if flip_signal == "SELL" and s_["bearish"] and original_signal == "BUY":
        triggers.append({"name": "الهيكل انقلب هابطاً", "score": 85, "icon": "🏗️"}); total_score += 35

    rsi = safe_float(last.get("rsi"), 50)
    if flip_signal == "BUY" and rsi <= 30:
        triggers.append({"name": f"RSI Oversold ({rsi:.0f})", "score": 65, "icon": "⚡"}); total_score += 15
    if flip_signal == "SELL" and rsi >= 70:
        triggers.append({"name": f"RSI Overbought ({rsi:.0f})", "score": 65, "icon": "⚡"}); total_score += 15

    vwap = safe_float(last.get("vwap"), current_price)
    if flip_signal == "BUY" and current_price > vwap * 1.002:
        triggers.append({"name": "فوق VWAP", "score": 55, "icon": "📊"}); total_score += 10
    if flip_signal == "SELL" and current_price < vwap * 0.998:
        triggers.append({"name": "تحت VWAP", "score": 55, "icon": "📊"}); total_score += 10

    if flip_signal == "BUY" and last["macd"] > last["macd_signal"] and last["macd_histogram"] > 0:
        triggers.append({"name": "MACD انقلب صاعداً", "score": 60, "icon": "📈"}); total_score += 15
    if flip_signal == "SELL" and last["macd"] < last["macd_signal"] and last["macd_histogram"] < 0:
        triggers.append({"name": "MACD انقلب هابطاً", "score": 60, "icon": "📉"}); total_score += 15

    if flip_signal == "BUY" and last["ema20"] > last["ema50"] and original_signal == "SELL":
        triggers.append({"name": "EMA20 > EMA50", "score": 60, "icon": "📈"}); total_score += 12
    if flip_signal == "SELL" and last["ema20"] < last["ema50"] and original_signal == "BUY":
        triggers.append({"name": "EMA20 < EMA50", "score": 60, "icon": "📉"}); total_score += 12

    total_score = clamp(total_score, 0, 100)
    if total_score < 22 or len(triggers) == 0:
        return {"flip_signal": None, "confidence": total_score,
                "triggers": triggers, "status": "NO_FLIP",
                "message": "لا يوجد انعكاس", "new_levels": None}

    if total_score >= 65:
        status = "STRONG_FLIP"; msg = f"🚨 إشارة {flip_signal} مستقلة قوية"
    elif total_score >= 42:
        status = "POSSIBLE_FLIP"; msg = f"⚠️ إشارة {flip_signal} مستقلة محتملة"
    else:
        status = "WEAK_FLIP"; msg = f"💡 إشارة {flip_signal} مستقلة أولية"

    new_levels = None
    try:
        new_levels = calculate_ict_sl_tp(df, flip_signal, current_price, profile)
    except Exception: pass

    return {"flip_signal": flip_signal, "confidence": total_score,
            "triggers": triggers, "status": status,
            "message": msg, "new_levels": new_levels}


def flip_raw_to_pct(raw_score):
    return round(clamp(50 + (raw_score - 22) * 45 / 78, 50, 95), 1)


# ============================================================
# ENTRY CONFIRMATION
# ============================================================

def entry_confirmation_score(df, direction, levels, pair_name):
    if df is None or len(df) < 50: return None
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else last
    atr = safe_float(last.get("atr"), 0)
    if atr <= 0: return None

    checks = []; total = 0

    if direction == "BUY":
        candle_ok = float(last["close"]) > float(last["open"]) and \
                    float(last["close"]) > float(prev["close"])
    else:
        candle_ok = float(last["close"]) < float(last["open"]) and \
                    float(last["close"]) < float(prev["close"])
    if candle_ok:
        checks.append({"name": "شمعة مؤكدة", "pass": True, "score": 15, "icon": "🕯️"}); total += 15
    else:
        checks.append({"name": "شمعة غير مؤكدة", "pass": False, "score": 0, "icon": "🕯️"})

    s_ = structure_state(df)
    struct_ok = (direction == "BUY" and s_["bullish"]) or (direction == "SELL" and s_["bearish"])
    if struct_ok:
        checks.append({"name": "الهيكل يدعم", "pass": True, "score": 15, "icon": "🏗️"}); total += 15
    else:
        checks.append({"name": "الهيكل ضد", "pass": False, "score": 0, "icon": "🏗️"})

    vol_avg = df["volume"].rolling(20).mean().iloc[-1]
    vol_now = safe_float(last.get("volume"), 0)
    if vol_avg > 0 and vol_now > vol_avg * 1.15:
        checks.append({"name": "فوليوم قوي", "pass": True, "score": 10, "icon": "📊"}); total += 10
    elif vol_avg > 0 and vol_now > vol_avg:
        checks.append({"name": "فوليوم عادي", "pass": True, "score": 5, "icon": "📊"}); total += 5
    else:
        checks.append({"name": "فوليوم ضعيف", "pass": False, "score": 0, "icon": "📊"})

    rsi = safe_float(last.get("rsi"), 50)
    macd_ok = (direction == "BUY" and last["macd_histogram"] > 0) or \
              (direction == "SELL" and last["macd_histogram"] < 0)
    rsi_ok = (direction == "BUY" and 50 <= rsi <= 72) or (direction == "SELL" and 28 <= rsi <= 50)
    if macd_ok and rsi_ok:
        checks.append({"name": "زخم متوافق", "pass": True, "score": 10, "icon": "⚡"}); total += 10
    elif macd_ok or rsi_ok:
        checks.append({"name": "زخم جزئي", "pass": True, "score": 5, "icon": "⚡"}); total += 5
    else:
        checks.append({"name": "زخم ضد", "pass": False, "score": 0, "icon": "⚡"})

    ema20 = safe_float(last.get("ema20"), 0)
    if ema20 > 0:
        dist = abs(float(last["close"]) - ema20) / atr
        if dist < 1.5:
            checks.append({"name": "قريب من EMA20", "pass": True, "score": 10, "icon": "📍"}); total += 10
        elif dist < 2.5:
            checks.append({"name": "متوسط البعد", "pass": True, "score": 5, "icon": "📍"}); total += 5
        else:
            checks.append({"name": "Overextended", "pass": False, "score": 0, "icon": "📍"})
    else:
        checks.append({"name": "EMA20 غير متاح", "pass": False, "score": 0, "icon": "📍"})

    h = datetime.now(timezone.utc).hour
    asset = asset_type_from_name(pair_name)
    active = (7 <= h <= 21) or asset == "crypto"
    if active:
        checks.append({"name": "جلسة نشطة", "pass": True, "score": 5, "icon": "🕐"}); total += 5
    else:
        checks.append({"name": "خارج الجلسات", "pass": False, "score": 0, "icon": "🕐"})

    dv = detect_divergence(df)
    div_ok = (direction == "BUY" and dv != "BEARISH") or (direction == "SELL" and dv != "BULLISH")
    if div_ok:
        checks.append({"name": "لا Divergence ضد", "pass": True, "score": 10, "icon": "🔄"}); total += 10
    else:
        checks.append({"name": "Divergence ضد", "pass": False, "score": 0, "icon": "🔄"})

    vwap = safe_float(last.get("vwap"), 0)
    if vwap > 0:
        vwap_ok = (direction == "BUY" and last["close"] > vwap) or \
                  (direction == "SELL" and last["close"] < vwap)
        if vwap_ok:
            checks.append({"name": "VWAP متوافق", "pass": True, "score": 5, "icon": "📉"}); total += 5
        else:
            checks.append({"name": "VWAP ضد", "pass": False, "score": 0, "icon": "📉"})
    else:
        checks.append({"name": "VWAP غير متاح", "pass": False, "score": 0, "icon": "📉"})

    bos_ok = False
    try:
        if direction == "BUY" and "bos_bullish" in df.columns:
            bos_ok = bool(df["bos_bullish"].iloc[-5:].any())
        elif direction == "SELL" and "bos_bearish" in df.columns:
            bos_ok = bool(df["bos_bearish"].iloc[-5:].any())
    except Exception: pass
    if bos_ok:
        checks.append({"name": "BOS حديث", "pass": True, "score": 10, "icon": "🔓"}); total += 10
    else:
        checks.append({"name": "لا BOS حديث", "pass": False, "score": 0, "icon": "🔓"})

    zone_ok = False
    if direction == "BUY":
        if safe_bool(last.get("in_discount")): zone_ok = True
        elif safe_bool(last.get("fvg_bullish")) or safe_bool(last.get("order_block_bullish")):
            zone_ok = True
    else:
        if safe_bool(last.get("in_premium")): zone_ok = True
        elif safe_bool(last.get("fvg_bearish")) or safe_bool(last.get("order_block_bearish")):
            zone_ok = True
    if zone_ok:
        checks.append({"name": "منطقة دخول ممتازة", "pass": True, "score": 10, "icon": "🎯"}); total += 10
    else:
        checks.append({"name": "منطقة دخول متباعدة", "pass": True, "score": 3, "icon": "🎯"}); total += 3

    final_total = max(0, min(total, 100))

    enter_thr = int(MIN_EMIT_CONFIDENCE)
    retr_thr  = max(55, enter_thr - 15)
    close_thr = max(35, enter_thr - 35)

    if final_total >= enter_thr:
        verdict = "ENTER_NOW"; vtext = "🟢 ادخل الآن"; vcolor = "#7cd4a0"
    elif final_total >= retr_thr:
        verdict = "WAIT_RETRACE"; vtext = "🟡 انتظر ارتداد"; vcolor = "#f5c87a"
    elif final_total >= close_thr:
        verdict = "WAIT_CLOSE"; vtext = "🟠 انتظر إغلاق الشمعة"; vcolor = "#f5a87a"
    else:
        verdict = "NO_ENTRY"; vtext = "🔴 لا تدخل الآن"; vcolor = "#f57a7a"

    return {"score": final_total, "raw_score": total,
            "verdict": verdict, "verdict_text": vtext,
            "verdict_color": vcolor, "checks": checks}


def compute_flip_grade(conf_pct, ec_score):
    if conf_pct >= A_PLUS_MIN and ec_score >= 80: return "A+"
    if conf_pct >= A_MIN and ec_score >= MIN_EMIT_CONFIDENCE: return "A"
    if conf_pct >= B_MIN and ec_score >= (MIN_EMIT_CONFIDENCE - 5): return "B"
    if conf_pct >= C_MIN and ec_score >= 50: return "C"
    return "WAIT"


def passes_confidence_gate(signal_conf, entry_score=None):
    if signal_conf < MIN_EMIT_CONFIDENCE:
        return False, f"الثقة {signal_conf:.1f}% < {MIN_EMIT_CONFIDENCE:.0f}%"
    if entry_score is not None and entry_score < MIN_EMIT_CONFIDENCE:
        return False, f"التأكيد {entry_score:.0f}/100 < {MIN_EMIT_CONFIDENCE:.0f}"
    return True, ""


def generate_signal(df, current_price, pair_name, symbol,
                    news_block=False, skip_external_filters=False,
                    precomputed=None, strict_soft=False):
    profile = profile_for(pair_name); profile_key = get_asset_profile(pair_name)
    _required = {"ema20","ema50","ema200","rsi","atr","swing_high",
                 "bos_bullish","vwap","bb_upper"}
    if not _required.issubset(df.columns):
        df = build_features(df, profile)

    if precomputed is None:
        mtf, mtfc, mtfd = get_mtf_analysis(symbol, pair_name)
        wk, _ = weekly_bias(symbol, pair_name)
        dxy, _, _ = get_dxy_context()
        gc = get_gold_dxy_correlation() if ("Gold" in pair_name or "XAU" in pair_name.upper()) else None
        ccs = get_currency_strength_matrix()
        st.session_state["_ccy_strength_cache"] = ccs
        rd, _ = get_interest_rate_differential(pair_name)
        rk = get_risk_sentiment(); bd = get_bond_yields(); sent = None
    else:
        mtf = precomputed.get("mtf_bias","NEUTRAL"); mtfc = precomputed.get("mtf_conf", 50.0)
        mtfd = precomputed.get("mtf_details", {}); wk = precomputed.get("weekly_bias","NEUTRAL")
        dxy = precomputed.get("dxy_bias","NEUTRAL"); gc = precomputed.get("gold_corr")
        ccs = precomputed.get("ccy_strength"); rd = precomputed.get("rate_diff", 0.0)
        rk = precomputed.get("risk"); bd = precomputed.get("bonds"); sent = precomputed.get("sentiment")

    sc = directional_score(df, pair_name, symbol, dxy_bias=dxy, gold_corr=gc,
                          ccy_strength=ccs, rate_diff=rd, risk=rk, bonds=bd)
    if sent is None: sent = estimate_retail_sentiment(df, profile)

    buy, sell = sc["buy"], sc["sell"]
    if mtf == "BULLISH": buy += 8; sell -= 4
    elif mtf == "BEARISH": sell += 8; buy -= 4
    if wk == "BULLISH": buy += 5; sell -= 3
    elif wk == "BEARISH": sell += 5; buy -= 3
    buy, sell = clamp(buy, 0, 100), clamp(sell, 0, 100)
    gap = abs(buy - sell)
    cand_dir = "BUY" if buy > sell else "SELL"
    smsg = ""
    if gap >= MIN_SIGNAL_GAP:
        sb, smsg = get_sentiment_bias_for_signal(sent, cand_dir)
        if sb != 0:
            if cand_dir == "BUY":
                buy = clamp(buy + sb, 0, 100)
            else:
                sell = clamp(sell + sb, 0, 100)
            if cand_dir == "BUY" and buy <= sell: buy = sell + 1.0
            if cand_dir == "SELL" and sell <= buy: sell = buy + 1.0
            gap = abs(buy - sell)
    signal = "WAIT" if gap < MIN_SIGNAL_GAP else ("BUY" if buy > sell else "SELL")

    l = df.iloc[-1]
    mc = False
    if safe_bool(l.get("mss_bullish")) and sell > buy: mc = True
    if safe_bool(l.get("mss_bearish")) and buy > sell: mc = True
    r = safe_float(l.get("rsi"), 50); reg = sc["regime"]
    if reg == "RANGE":
        if signal == "BUY" and r > profile["rsi_ob"] and not safe_bool(l.get("mss_bullish")):
            buy = max(0, buy - 5)
        if signal == "SELL" and r < profile["rsi_os"] and not safe_bool(l.get("mss_bearish")):
            sell = max(0, sell - 5)
    conf = clamp(50 + abs(buy-sell)*0.75 + max(0, max(buy,sell)-60)*0.25, 50, 95)
    sp = []
    if signal in ("BUY","SELL") and mtf != "NEUTRAL":
        if (signal == "BUY" and mtf != "BULLISH") or (signal == "SELL" and mtf != "BEARISH"):
            sp.append(("MTF ضد", PENALTY_MTF_AGAINST))
    if signal in ("BUY","SELL") and wk != "NEUTRAL":
        if (signal == "BUY" and wk != "BULLISH") or (signal == "SELL" and wk != "BEARISH"):
            sp.append(("Weekly ضد", PENALTY_WEEKLY_AGAINST))
    if signal in ("BUY","SELL") and sc["regime"] in ("RANGE","COMPRESSION"):
        sp.append((f"Regime {sc['regime']}", PENALTY_RANGE_REGIME))
    if signal in ("BUY","SELL"):
        an = safe_float(l.get("atr"), 0)
        if an > 0:
            bd_ = abs(float(l["close"]) - float(l["open"]))
            if bd_ < 0.50*an: sp.append(("شمعة ضعيفة", PENALTY_WEAK_CANDLE))
            elif signal == "BUY" and l["close"] < l["open"]:
                sp.append(("شمعة ضد", PENALTY_WEAK_CANDLE))
            elif signal == "SELL" and l["close"] > l["open"]:
                sp.append(("شمعة ضد", PENALTY_WEAK_CANDLE))
    if mc and signal in ("BUY","SELL"): sp.append(("MSS Conflict", 8))
    cand = signal if signal in ("BUY","SELL") else ("BUY" if buy > sell else "SELL")
    lv = calculate_ict_sl_tp(df, cand, current_price, profile)
    rok, rmsg = validate_levels(cand, lv, profile) if lv else (False, "")
    if signal in ("BUY","SELL") and not rok: signal = "WAIT"; conf = 0
    pil = sc["pillars"]; wc = weighted_confluence(pil, cand)
    co, cs, cr, cbl = confirmation_gate(df, cand, pil, sc["regime"], mtf, mtfc, profile, wk)
    flt = {}; flt["MSS Conflict"] = {"pass": not mc,
        "msg": "MSS معاكس" if mc else "MSS متوافق"}
    ap = True; br_ = ""
    efn = ["HTF Zone","LTF Trigger","Session","Volatility",
           "Kill Zone","OTE","Displacement","News Window"]
    if skip_external_filters:
        for n in efn: flt[n] = {"pass": True, "msg": "Backtest"}
        ntb = False
    else:
        ho, hm, hz = htf_zone_filter(symbol, cand, profile_key)
        flt["HTF Zone"] = {"pass": ho, "msg": hm, "zone": hz}
        if not ho: ap = False; br_ = hm
        lo_, lm = ltf_entry_trigger(symbol, cand, profile_key)
        flt["LTF Trigger"] = {"pass": lo_, "msg": lm}
        if not lo_: sp.append(("LTF", 6))
        _strict_session = (profile_key == "crypto")
        so, sm, sl_ = session_filter(pair_name, strict=_strict_session)
        if not so and MODE != "strict":
            so = True; sm += " (relaxed)"
        flt["Session"] = {"pass": so, "msg": sm, "label": sl_}
        if not so: sp.append(("Session", 5))
        vo, vm, vl = volatility_regime_filter(df)
        flt["Volatility"] = {"pass": vo, "msg": vm, "label": vl}
        if not vo:
            if vl == "CHAOS": ap = False; br_ = br_ or vm
            else: sp.append(("Volatility", 6))
        ko, km = in_kill_zone(asset_type_from_name(pair_name))
        flt["Kill Zone"] = {"pass": ko, "msg": km}
        if not ko and MODE == "strict": sp.append(("KZ", 3))
        oo, om = ote_filter(df, cand)
        flt["OTE"] = {"pass": oo, "msg": om}
        if not oo and MODE == "strict": sp.append(("OTE", 5))
        do, dm = displacement_check(df, cand)
        flt["Displacement"] = {"pass": do, "msg": dm}
        if not do: sp.append(("Disp", 4))
        ntb, ntm = news_time_block(st.session_state.get("economic_events") or [], pair_name)
        flt["News Window"] = {"pass": not ntb, "msg": ntm or "لا خبر"}
        if ntb: ap = False; br_ = br_ or ntm
    mo, mm = is_market_open(pair_name)
    flt["Market Open"] = {"pass": mo, "msg": mm}
    if not mo and not skip_external_filters: ap = False; br_ = br_ or mm
    wo = (wk == "NEUTRAL" or (cand == "BUY" and wk == "BULLISH") or
          (cand == "SELL" and wk == "BEARISH"))
    flt["Weekly Bias"] = {"pass": wo, "msg": f"Weekly: {wk}"}
    flt["Confluence"] = {"pass": wc >= 50, "msg": f"Confluence: {wc:.0f}/100"}
    rc = conf
    pt, ap2 = compute_soft_penalty(sp, strict=True)
    ec = clamp(rc - pt, 0, 95)
    mlp = st.session_state.get("ml_model"); mlprob = None; mlstat = "no_model"
    if mlp and signal in ("BUY","SELL"):
        rfm = {"pillars": pil, "mtf_conf": mtfc, "confirmation_score": cs,
               "raw_confidence": rc, "regime": sc["regime"], "mtf_bias": mtf,
               "weekly_bias": wk, "fund_buy": sc.get("fund_buy", 0),
               "fund_sell": sc.get("fund_sell", 0), "df": df}
        ec, mlprob, mlstat = ml_adjusted_confidence(rfm, signal, mlp)
        ec = clamp(ec, 0, 99)

    cs_a_plus = _p["cs_a_plus"]
    cs_a = _p["cs_a"]
    cs_b = _p["cs_b"]
    cs_c = _p["cs_c"]

    if ec >= A_PLUS_MIN and cs >= cs_a_plus: tg = "A+"
    elif ec >= A_MIN and cs >= cs_a: tg = "A"
    elif ec >= B_MIN and cs >= cs_b: tg = "B"
    elif ec >= C_MIN and cs >= cs_c: tg = "C"
    else: tg = "WAIT"

    if skip_external_filters:
        if signal == "WAIT": es, er = "WAIT", "Signal WAIT"
        elif not ap: es, er = "BLOCKED", f"Hard Gate: {br_}"
        elif tg in ("A+","A","B"): es, er = "EXECUTE", f"{tg} PASS (backtest)"
        elif tg == "C": es, er = "WATCH", "C مراقبة"
        else: es, er = "WAIT", "لا اجتياز"
    else:
        if signal == "WAIT":
            es, er = "WAIT", "Signal WAIT"
        elif not ap:
            es, er = "BLOCKED", f"Hard Gate: {br_}"
        elif news_block:
            es, er = "WAIT", "خبر عالي التأثير"
        elif ec < MIN_EMIT_CONFIDENCE:
            es, er = "WAIT", f"🔒 الثقة {ec:.1f}% < {MIN_EMIT_CONFIDENCE:.0f}%"
        elif cs < MIN_EMIT_CONFIDENCE:
            es, er = "WAIT", f"🔒 التأكيد {cs:.1f}/100 < {MIN_EMIT_CONFIDENCE:.0f}"
        elif tg == "A+":
            es, er = "EXECUTE", f"🚦 A+ (Conf {ec:.0f}% / Confirm {cs:.0f})"
        elif tg == "A":
            es, er = "EXECUTE", f"🚦 A (Conf {ec:.0f}% / Confirm {cs:.0f})"
        elif tg == "B":
            es, er = "EXECUTE", f"🟢 B (Conf {ec:.0f}% / Confirm {cs:.0f})"
        else:
            es, er = "WAIT", "لا اجتياز"
    conf = ec
    adv = ", ".join(f"{n}({p})" for n,p in sp) or "None"
    return {"signal": signal, "confidence": conf, "raw_confidence": rc,
            "buy_score": buy, "sell_score": sell, "weighted_confluence": wc,
            "pillars": pil, "mtf_bias": mtf, "mtf_conf": mtfc, "mtf_details": mtfd,
            "weekly_bias": wk, "levels": lv if rok else None, "df": df,
            "confirmation_ok": co, "confirmation_score": cs,
            "confirmation_reasons": cr, "confirmation_blockers": cbl,
            "execution_status": es, "execution_reason": er, "trade_grade": tg,
            "soft_penalties": pt, "soft_advisories": adv,
            "filter_results": flt, "all_filters_passed": ap,
            "filter_block_reason": br_, "regime": sc["regime"],
            "dxy_bias": sc["dxy_bias"], "usd_msg": sc["usd_msg"],
            "divergence": sc["divergence"], "reasons": sc["reasons"] + cr,
            "fund_details": sc.get("fund_details", []),
            "fund_buy": sc.get("fund_buy", 0), "fund_sell": sc.get("fund_sell", 0),
            "bond_data": bd, "sentiment_data": sent, "sentiment_msg": smsg,
            "ml_probability": mlprob, "ml_status": mlstat,
            "rate_diff": rd, "pair_name": pair_name}


def _bias_from_slice(df_s, pair_name):
    if df_s is None or len(df_s) < 60: return "NEUTRAL", 50.0
    try:
        x = df_s.copy()
        x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
        x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
        x["ema200"] = x["close"].ewm(span=200, adjust=False).mean()
        l = x.iloc[-1]; bu = be = 0
        if l["ema20"] > l["ema50"]: bu += 1
        elif l["ema20"] < l["ema50"]: be += 1
        if l["ema50"] > l["ema200"]: bu += 1
        elif l["ema50"] < l["ema200"]: be += 1
        if bu > be: return "BULLISH", 60.0 + bu*5
        if be > bu: return "BEARISH", 60.0 + be*5
        return "NEUTRAL", 50.0
    except Exception: return "NEUTRAL", 50.0

def _weekly_bias_from_slice(df_s, pair_name):
    if df_s is None or len(df_s) < 100: return "NEUTRAL"
    try:
        w = df_s.resample("1W").agg({"open":"first","high":"max","low":"min",
                                      "close":"last","volume":"sum"}).dropna()
        if len(w) < 10: return "NEUTRAL"
        sma = w["close"].rolling(min(20, len(w))).mean().iloc[-1]
        last = w["close"].iloc[-1]
        if not np.isfinite(sma): return "NEUTRAL"
        if last > sma * 1.005: return "BULLISH"
        if last < sma * 0.995: return "BEARISH"
        return "NEUTRAL"
    except Exception: return "NEUTRAL"

@st.cache_data(ttl=600, show_spinner=False)
def quick_backtest(symbol, pair_name, lookback=200, run_mc=True):
    try:
        dff = get_historical_data(symbol, "1y", "4h")
        if dff is None or len(dff) < lookback + 50: return None
        prof = profile_for(pair_name)
        try:
            dxy_df = get_historical_data("DX-Y.NYB", "1y", "4h")
            dxy_b = _bias_from_slice(dxy_df, "DXY")[0] if dxy_df is not None else "NEUTRAL"
        except Exception: dxy_b = "NEUTRAL"
        try: gc = get_gold_dxy_correlation() if ("Gold" in pair_name or "XAU" in pair_name.upper()) else None
        except Exception: gc = None
        try:
            ccs = get_currency_strength_matrix()
            st.session_state["_ccy_strength_cache"] = ccs
            rd, _ = get_interest_rate_differential(pair_name)
            rk = get_risk_sentiment(); bd = get_bond_yields()
        except Exception: ccs, rd, rk, bd = None, 0.0, None, None
        df = dff.copy()
        w = 0; l = 0; tr = 0.0; eq = 0.0; pk = 0.0; mdd = 0.0
        tlog = []; mlt = []
        si = 100; ei = len(df) - 20
        for i in range(si, ei):
            sl_df = df.iloc[:i].copy()
            price = float(df["close"].iloc[i-1])
            mb, mcf = _bias_from_slice(sl_df, pair_name)
            wb = _weekly_bias_from_slice(sl_df, pair_name)
            pcd = {"mtf_bias": mb, "mtf_conf": mcf, "mtf_details": {},
                   "weekly_bias": wb, "dxy_bias": dxy_b, "gold_corr": gc,
                   "ccy_strength": ccs, "rate_diff": rd, "risk": rk,
                   "bonds": bd, "sentiment": None}
            try:
                res = generate_signal(sl_df, price, pair_name, symbol,
                                      skip_external_filters=True, precomputed=pcd)
            except Exception: continue
            if res["signal"] == "WAIT" or res["levels"] is None: continue
            if res["execution_status"] != "EXECUTE": continue
            slv = res["levels"]["stop_loss"]; t1 = res["levels"]["target1"]
            d = res["signal"]; rr1 = res["levels"]["risk_reward_1"]
            fut = df.iloc[i:i+20]
            htp = hsl = False; out = "OPEN"
            for _, row in fut.iterrows():
                if d == "BUY":
                    if row["low"] <= slv: hsl = True; out = "LOSS"; break
                    if row["high"] >= t1: htp = True; out = "WIN"; break
                else:
                    if row["high"] >= slv: hsl = True; out = "LOSS"; break
                    if row["low"] <= t1: htp = True; out = "WIN"; break
            if htp: w += 1; tr += rr1; eq += rr1
            elif hsl: l += 1; tr -= 1.0; eq -= 1.0
            else: continue
            try:
                feat = extract_ml_features(res, d)
                mlt.append({"features": feat, "label": 1 if htp else 0})
            except Exception: pass
            pk = max(pk, eq); mdd = max(mdd, pk - eq)
            tlog.append({"bar_index": i, "direction": d, "outcome": out,
                         "r": rr1 if htp else -1.0,
                         "grade": res.get("trade_grade","?"),
                         "confidence": res["confidence"]})
        tot = w + l
        if tot == 0:
            return {"trades":0,"wins":0,"losses":0,"win_rate":0,"total_R":0,
                    "expectancy":0,"profit_factor":0,"max_drawdown":0,"sharpe":0,
                    "avg_r":0,"trades_log":[],"monte_carlo":None,"ml_trades":[]}
        ar = tr/tot
        wr_ = [t["r"] for t in tlog if t["outcome"] == "WIN"]
        lr_ = [t["r"] for t in tlog if t["outcome"] == "LOSS"]
        alr = wr_ + lr_
        sh = 0.0
        if len(alr) > 1:
            rs = float(np.std(alr, ddof=1))
            sh = (ar/rs*np.sqrt(len(alr))) if rs > 0 else 0.0
        mcr = monte_carlo_simulation(alr, 1000) if run_mc and len(alr) >= 5 else None
        return {"trades": tot, "wins": w, "losses": l,
                "win_rate": w/tot*100, "total_R": tr, "expectancy": ar, "avg_r": ar,
                "profit_factor": sum(wr_)/max(abs(sum(lr_)), 1e-9),
                "max_drawdown": mdd, "sharpe": sh,
                "trades_log": tlog[-50:], "monte_carlo": mcr, "ml_trades": mlt}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=600, show_spinner=False)
def get_all_signals_parallel():
    results = []
    def one(pn, sym):
        try:
            p, _ = get_spot_price(sym)
            d = get_historical_data(sym, "6mo", "4h")
            if p is None or d is None: return None
            r = generate_signal(d, p, pn, sym, skip_external_filters=False)
            lv = r["levels"] or {}
            sig_ = r["signal"]

            ec_score = 0; ec_verdict = "—"
            if sig_ in ("BUY","SELL") and lv:
                try:
                    ec = entry_confirmation_score(r.get("df"), sig_, lv, pn)
                    if ec:
                        ec_score = ec["score"]
                        ec_verdict = ec["verdict_text"]
                except Exception: pass

            orig_gate_ok = False; orig_gate = "—"
            if sig_ in ("BUY","SELL"):
                orig_gate_ok, _ = passes_confidence_gate(r["confidence"], ec_score)
                orig_gate = "✅" if orig_gate_ok else "❌"

            flip_sig = "—"; flip_conf_raw = 0; flip_status = "NONE"; flip_icon = ""
            flip_sl = "—"; flip_tp1 = "—"; flip_tp2 = "—"; flip_tp3 = "—"
            flip_rr1 = "—"; flip_sl_src = "—"
            flip_ec_score = 0; flip_ec_verdict = "—"; flip_grade_col = "—"
            flip_confidence_pct = 0
            flip_gate = "—"

            if sig_ in ("BUY", "SELL"):
                try:
                    fl = detect_signal_flip(r.get("df"), p, sig_, profile_for(pn))
                    if fl and fl.get("flip_signal"):
                        flip_sig = fl["flip_signal"]
                        flip_conf_raw = round(fl["confidence"], 0)
                        flip_status = fl["status"]
                        if fl["status"] == "STRONG_FLIP": flip_icon = "🚨"
                        elif fl["status"] == "POSSIBLE_FLIP": flip_icon = "⚠️"
                        else: flip_icon = "💡"
                        flip_confidence_pct = flip_raw_to_pct(fl["confidence"])
                        nl = fl.get("new_levels")
                        if nl:
                            flip_sl = fmt_price(nl["stop_loss"], pn)
                            flip_tp1 = fmt_price(nl["target1"], pn)
                            flip_tp2 = fmt_price(nl["target2"], pn)
                            flip_tp3 = fmt_price(nl["target3"], pn)
                            flip_rr1 = f"1:{nl['risk_reward_1']:.2f}"
                            flip_sl_src = nl.get("sources", {}).get("sl", "—")
                            fc = entry_confirmation_score(
                                r.get("df"), flip_sig, nl, pn)
                            if fc:
                                flip_ec_score = fc["score"]
                                flip_ec_verdict = fc["verdict_text"]
                                flip_grade_col = compute_flip_grade(
                                    flip_confidence_pct, fc["score"])
                        flip_gate_ok, _ = passes_confidence_gate(
                            flip_confidence_pct, flip_ec_score)
                        flip_gate = "✅" if flip_gate_ok else "❌"
                except Exception: pass

            return {
                "الزوج": pn, "الإشارة": sig_,
                "الثقة": round(r["confidence"], 1),
                "🎯 تأكيد": f"{ec_verdict} ({ec_score})" if ec_verdict != "—" else "—",
                "🚦 أصلي": orig_gate,
                "Grade": r.get("trade_grade", "WAIT"),
                "🔄 Flip": f"{flip_icon} {flip_sig}" if flip_sig != "—" else "—",
                "Flip Raw": flip_conf_raw if flip_conf_raw > 0 else "—",
                "Flip Conf%": flip_confidence_pct if flip_confidence_pct > 0 else "—",
                "Flip Status": flip_status if flip_status != "NONE" else "—",
                "🎯 Flip تأكيد": f"{flip_ec_verdict} ({flip_ec_score})" if flip_ec_score > 0 else "—",
                "🚦 Flip": flip_gate,
                "Flip Grade": flip_grade_col,
                "🛑 F-SL": flip_sl,
                "🎯 F-TP1": flip_tp1, "🎯 F-TP2": flip_tp2, "🎯 F-TP3": flip_tp3,
                "F-RR1": flip_rr1, "F-SL Src": flip_sl_src,
                "BUY": round(r["buy_score"], 1), "SELL": round(r["sell_score"], 1),
                "MTF": r["mtf_bias"], "Weekly": r["weekly_bias"],
                "Regime": r["regime"],
                "Conf": round(r["weighted_confluence"], 0),
                "Confirm": round(r["confirmation_score"], 1),
                "Execution": r["execution_status"],
                "السعر": fmt_price(p, pn),
                "SL": fmt_price(lv.get("stop_loss"), pn),
                "SLsrc": lv.get("sources", {}).get("sl", "—"),
                "TP1": fmt_price(lv.get("target1"), pn),
                "RR3": round(lv.get("risk_reward_3", 0), 2) if lv else 0,
                "_ec_score": ec_score, "_flip_ec_score": flip_ec_score}
        except Exception: return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(one, p, s): (p, i) for i, (p, s) in enumerate(PAIRS.items())}
        for f in concurrent.futures.as_completed(futs):
            try:
                r = f.result()
                if r: results.append(r)
            except Exception: pass
    if not results: return pd.DataFrame()
    out = pd.DataFrame(results)
    def sort_key(row):
        gate_score = 0
        if row.get("🚦 أصلي") == "✅": gate_score += 100
        if row.get("🚦 Flip") == "✅": gate_score += 100
        max_score = max(row.get("_ec_score", 0), row.get("_flip_ec_score", 0))
        sig = row["الإشارة"]
        sp_ = {"BUY": 0, "SELL": 1, "WAIT": 2}.get(sig, 3)
        return (-gate_score, -max_score, sp_)
    out["_sort"] = out.apply(sort_key, axis=1)
    out = out.sort_values("_sort").drop(columns=["_sort"])
    return out


def find_strongest_trade():
    """يمسح كل الأزواج، يرجع أقوى إشارة تمر البوابة مع كامل تفاصيلها."""
    df = get_all_signals_parallel()
    if df is None or df.empty:
        return {"status": "NONE"}
    mask = pd.Series([False] * len(df), index=df.index)
    if "🚦 أصلي" in df.columns:
        mask = mask | (df["🚦 أصلي"] == "✅")
    if "🚦 Flip" in df.columns:
        mask = mask | (df["🚦 Flip"] == "✅")
    strong = df[mask].copy()
    if strong.empty:
        return {"status": "NONE"}

    def calc_score(row):
        s_o = s_f = 0.0
        if row.get("🚦 أصلي") == "✅":
            s_o = row.get("_ec_score", 0) * 0.6 + row.get("الثقة", 0) * 0.4
        if row.get("🚦 Flip") == "✅":
            fc = row.get("Flip Conf%", 0)
            fc = fc if isinstance(fc, (int, float)) else 0
            s_f = row.get("_flip_ec_score", 0) * 0.6 + fc * 0.4
        return max(s_o, s_f)

    strong["_final_score"] = strong.apply(calc_score, axis=1)
    best = strong.sort_values("_final_score", ascending=False).iloc[0]
    pair = best["الزوج"]
    sym = PAIRS.get(pair)
    if not sym:
        return {"status": "NONE"}
    price, _ = get_spot_price(sym)
    data = get_historical_data(sym, "3mo", "4h")
    if price is None or data is None:
        return {"status": "NONE"}
    try:
        result = generate_signal(data, price, pair, sym, skip_external_filters=False)
    except Exception:
        return {"status": "NONE"}
    return {"status": "FOUND", "row": best.to_dict(), "result": result,
            "pair": pair, "price": price, "sym": sym}


@st.cache_data(ttl=300, show_spinner=False)
def get_fmp_economic_calendar():
    api_key = get_secret("FMP_API_KEY")
    if not api_key: return []
    try:
        r = requests.get("https://financialmodelingprep.com/api/v3/economic_calendar",
            params={"from": datetime.now().strftime("%Y-%m-%d"),
                    "to": (datetime.now()+timedelta(days=7)).strftime("%Y-%m-%d"),
                    "apikey": api_key}, timeout=10)
        d = r.json()
        return d if isinstance(d, list) else []
    except Exception: return []

def event_risk_message(events, pair_name):
    if not events: return "لا توجد بيانات تقويم"
    b, m = news_time_block(events, pair_name)
    if b: return f"⚠️ {m}"
    return "لا يوجد قفل خبر مطابق"


# ============================================================
# RENDER HELPERS
# ============================================================

def render_signal_card(title, direction, confidence, grade, verdict_text,
                       verdict_color, subtitle="", accent_color=None):
    if accent_color is None:
        accent_color = ("#7cd4a0" if direction == "BUY"
                        else "#f57a7a" if direction == "SELL" else "#f5c87a")
    st.markdown(f"""
    <div style="background:linear-gradient(145deg, #10141c, #0d1017);
                padding:26px 22px; border-radius:22px; text-align:center;
                border:2px solid {accent_color};
                box-shadow:0 0 28px {accent_color}44, 0 16px 40px rgba(0,0,0,0.6);">
        <div style="color:#7d879c; font-size:0.82rem; font-weight:500;
                    letter-spacing:1px;">{title}</div>
        <div style="font-size:3rem; font-weight:800; color:{accent_color};
                    letter-spacing:3px; margin:10px 0; line-height:1;">
            {direction}
        </div>
        <div style="color:#c8d2e2; font-size:1.05rem;">
            Confidence: <b>{confidence:.1f}%</b>
        </div>
        <div style="font-size:1.1rem; font-weight:800;
                    color:{accent_color}; letter-spacing:1.5px; margin-top:8px;">
            Grade: {grade}
        </div>
        <div style="background:{verdict_color}22; padding:8px 16px;
                    border-radius:10px; margin-top:12px;
                    border:1px solid {verdict_color}66;
                    display:inline-block;">
            <span style="color:{verdict_color}; font-weight:700; font-size:0.9rem;">
                {verdict_text}
            </span>
        </div>
        <div style="color:#6b7488; font-size:0.72rem; margin-top:10px;">
            {subtitle}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_entry_checks(ec, prefix=""):
    if not ec: return
    score = ec["score"]; color = ec["verdict_color"]; text = ec["verdict_text"]
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03); padding:8px 16px;
                border-radius:10px; margin-bottom:12px;
                border-left:3px solid {color};">
        <span style="color:#7d879c; font-size:0.82rem;">
            {prefix}Score: <b style="color:{color};">{score}/100</b>
            &nbsp;·&nbsp; <b style="color:{color};">{text}</b>
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.05); border-radius:10px;
                height:10px; overflow:hidden; margin-bottom:14px;">
        <div style="width:{score}%; height:100%;
                    background:linear-gradient(90deg, {color}88, {color});
                    border-radius:10px;"></div>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(5)
    for i, ch in enumerate(ec["checks"]):
        with cols[i % 5]:
            pc = "#7cd4a0" if ch["pass"] else "#f57a7a"
            pi = "✅" if ch["pass"] else "❌"
            st.markdown(f"""
            <div style="background:linear-gradient(145deg, #10141c, #0d1017);
                        padding:9px 10px; border-radius:10px;
                        border:1px solid {pc}44; text-align:center;
                        margin-bottom:8px;">
                <div style="font-size:1.1rem;">{ch['icon']}</div>
                <div style="color:#e8edf5; font-size:0.68rem; font-weight:600;
                            margin-top:4px; line-height:1.15;">{ch['name']}</div>
                <div style="color:{pc}; font-size:0.75rem; font-weight:700;
                            margin-top:3px;">{pi} {ch['score']}</div>
            </div>
            """, unsafe_allow_html=True)


def render_trade_plan(levels, pair_name, title="Trade Plan", accent="#e6c87c",
                      dimmed=False):
    if not levels: return
    src = levels.get("sources", {})
    if dimmed:
        st.warning("🔒 **البوابة فشلت — الـ Trade Plan ده للمرجعية فقط.** "
                   "لا تُتداول به حتى يعبر البوابة.")
    st.markdown(f'<div class="section-title" style="color:{accent};">{title} '
                f'<span>Static SL · RR validated</span></div>',
                unsafe_allow_html=True)
    l1, l2, l3, l4, l5 = st.columns(5)
    l1.metric("Entry", fmt_price(levels["entry"], pair_name))
    l2.metric("Stop Loss", fmt_price(levels["stop_loss"], pair_name),
              help=src.get("sl",""))
    l3.metric("TP1", fmt_price(levels["target1"], pair_name),
              help=src.get("tp1",""))
    l4.metric("TP2", fmt_price(levels["target2"], pair_name),
              help=src.get("tp2",""))
    l5.metric("TP3", fmt_price(levels["target3"], pair_name),
              help=src.get("tp3",""))
    rr1, rr2, rr3, _ = st.columns([1,1,1,2])
    rr1.metric("RR·TP1", f"1:{levels['risk_reward_1']:.2f}")
    rr2.metric("RR·TP2", f"1:{levels['risk_reward_2']:.2f}")
    rr3.metric("RR·TP3", f"1:{levels['risk_reward_3']:.2f}")
    st.markdown(f"""<div style="margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;">
        <span style="background:rgba(245,122,122,0.15); padding:5px 12px;
                     border-radius:18px; color:#f57a7a; font-size:0.8rem;
                     border:1px solid rgba(245,122,122,0.35); font-weight:600;">
            🛑 SL: {src.get('sl','—')}</span>
        <span style="background:rgba(230,200,124,0.15); padding:5px 12px;
                     border-radius:18px; color:#e6c87c; font-size:0.8rem;
                     border:1px solid rgba(230,200,124,0.35);">
            🎯 TP1: {src.get('tp1','—')}</span>
        <span style="background:rgba(124,212,160,0.12); padding:5px 12px;
                     border-radius:18px; color:#7cd4a0; font-size:0.8rem;
                     border:1px solid rgba(124,212,160,0.35);">
            🎯 TP2: {src.get('tp2','—')}</span>
        <span style="background:rgba(124,212,160,0.12); padding:5px 12px;
                     border-radius:18px; color:#7cd4a0; font-size:0.8rem;
                     border:1px solid rgba(124,212,160,0.35);">
            🎯 TP3: {src.get('tp3','—')}</span>
    </div>""", unsafe_allow_html=True)


# ============================================================
# UI
# ============================================================

st.set_page_config(page_title=f"BLACK PYRAMID {APP_VERSION}",
                   page_icon="▲", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter','Segoe UI',Tahoma,sans-serif; }
body { background: #0a0d13; color: #e8edf5; }
.main-header, .main-title, .main-subtitle,
.signal-card, .signal-meta, .signal-conf, .signal-grade,
.metric-card, .metric-label, .metric-value, .metric-sub,
.tool-card, .tool-name, .tool-value, .tool-desc,
.section-title, .footer-style,
div[data-testid="stMetric"] label, div[data-testid="stMetric"] .stMetricValue,
div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] td { direction: rtl; }
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"],
button[kind="header"] { position: fixed !important; left: 12px !important;
    right: auto !important; top: 14px !important; z-index: 999999 !important;
    background: rgba(230,200,124,0.08) !important;
    border: 1px solid rgba(230,200,124,0.25) !important;
    border-radius: 50% !important; width: 40px !important; height: 40px !important;
    display: flex !important; align-items: center !important;
    justify-content: center !important; transition: all 0.25s ease !important; }
[data-testid="collapsedControl"]:hover, [data-testid="stSidebarCollapsedControl"]:hover,
button[kind="header"]:hover { background: rgba(230,200,124,0.2) !important;
    border-color: rgba(230,200,124,0.6) !important; transform: scale(1.05) !important; }
[data-testid="stSidebar"] { direction: rtl; }
[data-testid="stSidebar"] > div:first-child { direction: rtl; }
.hero { background: radial-gradient(circle at 20% 30%, rgba(230,200,124,0.08), transparent 60%),
    radial-gradient(circle at 80% 70%, rgba(124,212,160,0.06), transparent 60%),
    linear-gradient(145deg, #10141c, #0d1017);
    padding: 18px 26px; border-radius: 20px;
    border: 1px solid rgba(230,200,124,0.12);
    box-shadow: 0 12px 30px rgba(0,0,0,0.55);
    position: relative; overflow: hidden; }
.hero::before { content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background: linear-gradient(90deg, transparent, #e6c87c, #7cd4a0, #e6c87c, transparent); }
.hero-title { font-size: 2rem; font-weight: 800; color: #e6c87c;
    letter-spacing: 3px; margin: 0; line-height: 1.1;
    text-shadow: 0 0 30px rgba(230,200,124,0.35); }
.hero-sub { color: #8b95a8; margin-top: 8px; font-size: 0.82rem;
    font-weight: 300; letter-spacing: 0.3px; line-height: 1.4; }
.hero-badge { display: inline-block; padding: 3px 12px; border-radius: 40px;
    background: rgba(230,200,124,0.1); color: #e6c87c; font-size: 0.7rem;
    font-weight: 600; border: 1px solid rgba(230,200,124,0.25);
    margin-left: 6px; letter-spacing: 1px; }
.hero-badge-gate { display: inline-block; padding: 3px 12px;
    border-radius: 40px; background: rgba(124,212,160,0.15); color: #7cd4a0;
    font-size: 0.7rem; font-weight: 700;
    border: 1px solid rgba(124,212,160,0.5);
    margin-left: 6px; letter-spacing: 1.5px; }
.hero-badge-mode { display: inline-block; padding: 3px 12px;
    border-radius: 40px; background: rgba(230,200,124,0.2); color: #e6c87c;
    font-size: 0.7rem; font-weight: 700;
    border: 1px solid rgba(230,200,124,0.6);
    margin-left: 6px; letter-spacing: 1.5px; text-transform: uppercase; }
.section-title { font-size: 1.4rem; font-weight: 700; color: #e6c87c;
    margin: 32px 0 18px 0; padding-bottom: 12px;
    border-bottom: 1px solid rgba(230,200,124,0.15); }
.section-title span { color: #6b7488; font-size: 0.85rem; font-weight: 400; }
.tool-card { background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 20px; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 6px 16px rgba(0,0,0,0.35);
    transition: all 0.25s ease; height: 100%; }
.tool-card:hover { border-color: rgba(230,200,124,0.3); transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(0,0,0,0.5); }
.tool-name { color: #e6c87c; font-size: 0.85rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase; margin-bottom: 10px; }
.tool-value { color: #e8edf5; font-size: 1.3rem; font-weight: 700; }
.tool-desc { color: #8892a5; font-size: 0.82rem; margin-top: 8px; line-height: 1.5; }
div.stButton > button { background: linear-gradient(145deg, #1a2130, #131821);
    color: #e8edf5; border: 1px solid rgba(230,200,124,0.2);
    border-radius: 40px; padding: 0.7rem 1.8rem; font-weight: 500;
    letter-spacing: 0.3px; transition: all 0.25s ease;
    box-shadow: 0 6px 16px rgba(0,0,0,0.4); width: 100%; }
div.stButton > button:hover { background: linear-gradient(145deg, #263049, #1a2233);
    border-color: rgba(230,200,124,0.55); color: #fff;
    transform: translateY(-1px); box-shadow: 0 10px 24px rgba(0,0,0,0.6); }
div[data-testid="stMetric"] { background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 16px 18px; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stMetric"] label { color: #7d879c !important;
    font-size: 0.78rem !important; text-transform: uppercase;
    letter-spacing: 1px; font-weight: 600; }
div[data-testid="stMetric"] .stMetricValue { color: #e8edf5 !important;
    font-weight: 700 !important; }
div[data-testid="stTextInput"] > label { color: #e6c87c !important;
    font-weight: 600 !important; font-size: 0.85rem !important;
    letter-spacing: 0.5px; }
div[data-testid="stTextInput"] > div > div > input {
    background: linear-gradient(145deg, #10141c, #0d1017) !important;
    border: 1px solid rgba(230,200,124,0.25) !important;
    border-radius: 12px !important; color: #e8edf5 !important;
    padding: 10px 14px !important; }
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: rgba(230,200,124,0.55) !important;
    box-shadow: 0 0 0 2px rgba(230,200,124,0.15) !important; }
hr { border: none; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(230,200,124,0.15), transparent);
    margin: 30px 0; }
.footer-style { text-align: center; color: #4a5266; padding: 40px 0 20px;
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: 40px; font-size: 0.85rem; letter-spacing: 0.5px; }
details { background: #0d1017 !important; border-radius: 16px !important;
    border: 1px solid rgba(255,255,255,0.05) !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════
_logo = load_logo_b64()
hl, hr = st.columns([1.15, 1.6])
with hl:
    if _logo:
        st.markdown(f"""
        <div class="hero">
            <img src="data:image/png;base64,{_logo}" alt="BP"
                 style="width: 190px; max-width: 100%; height: auto;
                        display: block; filter: drop-shadow(0 6px 20px rgba(230,200,124,0.3));">
            <div class="hero-sub" style="margin-top: 8px;">
                Institutional Analysis Terminal
                <span class="hero-badge">{APP_VERSION}</span>
                <span class="hero-badge-mode">{MODE.upper()}</span>
                <span class="hero-badge-gate">GATE ≥ {MIN_EMIT_CONFIDENCE:.0f}%</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="hero">
            <div class="hero-title">▲ BLACK PYRAMID</div>
            <div class="hero-sub" style="margin-top: 8px;">
                Institutional Analysis Terminal
                <span class="hero-badge">{APP_VERSION}</span>
                <span class="hero-badge-mode">{MODE.upper()}</span>
                <span class="hero-badge-gate">GATE ≥ {MIN_EMIT_CONFIDENCE:.0f}%</span>
            </div>
        </div>""", unsafe_allow_html=True)

with hr:
    st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
    br = st.columns([1, 1])
    with br[0]:
        if st.button("🔄 تحديث", width="stretch", key="btn_ref"):
            st.session_state.economic_events = get_fmp_economic_calendar()
            st.cache_data.clear()
            st.toast("✅ تم التحديث")
    with br[1]:
        if st.button("🎯 أعثر على صفقة قوية", width="stretch", key="btn_strong"):
            with st.spinner("🔍 جاري البحث عن أقوى صفقة..."):
                st.session_state.strong_trade_result = find_strongest_trade()
            st.rerun()


# ═══════════════════════════════════════════════
# API KEYS SECTION
# ═══════════════════════════════════════════════
st.markdown('<div class="section-title">🔑 مفاتيح المصادر <span>API Keys · Data Sources</span></div>',
            unsafe_allow_html=True)
st.caption("أدخل مفاتيح API لجلب البيانات من مصادر إضافية. "
           "يتم الحفظ في الجلسة الحالية فقط (Session).")

# Initialize widget state from env/secrets on first load
if "_td_api_input" not in st.session_state:
    st.session_state._td_api_input = get_secret("TWELVE_API_KEY", "")
if "_fmp_api_input" not in st.session_state:
    st.session_state._fmp_api_input = get_secret("FMP_API_KEY", "")

kc1, kc2 = st.columns(2)
with kc1:
    td_val = st.text_input(
        "TwelveData API Key",
        type="password",
        key="_td_api_input",
        placeholder="مفتاح TwelveData للأسعار",
        help="بديل مجاني: yfinance (مدمج). TwelveData يعطي دقة أعلى للفوركس.")
    _td_status = "✅ نشط" if td_val else "⚪ غير مفعّل (يستخدم yfinance)"
    st.caption(f"الحالة: {_td_status}")

with kc2:
    fmp_val = st.text_input(
        "FMP API Key",
        type="password",
        key="_fmp_api_input",
        placeholder="مفتاح Financial Modeling Prep للتقويم",
        help="مطلوب فقط لجلب التقويم الاقتصادي.")
    _fmp_status = "✅ نشط" if fmp_val else "⚪ غير مفعّل"
    st.caption(f"الحالة: {_fmp_status}")

# Sync to session_state and clear cache if changed
_changed = False
if td_val != st.session_state.get("TWELVE_API_KEY", ""):
    st.session_state.TWELVE_API_KEY = td_val
    _changed = True
if fmp_val != st.session_state.get("FMP_API_KEY", ""):
    st.session_state.FMP_API_KEY = fmp_val
    _changed = True
if _changed:
    st.cache_data.clear()


# ═══════════════════════════════════════════════
# STRONGEST TRADE DISPLAY (Simplified)
# ═══════════════════════════════════════════════
_str_res = st.session_state.get("strong_trade_result")
if _str_res:
    if _str_res.get("status") == "NONE":
        st.markdown('<div class="section-title">🏆 أقوى صفقة</div>',
                    unsafe_allow_html=True)
        st.warning("⏸️ **لا توجد صفقة قوية تمر البوابة الآن.** "
                   f"(تحتاج ≥ {MIN_EMIT_CONFIDENCE:.0f}% ثقة + تأكيد)")
    elif _str_res.get("status") == "FOUND":
        _bp = _str_res["pair"]; _br = _str_res["result"]
        _blv = _br["levels"]; _bsig = _br["signal"]
        _bc = _br["confidence"]; _bprice = _str_res["price"]
        _bacc = "#7cd4a0" if _bsig == "BUY" else "#f57a7a"

        st.markdown(
            f'<div class="section-title" style="color:#7cd4a0;">'
            f'🏆 أقوى صفقة في السوق الآن — {_bp}</div>',
            unsafe_allow_html=True)

        _bs1, _bs2 = st.columns([1.5, 1.2])
        with _bs1:
            st.markdown(f"""
            <div style="background:linear-gradient(145deg, #0a1a12, #0d1710);
                        padding:28px 22px; border-radius:22px; text-align:center;
                        border:2px solid {_bacc};
                        box-shadow:0 0 35px {_bacc}66, 0 16px 40px rgba(0,0,0,0.7);">
                <div style="color:#7cd4a0; font-size:0.9rem; font-weight:800;
                            letter-spacing:2px;">🏆 BEST TRADE FOUND</div>
                <div style="color:#e8edf5; font-size:1.35rem; font-weight:800;
                            margin-top:8px;">{_bp}</div>
                <div style="font-size:3.4rem; font-weight:900; color:{_bacc};
                            letter-spacing:4px; margin:12px 0; line-height:1;">{_bsig}</div>
                <div style="color:#c8d2e2; font-size:1.1rem;">
                    Confidence: <b>{_bc:.1f}%</b></div>
                <div style="color:{_bacc}; font-size:1.15rem; font-weight:800;
                            margin-top:10px; letter-spacing:1.5px;">
                    Grade: {_br['trade_grade']}</div>
            </div>""", unsafe_allow_html=True)
        with _bs2:
            st.metric("💵 السعر", fmt_price(_bprice, _bp))
            if _blv:
                st.metric("🛑 SL", fmt_price(_blv["stop_loss"], _bp),
                          help=_blv.get("sources", {}).get("sl", ""))
                st.metric("🎯 TP1", fmt_price(_blv["target1"], _bp),
                          help=_blv.get("sources", {}).get("tp1", ""))
                st.metric("🎯 TP2", fmt_price(_blv["target2"], _bp),
                          help=_blv.get("sources", {}).get("tp2", ""))
                st.metric("🎯 TP3", fmt_price(_blv["target3"], _bp),
                          help=_blv.get("sources", {}).get("tp3", ""))
else:
    st.markdown('<div class="section-title">🏆 أقوى صفقة</div>',
                unsafe_allow_html=True)
    st.info("🎯 اضغط **'أعثر على صفقة قوية'** أعلاه لبدء البحث في جميع الأزواج "
            f"({len(PAIRS)} زوج). سيتم عرض أفضل إشارة تمر البوابة ≥ {MIN_EMIT_CONFIDENCE:.0f}%.")


# ═══════════════════════════════════════════════
# FOOTER + STOP
# ═══════════════════════════════════════════════
st.markdown(f"""
<div class="footer-style">
    ▲ BLACK PYRAMID {APP_VERSION} ▲<br>
    {MODE.upper()} Mode · Gate ≥ {MIN_EMIT_CONFIDENCE:.0f}% · Strong Trade Finder · Analysis Only
</div>
""", unsafe_allow_html=True)

st.stop()