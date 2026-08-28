# ============================================================
# BLACK PYRAMID v2003 – PRECISION EDITION (High Probability Setups)
# Optimized for accurate entries with SMC + ICT + Session Filters
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

st.set_page_config(page_title="Black Pyramid v2003 - Precision", page_icon="🎯", layout="wide")

# -------------------- CSS مختصر --------------------
st.markdown("""
<style>
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0a0a !important; }
.price-card, .signal-box, .suggested-trade { background: rgba(10,10,10,0.8); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.1); border-radius: 12px; padding: 15px; }
.suggested-trade { border-color: #00ff88; }
.high-prob { border-left: 6px solid #00ff88; padding: 8px 12px; margin: 5px 0; background: rgba(0,255,136,0.05); }
.footer { text-align: center; color: #444; font-size: 0.65rem; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# -------------------- API & CONSTANTS --------------------
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
BACKTEST_LOOKBACK = 500
MIN_CONFIDENCE = 50  # رفعنا العتبة للدقة
BUY_THRESHOLD = 10   # رفعنا العتبة
SELL_THRESHOLD = -10
COOLDOWN_BARS = 6    # زيادة التبريد
MAX_TRADES_PER_DAY = 2  # صفقتين فقط في اليوم عالي الجودة

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
    # ... (نفس الكود السابق، اختصاراً للطول)
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

# -------------------- SWING POINTS (للهيكل الحقيقي) --------------------
def find_swing_points(df, order=5):
    """تحديد القمم والقيعان الفعلية"""
    highs = df['high'].values
    lows = df['low'].values
    peaks = np.array([False] * len(df))
    troughs = np.array([False] * len(df))
    for i in range(order, len(df) - order):
        if all(highs[i] > highs[i-j] for j in range(1, order+1)) and all(highs[i] > highs[i+j] for j in range(1, order+1)):
            peaks[i] = True
        if all(lows[i] < lows[i-j] for j in range(1, order+1)) and all(lows[i] < lows[i+j] for j in range(1, order+1)):
            troughs[i] = True
    return peaks, troughs

# -------------------- SMC ICT المتقدم (مع مناطق دقيقة) --------------------
def detect_smc_ict_advanced(df):
    df = df.copy()
    
    # 1. Order Blocks الحقيقية (شمعة انعكاسية قوية تسبق حركة)
    body = (df['close'] - df['open']).abs()
    avg_body = body.rolling(20).mean()
    strong_bull = (df['close'] > df['open']) & (body > avg_body * 1.5)
    strong_bear = (df['close'] < df['open']) & (body > avg_body * 1.5)
    
    # OB: شمعة قوية وبعدها شمعة تخترق في الاتجاه المعاكس (شمعة تأكيد)
    df['ob_bullish'] = strong_bear.shift(1) & (df['close'] > df['high'].shift(1))  # كسر قمة شمعة البيع القوية
    df['ob_bearish'] = strong_bull.shift(1) & (df['close'] < df['low'].shift(1))   # كسر قاع شمعة الشراء القوية
    
    # 2. FVG (Fair Value Gaps) مع منطقة العودة
    df['fvg_bullish'] = (df['low'] > df['high'].shift(2))
    df['fvg_bearish'] = (df['high'] < df['low'].shift(2))
    
    # 3. Liquidity Sweeps (كنس السيولة أعلى/أدنى القمم/القيعان)
    rolling_high_20 = df['high'].rolling(20).max()
    rolling_low_20 = df['low'].rolling(20).min()
    df['liquidity_sweep_bullish'] = (df['high'] > rolling_high_20.shift(1))  # كنس قمة
    df['liquidity_sweep_bearish'] = (df['low'] < rolling_low_20.shift(1))    # كنس قاع
    
    # 4. تغير الهيكل (CHOCH) بدلاً من BOS التقليدي
    peaks, troughs = find_swing_points(df, order=3)
    df['swing_high'] = peaks
    df['swing_low'] = troughs
    
    # CHOCH: كسر قمة سابقة + كسر قاع سابق (تغير الاتجاه)
    df['choch_bullish'] = df['swing_low'].shift(1) & (df['close'] > df['high'].shift(1))  # كسر قمة بعد قاع
    df['choch_bearish'] = df['swing_high'].shift(1) & (df['close'] < df['low'].shift(1))   # كسر قاع بعد قمة
    
    return df

# -------------------- فلتر الجلسات (التوقيت) --------------------
def is_london_ny_session():
    """تجاهل جلسة آسيا (ضعيفة) والتركيز على لندن ونيويورك"""
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    hour = now.hour
    # لندن: 2:00 صباحاً - 10:00 صباحاً بتوقيت نيويورك | نيويورك: 8:00 صباحاً - 4:00 عصراً
    return (2 <= hour <= 16)  # فترة النشاط العالي

# -------------------- DXY & REGIME --------------------
def get_dxy_correlation(df_pair, df_dxy, lookback=50):
    if df_pair is None or df_dxy is None or len(df_pair) < lookback: return 0.0
    pair = df_pair[['close']].pct_change().dropna()
    dxy = df_dxy[['close']].pct_change().dropna()
    combined = pd.concat([pair, dxy], axis=1, join='inner').dropna()
    if len(combined) < lookback: return 0.0
    return float(combined.iloc[-lookback:, 0].corr(combined.iloc[-lookback:, 1]) or 0.0)

def apply_dxy_filter(signal, dxy_signal, correlation):
    if dxy_signal is None or dxy_signal == "WAIT" or signal == "WAIT": return 0, "NEUTRAL"
    if abs(correlation) < 0.30: return 0, "WEAK"
    if correlation <= -0.60:
        aligned = (signal == "BUY" and dxy_signal == "SELL") or (signal == "SELL" and dxy_signal == "BUY")
        return (5 if aligned else -6), "STRONG_ALIGN" if aligned else "MISALIGN"
    elif correlation >= 0.60:
        aligned = signal == dxy_signal
        return (5 if aligned else -6), "STRONG_ALIGN" if aligned else "MISALIGN"
    else:
        aligned = (signal == "BUY" and dxy_signal == "SELL") if correlation < 0 else signal == dxy_signal
        return (2 if aligned else -3), "ALIGN" if aligned else "MISALIGN"

# -------------------- حساب المؤشرات دفعة واحدة --------------------
def calculate_all_indicators(df):
    if df is None or len(df) < 100: return df
    df = df.copy()
    df['ema20'] = df['close'].ewm(20).mean()
    df['ema50'] = df['close'].ewm(50).mean()
    df['ema200'] = df['close'].ewm(200).mean()  # للاتجاه العام
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx_correct(df)
    tenkan, kijun, senkou_a, senkou_b = calc_ichimoku(df)
    df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b
    df['mfi'] = calc_mfi(df)
    # SMC المتقدم
    smc_df = detect_smc_ict_advanced(df)
    for col in ['ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                'liquidity_sweep_bullish','liquidity_sweep_bearish',
                'choch_bullish','choch_bearish']:
        df[col] = smc_df[col]
    return df

# -------------------- إشارة الصفقة الدقيقة --------------------
def generate_precision_signal(df, symbol, dxy_signal=None, dxy_correlation=0.0,
                              df_daily=None, df_15m=None, df_1h=None, df_4h=None):
    """
    الفكرة الأساسية:
    1. لا ندخل إلا إذا كان هناك 'تغير هيكل' (CHOCH) أو 'كنس سيولة'.
    2. نتحقق من وجود منطقة عرض/طلب (OB/FVG) قريبة من السعر الحالي.
    3. نتأكد من أن الاتجاه العام (Daily) موافق للإشارة.
    4. نطبق فلتر الجلسة.
    """
    if df is None or len(df) < 100:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, None

    last = df.iloc[-1]
    current_price = last['close']
    
    # ---------- 1. فلتر الجلسة ----------
    if not is_london_ny_session():
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, None

    # ---------- 2. تحليل الهيكل (SMC) ----------
    has_choch_bull = last.get('choch_bullish', False)
    has_choch_bear = last.get('choch_bearish', False)
    has_liquidity_sweep_bull = last.get('liquidity_sweep_bullish', False)
    has_liquidity_sweep_bear = last.get('liquidity_sweep_bearish', False)
    has_ob_bull = last.get('ob_bullish', False)
    has_ob_bear = last.get('ob_bearish', False)
    has_fvg_bull = last.get('fvg_bullish', False)
    has_fvg_bear = last.get('fvg_bearish', False)

    # ---------- 3. الاتجاه العام (Daily Bias) ----------
    daily_bias = "NEUTRAL"
    if df_daily is not None and len(df_daily) > 50:
        daily_last = df_daily.iloc[-1]
        if daily_last['ema20'] > daily_last['ema50'] and daily_last['rsi'] > 50:
            daily_bias = "BULLISH"
        elif daily_last['ema20'] < daily_last['ema50'] and daily_last['rsi'] < 50:
            daily_bias = "BEARISH"

    # ---------- 4. بناء عوامل الدقة ----------
    factors = {"structure":0.0, "liquidity":0.0, "smc":0.0, "bias":0.0, "dxy":0.0, "momentum":0.0, "volatility":0.0}
    details = {}
    setup_type = None

    # شرط أساسي: يجب أن يكون هناك CHOCH أو Liquidity Sweep (تغير حقيقي)
    if has_choch_bull or has_liquidity_sweep_bull:
        factors['structure'] += 30.0
        details['Setup'] = "Bullish CHOCH/Liquidity Sweep"
        setup_type = "BUY"
    elif has_choch_bear or has_liquidity_sweep_bear:
        factors['structure'] -= 30.0
        details['Setup'] = "Bearish CHOCH/Liquidity Sweep"
        setup_type = "SELL"
    else:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, None  # لا ندخل بدون هيكل

    # التحقق من وجود منطقة SMC (OB/FVG) لتأكيد الدخول
    if setup_type == "BUY":
        if not (has_ob_bull or has_fvg_bull):
            return "WAIT", 0, {}, {}, None, None, None, None, None, None, None  # ننتظر العودة للمنطقة
        factors['smc'] += 25.0
        details['SMC'] = "Bullish OB/FVG Zone"
    elif setup_type == "SELL":
        if not (has_ob_bear or has_fvg_bear):
            return "WAIT", 0, {}, {}, None, None, None, None, None, None, None
        factors['smc'] += 25.0
        details['SMC'] = "Bearish OB/FVG Zone"

    # تأكيد الاتجاه مع Daily Bias
    if daily_bias == "BULLISH" and setup_type == "BUY":
        factors['bias'] += 15.0
        details['Bias'] = "✅ Aligned with Daily"
    elif daily_bias == "BEARISH" and setup_type == "SELL":
        factors['bias'] += 15.0
        details['Bias'] = "✅ Aligned with Daily"
    else:
        details['Bias'] = "⚠️ Neutral or Opposite (Lower Conviction)"

    # DXY
    dxy_adj, dxy_status = apply_dxy_filter(setup_type, dxy_signal, dxy_correlation)
    factors['dxy'] = dxy_adj
    details['DXY'] = dxy_status

    # Momentum (RSI)
    rsi = last['rsi']
    if setup_type == "BUY" and rsi < 50:
        factors['momentum'] += 10.0
        details['Momentum'] = f"Oversold RSI={rsi:.1f}"
    elif setup_type == "SELL" and rsi > 50:
        factors['momentum'] += 10.0
        details['Momentum'] = f"Overbought RSI={rsi:.1f}"
    else:
        factors['momentum'] += 2.0
        details['Momentum'] = f"RSI={rsi:.1f}"

    # التقلب (نفضل التقلب المنخفض للدقة)
    atr_ratio = last['atr'] / df['atr'].iloc[-20:].mean() if df['atr'].iloc[-20:].mean() > 0 else 1.0
    if 0.7 <= atr_ratio <= 1.3:
        factors['volatility'] += 5.0
        details['Volatility'] = "Optimal"
    else:
        factors['volatility'] -= 2.0
        details['Volatility'] = "High/Low Volatility"

    total_score = sum(factors.values())
    
    # رفع العتبة للدقة (نحتاج مجموع كبير)
    if setup_type == "BUY" and total_score >= 45:  # عتبة عالية
        signal = "BUY"
        confidence = min(95, 60 + total_score * 0.6)
    elif setup_type == "SELL" and total_score >= 45:
        signal = "SELL"
        confidence = min(95, 60 + abs(total_score) * 0.6)
    else:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, None

    confidence = max(50, min(95, confidence))

    # ---------- 5. Stop Loss & Targets (مع ATR و المناطق) ----------
    atr_val = last['atr'] if not pd.isna(last['atr']) else 10.0
    entry_price = current_price
    
    if signal == "BUY":
        # نضع الوقف أسفل منطقة OB أو قاع التصحيح الأخير
        recent_low = df['low'].iloc[-10:].min()
        ob_low = df['low'].iloc[-3:].min()
        stop_loss = min(recent_low, ob_low, current_price - atr_val * 1.0)
        stop_loss = max(stop_loss, current_price - atr_val * 2.5)
    else:
        recent_high = df['high'].iloc[-10:].max()
        ob_high = df['high'].iloc[-3:].max()
        stop_loss = max(recent_high, ob_high, current_price + atr_val * 1.0)
        stop_loss = min(stop_loss, current_price + atr_val * 2.5)

    risk = abs(entry_price - stop_loss)
    if risk < atr_val * 0.3:
        stop_loss = entry_price - atr_val * 0.6 if signal == "BUY" else entry_price + atr_val * 0.6
        risk = atr_val * 0.6

    if signal == "BUY":
        targets = {
            'target1': entry_price + risk * 1.0,
            'target2': entry_price + risk * 1.8,
            'target3': entry_price + risk * 3.0,
            'risk_reward': 2.5
        }
    else:
        targets = {
            'target1': entry_price - risk * 1.0,
            'target2': entry_price - risk * 1.8,
            'target3': entry_price - risk * 3.0,
            'risk_reward': 2.5
        }

    return signal, confidence, total_score, details, factors, "PRECISION", "NA", 0, stop_loss, entry_price, targets

# -------------------- BACKTEST مع إدارة خروج متقدمة --------------------
def run_backtest_precision(df, symbol, lookback=BACKTEST_LOOKBACK):
    if df is None or len(df) < 150: return {}
    test_df = df.iloc[-min(lookback, len(df)):].copy()
    test_df = calculate_all_indicators(test_df)
    
    # نحتاج بيانات Daily للإشارة
    df_daily = get_historical_data(symbol, period="3mo", interval="1d")
    if df_daily is not None and len(df_daily) > 50:
        df_daily = calculate_all_indicators(df_daily)
    else:
        df_daily = None
    
    trades = []; active = None; daily_count = {}
    
    for i in range(100, len(test_df) - 1):
        bar = test_df.iloc[i]
        day = str(bar.name.date()) if hasattr(bar.name, 'date') else str(i)
        
        # إدارة الصفقة النشطة (خروج متقدم)
        if active:
            # 1. خروج تقليدي (SL / TP)
            result, exit_price = _bar_exit_advanced(active, bar)
            if result:
                risk = abs(active['entry'] - active['stop'])
                reward = abs(exit_price - active['entry']) / risk if risk > 0 else 0
                trades.append({'result': result, 'r': reward if result == 'TP' else -1,
                               'direction': active['direction'], 'entry_i': active['entry_i'], 'exit_i': i})
                active = None
            else:
                # 2. تحريك وقف الخسارة إلى نقطة الدخول عند تحقيق TP1 (Breakeven)
                if active.get('breakeven_triggered', False) is False:
                    if active['direction'] == "BUY" and bar['high'] >= active['tp1']:
                        active['stop'] = active['entry']  # نقل SL إلى نقطة الدخول
                        active['breakeven_triggered'] = True
                    elif active['direction'] == "SELL" and bar['low'] <= active['tp1']:
                        active['stop'] = active['entry']
                        active['breakeven_triggered'] = True
                continue  # ننتظر الخروج في التكرار التالي
        
        # فتح صفقة جديدة
        if daily_count.get(day, 0) >= MAX_TRADES_PER_DAY: continue
        
        window = test_df.iloc[:i+1].copy()
        signal, conf, _, _, _, _, _, _, sl, entry, targets = generate_precision_signal(
            window, symbol, dxy_signal=None, dxy_correlation=0.0,
            df_daily=df_daily, df_15m=None, df_1h=None, df_4h=None
        )
        
        if signal == "WAIT" or conf < 55 or sl is None or not targets: continue
        next_open = float(test_df['open'].iloc[i+1])
        stop = float(sl); tp1 = float(targets['target1']); tp2 = float(targets['target2']); tp3 = float(targets['target3'])
        if (signal == 'BUY' and stop >= next_open) or (signal == 'SELL' and stop <= next_open): continue
        
        active = {
            'direction': signal,
            'entry': next_open,
            'stop': stop,
            'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
            'entry_i': i+1,
            'breakeven_triggered': False
        }
        daily_count[day] = daily_count.get(day, 0) + 1
    
    if not trades: return {}
    wins = [t for t in trades if t['result'] == 'win']
    losses = [t for t in trades if t['result'] == 'loss']
    gross_win = sum(t['r'] for t in wins)
    gross_loss = abs(sum(t['r'] for t in losses))
    return {
        'total_trades': len(trades),
        'win_rate': len(wins)/len(trades)*100,
        'avg_r': sum(t['r'] for t in trades)/len(trades),
        'profit_factor': gross_win/gross_loss if gross_loss>0 else float('inf'),
    }

def _bar_exit_advanced(active, bar):
    """نظام خروج ديناميكي: أولوية لوقف الخسارة"""
    if active['direction'] == "BUY":
        if bar['low'] <= active['stop']: return "loss", active['stop']
        if bar['high'] >= active['tp3']: return "win", active['tp3']
    else:
        if bar['high'] >= active['stop']: return "loss", active['stop']
        if bar['low'] <= active['tp3']: return "win", active['tp3']
    return None, None

# -------------------- جمع الإشارات لجميع الأدوات --------------------
@st.cache_data(ttl=120)
def get_all_signals_precision():
    results = []
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    dxy_signal = None
    if df_dxy is not None and len(df_dxy) > 100:
        df_dxy = calculate_all_indicators(df_dxy)
        dxy_signal, _, _, _, _, _, _, _, _, _, _ = generate_precision_signal(df_dxy, "DX-Y.NYB")
    
    # بيانات Daily لجميع الأدوات (نحضرها مرة واحدة)
    daily_cache = {}
    
    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval="1h")
            if df is None or len(df) < 100: continue
            df = calculate_all_indicators(df)
            
            # جلب Daily
            if symbol not in daily_cache:
                daily_cache[symbol] = get_historical_data(symbol, period="3mo", interval="1d")
                if daily_cache[symbol] is not None:
                    daily_cache[symbol] = calculate_all_indicators(daily_cache[symbol])
            df_daily = daily_cache.get(symbol)
            
            current_price = df['close'].iloc[-1]
            corr = get_dxy_correlation(df, df_dxy, lookback=50)
            
            signal, conf, score, details, factors, regime, mtf, mtf_c, sl, entry, targets = generate_precision_signal(
                df, symbol, dxy_signal, corr, df_daily
            )
            
            if signal in ["BUY", "SELL"] and conf >= 55:
                bt = run_backtest_precision(df, symbol)
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
                    "Setup": details.get('Setup', 'N/A'),
                    "Bias": details.get('Bias', 'N/A'),
                    "DXY": details.get('DXY', 'N/A'),
                    "Entry": fmt.format(entry) if entry else "N/A",
                    "SL": fmt.format(sl) if sl else "N/A",
                    "TP1": fmt.format(targets['target1']) if targets else "N/A",
                    "Win Rate": f"{bt.get('win_rate', 0):.1f}%" if bt else "N/A"
                })
        except Exception as e:
            continue
    return pd.DataFrame(results)

# -------------------- واجهة Streamlit --------------------
with st.sidebar:
    st.markdown("## 🎯 Precision Filter")
    st.caption("London/NY Session Only | CHOCH + OB/FVG | Daily Bias Confirmation")
    if st.button("🔄 Scan for Setups"):
        with st.spinner("Scanning for high-probability setups..."):
            st.session_state.all_signals = get_all_signals_precision()
            st.session_state.last_update = datetime.now()
        st.rerun()
    
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_sig = st.session_state.all_signals.copy()
        df_sig["Signal"] = df_sig["Signal"].apply(lambda x: "🟢 BUY" if x=="BUY" else "🔴 SELL")
        st.dataframe(df_sig[["Instrument","Signal","Confidence","Setup","Bias","DXY"]], 
                     hide_index=True, use_container_width=True, height=400)
        st.caption(f"🕐 {st.session_state.last_update.strftime('%H:%M:%S')} | {len(df_sig)} Setups Found")
    else:
        st.info("No high-probability setups at the moment.")
    
    selected_pair = st.selectbox("📊 Analyze", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]

# -------------------- عرض الأداة المختارة --------------------
price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="60d", interval="15m")
if df is None: st.error("Data Error"); st.stop()
if price is None: price = df['close'].iloc[-1]; change = 0

df = calculate_all_indicators(df)
df_daily = get_historical_data(selected_symbol, period="3mo", interval="1d")
if df_daily is not None: df_daily = calculate_all_indicators(df_daily)

df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
if df_dxy is not None and len(df_dxy) > 100:
    df_dxy = calculate_all_indicators(df_dxy)
    dxy_signal, _, _, _, _, _, _, _, _, _, _ = generate_precision_signal(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df, df_dxy, lookback=50)
else:
    dxy_signal = None; corr = 0.0

signal, conf, score, details, factors, regime, mtf, mtf_c, sl, entry, targets = generate_precision_signal(
    df, selected_symbol, dxy_signal, corr, df_daily
)

# عرض السعر
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

if dxy_signal: st.markdown(f"📊 DXY Signal: **{dxy_signal}** | Correlation: {corr:.2f}")

# عرض الصفقة الدقيقة
if signal in ["BUY","SELL"] and conf >= 55:
    st.markdown(f"""
    <div class="suggested-trade">
        <h4 style="color:#00ff88;">🎯 High Probability {signal} Setup</h4>
        <b>Confidence:</b> {conf:.0f}%<br>
        <b>📍 Entry:</b> {price_fmt.format(entry)}<br>
        <b>🛑 SL:</b> {price_fmt.format(sl)} (Risk: {abs(entry-sl)/price*100:.2f}%)<br>
        <b>🎯 TP1:</b> {price_fmt.format(targets['target1'])} | <b>TP2:</b> {price_fmt.format(targets['target2'])} | <b>TP3:</b> {price_fmt.format(targets['target3'])}<br>
        <b>📈 R:R</b> 1:{targets.get('risk_reward', 0):.1f}
    </div>
    """, unsafe_allow_html=True)
    st.info(f"🧠 Setup: {details.get('Setup')} | Bias: {details.get('Bias')} | DXY: {details.get('DXY')}")
else:
    st.warning("⏳ No high-probability setup currently. Waiting for CHOCH + OB/FVG + Session alignment.")

# باكتست
bt = run_backtest_precision(df, selected_symbol)
if bt:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Trades", bt['total_trades'])
    col2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    col3.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

# Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(dash='dash')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(dash='dash')))
if sl and entry:
    fig.add_hline(y=sl, line_dash='dash', line_color='red', annotation_text="SL")
    fig.add_hline(y=entry, line_dash='dash', line_color='green', annotation_text="Entry")
fig.update_layout(template='plotly_dark', height=450)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | BLACK PYRAMID v2003 - Precision Mode")
