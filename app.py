import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Gold Analysis", layout="wide")

st.title("🥇 Gold Price Analysis")
st.markdown("---")

# جلب البيانات
gold = yf.Ticker("GC=F")
df = gold.history(period="3d", interval="1h")
df.columns = [col.lower() for col in df.columns]

# حساب RSI يدوي
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'])
price = df['close'].iloc[-1]

# بطاقات
col1, col2 = st.columns(2)
col1.metric("💰 Gold Price", f"${price:.2f}")
col2.metric("📈 RSI", f"{df['rsi'].iloc[-1]:.1f}")

# الشارت
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold Price', line=dict(color='gold', width=2)))
fig.update_layout(template="plotly_dark", title=f"Gold Price - ${price:.2f}", height=400)
st.plotly_chart(fig, use_container_width=True)

# إشارة التداول
rsi_value = df['rsi'].iloc[-1]
if rsi_value < 35:
    st.success("🟢 BUY SIGNAL - Oversold")
elif rsi_value > 65:
    st.error("🔴 SELL SIGNAL - Overbought")
else:
    st.warning("🟡 WAIT - Neutral")

st.caption(f"🕐 Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
