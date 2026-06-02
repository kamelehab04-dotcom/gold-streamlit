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

# ==========================================
# إعدادات الصفحة
# ==========================================
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
    .mtf-bullish { color: #00ff88; }
    .mtf-bearish { color: #ff4444; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">PHARAOH GOLD DASHBOARD</div>
    <div class="main-subtitle">Gold Analysis Bot | SMC + ICT + Multi-Timeframe | Real-time Spot Price</div>
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
            Subscribe on Telegram for daily signals
        </a>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# إعدادات API
# ==========================================
GOLD_API_KEY = "goldapi-2262c60e69ce568bf76b982116077d1f-io"

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
                json.dump({"date": self.today, "pnl": self.daily_pnl, "trades": self.trades_today}, f)
        except:
            pass
    
    def reset_daily(self):
        self.daily_pnl = 0
        self.trades_today = 0
        self.save_daily_data()
    
    def can_trade(self):
        if self.daily_pnl <= -self.daily_max_loss:
            return False, f"Max daily loss reached (${self.daily_max_loss:,.2f})"
        if self.daily_pnl >= self.daily_max_profit:
            return False, f"Max daily profit reached (${self.daily_max_profit:,.2f})"
        if self.trades_today >= 10:
            return False, "Max 10 trades per day"
        return True, "You can trade"
    
    def get_recommended_lot(self, entry_price, stop_loss_price):
        stop_distance_pips = abs(entry_price - stop_loss_price)
        if stop_distance_pips > 0:
            return round(self.risk_per_trade / (stop_distance_pips * self.point_value_per_lot), 2)
        return 0
    
    def calculate_risk_per_trade(self, entry_price, stop_loss_price, lot_size):
        stop_distance_pips = abs(entry_price - stop_loss_price)
        return round(lot_size * stop_distance_pips * self.point_value_per_lot, 2)
    
    def get_trading_limits(self):
        remaining_loss = self.daily_max_loss + self.daily_pnl if self.daily_pnl < 0 else self.daily_max_loss
        return {
            "total_account": self.total_account,
            "trading_capital": self.trading_capital,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_percent": (self.daily_pnl / self.trading_capital) * 100,
            "daily_max_loss": self.daily_max_loss,
            "daily_max_profit": self.daily_max_profit,
            "profit_target": self.daily_profit_target,
            "remaining_loss": remaining_loss,
            "risk_per_trade": self.risk_per_trade,
            "trades_today": self.trades_today,
            "can_trade": self.can_trade()[0],
            "can_trade_message": self.can_trade()[1]
        }

risk_manager = RiskManager()
limits = risk_manager.get_trading_limits()

# ==========================================
# عرض لوحة المخاطر
# ==========================================
st.markdown("### Risk Management System")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Account", f"${limits['total_account']:,.0f}")
c2.metric("Trading Capital", f"${limits['trading_capital']:,.0f}", "10% of account")
c3.metric("Today's P&L", f"${limits['daily_pnl']:,.2f}", f"{limits['daily_pnl_percent']:+.2f}%")
c4.metric("Max Daily Loss", f"${limits['daily_max_loss']:,.0f}", "5% of capital")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Daily Target", f"${limits['profit_target']:,.0f}", "10%")
c2.metric("Max Daily Profit", f"${limits['daily_max_profit']:,.0f}", "12% max")
c3.metric("Risk Per Trade", f"${limits['risk_per_trade']:,.0f}", "1%")
c4.metric("Trades Today", f"{limits['trades_today']}/10")

if limits['can_trade']:
    st.success(limits['can_trade_message'])
else:
    st.error(limits['can_trade_message'])

st.markdown("---")

# ==========================================
# جلب البيانات
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
        df = gold.history(period="1mo", interval="1h")
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
# حساب المؤشرات الأساسية
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

def calc_macd(data):
    ema12 = data.ewm(span=12, adjust=False).mean()
    ema26 = data.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal, macd - signal

def calc_bollinger(data, period=20, std=2):
    sma = data.rolling(window=period).mean()
    std_dev = data.rolling(window=period).std()
    return sma + (std_dev * std), sma, sma - (std_dev * std)

def calc_adx(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.ewm(span=period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).ewm(span=period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(window=period).mean(), plus_di, minus_di

def calc_fib(high, low):
    diff = high - low
    return {
        '236': high - diff * 0.236,
        '382': high - diff * 0.382,
        '500': high - diff * 0.5,
        '618': high - diff * 0.618,
        '786': high - diff * 0.786
    }

# حساب المؤشرات
df['ema20'] = df['close'].ewm(span=20).mean()
df['ema50'] = df['close'].ewm(span=50).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger(df['close'])
df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df)
df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

# فيبوناتشي
recent_high = df['high'].iloc[-50:].max()
recent_low = df['low'].iloc[-50:].min()
fib = calc_fib(recent_high, recent_low)

# دعم ومقاومة
resistance = np.percentile(df['high'].iloc[-30:], 75)
support = np.percentile(df['low'].iloc[-30:], 25)

# القيم الحالية
current_rsi = df['rsi'].iloc[-1]
current_atr = df['atr'].iloc[-1]
current_adx = df['adx'].iloc[-1]
current_vwap = df['vwap'].iloc[-1]
current_bb_pos = (current_price - df['bb_lower'].iloc[-1]) / (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]) if df['bb_upper'].iloc[-1] != df['bb_lower'].iloc[-1] else 0.5
macd_bullish = df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]

# ==========================================
# Multi-Timeframe Analysis
# ==========================================
def get_tf_signal(tf):
    try:
        gold = yf.Ticker("GC=F")
        d = gold.history(period="1mo", interval=tf)
        if d.empty:
            return 0
        d.columns = [col.lower() for col in d.columns]
        d['ema20'] = d['close'].ewm(span=20).mean()
        d['rsi'] = calc_rsi(d['close'])
        latest = d.iloc[-1]
        score = 0
        if latest['close'] > latest['ema20']:
            score += 1
        if latest['rsi'] < 45:
            score += 1
        elif latest['rsi'] > 65:
            score -= 1
        return score
    except:
        return 0

tf_scores = {tf: get_tf_signal(tf) for tf in ["15m", "1h", "4h", "1d"]}
mtf_bullish = sum(1 for v in tf_scores.values() if v > 0)
mtf_bearish = sum(1 for v in tf_scores.values() if v < 0)
mtf_score = mtf_bullish - mtf_bearish

# ==========================================
# SMC / ICT Signals
# ==========================================
def detect_liquidity_sweep(df):
    recent_lows = df['low'].iloc[-20:-1].min()
    recent_highs = df['high'].iloc[-20:-1].max()
    return df['low'].iloc[-1] < recent_lows, df['high'].iloc[-1] > recent_highs

def detect_bos(df):
    return df['close'].iloc[-1] > df['high'].iloc[-6:-1].max(), df['close'].iloc[-1] < df['low'].iloc[-6:-1].min()

def detect_fvg(df):
    return df['low'].iloc[-1] > df['high'].iloc[-3], df['high'].iloc[-1] < df['low'].iloc[-3]

def detect_order_blocks(df):
    ob_bullish, ob_bearish = False, False
    for i in range(3, len(df)-1):
        if df['close'].iloc[i] > df['open'].iloc[i]:
            body = df['close'].iloc[i] - df['open'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                ob_bullish = True
        if df['close'].iloc[i] < df['open'].iloc[i]:
            body = df['open'].iloc[i] - df['close'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                ob_bearish = True
    return ob_bullish, ob_bearish

liquidity_bullish, liquidity_bearish = detect_liquidity_sweep(df)
bos_bullish, bos_bearish = detect_bos(df)
fvg_bullish, fvg_bearish = detect_fvg(df)
order_block_bullish, order_block_bearish = detect_order_blocks(df)
silver_bullet = liquidity_bullish and fvg_bullish and bos_bullish

# ==========================================
# نظام التسجيل
# ==========================================
bullish, bearish = 0, 0
signals = []

# RSI
if current_rsi < 45:
    bullish += 3
    signals.append(f"RSI: {current_rsi:.1f} (BUY)")
elif current_rsi > 65:
    bearish += 3
    signals.append(f"RSI: {current_rsi:.1f} (SELL)")
else:
    signals.append(f"RSI: {current_rsi:.1f} (NEUTRAL)")

# EMA
if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals.append("Price above EMA20")
else:
    bearish += 2
    signals.append("Price below EMA20")

# MACD
if macd_bullish:
    bullish += 2
    signals.append("MACD Positive")
else:
    bearish += 2
    signals.append("MACD Negative")

# Bollinger
if current_bb_pos < 0.1:
    bullish += 2
    signals.append("BB Lower Band (Oversold)")
elif current_bb_pos > 0.9:
    bearish += 2
    signals.append("BB Upper Band (Overbought)")

# Fibonacci
if current_price <= fib['382']:
    bullish += 2
    signals.append(f"Near Fib 38.2% (${fib['382']:.2f})")
if current_price >= fib['618']:
    bearish += 2
    signals.append(f"Near Fib 61.8% (${fib['618']:.2f})")

# ADX
if current_adx > 25:
    if current_price > df['ema20'].iloc[-1]:
        bullish += 2
        signals.append(f"ADX: {current_adx:.1f} (Strong Trend)")
    else:
        bearish += 2
        signals.append(f"ADX: {current_adx:.1f} (Strong Trend)")

# VWAP
if current_price > current_vwap:
    bullish += 1
    signals.append("Price above VWAP")
else:
    bearish += 1
    signals.append("Price below VWAP")

# Order Blocks
if order_block_bullish:
    bullish += 3
    signals.append("Bullish Order Block")
if order_block_bearish:
    bearish += 3
    signals.append("Bearish Order Block")

# FVG
if fvg_bullish:
    bullish += 2
    signals.append("Bullish FVG")
if fvg_bearish:
    bearish += 2
    signals.append("Bearish FVG")

# Liquidity Sweeps
if liquidity_bullish:
    bullish += 3
    signals.append("Liquidity Sweep Bullish")
if liquidity_bearish:
    bearish += 3
    signals.append("Liquidity Sweep Bearish")

# BOS
if bos_bullish:
    bullish += 2
    signals.append("BOS Bullish")
if bos_bearish:
    bearish += 2
    signals.append("BOS Bearish")

# Silver Bullet
if silver_bullet:
    bullish += 5
    signals.append("Silver Bullet (ICT) - Strong Signal")

# Support/Resistance
if current_price <= support + 5:
    bullish += 2
    signals.append(f"Near Support: ${support:.2f}")
if current_price >= resistance - 5:
    bearish += 2
    signals.append(f"Near Resistance: ${resistance:.2f}")

# Multi-Timeframe
if mtf_score >= 2:
    bullish += 4
    signals.append(f"MTF: {mtf_bullish}/4 timeframes bullish")
elif mtf_score <= -2:
    bearish += 4
    signals.append(f"MTF: {mtf_bearish}/4 timeframes bearish")

net = bullish - bearish

# الإشارة النهائية
if net >= 15:
    signal_type = "EXTREME STRONG BUY"
    signal_action = "BUY"
    confidence = 98
elif net >= 10:
    signal_type = "STRONG BUY"
    signal_action = "BUY"
    confidence = 90
elif net >= 5:
    signal_type = "BUY"
    signal_action = "BUY"
    confidence = 75
elif net <= -15:
    signal_type = "EXTREME STRONG SELL"
    signal_action = "SELL"
    confidence = 98
elif net <= -10:
    signal_type = "STRONG SELL"
    signal_action = "SELL"
    confidence = 90
elif net <= -5:
    signal_type = "SELL"
    signal_action = "SELL"
    confidence = 75
else:
    signal_type = "WAIT"
    signal_action = "NEUTRAL"
    confidence = 50

# ==========================================
# خطة التداول
# ==========================================
if signal_action == "BUY":
    entry = current_price
    stop_loss = support - (current_atr * 0.5)
    lot = risk_manager.get_recommended_lot(entry, stop_loss)
    risk_amt = risk_manager.calculate_risk_per_trade(entry, stop_loss, lot)
    targets = [resistance, resistance + (current_atr * 1.5), resistance + (current_atr * 3)]
elif signal_action == "SELL":
    entry = current_price
    stop_loss = resistance + (current_atr * 0.5)
    lot = risk_manager.get_recommended_lot(entry, stop_loss)
    risk_amt = risk_manager.calculate_risk_per_trade(entry, stop_loss, lot)
    targets = [support, support - (current_atr * 1.5), support - (current_atr * 3)]
else:
    entry, stop_loss, lot, risk_amt, targets = current_price, None, 0, 0, []

# التغير
change = current_price - df['close'].iloc[-2] if len(df) > 1 else 0
change_pct = (change / df['close'].iloc[-2]) * 100 if len(df) > 1 else 0

# ==========================================
# عرض السعر
# ==========================================
st.markdown(f"""
<div class="price-card">
    <div class="price-label">LIVE SPOT - XAU/USD (GOLDAPI.IO)</div>
    <div class="price-value">${current_price:,.2f}</div>
    <div class="price-change">{change:+.2f} ({change_pct:+.2f}%)</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# التبويبات
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["Market Analysis", "Indicators", "MTF & Levels", "SMC/ICT"])

with tab1:
    # بطاقات
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RSI", f"{current_rsi:.1f}")
    c2.metric("ATR", f"${current_atr:.2f}")
    c3.metric("ADX", f"{current_adx:.1f}")
    c4.metric("Net Score", f"{net:+d}")
    
    # الإشارة
    if signal_action == "BUY":
        st.success(f"### {signal_type} SIGNAL - Confidence: {confidence}%")
    elif signal_action == "SELL":
        st.error(f"### {signal_type} SIGNAL - Confidence: {confidence}%")
    else:
        st.warning(f"### {signal_type} - Confidence: {confidence}%")
    
    # اللوت
    if signal_action != "NEUTRAL" and limits['can_trade']:
        c1, c2 = st.columns(2)
        c1.metric("Recommended Lot Size", f"{lot:.2f} lots")
        c2.metric("Risk Amount", f"${risk_amt:.2f}")
    
    # الشارت
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        row_heights=[0.5, 0.25, 0.25])
    
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Price', line=dict(color='#ffd700')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='orange')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], mode='lines', name='BB Upper', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], mode='lines', name='BB Lower', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_hline(y=resistance, line_dash="dash", line_color="red", row=1, col=1, annotation_text="Resistance")
    fig.add_hline(y=support, line_dash="dash", line_color="green", row=1, col=1, annotation_text="Support")
    
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['macd'], mode='lines', name='MACD', line=dict(color='cyan')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], mode='lines', name='Signal', line=dict(color='yellow')), row=3, col=1)
    colors = ['red' if v < 0 else 'green' for v in df['macd_hist'].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], name='Histogram', marker_color=colors), row=3, col=1)
    
    fig.update_layout(template="plotly_dark", height=700)
    st.plotly_chart(fig, use_container_width=True)
    
    # خطة التداول
    if signal_action != "NEUTRAL" and limits['can_trade']:
        st.markdown("### Trading Plan")
        st.markdown(f"""
        | Level | Price |
        |-------|-------|
        | Entry | ${entry:.2f} |
        | Stop Loss | ${stop_loss:.2f} |
        | Target 1 | ${targets[0]:.2f} |
        | Target 2 | ${targets[1]:.2f} |
        | Target 3 | ${targets[2]:.2f} |
        """)
        rr = (targets[0] - entry) / (entry - stop_loss) if signal_action == "BUY" else (entry - targets[0]) / (stop_loss - entry)
        st.info(f"Risk/Reward Ratio: 1 : {rr:.2f}")

with tab2:
    st.markdown("### Advanced Indicators")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        - **MACD:** {'Bullish' if macd_bullish else 'Bearish'}
        - **Bollinger Position:** {current_bb_pos:.2f}
        - **ADX:** {current_adx:.1f} ({'Strong Trend' if current_adx > 25 else 'Weak Trend'})
        - **VWAP:** ${current_vwap:.2f}
        - **+DI:** {df['plus_di'].iloc[-1]:.1f}
        - **-DI:** {df['minus_di'].iloc[-1]:.1f}
        """)
    with c2:
        st.markdown(f"""
        - **ATR:** ${current_atr:.2f}
        - **RSI:** {current_rsi:.1f}
        - **Support:** ${support:.2f}
        - **Resistance:** ${resistance:.2f}
        - **Net Score:** {net:+d}
        - **Confidence:** {confidence}%
        """)
    
    st.markdown("#### Bollinger Bands")
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Price', line=dict(color='#ffd700')))
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], mode='lines', name='Upper', line=dict(color='gray', dash='dash')))
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], mode='lines', name='Middle', line=dict(color='blue')))
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], mode='lines', name='Lower', line=dict(color='gray', dash='dash')))
    fig_bb.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_bb, use_container_width=True)
    
    st.markdown("#### ADX (Trend Strength)")
    fig_adx = go.Figure()
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['adx'], mode='lines', name='ADX', line=dict(color='orange')))
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['plus_di'], mode='lines', name='+DI', line=dict(color='green')))
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['minus_di'], mode='lines', name='-DI', line=dict(color='red')))
    fig_adx.add_hline(y=25, line_dash="dash", line_color="gray")
    fig_adx.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_adx, use_container_width=True)

with tab3:
    st.markdown("### Multi-Timeframe Analysis")
    
    c1, c2, c3, c4 = st.columns(4)
    for tf, score in tf_scores.items():
        color = "#00ff88" if score > 0 else "#ff4444" if score < 0 else "#ffaa00"
        with eval(f"c{['1','2','3','4'][list(tf_scores.keys()).index(tf)]}"):
            st.markdown(f"""
            <div class="risk-card" style="text-align:center">
                <div style="font-size:1.5rem; font-weight:bold; color:{color}">{tf}</div>
                <div>{'BULLISH' if score > 0 else 'BEARISH' if score < 0 else 'NEUTRAL'}</div>
                <div>Score: {score:+d}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="risk-card">
        **Summary:** {mtf_bullish}/4 Bullish | {mtf_bearish}/4 Bearish | MTF Score: {mtf_score:+d}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Fibonacci Levels")
    st.markdown(f"""
    | Level | Price |
    |-------|-------|
    | 23.6% | ${fib['236']:.2f} |
    | 38.2% | ${fib['382']:.2f} |
    | 50.0% | ${fib['500']:.2f} |
    | 61.8% | ${fib['618']:.2f} |
    | 78.6% | ${fib['786']:.2f} |
    """)
    
    st.markdown("### Key Levels")
    st.markdown(f"""
    | Level | Price |
    |-------|-------|
    | Current Price | ${current_price:.2f} |
    | Resistance | ${resistance:.2f} |
    | Support | ${support:.2f} |
    | Recent High | ${recent_high:.2f} |
    | Recent Low | ${recent_low:.2f} |
    """)

with tab4:
    st.markdown("### SMC / ICT Signals")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="risk-card">
            **SMC Signals:**
            - Order Blocks: {'Bullish' if order_block_bullish else 'Bearish' if order_block_bearish else 'None'}
            - Fair Value Gaps: {'Bullish' if fvg_bullish else 'Bearish' if fvg_bearish else 'None'}
            - Liquidity Sweeps: {'Bullish' if liquidity_bullish else 'Bearish' if liquidity_bearish else 'None'}
            - Break of Structure: {'Bullish' if bos_bullish else 'Bearish' if bos_bearish else 'None'}
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="risk-card">
            **ICT Signals:**
            - Silver Bullet: {'Active' if silver_bullet else 'Inactive'}
            - Support: ${support:.2f}
            - Resistance: ${resistance:.2f}
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("All Technical Signals"):
        for s in signals:
            if "BUY" in s or "bullish" in s.lower() or "above" in s.lower():
                st.success(s)
            elif "SELL" in s or "bearish" in s.lower() or "below" in s.lower():
                st.error(s)
            else:
                st.info(s)

# ==========================================
# الفوتر
# ==========================================
st.markdown(f"""
<div class="footer">
    GoldAPI.io | SMC + ICT + MTF | Real-time Analysis
    <br>
    <a href="https://t.me/Ehabka2002" target="_blank" style="color:#0088cc;">Subscribe on Telegram</a>
    <br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
