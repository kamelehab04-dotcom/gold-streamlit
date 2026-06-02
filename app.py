import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import numpy as np
import requests

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS للتنسيق
# ==========================================
st.markdown("""
<style>
    .pharaoh-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #ffd70033;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    .pharaoh-title {
        font-size: 2rem;
        color: #ffd700;
        text-shadow: 2px 2px 4px #000000;
        margin: 0;
        font-weight: bold;
    }
    .pharaoh-subtitle {
        font-size: 0.8rem;
        color: #888;
        margin: 5px 0 0 0;
    }
    .signal-buy {
        background-color: #00ff8833;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #00ff88;
    }
    .signal-sell {
        background-color: #ff444433;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4444;
    }
    .signal-neutral {
        background-color: #ffaa0033;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffaa00;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #ffd70033;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر بالصورة
# ==========================================

# عرض الصورة (استخدم الرابط المباشر أو اسم الملف)
try:
    st.image("https://raw.githubusercontent.com/kamelehab04-dotcom/gold-streamlit/refs/heads/main/ChatGPT%20Image%202%20%D9%8A%D9%88%D9%86%D9%8A%D9%88%202026%D8%8C%2009_05_59%20%D8%B5.png", width=80)
except:
    # لو الصورة مش موجودة، اعرض النص فقط
    pass

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align:center">
        <h1 style="color:#ffd700; margin:0">𓋹 PHARAOH GOLD DASHBOARD 𓋹</h1>
        <p style="color:#888">بوت تحليل الذهب الفرعوني | SMC + ICT Analysis</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

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
# عرض السعر الرئيسي
# ==========================================
st.markdown(f"""
<div style="background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding:25px; border-radius:15px; margin-bottom:20px; text-align:center; border:1px solid #ffd700">
    <h2 style="color:#ffd700; margin:0">𓋹 REAL TIME GOLD PRICE 𓋹</h2>
    <h1 style="color:#ffffff; font-size:3.5rem; margin:10px 0">${current_price:.2f}</h1>
    <p style="color:#888">Live from GoldAPI.io • Updated every 30 seconds</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# البطاقات
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:2rem">📈</div>
        <div style="font-size:1.5rem; font-weight:bold">{current_rsi:.1f}</div>
        <div style="color:#888">RSI</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    color = "#00ff88" if "BUY" in signal_type else "#ff4444" if "SELL" in signal_type else "#ffaa00"
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:2rem">🎯</div>
        <div style="font-size:1.2rem; font-weight:bold; color:{color}">{signal_type.split('-')[0].strip()}</div>
        <div style="color:#888">Signal | {confidence}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:2rem">📊</div>
        <div style="font-size:1.2rem; font-weight:bold">{bullish} / {bearish}</div>
        <div style="color:#888">Net: {net:+d}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:2rem">📐</div>
        <div style="font-size:1.2rem; font-weight:bold">${current_atr:.2f}</div>
        <div style="color:#888">ATR</div>
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
fig.add_hline(y=current_price, line_dash="dot", line_color="white", annotation_text=f"Current: ${current_price:.2f}")
fig.update_layout(template="plotly_dark", height=450, title="📊 Gold Historical Chart")
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# RSI Chart
# ==========================================
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='#9b59b6', width=2)))
fig2.add_hline(y=70, line_dash="dash", line_color="#ff4444", annotation_text="Overbought")
fig2.add_hline(y=30, line_dash="dash", line_color="#00ff88", annotation_text="Oversold")
fig2.update_layout(template="plotly_dark", height=250, title="📊 RSI Indicator")
st.plotly_chart(fig2, use_container_width=True)

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

st.markdown("---")

# ==========================================
# خطة التداول
# ==========================================
st.subheader("🎯 Trading Plan")

if signal_action == "BUY":
    st.markdown(f"""
    <div class="signal-buy">
        <b>🟢 BUY SIGNAL - {confidence}% confidence</b><br><br>
        📍 <b>Entry:</b> ${entry:.2f}<br>
        🛑 <b>Stop Loss:</b> ${stop_loss:.2f}<br><br>
        🎯 <b>Targets:</b><br>
        • Target 1: ${targets[0]:.2f}<br>
        • Target 2: ${targets[1]:.2f}<br>
        • Target 3: ${targets[2]:.2f}
    </div>
    """, unsafe_allow_html=True)
elif signal_action == "SELL":
    st.markdown(f"""
    <div class="signal-sell">
        <b>🔴 SELL SIGNAL - {confidence}% confidence</b><br><br>
        📍 <b>Entry:</b> ${entry:.2f}<br>
        🛑 <b>Stop Loss:</b> ${stop_loss:.2f}<br><br>
        🎯 <b>Targets:</b><br>
        • Target 1: ${targets[0]:.2f}<br>
        • Target 2: ${targets[1]:.2f}<br>
        • Target 3: ${targets[2]:.2f}
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="signal-neutral">
        <b>🟡 WAIT - No clear signal</b><br><br>
        Continue monitoring the market.
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
