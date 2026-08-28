# ============================================================
# BLACK PYRAMID v2003 â€“ Advanced Trading Intelligence Engine
# Last updated: 2026-08-28
# Architecture: Regime + Confirmation + Risk + Backtesting
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
    page_title="Black Pyramid v2003",
    page_icon="â–²",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Visual identity â€“ enhanced
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
        content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: url('https://raw.githubusercontent.com/kamelehab04-dotcom/gold-streamlit/main/file_00000000a364820aa4218d02627011f1.png');
        background-size: cover; background-position: center;
        opacity: 0.25; pointer-events: none; z-index: 0;
    }
    .stApp::after {
        content: ''; position: fixed; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(ellipse at 30% 20%, rgba(255,215,0,0.03) 0%, transparent 50%),
                    radial-gradient(ellipse at 70% 80%, rgba(255,215,0,0.02) 0%, transparent 50%);
        pointer-events: none; z-index: 0; animation: bgPulse 10s ease-in-out infinite;
    }
    @keyframes bgPulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
    .main-header, .price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone, .target-zone, .stop-loss-level, .reversal-alert, .news-card, .explanation-box, .stButton button, .stSelectbox, .stDataFrame, .stMetric, .stPlotlyChart, .stTabs { position: relative; z-index: 1; }
    .css-1d391kg, .css-1d391kg * { background: rgba(10,10,10,0.85); backdrop-filter: blur(10px); border-right: 1px solid rgba(255,215,0,0.05); }
    .main-header { display: flex; justify-content: flex-end; align-items: center; padding: 10px 25px; min-height: 55px; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); border-radius: 12px; margin-bottom: 15px; border: 1px solid rgba(255,215,0,0.08); }
    .main-header .main-title { font-size: 1.2rem; color: #ffd700; font-weight: 700; letter-spacing: 2px; }
    .main-header .main-subtitle { font-size: 0.55rem; color: #666; letter-spacing: 1px; }
    .price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone, .target-zone, .stop-loss-level, .reversal-alert { background: rgba(10,10,10,0.75); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.10); border-radius: 12px; box-shadow: 0 4px 30px rgba(0,0,0,0.5); }
    .price-value { color: #fff; }
    .price-label { color: #888; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 2px; }
    .signal-box { border: 2px solid #ffd700; }
    .suggested-trade { border: 2px solid #00ff88; background: rgba(0,10,5,0.80); }
    .target-zone { border-left: 4px solid #ffd700; background: rgba(255,215,0,0.04); padding: 8px 12px; margin: 4px 0; }
    .target-zone:last-child { border-left-color: #00ff88; }
    .stop-loss-level { border-left: 4px solid #ff4444; background: rgba(255,68,68,0.04); padding: 8px 12px; margin: 4px 0; }
    .entry-zone { border-left: 4px solid #00ff88; background: rgba(0,255,136,0.04); padding: 8px 12px; margin: 4px 0; }
    .trade-row { border-left: 4px solid #ffd700; padding: 10px 15px; margin: 5px 0; }
    .footer { text-align: center; padding: 15px; color: #444; font-size: 0.65rem; border-top: 1px solid rgba(255,215,0,0.05); margin-top: 30px; letter-spacing: 1px; }
    .footer .brand { color: #ffd700; font-weight: 600; }
    .stButton button { background: linear-gradient(135deg, #ffd700 0%, #d4a800 100%) !important; color: #000 !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; padding: 8px 16px !important; width: 100% !important; transition: all 0.3s ease !important; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255,215,0,0.2); }
    .explanation-box { background: rgba(10,10,10,0.80); border: 1px solid rgba(255,215,0,0.05); border-radius: 10px; padding: 15px; margin: 8px 0; color: #bbb; font-size: 0.9rem; line-height: 1.6; }
    .news-card { background: rgba(10,10,10,0.65); border-left: 3px solid #ffd700; border-radius: 8px; padding: 10px 15px; margin: 5px 0; }
    .news-title { color: #eee; font-weight: 500; font-size: 0.9rem; }
    .news-date { color: #666; font-size: 0.7rem; }
    .reversal-alert { border: 1px solid #ff4444; background: rgba(255,68,68,0.04); padding: 10px 15px; margin: 5px 0; border-radius: 8px; font-size: 0.85rem; }
    .pattern-badge { display: inline-block; background: rgba(255,215,0,0.08); border: 1px solid rgba(255,215,0,0.12); border-radius: 16px; padding: 3px 12px; margin: 2px; font-size: 0.7rem; color: #ffd700; }
    .tbs-badge { display: inline-block; background: rgba(255,136,0,0.10); border: 1px solid rgba(255,136,0,0.15); border-radius: 16px; padding: 3px 12px; margin: 2px; font-size: 0.7rem; color: #ff8800; font-weight: bold; }
    .dxy-aligned { display: inline-block; background: rgba(0,255,136,0.10); border: 1px solid rgba(0,255,136,0.20); border-radius: 16px; padding: 3px 12px; margin: 2px; font-size: 0.7rem; color: #00ff88; font-weight: bold; }
    .dxy-misaligned { display: inline-block; background: rgba(255,68,68,0.10); border: 1px solid rgba(255,68,68,0.20); border-radius: 16px; padding: 3px 12px; margin: 2px; font-size: 0.7rem; color: #ff4444; font-weight: bold; }
    .regime-badge { display: inline-block; border-radius: 16px; padding: 3px 12px; margin: 2px; font-size: 0.7rem; font-weight: bold; }
    .regime-trending { background: rgba(0,255,136,0.15); color: #00ff88; border: 1px solid rgba(0,255,136,0.20); }
    .regime-ranging { background: rgba(255,170,0,0.15); color: #ffaa00; border: 1px solid rgba(255,170,0,0.20); }
    .regime-volatile { background: rgba(255,68,68,0.15); color: #ff4444; border: 1px solid rgba(255,68,68,0.20); }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Header
# ============================================================
st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">
            <span class="pyramid-icon">â–²</span>
            BLACK PYRAMID v2003
            <span class="pyramid-icon">â–²</span>
        </div>
        <div class="main-subtitle">Regime â€¢ Structure â€¢ Liquidity â€¢ SMC â€¢ MTF â€¢ DXY â€¢ Risk â€¢ Backtest</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# API Keys & Configuration
# ============================================================
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

BACKTEST_LOOKBACK = 500
# Daily trading profile: more opportunities, but still filtered
MIN_CONFIDENCE = 42
BUY_THRESHOLD = 8
SELL_THRESHOLD = -8
COOLDOWN_BARS = 4
MAX_TRADES_PER_DAY = 3

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
# Session state initialization
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
# Data retrieval functions
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
        return ("OPEN", "Market Open (Sunday)", close_time, close_time) if now >= open_time else ("CLOSED", "Waiting for Open", open_time, close_time)
    if 0 <= wd <= 3:
        if close_time <= now < open_time:
            return "CLOSED", "Daily Break", open_time, close_time
        return "OPEN", "Market Open", close_time if now < close_time else close_time + timedelta(days=1), close_time
    if wd == 4:
        if now < close_time:
            return "OPEN", "Market Open (Friday)", close_time, close_time
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

def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z") if dt else "N/A"

# ============================================================
# Core indicators (enhanced)
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
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
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
# Structure, Liquidity and SMC tools
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
# TBS (Turtle Body Soup) â€“ corrected
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
        return "BEARISH", last['close'], last['low'], lookback_high
    elif last['low'] < lookback_low and last['close'] > lookback_low:
        return "BULLISH", last['close'], last['high'], lookback_low
    return None, None, None, None

# ============================================================
# DXY Correlation (using returns)
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

# ============================================================
# DXY Filter (without reversing the signal)
# ============================================================
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
# Regime Filter
# ============================================================
def detect_regime(df):
    last = df.iloc[-1]
    adx = last['adx'] if 'adx' in df.columns else 20
    ema20 = df['ema20'].iloc[-1] if 'ema20' in df.columns else df['close'].iloc[-1]
    ema50 = df['ema50'].iloc[-1] if 'ema50' in df.columns else df['close'].iloc[-1]
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

# ============================================================
# MTF Engine (enhanced)
# ============================================================
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

# ============================================================
# Main signal engine (v2003) â€“ fully corrected
# ============================================================
def generate_signal_v2003(df, symbol, dxy_signal=None, dxy_correlation=0.0):
    if df is None or len(df) < 100:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, (None,None,None,None)
    
    # Calculate indicators
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
    
    # SMC
    df_smc = detect_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    
    # TBS
    tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs_correct(df)
    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)
    
    # Regime
    regime = detect_regime(df)
    
    # MTF
    mtf_consensus, mtf_count, mtf_details = mtf_analysis(df, symbol)
    
    last = df.iloc[-1]
    current_price = last['close']
    
    # ========== Factor system ==========
    factors = {
        "structure": 0.0,
        "liquidity": 0.0,
        "smc": 0.0,
        "mtf": 0.0,
        "dxy": 0.0,
        "momentum": 0.0,
        "volatility": 0.0,
        "pattern": 0.0,
        "volume": 0.0
    }
    details = {}
    
    # 1. Structure
    if last_smc.get('bos_bullish', False) or last_smc.get('mss_bullish', False):
        factors['structure'] += 25.0
        details['Structure'] = "Bullish BOS/MSS"
    elif last_smc.get('bos_bearish', False) or last_smc.get('mss_bearish', False):
        factors['structure'] -= 25.0
        details['Structure'] = "Bearish BOS/MSS"
    else:
        details['Structure'] = "Neutral"
    
    # 2. Liquidity
    if last_smc.get('liquidity_sweep_bullish', False):
        factors['liquidity'] += 20.0
        details['Liquidity'] = "Buy-side liquidity sweep"
    elif last_smc.get('liquidity_sweep_bearish', False):
        factors['liquidity'] -= 20.0
        details['Liquidity'] = "Sell-side liquidity sweep"
    else:
        details['Liquidity'] = "No sweep detected"
    
    # 3. SMC
    if last_smc.get('ob_bullish', False) or last_smc.get('fvg_bullish', False):
        factors['smc'] += 20.0
        details['SMC'] = "Bullish OB/FVG"
    elif last_smc.get('ob_bearish', False) or last_smc.get('fvg_bearish', False):
        factors['smc'] -= 20.0
        details['SMC'] = "Bearish OB/FVG"
    else:
        details['SMC'] = "No SMC signal"
    
    # 4. MTF
    if mtf_consensus == "BUY":
        factors['mtf'] += 15.0
        details['MTF'] = f"Bullish ({mtf_count} timeframes)"
    elif mtf_consensus == "SELL":
        factors['mtf'] -= 15.0
        details['MTF'] = f"Bearish ({mtf_count} timeframes)"
    else:
        details['MTF'] = "Neutral"
    
    # 5. DXY
    if dxy_signal is not None and dxy_signal != "WAIT":
        raw_direction = "BUY" if factors['structure'] + factors['liquidity'] + factors['smc'] + factors['mtf'] > 0 else "SELL"
        if raw_direction == "WAIT":
            raw_direction = "BUY" if factors['structure'] > 0 else "SELL"
        adjusted, status, adj = apply_dxy_filter(raw_direction, 0, dxy_signal, dxy_correlation)
        factors['dxy'] = float(adj)
        details['DXY'] = f"{status} (طھط¹ط¯ظٹظ„: {adj})"
    else:
        details['DXY'] = "No DXY signal"
    
    # 6. Momentum
    if last['rsi'] < 30:
        factors['momentum'] += 10.0
        details['Momentum'] = f"Oversold RSI={last['rsi']:.1f}"
    elif last['rsi'] > 70:
        factors['momentum'] -= 10.0
        details['Momentum'] = f"Overbought RSI={last['rsi']:.1f}"
    else:
        factors['momentum'] += (50 - last['rsi']) / 10.0
        details['Momentum'] = f"RSI Neutral {last['rsi']:.1f}"
    if last['macd'] > last['macd_signal']:
        factors['momentum'] += 5.0
    else:
        factors['momentum'] -= 5.0
    
    # 7. Volatility
    atr_ratio = last['atr'] / df['atr'].iloc[-20:].mean() if df['atr'].iloc[-20:].mean() > 0 else 1.0
    if atr_ratio > 1.5:
        factors['volatility'] -= 10.0
        details['Volatility'] = "High volatility"
    elif atr_ratio < 0.7:
        factors['volatility'] += 5.0
        details['Volatility'] = "Low Volatility"
    else:
        details['Volatility'] = "Normal volatility"
    
    # 8. Pattern
    if tbs_type == "BULLISH":
        factors['pattern'] += 20.0
        details['Pattern'] = f"TBS BUY"
    elif tbs_type == "BEARISH":
        factors['pattern'] -= 20.0
        details['Pattern'] = f"TBS SELL"
    else:
        details['Pattern'] = "No TBS"
    
    # 9. Volume / MFI
    if last['mfi'] < 20:
        factors['volume'] += 5.0
        details['Volume'] = f"MFI Oversold {last['mfi']:.1f}"
    elif last['mfi'] > 80:
        factors['volume'] -= 5.0
        details['Volume'] = f"MFI Overbought {last['mfi']:.1f}"
    else:
        details['Volume'] = f"MFI Neutral {last['mfi']:.1f}"
    
    total_score = sum(factors.values())
    
    # Determine signal
    if total_score >= BUY_THRESHOLD:
        signal = "BUY"
        confidence = min(90, 50 + total_score * 0.5)
    elif total_score <= SELL_THRESHOLD:
        signal = "SELL"
        confidence = min(90, 50 + abs(total_score) * 0.5)
    else:
        signal = "WAIT"
        confidence = 50 + total_score * 0.2
    
    confidence = max(0, min(100, confidence))
    
    # Adjust confidence by regime
    if "HIGH_VOL" in regime:
        confidence *= 0.9
    elif "LOW_VOL" in regime:
        confidence *= 1.1
    
    # ========== Stop Loss & Targets ==========
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
            targets = {
                'target1': entry_price + risk * 1.0,
                'target2': entry_price + risk * 1.5,
                'target3': entry_price + risk * 2.0,
                'risk_reward': 2.0
            }
        else:
            targets = {
                'target1': entry_price - risk * 1.0,
                'target2': entry_price - risk * 1.5,
                'target3': entry_price - risk * 2.0,
                'risk_reward': 2.0
            }
    
    return signal, confidence, total_score, details, factors, regime, mtf_consensus, mtf_count, stop_loss, entry_price, targets, tbs_info

# ============================================================
# Backtesting Engine
# ============================================================
def _bar_exit(direction, bar, stop, tp):
    # Conservative handling: if both SL and TP are touched in one candle,
    # count the stop first because intrabar order is unknown.
    if direction == "BUY":
        if bar['low'] <= stop:
            return "SL", stop
        if bar['high'] >= tp:
            return "TP", tp
    else:
        if bar['high'] >= stop:
            return "SL", stop
        if bar['low'] <= tp:
            return "TP", tp
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
            'direction': signal, 'entry': next_open, 'stop': stop,
            'tp': tp, 'entry_i': i + 1
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
        'wins': len(wins), 'losses': len(losses)
    }

# ============================================================
# Collect signals for all instruments
# ============================================================
@st.cache_data(ttl=120)
def get_all_signals():
    results = []
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    dxy_signal = None
    if df_dxy is not None and len(df_dxy) > 100:
        dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_v2003(
            df_dxy, "DX-Y.NYB", dxy_signal=None, dxy_correlation=0.0
        )
    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval="1h")
            if df is None or len(df) < 100:
                continue
            current_price = df['close'].iloc[-1]
            corr = get_dxy_correlation(df, df_dxy, lookback=50)
            signal, conf, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets, tbs = generate_signal_v2003(
                df, symbol, dxy_signal, corr
            )
            bt = run_backtest(df, symbol)
            if any(x in pair_name for x in ["Gold", "Silver", "Bitcoin", "Ethereum"]):
                price_str = f"${current_price:,.2f}"
                fmt = "${:,.2f}"
            else:
                price_str = f"{current_price:.4f}"
                fmt = "{:.4f}"
            
            results.append({
                "Instrument": pair_name,
                "Signal": signal,
                "Confidence": round(conf, 1),
                "Score": score,
                "Price": price_str,
                "Entry Price": fmt.format(entry) if entry else "N/A",
                "Stop Loss": fmt.format(sl) if sl else "N/A",
                "Target 1": fmt.format(targets.get('target1')) if targets else "N/A",
                "Target 2": fmt.format(targets.get('target2')) if targets else "N/A",
                "Target 3": fmt.format(targets.get('target3')) if targets else "N/A",
                "Risk:Reward": f"1:{targets.get('risk_reward',0):.1f}" if targets else "N/A",
                "DXY Alignment": details.get('DXY', 'N/A'),
                "Correlation": round(corr, 3),
                "Regime": regime,
                "MTF": mtf_cons,
                "Win Rate": f"{bt.get('win_rate', 0):.1f}%" if bt else "N/A",
                "Profit Factor": f"{bt.get('profit_factor', 0):.2f}" if bt else "N/A"
            })
        except Exception as e:
            continue
    return pd.DataFrame(results)

# ============================================================
# Active Trade Manager â€“ one locked trade per symbol
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
        "symbol": symbol, "pair": pair_name, "direction": direction,
        "entry": float(entry), "stop": float(stop),
        "tp1": float(targets['target1']), "tp2": float(targets['target2']),
        "tp3": float(targets['target3']), "confidence": float(confidence),
        "opened_at": datetime.now().isoformat(), "opened_bar": int(bar_index),
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

    # Conservative: unknown intrabar order -> SL wins if both touched.
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
# Streamlit interface
# ============================================================
with st.sidebar:
    st.markdown("### ًں“ٹ Market Status")
    status, status_text, next_event, close_time = get_market_status()
    if status == "OPEN":
        st.markdown(f"ًںں¢ **{status_text}**")
        st.markdown(f"âڈ³ **Closes in:** {time_remaining(next_event)}")
    else:
        st.markdown(f"ًں”´ **{status_text}**")
        st.markdown(f"âڈ³ **Opens in:** {time_remaining(next_event)}")
    st.markdown("---")
    
    st.markdown("### ًں“‹ All Signals")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ًں”„ Refresh All", use_container_width=True):
            with st.spinner("Analyzing..."):
                st.session_state.all_signals = get_all_signals()
                st.session_state.last_update = datetime.now()
                st.rerun()
    with col2:
        if st.button("ًں—‘ï¸ڈ Clear", use_container_width=True):
            st.session_state.all_signals = None
            st.rerun()
    
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_sig = st.session_state.all_signals.copy()
        df_sig["Signal"] = df_sig["Signal"].apply(lambda x: "ًںں¢ BUY" if x=="BUY" else "ًں”´ SELL" if x=="SELL" else "âڑھ WAIT")
        st.dataframe(
            df_sig[["Instrument", "Signal", "Confidence", "Score", "Price", "DXY Alignment"]],
            column_config={
                "Instrument": "Instrument",
                "Signal": "Signal",
                "Confidence": st.column_config.NumberColumn("Confidence", format="%.1f%%"),
                "Score": st.column_config.NumberColumn("Score", format="%d"),
                "Price": "Price",
                "DXY Alignment": "DXY"
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )
        buy = len(df_sig[df_sig["Signal"] == "ًںں¢ BUY"])
        sell = len(df_sig[df_sig["Signal"] == "ًں”´ SELL"])
        wait = len(df_sig) - buy - sell
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"ًںں¢ **{buy}** BUY")
        c2.markdown(f"ًں”´ **{sell}** SELL")
        c3.markdown(f"âڑھ **{wait}** WAIT")
        st.caption(f"ًں•گ {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("Press 'Refresh All'")
    
    st.markdown("---")
    st.markdown("### ًں”چ Select Instrument")
    selected_pair = st.selectbox("For advanced analysis", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]
    st.markdown("---")
    if st.button("â‍• New Trade", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form

# ============================================================
# Load selected instrument data
# ============================================================
price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="60d", interval="15m")
if df is None:
    st.error("Failed to load data")
    st.stop()
if price is None:
    price = df['close'].iloc[-1]
    change = 0

# DXY
df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
dxy_signal = None
corr = 0.0
if df_dxy is not None and len(df_dxy) > 100:
    dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_v2003(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df, df_dxy, lookback=50)

# Calculate indicators for selected instrument
df['ema20'] = df['close'].ewm(20).mean()
df['ema50'] = df['close'].ewm(50).mean()
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

# Generate signal for selected instrument
signal, confidence, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets, tbs_info = generate_signal_v2003(
    df, selected_symbol, dxy_signal, corr
)

# Lock the trade: update first, then open only if no active trade exists.
closed_now = update_active_trade(selected_symbol, df)
if selected_symbol not in st.session_state.active_trades:
    if signal in ["BUY", "SELL"] and confidence >= MIN_CONFIDENCE and sl is not None and targets:
        if can_open_trade(selected_symbol, len(df) - 1, datetime.now()):
            open_active_trade(selected_symbol, selected_pair, signal, entry, sl, targets, confidence, len(df) - 1)

active_trade = st.session_state.active_trades.get(selected_symbol)
if active_trade:
    signal = active_trade["direction"]
    confidence = active_trade["confidence"]
    entry = active_trade["entry"]
    sl = active_trade["stop"]
    targets = {"target1": active_trade["tp1"], "target2": active_trade["tp2"], "target3": active_trade["tp3"], "risk_reward": 2.0}

# ============================================================
# Display price and indicators
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

# DXY info
if dxy_signal:
    dxy_col = "#00ff88" if dxy_signal=="BUY" else "#ff4444" if dxy_signal=="SELL" else "#ffaa00"
    st.markdown(f"""
    <div style="background:rgba(10,10,10,0.5);border-radius:8px;padding:8px 15px;margin:5px 0;border:1px solid rgba(255,215,0,0.08);">
        <span style="color:#888;font-size:0.8rem;">ًں“ٹ DXY Signal: </span>
        <span style="color:{dxy_col};font-weight:bold;font-size:0.9rem;">{dxy_signal}</span>
        <span style="color:#888;font-size:0.8rem;margin-left:15px;">ًں”— Correlation: </span>
        <span style="color:{'#00ff88' if abs(corr)>0.3 else '#ffaa00'};font-weight:bold;font-size:0.9rem;">{corr:.2f}</span>
        <span style="color:#666;font-size:0.7rem;margin-left:10px;">({('Strong inverse' if corr < -0.6 else 'Strong direct' if corr > 0.6 else 'Moderate' if abs(corr)>0.3 else 'Weak')})</span>
    </div>
    """, unsafe_allow_html=True)

# Regime
regime_badge = ""
if "TRENDING" in regime:
    regime_badge = '<span class="regime-badge regime-trending">ًں“ˆ Trending</span>'
elif "RANGING" in regime:
    regime_badge = '<span class="regime-badge regime-ranging">â‍– Ranging</span>'
if "HIGH_VOL" in regime:
    regime_badge += ' <span class="regime-badge regime-volatile">âڑ، High Volatility</span>'
elif "LOW_VOL" in regime:
    regime_badge += ' <span class="regime-badge" style="background:rgba(0,150,255,0.15);color:#0096ff;border:1px solid rgba(0,150,255,0.20);">ًںŒٹ Low Volatility</span>'
st.markdown(f"**Current Regime:** {regime_badge}", unsafe_allow_html=True)

# ============================================================
# Display suggested trade
# ============================================================
if signal in ["BUY", "SELL"] and confidence >= MIN_CONFIDENCE:
    direction_text = "BUY" if signal=="BUY" else "SELL"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>Direction:</b> {direction_text} (Confidence: {confidence:.0f}%)<br>
        <b>ًں“چ Entry:</b> {price_fmt.format(entry)}<br>
        <b>ًں›‘ Stop Loss:</b> {price_fmt.format(sl)}<br>
        <div class="target-zone"><b>ًںژ¯ Target 1 (1:1):</b> {price_fmt.format(targets.get('target1'))}</div>
        <div class="target-zone" style="border-left-color:#ffaa00;"><b>ًںژ¯ Target 2 (1:1.5):</b> {price_fmt.format(targets.get('target2'))}</div>
        <div class="target-zone" style="border-left-color:#00ff88;"><b>ًںژ¯ Target 3 (1:2):</b> {price_fmt.format(targets.get('target3'))}</div>
        <b>ًں“ˆ R:R</b> 1:{targets.get('risk_reward',0):.1f}
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Factor details (error fixed)
# ============================================================
with st.expander("ًں“ٹ Integrated Factor Analysis", expanded=True):
    cols = st.columns(3)
    i = 0
    for factor, value in factors.items():
        col = cols[i % 3]
        # Use float formatting instead of int
        col.metric(factor.capitalize(), f"{value:+.1f}", delta_color="normal")
        i += 1
    st.markdown("#### Details Summary")
    for k, v in details.items():
        st.write(f"**{k}:** {v}")

# ============================================================
# Backtest selected instrument
# ============================================================
bt = run_backtest(df, selected_symbol)
if bt:
    st.markdown("#### ًں“ˆ Backtest (Last 500 Bars)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trades", bt['total_trades'])
    c2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    c3.metric("Average R", f"{bt['avg_r']:.2f}")
    c4.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

# ============================================================
# Chart
# ============================================================
st.markdown("---")
st.markdown("### ًں“ˆ Price Chart")
df_smc = detect_smc_ict(df)
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(color='red', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)
# SMC annotations
if df_smc['ob_bullish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1], text="OB+", showarrow=True, arrowhead=1, row=1, col=1)
if df_smc['ob_bearish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1], text="OB-", showarrow=True, arrowhead=1, row=1, col=1)
if sl and entry:
    fig.add_hline(y=sl, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=sl, text="SL", showarrow=True, arrowhead=1, row=1, col=1)
    fig.add_hline(y=entry, line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=entry, text="Entry", showarrow=True, arrowhead=1, row=1, col=1)
# RSI
fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
# MACD
fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
fig.add_bar(x=df.index, y=df['macd_hist'], name='Histogram', marker_color='gray', opacity=0.3, row=3, col=1)
fig.update_layout(height=800, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# Trade Management
# ============================================================
st.markdown("---")
st.markdown("### ًں’¼ Trade Management")
if active_trade:
    st.success(f"ًں”’ Active trade locked: {active_trade['direction']} â€” It will not change until TP3 or SL")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ط§ظ„ط¯ط®ظˆظ„", price_fmt.format(active_trade['entry']))
    c2.metric("SL", price_fmt.format(active_trade['stop']))
    c3.metric("TP3", price_fmt.format(active_trade['tp3']))
    c4.metric("Confidence at Open", f"{active_trade['confidence']:.0f}%")
else:
    st.info("No active trade â€” the system is scanning for a new opportunity within the daily limit and cooldown.")

if st.session_state.closed_trades:
    hist = pd.DataFrame(st.session_state.closed_trades[-20:])
    st.dataframe(hist[["pair", "direction", "entry", "stop", "tp3", "exit", "result", "opened_at", "closed_at"]], hide_index=True, use_container_width=True)


# ============================================================
# Footer
# ============================================================
st.markdown(f"""
<div class="footer">
    <span class="brand">â–² BLACK PYRAMID v2003</span> â€¢ Regime â€¢ Structure â€¢ Liquidity â€¢ SMC â€¢ MTF â€¢ DXY â€¢ Risk â€¢ Backtest<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
