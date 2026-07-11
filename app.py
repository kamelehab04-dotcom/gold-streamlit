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
# CSS للتنسيق (نفس السابق)
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
    .currency-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 10px 15px;
        text-align: center;
        border: 1px solid #ffd70033;
        margin: 5px 0;
    }
    .currency-symbol {
        font-size: 0.8rem;
        color: #888;
    }
    .currency-price {
        font-size: 1.2rem;
        font-weight: bold;
        color: #fff;
    }
    .currency-change {
        font-size: 0.9rem;
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
# 🆕 قائمة الأزواج المدعومة
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
    """جلب السعر الفوري للرمز المطلوب"""
    try:
        # إذا كان الذهب، استخدم GoldAPI
        if symbol == "GC=F":
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0)), float(data.get('change', 0))
    except:
        pass
    
    # البديل: استخدام yfinance لأي رمز
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
    """جلب البيانات التاريخية لأي رمز"""
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
    """جلب أسعار جميع الأزواج المعروضة في البطاقات"""
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
                results[name] = {
                    'price': float(last['Close']),
                    'change': float(change)
                }
            else:
                results[name] = {'price': 0, 'change': 0}
        except:
            results[name] = {'price': 0, 'change': 0}
    return results

# ==========================================
# دوال التحليل الفني (نفس السابق)
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
    if diff == 0:
        return {}
    return {
        'fib_236': high - diff * 0.236,
        'fib_382': high - diff * 0.382,
        'fib_500': high - diff * 0.5,
        'fib_618': high - diff * 0.618,
        'fib_786': high - diff * 0.786
    }

def generate_scored_signal(df, current_price):
    if df is None or len(df) < 50:
        return "WAIT", 50, 0, {}
    
    last = df.iloc[-1]
    scores = {'BUY': 0, 'SELL': 0}
    details = {}

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

    if 'macd' in df.columns and 'macd_signal' in df.columns and not pd.isna(last['macd']):
        if last['macd'] > last['macd_signal'] and last['macd'] > 0:
            scores['BUY'] += 2
            details['MACD'] = "إيجابي +2"
        elif last['macd'] < last['macd_signal'] and last['macd'] < 0:
            scores['SELL'] += 2
            details['MACD'] = "سلبي +2"
        else:
            details['MACD'] = "محايد"

    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and not pd.isna(last['bb_upper']):
        if current_price <= last['bb_lower'] * 1.005:
            scores['BUY'] += 2
            details['BB'] = "قرب الحد السفلي +2"
        elif current_price >= last['bb_upper'] * 0.995:
            scores['SELL'] += 2
            details['BB'] = "قرب الحد الأعلى +2"
        else:
            details['BB'] = "وسط النطاق"

    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += 1
            details['VWAP'] = "فوق VWAP +1"
        else:
            scores['SELL'] += 1
            details['VWAP'] = "تحت VWAP +1"

    if 'adx' in df.columns and not pd.isna(last['adx']):
        if last['adx'] > 25:
            details['ADX'] = f"اتجاه قوي ({last['adx']:.1f})"
        else:
            details['ADX'] = f"اتجاه ضعيف ({last['adx']:.1f})"

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
# 🆕 اختيار الزوج المراد تحليله
# ==========================================

st.markdown("### 🔍 اختر الزوج للتحليل")

selected_pair_name = st.selectbox(
    "اختر الزوج / الأداة المالية",
    list(PAIRS.keys()),
    index=0
)

selected_symbol = PAIRS[selected_pair_name]

# عرض البطاقات السريعة لجميع الأزواج (معلومات فقط)
st.markdown("### 💱 نظرة سريعة على جميع الأزواج")
forex_data = get_all_forex()

if forex_data:
    col_dxy, col_eur, col_gbp, col_jpy, col_btc = st.columns(5)
    
    # DXY
    if "DXY" in forex_data and forex_data["DXY"]['price'] > 0:
        dxy_price = forex_data["DXY"]['price']
        dxy_change = forex_data["DXY"]['change']
        dxy_color = "#00ff88" if dxy_change >= 0 else "#ff4444"
        col_dxy.markdown(f"""
        <div class="currency-card">
            <div class="currency-symbol">🇺🇸 DXY</div>
            <div class="currency-price">{dxy_price:.2f}</div>
            <div class="currency-change" style="color: {dxy_color};">{dxy_change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_dxy.markdown("""
        <div class="currency-card">
            <div class="currency-symbol">🇺🇸 DXY</div>
            <div class="currency-price">⏳</div>
        </div>
        """, unsafe_allow_html=True)
    
    # EURUSD
    if "EURUSD" in forex_data and forex_data["EURUSD"]['price'] > 0:
        eur_price = forex_data["EURUSD"]['price']
        eur_change = forex_data["EURUSD"]['change']
        eur_color = "#00ff88" if eur_change >= 0 else "#ff4444"
        col_eur.markdown(f"""
        <div class="currency-card">
            <div class="currency-symbol">🇪🇺 EURUSD</div>
            <div class="currency-price">{eur_price:.4f}</div>
            <div class="currency-change" style="color: {eur_color};">{eur_change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_eur.markdown("""
        <div class="currency-card">
            <div class="currency-symbol">🇪🇺 EURUSD</div>
            <div class="currency-price">⏳</div>
        </div>
        """, unsafe_allow_html=True)
    
    # GBPUSD
    if "GBPUSD" in forex_data and forex_data["GBPUSD"]['price'] > 0:
        gbp_price = forex_data["GBPUSD"]['price']
        gbp_change = forex_data["GBPUSD"]['change']
        gbp_color = "#00ff88" if gbp_change >= 0 else "#ff4444"
        col_gbp.markdown(f"""
        <div class="currency-card">
            <div class="currency-symbol">🇬🇧 GBPUSD</div>
            <div class="currency-price">{gbp_price:.4f}</div>
            <div class="currency-change" style="color: {gbp_color};">{gbp_change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_gbp.markdown("""
        <div class="currency-card">
            <div class="currency-symbol">🇬🇧 GBPUSD</div>
            <div class="currency-price">⏳</div>
        </div>
        """, unsafe_allow_html=True)
    
    # USDJPY
    if "USDJPY" in forex_data and forex_data["USDJPY"]['price'] > 0:
        jpy_price = forex_data["USDJPY"]['price']
        jpy_change = forex_data["USDJPY"]['change']
        jpy_color = "#00ff88" if jpy_change >= 0 else "#ff4444"
        col_jpy.markdown(f"""
        <div class="currency-card">
            <div class="currency-symbol">🇯🇵 USDJPY</div>
            <div class="currency-price">{jpy_price:.2f}</div>
            <div class="currency-change" style="color: {jpy_color};">{jpy_change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_jpy.markdown("""
        <div class="currency-card">
            <div class="currency-symbol">🇯🇵 USDJPY</div>
            <div class="currency-price">⏳</div>
        </div>
        """, unsafe_allow_html=True)
    
    # BTCUSD
    if "BTCUSD" in forex_data and forex_data["BTCUSD"]['price'] > 0:
        btc_price = forex_data["BTCUSD"]['price']
        btc_change = forex_data["BTCUSD"]['change']
        btc_color = "#00ff88" if btc_change >= 0 else "#ff4444"
        col_btc.markdown(f"""
        <div class="currency-card">
            <div class="currency-symbol">₿ BTCUSD</div>
            <div class="currency-price">${btc_price:,.2f}</div>
            <div class="currency-change" style="color: {btc_color};">{btc_change:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_btc.markdown("""
        <div class="currency-card">
            <div class="currency-symbol">₿ BTCUSD</div>
            <div class="currency-price">⏳</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# تحليل الزوج المختار
# ==========================================

st.markdown(f"### 📊 تحليل {selected_pair_name}")

# جلب البيانات للزوج المختار
current_price, change = get_spot_price(selected_symbol)
df = get_historical_data(selected_symbol, period="1mo", interval="1h")

if df is None:
    st.error(f"❌ تعذر تحميل بيانات {selected_pair_name}. حاول مرة أخرى لاحقاً.")
    st.stop()

if current_price is None and df is not None:
    current_price = df['close'].iloc[-1]
    change = 0

if current_price is None:
    st.error(f"❌ تعذر جلب سعر {selected_pair_name}.")
    st.stop()

# حساب المؤشرات
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['rsi'] = calc_rsi(df['close'])
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'])
df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df)
df['vwap'] = (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

recent_high = df['high'].iloc[-50:].max()
recent_low = df['low'].iloc[-50:].min()
fib_levels = calc_fibonacci_levels(recent_high, recent_low, current_price)

# ==========================================
# عرض السعر والمؤشرات
# ==========================================

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

last = df.iloc[-1]
rsi_val = last['rsi'] if not pd.isna(last['rsi']) else 0
atr_val = last['atr'] if not pd.isna(last['atr']) else 0
adx_val = last['adx'] if not pd.isna(last['adx']) else 0

signal, confidence, net_score, details = generate_scored_signal(df, current_price)

st.markdown("### 📊 مؤشرات السوق")
col_rsi, col_atr, col_adx, col_score = st.columns(4)
col_rsi.metric("RSI (14)", f"{rsi_val:.1f}")
col_atr.metric("ATR", f"${atr_val:.2f}")
col_adx.metric("ADX (Trend Strength)", f"{adx_val:.1f}")
col_score.metric("Net Score", f"{net_score}")

st.markdown("---")
st.markdown("### 🧠 إشارة التداول")
signal_color = "#ffaa00" if signal == "WAIT" else ("#00ff88" if signal == "BUY" else "#ff4444")
st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color: {signal_color};">{signal}</div>
    <div class="signal-confidence">Confidence: {confidence:.0f}% | Score: {net_score}</div>
</div>
""", unsafe_allow_html=True)

# عرض تفاصيل النقاط
if details:
    st.write("**تفاصيل التسجيل:**")
    for key, value in details.items():
        st.write(f"- {key}: {value}")

st.markdown("---")
st.markdown("### 📈 Price Chart")

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                    row_heights=[0.7, 0.3])

fig.add_trace(go.Scatter(x=df.index, y=df['close'], name=selected_pair_name, line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA 20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA 50', line=dict(color='red', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='blue', dash='solid', width=0.8)), row=1, col=1)

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

# ==========================================
# تحليل الارتباط إذا كان الزوج هو الذهب
# ==========================================
if selected_symbol == "GC=F":
    st.markdown("---")
    st.markdown("### 🔗 تحليل الارتباط: الذهب vs مؤشر الدولار")
    
    df_dxy = get_historical_data("DX-Y.NYB", "1mo", "1h")
    if df_dxy is not None and not df_dxy.empty:
        df_dxy_aligned = df_dxy.reindex(df.index, method='nearest')
        df_dxy_aligned = df_dxy_aligned.fillna(method='ffill')
        
        fig_corr = make_subplots(specs=[[{"secondary_y": True}]])
        fig_corr.add_trace(go.Scatter(x=df.index, y=df['close'], name='XAU/USD (Gold)', line=dict(color='gold', width=2)), secondary_y=False)
        fig_corr.add_trace(go.Scatter(x=df_dxy_aligned.index, y=df_dxy_aligned['close'], name='DXY (Dollar Index)', line=dict(color='cyan', width=2)), secondary_y=True)
        fig_corr.update_layout(height=400, template='plotly_dark', title="Gold vs DXY - العلاقة العكسية عادةً")
        fig_corr.update_yaxes(title_text="Gold Price", secondary_y=False)
        fig_corr.update_yaxes(title_text="DXY", secondary_y=True)
        st.plotly_chart(fig_corr, use_container_width=True)
        
        common_idx = df.index.intersection(df_dxy_aligned.index)
        if len(common_idx) > 10:
            gold_prices = df.loc[common_idx, 'close']
            dxy_prices = df_dxy_aligned.loc[common_idx, 'close']
            correlation = gold_prices.corr(dxy_prices)
            st.metric("معامل الارتباط (Correlation)", f"{correlation:.3f}", 
                      delta="علاقة عكسية قوية" if correlation < -0.5 else "علاقة طردية" if correlation > 0.5 else "علاقة ضعيفة")
    else:
        st.info("تعذر جلب بيانات مؤشر الدولار (DXY)")

# ==========================================
# تذييل
# ==========================================
st.markdown("""
<div class="footer">
    GoldAPI.io | SMC + ICT + MACD + BB + ADX + VWAP + Fibonacci | Advanced Analysis<br>
    استرداد قناة التداول | تحديث لحظي | تحليل ديناميكي لجميع الأزواج
</div>
""", unsafe_allow_html=True)
