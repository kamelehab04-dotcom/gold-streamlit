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
    .currency-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 10px 15px;
        text-align: center;
        border: 1px solid #ffd70033;
        margin: 5px 0;
    }
    .currency-symbol { font-size: 0.8rem; color: #888; }
    .currency-price { font-size: 1.2rem; font-weight: bold; color: #fff; }
    .currency-change { font-size: 0.9rem; }
    .trade-row {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #ffd700;
    }
    .footer {
        text-align: center;
        padding: 15px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
    .stButton button {
        background: #ffd700;
        color: #000;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">Advanced Analysis | SMC + ICT + MACD + BB + ADX + VWAP + Fibonacci + Ichimoku + MTF</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# إعدادات API
# ==========================================
GOLD_API_KEY = "goldapi-2262c60e69ce568bf76b982116077d1f-io"

# ==========================================
# قائمة الأزواج
# ==========================================
PAIRS = {
    "XAU/USD (Gold)": "GC=F",
    "DXY (Dollar Index)": "DX-Y.NYB",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
    "ETH/USD (Ethereum)": "ETH-USD"
}

# ==========================================
# دوال جلب البيانات
# ==========================================
@st.cache_data(ttl=10)
def get_spot_price(symbol="GC=F"):
    try:
        if symbol == "GC=F":
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0)), float(data.get('change', 0))
    except:
        pass
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="5m")
        if not data.empty:
            last = data.iloc[-1]
            first = data.iloc[0]
            change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
            return float(last['Close']), float(change)
    except:
        pass
    return None, None

@st.cache_data(ttl=300)
def get_historical_data(symbol, period="1mo", interval="1h"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return None

@st.cache_data(ttl=60)
def get_all_forex():
    symbols = {
        "DXY": "DX-Y.NYB",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "BTCUSD": "BTC-USD"
    }
    results = {}
    for name, symbol in symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="5m")
            if not data.empty:
                last = data.iloc[-1]
                first = data.iloc[0]
                change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
                results[name] = {'price': float(last['Close']), 'change': float(change)}
            else:
                results[name] = {'price': 0, 'change': 0}
        except:
            results[name] = {'price': 0, 'change': 0}
    return results

# ==========================================
# المؤشرات الفنية (جميع الدوال)
# ==========================================
def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calc_atr(df, period=14):
    high = df['high']; low = df['low']; close = df['close']
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
    high = df['high']; low = df['low']; close = df['close']
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

def calc_stochastic(high, low, close, k_period=14, d_period=3):
    low_min = low.rolling(window=k_period).min()
    high_max = high.rolling(window=k_period).max()
    k = 100 * ((close - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()
    return k, d

def calc_mfi(df, period=14):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    return mfi

def calc_cci(high, low, close, period=20):
    tp = (high + low + close) / 3
    sma_tp = tp.rolling(window=period).mean()
    mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci

def calc_obv(df):
    obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    return obv

def calc_ichimoku(df):
    high = df['high']; low = df['low']; close = df['close']
    tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
    kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
    chikou = close.shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou

# ==========================================
# نظام تسجيل النقاط المتقدم (بدون ML)
# ==========================================
def generate_advanced_signal(df, current_price, symbol=""):
    if df is None or len(df) < 100:
        return "WAIT", 50, 0, {}

    last = df.iloc[-1]
    scores = {'BUY': 0, 'SELL': 0}
    details = {}
    weights = {
        'rsi': 3, 'macd': 2, 'bb': 2, 'vwap': 1, 'adx': 1,
        'stoch': 2, 'mfi': 2, 'cci': 2, 'ichimoku': 3, 'obv': 1
    }

    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if rsi < 30:
            scores['BUY'] += weights['rsi']; details['RSI'] = f"مفرط البيع ({rsi:.1f}) +{weights['rsi']}"
        elif rsi > 70:
            scores['SELL'] += weights['rsi']; details['RSI'] = f"مفرط الشراء ({rsi:.1f}) +{weights['rsi']}"
        else:
            details['RSI'] = f"محايد ({rsi:.1f})"

    if 'macd' in df.columns and 'macd_signal' in df.columns and not pd.isna(last['macd']):
        if last['macd'] > last['macd_signal'] and last['macd'] > 0:
            scores['BUY'] += weights['macd']; details['MACD'] = f"إيجابي +{weights['macd']}"
        elif last['macd'] < last['macd_signal'] and last['macd'] < 0:
            scores['SELL'] += weights['macd']; details['MACD'] = f"سلبي +{weights['macd']}"
        else:
            details['MACD'] = "محايد"

    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and not pd.isna(last['bb_upper']):
        if current_price <= last['bb_lower'] * 1.005:
            scores['BUY'] += weights['bb']; details['BB'] = f"قرب الحد السفلي +{weights['bb']}"
        elif current_price >= last['bb_upper'] * 0.995:
            scores['SELL'] += weights['bb']; details['BB'] = f"قرب الحد الأعلى +{weights['bb']}"
        else:
            details['BB'] = "وسط النطاق"

    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += weights['vwap']; details['VWAP'] = f"فوق VWAP +{weights['vwap']}"
        else:
            scores['SELL'] += weights['vwap']; details['VWAP'] = f"تحت VWAP +{weights['vwap']}"

    if 'adx' in df.columns and not pd.isna(last['adx']):
        details['ADX'] = f"اتجاه {'قوي' if last['adx'] > 25 else 'ضعيف'} ({last['adx']:.1f})"
        if last['adx'] > 25:
            if df['close'].iloc[-1] > df['close'].iloc[-5]:
                scores['BUY'] += 1; details['ADX'] += " +1 BUY"
            else:
                scores['SELL'] += 1; details['ADX'] += " +1 SELL"

    if 'stoch_k' in df.columns and 'stoch_d' in df.columns and not pd.isna(last['stoch_k']):
        k = last['stoch_k']; d = last['stoch_d']
        if k < 20 and d < 20 and k > d:
            scores['BUY'] += weights['stoch']; details['Stoch'] = f"تشبع بيعي صاعد +{weights['stoch']}"
        elif k > 80 and d > 80 and k < d:
            scores['SELL'] += weights['stoch']; details['Stoch'] = f"تشبع شرائي هابط +{weights['stoch']}"
        else:
            details['Stoch'] = "محايد"

    if 'mfi' in df.columns and not pd.isna(last['mfi']):
        mfi = last['mfi']
        if mfi < 20:
            scores['BUY'] += weights['mfi']; details['MFI'] = f"مفرط البيع ({mfi:.1f}) +{weights['mfi']}"
        elif mfi > 80:
            scores['SELL'] += weights['mfi']; details['MFI'] = f"مفرط الشراء ({mfi:.1f}) +{weights['mfi']}"
        else:
            details['MFI'] = f"محايد ({mfi:.1f})"

    if 'cci' in df.columns and not pd.isna(last['cci']):
        cci = last['cci']
        if cci < -100:
            scores['BUY'] += weights['cci']; details['CCI'] = f"مفرط البيع ({cci:.1f}) +{weights['cci']}"
        elif cci > 100:
            scores['SELL'] += weights['cci']; details['CCI'] = f"مفرط الشراء ({cci:.1f}) +{weights['cci']}"
        else:
            details['CCI'] = f"محايد ({cci:.1f})"

    if 'senkou_a' in df.columns and 'senkou_b' in df.columns and 'chikou' in df.columns:
        if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']) and not pd.isna(last['chikou']):
            if current_price > last['senkou_a'] and current_price > last['senkou_b']:
                scores['BUY'] += weights['ichimoku']; details['Ichimoku'] = f"فوق السحابة +{weights['ichimoku']}"
            elif current_price < last['senkou_a'] and current_price < last['senkou_b']:
                scores['SELL'] += weights['ichimoku']; details['Ichimoku'] = f"تحت السحابة +{weights['ichimoku']}"
            else:
                details['Ichimoku'] = "داخل السحابة"

    if 'obv' in df.columns and len(df) > 10:
        obv_trend = df['obv'].iloc[-1] - df['obv'].iloc[-10]
        if obv_trend > 0:
            scores['BUY'] += weights['obv']; details['OBV'] = f"تجميع +{weights['obv']}"
        else:
            scores['SELL'] += weights['obv']; details['OBV'] = f"توزيع +{weights['obv']}"

    net_score = scores['BUY'] - scores['SELL']
    total_weight = sum(weights.values())
    if net_score >= 5:
        signal = "BUY"
        confidence = min(100, 60 + (net_score / total_weight) * 100)
    elif net_score <= -5:
        signal = "SELL"
        confidence = min(100, 60 + (abs(net_score) / total_weight) * 100)
    else:
        signal = "WAIT"
        confidence = 50 + (net_score / total_weight) * 50

    confidence = max(0, min(100, confidence))
    return signal, confidence, net_score, details

# ==========================================
# تحليل متعدد الأطر الزمنية
# ==========================================
def get_mtf_signal(symbol, current_price):
    timeframes = ['15m', '1h', '4h']
    signals = []
    for tf in timeframes:
        df = get_historical_data(symbol, period="5d", interval=tf)
        if df is not None and len(df) > 50:
            rsi = calc_rsi(df['close']).iloc[-1]
            if rsi < 30:
                signals.append(('BUY', tf))
            elif rsi > 70:
                signals.append(('SELL', tf))
            else:
                signals.append(('NEUTRAL', tf))
    buy_count = sum(1 for s in signals if s[0] == 'BUY')
    sell_count = sum(1 for s in signals if s[0] == 'SELL')
    if buy_count > sell_count:
        return "BUY", buy_count - sell_count
    elif sell_count > buy_count:
        return "SELL", sell_count - buy_count
    else:
        return "NEUTRAL", 0

# ==========================================
# إدارة الصفقات (مبسطة)
# ==========================================
class AdvancedTradeManager:
    def __init__(self):
        self.trades_file = "advanced_trades.json"
        self.load_trades()
    def load_trades(self):
        try:
            with open(self.trades_file, "r", encoding='utf-8') as f:
                data = json.load(f)
                self.open_trades = data.get("open_trades", [])
                self.closed_trades = data.get("closed_trades", [])
        except:
            self.open_trades = []
            self.closed_trades = []
    def save_trades(self):
        with open(self.trades_file, "w", encoding='utf-8') as f:
            json.dump({"open_trades": self.open_trades, "closed_trades": self.closed_trades}, f, indent=2, ensure_ascii=False)
    def add_trade(self, trade_data):
        trade_id = f"T{len(self.open_trades)+len(self.closed_trades)+1:03d}"
        trade = {
            "id": trade_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "direction": trade_data["direction"],
            "entry": trade_data["entry"],
            "lots": trade_data["lots"],
            "stop_loss": trade_data["stop_loss"],
            "take_profit": trade_data["take_profit"],
            "trailing_stop": trade_data.get("trailing_stop", 0),
            "status": "open",
            "notes": trade_data.get("notes", "")
        }
        self.open_trades.append(trade)
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

# ==========================================
# الواجهة الرئيسية
# ==========================================
st.markdown("### 🔍 اختر الزوج للتحليل المتقدم")
selected_pair_name = st.selectbox("اختر الزوج للتحليل المتقدم", list(PAIRS.keys()), index=0)
selected_symbol = PAIRS[selected_pair_name]

# عرض البطاقات السريعة
forex_data = get_all_forex()
if forex_data:
    cols = st.columns(5)
    for i, (name, data) in enumerate(forex_data.items()):
        if data['price'] > 0:
            color = "#00ff88" if data['change'] >= 0 else "#ff4444"
            # تحديد التنسيق حسب الاسم
            if 'USD' in name:
                price_str = f"{data['price']:.4f}"
            else:
                price_str = f"{data['price']:.2f}"
            cols[i].markdown(f"""
            <div class="currency-card">
                <div class="currency-symbol">{name}</div>
                <div class="currency-price">{price_str}</div>
                <div class="currency-change" style="color:{color};">{data['change']:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# جلب البيانات
current_price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="1mo", interval="1h")
if df is None:
    st.error("تعذر تحميل البيانات")
    st.stop()
if current_price is None:
    current_price = df['close'].iloc[-1]
    change = 0

# حساب المؤشرات
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'])
df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df)
df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()
df['stoch_k'], df['stoch_d'] = calc_stochastic(df['high'], df['low'], df['close'])
df['mfi'] = calc_mfi(df)
df['cci'] = calc_cci(df['high'], df['low'], df['close'])
df['obv'] = calc_obv(df)
tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(df)
df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b; df['chikou'] = chikou

# توليد الإشارة المتقدمة
signal, confidence, net_score, details = generate_advanced_signal(df, current_price, selected_symbol)
mtf_signal, mtf_count = get_mtf_signal(selected_symbol, current_price)

# عرض السعر
price_format = "${:,.2f}" if "BTC" in selected_pair_name or "Gold" in selected_pair_name else "${:.4f}"
st.markdown(f"""
<div class="price-card">
    <div style="font-size:1rem; color:#888;">{selected_pair_name} (Live)</div>
    <div class="price-value">{price_format.format(current_price)}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">
        {change:+.2f}%
    </div>
</div>
""", unsafe_allow_html=True)

# مؤشرات السوق
st.markdown("### 📊 مؤشرات السوق المتقدمة")
cols = st.columns(5)
last = df.iloc[-1]
cols[0].metric("RSI", f"{last['rsi']:.1f}")
cols[1].metric("ATR", f"${last['atr']:.2f}")
cols[2].metric("ADX", f"{last['adx']:.1f}")
cols[3].metric("Stoch K", f"{last['stoch_k']:.1f}")
cols[4].metric("MFI", f"{last['mfi']:.1f}")

# الإشارة
st.markdown("---")
st.markdown("### 🧠 إشارة التداول المتقدمة")
signal_color = "#ffaa00" if signal == "WAIT" else ("#00ff88" if signal == "BUY" else "#ff4444")
st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color: {signal_color};">{signal}</div>
    <div class="signal-confidence">الثقة: {confidence:.0f}% | النتيجة: {net_score}</div>
    <div style="font-size:0.9rem; color:#aaa; margin-top:10px;">
        MTF إجماع: {mtf_signal} (عدد الأطر: {mtf_count})
    </div>
</div>
""", unsafe_allow_html=True)

if details:
    with st.expander("تفاصيل التسجيل"):
        for key, val in details.items():
            st.write(f"- {key}: {val}")

# الرسم البياني
st.markdown("---")
st.markdown("### 📈 Price Chart with Indicators")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    row_heights=[0.6, 0.2, 0.2])
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(color='red', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='blue', width=0.8)), row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
fig.add_bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color='gray', opacity=0.3, row=3, col=1)

fig.update_layout(height=800, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# إدارة الصفقات
# ==========================================
st.markdown("---")
st.markdown("### 💼 إدارة الصفقات المتقدمة")
trade_manager = AdvancedTradeManager()

with st.form("add_trade_form"):
    st.write("إضافة صفقة جديدة")
    col1, col2, col3 = st.columns(3)
    direction = col1.selectbox("الاتجاه", ["BUY", "SELL"])
    entry = col2.number_input("سعر الدخول", value=float(current_price), format="%.2f")
    lots = col3.number_input("عدد اللوتات", min_value=0.01, value=0.1, step=0.01)
    col1, col2, col3 = st.columns(3)
    stop_loss = col1.number_input("وقف الخسارة", value=float(current_price - 20), format="%.2f")
    take_profit = col2.number_input("جني الربح", value=float(current_price + 40), format="%.2f")
    trailing = col3.number_input("وقف متحرك (نقاط)", min_value=0, value=10)
    submitted = st.form_submit_button("إضافة صفقة")
    if submitted and entry > 0 and stop_loss > 0:
        trade_data = {
            "direction": direction,
            "entry": entry,
            "lots": lots,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "trailing_stop": trailing,
            "notes": f"إشارة من البوت: {signal}"
        }
        trade_id = trade_manager.add_trade(trade_data)
        st.success(f"✅ تم إضافة الصفقة {trade_id}")

# عرض الصفقات المفتوحة
if trade_manager.open_trades:
    st.write("**الصفقات المفتوحة:**")
    for trade in trade_manager.open_trades:
        st.markdown(f"""
        <div class="trade-row">
            <b>{trade['id']}</b> | {trade['direction']} | الدخول: {trade['entry']} | اللوت: {trade['lots']} | الوقف: {trade['stop_loss']} | الهدف: {trade['take_profit']}
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"إغلاق {trade['id']}", key=f"close_{trade['id']}"):
            profit = trade_manager.close_trade(trade['id'], current_price)
            st.success(f"تم الإغلاق، الربح: ${profit:.2f}" if profit else "تم الإغلاق")
            st.experimental_rerun()

if trade_manager.closed_trades:
    profits = [t.get('profit', 0) for t in trade_manager.closed_trades if 'profit' in t]
    if profits:
        win_rate = sum(1 for p in profits if p > 0) / len(profits) * 100
        total_profit = sum(profits)
        avg_profit = total_profit / len(profits)
        st.metric("نسبة الربح", f"{win_rate:.1f}%")
        st.metric("إجمالي الربح", f"${total_profit:.2f}")
        st.metric("متوسط الربح", f"${avg_profit:.2f}")

# ==========================================
# تحليل الارتباط للذهب
# ==========================================
if selected_symbol == "GC=F":
    st.markdown("---")
    st.markdown("### 🔗 تحليل الارتباط: الذهب vs الدولار")
    df_dxy = get_historical_data("DX-Y.NYB", "1mo", "1h")
    if df_dxy is not None and not df_dxy.empty:
        df_dxy_aligned = df_dxy.reindex(df.index, method='nearest')
        df_dxy_aligned = df_dxy_aligned.ffill()  # ✅ التصحيح: استخدام .ffill() بدلاً من fillna(method='ffill')

        fig_corr = make_subplots(specs=[[{"secondary_y": True}]])
        fig_corr.add_trace(go.Scatter(x=df.index, y=df['close'], name='XAU/USD', line=dict(color='gold')), secondary_y=False)
        fig_corr.add_trace(go.Scatter(x=df_dxy_aligned.index, y=df_dxy_aligned['close'], name='DXY', line=dict(color='cyan')), secondary_y=True)
        fig_corr.update_layout(height=400, template='plotly_dark', title="Gold vs DXY")
        fig_corr.update_yaxes(title_text="Gold", secondary_y=False)
        fig_corr.update_yaxes(title_text="DXY", secondary_y=True)
        st.plotly_chart(fig_corr, use_container_width=True)

        if len(df) > 10:
            corr = df['close'].corr(df_dxy_aligned['close'])
            st.metric("معامل الارتباط", f"{corr:.3f}")
    else:
        st.info("تعذر جلب بيانات مؤشر الدولار")

# ==========================================
# تذييل
# ==========================================
st.markdown("""
<div class="footer">
    GoldAPI.io | SMC + ICT + MACD + BB + ADX + VWAP + Fibonacci + Ichimoku + MTF<br>
    استرداد قناة التداول | تحديث لحظي | نظام تسجيل متقدم
</div>
""", unsafe_allow_html=True)
