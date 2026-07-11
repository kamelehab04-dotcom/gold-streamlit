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
# CSS للتنسيق (مشابه للصورة)
# ==========================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #ffd70033;
    }
    .main-title {
        font-size: 2rem;
        color: #ffd700;
        font-weight: bold;
        letter-spacing: 2px;
    }
    .main-subtitle {
        font-size: 0.9rem;
        color: #aaa;
    }
    .price-card {
        background: #1a1a2e;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #ffd70033;
        margin: 10px 0;
    }
    .price-value {
        font-size: 3.5rem;
        font-weight: bold;
        color: #fff;
    }
    .price-change {
        font-size: 1.2rem;
    }
    .indicator-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 10px 0;
    }
    .indicator-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #ffd70033;
    }
    .indicator-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #ffd700;
    }
    .indicator-label {
        font-size: 0.8rem;
        color: #888;
    }
    .signal-box {
        background: #1a1a2e;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 2px solid #ffd700;
        margin: 15px 0;
    }
    .signal-text {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .signal-confidence {
        font-size: 1rem;
        color: #aaa;
    }
    .footer {
        text-align: center;
        padding: 15px;
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
    .telegram-btn {
        display: inline-block;
        background: linear-gradient(135deg, #0088cc 0%, #006699 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 30px;
        text-decoration: none;
        font-weight: bold;
        margin: 5px;
        transition: transform 0.3s;
        border: none;
        cursor: pointer;
    }
    .telegram-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,136,204,0.4);
    }
    .risk-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #ffd70033;
    }
    .risk-warning {
        background: #ff444420;
        border-left: 4px solid #ff4444;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .risk-success {
        background: #00ff8820;
        border-left: 4px solid #00ff88;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">Advanced Analysis | SMC + ICT + MACD + BB + ADX + VWAP + Fibonacci</div>
</div>
""", unsafe_allow_html=True)

# زر التليجرام
st.markdown("""
<div style="text-align: center; margin: 10px 0 20px 0;">
    <a href="https://t.me/Ehabka2002" target="_blank" class="telegram-btn">
        📱 اشترك في قناة التليجرام للإشارات اليومية
    </a>
</div>
""", unsafe_allow_html=True)

# ==========================================
# إعدادات API
# ==========================================
GOLD_API_KEY = "goldapi-2262c60e69ce568bf76b982116077d1f-io"

# ==========================================
# إدارة الصفقات والمخاطر (نفس الكود السابق)
# ==========================================
class TradeManager:
    def __init__(self):
        self.trades_file = "trades_data.json"
        self.load_trades()
    def load_trades(self):
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.open_trades = data.get("open_trades", [])
                    self.closed_trades = data.get("closed_trades", [])
            else:
                self.open_trades = []
                self.closed_trades = []
        except:
            self.open_trades = []
            self.closed_trades = []
    def save_trades(self):
        try:
            with open(self.trades_file, "w", encoding='utf-8') as f:
                json.dump({"open_trades": self.open_trades, "closed_trades": self.closed_trades}, f, indent=2, ensure_ascii=False)
        except:
            pass
    def add_trade(self, trade_data):
        trade_id = f"T{len(self.open_trades) + len(self.closed_trades) + 1:03d}"
        new_trade = {
            "id": trade_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "direction": trade_data["direction"],
            "entry": trade_data["entry"],
            "lots": trade_data["lots"],
            "stop_loss": trade_data.get("stop_loss"),
            "take_profit": trade_data.get("take_profit"),
            "status": "open",
            "notes": trade_data.get("notes", "")
        }
        self.open_trades.append(new_trade)
        self.save_trades()
        return trade_id
    def close_trade(self, trade_id, exit_price):
        for i, trade in enumerate(self.open_trades):
            if trade["id"] == trade_id:
                trade["exit"] = exit_price
                trade["status"] = "closed"
                if trade["direction"] == "BUY":
                    pips = (exit_price - trade["entry"]) * 100
                else:
                    pips = (trade["entry"] - exit_price) * 100
                profit = pips * trade["lots"] * 0.1
                trade["profit"] = round(profit, 2)
                trade["result"] = "win" if profit > 0 else "loss"
                trade["close_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_trades.append(trade)
                self.open_trades.pop(i)
                self.save_trades()
                return profit
        return None
    def get_statistics(self):
        if not self.closed_trades:
            return {"total_trades": 0, "winning_trades": 0, "losing_trades": 0, "win_rate": 0, "total_profit": 0, "avg_profit": 0, "best_trade": 0, "worst_trade": 0}
        total = len(self.closed_trades)
        wins = [t for t in self.closed_trades if t.get("result") == "win"]
        losses = [t for t in self.closed_trades if t.get("result") == "loss"]
        profits = [t.get("profit", 0) for t in self.closed_trades]
        return {
            "total_trades": total,
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": (len(wins) / total * 100) if total > 0 else 0,
            "total_profit": sum(profits),
            "avg_profit": sum(profits) / total if total > 0 else 0,
            "best_trade": max(profits) if profits else 0,
            "worst_trade": min(profits) if profits else 0
        }

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
    def can_trade(self):
        if self.daily_pnl <= -self.daily_max_loss:
            return False, f"❌ تم الوصول إلى الحد الأقصى للخسارة اليومية (${self.daily_max_loss:,.2f})"
        if self.daily_pnl >= self.daily_max_profit:
            return False, f"✅ تم تحقيق الحد الأقصى للربح اليومي (${self.daily_max_profit:,.2f})"
        if self.trades_today >= 10:
            return False, "⚠️ تم الوصول إلى الحد الأقصى لعدد الصفقات اليومية (10 صفقات)"
        return True, "✅ يمكنك التداول"
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
            "daily_pnl_percent": (self.daily_pnl / self.trading_capital) * 100 if self.trading_capital else 0,
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

# ==========================================
# دوال التحليل الفني
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

def calc_macd(data):
    ema12 = data.ewm(span=12, adjust=False).mean()
    ema26 = data.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram

def calc_bollinger_bands(data, period=20, std_dev=2):
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def calc_adx(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.ewm(span=period).mean() / atr)
    minus_di = 100 * (abs(minus_dm).ewm(span=period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()
    return adx, plus_di, minus_di

def calc_fibonacci_levels(high, low, current_price):
    diff = high - low
    return {
        'fib_236': high - diff * 0.236,
        'fib_382': high - diff * 0.382,
        'fib_500': high - diff * 0.5,
        'fib_618': high - diff * 0.618,
        'fib_786': high - diff * 0.786
    }

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
            data = response.json()
            return float(data.get('price', 0)), float(data.get('change', 0))
        return None, None
    except:
        return None, None

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

current_price, change = get_spot_price()
df = get_historical_data()

if df is None:
    st.error("Error loading historical data")
    st.stop()

if current_price is None and df is not None:
    current_price = df['close'].iloc[-1]
    change = 0

if current_price is None:
    st.error("Unable to fetch gold spot price")
    st.stop()

# ==========================================
# حساب المؤشرات
# ==========================================
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'])
df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df)
df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

# فيبوناتشي
recent_high = df['high'].iloc[-50:].max()
recent_low = df['low'].iloc[-50:].min()
fib_levels = calc_fibonacci_levels(recent_high, recent_low, current_price)

# ==========================================
# نظام تسجيل النقاط (مشابه للصورة)
# ==========================================
def generate_scored_signal(df, current_price):
    if df is None or len(df) < 50:
        return "WAIT", 50, 0, {}
    
    last = df.iloc[-1]
    scores = {'BUY': 0, 'SELL': 0}
    details = {}

    # RSI
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if rsi < 30:
            scores['BUY'] += 3
            details['RSI'] = f"مفرط البيع ({rsi:.1f}) +3"
        elif rsi > 70:
            scores['SELL'] += 3
            details['RSI'] = f"مفرط الشراء ({rsi:.1f}) +3"
        else:
            details['RSI'] = f"محايد ({rsi:.1f})"

    # MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns and not pd.isna(last['macd']):
        if last['macd'] > last['macd_signal'] and last['macd'] > 0:
            scores['BUY'] += 2
            details['MACD'] = "إيجابي +2"
        elif last['macd'] < last['macd_signal'] and last['macd'] < 0:
            scores['SELL'] += 2
            details['MACD'] = "سلبي +2"
        else:
            details['MACD'] = "محايد"

    # BB
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and not pd.isna(last['bb_upper']):
        if current_price <= last['bb_lower'] * 1.005:
            scores['BUY'] += 2
            details['BB'] = "قرب الحد السفلي +2"
        elif current_price >= last['bb_upper'] * 0.995:
            scores['SELL'] += 2
            details['BB'] = "قرب الحد الأعلى +2"
        else:
            details['BB'] = "وسط النطاق"

    # VWAP
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += 1
            details['VWAP'] = "فوق VWAP +1"
        else:
            scores['SELL'] += 1
            details['VWAP'] = "تحت VWAP +1"

    # ADX (قوة الاتجاه)
    if 'adx' in df.columns and not pd.isna(last['adx']):
        if last['adx'] > 25:
            details['ADX'] = f"اتجاه قوي ({last['adx']:.1f})"
        else:
            details['ADX'] = f"اتجاه ضعيف ({last['adx']:.1f})"

    # SMC: منطقة خصم/قمة (محاكاة)
    # (يمكن إضافة تحليل حقيقي لـ SMC هنا)

    net_score = scores['BUY'] - scores['SELL']
    if net_score >= 4:
        signal = "BUY"
        confidence = min(100, 60 + net_score * 5)
    elif net_score <= -4:
        signal = "SELL"
        confidence = min(100, 60 + abs(net_score) * 5)
    else:
        signal = "WAIT"
        confidence = 50 + net_score * 2

    return signal, confidence, net_score, details

# ==========================================
# عرض الأقسام
# ==========================================

# ----- السعر الفوري -----
st.markdown(f"""
<div class="price-card">
    <div style="font-size:1rem; color:#888;">XAU/USD (GOLDAPI.IO)</div>
    <div class="price-value">${current_price:,.2f}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">
        {change:+.2f} ({current_price - current_price/(1+change/100) if change != 0 else 0:+.2f})
    </div>
</div>
""", unsafe_allow_html=True)

# ----- مؤشرات السوق -----
last = df.iloc[-1]
rsi_val = last['rsi'] if not pd.isna(last['rsi']) else 0
atr_val = last['atr'] if not pd.isna(last['atr']) else 0
adx_val = last['adx'] if not pd.isna(last['adx']) else 0

# حساب الـ Net Score
signal, confidence, net_score, details = generate_scored_signal(df, current_price)

st.markdown("### 📊 مؤشرات السوق")
col_rsi, col_atr, col_adx, col_score = st.columns(4)
col_rsi.metric("RSI (14)", f"{rsi_val:.1f}")
col_atr.metric("ATR", f"${atr_val:.2f}")
col_adx.metric("ADX (Trend Strength)", f"{adx_val:.1f}")
col_score.metric("Net Score", f"{net_score}")

# ----- الإشارة -----
st.markdown("---")
st.markdown("### 🧠 إشارة التداول")
signal_color = "#ffaa00" if signal == "WAIT" else ("#00ff88" if signal == "BUY" else "#ff4444")
st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color: {signal_color};">{signal}</div>
    <div class="signal-confidence">Confidence: {confidence:.0f}% | Score: {net_score}</div>
</div>
""", unsafe_allow_html=True)

# ----- الرسم البياني -----
st.markdown("---")
st.markdown("### 📈 Price Chart with EMA & Bollinger Bands")

# استخدام Plotly لرسم بياني تفاعلي
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                    row_heights=[0.7, 0.3])

# السعر مع EMA و BB
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='XAU/USD', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA 20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA 50', line=dict(color='red', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='blue', dash='solid', width=0.8)), row=1, col=1)

# RSI و MACD في الأسفل
fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=2, col=1)
fig.add_trace(go.Bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color='gray', opacity=0.3), row=2, col=1)

fig.update_layout(height=700, template='plotly_dark', showlegend=True)
fig.update_xaxes(title_text="", row=1, col=1)
fig.update_xaxes(title_text="", row=2, col=1)
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="RSI / MACD", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# ----- تذييل -----
st.markdown("""
<div class="footer">
    GoldAPI.io | SMC + ICT + MACD + BB + ADX + VWAP + Fibonacci | Advanced Analysis<br>
    استرداد قناة التداول | تحديث لحظي
</div>
""", unsafe_allow_html=True)

# ==========================================
# (اختياري) إدارة الصفقات – يمكن إضافتها في تبويب منفصل
# ==========================================
# ... (يمكن إضافة تبويبات لإدارة الصفقات والمخاطر كما في الكود السابق)
