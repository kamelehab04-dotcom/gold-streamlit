import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np

# ==========================================
# إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="Gold Analysis Dashboard",
    page_icon="🥇",
    layout="wide"
)

st.title("🥇 Gold Price Analysis Dashboard")
st.markdown("---")

# ==========================================
# جلب البيانات
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    gold = yf.Ticker("GC=F")
    df = gold.history(period="3d", interval="1h")
    if df.empty:
        return None
    df.columns = [col.lower() for col in df.columns]
    return df

df = get_data()

if df is None:
    st.error("❌ Error fetching data")
    st.stop()

# ==========================================
# حساب المؤشرات (بدون مكتبات إضافية)
# ==========================================
def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

# حساب المؤشرات
df['ema20'] = calculate_ema(df['close'], 20)
df['ema50'] = calculate_ema(df['close'], 50)
df['rsi'] = calculate_rsi(df['close'])
df['atr'] = calculate_atr(df)

current_price = df['close'].iloc[-1]
current_rsi = df['rsi'].iloc[-1]
current_atr = df['atr'].iloc[-1]

# ==========================================
# إشارات SMC المبسطة
# ==========================================

# كشف القمم والقيعان
def find_peaks(data, order=3):
    peaks = []
    for i in range(order, len(data) - order):
        if all(data[i] > data[i-j] for j in range(1, order+1)) and all(data[i] > data[i+j] for j in range(1, order+1)):
            peaks.append(data[i])
    return peaks

def find_troughs(data, order=3):
    troughs = []
    for i in range(order, len(data) - order):
        if all(data[i] < data[i-j] for j in range(1, order+1)) and all(data[i] < data[i+j] for j in range(1, order+1)):
            troughs.append(data[i])
    return troughs

# كشف Liquidity Sweep (اصطياد السيولة)
recent_lows = df['low'].iloc[-20:].values
recent_highs = df['high'].iloc[-20:].values
current_low = df['low'].iloc[-1]
current_high = df['high'].iloc[-1]

liquidity_sweep_bullish = current_low < min(recent_lows[:-1])
liquidity_sweep_bearish = current_high > max(recent_highs[:-1])

# كشف Break of Structure (كسر الهيكل)
bos_bullish = current_price > df['high'].iloc[-6:-1].max()
bos_bearish = current_price < df['low'].iloc[-6:-1].min()

# ==========================================
# نظام التسجيل
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

# SMC Signals
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

net = bullish - bearish

# الإشارة النهائية
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

# ==========================================
# الأهداف ووقف الخسارة
# ==========================================
if signal_action == "BUY":
    entry = current_price
    stop_loss = current_price - (current_atr * 1.5)
    targets = [
        current_price + (current_atr * 1.5),
        current_price + (current_atr * 2.5),
        current_price + (current_atr * 4)
    ]
elif signal_action == "SELL":
    entry = current_price
    stop_loss = current_price + (current_atr * 1.5)
    targets = [
        current_price - (current_atr * 1.5),
        current_price - (current_atr * 2.5),
        current_price - (current_atr * 4)
    ]
else:
    entry = current_price
    stop_loss = None
    targets = []

# ==========================================
# عرض البطاقات
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 Gold Price", f"${current_price:.2f}")

with col2:
    st.metric("📈 RSI", f"{current_rsi:.1f}")

with col3:
    st.metric("🎯 Signal", signal_type, delta=f"Confidence {confidence}%")

with col4:
    st.metric("📊 ATR", f"${current_atr:.2f}")

st.markdown("---")

# ==========================================
# الشارت
# ==========================================
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Gold"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name="EMA 20", line=dict(color='orange')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name="EMA 50", line=dict(color='blue')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name="RSI", line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="Overbought")
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Oversold")

fig.update_layout(template="plotly_dark", height=600, title=f"Gold Price - ${current_price:.2f}")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# المؤشرات
# ==========================================
st.subheader("📊 Technical Indicators")
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
st.subheader("💰 Trading Plan")

if signal_action == "BUY":
    st.markdown(f"""
    ### 🟢 BUY SIGNAL
    - **Entry Price:** ${entry:.2f}
    - **Stop Loss:** ${stop_loss:.2f}
    - **Target 1:** ${targets[0]:.2f}
    - **Target 2:** ${targets[1]:.2f}
    - **Target 3:** ${targets[2]:.2f}
    """)
elif signal_action == "SELL":
    st.markdown(f"""
    ### 🔴 SELL SIGNAL
    - **Entry Price:** ${entry:.2f}
    - **Stop Loss:** ${stop_loss:.2f}
    - **Target 1:** ${targets[0]:.2f}
    - **Target 2:** ${targets[1]:.2f}
    - **Target 3:** ${targets[2]:.2f}
    """)
else:
    st.markdown("### 🟡 WAIT - No clear signal")

# ==========================================
# وقت التحديث
# ==========================================
st.markdown("---")
st.caption(f"🕐 Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
