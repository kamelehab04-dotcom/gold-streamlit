import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import json
import os

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS
# ==========================================
st.markdown("""
<style>
    .main-header { text-align: center; padding: 30px; background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); border-radius: 20px; margin-bottom: 30px; border: 1px solid #ffd70033; }
    .main-title { font-size: 2.5rem; color: #ffd700; text-shadow: 2px 2px 4px #000000; margin: 0; font-weight: bold; }
    .main-subtitle { font-size: 1rem; color: #aaa; margin-top: 10px; }
    .telegram-btn { display: inline-block; background: linear-gradient(135deg, #0088cc 0%, #006699 100%); color: white; padding: 12px 24px; border-radius: 30px; text-decoration: none; font-weight: bold; margin: 10px; transition: transform 0.3s; }
    .telegram-btn:hover { transform: translateY(-2px); }
    .price-card { background: linear-gradient(135deg, #ffd70015 0%, #ffaa0015 100%); border-radius: 20px; padding: 30px; text-align: center; border: 2px solid #ffd700; margin: 20px 0; }
    .price-value { font-size: 4rem; font-weight: bold; color: #ffffff; margin: 10px 0; }
    .live-badge { background: #ff4444; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; display: inline-block; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.6; } 100% { opacity: 1; } }
    .signal-card { border-radius: 15px; padding: 20px; margin: 20px 0; text-align: center; }
    .signal-buy { background: linear-gradient(135deg, #00ff8820 0%, #00cc6620 100%); border: 1px solid #00ff88; }
    .signal-sell { background: linear-gradient(135deg, #ff444420 0%, #cc333320 100%); border: 1px solid #ff4444; }
    .signal-neutral { background: linear-gradient(135deg, #ffaa0020 0%, #cc880020 100%); border: 1px solid #ffaa00; }
    .signal-title { font-size: 1.5rem; font-weight: bold; }
    .targets-table { background: #1e1e2e; border-radius: 12px; overflow: hidden; margin: 20px 0; }
    .target-row { display: flex; justify-content: space-between; padding: 12px 20px; border-bottom: 1px solid #333; }
    .target-label { color: #ffd700; font-weight: bold; }
    .footer { text-align: center; padding: 20px; color: #666; font-size: 0.8rem; border-top: 1px solid #333; margin-top: 30px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1e1e2e; border-radius: 10px; padding: 8px 20px; border: 1px solid #ffd70033; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #ffd70020 0%, #ffaa0020 100%); border-color: #ffd700; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="main-title">PHARAOH GOLD DASHBOARD</div>
    <div class="main-subtitle">Gold Analysis Bot | High Accuracy Signals</div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; margin: 10px 0 20px 0;">
        <a href="https://t.me/Ehabka2002" target="_blank" class="telegram-btn">
            Subscribe on Telegram for daily signals
        </a>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# API Settings
# ==========================================
GOLD_API_KEY = "goldapi-2262c60e69ce568bf76b982116077d1f-io"

# ==========================================
# Risk Manager
# ==========================================
class RiskManager:
    def __init__(self):
        self.trading_capital = 10000
        self.risk_per_trade = 100
        self.point_value = 0.1
    
    def get_recommended_lot(self, entry, stop_loss):
        stop_pips = abs(entry - stop_loss)
        if stop_pips > 0:
            return round(self.risk_per_trade / (stop_pips * self.point_value), 2)
        return 0

risk_manager = RiskManager()

# ==========================================
# Get Data
# ==========================================
@st.cache_data(ttl=10)
def get_spot_price():
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return float(response.json().get('price', 0))
        return None
    except:
        return None

@st.cache_data(ttl=300)
def get_historical_data():
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="3d", interval="1h")
        if df.empty:
            return None
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return None

current_price = get_spot_price()
df = get_historical_data()

if df is None:
    st.error("Error loading data")
    st.stop()

if current_price is None:
    current_price = df['close'].iloc[-1]

# ==========================================
# Calculate Indicators
# ==========================================
def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

df['ema20'] = df['close'].ewm(span=20).mean()
df['ema50'] = df['close'].ewm(span=50).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])

def calc_macd(data):
    ema12 = data.ewm(span=12).mean()
    ema26 = data.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal, macd - signal

current_rsi = df['rsi'].iloc[-1]
current_atr = df['atr'].iloc[-1]
current_macd = df['macd'].iloc[-1]
current_macd_signal = df['macd_signal'].iloc[-1]

# ==========================================
# SMC Signals (مؤكدة)
# ==========================================
# Liquidity Sweep - اصطياد سيولة حقيقي
recent_lows = df['low'].iloc[-20:-1].min()
recent_highs = df['high'].iloc[-20:-1].max()
liquidity_sweep_bullish = df['low'].iloc[-1] < recent_lows
liquidity_sweep_bearish = df['high'].iloc[-1] > recent_highs

# Break of Structure - كسر هيكل مؤكد
bos_bullish = current_price > df['high'].iloc[-6:-1].max()
bos_bearish = current_price < df['low'].iloc[-6:-1].min()

# Support/Resistance (مستويات قوية)
resistance = np.percentile(df['high'].iloc[-50:], 75)
support = np.percentile(df['low'].iloc[-50:], 25)

# Order Block (آخر شمعة قوية)
last_candle_bullish = df['close'].iloc[-2] > df['open'].iloc[-2]
last_candle_bearish = df['close'].iloc[-2] < df['open'].iloc[-2]
last_candle_body = abs(df['close'].iloc[-2] - df['open'].iloc[-2])
avg_body = df['close'].diff().abs().rolling(10).mean().iloc[-2]
order_block_bullish = last_candle_bullish and last_candle_body > avg_body * 1.5
order_block_bearish = last_candle_bearish and last_candle_body > avg_body * 1.5

# ==========================================
# نظام التسجيل المحكم (دقة عالية)
# ==========================================
bullish = 0
bearish = 0
signals = []
strong_buy_conditions = 0
strong_sell_conditions = 0

# 1. RSI (وزن 4 - مهم جداً)
if current_rsi < 35:
    bullish += 4
    strong_buy_conditions += 1
    signals.append(f"✅ RSI: {current_rsi:.1f} (OVERSOLD - BUY ZONE)")
elif current_rsi > 70:
    bearish += 4
    strong_sell_conditions += 1
    signals.append(f"⚠️ RSI: {current_rsi:.1f} (OVERBOUGHT - SELL ZONE)")
elif current_rsi < 45:
    bullish += 2
    signals.append(f"📈 RSI: {current_rsi:.1f} (Cheap zone)")
elif current_rsi > 60:
    bearish += 2
    signals.append(f"📉 RSI: {current_rsi:.1f} (Expensive zone)")
else:
    signals.append(f"📊 RSI: {current_rsi:.1f} (Neutral)")

# 2. MACD (وزن 3)
if current_macd > current_macd_signal and current_macd > 0:
    bullish += 3
    strong_buy_conditions += 1
    signals.append("🟢 MACD: POSITIVE & ABOVE SIGNAL")
elif current_macd < current_macd_signal and current_macd < 0:
    bearish += 3
    strong_sell_conditions += 1
    signals.append("🔴 MACD: NEGATIVE & BELOW SIGNAL")
elif current_macd > current_macd_signal:
    bullish += 1
    signals.append("🟢 MACD: Bullish crossover")
elif current_macd < current_macd_signal:
    bearish += 1
    signals.append("🔴 MACD: Bearish crossover")

# 3. Price vs EMA (وزن 2)
if current_price > df['ema20'].iloc[-1] and current_price > df['ema50'].iloc[-1]:
    bullish += 2
    strong_buy_conditions += 1
    signals.append("📈 Price above EMA20 & EMA50 (Uptrend)")
elif current_price < df['ema20'].iloc[-1] and current_price < df['ema50'].iloc[-1]:
    bearish += 2
    strong_sell_conditions += 1
    signals.append("📉 Price below EMA20 & EMA50 (Downtrend)")
elif current_price > df['ema20'].iloc[-1]:
    bullish += 1
    signals.append("📈 Price above EMA20")
elif current_price < df['ema20'].iloc[-1]:
    bearish += 1
    signals.append("📉 Price below EMA20")

# 4. Liquidity Sweep (وزن 3 - إشارة قوية)
if liquidity_sweep_bullish:
    bullish += 3
    strong_buy_conditions += 1
    signals.append("🎯 LIQUIDITY SWEEP BULLISH (Stop hunt complete)")
if liquidity_sweep_bearish:
    bearish += 3
    strong_sell_conditions += 1
    signals.append("🎯 LIQUIDITY SWEEP BEARISH (Stop hunt complete)")

# 5. Break of Structure (وزن 2)
if bos_bullish:
    bullish += 2
    signals.append("🚀 BOS BULLISH (Structure broken up)")
if bos_bearish:
    bearish += 2
    signals.append("🚀 BOS BEARISH (Structure broken down)")

# 6. Order Block (وزن 3)
if order_block_bullish:
    bullish += 3
    strong_buy_conditions += 1
    signals.append("🏛️ ORDER BLOCK BULLISH (Institutional buying)")
if order_block_bearish:
    bearish += 3
    strong_sell_conditions += 1
    signals.append("🏛️ ORDER BLOCK BEARISH (Institutional selling)")

# 7. Support/Resistance (وزن 2)
if current_price <= support + 3:
    bullish += 2
    strong_buy_conditions += 1
    signals.append(f"📍 NEAR SUPPORT: ${support:.2f}")
elif current_price >= resistance - 3:
    bearish += 2
    strong_sell_conditions += 1
    signals.append(f"📍 NEAR RESISTANCE: ${resistance:.2f}")

# 8. ATR Confirmation (تأكيد التقلب)
if current_atr > 15:
    signals.append(f"📊 ATR: ${current_atr:.2f} (Good volatility)")

net = bullish - bearish

# ==========================================
# الإشارة النهائية (فقط عندما تكون قوية)
# ==========================================
if net >= 10 and strong_buy_conditions >= 2:
    signal_type = "🔴🔴🔴 STRONG BUY 🔴🔴🔴"
    signal_action = "BUY"
    confidence = min(95, 70 + net)
    signal_reason = f"{strong_buy_conditions} strong factors"
elif net >= 6:
    signal_type = "🟢🟢 BUY 🟢🟢"
    signal_action = "BUY"
    confidence = min(85, 60 + net)
    signal_reason = "Moderate buy signal"
elif net <= -10 and strong_sell_conditions >= 2:
    signal_type = "🔴🔴🔴 STRONG SELL 🔴🔴🔴"
    signal_action = "SELL"
    confidence = min(95, 70 + abs(net))
    signal_reason = f"{strong_sell_conditions} strong factors"
elif net <= -6:
    signal_type = "🔴🔴 SELL 🔴🔴"
    signal_action = "SELL"
    confidence = min(85, 60 + abs(net))
    signal_reason = "Moderate sell signal"
else:
    signal_type = "🟡 WAIT 🟡"
    signal_action = "NEUTRAL"
    confidence = 50
    signal_reason = "No clear signal"

# ==========================================
# Trading Plan (دقيق)
# ==========================================
if signal_action == "BUY":
    entry = current_price
    stop_loss = support - (current_atr * 0.8)
    lot = risk_manager.get_recommended_lot(entry, stop_loss)
    targets = [resistance, resistance + (current_atr * 1.5), resistance + (current_atr * 3)]
    rr_ratio = (targets[0] - entry) / (entry - stop_loss)
elif signal_action == "SELL":
    entry = current_price
    stop_loss = resistance + (current_atr * 0.8)
    lot = risk_manager.get_recommended_lot(entry, stop_loss)
    targets = [support, support - (current_atr * 1.5), support - (current_atr * 3)]
    rr_ratio = (entry - targets[0]) / (stop_loss - entry)
else:
    entry, stop_loss, lot, targets, rr_ratio = current_price, None, 0, [], 0

# Change
change = current_price - df['close'].iloc[-2] if len(df) > 1 else 0
change_pct = (change / df['close'].iloc[-2]) * 100 if len(df) > 1 else 0

# ==========================================
# Display
# ==========================================
st.markdown(f"""
<div class="price-card">
    <div class="price-label">LIVE SPOT - XAU/USD</div>
    <div class="price-value">${current_price:,.2f}</div>
    <div style="color:#00ff88">{change:+.2f} ({change_pct:+.2f}%)</div>
    <div style="color:#888; font-size:0.8rem">Source: GoldAPI.io</div>
</div>
""", unsafe_allow_html=True)

# Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("RSI", f"{current_rsi:.1f}")
c2.metric("ATR", f"${current_atr:.2f}")
c3.metric("Score", f"{net:+d}", delta=f"{bullish}/{bearish}")
c4.metric("Confidence", f"{confidence}%")

# Signal Card
if signal_action == "BUY":
    st.markdown(f"""
    <div class="signal-card signal-buy">
        <div class="signal-title" style="color:#00ff88">{signal_type}</div>
        <div>Confidence: {confidence}% | {signal_reason}</div>
        <div style="margin-top:10px; font-size:0.9rem">⚠️ Risk: 1% of capital | Stop: ${stop_loss:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
elif signal_action == "SELL":
    st.markdown(f"""
    <div class="signal-card signal-sell">
        <div class="signal-title" style="color:#ff4444">{signal_type}</div>
        <div>Confidence: {confidence}% | {signal_reason}</div>
        <div style="margin-top:10px; font-size:0.9rem">⚠️ Risk: 1% of capital | Stop: ${stop_loss:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="signal-card signal-neutral">
        <div class="signal-title" style="color:#ffaa00">{signal_type}</div>
        <div>Confidence: {confidence}% | {signal_reason}</div>
        <div style="margin-top:10px; font-size:0.9rem">💡 Wait for stronger confluence</div>
    </div>
    """, unsafe_allow_html=True)

# Chart
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.4])
fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Gold"), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='orange')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='blue')), row=1, col=1)
fig.add_hline(y=resistance, line_dash="dash", line_color="#ff4444", row=1, col=1, annotation_text="Resistance")
fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", row=1, col=1, annotation_text="Support")
fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='#9b59b6')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", row=2, col=1)
fig.update_layout(template="plotly_dark", height=600)
st.plotly_chart(fig, use_container_width=True)

# Trading Plan
if signal_action != "NEUTRAL":
    st.markdown("### 🎯 Trading Plan")
    st.markdown(f"""
    <div class="targets-table">
        <div class="target-row"><span class="target-label">📍 Entry</span><span class="target-value"><b>${entry:.2f}</b></span></div>
        <div class="target-row"><span class="target-label">🛑 Stop Loss</span><span class="target-value">${stop_loss:.2f}</span></div>
        <div class="target-row"><span class="target-label">📊 Position Size</span><span class="target-value">{lot:.2f} lots</span></div>
        <div class="target-row"><span class="target-label">💰 Risk Amount</span><span class="target-value">${risk_manager.risk_per_trade:.0f}</span></div>
        <div class="target-row"><span class="target-label">🎯 Target 1</span><span class="target-value">${targets[0]:.2f}</span></div>
        <div class="target-row"><span class="target-label">🎯 Target 2</span><span class="target-value">${targets[1]:.2f}</span></div>
        <div class="target-row"><span class="target-label">🎯 Target 3</span><span class="target-value">${targets[2]:.2f}</span></div>
        <div class="target-row"><span class="target-label">📈 Risk/Reward</span><span class="target-value">1 : {rr_ratio:.2f}</span></div>
    </div>
    """, unsafe_allow_html=True)

# Signals
with st.expander("📋 Technical Analysis Details"):
    for s in signals:
        if "BUY" in s or "bullish" in s.lower() or "✅" in s or "🟢" in s or "📈" in s:
            st.success(s)
        elif "SELL" in s or "bearish" in s.lower() or "⚠️" in s or "🔴" in s or "📉" in s:
            st.error(s)
        else:
            st.info(s)

# Footer
st.markdown(f"""
<div class="footer">
    🔬 SMC + ICT + MACD + RSI + EMA | High Accuracy System
    <br>
    <a href="https://t.me/Ehabka2002" target="_blank" style="color:#0088cc;">📱 Subscribe on Telegram for daily signals</a>
    <br>
    🕐 Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
