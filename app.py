# ==========================================
# BLACK PYRAMID – الإصدار 2002 (مطور)
# تاريخ التحديث: 2026-08-27
# الإصلاح: تحسين جلب البيانات مع إعادة المحاولة ورموز بديلة
# ==========================================

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import requests
import json
import os
import time  # 👈 إضافة لاستخدام time.sleep

# ==========================================
# إعداد الصفحة – BLACK PYRAMID
# ==========================================
st.set_page_config(
    page_title="Black Pyramid",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🖤 BLACK PYRAMID – الهوية البصرية (نفسها)
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    /* ===== الخطوط ===== */
    .main-title, .signal-text, .price-value {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 3px;
    }
    .main-subtitle, .price-label, .signal-confidence, .footer {
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 1px;
    }

    /* ===== خلفية الصفحة ===== */
    html, body, .stApp {
        background: #0a0a0a !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .stApp {
        position: relative !important;
        background: #0a0a0a !important;
        min-height: 100vh !important;
    }

    /* ===== الصورة الخلفية ===== */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: url('https://raw.githubusercontent.com/kamelehab04-dotcom/gold-streamlit/main/file_00000000a364820aa4218d02627011f1.png') !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        opacity: 0.25 !important;
        pointer-events: none !important;
        z-index: 0 !important;
        filter: brightness(0.9) contrast(1.1) !important;
    }

    /* ===== توهج خلفي متحرك ===== */
    .stApp::after {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(ellipse at 30% 20%, rgba(255,215,0,0.03) 0%, transparent 50%),
                    radial-gradient(ellipse at 70% 80%, rgba(255,215,0,0.02) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
        animation: bgPulse 10s ease-in-out infinite;
    }
    @keyframes bgPulse {
        0%, 100% { opacity: 0.5; transform: scale(1) rotate(0deg); }
        50% { opacity: 1; transform: scale(1.05) rotate(0.5deg); }
    }

    /* ===== جميع المحتويات فوق الخلفية ===== */
    .main-header, .price-card, .signal-box, .suggested-trade, .trade-row, 
    .entry-zone, .target-zone, .stop-loss-level, .reversal-alert,
    .currency-card, .news-card, .explanation-box, .stButton button,
    .stSelectbox, .stTextInput, .stNumberInput, .stDataFrame,
    .stMetric, .stMarkdown, .stPlotlyChart, .stTabs, .stExpander {
        position: relative !important;
        z-index: 1 !important;
    }

    /* ===== الشريط الجانبي ===== */
    .css-1d391kg, .css-1d391kg * {
        background: rgba(10, 10, 10, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 215, 0, 0.05) !important;
    }

    /* ===== الهيدر المصغر ===== */
    .main-header {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 10px 25px !important;
        min-height: 55px !important;
        background: rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 12px !important;
        margin-bottom: 15px !important;
        border: 1px solid rgba(255, 215, 0, 0.08) !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
    }
    .main-header .main-title {
        font-size: 1.2rem !important;
        color: #ffd700 !important;
        font-weight: 700 !important;
        letter-spacing: 2px !important;
        text-shadow: 0 0 20px rgba(255,215,0,0.05) !important;
    }
    .main-header .pyramid-icon {
        font-size: 0.9rem !important;
        color: #ffd700 !important;
    }
    .main-header .main-subtitle {
        font-size: 0.55rem !important;
        color: #666 !important;
        letter-spacing: 1px !important;
        margin-top: 2px !important;
    }

    /* ===== البطاقات ===== */
    .price-card, .signal-box, .suggested-trade, .trade-row, 
    .entry-zone, .target-zone, .stop-loss-level, .reversal-alert {
        background: rgba(10, 10, 10, 0.75) !important;
        backdrop-filter: blur(6px) !important;
        -webkit-backdrop-filter: blur(6px) !important;
        border: 1px solid rgba(255, 215, 0, 0.10) !important;
        box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important;
        border-radius: 12px !important;
    }
    .price-card {
        border-color: rgba(255, 215, 0, 0.15) !important;
    }
    .price-value {
        color: #fff !important;
        text-shadow: 0 0 40px rgba(255,215,0,0.05);
    }
    .price-label {
        color: #888 !important;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 2px;
    }

    /* ===== الإشارة ===== */
    .signal-box {
        border: 2px solid #ffd700 !important;
        box-shadow: 0 0 40px rgba(255,215,0,0.05) !important;
    }
    .signal-text {
        text-shadow: 0 0 40px currentColor;
    }

    /* ===== الصفقة المقترحة ===== */
    .suggested-trade {
        border: 2px solid #00ff88 !important;
        background: rgba(0, 10, 5, 0.80) !important;
    }

    /* ===== الأهداف والاستوب ===== */
    .target-zone {
        border-left: 4px solid #ffd700 !important;
        background: rgba(255,215,0,0.04) !important;
        padding: 8px 12px;
        margin: 4px 0;
    }
    .target-zone:last-child {
        border-left-color: #00ff88 !important;
    }
    .stop-loss-level {
        border-left: 4px solid #ff4444 !important;
        background: rgba(255,68,68,0.04) !important;
        padding: 8px 12px;
        margin: 4px 0;
    }
    .entry-zone {
        border-left: 4px solid #00ff88 !important;
        background: rgba(0,255,136,0.04) !important;
        padding: 8px 12px;
        margin: 4px 0;
    }

    /* ===== صفوف الصفقات ===== */
    .trade-row {
        border-left: 4px solid #ffd700 !important;
        padding: 10px 15px;
        margin: 5px 0;
    }

    /* ===== التذييل ===== */
    .footer {
        text-align: center;
        padding: 15px;
        color: #444;
        font-size: 0.65rem;
        border-top: 1px solid rgba(255,215,0,0.05);
        margin-top: 30px;
        letter-spacing: 1px;
    }
    .footer .brand {
        color: #ffd700;
        font-weight: 600;
    }

    /* ===== الأزرار ===== */
    .stButton button {
        background: linear-gradient(135deg, #ffd700 0%, #d4a800 100%) !important;
        color: #000 !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 8px 16px !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(255,215,0,0.08) !important;
        font-size: 0.8rem !important;
    }
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(255,215,0,0.2) !important;
    }

    /* ===== شرح القرار ===== */
    .explanation-box {
        background: rgba(10, 10, 10, 0.80) !important;
        border: 1px solid rgba(255,215,0,0.05) !important;
        border-radius: 10px !important;
        padding: 15px !important;
        margin: 8px 0 !important;
        color: #bbb !important;
        font-size: 0.9rem !important;
        line-height: 1.6 !important;
    }

    /* ===== الأخبار ===== */
    .news-card {
        background: rgba(10, 10, 10, 0.65) !important;
        border-left: 3px solid #ffd700 !important;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        margin: 5px 0 !important;
        border: 1px solid rgba(255,215,0,0.05) !important;
    }
    .news-title {
        color: #eee !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    .news-date {
        color: #666 !important;
        font-size: 0.7rem !important;
    }

    /* ===== التنبيهات ===== */
    .reversal-alert {
        border: 1px solid #ff4444 !important;
        background: rgba(255,68,68,0.04) !important;
        padding: 10px 15px !important;
        margin: 5px 0 !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
    }

    /* ===== الحالة ===== */
    .status-open { color: #00ff88 !important; font-weight: bold; }
    .status-closed { color: #ff4444 !important; font-weight: bold; }

    /* ===== الشارات ===== */
    .pattern-badge {
        display: inline-block;
        background: rgba(255, 215, 0, 0.08) !important;
        border: 1px solid rgba(255, 215, 0, 0.12) !important;
        border-radius: 16px !important;
        padding: 3px 12px !important;
        margin: 2px !important;
        font-size: 0.7rem !important;
        color: #ffd700 !important;
    }
    .tbs-badge {
        display: inline-block;
        background: rgba(255, 136, 0, 0.10) !important;
        border: 1px solid rgba(255, 136, 0, 0.15) !important;
        border-radius: 16px !important;
        padding: 3px 12px !important;
        margin: 2px !important;
        font-size: 0.7rem !important;
        color: #ff8800 !important;
        font-weight: bold;
    }

    /* ===== أزرار المؤشرات ===== */
    .indicator-toggle {
        background: rgba(255,215,0,0.05) !important;
        border: 1px solid rgba(255,215,0,0.08) !important;
        border-radius: 8px !important;
        padding: 4px 8px !important;
        font-size: 0.7rem !important;
        color: #aaa !important;
        cursor: pointer !important;
        text-align: center !important;
    }
    .indicator-toggle:hover {
        background: rgba(255,215,0,0.10) !important;
        border-color: #ffd700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر المصغر – BLACK PYRAMID (يمين)
# ==========================================
st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">
            <span class="pyramid-icon">▲</span>
            BLACK PYRAMID
            <span class="pyramid-icon">▲</span>
        </div>
        <div class="main-subtitle">Advanced Trading Intelligence • SMC/ICT • Liquidity • SMR • Patterns • TBS • MTF</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🔑 إعدادات API
# ==========================================
GOLD_API_KEY = "goldapi-e2e53584d1ec7f76897b93bb0a88420f-io"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

# ==========================================
# قائمة الأزواج (نفسها)
# ==========================================
PAIRS = {
    "XAU/USD (Gold)": "GC=F",
    "XAG/USD (Silver)": "SI=F",
    "DXY (Dollar Index)": "DX-Y.NYB",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "EUR/CHF": "EURCHF=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/NZD": "EURNZD=X",
    "EUR/CAD": "EURCAD=X",
    "GBP/JPY": "GBPJPY=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/AUD": "GBPAUD=X",
    "GBP/NZD": "GBPNZD=X",
    "GBP/CAD": "GBPCAD=X",
    "AUD/JPY": "AUDJPY=X",
    "AUD/CHF": "AUDCHF=X",
    "AUD/NZD": "AUDNZD=X",
    "AUD/CAD": "AUDCAD=X",
    "NZD/JPY": "NZDJPY=X",
    "NZD/CHF": "NZDCHF=X",
    "NZD/CAD": "NZDCAD=X",
    "CAD/JPY": "CADJPY=X",
    "CAD/CHF": "CADCHF=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
    "ETH/USD (Ethereum)": "ETH-USD"
}

# ==========================================
# تهيئة حالة الجلسة
# ==========================================
if "df" not in st.session_state:
    st.session_state.df = None
if "current_trade" not in st.session_state:
    st.session_state.current_trade = None
if "trades" not in st.session_state:
    st.session_state.trades = []
if "price_data" not in st.session_state:
    st.session_state.price_data = None
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "daily_pnl" not in st.session_state:
    st.session_state.daily_pnl = 0
if "daily_trades" not in st.session_state:
    st.session_state.daily_trades = 0
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()
if "refresh_trigger" not in st.session_state:
    st.session_state.refresh_trigger = False
if "all_signals" not in st.session_state:
    st.session_state.all_signals = None
if "show_indicators" not in st.session_state:
    st.session_state.show_indicators = True

# ==========================================
# دوال جلب البيانات (المُعدّلة)
# ==========================================
def get_market_status():
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    weekday = now.weekday()
    open_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
    close_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
    if weekday == 5:
        next_open = open_time + timedelta(days=1)
        return "CLOSED", "عطلة نهاية الأسبوع (السبت)", next_open, close_time
    if weekday == 6:
        if now < open_time:
            return "CLOSED", "انتظار افتتاح الأسبوع", open_time, close_time
        else:
            return "OPEN", "السوق مفتوح (الأحد)", close_time, close_time
    if 0 <= weekday <= 3:
        if close_time <= now < open_time:
            return "CLOSED", "الاستراحة اليومية (17:00-18:00 ET)", open_time, close_time
        else:
            next_close = close_time if now < close_time else close_time + timedelta(days=1)
            return "OPEN", "السوق مفتوح", next_close, close_time
    if weekday == 4:
        if now < close_time:
            return "OPEN", "السوق مفتوح (الجمعة)", close_time, close_time
        else:
            next_open = open_time + timedelta(days=2)
            return "CLOSED", "نهاية الأسبوع (إغلاق الجمعة)", next_open, close_time
    return "UNKNOWN", "حالة غير معروفة", None, None

def format_time(dt):
    if dt is None:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

def time_remaining(dt):
    if dt is None:
        return "N/A"
    diff = dt - datetime.now(pytz.timezone('US/Eastern'))
    if diff.total_seconds() < 0:
        return "انتهى"
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    return f"{hours}h {minutes}m"

@st.cache_data(ttl=5)
def get_spot_price(symbol="GC=F"):
    if symbol == "GC=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('price', 0))
                change = float(data.get('change_percent', 0))
                return price, change
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

# 🔥 الدالة المُعدّلة مع إعادة المحاولة والرموز البديلة
@st.cache_data(ttl=300)
def get_historical_data(symbol, period="1mo", interval="1h", max_retries=3):
    """
    جلب البيانات التاريخية مع محاولات إعادة متعددة ورموز بديلة.
    """
    # قائمة الرموز البديلة
    alternative_symbols = {
        "GC=F": ["XAUUSD=X", "GOLD"],
        "SI=F": ["XAGUSD=X", "SILVER"],
        "DX-Y.NYB": ["DX=F", "DXY"],
        "BTC-USD": ["BTCUSD=X"],
        "ETH-USD": ["ETHUSD=X"]
    }
    
    symbols_to_try = [symbol] + alternative_symbols.get(symbol, [])
    
    for attempt in range(max_retries):
        for sym in symbols_to_try:
            try:
                ticker = yf.Ticker(sym)
                df = ticker.history(period=period, interval=interval)
                if not df.empty:
                    df.columns = [col.lower() for col in df.columns]
                    return df
            except Exception as e:
                continue
        
        # إذا فشلت كل المحاولات في هذه الدورة، انتظر ثم أعد المحاولة
        if attempt < max_retries - 1:
            time.sleep(2)
    
    # إذا فشلت كل المحاولات
    st.error(f"⚠️ تعذر تحميل البيانات للرمز {symbol} بعد {max_retries} محاولات.")
    return None

@st.cache_data(ttl=60)
def get_all_forex():
    main_symbols = {
        "DXY": "DX-Y.NYB",
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "USDCHF": "USDCHF=X",
        "AUDUSD": "AUDUSD=X",
        "NZDUSD": "NZDUSD=X",
        "USDCAD": "USDCAD=X"
    }
    results = {}
    for name, symbol in main_symbols.items():
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

@st.cache_data(ttl=600)
def get_economic_news():
    try:
        url = f"https://newsapi.org/v2/everything?q=gold OR forex OR economy&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=5"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get('articles', [])
            news_list = []
            for art in articles[:5]:
                news_list.append({
                    'title': art.get('title', ''),
                    'source': art.get('source', {}).get('name', ''),
                    'publishedAt': art.get('publishedAt', ''),
                    'url': art.get('url', '')
                })
            return news_list
    except:
        pass
    return []

# ==========================================
# باقي الدوال (المؤشرات، SMC، TBS، إلخ) كما هي
# ==========================================
# ... (سيتم تضمينها في الكود النهائي)

# ==========================================
# الواجهة الرئيسية (نفسها)
# ==========================================
# ... (سيتم تضمينها في الكود النهائي)

# ==========================================
# تذييل
# ==========================================
st.markdown(f"""
<div class="footer">
    <span class="brand">▲ BLACK PYRAMID v2002</span> • Advanced Trading Intelligence<br>
    SMC/ICT • Liquidity (BSL/SSL) • SMR • Patterns • TBS • MTF • Integrated Signals • Stop Loss & Targets
</div>
""", unsafe_allow_html=True)
