import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import json
import os

# ==========================================
# إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="Pharaoh Gold Dashboard",
    page_icon="🥇",
    layout="wide"
)

st.title("🥇 PHARAOH GOLD DASHBOARD")
st.markdown("---")

# ==========================================
# سجل الصفقات (Trade Journal)
# ==========================================
TRADES_FILE = "trades.json"

def load_trades():
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_trades(trades):
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)

def add_trade(trade):
    trades = load_trades()
    trade['id'] = len(trades) + 1
    trade['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    trades.append(trade)
    save_trades(trades)

# ==========================================
# جلب البيانات
# ==========================================
@st.cache_data(ttl=300)
def get_data():
    gold = yf.Ticker("GC=F")
    df = gold.history(period="1mo", interval="1h")
    if df.empty:
        return None
    df.columns = [col.lower() for col in df.columns]
    return df

df = get_data()

if df is None:
    st.error("Error fetching data")
    st.stop()

# ==========================================
# حساب المؤشرات الأساسية
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

def calculate_macd(data):
    ema12 = calculate_ema(data, 12)
    ema26 = calculate_ema(data, 26)
    macd = ema12 - ema26
    signal = calculate_ema(macd, 9)
    histogram = macd - signal
    return macd, signal, histogram

# حساب المؤشرات
df['ema20'] = calculate_ema(df['close'], 20)
df['ema50'] = calculate_ema(df['close'], 50)
df['rsi'] = calculate_rsi(df['close'])
df['atr'] = calculate_atr(df)
df['macd'], df['macd_signal'], df['macd_histogram'] = calculate_macd(df['close'])
df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

current_price = df['close'].iloc[-1]
current_rsi = df['rsi'].iloc[-1]
current_atr = df['atr'].iloc[-1]
current_vwap = df['vwap'].iloc[-1]
current_macd = df['macd'].iloc[-1]
current_macd_signal = df['macd_signal'].iloc[-1]

# ==========================================
# تحليل SMC (Smart Money Concepts)
# ==========================================

# كشف القمم والقيعان
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

# Order Block (آخر شمعة قوية قبل الحركة)
def detect_order_blocks(df):
    order_blocks = []
    for i in range(3, len(df)-1):
        if df['close'].iloc[i] > df['open'].iloc[i]:
            body = df['close'].iloc[i] - df['open'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                order_blocks.append(('bullish', df['low'].iloc[i-1], df['high'].iloc[i-1]))
        if df['close'].iloc[i] < df['open'].iloc[i]:
            body = df['open'].iloc[i] - df['close'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                order_blocks.append(('bearish', df['low'].iloc[i-1], df['high'].iloc[i-1]))
    return order_blocks

# Fair Value Gap (FVG)
def detect_fvg(df):
    fvgs = []
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            fvgs.append(('bullish', df['high'].iloc[i-2], df['low'].iloc[i]))
        if df['high'].iloc[i] < df['low'].iloc[i-2]:
            fvgs.append(('bearish', df['low'].iloc[i-2], df['high'].iloc[i]))
    return fvgs

# Liquidity Sweep
def detect_liquidity_sweeps(df):
    sweeps = []
    for i in range(10, len(df)):
        recent_lows = df['low'].iloc[i-10:i].tolist()
        if df['low'].iloc[i] < min(recent_lows[:-1]):
            sweeps.append(('bullish', df['low'].iloc[i]))
        recent_highs = df['high'].iloc[i-10:i].tolist()
        if df['high'].iloc[i] > max(recent_highs[:-1]):
            sweeps.append(('bearish', df['high'].iloc[i]))
    return sweeps

# Break of Structure (BOS)
def detect_bos(df):
    bos_list = []
    for i in range(5, len(df)):
        if df['close'].iloc[i] > df['high'].iloc[i-5:i].max():
            bos_list.append(('bullish', df['close'].iloc[i]))
        if df['close'].iloc[i] < df['low'].iloc[i-5:i].min():
            bos_list.append(('bearish', df['close'].iloc[i]))
    return bos_list

# الدعم والمقاومة
def get_support_resistance(df):
    recent_highs = df['high'].iloc[-30:].values
    recent_lows = df['low'].iloc[-30:].values
    resistance = np.percentile(recent_highs, 75)
    support = np.percentile(recent_lows, 25)
    return support, resistance

# مناطق الخصم والعلاوة
def get_premium_discount(df, current_price):
    range_high = df['high'].iloc[-50:].max()
    range_low = df['low'].iloc[-50:].min()
    discount = range_low + (range_high - range_low) * 0.382
    premium = range_high - (range_high - range_low) * 0.382
    return discount, premium

# ==========================================
# كشف النماذج (Chart Patterns)
# ==========================================

# Double Top / Bottom
def detect_double_top_bottom(df):
    peaks = find_peaks(df['high'].values)
    troughs = find_troughs(df['low'].values)
    
    if len(peaks) >= 2:
        last_two_peaks = peaks[-2:]
        if abs(last_two_peaks[-1] - last_two_peaks[-2]) / last_two_peaks[-2] < 0.02:
            return "Double Top", "bearish"
    
    if len(troughs) >= 2:
        last_two_troughs = troughs[-2:]
        if abs(last_two_troughs[-1] - last_two_troughs[-2]) / last_two_troughs[-2] < 0.02:
            return "Double Bottom", "bullish"
    
    return None, None

# Head and Shoulders (مبسط)
def detect_head_shoulders(df):
    peaks = find_peaks(df['high'].values, order=3)
    if len(peaks) >= 3:
        if peaks[-2] > peaks[-3] and peaks[-2] > peaks[-1]:
            return "Head and Shoulders", "bearish"
    return None, None

# ==========================================
# نظام التسجيل (Scoring System)
# ==========================================
bullish = 0
bearish = 0
signals_list = []

# 1. RSI (3 نقاط)
if current_rsi < 45:
    bullish += 3
    signals_list.append(f"✅ RSI: {current_rsi:.1f} - BUY ZONE")
elif current_rsi > 65:
    bearish += 3
    signals_list.append(f"⚠️ RSI: {current_rsi:.1f} - SELL ZONE")
else:
    signals_list.append(f"📊 RSI: {current_rsi:.1f} - NEUTRAL")

# 2. المتوسطات المتحركة (2 نقطة)
if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals_list.append("📈 Price above EMA20")
else:
    bearish += 2
    signals_list.append("📉 Price below EMA20")

# 3. MACD (2 نقطة)
if current_macd > current_macd_signal:
    bullish += 2
    signals_list.append("🟢 MACD Positive")
else:
    bearish += 2
    signals_list.append("🔴 MACD Negative")

# 4. VWAP (1 نقطة)
if current_price > current_vwap:
    bullish += 1
    signals_list.append("💰 Price above VWAP")
else:
    bearish += 1
    signals_list.append("💰 Price below VWAP")

# 5. Liquidity Sweeps (3 نقاط)
sweeps = detect_liquidity_sweeps(df)
if sweeps:
    last_sweep = sweeps[-1]
    if last_sweep[0] == 'bullish':
        bullish += 3
        signals_list.append("🎯 Liquidity Sweep Bullish")
    else:
        bearish += 3
        signals_list.append("🎯 Liquidity Sweep Bearish")

# 6. Break of Structure (2 نقطة)
bos_list = detect_bos(df)
if bos_list:
    last_bos = bos_list[-1]
    if last_bos[0] == 'bullish':
        bullish += 2
        signals_list.append("🚀 BOS Bullish")
    else:
        bearish += 2
        signals_list.append("🚀 BOS Bearish")

# 7. Premium/Discount Zones (2 نقطة)
discount, premium = get_premium_discount(df, current_price)
if current_price <= discount:
    bullish += 2
    signals_list.append(f"📍 Discount Zone: ${discount:.2f}")
if current_price >= premium:
    bearish += 2
    signals_list.append(f"📍 Premium Zone: ${premium:.2f}")

# 8. النماذج (Chart Patterns) - 3-5 نقاط
pattern, pattern_direction = detect_double_top_bottom(df)
if pattern:
    if pattern_direction == 'bullish':
        bullish += 4
        signals_list.append(f"📈 {pattern} Detected")
    else:
        bearish += 4
        signals_list.append(f"📉 {pattern} Detected")

pattern, pattern_direction = detect_head_shoulders(df)
if pattern:
    if pattern_direction == 'bullish':
        bullish += 5
        signals_list.append(f"📈 {pattern} Detected")
    else:
        bearish += 5
        signals_list.append(f"📉 {pattern} Detected")

# النتيجة النهائية
net = bullish - bearish

if net >= 10:
    signal_type = "🔴🔴🔴 STRONG BUY 🔴🔴🔴"
    signal_action = "BUY"
    confidence = 95
elif net >= 6:
    signal_type = "🟢🟢 BUY 🟢🟢"
    signal_action = "BUY"
    confidence = 85
elif net >= 3:
    signal_type = "🟢 LIGHT BUY 🟢"
    signal_action = "BUY"
    confidence = 70
elif net <= -10:
    signal_type = "🔴🔴🔴 STRONG SELL 🔴🔴🔴"
    signal_action = "SELL"
    confidence = 95
elif net <= -6:
    signal_type = "🔴🔴 SELL 🔴🔴"
    signal_action = "SELL"
    confidence = 85
elif net <= -3:
    signal_type = "🔴 LIGHT SELL 🔴"
    signal_action = "SELL"
    confidence = 70
else:
    signal_type = "🟡 WAIT 🟡"
    signal_action = "NEUTRAL"
    confidence = 50

# ==========================================
# الأهداف ووقف الخسارة
# ==========================================
support, resistance = get_support_resistance(df)

if signal_action == "BUY":
    entry = current_price
    stop_loss = support - (current_atr * 0.3)
    targets = [
        resistance,
        resistance + (current_atr * 1.5),
        resistance + (current_atr * 3)
    ]
elif signal_action == "SELL":
    entry = current_price
    stop_loss = resistance + (current_atr * 0.3)
    targets = [
        support,
        support - (current_atr * 1.5),
        support - (current_atr * 3)
    ]
else:
    entry = current_price
    stop_loss = None
    targets = []

# ==========================================
# عرض الواجهة
# ==========================================

# بطاقات المعلومات
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("💰 Gold Price", f"${current_price:.2f}")
with col2:
    st.metric("📈 RSI", f"{current_rsi:.1f}")
with col3:
    st.metric("📊 ATR", f"${current_atr:.2f}")
with col4:
    st.metric("🎯 Signal", signal_type.split('-')[0].strip(), delta=f"{confidence}%")
with col5:
    st.metric("📰 Score", f"+{bullish}/-{bearish}", delta=f"net {net:+d}")

st.markdown("---")

# التبويبات
tab1, tab2, tab3, tab4 = st.tabs(["📈 Chart", "📊 Indicators", "🎯 Trading Plan", "📋 Signals Detail"])

# تبويب 1: الشارت
with tab1:
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                        row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=("Price with EMA", "RSI", "MACD"))
    
    # السعر والمتوسطات
    fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Gold"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name="EMA 20", line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name="EMA 50", line=dict(color='blue')), row=1, col=1)
    fig.add_hline(y=resistance, line_dash="dash", line_color="red", row=1, col=1, annotation_text="Resistance")
    fig.add_hline(y=support, line_dash="dash", line_color="green", row=1, col=1, annotation_text="Support")
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name="RSI", line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name="MACD", line=dict(color='cyan')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name="Signal", line=dict(color='yellow')), row=3, col=1)
    
    colors = ['red' if val < 0 else 'green' for val in df['macd_histogram'].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df['macd_histogram'], name="Histogram", marker_color=colors), row=3, col=1)
    
    fig.update_layout(template="plotly_dark", height=800, title=f"Gold Price - ${current_price:.2f}")
    st.plotly_chart(fig, use_container_width=True)

# تبويب 2: المؤشرات
with tab2:
    st.subheader("📊 Technical Indicators")
    for s in signals_list[:8]:
        if "✅" in s or "📈" in s:
            st.success(s)
        elif "⚠️" in s or "📉" in s:
            st.error(s)
        else:
            st.info(s)

# تبويب 3: خطة التداول
with tab3:
    st.subheader("🎯 Trading Plan")
    
    if signal_action == "BUY":
        st.markdown(f"""
        ### 🟢 BUY SIGNAL
        | Level | Price |
        |-------|-------|
        | **Entry** | **${entry:.2f}** |
        | **Stop Loss** | ${stop_loss:.2f} |
        | **Target 1** | ${targets[0]:.2f} |
        | **Target 2** | ${targets[1]:.2f} |
        | **Target 3** | ${targets[2]:.2f} |
        
        **Risk/Reward:** 1:{(targets[0]-entry)/(entry-stop_loss):.1f}
        """)
    elif signal_action == "SELL":
        st.markdown(f"""
        ### 🔴 SELL SIGNAL
        | Level | Price |
        |-------|-------|
        | **Entry** | **${entry:.2f}** |
        | **Stop Loss** | ${stop_loss:.2f} |
        | **Target 1** | ${targets[0]:.2f} |
        | **Target 2** | ${targets[1]:.2f} |
        | **Target 3** | ${targets[2]:.2f} |
        
        **Risk/Reward:** 1:{(entry-targets[0])/(stop_loss-entry):.1f}
        """)
    else:
        st.markdown("### 🟡 WAIT - No clear signal")
        st.write("Continue monitoring the market")

# تبويب 4: تفاصيل الإشارات
with tab4:
    st.subheader("📋 Signal Details")
    st.write(f"**Bullish Points:** {bullish}")
    st.write(f"**Bearish Points:** {bearish}")
    st.write(f"**Net Score:** {net:+d}")
    st.write(f"**Confidence:** {confidence}%")
    
    st.markdown("---")
    st.subheader("🔬 SMC Analysis")
    st.write(f"**Support:** ${support:.2f}")
    st.write(f"**Resistance:** ${resistance:.2f}")
    st.write(f"**Discount Zone:** ${discount:.2f}")
    st.write(f"**Premium Zone:** ${premium:.2f}")

# وقت التحديث
st.markdown("---")
st.caption(f"🕐 Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
