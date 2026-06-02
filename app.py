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
# CSS للتنسيق - نفس نظام الصورة
# ==========================================
st.markdown("""
<style>
    /* التنسيق العام */
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
    
    /* بطاقات الإحصائيات */
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
    
    /* بطاقة السعر الرئيسية */
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
    
    /* بطاقات المؤشرات */
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
    
    /* إشارات التداول */
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
    
    /* جدول الأهداف */
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
    
    /* الفوتر */
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
    
    /* شارة التقييم */
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
# الهيدر الرئيسي (نفس نظام الصورة)
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">بوت تحليل الذهب الفرعوني | SMC + ICT Analysis | Real-time Trading Signals</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# بطاقات الإحصائيات (زي الصورة)
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
# جلب سعر الذهب الفوري
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
    df = gold.history(period="3d", interval="1h")
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
# حساب المؤشرات
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
# إشارات SMC
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
# نظام التسجيل
# ==========================================
bullish = 0
bearish = 0
signals = []

if current_rsi < 45:
    bullish += 3
    signals.append(f"✅ RSI: {current_rsi:.1f} (BUY ZONE)")
elif current_rsi > 65:
    bearish += 3
    signals.append(f"⚠️ RSI: {current_rsi:.1f} (SELL ZONE)")
else:
    signals.append(f"📊 RSI: {current_rsi:.1f} (NEUTRAL)")

if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals.append("📈 Price above EMA20")
else:
    bearish += 2
    signals.append("📉 Price below EMA20")

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

if current_price <= support + 5:
    bullish += 2
    signals.append(f"📍 Near Support: ${support:.2f}")
if current_price >= resistance - 5:
    bearish += 2
    signals.append(f"📍 Near Resistance: ${resistance:.2f}")

net = bullish - bearish

if net >= 8:
    signal_type = "STRONG BUY"
    signal_action = "BUY"
    confidence = 90
    signal_color = "#00ff88"
elif net >= 4:
    signal_type = "BUY"
    signal_action = "BUY"
    confidence = 75
    signal_color = "#00ff88"
elif net <= -8:
    signal_type = "STRONG SELL"
    signal_action = "SELL"
    confidence = 90
    signal_color = "#ff4444"
elif net <= -4:
    signal_type = "SELL"
    signal_action = "SELL"
    confidence = 75
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
# عرض السعر الرئيسي (نفس نظام الصورة)
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
# إشارة التداول (نفس نظام الصورة)
# ==========================================
signal_class = "signal-buy" if signal_action == "BUY" else "signal-sell" if signal_action == "SELL" else "signal-neutral"

st.markdown(f"""
<div class="signal-card {signal_class}">
    <div class="signal-title" style="color:{signal_color}">{signal_type} SIGNAL</div>
    <div class="signal-confidence">Confidence: {confidence}% | Score: {net:+d}</div>
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
fig.add_hline(y=current_price, line_dash="dot", line_color="white", annotation_text=f"Current: ${current_price:.2f}")
fig.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# جدول الأهداف (نفس نظام الصورة)
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
    targets_data = [
        {"level": "Target 1", "price": targets[0], "reward": f"{(targets[0]-entry):+.2f}" if signal_action=="BUY" else f"{(entry-targets[0]):+.2f}"},
        {"level": "Target 2", "price": targets[1], "reward": f"{(targets[1]-entry):+.2f}" if signal_action=="BUY" else f"{(entry-targets[1]):+.2f}"},
        {"level": "Target 3", "price": targets[2], "reward": f"{(targets[2]-entry):+.2f}" if signal_action=="BUY" else f"{(entry-targets[2]):+.2f}"},
    ]
    
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
    
    # نسبة المخاطرة/العائد
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
# شارة التقييم (نفس نظام الصورة)
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
    𓋹 Powered by GoldAPI.io + Yahoo Finance | SMC + ICT Analysis | Real-time Data 𓋹<br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
