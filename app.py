# ============================================================
# BLACK PYRAMID v2003 – HIERARCHICAL DECISION ENGINE
# Architecture: Regime → Bias → Confirmation → Trigger → Price → News → Risk
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

st.set_page_config(page_title="Black Pyramid v2003 - Hierarchical", page_icon="▲", layout="wide")

# -------------------- CSS (مدمج) --------------------
st.markdown("""
<style>
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0a0a !important; }
.card { background: rgba(10,10,10,0.8); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.1); border-radius: 12px; padding: 15px; margin: 5px 0; }
.buy { border-left: 6px solid #00ff88; }
.sell { border-left: 6px solid #ff4444; }
.wait { border-left: 6px solid #ffaa00; }
.layer { border-left: 4px solid #ffd700; padding: 8px 12px; margin: 4px 0; background: rgba(255,215,0,0.03); }
.footer { text-align: center; color: #444; font-size: 0.65rem; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# -------------------- CONSTANTS --------------------
GOLD_API_KEY = st.secrets.get("GOLD_API_KEY", "demo")
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY", "demo")
MAX_TRADES_PER_DAY = 2
MAX_OPEN_RISK = 0.05  # 5% من رأس المال
RISK_PER_TRADE = 0.02  # 2% لكل صفقة

PAIRS = {
    "XAU/USD (Gold)": "GC=F",
    "XAG/USD (Silver)": "SI=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
    "ETH/USD (Ethereum)": "ETH-USD",
}

# -------------------- SESSION STATE --------------------
if "all_signals" not in st.session_state: st.session_state.all_signals = None
if "last_update" not in st.session_state: st.session_state.last_update = datetime.now()
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

# -------------------- INDICATORS (Core) --------------------
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

# -------------------- SMC (Vectorized) --------------------
def detect_smc(df):
    df = df.copy()
    body = (df['close'] - df['open']).abs()
    avg_body = body.rolling(20).mean()
    strong_bull = (df['close'] > df['open']) & (body > avg_body * 1.5)
    strong_bear = (df['close'] < df['open']) & (body > avg_body * 1.5)
    df['ob_bullish'] = strong_bear.shift(1) & (df['close'] > df['high'].shift(1))
    df['ob_bearish'] = strong_bull.shift(1) & (df['close'] < df['low'].shift(1))
    df['fvg_bullish'] = (df['low'] > df['high'].shift(2))
    df['fvg_bearish'] = (df['high'] < df['low'].shift(2))
    df['liquidity_sweep_bullish'] = (df['high'] > df['high'].rolling(20).max().shift(1))
    df['liquidity_sweep_bearish'] = (df['low'] < df['low'].rolling(20).min().shift(1))
    df['mss_bullish'] = (df['low'] < df['low'].shift(1)) & (df['close'] > df['high'].shift(1))
    df['mss_bearish'] = (df['high'] > df['high'].shift(1)) & (df['close'] < df['low'].shift(1))
    # BOS
    df['bos_bullish'] = (df['close'] > df['high'].rolling(5).max().shift(1))
    df['bos_bearish'] = (df['close'] < df['low'].rolling(5).min().shift(1))
    return df

# -------------------- SWING POINTS (لـ Fibonacci و SL) --------------------
def find_swings(df, order=5):
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

def get_swing_levels(df):
    peaks, troughs = find_swings(df, order=5)
    swing_high = df['high'][peaks].iloc[-1] if any(peaks) else df['high'].max()
    swing_low = df['low'][troughs].iloc[-1] if any(troughs) else df['low'].min()
    return swing_high, swing_low

# -------------------- DXY --------------------
def get_dxy_correlation(df_pair, df_dxy, lookback=50):
    if df_pair is None or df_dxy is None or len(df_pair) < lookback: return 0.0
    pair = df_pair[['close']].pct_change().dropna()
    dxy = df_dxy[['close']].pct_change().dropna()
    combined = pd.concat([pair, dxy], axis=1, join='inner').dropna()
    if len(combined) < lookback: return 0.0
    return float(combined.iloc[-lookback:, 0].corr(combined.iloc[-lookback:, 1]) or 0.0)

# -------------------- NEWS FILTER (محاكاة) --------------------
def get_news_impact(symbol):
    """
    محاكاة: في الحقيقة يجب استخدام API وتحليل المشاعر.
    هنا نعيد None أو (impact, headline) حيث impact عالي/متوسط/منخفض
    """
    # في النسخة الحقيقية، استخدم Alpha Vantage أو NewsAPI
    return None  # لا يوجد أخبار مؤثرة حالياً

# -------------------- CALCULATE ALL INDICATORS --------------------
def calculate_all_indicators(df):
    if df is None or len(df) < 30:
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
    smc = detect_smc(df)
    for col in ['ob_bullish','ob_bearish','fvg_bullish','fvg_bearish',
                'liquidity_sweep_bullish','liquidity_sweep_bearish',
                'mss_bullish','mss_bearish','bos_bullish','bos_bearish']:
        df[col] = smc[col]
    return df

# -------------------- LAYER 1: MARKET REGIME --------------------
def detect_regime(df):
    if df is None or len(df) < 50:
        return "NEUTRAL", "بيانات غير كافية"
    last = df.iloc[-1]
    adx = last['adx'] if 'adx' in df.columns else 20
    atr = last['atr'] if 'atr' in df.columns else 10
    atr_ma = df['atr'].iloc[-20:].mean() if 'atr' in df.columns else atr
    ema20 = last['ema20'] if 'ema20' in df.columns else df['close'].iloc[-1]
    ema50 = last['ema50'] if 'ema50' in df.columns else df['close'].iloc[-1]
    bb_width = (last['bb_upper'] - last['bb_lower']) / last['bb_middle'] if all(k in df.columns for k in ['bb_upper','bb_lower','bb_middle']) else 0.05

    regime = "NEUTRAL"
    reason = "حالة السوق غير محددة"
    if adx > 25 and abs(ema20 - ema50) / ema50 > 0.01:
        regime = "TRENDING"
        reason = "اتجاه واضح (ADX مرتفع)"
    elif adx < 20 and bb_width < 0.05:
        regime = "RANGING"
        reason = "سوق عرضي (ADX منخفض وBB ضيق)"
    elif adx > 25 and atr > atr_ma * 1.5:
        regime = "HIGH_VOL"
        reason = "تقلب مرتفع"
    elif adx < 20 and atr < atr_ma * 0.7:
        regime = "LOW_VOL"
        reason = "تقلب منخفض - انتظار اختراق"
    return regime, reason

# -------------------- LAYER 2: 4H BIAS --------------------
def get_4h_bias(df_4h):
    if df_4h is None or len(df_4h) < 50:
        return "NEUTRAL", "بيانات 4H غير كافية"
    last = df_4h.iloc[-1]
    # EMA
    ema20 = last['ema20'] if 'ema20' in df_4h.columns else df_4h['close'].iloc[-1]
    ema50 = last['ema50'] if 'ema50' in df_4h.columns else df_4h['close'].iloc[-1]
    # Price relative to Ichimoku
    in_cloud = False
    if all(k in df_4h.columns for k in ['senkou_a','senkou_b']):
        price = last['close']
        if price > min(last['senkou_a'], last['senkou_b']) and price < max(last['senkou_a'], last['senkou_b']):
            in_cloud = True
    if in_cloud:
        return "NEUTRAL", "السعر داخل Ichimoku Cloud"
    if ema20 > ema50:
        return "BULLISH", "EMA20 > EMA50 (اتجاه صاعد)"
    elif ema20 < ema50:
        return "BEARISH", "EMA20 < EMA50 (اتجاه هابط)"
    else:
        return "NEUTRAL", "EMA متقاربة"

# -------------------- LAYER 3: 1H CONFIRMATION --------------------
def confirm_1h(df_1h, bias):
    if df_1h is None or len(df_1h) < 50 or bias == "NEUTRAL":
        return False, "الـ Bias محايد أو بيانات غير كافية"
    last = df_1h.iloc[-1]
    # EMA alignment
    ema20 = last['ema20'] if 'ema20' in df_1h.columns else df_1h['close'].iloc[-1]
    ema50 = last['ema50'] if 'ema50' in df_1h.columns else df_1h['close'].iloc[-1]
    if bias == "BULLISH" and ema20 < ema50:
        return False, "1H يخالف الاتجاه (EMA20 < EMA50)"
    if bias == "BEARISH" and ema20 > ema50:
        return False, "1H يخالف الاتجاه (EMA20 > EMA50)"

    # MACD
    if all(k in df_1h.columns for k in ['macd','macd_signal']):
        if bias == "BULLISH" and last['macd'] < last['macd_signal']:
            return False, "1H MACD سلبي"
        if bias == "BEARISH" and last['macd'] > last['macd_signal']:
            return False, "1H MACD إيجابي"

    # ADX + DI
    if all(k in df_1h.columns for k in ['adx','plus_di','minus_di']):
        if last['adx'] < 25:
            return False, "ADX ضعيف (<25)"
        if bias == "BULLISH" and last['plus_di'] < last['minus_di']:
            return False, "1H -DI > +DI (اتجاه هابط)"
        if bias == "BEARISH" and last['minus_di'] < last['plus_di']:
            return False, "1H +DI > -DI (اتجاه صاعد)"

    # BOS/MSS
    if bias == "BULLISH":
        if not (last.get('bos_bullish', False) or last.get('mss_bullish', False)):
            return False, "لا يوجد BOS/MSS صاعد على 1H"
    else:
        if not (last.get('bos_bearish', False) or last.get('mss_bearish', False)):
            return False, "لا يوجد BOS/MSS هابط على 1H"

    return True, "1H مؤكد للاتجاه"

# -------------------- LAYER 4: 15M TRIGGER --------------------
def get_15m_trigger(df_15m, bias):
    if df_15m is None or len(df_15m) < 30 or bias == "NEUTRAL":
        return False, "لا يوجد Trigger (بيانات غير كافية أو Bias محايد)"
    last = df_15m.iloc[-1]
    # البحث عن Trigger
    if bias == "BULLISH":
        # Liquidity Sweep للأسفل (كنس السيولة) ثم MSS/BOS صاعد
        if last.get('liquidity_sweep_bullish', False) or last.get('mss_bullish', False) or last.get('bos_bullish', False):
            # نتحقق من وجود منطقة FVG أو OB صاعدة
            if last.get('fvg_bullish', False) or last.get('ob_bullish', False):
                return True, "Trigger: Liquidity Sweep + FVG/OB صاعد"
        # شمعة تأكيد (جسم كبير صاعد)
        body = abs(last['close'] - last['open'])
        avg_body = abs(df_15m['close'] - df_15m['open']).rolling(20).mean().iloc[-1]
        if body > avg_body * 1.5 and last['close'] > last['open']:
            return True, "Trigger: شمعة تأكيد صاعدة قوية"
        return False, "لا يوجد Trigger صاعد مناسب"
    else:  # BEARISH
        if last.get('liquidity_sweep_bearish', False) or last.get('mss_bearish', False) or last.get('bos_bearish', False):
            if last.get('fvg_bearish', False) or last.get('ob_bearish', False):
                return True, "Trigger: Liquidity Sweep + FVG/OB هابط"
        body = abs(last['close'] - last['open'])
        avg_body = abs(df_15m['close'] - df_15m['open']).rolling(20).mean().iloc[-1]
        if body > avg_body * 1.5 and last['close'] < last['open']:
            return True, "Trigger: شمعة تأكيد هابطة قوية"
        return False, "لا يوجد Trigger هابط مناسب"

# -------------------- LAYER 5: PRICE LOCATION --------------------
def check_price_location(df, symbol, bias):
    if df is None or len(df) < 30:
        return False, "بيانات غير كافية لتحديد الموقع"
    last = df.iloc[-1]
    price = last['close']
    # Swing High/Low
    swing_high, swing_low = get_swing_levels(df)
    # Fibonacci
    diff = swing_high - swing_low
    if diff == 0:
        return False, "المدى السعري صفر"
    fib_618 = swing_high - diff * 0.618
    fib_382 = swing_high - diff * 0.382
    # BB
    bb_lower = last['bb_lower'] if 'bb_lower' in df.columns else price * 0.95
    bb_upper = last['bb_upper'] if 'bb_upper' in df.columns else price * 1.05

    if bias == "BULLISH":
        # نفضل Discount Zone (تحت 0.5) أو قرب الدعم
        if price < fib_382:
            return True, "السعر في منطقة Discount (تحت 0.382)"
        elif price < bb_lower:
            return True, "السعر تحت Bollinger Lower (منطقة شراء)"
        else:
            return False, "السعر ليس في منطقة شراء مناسبة (Premium)"
    else:  # BEARISH
        if price > fib_618:
            return True, "السعر في منطقة Premium (فوق 0.618)"
        elif price > bb_upper:
            return True, "السعر فوق Bollinger Upper (منطقة بيع)"
        else:
            return False, "السعر ليس في منطقة بيع مناسبة (Discount)"

# -------------------- LAYER 6: NEWS FILTER --------------------
def check_news(symbol, bias):
    news = get_news_impact(symbol)
    if news is None:
        return True, "لا توجد أخبار مؤثرة"
    impact, headline = news
    if impact == "HIGH":
        return False, f"خبر عالي التأثير: {headline}"
    elif impact == "MEDIUM" and bias != "NEUTRAL":
        # أخبار متوسطة قد تسبب تقلبات، نفضل الانتظار قليلاً
        return False, f"خبر متوسط التأثير: {headline} (انتظار)"
    else:
        return True, "الأخبار لا تعارض الصفقة"

# -------------------- LAYER 7: RISK MANAGEMENT --------------------
def calculate_position_size(account_balance, risk_per_trade, entry, stop_loss, pair):
    risk_amount = account_balance * risk_per_trade
    risk_per_unit = abs(entry - stop_loss)
    if risk_per_unit == 0:
        return 0
    # تبسيط: في الحقيقة تختلف حسب نوع الأصل
    if "USD" in pair or "XAU" in pair or "XAG" in pair:
        # لكل وحدة (عقد) الخسارة تساوي risk_per_unit دولار (لـ Gold و Forex)
        units = risk_amount / risk_per_unit
    else:
        # للعملات الرقمية: وحدة واحدة = 1 عملة
        units = risk_amount / risk_per_unit
    return max(0, units)

def check_total_risk(active_trades, new_risk):
    total_risk = sum(t.get('risk', 0) for t in active_trades.values())
    return (total_risk + new_risk) <= MAX_OPEN_RISK

# -------------------- MAIN HIERARCHICAL DECISION --------------------
def hierarchical_decision(df_4h, df_1h, df_15m, symbol, account_balance=10000):
    # Layer 1: Regime
    regime, regime_reason = detect_regime(df_4h)  # نستخدم 4H لتحديد النظام

    # إذا كان السوق في حالة RANGING أو LOW_VOL، نفضل الانتظار
    if regime in ["RANGING", "LOW_VOL"]:
        return "WAIT", f"WAIT — {regime_reason}", 0, {}, {}

    # Layer 2: 4H Bias
    bias, bias_reason = get_4h_bias(df_4h)
    if bias == "NEUTRAL":
        return "WAIT", f"WAIT — {bias_reason}", 0, {}, {}

    # Layer 3: 1H Confirmation
    confirmed, conf_reason = confirm_1h(df_1h, bias)
    if not confirmed:
        return "WAIT", f"WAIT — {conf_reason}", 0, {}, {}

    # Layer 4: 15M Trigger
    triggered, trigger_reason = get_15m_trigger(df_15m, bias)
    if not triggered:
        return "WAIT", f"WAIT — {trigger_reason}", 0, {}, {}

    # Layer 5: Price Location
    price_ok, price_reason = check_price_location(df_15m, symbol, bias)
    if not price_ok:
        return "WAIT", f"WAIT — {price_reason}", 0, {}, {}

    # Layer 6: News Filter
    news_ok, news_reason = check_news(symbol, bias)
    if not news_ok:
        return "WAIT", f"WAIT — {news_reason}", 0, {}, {}

    # إذا وصلنا هنا، جميع الطبقات متوافقة → نحدد الإشارة
    signal = "BUY" if bias == "BULLISH" else "SELL"

    # حساب الدخول والوقف والأهداف
    last_15m = df_15m.iloc[-1]
    price = last_15m['close']
    atr = last_15m['atr'] if 'atr' in df_15m.columns else 10

    # Stop Loss: Structure + ATR + Liquidity (تجنب مناطق السيولة الواضحة)
    if signal == "BUY":
        swing_low = df_15m['low'].iloc[-10:].min()
        sl = min(swing_low, price - atr * 1.5)
        # تجنب وضع SL تحت مستوى سيولة واضح (مثل قمة/قاع سابق)
        if df_15m['low'].iloc[-5:].min() == sl:
            sl = price - atr * 1.8  # نحركه قليلاً
        tp1 = price + (price - sl) * 1.5
        tp2 = price + (price - sl) * 2.5
        tp3 = price + (price - sl) * 4.0
    else:
        swing_high = df_15m['high'].iloc[-10:].max()
        sl = max(swing_high, price + atr * 1.5)
        if df_15m['high'].iloc[-5:].max() == sl:
            sl = price + atr * 1.8
        tp1 = price - (sl - price) * 1.5
        tp2 = price - (sl - price) * 2.5
        tp3 = price - (sl - price) * 4.0

    # حساب حجم الصفقة
    risk_per_trade = RISK_PER_TRADE
    units = calculate_position_size(account_balance, risk_per_trade, price, sl, symbol)

    # فحص المخاطرة الإجمالية
    new_risk = account_balance * risk_per_trade
    if not check_total_risk(st.session_state.active_trades, new_risk):
        return "WAIT", f"WAIT — إجمالي المخاطرة تجاوز الحد الأقصى ({MAX_OPEN_RISK*100:.0f}%)", 0, {}, {}

    # بناء النتيجة
    details = {
        "Regime": regime_reason,
        "Bias": bias_reason,
        "Confirmation": conf_reason,
        "Trigger": trigger_reason,
        "Price Location": price_reason,
        "News": news_reason,
        "Entry": price,
        "SL": sl,
        "TP1": tp1,
        "TP2": tp2,
        "TP3": tp3,
        "Units": units,
        "Risk": new_risk / account_balance * 100,
    }

    # الثقة تعكس مدى التوافق (عدد الطبقات المتوافقة)
    confidence = 70 + (10 if regime == "TRENDING" else 5) + (5 if price_ok else 0)
    confidence = min(95, confidence)

    return signal, f"{signal} — جميع الطبقات متوافقة", confidence, details, {"entry": price, "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3, "units": units}

# -------------------- BACKTEST (محاكاة بسيطة) --------------------
def run_backtest_hierarchical(df, symbol, lookback=500):
    # نحتاج بيانات 4H, 1H, 15M للاختبار
    # لكن للتبسيط، نستخدم الإطار الزمني الوحيد المتاح ونحاكي الطبقات
    # في النسخة الحقيقية، يجب جلب بيانات منفصلة لكل إطار
    return {"total_trades": 0, "win_rate": 0, "profit_factor": 0}  # للتبسيط

# -------------------- COLLECT SIGNALS (للجدول) --------------------
@st.cache_data(ttl=120)
def get_all_signals_hierarchical():
    results = []
    for pair_name, symbol in PAIRS.items():
        try:
            # جلب البيانات لكل إطار زمني
            df_4h = get_historical_data(symbol, period="1mo", interval="4h")
            df_1h = get_historical_data(symbol, period="1mo", interval="1h")
            df_15m = get_historical_data(symbol, period="7d", interval="15m")
            if df_4h is None or df_1h is None or df_15m is None:
                continue
            df_4h = calculate_all_indicators(df_4h)
            df_1h = calculate_all_indicators(df_1h)
            df_15m = calculate_all_indicators(df_15m)

            signal, reason, confidence, details, targets = hierarchical_decision(df_4h, df_1h, df_15m, symbol)

            if signal != "WAIT":
                results.append({
                    "Instrument": pair_name,
                    "Signal": signal,
                    "Confidence": round(confidence, 1),
                    "Reason": reason,
                    "Entry": f"{details['Entry']:.4f}",
                    "SL": f"{details['SL']:.4f}",
                    "TP1": f"{details['TP1']:.4f}",
                    "TP2": f"{details['TP2']:.4f}",
                    "TP3": f"{details['TP3']:.4f}",
                })
        except Exception as e:
            continue
    return pd.DataFrame(results)

# -------------------- STREAMLIT UI --------------------
with st.sidebar:
    st.markdown("## 📊 BLACK PYRAMID v2003")
    st.caption("Hierarchical Decision Engine")
    if st.button("🔄 Scan"):
        with st.spinner("Analyzing..."):
            st.session_state.all_signals = get_all_signals_hierarchical()
            st.session_state.last_update = datetime.now()
        st.rerun()
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        st.dataframe(st.session_state.all_signals, hide_index=True, use_container_width=True)
        st.caption(f"🕐 {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("Press Scan")
    selected_pair = st.selectbox("📊 Analyze", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]

# -------------------- MAIN DISPLAY --------------------
price, change = get_spot_price(selected_symbol)
df_4h = get_historical_data(selected_symbol, period="1mo", interval="4h")
df_1h = get_historical_data(selected_symbol, period="1mo", interval="1h")
df_15m = get_historical_data(selected_symbol, period="7d", interval="15m")

if df_4h is None or df_1h is None or df_15m is None:
    st.error("Failed to load data")
    st.stop()

df_4h = calculate_all_indicators(df_4h)
df_1h = calculate_all_indicators(df_1h)
df_15m = calculate_all_indicators(df_15m)

if price is None:
    price = df_15m['close'].iloc[-1]
    change = 0

signal, reason, confidence, details, targets = hierarchical_decision(df_4h, df_1h, df_15m, selected_symbol)

# عرض السعر
if "Gold" in selected_pair or "Silver" in selected_pair or "Bitcoin" in selected_pair:
    price_fmt = "${:,.2f}"
else:
    price_fmt = "{:.4f}"

st.markdown(f"""
<div class="card">
    <h3>{selected_pair}</h3>
    <span style="font-size:2rem;color:gold;">{price_fmt.format(price)}</span>
    <span style="color:{'#0f0' if change>=0 else '#f00'};"> {change:+.2f}%</span>
</div>
""", unsafe_allow_html=True)

# عرض القرار
if signal == "BUY":
    st.success(f"🟢 **BUY** — {reason} (Confidence: {confidence:.0f}%)")
elif signal == "SELL":
    st.error(f"🔴 **SELL** — {reason} (Confidence: {confidence:.0f}%)")
else:
    st.warning(f"🟡 **WAIT** — {reason}")

# عرض تفاصيل الطبقات
if details:
    with st.expander("📋 Layer Details", expanded=True):
        for key, value in details.items():
            st.write(f"**{key}:** {value}")

# عرض الأهداف والوقف
if signal != "WAIT" and targets:
    st.markdown(f"""
    <div class="card">
        <b>📍 Entry:</b> {price_fmt.format(targets['entry'])}<br>
        <b>🛑 SL:</b> {price_fmt.format(targets['sl'])} (Risk: {abs(targets['entry']-targets['sl'])/price*100:.2f}%)<br>
        <b>🎯 TP1:</b> {price_fmt.format(targets['tp1'])} (1.5R)<br>
        <b>🎯 TP2:</b> {price_fmt.format(targets['tp2'])} (2.5R)<br>
        <b>🎯 TP3:</b> {price_fmt.format(targets['tp3'])} (4R)<br>
        <b>📦 Units:</b> {targets['units']:.2f}
    </div>
    """, unsafe_allow_html=True)

# -------------------- CHART (مبسط) --------------------
fig = go.Figure()
fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['close'], name='Price', line=dict(color='gold')))
if 'ema20' in df_15m.columns:
    fig.add_trace(go.Scatter(x=df_15m.index, y=df_15m['ema20'], name='EMA20', line=dict(dash='dash')))
if signal != "WAIT" and targets:
    fig.add_hline(y=targets['sl'], line_dash='dash', line_color='red', annotation_text="SL")
    fig.add_hline(y=targets['entry'], line_dash='dash', line_color='green', annotation_text="Entry")
fig.update_layout(template='plotly_dark', height=400)
st.plotly_chart(fig, use_container_width=True)

# -------------------- FOOTER --------------------
st.markdown(f"""
<div class="footer">
    ▲ BLACK PYRAMID v2003 — Hierarchical Engine • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
