import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS للتنسيق المتناسق
# ==========================================
st.markdown("""
<style>
    /* التنسيق العام */
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        color: #ffd700;
        margin-bottom: 0.5rem;
        font-weight: bold;
    }
    .sub-title {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
    }
    .price-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #ffd70033;
        margin-bottom: 20px;
    }
    .price-label {
        color: #ffd700;
        font-size: 1rem;
        letter-spacing: 2px;
    }
    .price-value {
        color: #ffffff;
        font-size: 3rem;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #ffd70033;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #ffd700;
    }
    .metric-label {
        color: #888;
        font-size: 0.8rem;
        margin-top: 5px;
    }
    .signal-buy {
        background-color: #00ff8822;
        border: 1px solid #00ff88;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .signal-sell {
        background-color: #ff444422;
        border: 1px solid #ff4444;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .signal-neutral {
        background-color: #ffaa0022;
        border: 1px solid #ffaa00;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    .signal-text {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .targets-box {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 15px;
        margin-top: 20px;
    }
    .target-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #333;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
    hr {
        margin: 20px 0;
        border-color: #ffd70033;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown('<div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">بوت تحليل الذهب الفرعوني | SMC + ICT Analysis | Real-time Trading Signals</div>', unsafe_allow_html=True)

# محاولة عرض الصورة (لو موجودة)
try:
    st.image("file_0000000069e87246902490b6800f8681.png", width=150)
except:
    pass

st.markdown("---")

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
# SMC Signals
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
# التسجيل
# ==========================================
bullish = 0
bearish = 0
signals = []

if current_rsi < 45:
    bullish += 3
    signals.append(f"✅ RSI: {current_rsi:.1f} (BUY)")
elif current_rsi > 65:
    bearish += 3
    signals.append(f"⚠️ RSI: {current_rsi:.1f} (SELL)")
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
    signal_type = "🔴🔴 STRONG BUY 🔴🔴"
    signal_action = "BUY"
    confidence = 90
    signal_class = "signal-buy"
    signal_color = "#00ff88"
elif net >= 4:
    signal_type = "🟢 BUY 🟢"
    signal_action = "BUY"
    confidence = 75
    signal_class = "signal-buy"
    signal_color = "#00ff88"
elif net <= -8:
    signal_type = "🔴🔴 STRONG SELL 🔴🔴"
    signal_action = "SELL"
    confidence = 90
    signal_class = "signal-sell"
    signal_color = "#ff4444"
elif net <= -4:
    signal_type = "🔴 SELL 🔴"
    signal_action = "SELL"
    confidence = 75
    signal_class = "signal-sell"
    signal_color = "#ff4444"
else:
    signal_type = "🟡 WAIT 🟡"
    signal_action = "NEUTRAL"
    confidence = 50
    signal_class = "signal-neutral"
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
st.markdown(f"""
<div class="price-box">
    <div class="price-label">𓋹 REAL TIME GOLD PRICE 𓋹</div>
    <div class="price-value">${current_price:,.2f}</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# صف البطاقات
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{current_rsi:.1f}</div>
        <div class="metric-label">RSI (14)</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">${current_atr:.2f}</div>
        <div class="metric-label">ATR</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{bullish} / {bearish}</div>
        <div class="metric-label">Bullish / Bearish</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{net:+d}</div>
        <div class="metric-label">Net Score</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# الإشارة
# ==========================================
st.markdown(f"""
<div class="{signal_class}">
    <div class="signal-text" style="color:{signal_color}">{signal_type}</div>
    <div style="margin-top:5px">Confidence: {confidence}%</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# الشارت
# ==========================================
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold', line=dict(color='#ffd700', width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='#ff9f4a')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='#4a9eff')))
fig.add_hline(y=resistance, line_dash="dash", line_color="#ff4444", annotation_text="Resistance")
fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", annotation_text="Support")
fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# المؤشرات
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
# خطة التداول
# ==========================================
if signal_action != "NEUTRAL":
    st.subheader("🎯 Trading Plan")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**📍 Entry:** ${entry:.2f}")
        st.markdown(f"**🛑 Stop Loss:** ${stop_loss:.2f}")
    with col2:
        st.markdown(f"**📊 Risk/Reward:** 1 : {((targets[0]-entry)/(entry-stop_loss)):.2f}" if signal_action=="BUY" else f"**📊 Risk/Reward:** 1 : {((entry-targets[0])/(stop_loss-entry)):.2f}")
    
    st.markdown("**🎯 Take Profit Targets:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Target 1**\n${targets[0]:.2f}")
    with col2:
        st.markdown(f"**Target 2**\n${targets[1]:.2f}")
    with col3:
        st.markdown(f"**Target 3**\n${targets[2]:.2f}")

# ==========================================
# الفوتر
# ==========================================
st.markdown(f"""
<div class="footer">
    𓋹 Powered by GoldAPI.io + Yahoo Finance | SMC + ICT Analysis | Real-time Data 𓋹<br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
