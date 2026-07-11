import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import json
import os

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS للتنسيق (نفس السابق)
# ==========================================
st.markdown("""
<style>
    .main-header { text-align: center; padding: 20px; background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); border-radius: 15px; margin-bottom: 20px; border: 1px solid #ffd70033; }
    .main-title { font-size: 2rem; color: #ffd700; font-weight: bold; letter-spacing: 2px; }
    .main-subtitle { font-size: 0.9rem; color: #aaa; }
    .price-card { background: #1a1a2e; border-radius: 15px; padding: 20px; text-align: center; border: 1px solid #ffd70033; margin: 10px 0; }
    .price-value { font-size: 3.5rem; font-weight: bold; color: #fff; }
    .price-change { font-size: 1.2rem; }
    .signal-box { background: #1a1a2e; border-radius: 15px; padding: 20px; text-align: center; border: 2px solid #ffd700; margin: 15px 0; }
    .signal-text { font-size: 2.5rem; font-weight: bold; }
    .signal-confidence { font-size: 1rem; color: #aaa; }
    .explanation-box { background: #1a1a2e; border-radius: 10px; padding: 15px; margin: 10px 0; border: 1px solid #ffd70033; text-align: left; white-space: pre-wrap; }
    .currency-card { background: #1a1a2e; border-radius: 10px; padding: 10px 15px; text-align: center; border: 1px solid #ffd70033; margin: 5px 0; }
    .currency-symbol { font-size: 0.8rem; color: #888; }
    .currency-price { font-size: 1.2rem; font-weight: bold; color: #fff; }
    .currency-change { font-size: 0.9rem; }
    .trade-row { background: #1a1a2e; border-radius: 10px; padding: 10px; margin: 5px 0; border-left: 4px solid #ffd700; }
    .footer { text-align: center; padding: 15px; color: #666; font-size: 0.8rem; border-top: 1px solid #333; margin-top: 30px; }
    .stButton button { background: #ffd700; color: #000; font-weight: bold; border-radius: 10px; width: 100%; }
    .news-card { background: #1a1a2e; border-radius: 10px; padding: 10px; margin: 5px 0; border-left: 3px solid #ffd700; }
    .news-title { color: #fff; font-weight: bold; }
    .news-date { color: #888; font-size: 0.8rem; }
    .suggested-trade { background: #1a1a2e; border-radius: 15px; padding: 15px; border: 2px solid #00ff88; margin: 15px 0; }
    .pattern-badge { display: inline-block; background: #ffd70033; border: 1px solid #ffd700; border-radius: 12px; padding: 4px 12px; margin: 3px; font-size: 0.8rem; color: #ffd700; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">Indicators + SMC/ICT + Patterns + MTF</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# إعدادات API
# ==========================================
GOLD_API_KEY = "goldapi-2262c60e69ce568bf76b982116077d1f-io"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"  # استبدل بمفتاحك

# ==========================================
# قائمة الأزواج
# ==========================================
PAIRS = {
    "XAU/USD (Gold)": "GC=F",
    "DXY (Dollar Index)": "DX-Y.NYB",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
    "ETH/USD (Ethereum)": "ETH-USD"
}

# ==========================================
# دوال جلب البيانات (نفس السابق)
# ==========================================
@st.cache_data(ttl=10)
def get_spot_price(symbol="GC=F"):
    try:
        if symbol == "GC=F":
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0)), float(data.get('change', 0))
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
def get_historical_data(symbol, period="1mo", interval="1h"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return None

@st.cache_data(ttl=60)
def get_all_forex():
    symbols = {
        "DXY": "DX-Y.NYB",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "BTCUSD": "BTC-USD"
    }
    results = {}
    for name, symbol in symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="5m")
            if not data.empty:
                last = data.iloc[-1]
                first = data.iloc[0]
                change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
                results[name] = {'price': float(last['Close']), 'change': float(change)}
            else:
                results[name] = {'price': 0, 'change': 0}
        except:
            results[name] = {'price': 0, 'change': 0}
    return results

@st.cache_data(ttl=600)
def get_economic_news():
    try:
        url = f"https://newsapi.org/v2/everything?q=gold OR forex OR economy&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=5"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            news_list = []
            for art in articles[:5]:
                news_list.append({
                    'title': art.get('title', ''),
                    'source': art.get('source', {}).get('name', ''),
                    'publishedAt': art.get('publishedAt', ''),
                    'url': art.get('url', '')
                })
            return news_list
    except:
        pass
    return []

# ==========================================
# المؤشرات الأساسية (نفس السابق)
# ==========================================
def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_atr(df, period=14):
    high = df['high']; low = df['low']; close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calc_macd(data):
    ema12 = data.ewm(span=12, adjust=False).mean()
    ema26 = data.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram

def calc_bollinger_bands(data, period=20, std_dev=2):
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def calc_adx(df, period=14):
    high = df['high']; low = df['low']; close = df['close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.ewm(span=period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).ewm(span=period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    return adx, plus_di, minus_di

def calc_ichimoku(df):
    high = df['high']; low = df['low']; close = df['close']
    tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
    kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
    chikou = close.shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou

def calc_vwap(df):
    return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

# ==========================================
# تحليل SMC/ICT
# ==========================================
def analyze_smc_ict(df):
    """إضافة أعمدة SMC/ICT إلى DataFrame"""
    df = df.copy()
    # تهيئة الأعمدة
    df['order_block_bullish'] = False
    df['order_block_bearish'] = False
    df['fvg_bullish'] = False
    df['fvg_bearish'] = False
    df['liquidity_sweep_bullish'] = False
    df['liquidity_sweep_bearish'] = False
    df['bos_bullish'] = False
    df['bos_bearish'] = False
    df['mss_bullish'] = False
    df['mss_bearish'] = False
    df['in_discount'] = False
    df['in_premium'] = False

    # 1. Order Blocks
    for i in range(3, len(df)):
        if df['close'].iloc[i] > df['open'].iloc[i]:
            body = df['close'].iloc[i] - df['open'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                df.loc[df.index[i-1], 'order_block_bullish'] = True
        if df['close'].iloc[i] < df['open'].iloc[i]:
            body = df['open'].iloc[i] - df['close'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                df.loc[df.index[i-1], 'order_block_bearish'] = True

    # 2. Fair Value Gaps (FVG)
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bullish'] = True
        if df['high'].iloc[i] < df['low'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bearish'] = True

    # 3. Liquidity Sweeps
    for i in range(10, len(df)):
        recent_lows = df['low'].iloc[i-10:i].tolist()
        if df['low'].iloc[i] < min(recent_lows[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bullish'] = True
        recent_highs = df['high'].iloc[i-10:i].tolist()
        if df['high'].iloc[i] > max(recent_highs[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bearish'] = True

    # 4. Break of Structure (BOS)
    for i in range(5, len(df)):
        if df['close'].iloc[i] > df['high'].iloc[i-5:i].max():
            df.loc[df.index[i], 'bos_bullish'] = True
        if df['close'].iloc[i] < df['low'].iloc[i-5:i].min():
            df.loc[df.index[i], 'bos_bearish'] = True

    # 5. Market Structure Shift (MSS)
    for i in range(3, len(df)):
        if df['bos_bearish'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[i-2:i].max():
            df.loc[df.index[i], 'mss_bullish'] = True
        if df['bos_bullish'].iloc[i-1] and df['close'].iloc[i] < df['low'].iloc[i-2:i].min():
            df.loc[df.index[i], 'mss_bearish'] = True

    # 6. Premium / Discount Zones (Fibonacci 38.2% و 61.8%)
    for i in range(50, len(df)):
        range_high = df['high'].iloc[i-50:i].max()
        range_low = df['low'].iloc[i-50:i].min()
        if range_high != range_low:
            discount = range_low + (range_high - range_low) * 0.382
            premium = range_high - (range_high - range_low) * 0.382
            if df['close'].iloc[i] <= discount:
                df.loc[df.index[i], 'in_discount'] = True
            if df['close'].iloc[i] >= premium:
                df.loc[df.index[i], 'in_premium'] = True

    return df

# ==========================================
# اكتشاف النماذج الفنية (Patterns)
# ==========================================
def find_peaks_troughs(series, order=5):
    peaks = []
    troughs = []
    for i in range(order, len(series) - order):
        if all(series[i] > series[i-j] for j in range(1, order+1)) and all(series[i] > series[i+j] for j in range(1, order+1)):
            peaks.append((i, series[i]))
        if all(series[i] < series[i-j] for j in range(1, order+1)) and all(series[i] < series[i+j] for j in range(1, order+1)):
            troughs.append((i, series[i]))
    return peaks, troughs

def detect_head_shoulders(df, lookback=50):
    if len(df) < lookback:
        return None, 0
    recent_highs = df['high'].iloc[-lookback:].values
    peaks, _ = find_peaks_troughs(recent_highs, order=3)
    if len(peaks) >= 3:
        head_idx = np.argmax([p[1] for p in peaks])
        if head_idx > 0 and head_idx < len(peaks) - 1:
            left_shoulder = peaks[head_idx - 1][1]
            head = peaks[head_idx][1]
            right_shoulder = peaks[head_idx + 1][1]
            if head > left_shoulder and head > right_shoulder:
                if abs(left_shoulder - right_shoulder) / left_shoulder < 0.05:
                    return "HEAD_AND_SHOULDERS", 5
    return None, 0

def detect_double_top_bottom(df, lookback=50):
    if len(df) < lookback:
        return None, 0
    recent_highs = df['high'].iloc[-lookback:].values
    recent_lows = df['low'].iloc[-lookback:].values
    peaks, _ = find_peaks_troughs(recent_highs, order=3)
    _, troughs = find_peaks_troughs(recent_lows, order=3)
    if len(peaks) >= 2:
        last_two_peaks = sorted(peaks[-2:], key=lambda x: x[0])
        if abs(last_two_peaks[-1][1] - last_two_peaks[-2][1]) / last_two_peaks[-2][1] < 0.03:
            return "DOUBLE_TOP", 4
    if len(troughs) >= 2:
        last_two_troughs = sorted(troughs[-2:], key=lambda x: x[0])
        if abs(last_two_troughs[-1][1] - last_two_troughs[-2][1]) / last_two_troughs[-2][1] < 0.03:
            return "DOUBLE_BOTTOM", 4
    return None, 0

def detect_triangle_pattern(df, lookback=40):
    if len(df) < lookback:
        return None, 0
    recent_data = df.iloc[-lookback:]
    highs = recent_data['high'].values
    lows = recent_data['low'].values
    x = np.arange(len(highs))
    slope_highs = np.polyfit(x, highs, 1)[0]
    slope_lows = np.polyfit(x, lows, 1)[0]
    if slope_lows > 0.01 and abs(slope_highs) < 0.005:
        return "ASCENDING_TRIANGLE", 3
    if slope_highs < -0.01 and abs(slope_lows) < 0.005:
        return "DESCENDING_TRIANGLE", 3
    return None, 0

def analyze_chart_patterns(df):
    patterns = []
    total_score = 0
    pattern, score = detect_head_shoulders(df)
    if pattern:
        patterns.append({"pattern": pattern, "score": score, "direction": "BEARISH"})
        total_score += score
    pattern, score = detect_double_top_bottom(df)
    if pattern:
        direction = "BEARISH" if "DOUBLE_TOP" in pattern else "BULLISH"
        patterns.append({"pattern": pattern, "score": score, "direction": direction})
        total_score += score
    pattern, score = detect_triangle_pattern(df)
    if pattern:
        direction = "BULLISH" if "ASCENDING" in pattern else "BEARISH"
        patterns.append({"pattern": pattern, "score": score, "direction": direction})
        total_score += score
    return patterns, total_score

# ==========================================
# نظام التسجيل المتكامل (Indicators + SMC + Patterns)
# ==========================================
def generate_advanced_signal(df, current_price, symbol=""):
    if df is None or len(df) < 100:
        return "WAIT", 50, 0, {}, []

    # تحليل SMC والأنماط
    df_smc = analyze_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    patterns, _ = analyze_chart_patterns(df)

    last = df.iloc[-1]
    scores = {'BUY': 0, 'SELL': 0}
    details = {}
    weights = {
        'rsi': 3, 'macd': 2, 'bb': 2, 'vwap': 1, 'adx': 1, 'ichimoku': 3,
        'smc': 3, 'patterns': 4
    }

    # ===== المؤشرات الكلاسيكية =====
    # RSI
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if rsi < 30:
            scores['BUY'] += weights['rsi']; details['RSI'] = f"مفرط البيع ({rsi:.1f}) +{weights['rsi']}"
        elif rsi > 70:
            scores['SELL'] += weights['rsi']; details['RSI'] = f"مفرط الشراء ({rsi:.1f}) +{weights['rsi']}"
        else:
            details['RSI'] = f"محايد ({rsi:.1f})"

    # MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns and not pd.isna(last['macd']):
        if last['macd'] > last['macd_signal'] and last['macd'] > 0:
            scores['BUY'] += weights['macd']; details['MACD'] = f"إيجابي +{weights['macd']}"
        elif last['macd'] < last['macd_signal'] and last['macd'] < 0:
            scores['SELL'] += weights['macd']; details['MACD'] = f"سلبي +{weights['macd']}"
        else:
            details['MACD'] = "محايد"

    # BB
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and not pd.isna(last['bb_upper']):
        if current_price <= last['bb_lower'] * 1.005:
            scores['BUY'] += weights['bb']; details['BB'] = f"قرب الحد السفلي +{weights['bb']}"
        elif current_price >= last['bb_upper'] * 0.995:
            scores['SELL'] += weights['bb']; details['BB'] = f"قرب الحد الأعلى +{weights['bb']}"
        else:
            details['BB'] = "وسط النطاق"

    # VWAP
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += weights['vwap']; details['VWAP'] = f"فوق VWAP +{weights['vwap']}"
        else:
            scores['SELL'] += weights['vwap']; details['VWAP'] = f"تحت VWAP +{weights['vwap']}"

    # ADX
    if 'adx' in df.columns and not pd.isna(last['adx']):
        if last['adx'] > 25:
            if df['close'].iloc[-1] > df['close'].iloc[-5]:
                scores['BUY'] += 1; details['ADX'] = f"اتجاه قوي صاعد +1"
            else:
                scores['SELL'] += 1; details['ADX'] = f"اتجاه قوي هابط +1"
        else:
            details['ADX'] = f"اتجاه ضعيف ({last['adx']:.1f})"

    # Ichimoku
    if 'senkou_a' in df.columns and 'senkou_b' in df.columns and 'chikou' in df.columns:
        if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']) and not pd.isna(last['chikou']):
            if current_price > last['senkou_a'] and current_price > last['senkou_b']:
                scores['BUY'] += weights['ichimoku']; details['Ichimoku'] = f"فوق السحابة +{weights['ichimoku']}"
            elif current_price < last['senkou_a'] and current_price < last['senkou_b']:
                scores['SELL'] += weights['ichimoku']; details['Ichimoku'] = f"تحت السحابة +{weights['ichimoku']}"
            else:
                details['Ichimoku'] = "داخل السحابة"

    # ===== SMC/ICT =====
    if last_smc.get('order_block_bullish', False):
        scores['BUY'] += weights['smc']; details['SMC'] = f"كتلة أوامر شراء +{weights['smc']}"
    elif last_smc.get('order_block_bearish', False):
        scores['SELL'] += weights['smc']; details['SMC'] = f"كتلة أوامر بيع +{weights['smc']}"
    elif last_smc.get('fvg_bullish', False):
        scores['BUY'] += weights['smc']//2; details['SMC'] = f"FVG شراء +{weights['smc']//2}"
    elif last_smc.get('fvg_bearish', False):
        scores['SELL'] += weights['smc']//2; details['SMC'] = f"FVG بيع +{weights['smc']//2}"
    elif last_smc.get('liquidity_sweep_bullish', False):
        scores['BUY'] += weights['smc']//2; details['SMC'] = f"اجتياح سيولة شراء +{weights['smc']//2}"
    elif last_smc.get('liquidity_sweep_bearish', False):
        scores['SELL'] += weights['smc']//2; details['SMC'] = f"اجتياح سيولة بيع +{weights['smc']//2}"
    elif last_smc.get('mss_bullish', False):
        scores['BUY'] += weights['smc']; details['SMC'] = f"تحول هيكل صاعد +{weights['smc']}"
    elif last_smc.get('mss_bearish', False):
        scores['SELL'] += weights['smc']; details['SMC'] = f"تحول هيكل هابط +{weights['smc']}"
    elif last_smc.get('in_discount', False):
        scores['BUY'] += weights['smc']//2; details['SMC'] = f"منطقة خصم +{weights['smc']//2}"
    elif last_smc.get('in_premium', False):
        scores['SELL'] += weights['smc']//2; details['SMC'] = f"منطقة قمة +{weights['smc']//2}"
    else:
        details['SMC'] = "لا توجد إشارة SMC"

    # ===== النماذج الفنية =====
    if patterns:
        for p in patterns:
            if p['direction'] == 'BULLISH':
                scores['BUY'] += weights['patterns']
                details['Pattern'] = f"{p['pattern']} (صاعد) +{weights['patterns']}"
            else:
                scores['SELL'] += weights['patterns']
                details['Pattern'] = f"{p['pattern']} (هابط) +{weights['patterns']}"
    else:
        details['Pattern'] = "لا توجد نماذج"

    # حساب النتيجة النهائية
    net_score = scores['BUY'] - scores['SELL']
    total_weight = sum(weights.values())
    if net_score >= 5:
        signal = "BUY"
        confidence = min(100, 60 + (net_score / total_weight) * 100)
    elif net_score <= -5:
        signal = "SELL"
        confidence = min(100, 60 + (abs(net_score) / total_weight) * 100)
    else:
        signal = "WAIT"
        confidence = 50 + (net_score / total_weight) * 50

    confidence = max(0, min(100, confidence))
    return signal, confidence, net_score, details, patterns

# ==========================================
# شرح القرار (معدل ليشمل SMC والنماذج)
# ==========================================
def explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns):
    explanation = ""
    if signal == "BUY":
        explanation = "🔹 **قرار الشراء** بناءً على:\n"
        for k, v in details.items():
            if "+" in v or any(word in v for word in ["شراء", "صاعد", "فوق", "قرب الحد السفلي", "مفرط البيع", "قوي", "كتلة", "FVG", "اجتياح", "تحول", "خصم"]):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≥5 للشراء)\n📈 **الثقة**: {confidence:.0f}%"
    elif signal == "SELL":
        explanation = "🔻 **قرار البيع** بناءً على:\n"
        for k, v in details.items():
            if "-" in v or any(word in v for word in ["بيع", "هابط", "تحت", "قرب الحد الأعلى", "مفرط الشراء", "قمة", "كتلة بيع", "تحول هابط"]):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≤-5 للبيع)\n📉 **الثقة**: {confidence:.0f}%"
    else:
        explanation = "⏳ **قرار الانتظار** بسبب:\n"
        explanation += f"- النتيجة الصافية {net_score} بين -5 و +5 (لا يوجد إجماع).\n- تفاصيل النقاط:\n"
        for k, v in details.items():
            explanation += f"  - {k}: {v}\n"
        explanation += "💡 **نصيحة**: انتظر حتى تتجاوز النتيجة ±5 أو تتحسن الثقة فوق 60%."
    # إضافة MTF
    explanation += f"\n\n🕒 **تحليل الأطر الزمنية**: {mtf_signal} (عدد الأطر: {mtf_count})"
    # عرض النماذج المكتشفة
    if patterns:
        explanation += "\n\n📐 **النماذج المكتشفة:**\n"
        for p in patterns:
            explanation += f"- {p['pattern']} ({p['direction']}) - قوة: {p['score']}/5\n"
    return explanation

# ==========================================
# تحليل متعدد الأطر الزمنية
# ==========================================
def get_mtf_signal(symbol, current_price):
    timeframes = ['15m', '1h', '4h']
    signals = []
    for tf in timeframes:
        df = get_historical_data(symbol, period="5d", interval=tf)
        if df is not None and len(df) > 50:
            rsi = calc_rsi(df['close']).iloc[-1]
            if rsi < 30:
                signals.append(('BUY', tf))
            elif rsi > 70:
                signals.append(('SELL', tf))
            else:
                signals.append(('NEUTRAL', tf))
    buy_count = sum(1 for s in signals if s[0] == 'BUY')
    sell_count = sum(1 for s in signals if s[0] == 'SELL')
    if buy_count > sell_count:
        return "BUY", buy_count - sell_count
    elif sell_count > buy_count:
        return "SELL", sell_count - buy_count
    else:
        return "NEUTRAL", 0

# ==========================================
# إدارة الصفقات (نفس السابق)
# ==========================================
class AdvancedTradeManager:
    def __init__(self):
        self.trades_file = "advanced_trades.json"
        self.load_trades()
    def load_trades(self):
        try:
            with open(self.trades_file, "r", encoding='utf-8') as f:
                data = json.load(f)
                self.open_trades = data.get("open_trades", [])
                self.closed_trades = data.get("closed_trades", [])
        except:
            self.open_trades = []
            self.closed_trades = []
    def save_trades(self):
        with open(self.trades_file, "w", encoding='utf-8') as f:
            json.dump({"open_trades": self.open_trades, "closed_trades": self.closed_trades}, f, indent=2, ensure_ascii=False)
    def add_trade(self, trade_data):
        trade_id = f"T{len(self.open_trades)+len(self.closed_trades)+1:03d}"
        trade = {
            "id": trade_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "direction": trade_data["direction"],
            "entry": trade_data["entry"],
            "lots": trade_data["lots"],
            "stop_loss": trade_data["stop_loss"],
            "take_profit": trade_data["take_profit"],
            "trailing_enabled": trade_data.get("trailing_enabled", False),
            "trailing_distance": trade_data.get("trailing_distance", 0),
            "highest_price": trade_data["entry"],
            "lowest_price": trade_data["entry"],
            "status": "open",
            "notes": trade_data.get("notes", "")
        }
        self.open_trades.append(trade)
        self.save_trades()
        return trade_id
    def update_trailing_stop(self, trade_id, current_price):
        for trade in self.open_trades:
            if trade["id"] == trade_id and trade["status"] == "open" and trade["trailing_enabled"]:
                if trade["direction"] == "BUY":
                    if current_price > trade["highest_price"]:
                        trade["highest_price"] = current_price
                    new_stop = trade["highest_price"] - trade["trailing_distance"]
                    if new_stop > trade["stop_loss"]:
                        trade["stop_loss"] = new_stop
                        self.save_trades()
                        return True
                else:  # SELL
                    if current_price < trade["lowest_price"]:
                        trade["lowest_price"] = current_price
                    new_stop = trade["lowest_price"] + trade["trailing_distance"]
                    if new_stop < trade["stop_loss"]:
                        trade["stop_loss"] = new_stop
                        self.save_trades()
                        return True
        return False
    def close_trade(self, trade_id, exit_price):
        for i, trade in enumerate(self.open_trades):
            if trade["id"] == trade_id:
                trade["exit"] = exit_price
                trade["status"] = "closed"
                if trade["direction"] == "BUY":
                    pips = (exit_price - trade["entry"]) * 100
                else:
                    pips = (trade["entry"] - exit_price) * 100
                profit = pips * trade["lots"] * 0.1
                trade["profit"] = round(profit, 2)
                trade["result"] = "win" if profit > 0 else "loss"
                trade["close_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_trades.append(trade)
                self.open_trades.pop(i)
                self.save_trades()
                return profit
        return None

# ==========================================
# الواجهة الرئيسية
# ==========================================
st.markdown("### 🔍 اختر الزوج للتحليل المتقدم")
selected_pair_name = st.selectbox("اختر الزوج للتحليل المتقدم", list(PAIRS.keys()), index=0)
selected_symbol = PAIRS[selected_pair_name]

# عرض البطاقات السريعة
forex_data = get_all_forex()
if forex_data:
    cols = st.columns(5)
    for i, (name, data) in enumerate(forex_data.items()):
        if data['price'] > 0:
            color = "#00ff88" if data['change'] >= 0 else "#ff4444"
            if 'USD' in name:
                price_str = f"{data['price']:.4f}"
            else:
                price_str = f"{data['price']:.2f}"
            cols[i].markdown(f"""
            <div class="currency-card">
                <div class="currency-symbol">{name}</div>
                <div class="currency-price">{price_str}</div>
                <div class="currency-change" style="color:{color};">{data['change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# جلب البيانات
current_price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="1mo", interval="1h")
if df is None:
    st.error("تعذر تحميل البيانات")
    st.stop()
if current_price is None:
    current_price = df['close'].iloc[-1]
    change = 0

# حساب المؤشرات
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'])
df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df)
df['vwap'] = calc_vwap(df)
tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(df)
df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b; df['chikou'] = chikou

# توليد الإشارة المتكاملة (مع SMC والنماذج)
signal, confidence, net_score, details, patterns = generate_advanced_signal(df, current_price, selected_symbol)
mtf_signal, mtf_count = get_mtf_signal(selected_symbol, current_price)

# عرض السعر
price_format = "${:,.2f}" if "BTC" in selected_pair_name or "Gold" in selected_pair_name else "${:.4f}"
st.markdown(f"""
<div class="price-card">
    <div style="font-size:1rem; color:#888;">{selected_pair_name} (Live)</div>
    <div class="price-value">{price_format.format(current_price)}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">
        {change:+.2f}%
    </div>
</div>
""", unsafe_allow_html=True)

# مؤشرات السوق
st.markdown("### 📊 مؤشرات السوق")
cols = st.columns(4)
last = df.iloc[-1]
cols[0].metric("RSI", f"{last['rsi']:.1f}")
cols[1].metric("ATR", f"${last['atr']:.2f}")
cols[2].metric("ADX", f"{last['adx']:.1f}")
cols[3].metric("VWAP", f"${last['vwap']:.2f}")

# عرض النماذج المكتشفة
if patterns:
    st.markdown("#### 📐 النماذج المكتشفة")
    pattern_html = " ".join([f'<span class="pattern-badge">{p["pattern"]} ({p["direction"]})</span>' for p in patterns])
    st.markdown(pattern_html, unsafe_allow_html=True)

# الإشارة
st.markdown("---")
st.markdown("### 🧠 إشارة التداول المتكاملة")
signal_color = "#ffaa00" if signal == "WAIT" else ("#00ff88" if signal == "BUY" else "#ff4444")
st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color: {signal_color};">{signal}</div>
    <div class="signal-confidence">الثقة: {confidence:.0f}% | النتيجة: {net_score}</div>
    <div style="font-size:0.9rem; color:#aaa; margin-top:10px;">
        MTF إجماع: {mtf_signal} (عدد الأطر: {mtf_count})
    </div>
</div>
""", unsafe_allow_html=True)

# شرح القرار
with st.expander("📝 شرح القرار", expanded=True):
    explanation = explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns)
    st.markdown(f'<div class="explanation-box">{explanation}</div>', unsafe_allow_html=True)

# ==========================================
# الصفقة المقترحة
# ==========================================
if signal in ["BUY", "SELL"] and confidence >= 60:
    st.markdown("---")
    st.markdown("### 💼 الصفقة المقترحة")
    recent_high = df['high'].iloc[-20:].max()
    recent_low = df['low'].iloc[-20:].min()
    if signal == "BUY":
        entry = current_price
        stop_loss = recent_low - (recent_high - recent_low) * 0.1
        take_profit = recent_high + (recent_high - recent_low) * 0.5
        direction_text = "شراء (BUY)"
    else:
        entry = current_price
        stop_loss = recent_high + (recent_high - recent_low) * 0.1
        take_profit = recent_low - (recent_high - recent_low) * 0.5
        direction_text = "بيع (SELL)"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>الاتجاه:</b> {direction_text}<br>
        <b>سعر الدخول:</b> {price_format.format(entry)}<br>
        <b>وقف الخسارة الثابت:</b> {price_format.format(stop_loss)}<br>
        <b>جني الربح:</b> {price_format.format(take_profit)}
    </div>
    """, unsafe_allow_html=True)

    with st.form("suggested_trade_form"):
        st.write("إضافة هذه الصفقة مع تفعيل الوقف المتحرك؟")
        col1, col2 = st.columns(2)
        enable_trailing = col1.checkbox("تفعيل الوقف المتحرك", value=True)
        trail_distance = col2.number_input("مسافة التحرك (نقاط)", min_value=5, value=20, step=5)
        lots = st.number_input("عدد اللوتات", min_value=0.01, value=0.1, step=0.01)
        submitted = st.form_submit_button("إضافة الصفقة")
        if submitted:
            trade_manager = AdvancedTradeManager()
            trade_data = {
                "direction": signal,
                "entry": entry,
                "lots": lots,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "trailing_enabled": enable_trailing,
                "trailing_distance": trail_distance / 100,
                "notes": f"مقترحة من البوت (الثقة {confidence:.0f}%)"
            }
            trade_id = trade_manager.add_trade(trade_data)
            st.success(f"✅ تم إضافة الصفقة {trade_id} بنجاح!")
            st.experimental_rerun()

# ==========================================
# إدارة الصفقات
# ==========================================
st.markdown("---")
st.markdown("### 💼 إدارة الصفقات")
trade_manager = AdvancedTradeManager()

for trade in trade_manager.open_trades:
    if trade["status"] == "open" and trade["trailing_enabled"]:
        trade_manager.update_trailing_stop(trade["id"], current_price)

if trade_manager.open_trades:
    st.write("**الصفقات المفتوحة:**")
    for trade in trade_manager.open_trades:
        st.markdown(f"""
        <div class="trade-row">
            <b>{trade['id']}</b> | {trade['direction']} | الدخول: {trade['entry']} | اللوت: {trade['lots']} | 
            الوقف الحالي: {trade['stop_loss']} | الهدف: {trade['take_profit']}
            {" | 🔄 وقف متحرك مفعّل" if trade['trailing_enabled'] else ""}
        </div>
        """, unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button(f"تحديث الوقف المتحرك {trade['id']}", key=f"update_{trade['id']}"):
            if trade_manager.update_trailing_stop(trade['id'], current_price):
                st.success("تم تحديث الوقف المتحرك!")
                st.experimental_rerun()
            else:
                st.info("لم يتغير الوقف (السعر لم يتحرك بما يكفي)")
        if col2.button(f"إغلاق {trade['id']}", key=f"close_{trade['id']}"):
            profit = trade_manager.close_trade(trade['id'], current_price)
            st.success(f"تم الإغلاق، الربح: ${profit:.2f}" if profit else "تم الإغلاق")
            st.experimental_rerun()
else:
    st.write("لا توجد صفقات مفتوحة")

if trade_manager.closed_trades:
    profits = [t.get('profit', 0) for t in trade_manager.closed_trades if 'profit' in t]
    if profits:
        win_rate = sum(1 for p in profits if p > 0) / len(profits) * 100
        total_profit = sum(profits)
        avg_profit = total_profit / len(profits)
        st.metric("نسبة الربح", f"{win_rate:.1f}%")
        st.metric("إجمالي الربح", f"${total_profit:.2f}")
        st.metric("متوسط الربح", f"${avg_profit:.2f}")

# ==========================================
# ركن الأخبار والتقويم
# ==========================================
st.markdown("---")
st.markdown("### 📰 الأخبار الاقتصادية والتقويم")

news = get_economic_news()
if news:
    st.write("**آخر الأخبار:**")
    for item in news:
        st.markdown(f"""
        <div class="news-card">
            <div class="news-title"><a href="{item['url']}" target="_blank">{item['title']}</a></div>
            <div class="news-date">{item['source']} - {item['publishedAt'][:10]}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("لا توجد أخبار حالياً (يرجى تفعيل مفتاح NewsAPI في الكود)")

st.write("**📅 التقويم الاقتصادي:**")
st.markdown("""
- [Investing.com Economic Calendar](https://www.investing.com/economic-calendar/)
- [ForexFactory Economic Calendar](https://www.forexfactory.com/calendar)
""")

# ==========================================
# الرسم البياني
# ==========================================
st.markdown("---")
st.markdown("### 📈 Price Chart with Indicators + SMC Levels")

# نحتاج df_smc للرسم لإظهار مناطق السيولة
df_smc = analyze_smc_ict(df)

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    row_heights=[0.6, 0.2, 0.2])
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(color='red', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='blue', width=0.8)), row=1, col=1)

# إضافة نقاط SMC على الشارت (بسيطة)
if df_smc['order_block_bullish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1], text="OB+", showarrow=True, arrowhead=1, row=1, col=1)
if df_smc['order_block_bearish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1], text="OB-", showarrow=True, arrowhead=1, row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
fig.add_bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color='gray', opacity=0.3, row=3, col=1)

fig.update_layout(height=800, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# تحليل الارتباط للذهب
# ==========================================
if selected_symbol == "GC=F":
    st.markdown("---")
    st.markdown("### 🔗 تحليل الارتباط: الذهب vs الدولار")
    df_dxy = get_historical_data("DX-Y.NYB", "1mo", "1h")
    if df_dxy is not None and not df_dxy.empty:
        df_dxy_aligned = df_dxy.reindex(df.index, method='nearest')
        df_dxy_aligned = df_dxy_aligned.ffill()
        fig_corr = make_subplots(specs=[[{"secondary_y": True}]])
        fig_corr.add_trace(go.Scatter(x=df.index, y=df['close'], name='XAU/USD', line=dict(color='gold')), secondary_y=False)
        fig_corr.add_trace(go.Scatter(x=df_dxy_aligned.index, y=df_dxy_aligned['close'], name='DXY', line=dict(color='cyan')), secondary_y=True)
        fig_corr.update_layout(height=400, template='plotly_dark', title="Gold vs DXY")
        fig_corr.update_yaxes(title_text="Gold", secondary_y=False)
        fig_corr.update_yaxes(title_text="DXY", secondary_y=True)
        st.plotly_chart(fig_corr, use_container_width=True)
        if len(df) > 10:
            corr = df['close'].corr(df_dxy_aligned['close'])
            st.metric("معامل الارتباط", f"{corr:.3f}")
    else:
        st.info("تعذر جلب بيانات مؤشر الدولار")

# ==========================================
# تذييل
# ==========================================
st.markdown("""
<div class="footer">
    GoldAPI.io | Indicators + SMC/ICT + Patterns + MTF<br>
    نسخة متكاملة مع تحليل السوق المتقدم
</div>
""", unsafe_allow_html=True)
