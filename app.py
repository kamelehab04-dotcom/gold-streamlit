# ============================================================
# BLACK PYRAMID v2003 – ULTRA PRECISION ENGINE
# Optimized for 1-3 Trades Daily with All Pairs
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

st.set_page_config(
    page_title="Black Pyramid v2003 - Ultra",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CSS --------------------
st.markdown("""
<style>
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0a0a !important; }
.price-card, .suggested-trade { background: rgba(10,10,10,0.8); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.1); border-radius: 12px; padding: 15px; }
.suggested-trade { border-color: #00ff88; }
.footer { text-align: center; color: #444; font-size: 0.65rem; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------
st.markdown("""
<div style="text-align: right; padding: 10px 25px; background: rgba(0,0,0,0.5); border-radius: 12px; margin-bottom: 15px; border: 1px solid rgba(255,215,0,0.08);">
    <div style="font-size: 1.2rem; color: #ffd700; font-weight: 700; letter-spacing: 2px;">
        ▲ BLACK PYRAMID v2003 ▲
    </div>
    <div style="font-size: 0.55rem; color: #666; letter-spacing: 1px;">
        Ultra Precision • All Pairs • 1-3 Trades Daily
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------- CONSTANTS --------------------
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
BACKTEST_LOOKBACK = 500
MIN_CONFIDENCE = 42
BUY_THRESHOLD = 8
SELL_THRESHOLD = -8
COOLDOWN_BARS = 4
MAX_TRADES_PER_DAY = 3

# -------------------- ALL PAIRS --------------------
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

# -------------------- SESSION STATE --------------------
if "all_signals" not in st.session_state:
    st.session_state.all_signals = None
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
if "active_trades" not in st.session_state:
    st.session_state.active_trades = {}
if "closed_trades" not in st.session_state:
    st.session_state.closed_trades = []
if "trade_stats" not in st.session_state:
    st.session_state.trade_stats = {"day": None, "count": 0, "last_closed_bar": {}}

# -------------------- DATA FETCHING --------------------
@st.cache_data(ttl=60)
def get_spot_price(symbol="GC=F"):
    try:
        t = yf.Ticker(symbol)
        data = t.history(period="1d", interval="5m")
        if not data.empty:
            last = data.iloc[-1]; first = data.iloc[0]
            change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
            return float(last['Close']), float(change)
    except: pass
    return None, None

@st.cache_data(ttl=300)
def get_historical_data(symbol, period="1mo", interval="1h"):
    alt = {"GC=F": ["XAUUSD=X"], "SI=F": ["XAGUSD=X"], "DX-Y.NYB": ["DX=F"]}
    for sym in [symbol] + alt.get(symbol, []):
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]
                return df
        except: continue
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
    if dt is None: return "N/A"
    diff = dt - datetime.now(pytz.timezone('US/Eastern'))
    if diff.total_seconds() < 0: return "Expired"
    h = int(diff.total_seconds() // 3600)
    m = int((diff.total_seconds() % 3600) // 60)
    return f"{h}h {m}m"

# -------------------- INDICATORS --------------------
def calc_rsi(data, period=14):
    delta = data.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
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
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx.fillna(0), plus_di.fillna(0), minus_di.fillna(0)

def calc_ichimoku(df):
    high, low = df['high'], df['low']
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    return tenkan, kijun, senkou_a, senkou_b

def calc_mfi(df, period=14):
    typical = (df['high'] + df['low'] + df['close']) / 3
    flow = typical * df['volume']
    pos = flow.where(typical > typical.shift(), 0).rolling(period).sum()
    neg = flow.where(typical < typical.shift(), 0).rolling(period).sum()
    return 100 - (100 / (1 + pos / neg))

def calc_vwap(df):
    return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

# -------------------- SMC --------------------
def find_swings(df, order=5):
    highs = df['high'].values
    lows = df['low'].values
    peaks = []; troughs = []
    for i in range(order, len(df) - order):
        if all(highs[i] > highs[i-j] for j in range(1, order+1)) and all(highs[i] > highs[i+j] for j in range(1, order+1)):
            peaks.append((i, highs[i]))
        if all(lows[i] < lows[i-j] for j in range(1, order+1)) and all(lows[i] < lows[i+j] for j in range(1, order+1)):
            troughs.append((i, lows[i]))
    return peaks, troughs

def detect_smc_ict(df):
    df = df.copy()
    df['ob_bullish'] = False; df['ob_bearish'] = False
    df['fvg_bullish'] = False; df['fvg_bearish'] = False
    df['liquidity_sweep_bullish'] = False; df['liquidity_sweep_bearish'] = False
    df['bos_bullish'] = False; df['bos_bearish'] = False
    df['mss_bullish'] = False; df['mss_bearish'] = False

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

# -------------------- TBS --------------------
def detect_tbs_correct(df, lookback=20, body_mult=1.5):
    if len(df) < lookback + 2: return None, None, None, None
    last = df.iloc[-1]
    lookback_high = df['high'].iloc[-lookback-1:-1].max()
    lookback_low = df['low'].iloc[-lookback-1:-1].min()
    avg_body = abs(df['close'] - df['open']).iloc[-lookback-1:-1].mean()
    current_body = abs(last['close'] - last['open'])
    if current_body < avg_body * body_mult: return None, None, None, None
    if last['high'] > lookback_high and last['close'] < lookback_high:
        return "BEARISH", last['close'], last['high'], lookback_high
    elif last['low'] < lookback_low and last['close'] > lookback_low:
        return "BULLISH", last['close'], last['low'], lookback_low
    return None, None, None, None

# -------------------- DXY --------------------
def get_dxy_correlation(df_pair, df_dxy, lookback=50):
    if df_pair is None or df_dxy is None or len(df_pair) < lookback: return 0.0
    pair = df_pair[['close']].pct_change().dropna()
    dxy = df_dxy[['close']].pct_change().dropna()
    combined = pd.concat([pair, dxy], axis=1, join='inner').dropna()
    if len(combined) < lookback: return 0.0
    return float(combined.iloc[-lookback:, 0].corr(combined.iloc[-lookback:, 1]) or 0.0)

def apply_dxy_filter(signal, net_score, dxy_signal, correlation):
    adjustment = 0; status = "NEUTRAL"
    if dxy_signal is None or dxy_signal == "WAIT" or signal == "WAIT":
        return net_score, status, 0
    if abs(correlation) < 0.30: return net_score, "WEAK_CORRELATION", 0
    if correlation <= -0.60:
        aligned = (signal == "BUY" and dxy_signal == "SELL") or (signal == "SELL" and dxy_signal == "BUY")
        adjustment = 5 if aligned else -6; status = "STRONGLY_ALIGNED" if aligned else "MISALIGNED"
    elif correlation >= 0.60:
        aligned = signal == dxy_signal
        adjustment = 5 if aligned else -6; status = "STRONGLY_ALIGNED" if aligned else "MISALIGNED"
    else:
        aligned = (signal == "BUY" and dxy_signal == "SELL") if correlation < 0 else signal == dxy_signal
        adjustment = 2 if aligned else -3; status = "ALIGNED" if aligned else "MISALIGNED"
    return net_score + adjustment, status, adjustment

# -------------------- REGIME & MTF --------------------
def detect_regime(df):
    last = df.iloc[-1]
    adx = last['adx'] if 'adx' in df.columns else 20
    ema20 = last['ema20'] if 'ema20' in df.columns else df['close'].iloc[-1]
    ema50 = last['ema50'] if 'ema50' in df.columns else df['close'].iloc[-1]
    atr = last['atr'] if 'atr' in df.columns else 10
    atr_ma = df['atr'].iloc[-20:].mean() if 'atr' in df.columns else atr
    regime = "NEUTRAL"
    if adx > 25 and abs(ema20 - ema50) / ema50 > 0.01: regime = "TRENDING"
    elif adx < 20: regime = "RANGING"
    if atr > atr_ma * 1.5: regime = "HIGH_VOLATILITY" if regime == "NEUTRAL" else regime + "_HIGH_VOL"
    elif atr < atr_ma * 0.7: regime = "LOW_VOLATILITY" if regime == "NEUTRAL" else regime + "_LOW_VOL"
    return regime

def mtf_analysis(df, symbol):
    timeframes = ['15m', '1h', '4h']
    results = []
    for tf in timeframes:
        try:
            data = get_historical_data(symbol, period="5d", interval=tf)
            if data is None or len(data) < 50: continue
            rsi = calc_rsi(data['close']).iloc[-1]
            ema20 = data['close'].ewm(20).mean().iloc[-1]
            ema50 = data['close'].ewm(50).mean().iloc[-1]
            trend = "NEUTRAL"
            if ema20 > ema50 and rsi > 50: trend = "BULLISH"
            elif ema20 < ema50 and rsi < 50: trend = "BEARISH"
            results.append(trend)
        except: continue
    buy = results.count("BULLISH"); sell = results.count("BEARISH")
    if buy > sell: return "BUY", buy - sell
    elif sell > buy: return "SELL", sell - buy
    else: return "NEUTRAL", 0

# -------------------- CALCULATE ALL INDICATORS --------------------
def calculate_all_indicators(df):
    if df is None or len(df) < 20: return df
    df = df.copy()
    df['ema20'] = df['close'].ewm(20).mean()
    df['ema50'] = df['close'].ewm(50).mean()
    df['ema200'] = df['close'].ewm(200).mean()
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], _ = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
    tenkan, kijun, senkou_a, senkou_b = calc_ichimoku(df)
    df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
    df['mfi'] = calc_mfi(df)
    df['vwap'] = calc_vwap(df)
    smc = detect_smc_ict(df)
    for col in ['ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                'liquidity_sweep_bullish','liquidity_sweep_bearish',
                'bos_bullish','bos_bearish','mss_bullish','mss_bearish']:
        df[col] = smc[col]
    return df

# -------------------- ORIGINAL SIGNAL ENGINE (v2003) --------------------
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
    tenkan, kijun, senkou_a, senkou_b = calc_ichimoku(df)
    df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
    df['mfi'] = calc_mfi(df)
    df['vwap'] = calc_vwap(df)

    df_smc = detect_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    tbs_type, _, _, _ = detect_tbs_correct(df)
    regime = detect_regime(df)
    mtf_consensus, mtf_count = mtf_analysis(df, symbol)

    last = df.iloc[-1]
    current_price = last['close']

    factors = {"structure":0.0, "liquidity":0.0, "smc":0.0, "mtf":0.0, "dxy":0.0,
               "momentum":0.0, "volatility":0.0, "pattern":0.0, "volume":0.0}
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
    else: details['SMC'] = "No SMC"

    if mtf_consensus == "BUY":
        factors['mtf'] += 15.0; details['MTF'] = f"Bullish ({mtf_count})"
    elif mtf_consensus == "SELL":
        factors['mtf'] -= 15.0; details['MTF'] = f"Bearish ({mtf_count})"
    else: details['MTF'] = "Neutral"

    if dxy_signal not in [None, "WAIT"]:
        raw_dir = "BUY" if (factors['structure'] + factors['liquidity'] + factors['smc'] + factors['mtf']) > 0 else "SELL"
        if raw_dir == "WAIT": raw_dir = "BUY" if factors['structure'] > 0 else "SELL"
        adj_score, status, adj = apply_dxy_filter(raw_dir, 0, dxy_signal, dxy_correlation)
        factors['dxy'] = float(adj); details['DXY'] = f"{status} (تعديل: {adj})"
    else: details['DXY'] = "No DXY"

    if last['rsi'] < 30:
        factors['momentum'] += 10.0; details['Momentum'] = f"Oversold RSI={last['rsi']:.1f}"
    elif last['rsi'] > 70:
        factors['momentum'] -= 10.0; details['Momentum'] = f"Overbought RSI={last['rsi']:.1f}"
    else:
        factors['momentum'] += (50 - last['rsi']) / 10.0; details['Momentum'] = f"RSI {last['rsi']:.1f}"
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
    else: details['Volume'] = f"MFI {last['mfi']:.1f}"

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

    stop_loss = None; entry_price = current_price; targets = {}
    if signal in ["BUY","SELL"] and confidence >= MIN_CONFIDENCE:
        atr_val = last['atr'] if not pd.isna(last['atr']) else 10.0
        if signal == "BUY":
            struct_low = df['low'].iloc[-10:].min()
            ob_low = df['low'].iloc[-5:].min()
            stop_loss = max(min(struct_low, ob_low, current_price - atr_val * 1.5), current_price - atr_val * 3)
        else:
            struct_high = df['high'].iloc[-10:].max()
            ob_high = df['high'].iloc[-5:].max()
            stop_loss = min(max(struct_high, ob_high, current_price + atr_val * 1.5), current_price + atr_val * 3)
        risk = abs(entry_price - stop_loss)
        if risk < atr_val * 0.3:
            stop_loss = entry_price - atr_val * 0.5 if signal == "BUY" else entry_price + atr_val * 0.5
            risk = atr_val * 0.5
        if signal == "BUY":
            targets = {'target1': entry_price + risk, 'target2': entry_price + risk * 1.5,
                       'target3': entry_price + risk * 2.0, 'risk_reward': 2.0}
        else:
            targets = {'target1': entry_price - risk, 'target2': entry_price - risk * 1.5,
                       'target3': entry_price - risk * 2.0, 'risk_reward': 2.0}

    return signal, confidence, total_score, details, factors, regime, mtf_consensus, mtf_count, stop_loss, entry_price, targets, (tbs_type,None,None,None)

# -------------------- ULTRA SIGNAL ENGINE (معدل لظهور صفقات) --------------------
def generate_ultra_signal(df_4h, df_1h, df_15m, symbol, dxy_signal=None, dxy_correlation=0.0):
    """
    نظام مرن جداً يضمن ظهور صفقات.
    يعتمد على الإشارة الأصلية + بعض المرشحات الخفيفة.
    """
    # 1. الإشارة الأصلية (على 1H)
    original_signal, original_conf, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets, tbs_info = generate_signal_v2003(
        df_1h, symbol, dxy_signal, dxy_correlation
    )

    # إذا كانت الإشارة الأصلية WAIT، نعيدها فوراً
    if original_signal == "WAIT":
        return "WAIT", original_conf, "الإشارة الأصلية WAIT", details, targets, sl, entry

    # 2. تحليل سريع للطبقات (خفيف جداً)
    # 2.1 4H Bias (نحاول استخراجه)
    bias = "NEUTRAL"
    if df_4h is not None and len(df_4h) > 50:
        last4 = df_4h.iloc[-1]
        ema20_4 = last4['ema20'] if 'ema20' in df_4h.columns else df_4h['close'].iloc[-1]
        ema50_4 = last4['ema50'] if 'ema50' in df_4h.columns else df_4h['close'].iloc[-1]
        if ema20_4 > ema50_4:
            bias = "BULLISH"
        elif ema20_4 < ema50_4:
            bias = "BEARISH"
    
    # 2.2 1H Confirmation (خفيف)
    confirmed = True
    conf_reason = "1H مقبول"
    if df_1h is not None and len(df_1h) > 50:
        last1 = df_1h.iloc[-1]
        ema20_1 = last1['ema20'] if 'ema20' in df_1h.columns else df_1h['close'].iloc[-1]
        ema50_1 = last1['ema50'] if 'ema50' in df_1h.columns else df_1h['close'].iloc[-1]
        if original_signal == "BUY" and ema20_1 < ema50_1:
            confirmed = False
            conf_reason = "1H EMA يخالف (لكن الإشارة قوية)"
        elif original_signal == "SELL" and ema20_1 > ema50_1:
            confirmed = False
            conf_reason = "1H EMA يخالف (لكن الإشارة قوية)"
        # إذا كانت الإشارة الأصلية قوية > 70، نتجاوز هذا الشرط
        if original_conf >= 70:
            confirmed = True
            conf_reason = "1H تم تجاوزه بسبب قوة الإشارة"

    # 2.3 15M Trigger (خفيف جداً)
    triggered = True
    trigger_reason = "15M مقبول"
    if df_15m is not None and len(df_15m) > 30:
        last15 = df_15m.iloc[-1]
        # نبحث عن أي إشارة SMC بسيطة
        has_bos = last15.get('bos_bullish', False) or last15.get('bos_bearish', False)
        has_mss = last15.get('mss_bullish', False) or last15.get('mss_bearish', False)
        has_liquidity = last15.get('liquidity_sweep_bullish', False) or last15.get('liquidity_sweep_bearish', False)
        if original_signal == "BUY" and not (has_bos or has_mss or has_liquidity):
            triggered = False
            trigger_reason = "لا يوجد Trigger صاعد (لكن الإشارة قوية)"
        elif original_signal == "SELL" and not (has_bos or has_mss or has_liquidity):
            triggered = False
            trigger_reason = "لا يوجد Trigger هابط (لكن الإشارة قوية)"
        # إذا كانت الإشارة > 70، نتجاوز
        if original_conf >= 70:
            triggered = True
            trigger_reason = "15M تم تجاوزه بسبب قوة الإشارة"

    # 2.4 Regime (لا نمنع أبداً، فقط نلاحظ)
    regime_status, _ = "TRENDING", "طبيعي"
    if df_4h is not None and len(df_4h) > 50:
        regime_status = detect_regime(df_4h)

    # 3. قرار الإشارة النهائية (مرن جداً)
    if original_signal in ["BUY", "SELL"] and original_conf >= MIN_CONFIDENCE:
        # نسمح بالدخول حتى لو فشلت بعض الطبقات، طالما الثقة > 55
        if original_conf > 55:
            # نعدل الثقة بناءً على عدد الطبقات المتوافقة
            support_points = 0
            if bias != "NEUTRAL" and ((original_signal == "BUY" and bias == "BULLISH") or (original_signal == "SELL" and bias == "BEARISH")):
                support_points += 1
            if confirmed:
                support_points += 1
            if triggered:
                support_points += 1
            if regime_status not in ["RANGING", "LOW_VOL"]:
                support_points += 1

            new_conf = min(95, original_conf + support_points * 2)
            reason = f"{original_signal} — مؤكد ({support_points}/4 دعم)"

            # تحديث التفاصيل
            details['Ultra_Bias'] = bias
            details['Ultra_Confirmation'] = conf_reason
            details['Ultra_Trigger'] = trigger_reason
            details['Ultra_Regime'] = regime_status
            details['Support_Points'] = f"{support_points}/4"

            return original_signal, new_conf, reason, details, targets, sl, entry

    return "WAIT", original_conf, "الثقة منخفضة", details, targets, sl, entry

# -------------------- BACKTEST --------------------
def _bar_exit(direction, bar, stop, tp):
    if direction == "BUY":
        if bar['low'] <= stop: return "SL", stop
        if bar['high'] >= tp: return "TP", tp
    else:
        if bar['high'] >= stop: return "SL", stop
        if bar['low'] <= tp: return "TP", tp
    return None, None

def run_backtest(df, symbol, lookback=500):
    if df is None or len(df) < 150: return {}
    test_df = df.iloc[-min(lookback, len(df)):].copy()
    test_df = calculate_all_indicators(test_df)
    trades = []; active = None; daily_count = {}
    for i in range(100, len(test_df) - 1):
        bar = test_df.iloc[i]
        day = str(bar.name.date()) if hasattr(bar.name, 'date') else str(i)
        if active:
            result, exit_price = _bar_exit(active['direction'], bar, active['stop'], active['tp'])
            if result:
                risk = abs(active['entry'] - active['stop'])
                reward = abs(exit_price - active['entry']) / risk if risk > 0 else 0
                trades.append({'result': result, 'r': reward if result == 'TP' else -1,
                               'direction': active['direction'], 'entry_i': active['entry_i'], 'exit_i': i})
                active = None
            else: continue
        if daily_count.get(day, 0) >= MAX_TRADES_PER_DAY: continue
        window = test_df.iloc[:i+1].copy()
        signal, conf, _, _, _, _, _, _, sl, entry, targets, _ = generate_signal_v2003(
            window, symbol, dxy_signal=None, dxy_correlation=0.0
        )
        if signal == "WAIT" or conf < MIN_CONFIDENCE or sl is None or not targets: continue
        next_open = float(test_df['open'].iloc[i+1])
        stop = float(sl); tp = float(targets.get('target2'))
        if (signal == 'BUY' and stop >= next_open) or (signal == 'SELL' and stop <= next_open): continue
        active = {'direction':signal, 'entry':next_open, 'stop':stop, 'tp':tp, 'entry_i':i+1}
        daily_count[day] = daily_count.get(day, 0) + 1
    if not trades: return {}
    wins = [t for t in trades if t['result'] == 'win']; losses = [t for t in trades if t['result'] == 'loss']
    gross_win = sum(t['r'] for t in wins); gross_loss = abs(sum(t['r'] for t in losses))
    return {
        'total_trades': len(trades),
        'win_rate': len(wins)/len(trades)*100,
        'avg_r': sum(t['r'] for t in trades)/len(trades),
        'profit_factor': gross_win/gross_loss if gross_loss>0 else float('inf'),
        'wins': len(wins), 'losses': len(losses)
    }

# -------------------- COLLECT SIGNALS (للجدول) --------------------
@st.cache_data(ttl=120)
def get_all_signals_ultra():
    results = []
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    df_dxy = calculate_all_indicators(df_dxy)
    dxy_signal = None
    if df_dxy is not None and len(df_dxy) > 20:
        dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_v2003(df_dxy, "DX-Y.NYB")

    for pair_name, symbol in PAIRS.items():
        try:
            df_4h = get_historical_data(symbol, period="1mo", interval="4h")
            df_1h = get_historical_data(symbol, period="1mo", interval="1h")
            df_15m = get_historical_data(symbol, period="7d", interval="15m")
            if df_4h is None or df_1h is None or df_15m is None: continue

            df_4h = calculate_all_indicators(df_4h)
            df_1h = calculate_all_indicators(df_1h)
            df_15m = calculate_all_indicators(df_15m)

            corr = get_dxy_correlation(df_1h, df_dxy, lookback=50)

            signal, conf, reason, details, targets, sl, entry = generate_ultra_signal(
                df_4h, df_1h, df_15m, symbol, dxy_signal, corr
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

# -------------------- ACTIVE TRADE MANAGER --------------------
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
    if not trade or df is None or df.empty: return None
    bar = df.iloc[-1]
    if trade["direction"] == "BUY":
        hit_sl = bar['low'] <= trade['stop']
        hit_tp3 = bar['high'] >= trade['tp3']
    else:
        hit_sl = bar['high'] >= trade['stop']
        hit_tp3 = bar['low'] <= trade['tp3']
    result = None; exit_price = None
    if hit_sl: result, exit_price = "SL", trade['stop']
    elif hit_tp3: result, exit_price = "TP3", trade['tp3']
    if result:
        closed = trade.copy()
        closed.update({"closed_at": datetime.now().isoformat(), "result": result, "exit": float(exit_price)})
        st.session_state.closed_trades.append(closed)
        del st.session_state.active_trades[symbol]
        st.session_state.trade_stats["last_closed_bar"][symbol] = len(df) - 1
        return closed
    return None

# -------------------- STREAMLIT UI --------------------
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
    st.markdown("### 📋 All Signals")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh All", use_container_width=True):
            with st.spinner("Analyzing..."):
                st.session_state.all_signals = get_all_signals_ultra()
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

# -------------------- LOAD SELECTED INSTRUMENT DATA --------------------
price, change = get_spot_price(selected_symbol)

df_4h = get_historical_data(selected_symbol, period="1mo", interval="4h")
df_1h = get_historical_data(selected_symbol, period="1mo", interval="1h")
df_15m = get_historical_data(selected_symbol, period="7d", interval="15m")

if df_4h is None or df_1h is None or df_15m is None:
    st.error("Failed to load data")
    st.stop()

if price is None:
    price = df_15m['close'].iloc[-1]
    change = 0

df_4h = calculate_all_indicators(df_4h)
df_1h = calculate_all_indicators(df_1h)
df_15m = calculate_all_indicators(df_15m)

df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
df_dxy = calculate_all_indicators(df_dxy)
dxy_signal = None
corr = 0.0
if df_dxy is not None and len(df_dxy) > 20:
    dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_v2003(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df_1h, df_dxy, lookback=50)

signal, confidence, reason, details, targets, sl, entry = generate_ultra_signal(
    df_4h, df_1h, df_15m, selected_symbol, dxy_signal, corr
)

# -------------------- DISPLAY --------------------
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
    </div>
    """, unsafe_allow_html=True)

if signal != "WAIT":
    direction_text = "BUY" if signal=="BUY" else "SELL"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>Direction:</b> {direction_text} <span style="color:#00ff88;">(Confidence: {confidence:.0f}%)</span><br>
        <b>📍 Entry:</b> {price_fmt.format(entry)}<br>
        <b>🛑 Stop Loss:</b> {price_fmt.format(sl)}<br>
        <div class="target-zone"><b>🎯 TP1 (1R):</b> {price_fmt.format(targets['target1'])}</div>
        <div class="target-zone" style="border-left-color:#ffaa00;"><b>🎯 TP2 (1.5R):</b> {price_fmt.format(targets['target2'])}</div>
        <div class="target-zone" style="border-left-color:#00ff88;"><b>🎯 TP3 (2R):</b> {price_fmt.format(targets['target3'])}</div>
        <b>📈 R:R</b> 1:{targets.get('risk_reward',0):.1f}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Layer Details", expanded=True):
        for key, value in details.items():
            st.write(f"**{key}:** {value}")

else:
    st.warning(f"🟡 WAIT — {reason}")

# -------------------- BACKTEST --------------------
bt = run_backtest(df_1h, selected_symbol)
if bt:
    st.markdown("#### 📈 Backtest (Last 500 Bars)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Trades", bt['total_trades'])
    c2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    c3.metric("Average R", f"{bt['avg_r']:.2f}")
    c4.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

# -------------------- CHART --------------------
st.markdown("---")
st.markdown("### 📈 Price Chart (15M)")

df_smc = detect_smc_ict(df_15m)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['close'], name='Price', line=dict(color='gold')))
if 'ema20' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['ema20'], name='EMA20', line=dict(dash='dash')))
if 'ema50' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['ema50'], name='EMA50', line=dict(dash='dash')))
if sl and entry:
    fig.add_hline(y=sl, line_dash='dash', line_color='red', annotation_text="SL")
    fig.add_hline(y=entry, line_dash='dash', line_color='green', annotation_text="Entry")
fig.update_layout(template='plotly_dark', height=450)
st.plotly_chart(fig, use_container_width=True)

# -------------------- TRADE MANAGEMENT --------------------
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

# -------------------- FOOTER --------------------
st.markdown(f"""
<div class="footer">
    <span class="brand">▲ BLACK PYRAMID v2003</span> • Ultra Precision • All Pairs • 1-3 Trades Daily<br>
    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
