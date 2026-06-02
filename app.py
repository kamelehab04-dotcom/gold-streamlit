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
    .trade-row {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid;
    }
    .trade-win {
        border-left-color: #00ff88;
    }
    .trade-loss {
        border-left-color: #ff4444;
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
    <div class="main-subtitle">بوت تحليل الذهب الفرعوني | SMC + ICT + Advanced Indicators</div>
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
# إعدادات API
# ==========================================
GOLD_API_KEY = "goldapi-2262c60e69ce568bf76b982116077d1f-io"

# ==========================================
# نظام إدارة الصفقات (TRADE MANAGER)
# ==========================================

class TradeManager:
    def __init__(self):
        self.trades_file = "trades_data.json"
        self.load_trades()
    
    def load_trades(self):
        """تحميل الصفقات من الملف"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.open_trades = data.get("open_trades", [])
                    self.closed_trades = data.get("closed_trades", [])
            else:
                self.open_trades = []
                self.closed_trades = []
                # إضافة بعض الصفقات التجريبية
                self.add_demo_trades()
        except Exception as e:
            self.open_trades = []
            self.closed_trades = []
            self.add_demo_trades()
    
    def add_demo_trades(self):
        """إضافة صفقات تجريبية للعرض"""
        demo_trades = [
            {
                "id": "T001",
                "date": "2024-01-15 10:30:00",
                "direction": "BUY",
                "entry": 2030.50,
                "exit": 2045.20,
                "lots": 0.25,
                "status": "closed",
                "profit": 367.50,
                "result": "win",
                "notes": "اختراق مقاومة قوية"
            },
            {
                "id": "T002",
                "date": "2024-01-16 14:15:00",
                "direction": "SELL",
                "entry": 2048.30,
                "exit": 2040.10,
                "lots": 0.30,
                "status": "closed",
                "profit": 246.00,
                "result": "win",
                "notes": "ارتداد من فيبوناتشي 61.8%"
            },
            {
                "id": "T003",
                "date": "2024-01-17 09:45:00",
                "direction": "BUY",
                "entry": 2035.00,
                "exit": 2028.50,
                "lots": 0.20,
                "status": "closed",
                "profit": -130.00,
                "result": "loss",
                "notes": "ضرب الاستوب لوز"
            },
            {
                "id": "T004",
                "date": "2024-01-18 11:00:00",
                "direction": "BUY",
                "entry": 2025.00,
                "lots": 0.35,
                "stop_loss": 2018.00,
                "take_profit": 2040.00,
                "status": "open",
                "notes": "صفقة مفتوحة حالياً"
            }
        ]
        for trade in demo_trades:
            if trade["status"] == "open":
                self.open_trades.append(trade)
            else:
                self.closed_trades.append(trade)
        self.save_trades()
    
    def save_trades(self):
        """حفظ الصفقات في الملف"""
        try:
            with open(self.trades_file, "w", encoding='utf-8') as f:
                json.dump({
                    "open_trades": self.open_trades,
                    "closed_trades": self.closed_trades
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
    
    def add_trade(self, trade_data):
        """إضافة صفقة جديدة"""
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
        """إغلاق صفقة"""
        for i, trade in enumerate(self.open_trades):
            if trade["id"] == trade_id:
                trade["exit"] = exit_price
                trade["status"] = "closed"
                
                # حساب الربح/الخسارة
                if trade["direction"] == "BUY":
                    pips = (exit_price - trade["entry"]) * 100  # تحويل إلى بيبس
                else:
                    pips = (trade["entry"] - exit_price) * 100
                
                profit = pips * trade["lots"] * 0.1  # تقريبي لكل لوت = 10$ لكل بيب
                trade["profit"] = round(profit, 2)
                trade["result"] = "win" if profit > 0 else "loss"
                trade["close_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                self.closed_trades.append(trade)
                self.open_trades.pop(i)
                self.save_trades()
                return profit
        return None
    
    def delete_trade(self, trade_id, is_open=True):
        """حذف صفقة"""
        if is_open:
            self.open_trades = [t for t in self.open_trades if t["id"] != trade_id]
        else:
            self.closed_trades = [t for t in self.closed_trades if t["id"] != trade_id]
        self.save_trades()
    
    def get_statistics(self):
        """الحصول على إحصائيات الصفقات"""
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "total_profit": 0,
                "avg_profit": 0,
                "best_trade": 0,
                "worst_trade": 0
            }
        
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.get("result") == "win"]
        losing_trades = [t for t in self.closed_trades if t.get("result") == "loss"]
        profits = [t.get("profit", 0) for t in self.closed_trades]
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0,
            "total_profit": sum(profits),
            "avg_profit": sum(profits) / total_trades if total_trades > 0 else 0,
            "best_trade": max(profits) if profits else 0,
            "worst_trade": min(profits) if profits else 0
        }

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

risk_manager = RiskManager()
trade_manager = TradeManager()
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
# تحليل الذهب (جميع الأدوات المتقدمة)
# ==========================================

@st.cache_data(ttl=10)
def get_spot_price():
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
    try:
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1mo", interval="1h")
        if df.empty:
            return None
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return None

# جلب البيانات
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

# ==========================================
# حساب المؤشرات المتقدمة
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

def detect_fvg(df):
    fvgs = []
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            fvgs.append(('bullish', df['high'].iloc[i-2], df['low'].iloc[i]))
        if df['high'].iloc[i] < df['low'].iloc[i-2]:
            fvgs.append(('bearish', df['low'].iloc[i-2], df['high'].iloc[i]))
    return fvgs

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

def detect_bos(df):
    bos_list = []
    for i in range(5, len(df)):
        if df['close'].iloc[i] > df['high'].iloc[i-5:i].max():
            bos_list.append(('bullish', df['close'].iloc[i]))
        if df['close'].iloc[i] < df['low'].iloc[i-5:i].min():
            bos_list.append(('bearish', df['close'].iloc[i]))
    return bos_list

def detect_market_structure_shift(df):
    mss_list = []
    for i in range(3, len(df)):
        if df['bos_bearish'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[i-2:i].max():
            mss_list.append(('bullish', df['close'].iloc[i]))
        if df['bos_bullish'].iloc[i-1] and df['close'].iloc[i] < df['low'].iloc[i-2:i].min():
            mss_list.append(('bearish', df['close'].iloc[i]))
    return mss_list

def detect_silver_bullet(df):
    for i in range(3, len(df)):
        if df['liquidity_sweep_bullish'].iloc[i-1] and df['fvg_bullish'].iloc[i] and df['mss_bullish'].iloc[i]:
            return True
    return False

# حساب المؤشرات
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

# SMC/ICT
df['liquidity_sweep_bullish'] = False
df['liquidity_sweep_bearish'] = False
df['bos_bullish'] = False
df['bos_bearish'] = False
df['fvg_bullish'] = False
df['fvg_bearish'] = False

sweeps = detect_liquidity_sweeps(df)
for sweep in sweeps:
    if sweep[0] == 'bullish':
        df.loc[df.index[-1], 'liquidity_sweep_bullish'] = True
    else:
        df.loc[df.index[-1], 'liquidity_sweep_bearish'] = True

bos_list = detect_bos(df)
for bos in bos_list:
    if bos[0] == 'bullish':
        df.loc[df.index[-1], 'bos_bullish'] = True
    else:
        df.loc[df.index[-1], 'bos_bearish'] = True

fvgs = detect_fvg(df)
for fvg in fvgs:
    if fvg[0] == 'bullish':
        df.loc[df.index[-1], 'fvg_bullish'] = True
    else:
        df.loc[df.index[-1], 'fvg_bearish'] = True

# الدعم والمقاومة
resistance = np.percentile(df['high'].iloc[-30:], 75) if len(df) >= 30 else current_price + 20
support = np.percentile(df['low'].iloc[-30:], 25) if len(df) >= 30 else current_price - 20

# Order Blocks
order_blocks = detect_order_blocks(df)
order_block_bullish = any(ob[0] == 'bullish' for ob in order_blocks[-5:])
order_block_bearish = any(ob[0] == 'bearish' for ob in order_blocks[-5:])

# ICT
silver_bullet = detect_silver_bullet(df)
mss_list = detect_market_structure_shift(df)
mss_bullish = any(mss[0] == 'bullish' for mss in mss_list[-3:])
mss_bearish = any(mss[0] == 'bearish' for mss in mss_list[-3:])

# القيم الحالية
current_rsi = df['rsi'].iloc[-1] if not pd.isna(df['rsi'].iloc[-1]) else 50
current_atr = df['atr'].iloc[-1] if not pd.isna(df['atr'].iloc[-1]) else 20
current_macd = df['macd'].iloc[-1] if not pd.isna(df['macd'].iloc[-1]) else 0
current_macd_signal = df['macd_signal'].iloc[-1] if not pd.isna(df['macd_signal'].iloc[-1]) else 0
current_bb_position = (current_price - df['bb_lower'].iloc[-1]) / (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1]) if not pd.isna(df['bb_upper'].iloc[-1]) else 0.5
current_adx = df['adx'].iloc[-1] if not pd.isna(df['adx'].iloc[-1]) else 20
current_vwap = df['vwap'].iloc[-1] if not pd.isna(df['vwap'].iloc[-1]) else current_price

liquidity_sweep_bullish = df['liquidity_sweep_bullish'].iloc[-1] if 'liquidity_sweep_bullish' in df.columns else False
liquidity_sweep_bearish = df['liquidity_sweep_bearish'].iloc[-1] if 'liquidity_sweep_bearish' in df.columns else False
bos_bullish = df['bos_bullish'].iloc[-1] if 'bos_bullish' in df.columns else False
bos_bearish = df['bos_bearish'].iloc[-1] if 'bos_bearish' in df.columns else False
fvg_bullish = df['fvg_bullish'].iloc[-1] if 'fvg_bullish' in df.columns else False
fvg_bearish = df['fvg_bearish'].iloc[-1] if 'fvg_bearish' in df.columns else False

# نظام التسجيل المتقدم
bullish = 0
bearish = 0
signals = []

# 1. RSI (3 نقاط)
if current_rsi < 45:
    bullish += 3
    signals.append(f"✅ RSI: {current_rsi:.1f} (BUY ZONE)")
elif current_rsi > 65:
    bearish += 3
    signals.append(f"⚠️ RSI: {current_rsi:.1f} (SELL ZONE)")
else:
    signals.append(f"📊 RSI: {current_rsi:.1f} (NEUTRAL)")

# 2. EMA (2 نقاط)
if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals.append("📈 Price above EMA20")
else:
    bearish += 2
    signals.append("📉 Price below EMA20")

# 3. MACD (2 نقاط)
if current_macd > current_macd_signal:
    bullish += 2
    signals.append("🟢 MACD Positive")
else:
    bearish += 2
    signals.append("🔴 MACD Negative")

# 4. Bollinger Bands (2 نقاط)
if current_bb_position < 0.1:
    bullish += 2
    signals.append("📊 BB Lower Band (Oversold)")
elif current_bb_position > 0.9:
    bearish += 2
    signals.append("📊 BB Upper Band (Overbought)")

# 5. Fibonacci (2 نقاط)
if current_price <= fib_levels['fib_382']:
    bullish += 2
    signals.append(f"📐 Near Fib 38.2% (${fib_levels['fib_382']:.2f})")
if current_price >= fib_levels['fib_618']:
    bearish += 2
    signals.append(f"📐 Near Fib 61.8% (${fib_levels['fib_618']:.2f})")

# 6. ADX (2 نقاط - قوة الاتجاه)
if current_adx > 25:
    if current_price > df['ema20'].iloc[-1]:
        bullish += 2
        signals.append(f"💪 ADX: {current_adx:.1f} (Strong Trend)")
    else:
        bearish += 2
        signals.append(f"💪 ADX: {current_adx:.1f} (Strong Trend)")

# 7. VWAP (1 نقطة)
if current_price > current_vwap:
    bullish += 1
    signals.append("💰 Price above VWAP")
else:
    bearish += 1
    signals.append("💰 Price below VWAP")

# 8. Order Blocks (3 نقاط)
if order_block_bullish:
    bullish += 3
    signals.append("🏛️ Bullish Order Block")
if order_block_bearish:
    bearish += 3
    signals.append("🏛️ Bearish Order Block")

# 9. Fair Value Gaps (2 نقاط)
if fvg_bullish:
    bullish += 2
    signals.append("📉 Bullish FVG")
if fvg_bearish:
    bearish += 2
    signals.append("📈 Bearish FVG")

# 10. Liquidity Sweeps (3 نقاط)
if liquidity_sweep_bullish:
    bullish += 3
    signals.append("🎯 Liquidity Sweep Bullish")
if liquidity_sweep_bearish:
    bearish += 3
    signals.append("🎯 Liquidity Sweep Bearish")

# 11. Break of Structure (2 نقاط)
if bos_bullish:
    bullish += 2
    signals.append("🚀 BOS Bullish")
if bos_bearish:
    bearish += 2
    signals.append("🚀 BOS Bearish")

# 12. Market Structure Shift (3 نقاط - ICT)
if mss_bullish:
    bullish += 3
    signals.append("🔄 MSS Bullish (ICT)")
if mss_bearish:
    bearish += 3
    signals.append("🔄 MSS Bearish (ICT)")

# 13. Silver Bullet (5 نقاط - ICT)
if silver_bullet:
    bullish += 5
    signals.append("🔫 Silver Bullet (ICT) - Strong Signal")

# 14. الدعم/المقاومة (2 نقاط)
if current_price <= support + 5:
    bullish += 2
    signals.append(f"📍 Near Support: ${support:.2f}")
if current_price >= resistance - 5:
    bearish += 2
    signals.append(f"📍 Near Resistance: ${resistance:.2f}")

net = bullish - bearish

# الإشارة النهائية
if net >= 15:
    signal_type = "🔴🔴🔴 EXTREME STRONG BUY 🔴🔴🔴"
    signal_action = "BUY"
    confidence = 98
    signal_color = "#00ff88"
elif net >= 10:
    signal_type = "🔴🔴 STRONG BUY 🔴🔴"
    signal_action = "BUY"
    confidence = 90
    signal_color = "#00ff88"
elif net >= 5:
    signal_type = "🟢 BUY 🟢"
    signal_action = "BUY"
    confidence = 75
    signal_color = "#00ff88"
elif net <= -15:
    signal_type = "🔴🔴🔴 EXTREME STRONG SELL 🔴🔴🔴"
    signal_action = "SELL"
    confidence = 98
    signal_color = "#ff4444"
elif net <= -10:
    signal_type = "🔴🔴 STRONG SELL 🔴🔴"
    signal_action = "SELL"
    confidence = 90
    signal_color = "#ff4444"
elif net <= -5:
    signal_type = "🔴 SELL 🔴"
    signal_action = "SELL"
    confidence = 75
    signal_color = "#ff4444"
else:
    signal_type = "🟡 WAIT 🟡"
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

# التغير
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
        <span class="live-badge">LIVE SPOT</span> 𓋹 XAU/USD (GOLDAPI.IO) 𓋹
    </div>
    <div class="price-value">${current_price:,.2f}</div>
    <div class="price-change" style="color:{change_color}">{change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# التبويبات (مع إضافة تبويب الصفقات)
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Market Analysis", "📈 Advanced Indicators", "📐 Fibonacci & Levels", "🔬 SMC/ICT Details", "📝 Trade Journal"])

with tab1:
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
            <div class="indicator-value" style="color:#ffd700">{current_adx:.1f}</div>
            <div class="indicator-label">ADX (Trend Strength)</div>
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
        
        lot_options = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.00]
        lot_data = []
        for lot in lot_options:
            risk = risk_manager.calculate_risk_per_trade(entry, stop_loss, lot)
            lot_data.append({"Lot": f"{lot:.2f}", "Risk ($)": f"${risk:.2f}", "Risk %": f"{(risk / risk_manager.trading_capital) * 100:.2f}%"})
        st.dataframe(pd.DataFrame(lot_data), use_container_width=True, hide_index=True)
    
    # الشارت المتقدم (3 أقسام)
    st.markdown("### 📈 Price Chart")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, 
                        row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=("Price with EMA & Bollinger", "RSI", "MACD"))
    
    # السعر والمتوسطات
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='XAU/USD', line=dict(color='#ffd700', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='#ff9f4a')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='#4a9eff')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], mode='lines', name='BB Upper', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], mode='lines', name='BB Lower', line=dict(color='gray', dash='dash')), row=1, col=1)
    fig.add_hline(y=resistance, line_dash="dash", line_color="#ff4444", row=1, col=1, annotation_text="Resistance")
    fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", row=1, col=1, annotation_text="Support")
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], mode='lines', name='RSI', line=dict(color='#9b59b6')), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", row=2, col=1, annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", row=2, col=1, annotation_text="Oversold")
    
    # MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['macd'], mode='lines', name='MACD', line=dict(color='cyan')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], mode='lines', name='Signal', line=dict(color='yellow')), row=3, col=1)
    colors = ['red' if val < 0 else 'green' for val in df['macd_histogram'].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color=colors), row=3, col=1)
    
    fig.update_layout(template="plotly_dark", height=700)
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

with tab2:
    st.markdown("### 📈 Advanced Indicators")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="risk-card">
            <b>📊 MACD:</b> {'Bullish' if current_macd > current_macd_signal else 'Bearish'}<br>
            <b>📊 Bollinger Position:</b> {current_bb_position:.2f}<br>
            <b>📊 ADX (Trend):</b> {current_adx:.1f} - {'Strong Trend' if current_adx > 25 else 'Weak Trend'}<br>
            <b>💰 VWAP:</b> ${current_vwap:.2f}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="risk-card">
            <b>📈 +DI:</b> {df['plus_di'].iloc[-1]:.1f}<br>
            <b>📉 -DI:</b> {df['minus_di'].iloc[-1]:.1f}<br>
            <b>📊 ATR:</b> ${current_atr:.2f}<br>
            <b>📊 RSI:</b> {current_rsi:.1f}
        </div>
        """, unsafe_allow_html=True)
    
    # Bollinger Bands Chart
    st.markdown("#### 📊 Bollinger Bands")
    fig_bb = go.Figure()
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Price', line=dict(color='#ffd700')))
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], mode='lines', name='Upper Band', line=dict(color='gray', dash='dash')))
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], mode='lines', name='Middle Band', line=dict(color='blue')))
    fig_bb.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], mode='lines', name='Lower Band', line=dict(color='gray', dash='dash')))
    fig_bb.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_bb, use_container_width=True)
    
    # ADX Chart
    st.markdown("#### 📊 ADX (Trend Strength)")
    fig_adx = go.Figure()
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['adx'], mode='lines', name='ADX', line=dict(color='orange')))
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['plus_di'], mode='lines', name='+DI', line=dict(color='green')))
    fig_adx.add_trace(go.Scatter(x=df.index, y=df['minus_di'], mode='lines', name='-DI', line=dict(color='red')))
    fig_adx.add_hline(y=25, line_dash="dash", line_color="gray", annotation_text="Strong Trend Threshold")
    fig_adx.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_adx, use_container_width=True)

with tab3:
    st.markdown("### 📐 Fibonacci & Key Levels")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📈 Fibonacci Retracement")
        st.markdown(f"""
        <div class="targets-table">
            <div class="target-row"><span class="target-label">23.6%</span><span class="target-value">${fib_levels['fib_236']:.2f}</span></div>
            <div class="target-row"><span class="target-label">38.2%</span><span class="target-value">${fib_levels['fib_382']:.2f}</span></div>
            <div class="target-row"><span class="target-label">50.0%</span><span class="target-value">${fib_levels['fib_500']:.2f}</span></div>
            <div class="target-row"><span class="target-label">61.8%</span><span class="target-value">${fib_levels['fib_618']:.2f}</span></div>
            <div class="target-row"><span class="target-label">78.6%</span><span class="target-value">${fib_levels['fib_786']:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 🎯 Key Levels")
        st.markdown(f"""
        <div class="targets-table">
            <div class="target-row"><span class="target-label">Current Price</span><span class="target-value">${current_price:.2f}</span></div>
            <div class="target-row"><span class="target-label">Resistance</span><span class="target-value">${resistance:.2f}</span></div>
            <div class="target-row"><span class="target-label">Support</span><span class="target-value">${support:.2f}</span></div>
            <div class="target-row"><span class="target-label">Recent High</span><span class="target-value">${recent_high:.2f}</span></div>
            <div class="target-row"><span class="target-label">Recent Low</span><span class="target-value">${recent_low:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    # VWAP Chart
    st.markdown("#### 💰 VWAP (Volume Weighted Average Price)")
    fig_vwap = go.Figure()
    fig_vwap.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Price', line=dict(color='#ffd700')))
    fig_vwap.add_trace(go.Scatter(x=df.index, y=df['vwap'], mode='lines', name='VWAP', line=dict(color='cyan')))
    fig_vwap.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_vwap, use_container_width=True)

with tab4:
    st.markdown("### 🔬 SMC / ICT Details")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="risk-card">
            <b>🏛️ SMC Signals:</b><br>
            • Order Blocks: {'Bullish' if order_block_bullish else 'Bearish' if order_block_bearish else 'None'}<br>
            • Fair Value Gaps: {'Bullish' if fvg_bullish else 'Bearish' if fvg_bearish else 'None'}<br>
            • Liquidity Sweeps: {'Bullish' if liquidity_sweep_bullish else 'Bearish' if liquidity_sweep_bearish else 'None'}<br>
            • Break of Structure: {'Bullish' if bos_bullish else 'Bearish' if bos_bearish else 'None'}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="risk-card">
            <b>🎯 ICT Signals:</b><br>
            • MSS (Market Structure Shift): {'Bullish' if mss_bullish else 'Bearish' if mss_bearish else 'None'}<br>
            • Silver Bullet: {'✅ Active' if silver_bullet else '❌ Inactive'}<br>
            • Support: ${support:.2f}<br>
            • Resistance: ${resistance:.2f}
        </div>
        """, unsafe_allow_html=True)
    
    # جميع الإشارات
    with st.expander("📋 All Technical Signals"):
        for s in signals:
            if "✅" in s or "📈" in s or "🟢" in s:
                st.success(s)
            elif "⚠️" in s or "📉" in s or "🔴" in s:
                st.error(s)
            else:
                st.info(s)

# ==========================================
# TAB 5: TRADE JOURNAL - الصفقات
# ==========================================
with tab5:
    st.markdown("### 📝 Trade Journal")
    st.markdown("---")
    
    # إحصائيات الأداء
    stats = trade_manager.get_statistics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📊 Total Trades", stats["total_trades"])
    with col2:
        st.metric("✅ Win Rate", f"{stats['win_rate']:.1f}%")
    with col3:
        st.metric("💰 Total P&L", f"${stats['total_profit']:,.2f}")
    with col4:
        st.metric("🏆 Best Trade", f"${stats['best_trade']:.2f}")
    with col5:
        st.metric("💀 Worst Trade", f"${stats['worst_trade']:.2f}")
    
    st.markdown("---")
    
    # إضافة صفقة جديدة
    with st.expander("➕ ADD NEW TRADE", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            trade_direction = st.selectbox("Direction", ["BUY", "SELL"], key="trade_dir")
            trade_entry = st.number_input("Entry Price", value=current_price, step=1.0, format="%.2f", key="trade_entry")
            trade_lots = st.number_input("Lot Size", value=0.25, step=0.05, format="%.2f", key="trade_lots")
        with col2:
            trade_stop = st.number_input("Stop Loss", value=current_price - 10 if trade_direction == "BUY" else current_price + 10, step=1.0, format="%.2f", key="trade_stop")
            trade_tp = st.number_input("Take Profit", value=current_price + 20 if trade_direction == "BUY" else current_price - 20, step=1.0, format="%.2f", key="trade_tp")
            trade_notes = st.text_input("Notes", placeholder="Optional", key="trade_notes")
        
        if st.button("✅ ADD TRADE", use_container_width=True):
            if trade_entry > 0 and trade_lots > 0:
                trade_data = {
                    "direction": trade_direction,
                    "entry": trade_entry,
                    "lots": trade_lots,
                    "stop_loss": trade_stop,
                    "take_profit": trade_tp,
                    "notes": trade_notes
                }
                trade_id = trade_manager.add_trade(trade_data)
                st.success(f"✅ Trade {trade_id} added successfully!")
                st.rerun()
            else:
                st.error("Please enter valid trade details")
    
    st.markdown("---")
    
    # الصفقات المفتوحة
    st.markdown("### 🔓 Open Trades")
    if trade_manager.open_trades:
        for trade in trade_manager.open_trades:
            with st.container():
                color = "#00ff88" if trade["direction"] == "BUY" else "#ff4444"
                st.markdown(f"""
                <div class="trade-row" style="border-left-color: {color}">
                    <b>🆔 {trade['id']}</b> | 📅 {trade['date']}<br>
                    <b>{trade['direction']}</b> | Entry: ${trade['entry']:.2f} | Lots: {trade['lots']}<br>
                    🛑 SL: ${trade.get('stop_loss', 0):.2f} | 🎯 TP: ${trade.get('take_profit', 0):.2f}<br>
                    📝 {trade.get('notes', 'No notes')}
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    exit_price = st.number_input(f"Exit price for {trade['id']}", value=current_price, step=1.0, format="%.2f", key=f"exit_{trade['id']}")
                    if st.button(f"Close {trade['id']}", key=f"close_{trade['id']}"):
                        profit = trade_manager.close_trade(trade['id'], exit_price)
                        if profit:
                            st.success(f"Trade closed! Profit: ${profit:.2f}")
                            st.rerun()
    else:
        st.info("No open trades 📭")
    
    st.markdown("---")
    
    # الصفقات المغلقة
    st.markdown("### 🔒 Closed Trades")
    if trade_manager.closed_trades:
        for trade in reversed(trade_manager.closed_trades[-20:]):  # آخر 20 صفقة
            profit = trade.get("profit", 0)
            profit_color = "#00ff88" if profit > 0 else "#ff4444"
            profit_sign = "+" if profit > 0 else ""
            result_emoji = "✅" if trade.get("result") == "win" else "❌"
            
            st.markdown(f"""
            <div class="trade-row trade-{trade.get('result', 'loss')}">
                <b>{result_emoji} 🆔 {trade['id']}</b> | 📅 {trade['date']}<br>
                <b>{trade['direction']}</b> | Entry: ${trade['entry']:.2f} | Exit: ${trade.get('exit', 0):.2f} | Lots: {trade['lots']}<br>
                📊 P&L: <span style="color:{profit_color}">{profit_sign}${abs(profit):.2f}</span><br>
                📝 {trade.get('notes', 'No notes')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No closed trades yet 📭")

# ==========================================
# الفوتر
# ==========================================
st.markdown(f"""
<div class="footer">
    𓋹 GoldAPI.io | SMC + ICT + MACD + BB + ADX + VWAP + Fibonacci | Advanced Analysis 𓋹<br>
    <a href="https://t.me/Ehabka2002" target="_blank" style="color:#0088cc; text-decoration:none;">📱 اشترك في قناة التليجرام للإشارات اليومية</a><br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
