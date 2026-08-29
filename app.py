# ==========================================
# BLACK PYRAMID – الإصدار 2010 (Hierarchical Decision Engine)
# تاريخ التحديث: 2026-08-29
# إعادة هيكلة كاملة بناءً على التوصيات:
# - VRSI محدود التأثير
# - ADX قياسي مع +DI/-DI
# - ثقة منفصلة (Direction → Confirmation → Confidence)
# - أخبار لكل أصل، High Impact → WAIT
# - MTF هرمي (4H/1H/15M)
# - SL مبني على Structure + ATR + Liquidity
# - حجم لوت حسب قيمة النقطة
# - Fibonacci مع Swing والمناطق
# - Ichimoku بدون look-ahead
# - إدارة TP/Trailing المتقدمة
# - Reversal متعدد الأدلة
# - 7 طبقات لاتخاذ القرار
# - إصلاح NameError: إضافة POSITIVE_KEYWORDS و NEGATIVE_KEYWORDS
# - تحديث use_container_width → width='stretch'
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
from typing import Dict, Tuple, Optional, List, Any

# ==========================================
# 🔑 API Keys (يجب نقلها إلى st.secrets)
# ==========================================
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
NEWS_API_KEY = "b45e3a2b60d74c1bb1e8ddcdfa513bea"
ALPHA_VANTAGE_KEY = "017FGHT0JLG80XTG"

# ==========================================
# كلمات مفتاحية لتحليل المشاعر (مضافة)
# ==========================================
POSITIVE_KEYWORDS = [
    "higher", "increase", "growth", "positive", "strong", "beat", "surplus",
    "rally", "bullish", "up", "gain", "profit", "support", "stimulus",
    "cut", "reduce", "lower", "drop", "pullback", "correction", "recovery"
]

NEGATIVE_KEYWORDS = [
    "lower", "decrease", "decline", "negative", "weak", "miss", "deficit",
    "crash", "bearish", "down", "loss", "concern", "fear", "uncertainty",
    "hike", "raise", "higher rates", "inflation", "recession", "crisis",
    "war", "conflict", "sanctions", "default"
]

# ==========================================
# إعداد الصفحة
# ==========================================
st.set_page_config(
    page_title="Black Pyramid v2010",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🖤 الهوية البصرية
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
    .layer-indicator { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; margin: 2px; }
    .layer-1 { background: rgba(255,215,0,0.2); color: #ffd700; }
    .layer-2 { background: rgba(0,255,136,0.2); color: #00ff88; }
    .layer-3 { background: rgba(0,150,255,0.2); color: #0096ff; }
    .layer-4 { background: rgba(255,100,100,0.2); color: #ff6464; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">▲ BLACK PYRAMID v2010 ▲</div>
        <div class="main-subtitle">7-Layer Decision Engine • 4H→1H→15M • Smart Risk • WAIT Priority</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# قائمة الأزواج (مقسمة حسب الفئة)
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
if "max_total_risk" not in st.session_state:
    st.session_state.max_total_risk = 0.06  # 6% إجمالي
if "open_trades_risk" not in st.session_state:
    st.session_state.open_trades_risk = 0.0

# ==========================================
# إعدادات الأصول (موسعة)
# ==========================================
def get_asset_class(symbol: str) -> str:
    """تحديد فئة الأصل بدقة"""
    if symbol in ["GC=F", "SI=F", "XAUUSD=X", "XAGUSD=X"]:
        return "Gold"
    elif symbol == "BTC-USD":
        return "Bitcoin"
    elif symbol in ["ETH-USD", "ETHUSD=X"]:
        return "Ethereum"
    elif symbol in ["XRP-USD", "SOL-USD", "ADA-USD"]:
        return "CryptoAlt"
    else:
        return "Forex"

def get_asset_settings(symbol: str) -> Dict:
    """إعدادات لكل فئة أصل"""
    asset_class = get_asset_class(symbol)
    
    base_settings = {
        "vrsi_period": 14,
        "vrsi_overbought": 80,
        "vrsi_oversold": 20,
        "bb_period": 20,
        "adx_threshold": 25,
        "lookback_levels": 120,
        "confidence_threshold": 70,
        "atr_sl_multiplier": 1.5,
        "atr_trailing_multiplier": 1.0,
        "risk_cap": 0.70,
        "min_risk_reward": 1.5,
        "point_value": 1.0,  # قيمة النقطة بالدولار لكل لوت قياسي
        "lot_step": 0.01,
        "min_lot": 0.01,
        "max_lot": 100,
        "tp1_ratio": 0.3,
        "tp2_ratio": 0.3,
        "tp3_ratio": 0.4
    }
    
    if asset_class == "Gold":
        return {
            **base_settings,
            "bb_std": 2.2,
            "adx_threshold": 27,
            "lookback_levels": 175,
            "confidence_threshold": 72,
            "atr_sl_multiplier": 1.5,
            "atr_trailing_multiplier": 1.2,
            "risk_cap": 0.72,
            "point_value": 0.1,  # XAUUSD: 0.01 لوت = 1 دولار لكل نقطة
        }
    elif asset_class == "Bitcoin":
        return {
            **base_settings,
            "bb_std": 2.2,
            "adx_threshold": 30,
            "lookback_levels": 250,
            "confidence_threshold": 75,
            "atr_sl_multiplier": 1.8,
            "atr_trailing_multiplier": 1.5,
            "risk_cap": 0.75,
            "point_value": 1.0,  # BTCUSD: 1 لوت = 1 دولار لكل نقطة (لكن النقطة = 1$)
        }
    elif asset_class == "Ethereum":
        return {
            **base_settings,
            "bb_std": 2.2,
            "adx_threshold": 28,
            "lookback_levels": 200,
            "confidence_threshold": 72,
            "atr_sl_multiplier": 1.7,
            "atr_trailing_multiplier": 1.4,
            "risk_cap": 0.72,
            "point_value": 0.1,
        }
    elif asset_class == "CryptoAlt":
        return {
            **base_settings,
            "bb_std": 2.5,
            "adx_threshold": 28,
            "lookback_levels": 200,
            "confidence_threshold": 70,
            "atr_sl_multiplier": 2.0,
            "atr_trailing_multiplier": 1.6,
            "risk_cap": 0.70,
            "point_value": 0.1,
        }
    else:  # Forex
        return {
            **base_settings,
            "bb_std": 2.0,
            "adx_threshold": 25,
            "lookback_levels": 120,
            "confidence_threshold": 70,
            "atr_sl_multiplier": 1.2,
            "atr_trailing_multiplier": 0.9,
            "risk_cap": 0.70,
            "point_value": 10.0,  # Forex: 1 لوت قياسي = 10$ لكل نقطة
        }

# ==========================================
# دوال جلب البيانات (محسّنة)
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
def get_historical_data(symbol: str, period: str = "6mo", interval: str = "1h", max_retries: int = 5):
    """جلب البيانات مع فترات كافية لـ EMA200 على جميع الأطر"""
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
    
    # تحديد الفترة المناسبة للإطار
    if interval in ['15m', '5m']:
        period = "1mo"  # 15m يحتاج 1 شهر كافٍ
    elif interval == '1h':
        period = "3mo"  # 1h يحتاج 3 أشهر
    elif interval == '4h':
        period = "6mo"  # 4h يحتاج 6 أشهر
    else:
        period = "6mo"
    
    for attempt in range(max_retries):
        for sym in symbols_to_try:
            try:
                ticker = yf.Ticker(sym)
                df = ticker.history(period=period, interval=interval)
                if not df.empty and len(df) > 100:
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
# المؤشرات المحسّنة
# ==========================================
def calc_vrsi(data, volume, period=14, overbought=80, oversold=20):
    """
    VRSI مع تأثير محدود للحجم (يضيف/يطرح حتى 5 نقاط فقط).
    إذا كان الحجم مفقوداً، يعيد RSI عادي.
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    if volume is not None and not volume.isna().all():
        vol_ma = volume.rolling(window=period).mean()
        vol_ratio = volume / vol_ma
        vol_ratio = vol_ratio.fillna(1).clip(0.8, 1.2)  # تأثير محدود
        # تعديل طفيف: +/- 5 نقاط كحد أقصى
        adjustment = (vol_ratio - 1) * 25  # 0.8→-5, 1→0, 1.2→+5
        vrsi = rsi + adjustment
        vrsi = vrsi.clip(0, 100)
        return vrsi
    else:
        return rsi

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
    """
    حساب ADX بالطريقة القياسية (Wilder's smoothing).
    تعيد: ADX, +DI, -DI
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # حساب +DM و -DM
    up_move = high.diff()
    down_move = low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = (-down_move).where((down_move > up_move) & (down_move > 0), 0)
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's smoothing (EMA مع فترة = 2*period - 1)
    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(span=period, adjust=False).mean()
    
    return adx, plus_di, minus_di

def calc_ichimoku(df):
    """
    Ichimoku بدون look-ahead bias.
    Chikou محسوب من البيانات السابقة فقط.
    """
    high, low, close = df['high'], df['low'], df['close']
    tenkan = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
    kijun = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
    # Senkou A و B يتم إزاحتهما للأمام 26 شمعة (بيانات مستقبلية)
    # لكننا سنستخدمهما للإشارة إلى السحابة الحالية بدون look-ahead
    # نحسب السحابة من البيانات الحالية ثم نزحفها 26 شمعة للأمام
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
    # Chikou يتم إزاحته للخلف 26 شمعة (لا نستخدمه في القرار)
    # chikou = close.shift(-26)  # لا نستخدمه
    return tenkan, kijun, senkou_a, senkou_b

def calc_vwap(df):
    """Session VWAP (إعادة تعيين عند بداية الجلسة)"""
    # ببساطة نأخذ VWAP التراكمي، لكن يمكن تحسينه ليكون Session-based
    return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

def calc_mfi(df, period=14):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    return 100 - (100 / (1 + positive_flow / negative_flow))

def calc_fibonacci_levels(high: float, low: float, current_price: float, direction: str = "up"):
    """
    حساب مستويات فيبوناتشي بناءً على آخر Swing.
    direction: 'up' (Swing Low → Swing High) أو 'down' (Swing High → Swing Low)
    """
    diff = high - low
    if diff == 0:
        return {}
    
    if direction == "up":
        # من القاع إلى القمة (تصحيح صاعد)
        return {
            'fib_0': low,
            'fib_236': low + diff * 0.236,
            'fib_382': low + diff * 0.382,
            'fib_500': low + diff * 0.5,
            'fib_618': low + diff * 0.618,
            'fib_786': low + diff * 0.786,
            'fib_886': low + diff * 0.886,
            'fib_100': high
        }
    else:
        # من القمة إلى القاع (تصحيح هابط)
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
# SMC/ICT (محسّن)
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
    """تحليل SMC مع تركيز على الهيكل"""
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

# ==========================================
# الأخبار (مرتبطة بالأصل)
# ==========================================
def get_news_filters(symbol: str) -> Dict:
    """كلمات مفتاحية وتأثير حسب الأصل"""
    asset_class = get_asset_class(symbol)
    
    if asset_class == "Gold":
        return {
            "keywords": ["gold", "silver", "fed", "inflation", "cpi", "nfp", "dollar", "yield", "rates", "treasury"],
            "impact_multiplier": 1.0,
            "high_impact_words": ["emergency", "crisis", "plunge", "surge", "record high", "record low", "unexpected"]
        }
    elif asset_class in ["Bitcoin", "Ethereum", "CryptoAlt"]:
        return {
            "keywords": ["bitcoin", "btc", "crypto", "ethereum", "etf", "halving", "regulation", "sec", "fed", "liquidity", "mining"],
            "impact_multiplier": 1.3,
            "high_impact_words": ["ban", "approval", "rejection", "crash", "surge", "record", "unexpected", "black swan"]
        }
    else:
        return {
            "keywords": ["forex", "eur", "gbp", "jpy", "chf", "aud", "nzd", "cad", "central bank", "rates", "inflation", "gdp"],
            "impact_multiplier": 0.9,
            "high_impact_words": ["emergency", "crisis", "intervention", "unexpected", "surge", "plunge"]
        }

@st.cache_data(ttl=60)
def fetch_news(symbol: str = "EURUSD=X"):
    """جلب أخبار مرتبطة بالأصل"""
    news_filter = get_news_filters(symbol)
    query = " OR ".join(news_filter["keywords"])
    try:
        url = f"https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=10"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('articles', [])
    except:
        pass
    return []

def analyze_news_impact(articles: List, symbol: str) -> Tuple[str, float]:
    """
    تحليل الأخبار المرتبطة بالأصل.
    تعيد: (impact_level, score)
    impact_level: "HIGH", "MEDIUM", "LOW", "NEUTRAL"
    """
    if not articles:
        return "NEUTRAL", 0.0
    
    news_filter = get_news_filters(symbol)
    keywords = news_filter['keywords']
    high_impact_words = news_filter.get('high_impact_words', [])
    
    positive = 0
    negative = 0
    high_impact_count = 0
    relevance_score = 0
    
    for article in articles[:5]:
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = title + " " + description
        
        # حساب الصلة
        relevance = sum(1 for kw in keywords if kw in content)
        if relevance < 2:
            continue
        relevance_score += relevance
        
        # كلمات عالية التأثير
        high_impact = sum(1 for word in high_impact_words if word in content)
        high_impact_count += high_impact
        
        # المشاعر (باستخدام POSITIVE_KEYWORDS و NEGATIVE_KEYWORDS المعرفة)
        pos = sum(1 for word in POSITIVE_KEYWORDS if word in content)
        neg = sum(1 for word in NEGATIVE_KEYWORDS if word in content)
        
        if pos > neg:
            positive += 1
        elif neg > pos:
            negative += 1
    
    if high_impact_count >= 1:
        return "HIGH", 0.0
    elif relevance_score >= 5 and positive > negative:
        return "MEDIUM", 0.7
    elif relevance_score >= 5 and negative > positive:
        return "MEDIUM", -0.7
    elif relevance_score >= 3:
        return "LOW", 0.0
    else:
        return "NEUTRAL", 0.0

# ==========================================
# نظام القرار الهرمي (7 طبقات)
# ==========================================
def analyze_market_regime(df: pd.DataFrame) -> Dict:
    """الطبقة 1: تحديد نمط السوق"""
    if len(df) < 50:
        return {"regime": "UNKNOWN", "volatility": 0, "trend_strength": 0}
    
    last = df.iloc[-1]
    # حساب التقلب
    atr = calc_atr(df).iloc[-1] if 'atr' in df.columns else 0
    close = last['close']
    atr_pct = (atr / close) * 100 if close != 0 else 0
    
    # الاتجاه باستخدام EMA200
    if 'ema200' not in df.columns:
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    above_ema200 = last['close'] > df['ema200'].iloc[-1]
    
    # نمط السوق
    if atr_pct < 0.5:
        volatility = "LOW"
    elif atr_pct < 1.5:
        volatility = "MEDIUM"
    else:
        volatility = "HIGH"
    
    # اتجاه
    if above_ema200 and df['close'].iloc[-1] > df['close'].iloc[-20]:
        regime = "TRENDING_UP"
    elif not above_ema200 and df['close'].iloc[-1] < df['close'].iloc[-20]:
        regime = "TRENDING_DOWN"
    else:
        regime = "RANGING"
    
    return {
        "regime": regime,
        "volatility": volatility,
        "atr_pct": atr_pct,
        "trend_strength": abs(df['close'].iloc[-1] - df['close'].iloc[-20]) / close * 100 if close != 0 else 0
    }

def analyze_timeframe(symbol: str, interval: str, settings: Dict) -> Dict:
    """تحليل إطار زمني فردي (4H أو 1H أو 15M)"""
    df = get_historical_data(symbol, period="6mo", interval=interval)
    if df is None or len(df) < 50:
        return {"bias": "NEUTRAL", "confidence": 0, "details": []}
    
    # حساب المؤشرات الأساسية
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema100'] = df['close'].ewm(span=100, adjust=False).mean()
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    tenkan, kijun, senkou_a, senkou_b = calc_ichimoku(df)
    df['tenkan'] = tenkan
    df['kijun'] = kijun
    df['senkou_a'] = senkou_a
    df['senkou_b'] = senkou_b
    
    adx, plus_di, minus_di = calc_adx(df, period=14)
    df['adx'] = adx
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    
    last = df.iloc[-1]
    last_close = last['close']
    
    # 1. الاتجاه (EMA + Ichimoku)
    trend_score = 0
    trend_details = []
    
    # EMA
    if last_close > last['ema200']:
        trend_score += 2
        trend_details.append("فوق EMA200")
    else:
        trend_score -= 2
        trend_details.append("تحت EMA200")
    
    if last_close > last['ema100']:
        trend_score += 1
        trend_details.append("فوق EMA100")
    else:
        trend_score -= 1
        trend_details.append("تحت EMA100")
    
    # ترتيب المتوسطات
    if last['ema20'] > last['ema50'] > last['ema100'] > last['ema200']:
        trend_score += 2
        trend_details.append("ترتيب صاعد")
    elif last['ema20'] < last['ema50'] < last['ema100'] < last['ema200']:
        trend_score -= 2
        trend_details.append("ترتيب هابط")
    
    # Ichimoku
    if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']):
        if last_close > last['senkou_a'] and last_close > last['senkou_b']:
            trend_score += 2
            trend_details.append("فوق السحابة")
        elif last_close < last['senkou_a'] and last_close < last['senkou_b']:
            trend_score -= 2
            trend_details.append("تحت السحابة")
        else:
            trend_details.append("داخل السحابة")
    
    if not pd.isna(last['tenkan']) and not pd.isna(last['kijun']):
        if last['tenkan'] > last['kijun']:
            trend_score += 1
            trend_details.append("Tenkan > Kijun")
        else:
            trend_score -= 1
            trend_details.append("Tenkan < Kijun")
    
    # 2. الزخم (MACD + VRSI)
    macd, signal, hist = calc_macd(df['close'])
    df['macd'] = macd
    df['macd_signal'] = signal
    df['macd_histogram'] = hist
    if not pd.isna(df['macd'].iloc[-1]) and not pd.isna(df['macd_signal'].iloc[-1]):
        if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
            momentum = 1
        else:
            momentum = -1
    else:
        momentum = 0
    
    # 3. ADX وقوة الاتجاه
    adx_val = last['adx'] if not pd.isna(last['adx']) else 0
    di_bias = 0
    if not pd.isna(last['plus_di']) and not pd.isna(last['minus_di']):
        if last['plus_di'] > last['minus_di']:
            di_bias = 1
        else:
            di_bias = -1
    
    # 4. النتيجة النهائية
    bias = "NEUTRAL"
    confidence = 0
    
    if trend_score >= 3 and adx_val > settings['adx_threshold'] and di_bias >= 0:
        bias = "BULLISH"
        confidence = min(100, 50 + trend_score * 5 + adx_val * 0.5)
    elif trend_score <= -3 and adx_val > settings['adx_threshold'] and di_bias <= 0:
        bias = "BEARISH"
        confidence = min(100, 50 + abs(trend_score) * 5 + adx_val * 0.5)
    else:
        bias = "NEUTRAL"
        confidence = 50 + adx_val * 0.3
    
    return {
        "bias": bias,
        "confidence": confidence,
        "trend_score": trend_score,
        "adx": adx_val,
        "di_bias": di_bias,
        "details": trend_details
    }

def get_swing_levels(df: pd.DataFrame, lookback: int = 20) -> Tuple[float, float, str]:
    """تحديد آخر Swing High و Swing Low واتجاه الحركة"""
    if len(df) < lookback:
        return df['high'].max(), df['low'].min(), "up"
    
    recent_high = df['high'].iloc[-lookback:].max()
    recent_low = df['low'].iloc[-lookback:].min()
    
    # تحديد الاتجاه: مقارنة السعر الحالي بمنتصف النطاق
    mid = (recent_high + recent_low) / 2
    current = df['close'].iloc[-1]
    
    if current > mid:
        direction = "up"  # من القاع إلى القمة
    else:
        direction = "down"  # من القمة إلى القاع
    
    return recent_high, recent_low, direction

def calculate_position_size(entry: float, stop_loss: float, account_balance: float, risk_percent: float, point_value: float) -> float:
    """
    حساب حجم اللوت بناءً على قيمة النقطة.
    point_value: قيمة النقطة بالدولار لكل لوت قياسي.
    """
    risk_amount = account_balance * risk_percent
    risk_pips = abs(entry - stop_loss) * 10000  # تحويل إلى نقاط (تقريبي)
    if risk_pips <= 0:
        return 0.01
    lot_size = risk_amount / (risk_pips * point_value * 0.0001)  # معادلة تقريبية
    return max(0.01, min(100, round(lot_size, 2)))

# ==========================================
# المحرك الرئيسي (7 طبقات)
# ==========================================
def analyze_asset_hierarchical(df: pd.DataFrame, symbol: str, settings: Dict) -> Dict:
    """
    التحليل الهرمي الكامل (7 طبقات).
    تعيد: {
        'signal': 'BUY'/'SELL'/'WAIT',
        'confidence': float,
        'layers': {...},
        'entry': float,
        'stop_loss': float,
        'targets': {...},
        'risk_reward': float,
        'position_size': float,
        'trailing_distance': float,
        'explanation': str
    }
    """
    result = {
        'signal': 'WAIT',
        'confidence': 0,
        'layers': {},
        'entry': None,
        'stop_loss': None,
        'targets': {},
        'risk_reward': 0,
        'position_size': 0,
        'trailing_distance': 0,
        'explanation': ''
    }
    
    # ========================================
    # الطبقة 1: Market Regime
    # ========================================
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    regime_data = analyze_market_regime(df)
    result['layers']['regime'] = regime_data
    
    # ========================================
    # الطبقة 2: 4H Bias
    # ========================================
    tf_4h = analyze_timeframe(symbol, '4h', settings)
    result['layers']['4h'] = tf_4h
    
    # ========================================
    # الطبقة 3: 1H Confirmation
    # ========================================
    tf_1h = analyze_timeframe(symbol, '1h', settings)
    result['layers']['1h'] = tf_1h
    
    # ========================================
    # الطبقة 4: 15M Trigger
    # ========================================
    tf_15m = analyze_timeframe(symbol, '15m', settings)
    result['layers']['15m'] = tf_15m
    
    # ========================================
    # الطبقة 5: Price Location (Fibonacci + BB + SMC)
    # ========================================
    last = df.iloc[-1]
    current_price = last['close']
    
    # Swing High/Low
    swing_high, swing_low, swing_dir = get_swing_levels(df, lookback=settings['lookback_levels'])
    fib_levels = calc_fibonacci_levels(swing_high, swing_low, current_price, swing_dir)
    
    # Bollinger
    bb_upper, bb_middle, bb_lower = calc_bollinger_bands(df['close'], period=settings['bb_period'], std_dev=settings['bb_std'])
    bb_width = (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1] if bb_middle.iloc[-1] != 0 else 0
    
    # SMC
    df_smc = analyze_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    
    price_score = 0
    price_details = []
    
    # فيبوناتشي مناطق
    if fib_levels:
        fib_382 = fib_levels.get('fib_382', current_price)
        fib_618 = fib_levels.get('fib_618', current_price)
        fib_786 = fib_levels.get('fib_786', current_price)
        
        # Premium / Equilibrium / Discount
        if current_price < fib_382:
            price_score += 1
            price_details.append("منطقة Discount")
        elif current_price > fib_618:
            price_score -= 1
            price_details.append("منطقة Premium")
        else:
            price_details.append("منطقة Equilibrium")
        
        # مناطق اهتمام إضافية
        if current_price < fib_786 and current_price > fib_618:
            price_score += 0.5
            price_details.append("قرب 78.6% (دعم قوي)")
    
    # Bollinger
    if bb_width < 0.05:  # سوق جانبي
        if current_price < bb_lower.iloc[-1] * 1.005:
            price_score += 1
            price_details.append("BB سفلي (انعكاس محتمل)")
        elif current_price > bb_upper.iloc[-1] * 0.995:
            price_score -= 1
            price_details.append("BB علوي (انعكاس محتمل)")
    else:  # سوق واسع
        if current_price > bb_upper.iloc[-1] * 0.995:
            if tf_4h['bias'] == "BULLISH" and tf_1h['bias'] == "BULLISH":
                price_score += 1
                price_details.append("BB علوي + اتجاه صاعد → استمرار")
            else:
                price_score -= 1
                price_details.append("BB علوي في سوق غير صاعد → حذر")
        elif current_price < bb_lower.iloc[-1] * 1.005:
            if tf_4h['bias'] == "BEARISH" and tf_1h['bias'] == "BEARISH":
                price_score -= 1
                price_details.append("BB سفلي + اتجاه هابط → استمرار")
            else:
                price_score += 1
                price_details.append("BB سفلي في سوق غير هابط → حذر")
    
    # SMC (تأكيدات)
    smc_confirms = 0
    if last_smc.get('order_block_bullish', False):
        price_score += 1
        price_details.append("Bullish OB")
        smc_confirms += 1
    elif last_smc.get('order_block_bearish', False):
        price_score -= 1
        price_details.append("Bearish OB")
        smc_confirms += 1
    
    if last_smc.get('fvg_bullish', False):
        price_score += 0.5
        price_details.append("FVG شراء")
        smc_confirms += 0.5
    elif last_smc.get('fvg_bearish', False):
        price_score -= 0.5
        price_details.append("FVG بيع")
        smc_confirms += 0.5
    
    if last_smc.get('liquidity_sweep_bullish', False):
        price_score += 1
        price_details.append("اجتياح سيولة شراء")
    elif last_smc.get('liquidity_sweep_bearish', False):
        price_score -= 1
        price_details.append("اجتياح سيولة بيع")
    
    result['layers']['price'] = {
        'score': price_score,
        'details': price_details,
        'fib_levels': fib_levels,
        'bb_width': bb_width,
        'smc_confirms': smc_confirms
    }
    
    # ========================================
    # الطبقة 6: News Risk
    # ========================================
    news_articles = fetch_news(symbol)
    news_impact, news_score = analyze_news_impact(news_articles, symbol)
    result['layers']['news'] = {
        'impact': news_impact,
        'score': news_score,
        'articles': news_articles[:3]
    }
    
    # ========================================
    # الطبقة 7: Risk Engine & القرار النهائي
    # ========================================
    # تجميع الطبقات 2-5
    tf_4h_bias = tf_4h['bias']
    tf_1h_bias = tf_1h['bias']
    tf_15m_bias = tf_15m['bias']
    
    # حساب درجة الاتجاه (4H + 1H)
    direction_score = 0
    if tf_4h_bias == "BULLISH":
        direction_score += 3
    elif tf_4h_bias == "BEARISH":
        direction_score -= 3
    
    if tf_1h_bias == "BULLISH":
        direction_score += 2
    elif tf_1h_bias == "BEARISH":
        direction_score -= 2
    
    # حساب درجة التأكيد (15M + Price + SMC)
    confirmation_score = 0
    if tf_15m_bias == "BULLISH":
        confirmation_score += 1
    elif tf_15m_bias == "BEARISH":
        confirmation_score -= 1
    
    confirmation_score += price_score * 0.5  # price_score بين -4 و +4
    confirmation_score += smc_confirms * 0.5
    
    # قوة ADX
    adx_strength = (tf_4h.get('adx', 0) + tf_1h.get('adx', 0) + tf_15m.get('adx', 0)) / 3
    adx_filter = adx_strength > settings['adx_threshold']
    
    # ========================================
    # القرار النهائي
    # ========================================
    # شروط WAIT الصارمة
    wait_conditions = []
    
    # 1. تعارض 4H و 1H
    if tf_4h_bias != tf_1h_bias and tf_4h_bias != "NEUTRAL" and tf_1h_bias != "NEUTRAL":
        wait_conditions.append("تعارض بين 4H و 1H")
    
    # 2. 4H محايد
    if tf_4h_bias == "NEUTRAL":
        wait_conditions.append("4H محايد (لا اتجاه واضح)")
    
    # 3. ADX ضعيف
    if not adx_filter:
        wait_conditions.append(f"ADX ضعيف ({adx_strength:.1f} < {settings['adx_threshold']})")
    
    # 4. أخبار عالية التأثير
    if news_impact == "HIGH":
        wait_conditions.append("أخبار عالية التأثير → WAIT")
    
    # 5. السعر داخل السحابة (Ichimoku) على 4H
    df_4h = get_historical_data(symbol, interval='4h')
    if df_4h is not None and len(df_4h) > 50:
        _, _, senkou_a, senkou_b = calc_ichimoku(df_4h)
        if not pd.isna(senkou_a.iloc[-1]) and not pd.isna(senkou_b.iloc[-1]):
            price_4h = df_4h['close'].iloc[-1]
            if price_4h < max(senkou_a.iloc[-1], senkou_b.iloc[-1]) and price_4h > min(senkou_a.iloc[-1], senkou_b.iloc[-1]):
                wait_conditions.append("السعر داخل سحابة Ichimoku على 4H")
    
    # 6. 15M لا يعطي Trigger
    if tf_15m_bias == "NEUTRAL":
        wait_conditions.append("15M محايد (لا يوجد Trigger)")
    
    # إذا كان هناك شرط WAIT، نخرج مباشرة
    if wait_conditions:
        result['signal'] = 'WAIT'
        result['confidence'] = 50 + adx_strength * 0.3
        result['layers']['decision'] = {
            'signal': 'WAIT',
            'reasons': wait_conditions,
            'direction_score': direction_score,
            'confirmation_score': confirmation_score,
            'adx_strength': adx_strength
        }
        result['explanation'] = f"⏳ WAIT: " + " | ".join(wait_conditions)
        return result
    
    # ========================================
    # BUY / SELL (عند اجتياز جميع الشروط)
    # ========================================
    # تحديد الاتجاه النهائي
    if direction_score >= 4 and confirmation_score >= 1 and adx_filter:
        final_signal = "BUY"
    elif direction_score <= -4 and confirmation_score <= -1 and adx_filter:
        final_signal = "SELL"
    else:
        final_signal = "WAIT"
        result['signal'] = 'WAIT'
        result['confidence'] = 50 + adx_strength * 0.3
        result['layers']['decision'] = {
            'signal': 'WAIT',
            'reasons': ['درجة الاتجاه أو التأكيد غير كافية'],
            'direction_score': direction_score,
            'confirmation_score': confirmation_score,
            'adx_strength': adx_strength
        }
        result['explanation'] = f"⏳ WAIT: direction_score={direction_score}, confirmation_score={confirmation_score}"
        return result
    
    # ========================================
    # حساب الثقة
    # ========================================
    # اتجاه: 4H (40%) + 1H (30%)
    trend_conf = 0
    if tf_4h_bias == final_signal:
        trend_conf += 40
    if tf_1h_bias == final_signal:
        trend_conf += 30
    
    # تأكيد: 15M (15%) + Price (10%) + SMC (5%)
    confirm_conf = 0
    if tf_15m_bias == final_signal:
        confirm_conf += 15
    if (final_signal == "BUY" and price_score > 0) or (final_signal == "SELL" and price_score < 0):
        confirm_conf += 10
    if smc_confirms >= 1:
        confirm_conf += 5
    
    # ADX مكافأة
    adx_bonus = min(10, (adx_strength - settings['adx_threshold']) * 0.5)
    
    confidence = min(100, trend_conf + confirm_conf + adx_bonus)
    
    # ========================================
    # وقف الخسارة والأهداف
    # ========================================
    atr_value = calc_atr(df).iloc[-1] if 'atr' in df.columns else 0
    entry_price = current_price
    
    # SL بناءً على الهيكل + ATR + Liquidity
    if final_signal == "BUY":
        # آخر قاع مهم
        swing_low_recent = df['low'].iloc[-20:].min()
        # مناطق السيولة (SSL)
        ssl = df_smc['ssl'].iloc[-1] if 'ssl' in df_smc.columns else swing_low_recent
        
        # SL = أدنى (Swing Low, SSL) - Buffer ATR
        stop_loss = min(swing_low_recent, ssl) - atr_value * settings['atr_sl_multiplier'] * 0.3
        # حماية: لا يزيد عن 2x ATR من الدخول
        if (entry_price - stop_loss) > atr_value * 2:
            stop_loss = entry_price - atr_value * 2
        if (entry_price - stop_loss) < atr_value * 0.5:
            stop_loss = entry_price - atr_value * 0.5
    else:
        # آخر قمة مهمة
        swing_high_recent = df['high'].iloc[-20:].max()
        bsl = df_smc['bsl'].iloc[-1] if 'bsl' in df_smc.columns else swing_high_recent
        
        stop_loss = max(swing_high_recent, bsl) + atr_value * settings['atr_sl_multiplier'] * 0.3
        if (stop_loss - entry_price) > atr_value * 2:
            stop_loss = entry_price + atr_value * 2
        if (stop_loss - entry_price) < atr_value * 0.5:
            stop_loss = entry_price + atr_value * 0.5
    
    # التأكد من عدم وضع SL في منطقة السيولة (تحسين)
    # (سيتم تحسينه لاحقاً)
    
    risk = abs(entry_price - stop_loss)
    if risk == 0:
        risk = atr_value * 0.5
    
    # الأهداف الثلاثة
    if final_signal == "BUY":
        targets = {
            'target1': entry_price + risk * 1.5,
            'target2': entry_price + risk * 2.5,
            'target3': entry_price + risk * 4.0,
            'risk_reward_1': 1.5,
            'risk_reward_2': 2.5,
            'risk_reward_3': 4.0
        }
    else:
        targets = {
            'target1': entry_price - risk * 1.5,
            'target2': entry_price - risk * 2.5,
            'target3': entry_price - risk * 4.0,
            'risk_reward_1': 1.5,
            'risk_reward_2': 2.5,
            'risk_reward_3': 4.0
        }
    
    # R:R النهائي
    rr = targets['risk_reward_3']
    
    # إذا كان R:R أقل من الحد الأدنى، نخرج WAIT
    if rr < settings.get('min_risk_reward', 1.5):
        result['signal'] = 'WAIT'
        result['confidence'] = confidence * 0.6
        result['layers']['decision'] = {
            'signal': 'WAIT',
            'reasons': [f'R:R غير كافٍ ({rr:.1f})'],
            'direction_score': direction_score,
            'confirmation_score': confirmation_score,
            'adx_strength': adx_strength
        }
        result['explanation'] = f"⏳ WAIT: R:R = {rr:.1f} (أقل من {settings['min_risk_reward']})"
        return result
    
    # ========================================
    # حساب حجم اللوت
    # ========================================
    point_value = settings.get('point_value', 10)
    lot_size = calculate_position_size(entry_price, stop_loss, st.session_state.account_balance, 
                                      st.session_state.risk_per_trade, point_value)
    
    # ========================================
    # مسافة Trailing
    # ========================================
    trailing_distance = atr_value * settings['atr_trailing_multiplier']
    
    # ========================================
    # تجميع النتائج النهائية
    # ========================================
    result['signal'] = final_signal
    result['confidence'] = confidence
    result['layers']['decision'] = {
        'signal': final_signal,
        'reasons': [],
        'direction_score': direction_score,
        'confirmation_score': confirmation_score,
        'adx_strength': adx_strength,
        'wait_conditions': wait_conditions
    }
    result['entry'] = entry_price
    result['stop_loss'] = stop_loss
    result['targets'] = targets
    result['risk_reward'] = rr
    result['position_size'] = lot_size
    result['trailing_distance'] = trailing_distance
    
    # شرح القرار
    explanation = f"**{final_signal}** - الثقة: {confidence:.1f}%\n"
    explanation += f"الاتجاه (4H): {tf_4h_bias} | 1H: {tf_1h_bias} | 15M: {tf_15m_bias}\n"
    explanation += f"ADX: {adx_strength:.1f} | SMC: {smc_confirms} تأكيدات\n"
    explanation += f"R:R: 1:{rr:.1f} | حجم اللوت: {lot_size:.2f}\n"
    explanation += f"الدخول: {entry_price:.4f} | SL: {stop_loss:.4f}\n"
    explanation += f"TP1: {targets['target1']:.4f} | TP2: {targets['target2']:.4f} | TP3: {targets['target3']:.4f}"
    result['explanation'] = explanation
    
    return result

# ==========================================
# جمع جميع الإشارات
# ==========================================
@st.cache_data(ttl=120)
def get_all_signals():
    results = []
    
    data_dict = {}
    for pair_name, symbol in PAIRS.items():
        try:
            df = get_historical_data(symbol, period="6mo", interval="1h")
            if df is not None and len(df) > 100:
                data_dict[symbol] = df
        except:
            continue
    
    if data_dict:
        indices = calculate_currency_indices(data_dict)
        if indices:
            st.session_state.currency_indices = pd.DataFrame(indices)
    
    for pair_name, symbol in PAIRS.items():
        if symbol not in data_dict:
            continue
        
        df = data_dict[symbol]
        settings = get_asset_settings(symbol)
        
        result = analyze_asset_hierarchical(df, symbol, settings)
        
        # تنسيق العرض
        if "Gold" in pair_name or "Silver" in pair_name or "Bitcoin" in pair_name or "Ethereum" in pair_name or "Ripple" in pair_name or "Solana" in pair_name or "Cardano" in pair_name:
            price_str = f"${df['close'].iloc[-1]:,.2f}"
            fmt = "${:,.2f}"
        else:
            price_str = f"{df['close'].iloc[-1]:.4f}"
            fmt = "{:.4f}"
        
        results.append({
            "الزوج": pair_name,
            "الإشارة": result['signal'],
            "الثقة": round(result['confidence'], 1),
            "السعر": price_str,
            "سعر الدخول": fmt.format(result['entry']) if result['entry'] else "N/A",
            "وقف الخسارة": fmt.format(result['stop_loss']) if result['stop_loss'] else "N/A",
            "الهدف 1": fmt.format(result['targets'].get('target1')) if result['targets'] else "N/A",
            "الهدف 2": fmt.format(result['targets'].get('target2')) if result['targets'] else "N/A",
            "الهدف 3": fmt.format(result['targets'].get('target3')) if result['targets'] else "N/A",
            "نسبة المخاطرة": f"1:{result['risk_reward']:.1f}" if result['risk_reward'] else "N/A",
            "اللوت": result['position_size'] if result['position_size'] else 0
        })
    
    return pd.DataFrame(results)

# ==========================================
# إدارة الصفقات (محسّنة مع TP1/TP2/TP3)
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
            "take_profit": trade_data["take_profit"],  # TP2
            "targets": trade_data.get("targets", {}),
            "tp_ratios": trade_data.get("tp_ratios", [0.3, 0.3, 0.4]),
            "trailing_enabled": trade_data.get("trailing_enabled", False),
            "trailing_distance": trade_data.get("trailing_distance", 0),
            "highest_price": trade_data["entry"],
            "lowest_price": trade_data["entry"],
            "status": "open",
            "stage": 0,  # 0=ابتدائي, 1=TP1 محقق (Breakeven), 2=TP2 محقق (Trailing)
            "tp1_hit": False,
            "tp2_hit": False,
            "tp3_hit": False,
            "closed_parts": [],
            "notes": trade_data.get("notes", "")
        }
        self.open_trades.append(trade)
        self.save_trades()
        return trade_id
    
    def update_trade(self, trade_id, current_price):
        """تحديث الصفقة: التحقق من TP1/TP2/TP3 وتحديث الوقف"""
        for trade in self.open_trades:
            if trade["id"] != trade_id or trade["status"] != "open":
                continue
            
            direction = trade["direction"]
            entry = trade["entry"]
            targets = trade.get("targets", {})
            
            # التحقق من TP1
            if not trade["tp1_hit"] and targets:
                tp1 = targets.get("target1")
                if tp1:
                    if direction == "BUY" and current_price >= tp1:
                        trade["tp1_hit"] = True
                        trade["stage"] = 1
                        # نقل SL إلى Breakeven
                        trade["stop_loss"] = entry
                        # إغلاق جزء TP1
                        tp1_ratio = trade["tp_ratios"][0] if len(trade["tp_ratios"]) > 0 else 0.3
                        trade["closed_parts"].append({"level": "TP1", "price": tp1, "ratio": tp1_ratio})
                        self.save_trades()
                    elif direction == "SELL" and current_price <= tp1:
                        trade["tp1_hit"] = True
                        trade["stage"] = 1
                        trade["stop_loss"] = entry
                        tp1_ratio = trade["tp_ratios"][0] if len(trade["tp_ratios"]) > 0 else 0.3
                        trade["closed_parts"].append({"level": "TP1", "price": tp1, "ratio": tp1_ratio})
                        self.save_trades()
            
            # التحقق من TP2
            if trade["tp1_hit"] and not trade["tp2_hit"] and targets:
                tp2 = targets.get("target2")
                if tp2:
                    if direction == "BUY" and current_price >= tp2:
                        trade["tp2_hit"] = True
                        trade["stage"] = 2
                        # تفعيل Trailing
                        trade["trailing_enabled"] = True
                        tp2_ratio = trade["tp_ratios"][1] if len(trade["tp_ratios"]) > 1 else 0.3
                        trade["closed_parts"].append({"level": "TP2", "price": tp2, "ratio": tp2_ratio})
                        self.save_trades()
                    elif direction == "SELL" and current_price <= tp2:
                        trade["tp2_hit"] = True
                        trade["stage"] = 2
                        trade["trailing_enabled"] = True
                        tp2_ratio = trade["tp_ratios"][1] if len(trade["tp_ratios"]) > 1 else 0.3
                        trade["closed_parts"].append({"level": "TP2", "price": tp2, "ratio": tp2_ratio})
                        self.save_trades()
            
            # التحقق من TP3
            if trade["tp2_hit"] and not trade["tp3_hit"] and targets:
                tp3 = targets.get("target3")
                if tp3:
                    if direction == "BUY" and current_price >= tp3:
                        trade["tp3_hit"] = True
                        trade["stage"] = 3
                        tp3_ratio = trade["tp_ratios"][2] if len(trade["tp_ratios"]) > 2 else 0.4
                        trade["closed_parts"].append({"level": "TP3", "price": tp3, "ratio": tp3_ratio})
                        self.save_trades()
                    elif direction == "SELL" and current_price <= tp3:
                        trade["tp3_hit"] = True
                        trade["stage"] = 3
                        tp3_ratio = trade["tp_ratios"][2] if len(trade["tp_ratios"]) > 2 else 0.4
                        trade["closed_parts"].append({"level": "TP3", "price": tp3, "ratio": tp3_ratio})
                        self.save_trades()
            
            # تحديث Trailing Stop (بعد TP2)
            if trade["trailing_enabled"] and trade["tp2_hit"]:
                if direction == "BUY":
                    if current_price > trade["highest_price"]:
                        trade["highest_price"] = current_price
                    new_stop = trade["highest_price"] - trade["trailing_distance"]
                    if new_stop > trade["stop_loss"]:
                        trade["stop_loss"] = new_stop
                        self.save_trades()
                else:
                    if current_price < trade["lowest_price"]:
                        trade["lowest_price"] = current_price
                    new_stop = trade["lowest_price"] + trade["trailing_distance"]
                    if new_stop < trade["stop_loss"]:
                        trade["stop_loss"] = new_stop
                        self.save_trades()
    
    def close_trade(self, trade_id, exit_price):
        for i, trade in enumerate(self.open_trades):
            if trade["id"] == trade_id:
                # حساب الربح بناءً على الأجزاء المغلقة
                total_profit = 0
                remaining_ratio = 1.0
                
                for part in trade.get("closed_parts", []):
                    remaining_ratio -= part["ratio"]
                
                if remaining_ratio > 0.01:
                    if trade["direction"] == "BUY":
                        pips = (exit_price - trade["entry"]) * 100
                    else:
                        pips = (trade["entry"] - exit_price) * 100
                    profit = pips * trade["lots"] * remaining_ratio * 0.1
                    total_profit += profit
                
                trade["exit"] = exit_price
                trade["status"] = "closed"
                trade["profit"] = round(total_profit, 2)
                trade["result"] = "win" if total_profit > 0 else "loss"
                trade["close_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_trades.append(trade)
                self.open_trades.pop(i)
                self.save_trades()
                return total_profit
        return None

# ==========================================
# الشريط الجانبي المبسط
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ الإعدادات")
    
    # عرض نوع الأصل الحالي
    if 'selected_symbol' in locals():
        settings = get_asset_settings(selected_symbol)
        st.markdown(f"**نوع الأصل:** {get_asset_class(selected_symbol)}")
        st.markdown(f"**عتبة الثقة:** {settings['confidence_threshold']}%")
        st.markdown(f"**عتبة ADX:** {settings['adx_threshold']}")
    
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
                st.session_state.all_signals = get_all_signals()
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
news_filter = get_news_filters(selected_symbol)
if news_articles:
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

df = get_historical_data(selected_symbol, period="6mo", interval="1h")
if df is None:
    st.error("⚠️ تعذر تحميل البيانات")
    st.stop()
if current_price is None:
    current_price = df['close'].iloc[-1]
    change = 0

# التحليل الهرمي
settings = get_asset_settings(selected_symbol)
result = analyze_asset_hierarchical(df, selected_symbol, settings)

# عرض السعر
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

# عرض الصفقة المقترحة
if result['signal'] in ["BUY", "SELL"] and result['confidence'] >= settings['confidence_threshold']:
    direction_text = "شراء (BUY)" if result['signal'] == "BUY" else "بيع (SELL)"
    st.markdown(f"""
    <div class="suggested-trade">
        <b>الاتجاه:</b> {direction_text} (الثقة: {result['confidence']:.1f}%)<br>
        <b>📍 الدخول:</b> {price_format.format(result['entry'])}<br>
        <b>🛑 وقف الخسارة:</b> {price_format.format(result['stop_loss'])}<br>
        <b>📦 اللوت المقترح:</b> {result['position_size']:.2f}<br>
        <b>📈 Trailing Stop:</b> {result['trailing_distance']:.2f} نقطة<br>
        <div class="target-zone"><b>🎯 TP1 (1.5R):</b> {price_format.format(result['targets']['target1'])}</div>
        <div class="target-zone" style="border-left-color:#ffaa00;"><b>🎯 TP2 (2.5R):</b> {price_format.format(result['targets']['target2'])}</div>
        <div class="target-zone" style="border-left-color:#00ff88;"><b>🎯 TP3 (4R):</b> {price_format.format(result['targets']['target3'])}</div>
        <b>📈 R:R قصوى:</b> 1:{result['risk_reward']:.1f}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ إضافة الصفقة باللوت المحسوب", width='stretch'):
        tm = TradeManager()
        trade_data = {
            "direction": result['signal'],
            "entry": result['entry'],
            "lots": result['position_size'],
            "stop_loss": result['stop_loss'],
            "take_profit": result['targets']['target2'],
            "targets": result['targets'],
            "tp_ratios": [0.3, 0.3, 0.4],
            "trailing_enabled": False,
            "trailing_distance": result['trailing_distance'],
            "notes": f"الثقة {result['confidence']:.1f}%"
        }
        trade_id = tm.add_trade(trade_data)
        st.success(f"✅ تم إضافة {trade_id}")
        st.rerun()
else:
    st.markdown(f"""
    <div class="signal-box wait-box">
        <div class="signal-text wait-text">⏳ WAIT</div>
        <div class="signal-confidence">الثقة: {result['confidence']:.1f}% | السبب: {result.get('explanation', 'الأدلة غير كافية')}</div>
    </div>
    """, unsafe_allow_html=True)

# عرض الطبقات
st.markdown("---")
st.markdown("### 🏗️ التحليل الهرمي (7 طبقات)")

layers = result.get('layers', {})
cols = st.columns(7)

layer_names = ["Regime", "4H", "1H", "15M", "Price", "News", "Decision"]
layer_data = [
    layers.get('regime', {}).get('regime', 'UNKNOWN'),
    layers.get('4h', {}).get('bias', 'NEUTRAL'),
    layers.get('1h', {}).get('bias', 'NEUTRAL'),
    layers.get('15m', {}).get('bias', 'NEUTRAL'),
    f"{layers.get('price', {}).get('score', 0):.1f}",
    layers.get('news', {}).get('impact', 'NEUTRAL'),
    result['signal']
]

for i, (name, value) in enumerate(zip(layer_names, layer_data)):
    if i < len(cols):
        cols[i].metric(name, str(value))

# شرح القرار
with st.expander("📝 تفاصيل التحليل الكامل", expanded=True):
    st.markdown(f'<div class="explanation-box">{result.get("explanation", "لا توجد تفاصيل")}</div>', unsafe_allow_html=True)
    
    # عرض تفاصيل كل طبقة
    st.subheader("تفاصيل الطبقات")
    for layer_name, data in layers.items():
        st.markdown(f"**{layer_name.upper()}**")
        st.json(data)

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
# الرسم البياني
# ==========================================
st.markdown("---")
st.markdown("### 📈 Price Chart with Levels")
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
fib_levels = layers.get('price', {}).get('fib_levels', {})
for level, price in fib_levels.items():
    if level in ['fib_382', 'fib_618', 'fib_786']:
        fig.add_hline(y=price, line_dash="dash", line_color="rgba(255,170,0,0.3)", row=1, col=1)

# SL/Entry
if result['entry'] and result['stop_loss']:
    fig.add_hline(y=result['stop_loss'], line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
    fig.add_hline(y=result['entry'], line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)

# VRSI
if 'vrsi' in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df['vrsi'], name='VRSI', line=dict(color='purple')), row=2, col=1)
    fig.add_hline(y=settings['vrsi_overbought'], line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
    fig.add_hline(y=settings['vrsi_oversold'], line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

# MACD
if 'macd' in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
    fig.add_bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color='gray', opacity=0.3, row=3, col=1)

fig.update_layout(height=700, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# إدارة الصفقات
# ==========================================
st.markdown("---")
st.markdown("### 💼 إدارة الصفقات (مع TP1/TP2/TP3)")
tm = TradeManager()

# تحديث الصفقات المفتوحة
for trade in tm.open_trades:
    if trade["status"] == "open":
        tm.update_trade(trade["id"], current_price)

# عرض الصفقات المفتوحة
if tm.open_trades:
    for trade in tm.open_trades:
        # حساب نسبة الإغلاق
        closed_ratio = sum(p["ratio"] for p in trade.get("closed_parts", []))
        remaining_ratio = 1 - closed_ratio
        stage_text = ["🟡 ابتدائي", "🟢 Breakeven (TP1)", "🔵 Trailing (TP2)", "🟣 TP3 محقق"][trade.get("stage", 0)]
        
        st.markdown(f"""
        <div class="trade-row">
            <b>{trade['id']}</b> | {trade['direction']} | الدخول: {trade['entry']} | اللوت: {trade['lots']} | 
            الوقف: {trade['stop_loss']} | الهدف: {trade['take_profit']}
            <br><span style="color:#aaa;">{stage_text} | متبقي: {remaining_ratio*100:.0f}% | {"🔄 Trailing مفعّل" if trade.get('trailing_enabled') else ""}</span>
            <br><span style="color:#888;font-size:0.8rem;">
                TP1: {trade.get('tp1_hit', False)} | TP2: {trade.get('tp2_hit', False)} | TP3: {trade.get('tp3_hit', False)}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        if c1.button(f"🔄 تحديث {trade['id']}", key=f"up_{trade['id']}"):
            tm.update_trade(trade['id'], current_price)
            st.rerun()
        if c2.button(f"❌ إغلاق {trade['id']}", key=f"cl_{trade['id']}"):
            tm.close_trade(trade['id'], current_price)
            st.rerun()
else:
    st.write("لا توجد صفقات مفتوحة")

# عرض الصفقات المغلقة
if tm.closed_trades:
    profits = [t.get('profit', 0) for t in tm.closed_trades if 'profit' in t]
    if profits:
        win_rate = sum(1 for p in profits if p > 0) / len(profits) * 100
        total_profit = sum(profits)
        st.metric("نسبة الربح", f"{win_rate:.1f}%")
        st.metric("إجمالي الربح", f"${total_profit:.2f}")

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
                "targets": {},
                "tp_ratios": [0.3, 0.3, 0.4],
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
    <span class="brand">▲ BLACK PYRAMID v2010</span> • 7-Layer Decision Engine • 4H→1H→15M • Smart Risk • WAIT Priority
</div>
""", unsafe_allow_html=True)
