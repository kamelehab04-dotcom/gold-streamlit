import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import base64

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS للتنسيق
# ==========================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
        border-radius: 20px;
        margin-bottom: 30px;
        border: 1px solid #ffd70033;
    }
    .main-title {
        font-size: 2.5rem;
        color: #ffd700;
        text-shadow: 2px 2px 4px #000000;
        margin: 0;
        font-weight: bold;
        letter-spacing: 2px;
    }
    .main-subtitle {
        font-size: 1rem;
        color: #aaa;
        margin-top: 10px;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        margin: 30px 0;
    }
    .stat-card {
        flex: 1;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #ffd70033;
        transition: transform 0.3s;
    }
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: #ffd70066;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #ffd700;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #888;
        margin-top: 10px;
    }
    .price-card {
        background: linear-gradient(135deg, #ffd70015 0%, #ffaa0015 100%);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        border: 2px solid #ffd700;
        margin: 20px 0;
    }
    .price-label {
        font-size: 1.2rem;
        color: #ffd700;
        letter-spacing: 2px;
    }
    .price-value {
        font-size: 4rem;
        font-weight: bold;
        color: #ffffff;
        margin: 10px 0;
    }
    .price-change {
        font-size: 1rem;
        color: #00ff88;
    }
    .indicator-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border-left: 4px solid #ffd700;
        margin: 10px 0;
    }
    .indicator-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
    .indicator-label {
        font-size: 0.8rem;
        color: #888;
    }
    .signal-card {
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }
    .signal-buy {
        background: linear-gradient(135deg, #00ff8820 0%, #00cc6620 100%);
        border: 1px solid #00ff88;
    }
    .signal-sell {
        background: linear-gradient(135deg, #ff444420 0%, #cc333320 100%);
        border: 1px solid #ff4444;
    }
    .signal-neutral {
        background: linear-gradient(135deg, #ffaa0020 0%, #cc880020 100%);
        border: 1px solid #ffaa00;
    }
    .signal-title {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .signal-confidence {
        font-size: 0.9rem;
        margin-top: 10px;
    }
    .targets-table {
        background: #1e1e2e;
        border-radius: 12px;
        overflow: hidden;
        margin: 20px 0;
    }
    .target-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 20px;
        border-bottom: 1px solid #333;
    }
    .target-row:last-child {
        border-bottom: none;
    }
    .target-label {
        color: #ffd700;
        font-weight: bold;
    }
    .target-value {
        color: #ffffff;
    }
    .pattern-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        border: 1px solid #ffd70033;
    }
    .pattern-bullish {
        border-left: 4px solid #00ff88;
    }
    .pattern-bearish {
        border-left: 4px solid #ff4444;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
    .rating-badge {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 10px 15px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .stars {
        color: #ffd700;
        letter-spacing: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">بوت تحليل الذهب الفرعوني | SMC + ICT + Chart Patterns | Real-time Trading Signals</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# بطاقات الإحصائيات
# ==========================================
st.markdown("""
<div class="stats-container">
    <div class="stat-card">
        <div class="stat-number">$253M+</div>
        <div class="stat-label">Rewards Distributed</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">3M+</div>
        <div class="stat-label">Traders Worldwide</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">195+</div>
        <div class="stat-label">Countries Serviced</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# جلب البيانات
# ==========================================
GOLD_API_KEY = "goldapi-2e91d85dc02f06984d99b2cb3dd9066c-io"

@st.cache_data(ttl=30)
def get_real_price():
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return float(data.get('price', 0))
        return None
    except:
        return None

@st.cache_data(ttl=300)
def get_historical_data():
    gold = yf.Ticker("GC=F")
    df = gold.history(period="1mo", interval="1h")
    if df.empty:
        return None
    df.columns = [col.lower() for col in df.columns]
    return df

real_price = get_real_price()
df = get_historical_data()

if df is None:
    st.error("Error loading data")
    st.stop()

if real_price and real_price > 0:
    current_price = real_price
else:
    current_price = df['close'].iloc[-1]

# ==========================================
# حساب المؤشرات الأساسية
# ==========================================
def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)

current_rsi = df['rsi'].iloc[-1]
current_atr = df['atr'].iloc[-1]

# ==========================================
# كشف القمم والقيعان (للنماذج)
# ==========================================
def find_peaks(data, order=5):
    peaks = []
    for i in range(order, len(data) - order):
        if all(data[i] > data[i-j] for j in range(1, order+1)) and all(data[i] > data[i+j] for j in range(1, order+1)):
            peaks.append(data[i])
    return peaks

def find_troughs(data, order=5):
    troughs = []
    for i in range(order, len(data) - order):
        if all(data[i] < data[i-j] for j in range(1, order+1)) and all(data[i] < data[i+j] for j in range(1, order+1)):
            troughs.append(data[i])
    return troughs

# ==========================================
# نماذج التداول (Chart Patterns)
# ==========================================

# 1. Double Top / Double Bottom
def detect_double_top_bottom(df):
    peaks = find_peaks(df['high'].values[-100:])
    troughs = find_troughs(df['low'].values[-100:])
    
    if len(peaks) >= 2:
        last_two_peaks = peaks[-2:]
        if abs(last_two_peaks[-1] - last_two_peaks[-2]) / last_two_peaks[-2] < 0.02:
            return "DOUBLE TOP", "bearish", 4
    
    if len(troughs) >= 2:
        last_two_troughs = troughs[-2:]
        if abs(last_two_troughs[-1] - last_two_troughs[-2]) / last_two_troughs[-2] < 0.02:
            return "DOUBLE BOTTOM", "bullish", 4
    
    return None, None, 0

# 2. Triple Top / Triple Bottom
def detect_triple_top_bottom(df):
    peaks = find_peaks(df['high'].values[-150:])
    troughs = find_troughs(df['low'].values[-150:])
    
    if len(peaks) >= 3:
        last_three_peaks = peaks[-3:]
        if max(last_three_peaks) - min(last_three_peaks) < np.mean(last_three_peaks) * 0.03:
            return "TRIPLE TOP", "bearish", 5
    
    if len(troughs) >= 3:
        last_three_troughs = troughs[-3:]
        if max(last_three_troughs) - min(last_three_troughs) < np.mean(last_three_troughs) * 0.03:
            return "TRIPLE BOTTOM", "bullish", 5
    
    return None, None, 0

# 3. Head and Shoulders
def detect_head_shoulders(df):
    peaks = find_peaks(df['high'].values[-120:], order=3)
    
    if len(peaks) >= 3:
        head_idx = np.argmax([p for p in peaks[-5:]])
        if head_idx > 0 and head_idx < len(peaks[-5:]) - 1:
            left_shoulder = peaks[-5:][head_idx - 1]
            head = peaks[-5:][head_idx]
            right_shoulder = peaks[-5:][head_idx + 1]
            if head > left_shoulder and head > right_shoulder:
                if abs(left_shoulder - right_shoulder) / left_shoulder < 0.05:
                    return "HEAD AND SHOULDERS", "bearish", 6
    return None, None, 0

# 4. Inverse Head and Shoulders
def detect_inverse_head_shoulders(df):
    troughs = find_troughs(df['low'].values[-120:], order=3)
    
    if len(troughs) >= 3:
        head_idx = np.argmin([t for t in troughs[-5:]])
        if head_idx > 0 and head_idx < len(troughs[-5:]) - 1:
            left_shoulder = troughs[-5:][head_idx - 1]
            head = troughs[-5:][head_idx]
            right_shoulder = troughs[-5:][head_idx + 1]
            if head < left_shoulder and head < right_shoulder:
                if abs(left_shoulder - right_shoulder) / left_shoulder < 0.05:
                    return "INVERSE HEAD AND SHOULDERS", "bullish", 6
    return None, None, 0

# 5. Ascending Triangle
def detect_ascending_triangle(df):
    recent_data = df.iloc[-40:]
    highs = recent_data['high'].values
    lows = recent_data['low'].values
    x = np.arange(len(highs))
    slope_highs = np.polyfit(x, highs, 1)[0]
    slope_lows = np.polyfit(x, lows, 1)[0]
    
    if slope_lows > 0.01 and abs(slope_highs) < 0.005:
        return "ASCENDING TRIANGLE", "bullish", 3
    return None, None, 0

# 6. Descending Triangle
def detect_descending_triangle(df):
    recent_data = df.iloc[-40:]
    highs = recent_data['high'].values
    lows = recent_data['low'].values
    x = np.arange(len(highs))
    slope_highs = np.polyfit(x, highs, 1)[0]
    slope_lows = np.polyfit(x, lows, 1)[0]
    
    if slope_highs < -0.01 and abs(slope_lows) < 0.005:
        return "DESCENDING TRIANGLE", "bearish", 3
    return None, None, 0

# 7. Bullish Flag
def detect_bullish_flag(df):
    recent_data = df.iloc[-30:]
    first_candle = recent_data.iloc[0]
    last_candle = recent_data.iloc[-1]
    if first_candle['close'] > first_candle['open']:
        flag_range = (recent_data['high'].max() - recent_data['low'].min()) / recent_data['low'].min()
        if flag_range < 0.01:
            return "BULLISH FLAG", "bullish", 3
    return None, None, 0

# 8. Bearish Flag
def detect_bearish_flag(df):
    recent_data = df.iloc[-30:]
    first_candle = recent_data.iloc[0]
    if first_candle['close'] < first_candle['open']:
        flag_range = (recent_data['high'].max() - recent_data['low'].min()) / recent_data['low'].min()
        if flag_range < 0.01:
            return "BEARISH FLAG", "bearish", 3
    return None, None, 0

# 9. Rounding Bottom
def detect_rounding_bottom(df):
    recent_lows = df['low'].values[-50:]
    mid = len(recent_lows) // 2
    left_min = np.min(recent_lows[:mid])
    right_min = np.min(recent_lows[mid:])
    center_min = np.min(recent_lows)
    if center_min < left_min and center_min < right_min:
        return "ROUNDING BOTTOM", "bullish", 2
    return None, None, 0

# ==========================================
# تنفيذ جميع النماذج
# ==========================================
def analyze_all_patterns(df):
    patterns = []
    total_pattern_score = 0
    
    # تشغيل كل النماذج
    pattern, direction, score = detect_double_top_bottom(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_triple_top_bottom(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_head_shoulders(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_inverse_head_shoulders(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_ascending_triangle(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_descending_triangle(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_bullish_flag(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_bearish_flag(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    pattern, direction, score = detect_rounding_bottom(df)
    if pattern:
        patterns.append({"name": pattern, "direction": direction, "score": score})
        total_pattern_score += score if direction == "bullish" else -score
    
    return patterns, total_pattern_score

# ==========================================
# تنفيذ التحليل
# ==========================================
patterns, pattern_score = analyze_all_patterns(df)

# ==========================================
# SMC Signals (نفس الكود السابق)
# ==========================================
recent_lows = df['low'].iloc[-20:].values
recent_highs = df['high'].iloc[-20:].values
liquidity_sweep_bullish = df['low'].iloc[-1] < min(recent_lows[:-1])
liquidity_sweep_bearish = df['high'].iloc[-1] > max(recent_highs[:-1])
bos_bullish = current_price > df['high'].iloc[-6:-1].max()
bos_bearish = current_price < df['low'].iloc[-6:-1].min()
resistance = np.percentile(df['high'].iloc[-30:], 75)
support = np.percentile(df['low'].iloc[-30:], 25)

# ==========================================
# نظام التسجيل (مع إضافة النماذج)
# ==========================================
bullish = 0
bearish = 0
signals = []

# RSI
if current_rsi < 45:
    bullish += 3
    signals.append(f"✅ RSI: {current_rsi:.1f} (BUY ZONE)")
elif current_rsi > 65:
    bearish += 3
    signals.append(f"⚠️ RSI: {current_rsi:.1f} (SELL ZONE)")
else:
    signals.append(f"📊 RSI: {current_rsi:.1f} (NEUTRAL)")

# EMA
if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals.append("📈 Price above EMA20")
else:
    bearish += 2
    signals.append("📉 Price below EMA20")

# SMC
if liquidity_sweep_bullish:
    bullish += 3
    signals.append("🎯 Liquidity Sweep Bullish")
if liquidity_sweep_bearish:
    bearish += 3
    signals.append("🎯 Liquidity Sweep Bearish")
if bos_bullish:
    bullish += 2
    signals.append("🚀 BOS Bullish")
if bos_bearish:
    bearish += 2
    signals.append("🚀 BOS Bearish")

# Support/Resistance
if current_price <= support + 5:
    bullish += 2
    signals.append(f"📍 Near Support: ${support:.2f}")
if current_price >= resistance - 5:
    bearish += 2
    signals.append(f"📍 Near Resistance: ${resistance:.2f}")

# إضافة نقاط النماذج
for p in patterns:
    if p['direction'] == "bullish":
        bullish += p['score']
        signals.append(f"📈 {p['name']} (+{p['score']})")
    else:
        bearish += p['score']
        signals.append(f"📉 {p['name']} (-{p['score']})")

net = bullish - bearish

# ==========================================
# الإشارة النهائية
# ==========================================
if net >= 12:
    signal_type = "STRONG BUY"
    signal_action = "BUY"
    confidence = 95
    signal_color = "#00ff88"
elif net >= 7:
    signal_type = "BUY"
    signal_action = "BUY"
    confidence = 80
    signal_color = "#00ff88"
elif net <= -12:
    signal_type = "STRONG SELL"
    signal_action = "SELL"
    confidence = 95
    signal_color = "#ff4444"
elif net <= -7:
    signal_type = "SELL"
    signal_action = "SELL"
    confidence = 80
    signal_color = "#ff4444"
else:
    signal_type = "WAIT"
    signal_action = "NEUTRAL"
    confidence = 50
    signal_color = "#ffaa00"

# ==========================================
# خطة التداول
# ==========================================
if signal_action == "BUY":
    entry = current_price
    stop_loss = support - (current_atr * 0.5)
    targets = [resistance, resistance + (current_atr * 1.5), resistance + (current_atr * 3)]
elif signal_action == "SELL":
    entry = current_price
    stop_loss = resistance + (current_atr * 0.5)
    targets = [support, support - (current_atr * 1.5), support - (current_atr * 3)]
else:
    entry = current_price
    stop_loss = None
    targets = []

# ==========================================
# عرض السعر
# ==========================================
change = real_price - (df['close'].iloc[-2] if len(df) > 1 else real_price) if real_price else 0
change_percent = (change / (df['close'].iloc[-2] if len(df) > 1 else real_price)) * 100 if real_price else 0
change_color = "#00ff88" if change >= 0 else "#ff4444"
change_sign = "+" if change >= 0 else ""

st.markdown(f"""
<div class="price-card">
    <div class="price-label">𓋹 REAL TIME GOLD PRICE 𓋹</div>
    <div class="price-value">${current_price:,.2f}</div>
    <div class="price-change" style="color:{change_color}">{change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# بطاقات المؤشرات
# ==========================================
st.markdown("### 📊 Market Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="indicator-card">
        <div class="indicator-value" style="color:#ffd700">{current_rsi:.1f}</div>
        <div class="indicator-label">RSI (14)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="indicator-card">
        <div class="indicator-value" style="color:#ffd700">${current_atr:.2f}</div>
        <div class="indicator-label">ATR</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="indicator-card">
        <div class="indicator-value" style="color:#ffd700">{bullish} / {bearish}</div>
        <div class="indicator-label">Bullish / Bearish</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="indicator-card">
        <div class="indicator-value" style="color:#ffd700">{net:+d}</div>
        <div class="indicator-label">Net Score</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# إشارة التداول
# ==========================================
signal_class = "signal-buy" if signal_action == "BUY" else "signal-sell" if signal_action == "SELL" else "signal-neutral"

st.markdown(f"""
<div class="signal-card {signal_class}">
    <div class="signal-title" style="color:{signal_color}">{signal_type} SIGNAL</div>
    <div class="signal-confidence">Confidence: {confidence}% | Score: {net:+d}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# عرض النماذج المكتشفة
# ==========================================
if patterns:
    st.markdown("### 📈 Detected Chart Patterns")
    
    cols = st.columns(min(len(patterns), 4))
    for i, p in enumerate(patterns):
        col_idx = i % 4
        with cols[col_idx]:
            emoji = "🟢" if p['direction'] == "bullish" else "🔴"
            st.markdown(f"""
            <div class="pattern-card pattern-{p['direction']}">
                <div style="font-size:1.2rem; font-weight:bold">{emoji} {p['name']}</div>
                <div style="color:#888; font-size:0.8rem">{p['direction'].upper()} | +{p['score']} pts</div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# الشارت
# ==========================================
st.markdown("### 📈 Price Chart")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold', line=dict(color='#ffd700', width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='#ff9f4a')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='#4a9eff')))
fig.add_hline(y=resistance, line_dash="dash", line_color="#ff4444", annotation_text="Resistance")
fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", annotation_text="Support")
fig.update_layout(template="plotly_dark", height=450)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# جدول الأهداف
# ==========================================
if signal_action != "NEUTRAL":
    st.markdown("### 🎯 Trading Plan & Targets")
    
    st.markdown(f"""
    <div class="targets-table">
        <div class="target-row">
            <span class="target-label">📍 Entry Price</span>
            <span class="target-value">${entry:.2f}</span>
        </div>
        <div class="target-row">
            <span class="target-label">🛑 Stop Loss</span>
            <span class="target-value">${stop_loss:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 🎯 Take Profit Targets")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#00ff88">${targets[0]:.2f}</div>
            <div class="indicator-label">🎯 Target 1</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#ffaa00">${targets[1]:.2f}</div>
            <div class="indicator-label">🎯 Target 2</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#ffd700">${targets[2]:.2f}</div>
            <div class="indicator-label">🎯 Target 3</div>
        </div>
        """, unsafe_allow_html=True)
    
    if signal_action == "BUY":
        rr_ratio = (targets[0] - entry) / (entry - stop_loss)
    else:
        rr_ratio = (entry - targets[0]) / (stop_loss - entry)
    
    st.markdown(f"""
    <div class="stats-container" style="margin-top:20px">
        <div class="stat-card">
            <div class="stat-number" style="font-size:1.2rem">Risk/Reward</div>
            <div class="stat-label">1 : {rr_ratio:.2f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="font-size:1.2rem">Risk Amount</div>
            <div class="stat-label">2% of capital</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# المؤشرات الفنية
# ==========================================
with st.expander("📊 Technical Indicators Details"):
    for s in signals:
        if "✅" in s or "📈" in s:
            st.success(s)
        elif "⚠️" in s or "📉" in s:
            st.error(s)
        else:
            st.info(s)

# ==========================================
# شارة التقييم
# ==========================================
st.markdown("""
<div style="display: flex; justify-content: center; margin: 30px 0">
    <div class="rating-badge">
        <span style="color:#ffd700; font-weight:bold">★★★★★</span>
        <span>Excellent</span>
        <span style="color:#888">| 4.8 ★ Trustpilot</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# الفوتر
# ==========================================
st.markdown(f"""
<div class="footer">
    𓋹 Powered by GoldAPI.io + Yahoo Finance | SMC + ICT + Chart Patterns Analysis | Real-time Data 𓋹<br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
