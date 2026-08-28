# ============================================================
# BLACK PYRAMID v2003 – LIGHTNING EDITION (Original Logic)
# Only KeyError fixed, no weight/confidence changes
# ============================================================

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import requests
import time

st.set_page_config(page_title="Black Pyramid v2003", page_icon="▲", layout="wide")

# -------------------- CSS (مختصر) --------------------
st.markdown("""
<style>
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0a0a !important; }
.price-card, .suggested-trade { background: rgba(10,10,10,0.8); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.1); border-radius: 12px; padding: 15px; }
.suggested-trade { border-color: #00ff88; }
.footer { text-align: center; color: #444; font-size: 0.65rem; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# -------------------- CONSTANTS --------------------
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
MIN_CONFIDENCE = 42
BUY_THRESHOLD = 8
SELL_THRESHOLD = -8
MAX_TRADES_PER_DAY = 3

PAIRS = {
    "XAU/USD (Gold)": "GC=F",
    "XAG/USD (Silver)": "SI=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
}

# -------------------- SESSION STATE --------------------
if "all_signals" not in st.session_state: st.session_state.all_signals = None
if "active_trades" not in st.session_state: st.session_state.active_trades = {}
if "closed_trades" not in st.session_state: st.session_state.closed_trades = []
if "trade_stats" not in st.session_state: st.session_state.trade_stats = {"day": None, "count": 0}

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

# -------------------- INDICATORS (الأصلية) --------------------
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

# -------------------- SMC (الأصلي) --------------------
def detect_smc_ict_original(df):
    df = df.copy()
    body = (df['close'] - df['open']).abs()
    avg_body = body.rolling(20).mean()
    strong_bull = (df['close'] > df['open']) & (body > avg_body * 1.5)
    strong_bear = (df['close'] < df['open']) & (body > avg_body * 1.5)
    df['order_block_bullish'] = strong_bear.shift(1) & (df['close'] > df['high'].shift(1))
    df['order_block_bearish'] = strong_bull.shift(1) & (df['close'] < df['low'].shift(1))
    df['fvg_bullish'] = (df['low'] > df['high'].shift(2))
    df['fvg_bearish'] = (df['high'] < df['low'].shift(2))
    rolling_high_20 = df['high'].rolling(20).max()
    rolling_low_20 = df['low'].rolling(20).min()
    df['liquidity_sweep_bullish'] = (df['high'] > rolling_high_20.shift(1))
    df['liquidity_sweep_bearish'] = (df['low'] < rolling_low_20.shift(1))
    df['mss_bullish'] = (df['low'] < df['low'].shift(1)) & (df['close'] > df['high'].shift(1))
    df['mss_bearish'] = (df['high'] > df['high'].shift(1)) & (df['close'] < df['low'].shift(1))
    return df

# -------------------- TBS (الأصلي مع تصحيح منطق الانعكاس) --------------------
def detect_tbs_original(df, lookback=20, body_mult=1.5):
    if len(df) < lookback + 2: return None, None, None, None
    last = df.iloc[-1]
    lookback_high = df['high'].iloc[-lookback-1:-1].max()
    lookback_low = df['low'].iloc[-lookback-1:-1].min()
    avg_body = abs(df['close'] - df['open']).iloc[-lookback-1:-1].mean()
    current_body = abs(last['close'] - last['open'])
    if current_body < avg_body * body_mult: return None, None, None, None
    # Bearish Turtle Soup
    if last['high'] > lookback_high and last['close'] < lookback_high:
        return "BEARISH", last['close'], last['high'], lookback_high
    # Bullish Turtle Soup
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

def mtf_consensus_from_dataframes(df_15m, df_1h, df_4h):
    results = []
    for tf, df in [("15m", df_15m), ("1h", df_1h), ("4h", df_4h)]:
        if df is not None and len(df) > 50:
            rsi = calc_rsi(df['close']).iloc[-1]
            ema20 = df['close'].ewm(20).mean().iloc[-1]
            ema50 = df['close'].ewm(50).mean().iloc[-1]
            trend = "BULLISH" if (ema20 > ema50 and rsi > 50) else "BEARISH" if (ema20 < ema50 and rsi < 50) else "NEUTRAL"
            results.append(trend)
    buy = results.count("BULLISH"); sell = results.count("BEARISH")
    if buy > sell: return "BUY", buy - sell
    elif sell > buy: return "SELL", sell - buy
    else: return "NEUTRAL", 0

# -------------------- CALCULATE ALL INDICATORS (مع إصلاح الحد الأدنى للصفوف) --------------------
def calculate_all_indicators(df):
    if df is None or len(df) < 20:
        return df
    df = df.copy()
    df['ema20'] = df['close'].ewm(20).mean()
    df['ema50'] = df['close'].ewm(50).mean()
    df['ema200'] = df['close'].ewm(200).mean()
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
    tenkan, kijun, senkou_a, senkou_b = calc_ichimoku(df)
    df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
    df['mfi'] = calc_mfi(df)
    df['vwap'] = calc_vwap(df)
    smc_df = detect_smc_ict_original(df)
    for col in ['order_block_bullish', 'order_block_bearish',
                'fvg_bullish', 'fvg_bearish',
                'liquidity_sweep_bullish', 'liquidity_sweep_bearish',
                'mss_bullish', 'mss_bearish']:
        df[col] = smc_df[col]
    return df

# -------------------- الإشارة الأصلية (بدون تعديل الأوزان) --------------------
def generate_original_signal(df, symbol, dxy_signal=None, dxy_correlation=0.0,
                             df_15m=None, df_1h=None, df_4h=None, df_daily=None):
    if df is None or len(df) < 100:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, None

    # المؤشرات محسوبة مسبقاً
    last = df.iloc[-1]
    current_price = last['close']

    # SMC (من الأعمدة)
    smc_cols = ['order_block_bullish', 'order_block_bearish',
                'fvg_bullish', 'fvg_bearish',
                'liquidity_sweep_bullish', 'liquidity_sweep_bearish',
                'mss_bullish', 'mss_bearish']
    last_smc = {c: last.get(c, False) for c in smc_cols}

    # TBS
    tbs_type, _, _, _ = detect_tbs_original(df)

    # Regime
    regime = detect_regime(df)

    # MTF
    mtf_cons, mtf_count = mtf_consensus_from_dataframes(df_15m, df_1h, df_4h)

    # ===== FACTORS (الأصلية) =====
    factors = {"structure":0.0, "liquidity":0.0, "smc":0.0, "mtf":0.0, "dxy":0.0,
               "momentum":0.0, "volatility":0.0, "pattern":0.0, "volume":0.0}
    details = {}

    # Structure
    if last_smc.get('mss_bullish', False) or last_smc.get('mss_bullish', False):
        factors['structure'] += 25.0; details['Structure'] = "Bullish MSS"
    elif last_smc.get('mss_bearish', False) or last_smc.get('mss_bearish', False):
        factors['structure'] -= 25.0; details['Structure'] = "Bearish MSS"
    else: details['Structure'] = "Neutral"

    # Liquidity
    if last_smc.get('liquidity_sweep_bullish', False):
        factors['liquidity'] += 20.0; details['Liquidity'] = "Buy-side sweep"
    elif last_smc.get('liquidity_sweep_bearish', False):
        factors['liquidity'] -= 20.0; details['Liquidity'] = "Sell-side sweep"
    else: details['Liquidity'] = "No sweep"

    # SMC (إشارة واحدة فقط – كما في الأصل)
    if last_smc.get('order_block_bullish', False) or last_smc.get('fvg_bullish', False):
        factors['smc'] += 20.0; details['SMC'] = "Bullish OB/FVG"
    elif last_smc.get('order_block_bearish', False) or last_smc.get('fvg_bearish', False):
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
    atr_ratio = last['atr'] / df['atr'].iloc[-20:].mean() if df['atr'].iloc[-20:].mean() > 0 else 1.0
    if atr_ratio > 1.5:
        factors['volatility'] -= 10.0; details['Volatility'] = "High"
    elif atr_ratio < 0.7:
        factors['volatility'] += 5.0; details['Volatility'] = "Low"
    else: details['Volatility'] = "Normal"

    # Pattern (TBS)
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

    # Signal (الأصلي: ±8)
    if total_score >= BUY_THRESHOLD:
        signal = "BUY"; confidence = min(90, 50 + total_score * 0.5)
    elif total_score <= SELL_THRESHOLD:
        signal = "SELL"; confidence = min(90, 50 + abs(total_score) * 0.5)
    else:
        signal = "WAIT"; confidence = 50 + total_score * 0.2
    confidence = max(0, min(100, confidence))
    if "HIGH_VOL" in regime: confidence *= 0.9
    elif "LOW_VOL" in regime: confidence *= 1.1

    # Stop Loss & Targets (نفس الأصل)
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

    return signal, confidence, total_score, details, factors, regime, mtf_cons, mtf_count, stop_loss, entry_price, targets

# -------------------- BACKTEST (الأصلي) --------------------
def run_backtest_original(df, symbol, lookback=500):
    if df is None or len(df) < 150: return {}
    test_df = df.iloc[-min(lookback, len(df)):].copy()
    test_df = calculate_all_indicators(test_df)
    trades = []; active = None; daily_count = {}
    for i in range(100, len(test_df) - 1):
        bar = test_df.iloc[i]
        day = str(bar.name.date()) if hasattr(bar.name, 'date') else str(i)
        if active:
            result, exit_price = _bar_exit(active, bar)
            if result:
                risk = abs(active['entry'] - active['stop'])
                reward = abs(exit_price - active['entry']) / risk if risk > 0 else 0
                trades.append({'result': result, 'r': reward if result == 'TP' else -1,
                               'direction': active['direction'], 'entry_i': active['entry_i'], 'exit_i': i})
                active = None
            else:
                continue
        if daily_count.get(day, 0) >= MAX_TRADES_PER_DAY: continue
        window = test_df.iloc[:i+1].copy()
        signal, conf, _, _, _, _, _, _, sl, entry, targets = generate_original_signal(
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
    return {'total_trades': len(trades), 'win_rate': len(wins)/len(trades)*100,
            'avg_r': sum(t['r'] for t in trades)/len(trades),
            'profit_factor': gross_win/gross_loss if gross_loss>0 else float('inf')}

def _bar_exit(active, bar):
    if active['direction'] == "BUY":
        if bar['low'] <= active['stop']: return "loss", active['stop']
        if bar['high'] >= active['tp']: return "win", active['tp']
    else:
        if bar['high'] >= active['stop']: return "loss", active['stop']
        if bar['low'] <= active['tp']: return "win", active['tp']
    return None, None

# -------------------- جمع الإشارات (الأصلي) --------------------
@st.cache_data(ttl=120)
def get_all_signals_original():
    results = []
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    df_dxy = calculate_all_indicators(df_dxy)
    dxy_signal = None
    if df_dxy is not None and len(df_dxy) > 20:
        dxy_signal, _, _, _, _, _, _, _, _, _, _ = generate_original_signal(df_dxy, "DX-Y.NYB")

    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval="1h")
            if df is None or len(df) < 50: continue
            df = calculate_all_indicators(df)
            current_price = df['close'].iloc[-1]
            corr = get_dxy_correlation(df, df_dxy, lookback=50)
            signal, conf, score, details, factors, regime, mtf_cons, mtf_count, sl, entry, targets = generate_original_signal(
                df, symbol, dxy_signal, corr
            )
            if signal in ["BUY","SELL"] and conf >= MIN_CONFIDENCE:
                bt = run_backtest_original(df, symbol)
                if any(x in pair_name for x in ["Gold","Silver","Bitcoin"]):
                    price_str = f"${current_price:,.2f}"; fmt = "${:,.2f}"
                else:
                    price_str = f"{current_price:.4f}"; fmt = "{:.4f}"
                results.append({
                    "Instrument": pair_name,
                    "Signal": signal,
                    "Confidence": round(conf, 1),
                    "Score": score,
                    "Price": price_str,
                    "Entry": fmt.format(entry) if entry else "N/A",
                    "SL": fmt.format(sl) if sl else "N/A",
                    "TP1": fmt.format(targets['target1']) if targets else "N/A",
                    "Win Rate": f"{bt.get('win_rate', 0):.1f}%" if bt else "N/A"
                })
        except Exception as e: continue
    return pd.DataFrame(results)

# -------------------- واجهة Streamlit (الأصلية) --------------------
with st.sidebar:
    st.markdown("## 📊 Black Pyramid v2003")
    st.caption("Original Logic (Threshold ±8)")
    if st.button("🔄 Refresh"):
        with st.spinner("Analyzing..."):
            st.session_state.all_signals = get_all_signals_original()
            st.session_state.last_update = datetime.now()
        st.rerun()
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_sig = st.session_state.all_signals.copy()
        df_sig["Signal"] = df_sig["Signal"].apply(lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL")
        st.dataframe(df_sig[["Instrument","Signal","Confidence","Score","Price"]], hide_index=True, use_container_width=True, height=300)
        st.caption(f"🕐 {st.session_state.last_update.strftime('%H:%M:%S')}")
    else: st.info("Press Refresh")
    selected_pair = st.selectbox("📊 Analyze", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]

# -------------------- عرض الأداة --------------------
price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="60d", interval="15m")
if df is None: st.error("Data Error"); st.stop()
if price is None: price = df['close'].iloc[-1]; change = 0
df = calculate_all_indicators(df)

df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
df_dxy = calculate_all_indicators(df_dxy)
dxy_signal = None; corr = 0.0
if df_dxy is not None and len(df_dxy) > 20:
    dxy_signal, _, _, _, _, _, _, _, _, _, _ = generate_original_signal(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df, df_dxy, lookback=50)

signal, conf, score, details, factors, regime, mtf, mtf_c, sl, entry, targets = generate_original_signal(
    df, selected_symbol, dxy_signal, corr
)

if "Gold" in selected_pair or "Silver" in selected_pair or "Bitcoin" in selected_pair:
    price_fmt = "${:,.2f}"
else: price_fmt = "{:.4f}"

st.markdown(f"""
<div class="price-card">
    <h3>{selected_pair}</h3>
    <span style="font-size:2rem;color:gold;">{price_fmt.format(price)}</span>
    <span style="color:{'#0f0' if change>=0 else '#f00'};"> {change:+.2f}%</span>
</div>
""", unsafe_allow_html=True)

if signal in ["BUY","SELL"] and conf >= MIN_CONFIDENCE:
    st.markdown(f"""
    <div class="suggested-trade">
        <h4>{signal} (Confidence: {conf:.0f}%)</h4>
        <b>Entry:</b> {price_fmt.format(entry)}<br>
        <b>SL:</b> {price_fmt.format(sl)}<br>
        <b>TP1:</b> {price_fmt.format(targets['target1'])} | <b>TP2:</b> {price_fmt.format(targets['target2'])} | <b>TP3:</b> {price_fmt.format(targets['target3'])}
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("No signal")

bt = run_backtest_original(df, selected_symbol)
if bt:
    col1, col2, col3 = st.columns(3)
    col1.metric("Trades", bt['total_trades'])
    col2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    col3.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold')))
if 'ema20' in df.columns: fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(dash='dash')))
if sl and entry:
    fig.add_hline(y=sl, line_dash='dash', line_color='red', annotation_text="SL")
    fig.add_hline(y=entry, line_dash='dash', line_color='green', annotation_text="Entry")
fig.update_layout(template='plotly_dark', height=450)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | BLACK PYRAMID v2003 (Original)")
