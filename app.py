import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# محاولة عرض الصورة بثلاث طرق مختلفة
# ==========================================

st.markdown("### 𓋹 PHARAOH GOLD DASHBOARD 𓋹")
st.markdown("---")

# الطريقة الأولى: محاولة تحميل الصورة من الرابط المباشر
image_url = "https://raw.githubusercontent.com/kamelehab04-dotcom/gold-streamlit/refs/heads/main/file_0000000069e87246902490b6800f8681.png"

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        # محاولة عرض الصورة من الرابط
        st.image(image_url, width=200)
        st.success("✅ الصورة ظهرت من الرابط!")
    except:
        st.warning("⚠️ الصورة غير متاحة من الرابط")
        
        # الطريقة الثانية: لو الصورة موجودة في نفس المجلد
        try:
            st.image("file_0000000069e87246902490b6800f8681.png", width=200)
            st.success("✅ الصورة ظهرت من الملف المحلي!")
        except:
            st.warning("⚠️ الصورة غير موجودة محلياً")
            
            # الطريقة الثالثة: عرض النص فقط
            st.markdown("""
            <div style="text-align:center">
                <h1 style="color:#ffd700">𓋹 PHARAOH GOLD 𓋹</h1>
                <p style="color:#888">Gold Analysis Dashboard</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# باقي الكود (جلب البيانات والتحليل)
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

recent_lows = df['low'].iloc[-20:].values
recent_highs = df['high'].iloc[-20:].values
liquidity_sweep_bullish = df['low'].iloc[-1] < min(recent_lows[:-1])
liquidity_sweep_bearish = df['high'].iloc[-1] > max(recent_highs[:-1])
bos_bullish = current_price > df['high'].iloc[-6:-1].max()
bos_bearish = current_price < df['low'].iloc[-6:-1].min()
resistance = np.percentile(df['high'].iloc[-30:], 75)
support = np.percentile(df['low'].iloc[-30:], 25)

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
elif net >= 4:
    signal_type = "🟢 BUY 🟢"
    signal_action = "BUY"
    confidence = 75
elif net <= -8:
    signal_type = "🔴🔴 STRONG SELL 🔴🔴"
    signal_action = "SELL"
    confidence = 90
elif net <= -4:
    signal_type = "🔴 SELL 🔴"
    signal_action = "SELL"
    confidence = 75
else:
    signal_type = "🟡 WAIT 🟡"
    signal_action = "NEUTRAL"
    confidence = 50

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
# عرض البيانات
# ==========================================
st.markdown(f"""
<div style="background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding:25px; border-radius:15px; margin-bottom:20px; text-align:center">
    <h2 style="color:#ffd700; margin:0">𓋹 REAL TIME GOLD PRICE 𓋹</h2>
    <h1 style="color:#ffffff; font-size:3rem; margin:10px 0">${current_price:.2f}</h1>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("📈 RSI", f"{current_rsi:.1f}")
col2.metric("🎯 Signal", signal_type, delta=f"{confidence}%")
col3.metric("📊 Net Score", f"{net:+d}")
col4.metric("📐 ATR", f"${current_atr:.2f}")

st.markdown("---")

# الشارت
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold', line=dict(color='#ffd700', width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='#ff9f4a')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='#4a9eff')))
fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text="Resistance")
fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="Support")
fig.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# المؤشرات
with st.expander("📊 Technical Indicators"):
    for s in signals:
        if "✅" in s or "📈" in s:
            st.success(s)
        elif "⚠️" in s or "📉" in s:
            st.error(s)
        else:
            st.info(s)

# خطة التداول
if signal_action != "NEUTRAL":
    st.markdown("---")
    st.subheader("🎯 Trading Plan")
    st.markdown(f"**Entry:** ${entry:.2f}")
    st.markdown(f"**Stop Loss:** ${stop_loss:.2f}")
    st.markdown(f"**Target 1:** ${targets[0]:.2f}")
    st.markdown(f"**Target 2:** ${targets[1]:.2f}")
    st.markdown(f"**Target 3:** ${targets[2]:.2f}")

st.markdown("---")
st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
