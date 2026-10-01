# ============================================================
# BLACK PYRAMID v2009.2 — FLIP DETECTION EDITION
# Institutional Analysis Terminal
#
# FEATURES:
#  - SL at Nearest Discovered Level (IDM, OB, FVG, Pivot, Fib, S/R)
#  - Signal Flip Detection (10 indicators)
#  - Flip shown in main signal + All Signals table + Portfolio
#  - ICT Levels + Live Portfolio Monitor
#  - ML (4 models + Hyperparameter Tuning)
#  - Fundamentals + Sentiment + Bond Yields + Monte Carlo
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

APP_VERSION = "v2009.2-FlipDetection"

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

MIN_RR_TP1 = 0.80
MIN_RR_TP2 = 1.30
MIN_RR_TP3 = 1.90

MAX_SOFT_PENALTY = 12.0
SOFT_PENALTY_TOP_N = 4
MAX_CONSECUTIVE_LOSSES = 3

CORRELATION_WINDOW_DAYS = 30
CORRELATION_THRESHOLD = 0.70
CORRELATION_BLOCK_THRESHOLD = 0.85
MAX_SAME_CURRENCY_EXPOSURE = 2

SENTIMENT_EXTREME_LONG = 75
SENTIMENT_EXTREME_SHORT = 25
PIP_VALUE_STANDARD = 10.0

ML_MIN_TRADES = 30
ML_TEST_SIZE = 0.25
ML_FEATURE_SELECTION_THRESHOLD = 0.02
ML_CV_FOLDS = 5

TUNING_MODE = "randomized"
TUNING_N_ITER = 20
TUNING_CV_FOLDS = 5
TUNING_SCORING = "roc_auc"
TUNING_N_JOBS = -1

# SL NEAREST LEVEL CONFIG
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
    try:
        v = st.secrets.get(name, None)
        if v is not None: return str(v)
    except Exception: pass
    return os.getenv(name, default)

TWELVE_API_KEY = get_secret("TWELVE_API_KEY")
FMP_API_KEY = get_secret("FMP_API_KEY")


def init_state():
    defaults = {
        "selected_pair": "XAU/USD (Gold)", "all_signals": None,
        "economic_events": None, "analyzing_all": False, "analysis_time": None,
        "backtest_results": None, "strict_filters": False,
        "show_calendar_today": False, "show_session_info": False,
        "show_market_status": False, "recent_results": [], "trade_journal": [],
        "open_positions": [], "ml_model": None, "_ccy_strength_cache": {}}
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


def check_kill_switch():
    recent = st.session_state.get("recent_results", [])[-MAX_CONSECUTIVE_LOSSES:]
    if len(recent) < MAX_CONSECUTIVE_LOSSES:
        return False, len([r for r in recent if r == "LOSS"])
    if all(r == "LOSS" for r in recent): return True, MAX_CONSECUTIVE_LOSSES
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
    if not TWELVE_API_KEY: return None
    mp = {"GC=F":"XAU/USD","SI=F":"XAG/USD","DX-Y.NYB":"DXY","EURUSD=X":"EUR/USD",
          "GBPUSD=X":"GBP/USD","USDJPY=X":"USD/JPY","USDCHF=X":"USD/CHF",
          "AUDUSD=X":"AUD/USD","NZDUSD=X":"NZD/USD","USDCAD=X":"USD/CAD",
          "BTC-USD":"BTC/USD","ETH-USD":"ETH/USD"}
    td = mp.get(symbol, sanitize_yf_symbol(symbol))
    im = {"15m":"15min","1h":"1h","4h":"4h","1d":"1day"}
    try:
        r = requests.get("https://api.twelvedata.com/time_series",
            params={"symbol": td, "interval": im.get(interval, interval),
                    "outputsize": outputsize, "apikey": TWELVE_API_KEY,
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


# ============================================================
# FUNDAMENTAL LAYER
# ============================================================

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


@st.cache_data(ttl=600, show_spinner=False)
def get_pair_correlation(s1, s2, days=30):
    try:
        d1 = get_historical_data(s1, "3mo", "1d")
        d2 = get_historical_data(s2, "3mo", "1d")
        if d1 is None or d2 is None: return None
        a = pd.concat([d1["close"].pct_change(), d2["close"].pct_change()],
                     axis=1, join="inner").dropna()
        if len(a) < days: return None
        c = float(a.iloc[-days:, 0].corr(a.iloc[-days:, 1]))
        return c if np.isfinite(c) else None
    except Exception: return None

@st.cache_data(ttl=900, show_spinner=False)
def build_correlation_matrix(symbols_tuple):
    syms = list(symbols_tuple); n = len(syms)
    m = np.eye(n)
    for i in range(n):
        for j in range(i+1, n):
            c = get_pair_correlation(syms[i], syms[j])
            if c is not None: m[i,j] = c; m[j,i] = c
    return m, syms

def check_portfolio_conflict(symbol, direction, pair_name, open_positions):
    r = {"blocked": False, "warnings": [], "max_corr": 0.0,
         "conflicting_pair": None, "same_currency_count": 0}
    if not open_positions: return r
    bn, qn = parse_pair_currencies(pair_name)
    for pos in open_positions:
        if pos["symbol"] == symbol: continue
        c = get_pair_correlation(symbol, pos["symbol"])
        if c is None: continue
        ac = abs(c)
        if ac > r["max_corr"]:
            r["max_corr"] = ac; r["conflicting_pair"] = pos["pair"]
        if ac >= CORRELATION_BLOCK_THRESHOLD and pos["direction"] == direction:
            r["blocked"] = True
            r["warnings"].append(f"🚫 ارتباط {ac:.0%} مع {pos['pair']}")
        elif ac >= CORRELATION_THRESHOLD and pos["direction"] == direction:
            r["warnings"].append(f"⚠️ ارتباط {ac:.0%} مع {pos['pair']}")
        if ac >= CORRELATION_THRESHOLD and pos["direction"] != direction:
            r["warnings"].append(f"ℹ️ تحوط مع {pos['pair']}")
    for c in [bn, qn]:
        if not c: continue
        cnt = 0
        for pos in open_positions:
            pb, pq = parse_pair_currencies(pos["pair"])
            if (c == pb or c == pq) and pos["direction"] == direction: cnt += 1
        if cnt >= MAX_SAME_CURRENCY_EXPOSURE:
            r["blocked"] = True
            r["warnings"].append(f"🚫 {cnt} صفقات {direction} على {c}")
        elif cnt == MAX_SAME_CURRENCY_EXPOSURE - 1:
            r["warnings"].append(f"⚠️ {cnt} صفقة على {c}")
        r["same_currency_count"] = max(r["same_currency_count"], cnt)
    return r

def add_open_position(result, pair_name, symbol, lot_size=None, notes=""):
    if result.get("signal") not in ("BUY","SELL"): return False
    if "open_positions" not in st.session_state:
        st.session_state.open_positions = []
    lv = result.get("levels") or {}
    st.session_state.open_positions.append({
        "id": len(st.session_state.open_positions) + 1,
        "pair": pair_name, "symbol": symbol, "direction": result["signal"],
        "entry": lv.get("entry"), "stop_loss": lv.get("stop_loss"),
        "target1": lv.get("target1"), "target2": lv.get("target2"),
        "target3": lv.get("target3"),
        "grade": result.get("trade_grade", "?"),
        "confidence": result.get("confidence", 0),
        "lot_size": lot_size,
        "opened_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "notes": notes, "status": "OPEN"})
    return True

def close_open_position(pid):
    if "open_positions" not in st.session_state: return False
    st.session_state.open_positions = [
        p for p in st.session_state.open_positions if p["id"] != pid]
    return True

def get_portfolio_exposure():
    exp = {}
    for pos in st.session_state.get("open_positions", []):
        b, q = parse_pair_currencies(pos["pair"])
        d = pos["direction"]; sz = pos.get("lot_size") or 1.0
        for c in [b, q]:
            if c and c not in exp:
                exp[c] = {"long": 0.0, "short": 0.0, "net": 0.0, "count": 0}
        if b and q:
            if d == "BUY":
                exp[b]["long"] += sz; exp[q]["short"] += sz
                exp[b]["net"] += sz; exp[q]["net"] -= sz
            else:
                exp[b]["short"] += sz; exp[q]["long"] += sz
                exp[b]["net"] -= sz; exp[q]["net"] += sz
            exp[b]["count"] += 1; exp[q]["count"] += 1
    return exp

def calculate_pnl_for_position(pos):
    try:
        cur, _ = get_spot_price(pos["symbol"])
        if cur is None: return None
        e = pos.get("entry")
        if e is None or e <= 0: return None
        d = pos["direction"]; sz = pos.get("lot_size") or 1.0
        pts = (cur - e) if d == "BUY" else (e - cur)
        asset = asset_type_from_name(pos["pair"])
        if asset == "forex":
            if "JPY" in pos["pair"].upper(): usd = pts * sz * 1000 / cur
            else: usd = pts * sz * 100000 / e
        elif asset == "gold": usd = pts * sz * 100
        elif asset == "crypto": usd = pts * sz
        else: usd = pts * sz
        sl = pos.get("stop_loss")
        r = 0.0
        if sl is not None and sl != e:
            ru = abs(e - sl)
            if ru > 0: r = pts / ru
        tp1 = pos.get("target1"); prog = 0.0
        if tp1 is not None and tp1 != e:
            tot = abs(tp1 - e)
            if tot > 0: prog = min(abs(pts) / tot * 100, 200)
        return {"current_price": cur, "pnl_points": pts, "pnl_usd": usd,
                "r_multiple": r, "progress_to_tp1": prog,
                "status": ("🟢 WIN" if r > 0.1 else "🔴 LOSS" if r < -0.1 else "⚪ BE")}
    except Exception: return None

def calculate_portfolio_pnl():
    ops = st.session_state.get("open_positions", [])
    t = 0.0; tr = 0.0; w = 0; l = 0; n = 0; det = []
    for pos in ops:
        p = calculate_pnl_for_position(pos)
        if p is None: continue
        det.append({"pos": pos, "pnl": p})
        t += p["pnl_usd"]; tr += p["r_multiple"]; n += 1
        if p["r_multiple"] > 0.05: w += 1
        elif p["r_multiple"] < -0.05: l += 1
    return {"total_positions": n, "total_pnl_usd": t, "total_r": tr,
            "winners": w, "losers": l, "win_rate": (w/n*100) if n > 0 else 0,
            "detailed": det}


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
    if not np.isfinite(atr) or atr <= 0: return "UNKNOWN", 50.0
    ts = abs(l["ema20"] - l["ema50"]) / atr
    bw = (l["bb_upper"] - l["bb_lower"]) / max(l["close"], 1e-12)
    if ts >= 1.0:
        return ("TREND_BULLISH" if l["ema20"] > l["ema50"] else "TREND_BEARISH"), 75
    if bw < 0.015: return "COMPRESSION", 65
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
    w = [1.0, 0.5, 0.25, 0.15]
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
    if bool(l["bos_bullish"]): sc["BUY"]["structure"] += 35; rs.append("BOS صاعد")
    if bool(l["bos_bearish"]): sc["SELL"]["structure"] += 35; rs.append("BOS هابط")
    if bool(l["mss_bullish"]): sc["BUY"]["structure"] += 20; rs.append("MSS صاعد")
    if bool(l["mss_bearish"]): sc["SELL"]["structure"] += 20; rs.append("MSS هابط")
    if bool(l["liquidity_sweep_bullish"]): sc["BUY"]["structure"] += 25
    if bool(l["liquidity_sweep_bearish"]): sc["SELL"]["structure"] += 25
    if bool(l["order_block_bullish"]): sc["BUY"]["structure"] += 15
    if bool(l["order_block_bearish"]): sc["SELL"]["structure"] += 15
    if bool(l["fvg_bullish"]): sc["BUY"]["structure"] += 10
    if bool(l["fvg_bearish"]): sc["SELL"]["structure"] += 10
    if bool(l["in_discount"]): sc["BUY"]["structure"] += 10
    if bool(l["in_premium"]): sc["SELL"]["structure"] += 10
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
    elif regime == "RANGE": sc += 8; rs.append("Range")
    elif regime == "COMPRESSION": sc += 5; rs.append("Compression")
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
    th = profile.get("confirmation_threshold", 65)
    ok = sc >= th and not hard and len(bl) <= 2
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


def calc_position_size(balance, risk_pct, entry, stop_loss, pair_name):
    if balance <= 0 or risk_pct <= 0: return None
    ra = balance * (risk_pct/100); sd = abs(entry - stop_loss)
    if sd <= 0: return None
    a = asset_type_from_name(pair_name)
    if a == "forex":
        if "JPY" in pair_name.upper(): p = 0.01; sp = sd/p; pvpl = 1000/entry
        else: p = 0.0001; sp = sd/p; pvpl = 10.0
        lots = ra/(sp*pvpl) if sp > 0 else 0
        return {"asset": a, "risk_amount": round(ra, 2),
                "sl_distance": round(sd, 5), "sl_pips": round(sp, 1),
                "lots": round(lots, 2), "units": int(lots*100000),
                "unit_label": "lots"}
    if a == "gold":
        sp = sd/0.1; pvpl = 10.0
        lots = ra/(sp*pvpl) if sp > 0 else 0
        return {"asset": a, "risk_amount": round(ra, 2),
                "sl_distance": round(sd, 2), "sl_pips": round(sp, 1),
                "lots": round(lots, 2), "ounces": round(lots*100, 2),
                "unit_label": "lots (100 oz)"}
    if a == "crypto":
        u = ra/sd if sd > 0 else 0
        return {"asset": a, "risk_amount": round(ra, 2),
                "sl_distance": round(sd, 2), "units": round(u, 6),
                "unit_label": "units"}
    return None

def build_trade_management(signal, levels, profile):
    if not levels: return None
    e = levels["entry"]; at = profile.get("atr_trail", 1.1)
    return [{"stage": "TP1", "action": "إغلاق 40%",
             "details": f"نقل SL للتعادل ({fmt_price(e,'')})", "icon": "🎯"},
            {"stage": "TP2", "action": "إغلاق 30%",
             "details": f"Trailing = {at}× ATR", "icon": "🎯"},
            {"stage": "TP3", "action": "إغلاق 30% النهائي",
             "details": "إغلاق كامل + تسجيل", "icon": "🏁"}]


# ============================================================
# SIGNAL FLIP DETECTION
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
    if total_score < 25 or len(triggers) == 0:
        return {"flip_signal": None, "confidence": total_score,
                "triggers": triggers, "status": "NO_FLIP",
                "message": "الإشارة الأصلية سارية", "new_levels": None}

    if total_score >= 70:
        status = "STRONG_FLIP"
        msg = f"🚨 إشارة قوية للانعكاس إلى {flip_signal}"
    elif total_score >= 45:
        status = "POSSIBLE_FLIP"
        msg = f"⚠️ احتمال انعكاس إلى {flip_signal}"
    else:
        status = "WEAK_FLIP"
        msg = f"💡 مؤشرات أولية نحو {flip_signal}"

    new_levels = None
    try:
        new_levels = calculate_ict_sl_tp(df, flip_signal, current_price, profile)
    except Exception: pass

    return {"flip_signal": flip_signal, "confidence": total_score,
            "triggers": triggers, "status": status,
            "message": msg, "new_levels": new_levels}


# ============================================================
# DYNAMIC POSITION MONITOR
# ============================================================

def monitor_position(pos):
    dfx = get_historical_data(pos["symbol"], "3mo", "4h")
    if dfx is None or len(dfx) < 50:
        return {"state": "NO_DATA", "action": "بيانات قليلة", "severity": 0,
                "reversal_signals": [], "suggested_sl": pos.get("stop_loss"),
                "flip_info": None}
    profile = profile_for(pos["pair"])
    dfx = build_features(dfx, profile)
    last = dfx.iloc[-1]
    cur, _ = get_spot_price(pos["symbol"])
    if cur is None:
        return {"state": "NO_PRICE", "action": "انتظر", "severity": 0,
                "reversal_signals": [], "suggested_sl": pos.get("stop_loss"),
                "flip_info": None}
    d = pos["direction"]
    e = pos.get("entry", cur); sl = pos.get("stop_loss", e)
    tp1 = pos.get("target1", e); tp2 = pos.get("target2", e); tp3 = pos.get("target3", e)
    if d == "BUY":
        pnl_pts = cur - e
        h1 = cur >= tp1; h2 = cur >= tp2; h3 = cur >= tp3; hs = cur <= sl
    else:
        pnl_pts = e - cur
        h1 = cur <= tp1; h2 = cur <= tp2; h3 = cur <= tp3; hs = cur >= sl
    rk = abs(e - sl); r = pnl_pts / rk if rk > 0 else 0
    if d == "SELL": r = -r
    sigs = []; sev = 0
    if d == "BUY" and safe_bool(last.get("mss_bearish")):
        sigs.append("MSS هابط"); sev += 30
    if d == "SELL" and safe_bool(last.get("mss_bullish")):
        sigs.append("MSS صاعد"); sev += 30
    st_ = structure_state(dfx)
    if d == "BUY" and st_["bearish"]:
        sigs.append("الهيكل انقلب"); sev += 40
    if d == "SELL" and st_["bullish"]:
        sigs.append("الهيكل انقلب"); sev += 40
    if d == "BUY" and last["macd"] < last["macd_signal"] and last["macd_histogram"] < 0:
        sigs.append("MACD انقلب"); sev += 20
    if d == "SELL" and last["macd"] > last["macd_signal"] and last["macd_histogram"] > 0:
        sigs.append("MACD انقلب"); sev += 20
    dv = detect_divergence(dfx)
    if d == "BUY" and dv == "BEARISH":
        sigs.append("Divergence هبوطي"); sev += 25
    if d == "SELL" and dv == "BULLISH":
        sigs.append("Divergence صعودي"); sev += 25
    vw = safe_float(last.get("vwap"), cur)
    if d == "BUY" and cur < vw * 0.998: sigs.append("كسر VWAP"); sev += 15
    if d == "SELL" and cur > vw * 1.002: sigs.append("كسر VWAP"); sev += 15
    if d == "BUY" and last["ema20"] < last["ema50"]: sigs.append("EMA20<50"); sev += 20
    if d == "SELL" and last["ema20"] > last["ema50"]: sigs.append("EMA20>50"); sev += 20

    # FLIP DETECTION
    flip_info = None
    try:
        flip_res = detect_signal_flip(dfx, cur, d, profile)
        if flip_res and flip_res.get("flip_signal"):
            flip_info = flip_res
            if flip_res["status"] == "STRONG_FLIP":
                sev = max(sev, 80)
            elif flip_res["status"] == "POSSIBLE_FLIP":
                sev = max(sev, 55)
    except Exception: pass

    if hs: state = "STOPPED"; action = "تم الإيقاف"; sev = 100
    elif h3: state = "TARGET_HIT"; action = "🎯 TP3 — أغلق"; sev = 5
    elif sev >= 80 and flip_info and flip_info["status"] == "STRONG_FLIP":
        state = "FLIP_ALERT"
        action = f"🔀 انعكاس إلى {flip_info['flip_signal']} ({flip_info['confidence']:.0f}%)"
    elif sev >= 60:
        state = "EXIT_NOW"
        action = f"🛑 خروج فوري — {', '.join(sigs[:3])}"; sev = 90
    elif sev >= 40:
        state = "TREND_CHANGE"
        action = f"⚠️ تغير هيكل — شدد SL"; sev = 70
    elif flip_info and flip_info["status"] == "POSSIBLE_FLIP":
        state = "FLIP_WARNING"
        action = f"⚠️ احتمال انعكاس ({flip_info['confidence']:.0f}%)"
    elif sev >= 25:
        state = "REVERSAL_WARNING"
        action = f"⚡ انعكاس محتمل: {', '.join(sigs[:2])}"; sev = 50
    elif h2: state = "SCALE_OUT_2"; action = "✅ TP2 — اخرج 30% + Trailing"; sev = 10
    elif h1: state = "SCALE_OUT_1"; action = "✅ TP1 — اخرج 40% + SL BE"; sev = 15
    elif r > 0.7: state = "SL_TO_BE"; action = "💡 قرب TP1 — جهّز نقل SL"; sev = 20
    else: state = "ACTIVE"; action = "✅ استمر"; sev = 0
    suggested = _suggest_sl(pos, dfx, cur, d) if state not in ("STOPPED", "TARGET_HIT") else sl
    return {"state": state, "action": action, "severity": sev,
            "reversal_signals": sigs, "current_price": cur,
            "r_multiple": r, "hit_tp1": h1, "hit_tp2": h2, "hit_tp3": h3,
            "hit_sl": hs, "suggested_sl": suggested,
            "flip_info": flip_info}


def _suggest_sl(pos, dfx, cur, direction):
    last = dfx.iloc[-1]
    atr = safe_float(last.get("atr"), 0)
    if atr <= 0: return pos.get("stop_loss", cur)
    e = pos.get("entry", cur); csl = pos.get("stop_loss", e)
    tp1 = pos.get("target1")
    if tp1:
        if direction == "BUY" and cur >= tp1: return max(e, csl)
        if direction == "SELL" and cur <= tp1: return min(e, csl)
    sw = get_last_two_swings(dfx, "low" if direction == "BUY" else "high")
    if sw:
        lsw = sw[-1][1]
        if direction == "BUY" and lsw > csl and lsw < cur: return lsw - 0.3 * atr
        if direction == "SELL" and lsw < csl and lsw > cur: return lsw + 0.3 * atr
    return csl


def update_position_sl(pos_id, new_sl):
    for p in st.session_state.get("open_positions", []):
        if p["id"] == pos_id:
            p["stop_loss"] = new_sl; return True
    return False

def close_position_with_result(pos_id, outcome):
    pos = None
    for p in st.session_state.get("open_positions", []):
        if p["id"] == pos_id: pos = p; break
    if pos is None: return False
    st.session_state.recent_results.append(outcome)
    st.session_state.recent_results = st.session_state.recent_results[-20:]
    st.session_state.trade_journal.append({
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "pair": pos["pair"], "direction": pos["direction"],
        "grade": pos.get("grade", "?"), "confidence": pos.get("confidence", 0),
        "outcome": outcome})
    close_open_position(pos_id)
    return True

def state_color_severity(sev):
    if sev >= 80: return "#f57a7a", "🔴"
    if sev >= 50: return "#f5c87a", "🟡"
    if sev >= 20: return "#7cd4a0", "🟢"
    return "#7cd4a0", "✅"


# ============================================================
# SIGNAL ENGINE
# ============================================================

def generate_signal(df, current_price, pair_name, symbol,
                    news_block=False, skip_external_filters=False,
                    precomputed=None, strict_soft=False):
    profile = profile_for(pair_name); profile_key = get_asset_profile(pair_name)
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
    cand_dir = "BUY" if sc["buy"] > sc["sell"] else "SELL"
    sb, smsg = get_sentiment_bias_for_signal(sent, cand_dir)
    if sb > 0:
        if cand_dir == "BUY": sc["buy"] += sb
        else: sc["sell"] += sb
    elif sb < 0:
        if cand_dir == "BUY": sc["buy"] += sb
        else: sc["sell"] += sb
    buy, sell = sc["buy"], sc["sell"]
    if mtf == "BULLISH": buy += 8; sell -= 4
    elif mtf == "BEARISH": sell += 8; buy -= 4
    if wk == "BULLISH": buy += 5; sell -= 3
    elif wk == "BEARISH": sell += 5; buy -= 3
    buy, sell = clamp(buy, 0, 100), clamp(sell, 0, 100)
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
    if mc and signal in ("BUY","SELL"): sp.append(("MSS Conflict", 10))
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
        so, sm, sl_ = session_filter(pair_name, strict=(profile_key != "crypto"))
        flt["Session"] = {"pass": so, "msg": sm, "label": sl_}
        if not so: sp.append(("Session", 5))
        vo, vm, vl = volatility_regime_filter(df)
        flt["Volatility"] = {"pass": vo, "msg": vm, "label": vl}
        if not vo:
            if vl == "CHAOS": ap = False; br_ = br_ or vm
            else: sp.append(("Volatility", 8))
        ko, km = in_kill_zone(asset_type_from_name(pair_name))
        flt["Kill Zone"] = {"pass": ko, "msg": km}
        if not ko: sp.append(("KZ", 3))
        oo, om = ote_filter(df, cand)
        flt["OTE"] = {"pass": oo, "msg": om}
        if not oo: sp.append(("OTE", 5))
        do, dm = displacement_check(df, cand)
        flt["Displacement"] = {"pass": do, "msg": dm}
        if not do: sp.append(("Disp", 5))
        ntb, ntm = news_time_block(st.session_state.get("economic_events") or [], pair_name)
        flt["News Window"] = {"pass": not ntb, "msg": ntm or "لا خبر"}
        if ntb: ap = False; br_ = br_ or ntm
    mo, mm = is_market_open(pair_name)
    flt["Market Open"] = {"pass": mo, "msg": mm}
    if not mo and not skip_external_filters: ap = False; br_ = br_ or mm
    kb, cons = check_kill_switch()
    if kb and not skip_external_filters:
        flt["Kill Switch"] = {"pass": False, "msg": f"{MAX_CONSECUTIVE_LOSSES} خسائر"}
        ap = False; br_ = br_ or f"Kill Switch ({cons})"
    else:
        flt["Kill Switch"] = {"pass": True, "msg": f"OK ({cons})"}
    cb_ = False; cw_ = []
    if not skip_external_filters and st.session_state.get("open_positions") and signal in ("BUY","SELL"):
        cc = check_portfolio_conflict(symbol, signal, pair_name, st.session_state.open_positions)
        cb_ = cc["blocked"]; cw_ = cc["warnings"]
        if cb_: ap = False; br_ = br_ or "Portfolio Conflict"
        flt["Correlation Guard"] = {"pass": not cb_,
            "msg": f"⚠️ {len(cw_)}" if cw_ else "✅ متوافق"}
    else:
        flt["Correlation Guard"] = {"pass": True, "msg": "لا مراكز"}
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
    if rc >= A_PLUS_MIN and cs >= 78: tg = "A+"
    elif rc >= A_MIN and cs >= 72: tg = "A"
    elif rc >= B_MIN and cs >= 65: tg = "B"
    elif rc >= C_MIN and cs >= 58: tg = "C"
    else: tg = "WAIT"
    if signal == "WAIT": es, er = "WAIT", "Signal WAIT"
    elif not ap: es, er = "BLOCKED", f"Hard Gate: {br_}"
    elif news_block: es, er = "WAIT", "خبر عالي التأثير"
    elif ec < profile.get("confidence_threshold", 72):
        es, er = "WAIT", f"Conf < {profile.get('confidence_threshold', 72)}"
    elif cs < profile.get("confirmation_threshold", 65):
        es, er = "WAIT", f"Confirm < {profile.get('confirmation_threshold', 65)}"
    elif tg in ("A+","A"): es, er = "EXECUTE", f"{tg} PASS"
    elif tg == "B": es, er = "EXECUTE", "B PASS"
    elif tg == "C": es, er = "WATCH", "C مراقبة"
    else: es, er = "WAIT", "لا اجتياز"
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
            "corr_blocked": cb_, "corr_warnings": cw_,
            "ml_probability": mlprob, "ml_status": mlstat,
            "rate_diff": rd, "pair_name": pair_name}


# ============================================================
# BACKTEST
# ============================================================

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
        if len(w) < 20: return "NEUTRAL"
        b, _ = _bias_from_slice(w, pair_name); return b
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
        df = build_features(dff, prof)
        w = 0; l = 0; tr = 0.0; eq = 0.0; pk = 0.0; mdd = 0.0
        tlog = []; mlt = []
        si = 100; ei = len(df) - 20
        for i in range(si, ei):
            sl_df = df.iloc[:i].copy()
            price = float(df["close"].iloc[i])
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
            fut = df.iloc[i+1:i+21]
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
            d = get_historical_data(sym, "3mo", "4h")
            if p is None or d is None: return None
            r = generate_signal(d, p, pn, sym, skip_external_filters=True)
            lv = r["levels"] or {}
            flip_sig = "—"; flip_conf = 0; flip_status = "NONE"; flip_icon = ""
            sig_ = r["signal"]
            if sig_ in ("BUY", "SELL"):
                try:
                    df_feat = r.get("df")
                    if df_feat is not None and len(df_feat) >= 50:
                        fl = detect_signal_flip(df_feat, p, sig_, profile_for(pn))
                        if fl and fl.get("flip_signal"):
                            flip_sig = fl["flip_signal"]
                            flip_conf = round(fl["confidence"], 0)
                            flip_status = fl["status"]
                            if fl["status"] == "STRONG_FLIP": flip_icon = "🚨"
                            elif fl["status"] == "POSSIBLE_FLIP": flip_icon = "⚠️"
                            else: flip_icon = "💡"
                except Exception: pass
            return {"الزوج": pn, "الإشارة": sig_,
                    "الثقة": round(r["confidence"], 1),
                    "🔄 Flip": f"{flip_icon} {flip_sig}" if flip_sig != "—" else "—",
                    "Flip%": flip_conf if flip_conf > 0 else "—",
                    "BUY": round(r["buy_score"], 1),
                    "SELL": round(r["sell_score"], 1),
                    "MTF": r["mtf_bias"], "Weekly": r["weekly_bias"],
                    "Regime": r["regime"],
                    "Fund": f"B{r.get('fund_buy',0):.0f}/S{r.get('fund_sell',0):.0f}",
                    "Conf": round(r["weighted_confluence"], 0),
                    "Confirm": round(r["confirmation_score"], 1),
                    "Grade": r.get("trade_grade","WAIT"),
                    "Execution": r["execution_status"],
                    "السعر": fmt_price(p, pn),
                    "SL": fmt_price(lv.get("stop_loss"), pn),
                    "SLsrc": lv.get("sources", {}).get("sl", "—"),
                    "TP1": fmt_price(lv.get("target1"), pn),
                    "RR3": round(lv.get("risk_reward_3", 0), 2) if lv else 0,
                    "_flip_status": flip_status}
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
        status = row.get("_flip_status", "NONE")
        sig = row["الإشارة"]
        fp = {"STRONG_FLIP": 0, "POSSIBLE_FLIP": 1, "WEAK_FLIP": 2, "NONE": 3}.get(status, 3)
        sp_ = {"BUY": 0, "SELL": 1, "WAIT": 2}.get(sig, 3)
        return (fp, sp_, -float(row.get("Flip%", 0) or 0))
    out["_sort"] = out.apply(lambda r: sort_key(r), axis=1)
    out = out.sort_values("_sort").drop(columns=["_sort", "_flip_status"])
    return out


@st.cache_data(ttl=300, show_spinner=False)
def get_fmp_economic_calendar():
    if not FMP_API_KEY: return []
    try:
        r = requests.get("https://financialmodelingprep.com/api/v3/economic_calendar",
            params={"from": datetime.now().strftime("%Y-%m-%d"),
                    "to": (datetime.now()+timedelta(days=7)).strftime("%Y-%m-%d"),
                    "apikey": FMP_API_KEY}, timeout=10)
        d = r.json()
        return d if isinstance(d, list) else []
    except Exception: return []

def event_risk_message(events, pair_name):
    if not events: return "لا توجد بيانات تقويم"
    b, m = news_time_block(events, pair_name)
    if b: return f"⚠️ {m}"
    return "لا يوجد قفل خبر مطابق"


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
.hero-badge-balanced { display: inline-block; padding: 3px 12px;
    border-radius: 40px; background: rgba(124,212,160,0.12); color: #7cd4a0;
    font-size: 0.7rem; font-weight: 700;
    border: 1px solid rgba(124,212,160,0.35);
    margin-left: 6px; letter-spacing: 1.5px; }
div[data-testid="stHorizontalBlock"] > div > div > div[data-testid="stButton"] { margin-top: 0 !important; }
div[data-testid="stHorizontalBlock"] > div > div > div[data-testid="stButton"] > button {
    padding: 0.55rem 0.8rem !important; font-size: 0.85rem !important;
    white-space: nowrap !important; min-height: 42px !important; }
.signal-card { background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 40px 24px; border-radius: 28px; text-align: center;
    border: 1px solid rgba(255,255,255,0.06);
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
    position: relative; overflow: hidden; }
.signal-card::after { content:''; position:absolute; inset:0;
    background: radial-gradient(circle at 50% 0%, rgba(230,200,124,0.06), transparent 70%);
    pointer-events: none; }
.signal-value { font-size: 4rem; font-weight: 800; letter-spacing: 4px; margin: 8px 0; }
.signal-conf { font-size: 1.35rem; color: #c8d2e2; font-weight: 500; }
.signal-meta { color: #7d879c; font-size: 0.9rem; margin-top: 8px; }
.signal-grade { font-size: 1.6rem; font-weight: 800; color: #e6c87c;
    letter-spacing: 2px; margin-top: 10px; }
.metric-card { background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 18px 20px; border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.05);
    box-shadow: 0 8px 20px rgba(0,0,0,0.4); transition: all 0.25s ease; }
.metric-card:hover { border-color: rgba(230,200,124,0.25); transform: translateY(-2px); }
.metric-label { color: #7d879c; font-size: 0.78rem;
    text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }
.metric-value { color: #e8edf5; font-size: 1.5rem; font-weight: 700; margin-top: 6px; }
.metric-sub { color: #a0aab8; font-size: 0.82rem; margin-top: 4px; }
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
.section-title { font-size: 1.4rem; font-weight: 700; color: #e6c87c;
    margin: 32px 0 18px 0; padding-bottom: 12px;
    border-bottom: 1px solid rgba(230,200,124,0.15); }
.section-title span { color: #6b7488; font-size: 0.85rem; font-weight: 400; }
div.stButton > button { background: linear-gradient(145deg, #1a2130, #131821);
    color: #e8edf5; border: 1px solid rgba(230,200,124,0.2);
    border-radius: 40px; padding: 0.7rem 1.8rem; font-weight: 500;
    letter-spacing: 0.3px; transition: all 0.25s ease;
    box-shadow: 0 6px 16px rgba(0,0,0,0.4); width: 100%; }
div.stButton > button:hover { background: linear-gradient(145deg, #263049, #1a2233);
    border-color: rgba(230,200,124,0.55); color: #fff;
    transform: translateY(-1px); box-shadow: 0 10px 24px rgba(0,0,0,0.6); }
div[data-testid="stSelectbox"] > label { color: #e6c87c !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    letter-spacing: 0.5px; margin-bottom: 6px !important; }
div[data-testid="stSelectbox"] > div > div {
    background: linear-gradient(145deg, #10141c, #0d1017) !important;
    border: 1px solid rgba(230,200,124,0.25) !important;
    border-radius: 12px !important; min-height: 46px !important; }
div[data-baseweb="select"] > div { background: transparent !important; }
div[data-baseweb="select"] input { color: #e8edf5 !important; }
button[data-baseweb="tab"] { background: transparent; color: #8892a5;
    border-radius: 12px 12px 0 0; font-weight: 500; padding: 12px 20px; }
button[data-baseweb="tab"][aria-selected="true"] { color: #e6c87c !important;
    background: rgba(230,200,124,0.05); border-bottom: 2px solid #e6c87c; }
div[data-testid="stDataFrame"] { background: #0d1017; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stDataFrame"] th { background: #10141c !important;
    color: #e6c87c !important; font-weight: 600 !important;
    text-transform: uppercase; font-size: 0.75rem !important;
    letter-spacing: 0.5px; }
div[data-testid="stDataFrame"] td { background: #0d1017 !important;
    color: #ced6e6 !important; }
div[data-testid="stMetric"] { background: linear-gradient(145deg, #10141c, #0d1017);
    padding: 16px 18px; border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.05); }
div[data-testid="stMetric"] label { color: #7d879c !important;
    font-size: 0.78rem !important; text-transform: uppercase;
    letter-spacing: 1px; font-weight: 600; }
div[data-testid="stMetric"] .stMetricValue { color: #e8edf5 !important;
    font-weight: 700 !important; }
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
                <span class="hero-badge-balanced">FLIP WATCH</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="hero">
            <div class="hero-title">▲ BLACK PYRAMID</div>
            <div class="hero-sub" style="margin-top: 8px;">
                Institutional Analysis Terminal
                <span class="hero-badge">{APP_VERSION}</span>
                <span class="hero-badge-balanced">FLIP WATCH</span>
            </div>
        </div>""", unsafe_allow_html=True)

with hr:
    st.markdown('<div style="height: 32px;"></div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
    with b1:
        if st.button("📅 التقويم", width="stretch", key="btn_cal"):
            st.session_state.show_calendar_today = not st.session_state.show_calendar_today
            st.session_state.show_session_info = False
            st.session_state.show_market_status = False
    with b2:
        if st.button("🕐 الجلسة", width="stretch", key="btn_sess"):
            st.session_state.show_session_info = not st.session_state.show_session_info
            st.session_state.show_calendar_today = False
            st.session_state.show_market_status = False
    with b3:
        if st.button("📊 السوق", width="stretch", key="btn_mkt"):
            st.session_state.show_market_status = not st.session_state.show_market_status
            st.session_state.show_calendar_today = False
            st.session_state.show_session_info = False
    with b4:
        if st.button("🔄 تحديث", width="stretch", key="btn_ref"):
            st.session_state.economic_events = get_fmp_economic_calendar()
            st.toast("✅ تم التحديث")


if st.session_state.show_calendar_today:
    st.markdown("### 📅 أحداث اليوم")
    if not st.session_state.economic_events:
        st.info("اضغط '🔄 تحديث'.")
    else:
        tt = get_todays_events(st.session_state.economic_events, st.session_state.selected_pair)
        if not tt: st.success("✅ لا أحداث عالية.")
        else:
            cc = st.columns(3)
            for i, ev in enumerate(tt[:9]):
                imp = ev["impact"]
                if imp in ("high","3","high impact"): ic_ = "🔴"; cl = "#f57a7a"
                elif imp in ("medium","2"): ic_ = "🟡"; cl = "#f5c87a"
                else: ic_ = "🟢"; cl = "#7cd4a0"
                with cc[i % 3]:
                    st.markdown(f"""<div class="tool-card" style="margin-bottom:12px;">
                        <div class="tool-name">{ic_} {ev['time']} · {ev['country']}</div>
                        <div class="tool-value" style="font-size:0.95rem; color:{cl};">
                            {ev['event'][:50]}</div>
                        <div class="tool-desc">التأثير: <b>{ev['impact'].upper()}</b></div>
                    </div>""", unsafe_allow_html=True)

if st.session_state.show_session_info:
    st.markdown("### 🕐 الجلسة الحالية")
    si = get_current_session_info()
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🌍 الجلسة</div>
            <div class="tool-value">{si['icon']} {si['session']}</div>
            <div class="tool-desc">{si['desc']}</div></div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">⏰ التوقيت</div>
            <div class="tool-value">{si['time_utc']}</div>
            <div class="tool-desc">UTC</div></div>""", unsafe_allow_html=True)
    with sc3:
        kic = "✅" if "داخل" in si["kill_zone"] else "⚪"
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🎯 Kill Zone</div>
            <div class="tool-value">{kic}</div>
            <div class="tool-desc">{si['kill_zone']}</div></div>""", unsafe_allow_html=True)

if st.session_state.show_market_status:
    st.markdown("### 📊 وضع السوق")
    _ms = PAIRS.get(st.session_state.selected_pair, "GC=F")
    mst = get_market_status_info(_ms, st.session_state.selected_pair)
    if mst is None: st.warning("تعذر التحميل.")
    else:
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">📈 الاتجاه</div>
                <div class="tool-value">{mst['trend_icon']}</div>
                <div class="tool-desc">{mst['trend_align']}</div></div>""", unsafe_allow_html=True)
        with mc2:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">🌊 التقلب</div>
                <div class="tool-value">{mst['vol_icon']} {mst['vol_state']}</div>
                <div class="tool-desc">ATR ratio: <b>{mst['atr_ratio']:.2f}×</b></div></div>""",
                unsafe_allow_html=True)
        with mc3:
            rgi = trend_icon(mst["regime"])
            st.markdown(f"""<div class="tool-card"><div class="tool-name">🎯 النظام</div>
                <div class="tool-value">{rgi} {mst['regime']}</div>
                <div class="tool-desc">الهيكل: <b>{mst['structure']}</b></div></div>""",
                unsafe_allow_html=True)
        with mc4:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">⚖️ الحالة</div>
                <div class="tool-value">{mst['overall_icon']}</div>
                <div class="tool-desc">{mst['overall']}</div></div>""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.caption(f"Version {APP_VERSION}")
    st.markdown("---")
    st.markdown("**🎯 SL Mode: أقرب نقطة**")
    st.caption(f"• Min: {SL_MIN_DIST_ATR} ATR · Max: {SL_MAX_DIST_ATR} ATR")
    st.markdown("---")
    st.markdown("**🧠 ML Model**")
    if not SKLEARN_AVAILABLE: st.caption("⚠️ sklearn غير مثبت")
    elif st.session_state.get("ml_model"):
        mp = st.session_state.ml_model
        st.success(f"✅ {mp.get('model_name','?')}")
        st.caption(f"AUC: {mp.get('auc',0):.3f}")
        if st.button("🗑️ Clear ML", width="stretch", key="clr_ml"):
            st.session_state.ml_model = None; st.rerun()
    else:
        xb = "✅" if XGBOOST_AVAILABLE else "⚠️"
        st.caption(f"⚪ Not trained · XGB {xb}")
    st.markdown("---")
    st.markdown("**💼 Portfolio**")
    ops_ = st.session_state.get("open_positions", [])
    st.caption(f"• Open: {len(ops_)}")
    if ops_:
        _pnl = calculate_portfolio_pnl()
        st.caption(f"• P&L: ${_pnl['total_pnl_usd']:+,.2f}")
        st.caption(f"• R: {_pnl['total_r']:+.2f}R")
    st.markdown("---")
    st.markdown("**🛑 Kill Switch**")
    kb, cs = check_kill_switch()
    if kb: st.error(f"🚫 نشط — {cs} خسائر")
    else: st.success(f"✅ ({cs}/{MAX_CONSECUTIVE_LOSSES})")
    if st.button("🗑️ Reset", width="stretch", key="rstk"):
        st.session_state.recent_results = []; st.rerun()
    st.markdown("---")
    sm = st.checkbox("🔒 Strict Filters",
        value=st.session_state.get("strict_filters", False))
    st.session_state.strict_filters = sm
    st.markdown("---")
    if st.button("🔄 Refresh Cache", width="stretch"):
        st.cache_data.clear(); st.rerun()


st.markdown('<div class="section-title">🎯 Analysis Control <span>اختر الأصل</span></div>',
            unsafe_allow_html=True)
cc1, cc2, cc3 = st.columns([2.2, 1, 1])
with cc1:
    sp_ = st.selectbox("🎯 اختر الأصل للتحليل", list(PAIRS.keys()),
        index=list(PAIRS.keys()).index(st.session_state.selected_pair)
        if st.session_state.selected_pair in PAIRS else 0, key="pair_sel")
    st.session_state.selected_pair = sp_
    sym = PAIRS[sp_]
with cc2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    ana1 = st.button("🎯 تحليل الأصل", width="stretch", key="btn_one")
with cc3:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    ana_all = st.button("🌐 تحليل الكل", width="stretch", key="btn_all")

if ana_all:
    with st.spinner("Scanning..."):
        t0 = time.time()
        st.session_state.all_signals = get_all_signals_parallel()
        st.session_state.analysis_time = time.time() - t0
if ana1:
    st.cache_data.clear(); st.rerun()

if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
    st.markdown('<div class="section-title">🌐 All Assets <span>مع Flip Detection</span></div>',
                unsafe_allow_html=True)
    r1, r2, r3 = st.columns([3, 1, 1])
    with r1:
        n_flips = 0
        if "🔄 Flip" in st.session_state.all_signals.columns:
            n_flips = (st.session_state.all_signals["🔄 Flip"] != "—").sum()
        if n_flips > 0:
            st.warning(f"✅ {len(st.session_state.all_signals)} أصول · "
                       f"🔄 **{n_flips} فيها إشارة انعكاس**")
        else:
            st.success(f"✅ {len(st.session_state.all_signals)} أصول.")
    with r2:
        show_flips_only = st.checkbox("🔄 Flip فقط", value=False,
                                       key="filter_flip_only")
    with r3:
        if st.button("🗑️ مسح", width="stretch", key="clr_all"):
            st.session_state.all_signals = None; st.rerun()
    df_show = st.session_state.all_signals.copy()
    if show_flips_only and "🔄 Flip" in df_show.columns:
        df_show = df_show[df_show["🔄 Flip"] != "—"]
    st.dataframe(df_show, hide_index=True, width="stretch", height=460)
    
    if "🔄 Flip" in st.session_state.all_signals.columns:
        flips_df = st.session_state.all_signals[
            st.session_state.all_signals["🔄 Flip"] != "—"]
        if not flips_df.empty:
            with st.expander(f"🔀 {len(flips_df)} إشارات Flip مكتشفة", expanded=True):
                for _, row in flips_df.iterrows():
                    flip_txt = row["🔄 Flip"]
                    flip_conf = row.get("Flip%", 0)
                    pair_name = row["الزوج"]
                    if "🚨" in flip_txt:
                        color = "#f57a7a"; label = "STRONG"
                    elif "⚠️" in flip_txt:
                        color = "#f5c87a"; label = "POSSIBLE"
                    else:
                        color = "#7cd4a0"; label = "WATCH"
                    st.markdown(f"""
                    <div style="margin:6px 0; padding:10px 16px;
                                background:linear-gradient(145deg, #10141c, #0d1017);
                                border-radius:12px;
                                border:1px solid {color}44;
                                border-left:4px solid {color};
                                display:flex; justify-content:space-between;
                                align-items:center; flex-wrap:wrap; gap:10px;">
                        <div>
                            <span style="color:#e6c87c; font-weight:700;
                                         font-size:0.95rem;">{pair_name}</span>
                            <span style="color:#7d879c; font-size:0.8rem;
                                         margin-left:8px;">
                                الأصل: {row['الإشارة']}</span>
                        </div>
                        <div>
                            <span style="color:{color}; font-weight:700;
                                         font-size:0.95rem;">{flip_txt}</span>
                            <span style="color:#a0aab8; font-size:0.85rem;
                                         margin-left:10px;">
                                ثقة {flip_conf}% · {label}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
    st.markdown("---")


cur_price, chg = get_spot_price(sym)
if cur_price is None: st.error(f"تعذر السعر لـ {sp_}."); st.stop()
df_raw = get_historical_data(sym, "3mo", "4h")
if df_raw is None: st.error(f"تعذر البيانات لـ {sp_}."); st.stop()

ntb, _ = news_time_block(st.session_state.economic_events or [], sp_)
ss_soft = st.session_state.get("strict_filters", False)
_ccs = get_currency_strength_matrix()
st.session_state["_ccy_strength_cache"] = _ccs
_rd, _rm = get_interest_rate_differential(sp_)
_rsk = get_risk_sentiment()

result = generate_signal(df_raw, cur_price, sp_, sym, news_block=ntb, strict_soft=ss_soft)
df = result["df"]; lv = result["levels"]; sig = result["signal"]; conf = result["confidence"]

# FLIP DETECTION
flip_result = None
if sig in ("BUY", "SELL"):
    try:
        flip_result = detect_signal_flip(df, cur_price, sig, profile_for(sp_))
    except Exception:
        flip_result = None


# Status banners
mo_, mm_ = is_market_open(sp_)
if not mo_: st.error(f"🚫 **{mm_}**")
kb_, cs_ = check_kill_switch()
if kb_: st.error(f"🛑 **Kill Switch نشط** — {cs_} خسائر")

if sig in ("BUY","SELL") and st.session_state.get("open_positions"):
    corr_c = check_portfolio_conflict(sym, sig, sp_, st.session_state.open_positions)
    if corr_c["blocked"]:
        st.error("🚫 **Portfolio Conflict** — محظور:")
        for w in corr_c["warnings"]: st.markdown(f"- {w}")
    elif corr_c["warnings"]:
        st.warning("⚠️ **Correlation Warnings:**")
        for w in corr_c["warnings"]: st.markdown(f"- {w}")

if st.session_state.get("open_positions"):
    urgent_alerts = []
    for p in st.session_state.open_positions:
        m = p.get("_monitor")
        if m is None:
            try:
                m = monitor_position(p); p["_monitor"] = m
            except Exception: m = None
        if m and m.get("severity", 0) >= 60:
            urgent_alerts.append((p, m))
    if urgent_alerts:
        for p, m in urgent_alerts:
            st.error(f"⚠️ **#{p['id']} {p['pair']}** — {m['action']}")

# FLIP BANNER
if flip_result and flip_result.get("flip_signal"):
    flip_sig = flip_result["flip_signal"]
    flip_conf = flip_result["confidence"]
    flip_status = flip_result["status"]
    if flip_status == "STRONG_FLIP":
        st.error(f"🚨 **FLIP ALERT** — إشارة قوية للانعكاس إلى **{flip_sig}** "
                 f"(ثقة {flip_conf:.0f}%) · {len(flip_result['triggers'])} مؤشر")
    elif flip_status == "POSSIBLE_FLIP":
        st.warning(f"⚠️ **Possible Flip** — قد يتحول إلى **{flip_sig}** "
                   f"(ثقة {flip_conf:.0f}%) · {len(flip_result['triggers'])} مؤشر")
    else:
        st.info(f"💡 **Flip Watch** — مؤشرات أولية نحو **{flip_sig}** "
                f"(ثقة {flip_conf:.0f}%)")


c_sig, c_stat = st.columns([1.6, 1])
with c_sig:
    sc_ = ("#7cd4a0" if sig == "BUY"
           else "#f57a7a" if sig == "SELL" else "#f5c87a")
    ec_ = ("#7cd4a0" if result["execution_status"] == "EXECUTE"
           else "#f5c87a" if result["execution_status"] in ("WATCH","WAIT") else "#f57a7a")
    mlp_ = result.get("ml_probability")
    mls_ = result.get("ml_status", "no_model")
    mlb = ""
    if mls_ == "applied" and mlp_ is not None:
        mc_ = "#7cd4a0" if mlp_ >= 0.55 else "#f57a7a" if mlp_ <= 0.45 else "#f5c87a"
        mlb = f'<div class="signal-meta" style="margin-top:8px; color:{mc_};">🎓 ML Win: <b>{mlp_*100:.1f}%</b></div>'
    elif mls_ == "no_model":
        mlb = '<div class="signal-meta" style="margin-top:8px; color:#6b7488;">🎓 ML: Not trained</div>'
    flip_badge = ""
    if flip_result and flip_result.get("flip_signal"):
        flip_sig_ = flip_result["flip_signal"]; flip_conf_ = flip_result["confidence"]
        flip_status_ = flip_result["status"]
        if flip_status_ == "STRONG_FLIP":
            flip_badge = (f'<div style="margin-top:10px; padding:8px 14px; '
                          f'background:rgba(245,122,122,0.12); border-radius:12px; '
                          f'border:1px solid rgba(245,122,122,0.35); color:#f57a7a; '
                          f'font-weight:700;">🚨 FLIP → {flip_sig_} ({flip_conf_:.0f}%)</div>')
        elif flip_status_ == "POSSIBLE_FLIP":
            flip_badge = (f'<div style="margin-top:10px; padding:8px 14px; '
                          f'background:rgba(245,200,122,0.10); border-radius:12px; '
                          f'border:1px solid rgba(245,200,122,0.35); color:#f5c87a; '
                          f'font-weight:600;">⚠️ احتمالي → {flip_sig_} ({flip_conf_:.0f}%)</div>')
    st.markdown(f"""
    <div class="signal-card">
        <div class="signal-meta">BLACK PYRAMID · {sp_}</div>
        <div class="signal-value" style="color:{sc_};">{sig}</div>
        <div class="signal-conf">Confidence: <b>{conf:.1f}%</b></div>
        <div class="signal-grade">Grade: {result['trade_grade']}</div>
        <div class="signal-meta" style="margin-top:14px;">
            Execution: <b style="color:{ec_};">{result['execution_status']}</b>
            &nbsp;·&nbsp; {result['execution_reason']}
        </div>
        {flip_badge}
        {mlb}
    </div>""", unsafe_allow_html=True)

with c_stat:
    st.markdown(f"""
    <div class="metric-card" style="margin-bottom:14px;">
        <div class="metric-label">Current Price</div>
        <div class="metric-value">{fmt_price(cur_price, sp_)}</div>
        <div class="metric-sub">Change: {chg:+.2f}%</div>
    </div>""", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">BUY</div>
            <div class="metric-value" style="color:#7cd4a0;">{result['buy_score']:.0f}</div></div>""",
            unsafe_allow_html=True)
    with s2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">SELL</div>
            <div class="metric-value" style="color:#f57a7a;">{result['sell_score']:.0f}</div></div>""",
            unsafe_allow_html=True)
    st.markdown(f"""<div class="metric-card" style="margin-top:14px;">
        <div class="metric-label">Confluence</div>
        <div class="metric-value">{result['weighted_confluence']:.0f}
        <span style="font-size:1rem; color:#6b7488;">/ 100</span></div>
        <div class="metric-sub">Confirmation: {result['confirmation_score']:.1f}</div>
    </div>""", unsafe_allow_html=True)

sadv = result.get("soft_advisories", "None")
if sadv and sadv != "None":
    if not ss_soft: st.info(f"💡 **Advisories:** {sadv}")
    else: st.warning(f"⚠️ **Strict ({result['soft_penalties']:.1f}):** {sadv}")


if sig in ("BUY","SELL") and lv:
    src = lv.get("sources", {})
    st.markdown('<div class="section-title">🎯 Trade Plan <span>أقرب نقطة مكتشفة</span></div>',
                unsafe_allow_html=True)
    l1, l2, l3, l4, l5 = st.columns(5)
    l1.metric("Entry", fmt_price(lv["entry"], sp_))
    l2.metric("Stop Loss", fmt_price(lv["stop_loss"], sp_), help=src.get("sl", ""))
    l3.metric("TP1", fmt_price(lv["target1"], sp_), help=src.get("tp1",""))
    l4.metric("TP2", fmt_price(lv["target2"], sp_), help=src.get("tp2",""))
    l5.metric("TP3", fmt_price(lv["target3"], sp_), help=src.get("tp3",""))
    rr1, rr2, rr3, _ = st.columns([1, 1, 1, 2])
    rr1.metric("RR·TP1", f"1:{lv['risk_reward_1']:.2f}")
    rr2.metric("RR·TP2", f"1:{lv['risk_reward_2']:.2f}")
    rr3.metric("RR·TP3", f"1:{lv['risk_reward_3']:.2f}")
    st.markdown(f"""<div style="margin-top:14px; display:flex; gap:10px; flex-wrap:wrap;">
        <span style="background:rgba(245,122,122,0.15); padding:6px 14px;
                     border-radius:20px; color:#f57a7a; font-size:0.85rem;
                     border:1px solid rgba(245,122,122,0.35); font-weight:600;">
            🛑 SL: {src.get('sl','—')}</span>
        <span style="background:rgba(230,200,124,0.15); padding:6px 14px;
                     border-radius:20px; color:#e6c87c; font-size:0.85rem;
                     border:1px solid rgba(230,200,124,0.35);">
            🎯 TP1: {src.get('tp1','—')}</span>
        <span style="background:rgba(124,212,160,0.12); padding:6px 14px;
                     border-radius:20px; color:#7cd4a0; font-size:0.85rem;
                     border:1px solid rgba(124,212,160,0.35);">
            🎯 TP2: {src.get('tp2','—')}</span>
        <span style="background:rgba(124,212,160,0.12); padding:6px 14px;
                     border-radius:20px; color:#7cd4a0; font-size:0.85rem;
                     border:1px solid rgba(124,212,160,0.35);">
            🎯 TP3: {src.get('tp3','—')}</span>
    </div>""", unsafe_allow_html=True)

    with st.expander("🔍 التفاصيل: من أين جاء SL؟", expanded=False):
        if lv.get("sl_level_price"):
            st.markdown(f"**SL Level:** `{fmt_price(lv['sl_level_price'], sp_)}` ← {src.get('sl','—')}")
        if lv.get("idm"):
            st.markdown(f"**IDM:** `{fmt_price(lv['idm'], sp_)}`")
        if lv.get("obs"):
            st.markdown("**Order Blocks:**")
            for ob in lv["obs"][:3]:
                st.markdown(f"- {ob['name']}: `{fmt_price(ob['low'], sp_)} → {fmt_price(ob['high'], sp_)}`")
        if lv.get("fvgs"):
            st.markdown("**FVG Zones:**")
            for fv in lv["fvgs"][:3]:
                st.markdown(f"- {fv['name']}: `{fmt_price(fv['low'], sp_)} → {fmt_price(fv['high'], sp_)}`")
        if lv.get("liq"):
            st.markdown("**Liquidity:**")
            for lq in lv["liq"][:3]:
                st.markdown(f"- {lq['name']}: `{fmt_price(lq['level'], sp_)}`")

    st.markdown('<div class="section-title">💰 Position Size</div>', unsafe_allow_html=True)
    psc1, psc2 = st.columns(2)
    with psc1:
        ab = st.number_input("💵 الرصيد (USD)", min_value=100.0, value=10000.0,
                             step=500.0, key=f"bal_{sp_}")
    with psc2:
        rp = st.number_input("⚠️ المخاطرة %", min_value=0.25, max_value=5.0,
                             value=1.0, step=0.25, key=f"rsk_{sp_}")
    ps = calc_position_size(ab, rp, lv["entry"], lv["stop_loss"], sp_)
    if ps:
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("💵 مخاطرة", f"${ps['risk_amount']:.2f}")
        p2.metric("📏 SL", f"{ps.get('sl_pips', ps['sl_distance']):.1f}")
        if ps["asset"] == "crypto":
            p3.metric("🪙 كمية", f"{ps['units']:.6f}")
            p4.metric("📊 وحدة", "Coins")
        else:
            p3.metric("📦 لوتات", f"{ps['lots']:.2f}")
            p4.metric("📊 وحدة", ps["unit_label"])

    st.markdown('<div class="section-title">📋 Management</div>', unsafe_allow_html=True)
    mgmt = build_trade_management(sig, lv, profile_for(sp_))
    if mgmt:
        mc = st.columns(3)
        for i, stg in enumerate(mgmt):
            with mc[i]:
                st.markdown(f"""<div class="tool-card">
                    <div class="tool-name">{stg['icon']} {stg['stage']}</div>
                    <div class="tool-value" style="font-size:1rem;">{stg['action']}</div>
                    <div class="tool-desc">{stg['details']}</div></div>""",
                    unsafe_allow_html=True)

    st.markdown('<div class="section-title">📌 Portfolio Action</div>', unsafe_allow_html=True)
    cs_conf = None
    if st.session_state.get("open_positions"):
        cs_conf = check_portfolio_conflict(sym, sig, sp_, st.session_state.open_positions)
    pa1, pa2, pa3 = st.columns([1, 1, 2])
    with pa1:
        lot_in = st.number_input("📦 حجم", min_value=0.01, value=1.0,
                                 step=0.1, key=f"lot_{sp_}")
    with pa2:
        can = not (cs_conf and cs_conf["blocked"])
        if can:
            if st.button("📌 فتح صفقة", width="stretch", key="open_p"):
                if add_open_position(result, sp_, sym, lot_in):
                    st.success("✅ تم"); st.rerun()
        else:
            st.button("🚫 محظور", width="stretch", disabled=True, key="opd")
    with pa3:
        if cs_conf and cs_conf["blocked"]: st.error("🚫 تعارض")
        elif cs_conf and cs_conf["warnings"]: st.warning("⚠️ تحذيرات")
        else: st.info("💡 أضف الصفقة")

    # FLIP WATCH
    if flip_result and flip_result.get("flip_signal"):
        flip_sig = flip_result["flip_signal"]
        flip_conf = flip_result["confidence"]
        flip_status = flip_result["status"]
        flip_color = ("#f57a7a" if flip_status == "STRONG_FLIP"
                      else "#f5c87a" if flip_status == "POSSIBLE_FLIP"
                      else "#7cd4a0")
        st.markdown('<div class="section-title">🔀 Signal Flip Watch '
                    '<span>متى تنعكس الإشارة؟</span></div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:linear-gradient(145deg, #10141c, #0d1017);
                    padding:18px 22px; border-radius:16px;
                    border:1px solid {flip_color}44; border-left:4px solid {flip_color};">
            <div style="display:flex; justify-content:space-between; align-items:center;
                        flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="color:#7d879c; font-size:0.75rem; letter-spacing:1px;
                                text-transform:uppercase;">Flip Signal</div>
                    <div style="color:{flip_color}; font-size:1.8rem; font-weight:800;
                                letter-spacing:2px; margin-top:4px;">{flip_sig}</div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#7d879c; font-size:0.75rem; letter-spacing:1px;
                                text-transform:uppercase;">Confidence</div>
                    <div style="color:{flip_color}; font-size:1.6rem; font-weight:800;
                                margin-top:4px;">{flip_conf:.0f}%</div>
                </div>
                <div style="flex:1; text-align:right;">
                    <div style="color:#e8edf5; font-size:0.95rem;">{flip_result['message']}</div>
                    <div style="color:#8892a5; font-size:0.82rem; margin-top:4px;">
                        {len(flip_result['triggers'])} مؤشر داعم
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
        with st.expander(f"🔍 تفاصيل الانعكاس ({len(flip_result['triggers'])} مؤشر)",
                         expanded=(flip_conf >= 45)):
            for tr in flip_result["triggers"]:
                st.markdown(f"- {tr['icon']} **{tr['name']}** — قوة {tr['score']}")
            if flip_result.get("new_levels") and flip_conf >= 45:
                nl = flip_result["new_levels"]
                st.markdown("---")
                st.markdown(f"**🎯 Trade Plan الجديد للـ {flip_sig}:**")
                fc1, fc2, fc3, fc4, fc5 = st.columns(5)
                fc1.metric("Entry", fmt_price(nl["entry"], sp_))
                fc2.metric("SL", fmt_price(nl["stop_loss"], sp_),
                          help=nl["sources"].get("sl", ""))
                fc3.metric("TP1", fmt_price(nl["target1"], sp_),
                          help=nl["sources"].get("tp1", ""))
                fc4.metric("TP2", fmt_price(nl["target2"], sp_))
                fc5.metric("RR·TP1", f"1:{nl['risk_reward_1']:.2f}")
                if flip_conf >= 70:
                    st.error(f"⚠️ **يُنصح بالتفكير في دخول {flip_sig}** — "
                             f"الستوب عند {nl['sources'].get('sl', '?')}")
                else:
                    st.info(f"💡 **راقب السعر** — إن أغلقت الشمعة القادمة "
                             f"فوق/تحت النقطة الحالية، فقد يتأكد الانعكاس")


tab_ov, tab_tl, tab_smc, tab_mtf, tab_fnd, tab_prt, tab_ml, tab_flt, tab_cht, tab_cal, tab_jrn, tab_bt = st.tabs([
    "📊 Overview","🧰 Tools","🏛️ SMC","⏱️ MTF",
    "💰 Fundamentals","💼 Portfolio","🎓 ML Model","🎛️ Filters",
    "📈 Chart","📅 Calendar","📔 Journal","🔬 Backtest"])


with tab_ov:
    st.markdown('<div class="section-title">🧠 Five Pillars</div>', unsafe_allow_html=True)
    pn = {"structure": "Structure", "trend": "Trend", "momentum": "Momentum",
          "volume": "Volume & Flow", "context": "Context"}
    c = st.columns(5)
    for i, p in enumerate(PILLAR_WEIGHTS):
        b = result["pillars"]["BUY"][p]; s = result["pillars"]["SELL"][p]
        c[i].metric(pn[p], f"B {b:.0f}", delta=f"S {s:.0f}", delta_color="inverse")
    st.markdown('<div class="section-title">📝 Reasons</div>', unsafe_allow_html=True)
    if result["reasons"]:
        for r in result["reasons"][:10]: st.markdown(f"- {r}")
    else: st.caption("—")
    st.markdown('<div class="section-title">🛡️ Confirmation</div>', unsafe_allow_html=True)
    gc1, gc2, gc3 = st.columns(3)
    gc1.metric("Score", f"{result['confirmation_score']:.1f}/100")
    gc2.metric("Gate", "✅ PASS" if result["confirmation_ok"] else "⚠️ SOFT")
    gc3.metric("Raw/Eff", f"{result['raw_confidence']:.1f} / {result['confidence']:.1f}")
    if lv and lv.get("sources"):
        st.markdown('<div class="section-title">🎯 Sources <span>من أين كل مستوى؟</span></div>',
                    unsafe_allow_html=True)
        src = lv["sources"]
        ic1, ic2, ic3, ic4 = st.columns(4)
        ic1.metric("🛑 SL Source", src.get("sl", "—"))
        ic2.metric("🎯 TP1 Source", src.get("tp1", "—"))
        ic3.metric("🎯 TP2 Source", src.get("tp2", "—"))
        ic4.metric("🎯 TP3 Source", src.get("tp3", "—"))


with tab_tl:
    l = df.iloc[-1]
    st.markdown('<div class="section-title">📈 Trend</div>', unsafe_allow_html=True)
    e20 = safe_float(l.get("ema20")); e50 = safe_float(l.get("ema50")); e200 = safe_float(l.get("ema200"))
    if e20 > e50 > e200: es = "Fully Bullish"; ei = "🟢"
    elif e20 < e50 < e200: es = "Fully Bearish"; ei = "🔴"
    elif e20 > e50: es = "Short-term Bullish"; ei = "🟡"
    else: es = "Short-term Bearish"; ei = "🟡"
    vw = safe_float(l.get("vwap")); vt = l.get("vwap_type", "session")
    vs_ = "Above VWAP" if cur_price > vw else "Below VWAP"
    vi = "🟢" if cur_price > vw else "🔴"
    vl = "Rolling(20)" if vt == "rolling" else "Session"
    t1, t2 = st.columns(2)
    with t1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📊 EMA</div>
            <div class="tool-value">{ei} {es}</div>
            <div class="tool-desc">EMA20: <b>{e20:.5f}</b><br>EMA50: <b>{e50:.5f}</b><br>
            EMA200: <b>{e200:.5f}</b></div></div>""", unsafe_allow_html=True)
    with t2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📉 VWAP·{vl}</div>
            <div class="tool-value">{vi} {vs_}</div>
            <div class="tool-desc">VWAP: <b>{vw:.5f}</b><br>
            Distance: <b>{((cur_price-vw)/vw*100):+.2f}%</b></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚡ Momentum</div>', unsafe_allow_html=True)
    r_ = safe_float(l.get("rsi"), 50); mh = safe_float(l.get("macd_histogram"))
    if r_ >= 70: rs_ = "Overbought"; ri = "🔴"
    elif r_ <= 30: rs_ = "Oversold"; ri = "🟢"
    elif r_ >= 55: rs_ = "Bullish"; ri = "🟢"
    elif r_ <= 45: rs_ = "Bearish"; ri = "🔴"
    else: rs_ = "Neutral"; ri = "🟡"
    ms_ = "Bullish" if mh > 0 else "Bearish"; mi = "🟢" if mh > 0 else "🔴"
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">🎯 RSI</div>
            <div class="tool-value">{ri} {r_:.1f}</div>
            <div class="tool-desc">{rs_}</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📈 MACD</div>
            <div class="tool-value">{mi} {ms_}</div>
            <div class="tool-desc">Hist: <b>{mh:.5f}</b></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">🌊 Volatility</div>', unsafe_allow_html=True)
    atr_ = safe_float(l.get("atr")); ap_ = (atr_/cur_price*100) if cur_price else 0
    bu = safe_float(l.get("bb_upper")); bl = safe_float(l.get("bb_lower"))
    bw = ((bu-bl)/cur_price*100) if cur_price else 0
    if bw < 1.5: bs_ = "Compression"
    elif bw > 5.0: bs_ = "Expansion"
    else: bs_ = "Normal"
    v1, v2 = st.columns(2)
    with v1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📊 ATR</div>
            <div class="tool-value">{atr_:.5f}</div>
            <div class="tool-desc">ATR %: <b>{ap_:.3f}%</b></div></div>""", unsafe_allow_html=True)
    with v2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📉 BB</div>
            <div class="tool-value">{bs_}</div>
            <div class="tool-desc">Width: <b>{bw:.2f}%</b></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">💧 Volume</div>', unsafe_allow_html=True)
    cm = safe_float(l.get("chaikin_mf"), 0)
    cms = "Accumulation" if cm > 0 else "Distribution"; cmi = "🟢" if cm > 0 else "🔴"
    va_ = df["volume"].rolling(20).mean().iloc[-1]
    vn_ = safe_float(l.get("volume"), 0); vr_ = (vn_/va_) if va_ > 0 else 1.0
    cf1, cf2 = st.columns(2)
    with cf1:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">💰 CMF</div>
            <div class="tool-value">{cmi} {cm:+.3f}</div>
            <div class="tool-desc">{cms}</div></div>""", unsafe_allow_html=True)
    with cf2:
        st.markdown(f"""<div class="tool-card"><div class="tool-name">📊 Volume</div>
            <div class="tool-value">{vr_:.2f}x</div>
            <div class="tool-desc">vs 20-avg</div></div>""", unsafe_allow_html=True)


with tab_smc:
    l = df.iloc[-1]
    st.markdown('<div class="section-title">🏛️ SMC</div>', unsafe_allow_html=True)
    s_ = structure_state(df); si_ = trend_icon(s_["state"])
    st.markdown(f"""<div class="tool-card" style="margin-bottom:20px;">
        <div class="tool-name">🏗️ Structure</div>
        <div class="tool-value">{si_} {s_['state']}</div></div>""", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (bk, sk, nm) in enumerate([
        ("bos_bullish","bos_bearish","BOS"), ("mss_bullish","mss_bearish","MSS"),
        ("liquidity_sweep_bullish","liquidity_sweep_bearish","Liquidity"),
        ("fvg_bullish","fvg_bearish","FVG")]):
        bb = safe_bool(l.get(bk)); be = safe_bool(l.get(sk))
        ic_ = "🟢" if bb else "🔴" if be else "⚪"
        stt = "Bullish" if bb else "Bearish" if be else "None"
        with cols[i]:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">{nm}</div>
                <div class="tool-value">{ic_}</div>
                <div class="tool-desc">{stt}</div></div>""", unsafe_allow_html=True)


with tab_mtf:
    st.markdown('<div class="section-title">⏱️ MTF</div>', unsafe_allow_html=True)
    mc = st.columns(4)
    for i, (tf, info) in enumerate(result["mtf_details"].items()):
        bias = info["bias"]
        ic_ = "🟢" if bias == "BULLISH" else "🔴" if bias == "BEARISH" else "🟡"
        cl = "#7cd4a0" if bias == "BULLISH" else "#f57a7a" if bias == "BEARISH" else "#f5c87a"
        with mc[i]:
            st.markdown(f"""<div class="tool-card"><div class="tool-name">{tf}</div>
                <div class="tool-value" style="color:{cl};">{ic_} {bias}</div>
                <div class="tool-desc">Strength: <b>{info['strength']}/10</b></div></div>""",
                unsafe_allow_html=True)


with tab_fnd:
    st.markdown('<div class="section-title">💪 Currency Strength</div>', unsafe_allow_html=True)
    if _ccs:
        sc_ = sorted(_ccs.items(), key=lambda x: x[1], reverse=True)
        cc_ = st.columns(len(sc_))
        for i, (cy, scr) in enumerate(sc_):
            if scr > 20: cl = "#7cd4a0"; stn = "STRONG"
            elif scr > 5: cl = "#a0d4b0"; stn = "Mild Bull"
            elif scr < -20: cl = "#f57a7a"; stn = "WEAK"
            elif scr < -5: cl = "#d4a0a0"; stn = "Mild Bear"
            else: cl = "#f5c87a"; stn = "Neutral"
            with cc_[i]:
                st.markdown(f"""<div class="tool-card"><div class="tool-name">{cy}</div>
                    <div class="tool-value" style="color:{cl}; font-size:1.1rem;">{scr:+.0f}</div>
                    <div class="tool-desc">{stn}</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Bond Yields</div>', unsafe_allow_html=True)
    _bd = get_bond_yields()
    if _bd["us10y"] is not None:
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("US10Y", f"{_bd['us10y']:.2f}%", delta=f"{_bd['us10y_change']:+.2f}")
        b2.metric("US5Y", f"{_bd['us5y']:.2f}%" if _bd['us5y'] else "N/A")
        b3.metric("US30Y", f"{_bd['us30y']:.2f}%" if _bd['us30y'] else "N/A")
        b4.metric("Curve", f"{_bd['curve_10y_5y']:+.2f}%" if _bd['curve_10y_5y'] else "N/A")
    st.markdown('<div class="section-title">🌊 Risk (VIX)</div>', unsafe_allow_html=True)
    if _rsk and _rsk.get("vix") is not None:
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("VIX", f"{_rsk['vix']:.2f}")
        r2.metric("20-avg", f"{_rsk.get('vix_avg', 0):.2f}")
        r3.metric("Change", f"{_rsk.get('vix_change', 0):+.2f}%")
        r4.metric("State", _rsk["vix_state"])


with tab_prt:
    st.markdown('<div class="section-title">💼 Live Portfolio Monitor</div>',
                unsafe_allow_html=True)
    ops = st.session_state.get("open_positions", [])
    if not ops:
        st.info("📭 لا توجد صفقات مفتوحة.")
    else:
        uc1, uc2 = st.columns([1, 3])
        with uc1:
            if st.button("🔄 Update All", width="stretch", key="upd_all"):
                with st.spinner("Monitoring..."):
                    for p in ops:
                        try: p["_monitor"] = monitor_position(p)
                        except Exception: pass
                st.success("✅ تم التحديث"); st.rerun()
        with uc2:
            st.caption("💡 حدّث حالة كل صفقة (ICT + Indicators + Flip + Reversal)")
        pnl = calculate_portfolio_pnl()
        pm1, pm2, pm3, pm4, pm5 = st.columns(5)
        pm1.metric("Positions", pnl["total_positions"])
        pm2.metric("💵 P&L", f"${pnl['total_pnl_usd']:+,.2f}",
                   delta_color="normal" if pnl["total_pnl_usd"] >= 0 else "inverse")
        pm3.metric("📊 R", f"{pnl['total_r']:+.2f}R",
                   delta_color="normal" if pnl["total_r"] >= 0 else "inverse")
        pm4.metric("✅", pnl["winners"])
        pm5.metric("❌", pnl["losers"])
        for it in pnl["detailed"]:
            p = it["pos"]; pd_ = it["pnl"]
            m = p.get("_monitor")
            if m is None:
                try:
                    m = monitor_position(p); p["_monitor"] = m
                except Exception:
                    m = {"state": "ERR", "action": "فشل", "severity": 0,
                         "reversal_signals": [], "suggested_sl": p.get("stop_loss")}
            sev = m.get("severity", 0); col, icon = state_color_severity(sev)
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.2, 1, 1, 1, 1.2])
                with c1:
                    st.markdown(f"""<div style="background:linear-gradient(145deg, #10141c, #0d1017);
                        padding:14px 16px; border-radius:12px;
                        border:1px solid {col}33; border-left:3px solid {col};">
                        <div style="color:#e6c87c; font-size:0.78rem; font-weight:700;">#{p['id']} {p['pair']}</div>
                        <div style="color:#e8edf5; font-size:1.05rem; font-weight:700; margin-top:4px;">
                        {p['direction']} <span style="color:#7d879c; font-size:0.85rem;">({p.get('grade','?')})</span></div></div>""",
                        unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""<div style="background:linear-gradient(145deg, #10141c, #0d1017);
                        padding:14px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.05);">
                        <div style="color:#7d879c; font-size:0.7rem;">P&L / R</div>
                        <div style="color:{'#7cd4a0' if pd_['pnl_usd'] >= 0 else '#f57a7a'};
                        font-size:1.05rem; font-weight:700;">${pd_['pnl_usd']:+,.2f}</div>
                        <div style="color:#a0aab8; font-size:0.85rem;">{pd_['r_multiple']:+.2f}R</div></div>""",
                        unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""<div style="background:linear-gradient(145deg, #10141c, #0d1017);
                        padding:14px 16px; border-radius:12px; border:1px solid rgba(255,255,255,0.05);">
                        <div style="color:#7d879c; font-size:0.7rem;">Current</div>
                        <div style="color:#e8edf5; font-size:1rem; font-weight:700;">
                        {fmt_price(pd_['current_price'], p['pair'])}</div>
                        <div style="color:#a0aab8; font-size:0.8rem;">
                        Entry: {fmt_price(p.get('entry'), p['pair'])}</div></div>""",
                        unsafe_allow_html=True)
                with c4:
                    st.markdown(f"""<div style="background:linear-gradient(145deg, #10141c, #0d1017);
                        padding:14px 16px; border-radius:12px; border:1px solid {col}33;">
                        <div style="color:#7d879c; font-size:0.7rem;">Status</div>
                        <div style="color:{col}; font-size:1rem; font-weight:700;">{icon} {m['state']}</div>
                        <div style="color:#a0aab8; font-size:0.78rem;">TP1%: {pd_['progress_to_tp1']:.0f}%</div></div>""",
                        unsafe_allow_html=True)
                with c5:
                    st.markdown(f"""<div style="background:linear-gradient(145deg, #10141c, #0d1017);
                        padding:14px 16px; border-radius:12px; border:1px solid {col}33;">
                        <div style="color:#7d879c; font-size:0.7rem;">Action</div>
                        <div style="color:#e8edf5; font-size:0.85rem;">{m['action']}</div></div>""",
                        unsafe_allow_html=True)
                if m.get("reversal_signals"):
                    st.markdown(f"""<div style="margin:6px 0; padding:8px 14px;
                        background:rgba(245,122,122,0.08); border-radius:10px;
                        border:1px solid rgba(245,122,122,0.2);">
                        <span style="color:#f57a7a; font-size:0.82rem;">
                        ⚠️ {', '.join(m['reversal_signals'])}</span></div>""",
                        unsafe_allow_html=True)
                flip_i = m.get("flip_info")
                if flip_i and flip_i.get("flip_signal"):
                    fi_color = ("#f57a7a" if flip_i["status"] == "STRONG_FLIP" else "#f5c87a")
                    st.markdown(f"""<div style="margin:6px 0; padding:10px 14px;
                        background:rgba(245,122,122,0.10); border-radius:10px;
                        border:1px solid {fi_color}44;">
                        <span style="color:{fi_color}; font-weight:700; font-size:0.9rem;">
                            🔀 انعكاس محتمل إلى {flip_i['flip_signal']} 
                            ({flip_i['confidence']:.0f}%)
                        </span>
                        <div style="color:#a0aab8; font-size:0.8rem; margin-top:4px;">
                            {' · '.join([t['icon'] + ' ' + t['name'] for t in flip_i['triggers'][:3]])}
                        </div>
                    </div>""", unsafe_allow_html=True)
                act1, act2, act3, act4, act5 = st.columns([1, 1, 1, 1, 1])
                with act1:
                    sug = m.get("suggested_sl")
                    if sug and abs(sug - p.get("stop_loss", sug)) > 1e-6:
                        if st.button(f"📌 نقل SL", width="stretch", key=f"appsl_{p['id']}"):
                            update_position_sl(p["id"], sug)
                            st.success("✅ تم"); st.rerun()
                    else:
                        st.button("📌 SL OK", width="stretch", disabled=True, key=f"appsl_d_{p['id']}")
                with act2:
                    if st.button("✅ Win", width="stretch", key=f"closew_{p['id']}"):
                        close_position_with_result(p["id"], "WIN"); st.rerun()
                with act3:
                    if st.button("❌ Loss", width="stretch", key=f"closel_{p['id']}"):
                        close_position_with_result(p["id"], "LOSS"); st.rerun()
                with act4:
                    if st.button("⏸️", width="stretch", key=f"hold_{p['id']}"):
                        st.toast(f"Hold"); st.rerun()
                with act5:
                    if st.button("🗑️", width="stretch", key=f"del_{p['id']}"):
                        close_open_position(p["id"]); st.rerun()
                st.markdown("<hr style='margin:14px 0; opacity:0.3;'>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🌍 Exposure</div>', unsafe_allow_html=True)
        exp = get_portfolio_exposure()
        if exp:
            ec = st.columns(min(len(exp), 6))
            for i, (cy, ex) in enumerate(sorted(exp.items())):
                n = ex["net"]
                if n > 0.5: cl = "#7cd4a0"; sn = "LONG"
                elif n < -0.5: cl = "#f57a7a"; sn = "SHORT"
                else: cl = "#f5c87a"; sn = "NEUTRAL"
                with ec[i % 6]:
                    st.markdown(f"""<div class="tool-card"><div class="tool-name">{cy}</div>
                        <div class="tool-value" style="color:{cl}; font-size:1.1rem;">{n:+.1f}</div>
                        <div class="tool-desc">{sn} · {ex['count']}</div></div>""",
                        unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ Clear All Positions", width="stretch", key="clr_pos"):
        st.session_state.open_positions = []; st.rerun()


with tab_ml:
    st.markdown('<div class="section-title">🎓 ML Calibration</div>', unsafe_allow_html=True)
    if not SKLEARN_AVAILABLE:
        st.error("⚠️ scikit-learn غير مثبت. pip install scikit-learn")
    else:
        l1, l2 = st.columns(2)
        l1.success("✅ scikit-learn")
        if XGBOOST_AVAILABLE: l2.success("✅ xgboost")
        else: l2.warning("⚠️ xgboost غير مثبت")
        bt = st.session_state.get("backtest_results")
        if bt and bt.get("ml_trades"):
            nt = len(bt["ml_trades"])
            st.success(f"✅ {nt} صفقة · {len(ML_FEATURE_NAMES)} feature")
        else:
            nt = 0
            st.warning("⚠️ اذهب إلى Backtest tab أولاً.")
        tc1, tc2, tc3 = st.columns(3)
        with tc1: ut = st.checkbox("🎯 Tuning", value=False, key="ut")
        with tc2: tm = st.selectbox("طريقة", ["randomized","grid"], index=0, key="tm", disabled=not ut)
        with tc3: ti = st.number_input("محاولات", 5, 100, 20, 5, key="ti", disabled=not ut or tm == "grid")
        tr1, tr2 = st.columns(2)
        with tr1:
            if st.button("🎓 Train All", width="stretch", disabled=(nt < ML_MIN_TRADES), key="train_ml"):
                with st.spinner("Training..."):
                    mp = train_ml_model(bt["ml_trades"], use_tuning=ut,
                                         tuning_mode=tm, tuning_n_iter=int(ti))
                    if "error" in mp: st.error(f"فشل: {mp['error']}")
                    else:
                        st.session_state.ml_model = mp
                        st.success(f"✅ {mp['model_name']} (AUC={mp['auc']:.3f})"); st.rerun()
        with tr2:
            if st.session_state.get("ml_model"):
                if st.button("🔄 Retrain", width="stretch", key="retr"):
                    with st.spinner("Retraining..."):
                        mp = train_ml_model(bt["ml_trades"], use_tuning=ut,
                                             tuning_mode=tm, tuning_n_iter=int(ti))
                        if "error" not in mp:
                            st.session_state.ml_model = mp; st.rerun()
        mp = st.session_state.get("ml_model")
        if mp:
            rows = []
            for name, d in mp.get("all_models", {}).items():
                if d.get("error"): rows.append({"Model": name, "AUC": "❌", "Acc": "-"})
                else:
                    bg = "🏆" if name == mp["model_name"] else ""
                    rows.append({"Model": f"{name} {bg}", "AUC": f"{d['auc']:.3f}",
                                 "Acc": f"{d['accuracy']*100:.1f}%"})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            pm1, pm2, pm3, pm4, pm5 = st.columns(5)
            pm1.metric("Model", mp["model_name"])
            pm2.metric("AUC", f"{mp['auc']:.3f}")
            pm3.metric("Accuracy", f"{mp['accuracy']*100:.1f}%")
            pm4.metric("F1", f"{mp['f1']:.3f}")
            pm5.metric("Samples", f"{mp['n_total']}")


with tab_flt:
    st.markdown('<div class="section-title">🎛️ Filters</div>', unsafe_allow_html=True)
    items = list(result["filter_results"].items())
    for r in range(0, len(items), 4):
        row = items[r:r+4]; cc = st.columns(4)
        for i, (n, info) in enumerate(row):
            p_ = info.get("pass", True); ic_ = "✅" if p_ else "❌"
            with cc[i]:
                st.markdown(f"""<div class="tool-card"><div class="tool-name">{n}</div>
                    <div class="tool-value">{ic_}</div>
                    <div class="tool-desc">{info.get('msg','')[:60]}</div></div>""",
                    unsafe_allow_html=True)
    if not result["all_filters_passed"]:
        st.error(f"🚫 **Block:** {result['filter_block_reason']}")


with tab_cht:
    st.markdown('<div class="section-title">📈 Chart</div>', unsafe_allow_html=True)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.04, row_heights=[0.60,0.20,0.20])
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
    if lv and lv.get("sl_level_price"):
        fig.add_hline(y=lv["sl_level_price"], row=1, col=1, line_dash="dash",
                      line_color="#f5c87a", opacity=0.8,
                      annotation_text=f"SL: {lv['sources']['sl']}",
                      annotation_position="left")
    if lv:
        for k, cl, lb in [("stop_loss","#f57a7a","SL"), ("target1","#7cd4a0","TP1"),
                          ("target2","#7cd4a0","TP2"), ("target3","#7cd4a0","TP3")]:
            fig.add_hline(y=lv[k], row=1, col=1, line_dash="dot",
                          line_color=cl, opacity=0.7, annotation_text=lb,
                          annotation_position="right")
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                             line=dict(color="#7cd4a0")), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                             line=dict(color="#7cd4a0")), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Sig",
                             line=dict(color="#f5c87a")), row=3, col=1)
    fig.update_layout(height=850, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0a0d13", plot_bgcolor="#0a0d13",
        font=dict(family="Inter", color="#c8d2e2"),
        legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
        margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, width="stretch")


with tab_cal:
    st.markdown('<div class="section-title">📅 Calendar</div>', unsafe_allow_html=True)
    if st.button("🔄 Update Calendar", width="stretch"):
        st.session_state.economic_events = get_fmp_economic_calendar()
    if st.session_state.economic_events:
        st.caption(event_risk_message(st.session_state.economic_events, sp_))
        rows = [{"Country": e.get("country",""), "Event": e.get("event",""),
                 "Impact": e.get("impact",""), "Date": e.get("date","")}
                for e in st.session_state.economic_events[:20]]
        if rows: st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


with tab_jrn:
    st.markdown('<div class="section-title">📔 Journal</div>', unsafe_allow_html=True)
    if not st.session_state.trade_journal:
        st.info("لا صفقات مسجلة.")
    else:
        jdf = pd.DataFrame(st.session_state.trade_journal)
        st.dataframe(jdf, hide_index=True, width="stretch")
        tt = len(jdf); ww = (jdf["outcome"] == "WIN").sum()
        ll = (jdf["outcome"] == "LOSS").sum()
        wr = (ww/tt*100) if tt > 0 else 0
        j1, j2, j3 = st.columns(3)
        j1.metric("Total", tt); j2.metric("WR", f"{wr:.1f}%")
        j3.metric("W/L", f"{ww}/{ll}")
    st.markdown("---")
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        if st.button("✅ WIN", width="stretch", key="lgw"):
            log_trade_result(result, "WIN"); st.rerun()
    with rc2:
        if st.button("❌ LOSS", width="stretch", key="lgl"):
            log_trade_result(result, "LOSS"); st.rerun()
    with rc3:
        if st.button("🗑️ Clear", width="stretch", key="clj"):
            st.session_state.trade_journal = []
            st.session_state.recent_results = []; st.rerun()


with tab_bt:
    st.markdown('<div class="section-title">🔬 Backtest + Monte Carlo</div>', unsafe_allow_html=True)
    if st.button("▶️ Run Backtest", width="stretch"):
        with st.spinner("Running..."):
            st.session_state.backtest_results = quick_backtest(sym, sp_)
        st.rerun()
    if st.session_state.backtest_results:
        bt = st.session_state.backtest_results
        if bt.get("error"): st.error(f"فشل: {bt['error']}")
        else:
            b1, b2, b3, b4, b5 = st.columns(5)
            b1.metric("Trades", bt["trades"]); b2.metric("WR", f"{bt['win_rate']:.1f}%")
            b3.metric("Total R", f"{bt['total_R']:.2f}")
            b4.metric("Expectancy", f"{bt['expectancy']:.3f}R")
            b5.metric("PF", f"{bt['profit_factor']:.2f}")
            mc = bt.get("monte_carlo")
            if mc:
                m1, m2, m3 = st.columns(3)
                m1.metric("Mean", f"{mc['mean_final']:.2f}R")
                m2.metric("Median", f"{mc['median_final']:.2f}R")
                m3.metric("Prob Profit", f"{mc['prob_profit']:.1f}%")


st.markdown(f"""
<div class="footer-style">
    ▲ BLACK PYRAMID {APP_VERSION} ▲<br>
    Nearest Level SL · Flip Detection · Live Monitor · Hyper-Tuned ML
</div>
""", unsafe_allow_html=True)