# ==========================================
# BLACK PYRAMID – الإصدار 2004 (Pro)
# تاريخ التحديث: 2026-08-29
# التحديثات الاحترافية:
# - VRSI (Volume-Weighted RSI) بدلاً من RSI التقليدي (فترة 14، مستويات 80/20)
# - تعزيز VWAP مع شرح Session-based
# - إضافة مستويات فيبوناتشي 78.6% و 88.6%
# - تحديث لوحة التحكم لتعكس الإعدادات الجديدة
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
import time
import re

# ==========================================
# 🔑 API Keys
# ==========================================
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
NEWS_API_KEY = "b45e3a2b60d74c1bb1e8ddcdfa513bea"
ALPHA_VANTAGE_KEY = "017FGHT0JLG80XTG"

# ==========================================
# إعداد الصفحة
# ==========================================
st.set_page_config(
    page_title="Black Pyramid Pro",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🖤 الهوية البصرية (نفس السابق مع تحديث بسيط)
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    .main-title, .signal-text, .price-value { font-family: 'Orbitron', sans-serif !important; letter-spacing: 3px; }
    .main-subtitle, .price-label, .signal-confidence, .footer { font-family: 'Inter', sans-serif !important; letter-spacing: 1px; }
    html, body, .stApp { background: #0a0a0a !important; margin: 0 !important; padding: 0 !important; }
    .stApp { position: relative !important; background: #0a0a0a !important; min-height: 100vh !important; }
    .stApp::before {
        content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: url('https://raw.githubusercontent.com/kamelehab04-dotcom/gold-streamlit/main/file_00000000a364820aa4218d02627011f1.png') !important;
        background-size: cover !important; background-position: center !important;
        opacity: 0.25 !important; pointer-events: none !important; z-index: 0 !important;
    }
    .stApp::after {
        content: ''; position: fixed; top: -50%; left: -50%; width: 200%; height: 200%;
        background: radial-gradient(ellipse at 30% 20%, rgba(255,215,0,0.03) 0%, transparent 50%),
                    radial-gradient(ellipse at 70% 80%, rgba(255,215,0,0.02) 0%, transparent 50%);
        pointer-events: none; z-index: 0; animation: bgPulse 10s ease-in-out infinite;
    }
    @keyframes bgPulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
    .main-header, .price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone, .target-zone, .stop-loss-level, .reversal-alert, .news-card, .news-alert, .explanation-box, .stButton button, .stSelectbox, .stDataFrame, .stMetric, .stPlotlyChart, .stTabs { position: relative !important; z-index: 1 !important; }
    .css-1d391kg, .css-1d391kg * { background: rgba(10,10,10,0.85) !important; backdrop-filter: blur(10px) !important; border-right: 1px solid rgba(255,215,0,0.05) !important; }
    .main-header { display: flex; justify-content: flex-end; align-items: center; padding: 10px 25px !important; min-height: 55px !important; background: rgba(0,0,0,0.5) !important; backdrop-filter: blur(8px) !important; border-radius: 12px !important; margin-bottom: 15px !important; border: 1px solid rgba(255,215,0,0.08) !important; }
    .main-header .main-title { font-size: 1.2rem !important; color: #ffd700 !important; font-weight: 700 !important; letter-spacing: 2px !important; }
    .main-header .main-subtitle { font-size: 0.55rem !important; color: #666 !important; letter-spacing: 1px !important; }
    .price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone, .target-zone, .stop-loss-level, .reversal-alert { background: rgba(10,10,10,0.75) !important; backdrop-filter: blur(6px) !important; border: 1px solid rgba(255,215,0,0.10) !important; border-radius: 12px !important; box-shadow: 0 4px 30px rgba(0,0,0,0.5) !important; }
    .price-value { color: #fff !important; }
    .price-label { color: #888 !important; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 2px; }
    .signal-box { border: 2px solid #ffd700 !important; }
    .suggested-trade { border: 2px solid #00ff88 !important; background: rgba(0,10,5,0.80) !important; }
    .target-zone { border-left: 4px solid #ffd700 !important; background: rgba(255,215,0,0.04) !important; padding: 8px 12px; margin: 4px 0; }
    .target-zone:last-child { border-left-color: #00ff88 !important; }
    .stop-loss-level { border-left: 4px solid #ff4444 !important; background: rgba(255,68,68,0.04) !important; padding: 8px 12px; margin: 4px 0; }
    .entry-zone { border-left: 4px solid #00ff88 !important; background: rgba(0,255,136,0.04) !important; padding: 8px 12px; margin: 4px 0; }
    .trade-row { border-left: 4px solid #ffd700 !important; padding: 10px 15px; margin: 5px 0; }
    .footer { text-align: center; padding: 15px; color: #444; font-size: 0.65rem; border-top: 1px solid rgba(255,215,0,0.05); margin-top: 30px; letter-spacing: 1px; }
    .footer .brand { color: #ffd700; font-weight: 600; }
    .stButton button { background: linear-gradient(135deg, #ffd700 0%, #d4a800 100%) !important; color: #000 !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; padding: 8px 16px !important; width: 100% !important; transition: all 0.3s ease !important; }
    .stButton button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(255,215,0,0.2) !important; }
    .explanation-box { background: rgba(10,10,10,0.80) !important; border: 1px solid rgba(255,215,0,0.05) !important; border-radius: 10px !important; padding: 15px !important; margin: 8px 0 !important; color: #bbb !important; font-size: 0.9rem !important; line-height: 1.6 !important; }
    .news-card { background: rgba(10,10,10,0.65) !important; border-left: 3px solid #ffd700 !important; border-radius: 8px !important; padding: 10px 15px !important; margin: 5px 0 !important; }
    .news-title { color: #eee !important; font-weight: 500 !important; font-size: 0.9rem !important; }
    .news-date { color: #666 !important; font-size: 0.7rem !important; }
    .news-alert { background: rgba(255,68,68,0.15) !important; border: 2px solid #ff4444 !important; border-radius: 10px !important; padding: 15px !important; margin: 10px 0 !important; animation: pulseAlert 2s ease-in-out infinite; }
    .news-alert-bullish { background: rgba(0,255,136,0.10) !important; border: 2px solid #00ff88 !important; border-radius: 10px !important; padding: 15px !important; margin: 10px 0 !important; animation: pulseAlert 2s ease-in-out infinite; }
    @keyframes pulseAlert { 0%,100% { opacity: 0.8; transform: scale(1); } 50% { opacity: 1; transform: scale(1.01); } }
    .reversal-alert { border: 1px solid #ff4444 !important; background: rgba(255,68,68,0.04) !important; padding: 10px 15px !important; margin: 5px 0 !important; border-radius: 8px !important; font-size: 0.85rem !important; }
    .pattern-badge { display: inline-block; background: rgba(255,215,0,0.08) !important; border: 1px solid rgba(255,215,0,0.12) !important; border-radius: 16px !important; padding: 3px 12px !important; margin: 2px !important; font-size: 0.7rem !important; color: #ffd700 !important; }
    .impact-high { color: #ff4444 !important; font-weight: bold; }
    .impact-medium { color: #ffaa00 !important; font-weight: bold; }
    .impact-low { color: #00ff88 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">▲ BLACK PYRAMID PRO ▲</div>
        <div class="main-subtitle">VRSI • VWAP Session • Fibonacci 78.6% & 88.6% • Smart Money • Auto-Risk</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# قائمة الأزواج (كما هي)
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
    "ETH/USD (Ethereum)": "ETH-USD",
    "XRP/USD (Ripple)": "XRP-USD",
    "SOL/USD (Solana)": "SOL-USD",
    "ADA/USD (Cardano)": "ADA-USD"
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
if "currency_indices" not in st.session_state:
    st.session_state.currency_indices = None
if "account_balance" not in st.session_state:
    st.session_state.account_balance = 100000

# ==========================================
# دوال جلب البيانات (نفس السابق)
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
                return float(data.get('price', 0)), float(data.get('change_percent', 0))
        except:
            pass
    if symbol == "SI=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAG/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0)), float(data.get('change_percent', 0))
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
def get_historical_data(symbol, period="1mo", interval="1h", max_retries=5):
    alt = {
        "GC=F": ["XAUUSD=X", "GOLD"],
        "SI=F": ["XAGUSD=X", "SILVER"],
        "DX-Y.NYB": ["DX=F", "DXY"],
        "BTC-USD": ["BTCUSD=X"],
        "ETH-USD": ["ETHUSD=X"],
        "XRP-USD": ["XRPUSD=X"],
        "SOL-USD": ["SOLUSD=X"],
        "ADA-USD": ["ADAUSD=X"]
    }
    symbols_to_try = [symbol] + alt.get(symbol, [])
    for attempt in range(max_retries):
        for sym in symbols_to_try:
            try:
                ticker = yf.Ticker(sym)
                df = ticker.history(period=period, interval=interval)
                if not df.empty:
                    df.columns = [col.lower() for col in df.columns]
                    return df
            except:
                continue
        if attempt < max_retries - 1:
            time.sleep(3)
    return None

# ==========================================
# مؤشرات العملات (نفس السابق مع إمكانية تخصيص الأوزان)
# ==========================================
@st.cache_data(ttl=300)
def calculate_currency_indices(data_dict, base_date=None, weights=None):
    indices = {}
    currency_pairs = {
        'EUR': ['EURUSD=X', 'EURGBP=X', 'EURJPY=X', 'EURCHF=X', 'EURAUD=X', 'EURNZD=X', 'EURCAD=X'],
        'GBP': ['GBPUSD=X', 'GBPEUR=X', 'GBPJPY=X', 'GBPCHF=X', 'GBPAUD=X', 'GBPNZD=X', 'GBPCAD=X'],
        'JPY': ['USDJPY=X', 'EURJPY=X', 'GBPJPY=X', 'AUDJPY=X', 'NZDJPY=X', 'CADJPY=X', 'CHFJPY=X'],
        'CHF': ['USDCHF=X', 'EURCHF=X', 'GBPCHF=X', 'AUDCHF=X', 'NZDCHF=X', 'CADCHF=X', 'JPYCHF=X'],
        'AUD': ['AUDUSD=X', 'AUDJPY=X', 'AUDCHF=X', 'AUDNZD=X', 'AUDCAD=X', 'AUDGBP=X', 'AUDEUR=X'],
        'NZD': ['NZDUSD=X', 'NZDJPY=X', 'NZDCHF=X', 'NZDCAD=X', 'NZDEUR=X', 'NZDGBP=X', 'NZDAUD=X'],
        'CAD': ['USDCAD=X', 'CADJPY=X', 'CADCHF=X', 'CADAUD=X', 'CADNZD=X', 'CADEUR=X', 'CADGBP=X']
    }
    default_weights = {pair: 1 for pairs in currency_pairs.values() for pair in pairs}
    if weights:
        default_weights.update(weights)
    
    for currency, pair_list in currency_pairs.items():
        valid_series = []; valid_pairs = []
        for pair in pair_list:
            if pair in data_dict and data_dict[pair] is not None and not data_dict[pair].empty:
                valid_series.append(data_dict[pair]['close'])
                valid_pairs.append(pair)
        if valid_series:
            common_idx = valid_series[0].index
            for ser in valid_series[1:]:
                common_idx = common_idx.intersection(ser.index)
            if len(common_idx) > 10:
                weighted_sum = pd.Series(0, index=common_idx)
                total_weight = 0
                for pair, ser in zip(valid_pairs, valid_series):
                    w = default_weights.get(pair, 1)
                    weighted_sum += ser.loc[common_idx] * w
                    total_weight += w
                avg_series = weighted_sum / total_weight
                if base_date is None:
                    base_value = avg_series.iloc[0]
                else:
                    base_value = avg_series.loc[base_date] if base_date in avg_series.index else avg_series.iloc[0]
                indices[currency] = (avg_series / base_value) * 100
    return indices

# ==========================================
# المؤشرات الاحترافية (الجديدة والمعدلة)
# ==========================================

# 1. VRSI – Volume-Weighted RSI (بديل RSI التقليدي)
def calc_vrsi(data, volume, period=14):
    """
    حساب مؤشر القوة النسبية الموزون بالحجم.
    data: سلسلة الأسعار (close)
    volume: سلسلة الحجم
    period: الفترة (افتراضي 14)
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # ترجيح RSI بالحجم النسبي
    vol_ma = volume.rolling(window=period).mean()
    vol_ratio = volume / vol_ma
    vol_ratio = vol_ratio.fillna(1).clip(0.5, 2)  # الحد من الترجيح الشاذ
    vrsi = rsi * vol_ratio
    vrsi = vrsi.clip(0, 100)
    return vrsi

# 2. VWAP (نفس السابق لكن مع تأكيد Session-based)
def calc_vwap(df):
    """حساب VWAP التراكمي (الجلسة)"""
    return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

# 3. Fibonacci المحسّن مع مستويات 78.6% و 88.6%
def calc_fibonacci_levels_pro(high, low, current_price):
    diff = high - low
    if diff == 0:
        return {}
    return {
        'fib_0': high,
        'fib_236': high - diff * 0.236,
        'fib_382': high - diff * 0.382,
        'fib_500': high - diff * 0.5,
        'fib_618': high - diff * 0.618,
        'fib_786': high - diff * 0.786,   # المستوى الذهبي المخفي
        'fib_886': high - diff * 0.886,   # المستوى التوافقي
        'fib_100': low
    }

# ==========================================
# باقي المؤشرات الأساسية (ATR, MACD, BB, ADX, Ichimoku, MFI)
# ==========================================
def calc_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
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
    return sma + (std * std_dev), sma, sma - (std * std_dev)

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

def calc_ichimoku(df):
    high, low, close = df['high'], df['low'], df['close']
    tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
    kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
    chikou = close.shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou

def calc_mfi(df, period=14):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    return 100 - (100 / (1 + positive_flow / negative_flow))

# ==========================================
# Liquidity, SMR, SMC, TBS, Patterns (نفس السابق)
# ==========================================
def detect_liquidity_levels(df, lookback=50):
    return df['high'].rolling(window=lookback).max(), df['low'].rolling(window=lookback).min()

def detect_smart_money_reversal(df, lookback=20):
    df = df.copy()
    df['smr_bullish'] = False
    df['smr_bearish'] = False
    for i in range(lookback, len(df)):
        high_liquidity = df['high'].iloc[i-lookback:i].max()
        low_liquidity = df['low'].iloc[i-lookback:i].min()
        if df['high'].iloc[i] > high_liquidity and df['close'].iloc[i] < df['open'].iloc[i]:
            df.loc[df.index[i], 'smr_bearish'] = True
        if df['low'].iloc[i] < low_liquidity and df['close'].iloc[i] > df['open'].iloc[i]:
            df.loc[df.index[i], 'smr_bullish'] = True
    return df

def analyze_smc_ict(df):
    df = df.copy()
    df['order_block_bullish'] = False
    df['order_block_bearish'] = False
    df['fvg_bullish'] = False
    df['fvg_bearish'] = False
    df['liquidity_sweep_bullish'] = False
    df['liquidity_sweep_bearish'] = False
    df['bos_bullish'] = False
    df['bos_bearish'] = False
    df['mss_bullish'] = False
    df['mss_bearish'] = False
    df['in_discount'] = False
    df['in_premium'] = False
    df['tbs_bullish'] = False
    df['tbs_bearish'] = False
    df['bsl'] = np.nan
    df['ssl'] = np.nan
    df['smr_bullish'] = False
    df['smr_bearish'] = False
    bsl, ssl = detect_liquidity_levels(df, lookback=50)
    df['bsl'] = bsl
    df['ssl'] = ssl
    df = detect_smart_money_reversal(df, lookback=20)
    for i in range(3, len(df)):
        if df['close'].iloc[i] > df['open'].iloc[i]:
            body = df['close'].iloc[i] - df['open'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                df.loc[df.index[i-1], 'order_block_bullish'] = True
        if df['close'].iloc[i] < df['open'].iloc[i]:
            body = df['open'].iloc[i] - df['close'].iloc[i]
            avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
            if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                df.loc[df.index[i-1], 'order_block_bearish'] = True
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bullish'] = True
        if df['high'].iloc[i] < df['low'].iloc[i-2]:
            df.loc[df.index[i], 'fvg_bearish'] = True
    for i in range(10, len(df)):
        recent_lows = df['low'].iloc[i-10:i].tolist()
        if df['low'].iloc[i] < min(recent_lows[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bullish'] = True
        recent_highs = df['high'].iloc[i-10:i].tolist()
        if df['high'].iloc[i] > max(recent_highs[:-1]):
            df.loc[df.index[i], 'liquidity_sweep_bearish'] = True
    for i in range(5, len(df)):
        if df['close'].iloc[i] > df['high'].iloc[i-5:i].max():
            df.loc[df.index[i], 'bos_bullish'] = True
        if df['close'].iloc[i] < df['low'].iloc[i-5:i].min():
            df.loc[df.index[i], 'bos_bearish'] = True
    for i in range(3, len(df)):
        if df['bos_bearish'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[i-2:i].max():
            df.loc[df.index[i], 'mss_bullish'] = True
        if df['bos_bullish'].iloc[i-1] and df['close'].iloc[i] < df['low'].iloc[i-2:i].min():
            df.loc[df.index[i], 'mss_bearish'] = True
    for i in range(50, len(df)):
        range_high = df['high'].iloc[i-50:i].max()
        range_low = df['low'].iloc[i-50:i].min()
        if range_high != range_low:
            discount = range_low + (range_high - range_low) * 0.382
            premium = range_high - (range_high - range_low) * 0.382
            if df['close'].iloc[i] <= discount:
                df.loc[df.index[i], 'in_discount'] = True
            if df['close'].iloc[i] >= premium:
                df.loc[df.index[i], 'in_premium'] = True
    tbs_type, _, _, _ = detect_tbs(df)
    if tbs_type == "BULLISH":
        df.loc[df.index[-1], 'tbs_bullish'] = True
    elif tbs_type == "BEARISH":
        df.loc[df.index[-1], 'tbs_bearish'] = True
    return df

def detect_tbs(df, lookback=20, body_multiplier=1.5):
    if len(df) < lookback + 2:
        return None, None, None, None
    last_idx = len(df) - 1
    current = df.iloc[last_idx]
    lookback_high = df['high'].iloc[last_idx - lookback:last_idx].max()
    lookback_low = df['low'].iloc[last_idx - lookback:last_idx].min()
    avg_body = abs(df['close'] - df['open']).iloc[last_idx - lookback:last_idx].mean()
    current_body = abs(current['close'] - current['open'])
    if current_body < avg_body * body_multiplier:
        return None, None, None, None
    if current['high'] > lookback_high and current['close'] > lookback_high:
        return "BEARISH", current['close'], current['low'], lookback_high
    elif current['low'] < lookback_low and current['close'] < lookback_low:
        return "BULLISH", current['close'], current['high'], lookback_low
    return None, None, None, None

def find_peaks_troughs(series, order=5):
    peaks, troughs = [], []
    for i in range(order, len(series) - order):
        if all(series[i] > series[i-j] for j in range(1, order+1)) and all(series[i] > series[i+j] for j in range(1, order+1)):
            peaks.append((i, series[i]))
        if all(series[i] < series[i-j] for j in range(1, order+1)) and all(series[i] < series[i+j] for j in range(1, order+1)):
            troughs.append((i, series[i]))
    return peaks, troughs

def detect_head_shoulders(df, lookback=50):
    if len(df) < lookback:
        return None, 0
    recent_highs = df['high'].iloc[-lookback:].values
    peaks, _ = find_peaks_troughs(recent_highs, order=3)
    if len(peaks) >= 3:
        head_idx = np.argmax([p[1] for p in peaks])
        if head_idx > 0 and head_idx < len(peaks) - 1:
            left = peaks[head_idx - 1][1]
            head = peaks[head_idx][1]
            right = peaks[head_idx + 1][1]
            if head > left and head > right and abs(left - right) / left < 0.05:
                return "HEAD_AND_SHOULDERS", 5
    return None, 0

def detect_double_top_bottom(df, lookback=50):
    if len(df) < lookback:
        return None, 0
    recent_highs = df['high'].iloc[-lookback:].values
    recent_lows = df['low'].iloc[-lookback:].values
    peaks, _ = find_peaks_troughs(recent_highs, order=3)
    _, troughs = find_peaks_troughs(recent_lows, order=3)
    if len(peaks) >= 2:
        last_two_peaks = sorted(peaks[-2:], key=lambda x: x[0])
        if abs(last_two_peaks[-1][1] - last_two_peaks[-2][1]) / last_two_peaks[-2][1] < 0.03:
            return "DOUBLE_TOP", 4
    if len(troughs) >= 2:
        last_two_troughs = sorted(troughs[-2:], key=lambda x: x[0])
        if abs(last_two_troughs[-1][1] - last_two_troughs[-2][1]) / last_two_troughs[-2][1] < 0.03:
            return "DOUBLE_BOTTOM", 4
    return None, 0

def detect_triangle_pattern(df, lookback=40):
    if len(df) < lookback:
        return None, 0
    recent_data = df.iloc[-lookback:]
    highs = recent_data['high'].values
    lows = recent_data['low'].values
    x = np.arange(len(highs))
    slope_highs = np.polyfit(x, highs, 1)[0]
    slope_lows = np.polyfit(x, lows, 1)[0]
    if slope_lows > 0.01 and abs(slope_highs) < 0.005:
        return "ASCENDING_TRIANGLE", 3
    if slope_highs < -0.01 and abs(slope_lows) < 0.005:
        return "DESCENDING_TRIANGLE", 3
    return None, 0

def analyze_chart_patterns(df):
    patterns = []
    total_score = 0
    p, s = detect_head_shoulders(df)
    if p:
        patterns.append({"pattern": p, "score": s, "direction": "BEARISH"})
        total_score += s
    p, s = detect_double_top_bottom(df)
    if p:
        direction = "BEARISH" if "DOUBLE_TOP" in p else "BULLISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s
    p, s = detect_triangle_pattern(df)
    if p:
        direction = "BULLISH" if "ASCENDING" in p else "BEARISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s
    return patterns, total_score

# ==========================================
# دوال الأخبار (نفس السابق)
# ==========================================
POSITIVE_KEYWORDS = ["higher", "increase", "growth", "positive", "strong", "beat", "surplus", "rally", "bullish", "up", "gain", "profit", "support", "stimulus", "cut", "reduce", "lower", "drop", "pullback", "correction", "recovery"]
NEGATIVE_KEYWORDS = ["lower", "decrease", "decline", "negative", "weak", "miss", "deficit", "crash", "bearish", "down", "loss", "concern", "fear", "uncertainty", "hike", "raise", "higher rates", "inflation", "recession", "crisis", "war", "conflict", "sanctions", "default"]
ECONOMIC_INDICATORS = {"CPI": "تضخم أسعار المستهلكين", "PPI": "تضخم أسعار المنتجين", "GDP": "الناتج المحلي الإجمالي", "NFP": "الوظائف غير الزراعية", "Unemployment": "البطالة", "PMI": "مؤشر مديري المشتريات", "Fed": "الاحتياطي الفيدرالي", "FOMC": "لجنة السوق المفتوحة", "ECB": "البنك المركزي الأوروبي", "BOE": "بنك إنجلترا", "BOJ": "بنك اليابان", "Rate": "سعر الفائدة", "Inflation": "التضخم", "Retail Sales": "مبيعات التجزئة", "Durable Goods": "السلع المعمرة", "Consumer Confidence": "ثقة المستهلك"}

@st.cache_data(ttl=60)
def fetch_news():
    try:
        url = f"https://newsapi.org/v2/everything?q=forex OR gold OR economy OR inflation OR fed OR interest rates OR stock market&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=15"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('articles', [])
    except:
        pass
    return []

def analyze_news_impact(articles):
    analyzed_news = []
    for article in articles[:8]:
        title = article.get('title', '')
        description = article.get('description', '')
        content = f"{title} {description}".lower()
        indicator = None
        for key, name in ECONOMIC_INDICATORS.items():
            if key.lower() in content or name in content:
                indicator = name
                break
        positive_score = sum(1 for word in POSITIVE_KEYWORDS if word in content)
        negative_score = sum(1 for word in NEGATIVE_KEYWORDS if word in content)
        if positive_score > negative_score:
            impact = "BULLISH"; impact_text = "📈 إيجابي (صاعد)"; color = "#00ff88"
        elif negative_score > positive_score:
            impact = "BEARISH"; impact_text = "📉 سلبي (هابط)"; color = "#ff4444"
        else:
            impact = "NEUTRAL"; impact_text = "➖ محايد"; color = "#ffaa00"
        total_score = positive_score + negative_score
        if total_score >= 5: strength = "HIGH"; strength_text = "🔴 قوي"
        elif total_score >= 3: strength = "MEDIUM"; strength_text = "🟡 متوسط"
        else: strength = "LOW"; strength_text = "🟢 ضعيف"
        analyzed_news.append({"title": title, "description": description, "source": article.get('source', {}).get('name', 'Unknown'), "publishedAt": article.get('publishedAt', ''), "url": article.get('url', ''), "indicator": indicator, "impact": impact, "impact_text": impact_text, "strength": strength, "strength_text": strength_text, "color": color, "positive_score": positive_score, "negative_score": negative_score})
    return analyzed_news

def get_market_sentiment(analyzed_news):
    bullish_count = sum(1 for n in analyzed_news if n['impact'] == "BULLISH")
    bearish_count = sum(1 for n in analyzed_news if n['impact'] == "BEARISH")
    neutral_count = sum(1 for n in analyzed_news if n['impact'] == "NEUTRAL")
    total = bullish_count + bearish_count + neutral_count
    if total == 0: return "NEUTRAL", 0
    sentiment_score = (bullish_count - bearish_count) / total * 100
    if sentiment_score > 30: return "BULLISH", sentiment_score
    elif sentiment_score < -30: return "BEARISH", sentiment_score
    else: return "NEUTRAL", sentiment_score

def get_economic_calendar():
    return [{"time": "08:30", "event": "مؤشر أسعار المستهلكين (CPI)", "impact": "HIGH", "previous": "3.2%", "forecast": "3.0%"},
            {"time": "10:00", "event": "مبيعات التجزئة", "impact": "MEDIUM", "previous": "0.5%", "forecast": "0.3%"},
            {"time": "14:00", "event": "قرار سعر الفائدة - الاحتياطي الفيدرالي", "impact": "HIGH", "previous": "5.50%", "forecast": "5.50%"},
            {"time": "16:30", "event": "محضر اجتماع FOMC", "impact": "HIGH", "previous": "-", "forecast": "-"}]

# ==========================================
# الإشارة المتكاملة (محدثة لاستخدام VRSI و فيبوناتشي المحسّن)
# ==========================================
def generate_advanced_signal(df, current_price, symbol="", news_sentiment=None, currency_indices=None, params=None):
    if df is None or len(df) < 100:
        return "WAIT", 50, 0, {}, [], None, None, None, None

    p = params or {}
    vrsi_period = p.get('vrsi_period', 14)
    adx_threshold = p.get('adx_threshold', 25)
    bb_period = p.get('bb_period', 20)
    bb_std = p.get('bb_std', 2)
    confidence_threshold = p.get('confidence_threshold', 60)

    df_smc = analyze_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    patterns, _ = analyze_chart_patterns(df)
    tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs(df)

    last = df.iloc[-1]
    scores = {'BUY': 0, 'SELL': 0}
    details = {}
    weights = {'vrsi': 3, 'macd': 2, 'bb': 2, 'vwap': 1, 'adx': 1, 'ichimoku': 3, 'smc': 3, 'patterns': 4, 'tbs': 4, 'mfi': 3, 'smr': 3, 'currency': 3, 'fibonacci': 2}

    # ===== VRSI (بدلاً من RSI) =====
    if 'vrsi' in df.columns and not pd.isna(last['vrsi']):
        vrsi = last['vrsi']
        if vrsi < 20:
            scores['BUY'] += weights['vrsi']
            details['VRSI'] = f"مفرط البيع بالحجم ({vrsi:.1f}) +{weights['vrsi']}"
        elif vrsi > 80:
            scores['SELL'] += weights['vrsi']
            details['VRSI'] = f"مفرط الشراء بالحجم ({vrsi:.1f}) +{weights['vrsi']}"
        else:
            details['VRSI'] = f"محايد ({vrsi:.1f})"

    # MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns and not pd.isna(last['macd']):
        if last['macd'] > last['macd_signal'] and last['macd'] > 0:
            scores['BUY'] += weights['macd']; details['MACD'] = f"إيجابي +{weights['macd']}"
        elif last['macd'] < last['macd_signal'] and last['macd'] < 0:
            scores['SELL'] += weights['macd']; details['MACD'] = f"سلبي +{weights['macd']}"
        else: details['MACD'] = "محايد"

    # Bollinger
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and not pd.isna(last['bb_upper']):
        if current_price <= last['bb_lower'] * 1.005:
            scores['BUY'] += weights['bb']; details['BB'] = f"قرب الحد السفلي +{weights['bb']}"
        elif current_price >= last['bb_upper'] * 0.995:
            scores['SELL'] += weights['bb']; details['BB'] = f"قرب الحد الأعلى +{weights['bb']}"
        else: details['BB'] = "وسط النطاق"

    # VWAP (مع شرح)
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += weights['vwap']; details['VWAP'] = f"فوق VWAP (مؤسسات شراء) +{weights['vwap']}"
        else:
            scores['SELL'] += weights['vwap']; details['VWAP'] = f"تحت VWAP (مؤسسات بيع) +{weights['vwap']}"

    # ADX
    if 'adx' in df.columns and not pd.isna(last['adx']):
        if last['adx'] > adx_threshold:
            if df['close'].iloc[-1] > df['close'].iloc[-5]:
                scores['BUY'] += 1; details['ADX'] = f"اتجاه قوي صاعد +1"
            else:
                scores['SELL'] += 1; details['ADX'] = f"اتجاه قوي هابط +1"
        else: details['ADX'] = f"اتجاه ضعيف ({last['adx']:.1f})"

    # Ichimoku
    if 'senkou_a' in df.columns and 'senkou_b' in df.columns and 'chikou' in df.columns:
        if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']) and not pd.isna(last['chikou']):
            if current_price > last['senkou_a'] and current_price > last['senkou_b']:
                scores['BUY'] += weights['ichimoku']; details['Ichimoku'] = f"فوق السحابة +{weights['ichimoku']}"
            elif current_price < last['senkou_a'] and current_price < last['senkou_b']:
                scores['SELL'] += weights['ichimoku']; details['Ichimoku'] = f"تحت السحابة +{weights['ichimoku']}"
            else: details['Ichimoku'] = "داخل السحابة"

    # SMC
    if last_smc.get('order_block_bullish', False):
        scores['BUY'] += weights['smc']; details['SMC'] = f"كتلة أوامر شراء +{weights['smc']}"
    elif last_smc.get('order_block_bearish', False):
        scores['SELL'] += weights['smc']; details['SMC'] = f"كتلة أوامر بيع +{weights['smc']}"
    elif last_smc.get('fvg_bullish', False):
        scores['BUY'] += weights['smc']//2; details['SMC'] = f"FVG شراء +{weights['smc']//2}"
    elif last_smc.get('fvg_bearish', False):
        scores['SELL'] += weights['smc']//2; details['SMC'] = f"FVG بيع +{weights['smc']//2}"
    elif last_smc.get('liquidity_sweep_bullish', False):
        scores['BUY'] += weights['smc']//2; details['SMC'] = f"اجتياح سيولة شراء +{weights['smc']//2}"
    elif last_smc.get('liquidity_sweep_bearish', False):
        scores['SELL'] += weights['smc']//2; details['SMC'] = f"اجتياح سيولة بيع +{weights['smc']//2}"
    elif last_smc.get('mss_bullish', False):
        scores['BUY'] += weights['smc']; details['SMC'] = f"تحول هيكل صاعد +{weights['smc']}"
    elif last_smc.get('mss_bearish', False):
        scores['SELL'] += weights['smc']; details['SMC'] = f"تحول هيكل هابط +{weights['smc']}"
    elif last_smc.get('in_discount', False):
        scores['BUY'] += weights['smc']//2; details['SMC'] = f"منطقة خصم +{weights['smc']//2}"
    elif last_smc.get('in_premium', False):
        scores['SELL'] += weights['smc']//2; details['SMC'] = f"منطقة قمة +{weights['smc']//2}"
    else: details['SMC'] = "لا توجد إشارة SMC"

    # SMR
    if last_smc.get('smr_bullish', False):
        scores['BUY'] += weights['smr']; details['SMR'] = f"انعكاس Smart Money صاعد +{weights['smr']}"
    elif last_smc.get('smr_bearish', False):
        scores['SELL'] += weights['smr']; details['SMR'] = f"انعكاس Smart Money هابط +{weights['smr']}"
    else: details['SMR'] = "لا توجد إشارة SMR"

    # Patterns
    if patterns:
        for p in patterns:
            if p['direction'] == 'BULLISH':
                scores['BUY'] += weights['patterns']; details['Pattern'] = f"{p['pattern']} (صاعد) +{weights['patterns']}"
            else:
                scores['SELL'] += weights['patterns']; details['Pattern'] = f"{p['pattern']} (هابط) +{weights['patterns']}"
    else: details['Pattern'] = "لا توجد نماذج"

    # TBS
    if tbs_type == "BULLISH":
        scores['BUY'] += weights['tbs']; details['TBS'] = f"TBS شراء (الدخول: {tbs_entry:.4f}) +{weights['tbs']}"
    elif tbs_type == "BEARISH":
        scores['SELL'] += weights['tbs']; details['TBS'] = f"TBS بيع (الدخول: {tbs_entry:.4f}) +{weights['tbs']}"
    else: details['TBS'] = "لا توجد إشارة TBS"

    # MFI
    if 'mfi' in df.columns and not pd.isna(last['mfi']):
        mfi = last['mfi']
        if mfi < 20:
            scores['BUY'] += weights['mfi']; details['MFI'] = f"مفرط البيع ({mfi:.1f}) +{weights['mfi']}"
        elif mfi > 80:
            scores['SELL'] += weights['mfi']; details['MFI'] = f"مفرط الشراء ({mfi:.1f}) +{weights['mfi']}"
        else: details['MFI'] = f"محايد ({mfi:.1f})"

    # ===== Fibonacci المحسّن (مع 78.6% و 88.6%) =====
    recent_high = df['high'].iloc[-50:].max()
    recent_low = df['low'].iloc[-50:].min()
    fib = calc_fibonacci_levels_pro(recent_high, recent_low, current_price)
    if fib:
        if current_price > fib.get('fib_618', current_price):
            scores['BUY'] += weights['fibonacci']
            details['Fibonacci'] = f"فوق 61.8% (قوي) +{weights['fibonacci']}"
        elif current_price < fib.get('fib_382', current_price):
            scores['SELL'] += weights['fibonacci']
            details['Fibonacci'] = f"تحت 38.2% (قوي) +{weights['fibonacci']}"
        # المستويات الذهبية
        if fib.get('fib_786', current_price) and current_price < fib['fib_786'] < current_price * 1.01:
            details['Fibonacci_786'] = "⚠️ قرب 78.6% (آخر خط دفاع)"
        if fib.get('fib_886', current_price) and current_price < fib['fib_886'] < current_price * 1.01:
            details['Fibonacci_886'] = "🔴 قرب 88.6% (نموذج توافقي)"

    # ===== تأثير الأخبار =====
    if news_sentiment:
        sentiment, score = news_sentiment
        if sentiment == "BULLISH":
            scores['BUY'] += 2; details['News_Sentiment'] = f"📈 أخبار إيجابية ({score:.0f}%) +2 BUY"
        elif sentiment == "BEARISH":
            scores['SELL'] += 2; details['News_Sentiment'] = f"📉 أخبار سلبية ({score:.0f}%) +2 SELL"
        else: details['News_Sentiment'] = "➖ أخبار محايدة"

    # ===== فلتر العملات =====
    if currency_indices is not None and len(currency_indices) > 0:
        base_cur = None; quote_cur = None
        for cur in ['EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD']:
            if symbol.startswith(cur): base_cur = cur
            if symbol.endswith(cur + '=X') or symbol.endswith(cur + '-USD') or symbol.endswith(cur + '=F'):
                quote_cur = cur
        if symbol == "GC=F" or symbol == "XAUUSD=X": base_cur = "XAU"; quote_cur = "USD"
        if symbol == "DX-Y.NYB": base_cur = "USD"; quote_cur = "DXY"
        if base_cur and quote_cur and base_cur in currency_indices and quote_cur in currency_indices:
            base_val = currency_indices[base_cur].iloc[-1]
            quote_val = currency_indices[quote_cur].iloc[-1]
            diff = base_val - quote_val
            if diff > 0.2:
                scores['BUY'] += weights['currency']; details['Currency_Filter'] = f"💪 {base_cur} أقوى من {quote_cur} ({diff:.2f}) +{weights['currency']}"
            elif diff < -0.2:
                scores['SELL'] += weights['currency']; details['Currency_Filter'] = f"💪 {quote_cur} أقوى من {base_cur} ({-diff:.2f}) +{weights['currency']}"
            else: details['Currency_Filter'] = f"⚖️ متعادلان ({diff:.2f})"

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

    if 'atr' in df.columns and len(df) > 50:
        current_atr = last['atr']; avg_atr = df['atr'].iloc[-50:].mean()
        if not pd.isna(current_atr) and not pd.isna(avg_atr):
            if current_atr < avg_atr * 0.7:
                confidence = confidence * 0.6; details['ATR_Filter'] = "⚠️ تقلب منخفض (إشارة ضعيفة)"

    if news_sentiment:
        sentiment, score = news_sentiment
        if abs(score) > 50:
            confidence = confidence * 0.7; details['News_Warning'] = f"⚠️ أخبار قوية قد تغير الاتجاه (ثقة مخفضة)"

    confidence = max(0, min(100, confidence))
    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)
    
    stop_loss = None; entry_price = None; targets = {}
    if signal in ["BUY", "SELL"] and confidence >= confidence_threshold:
        atr_value = last['atr'] if not pd.isna(last['atr']) else 10
        blocks = []
        start_idx = max(3, len(df) - 30)
        for i in range(start_idx, len(df) - 1):
            if df['close'].iloc[i] > df['open'].iloc[i]:
                body = df['close'].iloc[i] - df['open'].iloc[i]
                avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
                if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                    blocks.append(('bullish', df['low'].iloc[i-1], df['high'].iloc[i-1]))
            if df['close'].iloc[i] < df['open'].iloc[i]:
                body = df['open'].iloc[i] - df['close'].iloc[i]
                avg_range = (df['high'].iloc[i-3:i].max() - df['low'].iloc[i-3:i].min()) / 3
                if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                    blocks.append(('bearish', df['low'].iloc[i-1], df['high'].iloc[i-1]))
        order_blocks = blocks[-5:] if blocks else []
        entry_price = current_price
        if signal == "BUY":
            recent_low = df['low'].iloc[-20:].min()
            ob_low = min([block[1] for block in order_blocks if block[0] == 'bullish'], default=current_price - atr_value * 0.8)
            stop_loss = max(recent_low, ob_low, current_price - atr_value * 2.0)
            stop_loss = min(stop_loss, current_price - atr_value * 0.5)
        else:
            recent_high = df['high'].iloc[-20:].max()
            ob_high = max([block[2] for block in order_blocks if block[0] == 'bearish'], default=current_price + atr_value * 0.8)
            stop_loss = min(recent_high, ob_high, current_price + atr_value * 2.0)
            stop_loss = max(stop_loss, current_price + atr_value * 0.5)
        min_distance = atr_value * 0.3
        if signal == "BUY" and (entry_price - stop_loss) < min_distance:
            stop_loss = entry_price - min_distance
        elif signal == "SELL" and (stop_loss - entry_price) < min_distance:
            stop_loss = entry_price + min_distance
        risk = abs(entry_price - stop_loss) if stop_loss else atr_value
        if signal == "BUY":
            targets = {'target1': entry_price + risk * 1.0, 'target2': entry_price + risk * 1.5, 'target3': entry_price + risk * 2.0, 'risk_reward_1': 1.0, 'risk_reward_2': 1.5, 'risk_reward_3': 2.0, 'risk': risk}
        else:
            targets = {'target1': entry_price - risk * 1.0, 'target2': entry_price - risk * 1.5, 'target3': entry_price - risk * 2.0, 'risk_reward_1': 1.0, 'risk_reward_2': 1.5, 'risk_reward_3': 2.0, 'risk': risk}
    
    return signal, confidence, net_score, details, patterns, tbs_info, stop_loss, entry_price, targets

# ==========================================
# دوال مساعدة أخرى (MTF, Reversal, Explanation) – مختصرة
# ==========================================
def get_mtf_signal(symbol, current_price, interval='1h'):
    timeframes = ['15m', '1h', '4h'] if interval == '1h' else ['5m', '15m', '1h']
    signals = []
    for tf in timeframes:
        df = get_historical_data(symbol, period="5d", interval=tf)
        if df is not None and len(df) > 50:
            # نستخدم VRSI بدلاً من RSI في MTF أيضاً
            if 'volume' in df.columns:
                vrsi = calc_vrsi(df['close'], df['volume'], period=14).iloc[-1]
            else:
                vrsi = calc_rsi(df['close']).iloc[-1]  # fallback
            if vrsi < 20: signals.append(('BUY', tf))
            elif vrsi > 80: signals.append(('SELL', tf))
            else: signals.append(('NEUTRAL', tf))
    buy_count = sum(1 for s in signals if s[0] == 'BUY')
    sell_count = sum(1 for s in signals if s[0] == 'SELL')
    if buy_count > sell_count: return "BUY", buy_count - sell_count
    elif sell_count > buy_count: return "SELL", sell_count - buy_count
    else: return "NEUTRAL", 0

def detect_reversal(df, trade):
    if df is None or len(df) < 20: return False, "بيانات غير كافية"
    last = df.iloc[-1]; prev = df.iloc[-2]
    direction = trade["direction"]; entry = trade["entry"]
    current_price = last['close']; signals = []
    if 'vrsi' in df.columns and not pd.isna(last['vrsi']):
        vrsi = last['vrsi']
        if direction == "BUY":
            if vrsi > 80: signals.append("VRSI فوق 80 (تشبع شرائي)")
            elif vrsi < 20 and current_price < entry: signals.append("VRSI تحت 20 مع هبوط (ضعف)")
        else:
            if vrsi < 20: signals.append("VRSI تحت 20 (تشبع بيعي)")
            elif vrsi > 80 and current_price > entry: signals.append("VRSI فوق 80 مع صعود (ضعف)")
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if direction == "BUY":
            if last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                signals.append("MACD تقاطع هابط (انعكاس)")
        else:
            if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                signals.append("MACD تقاطع صاعد (انعكاس)")
    candle_range = abs(last['high'] - last['low'])
    if candle_range > 0:
        if direction == "BUY":
            upper_wick = last['high'] - max(last['close'], last['open'])
            if upper_wick > candle_range * 0.5: signals.append("شمعة انعكاس هابط (ذيل علوي طويل)")
        else:
            lower_wick = min(last['close'], last['open']) - last['low']
            if lower_wick > candle_range * 0.5: signals.append("شمعة انعكاس صاعد (ذيل سفلي طويل)")
    if direction == "BUY":
        recent_low = df['low'].iloc[-10:].min()
        if current_price < recent_low: signals.append(f"كسر الدعم القريب ({recent_low:.4f})")
    else:
        recent_high = df['high'].iloc[-10:].max()
        if current_price > recent_high: signals.append(f"كسر المقاومة القريبة ({recent_high:.4f})")
    if signals: return True, " | ".join(signals)
    return False, ""

def explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns, tbs_info, df, current_price, stop_loss, entry_price, targets):
    explanation = ""
    if signal == "BUY":
        explanation = "🔹 **قرار الشراء** بناءً على:\n"
        for k, v in details.items():
            if "+" in v or any(w in v for w in ["شراء", "صاعد", "فوق", "قرب الحد السفلي", "مفرط البيع", "قوي", "كتلة", "FVG", "اجتياح", "تحول", "خصم", "TBS", "MFI", "فيبوناتشي", "انعكاس Smart Money صاعد", "أخبار إيجابية", "أقوى"]):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≥5 للشراء)\n📈 **الثقة**: {confidence:.0f}%"
    elif signal == "SELL":
        explanation = "🔻 **قرار البيع** بناءً على:\n"
        for k, v in details.items():
            if "-" in v or any(w in v for w in ["بيع", "هابط", "تحت", "قرب الحد الأعلى", "مفرط الشراء", "قمة", "كتلة بيع", "تحول هابط", "TBS", "انعكاس Smart Money هابط", "أخبار سلبية", "أقوى"]):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≤-5 للبيع)\n📉 **الثقة**: {confidence:.0f}%"
    else:
        explanation = "⏳ **قرار الانتظار** بسبب:\n- النتيجة الصافية {net_score} بين -5 و +5.\n- تفاصيل النقاط:\n"
        for k, v in details.items(): explanation += f"  - {k}: {v}\n"
        explanation += "💡 انتظر حتى تتجاوز النتيجة ±5."
    if "News_Warning" in details:
        explanation += f"\n\n⚠️ **تنبيه**: {details['News_Warning']}"
    if stop_loss and entry_price and targets:
        explanation += f"\n\n📍 **الدخول:** {entry_price:.4f}\n🛑 **وقف الخسارة:** {stop_loss:.4f}\n🎯 **الأهداف:** 1: {targets['target1']:.4f}, 2: {targets['target2']:.4f}, 3: {targets['target3']:.4f}"
    explanation += f"\n\n🕒 **MTF**: {mtf_signal} (عدد الأطر: {mtf_count})"
    if patterns:
        explanation += "\n\n📐 **النماذج:**\n" + "\n".join([f"- {p['pattern']} ({p['direction']})" for p in patterns])
    if tbs_info[0]:
        tbs_type, tbs_entry, tbs_stop, tbs_level = tbs_info
        explanation += f"\n\n🐢 **TBS:** {tbs_type} عند {tbs_entry:.4f}"
    return explanation

# ==========================================
# جمع كل الإشارات (محدثة)
# ==========================================
@st.cache_data(ttl=120)
def get_all_signals_with_trades(interval='1h', params=None, weights=None):
    results = []
    articles = fetch_news()
    analyzed_news = analyze_news_impact(articles) if articles else []
    news_sentiment = get_market_sentiment(analyzed_news) if analyzed_news else ("NEUTRAL", 0)
    
    data_dict = {}
    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval=interval)
            if df is not None and len(df) > 100:
                data_dict[symbol] = df
        except:
            continue
    
    # حساب مؤشرات العملات
    if data_dict:
        indices = calculate_currency_indices(data_dict, weights=weights)
        if indices:
            st.session_state.currency_indices = pd.DataFrame(indices)
    
    for pair_name, symbol in PAIRS.items():
        if symbol not in data_dict:
            continue
        df = data_dict[symbol]
        current_price = df['close'].iloc[-1]
        
        # حساب المؤشرات الأساسية
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['atr'] = calc_atr(df)
        df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'], period=params.get('bb_period', 20), std_dev=params.get('bb_std', 2))
        df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df, period=14)
        df['vwap'] = calc_vwap(df)
        tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(df)
        df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b; df['chikou'] = chikou
        df['mfi'] = calc_mfi(df)
        
        # VRSI (بدلاً من RSI)
        if 'volume' in df.columns and not df['volume'].isna().all():
            df['vrsi'] = calc_vrsi(df['close'], df['volume'], period=params.get('vrsi_period', 14))
        else:
            df['vrsi'] = calc_rsi(df['close'], period=params.get('vrsi_period', 14))  # fallback
        
        currency_indices = st.session_state.currency_indices if st.session_state.currency_indices is not None else None
        signal, confidence, net_score, _, _, _, stop_loss, entry_price, targets = generate_advanced_signal(
            df, current_price, symbol, news_sentiment, currency_indices, params
        )
        
        if "Gold" in pair_name or "Silver" in pair_name or "Bitcoin" in pair_name or "Ethereum" in pair_name or "Ripple" in pair_name or "Solana" in pair_name or "Cardano" in pair_name:
            price_str = f"${current_price:,.2f}"; fmt = "${:,.2f}"
        else:
            price_str = f"{current_price:.4f}"; fmt = "{:.4f}"
        
        trade_details = {}
        if signal in ["BUY", "SELL"] and confidence >= params.get('confidence_threshold', 60) and stop_loss and entry_price and targets:
            trade_details = {"entry": entry_price, "stop_loss": stop_loss, "target1": targets.get('target1'), "target2": targets.get('target2'), "target3": targets.get('target3'), "risk_reward": f"1:{targets.get('risk_reward_3', 0):.1f}"}
        
        results.append({
            "الزوج": pair_name, "الإشارة": signal, "الثقة": round(confidence, 1),
            "النتيجة": net_score, "السعر": price_str,
            "سعر الدخول": fmt.format(entry_price) if entry_price else "N/A",
            "وقف الخسارة": fmt.format(stop_loss) if stop_loss else "N/A",
            "الهدف 1": fmt.format(trade_details.get('target1')) if trade_details.get('target1') else "N/A",
            "الهدف 2": fmt.format(trade_details.get('target2')) if trade_details.get('target2') else "N/A",
            "الهدف 3": fmt.format(trade_details.get('target3')) if trade_details.get('target3') else "N/A",
            "نسبة المخاطرة": trade_details.get('risk_reward', "N/A")
        })
    
    return pd.DataFrame(results), analyzed_news, news_sentiment

# ==========================================
# إدارة الصفقات (نفس السابق)
# ==========================================
class TradeManager:
    def __init__(self):
        self.trades_file = "trades_data.json"; self.load_trades()
    def load_trades(self):
        try:
            with open(self.trades_file, "r", encoding='utf-8') as f:
                data = json.load(f); self.open_trades = data.get("open_trades", []); self.closed_trades = data.get("closed_trades", [])
        except: self.open_trades = []; self.closed_trades = []
    def save_trades(self):
        with open(self.trades_file, "w", encoding='utf-8') as f:
            json.dump({"open_trades": self.open_trades, "closed_trades": self.closed_trades}, f, indent=2, ensure_ascii=False)
    def add_trade(self, trade_data):
        trade_id = f"T{len(self.open_trades)+len(self.closed_trades)+1:03d}"
        trade = {"id": trade_id, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "direction": trade_data["direction"], "entry": trade_data["entry"], "lots": trade_data["lots"], "stop_loss": trade_data["stop_loss"], "take_profit": trade_data["take_profit"], "trailing_enabled": trade_data.get("trailing_enabled", False), "trailing_distance": trade_data.get("trailing_distance", 0), "highest_price": trade_data["entry"], "lowest_price": trade_data["entry"], "status": "open", "stage": 0, "notes": trade_data.get("notes", "")}
        self.open_trades.append(trade); self.save_trades(); return trade_id
    def update_trailing_stop(self, trade_id, current_price):
        for trade in self.open_trades:
            if trade["id"] == trade_id and trade["status"] == "open" and trade["trailing_enabled"]:
                if trade["direction"] == "BUY":
                    if current_price > trade["highest_price"]: trade["highest_price"] = current_price
                    new_stop = trade["highest_price"] - trade["trailing_distance"]
                    if new_stop > trade["stop_loss"]: trade["stop_loss"] = new_stop; self.save_trades(); return True
                else:
                    if current_price < trade["lowest_price"]: trade["lowest_price"] = current_price
                    new_stop = trade["lowest_price"] + trade["trailing_distance"]
                    if new_stop < trade["stop_loss"]: trade["stop_loss"] = new_stop; self.save_trades(); return True
        return False
    def close_trade(self, trade_id, exit_price):
        for i, trade in enumerate(self.open_trades):
            if trade["id"] == trade_id:
                trade["exit"] = exit_price; trade["status"] = "closed"
                if trade["direction"] == "BUY": pips = (exit_price - trade["entry"]) * 100
                else: pips = (trade["entry"] - exit_price) * 100
                profit = pips * trade["lots"] * 0.1; trade["profit"] = round(profit, 2); trade["result"] = "win" if profit > 0 else "loss"; trade["close_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_trades.append(trade); self.open_trades.pop(i); self.save_trades(); return profit
        return None

# ==========================================
# الشريط الجانبي (لوحة التحكم)
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ لوحة التحكم Pro")
    st.session_state.account_balance = st.number_input("💰 رصيد الحساب", value=st.session_state.account_balance, step=1000, format="%d")
    risk_pct = st.slider("⚠️ نسبة المخاطرة (%)", 0.5, 5.0, 2.0, 0.1)
    st.session_state.risk_per_trade = risk_pct / 100
    
    st.markdown("#### 📊 مؤشرات احترافية")
    vrsi_period = st.slider("فترة VRSI", 5, 30, 14, help="مؤشر القوة النسبية الموزون بالحجم (مستويات 80/20)")
    adx_threshold = st.slider("عتبة ADX", 15, 40, 25)
    bb_period = st.slider("فترة بولينجر", 10, 30, 20)
    bb_std = st.slider("انحراف بولينجر", 1.5, 3.0, 2.0, 0.1)
    confidence_threshold = st.slider("عتبة الثقة (%)", 40, 80, 60)
    
    st.markdown("#### 🕒 الإطار الزمني")
    interval_map = {'5 دقائق': '5m', '15 دقيقة': '15m', 'ساعة': '1h', '4 ساعات': '4h', 'يوم': '1d'}
    selected_interval_label = st.selectbox("الفترة", list(interval_map.keys()), index=2)
    selected_interval = interval_map[selected_interval_label]
    
    params = {
        'vrsi_period': vrsi_period,
        'adx_threshold': adx_threshold,
        'bb_period': bb_period,
        'bb_std': bb_std,
        'confidence_threshold': confidence_threshold
    }
    
    st.markdown("#### ⚖️ أوزان العملات")
    weight_eurusd = st.slider("وزن EURUSD", 0.5, 2.0, 1.0, 0.1, key="w_eur")
    weight_usdjpy = st.slider("وزن USDJPY", 0.5, 2.0, 1.0, 0.1, key="w_jpy")
    custom_weights = {'EURUSD=X': weight_eurusd, 'USDJPY=X': weight_usdjpy}
    
    st.markdown("---")
    st.markdown("### 📊 حالة السوق")
    status, status_text, next_event, close_time = get_market_status()
    if status == "OPEN": st.markdown(f"🟢 {status_text} - يغلق: {time_remaining(next_event)}")
    else: st.markdown(f"🔴 {status_text} - يفتح: {time_remaining(next_event)}")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 تحديث الكل", use_container_width=True):
            with st.spinner("جارٍ التحليل..."):
                st.session_state.all_signals, st.session_state.news_analyzed, st.session_state.news_sentiment = get_all_signals_with_trades(selected_interval, params, custom_weights)
                st.session_state.last_update = datetime.now()
                st.rerun()
    with col2:
        if st.button("🗑️ مسح", use_container_width=True): st.session_state.all_signals = None; st.rerun()
    
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_s = st.session_state.all_signals.copy()
        def cs(val):
            if val == "BUY": return "🟢 شراء"
            elif val == "SELL": return "🔴 بيع"
            else: return "⚪ انتظار"
        df_s["الإشارة"] = df_s["الإشارة"].apply(cs)
        st.dataframe(df_s[["الزوج", "الإشارة", "الثقة", "النتيجة", "السعر"]], use_container_width=True, height=300, hide_index=True)
    else: st.info("اضغط 'تحديث الكل'")
    
    st.markdown("---")
    st.markdown("### 🔍 اختر الزوج")
    selected_pair_name = st.selectbox("للتحليل المتقدم", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair_name]
    st.markdown("---")
    if st.button("➕ صفقة جديدة", use_container_width=True):
        st.session_state.show_form = not st.session_state.show_form; st.rerun()

# ==========================================
# بداية المحتوى الرئيسي
# ==========================================
# عرض الأخبار
st.markdown("---")
st.markdown("### 🔴 أخبار عاجلة")
articles = fetch_news()
if articles:
    analyzed_news = analyze_news_impact(articles); sentiment, sentiment_score = get_market_sentiment(analyzed_news)
    if sentiment == "BULLISH":
        st.markdown(f'<div class="news-alert-bullish"><b>📈 معنويات إيجابية</b> ({sentiment_score:.1f}%)</div>', unsafe_allow_html=True)
    elif sentiment == "BEARISH":
        st.markdown(f'<div class="news-alert"><b>📉 معنويات سلبية</b> ({sentiment_score:.1f}%)</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:rgba(255,170,0,0.1);border:2px solid #ffaa00;border-radius:10px;padding:15px;margin:10px 0;"><b>➖ محايد</b></div>', unsafe_allow_html=True)
    for news in analyzed_news[:3]:
        st.markdown(f'<div class="news-card"><div class="news-title"><a href="{news["url"]}" target="_blank">{news["title"][:80]}...</a></div><div class="news-date">{news["impact_text"]} | {news["source"]}</div></div>', unsafe_allow_html=True)
else: st.info("لا توجد أخبار")

st.markdown("---")

# جلب البيانات للزوج المختار
for attempt in range(3):
    current_price, change = get_spot_price(selected_symbol)
    if current_price is not None: break
    time.sleep(1)

df = get_historical_data(selected_symbol, period="1mo", interval=selected_interval)
if df is None:
    st.error("⚠️ تعذر تحميل البيانات"); st.stop()
if current_price is None: current_price = df['close'].iloc[-1]; change = 0

# حساب المؤشرات
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['atr'] = calc_atr(df)
df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'], period=bb_period, std_dev=bb_std)
df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df, period=14)
df['vwap'] = calc_vwap(df)
tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(df)
df['tenkan'] = tenkan; df['kijun'] = kijun; df['senkou_a'] = senkou_a; df['senkou_b'] = senkou_b; df['chikou'] = chikou
df['mfi'] = calc_mfi(df)
# VRSI
if 'volume' in df.columns and not df['volume'].isna().all():
    df['vrsi'] = calc_vrsi(df['close'], df['volume'], period=vrsi_period)
else:
    df['vrsi'] = calc_rsi(df['close'], period=vrsi_period)

# توليد الإشارة
news_sentiment = get_market_sentiment(analyzed_news) if articles else ("NEUTRAL", 0)
currency_indices = st.session_state.currency_indices if st.session_state.currency_indices is not None else None
signal, confidence, net_score, details, patterns, tbs_info, stop_loss, entry_price, targets = generate_advanced_signal(
    df, current_price, selected_symbol, news_sentiment, currency_indices, params
)
mtf_signal, mtf_count = get_mtf_signal(selected_symbol, current_price, selected_interval)

# عرض السعر
if "Gold" in selected_pair_name or "Silver" in selected_pair_name or "Bitcoin" in selected_pair_name or "Ethereum" in selected_pair_name or "Ripple" in selected_pair_name or "Solana" in selected_pair_name or "Cardano" in selected_pair_name:
    price_format = "${:,.2f}"
else: price_format = "{:.4f}"

st.markdown(f"""
<div class="price-card">
    <div class="price-label">{selected_pair_name}</div>
    <div class="price-value">{price_format.format(current_price)}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">{change:+.2f}%</div>
</div>
""", unsafe_allow_html=True)

# عرض الصفقة المقترحة مع حساب اللوت الآلي
if signal in ["BUY", "SELL"] and confidence >= confidence_threshold and stop_loss and entry_price and targets:
    risk_amount = abs(entry_price - stop_loss)
    risk_per_trade_dollar = st.session_state.account_balance * st.session_state.risk_per_trade
    lot_size = risk_per_trade_dollar / (risk_amount * 100) if risk_amount > 0 else 0.01
    lot_size = round(max(lot_size, 0.01), 2)
    
    direction_text = "شراء (BUY)" if signal == "BUY" else "بيع (SELL)"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>الاتجاه:</b> {direction_text} (الثقة: {confidence:.0f}%)<br>
        <b>📍 الدخول:</b> {price_format.format(entry_price)}<br>
        <b>🛑 وقف الخسارة:</b> {price_format.format(stop_loss)}<br>
        <b>📦 اللوت المقترح (Auto-Risk {st.session_state.risk_per_trade*100:.1f}%):</b> {lot_size}<br>
        <div class="target-zone"><b>🎯 الهدف 1 (1:1):</b> {price_format.format(targets['target1'])}</div>
        <div class="target-zone" style="border-left-color:#ffaa00;"><b>🎯 الهدف 2 (1:1.5):</b> {price_format.format(targets['target2'])}</div>
        <div class="target-zone" style="border-left-color:#00ff88;"><b>🎯 الهدف 3 (1:2):</b> {price_format.format(targets['target3'])}</div>
        <b>📈 R:R قصوى:</b> 1:{targets['risk_reward_3']:.1f}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ إضافة الصفقة باللوت المحسوب", use_container_width=True):
        tm = TradeManager()
        trailing_dist = last['atr'] * 0.3 if 'atr' in last and not pd.isna(last['atr']) else (3 if "Gold" in selected_pair_name else 0.0003)
        trade_data = {"direction": signal, "entry": entry_price, "lots": lot_size, "stop_loss": stop_loss, "take_profit": targets['target2'], "trailing_enabled": True, "trailing_distance": trailing_dist, "notes": f"Auto-Risk {st.session_state.risk_per_trade*100:.1f}%"}
        trade_id = tm.add_trade(trade_data); st.success(f"✅ تم إضافة {trade_id}"); st.rerun()
else:
    st.info("⏳ انتظر إشارة قوية")

# الإشارة الرئيسية
st.markdown("---")
st.markdown("### 🧠 الإشارة المتكاملة (VRSI + Fibonacci Pro)")
signal_color = "#ffaa00" if signal == "WAIT" else ("#00ff88" if signal == "BUY" else "#ff4444")
st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color:{signal_color};">{signal}</div>
    <div class="signal-confidence">الثقة: {confidence:.0f}% | النتيجة: {net_score}</div>
    <div style="font-size:0.9rem;color:#aaa;">MTF: {mtf_signal} ({mtf_count})</div>
</div>
""", unsafe_allow_html=True)

with st.expander("📝 شرح القرار (Pro)", expanded=True):
    explanation = explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns, tbs_info, df, current_price, stop_loss, entry_price, targets)
    st.markdown(f'<div class="explanation-box">{explanation}</div>', unsafe_allow_html=True)

# ==========================================
# جميع الصفقات المقترحة
# ==========================================
st.markdown("---")
st.markdown("### 🚀 جميع الصفقات المقترحة")
if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
    df_all = st.session_state.all_signals.copy()
    df_trades = df_all[(df_all["الإشارة"].isin(["BUY", "SELL"])) & (df_all["الثقة"] >= confidence_threshold)]
    if not df_trades.empty:
        cols = ["الزوج", "الإشارة", "الثقة", "سعر الدخول", "وقف الخسارة", "الهدف 1", "الهدف 2", "الهدف 3", "نسبة المخاطرة"]
        df_trades["الإشارة"] = df_trades["الإشارة"].apply(lambda x: "🟢 شراء" if x=="BUY" else "🔴 بيع")
        st.dataframe(df_trades[cols], use_container_width=True, hide_index=True)
        csv = df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 تحميل التقرير (CSV)", csv, "black_pyramid_report.csv", "text/csv")
    else: st.info("لا توجد صفقات مقترحة حالياً")
else: st.info("اضغط 'تحديث الكل'")

# ==========================================
# مؤشرات العملات + خريطة حرارية
# ==========================================
st.markdown("---")
st.markdown("### 🌐 مؤشرات العملات & خريطة الارتباط")
if st.session_state.currency_indices is not None and not st.session_state.currency_indices.empty:
    indices_df = st.session_state.currency_indices
    latest = indices_df.iloc[-1]
    cols_cur = st.columns(len(latest))
    for i, (cur, val) in enumerate(latest.items()):
        cols_cur[i].metric(cur, f"{val:.2f}")
    
    fig_idx = go.Figure()
    for col in indices_df.columns:
        fig_idx.add_trace(go.Scatter(x=indices_df.index, y=indices_df[col], name=col))
    fig_idx.update_layout(height=350, template='plotly_dark', title="تطور المؤشرات")
    st.plotly_chart(fig_idx, use_container_width=True)
    
    # مصفوفة الارتباط
    if selected_symbol in ["GC=F", "EURUSD=X", "GBPUSD=X"]:
        st.markdown("#### 🔥 مصفوفة الارتباط")
        corr_data = {}
        for pair in ["GC=F", "EURUSD=X", "GBPUSD=X", "USDJPY=X"]:
            if pair in PAIRS.values():
                d = get_historical_data(pair, period="1mo", interval=selected_interval)
                if d is not None and not d.empty:
                    corr_data[pair] = d['close']
        if corr_data:
            corr_df = pd.DataFrame(corr_data)
            common_idx = corr_df.index
            for col in corr_df.columns:
                common_idx = common_idx.intersection(corr_df[col].dropna().index)
            corr_df = corr_df.loc[common_idx]
            for cur in indices_df.columns:
                idx_cur = indices_df[cur].reindex(common_idx, method='nearest')
                corr_df[cur] = idx_cur
            corr_matrix = corr_df.corr()
            fig_heat = go.Figure(data=go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.index, colorscale='RdBu', zmid=0))
            fig_heat.update_layout(height=500, template='plotly_dark', title="مصفوفة الارتباط")
            st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("قم بتحديث الإشارات لحساب المؤشرات.")

# ==========================================
# الرسم البياني الرئيسي (مع VRSI بدلاً من RSI)
# ==========================================
st.markdown("---")
st.markdown("### 📈 Price Chart with VRSI")
df_smc = analyze_smc_ict(df)
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(color='red', dash='dash')), row=1, col=1)
if not df_smc['bsl'].isna().all():
    fig.add_hline(y=df_smc['bsl'].iloc[-1], line_dash="dash", line_color="rgba(0,255,0,0.5)", row=1, col=1)
if not df_smc['ssl'].isna().all():
    fig.add_hline(y=df_smc['ssl'].iloc[-1], line_dash="dash", line_color="rgba(255,0,0,0.5)", row=1, col=1)
if stop_loss and entry_price:
    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
    fig.add_hline(y=entry_price, line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)
# VRSI بدلاً من RSI
fig.add_trace(go.Scatter(x=df.index, y=df['vrsi'], name='VRSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
fig.add_bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color='gray', opacity=0.3, row=3, col=1)
fig.update_layout(height=700, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# إدارة الصفقات
# ==========================================
st.markdown("---")
st.markdown("### 💼 إدارة الصفقات")
tm = TradeManager()
reversal_messages = []
for trade in tm.open_trades:
    if trade["status"] == "open":
        is_rev, msg = detect_reversal(df, trade)
        if is_rev: reversal_messages.append(f"⚠️ {trade['id']}: {msg}")
        if trade["trailing_enabled"]: tm.update_trailing_stop(trade["id"], current_price)

if reversal_messages:
    for msg in reversal_messages:
        st.markdown(f'<div class="reversal-alert">{msg}</div>', unsafe_allow_html=True)

if tm.open_trades:
    for trade in tm.open_trades:
        st.markdown(f"""
        <div class="trade-row">
            <b>{trade['id']}</b> | {trade['direction']} | الدخول: {trade['entry']} | اللوت: {trade['lots']} | 
            الوقف: {trade['stop_loss']} | الهدف: {trade['take_profit']}
            <br><span style="color:#aaa;">{"🔄 وقف متحرك مفعّل" if trade['trailing_enabled'] else ""}</span>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        if c1.button(f"🔄 تحديث {trade['id']}", key=f"up_{trade['id']}"):
            tm.update_trailing_stop(trade['id'], current_price); st.rerun()
        if c2.button(f"🔍 انعكاس {trade['id']}", key=f"rev_{trade['id']}"):
            is_rev, msg = detect_reversal(df, trade); st.warning(msg) if is_rev else st.success("لا انعكاس")
        if c3.button(f"❌ إغلاق {trade['id']}", key=f"cl_{trade['id']}"):
            tm.close_trade(trade['id'], current_price); st.rerun()
else: st.write("لا توجد صفقات مفتوحة")

if st.session_state.show_form:
    with st.form("new_trade_form"):
        st.subheader("➕ تفاصيل الصفقة")
        direction = st.selectbox("الاتجاه", ["BUY", "SELL"])
        entry = st.number_input("الدخول", value=float(current_price), format="%.2f" if "Gold" in selected_pair_name else "%.4f")
        stop = st.number_input("وقف الخسارة", value=float(current_price - 20 if "Gold" in selected_pair_name else 0.001), format="%.2f" if "Gold" in selected_pair_name else "%.4f")
        lots = st.number_input("اللوت", min_value=0.01, value=0.1, step=0.01)
        if st.form_submit_button("إضافة"):
            td = {"direction": direction, "entry": entry, "lots": lots, "stop_loss": stop, "take_profit": entry + 40 if "Gold" in selected_pair_name else entry + 0.002, "trailing_enabled": False, "trailing_distance": 0, "notes": "يدوي"}
            tm.add_trade(td); st.success("تمت الإضافة"); st.session_state.show_form = False; st.rerun()

# ==========================================
# تذييل
# ==========================================
st.markdown(f"""
<div class="footer">
    <span class="brand">▲ BLACK PYRAMID PRO v2004</span> • VRSI • VWAP Session • Fibonacci 78.6% & 88.6% • Auto-Risk • Heatmap
</div>
""", unsafe_allow_html=True)
