# ==========================================
# 𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹
# 𓋹         PHARAOH GOLD DASHBOARD           𓋹
# 𓋹      موقع تحليل الذهب الفرعوني          𓋹
# 𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹𓋹
# ==========================================

import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
from textblob import TextBlob
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# إعدادات الصفحة
# ==========================================
st.set_page_config(
    page_title="𓋹 Pharaoh Gold Dashboard 𓋹",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS للتنسيق الفرعوني
# ==========================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        font-size: 2.5rem;
        color: #ffd700;
        margin-bottom: 1rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px #000000;
    }
    .pharaoh-text {
        color: #ffd700;
        font-size: 1.2rem;
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
        background-color: #1e1e2e;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        border: 1px solid #ffd70033;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# العنوان الرئيسي
# ==========================================
st.markdown('<div class="main-header">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# الشريط الجانبي
# ==========================================
with st.sidebar:
    st.header("⚙️ إعدادات الفرعون")
    period = st.selectbox("الفترة الزمنية", ["3d", "1wk", "1mo"], index=0)
    interval = st.selectbox("الإطار الزمني", ["1h", "4h", "1d"], index=0)
    st.markdown("---")
    st.caption("𓋹 *Powered by SMC/ICT Analysis* 𓋹")
    st.caption("📊 *Data: Yahoo Finance*")

# ==========================================
# دوال التحليل
# ==========================================

@st.cache_data(ttl=300)
def get_gold_data():
    """جلب بيانات الذهب"""
    gold = yf.Ticker("GC=F")
    df = gold.history(period="1mo", interval="1h")
    if df.empty:
        return None
    df.columns = [col.lower() for col in df.columns]
    return df

@st.cache_data(ttl=300)
def calculate_indicators(df):
    """حساب المؤشرات"""
    df = df.copy()
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['ema20'] = ta.ema(df['close'], length=20)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
    
    macd_df = ta.macd(df['close'])
    if macd_df is not None and len(macd_df.columns) >= 2:
        df['macd'] = macd_df.iloc[:, 0]
        df['macd_signal'] = macd_df.iloc[:, 1]
    
    return df

def detect_liquidity_sweeps(df):
    """كشف اصطياد السيولة"""
    df = df.copy()
    df['liquidity_sweep_bullish'] = False
    df['liquidity_sweep_bearish'] = False
    
    for i in range(10, len(df)):
        recent_lows = df['low'].iloc[i-10:i].tolist()
        if df['low'].iloc[i] < min(recent_lows[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bullish'] = True
        recent_highs = df['high'].iloc[i-10:i].tolist()
        if df['high'].iloc[i] > max(recent_highs[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bearish'] = True
    
    return df

def detect_bos(df):
    """كشف كسر الهيكل"""
    df = df.copy()
    df['bos_bullish'] = False
    df['bos_bearish'] = False
    
    for i in range(5, len(df)):
        if df['close'].iloc[i] > df['high'].iloc[i-5:i].max():
            df.loc[df.index[i], 'bos_bullish'] = True
        if df['close'].iloc[i] < df['low'].iloc[i-5:i].min():
            df.loc[df.index[i], 'bos_bearish'] = True
    
    return df

def get_support_resistance(df):
    """حساب الدعم والمقاومة"""
    current_price = df['close'].iloc[-1]
    recent_highs = df['high'].iloc[-30:].values
    recent_lows = df['low'].iloc[-30:].values
    
    resistance = np.percentile(recent_highs, 75)
    support = np.percentile(recent_lows, 25)
    
    return support, resistance

def get_nyt_sentiment():
    """تحليل المشاعر الإخبارية"""
    NYT_API_KEY = "suEqGgxLCKO95ktzKCjmqAlBAtfb4CgVj800GTHgMJHnR2So"
    try:
        params = {"api-key": NYT_API_KEY, "q": "gold", "page": 0}
        response = requests.get("https://api.nytimes.com/svc/search/v2/articlesearch.json", params=params, timeout=10)
        if response.status_code == 200:
            articles = response.json().get("response", {}).get("docs", [])
            sentiments = []
            for article in articles[:5]:
                title = article.get("headline", {}).get("main", "")
                if title:
                    blob = TextBlob(title)
                    sentiments.append(blob.sentiment.polarity)
            if sentiments:
                avg = sum(sentiments) / len(sentiments)
                if avg > 0.15:
                    return "🟢 إيجابي", 2
                elif avg < -0.15:
                    return "🔴 سلبي", -2
        return "⚪ محايد", 0
    except:
        return "⚪ محايد", 0

# ==========================================
# التحليل الرئيسي
# ==========================================
with st.spinner("𓋹 جاري تحليل الذهب... ⏳ 𓋹"):
    df = get_gold_data()

if df is None:
    st.error("❌ خطأ في جلب البيانات")
    st.stop()

df = calculate_indicators(df)
df = detect_liquidity_sweeps(df)
df = detect_bos(df)

current_price = df['close'].iloc[-1]
support, resistance = get_support_resistance(df)
sentiment_text, sentiment_score = get_nyt_sentiment()

# نظام التسجيل
bullish = 0
bearish = 0
signals = []
smc_signals = []

# RSI
if df['rsi'].iloc[-1] < 45:
    bullish += 3
    signals.append(f"✅ RSI: {df['rsi'].iloc[-1]:.1f} (شراء)")
elif df['rsi'].iloc[-1] > 65:
    bearish += 3
    signals.append(f"⚠️ RSI: {df['rsi'].iloc[-1]:.1f} (بيع)")
else:
    signals.append(f"📊 RSI: {df['rsi'].iloc[-1]:.1f} (محايد)")

# المتوسطات
if current_price > df['ema20'].iloc[-1]:
    bullish += 2
    signals.append("📈 فوق EMA20")
else:
    bearish += 2
    signals.append("📉 تحت EMA20")

# MACD
if 'macd' in df.columns and df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
    bullish += 2
    signals.append("🟢 MACD إيجابي")
else:
    bearish += 2
    signals.append("🔴 MACD سلبي")

# VWAP
if current_price > df['vwap'].iloc[-1]:
    bullish += 1
    signals.append("💰 فوق VWAP")
else:
    bearish += 1
    signals.append("💰 تحت VWAP")

# SMC Signals
if df['liquidity_sweep_bullish'].iloc[-1]:
    bullish += 3
    smc_signals.append("🎯 اصطياد سيولة (صاعد)")
if df['liquidity_sweep_bearish'].iloc[-1]:
    bearish += 3
    smc_signals.append("🎯 اصطياد سيولة (هابط)")
if df['bos_bullish'].iloc[-1]:
    bullish += 2
    smc_signals.append("🚀 BOS صاعد")
if df['bos_bearish'].iloc[-1]:
    bearish += 2
    smc_signals.append("🚀 BOS هابط")

# أخبار
if sentiment_score > 0:
    bullish += sentiment_score
    signals.append(f"📰 أخبار: {sentiment_text}")
elif sentiment_score < 0:
    bearish += abs(sentiment_score)
    signals.append(f"📰 أخبار: {sentiment_text}")

net = bullish - bearish

# الإشارة النهائية
if net >= 10:
    signal_type = "🔴🔴🔴 إشارة شراء قوية جدا 🔴🔴🔴"
    signal_action = "BUY"
    confidence = 95
elif net >= 6:
    signal_type = "🟢🟢 إشارة شراء قوية 🟢🟢"
    signal_action = "BUY"
    confidence = 85
elif net >= 3:
    signal_type = "🟢 إشارة شراء خفيفة 🟢"
    signal_action = "BUY"
    confidence = 70
elif net <= -10:
    signal_type = "🔴🔴🔴 إشارة بيع قوية جدا 🔴🔴🔴"
    signal_action = "SELL"
    confidence = 95
elif net <= -6:
    signal_type = "🔴🔴 إشارة بيع قوية 🔴🔴"
    signal_action = "SELL"
    confidence = 85
elif net <= -3:
    signal_type = "🔴 إشارة بيع خفيفة 🔴"
    signal_action = "SELL"
    confidence = 70
else:
    signal_type = "🟡 انتظار - لا توجد إشارة واضحة 🟡"
    signal_action = "NEUTRAL"
    confidence = 50

# الأهداف ووقف الخسارة
atr = df['atr'].iloc[-1]
if signal_action == "BUY":
    entry = current_price
    stop_loss = support - (atr * 0.3)
    targets = [resistance, resistance + (atr * 1.5), resistance + (atr * 3)]
elif signal_action == "SELL":
    entry = current_price
    stop_loss = resistance + (atr * 0.3)
    targets = [support, support - (atr * 1.5), support - (atr * 3)]
else:
    entry = current_price
    stop_loss = None
    targets = []

# ==========================================
# عرض البطاقات
# ==========================================
st.subheader("📊 نظرة عامة")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 سعر الذهب", f"${current_price:.2f}")

with col2:
    st.metric("📈 RSI", f"{df['rsi'].iloc[-1]:.1f}")

with col3:
    st.metric("🎯 الإشارة", signal_type.split('-')[0], delta=f"ثقة {confidence}%")

with col4:
    st.metric("📰 المشاعر", sentiment_text, delta=f"{sentiment_score:+d}")

st.markdown("---")

# ==========================================
# التبويبات
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📈 الشارت", "🏛️ المؤشرات", "🎯 خطة التداول", "📰 الأخبار"])

# ==========================================
# تبويب 1: الشارت
# ==========================================
with tab1:
    # جلب بيانات الشارت
    chart_df = yf.Ticker("GC=F").history(period=period, interval=interval)
    if not chart_df.empty:
        chart_df.columns = [col.lower() for col in chart_df.columns]
        chart_df['ema20'] = chart_df['close'].ewm(span=20).mean()
        chart_df['ema50'] = chart_df['close'].ewm(span=50).mean()
        chart_df['rsi'] = ta.rsi(chart_df['close'], length=14)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # الشموع
        fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['open'], high=chart_df['high'], low=chart_df['low'], close=chart_df['close'], name="الذهب"), row=1, col=1)
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['ema20'], name="EMA 20", line=dict(color='#ff9f4a')), row=1, col=1)
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['ema50'], name="EMA 50", line=dict(color='#4a9eff')), row=1, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['rsi'], name="RSI", line=dict(color='#9b59b6')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="تشبع شرائي")
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="تشبع بيعي")
        
        fig.update_layout(template="plotly_dark", height=600, title=f"𓋹 شارت الذهب الفرعوني - ${current_price:.2f} 𓋹")
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# تبويب 2: المؤشرات
# ==========================================
with tab2:
    st.subheader("📈 المؤشرات الكلاسيكية")
    for s in signals:
        if "✅" in s or "📈" in s or "💰" in s:
            st.success(s)
        elif "⚠️" in s or "📉" in s or "🔴" in s:
            st.error(s)
        else:
            st.info(s)
    
    if smc_signals:
        st.subheader("🏛️ إشارات SMC")
        for s in smc_signals:
            st.info(s)

# ==========================================
# تبويب 3: خطة التداول
# ==========================================
with tab3:
    st.subheader("🎯 خطة التداول الفرعونية")
    
    if signal_action == "BUY":
        st.markdown(f"""
        <div class="signal-buy">
            <b>🟢 إشارة شراء - ثقة {confidence}%</b><br><br>
            📍 <b>سعر الدخول:</b> ${entry:.2f}<br>
            🛑 <b>وقف الخسارة:</b> ${stop_loss:.2f}<br><br>
            🎯 <b>الأهداف:</b><br>
            • 🥇 الهدف الأول: ${targets[0]:.2f}<br>
            • 🥈 الهدف الثاني: ${targets[1]:.2f}<br>
            • 🥉 الهدف الثالث: ${targets[2]:.2f}<br><br>
            💡 <b>نصيحة:</b> استخدم وقف متحرك عند كسر القمم
        </div>
        """, unsafe_allow_html=True)
    elif signal_action == "SELL":
        st.markdown(f"""
        <div class="signal-sell">
            <b>🔴 إشارة بيع - ثقة {confidence}%</b><br><br>
            📍 <b>سعر الدخول:</b> ${entry:.2f}<br>
            🛑 <b>وقف الخسارة:</b> ${stop_loss:.2f}<br><br>
            🎯 <b>الأهداف:</b><br>
            • 🥇 الهدف الأول: ${targets[0]:.2f}<br>
            • 🥈 الهدف الثاني: ${targets[1]:.2f}<br>
            • 🥉 الهدف الثالث: ${targets[2]:.2f}<br><br>
            💡 <b>نصيحة:</b> استخدم وقف متحرك عند كسر القيعان
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="signal-neutral">
            <b>🟡 انتظار - لا توجد إشارة واضحة</b><br><br>
            ثقة التحليل: {confidence}%<br>
            استمر في مراقبة السوق حتى تظهر إشارة أقوى.
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# تبويب 4: الأخبار
# ==========================================
with tab4:
    st.subheader("📰 آخر أخبار الذهب")
    try:
        params = {"api-key": "suEqGgxLCKO95ktzKCjmqAlBAtfb4CgVj800GTHgMJHnR2So", "q": "gold", "page": 0}
        response = requests.get("https://api.nytimes.com/svc/search/v2/articlesearch.json", params=params, timeout=10)
        if response.status_code == 200:
            articles = response.json().get("response", {}).get("docs", [])
            for article in articles[:5]:
                title = article.get("headline", {}).get("main", "")
                date = article.get("pub_date", "")[:10]
                st.markdown(f"**📌 {title}**  \n🕐 {date}")
                st.markdown("---")
    except:
        st.warning("لا توجد أخبار حالياً")

# ==========================================
# وقت التحديث
# ==========================================
st.markdown("---")
st.caption(f"🕐 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 𓋹 بوت تحليل الذهب الفرعوني 𓋹")
