# ============================================================
# BLACK PYRAMID v2003 – PRECISION EDITION (Full Integration)
# Advanced Signal Engine with Balanced Weights & Dynamic Confidence
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

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="Black Pyramid v2003 - Precision",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CSS (مختصر ومحسّن) --------------------
st.markdown("""
<style>
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0a0a !important; }
.price-card, .suggested-trade { background: rgba(10,10,10,0.8); backdrop-filter: blur(6px); border: 1px solid rgba(255,215,0,0.1); border-radius: 12px; padding: 15px; }
.suggested-trade { border-color: #00ff88; }
.high-prob { border-left: 6px solid #00ff88; padding: 8px 12px; margin: 5px 0; background: rgba(0,255,136,0.05); }
.footer { text-align: center; color: #444; font-size: 0.65rem; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# -------------------- CONSTANTS & SECRETS --------------------
# ⚠️ IMPORTANT: Use st.secrets or environment variables instead of hardcoding keys!
GOLD_API_KEY = st.secrets.get("GOLD_API_KEY", "your-goldapi-key")
NEWS_API_KEY = st.secrets.get("NEWS_API_KEY", "your-news-api-key")
ALPHA_VANTAGE_KEY = st.secrets.get("ALPHA_VANTAGE_KEY", "your-alpha-vantage-key")

MIN_CONFIDENCE = 62          # الحد الأدنى للثقة للإشارة العادية
STRONG_CONFIDENCE = 75       # للإشارة القوية
BUY_THRESHOLD = 7            # net_score العادي
STRONG_BUY_THRESHOLD = 12    # net_score القوي
SELL_THRESHOLD = -7
STRONG_SELL_THRESHOLD = -12
MAX_TRADES_PER_DAY = 2
COOLDOWN_BARS = 6

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
if "all_signals" not in st.session_state:
    st.session_state.all_signals = None
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
if "active_trades" not in st.session_state:
    st.session_state.active_trades = {}
if "closed_trades" not in st.session_state:
    st.session_state.closed_trades = []
if "trade_stats" not in st.session_state:
    st.session_state.trade_stats = {"day": None, "count": 0}

# -------------------- DATA FETCHING --------------------
@st.cache_data(ttl=60)
def get_spot_price(symbol="GC=F"):
    try:
        t = yf.Ticker(symbol)
        data = t.history(period="1d", interval="5m")
        if not data.empty:
            last = data.iloc[-1]
            first = data.iloc[0]
            change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
            return float(last['Close']), float(change)
    except:
        pass
    return None, None

@st.cache_data(ttl=300)
def get_historical_data(symbol, period="1mo", interval="1h"):
    alt = {
        "GC=F": ["XAUUSD=X"],
        "SI=F": ["XAGUSD=X"],
        "DX-Y.NYB": ["DX=F"],
        "BTC-USD": ["BTCUSD=X"]
    }
    for sym in [symbol] + alt.get(symbol, []):
        try:
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=interval)
            if not df.empty:
                df.columns = [c.lower() for c in df.columns]
                return df
        except:
            continue
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

# -------------------- SMC / ICT (Vectorized) --------------------
def detect_smc_ict_advanced(df):
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

    # MSS (Market Structure Shift) – مبسط
    df['mss_bullish'] = (df['low'] < df['low'].shift(1)) & (df['close'] > df['high'].shift(1))
    df['mss_bearish'] = (df['high'] > df['high'].shift(1)) & (df['close'] < df['low'].shift(1))

    return df

# -------------------- SMR (Smart Money Reversal) --------------------
def detect_smr(df, lookback=10):
    if len(df) < lookback + 2:
        return None, None, None, None
    last = df.iloc[-1]
    low_zone = df['low'].iloc[-lookback-1:-1].min()
    high_zone = df['high'].iloc[-lookback-1:-1].max()
    if last['close'] > high_zone and last['close'] > last['open']:
        return "BULLISH", last['close'], low_zone, high_zone
    elif last['close'] < low_zone and last['close'] < last['open']:
        return "BEARISH", last['close'], high_zone, low_zone
    return None, None, None, None

# -------------------- PATTERNS (مبسط) --------------------
def detect_patterns(df):
    if len(df) < 3:
        return None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    # نموذج اختراق
    if last['close'] > df['high'].iloc[-3:-1].max() and last['close'] > last['open']:
        return "BULLISH"
    elif last['close'] < df['low'].iloc[-3:-1].min() and last['close'] < last['open']:
        return "BEARISH"
    return None

# -------------------- FIBONACCI --------------------
def calculate_fibonacci(df, lookback=20):
    if len(df) < lookback:
        return {}
    high = df['high'].iloc[-lookback:].max()
    low = df['low'].iloc[-lookback:].min()
    diff = high - low
    if diff == 0:
        return {}
    return {
        'fib_236': high - diff * 0.236,
        'fib_382': high - diff * 0.382,
        'fib_500': high - diff * 0.500,
        'fib_618': high - diff * 0.618,
        'fib_786': high - diff * 0.786,
    }

# -------------------- TBS (Turtle Soup Reversal) --------------------
def detect_tbs_correct(df, lookback=20, body_multiplier=1.5):
    if len(df) < lookback + 2:
        return None, None, None, None
    last = df.iloc[-1]
    lookback_high = df['high'].iloc[-lookback-1:-1].max()
    lookback_low = df['low'].iloc[-lookback-1:-1].min()
    avg_body = abs(df['close'] - df['open']).iloc[-lookback-1:-1].mean()
    current_body = abs(last['close'] - last['open'])
    if current_body < avg_body * body_multiplier:
        return None, None, None, None
    # Bearish Turtle Soup: اختراق القمة ثم العودة والإغلاق أسفلها
    if last['high'] > lookback_high and last['close'] < lookback_high:
        return "BEARISH", last['close'], last['high'], lookback_high
    # Bullish Turtle Soup: كسر القاع ثم العودة والإغلاق فوقه
    elif last['low'] < lookback_low and last['close'] > lookback_low:
        return "BULLISH", last['close'], last['low'], lookback_low
    return None, None, None, None

# -------------------- DXY & MTF --------------------
def get_dxy_correlation(df_pair, df_dxy, lookback=50):
    if df_pair is None or df_dxy is None or len(df_pair) < lookback:
        return 0.0
    pair = df_pair[['close']].pct_change().dropna()
    dxy = df_dxy[['close']].pct_change().dropna()
    combined = pd.concat([pair, dxy], axis=1, join='inner').dropna()
    if len(combined) < lookback:
        return 0.0
    return float(combined.iloc[-lookback:, 0].corr(combined.iloc[-lookback:, 1]) or 0.0)

def apply_dxy_filter(signal, dxy_signal, correlation):
    """ترجع (adjustment, status) حيث adjustment رقمي يُضاف للنتيجة"""
    if dxy_signal is None or dxy_signal == "WAIT" or signal == "WAIT":
        return 0, "NEUTRAL"
    if abs(correlation) < 0.30:
        return 0, "WEAK_CORRELATION"
    if correlation <= -0.60:
        aligned = (signal == "BUY" and dxy_signal == "SELL") or (signal == "SELL" and dxy_signal == "BUY")
        return (5 if aligned else -6), "STRONG_ALIGN" if aligned else "MISALIGN"
    elif correlation >= 0.60:
        aligned = signal == dxy_signal
        return (5 if aligned else -6), "STRONG_ALIGN" if aligned else "MISALIGN"
    else:
        aligned = (signal == "BUY" and dxy_signal == "SELL") if correlation < 0 else signal == dxy_signal
        return (2 if aligned else -3), "ALIGN" if aligned else "MISALIGN"

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
    if buy > sell:
        return "BUY", buy - sell
    elif sell > buy:
        return "SELL", sell - buy
    else:
        return "NEUTRAL", 0

# -------------------- NEWS SENTIMENT (محاكاة) --------------------
def get_news_sentiment(symbol):
    """
    في الواقع ستستخدم API مثل Alpha Vantage أو NewsAPI.
    هنا نعيد محاكاة بسيطة للتوضيح.
    """
    # استخدام st.cache_data لتجنب الطلبات المتكررة
    @st.cache_data(ttl=300)
    def _fetch_news(sym):
        # محاكاة: نعيد إشارة عشوائية لكن مع منطق
        # في الواقع: استخدم requests لجلب الأخبار وتحليل المشاعر
        import random
        sentiment = random.choice(["BULLISH", "BEARISH", "NEUTRAL"])
        score = random.uniform(20, 90) if sentiment != "NEUTRAL" else 0
        return sentiment, score
    return _fetch_news(symbol)

# -------------------- CALCULATE ALL INDICATORS --------------------
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
    df['tenkan'] = tenkan
    df['kijun'] = kijun
    df['senkou_a'] = senkou_a
    df['senkou_b'] = senkou_b
    df['mfi'] = calc_mfi(df)
    df['vwap'] = calc_vwap(df)
    smc_df = detect_smc_ict_advanced(df)
    for col in ['order_block_bullish', 'order_block_bearish',
                'fvg_bullish', 'fvg_bearish',
                'liquidity_sweep_bullish', 'liquidity_sweep_bearish',
                'mss_bullish', 'mss_bearish']:
        df[col] = smc_df[col]
    return df

# -------------------- SESSION FILTER --------------------
def is_london_ny_session():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    hour = now.hour
    return 2 <= hour <= 16  # London + NY

# -------------------- MAIN SIGNAL ENGINE (ADVANCED) --------------------
def generate_advanced_signal(df, symbol, period='1h', dxy_signal=None, dxy_correlation=0.0,
                             df_15m=None, df_1h=None, df_4h=None, df_daily=None):
    """
    BLACK PYRAMID v2003 – Advanced Signal Engine
    الأوزان الجديدة + الثقة الديناميكية + SMC التراكمي + TBS المصحح
    """
    if df is None or len(df) < 100:
        return "WAIT", 0, {}, {}, None, None, None, None, None, None, None

    # إذا لم تكن المؤشرات محسوبة، نحسبها
    required_cols = ['ema20', 'ema50', 'rsi', 'atr', 'macd', 'macd_signal',
                     'bb_upper', 'bb_lower', 'adx', 'plus_di', 'minus_di',
                     'tenkan', 'kijun', 'senkou_a', 'senkou_b', 'mfi', 'vwap']
    if not all(col in df.columns for col in required_cols):
        df = calculate_all_indicators(df)

    last = df.iloc[-1]
    current_price = last['close']

    # -------------------- الأوزان الجديدة --------------------
    weights = {
        'smc': 6,
        'smr': 5,
        'tbs': 5,
        'patterns': 4,
        'ichimoku': 3,
        'news': 3,
        'rsi': 2,
        'macd': 2,
        'bb': 2,
        'vwap': 2,
        'adx': 2,
        'mfi': 2,
        'fibonacci': 2,
    }

    scores = {'BUY': 0, 'SELL': 0}
    details = {}
    active_count = 0  # عدد المؤشرات الفعالة

    # -------------------- 1. SMC / ICT (تراكمي) --------------------
    smc_score = 0
    smc_msgs = []
    if last.get('order_block_bullish', False):
        smc_score += 2
        smc_msgs.append("OB صاعد")
    if last.get('order_block_bearish', False):
        smc_score -= 2
        smc_msgs.append("OB هابط")
    if last.get('fvg_bullish', False):
        smc_score += 1
        smc_msgs.append("FVG صاعد")
    if last.get('fvg_bearish', False):
        smc_score -= 1
        smc_msgs.append("FVG هابط")
    if last.get('liquidity_sweep_bullish', False):
        smc_score += 2
        smc_msgs.append("Liquidity Sweep صاعد")
    if last.get('liquidity_sweep_bearish', False):
        smc_score -= 2
        smc_msgs.append("Liquidity Sweep هابط")
    if last.get('mss_bullish', False):
        smc_score += 3
        smc_msgs.append("MSS صاعد")
    if last.get('mss_bearish', False):
        smc_score -= 3
        smc_msgs.append("MSS هابط")

    if smc_score > 0:
        add = min(weights['smc'], smc_score)
        scores['BUY'] += add
        details['SMC'] = f"{' | '.join(smc_msgs)} (+{add} BUY)"
        active_count += 1
    elif smc_score < 0:
        add = min(weights['smc'], abs(smc_score))
        scores['SELL'] += add
        details['SMC'] = f"{' | '.join(smc_msgs)} (+{add} SELL)"
        active_count += 1
    else:
        details['SMC'] = "لا توجد إشارة SMC"

    # -------------------- 2. SMR --------------------
    smr_signal, _, _, _ = detect_smr(df)
    if smr_signal == "BULLISH":
        scores['BUY'] += weights['smr']
        details['SMR'] = f"إشارة SMR صاعدة (+{weights['smr']} BUY)"
        active_count += 1
    elif smr_signal == "BEARISH":
        scores['SELL'] += weights['smr']
        details['SMR'] = f"إشارة SMR هابطة (+{weights['smr']} SELL)"
        active_count += 1
    else:
        details['SMR'] = "لا توجد إشارة SMR"

    # -------------------- 3. TBS المُصحّح --------------------
    tbs_type, _, _, _ = detect_tbs_correct(df)
    if tbs_type == "BULLISH":
        scores['BUY'] += weights['tbs']
        details['TBS'] = f"TBS شراء (+{weights['tbs']} BUY)"
        active_count += 1
    elif tbs_type == "BEARISH":
        scores['SELL'] += weights['tbs']
        details['TBS'] = f"TBS بيع (+{weights['tbs']} SELL)"
        active_count += 1
    else:
        details['TBS'] = "لا توجد إشارة TBS"

    # -------------------- 4. Patterns --------------------
    pattern_signal = detect_patterns(df)
    if pattern_signal == "BULLISH":
        scores['BUY'] += weights['patterns']
        details['Patterns'] = f"نمط صاعد (+{weights['patterns']} BUY)"
        active_count += 1
    elif pattern_signal == "BEARISH":
        scores['SELL'] += weights['patterns']
        details['Patterns'] = f"نمط هابط (+{weights['patterns']} SELL)"
        active_count += 1
    else:
        details['Patterns'] = "لا توجد أنماط"

    # -------------------- 5. Ichimoku --------------------
    if all(k in df.columns for k in ['tenkan', 'kijun', 'senkou_a', 'senkou_b']):
        tenkan = last['tenkan']; kijun = last['kijun']
        senkou_a = last['senkou_a']; senkou_b = last['senkou_b']
        if current_price > senkou_a and current_price > senkou_b and tenkan > kijun:
            scores['BUY'] += weights['ichimoku']
            details['Ichimoku'] = f"إيجابي (+{weights['ichimoku']} BUY)"
            active_count += 1
        elif current_price < senkou_a and current_price < senkou_b and tenkan < kijun:
            scores['SELL'] += weights['ichimoku']
            details['Ichimoku'] = f"سلبي (+{weights['ichimoku']} SELL)"
            active_count += 1
        else:
            details['Ichimoku'] = "محايد"

    # -------------------- 6. News (مع قوة المعنويات) --------------------
    news_sentiment = get_news_sentiment(symbol)
    if news_sentiment:
        sentiment, score = news_sentiment
        news_weight = weights['news']
        strength = min(abs(score) / 100, 1.0)
        effective = max(1, round(news_weight * strength))
        if sentiment == "BULLISH":
            scores['BUY'] += effective
            details['News_Sentiment'] = f"أخبار إيجابية ({score:.0f}%) +{effective} BUY"
            if effective > 0:
                active_count += 1
        elif sentiment == "BEARISH":
            scores['SELL'] += effective
            details['News_Sentiment'] = f"أخبار سلبية ({score:.0f}%) +{effective} SELL"
            if effective > 0:
                active_count += 1
        else:
            details['News_Sentiment'] = "محايدة"
    else:
        details['News_Sentiment'] = "لا توجد أخبار"

    # -------------------- 7. RSI --------------------
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if rsi < 30:
            scores['BUY'] += weights['rsi']
            details['RSI'] = f"تشبع بيعي ({rsi:.1f}) +{weights['rsi']} BUY"
            active_count += 1
        elif rsi > 70:
            scores['SELL'] += weights['rsi']
            details['RSI'] = f"تشبع شرائي ({rsi:.1f}) +{weights['rsi']} SELL"
            active_count += 1
        else:
            details['RSI'] = f"محايد ({rsi:.1f})"

    # -------------------- 8. MACD --------------------
    if all(k in df.columns for k in ['macd', 'macd_signal']):
        if last['macd'] > last['macd_signal']:
            scores['BUY'] += weights['macd']
            details['MACD'] = f"إيجابي (+{weights['macd']} BUY)"
            active_count += 1
        elif last['macd'] < last['macd_signal']:
            scores['SELL'] += weights['macd']
            details['MACD'] = f"سلبي (+{weights['macd']} SELL)"
            active_count += 1
        else:
            details['MACD'] = "محايد"

    # -------------------- 9. Bollinger --------------------
    if all(k in df.columns for k in ['bb_upper', 'bb_lower']):
        if current_price < last['bb_lower']:
            scores['BUY'] += weights['bb']
            details['BB'] = f"تحت النطاق السفلي (+{weights['bb']} BUY)"
            active_count += 1
        elif current_price > last['bb_upper']:
            scores['SELL'] += weights['bb']
            details['BB'] = f"فوق النطاق العلوي (+{weights['bb']} SELL)"
            active_count += 1
        else:
            details['BB'] = "داخل النطاق"

    # -------------------- 10. VWAP --------------------
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += weights['vwap']
            details['VWAP'] = f"فوق VWAP (+{weights['vwap']} BUY)"
            active_count += 1
        else:
            scores['SELL'] += weights['vwap']
            details['VWAP'] = f"تحت VWAP (+{weights['vwap']} SELL)"
            active_count += 1

    # -------------------- 11. ADX + DI --------------------
    if all(k in df.columns for k in ['adx', 'plus_di', 'minus_di']):
        adx = last['adx']; plus = last['plus_di']; minus = last['minus_di']
        if adx >= 25:
            if plus > minus:
                scores['BUY'] += weights['adx']
                details['ADX'] = f"اتجاه صاعد قوي ADX={adx:.1f} +{weights['adx']} BUY"
                active_count += 1
            elif minus > plus:
                scores['SELL'] += weights['adx']
                details['ADX'] = f"اتجاه هابط قوي ADX={adx:.1f} +{weights['adx']} SELL"
                active_count += 1
            else:
                details['ADX'] = f"اتجاه ضعيف ADX={adx:.1f}"
        else:
            details['ADX'] = f"ADX منخفض ({adx:.1f})"

    # -------------------- 12. MFI --------------------
    if 'mfi' in df.columns and not pd.isna(last['mfi']):
        mfi = last['mfi']
        if mfi < 20:
            scores['BUY'] += weights['mfi']
            details['MFI'] = f"تشبع بيعي MFI={mfi:.1f} +{weights['mfi']} BUY"
            active_count += 1
        elif mfi > 80:
            scores['SELL'] += weights['mfi']
            details['MFI'] = f"تشبع شرائي MFI={mfi:.1f} +{weights['mfi']} SELL"
            active_count += 1
        else:
            details['MFI'] = f"محايد ({mfi:.1f})"

    # -------------------- 13. Fibonacci --------------------
    fib_levels = calculate_fibonacci(df)
    if fib_levels:
        fib_weight = weights['fibonacci']
        if current_price > fib_levels.get('fib_618', current_price):
            scores['BUY'] += fib_weight
            details['Fibonacci'] = f"فوق 0.618 (+{fib_weight} BUY)"
            active_count += 1
        elif current_price < fib_levels.get('fib_382', current_price):
            scores['SELL'] += fib_weight
            details['Fibonacci'] = f"تحت 0.382 (+{fib_weight} SELL)"
            active_count += 1
        else:
            details['Fibonacci'] = "منطقة محايدة"

    # -------------------- 14. DXY --------------------
    if dxy_signal is not None and dxy_signal != "WAIT":
        # نحدد اتجاه الإشارة المبدئي (BUY/SELL) بناءً على scores الحالية
        temp_signal = "BUY" if scores['BUY'] > scores['SELL'] else "SELL" if scores['SELL'] > scores['BUY'] else "WAIT"
        if temp_signal != "WAIT":
            dxy_adj, dxy_status = apply_dxy_filter(temp_signal, dxy_signal, dxy_correlation)
            if dxy_adj > 0:
                scores['BUY'] += dxy_adj
                details['DXY'] = f"{dxy_status} (+{dxy_adj} BUY)"
                active_count += 1
            elif dxy_adj < 0:
                scores['SELL'] += abs(dxy_adj)
                details['DXY'] = f"{dxy_status} (+{abs(dxy_adj)} SELL)"
                active_count += 1
            else:
                details['DXY'] = dxy_status
        else:
            details['DXY'] = "إشارة مؤقتة WAIT"

    # -------------------- 15. MTF --------------------
    mtf_consensus, mtf_count = mtf_consensus_from_dataframes(df_15m, df_1h, df_4h)
    if mtf_consensus == "BUY":
        scores['BUY'] += 3
        details['MTF'] = f"إيجابي ({mtf_count} أطر) +3 BUY"
        active_count += 1
    elif mtf_consensus == "SELL":
        scores['SELL'] += 3
        details['MTF'] = f"سلبي ({mtf_count} أطر) +3 SELL"
        active_count += 1
    else:
        details['MTF'] = "محايد"

    # -------------------- حساب النتيجة والثقة --------------------
    net_score = scores['BUY'] - scores['SELL']
    total_score = scores['BUY'] + scores['SELL']

    if total_score > 0:
        direction_strength = abs(net_score) / total_score
    else:
        direction_strength = 0

    if net_score > 0:
        agreement = scores['BUY'] / total_score if total_score > 0 else 0
    elif net_score < 0:
        agreement = scores['SELL'] / total_score if total_score > 0 else 0
    else:
        agreement = 0.5

    confidence = agreement * 100
    confidence += direction_strength * 15
    confidence = min(100, confidence)

    # فلتر عدد الإشارات النشطة (يجب أن يكون 3 على الأقل)
    if active_count < 3:
        confidence = min(confidence, 55)
        signal = "WAIT"
        confidence = max(0, min(100, confidence))
        return "WAIT", confidence, net_score, details, scores, "Advanced", mtf_consensus, mtf_count, None, None, None

    # تحديد الإشارة حسب العتبات الجديدة
    if net_score >= STRONG_BUY_THRESHOLD and confidence >= STRONG_CONFIDENCE:
        signal = "STRONG BUY"
    elif net_score >= BUY_THRESHOLD and confidence >= MIN_CONFIDENCE:
        signal = "BUY"
    elif net_score <= STRONG_SELL_THRESHOLD and confidence >= STRONG_CONFIDENCE:
        signal = "STRONG SELL"
    elif net_score <= SELL_THRESHOLD and confidence >= MIN_CONFIDENCE:
        signal = "SELL"
    else:
        signal = "WAIT"

    confidence = max(0, min(100, confidence))

    # -------------------- Stop Loss & Targets --------------------
    stop_loss = None
    entry_price = current_price
    targets = {}

    if signal in ["BUY", "STRONG BUY", "SELL", "STRONG SELL"] and confidence >= MIN_CONFIDENCE:
        atr_val = last['atr'] if not pd.isna(last['atr']) else 10.0
        if signal in ["BUY", "STRONG BUY"]:
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
            stop_loss = entry_price - atr_val * 0.6 if signal in ["BUY", "STRONG BUY"] else entry_price + atr_val * 0.6
            risk = atr_val * 0.6

        if signal in ["BUY", "STRONG BUY"]:
            targets = {
                'target1': entry_price + risk,
                'target2': entry_price + risk * 1.8,
                'target3': entry_price + risk * 3.0,
                'risk_reward': 2.5
            }
        else:
            targets = {
                'target1': entry_price - risk,
                'target2': entry_price - risk * 1.8,
                'target3': entry_price - risk * 3.0,
                'risk_reward': 2.5
            }

    return signal, confidence, net_score, details, scores, "Advanced", mtf_consensus, mtf_count, stop_loss, entry_price, targets

# -------------------- BACKTEST (محسّن) --------------------
def run_backtest_advanced(df, symbol, lookback=500):
    if df is None or len(df) < 150:
        return {}
    test_df = df.iloc[-min(lookback, len(df)):].copy()
    test_df = calculate_all_indicators(test_df)

    df_daily = get_historical_data(symbol, period="3mo", interval="1d")
    df_daily = calculate_all_indicators(df_daily)

    trades = []
    active = None
    daily_count = {}

    for i in range(100, len(test_df) - 1):
        bar = test_df.iloc[i]
        day = str(bar.name.date()) if hasattr(bar.name, 'date') else str(i)

        # إدارة الصفقة المفتوحة
        if active:
            result, exit_price = _bar_exit_advanced(active, bar)
            if result:
                risk = abs(active['entry'] - active['stop'])
                reward = abs(exit_price - active['entry']) / risk if risk > 0 else 0
                trades.append({
                    'result': result,
                    'r': reward if result == 'TP' else -1,
                    'direction': active['direction'],
                    'entry_i': active['entry_i'],
                    'exit_i': i
                })
                active = None
            else:
                # Breakeven عند TP1
                if not active.get('breakeven_triggered', False):
                    if active['direction'] == "BUY" and bar['high'] >= active['tp1']:
                        active['stop'] = active['entry']
                        active['breakeven_triggered'] = True
                    elif active['direction'] == "SELL" and bar['low'] <= active['tp1']:
                        active['stop'] = active['entry']
                        active['breakeven_triggered'] = True
                continue

        if daily_count.get(day, 0) >= MAX_TRADES_PER_DAY:
            continue

        window = test_df.iloc[:i+1].copy()
        signal, conf, _, _, _, _, _, _, sl, entry, targets = generate_advanced_signal(
            window, symbol, dxy_signal=None, dxy_correlation=0.0,
            df_daily=df_daily
        )

        if signal == "WAIT" or conf < MIN_CONFIDENCE or sl is None or not targets:
            continue

        next_open = float(test_df['open'].iloc[i+1])
        stop = float(sl)
        tp1 = float(targets['target1'])
        tp3 = float(targets['target3'])

        if (signal in ["BUY", "STRONG BUY"] and stop >= next_open) or (signal in ["SELL", "STRONG SELL"] and stop <= next_open):
            continue

        active = {
            'direction': signal,
            'entry': next_open,
            'stop': stop,
            'tp1': tp1,
            'tp3': tp3,
            'entry_i': i + 1,
            'breakeven_triggered': False
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
    }

def _bar_exit_advanced(active, bar):
    if active['direction'] in ["BUY", "STRONG BUY"]:
        if bar['low'] <= active['stop']:
            return "loss", active['stop']
        if bar['high'] >= active['tp3']:
            return "win", active['tp3']
    else:
        if bar['high'] >= active['stop']:
            return "loss", active['stop']
        if bar['low'] <= active['tp3']:
            return "win", active['tp3']
    return None, None

# -------------------- COLLECT ALL SIGNALS --------------------
@st.cache_data(ttl=120)
def get_all_signals_advanced():
    results = []

    # DXY
    df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
    df_dxy = calculate_all_indicators(df_dxy)
    dxy_signal = None
    if df_dxy is not None and len(df_dxy) > 20:
        dxy_signal, _, _, _, _, _, _, _, _, _, _ = generate_advanced_signal(df_dxy, "DX-Y.NYB")

    daily_cache = {}

    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval="1h")
            if df is None or len(df) < 50:
                continue
            df = calculate_all_indicators(df)

            if symbol not in daily_cache:
                daily_cache[symbol] = get_historical_data(symbol, period="3mo", interval="1d")
                daily_cache[symbol] = calculate_all_indicators(daily_cache[symbol])
            df_daily = daily_cache.get(symbol)

            current_price = df['close'].iloc[-1]
            corr = get_dxy_correlation(df, df_dxy, lookback=50)

            signal, conf, score, details, factors, _, mtf, mtf_c, sl, entry, targets = generate_advanced_signal(
                df, symbol, dxy_signal=dxy_signal, dxy_correlation=corr,
                df_daily=df_daily
            )

            if signal not in ["WAIT"] and conf >= MIN_CONFIDENCE:
                bt = run_backtest_advanced(df, symbol)
                if any(x in pair_name for x in ["Gold", "Silver", "Bitcoin"]):
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
                    "Setup": details.get('SMC', 'N/A'),
                    "Bias": details.get('DXY', 'N/A'),
                    "Entry": fmt.format(entry) if entry else "N/A",
                    "SL": fmt.format(sl) if sl else "N/A",
                    "TP1": fmt.format(targets['target1']) if targets else "N/A",
                    "Win Rate": f"{bt.get('win_rate', 0):.1f}%" if bt else "N/A"
                })
        except Exception as e:
            continue

    return pd.DataFrame(results)

# -------------------- STREAMLIT UI --------------------
with st.sidebar:
    st.markdown("## 🎯 Precision Engine")
    st.caption("Balanced Weights | Dynamic Confidence | SMC Accumulation")
    if st.button("🔄 Scan for Setups"):
        with st.spinner("Analyzing..."):
            st.session_state.all_signals = get_all_signals_advanced()
            st.session_state.last_update = datetime.now()
        st.rerun()

    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_sig = st.session_state.all_signals.copy()
        df_sig["Signal"] = df_sig["Signal"].apply(lambda x: "🟢 "+x if "BUY" in x else "🔴 "+x if "SELL" in x else x)
        st.dataframe(
            df_sig[["Instrument", "Signal", "Confidence", "Score", "Setup", "Bias"]],
            hide_index=True,
            use_container_width=True,
            height=400
        )
        st.caption(f"🕐 {st.session_state.last_update.strftime('%H:%M:%S')} | {len(df_sig)} Setups")
    else:
        st.info("No setups found. Adjust filters or try again.")

    selected_pair = st.selectbox("📊 Analyze", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair]

# -------------------- MAIN DISPLAY --------------------
price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="60d", interval="15m")
if df is None:
    st.error("Failed to load data")
    st.stop()
if price is None:
    price = df['close'].iloc[-1]
    change = 0

df = calculate_all_indicators(df)

df_daily = get_historical_data(selected_symbol, period="3mo", interval="1d")
df_daily = calculate_all_indicators(df_daily)

df_dxy = get_historical_data("DX-Y.NYB", period="1mo", interval="1h")
df_dxy = calculate_all_indicators(df_dxy)
dxy_signal = None
corr = 0.0
if df_dxy is not None and len(df_dxy) > 20:
    dxy_signal, _, _, _, _, _, _, _, _, _, _ = generate_advanced_signal(df_dxy, "DX-Y.NYB")
    corr = get_dxy_correlation(df, df_dxy, lookback=50)

signal, conf, score, details, factors, regime, mtf, mtf_c, sl, entry, targets = generate_advanced_signal(
    df, selected_symbol, dxy_signal=dxy_signal, dxy_correlation=corr,
    df_daily=df_daily
)

if "Gold" in selected_pair or "Silver" in selected_pair or "Bitcoin" in selected_pair:
    price_fmt = "${:,.2f}"
else:
    price_fmt = "{:.4f}"

st.markdown(f"""
<div class="price-card">
    <h3>{selected_pair}</h3>
    <span style="font-size:2rem;color:gold;">{price_fmt.format(price)}</span>
    <span style="color:{'#0f0' if change>=0 else '#f00'};"> {change:+.2f}%</span>
</div>
""", unsafe_allow_html=True)

if dxy_signal:
    st.markdown(f"📊 DXY Signal: **{dxy_signal}** | Correlation: {corr:.2f}")

if signal not in ["WAIT"] and conf >= MIN_CONFIDENCE:
    st.markdown(f"""
    <div class="suggested-trade">
        <h4 style="color:#00ff88;">🎯 {signal} Setup</h4>
        <b>Confidence:</b> {conf:.0f}%<br>
        <b>📍 Entry:</b> {price_fmt.format(entry)}<br>
        <b>🛑 SL:</b> {price_fmt.format(sl)} (Risk: {abs(entry-sl)/price*100:.2f}%)<br>
        <b>🎯 TP1:</b> {price_fmt.format(targets['target1'])} | <b>TP2:</b> {price_fmt.format(targets['target2'])} | <b>TP3:</b> {price_fmt.format(targets['target3'])}<br>
        <b>📈 R:R</b> 1:{targets.get('risk_reward', 0):.1f}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📊 Factor Details", expanded=True):
        for k, v in details.items():
            st.write(f"**{k}:** {v}")
else:
    st.warning("⏳ No high-probability setup currently. Waiting for confluence.")

# Backtest
bt = run_backtest_advanced(df, selected_symbol)
if bt:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Trades", bt['total_trades'])
    col2.metric("Win Rate", f"{bt['win_rate']:.1f}%")
    col3.metric("Profit Factor", f"{bt['profit_factor']:.2f}")

# Chart
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold')))
if 'ema20' in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(dash='dash')))
if 'ema50' in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(dash='dash')))
if sl and entry:
    fig.add_hline(y=sl, line_dash='dash', line_color='red', annotation_text="SL")
    fig.add_hline(y=entry, line_dash='dash', line_color='green', annotation_text="Entry")
fig.update_layout(template='plotly_dark', height=450)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | BLACK PYRAMID v2003 - Precision Mode (Full Integration)")
