# ============================================================
# BLACK PYRAMID v2003 – HIERARCHICAL PRECISION ENGINE
# Full Integration: 7 Layers + All Pairs + 1-3 Trades/Day
# ============================================================

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import requests
import json
import time
from typing import Dict, Tuple, List, Optional

# ============================================================
# Page setup
# ============================================================

st.set_page_config(
    page_title="Black Pyramid v2003 - Precision",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Visual identity
# ============================================================

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
* { font-family: 'Inter', sans-serif; }
.main-title, .signal-text, .price-value { font-family: 'Orbitron', sans-serif !important; letter-spacing: 3px; }
.main-subtitle, .price-label, .signal-confidence, .footer { font-family: 'Inter', sans-serif !important; letter-spacing: 1px; }
html, body, .stApp { background: #0a0a0a !important; margin: 0; padding: 0; }
.stApp { position: relative; background: #0a0a0a; min-height: 100vh; }
.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: url('https://raw.githubusercontent.com/kamelehab04-dotcom/gold-streamlit/main/file_00000000a364820aa4218d02627011f1.png');
    background-size: cover;
    background-position: center;
    opacity: 0.25;
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 20%, rgba(255,215,0,0.03) 0%, transparent 50%),
                 radial-gradient(ellipse at 70% 80%, rgba(255,215,0,0.02) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
    animation: bgPulse 10s ease-in-out infinite;
}
@keyframes bgPulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
.main-header, .price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone,
.target-zone, .stop-loss-level, .reversal-alert, .news-card, .explanation-box,
.stButton button, .stSelectbox, .stDataFrame, .stMetric, .stPlotlyChart, .stTabs {
    position: relative;
    z-index: 1;
}
.css-1d391kg, .css-1d391kg * {
    background: rgba(10,10,10,0.85);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255,215,0,0.05);
}
.main-header {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 10px 25px;
    min-height: 55px;
    background: rgba(0,0,0,0.5);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    margin-bottom: 15px;
    border: 1px solid rgba(255,215,0,0.08);
}
.main-header .main-title {
    font-size: 1.2rem;
    color: #ffd700;
    font-weight: 700;
    letter-spacing: 2px;
}
.main-header .main-subtitle {
    font-size: 0.55rem;
    color: #666;
    letter-spacing: 1px;
}
.price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone,
.target-zone, .stop-loss-level, .reversal-alert {
    background: rgba(10,10,10,0.75);
    backdrop-filter: blur(6px);
    border: 1px solid rgba(255,215,0,0.10);
    border-radius: 12px;
    box-shadow: 0 4px 30px rgba(0,0,0,0.5);
}
.price-value { color: #fff; }
.price-label { color: #888; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 2px; }
.signal-box { border: 2px solid #ffd700; }
.suggested-trade { border: 2px solid #00ff88; background: rgba(0,10,5,0.80); }
.target-zone { border-left: 4px solid #ffd700; background: rgba(255,215,0,0.04); padding: 8px 12px; margin: 4px 0; }
.target-zone:last-child { border-left-color: #00ff88; }
.stop-loss-level { border-left: 4px solid #ff4444; background: rgba(255,68,68,0.04); padding: 8px 12px; margin: 4px 0; }
.entry-zone { border-left: 4px solid #00ff88; background: rgba(0,255,136,0.04); padding: 8px 12px; margin: 4px 0; }
.trade-row { border-left: 4px solid #ffd700; padding: 10px 15px; margin: 5px 0; }
.footer {
    text-align: center;
    padding: 15px;
    color: #444;
    font-size: 0.65rem;
    border-top: 1px solid rgba(255,215,0,0.05);
    margin-top: 30px;
    letter-spacing: 1px;
}
.footer .brand { color: #ffd700; font-weight: 600; }
.stButton button {
    background: linear-gradient(135deg, #ffd700 0%, #d4a800 100%) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 8px 16px !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255,215,0,0.2);
}
.explanation-box {
    background: rgba(10,10,10,0.80);
    border: 1px solid rgba(255,215,0,0.05);
    border-radius: 10px;
    padding: 15px;
    margin: 8px 0;
    color: #bbb;
    font-size: 0.9rem;
    line-height: 1.6;
}
.news-card {
    background: rgba(10,10,10,0.65);
    border-left: 3px solid #ffd700;
    border-radius: 8px;
    padding: 10px 15px;
    margin: 5px 0;
}
.news-title { color: #eee; font-weight: 500; font-size: 0.9rem; }
.news-date { color: #666; font-size: 0.7rem; }
.reversal-alert {
    border: 1px solid #ff4444;
    background: rgba(255,68,68,0.04);
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 8px;
    font-size: 0.85rem;
}
.pattern-badge {
    display: inline-block;
    background: rgba(255,215,0,0.08);
    border: 1px solid rgba(255,215,0,0.12);
    border-radius: 16px;
    padding: 3px 12px;
    margin: 2px;
    font-size: 0.7rem;
    color: #ffd700;
}
.tbs-badge {
    display: inline-block;
    background: rgba(255,136,0,0.10);
    border: 1px solid rgba(255,136,0,0.15);
    border-radius: 16px;
    padding: 3px 12px;
    margin: 2px;
    font-size: 0.7rem;
    color: #ff8800;
    font-weight: bold;
}
.dxy-aligned {
    display: inline-block;
    background: rgba(0,255,136,0.10);
    border: 1px solid rgba(0,255,136,0.20);
    border-radius: 16px;
    padding: 3px 12px;
    margin: 2px;
    font-size: 0.7rem;
    color: #00ff88;
    font-weight: bold;
}
.dxy-misaligned {
    display: inline-block;
    background: rgba(255,68,68,0.10);
    border: 1px solid rgba(255,68,68,0.20);
    border-radius: 16px;
    padding: 3px 12px;
    margin: 2px;
    font-size: 0.7rem;
    color: #ff4444;
    font-weight: bold;
}
.regime-badge {
    display: inline-block;
    border-radius: 16px;
    padding: 3px 12px;
    margin: 2px;
    font-size: 0.7rem;
    font-weight: bold;
}
.regime-trending {
    background: rgba(0,255,136,0.15);
    color: #00ff88;
    border: 1px solid rgba(0,255,136,0.20);
}
.regime-ranging {
    background: rgba(255,170,0,0.15);
    color: #ffaa00;
    border: 1px solid rgba(255,170,0,0.20);
}
.regime-volatile {
    background: rgba(255,68,68,0.15);
    color: #ff4444;
    border: 1px solid rgba(255,68,68,0.20);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# Header
# ============================================================

st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">
            <span class="pyramid-icon">▲</span> BLACK PYRAMID v2003 <span class="pyramid-icon">▲</span>
        </div>
        <div class="main-subtitle">7 Layers • All Pairs • Precision • 1-3 Trades/Day</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# API Keys & Configuration
# ============================================================

GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"
BACKTEST_LOOKBACK = 500
MIN_CONFIDENCE = 42
BUY_THRESHOLD = 8
SELL_THRESHOLD = -8
COOLDOWN_BARS = 4
MAX_TRADES_PER_DAY = 3
MAX_OPEN_RISK = 0.05
RISK_PER_TRADE = 0.02

# ============================================================
# ALL PAIRS – FULL LIST (استرداد جميع الأزواج)
# ============================================================

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
    "ETH/USD (Ethereum)": "ETH-USD"
}

# ============================================================
# Session state
# ============================================================

if "all_signals" not in st.session_state:
    st.session_state.all_signals = None
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
if "show_indicators" not in st.session_state:
    st.session_state.show_indicators = True
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "active_trades" not in st.session_state:
    st.session_state.active_trades = {}
if "closed_trades" not in st.session_state:
    st.session_state.closed_trades = []
if "trade_stats" not in st.session_state:
    st.session_state.trade_stats = {"day": None, "count": 0, "last_closed_bar": {}}

# ============================================================
# DATA RETRIEVAL
# ============================================================

@st.cache_data(ttl=5)
def get_spot_price(symbol="GC=F"):
    if symbol == "GC=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data['price']), float(data['change_percent'])
        except:
            pass
    if symbol == "SI=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAG/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data['price']), float(data['change_percent'])
        except:
            pass
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="5m")
        if not data.empty:
            last = data.iloc[-1]
            first = data.iloc[0]
            change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
            return float(last['Close']), float(change)
    except:
        pass
    return None, None

@st.cache_data(ttl=300)
def get_historical_data(symbol, period="1mo", interval="1h", max_retries=3):
    alt = {
        "GC=F": ["XAUUSD=X", "GOLD"],
        "SI=F": ["XAGUSD=X", "SILVER"],
        "DX-Y.NYB": ["DX=F", "DXY"],
        "BTC-USD": ["BTCUSD=X"],
        "ETH-USD": ["ETHUSD=X"]
    }
    symbols = [symbol] + alt.get(symbol, [])
    for attempt in range(max_retries):
        for sym in symbols:
            try:
                ticker = yf.Ticker(sym)
                df = ticker.history(period=period, interval=interval)
                if not df.empty:
                    df.columns = [c.lower() for c in df.columns]
                    return df
            except:
                continue
        time.sleep(2)
    return None

def get_market_status():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    wd = now.weekday()
    open_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
    close_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
    if wd == 5:
        return "CLOSED", "Weekend", open_time + timedelta(days=1), close_time
    if wd == 6:
        if now >= open_time:
            return "OPEN", "Market Open (Sunday)", close_time, close_time
        else:
            return "CLOSED", "Waiting for Open", open_time, close_time
    if 0 <= wd <= 3:
        if close_time <= now < open_time:
            return "CLOSED", "Daily Break", open_time, close_time
        if now < close_time:
            return "OPEN", "Market Open", close_time, close_time
        else:
            return "OPEN", "Market Open", close_time + timedelta(days=1), close_time
    if wd == 4:
        if now < close_time:
            return "OPEN", "Market Open (Friday)", close_time, close_time
        else:
            return "CLOSED", "Weekend", open_time + timedelta(days=2), close_time
    return "UNKNOWN", "Unknown", None, None

def time_remaining(dt):
    if dt is None:
        return "N/A"
    diff = dt - datetime.now(pytz.timezone('US/Eastern'))
    if diff.total_seconds() < 0:
        return "Expired"
    h = int(diff.total_seconds() // 3600)
    m = int((diff.total_seconds() % 3600) // 60)
    return f"{h}h {m}m"

# ============================================================
# INDICATORS
# ============================================================

def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calc_macd(data):
    e12 = data.ewm(span=12, adjust=False).mean()
    e26 = data.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal, macd - signal

def calc_bollinger(data, period=20, std=2):
    sma = data.rolling(window=period).mean()
    s = data.rolling(window=period).std()
    return sma + std*s, sma, sma - std*s

def calc_adx_correct(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=df.index, dtype=float
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=df.index, dtype=float
    )
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False, min_periods=period).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False, min_periods=period).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    return adx.fillna(0), plus_di.fillna(0), minus_di.fillna(0)

def calc_ichimoku(df):
    high, low, close = df['high'], df['low'], df['close']
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    chikou = close.shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou

def calc_vwap_anchor(df, anchor=None):
    if anchor is None:
        return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
    else:
        idx = df.index.get_loc(anchor) if anchor in df.index else 0
        vol = df['volume'].iloc[idx:].copy()
        price = df['close'].iloc[idx:].copy()
        return (vol * price).cumsum() / vol.cumsum()

def calc_mfi(df, period=14):
    typical = (df['high'] + df['low'] + df['close']) / 3
    flow = typical * df['volume']
    pos = flow.where(typical > typical.shift(), 0).rolling(period).sum()
    neg = flow.where(typical < typical.shift(), 0).rolling(period).sum()
    return 100 - (100 / (1 + pos / neg))

# ============================================================
# SMC / ICT
# ============================================================

def find_swings(df, order=5):
    highs = df['high'].values
    lows = df['low'].values
    peaks = []
    troughs = []
    for i in range(order, len(df) - order):
        if all(highs[i] > highs[i-j] for j in range(1, order+1)) and all(highs[i] > highs[i+j] for j in range(1, order+1)):
            peaks.append((i, highs[i]))
        if all(lows[i] < lows[i-j] for j in range(1, order+1)) and all(lows[i] < lows[i+j] for j in range(1, order+1)):
            troughs.append((i, lows[i]))
    return peaks, troughs

def detect_liquidity_levels(df, lookback=50):
    return df['high'].rolling(lookback).max(), df['low'].rolling(lookback).min()

def detect_smc_ict(df):
    df = df.copy()
    df['ob_bullish'] = False
    df['ob_bearish'] = False
    df['fvg_bullish'] = False
    df['fvg_bearish'] = False
    df['liquidity_sweep_bullish'] = False
    df['liquidity_sweep_bearish'] = False
    df['bos_bullish'] = False
    df['bos_bearish'] = False
    df['mss_bullish'] = False
    df['mss_bearish'] = False

    for i in range(3, len(df)):
        if df['close'].iloc[i] > df['open'].iloc[i]:
            body = df['close'].iloc[i] - df['open'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                df.loc[df.index[i-1], 'ob_bullish'] = True
        if df['close'].iloc[i] < df['open'].iloc[i]:
            body = df['open'].iloc[i] - df['close'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                df.loc[df.index[i-1], 'ob_bearish'] = True

    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bullish'] = True
        if df['high'].iloc[i] < df['low'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bearish'] = True

    for i in range(10, len(df)):
        recent_lows = df['low'].iloc[i-10:i].tolist()
        if df['low'].iloc[i] < min(recent_lows[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bullish'] = True
        recent_highs = df['high'].iloc[i-10:i].tolist()
        if df['high'].iloc[i] > max(recent_highs[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bearish'] = True

    for i in range(5, len(df)):
        if df['close'].iloc[i] > df['high'].iloc[i-5:i].max():
            df.loc[df.index[i], 'bos_bullish'] = True
        if df['close'].iloc[i] < df['low'].iloc[i-5:i].min():
            df.loc[df.index[i], 'bos_bearish'] = True

    for i in range(3, len(df)):
        if df['bos_bearish'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[i-2:i].max():
            df.loc[df.index[i], 'mss_bullish'] = True
        if df['bos_bullish'].iloc[i-1] and df['close'].iloc[i] < df['low'].iloc[i-2:i].min():
            df.loc[df.index[i], 'mss_bearish'] = True

    return df

# ============================================================
# TBS (Turtle Body Soup)
# ============================================================

def detect_tbs_correct(df, lookback=20, body_mult=1.5):
    if len(df) < lookback + 2:
        return None, None, None, None
    last = df.iloc[-1]
    lookback_high = df['high'].iloc[-lookback-1:-1].max()
    lookback_low = df['low'].iloc[-lookback-1:-1].min()
    avg_body = abs(df['close'] - df['open']).iloc[-lookback-1:-1].mean()
    current_body = abs(last['close'] - last['open'])
    if current_body < avg_body * body_mult:
        return None, None, None, None
    if last['high'] > lookback_high and last['close'] < lookback_high:
        return "BEARISH", last['close'], last['high'], lookback_high
    elif last['low'] < lookback_low and last['close'] > lookback_low:
        return "BULLISH", last['close'], last['low'], lookback_low
    return None, None, None, None

# ============================================================
# DXY
# ============================================================

def get_dxy_correlation(df_pair, df_dxy, lookback=50):
    if df_pair is None or df_dxy is None:
        return 0.0
    if len(df_pair) < lookback or len(df_dxy) < lookback:
        return 0.0
    pair = df_pair[['close']].copy()
    dxy = df_dxy[['close']].copy()
    pair_ret = pair['close'].pct_change()
    dxy_ret = dxy['close'].pct_change()
    combined = pd.concat([pair_ret, dxy_ret], axis=1, join='inner').dropna()
    if len(combined) < lookback:
        return 0.0
    corr = combined.iloc[-lookback:, 0].corr(combined.iloc[-lookback:, 1])
    return float(corr) if not pd.isna(corr) else 0.0

def apply_dxy_filter(signal, net_score, dxy_signal, correlation):
    adjustment = 0
    status = "NEUTRAL"
    if dxy_signal is None or dxy_signal == "WAIT" or signal == "WAIT":
        return net_score, status, 0
    if abs(correlation) < 0.30:
        return net_score, "WEAK_CORRELATION", 0
    if correlation <= -0.60:
        if (signal == "BUY" and dxy_signal == "SELL") or (signal == "SELL" and dxy_signal == "BUY"):
            adjustment = 5
            status = "STRONGLY_ALIGNED"
        else:
            adjustment = -6
            status = "MISALIGNED"
    elif correlation >= 0.60:
        if signal == dxy_signal:
            adjustment = 5
            status = "STRONGLY_ALIGNED"
        else:
            adjustment = -6
            status = "MISALIGNED"
    else:
        if correlation < 0:
            aligned = (signal == "BUY" and dxy_signal == "SELL") or (signal == "SELL" and dxy_signal == "BUY")
        else:
            aligned = signal == dxy_signal
        adjustment = 2 if aligned else -3
        status = "ALIGNED" if aligned else "MISALIGNED"
    return net_score + adjustment, status, adjustment

# ============================================================
# ORIGINAL SIGNAL ENGINE (v2003)
# ============================================================

def detect_regime(df):
    last = df.iloc[-1]
    adx = last['adx'] if 'adx' in df.columns else 20
    ema20 = last['ema20'] if 'ema20' in df.columns else df['close'].iloc[-1]
    ema50 = last['ema50'] if 'ema50' in df.columns else df['close'].iloc[-1]
    atr = last['atr'] if 'atr' in df.columns else 10
    atr_ma = df['atr'].iloc[-20:].mean() if 'atr' in df.columns else atr
    regime = "NEUTRAL"
    if adx > 25 and abs(ema20 - ema50) / ema50 > 0.01:
        regime = "TRENDING"
    elif adx < 20:
        regime = "RANGING"
    if atr > atr_ma * 1.5:
        regime = "HIGH_VOLATILITY" if regime == "NEUTRAL" else regime + "_HIGH_VOL"
    elif atr < atr_ma * 0.7:
        regime = "LOW_VOLATILITY" if regime == "NEUTRAL" else regime + "_LOW_VOL"
    return regime

def mtf_analysis(df, symbol):
    timeframes = ['15m', '1h', '4h']
    results = []
    for tf in timeframes:
        try:
            data = get_historical_data(symbol, period="5d", interval=tf)
            if data is None or len(data) < 50:
                continue
            rsi = calc_rsi(data['close']).iloc[-1]
            ema20 = data['close'].ewm(20).mean().iloc[-1]
            ema50 = data['close'].ewm(50).mean().iloc[-1]
            trend = "NEUTRAL"
            if ema20 > ema50 and rsi > 50:
                trend = "BULLISH"
            elif ema20 < ema50 and rsi < 50:
                trend = "BEARISH"
            last = data.iloc[-1]
            candle = "BULLISH" if last['close'] > last['open'] else "BEARISH"
            results.append({
                "timeframe": tf,
                "trend": trend,
                "rsi": rsi,
                "candle": candle
            })
        except:
            continue
    buy = sum(1 for r in results if r['trend'] == "BULLISH")
    sell = sum(1 for r in results if r['trend'] == "BEARISH")
    if buy > sell:
        consensus = "BUY"
        count = buy - sell
    elif sell > buy:
        consensus = "SELL"
        count = sell - buy
    else:
        consensus = "NEUTRAL"
        count = 0
    return consensus, count, results

def generate_signal_v2003(df, symbol, dxy_signal=None, dxy_correlation=0.0):
    if df is None or len(df) < 100:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, (None,None,None,None)

    df['ema20'] = df['close'].ewm(20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(50, adjust=False).mean()
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
    tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(df)
    df['tenkan'] = tenkan
    df['kijun'] = kijun
    df['senkou_a'] = senkou_a
    df['senkou_b'] = senkou_b
    df['chikou'] = chikou
    df['mfi'] = calc_mfi(df)
    df['vwap'] = calc_vwap_anchor(df)

    df_smc = detect_smc_ict(df)
    last_smc = df_smc.iloc[-1]

    tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs_correct(df)
    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)

    regime = detect_regime(df)
    mtf_consensus, mtf_count, mtf_details = mtf_analysis(df, symbol)

    last = df.iloc[-1]
    current_price = last['close']

    factors = {
        "structure": 0.0, "liquidity": 0.0, "smc": 0.0, "mtf": 0.0,
        "dxy": 0.0, "momentum": 0.0, "volatility": 0.0, "pattern": 0.0, "volume": 0.0
    }
    details = {}

    if last_smc.get('bos_bullish', False) or last_smc.get('mss_bullish', False):
        factors['structure'] += 25.0; details['Structure'] = "Bullish BOS/MSS"
    elif last_smc.get('bos_bearish', False) or last_smc.get('mss_bearish', False):
        factors['structure'] -= 25.0; details['Structure'] = "Bearish BOS/MSS"
    else: details['Structure'] = "Neutral"

    if last_smc.get('liquidity_sweep_bullish', False):
        factors['liquidity'] += 20.0; details['Liquidity'] = "Buy-side sweep"
    elif last_smc.get('liquidity_sweep_bearish', False):
        factors['liquidity'] -= 20.0; details['Liquidity'] = "Sell-side sweep"
    else: details['Liquidity'] = "No sweep"

    if last_smc.get('ob_bullish', False) or last_smc.get('fvg_bullish', False):
        factors['smc'] += 20.0; details['SMC'] = "Bullish OB/FVG"
    elif last_smc.get('ob_bearish', False) or last_smc.get('fvg_bearish', False):
        factors['smc'] -= 20.0; details['SMC'] = "Bearish OB/FVG"
    else: details['SMC'] = "No SMC signal"

    if mtf_consensus == "BUY":
        factors['mtf'] += 15.0; details['MTF'] = f"Bullish ({mtf_count})"
    elif mtf_consensus == "SELL":
        factors['mtf'] -= 15.0; details['MTF'] = f"Bearish ({mtf_count})"
    else: details['MTF'] = "Neutral"

    if dxy_signal is not None and dxy_signal != "WAIT":
        raw_direction = "BUY" if factors['structure'] + factors['liquidity'] + factors['smc'] + factors['mtf'] > 0 else "SELL"
        if raw_direction == "WAIT":
            raw_direction = "BUY" if factors['structure'] > 0 else "SELL"
        adjusted, status, adj = apply_dxy_filter(raw_direction, 0, dxy_signal, dxy_correlation)
        factors['dxy'] = float(adj); details['DXY'] = f"{status} (تعديل: {adj})"
    else: details['DXY'] = "No DXY"

    if last['rsi'] < 30:
        factors['momentum'] += 10.0; details['Momentum'] = f"Oversold RSI={last['rsi']:.1f}"
    elif last['rsi'] > 70:
        factors['momentum'] -= 10.0; details['Momentum'] = f"Overbought RSI={last['rsi']:.1f}"
    else:
        factors['momentum'] += (50 - last['rsi']) / 10.0; details['Momentum'] = f"RSI Neutral {last['rsi']:.1f}"
    if last['macd'] > last['macd_signal']: factors['momentum'] += 5.0
    else: factors['momentum'] -= 5.0

    atr_ratio = last['atr'] / df['atr'].iloc[-20:].mean() if df['atr'].iloc[-20:].mean() > 0 else 1.0
    if atr_ratio > 1.5:
        factors['volatility'] -= 10.0; details['Volatility'] = "High"
    elif atr_ratio < 0.7:
        factors['volatility'] += 5.0; details['Volatility'] = "Low"
    else: details['Volatility'] = "Normal"

    if tbs_type == "BULLISH":
        factors['pattern'] += 20.0; details['Pattern'] = "TBS BUY"
    elif tbs_type == "BEARISH":
        factors['pattern'] -= 20.0; details['Pattern'] = "TBS SELL"
    else: details['Pattern'] = "No TBS"

    if last['mfi'] < 20:
        factors['volume'] += 5.0; details['Volume'] = f"MFI Oversold {last['mfi']:.1f}"
    elif last['mfi'] > 80:
        factors['volume'] -= 5.0; details['Volume'] = f"MFI Overbought {last['mfi']:.1f}"
    else: details['Volume'] = f"MFI Neutral {last['mfi']:.1f}"

    total_score = sum(factors.values())

    if total_score >= BUY_THRESHOLD:
        signal = "BUY"; confidence = min(90, 50 + total_score * 0.5)
    elif total_score <= SELL_THRESHOLD:
        signal = "SELL"; confidence = min(90, 50 + abs(total_score) * 0.5)
    else:
        signal = "WAIT"; confidence = 50 + total_score * 0.2

    confidence = max(0, min(100, confidence))
    if "HIGH_VOL" in regime: confidence *= 0.9
    elif "LOW_VOL" in regime: confidence *= 1.1

    stop_loss = None
    entry_price = current_price
    targets = {}

    if signal in ["BUY", "SELL"] and confidence >= MIN_CONFIDENCE:
        atr_val = last['atr'] if not pd.isna(last['atr']) else 10.0
        if signal == "BUY":
            struct_low = df['low'].iloc[-10:].min()
            ob_low = df['low'].iloc[-5:].min()
            stop_loss = min(struct_low, ob_low, current_price - atr_val * 1.5)
            stop_loss = max(stop_loss, current_price - atr_val * 3)
        else:
            struct_high = df['high'].iloc[-10:].max()
            ob_high = df['high'].iloc[-5:].max()
            stop_loss = max(struct_high, ob_high, current_price + atr_val * 1.5)
            stop_loss = min(stop_loss, current_price + atr_val * 3)

        risk = abs(entry_price - stop_loss)
        if risk < atr_val * 0.3:
            stop_loss = entry_price - atr_val * 0.5 if signal == "BUY" else entry_price + atr_val * 0.5
            risk = atr_val * 0.5

        if signal == "BUY":
            targets = {'target1': entry_price + risk * 1.0, 'target2': entry_price + risk * 1.5,
                       'target3': entry_price + risk * 2.0, 'risk_reward': 2.0}
        else:
            targets = {'target1': entry_price - risk * 1.0, 'target2': entry_price - risk * 1.5,
                       'target3': entry_price - risk * 2.0, 'risk_reward': 2.0}

    return signal, confidence, total_score, details, factors, regime, mtf_consensus, mtf_count, stop_loss, entry_price, targets, tbs_info

# ============================================================
# HIERARCHICAL LAYERS (المضافة الجديدة)
# ============================================================

def get_swing_levels(df):
    if df is None or len(df) < 20:
        return df['high'].max(), df['low'].min()
    peaks, troughs = find_swings(df, order=5)
    if peaks:
        swing_high = df['high'].iloc[peaks[-1][0]] if peaks else df['high'].max()
    else:
        swing_high = df['high'].max()
    if troughs:
        swing_low = df['low'].iloc[troughs[-1][0]] if troughs else df['low'].min()
    else:
        swing_low = df['low'].min()
    return swing_high, swing_low

def calculate_fib_levels(swing_high, swing_low):
    diff = swing_high - swing_low
    if diff == 0:
        return {}
    return {
        'fib_236': swing_high - diff * 0.236,
        'fib_382': swing_high - diff * 0.382,
        'fib_500': swing_high - diff * 0.500,
        'fib_618': swing_high - diff * 0.618,
        'fib_786': swing_high - diff * 0.786,
    }

def get_news_impact(symbol):
    """محاكاة الأخبار – استبدلها بـ API حقيقي"""
    return None

# ---- Layer 1: Market Regime ----
def layer_regime(df_4h):
    if df_4h is None or len(df_4h) < 50:
        return "NEUTRAL", "بيانات غير كافية"
    last = df_4h.iloc[-1]
    adx = last['adx'] if 'adx' in df_4h.columns else 20
    atr = last['atr'] if 'atr' in df_4h.columns else 10
    atr_ma = df_4h['atr'].iloc[-20:].mean() if 'atr' in df_4h.columns else atr
    ema20 = last['ema20'] if 'ema20' in df_4h.columns else df_4h['close'].iloc[-1]
    ema50 = last['ema50'] if 'ema50' in df_4h.columns else df_4h['close'].iloc[-1]
    bb_width = (last['bb_upper'] - last['bb_lower']) / last['bb_middle'] if all(k in df_4h.columns for k in ['bb_upper','bb_lower','bb_middle']) else 0.05

    if adx > 25 and abs(ema20 - ema50) / ema50 > 0.01:
        return "TRENDING", "اتجاه واضح (ADX مرتفع)"
    elif adx < 20 and bb_width < 0.05:
        return "RANGING", "سوق عرضي (ADX منخفض وBB ضيق)"
    elif adx > 25 and atr > atr_ma * 1.5:
        return "HIGH_VOL", "تقلب مرتفع"
    elif adx < 20 and atr < atr_ma * 0.7:
        return "LOW_VOL", "تقلب منخفض - انتظار اختراق"
    return "NEUTRAL", "حالة سوق غير محددة"

# ---- Layer 2: 4H Bias (محسّن) ----
def layer_4h_bias_advanced(df_4h):
    if df_4h is None or len(df_4h) < 50:
        return "NEUTRAL", "بيانات 4H غير كافية"
    last = df_4h.iloc[-1]
    price = last['close']
    
    ema20 = last['ema20'] if 'ema20' in df_4h.columns else price
    ema50 = last['ema50'] if 'ema50' in df_4h.columns else price
    ema200 = last['ema200'] if 'ema200' in df_4h.columns else price
    
    in_cloud = False
    if all(k in df_4h.columns for k in ['senkou_a','senkou_b']):
        if price > min(last['senkou_a'], last['senkou_b']) and price < max(last['senkou_a'], last['senkou_b']):
            in_cloud = True
    
    adx = last['adx'] if 'adx' in df_4h.columns else 0
    plus_di = last['plus_di'] if 'plus_di' in df_4h.columns else 0
    minus_di = last['minus_di'] if 'minus_di' in df_4h.columns else 0
    
    bos_bull = last.get('bos_bullish', False)
    bos_bear = last.get('bos_bearish', False)
    mss_bull = last.get('mss_bullish', False)
    mss_bear = last.get('mss_bearish', False)
    
    bullish_points = 0
    bearish_points = 0
    
    if ema20 > ema50: bullish_points += 1
    else: bearish_points += 1
    if ema50 > ema200: bullish_points += 1
    else: bearish_points += 1
    if not in_cloud:
        if price > max(last['senkou_a'], last['senkou_b']): bullish_points += 1
        elif price < min(last['senkou_a'], last['senkou_b']): bearish_points += 1
    if adx >= 25:
        if plus_di > minus_di: bullish_points += 1
        elif minus_di > plus_di: bearish_points += 1
    if bos_bull or mss_bull: bullish_points += 1
    if bos_bear or mss_bear: bearish_points += 1
    
    if bullish_points >= 3 and bullish_points > bearish_points:
        return "BULLISH", f"صاعد ({bullish_points}/{bullish_points+bearish_points})"
    elif bearish_points >= 3 and bearish_points > bullish_points:
        return "BEARISH", f"هابط ({bearish_points}/{bullish_points+bearish_points})"
    else:
        return "NEUTRAL", f"محايد ({bullish_points}/{bearish_points})"

# ---- Layer 3: 1H Confirmation (محسّن) ----
def layer_1h_confirmation_advanced(df_1h, bias):
    if df_1h is None or len(df_1h) < 50 or bias == "NEUTRAL":
        return False, "الـ Bias محايد أو بيانات غير كافية"
    last = df_1h.iloc[-1]
    price = last['close']
    
    ema20 = last['ema20'] if 'ema20' in df_1h.columns else price
    ema50 = last['ema50'] if 'ema50' in df_1h.columns else price
    
    if bias == "BULLISH" and ema20 < ema50:
        return False, "1H يخالف الاتجاه (EMA20 < EMA50)"
    if bias == "BEARISH" and ema20 > ema50:
        return False, "1H يخالف الاتجاه (EMA20 > EMA50)"
    
    if all(k in df_1h.columns for k in ['macd','macd_signal']):
        if bias == "BULLISH" and last['macd'] < last['macd_signal']:
            return False, "1H MACD سلبي"
        if bias == "BEARISH" and last['macd'] > last['macd_signal']:
            return False, "1H MACD إيجابي"
    
    adx = last['adx'] if 'adx' in df_1h.columns else 0
    plus_di = last['plus_di'] if 'plus_di' in df_1h.columns else 0
    minus_di = last['minus_di'] if 'minus_di' in df_1h.columns else 0
    
    bos_bull = last.get('bos_bullish', False)
    bos_bear = last.get('bos_bearish', False)
    mss_bull = last.get('mss_bullish', False)
    mss_bear = last.get('mss_bearish', False)
    
    if adx < 25:
        if bias == "BULLISH" and not (bos_bull or mss_bull):
            return False, "ADX ضعيف ولا يوجد BOS/MSS صاعد"
        if bias == "BEARISH" and not (bos_bear or mss_bear):
            return False, "ADX ضعيف ولا يوجد BOS/MSS هابط"
    else:
        if bias == "BULLISH" and plus_di < minus_di:
            return False, "ADX قوي لكن -DI > +DI (اتجاه هابط)"
        if bias == "BEARISH" and minus_di < plus_di:
            return False, "ADX قوي لكن +DI > -DI (اتجاه صاعد)"
    
    return True, "1H مؤكد للاتجاه"

# ---- Layer 4: 15M Trigger (محسّن) ----
def layer_15m_trigger_advanced(df_15m, bias):
    if df_15m is None or len(df_15m) < 30 or bias == "NEUTRAL":
        return False, "لا يوجد Trigger", None
    
    last = df_15m.iloc[-1]
    price = last['close']
    
    triggers = []
    
    if bias == "BULLISH":
        if last.get('liquidity_sweep_bullish', False) and (last.get('mss_bullish', False) or last.get('bos_bullish', False)):
            if last.get('fvg_bullish', False) or last.get('ob_bullish', False):
                triggers.append(("Liquidity Sweep + FVG/OB", price))
    else:
        if last.get('liquidity_sweep_bearish', False) and (last.get('mss_bearish', False) or last.get('bos_bearish', False)):
            if last.get('fvg_bearish', False) or last.get('ob_bearish', False):
                triggers.append(("Liquidity Sweep + FVG/OB", price))
    
    body = abs(last['close'] - last['open'])
    avg_body = abs(df_15m['close'] - df_15m['open']).rolling(20).mean().iloc[-1]
    if body > avg_body * 1.5:
        if bias == "BULLISH" and last['close'] > last['open']:
            triggers.append(("شمعة تأكيد صاعدة", price))
        elif bias == "BEARISH" and last['close'] < last['open']:
            triggers.append(("شمعة تأكيد هابطة", price))
    
    if bias == "BULLISH":
        if last['high'] > df_15m['high'].iloc[-5:-1].max():
            triggers.append(("اختراق قمة", last['high']))
    else:
        if last['low'] < df_15m['low'].iloc[-5:-1].min():
            triggers.append(("اختراق قاع", last['low']))
    
    if triggers:
        for trigger_type, trigger_price in triggers:
            if "Liquidity" in trigger_type:
                return True, f"Trigger: {trigger_type}", trigger_price
        for trigger_type, trigger_price in triggers:
            if "تأكيد" in trigger_type:
                return True, f"Trigger: {trigger_type}", trigger_price
        return True, f"Trigger: {triggers[0][0]}", triggers[0][1]
    
    return False, "لا يوجد Trigger مناسب", None

# ---- Layer 5: Price Location (محسّن) ----
def layer_price_location_advanced(df_15m, symbol, bias):
    if df_15m is None or len(df_15m) < 30:
        return False, "بيانات غير كافية", None
    
    last = df_15m.iloc[-1]
    price = last['close']
    
    swing_high, swing_low = get_swing_levels(df_15m)
    fibs = calculate_fib_levels(swing_high, swing_low)
    if not fibs:
        return False, "لا يمكن حساب Fibonacci", None
    
    fib_382 = fibs['fib_382']
    fib_618 = fibs['fib_618']
    fib_500 = fibs['fib_500']
    
    bb_lower = last['bb_lower'] if 'bb_lower' in df_15m.columns else price * 0.95
    bb_upper = last['bb_upper'] if 'bb_upper' in df_15m.columns else price * 1.05
    
    if bias == "BULLISH":
        if price < fib_382:
            return True, f"منطقة شراء ممتازة (تحت 0.382)", fib_382
        elif price < fib_500:
            return True, f"منطقة شراء جيدة (تحت 0.5)", fib_500
        elif price < bb_lower:
            return True, f"منطقة شراء (تحت BB Lower)", bb_lower
        else:
            if price - swing_low < (swing_high - swing_low) * 0.1:
                return True, f"قرب الدعم الرئيسي", swing_low
            return False, "السعر ليس في منطقة شراء مناسبة", None
    else:
        if price > fib_618:
            return True, f"منطقة بيع ممتازة (فوق 0.618)", fib_618
        elif price > fib_500:
            return True, f"منطقة بيع جيدة (فوق 0.5)", fib_500
        elif price > bb_upper:
            return True, f"منطقة بيع (فوق BB Upper)", bb_upper
        else:
            if swing_high - price < (swing_high - swing_low) * 0.1:
                return True, f"قرب المقاومة الرئيسية", swing_high
            return False, "السعر ليس في منطقة بيع مناسبة", None

# ---- Layer 6: News (محسّن) ----
def layer_news_advanced(symbol, bias):
    news = get_news_impact(symbol)
    if news is None:
        return True, "لا توجد أخبار مؤثرة"
    impact, sentiment, headline = news
    if impact == "HIGH":
        if (bias == "BULLISH" and sentiment == "BEARISH") or (bias == "BEARISH" and sentiment == "BULLISH"):
            return False, f"خبر عالي التأثير ضد الاتجاه: {headline}"
        else:
            return True, f"خبر عالي التأثير لكنه مع الاتجاه"
    else:
        return True, "الأخبار لا تعارض الصفقة"

# ---- حساب Stop Loss متقدم ----
def calculate_advanced_stop_loss(df, entry_price, bias):
    if df is None or len(df) < 20:
        return entry_price - (entry_price * 0.01) if bias == "BULLISH" else entry_price + (entry_price * 0.01), "افتراضي"
    
    last = df.iloc[-1]
    atr = last['atr'] if 'atr' in df.columns else (df['high'] - df['low']).rolling(14).mean().iloc[-1]
    
    if bias == "BULLISH":
        swing_low = df['low'].iloc[-10:].min()
        liquidity_levels = df['low'].iloc[-5:].tolist()
        if entry_price - swing_low < atr * 0.5:
            sl = entry_price - atr * 1.2
        else:
            sl = min(swing_low, entry_price - atr * 1.0)
        if sl in liquidity_levels:
            sl = sl - atr * 0.3
        return sl, f"Swing Low {swing_low:.2f} + ATR"
    else:
        swing_high = df['high'].iloc[-10:].max()
        liquidity_levels = df['high'].iloc[-5:].tolist()
        if swing_high - entry_price < atr * 0.5:
            sl = entry_price + atr * 1.2
        else:
            sl = max(swing_high, entry_price + atr * 1.0)
        if sl in liquidity_levels:
            sl = sl + atr * 0.3
        return sl, f"Swing High {swing_high:.2f} + ATR"

# ---- حساب الأهداف المتقدمة ----
def calculate_advanced_targets(entry, stop_loss, bias):
    risk = abs(entry - stop_loss)
    if bias == "BULLISH":
        targets = {
            'target1': entry + risk * 1.5,
            'target2': entry + risk * 2.5,
            'target3': entry + risk * 4.0,
            'risk_reward': 2.5,
            'breakeven': entry,
            'trailing_activation': entry + risk * 1.8
        }
    else:
        targets = {
            'target1': entry - risk * 1.5,
            'target2': entry - risk * 2.5,
            'target3': entry - risk * 4.0,
            'risk_reward': 2.5,
            'breakeven': entry,
            'trailing_activation': entry - risk * 1.8
        }
    return targets

# ---- MAIN DECISION ENGINE مع الطبقات ----
def generate_signal_with_layers(df_4h, df_1h, df_15m, symbol, dxy_signal=None, dxy_correlation=0.0, flexibility="Moderate"):
    original_signal, original_conf, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets, tbs_info = generate_signal_v2003(
        df_1h, symbol, dxy_signal, dxy_correlation
    )
    
    if original_signal == "WAIT":
        return "WAIT", original_conf, "الإشارة الأصلية WAIT", details, targets, sl, entry

    # ---- تحليل الطبقات ----
    regime_status, regime_reason = layer_regime(df_4h)
    bias, bias_reason = layer_4h_bias_advanced(df_4h)
    confirmed, conf_reason = layer_1h_confirmation_advanced(df_1h, bias)
    triggered, trigger_reason, trigger_price = layer_15m_trigger_advanced(df_15m, bias)
    price_ok, price_reason, optimal_entry = layer_price_location_advanced(df_15m, symbol, bias)
    news_ok, news_reason = layer_news_advanced(symbol, bias)

    # ---- نقاط الطبقات الداعمة ----
    support_points = 0
    if regime_status not in ["RANGING", "LOW_VOL"]:
        support_points += 1
    if price_ok:
        support_points += 1
    if news_ok:
        support_points += 1

    # ====== منطق القرار حسب المرونة ======
    if flexibility == "Strict":
        if bias == "NEUTRAL":
            return "WAIT", original_conf * 0.5, f"WAIT — {bias_reason}", details, targets, sl, entry
        if not confirmed:
            return "WAIT", original_conf * 0.6, f"WAIT — {conf_reason}", details, targets, sl, entry
        if not triggered:
            return "WAIT", original_conf * 0.6, f"WAIT — {trigger_reason}", details, targets, sl, entry
        if not price_ok:
            return "WAIT", original_conf * 0.6, f"WAIT — {price_reason}", details, targets, sl, entry
        if not news_ok:
            return "WAIT", original_conf * 0.6, f"WAIT — {news_reason}", details, targets, sl, entry
        if regime_status in ["RANGING", "LOW_VOL"]:
            return "WAIT", original_conf * 0.5, f"WAIT — {regime_reason}", details, targets, sl, entry

    elif flexibility == "Moderate":
        if bias == "NEUTRAL":
            return "WAIT", original_conf * 0.6, f"WAIT — {bias_reason}", details, targets, sl, entry
        if not confirmed:
            return "WAIT", original_conf * 0.6, f"WAIT — {conf_reason}", details, targets, sl, entry
        if not triggered:
            return "WAIT", original_conf * 0.6, f"WAIT — {trigger_reason}", details, targets, sl, entry
        if original_conf >= 75 and support_points >= 2:
            pass
        elif support_points < 2:
            return "WAIT", original_conf * 0.6, f"WAIT — نقاط الدعم منخفضة ({support_points}/3)", details, targets, sl, entry

    else:  # "Loose"
        if bias == "NEUTRAL":
            return "WAIT", original_conf * 0.5, f"WAIT — {bias_reason}", details, targets, sl, entry
        if not confirmed:
            return "WAIT", original_conf * 0.5, f"WAIT — {conf_reason}", details, targets, sl, entry
        if not triggered and original_conf < 70:
            return "WAIT", original_conf * 0.5, f"WAIT — {trigger_reason}", details, targets, sl, entry
        if support_points < 1:
            return "WAIT", original_conf * 0.5, f"WAIT — نقاط الدعم منخفضة ({support_points}/3)", details, targets, sl, entry

    # ---- حساب الإشارة النهائية ----
    if trigger_price is not None:
        entry_price = trigger_price
    elif optimal_entry is not None:
        entry_price = optimal_entry
    else:
        entry_price = df_15m['close'].iloc[-1]

    stop_loss, sl_reason = calculate_advanced_stop_loss(df_15m, entry_price, bias)
    targets = calculate_advanced_targets(entry_price, stop_loss, bias)

    confidence = min(95, original_conf + (support_points * 3))

    details['Regime'] = regime_reason
    details['4H_Bias'] = bias_reason
    details['1H_Confirmation'] = conf_reason
    details['15M_Trigger'] = trigger_reason
    details['Price_Location'] = price_reason
    details['News'] = news_reason
    details['Support_Points'] = f"{support_points}/3"
    details['Flexibility'] = flexibility

    return original_signal, confidence, f"{original_signal} — مؤكد ({flexibility})", details, targets, stop_loss, entry_price

# ============================================================
# BACKTEST
# ============================================================

def _bar_exit(direction, bar, stop, tp):
    if direction == "BUY":
        if bar['low'] <= stop: return "SL", stop
        if bar['high'] >= tp: return "TP", tp
    else:
        if bar['high'] >= stop: return "SL", stop
        if bar['low'] <= tp: return "TP", tp
    return None, None

def run_backtest(df, symbol, lookback=BACKTEST_LOOKBACK):
    if df is None or len(df) < 150:
        return {}
    test_df = df.iloc[-min(lookback, len(df)):].copy()
    trades, active = [], None
    daily_count = {}

    for i in range(100, len(test_df) - 1):
        bar = test_df.iloc[i]
        day = str(bar.name.date()) if hasattr(bar.name, 'date') else str(i)

        if active is not None:
            result, exit_price = _bar_exit(active['direction'], bar, active['stop'], active['tp'])
            if result:
                risk = abs(active['entry'] - active['stop'])
                reward = abs(exit_price - active['entry']) / risk if risk > 0 else 0
                trades.append({
                    'result': 'win' if result == 'TP' else 'loss',
                    'r': reward if result == 'TP' else -1,
                    'direction': active['direction'],
                    'entry_i': active['entry_i'],
                    'exit_i': i
                })
                active = None
            else:
                continue

        if daily_count.get(day, 0) >= MAX_TRADES_PER_DAY:
            continue

        window = test_df.iloc[:i+1].copy()
        signal, conf, _, _, _, _, _, _, sl, entry, targets, _ = generate_signal_v2003(
            window, symbol, dxy_signal=None, dxy_correlation=0.0
        )

        if signal == "WAIT" or conf < MIN_CONFIDENCE or sl is None or not targets:
            continue

        next_open = float(test_df['open'].iloc[i+1])
        stop = float(sl)
        tp = float(targets.get('target2'))

        if (signal == 'BUY' and stop >= next_open) or (signal == 'SELL' and stop <= next_open):
            continue

        active = {
            'direction': signal,
            'entry': next_open,
            'stop': stop,
            'tp': tp,
            'entry_i': i + 1
        }
        daily_count[day] = daily_count.get(day, 0) + 1

    if not trades:
        return {}

    wins = [t for t in trades if t['result'] == 'win']
    losses = [t for t in trades if t['result'] == 'loss']
    gross_win = sum(t['r'] for t in wins)
    gross_loss = abs(sum(t['r'] for t in losses))

    return {
        'total_trades': len(trades),
        'win_rate': len(wins) / len(trades) * 100,
        'avg_r': sum(t['r'] for t in trades) / len(trades),
        'profit_factor': gross_win / gross_loss if gross_loss > 0 else float('inf'),
        'wins': len(wins),
        'losses': len(losses)
    }

# ============================================================
# COLLECT SIGNALS (للجدول)
# ============================================================

@st.cache_data(ttl=120)
def get_all_signals_with_layers(flexibility="Moderate"):
    results = []
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    dxy_signal = None
    if df_dxy is not None and len(df_dxy) > 100:
        dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_v2003(
            df_dxy, "DX-Y.NYB", dxy_signal=None, dxy_correlation=0.0
        )

    for pair_name, symbol in PAIRS.items():
        try:
            df_4h = get_historical_data(symbol, period="1mo", interval="4h")
            df_1h = get_historical_data(symbol, period="1mo", interval="1h")
            df_15m = get_historical_data(symbol, period="7d", interval="15m")
            if df_4h is None or df_1h is None or df_15m is None:
                continue

            def prepare_df(df):
                if df is None or len(df) < 30:
                    return df
                df = df.copy()
                df['ema20'] = df['close'].ewm(20).mean()
                df['ema50'] = df['close'].ewm(50).mean()
                df['ema200'] = df['close'].ewm(200).mean()
                df['rsi'] = calc_rsi(df['close'])
                df['atr'] = calc_atr(df)
                df['macd'], df['macd_signal'], _ = calc_macd(df['close'])
                df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
                df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
                if len(df) >= 50:
                    tenkan, kijun, senkou_a, senkou_b, _ = calc_ichimoku(df)
                    df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
                smc = detect_smc_ict(df)
                for col in ['bos_bullish','bos_bearish','mss_bullish','mss_bearish',
                            'ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                            'liquidity_sweep_bullish','liquidity_sweep_bearish']:
                    df[col] = smc[col]
                return df

            df_4h = prepare_df(df_4h)
            df_1h = prepare_df(df_1h)
            df_15m = prepare_df(df_15m)

            corr = get_dxy_correlation(df_1h, df_dxy, lookback=50)

            signal, conf, reason, details, targets, sl, entry = generate_signal_with_layers(
                df_4h, df_1h, df_15m, symbol, dxy_signal, corr, flexibility
            )

            if signal != "WAIT":
                if any(x in pair_name for x in ["Gold", "Silver", "Bitcoin", "Ethereum"]):
                    fmt = "${:,.2f}"
                else:
                    fmt = "{:.4f}"

                results.append({
                    "Instrument": pair_name,
                    "Signal": signal,
                    "Confidence": round(conf, 1),
                    "Reason": reason[:50] + "..." if len(reason) > 50 else reason,
                    "Entry": fmt.format(entry) if entry else "N/A",
                    "SL": fmt.format(sl) if sl else "N/A",
                    "TP1": fmt.format(targets['target1']) if targets else "N/A",
                    "TP2": fmt.format(targets['target2']) if targets else "N/A",
                    "TP3": fmt.format(targets['target3']) if targets else "N/A",
                })
        except Exception as e:
            continue

    return pd.DataFrame(results)

# ============================================================
# ACTIVE TRADE MANAGER
# ============================================================

def _today_key(ts):
    return ts.strftime("%Y-%m-%d")

def can_open_trade(symbol, bar_index, now):
    stats = st.session_state.trade_stats
    today = _today_key(now)
    if stats["day"] != today:
        stats["day"] = today
        stats["count"] = 0
        stats["last_closed_bar"] = {}
    if symbol in st.session_state.active_trades:
        return False
    if stats["count"] >= MAX_TRADES_PER_DAY:
        return False
    last_closed = stats["last_closed_bar"].get(symbol, -10**9)
    return (bar_index - last_closed) >= COOLDOWN_BARS

def open_active_trade(symbol, pair_name, direction, entry, stop, targets, confidence, bar_index):
    st.session_state.active_trades[symbol] = {
        "symbol": symbol,
        "pair": pair_name,
        "direction": direction,
        "entry": float(entry),
        "stop": float(stop),
        "tp1": float(targets['target1']),
        "tp2": float(targets['target2']),
        "tp3": float(targets['target3']),
        "confidence": float(confidence),
        "opened_at": datetime.now().isoformat(),
        "opened_bar": int(bar_index),
        "status": "OPEN"
    }
    st.session_state.trade_stats["count"] += 1

def update_active_trade(symbol, df):
    trade = st.session_state.active_trades.get(symbol)
    if not trade or df is None or df.empty:
        return None
    bar = df.iloc[-1]
    if trade["direction"] == "BUY":
        hit_sl = bar['low'] <= trade['stop']
        hit_tp3 = bar['high'] >= trade['tp3']
    else:
        hit_sl = bar['high'] >= trade['stop']
        hit_tp3 = bar['low'] <= trade['tp3']

    result = None
    exit_price = None
    if hit_sl:
        result, exit_price = "SL", trade['stop']
    elif hit_tp3:
        result, exit_price = "TP3", trade['tp3']

    if result:
        closed = trade.copy()
        closed.update({"closed_at": datetime.now().isoformat(), "result": result, "exit": float(exit_price)})
        st.session_state.closed_trades.append(closed)
        del st.session_state.active_trades[symbol]
        st.session_state.trade_stats["last_closed_bar"][symbol] = len(df) - 1
        return closed
    return None

# ============================================================
# STREAMLIT UI
# ============================================================

with st.sidebar:
    st.markdown("### 📊 Market Status")
    status, status_text, next_event, close_time = get_market_status()
    if status == "OPEN":
        st.markdown(f"🟢 **{status_text}**")
        st.markdown(f"⏳ **Closes in:** {time_remaining(next_event)}")
    else:
        st.markdown(f"🔴 **{status_text}**")
        st.markdown(f"⏳ **Opens in:** {time_remaining(next_event)}")

    st.markdown("---")
    st.markdown("### ⚙️ Signal Flexibility")
    flexibility = st.selectbox(
        "Filter Level",
        ["Moderate (1-3/day)", "Loose (3-5/day)", "Strict (0-1/day)"],
        index=0,
        help="Moderate: أساسي فقط. Loose: نظام نقاط. Strict: كل الطبقات."
    )
    flex_value = flexibility.split(" ")[0]  # "Moderate", "Loose", "Strict"

    st.markdown("---")
    st.markdown("### 📋 All Signals")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh All", use_container_width=True):
            with st.spinner("Analyzing..."):
                st.session_state.all_signals = get_all_signals_with_layers(flex_value)
                st.session_state.last_update = datetime.now()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.all_signals = None
            st.rerun()

    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_sig = st.session_state.all_signals.copy()
        df_sig["Signal"] = df_sig["Signal"].apply(
            lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL" if x=="SELL" else "⚪ WAIT"
        )
        st.dataframe(
            df_sig[["Instrument", "Signal", "Confidence", "Reason", "Entry", "SL", "TP1", "TP2", "TP3"]],
            hide_index=True,
            use_container_width=True,
            height=350
        )
        buy = len(df_sig[df_sig["Signal"] == "🟢 BUY"])
        sell = len(df_sig[df_sig["Signal"] == "🔴 SELL"])
        wait = len(df_sig) - buy - sell
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"🟢 **{buy}** BUY")
        c2.markdown(f"🔴 **{sell}** SELL")
        c3.markdown(f"⚪ **{wait}** WAIT")
        st.caption(f"🕐 {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("Press 'Refresh All'")

    st.markdown("---")
    st.markdown("### 🔍 Select Instrument")
    selected_pair = st.selectbox("For advanced analysis", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]

    st.markdown("---")
    if st.button("➕ New Trade", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form

# ============================================================
# LOAD SELECTED INSTRUMENT DATA
# ============================================================

price, change = get_spot_price(selected_symbol)

df_4h = get_historical_data(selected_symbol, period="1mo", interval="4h")
df_1h = get_historical_data(selected_symbol, period="1mo", interval="1h")
df_15m = get_historical_data(selected_symbol, period="7d", interval="15m")

if df_4h is None or df_1h is None or df_15m is None:
    st.error("Failed to load data for one or more timeframes")
    st.stop()

if price is None:
    price = df_15m['close'].iloc[-1]
    change = 0

def prepare_df_ui(df):
    if df is None or len(df) < 30:
        return df
    df = df.copy()
    df['ema20'] = df['close'].ewm(20).mean()
    df['ema50'] = df['close'].ewm(50).mean()
    df['ema200'] = df['close'].ewm(200).mean()
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], _ = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
    if len(df) >= 50:
        tenkan, kijun, senkou_a, senkou_b, _ = calc_ichimoku(df)
        df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
    smc = detect_smc_ict(df)
    for col in ['bos_bullish','bos_bearish','mss_bullish','mss_bearish',
                'ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                'liquidity_sweep_bullish','liquidity_sweep_bearish']:
        df[col] = smc[col]
    return df

df_4h = prepare_df_ui(df_4h)
df_1h = prepare_df_ui(df_1h)
df_15m = prepare_df_ui(df_15m)

df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
dxy_signal = None
corr = 0.0
if df_dxy is not None and len(df_dxy) > 100:
    dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_v2003(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df_1h, df_dxy, lookback=50)

signal, confidence, reason, details, targets, sl, entry = generate_signal_with_layers(
    df_4h, df_1h, df_15m, selected_symbol, dxy_signal, corr, flex_value
)

# ============================================================
# DISPLAY
# ============================================================

if "Gold" in selected_pair or "Silver" in selected_pair or "Bitcoin" in selected_pair or "Ethereum" in selected_pair:
    price_fmt = "${:,.2f}"
else:
    price_fmt = "{:.4f}"

st.markdown(f"""
<div class="price-card">
    <div class="price-label">{selected_pair}</div>
    <div class="price-value">{price_fmt.format(price)}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">
        {change:+.2f}%
    </div>
</div>
""", unsafe_allow_html=True)

if dxy_signal:
    dxy_col = "#00ff88" if dxy_signal=="BUY" else "#ff4444" if dxy_signal=="SELL" else "#ffaa00"
    st.markdown(f"""
    <div style="background:rgba(10,10,10,0.5);border-radius:8px;padding:8px 15px;margin:5px 0;border:1px solid rgba(255,215,0,0.08);">
        <span style="color:#888;font-size:0.8rem;">📊 DXY Signal: </span>
        <span style="color:{dxy_col};font-weight:bold;font-size:0.9rem;">{dxy_signal}</span>
        <span style="color:#888;font-size:0.8rem;margin-left:15px;">🔗 Correlation: </span>
        <span style="color:{'#00ff88' if abs(corr)>0.3 else '#ffaa00'};font-weight:bold;font-size:0.9rem;">{corr:.2f}</span>
        <span style="color:#666;font-size:0.7rem;margin-left:10px;">({('Strong inverse' if corr < -0.6 else 'Strong direct' if corr > 0.6 else 'Moderate' if abs(corr)>0.3 else 'Weak')})</span>
    </div>
    """, unsafe_allow_html=True)

if signal != "WAIT":
    direction_text = "BUY" if signal=="BUY" else "SELL"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>Direction:</b> {direction_text} <span style="color:#00ff88;">(Confidence: {confidence:.0f}%)</span><br>
        <b>📍 Entry:</b> {price_fmt.format(entry)}<br>
        <b>🛑 Stop Loss:</b> {price_fmt.format(sl)}<br>
        <div class="target-zone"><b>🎯 TP1 (1.5R):</b> {price_fmt.format(targets['target1'])}</div>
        <div class="target-zone" style="border-left-color:#ffaa00;"><b>🎯 TP2 (2.5R):</b> {price_fmt.format(targets['target2'])}</div>
        <div class="target-zone" style="border-left-color:#00ff88;"><b>🎯 TP3 (4R):</b> {price_fmt.format(targets['target3'])}</div>
        <b>📈 R:R</b> 1:{targets.get('risk_reward',0):.1f}<br>
        <b>🔒 Breakeven:</b> عند TP1 | <b>Trailing:</b> عند TP2
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Layer Details", expanded=True):
        for key, value in details.items():
            if key not in ['Entry_Price', 'Stop_Loss', 'SL_Reason']:
                st.write(f"**{key}:** {value}")

else:
    st.warning(f"🟡 WAIT — {reason}")

# Regime Badge
if details and 'Regime' in details:
    regime_text = details['Regime']
    if "اتجاه واضح" in regime_text:
        st.markdown('<span class="regime-badge regime-trending">📈 Trending</span>', unsafe_allow_html=True)
    elif "عرضي" in regime_text:
        st.markdown('<span class="regime-badge regime-ranging">➖ Ranging</span>', unsafe_allow_html=True)
    elif "تقلب مرتفع" in regime_text:
        st.markdown('<span class="regime-badge regime-volatile">⚡ High Volatility</span>', unsafe_allow_html=True)
    elif "تقلب منخفض" in regime_text:
        st.markdown('<span class="regime-badge" style="background:rgba(0,150,255,0.15);color:#0096ff;border:1px solid rgba(0,150,255,0.20);">🌊 Low Volatility</span>', unsafe_allow_html=True)

# ============================================================
# BACKTEST
# ============================================================

bt = run_backtest(df_1h, selected_symbol)
if bt:
    st.markdown("#### 📈 Backtest (Last 500 Bars)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trades", bt['total_trades'])
    c2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    c3.metric("Average R", f"{bt['avg_r']:.2f}")
    c4.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

# ============================================================
# CHART
# ============================================================

st.markdown("---")
st.markdown("### 📈 Price Chart (15M)")

df_smc = detect_smc_ict(df_15m)

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])

fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
if 'ema20' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
if 'ema50' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['ema50'], name='EMA50', line=dict(color='red', dash='dash')), row=1, col=1)

if sl and entry:
    fig.add_hline(y=sl, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df_15m.index[-1], y=sl, text="SL", showarrow=True, arrowhead=1, row=1, col=1)
    fig.add_hline(y=entry, line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df_15m.index[-1], y=entry, text="Entry", showarrow=True, arrowhead=1, row=1, col=1)

if 'rsi' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

if 'macd' in df_15m.columns and 'macd_signal' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)

fig.update_layout(height=800, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TRADE MANAGEMENT
# ============================================================

st.markdown("---")
st.markdown("### 💼 Trade Management")

if selected_symbol in st.session_state.active_trades:
    active_trade = st.session_state.active_trades[selected_symbol]
    st.success(f"🔒 Active trade locked: {active_trade['direction']} — TP3 or SL")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("الدخول", price_fmt.format(active_trade['entry']))
    c2.metric("SL", price_fmt.format(active_trade['stop']))
    c3.metric("TP3", price_fmt.format(active_trade['tp3']))
    c4.metric("Confidence", f"{active_trade['confidence']:.0f}%")
else:
    st.info("No active trade — scanning for new opportunities")

if st.session_state.closed_trades:
    hist = pd.DataFrame(st.session_state.closed_trades[-20:])
    st.dataframe(
        hist[["pair", "direction", "entry", "stop", "tp3", "exit", "result", "opened_at", "closed_at"]],
        hide_index=True,
        use_container_width=True
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown(f"""
<div class="footer">
    <span class="brand">▲ BLACK PYRAMID v2003</span> • 7 Layers • All Pairs • Precision Engine • 1-3 Trades/Day<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
