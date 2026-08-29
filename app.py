# ==========================================
# BLACK PYRAMID – الإصدار 2009 (Hierarchical)
# تاريخ التحديث: 2026-08-29
# التغييرات الجوهرية:
# - نظام تقييم هرمي (5 محاور رئيسية)
# - إعدادات تلقائية حسب نوع الأصل (Forex/Gold/Bitcoin)
# - منطق WAIT الذكي عند تضارب الأدلة
# - Stop Loss مبني على الهيكل + ATR
# - إدارة مخاطر دقيقة (حجم اللوت، أهداف متعددة، Trailing)
# - Multi-Timeframe بأدوار محددة (4H/1H/15M)
# - ربط الأخبار بالأصل
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
    page_title="Black Pyramid v2009",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🖤 الهوية البصرية (نفسها)
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
    .wait-box { border: 2px solid #ffaa00 !important; background: rgba(255,170,0,0.05) !important; }
    .wait-text { color: #ffaa00 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">▲ BLACK PYRAMID v2009 ▲</div>
        <div class="main-subtitle">Hierarchical • 5 Pillars • Auto-Detection • WAIT Logic • Smart Risk</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# قائمة الأزواج
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
if "signal_lock" not in st.session_state:
    st.session_state.signal_lock = {}
if "risk_per_trade" not in st.session_state:
    st.session_state.risk_per_trade = 0.02  # 2%

# ==========================================
# إعدادات الأصول (ثابتة)
# ==========================================
def get_asset_settings(symbol):
    """تحديد إعدادات الأصل تلقائياً بناءً على الرمز"""
    if symbol in ["GC=F", "SI=F", "XAUUSD=X", "XAGUSD=X"]:
        return {
            "type": "Gold",
            "vrsi_period": 14,
            "vrsi_overbought": 80,
            "vrsi_oversold": 20,
            "bb_period": 20,
            "bb_std": 2.2,
            "adx_threshold": 27,
            "lookback_levels": 175,
            "confidence_threshold": 72,
            "weights": {  # المحاور الخمسة
                "trend": 0.22,
                "momentum": 0.20,
                "adx": 0.18,
                "volume": 0.15,
                "price": 0.25   # Bollinger + Fibonacci + SMC
            },
            "atr_sl_multiplier": 1.5,
            "atr_trailing_multiplier": 1.2,
            "risk_cap": 0.72
        }
    elif symbol in ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "ADA-USD"]:
        return {
            "type": "Bitcoin",
            "vrsi_period": 14,
            "vrsi_overbought": 80,
            "vrsi_oversold": 20,
            "bb_period": 20,
            "bb_std": 2.2,
            "adx_threshold": 30,
            "lookback_levels": 250,
            "confidence_threshold": 75,
            "weights": {
                "trend": 0.22,
                "momentum": 0.20,
                "adx": 0.18,
                "volume": 0.15,
                "price": 0.25
            },
            "atr_sl_multiplier": 1.8,
            "atr_trailing_multiplier": 1.5,
            "risk_cap": 0.75
        }
    else:
        # Forex افتراضي
        return {
            "type": "Forex",
            "vrsi_period": 14,
            "vrsi_overbought": 75,
            "vrsi_oversold": 25,
            "bb_period": 20,
            "bb_std": 2.0,
            "adx_threshold": 25,
            "lookback_levels": 120,
            "confidence_threshold": 70,
            "weights": {
                "trend": 0.25,
                "momentum": 0.20,
                "adx": 0.15,
                "volume": 0.15,
                "price": 0.25
            },
            "atr_sl_multiplier": 1.2,
            "atr_trailing_multiplier": 0.9,
            "risk_cap": 0.70
        }

# ==========================================
# دوال جلب البيانات
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
# مؤشرات العملات
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
# المؤشرات الأساسية (محسّنة)
# ==========================================
def calc_vrsi(data, volume, period=14, overbought=80, oversold=20):
    """VRSI محسّن: الحجم يؤكد ولا يسيطر"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    # تأثير محدود للحجم (حد أقصى 10% تعديل)
    vol_ma = volume.rolling(window=period).mean()
    vol_ratio = (volume / vol_ma).clip(0.8, 1.2)
    vrsi = rsi * vol_ratio
    vrsi = vrsi.clip(0, 100)
    return vrsi

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

def calc_vwap(df):
    return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

def calc_mfi(df, period=14):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    return 100 - (100 / (1 + positive_flow / negative_flow))

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
        'fib_786': high - diff * 0.786,
        'fib_886': high - diff * 0.886,
        'fib_100': low
    }

# ==========================================
# SMC/ICT (نفسها مع تركيز أقل)
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

# ==========================================
# دوال الأخبار (محسّنة)
# ==========================================
def get_news_filters(symbol):
    """تحديد الكلمات المفتاحية حسب الأصل"""
    if symbol in ["GC=F", "SI=F", "XAUUSD=X", "XAGUSD=X"]:
        return {
            "keywords": ["gold", "silver", "fed", "inflation", "cpi", "nfp", "dollar", "yield", "rates"],
            "impact_multiplier": 1.0
        }
    elif symbol in ["BTC-USD", "ETH-USD", "XRP-USD", "SOL-USD", "ADA-USD"]:
        return {
            "keywords": ["bitcoin", "btc", "crypto", "etf", "halving", "regulation", "fed", "liquidity"],
            "impact_multiplier": 1.3
        }
    else:
        return {
            "keywords": ["forex", "eur", "gbp", "jpy", "chf", "aud", "nzd", "cad", "central bank", "rates"],
            "impact_multiplier": 0.9
        }

@st.cache_data(ttl=60)
def fetch_news(symbol="EURUSD=X"):
    try:
        news_filter = get_news_filters(symbol)
        query = " OR ".join(news_filter["keywords"])
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=10"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('articles', [])
    except:
        pass
    return []

# ==========================================
# نظام التقييم الهرمي (المحاور الخمسة)
# ==========================================
def analyze_asset(df, current_price, symbol, news_articles=None):
    """
    تحليل هرمي يعتمد على 5 محاور رئيسية.
    يعيد: signal, confidence, score_details, stop_loss, entry_price, targets
    """
    # 1. الحصول على إعدادات الأصل
    settings = get_asset_settings(symbol)
    asset_type = settings["type"]
    
    # 2. حساب المؤشرات الأساسية
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema100'] = df['close'].ewm(span=100, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # Ichimoku
    tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(df)
    df['tenkan'] = tenkan
    df['kijun'] = kijun
    df['senkou_a'] = senkou_a
    df['senkou_b'] = senkou_b
    df['chikou'] = chikou
    
    # المؤشرات الأخرى
    df['atr'] = calc_atr(df)
    df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(df['close'], period=settings['bb_period'], std_dev=settings['bb_std'])
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df, period=14)
    df['vwap'] = calc_vwap(df)
    df['mfi'] = calc_mfi(df)
    
    if 'volume' in df.columns and not df['volume'].isna().all():
        df['vrsi'] = calc_vrsi(df['close'], df['volume'], period=settings['vrsi_period'])
    else:
        df['vrsi'] = calc_rsi(df['close'], period=settings['vrsi_period'])
    
    # SMC
    df_smc = analyze_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    
    # مستويات فيبوناتشي
    recent_high = df['high'].iloc[-settings['lookback_levels']:].max()
    recent_low = df['low'].iloc[-settings['lookback_levels']:].min()
    fib_levels = calc_fibonacci_levels_pro(recent_high, recent_low, current_price)
    
    last = df.iloc[-1]
    last_close = last['close']
    
    # ==========================================
    # المحور 1: الاتجاه (TREND) – الوزن الأكبر
    # ==========================================
    trend_score = 0
    trend_details = []
    
    # 1A: موقع السعر بالنسبة للمتوسطات
    if last_close > last['ema200']:
        trend_score += 2
        trend_details.append("فوق EMA200")
    if last_close > last['ema100']:
        trend_score += 1
        trend_details.append("فوق EMA100")
    if last_close > last['ema50']:
        trend_score += 1
        trend_details.append("فوق EMA50")
    if last_close > last['ema20']:
        trend_score += 1
        trend_details.append("فوق EMA20")
    
    # 1B: ترتيب المتوسطات (مؤشر قوي)
    if last['ema20'] > last['ema50'] > last['ema100'] > last['ema200']:
        trend_score += 2
        trend_details.append("ترتيب صاعد مثالي")
    elif last['ema20'] < last['ema50'] < last['ema100'] < last['ema200']:
        trend_score -= 2
        trend_details.append("ترتيب هابط مثالي")
    
    # 1C: Ichimoku
    if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']):
        if last_close > last['senkou_a'] and last_close > last['senkou_b']:
            trend_score += 2
            trend_details.append("فوق سحابة Ichimoku")
        elif last_close < last['senkou_a'] and last_close < last['senkou_b']:
            trend_score -= 2
            trend_details.append("تحت سحابة Ichimoku")
        else:
            trend_score += 0
            trend_details.append("داخل السحابة → WAIT محتمل")
        
        if 'tenkan' in last and 'kijun' in last:
            if last['tenkan'] > last['kijun']:
                trend_score += 1
                trend_details.append("Tenkan فوق Kijun")
            else:
                trend_score -= 1
                trend_details.append("Tenkan تحت Kijun")
    
    # 1D: Break of Structure (BOS)
    if last_smc.get('bos_bullish', False):
        trend_score += 1
        trend_details.append("BOS صاعد")
    elif last_smc.get('bos_bearish', False):
        trend_score -= 1
        trend_details.append("BOS هابط")
    
    # 1E: Market Structure Shift (MSS)
    if last_smc.get('mss_bullish', False):
        trend_score += 2
        trend_details.append("MSS صاعد (تحول هيكلي)")
    elif last_smc.get('mss_bearish', False):
        trend_score -= 2
        trend_details.append("MSS هابط (تحول هيكلي)")
    
    # تطبيع درجة الاتجاه إلى -10 .. +10
    trend_score = max(-10, min(10, trend_score))
    trend_direction = "NEUTRAL"
    if trend_score >= 4:
        trend_direction = "BULLISH"
    elif trend_score <= -4:
        trend_direction = "BEARISH"
    
    # ==========================================
    # المحور 2: الزخم (MOMENTUM)
    # ==========================================
    momentum_score = 0
    momentum_details = []
    
    # MACD
    if 'macd' in last and 'macd_signal' in last and not pd.isna(last['macd']):
        if last['macd'] > last['macd_signal'] and last['macd_histogram'] > 0:
            momentum_score += 2
            momentum_details.append("MACD إيجابي")
            # تحسن الهيستوجرام
            if len(df) > 2 and df['macd_histogram'].iloc[-1] > df['macd_histogram'].iloc[-2]:
                momentum_score += 1
                momentum_details.append("Histogram في تحسن")
        elif last['macd'] < last['macd_signal'] and last['macd_histogram'] < 0:
            momentum_score -= 2
            momentum_details.append("MACD سلبي")
            if len(df) > 2 and df['macd_histogram'].iloc[-1] < df['macd_histogram'].iloc[-2]:
                momentum_score -= 1
                momentum_details.append("Histogram في تدهور")
    
    # VRSI (محدود)
    if 'vrsi' in last and not pd.isna(last['vrsi']):
        vrsi = last['vrsi']
        if vrsi > settings['vrsi_overbought']:
            momentum_score -= 1
            momentum_details.append(f"VRSI تشبع شراء ({vrsi:.1f})")
        elif vrsi < settings['vrsi_oversold']:
            momentum_score += 1
            momentum_details.append(f"VRSI تشبع بيع ({vrsi:.1f})")
        elif vrsi > 50:
            momentum_score += 1
            momentum_details.append(f"VRSI إيجابي ({vrsi:.1f})")
        else:
            momentum_score -= 1
            momentum_details.append(f"VRSI سلبي ({vrsi:.1f})")
    
    # تطبيع الزخم
    momentum_score = max(-5, min(5, momentum_score))
    
    # ==========================================
    # المحور 3: ADX (فلتر القوة)
    # ==========================================
    if 'adx' in last and not pd.isna(last['adx']):
        adx_value = last['adx']
        adx_threshold = settings['adx_threshold']
        if adx_value > adx_threshold + 5:
            adx_score = 3  # قوي جداً
            adx_detail = f"ADX قوي جداً ({adx_value:.1f})"
        elif adx_value > adx_threshold:
            adx_score = 2  # قوي
            adx_detail = f"ADX قوي ({adx_value:.1f})"
        elif adx_value > adx_threshold - 5:
            adx_score = 1  # متوسط
            adx_detail = f"ADX متوسط ({adx_value:.1f})"
        else:
            adx_score = 0  # ضعيف
            adx_detail = f"ADX ضعيف ({adx_value:.1f}) - يفضل الانتظار"
    else:
        adx_score = 0
        adx_detail = "ADX غير متوفر"
    
    # ==========================================
    # المحور 4: الحجم والسيولة (VOLUME)
    # ==========================================
    volume_score = 0
    volume_details = []
    
    # VWAP
    if 'vwap' in last and not pd.isna(last['vwap']):
        if last_close > last['vwap']:
            volume_score += 1
            volume_details.append("فوق VWAP (سيولة إيجابية)")
        else:
            volume_score -= 1
            volume_details.append("تحت VWAP (سيولة سلبية)")
    
    # MFI
    if 'mfi' in last and not pd.isna(last['mfi']):
        mfi = last['mfi']
        if mfi < 20:
            volume_score += 1
            volume_details.append(f"MFI مفرط بيع ({mfi:.1f})")
        elif mfi > 80:
            volume_score -= 1
            volume_details.append(f"MFI مفرط شراء ({mfi:.1f})")
        elif mfi > 50:
            volume_score += 0.5
            volume_details.append(f"MFI إيجابي ({mfi:.1f})")
        else:
            volume_score -= 0.5
            volume_details.append(f"MFI سلبي ({mfi:.1f})")
    
    volume_score = max(-3, min(3, volume_score))
    
    # ==========================================
    # المحور 5: مناطق السعر (PRICE LEVELS)
    # ==========================================
    price_score = 0
    price_details = []
    
    # Bollinger Bands (مع المنطق الجديد)
    if not pd.isna(last['bb_upper']) and not pd.isna(last['bb_lower']):
        bb_width = (last['bb_upper'] - last['bb_lower']) / last['bb_middle']
        
        # سوق جانبي (BB ضيق)
        if bb_width < 0.05:  # ضيق نسبياً
            if last_close < last['bb_lower'] * 1.005 and (last_smc.get('smr_bullish', False) or last_smc.get('fvg_bullish', False)):
                price_score += 2
                price_details.append("BB سفلي + تأكيد انعكاس → شراء")
            elif last_close > last['bb_upper'] * 0.995 and (last_smc.get('smr_bearish', False) or last_smc.get('fvg_bearish', False)):
                price_score -= 2
                price_details.append("BB علوي + تأكيد انعكاس → بيع")
        # سوق قوي (BB واسع)
        else:
            if last_close > last['bb_upper'] * 0.995:
                if trend_direction == "BULLISH" and adx_score >= 2:
                    price_score += 1
                    price_details.append("BB علوي في سوق صاعد → استمرار")
                else:
                    price_score -= 1
                    price_details.append("BB علوي في سوق غير صاعد → حذر")
            elif last_close < last['bb_lower'] * 1.005:
                if trend_direction == "BEARISH" and adx_score >= 2:
                    price_score -= 1
                    price_details.append("BB سفلي في سوق هابط → استمرار")
                else:
                    price_score += 1
                    price_details.append("BB سفلي في سوق غير هابط → حذر")
    
    # Fibonacci
    if fib_levels:
        if last_close < fib_levels.get('fib_618', last_close):
            price_score += 1
            price_details.append("دعم فيبوناتشي (61.8%)")
        if last_close < fib_levels.get('fib_786', last_close) and last_close > fib_levels.get('fib_618', last_close):
            price_score += 0.5
            price_details.append("منطقة 61.8-78.6% (اهتمام)")
        if last_close > fib_levels.get('fib_382', last_close):
            price_score -= 1
            price_details.append("مقاومة فيبوناتشي (38.2%)")
    
    # SMC كتأكيد إضافي
    if last_smc.get('order_block_bullish', False):
        price_score += 1
        price_details.append("Bullish Order Block")
    elif last_smc.get('order_block_bearish', False):
        price_score -= 1
        price_details.append("Bearish Order Block")
    
    if last_smc.get('fvg_bullish', False):
        price_score += 0.5
        price_details.append("FVG شراء")
    elif last_smc.get('fvg_bearish', False):
        price_score -= 0.5
        price_details.append("FVG بيع")
    
    price_score = max(-4, min(4, price_score))
    
    # ==========================================
    # تجميع المحاور مع الأوزان
    # ==========================================
    weights = settings['weights']
    
    # تطبيع النقاط إلى نسب مئوية (لكل محور)
    trend_norm = (trend_score + 10) / 20  # 0..1
    momentum_norm = (momentum_score + 5) / 10
    adx_norm = adx_score / 3  # 0..1 (0 ضعيف، 1 قوي جداً)
    volume_norm = (volume_score + 3) / 6
    price_norm = (price_score + 4) / 8
    
    # حساب الثقة الكلية (مرجحة)
    total_confidence = (
        trend_norm * weights['trend'] * 100 +
        momentum_norm * weights['momentum'] * 100 +
        adx_norm * weights['adx'] * 100 +
        volume_norm * weights['volume'] * 100 +
        price_norm * weights['price'] * 100
    )
    
    # تحديد الاتجاه النهائي
    if trend_score >= 3 and momentum_score >= 1 and adx_score >= 2:
        final_signal = "BUY"
        final_confidence = min(100, total_confidence * 1.1)  # مكافأة للتوافق
    elif trend_score <= -3 and momentum_score <= -1 and adx_score >= 2:
        final_signal = "SELL"
        final_confidence = min(100, total_confidence * 1.1)
    else:
        # WAIT إذا كان الاتجاه غير واضح أو ADX ضعيف
        if adx_score < 1:
            final_signal = "WAIT"
            final_confidence = total_confidence * 0.5
        elif abs(trend_score) < 3:
            final_signal = "WAIT"
            final_confidence = total_confidence * 0.6
        elif (trend_score >= 3 and momentum_score < -1) or (trend_score <= -3 and momentum_score > 1):
            final_signal = "WAIT"  # تعارض بين الاتجاه والزخم
            final_confidence = total_confidence * 0.7
        else:
            final_signal = "WAIT"
            final_confidence = total_confidence * 0.8
    
    # تطبيق حد الثقة حسب الأصل
    if final_confidence < settings['confidence_threshold']:
        final_signal = "WAIT"
    
    # ==========================================
    # Stop Loss & Targets (محسّنة)
    # ==========================================
    if final_signal in ["BUY", "SELL"] and final_confidence >= settings['confidence_threshold']:
        atr_value = last['atr'] if not pd.isna(last['atr']) else 10
        
        # تحديد مستويات الهيكل (Swing High/Low)
        swing_high = df['high'].iloc[-20:].max()
        swing_low = df['low'].iloc[-20:].min()
        
        if final_signal == "BUY":
            # وقف تحت آخر Swing Low + Buffer من ATR
            stop_loss = swing_low - (atr_value * settings['atr_sl_multiplier'] * 0.5)
            # تأكد أن الوقف ليس قريباً جداً
            if (current_price - stop_loss) < atr_value * 0.5:
                stop_loss = current_price - atr_value * 0.5
            entry_price = current_price
            risk = abs(entry_price - stop_loss)
            targets = {
                'target1': entry_price + risk * 1.5,
                'target2': entry_price + risk * 2.5,
                'target3': entry_price + risk * 4.0,
                'risk_reward_1': 1.5,
                'risk_reward_2': 2.5,
                'risk_reward_3': 4.0,
                'risk': risk
            }
        else:
            # وقف فوق آخر Swing High + Buffer من ATR
            stop_loss = swing_high + (atr_value * settings['atr_sl_multiplier'] * 0.5)
            if (stop_loss - current_price) < atr_value * 0.5:
                stop_loss = current_price + atr_value * 0.5
            entry_price = current_price
            risk = abs(entry_price - stop_loss)
            targets = {
                'target1': entry_price - risk * 1.5,
                'target2': entry_price - risk * 2.5,
                'target3': entry_price - risk * 4.0,
                'risk_reward_1': 1.5,
                'risk_reward_2': 2.5,
                'risk_reward_3': 4.0,
                'risk': risk
            }
        
        trailing_distance = atr_value * settings['atr_trailing_multiplier']
    else:
        stop_loss = None
        entry_price = None
        targets = {}
        trailing_distance = None
    
    # ==========================================
    # تحليل MTF (4H, 1H, 15M)
    # ==========================================
    mtf_signal, mtf_count = get_mtf_signal(symbol, current_price, '1h', settings)
    
    # إذا كان MTF متعارضاً، نخفف الثقة
    if final_signal != "WAIT" and mtf_signal != final_signal and mtf_count >= 2:
        final_confidence *= 0.7
        if final_confidence < settings['confidence_threshold']:
            final_signal = "WAIT"
    
    # ==========================================
    # تحليل الأخبار (مرتبطة بالأصل)
    # ==========================================
    if news_articles:
        news_impact = analyze_news_impact(news_articles, symbol)
        if news_impact == "BEARISH" and final_signal == "BUY":
            final_confidence *= 0.7
        elif news_impact == "BULLISH" and final_signal == "SELL":
            final_confidence *= 0.7
        elif news_impact == "HIGH_IMPACT":
            final_confidence *= 0.6  # أخبار قوية → انتظار
    
    # ==========================================
    # تجميع النتائج
    # ==========================================
    score_details = {
        "trend": {"score": trend_score, "details": trend_details},
        "momentum": {"score": momentum_score, "details": momentum_details},
        "adx": {"score": adx_score, "detail": adx_detail},
        "volume": {"score": volume_score, "details": volume_details},
        "price": {"score": price_score, "details": price_details},
        "mtf": {"signal": mtf_signal, "count": mtf_count}
    }
    
    return final_signal, final_confidence, score_details, stop_loss, entry_price, targets, trailing_distance

# ==========================================
# MTF
# ==========================================
def get_mtf_signal(symbol, current_price, interval='1h', settings=None):
    """تحليل متعدد الأطر الزمنية: 4H للاتجاه، 1H للتأكيد، 15M للتوقيت"""
    if settings is None:
        settings = get_asset_settings(symbol)
    
    timeframes = {
        '4H': '4h',
        '1H': '1h',
        '15M': '15m'
    }
    signals = {}
    
    for name, tf in timeframes.items():
        df = get_historical_data(symbol, period="1mo", interval=tf)
        if df is not None and len(df) > 50:
            # حساب مؤشرات بسيطة
            df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
            df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
            last = df.iloc[-1]
            current = last['close']
            
            # الاتجاه العام
            above_ema50 = current > last['ema50']
            above_ema200 = current > last['ema200']
            adx, _, _ = calc_adx(df)
            current_adx = adx.iloc[-1] if not adx.isna().all() else 0
            
            if above_ema50 and above_ema200 and current_adx > settings['adx_threshold']:
                signals[name] = "BUY"
            elif not above_ema50 and not above_ema200 and current_adx > settings['adx_threshold']:
                signals[name] = "SELL"
            else:
                signals[name] = "NEUTRAL"
        else:
            signals[name] = "NEUTRAL"
    
    # حساب الإجماع
    buy_count = sum(1 for s in signals.values() if s == "BUY")
    sell_count = sum(1 for s in signals.values() if s == "SELL")
    
    if buy_count >= 2:
        return "BUY", buy_count
    elif sell_count >= 2:
        return "SELL", sell_count
    else:
        return "NEUTRAL", 0

# ==========================================
# تحليل الأخبار (مرتبط بالأصل)
# ==========================================
def analyze_news_impact(articles, symbol):
    """تحليل الأخبار مع تركيز على الأصل"""
    news_filter = get_news_filters(symbol)
    keywords = news_filter['keywords']
    
    if not articles:
        return "NEUTRAL"
    
    positive = 0
    negative = 0
    high_impact = False
    
    for article in articles[:5]:
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = title + " " + description
        
        # التحقق من وجود كلمات مفتاحية خاصة بالأصل
        relevance = sum(1 for kw in keywords if kw in content)
        if relevance < 2:
            continue
        
        # تحليل المشاعر
        pos = sum(1 for word in POSITIVE_KEYWORDS if word in content)
        neg = sum(1 for word in NEGATIVE_KEYWORDS if word in content)
        
        if pos > neg:
            positive += 1
        elif neg > pos:
            negative += 1
        else:
            pass
        
        # أخبار عالية التأثير (كلمات قوية)
        high_impact_words = ["emergency", "crash", "surge", "plunge", "record", "historic", "unexpected"]
        if any(word in content for word in high_impact_words):
            high_impact = True
    
    if high_impact:
        return "HIGH_IMPACT"
    elif positive > negative:
        return "BULLISH"
    elif negative > positive:
        return "BEARISH"
    else:
        return "NEUTRAL"

# ==========================================
# دوال مساعدة (Reversal, Explanation)
# ==========================================
def detect_reversal(df, trade):
    if df is None or len(df) < 20:
        return False, "بيانات غير كافية"
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    direction = trade["direction"]
    entry = trade["entry"]
    current_price = last['close']
    signals = []
    
    # VRSI
    if 'vrsi' in df.columns and not pd.isna(last['vrsi']):
        vrsi = last['vrsi']
        if direction == "BUY":
            if vrsi > 80:
                signals.append("VRSI فوق 80 (تشبع شرائي)")
            elif vrsi < 20 and current_price < entry:
                signals.append("VRSI تحت 20 مع هبوط")
        else:
            if vrsi < 20:
                signals.append("VRSI تحت 20 (تشبع بيعي)")
            elif vrsi > 80 and current_price > entry:
                signals.append("VRSI فوق 80 مع صعود")
    
    # MACD
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if direction == "BUY":
            if last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                signals.append("MACD تقاطع هابط")
        else:
            if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                signals.append("MACD تقاطع صاعد")
    
    # شموع
    candle_range = abs(last['high'] - last['low'])
    if candle_range > 0:
        if direction == "BUY":
            upper_wick = last['high'] - max(last['close'], last['open'])
            if upper_wick > candle_range * 0.6:
                signals.append("شمعة انعكاس هابط (ذيل علوي طويل)")
        else:
            lower_wick = min(last['close'], last['open']) - last['low']
            if lower_wick > candle_range * 0.6:
                signals.append("شمعة انعكاس صاعد (ذيل سفلي طويل)")
    
    # كسر مستويات
    recent_high = df['high'].iloc[-20:].max()
    recent_low = df['low'].iloc[-20:].min()
    if direction == "BUY" and current_price < recent_low:
        signals.append("كسر دعم")
    elif direction == "SELL" and current_price > recent_high:
        signals.append("كسر مقاومة")
    
    if signals:
        return True, " | ".join(signals)
    return False, ""

def explain_decision(signal, confidence, score_details, stop_loss, entry_price, targets):
    explanation = ""
    
    if signal == "WAIT":
        explanation = "⏳ **WAIT – انتظار**\n\n"
        reasons = []
        
        # أسباب الانتظار
        trend = score_details.get("trend", {})
        adx = score_details.get("adx", {})
        mtf = score_details.get("mtf", {})
        
        if abs(trend.get("score", 0)) < 3:
            reasons.append("الاتجاه غير واضح (النتيجة بين -3 و +3)")
        if adx.get("score", 0) < 1:
            reasons.append(f"ADX ضعيف – {adx.get('detail', '')}")
        if mtf.get("signal") != "NEUTRAL" and mtf.get("count", 0) < 2:
            reasons.append("الأطر الزمنية متعارضة")
        if signal == "WAIT" and confidence > 0:
            reasons.append(f"الثقة {confidence:.1f}% أقل من العتبة المطلوبة")
        
        if not reasons:
            reasons.append("الأدلة غير كافية لاتخاذ قرار")
        
        for r in reasons:
            explanation += f"- {r}\n"
        explanation += "\n💡 الانتظار ليس فشلاً؛ إنه فلتر جودة."
        return explanation
    
    # BUY / SELL
    direction = "شراء (BUY)" if signal == "BUY" else "بيع (SELL)"
    explanation = f"🔹 **{direction}** - الثقة: {confidence:.1f}%\n\n"
    
    # تفاصيل المحاور
    for key, value in score_details.items():
        if key == "trend":
            explanation += f"**الاتجاه**: {value['score']} نقطة\n"
            for d in value['details']:
                explanation += f"  - {d}\n"
        elif key == "momentum":
            explanation += f"**الزخم**: {value['score']} نقطة\n"
            for d in value['details']:
                explanation += f"  - {d}\n"
        elif key == "adx":
            explanation += f"**ADX**: {value['score']}/3 - {value.get('detail', '')}\n"
        elif key == "volume":
            explanation += f"**الحجم**: {value['score']} نقطة\n"
            for d in value['details']:
                explanation += f"  - {d}\n"
        elif key == "price":
            explanation += f"**مناطق السعر**: {value['score']} نقطة\n"
            for d in value['details']:
                explanation += f"  - {d}\n"
    
    if stop_loss and entry_price and targets:
        explanation += f"\n📍 **الدخول**: {entry_price:.4f}\n"
        explanation += f"🛑 **وقف الخسارة**: {stop_loss:.4f}\n"
        explanation += f"🎯 **الأهداف**:\n"
        explanation += f"  - TP1 (1.5R): {targets['target1']:.4f}\n"
        explanation += f"  - TP2 (2.5R): {targets['target2']:.4f}\n"
        explanation += f"  - TP3 (4R): {targets['target3']:.4f}\n"
        explanation += f"📈 **R:R**: 1:{targets['risk_reward_3']:.1f}\n"
    
    return explanation

# ==========================================
# جمع كل الإشارات (مختصر)
# ==========================================
@st.cache_data(ttl=120)
def get_all_signals_with_trades(interval='1h', weights=None):
    results = []
    articles = fetch_news("EURUSD=X")  # مؤقتاً
    
    data_dict = {}
    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="1mo", interval=interval)
            if df is not None and len(df) > 100:
                data_dict[symbol] = df
        except:
            continue
    
    if data_dict:
        indices = calculate_currency_indices(data_dict, weights=weights)
        if indices:
            st.session_state.currency_indices = pd.DataFrame(indices)
    
    for pair_name, symbol in PAIRS.items():
        if symbol not in data_dict:
            continue
        
        df = data_dict[symbol]
        current_price = df['close'].iloc[-1]
        
        # إعدادات الأصل
        settings = get_asset_settings(symbol)
        
        # تحليل
        signal, confidence, score_details, stop_loss, entry_price, targets, trailing = analyze_asset(
            df, current_price, symbol, articles
        )
        
        # حساب اللوت
        if signal in ["BUY", "SELL"] and stop_loss and entry_price:
            risk_amount = abs(entry_price - stop_loss)
            risk_per_trade_dollar = st.session_state.account_balance * st.session_state.risk_per_trade
            lot_size = risk_per_trade_dollar / (risk_amount * 100) if risk_amount > 0 else 0.01
            lot_size = round(max(lot_size, 0.01), 2)
        else:
            lot_size = 0
        
        if "Gold" in pair_name or "Silver" in pair_name or "Bitcoin" in pair_name or "Ethereum" in pair_name or "Ripple" in pair_name or "Solana" in pair_name or "Cardano" in pair_name:
            price_str = f"${current_price:,.2f}"
            fmt = "${:,.2f}"
        else:
            price_str = f"{current_price:.4f}"
            fmt = "{:.4f}"
        
        trade_details = {}
        if signal in ["BUY", "SELL"] and confidence >= settings['confidence_threshold'] and stop_loss and entry_price and targets:
            trade_details = {
                "entry": entry_price,
                "stop_loss": stop_loss,
                "target1": targets.get('target1'),
                "target2": targets.get('target2'),
                "target3": targets.get('target3'),
                "risk_reward": f"1:{targets.get('risk_reward_3', 0):.1f}",
                "lot": lot_size
            }
        
        results.append({
            "الزوج": pair_name,
            "الإشارة": signal,
            "الثقة": round(confidence, 1),
            "السعر": price_str,
            "سعر الدخول": fmt.format(entry_price) if entry_price else "N/A",
            "وقف الخسارة": fmt.format(stop_loss) if stop_loss else "N/A",
            "الهدف 1": fmt.format(trade_details.get('target1')) if trade_details.get('target1') else "N/A",
            "الهدف 2": fmt.format(trade_details.get('target2')) if trade_details.get('target2') else "N/A",
            "الهدف 3": fmt.format(trade_details.get('target3')) if trade_details.get('target3') else "N/A",
            "نسبة المخاطرة": trade_details.get('risk_reward', "N/A"),
            "اللوت": trade_details.get('lot', 0)
        })
    
    return pd.DataFrame(results), articles

# ==========================================
# إدارة الصفقات (نفسها)
# ==========================================
class TradeManager:
    def __init__(self):
        self.trades_file = "trades_data.json"
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
            "trailing_enabled": trade_data.get("trailing_enabled", False),
            "trailing_distance": trade_data.get("trailing_distance", 0),
            "highest_price": trade_data["entry"],
            "lowest_price": trade_data["entry"],
            "status": "open",
            "stage": 0,
            "notes": trade_data.get("notes", "")
        }
        self.open_trades.append(trade)
        self.save_trades()
        return trade_id
    def update_trailing_stop(self, trade_id, current_price):
        for trade in self.open_trades:
            if trade["id"] == trade_id and trade["status"] == "open" and trade["trailing_enabled"]:
                if trade["direction"] == "BUY":
                    if current_price > trade["highest_price"]:
                        trade["highest_price"] = current_price
                    new_stop = trade["highest_price"] - trade["trailing_distance"]
                    if new_stop > trade["stop_loss"]:
                        trade["stop_loss"] = new_stop
                        self.save_trades()
                        return True
                else:
                    if current_price < trade["lowest_price"]:
                        trade["lowest_price"] = current_price
                    new_stop = trade["lowest_price"] + trade["trailing_distance"]
                    if new_stop < trade["stop_loss"]:
                        trade["stop_loss"] = new_stop
                        self.save_trades()
                        return True
        return False
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
# الشريط الجانبي المبسط
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    
    # إظهار نوع الأصل الحالي
    st.markdown("**نوع الأصل الحالي:**")
    if 'selected_symbol' in locals():
        settings = get_asset_settings(selected_symbol)
        st.markdown(f"🔹 {settings['type']}")
        st.markdown(f"   عتبة الثقة: {settings['confidence_threshold']}%")
        st.markdown(f"   عتبة ADX: {settings['adx_threshold']}")
    
    st.markdown("---")
    st.markdown("### 📊 حالة السوق")
    status, status_text, next_event, close_time = get_market_status()
    if status == "OPEN":
        st.markdown(f"🟢 {status_text} - يغلق: {time_remaining(next_event)}")
    else:
        st.markdown(f"🔴 {status_text} - يفتح: {time_remaining(next_event)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 تحديث الكل", width='stretch'):
            with st.spinner("جارٍ التحليل..."):
                st.session_state.all_signals, st.session_state.news_articles = get_all_signals_with_trades('1h', {})
                st.session_state.last_update = datetime.now()
                st.rerun()
    with col2:
        if st.button("🗑️ مسح", width='stretch'):
            st.session_state.all_signals = None
            st.rerun()
    
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_s = st.session_state.all_signals.copy()
        def cs(val):
            if val == "BUY": return "🟢 شراء"
            elif val == "SELL": return "🔴 بيع"
            else: return "🟡 انتظار"
        df_s["الإشارة"] = df_s["الإشارة"].apply(cs)
        st.dataframe(df_s[["الزوج", "الإشارة", "الثقة", "السعر"]], use_container_width=True, height=300, hide_index=True)
    else:
        st.info("اضغط 'تحديث الكل'")
    
    st.markdown("---")
    st.markdown("### 🔍 اختر الزوج")
    selected_pair_name = st.selectbox("للتحليل المتقدم", list(PAIRS.keys()), index=0)
    selected_symbol = PAIRS[selected_pair_name]
    
    st.markdown("---")
    if st.button("➕ صفقة جديدة", width='stretch'):
        st.session_state.show_form = not st.session_state.show_form
        st.rerun()

# ==========================================
# المحتوى الرئيسي
# ==========================================
# عرض الأخبار
st.markdown("---")
st.markdown("### 🔴 أخبار عاجلة (مرتبطة بالأصل)")
news_articles = fetch_news(selected_symbol)
if news_articles:
    news_filter = get_news_filters(selected_symbol)
    filtered_news = []
    for article in news_articles[:5]:
        title = article.get('title', '').lower()
        desc = article.get('description', '').lower()
        content = title + " " + desc
        relevance = sum(1 for kw in news_filter['keywords'] if kw in content)
        if relevance >= 2:
            filtered_news.append(article)
    
    if filtered_news:
        for news in filtered_news[:3]:
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title"><a href="{news['url']}" target="_blank">{news['title'][:80]}...</a></div>
                <div class="news-date">{news['source']['name']} - {news['publishedAt'][:10]}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد أخبار ذات صلة حالياً")
else:
    st.info("لا توجد أخبار")

st.markdown("---")

# جلب البيانات للزوج المختار
for attempt in range(3):
    current_price, change = get_spot_price(selected_symbol)
    if current_price is not None:
        break
    time.sleep(1)

df = get_historical_data(selected_symbol, period="1mo", interval="1h")
if df is None:
    st.error("⚠️ تعذر تحميل البيانات")
    st.stop()
if current_price is None:
    current_price = df['close'].iloc[-1]
    change = 0

# التحليل
signal, confidence, score_details, stop_loss, entry_price, targets, trailing_distance = analyze_asset(
    df, current_price, selected_symbol, news_articles
)

# عرض السعر
settings = get_asset_settings(selected_symbol)
if "Gold" in selected_pair_name or "Silver" in selected_pair_name or "Bitcoin" in selected_pair_name or "Ethereum" in selected_pair_name or "Ripple" in selected_pair_name or "Solana" in selected_pair_name or "Cardano" in selected_pair_name:
    price_format = "${:,.2f}"
else:
    price_format = "{:.4f}"

st.markdown(f"""
<div class="price-card">
    <div class="price-label">{selected_pair_name}</div>
    <div class="price-value">{price_format.format(current_price)}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">{change:+.2f}%</div>
</div>
""", unsafe_allow_html=True)

# عرض الصفقة
if signal in ["BUY", "SELL"] and confidence >= settings['confidence_threshold'] and stop_loss and entry_price and targets:
    # حساب حجم اللوت
    risk_amount = abs(entry_price - stop_loss)
    risk_per_trade_dollar = st.session_state.account_balance * st.session_state.risk_per_trade
    lot_size = risk_per_trade_dollar / (risk_amount * 100) if risk_amount > 0 else 0.01
    lot_size = round(max(lot_size, 0.01), 2)
    
    direction_text = "شراء (BUY)" if signal == "BUY" else "بيع (SELL)"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>الاتجاه:</b> {direction_text} (الثقة: {confidence:.1f}%)<br>
        <b>📍 الدخول:</b> {price_format.format(entry_price)}<br>
        <b>🛑 وقف الخسارة:</b> {price_format.format(stop_loss)}<br>
        <b>📦 اللوت المقترح:</b> {lot_size}<br>
        <b>📈 Trailing Stop:</b> {trailing_distance:.2f} نقطة<br>
        <div class="target-zone"><b>🎯 TP1 (1.5R):</b> {price_format.format(targets['target1'])}</div>
        <div class="target-zone" style="border-left-color:#ffaa00;"><b>🎯 TP2 (2.5R):</b> {price_format.format(targets['target2'])}</div>
        <div class="target-zone" style="border-left-color:#00ff88;"><b>🎯 TP3 (4R):</b> {price_format.format(targets['target3'])}</div>
        <b>📈 R:R قصوى:</b> 1:{targets['risk_reward_3']:.1f}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ إضافة الصفقة باللوت المحسوب", width='stretch'):
        tm = TradeManager()
        trade_data = {
            "direction": signal,
            "entry": entry_price,
            "lots": lot_size,
            "stop_loss": stop_loss,
            "take_profit": targets['target2'],
            "trailing_enabled": True,
            "trailing_distance": trailing_distance,
            "notes": f"الثقة {confidence:.1f}%"
        }
        trade_id = tm.add_trade(trade_data)
        st.success(f"✅ تم إضافة {trade_id}")
        st.rerun()
else:
    # عرض WAIT بتصميم مميز
    st.markdown(f"""
    <div class="signal-box wait-box">
        <div class="signal-text wait-text">⏳ WAIT</div>
        <div class="signal-confidence">الثقة: {confidence:.1f}% | السبب: الأدلة غير كافية</div>
    </div>
    """, unsafe_allow_html=True)

# الإشارة الرئيسية
st.markdown("---")
st.markdown("### 🧠 التحليل الهرمي - 5 محاور")

# عرض المحاور بشكل منظم
cols = st.columns(5)
axis_data = {
    "الاتجاه": score_details.get("trend", {}).get("score", 0),
    "الزخم": score_details.get("momentum", {}).get("score", 0),
    "ADX": score_details.get("adx", {}).get("score", 0),
    "الحجم": score_details.get("volume", {}).get("score", 0),
    "السعر": score_details.get("price", {}).get("score", 0)
}

for i, (name, score) in enumerate(axis_data.items()):
    color = "#00ff88" if score > 0 else ("#ff4444" if score < 0 else "#ffaa00")
    cols[i].metric(name, f"{score:.1f}", delta_color="normal")

with st.expander("📝 تفاصيل التحليل", expanded=True):
    explanation = explain_decision(signal, confidence, score_details, stop_loss, entry_price, targets)
    st.markdown(f'<div class="explanation-box">{explanation}</div>', unsafe_allow_html=True)

# ==========================================
# جميع الصفقات المقترحة
# ==========================================
st.markdown("---")
st.markdown("### 🚀 جميع الصفقات المقترحة")
if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
    df_all = st.session_state.all_signals.copy()
    df_trades = df_all[(df_all["الإشارة"].isin(["BUY", "SELL"])) & (df_all["الثقة"] >= 60)]
    if not df_trades.empty:
        cols = ["الزوج", "الإشارة", "الثقة", "سعر الدخول", "وقف الخسارة", "الهدف 1", "الهدف 2", "الهدف 3", "نسبة المخاطرة", "اللوت"]
        df_trades["الإشارة"] = df_trades["الإشارة"].apply(lambda x: "🟢 شراء" if x=="BUY" else "🔴 بيع")
        st.dataframe(df_trades[cols], use_container_width=True, hide_index=True)
        csv = df_trades.to_csv(index=False).encode('utf-8')
        st.download_button("📥 تحميل التقرير (CSV)", csv, "black_pyramid_report.csv", "text/csv")
    else:
        st.info("لا توجد صفقات مقترحة حالياً (WAIT)")
else:
    st.info("اضغط 'تحديث الكل'")

# ==========================================
# مؤشرات العملات
# ==========================================
st.markdown("---")
st.markdown("### 🌐 مؤشرات العملات")
if st.session_state.currency_indices is not None and not st.session_state.currency_indices.empty:
    indices_df = st.session_state.currency_indices
    latest = indices_df.iloc[-1]
    cols_cur = st.columns(len(latest))
    for i, (cur, val) in enumerate(latest.items()):
        cols_cur[i].metric(cur, f"{val:.2f}")
    
    fig_idx = go.Figure()
    for col in indices_df.columns:
        fig_idx.add_trace(go.Scatter(x=indices_df.index, y=indices_df[col], name=col))
    fig_idx.update_layout(height=350, template='plotly_dark', title="تطور مؤشرات العملات")
    st.plotly_chart(fig_idx, use_container_width=True)
else:
    st.info("قم بتحديث الإشارات لحساب المؤشرات.")

# ==========================================
# الرسم البياني (محسّن)
# ==========================================
st.markdown("---")
st.markdown("### 📈 Price Chart")
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])

# السعر والمتوسطات
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(color='cyan', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema100'], name='EMA100', line=dict(color='magenta', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema200'], name='EMA200', line=dict(color='white', dash='dash')), row=1, col=1)

# Bollinger
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)

# VWAP
fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='blue', width=0.8)), row=1, col=1)

# مستويات فيبوناتشي
if 'fib_levels' in locals():
    for level, price in fib_levels.items():
        if level in ['fib_382', 'fib_618', 'fib_786']:
            fig.add_hline(y=price, line_dash="dash", line_color="rgba(255,170,0,0.3)", row=1, col=1)

# SL/Entry
if stop_loss and entry_price:
    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
    fig.add_hline(y=entry_price, line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)

# VRSI
fig.add_trace(go.Scatter(x=df.index, y=df['vrsi'], name='VRSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=settings['vrsi_overbought'], line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=settings['vrsi_oversold'], line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

# MACD
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
        if is_rev:
            reversal_messages.append(f"⚠️ {trade['id']}: {msg}")
        if trade["trailing_enabled"]:
            tm.update_trailing_stop(trade["id"], current_price)

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
            tm.update_trailing_stop(trade['id'], current_price)
            st.rerun()
        if c2.button(f"🔍 انعكاس {trade['id']}", key=f"rev_{trade['id']}"):
            is_rev, msg = detect_reversal(df, trade)
            st.warning(msg) if is_rev else st.success("لا انعكاس")
        if c3.button(f"❌ إغلاق {trade['id']}", key=f"cl_{trade['id']}"):
            tm.close_trade(trade['id'], current_price)
            st.rerun()
else:
    st.write("لا توجد صفقات مفتوحة")

if st.session_state.show_form:
    with st.form("new_trade_form"):
        st.subheader("➕ تفاصيل الصفقة")
        direction = st.selectbox("الاتجاه", ["BUY", "SELL"])
        entry = st.number_input("الدخول", value=float(current_price), format="%.2f" if "Gold" in selected_pair_name else "%.4f")
        stop = st.number_input("وقف الخسارة", value=float(current_price - 20 if "Gold" in selected_pair_name else 0.001), format="%.2f" if "Gold" in selected_pair_name else "%.4f")
        lots = st.number_input("اللوت", min_value=0.01, value=0.1, step=0.01)
        if st.form_submit_button("إضافة"):
            td = {
                "direction": direction,
                "entry": entry,
                "lots": lots,
                "stop_loss": stop,
                "take_profit": entry + 40 if "Gold" in selected_pair_name else entry + 0.002,
                "trailing_enabled": False,
                "trailing_distance": 0,
                "notes": "يدوي"
            }
            tm.add_trade(td)
            st.success("تمت الإضافة")
            st.session_state.show_form = False
            st.rerun()

# ==========================================
# تذييل
# ==========================================
st.markdown(f"""
<div class="footer">
    <span class="brand">▲ BLACK PYRAMID v2009</span> • Hierarchical • 5 Pillars • Auto-Detection • WAIT Logic • Smart Risk
</div>
""", unsafe_allow_html=True)
