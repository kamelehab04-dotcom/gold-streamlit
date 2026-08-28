# ============================================================
# BLACK PYRAMID v2003 – LIGHTNING EDITION
# Optimized for speed & low memory usage
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
import time
from typing import Dict, Tuple, List, Optional
import functools

st.set_page_config(page_title="Black Pyramid v2003", page_icon="▲", layout="wide", initial_sidebar_state="expanded")

# -------------------- CSS (مختصر) --------------------
st.markdown("""
<style>
* { font-family: 'Inter', sans-serif; }
.main-title, .price-value { font-family: 'Orbitron', sans-serif !important; letter-spacing: 2px; }
.stApp { background: #0a0a0a !important; }
.price-card, .signal-box, .suggested-trade { background: rgba(10,10,10,0.75); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.1); border-radius: 12px; padding: 10px; }
.suggested-trade { border-color: #00ff88; }
.target-zone { border-left: 4px solid #ffd700; padding: 4px 8px; margin: 2px 0; }
.stop-loss { border-left: 4px solid #ff4444; }
.footer { text-align: center; color: #444; font-size: 0.65rem; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# -------------------- API & CONSTANTS --------------------
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
BACKTEST_LOOKBACK = 500
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

# -------------------- SESSION STATE --------------------
if "all_signals" not in st.session_state: st.session_state.all_signals = None
if "last_update" not in st.session_state: st.session_state.last_update = datetime.now()
if "active_trades" not in st.session_state: st.session_state.active_trades = {}
if "closed_trades" not in st.session_state: st.session_state.closed_trades = []
if "trade_stats" not in st.session_state: st.session_state.trade_stats = {"day": None, "count": 0, "last_closed_bar": {}}
if "df_cache" not in st.session_state: st.session_state.df_cache = {}

# -------------------- DATA FETCHING (مع تخزين مؤقت قوي) --------------------
@st.cache_data(ttl=60)
def get_spot_price(symbol="GC=F"):
    if symbol == "GC=F" and GOLD_API_KEY:
        try:
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            r = requests.get("https://www.goldapi.io/api/XAU/USD", headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json(); return float(d['price']), float(d['change_percent'])
        except: pass
    if symbol == "SI=F" and GOLD_API_KEY:
        try:
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            r = requests.get("https://www.goldapi.io/api/XAG/USD", headers=headers, timeout=5)
            if r.status_code == 200:
                d = r.json(); return float(d['price']), float(d['change_percent'])
        except: pass
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
    alt = {"GC=F": ["XAUUSD=X", "GOLD"], "SI=F": ["XAGUSD=X", "SILVER"], "DX-Y.NYB": ["DX=F", "DXY"], "BTC-USD": ["BTCUSD=X"], "ETH-USD": ["ETHUSD=X"]}
    for sym in [symbol] + alt.get(symbol, []):
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]
                return df
        except: continue
    return None

# -------------------- INDICATORS (سريعة) --------------------
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

# -------------------- SMC ICT (vectorized بالكامل) --------------------
def detect_smc_ict_vectorized(df):
    df = df.copy()
    # Order Blocks
    body = (df['close'] - df['open']).abs()
    avg_range = (df['high'].rolling(3).max() - df['low'].rolling(3).min()) / 3
    bull_body = (df['close'] > df['open']) & (body > avg_range)
    bear_body = (df['close'] < df['open']) & (body > avg_range)
    df['ob_bullish'] = bull_body & (df['close'].shift(1) < df['open'].shift(1))
    df['ob_bearish'] = bear_body & (df['close'].shift(1) > df['open'].shift(1))
    
    # FVG (Fair Value Gaps)
    df['fvg_bullish'] = (df['low'] > df['high'].shift(2))
    df['fvg_bearish'] = (df['high'] < df['low'].shift(2))
    
    # Liquidity Sweeps (lookback 10)
    rolling_low = df['low'].rolling(10, min_periods=1).min()
    rolling_high = df['high'].rolling(10, min_periods=1).max()
    df['liquidity_sweep_bullish'] = (df['low'] < rolling_low.shift(1))
    df['liquidity_sweep_bearish'] = (df['high'] > rolling_high.shift(1))
    
    # BOS (Break of Structure) – lookback 5
    rolling_high_5 = df['high'].rolling(5, min_periods=1).max()
    rolling_low_5 = df['low'].rolling(5, min_periods=1).min()
    df['bos_bullish'] = (df['close'] > rolling_high_5.shift(1))
    df['bos_bearish'] = (df['close'] < rolling_low_5.shift(1))
    
    # MSS (Market Structure Shift)
    df['mss_bullish'] = df['bos_bearish'].shift(1) & (df['close'] > df['high'].rolling(2).max().shift(1))
    df['mss_bearish'] = df['bos_bullish'].shift(1) & (df['close'] < df['low'].rolling(2).min().shift(1))
    
    return df

# -------------------- TBS (محسّن) --------------------
def detect_tbs_correct(df, lookback=20, body_mult=1.5):
    if len(df) < lookback + 2: return None, None, None, None
    last = df.iloc[-1]
    lookback_high = df['high'].iloc[-lookback-1:-1].max()
    lookback_low = df['low'].iloc[-lookback-1:-1].min()
    avg_body = abs(df['close'] - df['open']).iloc[-lookback-1:-1].mean()
    current_body = abs(last['close'] - last['open'])
    if current_body < avg_body * body_mult: return None, None, None, None
    if last['high'] > lookback_high and last['close'] < lookback_high:
        return "BEARISH", last['close'], last['low'], lookback_high
    elif last['low'] < lookback_low and last['close'] > lookback_low:
        return "BULLISH", last['close'], last['high'], lookback_low
    return None, None, None, None

# -------------------- DXY --------------------
def get_dxy_correlation(df_pair, df_dxy, lookback=50):
    if df_pair is None or df_dxy is None or len(df_pair) < lookback or len(df_dxy) < lookback:
        return 0.0
    pair = df_pair[['close']].pct_change().dropna()
    dxy = df_dxy[['close']].pct_change().dropna()
    combined = pd.concat([pair, dxy], axis=1, join='inner').dropna()
    if len(combined) < lookback: return 0.0
    return float(combined.iloc[-lookback:, 0].corr(combined.iloc[-lookback:, 1]) or 0.0)

def apply_dxy_filter(signal, net_score, dxy_signal, correlation):
    if dxy_signal is None or dxy_signal == "WAIT" or signal == "WAIT":
        return net_score, "NEUTRAL", 0
    if abs(correlation) < 0.30:
        return net_score, "WEAK_CORRELATION", 0
    if correlation <= -0.60:
        aligned = (signal == "BUY" and dxy_signal == "SELL") or (signal == "SELL" and dxy_signal == "BUY")
        adj = 5 if aligned else -6
        status = "STRONGLY_ALIGNED" if aligned else "MISALIGNED"
    elif correlation >= 0.60:
        aligned = signal == dxy_signal
        adj = 5 if aligned else -6
        status = "STRONGLY_ALIGNED" if aligned else "MISALIGNED"
    else:
        aligned = (signal == "BUY" and dxy_signal == "SELL") if correlation < 0 else signal == dxy_signal
        adj = 2 if aligned else -3
        status = "ALIGNED" if aligned else "MISALIGNED"
    return net_score + adj, status, adj

# -------------------- REGIME (سريع) --------------------
def detect_regime_from_indicators(adx, ema20, ema50, atr, atr_ma):
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

# -------------------- MTF (بيانات جاهزة) --------------------
def mtf_consensus_from_dataframes(df_15m, df_1h, df_4h):
    results = []
    for tf, df in [("15m", df_15m), ("1h", df_1h), ("4h", df_4h)]:
        if df is not None and len(df) > 50:
            rsi = calc_rsi(df['close']).iloc[-1]
            ema20 = df['close'].ewm(20).mean().iloc[-1]
            ema50 = df['close'].ewm(50).mean().iloc[-1]
            trend = "BULLISH" if (ema20 > ema50 and rsi > 50) else "BEARISH" if (ema20 < ema50 and rsi < 50) else "NEUTRAL"
            results.append(trend)
    buy = results.count("BULLISH")
    sell = results.count("BEARISH")
    if buy > sell: return "BUY", buy - sell
    elif sell > buy: return "SELL", sell - buy
    else: return "NEUTRAL", 0

# -------------------- إشارة سريعة (بدون إعادة حساب المؤشرات) --------------------
def generate_signal_fast(df, symbol, dxy_signal=None, dxy_correlation=0.0,
                         df_15m=None, df_1h=None, df_4h=None):
    if df is None or len(df) < 100:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, (None,None,None,None)
    
    # المؤشرات محسوبة مسبقاً في df
    last = df.iloc[-1]
    current_price = last['close']
    
    # SMC (محسوب مسبقاً)
    smc_cols = ['ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                'liquidity_sweep_bullish','liquidity_sweep_bearish',
                'bos_bullish','bos_bearish','mss_bullish','mss_bearish']
    last_smc = {c: last.get(c, False) for c in smc_cols}
    
    # TBS
    tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs_correct(df)
    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)
    
    # Regime
    adx = last['adx']
    ema20 = last['ema20']; ema50 = last['ema50']
    atr = last['atr']; atr_ma = df['atr'].iloc[-20:].mean() if 'atr' in df else atr
    regime = detect_regime_from_indicators(adx, ema20, ema50, atr, atr_ma)
    
    # MTF
    mtf_cons, mtf_count = mtf_consensus_from_dataframes(df_15m, df_1h, df_4h)
    
    # ===== FACTORS =====
    factors = {"structure":0.0,"liquidity":0.0,"smc":0.0,"mtf":0.0,"dxy":0.0,
               "momentum":0.0,"volatility":0.0,"pattern":0.0,"volume":0.0}
    details = {}
    
    # Structure
    if last_smc['bos_bullish'] or last_smc['mss_bullish']:
        factors['structure'] += 25.0; details['Structure'] = "Bullish BOS/MSS"
    elif last_smc['bos_bearish'] or last_smc['mss_bearish']:
        factors['structure'] -= 25.0; details['Structure'] = "Bearish BOS/MSS"
    else: details['Structure'] = "Neutral"
    
    # Liquidity
    if last_smc['liquidity_sweep_bullish']:
        factors['liquidity'] += 20.0; details['Liquidity'] = "Buy-side sweep"
    elif last_smc['liquidity_sweep_bearish']:
        factors['liquidity'] -= 20.0; details['Liquidity'] = "Sell-side sweep"
    else: details['Liquidity'] = "No sweep"
    
    # SMC
    if last_smc['ob_bullish'] or last_smc['fvg_bullish']:
        factors['smc'] += 20.0; details['SMC'] = "Bullish OB/FVG"
    elif last_smc['ob_bearish'] or last_smc['fvg_bearish']:
        factors['smc'] -= 20.0; details['SMC'] = "Bearish OB/FVG"
    else: details['SMC'] = "None"
    
    # MTF
    if mtf_cons == "BUY":
        factors['mtf'] += 15.0; details['MTF'] = f"Bullish ({mtf_count})"
    elif mtf_cons == "SELL":
        factors['mtf'] -= 15.0; details['MTF'] = f"Bearish ({mtf_count})"
    else: details['MTF'] = "Neutral"
    
    # DXY
    if dxy_signal not in [None, "WAIT"]:
        raw_dir = "BUY" if (factors['structure'] + factors['liquidity'] + factors['smc'] + factors['mtf']) > 0 else "SELL"
        if raw_dir == "WAIT": raw_dir = "BUY" if factors['structure'] > 0 else "SELL"
        adj_score, status, adj = apply_dxy_filter(raw_dir, 0, dxy_signal, dxy_correlation)
        factors['dxy'] = float(adj)
        details['DXY'] = f"{status} (تعديل: {adj})"
    else: details['DXY'] = "No DXY"
    
    # Momentum
    rsi = last['rsi']
    if rsi < 30:
        factors['momentum'] += 10.0; details['Momentum'] = f"Oversold RSI={rsi:.1f}"
    elif rsi > 70:
        factors['momentum'] -= 10.0; details['Momentum'] = f"Overbought RSI={rsi:.1f}"
    else:
        factors['momentum'] += (50 - rsi) / 10.0; details['Momentum'] = f"RSI {rsi:.1f}"
    if last['macd'] > last['macd_signal']: factors['momentum'] += 5.0
    else: factors['momentum'] -= 5.0
    
    # Volatility
    atr_ratio = atr / atr_ma if atr_ma > 0 else 1.0
    if atr_ratio > 1.5:
        factors['volatility'] -= 10.0; details['Volatility'] = "High"
    elif atr_ratio < 0.7:
        factors['volatility'] += 5.0; details['Volatility'] = "Low"
    else: details['Volatility'] = "Normal"
    
    # Pattern
    if tbs_type == "BULLISH":
        factors['pattern'] += 20.0; details['Pattern'] = "TBS BUY"
    elif tbs_type == "BEARISH":
        factors['pattern'] -= 20.0; details['Pattern'] = "TBS SELL"
    else: details['Pattern'] = "No TBS"
    
    # Volume (MFI)
    mfi = last['mfi']
    if mfi < 20:
        factors['volume'] += 5.0; details['Volume'] = f"MFI Oversold {mfi:.1f}"
    elif mfi > 80:
        factors['volume'] -= 5.0; details['Volume'] = f"MFI Overbought {mfi:.1f}"
    else: details['Volume'] = f"MFI {mfi:.1f}"
    
    total_score = sum(factors.values())
    
    # Signal
    if total_score >= BUY_THRESHOLD:
        signal = "BUY"; confidence = min(90, 50 + total_score * 0.5)
    elif total_score <= SELL_THRESHOLD:
        signal = "SELL"; confidence = min(90, 50 + abs(total_score) * 0.5)
    else:
        signal = "WAIT"; confidence = 50 + total_score * 0.2
    confidence = max(0, min(100, confidence))
    if "HIGH_VOL" in regime: confidence *= 0.9
    elif "LOW_VOL" in regime: confidence *= 1.1
    
    # Stop Loss & Targets
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
    
    return signal, confidence, total_score, details, factors, regime, mtf_cons, mtf_count, stop_loss, entry_price, targets, tbs_info

# -------------------- BACKTEST (محسّن) --------------------
def run_backtest_fast(df, symbol, lookback=BACKTEST_LOOKBACK):
    if df is None or len(df) < 150: return {}
    # نأخذ جزء من البيانات
    test_df = df.iloc[-min(lookback, len(df)):].copy()
    # نحسب المؤشرات مسبقاً على النطاق الكامل
    # لكننا سنستخدم الدالة generate_signal_fast التي تتطلب المؤشرات في df، لذا سنمرر df كاملاً مع المؤشرات
    # لكننا سنحاكي على نافذة متحركة، لكن لسرعة يمكننا استخدام مؤشرات محسوبة مسبقاً مع تحديث بسيط.
    # لحل هذا، سنقوم بحساب المؤشرات مرة واحدة على كامل test_df، ثم نمرر القيم الجاهزة.
    # لكن generate_signal_fast تتوقع أن تكون المؤشرات في df، لذا سنقوم بتمرير test_df كامل مع المؤشرات.
    # لكن بالنسبة للمؤشرات المتجددة مثل RSI و MACD، فإنها تعتمد على النافذة الكاملة، لذا نحتاج إلى حسابها على test_df بالكامل.
    # الطريقة الأسرع: حساب المؤشرات على test_df بالكامل، ثم في كل خطوة نأخذ الصف i كـ "آخر" صف، ولكن المؤشرات ستكون محسوبة على كل البيانات.
    # هذا يعطي نتائج مقبولة للاختبار الخلفي مع تسارع كبير.
    # سنقوم بحساب المؤشرات مرة واحدة على test_df.
    test_df = calculate_all_indicators(test_df)
    # الآن نمرر test_df كامل، لكن generate_signal_fast تستخدم df.iloc[-1] فقط، لذا سنمرر test_df.iloc[:i+1] في كل خطوة.
    trades = []; active = None; daily_count = {}
    for i in range(100, len(test_df) - 1):
        bar = test_df.iloc[i]
        day = str(bar.name.date()) if hasattr(bar.name, 'date') else str(i)
        if active:
            result, exit_price = _bar_exit(active['direction'], bar, active['stop'], active['tp'])
            if result:
                risk = abs(active['entry'] - active['stop'])
                reward = abs(exit_price - active['entry']) / risk if risk > 0 else 0
                trades.append({'result':'win' if result=='TP' else 'loss', 'r':reward if result=='TP' else -1,
                               'direction':active['direction'], 'entry_i':active['entry_i'], 'exit_i':i})
                active = None
            else:
                continue
        if daily_count.get(day, 0) >= MAX_TRADES_PER_DAY: continue
        window = test_df.iloc[:i+1].copy()  # نسخة للاستخدام
        # استدعاء سريع مع مرور dataframes فارغة لـ MTF (لن نستخدم MTF في الباك تست للسرعة)
        signal, conf, _, _, _, _, _, _, sl, entry, targets, _ = generate_signal_fast(
            window, symbol, dxy_signal=None, dxy_correlation=0.0,
            df_15m=None, df_1h=None, df_4h=None
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

def _bar_exit(direction, bar, stop, tp):
    if direction == "BUY":
        if bar['low'] <= stop: return "SL", stop
        if bar['high'] >= tp: return "TP", tp
    else:
        if bar['high'] >= stop: return "SL", stop
        if bar['low'] <= tp: return "TP", tp
    return None, None

# -------------------- حساب جميع المؤشرات دفعة واحدة --------------------
def calculate_all_indicators(df):
    if df is None or len(df) < 100: return df
    df = df.copy()
    df['ema20'] = df['close'].ewm(20).mean()
    df['ema50'] = df['close'].ewm(50).mean()
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
    tenkan, kijun, senkou_a, senkou_b = calc_ichimoku(df)
    df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
    df['mfi'] = calc_mfi(df)
    # SMC vectorized
    smc_df = detect_smc_ict_vectorized(df)
    for col in ['ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                'liquidity_sweep_bullish','liquidity_sweep_bearish',
                'bos_bullish','bos_bearish','mss_bullish','mss_bearish']:
        df[col] = smc_df[col]
    return df

# -------------------- جمع الإشارات لجميع الأدوات (محسّن) --------------------
@st.cache_data(ttl=120)
def get_all_signals_optimized():
    results = []
    # DXY
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    if df_dxy is not None and len(df_dxy) > 100:
        df_dxy = calculate_all_indicators(df_dxy)
        dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_fast(
            df_dxy, "DX-Y.NYB", dxy_signal=None, dxy_correlation=0.0
        )
    else:
        dxy_signal = None
    
    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval="1h")
            if df is None or len(df) < 100: continue
            df = calculate_all_indicators(df)
            current_price = df['close'].iloc[-1]
            corr = get_dxy_correlation(df, df_dxy, lookback=50)
            # جلب بيانات MTF (15m, 1h, 4h) – مرة واحدة لكل رمز
            df_15m = get_historical_data(symbol, period="5d", interval="15m")
            df_1h = get_historical_data(symbol, period="5d", interval="1h")  # قد يكون نفس df ولكن نستخدمه للاتساق
            df_4h = get_historical_data(symbol, period="5d", interval="4h")
            # حساب مؤشرات MTF (سنمررها مباشرة)
            signal, conf, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets, _ = generate_signal_fast(
                df, symbol, dxy_signal, corr, df_15m, df_1h, df_4h
            )
            # backtest سريع (بدون MTF)
            bt = run_backtest_fast(df, symbol)
            if any(x in pair_name for x in ["Gold","Silver","Bitcoin","Ethereum"]):
                price_str = f"${current_price:,.2f}"; fmt = "${:,.2f}"
            else:
                price_str = f"{current_price:.4f}"; fmt = "{:.4f}"
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

# -------------------- واجهة Streamlit (مبسطة) --------------------
with st.sidebar:
    st.markdown("### 📊 Market Status")
    # دوال get_market_status و time_remaining محذوفة للاختصار، يمكن إضافتها
    st.markdown("---")
    if st.button("🔄 Refresh All"):
        with st.spinner("Analyzing..."):
            st.session_state.all_signals = get_all_signals_optimized()
            st.session_state.last_update = datetime.now()
        st.rerun()
    if st.session_state.all_signals is not None:
        df_sig = st.session_state.all_signals.copy()
        df_sig["Signal"] = df_sig["Signal"].apply(lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL" if x=="SELL" else "⚪ WAIT")
        st.dataframe(df_sig[["Instrument","Signal","Confidence","Score","Price"]], hide_index=True, use_container_width=True, height=300)
    selected_pair = st.selectbox("Select Instrument", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]

# تحميل البيانات للأداة المختارة
price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="60d", interval="15m")
if df is None: st.error("Failed to load data"); st.stop()
if price is None: price = df['close'].iloc[-1]; change = 0

# حساب المؤشرات
df = calculate_all_indicators(df)
df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
if df_dxy is not None and len(df_dxy) > 100:
    df_dxy = calculate_all_indicators(df_dxy)
    dxy_signal, _, _, _, _, _, _, _, _, _, _, _ = generate_signal_fast(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df, df_dxy, lookback=50)
else:
    dxy_signal = None; corr = 0.0

# بيانات MTF للأداة المختارة
df_15m = get_historical_data(selected_symbol, period="5d", interval="15m")
df_1h = get_historical_data(selected_symbol, period="5d", interval="1h")
df_4h = get_historical_data(selected_symbol, period="5d", interval="4h")

signal, confidence, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets, _ = generate_signal_fast(
    df, selected_symbol, dxy_signal, corr, df_15m, df_1h, df_4h
)

# عرض السعر
if "Gold" in selected_pair or "Silver" in selected_pair or "Bitcoin" in selected_pair or "Ethereum" in selected_pair:
    price_fmt = "${:,.2f}"
else:
    price_fmt = "{:.4f}"
st.markdown(f"<div class='price-card'><b>{selected_pair}</b><br><span style='font-size:1.5rem;color:gold;'>{price_fmt.format(price)}</span> <span style='color:{'#0f0' if change>=0 else '#f00'}'>{change:+.2f}%</span></div>", unsafe_allow_html=True)

if dxy_signal:
    st.markdown(f"📊 DXY: {dxy_signal} | Correlation: {corr:.2f}")

# عرض الإشارة
if signal in ["BUY","SELL"] and confidence >= MIN_CONFIDENCE:
    st.markdown(f"""
    <div class='suggested-trade'>
    <b>{signal}</b> (Confidence: {confidence:.0f}%)<br>
    Entry: {price_fmt.format(entry)}<br>
    SL: {price_fmt.format(sl)}<br>
    TP1: {price_fmt.format(targets['target1'])} &nbsp; TP2: {price_fmt.format(targets['target2'])} &nbsp; TP3: {price_fmt.format(targets['target3'])}
    </div>
    """, unsafe_allow_html=True)

# باكتست
bt = run_backtest_fast(df, selected_symbol)
if bt:
    st.markdown("### Backtest")
    c1,c2,c3 = st.columns(3)
    c1.metric("Trades", bt['total_trades'])
    c2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    c3.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

# Chart (مبسط)
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(dash='dash')))
if sl and entry:
    fig.add_hline(y=sl, line_dash='dash', line_color='red')
    fig.add_hline(y=entry, line_dash='dash', line_color='green')
fig.update_layout(template='plotly_dark', height=500)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | BLACK PYRAMID v2003 (Lightning)")
