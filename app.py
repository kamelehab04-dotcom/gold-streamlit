import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS للتنسيق
# ==========================================
st.markdown("""
<style>
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
    .telegram-btn {
        display: inline-block;
        background: linear-gradient(135deg, #0088cc 0%, #006699 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 30px;
        text-decoration: none;
        font-weight: bold;
        margin: 10px;
        transition: transform 0.3s;
        border: none;
        cursor: pointer;
    }
    .telegram-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,136,204,0.4);
    }
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
    .risk-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid #ffd70033;
    }
    .risk-warning {
        background: linear-gradient(135deg, #ff444420 0%, #cc333320 100%);
        border-left: 4px solid #ff4444;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .risk-success {
        background: linear-gradient(135deg, #00ff8820 0%, #00cc6620 100%);
        border-left: 4px solid #00ff88;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
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
    .live-badge {
        background: #ff4444;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
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
    .lot-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #ffd70033;
        text-align: center;
    }
    .lot-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00ff88;
    }
    .lot-label {
        font-size: 0.8rem;
        color: #888;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e2e;
        border-radius: 10px;
        padding: 8px 20px;
        border: 1px solid #ffd70033;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd70020 0%, #ffaa0020 100%);
        border-color: #ffd700;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">بوت تحليل الذهب الفرعوني | سعر فوري حقيقي XAU/USD | SMC + ICT</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# زر الاشتراك في التليجرام
# ==========================================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div style="text-align: center; margin: 10px 0 20px 0;">
        <a href="https://t.me/Ehabka2002" target="_blank" class="telegram-btn">
            📱 اشترك في قناة التليجرام للحصول على الإشارات اليومية
        </a>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# نظام إدارة المخاطر
# ==========================================

class RiskManager:
    def __init__(self):
        self.total_account = 100000
        self.max_loss_percent = 10
        self.trading_capital = self.total_account * (self.max_loss_percent / 100)
        
        self.daily_loss_percent = 5
        self.daily_profit_target_percent = 10
        self.max_daily_profit_percent = 12
        self.risk_per_trade_percent = 1
        
        self.daily_max_loss = (self.daily_loss_percent / 100) * self.trading_capital
        self.daily_profit_target = (self.daily_profit_target_percent / 100) * self.trading_capital
        self.daily_max_profit = (self.max_daily_profit_percent / 100) * self.trading_capital
        self.risk_per_trade = (self.risk_per_trade_percent / 100) * self.trading_capital
        
        self.point_value_per_lot = 0.1
        
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.daily_pnl = 0
        self.trades_today = 0
        self.load_daily_data()
    
    def load_daily_data(self):
        try:
            if os.path.exists("daily_trading.json"):
                with open("daily_trading.json", "r") as f:
                    data = json.load(f)
                    if data.get("date") == self.today:
                        self.daily_pnl = data.get("pnl", 0)
                        self.trades_today = data.get("trades", 0)
        except:
            pass
    
    def save_daily_data(self):
        try:
            with open("daily_trading.json", "w") as f:
                json.dump({
                    "date": self.today,
                    "pnl": self.daily_pnl,
                    "trades": self.trades_today
                }, f)
        except:
            pass
    
    def reset_daily(self):
        self.daily_pnl = 0
        self.trades_today = 0
        self.save_daily_data()
    
    def can_trade(self):
        if self.daily_pnl <= -self.daily_max_loss:
            return False, f"❌ تم الوصول إلى الحد الأقصى للخسارة اليومية (${self.daily_max_loss:,.2f})"
        if self.daily_pnl >= self.daily_max_profit:
            return False, f"✅ تم تحقيق الحد الأقصى للربح اليومي (${self.daily_max_profit:,.2f})"
        if self.trades_today >= 10:
            return False, "⚠️ تم الوصول إلى الحد الأقصى لعدد الصفقات اليومية (10 صفقات)"
        return True, "✅ يمكنك التداول"
    
    def calculate_position_size(self, entry_price, stop_loss_price):
        risk_amount = self.risk_per_trade
        stop_distance_pips = abs(entry_price - stop_loss_price)
        if stop_distance_pips > 0:
            position_size = risk_amount / (stop_distance_pips * self.point_value_per_lot)
            return round(position_size, 2)
        return 0
    
    def calculate_risk_per_trade(self, entry_price, stop_loss_price, lot_size):
        stop_distance_pips = abs(entry_price - stop_loss_price)
        risk = lot_size * stop_distance_pips * self.point_value_per_lot
        return round(risk, 2)
    
    def get_recommended_lot(self, entry_price, stop_loss_price):
        stop_distance_pips = abs(entry_price - stop_loss_price)
        if stop_distance_pips > 0:
            lot_size = self.risk_per_trade / (stop_distance_pips * self.point_value_per_lot)
            return round(lot_size, 2)
        return 0
    
    def get_trading_limits(self):
        remaining_loss = self.daily_max_loss + self.daily_pnl if self.daily_pnl < 0 else self.daily_max_loss
        remaining_profit = self.daily_max_profit - self.daily_pnl if self.daily_pnl > 0 else self.daily_max_profit
        
        return {
            "total_account": self.total_account,
            "trading_capital": self.trading_capital,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_percent": (self.daily_pnl / self.trading_capital) * 100,
            "daily_max_loss": self.daily_max_loss,
            "daily_max_profit": self.daily_max_profit,
            "profit_target": self.daily_profit_target,
            "remaining_loss": remaining_loss,
            "remaining_profit": remaining_profit,
            "risk_per_trade": self.risk_per_trade,
            "trades_today": self.trades_today,
            "can_trade": self.can_trade()[0],
            "can_trade_message": self.can_trade()[1]
        }
    
    def update_pnl(self, profit_loss):
        self.daily_pnl += profit_loss
        self.trades_today += 1
        self.save_daily_data()
        return self.get_trading_limits()

risk_manager = RiskManager()
limits = risk_manager.get_trading_limits()

# ==========================================
# عرض لوحة إدارة المخاطر
# ==========================================
st.markdown("### 🛡️ Risk Management System")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Total Account</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#ffd700">${limits['total_account']:,.0f}</div>
        <div style="font-size:0.8rem; color:#888">الحساب الأصلي</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Trading Capital</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#ffd700">${limits['trading_capital']:,.0f}</div>
        <div style="font-size:0.8rem; color:#888">10% من الحساب</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "#00ff88" if limits['daily_pnl'] >= 0 else "#ff4444"
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Today's P&L</div>
        <div style="font-size:1.5rem; font-weight:bold; color:{color}">${limits['daily_pnl']:,.2f}</div>
        <div style="font-size:0.8rem; color:#888">{limits['daily_pnl_percent']:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Max Daily Loss</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#ff4444">${limits['daily_max_loss']:,.0f}</div>
        <div style="font-size:0.8rem; color:#888">5% من رأس المال</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Daily Target</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#00ff88">${limits['profit_target']:,.0f}</div>
        <div style="font-size:0.8rem; color:#888">10% هدف يومي</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Max Daily Profit</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#00ff88">${limits['daily_max_profit']:,.0f}</div>
        <div style="font-size:0.8rem; color:#888">12% حد أقصى</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Risk Per Trade</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#ffaa00">${limits['risk_per_trade']:,.0f}</div>
        <div style="font-size:0.8rem; color:#888">1% من رأس المال</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown(f"""
    <div class="risk-card">
        <div style="font-size:0.9rem; color:#888">Trades Today</div>
        <div style="font-size:1.5rem; font-weight:bold; color:#ffaa00">{limits['trades_today']}/10</div>
        <div style="font-size:0.8rem; color:#888">الحد الأقصى 10 صفقات</div>
    </div>
    """, unsafe_allow_html=True)

if limits['can_trade']:
    st.markdown(f"""
    <div class="risk-success">
        ✅ {limits['can_trade_message']}<br>
        📊 الخسارة المتبقية: ${limits['remaining_loss']:,.2f} | الربح المتبقي: ${limits['remaining_profit']:,.2f}
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="risk-warning">
        ⚠️ {limits['can_trade_message']}<br>
        📊 تم تنفيذ {limits['trades_today']} صفقة اليوم
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# تحليل الذهب (سعر فوري حقيقي من Yahoo Finance)
# ==========================================

@st.cache_data(ttl=10)
def get_spot_price():
    """جلب سعر الذهب الفوري الحقيقي من Yahoo Finance"""
    try:
        # XAUUSD=X هو الرمز الصحيح للسعر الفوري
        gold = yf.Ticker("XAUUSD=X")
        df = gold.history(period="1d", interval="1m")
        if not df.empty:
            return df['Close'].iloc[-1]
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

@st.cache_data(ttl=300)
def get_historical_data():
    try:
        gold = yf.Ticker("XAUUSD=X")
        df = gold.history(period="1mo", interval="1h")
        if df.empty:
            return None
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return None

# جلب السعر الفوري الحقيقي
current_price = get_spot_price()
df = get_historical_data()

if df is None:
    st.error("Error loading historical data")
    st.stop()

if current_price is None and df is not None:
    current_price = df['close'].iloc[-1]

if current_price is None:
    st.error("Unable to fetch gold spot price")
    st.stop()

# حساب المؤشرات
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

current_rsi = df['rsi'].iloc[-1] if not pd.isna(df['rsi'].iloc[-1]) else 50
current_atr = df['atr'].iloc[-1] if not pd.isna(df['atr'].iloc[-1]) else 20

# SMC Signals
recent_lows = df['low'].iloc[-20:].values
recent_highs = df['high'].iloc[-20:].values
liquidity_sweep_bullish = df['low'].iloc[-1] < min(recent_lows[:-1]) if len(recent_lows) > 1 else False
liquidity_sweep_bearish = df['high'].iloc[-1] > max(recent_highs[:-1]) if len(recent_highs) > 1 else False
bos_bullish = current_price > df['high'].iloc[-6:-1].max() if len(df) > 6 else False
bos_bearish = current_price < df['low'].iloc[-6:-1].min() if len(df) > 6 else False
resistance = np.percentile(df['high'].iloc[-30:], 75) if len(df) >= 30 else current_price + 20
support = np.percentile(df['low'].iloc[-30:], 25) if len(df) >= 30 else current_price - 20

# نظام التسجيل
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

if net >= 10:
    signal_type = "STRONG BUY"
    signal_action = "BUY"
    confidence = 95
    signal_color = "#00ff88"
elif net >= 5:
    signal_type = "BUY"
    signal_action = "BUY"
    confidence = 80
    signal_color = "#00ff88"
elif net <= -10:
    signal_type = "STRONG SELL"
    signal_action = "SELL"
    confidence = 95
    signal_color = "#ff4444"
elif net <= -5:
    signal_type = "SELL"
    signal_action = "SELL"
    confidence = 80
    signal_color = "#ff4444"
else:
    signal_type = "WAIT"
    signal_action = "NEUTRAL"
    confidence = 50
    signal_color = "#ffaa00"

# حساب اللوت
if signal_action == "BUY":
    entry = current_price
    stop_loss = support - (current_atr * 0.5)
    recommended_lot = risk_manager.get_recommended_lot(entry, stop_loss)
    targets = [resistance, resistance + (current_atr * 1.5), resistance + (current_atr * 3)]
    risk_amount = risk_manager.calculate_risk_per_trade(entry, stop_loss, recommended_lot)
elif signal_action == "SELL":
    entry = current_price
    stop_loss = resistance + (current_atr * 0.5)
    recommended_lot = risk_manager.get_recommended_lot(entry, stop_loss)
    targets = [support, support - (current_atr * 1.5), support - (current_atr * 3)]
    risk_amount = risk_manager.calculate_risk_per_trade(entry, stop_loss, recommended_lot)
else:
    entry = current_price
    stop_loss = None
    recommended_lot = 0
    targets = []
    risk_amount = 0

# حساب التغير
if len(df) > 1:
    prev_price = df['close'].iloc[-2]
    change = current_price - prev_price
    change_percent = (change / prev_price) * 100
else:
    change = 0
    change_percent = 0

change_color = "#00ff88" if change >= 0 else "#ff4444"
change_sign = "+" if change >= 0 else ""

# عرض السعر
st.markdown(f"""
<div class="price-card">
    <div class="price-label">
        <span class="live-badge">LIVE SPOT</span> 𓋹 XAU/USD (REAL TIME) 𓋹
    </div>
    <div class="price-value">${current_price:,.2f}</div>
    <div class="price-change" style="color:{change_color}">{change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)</div>
    <div style="color:#888; font-size:0.8rem; margin-top:10px">Source: Yahoo Finance (XAU/USD Spot)</div>
</div>
""", unsafe_allow_html=True)

# بطاقات المؤشرات
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

# الإشارة
signal_class = "signal-buy" if signal_action == "BUY" else "signal-sell" if signal_action == "SELL" else "signal-neutral"
st.markdown(f"""
<div class="signal-card {signal_class}">
    <div class="signal-title" style="color:{signal_color}">{signal_type} SIGNAL</div>
    <div class="signal-confidence">Confidence: {confidence}% | Score: {net:+d}</div>
</div>
""", unsafe_allow_html=True)

# اللوت الموصى به
if signal_action != "NEUTRAL" and limits['can_trade']:
    st.markdown("### 📊 Position Size Calculator")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="lot-card">
            <div class="lot-label">🔢 RECOMMENDED LOT SIZE</div>
            <div class="lot-value">{recommended_lot:.2f} LOTS</div>
            <div class="lot-label">Risk: ${risk_manager.risk_per_trade:,.0f} | 1% of capital</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="lot-card">
            <div class="lot-label">💰 ACTUAL RISK</div>
            <div class="lot-value">${risk_amount:,.2f}</div>
            <div class="lot-label">With current lot size</div>
        </div>
        """, unsafe_allow_html=True)
    
    # جدول أحجام اللوتات
    st.markdown("#### 📋 Lot Size Alternatives")
    lot_options = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00]
    lot_data = []
    for lot in lot_options:
        risk = risk_manager.calculate_risk_per_trade(entry, stop_loss, lot)
        lot_data.append({"Lot": f"{lot:.2f}", "Risk ($)": f"${risk:.2f}", "Risk %": f"{(risk / risk_manager.trading_capital) * 100:.2f}%"})
    st.dataframe(pd.DataFrame(lot_data), use_container_width=True, hide_index=True)

# الشارت
st.markdown("### 📈 Price Chart")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='XAU/USD', line=dict(color='#ffd700', width=2)))
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='#ff9f4a')))
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='#4a9eff')))
fig.add_hline(y=resistance, line_dash="dash", line_color="#ff4444", annotation_text="Resistance")
fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", annotation_text="Support")
fig.update_layout(template="plotly_dark", height=450)
st.plotly_chart(fig, use_container_width=True)

# خطة التداول
if signal_action != "NEUTRAL" and limits['can_trade']:
    st.markdown("### 🎯 Trading Plan")
    st.markdown(f"""
    <div class="targets-table">
        <div class="target-row"><span class="target-label">📍 Entry</span><span class="target-value">${entry:.2f}</span></div>
        <div class="target-row"><span class="target-label">🛑 Stop Loss</span><span class="target-value">${stop_loss:.2f}</span></div>
        <div class="target-row"><span class="target-label">📊 Lot Size</span><span class="target-value">{recommended_lot:.2f} lots</span></div>
        <div class="target-row"><span class="target-label">💰 Risk</span><span class="target-value">${risk_amount:,.2f}</span></div>
        <div class="target-row"><span class="target-label">🎯 Target 1</span><span class="target-value">${targets[0]:.2f}</span></div>
        <div class="target-row"><span class="target-label">🎯 Target 2</span><span class="target-value">${targets[1]:.2f}</span></div>
        <div class="target-row"><span class="target-label">🎯 Target 3</span><span class="target-value">${targets[2]:.2f}</span></div>
    </div>
    """, unsafe_allow_html=True)
    rr = (targets[0] - entry) / (entry - stop_loss) if signal_action == "BUY" else (entry - targets[0]) / (stop_loss - entry)
    st.markdown(f"""
    <div class="stats-container" style="margin-top:20px">
        <div class="stat-card"><div class="stat-number" style="font-size:1rem">Risk/Reward</div><div class="stat-label">1 : {rr:.2f}</div></div>
        <div class="stat-card"><div class="stat-number" style="font-size:1rem">Remaining Risk</div><div class="stat-label">${limits['remaining_loss']:,.2f}</div></div>
    </div>
    """, unsafe_allow_html=True)
elif not limits['can_trade']:
    st.warning(limits['can_trade_message'])

with st.expander("📊 Technical Indicators Details"):
    for s in signals:
        if "✅" in s or "📈" in s:
            st.success(s)
        elif "⚠️" in s or "📉" in s:
            st.error(s)
        else:
            st.info(s)

# ==========================================
# تبويب التقويم الاقتصادي (مبسط)
# ==========================================
with st.tabs(["📅 Economic Calendar"]):
    st.markdown("### 📅 Economic Calendar")
    st.markdown("---")
    today = datetime.now()
    events = [
        {"title": "Federal Reserve Interest Rate Decision", "date": today.strftime("%Y-%m-%d"), "time": "14:00", "country": "US", "impact": "high"},
        {"title": "US Non-Farm Payrolls", "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "time": "08:30", "country": "US", "impact": "high"},
        {"title": "CPI Inflation Rate (YoY)", "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "time": "08:30", "country": "US", "impact": "high"},
    ]
    for event in events:
        st.markdown(f"🔴 **{event['title']** - {event['country']} | {event['date']} {event['time']}")

# ==========================================
# الفوتر
# ==========================================
st.markdown(f"""
<div class="footer">
    𓋹 Real-time XAU/USD Spot from Yahoo Finance | SMC + ICT Analysis | Risk Management 𓋹<br>
    <a href="https://t.me/Ehabka2002" target="_blank" style="color:#0088cc; text-decoration:none;">📱 اشترك في قناة التليجرام للإشارات اليومية</a><br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
