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
            'mfi': 3, 'smr': 4, 'candle': 4, 'divergence': 5,
            'fresh_ob': 4, 'fibonacci': 3, 'macd_hist': 3
        }
    elif asset_type == "crypto":
        weights = {
            'rsi': 2, 'macd': 4, 'bb': 3, 'vwap': 2, 'adx': 2,
            'ichimoku': 5, 'smc': 5, 'patterns': 5, 'tbs': 5,
            'mfi': 3, 'smr': 4, 'candle': 4, 'divergence': 5,
            'fresh_ob': 4, 'fibonacci': 3, 'macd_hist': 3
        }
    else:  # forex
        weights = {
            'rsi': 3, 'macd': 3, 'bb': 3, 'vwap': 2, 'adx': 2,
            'ichimoku': 3, 'smc': 4, 'patterns': 5, 'tbs': 5,
            'mfi': 3, 'smr': 4, 'candle': 4, 'divergence': 5,
            'fresh_ob': 4, 'fibonacci': 3, 'macd_hist': 2
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
# الإشارة المتكاملة (النسخة النهائية مع الإعدادات الديناميكية)
# ==========================================
def generate_advanced_signal(df, current_price, symbol_name="", symbol=""):
    if df is None or len(df) < 100:
        return "WAIT", 50, 0, {}, [], None, None, None, None

    # ===== الحصول على الإعدادات حسب نوع الأصل =====
    settings = get_indicator_settings(symbol_name)
    asset_type = settings['asset_type']
    
    # ===== حساب المؤشرات بالإعدادات الديناميكية =====
    macd_settings = settings['macd']
    rsi_settings = settings['rsi']
    mfi_settings = settings['mfi']
    bb_settings = settings['bb']
    ichimoku_settings = settings['ichimoku']
    
    # إعادة حساب المؤشرات بالإعدادات الجديدة
    df['rsi'] = calc_rsi(df['close'], period=rsi_settings['period'])
    df['atr'] = calc_atr(df, period=settings['atr_period'])
    df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(
        df['close'], 
        fast=macd_settings['fast'],
        slow=macd_settings['slow'],
        signal=macd_settings['signal']
    )
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(
        df['close'],
        period=bb_settings['period'],
        std_dev=bb_settings['std_dev']
    )
    df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df, period=settings['adx_period'])
    df['vwap'] = calc_vwap(df)
    tenkan, kijun, senkou_a, senkou_b, chikou = calc_ichimoku(
        df,
        tenkan=ichimoku_settings['tenkan'],
        kijun=ichimoku_settings['kijun'],
        senkou=ichimoku_settings['senkou']
    )
    df['tenkan'] = tenkan
    df['kijun'] = kijun
    df['senkou_a'] = senkou_a
    df['senkou_b'] = senkou_b
    df['chikou'] = chikou
    df['mfi'] = calc_mfi(df, period=mfi_settings['period'])

    df_smc = analyze_smc_ict(df)
    last_smc = df_smc.iloc[-1]
    patterns, _ = analyze_chart_patterns(df)
    tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs(df)
    last = df.iloc[-1]

    # ===== الحصول على الأوزان الديناميكية =====
    weights = get_dynamic_weights(df, asset_type)
    scores = {'BUY': 0, 'SELL': 0}
    details = {}

    # ===== RSI =====
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if rsi < rsi_settings['oversold']:
            scores['BUY'] += weights['rsi']
            details['RSI'] = f"مفرط البيع ({rsi:.1f}) - المستوى {rsi_settings['oversold']} +{weights['rsi']}"
        elif rsi > rsi_settings['overbought']:
            scores['SELL'] += weights['rsi']
            details['RSI'] = f"مفرط الشراء ({rsi:.1f}) - المستوى {rsi_settings['overbought']} +{weights['rsi']}"
        else:
            details['RSI'] = f"محايد ({rsi:.1f})"

    # ===== MACD =====
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if not pd.isna(last['macd']) and not pd.isna(last['macd_signal']):
            if last['macd'] > last['macd_signal'] and last['macd'] > 0:
                scores['BUY'] += weights['macd']
                details['MACD'] = f"إيجابي ({macd_settings['fast']},{macd_settings['slow']},{macd_settings['signal']}) +{weights['macd']}"
            elif last['macd'] < last['macd_signal'] and last['macd'] < 0:
                scores['SELL'] += weights['macd']
                details['MACD'] = f"سلبي ({macd_settings['fast']},{macd_settings['slow']},{macd_settings['signal']}) +{weights['macd']}"
            else:
                details['MACD'] = "محايد"
        else:
            details['MACD'] = "بيانات غير كافية"

    # ===== MACD Histogram =====
    if 'macd_histogram' in df.columns and not pd.isna(last['macd_histogram']):
        if last['macd_histogram'] > 0 and last['macd_histogram'] > df['macd_histogram'].iloc[-3]:
            scores['BUY'] += weights['macd_hist']
            details['MACD_Hist'] = f"هيستوجرام صاعد +{weights['macd_hist']}"
        elif last['macd_histogram'] < 0 and last['macd_histogram'] < df['macd_histogram'].iloc[-3]:
            scores['SELL'] += weights['macd_hist']
            details['MACD_Hist'] = f"هيستوجرام هابط +{weights['macd_hist']}"
        else:
            details['MACD_Hist'] = "هيستوجرام محايد"

    # ===== Bollinger Bands =====
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
        if not pd.isna(last['bb_upper']) and not pd.isna(last['bb_lower']):
            if current_price <= last['bb_lower'] * 1.005:
                scores['BUY'] += weights['bb']
                details['BB'] = f"قرب الحد السفلي ({bb_settings['period']},{bb_settings['std_dev']}) +{weights['bb']}"
            elif current_price >= last['bb_upper'] * 0.995:
                scores['SELL'] += weights['bb']
                details['BB'] = f"قرب الحد الأعلى ({bb_settings['period']},{bb_settings['std_dev']}) +{weights['bb']}"
            else:
                details['BB'] = "وسط النطاق"
        else:
            details['BB'] = "بيانات غير كافية"

    # ===== VWAP =====
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += weights['vwap']
            details['VWAP'] = f"فوق VWAP +{weights['vwap']}"
        else:
            scores['SELL'] += weights['vwap']
            details['VWAP'] = f"تحت VWAP +{weights['vwap']}"

    # ===== ADX =====
    if 'adx' in df.columns and not pd.isna(last['adx']):
        if last['adx'] > 25:
            if df['close'].iloc[-1] > df['close'].iloc[-5]:
                scores['BUY'] += weights['adx']
                details['ADX'] = f"اتجاه قوي صاعد +{weights['adx']}"
            else:
                scores['SELL'] += weights['adx']
                details['ADX'] = f"اتجاه قوي هابط +{weights['adx']}"
        else:
            details['ADX'] = f"اتجاه ضعيف ({last['adx']:.1f})"

    # ===== Ichimoku =====
    if 'senkou_a' in df.columns and 'senkou_b' in df.columns:
        if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']):
            if current_price > last['senkou_a'] and current_price > last['senkou_b']:
                scores['BUY'] += weights['ichimoku']
                details['Ichimoku'] = f"فوق السحابة ({ichimoku_settings['tenkan']},{ichimoku_settings['kijun']},{ichimoku_settings['senkou']}) +{weights['ichimoku']}"
            elif current_price < last['senkou_a'] and current_price < last['senkou_b']:
                scores['SELL'] += weights['ichimoku']
                details['Ichimoku'] = f"تحت السحابة ({ichimoku_settings['tenkan']},{ichimoku_settings['kijun']},{ichimoku_settings['senkou']}) +{weights['ichimoku']}"
            else:
                details['Ichimoku'] = "داخل السحابة"

    # ===== MFI =====
    if 'mfi' in df.columns and not pd.isna(last['mfi']):
        mfi = last['mfi']
        if mfi < mfi_settings['oversold']:
            scores['BUY'] += weights['mfi']
            details['MFI'] = f"مفرط البيع ({mfi:.1f}) - المستوى {mfi_settings['oversold']} +{weights['mfi']}"
        elif mfi > mfi_settings['overbought']:
            scores['SELL'] += weights['mfi']
            details['MFI'] = f"مفرط الشراء ({mfi:.1f}) - المستوى {mfi_settings['overbought']} +{weights['mfi']}"
        else:
            details['MFI'] = f"محايد ({mfi:.1f})"

    # ===== Fibonacci =====
    recent_high = df['high'].iloc[-50:].max()
    recent_low = df['low'].iloc[-50:].min()
    fib_levels = calc_fibonacci_levels(recent_high, recent_low, current_price)
    if fib_levels:
        if current_price > fib_levels.get('fib_618', current_price):
            scores['BUY'] += weights['fibonacci']
            details['Fibonacci'] = f"فوق 0.618 +{weights['fibonacci']} BUY"
        elif current_price < fib_levels.get('fib_382', current_price):
            scores['SELL'] += weights['fibonacci']
            details['Fibonacci'] = f"تحت 0.382 +{weights['fibonacci']} SELL"
        else:
            details['Fibonacci'] = "منطقة وسط"

    # ===== SMC/SMR =====
    if last_smc.get('order_block_bullish', False):
        scores['BUY'] += weights['smc']
        details['SMC'] = f"كتلة أوامر شراء +{weights['smc']}"
    elif last_smc.get('order_block_bearish', False):
        scores['SELL'] += weights['smc']
        details['SMC'] = f"كتلة أوامر بيع +{weights['smc']}"
    elif last_smc.get('fvg_bullish', False):
        scores['BUY'] += weights['smc']//2
        details['SMC'] = f"FVG شراء +{weights['smc']//2}"
    elif last_smc.get('fvg_bearish', False):
        scores['SELL'] += weights['smc']//2
        details['SMC'] = f"FVG بيع +{weights['smc']//2}"
    elif last_smc.get('mss_bullish', False):
        scores['BUY'] += weights['smc']
        details['SMC'] = f"تحول هيكل صاعد +{weights['smc']}"
    elif last_smc.get('mss_bearish', False):
        scores['SELL'] += weights['smc']
        details['SMC'] = f"تحول هيكل هابط +{weights['smc']}"
    elif last_smc.get('in_discount', False):
        scores['BUY'] += weights['smc']//2
        details['SMC'] = f"منطقة خصم +{weights['smc']//2}"
    elif last_smc.get('in_premium', False):
        scores['SELL'] += weights['smc']//2
        details['SMC'] = f"منطقة قمة +{weights['smc']//2}"

    if last_smc.get('smr_bullish', False):
        scores['BUY'] += weights['smr']
        details['SMR'] = f"انعكاس Smart Money صاعد +{weights['smr']}"
    elif last_smc.get('smr_bearish', False):
        scores['SELL'] += weights['smr']
        details['SMR'] = f"انعكاس Smart Money هابط +{weights['smr']}"

    # ===== الأنماط الهيكلية =====
    if patterns:
        for p in patterns:
            if p['direction'] == 'BULLISH':
                scores['BUY'] += weights['patterns']
                details['Structure'] = f"{p['pattern']} (صاعد) +{weights['patterns']}"
            else:
                scores['SELL'] += weights['patterns']
                details['Structure'] = f"{p['pattern']} (هابط) +{weights['patterns']}"

    # ===== TBS =====
    if tbs_type == "BULLISH":
        scores['BUY'] += weights['tbs']
        details['TBS'] = f"TBS شراء (الدخول: {tbs_entry:.4f}) +{weights['tbs']}"
    elif tbs_type == "BEARISH":
        scores['SELL'] += weights['tbs']
        details['TBS'] = f"TBS بيع (الدخول: {tbs_entry:.4f}) +{weights['tbs']}"

    # ===== أنماط الشموع =====
    candle_patterns = detect_candlestick_patterns(df)
    for cp in candle_patterns:
        if cp['direction'] == 'BULLISH':
            scores['BUY'] += weights['candle']
            details[f"Candle_{cp['pattern']}"] = f"{cp['pattern']} (+{weights['candle']})"
        elif cp['direction'] == 'BEARISH':
            scores['SELL'] += weights['candle']
            details[f"Candle_{cp['pattern']}"] = f"{cp['pattern']} (+{weights['candle']})"
        else:
            details[f"Candle_{cp['pattern']}"] = f"{cp['pattern']} (محايد)"

    # ===== تباعد RSI =====
    div_type, div_score = detect_rsi_divergence(df)
    if div_type:
        if "BULLISH" in div_type:
            scores['BUY'] += weights['divergence']
            details['Divergence'] = f"{div_type} (+{weights['divergence']})"
        elif "BEARISH" in div_type:
            scores['SELL'] += weights['divergence']
            details['Divergence'] = f"{div_type} (+{weights['divergence']})"

    # ===== تكامل الأنماط الهيكلية مع الشموع (مصحح) =====
    if patterns and candle_patterns:
        try:
            last_struct = next((p for p in reversed(patterns) if p.get('direction') != 'NEUTRAL'), None)
            last_candle = next((c for c in reversed(candle_patterns) if c.get('direction') != 'NEUTRAL'), None)
            if last_struct is not None and last_candle is not None and last_struct.get('direction') == last_candle.get('direction'):
                bonus = weights['patterns'] // 2
                direction = last_struct.get('direction')
                if direction in scores:
                    scores[direction] += bonus
                else:
                    scores[direction] = bonus
                details['Confluence'] = f"تطابق {last_struct.get('pattern', '')} مع {last_candle.get('pattern', '')} (تأكيد مضاعف +{bonus})"
        except Exception as e:
            pass

    # ===== كتل الأوامر الطازجة =====
    is_fresh, fresh_dir = check_fresh_order_block(df_smc)
    if is_fresh and fresh_dir:
        scores[fresh_dir] += weights['fresh_ob']
        details['Fresh_OB'] = f"كتلة أوامر طازجة لصالح {fresh_dir} (+{weights['fresh_ob']})"

    # ===== Currency Strength =====
    if symbol in PAIRS.values():
        currency_strength = get_currency_strength()
        if currency_strength:
            pair_name = symbol_name
            currencies = pair_name.split("/") if "/" in pair_name else []
            
            if len(currencies) == 2:
                base = currencies[0]
                quote = currencies[1]
                base_strength = currency_strength.get(base, 0)
                quote_strength = currency_strength.get(quote, 0)
                
                net_score_temp = scores['BUY'] - scores['SELL']
                if net_score_temp >= 5:
                    temp_signal = "BUY"
                elif net_score_temp <= -5:
                    temp_signal = "SELL"
                else:
                    temp_signal = "WAIT"
                
                if temp_signal == "BUY" and base_strength < quote_strength:
                    scores['BUY'] -= 1
                    details['Currency_Strength'] = f"⚠️ {base} أضعف من {quote} (-1 BUY)"
                elif temp_signal == "SELL" and quote_strength < base_strength:
                    scores['SELL'] -= 1
                    details['Currency_Strength'] = f"⚠️ {quote} أضعف من {base} (-1 SELL)"
                elif temp_signal == "BUY" and base_strength > quote_strength + 0.5:
                    scores['BUY'] += 1
                    details['Currency_Strength'] = f"✅ {base} قوي مقابل {quote} (+1 BUY)"
                elif temp_signal == "SELL" and quote_strength > base_strength + 0.5:
                    scores['SELL'] += 1
                    details['Currency_Strength'] = f"✅ {quote} قوي مقابل {base} (+1 SELL)"

    # ===== النتيجة الأولية =====
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

    # ===== MTF Filter =====
    mtf_signal = "NEUTRAL"
    mtf_count = 0
    if symbol and symbol != "":
        try:
            mtf_signal, mtf_count = get_mtf_signal(symbol, current_price)
        except:
            mtf_signal = "NEUTRAL"
            mtf_count = 0
    
    if signal != "WAIT" and mtf_signal != "NEUTRAL":
        if signal != mtf_signal:
            confidence = confidence * 0.7
            details['MTF_Filter'] = f"⚠️ تعارض مع MTF ({mtf_signal}) ثقة ×0.7"
        else:
            confidence = min(100, confidence * 1.1)
            details['MTF_Filter'] = f"✅ متوافق مع MTF ({mtf_signal}) +10% ثقة"

    # ===== News Impact =====
    news_impact_score = 0
    news_details = ""
    try:
        news = get_fmp_news()
        if news:
            news_analysis = analyze_news_impact(news)
            st.session_state.news_analysis = news_analysis
            news_impact_score, news_details = get_news_impact_score(news_analysis, symbol)
            
            if signal != "WAIT" and abs(news_impact_score) > 10:
                if (signal == "BUY" and news_impact_score > 0) or (signal == "SELL" and news_impact_score < 0):
                    confidence = min(100, confidence * 1.1)
                    details['News_Impact'] = f"✅ الأخبار تدعم الإشارة ({news_impact_score:+.0f}) +10% ثقة"
                elif (signal == "BUY" and news_impact_score < 0) or (signal == "SELL" and news_impact_score > 0):
                    confidence = confidence * 0.8
                    details['News_Impact'] = f"⚠️ الأخبار تعارض الإشارة ({news_impact_score:+.0f}) ×0.8 ثقة"
            elif news_impact_score != 0:
                details['News_Impact'] = f"📰 تأثير الأخبار: {news_impact_score:+.0f}"
    except:
        pass

    # ===== Trend Filter =====
    major_trend = get_major_trend(df)
    if signal != "WAIT":
        if signal == "BUY" and major_trend == "BEARISH":
            confidence = confidence * 0.6
            details['Trend_Filter'] = "⚠️ شراء مع اتجاه رئيسي هابط (ثقة ×0.6)"
        elif signal == "SELL" and major_trend == "BULLISH":
            confidence = confidence * 0.6
            details['Trend_Filter'] = "⚠️ بيع مع اتجاه رئيسي صاعد (ثقة ×0.6)"
        elif (signal == "BUY" and major_trend == "BULLISH") or (signal == "SELL" and major_trend == "BEARISH"):
            confidence = min(100, confidence * 1.15)
            details['Trend_Filter'] = f"✅ متوافق مع الاتجاه الرئيسي ({major_trend}) +15% ثقة"

    # ===== Killzone =====
    killzone, kz_bonus = is_ict_killzone()
    if killzone and signal != "WAIT":
        confidence = min(100, confidence + kz_bonus * 2)
        details['ICT_Killzone'] = f"إشارة داخل منطقة {killzone} (+{kz_bonus*2}% ثقة)"

    # ===== Session Filter =====
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    hour = now.hour
    if 16 <= hour < 17:
        confidence = confidence * 0.85
        details['Session_Filter'] = "⚠️ آخر ساعة قبل الإغلاق (سيولة منخفضة) ×0.85"
    elif 9 <= hour < 11:
        confidence = min(100, confidence * 1.05)
        details['Session_Filter'] = "✅ ذروة السيولة في نيويورك +5% ثقة"

    # ===== ATR Filter =====
    if 'atr' in df.columns and len(df) > 50:
        current_atr = last['atr']
        avg_atr = df['atr'].iloc[-50:].mean()
        if not pd.isna(current_atr) and not pd.isna(avg_atr):
            if current_atr < avg_atr * 0.7:
                confidence = confidence * 0.6
                details['ATR_Filter'] = "⚠️ تقلب منخفض (إشارة ضعيفة ×0.6)"

    # ===== Weak Signal Filter =====
    if signal != "WAIT":
        has_strong_signal = False
        if last_smc.get('order_block_bullish', False) or last_smc.get('order_block_bearish', False):
            has_strong_signal = True
        if patterns:
            for p in patterns:
                if p['score'] >= 4:
                    has_strong_signal = True
        if not has_strong_signal and confidence < 70:
            confidence = confidence * 0.8
            details['Weak_Signal_Filter'] = "⚠️ إشارة ضعيفة بدون دعم قوي ×0.8"

    confidence = max(0, min(100, confidence))
    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)

    # ===== Stop Loss & Targets =====
    stop_loss = None
    entry_price = None
    targets = {}
    
    if signal in ["BUY", "SELL"] and confidence >= 60:
        atr_value = last['atr'] if not pd.isna(last['atr']) else 10
        entry_price = current_price
        
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
            targets = {
                'target1': entry_price + risk * 1.0,
                'target2': entry_price + risk * 1.5,
                'target3': entry_price + risk * 2.0,
                'risk_reward_1': 1.0,
                'risk_reward_2': 1.5,
                'risk_reward_3': 2.0,
                'risk': risk
            }
        else:
            targets = {
                'target1': entry_price - risk * 1.0,
                'target2': entry_price - risk * 1.5,
                'target3': entry_price - risk * 2.0,
                'risk_reward_1': 1.0,
                'risk_reward_2': 1.5,
                'risk_reward_3': 2.0,
                'risk': risk
            }

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
                    "target1": targets.get('target1'),
                    "target2": targets.get('target2'),
                    "target3": targets.get('target3'),
                    "risk_reward": f"1:{targets.get('risk_reward_3', 0):.1f}"
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
        explanation += f"- النتيجة الصافية {net_score} بين -5 و +5 (لا يوجد إجماع).\n- تفاصيل النقاط:\n"
        for k, v in details.items():
            if v:
                explanation += f"  - {k}: {v}\n"
        explanation += "💡 **نصيحة**: انتظر حتى تتجاوز النتيجة ±5 أو تتحسن الثقة فوق 60%."
    
    if stop_loss and entry_price and targets:
        explanation += f"\n\n📍 **سعر الدخول المقترح:** {entry_price:.4f}"
        explanation += f"\n🛑 **وقف الخسارة:** {stop_loss:.4f} (المسافة: {abs(entry_price - stop_loss):.4f})"
        explanation += f"\n🎯 **الأهداف:**"
        explanation += f"\n   - الهدف 1 (1:1): {targets['target1']:.4f}"
        explanation += f"\n   - الهدف 2 (1:1.5): {targets['target2']:.4f}"
        explanation += f"\n   - الهدف 3 (1:2): {targets['target3']:.4f}"
    
    explanation += f"\n\n🕒 **تحليل الأطر الزمنية**: {mtf_signal} (عدد الأطر: {mtf_count})"
    if mtf_signal != "NEUTRAL":
        explanation += f"\n📊 **إجماع MTF**: {mtf_count} إطار زمني متفق مع الإشارة"
    
    if patterns:
        explanation += "\n\n📐 **النماذج المكتشفة:**\n"
        for p in patterns:
            explanation += f"- {p['pattern']} ({p['direction']}) - قوة: {p['score']}/5\n"
    
    if tbs_info and tbs_info[0]:
        tbs_type, tbs_entry, tbs_stop, tbs_level = tbs_info
        if tbs_type:
            explanation += f"\n\n🐢 **TBS (Turtle Body Soup) مكتشف:** {tbs_type}\n"
            if tbs_level:
                explanation += f"   - المستوى القديم المُختَرق: {tbs_level:.4f}\n"
            if tbs_entry:
                explanation += f"   - سعر الدخول المقترح: {tbs_entry:.4f}\n"
            if tbs_stop:
                explanation += f"   - وقف الخسارة: {tbs_stop:.4f}\n"

    if 'News_Impact' in details:
        explanation += f"\n\n📰 **تأثير الأخبار:** {details['News_Impact']}"

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
    risk_reward = f"1:{targets['risk_reward_3']:.1f}"
    
    st.markdown(f"""
    <div class="suggested-trade">
        <b>الاتجاه:</b> {direction_text} (الثقة: {confidence:.0f}%)<br>
        <b>📍 سعر الدخول المقترح:</b> {price_format.format(entry_price)}<br>
        <b>🛑 وقف الخسارة:</b> {price_format.format(stop_loss)} (المسافة: {abs(entry_price - stop_loss):.2f} نقطة)<br>
        <div class="target-zone"><b>🎯 الهدف 1 (1:1):</b> {price_format.format(targets['target1'])}</div>
        <div class="target-zone" style="border-left-color: #ffaa00;"><b>🎯 الهدف 2 (1:1.5):</b> {price_format.format(targets['target2'])}</div>
        <div class="target-zone" style="border-left-color: #00ff88;"><b>🎯 الهدف 3 (1:2):</b> {price_format.format(targets['target3'])}</div>
        <b>📈 نسبة المخاطرة/المكافأة القصوى:</b> {risk_reward}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➕ إضافة هذه الصفقة", key="add_suggested_trade", width='stretch'):
        trade_manager = TradeManager()
        account_balance = 100000
        risk_per_trade_pct = 2
        risk_per_trade = account_balance * (risk_per_trade_pct / 100)
        risk_amount = abs(entry_price - stop_loss)
        lot_size = risk_per_trade / (risk_amount * 100) if risk_amount > 0 else 0.01
        lot_size = round(lot_size, 2)
        
        trailing_dist = last['atr'] * 0.3 if 'atr' in last and not pd.isna(last['atr']) else (3 if "Gold" in selected_pair_name else 0.0003)
        
        trade_data = {
            "direction": signal,
            "entry": entry_price,
            "lots": max(lot_size, 0.01),
            "stop_loss": stop_loss,
            "take_profit": targets['target2'],
            "trailing_enabled": True,
            "trailing_distance": trailing_dist,
            "notes": f"مقترحة من الإشارة المتكاملة (الثقة {confidence:.0f}%)"
        }
        trade_id = trade_manager.add_trade(trade_data)
        st.success(f"✅ تم إضافة الصفقة {trade_id} بنجاح!")
        st.rerun()

else:
    st.info("⏳ لا توجد صفقة مقترحة حالياً (انتظر إشارة قوية)")

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
            st.session_state.news_analysis = analyze_news_impact(news)
        else:
            st.session_state.news_analysis = None

if st.session_state.news_analysis:
    display_news_analysis(st.session_state.news_analysis)
    
    if signal != "WAIT":
        news_impact, _ = get_news_impact_score(st.session_state.news_analysis, selected_symbol)
        if abs(news_impact) > 10:
            if (signal == "BUY" and news_impact > 0) or (signal == "SELL" and news_impact < 0):
                st.success(f"✅ الأخبار تدعم قرار {signal} (تأثير: {news_impact:+.0f})")
            else:
                st.warning(f"⚠️ الأخبار تعارض قرار {signal} (تأثير: {news_impact:+.0f})")
        else:
            st.info(f"📰 تأثير الأخبار محايد ({news_impact:+.0f})")
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
# تحليل ارتباط الأزواج بالذهب
# ==========================================
st.markdown("---")
st.markdown("### 📊 ارتباط الأزواج بالذهب")

if st.button("🔄 تحليل ارتباط الأزواج بالذهب", key="analyze_gold_correlation", width='stretch'):
    with st.spinner("جارٍ التحليل..."):
        gold_symbol = "GC=F"
        correlation_results = []
        
        for pair_name, symbol in PAIRS.items():
            if symbol != gold_symbol and "Gold" not in pair_name and "Silver" not in pair_name:
                corr = get_pair_correlation(gold_symbol, symbol)
                if corr is not None:
                    correlation_results.append({
                        "الزوج": pair_name,
                        "الارتباط بالذهب": corr,
                        "القوة": "قوي" if abs(corr) > 0.7 else ("متوسط" if abs(corr) > 0.4 else "ضعيف"),
                        "الاتجاه": "نفس" if corr > 0 else "عكس"
                    })
        
        if correlation_results:
            df_corr = pd.DataFrame(correlation_results)
            df_corr = df_corr.sort_values("الارتباط بالذهب", ascending=False)
            
            st.dataframe(
                df_corr,
                column_config={
                    "الزوج": st.column_config.TextColumn("الزوج"),
                    "الارتباط بالذهب": st.column_config.NumberColumn("الارتباط", format="%.3f"),
                    "القوة": st.column_config.TextColumn("القوة"),
                    "الاتجاه": st.column_config.TextColumn("الاتجاه")
                },
                hide_index=True,
                use_container_width=True
            )
            
            fig_gold_corr = go.Figure()
            fig_gold_corr.add_trace(go.Bar(
                x=df_corr["الزوج"],
                y=df_corr["الارتباط بالذهب"],
                marker_color=['#00ff88' if val > 0 else '#ff4444' for val in df_corr["الارتباط بالذهب"]],
                text=[f"{val:.3f}" for val in df_corr["الارتباط بالذهب"]],
                textposition='outside'
            ))
            fig_gold_corr.update_layout(
                height=400,
                template='plotly_dark',
                title="ارتباط الأزواج بالذهب",
                xaxis_title="الزوج",
                yaxis_title="معامل الارتباط",
                yaxis=dict(range=[-1, 1])
            )
            st.plotly_chart(fig_gold_corr, use_container_width=True)
            
            if correlation_results:
                max_pos = max([r for r in correlation_results if r["الارتباط بالذهب"] > 0], key=lambda x: x["الارتباط بالذهب"]) if any(r["الارتباط بالذهب"] > 0 for r in correlation_results) else None
                max_neg = min([r for r in correlation_results if r["الارتباط بالذهب"] < 0], key=lambda x: x["الارتباط بالذهب"]) if any(r["الارتباط بالذهب"] < 0 for r in correlation_results) else None
                
                if max_pos:
                    st.info(f"🟢 أقوى ارتباط موجب: **{max_pos['الزوج']}** ({max_pos['الارتباط بالذهب']:.3f}) - يتحرك بنفس اتجاه الذهب")
                if max_neg:
                    st.info(f"🔴 أقوى ارتباط سالب: **{max_neg['الزوج']}** ({max_neg['الارتباط بالذهب']:.3f}) - يتحرك بعكس اتجاه الذهب")
        else:
            st.info("لا توجد بيانات كافية لحساب الارتباطات")

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
    SMC/ICT • Liquidity (BSL/SSL) • SMR • Patterns (HS, Double, Triple, Wedge, Flag) • TBS • MTF • Divergence • Candlestick • Killzones • Fibonacci • Currency Strength • Correlation Analysis • Economic Calendar • News Analysis • Dynamic Settings • Integrated Signals & Trade Management
</div>
""", unsafe_allow_html=True)
