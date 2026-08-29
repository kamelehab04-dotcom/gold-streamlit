# ==========================================
# BLACK PYRAMID – الإصدار 2002 (النسخة النهائية المتكاملة بالكامل)
# تاريخ التحديث: 2026-08-29
# المصدر: GoldAPI + yfinance + FMP API + تحليلات متقدمة
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

# ==========================================
# إعداد الصفحة
# ==========================================
st.set_page_config(
    page_title="Black Pyramid",
    page_icon="▲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# الهوية البصرية
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
    .main-header, .price-card, .signal-box, .suggested-trade, .trade-row, .entry-zone, .target-zone, .stop-loss-level, .reversal-alert, .news-card, .explanation-box, .stButton button, .stSelectbox, .stDataFrame, .stMetric, .stPlotlyChart, .stTabs { position: relative !important; z-index: 1 !important; }
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
    .reversal-alert { border: 1px solid #ff4444 !important; background: rgba(255,68,68,0.04) !important; padding: 10px 15px !important; margin: 5px 0 !important; border-radius: 8px !important; font-size: 0.85rem !important; }
    .pattern-badge { display: inline-block; background: rgba(255,215,0,0.08) !important; border: 1px solid rgba(255,215,0,0.12) !important; border-radius: 16px !important; padding: 3px 12px !important; margin: 2px !important; font-size: 0.7rem !important; color: #ffd700 !important; }
    .tbs-badge { display: inline-block; background: rgba(255,136,0,0.10) !important; border: 1px solid rgba(255,136,0,0.15) !important; border-radius: 16px !important; padding: 3px 12px !important; margin: 2px !important; font-size: 0.7rem !important; color: #ff8800 !important; font-weight: bold; }
    .currency-card { background: rgba(10,10,10,0.6); border: 1px solid rgba(255,215,0,0.08); border-radius: 8px; padding: 8px 12px; margin: 3px 0; text-align: center; }
    .currency-card .currency { font-weight: bold; font-size: 1.1rem; }
    .currency-card .strength { font-size: 0.9rem; }
    .currency-card .strong { color: #00ff88; }
    .currency-card .weak { color: #ff4444; }
    .currency-card .neutral { color: #ffaa00; }
    .event-high { border-left: 4px solid #ff4444 !important; }
    .event-medium { border-left: 4px solid #ffaa00 !important; }
    .event-low { border-left: 4px solid #00ff88 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر المصغر
# ==========================================
st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">
            <span class="pyramid-icon">▲</span>
            BLACK PYRAMID
            <span class="pyramid-icon">▲</span>
        </div>
        <div class="main-subtitle">Advanced Trading Intelligence • SMC/ICT • Liquidity • SMR • Patterns • TBS • MTF • Divergence • Candlestick • Killzones • Currency Strength • Economic Calendar • News Analysis</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# API Keys
# ==========================================
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"
FMP_API_KEY = "EBdaCkJXtIphxCdiZpW3EWCAb4IKpz8N"

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
    "ETH/USD (Ethereum)": "ETH-USD"
}

# ==========================================
# مؤشرات العملات الرئيسية
# ==========================================

CURRENCY_INDICES = {
    "USD": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X", "NZDUSD=X"],
    "EUR": ["EURUSD=X", "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X", "EURCAD=X", "EURNZD=X"],
    "GBP": ["GBPUSD=X", "EURGBP=X", "GBPJPY=X", "GBPCHF=X", "GBPAUD=X", "GBPCAD=X", "GBPNZD=X"],
    "JPY": ["USDJPY=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", "NZDJPY=X", "CADJPY=X"],
    "CHF": ["USDCHF=X", "EURCHF=X", "GBPCHF=X", "AUDCHF=X", "NZDCHF=X", "CADCHF=X"],
    "AUD": ["AUDUSD=X", "EURAUD=X", "GBPAUD=X", "AUDJPY=X", "AUDNZD=X", "AUDCAD=X"],
    "NZD": ["NZDUSD=X", "EURNZD=X", "GBPNZD=X", "AUDNZD=X", "NZDJPY=X", "NZDCAD=X"],
    "CAD": ["USDCAD=X", "EURCAD=X", "GBPCAD=X", "AUDCAD=X", "NZDCAD=X", "CADJPY=X", "CADCHF=X"]
}

# ==========================================
# إعدادات المؤشرات الديناميكية لكل نوع أصل
# ==========================================

def get_indicator_settings(symbol_name):
    """
    إرجاع إعدادات المؤشرات المناسبة حسب نوع الأصل
    """
    # تحديد نوع الأصل
    if "Gold" in symbol_name or "XAU" in symbol_name or "Silver" in symbol_name or "XAG" in symbol_name:
        asset_type = "gold"
    elif "BTC" in symbol_name or "ETH" in symbol_name or "Bitcoin" in symbol_name or "Ethereum" in symbol_name:
        asset_type = "crypto"
    else:
        asset_type = "forex"
    
    settings = {
        'asset_type': asset_type,
        'macd': {},
        'rsi': {},
        'mfi': {},
        'bb': {},
        'ichimoku': {}
    }
    
    if asset_type == "gold":
        # ===== إعدادات الذهب =====
        settings['macd'] = {
            'fast': 5,
            'slow': 13,
            'signal': 4,
            'description': 'سريع للمضاربة'
        }
        settings['rsi'] = {
            'period': 14,
            'overbought': 80,
            'oversold': 20,
            'description': 'مستويات موسعة للترند القوي'
        }
        settings['mfi'] = {
            'period': 9,
            'overbought': 80,
            'oversold': 20,
            'description': 'فترة قصيرة للسيولة'
        }
        settings['bb'] = {
            'period': 20,
            'std_dev': 2.5,
            'description': 'نطاق موسع للتقلبات الحادة'
        }
        settings['ichimoku'] = {
            'tenkan': 10,
            'kijun': 30,
            'senkou': 60,
            'description': 'معدل لنظام 5 أيام'
        }
        settings['atr_period'] = 14
        settings['adx_period'] = 14
        
    elif asset_type == "crypto":
        # ===== إعدادات البتكوين والعملات الرقمية =====
        settings['macd'] = {
            'fast': 6,
            'slow': 13,
            'signal': 5,
            'description': 'سريع للمضاربة'
        }
        settings['rsi'] = {
            'period': 14,
            'overbought': 80,
            'oversold': 20,
            'description': 'مستويات موسعة للترندات العنيفة'
        }
        settings['mfi'] = {
            'period': 10,
            'overbought': 85,
            'oversold': 15,
            'description': 'مستويات واسعة جداً'
        }
        settings['bb'] = {
            'period': 50,
            'std_dev': 2.3,
            'description': 'فترة طويلة لتخفيف الضوضاء'
        }
        settings['ichimoku'] = {
            'tenkan': 10,
            'kijun': 30,
            'senkou': 60,
            'description': 'معدل لسوق 24/7'
        }
        settings['atr_period'] = 14
        settings['adx_period'] = 14
        
    else:  # forex
        # ===== إعدادات الفوركس =====
        settings['macd'] = {
            'fast': 12,
            'slow': 26,
            'signal': 9,
            'description': 'قياسي'
        }
        settings['rsi'] = {
            'period': 14,
            'overbought': 70,
            'oversold': 30,
            'description': 'قياسي'
        }
        settings['mfi'] = {
            'period': 14,
            'overbought': 80,
            'oversold': 20,
            'description': 'قياسي'
        }
        settings['bb'] = {
            'period': 20,
            'std_dev': 2,
            'description': 'قياسي'
        }
        settings['ichimoku'] = {
            'tenkan': 9,
            'kijun': 26,
            'senkou': 52,
            'description': 'كلاسيكي'
        }
        settings['atr_period'] = 14
        settings['adx_period'] = 14
    
    return settings

# ==========================================
# المؤشرات الأساسية
# ==========================================

def calc_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calc_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

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

def calc_ichimoku(df, tenkan=9, kijun=26, senkou=52):
    high, low, close = df['high'], df['low'], df['close']
    tenkan_line = (high.rolling(window=tenkan).max() + low.rolling(window=tenkan).min()) / 2
    kijun_line = (high.rolling(window=kijun).max() + low.rolling(window=kijun).min()) / 2
    senkou_a = ((tenkan_line + kijun_line) / 2).shift(kijun)
    senkou_b = ((high.rolling(window=senkou).max() + low.rolling(window=senkou).min()) / 2).shift(kijun)
    chikou = close.shift(-kijun)
    return tenkan_line, kijun_line, senkou_a, senkou_b, chikou

def calc_vwap(df):
    return (df['volume'] * df['close']).cumsum() / df['volume'].cumsum()

def calc_mfi(df, period=14):
    """
    حساب مؤشر التدفق النقدي (Money Flow Index)
    """
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    return mfi

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

# ==========================================
# Liquidity & SMR
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

# ==========================================
# SMC/ICT
# ==========================================
@st.cache_data(ttl=300)
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
    
    if len(df) < 50:
        return df
    
    bsl, ssl = detect_liquidity_levels(df, lookback=50)
    df['bsl'] = bsl
    df['ssl'] = ssl
    df = detect_smart_money_reversal(df, lookback=20)
    
    for i in range(3, len(df)):
        try:
            if df['close'].iloc[i] > df['open'].iloc[i]:
                body = df['close'].iloc[i] - df['open'].iloc[i]
                avg_range = (df['high'].iloc[max(0,i-3):i].max() - df['low'].iloc[max(0,i-3):i].min()) / 3
                if body > avg_range and df['close'].iloc[i-1] < df['open'].iloc[i-1]:
                    df.loc[df.index[i-1], 'order_block_bullish'] = True
            if df['close'].iloc[i] < df['open'].iloc[i]:
                body = df['open'].iloc[i] - df['close'].iloc[i]
                avg_range = (df['high'].iloc[max(0,i-3):i].max() - df['low'].iloc[max(0,i-3):i].min()) / 3
                if body > avg_range and df['close'].iloc[i-1] > df['open'].iloc[i-1]:
                    df.loc[df.index[i-1], 'order_block_bearish'] = True
        except:
            continue

    for i in range(2, len(df)):
        try:
            if df['low'].iloc[i] > df['high'].iloc[i-2]:
                df.loc[df.index[i], 'fvg_bullish'] = True
            if df['high'].iloc[i] < df['low'].iloc[i-2]:
                df.loc[df.index[i], 'fvg_bearish'] = True
        except:
            continue

    for i in range(10, len(df)):
        try:
            recent_lows = df['low'].iloc[max(0,i-10):i].tolist()
            if df['low'].iloc[i] < min(recent_lows[:-1]):
                df.loc[df.index[i], 'liquidity_sweep_bullish'] = True
            recent_highs = df['high'].iloc[max(0,i-10):i].tolist()
            if df['high'].iloc[i] > max(recent_highs[:-1]):
                df.loc[df.index[i], 'liquidity_sweep_bearish'] = True
        except:
            continue

    for i in range(5, len(df)):
        try:
            if df['close'].iloc[i] > df['high'].iloc[max(0,i-5):i].max():
                df.loc[df.index[i], 'bos_bullish'] = True
            if df['close'].iloc[i] < df['low'].iloc[max(0,i-5):i].min():
                df.loc[df.index[i], 'bos_bearish'] = True
        except:
            continue

    for i in range(3, len(df)):
        try:
            if df['bos_bearish'].iloc[i-1] and df['close'].iloc[i] > df['high'].iloc[max(0,i-2):i].max():
                df.loc[df.index[i], 'mss_bullish'] = True
            if df['bos_bullish'].iloc[i-1] and df['close'].iloc[i] < df['low'].iloc[max(0,i-2):i].min():
                df.loc[df.index[i], 'mss_bearish'] = True
        except:
            continue

    for i in range(50, len(df)):
        try:
            range_high = df['high'].iloc[max(0,i-50):i].max()
            range_low = df['low'].iloc[max(0,i-50):i].min()
            if range_high != range_low:
                discount = range_low + (range_high - range_low) * 0.382
                premium = range_high - (range_high - range_low) * 0.382
                if df['close'].iloc[i] <= discount:
                    df.loc[df.index[i], 'in_discount'] = True
                if df['close'].iloc[i] >= premium:
                    df.loc[df.index[i], 'in_premium'] = True
        except:
            continue

    try:
        tbs_type, _, _, _ = detect_tbs(df) or (None, None, None, None)
        if tbs_type == "BULLISH":
            df.loc[df.index[-1], 'tbs_bullish'] = True
        elif tbs_type == "BEARISH":
            df.loc[df.index[-1], 'tbs_bearish'] = True
    except:
        pass

    return df

# ==========================================
# TBS
# ==========================================
def detect_tbs(df, lookback=20, body_multiplier=1.5):
    if df is None or len(df) < lookback + 2:
        return None, None, None, None
    
    try:
        last_idx = len(df) - 1
        current = df.iloc[last_idx]
        lookback_high = df['high'].iloc[max(0, last_idx - lookback):last_idx].max()
        lookback_low = df['low'].iloc[max(0, last_idx - lookback):last_idx].min()
        avg_body = abs(df['close'] - df['open']).iloc[max(0, last_idx - lookback):last_idx].mean()
        current_body = abs(current['close'] - current['open'])
        
        if current_body < avg_body * body_multiplier:
            return None, None, None, None
            
        if current['high'] > lookback_high and current['close'] > lookback_high:
            return "BEARISH", current['close'], current['low'], lookback_high
        elif current['low'] < lookback_low and current['close'] < lookback_low:
            return "BULLISH", current['close'], current['high'], lookback_low
    except:
        pass
    
    return None, None, None, None

# ==========================================
# أنماط هيكلية
# ==========================================
def find_peaks_troughs(series, order=5):
    peaks, troughs = [], []
    if series is None or len(series) < order * 2 + 1:
        return peaks, troughs
    
    for i in range(order, len(series) - order):
        try:
            if all(series[i] > series[i-j] for j in range(1, order+1)) and all(series[i] > series[i+j] for j in range(1, order+1)):
                peaks.append((i, series[i]))
            if all(series[i] < series[i-j] for j in range(1, order+1)) and all(series[i] < series[i+j] for j in range(1, order+1)):
                troughs.append((i, series[i]))
        except:
            continue
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

def detect_triple_top_bottom(df, lookback=50, tolerance=0.02):
    if len(df) < lookback:
        return None, 0
    highs = df['high'].iloc[-lookback:].values
    lows = df['low'].iloc[-lookback:].values
    peaks, _ = find_peaks_troughs(highs, order=3)
    _, troughs = find_peaks_troughs(lows, order=3)
    if len(peaks) >= 3:
        last_three = sorted(peaks[-3:], key=lambda x: x[0])
        p1, p2, p3 = last_three[-3][1], last_three[-2][1], last_three[-1][1]
        if abs(p1 - p2) / p1 < tolerance and abs(p2 - p3) / p2 < tolerance:
            return "TRIPLE_TOP", 5
    if len(troughs) >= 3:
        last_three = sorted(troughs[-3:], key=lambda x: x[0])
        t1, t2, t3 = last_three[-3][1], last_three[-2][1], last_three[-1][1]
        if abs(t1 - t2) / t1 < tolerance and abs(t2 - t3) / t2 < tolerance:
            return "TRIPLE_BOTTOM", 5
    return None, 0

def detect_wedge(df, lookback=40):
    if len(df) < lookback:
        return None, 0
    recent = df.iloc[-lookback:]
    highs = recent['high'].values
    lows = recent['low'].values
    x = np.arange(len(highs))
    slope_h = np.polyfit(x, highs, 1)[0]
    slope_l = np.polyfit(x, lows, 1)[0]
    if slope_h > 0.002 and slope_l > 0.001 and slope_h > slope_l:
        return "RISING_WEDGE", 3
    if slope_h < -0.002 and slope_l < -0.001 and slope_h < slope_l:
        return "FALLING_WEDGE", 3
    return None, 0

def detect_flag_pennant(df, lookback=30):
    if len(df) < lookback:
        return None, 0
    recent = df.iloc[-lookback:]
    first_half = recent.iloc[:lookback//2]
    second_half = recent.iloc[lookback//2:]
    if first_half['close'].max() - first_half['close'].min() > 2 * (second_half['close'].max() - second_half['close'].min()):
        return "FLAG", 3
    return None, 0

def analyze_chart_patterns(df):
    patterns = []
    total_score = 0

    p, s = detect_head_shoulders(df)
    if p:
        direction = "BEARISH" if "HEAD" in p else "BULLISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s

    p, s = detect_double_top_bottom(df)
    if p:
        direction = "BEARISH" if "TOP" in p else "BULLISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s

    p, s = detect_triangle_pattern(df)
    if p:
        direction = "BULLISH" if "ASCENDING" in p else "BEARISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s

    p, s = detect_triple_top_bottom(df)
    if p:
        direction = "BEARISH" if "TOP" in p else "BULLISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s

    p, s = detect_wedge(df)
    if p:
        direction = "BEARISH" if "RISING" in p else "BULLISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s

    p, s = detect_flag_pennant(df)
    if p:
        last_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-5] if len(df) >= 5 else df['close'].iloc[0]
        direction = "BULLISH" if last_close > prev_close else "BEARISH"
        patterns.append({"pattern": p, "score": s, "direction": direction})
        total_score += s

    return patterns, total_score

# ==========================================
# دوال متقدمة
# ==========================================

def detect_candlestick_patterns(df):
    """كشف أنماط الشموع اليابانية الانعكاسية"""
    patterns = []
    if len(df) < 3:
        return patterns
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    body = abs(last['close'] - last['open'])
    total_range = last['high'] - last['low']
    
    if (prev['close'] < prev['open'] and 
        last['close'] > last['open'] and 
        last['open'] < prev['close'] and 
        last['close'] > prev['open']):
        patterns.append({"pattern": "BULLISH_ENGULFING", "direction": "BULLISH", "score": 3})
    
    if (prev['close'] > prev['open'] and 
        last['close'] < last['open'] and 
        last['open'] > prev['close'] and 
        last['close'] < prev['open']):
        patterns.append({"pattern": "BEARISH_ENGULFING", "direction": "BEARISH", "score": 3})
    
    lower_wick = min(last['close'], last['open']) - last['low']
    upper_wick = last['high'] - max(last['close'], last['open'])
    if body > 0 and lower_wick > body * 2 and upper_wick < body * 0.3:
        patterns.append({"pattern": "HAMMER", "direction": "BULLISH", "score": 2})
    
    if body > 0 and upper_wick > body * 2 and lower_wick < body * 0.3:
        patterns.append({"pattern": "SHOOTING_STAR", "direction": "BEARISH", "score": 2})
    
    if total_range > 0 and body < total_range * 0.15:
        patterns.append({"pattern": "DOJI", "direction": "NEUTRAL", "score": 1})
    
    if (prev2['close'] < prev2['open'] and 
        abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and
        last['close'] > last['open'] and 
        last['close'] > (prev2['open'] + prev2['close']) / 2):
        patterns.append({"pattern": "MORNING_STAR", "direction": "BULLISH", "score": 4})
    
    if (prev2['close'] > prev2['open'] and 
        abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and
        last['close'] < last['open'] and 
        last['close'] < (prev2['open'] + prev2['close']) / 2):
        patterns.append({"pattern": "EVENING_STAR", "direction": "BEARISH", "score": 4})
    
    return patterns

def detect_rsi_divergence(df, rsi_column='rsi', lookback=20):
    """كشف التباعد (Divergence) بين السعر و RSI"""
    if len(df) < lookback or rsi_column not in df.columns:
        return None, 0
    
    recent_highs = df['high'].iloc[-lookback:].values
    recent_lows = df['low'].iloc[-lookback:].values
    recent_rsi = df[rsi_column].iloc[-lookback:].values
    
    if len(recent_lows) > 5:
        min1_idx = np.argmin(recent_lows)
        if min1_idx > 2:
            prev_min_idx = np.argmin(recent_lows[:min1_idx-1])
            if recent_lows[min1_idx] < recent_lows[prev_min_idx] and recent_rsi[min1_idx] > recent_rsi[prev_min_idx]:
                return "BULLISH_DIVERGENCE", 4
            if recent_lows[min1_idx] > recent_lows[prev_min_idx] and recent_rsi[min1_idx] < recent_rsi[prev_min_idx]:
                return "HIDDEN_BULLISH_DIV", 3

    if len(recent_highs) > 5:
        max1_idx = np.argmax(recent_highs)
        if max1_idx > 2:
            prev_max_idx = np.argmax(recent_highs[:max1_idx-1])
            if recent_highs[max1_idx] > recent_highs[prev_max_idx] and recent_rsi[max1_idx] < recent_rsi[prev_max_idx]:
                return "BEARISH_DIVERGENCE", 4
            if recent_highs[max1_idx] < recent_highs[prev_max_idx] and recent_rsi[max1_idx] > recent_rsi[prev_max_idx]:
                return "HIDDEN_BEARISH_DIV", 3
    
    return None, 0

def check_fresh_order_block(df_smc):
    """التحقق من وجود كتلة أوامر طازجة (لم يتم لمسها)"""
    if len(df_smc) < 10:
        return False, None
    
    bull_obs = df_smc[df_smc['order_block_bullish'] == True]
    if not bull_obs.empty:
        last_idx = bull_obs.index[-1]
        if df_smc['close'].iloc[-1] > df_smc['high'].loc[last_idx]:
            return True, "BUY"
    
    bear_obs = df_smc[df_smc['order_block_bearish'] == True]
    if not bear_obs.empty:
        last_idx = bear_obs.index[-1]
        if df_smc['close'].iloc[-1] < df_smc['low'].loc[last_idx]:
            return True, "SELL"
    
    return False, None

def is_ict_killzone():
    """تحديد منطقة القتل الزمنية ICT (لندن/نيويورك)"""
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    hour = now.hour
    minute = now.minute
    current_time = hour + minute/60.0
    
    if 2.0 <= current_time < 5.0:
        return "LONDON", 3
    elif 8.0 <= current_time < 11.0:
        return "NY", 3
    elif 18.0 <= current_time or current_time < 2.0:
        return "ASIA", 1
    return None, 0

def get_major_trend(df):
    """تحديد الاتجاه الرئيسي بناءً على EMA200"""
    if len(df) < 200:
        return "NEUTRAL"
    ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
    price = df['close'].iloc[-1]
    if price > ema200 * 1.01:
        return "BULLISH"
    elif price < ema200 * 0.99:
        return "BEARISH"
    return "NEUTRAL"

def get_dynamic_weights(df, asset_type="forex"):
    """
    تعديل أوزان المؤشرات حسب حالة السوق ونوع الأصل
    """
    adx_val = 20
    if 'adx' in df.columns and not df['adx'].empty:
        try:
            last_adx = df['adx'].iloc[-1]
            if not pd.isna(last_adx):
                adx_val = last_adx
        except:
            pass
    
    # ====== الأوزان الأساسية حسب نوع الأصل ======
    if asset_type == "gold":
        weights = {
            'rsi': 3, 'macd': 4, 'bb': 3, 'vwap': 2, 'adx': 2,
            'ichimoku': 4, 'smc': 5, 'patterns': 5, 'tbs': 5,
            'mfi': 3, 'smr': 4, 'candle': 4, 
            'divergence': 5, 'fresh_ob': 4, 
            'fibonacci': 3, 'macd_hist': 3
        }
    elif asset_type == "crypto":
        weights = {
            'rsi': 2, 'macd': 4, 'bb': 3, 'vwap': 2, 'adx': 2,
            'ichimoku': 5, 'smc': 5, 'patterns': 5, 'tbs': 5,
            'mfi': 3, 'smr': 4, 'candle': 4, 
            'divergence': 5, 'fresh_ob': 4, 
            'fibonacci': 3, 'macd_hist': 3
        }
    else:  # forex
        weights = {
            'rsi': 3, 'macd': 3, 'bb': 3, 'vwap': 2, 'adx': 2,
            'ichimoku': 3, 'smc': 4, 'patterns': 5, 'tbs': 5,
            'mfi': 3, 'smr': 4, 'candle': 4, 
            'divergence': 5, 'fresh_ob': 4, 
            'fibonacci': 3, 'macd_hist': 2
        }
    
    # ====== الأوزان الديناميكية حسب حالة السوق ======
    if adx_val > 25:  # سوق اتجاهي قوي
        weights['ichimoku'] = weights.get('ichimoku', 3) + 1
        weights['macd'] = weights.get('macd', 3) + 1
        weights['rsi'] = max(1, weights.get('rsi', 3) - 1)
        weights['bb'] = max(1, weights.get('bb', 3) - 1)
        weights['adx'] = weights.get('adx', 2) + 1
    else:  # سوق عرضي
        weights['bb'] = weights.get('bb', 3) + 2
        weights['rsi'] = weights.get('rsi', 3) + 2
        weights['ichimoku'] = max(1, weights.get('ichimoku', 3) - 2)
        weights['macd'] = max(1, weights.get('macd', 3) - 1)
        weights['mfi'] = weights.get('mfi', 3) + 1
    
    return weights

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

# ==========================================
# دوال FMP API
# ==========================================

@st.cache_data(ttl=300)
def get_fmp_economic_calendar():
    try:
        url = f"https://financialmodelingprep.com/api/v3/economic_calendar?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            events = []
            for item in data[:20]:
                events.append({
                    'country': item.get('country', ''),
                    'event': item.get('event', ''),
                    'date': item.get('date', ''),
                    'time': item.get('time', ''),
                    'impact': item.get('impact', ''),
                    'actual': item.get('actual', ''),
                    'forecast': item.get('forecast', ''),
                    'previous': item.get('previous', '')
                })
            return events
    except Exception as e:
        pass
    return []

@st.cache_data(ttl=300)
def get_fmp_news():
    try:
        url = f"https://financialmodelingprep.com/api/v3/fmp-news?apikey={FMP_API_KEY}&limit=10"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            news_list = []
            for item in data[:10]:
                news_list.append({
                    'title': item.get('title', ''),
                    'source': 'FMP',
                    'publishedAt': item.get('publishedDate', ''),
                    'url': item.get('url', ''),
                    'content': item.get('text', '')
                })
            return news_list
    except Exception as e:
        pass
    return []

# ==========================================
# تحليل الأخبار المتقدم
# ==========================================

NEWS_KEYWORDS = {
    'positive': {
        'gold': ['gold rally', 'gold surge', 'gold bullish', 'gold gains', 'gold positive', 'gold up', 'gold rises', 'gold strong', 'gold support', 'gold buying', 'gold rebound'],
        'forex': ['dollar weak', 'dollar down', 'dollar falls', 'euro strong', 'pound strong', 'currency rally', 'forex positive', 'dollar negative', 'yen weak'],
        'economy': ['fed cut', 'rate cut', 'stimulus', 'economic growth', 'gdp up', 'jobs strong', 'inflation down', 'recovery', 'boom']
    },
    'negative': {
        'gold': ['gold drop', 'gold falls', 'gold bearish', 'gold decline', 'gold down', 'gold selling', 'gold crash', 'gold weak', 'gold resistance', 'gold plunge'],
        'forex': ['dollar strong', 'dollar up', 'dollar rises', 'euro weak', 'pound weak', 'currency drop', 'forex negative', 'dollar positive', 'yen strong'],
        'economy': ['fed hike', 'rate hike', 'inflation up', 'economic slowdown', 'gdp down', 'jobs weak', 'recession', 'crisis', 'crash']
    }
}

def analyze_news_impact(news_list):
    if not news_list:
        return {
            'gold_sentiment': 0,
            'forex_sentiment': 0,
            'overall_sentiment': 0,
            'high_impact_news': [],
            'news_analysis': [],
            'summary': "لا توجد أخبار للتحليل",
            'count': 0
        }
    
    gold_score = 0
    forex_score = 0
    high_impact = []
    news_analysis = []
    
    for item in news_list:
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        combined_text = title + " " + content
        source = item.get('source', '')
        impact = 0
        category = 'neutral'
        
        gold_positive = any(kw in combined_text for kw in NEWS_KEYWORDS['positive']['gold'])
        gold_negative = any(kw in combined_text for kw in NEWS_KEYWORDS['negative']['gold'])
        
        if gold_positive:
            gold_score += 2
            impact += 2
            category = 'positive_gold'
        elif gold_negative:
            gold_score -= 2
            impact -= 2
            category = 'negative_gold'
        
        forex_positive = any(kw in combined_text for kw in NEWS_KEYWORDS['positive']['forex'])
        forex_negative = any(kw in combined_text for kw in NEWS_KEYWORDS['negative']['forex'])
        
        if forex_positive:
            forex_score += 2
            impact += 1
            if category == 'neutral':
                category = 'positive_forex'
        elif forex_negative:
            forex_score -= 2
            impact -= 1
            if category == 'neutral':
                category = 'negative_forex'
        
        eco_positive = any(kw in combined_text for kw in NEWS_KEYWORDS['positive']['economy'])
        eco_negative = any(kw in combined_text for kw in NEWS_KEYWORDS['negative']['economy'])
        
        if eco_positive:
            gold_score += 1
            forex_score += 1
            impact += 1
        elif eco_negative:
            gold_score -= 1
            forex_score -= 1
            impact -= 1
        
        impact_level = "منخفض"
        if abs(impact) >= 3:
            impact_level = "عالٍ"
            high_impact.append({
                'title': item.get('title', ''),
                'source': source,
                'impact': impact,
                'category': category
            })
        elif abs(impact) >= 1:
            impact_level = "متوسط"
        
        news_analysis.append({
            'title': item.get('title', ''),
            'source': source,
            'category': category,
            'impact': impact,
            'impact_level': impact_level,
            'date': item.get('publishedAt', '')
        })
    
    gold_sentiment = min(100, max(-100, gold_score * 10))
    forex_sentiment = min(100, max(-100, forex_score * 10))
    overall_sentiment = (gold_sentiment + forex_sentiment) / 2
    
    if overall_sentiment > 30:
        summary = "📈 الأخبار إيجابية بشكل عام، تدعم الشراء"
    elif overall_sentiment < -30:
        summary = "📉 الأخبار سلبية بشكل عام، تدعم البيع"
    elif high_impact:
        summary = f"⚠️ أخبار عالية التأثير: {len(high_impact)} خبر"
    else:
        summary = "➡️ الأخبار محايدة، لا تأثير كبير"
    
    return {
        'gold_sentiment': gold_sentiment,
        'forex_sentiment': forex_sentiment,
        'overall_sentiment': overall_sentiment,
        'high_impact_news': high_impact,
        'news_analysis': news_analysis,
        'summary': summary,
        'count': len(news_list)
    }

def get_news_impact_score(news_analysis, symbol=""):
    if not news_analysis or news_analysis.get('count', 0) == 0:
        return 0, "لا توجد أخبار"
    
    impact_score = 0
    impact_details = []
    
    if "Gold" in symbol or "XAU" in symbol:
        impact_score = news_analysis.get('gold_sentiment', 0)
        impact_details.append(f"الذهب: {impact_score:+.0f}")
    elif any(x in symbol for x in ["EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD"]):
        impact_score = news_analysis.get('forex_sentiment', 0)
        impact_details.append(f"الفوركس: {impact_score:+.0f}")
    else:
        impact_score = news_analysis.get('overall_sentiment', 0)
        impact_details.append(f"عام: {impact_score:+.0f}")
    
    high_impact = news_analysis.get('high_impact_news', [])
    if high_impact:
        impact_score -= len(high_impact) * 5
        impact_details.append(f"أخبار عالية التأثير: -{len(high_impact) * 5}")
    
    return impact_score, " | ".join(impact_details)

def display_news_analysis(news_analysis):
    if not news_analysis or news_analysis.get('count', 0) == 0:
        st.info("لا توجد أخبار للتحليل")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gold_sent = news_analysis.get('gold_sentiment', 0)
        color = "🟢" if gold_sent > 0 else ("🔴" if gold_sent < 0 else "🟡")
        st.metric(f"{color} الذهب", f"{gold_sent:+.0f}")
    
    with col2:
        forex_sent = news_analysis.get('forex_sentiment', 0)
        color = "🟢" if forex_sent > 0 else ("🔴" if forex_sent < 0 else "🟡")
        st.metric(f"{color} الفوركس", f"{forex_sent:+.0f}")
    
    with col3:
        overall = news_analysis.get('overall_sentiment', 0)
        color = "🟢" if overall > 0 else ("🔴" if overall < 0 else "🟡")
        st.metric(f"{color} الإجمالي", f"{overall:+.0f}")
    
    st.info(news_analysis.get('summary', ''))
    
    if news_analysis.get('news_analysis'):
        st.markdown("#### 📰 تحليل الأخبار:")
        for item in news_analysis['news_analysis'][:5]:
            impact = item.get('impact', 0)
            impact_level = item.get('impact_level', '')
            if impact_level == "عالٍ":
                icon = "🔴"
            elif impact_level == "متوسط":
                icon = "🟡"
            else:
                icon = "🟢"
            
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">
                    {icon} {item.get('title', '')[:100]}...
                </div>
                <div class="news-date">
                    {item.get('source', '')} | التأثير: {impact_level} ({impact:+.0f}) | {item.get('date', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

def display_economic_events(events):
    if not events:
        st.info("لا توجد أحداث اقتصادية")
        return
    
    for event in events[:15]:
        impact = event.get('impact', '')
        if impact == 'High' or impact == 'عالٍ':
            impact_icon = "🔴"
            impact_class = "event-high"
        elif impact == 'Medium' or impact == 'متوسط':
            impact_icon = "🟡"
            impact_class = "event-medium"
        else:
            impact_icon = "🟢"
            impact_class = "event-low"
        
        st.markdown(f"""
        <div class="news-card {impact_class}">
            <div class="news-title">
                {impact_icon} <b>{event.get('country', '')}</b> - {event.get('event', '')}
            </div>
            <div class="news-date">
                🕐 {event.get('date', '')} {event.get('time', '')} | 
                التوقع: {event.get('forecast', 'N/A')} | 
                السابق: {event.get('previous', 'N/A')} | 
                الفعلي: {event.get('actual', 'N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# دوال جلب البيانات الأساسية
# ==========================================

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
        except Exception as e:
            pass
    
    if symbol == "SI=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAG/USD"
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
        if not data.empty and len(data) > 1:
            last = data.iloc[-1]
            first = data.iloc[0]
            change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
            return float(last['Close']), float(change)
        else:
            data = ticker.history(period="5d", interval="1h")
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
                if not df.empty and len(df) > 10:
                    df.columns = [col.lower() for col in df.columns]
                    return df
            except Exception as e:
                continue
        if attempt < max_retries - 1:
            time.sleep(3)
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo", interval="1d")
        if not df.empty and len(df) > 10:
            df.columns = [col.lower() for col in df.columns]
            return df
    except:
        pass
    
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

@st.cache_data(ttl=60)
def get_currency_strength():
    strength = {}
    for currency, pairs in CURRENCY_INDICES.items():
        changes = []
        for pair in pairs:
            try:
                ticker = yf.Ticker(pair)
                data = ticker.history(period="1d", interval="5m")
                if not data.empty and len(data) > 1:
                    last = data.iloc[-1]
                    first = data.iloc[0]
                    change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
                    if pair.split('=')[0].startswith(currency):
                        changes.append(change)
                    else:
                        changes.append(-change)
            except Exception as e:
                continue
        if changes:
            strength[currency] = round(sum(changes) / len(changes), 2)
        else:
            strength[currency] = 0.0
    return strength

@st.cache_data(ttl=120)
def get_correlation_matrix(pairs):
    correlation_data = {}
    for pair in pairs:
        try:
            df = get_historical_data(pair, period="5d", interval="1h")
            if df is not None and not df.empty:
                correlation_data[pair] = df['close']
        except:
            continue
    
    if correlation_data:
        df_corr = pd.DataFrame(correlation_data)
        return df_corr.corr()
    return pd.DataFrame()

@st.cache_data(ttl=120)
def get_pair_correlation(symbol1, symbol2):
    try:
        df1 = get_historical_data(symbol1, period="5d", interval="1h")
        df2 = get_historical_data(symbol2, period="5d", interval="1h")
        if df1 is not None and df2 is not None and not df1.empty and not df2.empty:
            df1_aligned = df1['close'].reindex(df2.index, method='nearest')
            return round(df1_aligned.corr(df2['close']), 3)
    except:
        pass
    return None

# ==========================================
# نظام القرار الهرمي الجديد (Black Pyramid Hierarchy)
# ==========================================

def get_asset_type_from_symbol(symbol_name):
    """تحديد نوع الأصل لتصفية الأخبار"""
    if "Gold" in symbol_name or "XAU" in symbol_name:
        return "gold"
    elif "Silver" in symbol_name or "XAG" in symbol_name:
        return "silver"
    elif "BTC" in symbol_name or "Bitcoin" in symbol_name:
        return "bitcoin"
    elif "ETH" in symbol_name or "Ethereum" in symbol_name:
        return "ethereum"
    elif any(x in symbol_name for x in ["EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD"]):
        return "forex"
    else:
        return "crypto"

def get_asset_specific_news(news_list, asset_type):
    """
    تصفية الأخبار حسب نوع الأصل
    """
    if not news_list:
        return []
    
    filtered_news = []
    
    # كلمات مفتاحية خاصة بكل أصل
    asset_keywords = {
        "gold": ["gold", "federal reserve", "fed", "interest rate", "cpi", "nfp", "inflation", "dollar", "treasury", "geopolitical", "xau"],
        "silver": ["silver", "xag", "federal reserve", "fed", "interest rate", "inflation", "dollar"],
        "bitcoin": ["bitcoin", "btc", "etf", "regulation", "sec", "crypto", "fed", "institutional", "exchange"],
        "ethereum": ["ethereum", "eth", "etf", "regulation", "sec", "crypto", "fed"],
        "forex": ["ecb", "eurozone", "cpi", "nfp", "pce", "fed", "employment", "dollar", "euro", "pound", "yen", "swiss", "aud", "nzd", "cad"],
        "crypto": ["bitcoin", "ethereum", "crypto", "etf", "regulation", "sec", "exchange", "fed"]
    }
    
    keywords = asset_keywords.get(asset_type, [])
    
    for item in news_list:
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        combined = title + " " + content
        
        # التحقق من وجود كلمة مفتاحية
        if any(kw in combined for kw in keywords):
            filtered_news.append(item)
        # إذا كان الخبر عاماً لكنه عالي التأثير، نضيفه
        elif any(kw in combined for kw in ["fed", "federal reserve", "rate", "cpi", "nfp"]):
            filtered_news.append(item)
    
    return filtered_news

def analyze_asset_news(news_list, asset_type):
    """
    تحليل الأخبار الخاصة بالأصل
    """
    if not news_list:
        return {
            'impact_score': 0,
            'high_impact': False,
            'summary': "لا توجد أخبار خاصة بالأصل"
        }
    
    # كلمات مفتاحية عالية التأثير
    high_impact_keywords = {
        "gold": ["fed", "federal reserve", "rate decision", "interest rate", "cpi", "nfp", "geopolitical"],
        "forex": ["rate decision", "ecb", "fed", "cpi", "employment", "nfp"],
        "bitcoin": ["sec", "etf", "regulation", "fed", "rate"],
        "ethereum": ["sec", "etf", "regulation", "fed"],
        "crypto": ["sec", "regulation", "fed"]
    }
    
    high_keywords = high_impact_keywords.get(asset_type, ["fed", "rate", "cpi"])
    
    impact_score = 0
    high_impact = False
    
    for item in news_list:
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        combined = title + " " + content
        
        # تحليل التأثير
        if any(kw in combined for kw in high_keywords):
            impact_score += 3
            high_impact = True
        elif any(kw in combined for kw in ["forecast", "expect", "inflation", "growth", "employment"]):
            impact_score += 1
    
    # تحديد مستوى الخطر
    risk_level = "منخفض"
    if impact_score >= 5:
        risk_level = "عالٍ"
    elif impact_score >= 3:
        risk_level = "متوسط"
    
    return {
        'impact_score': impact_score,
        'high_impact': high_impact,
        'risk_level': risk_level,
        'summary': f"تأثير الأخبار: {risk_level} (نقاط: {impact_score})"
    }

def analyze_market_regime(df_4h, df_1h, df_15m, symbol_name=""):
    """
    تحليل حالة السوق (الطبقة الأولى)
    """
    if df_4h is None or len(df_4h) < 50:
        return {
            'regime': 'UNKNOWN',
            'trend': 'NEUTRAL',
            'volatility': 'LOW',
            'compression': False,
            'summary': 'بيانات غير كافية'
        }
    
    # حساب المؤشرات
    adx_4h = calc_adx(df_4h)[0].iloc[-1]
    rsi_4h = calc_rsi(df_4h['close']).iloc[-1]
    bb_4h = calc_bollinger_bands(df_4h['close'])
    bb_width = (bb_4h[0].iloc[-1] - bb_4h[2].iloc[-1]) / bb_4h[1].iloc[-1]
    atr_4h = calc_atr(df_4h).iloc[-1]
    atr_avg = calc_atr(df_4h).iloc[-50:].mean()
    
    # تحديد الاتجاه
    ema50 = df_4h['close'].ewm(span=50).mean().iloc[-1]
    ema200 = df_4h['close'].ewm(span=200).mean().iloc[-1]
    price = df_4h['close'].iloc[-1]
    
    if price > ema50 and price > ema200 and rsi_4h > 50:
        trend = "BULLISH"
    elif price < ema50 and price < ema200 and rsi_4h < 50:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    
    # تحديد حالة التقلب
    volatility = "MEDIUM"
    if atr_4h > atr_avg * 1.5:
        volatility = "HIGH"
    elif atr_4h < atr_avg * 0.7:
        volatility = "LOW"
    
    # تحديد الانكماش
    compression = False
    if bb_width < 0.05:  # نطاق ضيق
        compression = True
    
    # تحديد نوع السوق
    if adx_4h > 25 and trend != "NEUTRAL":
        regime = "TRENDING"
    elif adx_4h < 25:
        regime = "RANGING"
    else:
        regime = "MIXED"
    
    return {
        'regime': regime,
        'trend': trend,
        'volatility': volatility,
        'compression': compression,
        'adx': adx_4h,
        'rsi': rsi_4h,
        'summary': f"السوق {regime}، اتجاه {trend}، تقلب {volatility}"
    }

def analyze_trend_4h(df_4h, symbol_name=""):
    """
    تحليل الطبقة الثانية: الاتجاه الرئيسي 4H
    """
    if df_4h is None or len(df_4h) < 50:
        return {
            'bias': 'NEUTRAL',
            'strength': 0,
            'summary': 'بيانات غير كافية'
        }
    
    # المؤشرات الأساسية
    ema50 = df_4h['close'].ewm(span=50).mean().iloc[-1]
    ema200 = df_4h['close'].ewm(span=200).mean().iloc[-1]
    price = df_4h['close'].iloc[-1]
    rsi = calc_rsi(df_4h['close']).iloc[-1]
    
    # تحديد الاتجاه
    if price > ema50 and price > ema200 and rsi > 50:
        bias = "BULLISH"
        strength = min(100, 50 + (rsi - 50) * 2)
    elif price < ema50 and price < ema200 and rsi < 50:
        bias = "BEARISH"
        strength = min(100, 50 + (50 - rsi) * 2)
    else:
        bias = "NEUTRAL"
        strength = 50
    
    return {
        'bias': bias,
        'strength': strength,
        'price': price,
        'ema50': ema50,
        'ema200': ema200,
        'rsi': rsi,
        'summary': f"4H: {bias} (القوة: {strength:.0f}%)"
    }

def analyze_confirmation_1h(df_1h, symbol_name=""):
    """
    تحليل الطبقة الثالثة: تأكيد 1H
    """
    if df_1h is None or len(df_1h) < 50:
        return {
            'confirmed': False,
            'bias': 'NEUTRAL',
            'score': 0,
            'summary': 'بيانات غير كافية'
        }
    
    score = 0
    details = []
    
    # EMA
    ema50 = df_1h['close'].ewm(span=50).mean().iloc[-1]
    ema200 = df_1h['close'].ewm(span=200).mean().iloc[-1]
    price = df_1h['close'].iloc[-1]
    
    if price > ema50 and price > ema200:
        score += 2
        details.append("EMA: صاعد")
    elif price < ema50 and price < ema200:
        score -= 2
        details.append("EMA: هابط")
    else:
        details.append("EMA: محايد")
    
    # MACD
    macd, signal, hist = calc_macd(df_1h['close'])
    if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-1] > 0:
        score += 2
        details.append("MACD: إيجابي")
    elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-1] < 0:
        score -= 2
        details.append("MACD: سلبي")
    else:
        details.append("MACD: محايد")
    
    # ADX + DI
    adx, plus_di, minus_di = calc_adx(df_1h)
    adx_val = adx.iloc[-1]
    plus = plus_di.iloc[-1]
    minus = minus_di.iloc[-1]
    
    if adx_val > 25:
        if plus > minus:
            score += 2
            details.append(f"ADX: قوي صاعد ({adx_val:.0f})")
        else:
            score -= 2
            details.append(f"ADX: قوي هابط ({adx_val:.0f})")
    else:
        details.append(f"ADX: ضعيف ({adx_val:.0f})")
    
    # SMC Analysis
    df_smc = analyze_smc_ict(df_1h)
    if df_smc['bos_bullish'].iloc[-1] or df_smc['mss_bullish'].iloc[-1]:
        score += 1
        details.append("SMC: BOS/MSS صاعد")
    elif df_smc['bos_bearish'].iloc[-1] or df_smc['mss_bearish'].iloc[-1]:
        score -= 1
        details.append("SMC: BOS/MSS هابط")
    
    # تحديد النتيجة
    if score >= 4:
        bias = "BULLISH"
        confirmed = True
    elif score <= -4:
        bias = "BEARISH"
        confirmed = True
    else:
        bias = "NEUTRAL"
        confirmed = False
    
    return {
        'confirmed': confirmed,
        'bias': bias,
        'score': score,
        'details': details,
        'summary': f"1H: {bias} (نقاط: {score})"
    }

def analyze_trigger_15m(df_15m, symbol_name=""):
    """
    تحليل الطبقة الرابعة: توقيت الدخول 15M
    """
    if df_15m is None or len(df_15m) < 30:
        return {
            'trigger': 'NEUTRAL',
            'has_trigger': False,
            'details': [],
            'summary': 'بيانات غير كافية'
        }
    
    trigger_details = []
    trigger_score = 0
    
    # SMC Analysis
    df_smc = analyze_smc_ict(df_15m)
    last_smc = df_smc.iloc[-1]
    
    # Liquidity Sweep
    if last_smc.get('liquidity_sweep_bullish', False):
        trigger_score += 2
        trigger_details.append("Liquidity Sweep صاعد")
    elif last_smc.get('liquidity_sweep_bearish', False):
        trigger_score -= 2
        trigger_details.append("Liquidity Sweep هابط")
    
    # BOS
    if last_smc.get('bos_bullish', False):
        trigger_score += 2
        trigger_details.append("BOS صاعد")
    elif last_smc.get('bos_bearish', False):
        trigger_score -= 2
        trigger_details.append("BOS هابط")
    
    # MSS
    if last_smc.get('mss_bullish', False):
        trigger_score += 2
        trigger_details.append("MSS صاعد")
    elif last_smc.get('mss_bearish', False):
        trigger_score -= 2
        trigger_details.append("MSS هابط")
    
    # FVG
    if last_smc.get('fvg_bullish', False):
        trigger_score += 1
        trigger_details.append("FVG صاعد")
    elif last_smc.get('fvg_bearish', False):
        trigger_score -= 1
        trigger_details.append("FVG هابط")
    
    # Order Block
    if last_smc.get('order_block_bullish', False):
        trigger_score += 1
        trigger_details.append("Order Block شراء")
    elif last_smc.get('order_block_bearish', False):
        trigger_score -= 1
        trigger_details.append("Order Block بيع")
    
    # Candlestick Confirmation
    candle_patterns = detect_candlestick_patterns(df_15m)
    if candle_patterns:
        for cp in candle_patterns:
            if cp['direction'] == 'BULLISH' and cp['score'] >= 3:
                trigger_score += 1
                trigger_details.append(f"شمعة: {cp['pattern']}")
            elif cp['direction'] == 'BEARISH' and cp['score'] >= 3:
                trigger_score -= 1
                trigger_details.append(f"شمعة: {cp['pattern']}")
    
    # تحديد الـ Trigger
    if trigger_score >= 3:
        trigger = "BULLISH"
        has_trigger = True
    elif trigger_score <= -3:
        trigger = "BEARISH"
        has_trigger = True
    else:
        trigger = "NEUTRAL"
        has_trigger = False
    
    return {
        'trigger': trigger,
        'has_trigger': has_trigger,
        'score': trigger_score,
        'details': trigger_details,
        'summary': f"15M: {trigger} (نقاط: {trigger_score})"
    }

def analyze_price_location(df, current_price, symbol_name=""):
    """
    تحليل الطبقة الخامسة: موقع السعر
    """
    if df is None or len(df) < 100:
        return {
            'location': 'NEUTRAL',
            'score': 0,
            'details': [],
            'summary': 'بيانات غير كافية'
        }
    
    score = 0
    details = []
    
    # تحديد أعلى وأدنى سعر (Swing High/Low)
    recent_high = df['high'].iloc[-50:].max()
    recent_low = df['low'].iloc[-50:].min()
    price_range = recent_high - recent_low
    
    # تحديد منطقة السعر
    if price_range > 0:
        price_percent = (current_price - recent_low) / price_range
        
        # Premium / Discount
        if price_percent >= 0.618:
            score -= 1
            details.append("منطقة Premium (ذروة)")
            location = "PREMIUM"
        elif price_percent <= 0.382:
            score += 1
            details.append("منطقة Discount (قاع)")
            location = "DISCOUNT"
        else:
            location = "MIDDLE"
            details.append("منتصف النطاق")
        
        # Fibonacci
        fib_levels = calc_fibonacci_levels(recent_high, recent_low, current_price)
        if fib_levels:
            if current_price <= fib_levels.get('fib_382', current_price):
                score += 1
                details.append("فيبوناتشي: تحت 0.382 (دعم)")
            elif current_price >= fib_levels.get('fib_618', current_price):
                score -= 1
                details.append("فيبوناتشي: فوق 0.618 (مقاومة)")
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = calc_bollinger_bands(df['close'])
    if not pd.isna(bb_upper.iloc[-1]) and not pd.isna(bb_lower.iloc[-1]):
        if current_price <= bb_lower.iloc[-1]:
            score += 1
            details.append("Bollinger: قرب الحد السفلي")
        elif current_price >= bb_upper.iloc[-1]:
            score -= 1
            details.append("Bollinger: قرب الحد الأعلى")
    
    # Support/Resistance
    if current_price <= recent_low * 1.01:
        score += 1
        details.append("قرب مستوى دعم")
    elif current_price >= recent_high * 0.99:
        score -= 1
        details.append("قرب مستوى مقاومة")
    
    return {
        'location': location if 'location' in locals() else 'NEUTRAL',
        'score': score,
        'details': details,
        'summary': f"موقع السعر: {location if 'location' in locals() else 'NEUTRAL'} (نقاط: {score})"
    }

def calculate_risk_management(entry_price, stop_loss, account_balance=100000, risk_percent=1.5, asset_type="forex"):
    """
    حساب إدارة المخاطر
    """
    if stop_loss is None or entry_price is None:
        return None
    
    risk_amount = abs(entry_price - stop_loss)
    risk_per_trade = account_balance * (risk_percent / 100)
    
    # حساب حجم الصفقة حسب نوع الأصل
    if asset_type == "forex":
        # الفوركس - النقطة تساوي 0.0001
        pip_value = 0.0001
        pip_distance = risk_amount / pip_value if pip_value > 0 else 0
        contract_size = risk_per_trade / (pip_distance * 10) if pip_distance > 0 else 0.01
        lot_size = round(contract_size, 2)
    elif asset_type in ["gold", "silver"]:
        # الذهب - النقطة تساوي 0.1
        pip_value = 0.1
        pip_distance = risk_amount / pip_value if pip_value > 0 else 0
        contract_size = risk_per_trade / (pip_distance * 10) if pip_distance > 0 else 0.01
        lot_size = round(contract_size, 2)
    else:
        # الكريبتو
        lot_size = risk_per_trade / risk_amount if risk_amount > 0 else 0.01
        lot_size = round(lot_size, 4)
    
    # تحديد الحد الأدنى
    min_lot = 0.01 if asset_type in ["forex", "gold", "silver"] else 0.0001
    lot_size = max(lot_size, min_lot)
    
    # حساب الأهداف
    risk = abs(entry_price - stop_loss)
    targets = {
        'tp1': entry_price + (risk * 1.5) if entry_price > stop_loss else entry_price - (risk * 1.5),
        'tp2': entry_price + (risk * 2.5) if entry_price > stop_loss else entry_price - (risk * 2.5),
        'tp3': entry_price + (risk * 4.0) if entry_price > stop_loss else entry_price - (risk * 4.0)
    }
    
    return {
        'lot_size': lot_size,
        'risk_per_trade': risk_per_trade,
        'risk_amount': risk_amount,
        'risk_percent': risk_percent,
        'targets': targets,
        'r_multiple': 1.5,
        'summary': f"اللوت: {lot_size}, المخاطرة: ${risk_per_trade:.2f} ({risk_percent}%)"
    }

# ==========================================
# نظام القرار النهائي (Hierarchical Decision System)
# ==========================================

def generate_hierarchical_signal(df_4h, df_1h, df_15m, current_price, symbol_name="", symbol=""):
    """
    توليد الإشارة بناءً على النظام الهرمي
    """
    # ===== التحقق من البيانات =====
    if df_4h is None or df_1h is None or df_15m is None:
        return "WAIT", 0, {"reason": "بيانات غير كافية"}, None, None, None, None
    
    if len(df_4h) < 50 or len(df_1h) < 50 or len(df_15m) < 30:
        return "WAIT", 0, {"reason": "بيانات غير كافية"}, None, None, None, None
    
    # ===== الطبقة الأولى: حالة السوق =====
    regime = analyze_market_regime(df_4h, df_1h, df_15m, symbol_name)
    
    # إذا كان السوق مضغوطاً، انتظار
    if regime['compression']:
        return "WAIT", 0, {"reason": f"انكماش سعري - {regime['summary']}"}, None, None, None, None
    
    # ===== الطبقة الثانية: اتجاه 4H =====
    trend_4h = analyze_trend_4h(df_4h, symbol_name)
    
    if trend_4h['bias'] == 'NEUTRAL':
        return "WAIT", 0, {"reason": f"اتجاه 4H محايد - {trend_4h['summary']}"}, None, None, None, None
    
    # ===== الطبقة الثالثة: تأكيد 1H =====
    confirm_1h = analyze_confirmation_1h(df_1h, symbol_name)
    
    if not confirm_1h['confirmed']:
        return "WAIT", 0, {"reason": f"1H غير مؤكد - {confirm_1h['summary']}"}, None, None, None, None
    
    if confirm_1h['bias'] != trend_4h['bias']:
        return "WAIT", 0, {"reason": f"تعارض 4H و1H - 4H:{trend_4h['bias']} vs 1H:{confirm_1h['bias']}"}, None, None, None, None
    
    # ===== الطبقة الرابعة: Trigger 15M =====
    trigger_15m = analyze_trigger_15m(df_15m, symbol_name)
    
    if not trigger_15m['has_trigger']:
        return "WAIT", 0, {"reason": f"لا يوجد Trigger على 15M - {trigger_15m['summary']}"}, None, None, None, None
    
    if trigger_15m['trigger'] != trend_4h['bias']:
        return "WAIT", 0, {"reason": f"تعارض 4H و15M - 4H:{trend_4h['bias']} vs 15M:{trigger_15m['trigger']}"}, None, None, None, None
    
    # ===== الطبقة الخامسة: موقع السعر =====
    price_location = analyze_price_location(df_1h, current_price, symbol_name)
    
    # التحقق من موقع السعر
    if price_location['location'] == 'PREMIUM' and trend_4h['bias'] == 'BUY':
        return "WAIT", 0, {"reason": f"السعر في Premium مع اتجاه شراء - {price_location['summary']}"}, None, None, None, None
    elif price_location['location'] == 'DISCOUNT' and trend_4h['bias'] == 'SELL':
        return "WAIT", 0, {"reason": f"السعر في Discount مع اتجاه بيع - {price_location['summary']}"}, None, None, None, None
    
    # ===== الطبقة السادسة: الأخبار =====
    asset_type = get_asset_type_from_symbol(symbol_name)
    news = get_fmp_news()
    if news:
        asset_news = get_asset_specific_news(news, asset_type)
        news_analysis = analyze_asset_news(asset_news, asset_type)
        
        if news_analysis['risk_level'] == 'عالٍ':
            return "WAIT", 0, {"reason": f"أخبار عالية التأثير - {news_analysis['summary']}"}, None, None, None, None
    
    # ===== حساب نقاط الثقة =====
    confidence_score = 0
    confidence_details = []
    
    # قوة الاتجاه 4H
    confidence_score += trend_4h['strength'] * 0.3
    confidence_details.append(f"4H: {trend_4h['strength']:.0f}%")
    
    # تأكيد 1H
    confidence_score += min(100, abs(confirm_1h['score']) * 10) * 0.3
    confidence_details.append(f"1H: {confirm_1h['score']:+d}")
    
    # Trigger 15M
    confidence_score += min(100, abs(trigger_15m['score']) * 15) * 0.3
    confidence_details.append(f"15M: {trigger_15m['score']:+d}")
    
    # موقع السعر
    confidence_score += max(0, price_location['score']) * 5
    confidence_details.append(f"Price: {price_location['score']:+d}")
    
    # الحد الأقصى 100
    confidence = min(100, confidence_score)
    
    # ===== تحديد الإشارة النهائية =====
    signal = trend_4h['bias']
    
    # ===== حساب وقف الخسارة =====
    # بناءً على هيكل 1H
    recent_low = df_1h['low'].iloc[-20:].min() if signal == 'BUY' else None
    recent_high = df_1h['high'].iloc[-20:].max() if signal == 'SELL' else None
    
    atr = calc_atr(df_1h).iloc[-1]
    
    if signal == 'BUY':
        stop_loss = min(recent_low, current_price - atr * 1.5) if recent_low else current_price - atr * 2
    else:
        stop_loss = max(recent_high, current_price + atr * 1.5) if recent_high else current_price + atr * 2
    
    entry_price = current_price
    
    # ===== حساب الأهداف =====
    risk = abs(entry_price - stop_loss)
    if signal == 'BUY':
        targets = {
            'tp1': entry_price + risk * 1.5,
            'tp2': entry_price + risk * 2.5,
            'tp3': entry_price + risk * 4.0
        }
    else:
        targets = {
            'tp1': entry_price - risk * 1.5,
            'tp2': entry_price - risk * 2.5,
            'tp3': entry_price - risk * 4.0
        }
    
    # ===== معلومات إضافية =====
    extra_info = {
        'regime': regime,
        'trend_4h': trend_4h,
        'confirm_1h': confirm_1h,
        'trigger_15m': trigger_15m,
        'price_location': price_location,
        'confidence_details': confidence_details
    }
    
    return signal, confidence, extra_info, stop_loss, entry_price, targets, None

# ==========================================
# الإشارة المتكاملة (النسخة النهائية مع النظام الهرمي)
# ==========================================

def generate_advanced_signal(df, current_price, symbol_name="", symbol=""):
    """
    الإشارة المتكاملة باستخدام النظام الهرمي
    """
    if df is None or len(df) < 100:
        return "WAIT", 50, 0, {}, [], None, None, None, None

    # ===== الحصول على البيانات للأطر الزمنية المختلفة =====
    # 4H
    df_4h = get_historical_data(symbol, period="3mo", interval="4h")
    # 1H (المستخدمة بالفعل)
    df_1h = df
    # 15M
    df_15m = get_historical_data(symbol, period="5d", interval="15m")
    
    # ===== نظام القرار الهرمي =====
    signal, confidence, extra_info, stop_loss, entry_price, targets, _ = generate_hierarchical_signal(
        df_4h, df_1h, df_15m, current_price, symbol_name, symbol
    )
    
    # ===== الحفاظ على التوافق مع الواجهة الحالية =====
    if signal == "WAIT":
        reason = extra_info.get('reason', 'لا توجد إشارة') if extra_info else 'لا توجد إشارة'
        details = {'Wait_Reason': reason}
        if extra_info:
            if 'regime' in extra_info:
                details['Market_Regime'] = extra_info['regime']['summary']
            if 'trend_4h' in extra_info:
                details['4H_Trend'] = extra_info['trend_4h']['summary']
            if 'confirm_1h' in extra_info:
                details['1H_Confirm'] = extra_info['confirm_1h']['summary']
            if 'trigger_15m' in extra_info:
                details['15M_Trigger'] = extra_info['trigger_15m']['summary']
            if 'price_location' in extra_info:
                details['Price_Location'] = extra_info['price_location']['summary']
        return signal, confidence, 0, details, [], None, None, None, None
    
    # ===== بناء التفاصيل =====
    details = {}
    net_score = confidence // 10
    
    if extra_info:
        if 'regime' in extra_info:
            details['Market_Regime'] = extra_info['regime']['summary']
        if 'trend_4h' in extra_info:
            details['4H_Trend'] = extra_info['trend_4h']['summary']
        if 'confirm_1h' in extra_info:
            details['1H_Confirm'] = extra_info['confirm_1h']['summary']
        if 'trigger_15m' in extra_info:
            details['15M_Trigger'] = extra_info['trigger_15m']['summary']
        if 'price_location' in extra_info:
            details['Price_Location'] = extra_info['price_location']['summary']
        if 'confidence_details' in extra_info:
            details['Confidence_Components'] = " | ".join(extra_info['confidence_details'])
    
    # ===== الأنماط الهيكلية =====
    patterns, _ = analyze_chart_patterns(df_1h)
    
    # ===== TBS =====
    tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs(df_1h)
    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)
    
    return signal, confidence, net_score, details, patterns, tbs_info, stop_loss, entry_price, targets

# ==========================================
# تحليل متعدد الأطر الزمنية (MTF)
# ==========================================
def get_mtf_signal(symbol, current_price):
    timeframes = ['15m', '1h', '4h']
    signals = []
    for tf in timeframes:
        try:
            df = get_historical_data(symbol, period="5d", interval=tf)
            if df is not None and len(df) > 50:
                rsi = calc_rsi(df['close']).iloc[-1]
                if rsi < 30:
                    signals.append(('BUY', tf))
                elif rsi > 70:
                    signals.append(('SELL', tf))
                else:
                    signals.append(('NEUTRAL', tf))
        except:
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
# جمع إشارات جميع الأزواج
# ==========================================
@st.cache_data(ttl=120)
def get_all_signals_with_trades():
    results = []
    total_pairs = len(PAIRS)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (pair_name, symbol) in enumerate(PAIRS.items()):
        status_text.text(f"جاري تحليل {pair_name}... ({idx+1}/{total_pairs})")
        progress_bar.progress((idx + 1) / total_pairs)
        
        try:
            df = get_historical_data(symbol, period="1mo", interval="1h")
            if df is None or len(df) < 100:
                continue
            current_price = df['close'].iloc[-1]
            
            signal, confidence, net_score, _, _, _, stop_loss, entry_price, targets = generate_advanced_signal(df, current_price, pair_name, symbol)
            
            if "Gold" in pair_name or "Silver" in pair_name or "Bitcoin" in pair_name or "Ethereum" in pair_name:
                price_str = f"${current_price:,.2f}"
                fmt = "${:,.2f}"
            else:
                price_str = f"{current_price:.4f}"
                fmt = "{:.4f}"
            
            trade_details = {}
            if signal in ["BUY", "SELL"] and confidence >= 60 and stop_loss and entry_price and targets:
                trade_details = {
                    "entry": entry_price,
                    "stop_loss": stop_loss,
                    "target1": targets.get('tp1'),
                    "target2": targets.get('tp2'),
                    "target3": targets.get('tp3'),
                    "risk_reward": f"1:{targets.get('tp3', 0)/abs(entry_price - stop_loss):.1f}" if stop_loss else "N/A"
                }
            
            results.append({
                "الزوج": pair_name,
                "الإشارة": signal,
                "الثقة": round(confidence, 1),
                "النتيجة": net_score,
                "السعر": price_str,
                "سعر الدخول": fmt.format(entry_price) if entry_price else "N/A",
                "وقف الخسارة": fmt.format(stop_loss) if stop_loss else "N/A",
                "الهدف 1": fmt.format(trade_details.get('target1')) if trade_details.get('target1') else "N/A",
                "الهدف 2": fmt.format(trade_details.get('target2')) if trade_details.get('target2') else "N/A",
                "الهدف 3": fmt.format(trade_details.get('target3')) if trade_details.get('target3') else "N/A",
                "نسبة المخاطرة": trade_details.get('risk_reward', "N/A")
            })
        except Exception as e:
            continue
    
    progress_bar.empty()
    status_text.empty()
    return pd.DataFrame(results)

# ==========================================
# إدارة الصفقات
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
# كشف الانعكاس (Reversal)
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
    
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if direction == "BUY":
            if rsi > 70:
                signals.append("RSI فوق 70 (تشبع شرائي)")
            elif rsi < 30 and current_price < entry:
                signals.append("RSI تحت 30 مع هبوط (ضعف)")
        else:
            if rsi < 30:
                signals.append("RSI تحت 30 (تشبع بيعي)")
            elif rsi > 70 and current_price > entry:
                signals.append("RSI فوق 70 مع صعود (ضعف)")

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
            if upper_wick > candle_range * 0.5:
                signals.append("شمعة انعكاس هابط (ذيل علوي طويل)")
        else:
            lower_wick = min(last['close'], last['open']) - last['low']
            if lower_wick > candle_range * 0.5:
                signals.append("شمعة انعكاس صاعد (ذيل سفلي طويل)")

    if direction == "BUY":
        recent_low = df['low'].iloc[-10:].min()
        if current_price < recent_low:
            signals.append(f"كسر الدعم القريب ({recent_low:.4f})")
    else:
        recent_high = df['high'].iloc[-10:].max()
        if current_price > recent_high:
            signals.append(f"كسر المقاومة القريبة ({recent_high:.4f})")

    if signals:
        return True, " | ".join(signals)
    return False, ""

# ==========================================
# شرح القرار
# ==========================================
def explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns, tbs_info, df, current_price, stop_loss, entry_price, targets):
    explanation = ""
    if signal == "BUY":
        explanation = "🔹 **قرار الشراء** بناءً على:\n"
        for k, v in details.items():
            if v and ("+" in str(v) or any(word in str(v) for word in ["شراء", "صاعد", "فوق", "قرب الحد السفلي", "مفرط البيع", "قوي", "كتلة", "FVG", "اجتياح", "تحول", "خصم", "TBS", "MFI", "فيبوناتشي", "انعكاس Smart Money صاعد", "متوافق", "لندن", "نيويورك"])):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≥5 للشراء)\n📈 **الثقة**: {confidence:.0f}%"
    elif signal == "SELL":
        explanation = "🔻 **قرار البيع** بناءً على:\n"
        for k, v in details.items():
            if v and ("-" in str(v) or any(word in str(v) for word in ["بيع", "هابط", "تحت", "قرب الحد الأعلى", "مفرط الشراء", "قمة", "كتلة بيع", "تحول هابط", "TBS", "انعكاس Smart Money هابط"])):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≤-5 للبيع)\n📉 **الثقة**: {confidence:.0f}%"
    else:
        explanation = "⏳ **قرار الانتظار** بسبب:\n"
        for k, v in details.items():
            if v:
                explanation += f"- {k}: {v}\n"
        explanation += "💡 **نصيحة**: انتظر حتى تتوفر جميع الظروف المطلوبة للدخول."
    
    if stop_loss and entry_price and targets:
        explanation += f"\n\n📍 **سعر الدخول المقترح:** {entry_price:.4f}"
        explanation += f"\n🛑 **وقف الخسارة:** {stop_loss:.4f} (المسافة: {abs(entry_price - stop_loss):.4f})"
        explanation += f"\n🎯 **الأهداف:**"
        explanation += f"\n   - الهدف 1 (1:1.5): {targets.get('tp1', 0):.4f}"
        explanation += f"\n   - الهدف 2 (1:2.5): {targets.get('tp2', 0):.4f}"
        explanation += f"\n   - الهدف 3 (1:4): {targets.get('tp3', 0):.4f}"
    
    explanation += f"\n\n🕒 **تحليل الأطر الزمنية**: {mtf_signal} (عدد الأطر: {mtf_count})"
    
    if patterns:
        explanation += "\n\n📐 **النماذج المكتشفة:**\n"
        for p in patterns:
            explanation += f"- {p['pattern']} ({p['direction']}) - قوة: {p['score']}/5\n"
    
    if tbs_info and tbs_info[0]:
        tbs_type, tbs_entry, tbs_stop, tbs_level = tbs_info
        if tbs_type:
            explanation += f"\n\n🐢 **TBS (Turtle Body Soup) مكتشف:** {tbs_type}\n"

    return explanation

# ==========================================
# بداية الواجهة الرئيسية (Streamlit)
# ==========================================

# تهيئة حالة الجلسة
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
if "currency_strength" not in st.session_state:
    st.session_state.currency_strength = None
if "economic_events" not in st.session_state:
    st.session_state.economic_events = None
if "news_analysis" not in st.session_state:
    st.session_state.news_analysis = None

with st.sidebar:
    st.markdown("### 📊 حالة السوق")
    status, status_text, next_event, close_time = get_market_status()
    if status == "OPEN":
        st.markdown(f"🟢 **{status_text}**")
        st.markdown(f"⏳ **يغلق في:** {time_remaining(next_event)}")
        st.markdown(f"🔒 **إغلاق:** {format_time(close_time)}")
    else:
        st.markdown(f"🔴 **{status_text}**")
        st.markdown(f"⏳ **يفتح في:** {time_remaining(next_event)}")
        st.markdown(f"🔓 **افتتاح:** {format_time(next_event)}")
    st.markdown("---")
    
    # ===== مؤشرات العملات =====
    st.markdown("### 💰 قوة العملات")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 تحديث القوة", key="refresh_currency_strength", width='stretch'):
            with st.spinner("جارٍ حساب القوة..."):
                st.session_state.currency_strength = get_currency_strength()
                st.rerun()
    with col2:
        if st.button("🗑️ مسح", key="clear_currency_strength", width='stretch'):
            st.session_state.currency_strength = None
            st.rerun()
    
    if st.session_state.currency_strength:
        strength = st.session_state.currency_strength
        sorted_currencies = sorted(strength.items(), key=lambda x: x[1], reverse=True)
        
        cols = st.columns(4)
        for i, (currency, value) in enumerate(sorted_currencies):
            if i >= 4:
                break
            color = "🟢" if value > 0.5 else ("🟡" if value > -0.5 else "🔴")
            with cols[i % 4]:
                st.metric(
                    f"{color} {currency}",
                    f"{value:+.2f}%",
                    delta_color="normal"
                )
        
        if len(sorted_currencies) >= 2:
            strongest = sorted_currencies[0]
            weakest = sorted_currencies[-1]
            st.markdown(f"""
            <div style="font-size: 0.8rem; background: rgba(10,10,10,0.4); border-radius: 8px; padding: 10px; margin: 5px 0;">
                <span style="color: #00ff88;">▲ {strongest[0]} {strongest[1]:+.2f}%</span><br>
                <span style="color: #ff4444;">▼ {weakest[0]} {weakest[1]:+.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
            
            best_pairs = []
            if strongest[0] != weakest[0]:
                best_buy = f"{strongest[0]}/{weakest[0]}"
                best_sell = f"{weakest[0]}/{strongest[0]}"
                for pair_name, symbol in PAIRS.items():
                    if best_buy in pair_name and "XAU" not in pair_name and "XAG" not in pair_name and "BTC" not in pair_name and "ETH" not in pair_name:
                        best_pairs.append(("🟢 شراء", best_buy))
                    if best_sell in pair_name and "XAU" not in pair_name and "XAG" not in pair_name and "BTC" not in pair_name and "ETH" not in pair_name:
                        best_pairs.append(("🔴 بيع", best_sell))
            
            if best_pairs:
                st.markdown("**📊 أفضل الصفقات:**")
                for action, pair in best_pairs[:2]:
                    st.markdown(f"- {action} {pair}")
    else:
        st.info("اضغط 'تحديث القوة'")
    
    st.markdown("---")
    
    # ===== جميع الإشارات =====
    st.markdown("### 📋 جميع الإشارات المتاحة")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 تحديث الكل", key="refresh_all_signals", width='stretch'):
            with st.spinner("جارٍ التحليل..."):
                st.session_state.all_signals = get_all_signals_with_trades()
                st.session_state.last_update = datetime.now()
                st.rerun()
    with col2:
        if st.button("🗑️ مسح", key="clear_all_signals", width='stretch'):
            st.session_state.all_signals = None
            st.rerun()
    
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_signals = st.session_state.all_signals.copy()
        def color_signal(val):
            if val == "BUY": return "🟢 شراء"
            elif val == "SELL": return "🔴 بيع"
            else: return "⚪ انتظار"
        df_signals["الإشارة"] = df_signals["الإشارة"].apply(color_signal)
        st.dataframe(
            df_signals[["الزوج", "الإشارة", "الثقة", "النتيجة", "السعر"]],
            column_config={
                "الزوج": st.column_config.TextColumn("الزوج", width="medium"),
                "الإشارة": st.column_config.TextColumn("الإشارة", width="small"),
                "الثقة": st.column_config.NumberColumn("الثقة", format="%.1f%%"),
                "النتيجة": st.column_config.NumberColumn("النتيجة", format="%d"),
                "السعر": st.column_config.TextColumn("السعر"),
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )
        buy_count = len(df_signals[df_signals["الإشارة"] == "🟢 شراء"])
        sell_count = len(df_signals[df_signals["الإشارة"] == "🔴 بيع"])
        wait_count = len(df_signals) - buy_count - sell_count
        col_b, col_s, col_w = st.columns(3)
        col_b.markdown(f"🟢 **{buy_count}** شراء")
        col_s.markdown(f"🔴 **{sell_count}** بيع")
        col_w.markdown(f"⚪ **{wait_count}** انتظار")
        st.caption(f"🕐 آخر تحديث: {st.session_state.last_update.strftime('%H:%M:%S')}")
    else:
        st.info("اضغط 'تحديث الكل' لعرض جميع الإشارات")
    
    st.markdown("---")
    st.markdown("### 🔍 اختر الزوج للتحليل")
    selected_pair_name = st.selectbox("اختر الزوج للتحليل المتقدم", list(PAIRS.keys()), index=0, key="pair_selector")
    selected_symbol = PAIRS[selected_pair_name]
    st.markdown("---")
    st.markdown("### 📋 إدارة الصفقات اليدوية")
    if st.button("➕ صفقة جديدة", key="new_trade_button", width='stretch'):
        st.session_state.show_form = not st.session_state.show_form
        st.rerun()

# جلب البيانات للزوج المختار
for attempt in range(3):
    current_price, change = get_spot_price(selected_symbol)
    if current_price is not None:
        break
    time.sleep(1)

df = get_historical_data(selected_symbol, period="1mo", interval="1h")

if df is None:
    st.error("⚠️ تعذر تحميل البيانات بعد عدة محاولات. يرجى التحقق من اتصال الإنترنت أو اختيار زوج آخر.")
    if st.button("🔄 إعادة محاولة تحميل البيانات", key="retry_load_data", width='stretch'):
        st.cache_data.clear()
        st.rerun()
    st.stop()

if current_price is None:
    current_price = df['close'].iloc[-1]
    change = 0

# توليد الإشارة
signal, confidence, net_score, details, patterns, tbs_info, stop_loss, entry_price, targets = generate_advanced_signal(df, current_price, selected_pair_name, selected_symbol)
mtf_signal, mtf_count = get_mtf_signal(selected_symbol, current_price)

# عرض السعر
if "Gold" in selected_pair_name or "Silver" in selected_pair_name:
    price_format = "${:,.2f}"
elif "Bitcoin" in selected_pair_name or "Ethereum" in selected_pair_name:
    price_format = "${:,.2f}"
else:
    price_format = "{:.4f}"

st.markdown(f"""
<div class="price-card">
    <div class="price-label">{selected_pair_name}</div>
    <div class="price-value">{price_format.format(current_price)}</div>
    <div class="price-change" style="color: {'#00ff88' if change >= 0 else '#ff4444'};">
        {change:+.2f}%
    </div>
</div>
""", unsafe_allow_html=True)

# زر تحديث
col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 2, 1])
with col_refresh2:
    if st.button("🔄 تحديث البيانات", key="refresh_data_button", width='stretch'):
        st.session_state.refresh_trigger = not st.session_state.refresh_trigger
        st.session_state.last_update = datetime.now()
        st.cache_data.clear()
        st.success("✅ تم تحديث البيانات بنجاح!")
        st.rerun()

st.caption(f"🕐 آخر تحديث: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# مؤشرات السوق
col_btn, col_title = st.columns([1, 5])
with col_btn:
    btn_label = "📊 إخفاء" if st.session_state.show_indicators else "📊 إظهار"
    if st.button(btn_label, key="toggle_indicators", width='stretch'):
        st.session_state.show_indicators = not st.session_state.show_indicators
        st.rerun()
with col_title:
    st.markdown("### مؤشرات السوق")

if st.session_state.show_indicators:
    cols = st.columns(6)
    last = df.iloc[-1]
    cols[0].metric("RSI", f"{last['rsi']:.1f}")
    cols[1].metric("ATR", f"${last['atr']:.2f}" if "Gold" in selected_pair_name else f"{last['atr']:.4f}")
    cols[2].metric("ADX", f"{last['adx']:.1f}")
    cols[3].metric("VWAP", f"${last['vwap']:.2f}" if "Gold" in selected_pair_name else f"{last['vwap']:.4f}")
    cols[4].metric("MFI", f"{last['mfi']:.1f}")
    cols[5].metric("MACD Hist", f"{last['macd_histogram']:.4f}")
else:
    st.caption("👆 اضغط 'إظهار' لعرض مؤشرات السوق")

st.markdown("---")

# عرض الصفقة المقترحة
if signal in ["BUY", "SELL"] and confidence >= 60 and stop_loss and entry_price and targets:
    direction_text = "شراء (BUY)" if signal == "BUY" else "بيع (SELL)"
    risk_reward = f"1:{targets.get('tp3', 0)/abs(entry_price - stop_loss):.1f}" if stop_loss else "N/A"
    
    st.markdown(f"""
    <div class="suggested-trade">
        <b>الاتجاه:</b> {direction_text} (الثقة: {confidence:.0f}%)<br>
        <b>📍 سعر الدخول المقترح:</b> {price_format.format(entry_price)}<br>
        <b>🛑 وقف الخسارة:</b> {price_format.format(stop_loss)} (المسافة: {abs(entry_price - stop_loss):.2f} نقطة)<br>
        <div class="target-zone"><b>🎯 الهدف 1 (1:1.5):</b> {price_format.format(targets.get('tp1', 0))}</div>
        <div class="target-zone" style="border-left-color: #ffaa00;"><b>🎯 الهدف 2 (1:2.5):</b> {price_format.format(targets.get('tp2', 0))}</div>
        <div class="target-zone" style="border-left-color: #00ff88;"><b>🎯 الهدف 3 (1:4):</b> {price_format.format(targets.get('tp3', 0))}</div>
        <b>📈 نسبة المخاطرة/المكافأة القصوى:</b> {risk_reward}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ إضافة هذه الصفقة", key="add_suggested_trade", width='stretch'):
        trade_manager = TradeManager()
        account_balance = 100000
        risk_per_trade_pct = 1.5
        risk_per_trade = account_balance * (risk_per_trade_pct / 100)
        risk_amount = abs(entry_price - stop_loss)
        
        # حساب حجم الصفقة حسب نوع الأصل
        asset_type = get_asset_type_from_symbol(selected_pair_name)
        if asset_type in ["forex"]:
            lot_size = risk_per_trade / (risk_amount * 100) if risk_amount > 0 else 0.01
        elif asset_type in ["gold", "silver"]:
            lot_size = risk_per_trade / (risk_amount * 10) if risk_amount > 0 else 0.01
        else:
            lot_size = risk_per_trade / risk_amount if risk_amount > 0 else 0.01
        lot_size = round(max(lot_size, 0.01), 2)
        
        trailing_dist = last['atr'] * 0.3 if 'atr' in last and not pd.isna(last['atr']) else (3 if "Gold" in selected_pair_name else 0.0003)
        
        trade_data = {
            "direction": signal,
            "entry": entry_price,
            "lots": lot_size,
            "stop_loss": stop_loss,
            "take_profit": targets.get('tp2', entry_price + (abs(entry_price - stop_loss) * 2.5)),
            "trailing_enabled": True,
            "trailing_distance": trailing_dist,
            "notes": f"مقترحة من الإشارة الهرمية (الثقة {confidence:.0f}%)"
        }
        trade_id = trade_manager.add_trade(trade_data)
        st.success(f"✅ تم إضافة الصفقة {trade_id} بنجاح!")
        st.rerun()

else:
    st.info("⏳ لا توجد صفقة مقترحة حالياً (انتظر توفر جميع شروط الدخول)")

# النماذج و TBS
if patterns:
    st.markdown("#### 📐 النماذج المكتشفة")
    pattern_html = " ".join([f'<span class="pattern-badge">{p["pattern"]} ({p["direction"]})</span>' for p in patterns])
    st.markdown(pattern_html, unsafe_allow_html=True)

tbs_type, tbs_entry, tbs_stop, tbs_level = tbs_info
if tbs_type:
    st.markdown("#### 🐢 TBS (Turtle Body Soup) مكتشف!")
    if tbs_type == "BULLISH":
        st.success(f"**إشارة TBS شراء** عند {price_format.format(tbs_entry)} (وقف: {price_format.format(tbs_stop)})")
    else:
        st.error(f"**إشارة TBS بيع** عند {price_format.format(tbs_entry)} (وقف: {price_format.format(tbs_stop)})")
    st.caption(f"المستوى القديم المُختَرق: {price_format.format(tbs_level)}")

# الإشارة
st.markdown("---")
st.markdown("### 🧠 إشارة التداول المتكاملة")

if confidence < 40:
    strength = "ضعيفة جداً"
elif confidence < 60:
    strength = "متوسطة"
else:
    strength = "قوية"

signal_color = "#ffaa00" if signal == "WAIT" else ("#00ff88" if signal == "BUY" else "#ff4444")
st.markdown(f"""
<div class="signal-box">
    <div class="signal-text" style="color: {signal_color};">{signal}</div>
    <div class="signal-confidence">الثقة: {confidence:.0f}% | النتيجة: {net_score} | القوة: {strength}</div>
    <div style="font-size:0.9rem; color:#aaa; margin-top:10px;">
        MTF إجماع: {mtf_signal} (عدد الأطر: {mtf_count})
    </div>
</div>
""", unsafe_allow_html=True)

# شرح القرار
with st.expander("📝 شرح القرار", expanded=True):
    explanation = explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns, tbs_info, df, current_price, stop_loss, entry_price, targets)
    st.markdown(f'<div class="explanation-box">{explanation}</div>', unsafe_allow_html=True)

# ==========================================
# التقويم الاقتصادي
# ==========================================
st.markdown("---")
st.markdown("### 📅 التقويم الاقتصادي")

if st.button("🔄 تحديث التقويم الاقتصادي", key="refresh_economic_calendar", width='stretch'):
    with st.spinner("جارٍ جلب بيانات التقويم..."):
        st.session_state.economic_events = get_fmp_economic_calendar()

if st.session_state.economic_events:
    display_economic_events(st.session_state.economic_events)
else:
    st.info("اضغط 'تحديث التقويم الاقتصادي' لعرض الأحداث")

# ==========================================
# تحليل الأخبار
# ==========================================
st.markdown("---")
st.markdown("### 📰 تحليل الأخبار")

if st.button("🔄 تحديث تحليل الأخبار", key="refresh_news_analysis", width='stretch'):
    with st.spinner("جارٍ تحليل الأخبار..."):
        news = get_fmp_news()
        if news:
            asset_type = get_asset_type_from_symbol(selected_pair_name)
            asset_news = get_asset_specific_news(news, asset_type)
            st.session_state.news_analysis = analyze_asset_news(asset_news, asset_type)
        else:
            st.session_state.news_analysis = None

if st.session_state.news_analysis:
    news_data = st.session_state.news_analysis
    st.info(f"📊 {news_data['summary']}")
else:
    st.info("اضغط 'تحديث تحليل الأخبار' لعرض التحليل")

# ==========================================
# تحليل الارتباط بين العملات
# ==========================================
st.markdown("---")
st.markdown("### 🔗 تحليل الارتباط بين العملات")

corr_pairs = st.multiselect(
    "اختر الأزواج لتحليل الارتباط:",
    options=list(PAIRS.keys()),
    default=["XAU/USD (Gold)", "EUR/USD", "USD/JPY", "GBP/USD"],
    key="correlation_pairs"
)

if corr_pairs and st.button("📊 عرض مصفوفة الارتباط", key="show_correlation_matrix", width='stretch'):
    with st.spinner("جارٍ حساب الارتباطات..."):
        symbols = [PAIRS[pair] for pair in corr_pairs]
        corr_matrix = get_correlation_matrix(symbols)
        
        if not corr_matrix.empty:
            st.dataframe(
                corr_matrix.round(3),
                use_container_width=True,
                column_config={col: st.column_config.NumberColumn(format="%.3f") for col in corr_matrix.columns}
            )
            
            fig_corr = go.Figure()
            pair_names = list(corr_matrix.columns)
            for i, pair1 in enumerate(pair_names):
                fig_corr.add_trace(go.Bar(
                    x=pair_names,
                    y=corr_matrix.iloc[i].values,
                    name=pair1,
                    text=[f"{val:.2f}" for val in corr_matrix.iloc[i].values],
                    textposition='outside'
                ))
            
            fig_corr.update_layout(
                height=400,
                template='plotly_dark',
                title="مصفوفة الارتباط بين الأزواج",
                barmode='group',
                xaxis_title="الأزواج",
                yaxis_title="معامل الارتباط",
                yaxis=dict(range=[-1, 1])
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            strong_correlations = []
            for i, pair1 in enumerate(pair_names):
                for j, pair2 in enumerate(pair_names):
                    if i < j:
                        corr_val = corr_matrix.iloc[i, j]
                        if abs(corr_val) > 0.7:
                            direction = "موجب (نفس الاتجاه)" if corr_val > 0 else "سالب (عكس الاتجاه)"
                            strong_correlations.append(f"**{corr_pairs[i]}** ↔ **{corr_pairs[j]}**: {corr_val:.3f} ({direction})")
            
            if strong_correlations:
                st.markdown("#### 📌 ارتباطات قوية مكتشفة:")
                for corr in strong_correlations:
                    st.markdown(f"- {corr}")
        else:
            st.warning("لا توجد بيانات كافية لحساب الارتباط")

# ==========================================
# جميع الصفقات المقترحة
# ==========================================
st.markdown("---")
st.markdown("### 🚀 جميع الصفقات المقترحة (عبر جميع الأزواج)")

if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
    df_all = st.session_state.all_signals.copy()
    df_trades = df_all[(df_all["الإشارة"].isin(["BUY", "SELL"])) & (df_all["الثقة"] >= 60)]
    
    if not df_trades.empty:
        cols_to_show = ["الزوج", "الإشارة", "الثقة", "سعر الدخول", "وقف الخسارة", "الهدف 1", "الهدف 2", "الهدف 3", "نسبة المخاطرة"]
        def style_signal(val):
            if val == "BUY":
                return "🟢 شراء"
            elif val == "SELL":
                return "🔴 بيع"
            return val
        df_trades["الإشارة"] = df_trades["الإشارة"].apply(style_signal)
        
        st.dataframe(
            df_trades[cols_to_show],
            column_config={
                "الزوج": st.column_config.TextColumn("الزوج", width="medium"),
                "الإشارة": st.column_config.TextColumn("الإشارة", width="small"),
                "الثقة": st.column_config.NumberColumn("الثقة", format="%.1f%%"),
                "سعر الدخول": st.column_config.TextColumn("الدخول"),
                "وقف الخسارة": st.column_config.TextColumn("الوقف"),
                "الهدف 1": st.column_config.TextColumn("هدف 1"),
                "الهدف 2": st.column_config.TextColumn("هدف 2"),
                "الهدف 3": st.column_config.TextColumn("هدف 3"),
                "نسبة المخاطرة": st.column_config.TextColumn("R/R"),
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.caption(f"🟢 إجمالي صفقات الشراء: {len(df_trades[df_trades['الإشارة'] == '🟢 شراء'])}  |  🔴 إجمالي صفقات البيع: {len(df_trades[df_trades['الإشارة'] == '🔴 بيع'])}")
    else:
        st.info("لا توجد صفقات مقترحة حالياً (جميع الإشارات ضعيفة أو انتظار).")
else:
    st.info("اضغط 'تحديث الكل' في الشريط الجانبي لعرض جميع الصفقات المقترحة.")

# إدارة الصفقات
st.markdown("---")
st.markdown("### 💼 إدارة الصفقات")
trade_manager = TradeManager()

reversal_messages = []
for trade in trade_manager.open_trades:
    if trade["status"] == "open":
        is_reversal, reversal_msg = detect_reversal(df, trade)
        if is_reversal:
            reversal_messages.append(f"⚠️ الصفقة {trade['id']}: {reversal_msg}")
        if trade["trailing_enabled"]:
            trade_manager.update_trailing_stop(trade["id"], current_price)

if reversal_messages:
    st.markdown("---")
    st.markdown("### 🔄 تنبيهات الانعكاس")
    for msg in reversal_messages:
        st.markdown(f"""
        <div class="reversal-alert">
            {msg}
            <br><span style="color:#aaa; font-size:0.8rem;">يُنصح بمراجعة الصفقة أو إغلاقها</span>
        </div>
        """, unsafe_allow_html=True)

if trade_manager.open_trades:
    st.write("**الصفقات المفتوحة:**")
    for trade in trade_manager.open_trades:
        if trade["stage"] == 0:
            stage_text = "🟡 وقف ثابت"
        elif trade["stage"] == 1:
            stage_text = "🟢 نقطة تعادل"
        elif trade["stage"] >= 2:
            stage_text = "🔵 وقف متحرك"
        st.markdown(f"""
        <div class="trade-row">
            <b>{trade['id']}</b> | {trade['direction']} | الدخول: {trade['entry']} | اللوت: {trade['lots']} | 
            الوقف الحالي: {trade['stop_loss']} | الهدف: {trade['take_profit']}
            <br><span style="color:#aaa;">المرحلة: {stage_text} {" | 🔄 وقف متحرك مفعّل" if trade['trailing_enabled'] else ""}</span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        if col1.button(f"🔄 تحديث الوقف {trade['id']}", key=f"update_stop_{trade['id']}", width='stretch'):
            if trade_manager.update_trailing_stop(trade["id"], current_price):
                st.success("تم تحديث الوقف المتحرك!")
                st.rerun()
            else:
                st.info("الوقف في أفضل وضعية حالياً")
        if col2.button(f"🔍 كشف انعكاس {trade['id']}", key=f"check_reversal_{trade['id']}", width='stretch'):
            is_reversal, msg = detect_reversal(df, trade)
            if is_reversal:
                st.warning(f"⚠️ انعكاس مكتشف: {msg}")
            else:
                st.success("✅ لا توجد إشارة انعكاس حالياً")
        if col3.button(f"❌ إغلاق {trade['id']}", key=f"close_trade_{trade['id']}", width='stretch'):
            profit = trade_manager.close_trade(trade['id'], current_price)
            st.success(f"تم الإغلاق، الربح: ${profit:.2f}" if profit else "تم الإغلاق")
            st.rerun()
else:
    st.write("لا توجد صفقات مفتوحة")

if trade_manager.closed_trades:
    profits = [t.get('profit', 0) for t in trade_manager.closed_trades if 'profit' in t]
    if profits:
        win_rate = sum(1 for p in profits if p > 0) / len(profits) * 100
        total_profit = sum(profits)
        avg_profit = total_profit / len(profits)
        st.metric("نسبة الربح", f"{win_rate:.1f}%")
        st.metric("إجمالي الربح", f"${total_profit:.2f}")
        st.metric("متوسط الربح", f"${avg_profit:.2f}")

if st.session_state.show_form:
    with st.form("new_trade_form"):
        st.subheader("➕ تفاصيل الصفقة")
        direction = st.selectbox("الاتجاه", ["BUY", "SELL"], key="trade_direction")
        entry = st.number_input("سعر الدخول", value=float(current_price), format="%.2f" if "Gold" in selected_pair_name else "%.4f", key="trade_entry")
        stop = st.number_input("وقف الخسارة", value=float(current_price - 20 if "Gold" in selected_pair_name else 0.001), format="%.2f" if "Gold" in selected_pair_name else "%.4f", key="trade_stop")
        targets_input = st.text_input("الأهداف (مفصولة بفاصلة)", placeholder="1950, 1960, 1970" if "Gold" in selected_pair_name else "1.1050, 1.1080, 1.1120", key="trade_targets")
        lots = st.number_input("عدد اللوتات", min_value=0.01, value=0.1, step=0.01, key="trade_lots")
        submitted = st.form_submit_button("إضافة الصفقة")
        if submitted and entry > 0 and stop > 0:
            targets_list = [float(x.strip()) for x in targets_input.split(",") if x.strip()]
            trade_data = {
                "direction": direction,
                "entry": entry,
                "lots": lots,
                "stop_loss": stop,
                "take_profit": targets_list[0] if targets_list else (entry + 40 if "Gold" in selected_pair_name else entry + 0.002),
                "trailing_enabled": False,
                "trailing_distance": 0,
                "notes": "تمت إضافتها يدوياً"
            }
            trade_id = trade_manager.add_trade(trade_data)
            st.success(f"✅ تم إضافة الصفقة {trade_id}")
            st.session_state.show_form = False
            st.rerun()

# الرسم البياني
st.markdown("---")
st.markdown("### 📈 Price Chart")
df_smc = analyze_smc_ict(df)
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                    row_heights=[0.6, 0.2, 0.2])
fig.add_trace(go.Scatter(x=df.index, y=df['close'], name='Price', line=dict(color='gold', width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', line=dict(color='orange', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], name='EMA50', line=dict(color='red', dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_middle'], name='BB Middle', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dot')), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['vwap'], name='VWAP', line=dict(color='blue', width=0.8)), row=1, col=1)

# BSL/SSL
if not df_smc['bsl'].isna().all():
    fig.add_hline(y=df_smc['bsl'].iloc[-1], line_dash="dash", line_color="rgba(0,255,0,0.5)", row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=df_smc['bsl'].iloc[-1], text="BSL", showarrow=True, arrowhead=1, row=1, col=1)
if not df_smc['ssl'].isna().all():
    fig.add_hline(y=df_smc['ssl'].iloc[-1], line_dash="dash", line_color="rgba(255,0,0,0.5)", row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=df_smc['ssl'].iloc[-1], text="SSL", showarrow=True, arrowhead=1, row=1, col=1)

# SMC signals
if df_smc['order_block_bullish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1], text="OB+", showarrow=True, arrowhead=1, row=1, col=1)
if df_smc['order_block_bearish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1], text="OB-", showarrow=True, arrowhead=1, row=1, col=1)

# SMR signals
if df_smc['smr_bullish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1] + (5 if "Gold" in selected_pair_name else 0.001), text="SMR ▲", showarrow=True, arrowhead=1, row=1, col=1, font_color="green")
if df_smc['smr_bearish'].iloc[-1]:
    fig.add_annotation(x=df.index[-1], y=df['close'].iloc[-1] - (5 if "Gold" in selected_pair_name else 0.001), text="SMR ▼", showarrow=True, arrowhead=1, row=1, col=1, font_color="red")

if tbs_type:
    fig.add_hline(y=tbs_level, line_dash="dot", line_color="orange", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=tbs_level, text="TBS Old Level", showarrow=True, arrowhead=1, row=1, col=1)
    fig.add_hline(y=tbs_entry, line_dash="dash", line_color="yellow", opacity=0.5, row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=tbs_entry, text="TBS Entry", showarrow=True, arrowhead=1, row=1, col=1)

if stop_loss and entry_price:
    fig.add_hline(y=stop_loss, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=stop_loss, text="Stop Loss", showarrow=True, arrowhead=1, row=1, col=1)
    fig.add_hline(y=entry_price, line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)
    fig.add_annotation(x=df.index[-1], y=entry_price, text="Entry", showarrow=True, arrowhead=1, row=1, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['rsi'], name='RSI', line=dict(color='purple')), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)

fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
fig.add_bar(x=df.index, y=df['macd_histogram'], name='Histogram', marker_color='gray', opacity=0.3, row=3, col=1)

fig.update_layout(height=800, template='plotly_dark', showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# تحليل DXY للذهب
if selected_symbol == "GC=F":
    st.markdown("---")
    st.markdown("### 🔗 تحليل الارتباط: الذهب vs الدولار")
    df_dxy = get_historical_data("DX-Y.NYB", "1mo", "1h")
    if df_dxy is not None and not df_dxy.empty:
        df_dxy_aligned = df_dxy.reindex(df.index, method='nearest')
        df_dxy_aligned = df_dxy_aligned.ffill()
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

# تذييل
st.markdown(f"""
<div class="footer">
    <span class="brand">▲ BLACK PYRAMID v2002</span> • Advanced Trading Intelligence<br>
    SMC/ICT • Liquidity (BSL/SSL) • SMR • Patterns • TBS • Hierarchical Decision System<br>
    4H Bias → 1H Confirmation → 15M Trigger → Price Location → News Filter → Risk Management<br>
    Integrated Signals & Trade Management
</div>
""", unsafe_allow_html=True)
