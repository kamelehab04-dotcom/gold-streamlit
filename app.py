import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import numpy as np

st.set_page_config(page_title="Gold Analysis", layout="wide")

st.title("🥇 PHARAOH GOLD DASHBOARD")
st.markdown("---")

# جلب البيانات
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
    st.error("Error loading data")
    st.stop()

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

current_price = df['close'].iloc[-1]
current_rsi = df['rsi'].iloc[-1]
current_atr = df['atr'].iloc[-1]

# ==========================================
# إشارات SMC
# ==========================================

# Liquidity Sweep (اصطياد السيولة)
recent_lows = df['low'].iloc[-20:].values
recent_highs = df['high'].iloc[-20:].values
liquidity_sweep_bullish = df['low'].iloc[-1] < min(recent_lows[:-1])
liquidity_sweep_bearish = df['high'].iloc[-1] > max(recent_highs[:-1])

# Break of Structure (كسر الهيكل)
bos_bullish = current_price > df['high'].iloc[-6:-1].max()
bos_bearish = current_price < df['low'].iloc[-6:-1].min()

# الدعم والمقاومة
resistance = np.percentile(df['high'].iloc[-30:], 75)
support = np.percentile(df['low'].iloc[-30:], 25)

# ==========================================
# نظام التسجيل
# ==========================================
bullish = 0
bearish = 0
signals = []

# RSI
if current_rsi < 45:
    bullish += 3
    signals.append(f"✅ RSI: {current_rsi:.1f} (BUY)")
elif current_rsi > 65:
    bearish += 3
    signals.append(f"⚠️ RSI: {current_rsi:.1f} (SELL)")
else:
    signals.append(f"📊 RSI: {current_rsi:.1f} (NEUTRAL)")

# EMA
if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals.append("📈 Price above EMA20")
else:
    bearish += 2
    signals.append("📉 Price below EMA20")

# Liquidity Sweep
if liquidity_sweep_bullish:
    bullish += 3
    signals.append("🎯 Liquidity Sweep Bullish")
if liquidity_sweep_bearish:
    bearish += 3
    signals.append("🎯 Liquidity Sweep Bearish")

# Break of Structure
if bos_bullish:
    bullish += 2
    signals.append("🚀 BOS Bullish")
if bos_bearish:
    bearish += 2
    signals.append("🚀 BOS Bearish")

# السعر بجانب الدعم/المقاومة
if current_price <= support + 5:
    bullish += 2
    signals.append(f"📍 Near Support: ${support:.2f}")
if current_price >= resistance - 5:
    bearish += 2
    signals.append(f"📍 Near Resistance: ${resistance:.2f}")

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
# عرض الواجهة
# ==========================================

# بطاقات
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Gold Price", f"${current_price:.2f}")
col2.metric("📈 RSI", f"{current_rsi:.1f}")
col3.metric("🎯 Signal", signal_type, delta=f"{confidence}%")
col4.metric("📊 Net Score", f"+{bullish}/-{bearish}", delta=f"net {net:+d}")

st.markdown("---")

# الشارت
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold', line=dict(color='gold', width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='blue')))
fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text="Resistance")
fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text="Support")
fig.update_layout(template="plotly_dark", height=450, title=f"Gold Price - ${current_price:.2f}")
st.plotly_chart(fig, use_container_width=True)

# RSI Chart
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='purple', width=2)))
fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
fig2.update_layout(template="plotly_dark", height=250, title="RSI Indicator")
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# المؤشرات
st.subheader("📊 Indicators")
for s in signals:
    if "✅" in s or "📈" in s:
        st.success(s)
    elif "⚠️" in s or "📉" in s:
        st.error(s)
    else:
        st.info(s)

st.markdown("---")

# خطة التداول
st.subheader("🎯 Trading Plan")

if signal_action == "BUY":
    st.markdown(f"""
    | Level | Price |
    |-------|-------|
    | **Entry** | **${entry:.2f}** |
    | **Stop Loss** | ${stop_loss:.2f} |
    | **Target 1** | ${targets[0]:.2f} |
    | **Target 2** | ${targets[1]:.2f} |
    | **Target 3** | ${targets[2]:.2f} |
    """)
elif signal_action == "SELL":
    st.markdown(f"""
    | Level | Price |
    |-------|-------|
    | **Entry** | **${entry:.2f}** |
    | **Stop Loss** | ${stop_loss:.2f} |
    | **Target 1** | ${targets[0]:.2f} |
    | **Target 2** | ${targets[1]:.2f} |
    | **Target 3** | ${targets[2]:.2f} |
    """)
else:
    st.info("No clear signal. Continue monitoring.")

st.markdown("---")
st.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
