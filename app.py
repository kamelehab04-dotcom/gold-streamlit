import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Gold Analysis", layout="wide")

st.title("🥇 Gold Price Analysis")
st.markdown("---")

# جلب البيانات
@st.cache_data(ttl=300)
def get_data():
    gold = yf.Ticker("GC=F")
    df = gold.history(period="2d", interval="1h")
    if df.empty:
        return None
    df.columns = [col.lower() for col in df.columns]
    return df

df = get_data()

if df is None:
    st.error("Error loading data")
    st.stop()

# حساب المتوسطات
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()

# حساب RSI
def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calc_rsi(df['close'])

current_price = df['close'].iloc[-1]
current_rsi = df['rsi'].iloc[-1]

# عرض الأسعار
col1, col2, col3 = st.columns(3)
col1.metric("💰 Gold Price", f"${current_price:.2f}")
col2.metric("📈 RSI", f"{current_rsi:.1f}")
col3.metric("📊 Trend", "Bullish" if current_price > df['ema20'].iloc[-1] else "Bearish")

st.markdown("---")

# الشارت
fig = go.Figure()

# خط السعر
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold Price', line=dict(color='gold', width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='orange', width=1)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='blue', width=1)))

fig.update_layout(
    title=f"Gold Price - ${current_price:.2f}",
    template="plotly_dark",
    height=500,
    xaxis_title="Date",
    yaxis_title="Price (USD)"
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# RSI Chart
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='purple', width=2)))
fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
fig2.update_layout(template="plotly_dark", height=300, title="RSI Indicator")
st.plotly_chart(fig2, use_container_width=True)

# إشارة التداول
st.markdown("---")
st.subheader("🎯 Trading Signal")

if current_rsi < 35:
    st.success("🟢 **BUY SIGNAL** - Oversold area")
elif current_rsi > 65:
    st.error("🔴 **SELL SIGNAL** - Overbought area")
else:
    st.warning("🟡 **WAIT** - Neutral zone")

# وقت التحديث
st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
