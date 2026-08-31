# ==========================================
# BLACK PYRAMID – الإصدار 2002 (النسخة النهائية مع التحديثات الهرمية والتخفيفات)
# تاريخ التحديث: 2026-08-31
# المصدر: Twelve Data (رئيسي) + FastForex + GoldAPI + yfinance (احتياطي)
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
# API Keys
# ==========================================
GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
FMP_API_KEY = "EBdaCkJXtIphxCdiZpW3EWCAb4IKpz8N"
TWELVE_API_KEY = "b46ffed1c34b4a89ac203bc5c0756fd8"  # المفتاح الجديد
FASTFOREX_API_KEY = "4cd179a14f-a982d5aedd-tkn80n"  # مفتاح Fast Forex

# Telegram Config (اختياري)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ==========================================
# الهوية البصرية
# ==========================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #ffd700;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffd700;
        text-align: center;
        text-shadow: 0 0 10px #ffd700;
    }
    .main-subtitle {
        color: #ccc;
        text-align: center;
        font-size: 1rem;
        margin-top: 5px;
    }
    .price-card {
        background: #1a1a2e;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #ffd700;
    }
    .price-label {
        color: #aaa;
        font-size: 0.9rem;
    }
    .price-value {
        font-size: 2rem;
        font-weight: bold;
        color: #fff;
    }
    .price-change {
        font-size: 1rem;
        margin-top: 5px;
    }
    .signal-box {
        background: #1a1a2e;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 15px 0;
        border: 2px solid #ffd700;
    }
    .signal-text {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .signal-confidence {
        font-size: 1.2rem;
        color: #ccc;
        margin-top: 10px;
    }
    .suggested-trade {
        background: #1a1a2e;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #00ff88;
    }
    .target-zone {
        background: #16213e;
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #ffd700;
    }
    .pattern-badge {
        display: inline-block;
        background: #2a2a4a;
        padding: 5px 10px;
        border-radius: 15px;
        margin: 3px;
        font-size: 0.85rem;
    }
    .explanation-box {
        background: #0f0f1a;
        padding: 15px;
        border-radius: 8px;
        white-space: pre-line;
        font-family: monospace;
        color: #ddd;
    }
    .trade-row {
        background: #1a1a2e;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 3px solid #ffaa00;
    }
    .reversal-alert {
        background: #2a1a1a;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #ff4444;
        margin: 5px 0;
    }
    .news-card {
        background: #1a1a2e;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .footer {
        text-align: center;
        margin-top: 30px;
        padding: 15px;
        color: #aaa;
        font-size: 0.8rem;
        border-top: 1px solid #333;
    }
    .brand {
        color: #ffd700;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">▲ BLACK PYRAMID ▲</div>
        <div class="main-subtitle">Advanced Trading Intelligence • Multi-Timeframe (4H/Daily) • SMC/ICT • Liquidity • SMR • Patterns • TBS • MTF • Divergence • Candlestick • Killzones • Currency Strength • Economic Calendar • News Analysis</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
if "currency_strength" not in st.session_state:
    st.session_state.currency_strength = None
if "economic_events" not in st.session_state:
    st.session_state.economic_events = None
if "news_analysis" not in st.session_state:
    st.session_state.news_analysis = None
if "data_errors" not in st.session_state:
    st.session_state.data_errors = []
if "failed_indicators" not in st.session_state:
    st.session_state.failed_indicators = []
if "indicator_status" not in st.session_state:
    st.session_state.indicator_status = {}

# ==========================================
# قائمة الأزواج وخريطة Twelve Data
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

TWELVE_SYMBOL_MAP = {
    "GC=F": "XAU/USD",
    "SI=F": "XAG/USD",
    "DX-Y.NYB": "DXY",
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "USDCHF=X": "USD/CHF",
    "AUDUSD=X": "AUD/USD",
    "NZDUSD=X": "NZD/USD",
    "USDCAD=X": "USD/CAD",
    "EURGBP=X": "EUR/GBP",
    "EURJPY=X": "EUR/JPY",
    "EURCHF=X": "EUR/CHF",
    "EURAUD=X": "EUR/AUD",
    "EURNZD=X": "EUR/NZD",
    "EURCAD=X": "EUR/CAD",
    "GBPJPY=X": "GBP/JPY",
    "GBPCHF=X": "GBP/CHF",
    "GBPAUD=X": "GBP/AUD",
    "GBPNZD=X": "GBP/NZD",
    "GBPCAD=X": "GBP/CAD",
    "AUDJPY=X": "AUD/JPY",
    "AUDCHF=X": "AUD/CHF",
    "AUDNZD=X": "AUD/NZD",
    "AUDCAD=X": "AUD/CAD",
    "NZDJPY=X": "NZD/JPY",
    "NZDCHF=X": "NZD/CHF",
    "NZDCAD=X": "NZD/CAD",
    "CADJPY=X": "CAD/JPY",
    "CADCHF=X": "CAD/CHF",
    "BTC-USD": "BTC/USD",
    "ETH-USD": "ETH/USD"
}

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
# دوال Twelve Data
# ==========================================
def get_twelvedata_price(symbol_key):
    td_symbol = TWELVE_SYMBOL_MAP.get(symbol_key, symbol_key)
    url = f"https://api.twelvedata.com/price?symbol={td_symbol}&apikey={TWELVE_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'price' in data and data['price'] is not None:
                return float(data['price'])
    except:
        pass
    return None

def get_fastforex_price(symbol_key):
    """جلب سعر الصرف من Fast Forex API"""
    iso = symbol_key.replace("=X", "")
    if "/" in iso:
        iso = iso.replace("/", "")
    if len(iso) != 6:
        return None
    base = iso[:3]
    quote = iso[3:]
    url = f"https://api.fastforex.io/fetch-one?from={base}&to={quote}&api_key={FASTFOREX_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                return float(data['result'])
    except:
        pass
    return None

def get_twelvedata_historical(symbol_key, interval="1h", outputsize=500):
    td_symbol = TWELVE_SYMBOL_MAP.get(symbol_key, symbol_key)
    interval_map = {
        "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
        "1h": "1h", "4h": "4h", "1d": "1day", "1mo": "1day"
    }
    td_interval = interval_map.get(interval, "1h")
    url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={td_interval}&outputsize={outputsize}&apikey={TWELVE_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'values' in data and data['values']:
                df = pd.DataFrame(data['values'])
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.set_index('datetime')
                df = df.astype(float)
                df.columns = ['open', 'high', 'low', 'close', 'volume']
                df = df.sort_index()
                return df
    except:
        pass
    return None

@st.cache_data(ttl=30)
def get_spot_price(symbol="GC=F"):
    errors = []
    # Twelve Data
    try:
        price = get_twelvedata_price(symbol)
        if price is not None:
            return price, 0.0
    except Exception as e:
        errors.append(f"TwelveData: {e}")
    # Fast Forex للأزواج
    if symbol not in ["GC=F", "SI=F", "BTC-USD", "ETH-USD"] and "=X" in symbol:
        try:
            price = get_fastforex_price(symbol)
            if price is not None:
                return price, 0.0
        except Exception as e:
            errors.append(f"FastForex: {e}")
    # GoldAPI للذهب والفضة
    if symbol == "GC=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('price', 0))
                change = float(data.get('change_percent', 0))
                return price, change
        except Exception as e:
            errors.append(f"GoldAPI XAU: {e}")
    if symbol == "SI=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAG/USD"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('price', 0))
                change = float(data.get('change_percent', 0))
                return price, change
        except Exception as e:
            errors.append(f"GoldAPI XAG: {e}")
    # yfinance
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="5m")
        if not data.empty:
            last = data.iloc[-1]
            first = data.iloc[0]
            change = ((last['Close'] - first['Close']) / first['Close']) * 100 if first['Close'] != 0 else 0
            return float(last['Close']), float(change)
    except Exception as e:
        errors.append(f"yfinance: {e}")
    st.session_state.data_errors = errors
    return None, None

@st.cache_data(ttl=300)
def get_historical_data(symbol, period="3mo", interval="4h", max_retries=3):
    """جلب البيانات التاريخية – الإطار الأساسي الآن 4 ساعات"""
    output_size = 500
    if period == "5d":
        output_size = 50
    elif period == "1mo":
        output_size = 200
    elif period == "3mo":
        output_size = 500
    elif period == "6mo":
        output_size = 1000
    # Twelve Data
    try:
        df = get_twelvedata_historical(symbol, interval, output_size)
        if df is not None and len(df) > 50:
            return df
    except:
        pass
    # yfinance
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
            except:
                continue
        if attempt < max_retries - 1:
            time.sleep(2)
    return None

# ==========================================
# دوال البيانات الأخرى
# ==========================================
@st.cache_data(ttl=30)
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
    symbols_list = [TWELVE_SYMBOL_MAP.get(sym, sym) for sym in main_symbols.values()]
    symbols_str = ",".join(symbols_list)
    url = f"https://api.twelvedata.com/price?symbol={symbols_str}&apikey={TWELVE_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data:
                    if 'symbol' in item and 'price' in item:
                        for name, sym in main_symbols.items():
                            if TWELVE_SYMBOL_MAP.get(sym, sym) == item['symbol']:
                                results[name] = {'price': float(item['price']), 'change': 0.0}
                                break
    except:
        pass
    for name, symbol in main_symbols.items():
        if name not in results:
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
    all_pairs = []
    for pairs in CURRENCY_INDICES.values():
        all_pairs.extend(pairs)
    all_pairs = list(set(all_pairs))
    symbols_list = [TWELVE_SYMBOL_MAP.get(pair, pair) for pair in all_pairs if pair in TWELVE_SYMBOL_MAP]
    if not symbols_list:
        return {}
    prices = {}
    for i in range(0, len(symbols_list), 8):
        chunk = symbols_list[i:i+8]
        symbols_str = ",".join(chunk)
        url = f"https://api.twelvedata.com/price?symbol={symbols_str}&apikey={TWELVE_API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        if 'symbol' in item and 'price' in item:
                            prices[item['symbol']] = float(item['price'])
        except:
            pass
    for currency, pairs in CURRENCY_INDICES.items():
        changes = []
        for pair in pairs:
            td_sym = TWELVE_SYMBOL_MAP.get(pair, pair)
            if td_sym in prices:
                try:
                    df = get_twelvedata_historical(pair, interval="1h", outputsize=24)
                    if df is not None and len(df) > 1:
                        last = df['close'].iloc[-1]
                        first = df['close'].iloc[0]
                        change = ((last - first) / first) * 100 if first != 0 else 0
                        if pair.split('=')[0].startswith(currency):
                            changes.append(change)
                        else:
                            changes.append(-change)
                except:
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
            df = get_twelvedata_historical(pair, interval="4h", outputsize=100)
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
        df1 = get_twelvedata_historical(symbol1, interval="4h", outputsize=100)
        df2 = get_twelvedata_historical(symbol2, interval="4h", outputsize=100)
        if df1 is not None and df2 is not None and not df1.empty and not df2.empty:
            df1_aligned = df1['close'].reindex(df2.index, method='nearest')
            return round(df1_aligned.corr(df2['close']), 3)
    except:
        pass
    return None

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

def calc_mfi(df, period=14):
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    money_flow = typical_price * df['volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(), 0).rolling(window=period).sum()
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    return mfi

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

def calc_chaikin_money_flow(high, low, close, volume, period=21):
    mf_multiplier = ((close - low) - (high - close)) / (high - low)
    mf_volume = mf_multiplier * volume
    return mf_volume.rolling(window=period).sum() / volume.rolling(window=period).sum()

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
    patterns = []
    if len(df) < 3:
        return patterns
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    body = abs(last['close'] - last['open'])
    total_range = last['high'] - last['low']
    if (prev['close'] < prev['open'] and last['close'] > last['open'] and last['open'] < prev['close'] and last['close'] > prev['open']):
        patterns.append({"pattern": "BULLISH_ENGULFING", "direction": "BULLISH", "score": 3})
    if (prev['close'] > prev['open'] and last['close'] < last['open'] and last['open'] > prev['close'] and last['close'] < prev['open']):
        patterns.append({"pattern": "BEARISH_ENGULFING", "direction": "BEARISH", "score": 3})
    lower_wick = min(last['close'], last['open']) - last['low']
    upper_wick = last['high'] - max(last['close'], last['open'])
    if body > 0 and lower_wick > body * 2 and upper_wick < body * 0.3:
        patterns.append({"pattern": "HAMMER", "direction": "BULLISH", "score": 2})
    if body > 0 and upper_wick > body * 2 and lower_wick < body * 0.3:
        patterns.append({"pattern": "SHOOTING_STAR", "direction": "BEARISH", "score": 2})
    if total_range > 0 and body < total_range * 0.15:
        patterns.append({"pattern": "DOJI", "direction": "NEUTRAL", "score": 1})
    if (prev2['close'] < prev2['open'] and abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and
        last['close'] > last['open'] and last['close'] > (prev2['open'] + prev2['close']) / 2):
        patterns.append({"pattern": "MORNING_STAR", "direction": "BULLISH", "score": 4})
    if (prev2['close'] > prev2['open'] and abs(prev['close'] - prev['open']) < abs(prev2['close'] - prev2['open']) * 0.3 and
        last['close'] < last['open'] and last['close'] < (prev2['open'] + prev2['close']) / 2):
        patterns.append({"pattern": "EVENING_STAR", "direction": "BEARISH", "score": 4})
    return patterns

def detect_rsi_divergence(df, rsi_column='rsi', lookback=20):
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
    if len(df) < 200:
        return "NEUTRAL"
    ema200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1]
    price = df['close'].iloc[-1]
    if price > ema200 * 1.01:
        return "BULLISH"
    elif price < ema200 * 0.99:
        return "BEARISH"
    return "NEUTRAL"

# ==========================================
# دوال MTF
# ==========================================
def get_mtf_signal(symbol, current_price):
    timeframes = ['15min', '1h', '4h', '1day']
    signals = []
    weights = {'15min': 1, '1h': 2, '4h': 3, '1day': 4}
    for tf in timeframes:
        try:
            df = get_twelvedata_historical(symbol, interval=tf, outputsize=100)
            if df is not None and len(df) > 50:
                rsi = calc_rsi(df['close']).iloc[-1]
                if rsi < 30:
                    signals.append(('BUY', tf, weights[tf]))
                elif rsi > 70:
                    signals.append(('SELL', tf, weights[tf]))
                else:
                    signals.append(('NEUTRAL', tf, 0))
        except:
            try:
                interval_map = {"15min": "15m", "1h": "1h", "4h": "4h", "1day": "1d"}
                df = get_historical_data(symbol, period="1mo", interval=interval_map.get(tf, "1h"))
                if df is not None and len(df) > 50:
                    rsi = calc_rsi(df['close']).iloc[-1]
                    if rsi < 30:
                        signals.append(('BUY', tf, weights[tf]))
                    elif rsi > 70:
                        signals.append(('SELL', tf, weights[tf]))
                    else:
                        signals.append(('NEUTRAL', tf, 0))
            except:
                signals.append(('NEUTRAL', tf, 0))
    buy_weight = sum(w for s, tf, w in signals if s == 'BUY')
    sell_weight = sum(w for s, tf, w in signals if s == 'SELL')
    if buy_weight > sell_weight:
        return "BUY", buy_weight
    elif sell_weight > buy_weight:
        return "SELL", sell_weight
    else:
        return "NEUTRAL", 0

def get_daily_trend(symbol):
    try:
        df = get_twelvedata_historical(symbol, interval="1day", outputsize=50)
        if df is not None and len(df) > 20:
            ema50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            price = df['close'].iloc[-1]
            if price > ema50 * 1.01:
                return "BULLISH"
            elif price < ema50 * 0.99:
                return "BEARISH"
    except:
        pass
    return "NEUTRAL"

def confirm_signal(df, signal, bars=1):  # تم تخفيف التأكيد إلى شمعة واحدة
    if len(df) < bars:
        return False
    for i in range(1, bars+1):
        if signal == "BUY":
            if df['close'].iloc[-i] < df['open'].iloc[-i]:
                return False
        elif signal == "SELL":
            if df['close'].iloc[-i] > df['open'].iloc[-i]:
                return False
    return True

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
    except:
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
    except:
        pass
    return []

# ==========================================
# تحليل الأخبار
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
            icon = "🔴" if impact_level == "عالٍ" else ("🟡" if impact_level == "متوسط" else "🟢")
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">{icon} {item.get('title', '')[:100]}...</div>
                <div class="news-date">{item.get('source', '')} | التأثير: {impact_level} ({impact:+.0f}) | {item.get('date', '')}</div>
            </div>
            """, unsafe_allow_html=True)

def display_economic_events(events):
    if not events:
        st.info("لا توجد أحداث اقتصادية")
        return
    for event in events[:15]:
        impact = event.get('impact', '')
        impact_icon = "🔴" if impact in ['High', 'عالٍ'] else ("🟡" if impact in ['Medium', 'متوسط'] else "
                impact_icon = "🔴" if impact in ['High', 'عالٍ'] else ("🟡" if impact in ['Medium', 'متوسط'] else "🟢")
        impact_class = "event-high" if impact in ['High', 'عالٍ'] else ("event-medium" if impact in ['Medium', 'متوسط'] else "event-low")
        st.markdown(f"""
        <div class="news-card {impact_class}">
            <div class="news-title">{impact_icon} <b>{event.get('country', '')}</b> - {event.get('event', '')}</div>
            <div class="news-date">🕐 {event.get('date', '')} {event.get('time', '')} | التوقع: {event.get('forecast', 'N/A')} | السابق: {event.get('previous', 'N/A')} | الفعلي: {event.get('actual', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# دوال التنبيهات وحجم الصفقة
# ==========================================
def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        return response.status_code == 200
    except:
        return False

def calculate_lot_size(entry_price, stop_loss, account_balance=100000, risk_percent=1.0, pip_value=10):
    risk_amount = account_balance * (risk_percent / 100)
    stop_distance = abs(entry_price - stop_loss)
    if stop_distance == 0:
        return 0.01
    lot_size = risk_amount / (stop_distance * 100000 * pip_value / 100)
    lot_size = max(0.01, round(lot_size, 2))
    return lot_size

# ==========================================
# إعدادات المؤشرات والأوزان
# ==========================================
def get_indicator_settings(symbol_name):
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
        'ichimoku': {},
        'atr_period': 14
    }
    if asset_type == "gold":
        settings['macd'] = {'fast': 5, 'slow': 13, 'signal': 4}
        settings['rsi'] = {'period': 14, 'overbought': 80, 'oversold': 20}
        settings['mfi'] = {'period': 9, 'overbought': 80, 'oversold': 20}
        settings['bb'] = {'period': 20, 'std_dev': 2.5}
        settings['ichimoku'] = {'tenkan': 10, 'kijun': 30, 'senkou': 60}
    elif asset_type == "crypto":
        settings['macd'] = {'fast': 6, 'slow': 13, 'signal': 5}
        settings['rsi'] = {'period': 14, 'overbought': 80, 'oversold': 20}
        settings['mfi'] = {'period': 10, 'overbought': 85, 'oversold': 15}
        settings['bb'] = {'period': 50, 'std_dev': 2.3}
        settings['ichimoku'] = {'tenkan': 10, 'kijun': 30, 'senkou': 60}
    else:
        settings['macd'] = {'fast': 12, 'slow': 26, 'signal': 9}
        settings['rsi'] = {'period': 14, 'overbought': 70, 'oversold': 30}
        settings['mfi'] = {'period': 14, 'overbought': 80, 'oversold': 20}
        settings['bb'] = {'period': 20, 'std_dev': 2}
        settings['ichimoku'] = {'tenkan': 9, 'kijun': 26, 'senkou': 52}
    return settings

def get_dynamic_weights(df, asset_type="forex"):
    weights = {
        'rsi': 2, 'macd': 3, 'bb': 2, 'vwap': 2,
        'ichimoku': 3, 'smc': 5, 'patterns': 5, 'tbs': 5,
        'mfi': 2, 'smr': 4, 'candle': 3, 'divergence': 5,
        'fresh_ob': 4, 'fibonacci': 3,
        'chaikin': 2
    }
    if asset_type == "gold":
        weights.update({'ichimoku': 3, 'smc': 5, 'tbs': 5, 'mfi': 2, 'chaikin': 2})
    elif asset_type == "crypto":
        weights.update({'ichimoku': 4, 'smc': 5, 'tbs': 5, 'mfi': 2, 'chaikin': 2})
    else:
        weights.update({'ichimoku': 3, 'smc': 4, 'tbs': 5, 'mfi': 2, 'chaikin': 2})
    return weights

# ==========================================
# دالة الإشارة المتكاملة (مع التخفيفات)
# ==========================================
def generate_advanced_signal(df, current_price, symbol_name="", symbol=""):
    if df is None or len(df) < 50:  # خفض الحد الأدنى من 100 إلى 50
        return "WAIT", 50, 0, {}, [], None, None, None, None, {}

    indicator_status = {}

    settings = get_indicator_settings(symbol_name)
    asset_type = settings['asset_type']
    macd_settings = settings['macd']
    rsi_settings = settings['rsi']
    mfi_settings = settings['mfi']
    bb_settings = settings['bb']
    ichimoku_settings = settings['ichimoku']

    # حساب المؤشرات
    try:
        df['rsi'] = calc_rsi(df['close'], period=rsi_settings['period'])
        indicator_status['RSI'] = '✅ ناجح'
    except Exception as e:
        indicator_status['RSI'] = f'❌ فشل: {str(e)}'
        df['rsi'] = pd.Series([np.nan] * len(df))

    try:
        df['atr'] = calc_atr(df, period=settings['atr_period'])
        indicator_status['ATR'] = '✅ ناجح'
    except Exception as e:
        indicator_status['ATR'] = f'❌ فشل: {str(e)}'
        df['atr'] = pd.Series([np.nan] * len(df))

    try:
        df['macd'], df['macd_signal'], df['macd_histogram'] = calc_macd(
            df['close'],
            fast=macd_settings['fast'],
            slow=macd_settings['slow'],
            signal=macd_settings['signal']
        )
        indicator_status['MACD'] = '✅ ناجح'
    except Exception as e:
        indicator_status['MACD'] = f'❌ فشل: {str(e)}'
        df['macd'] = pd.Series([np.nan] * len(df))
        df['macd_signal'] = pd.Series([np.nan] * len(df))
        df['macd_histogram'] = pd.Series([np.nan] * len(df))

    try:
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = calc_bollinger_bands(
            df['close'],
            period=bb_settings['period'],
            std_dev=bb_settings['std_dev']
        )
        indicator_status['Bollinger'] = '✅ ناجح'
    except Exception as e:
        indicator_status['Bollinger'] = f'❌ فشل: {str(e)}'
        df['bb_upper'] = pd.Series([np.nan] * len(df))
        df['bb_middle'] = pd.Series([np.nan] * len(df))
        df['bb_lower'] = pd.Series([np.nan] * len(df))

    try:
        df['vwap'] = calc_vwap(df)
        indicator_status['VWAP'] = '✅ ناجح'
    except Exception as e:
        indicator_status['VWAP'] = f'❌ فشل: {str(e)}'
        df['vwap'] = pd.Series([np.nan] * len(df))

    try:
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
        indicator_status['Ichimoku'] = '✅ ناجح'
    except Exception as e:
        indicator_status['Ichimoku'] = f'❌ فشل: {str(e)}'
        df['tenkan'] = pd.Series([np.nan] * len(df))
        df['kijun'] = pd.Series([np.nan] * len(df))
        df['senkou_a'] = pd.Series([np.nan] * len(df))
        df['senkou_b'] = pd.Series([np.nan] * len(df))
        df['chikou'] = pd.Series([np.nan] * len(df))

    try:
        df['mfi'] = calc_mfi(df, period=mfi_settings['period'])
        indicator_status['MFI'] = '✅ ناجح'
    except Exception as e:
        indicator_status['MFI'] = f'❌ فشل: {str(e)}'
        df['mfi'] = pd.Series([np.nan] * len(df))

    try:
        df['chaikin_mf'] = calc_chaikin_money_flow(df['high'], df['low'], df['close'], df['volume'], period=21)
        indicator_status['Chaikin MF'] = '✅ ناجح'
    except Exception as e:
        indicator_status['Chaikin MF'] = f'❌ فشل: {str(e)}'
        df['chaikin_mf'] = pd.Series([np.nan] * len(df))

    try:
        df_smc = analyze_smc_ict(df)
        indicator_status['SMC'] = '✅ ناجح'
    except Exception as e:
        indicator_status['SMC'] = f'❌ فشل: {str(e)}'
        df_smc = df.copy()
        for col in ['order_block_bullish', 'order_block_bearish', 'fvg_bullish', 'fvg_bearish',
                    'liquidity_sweep_bullish', 'liquidity_sweep_bearish', 'bos_bullish', 'bos_bearish',
                    'mss_bullish', 'mss_bearish', 'in_discount', 'in_premium', 'tbs_bullish', 'tbs_bearish',
                    'bsl', 'ssl', 'smr_bullish', 'smr_bearish']:
            if col not in df_smc.columns:
                df_smc[col] = False if col not in ['bsl', 'ssl'] else np.nan

    try:
        patterns, _ = analyze_chart_patterns(df)
        indicator_status['Patterns'] = '✅ ناجح'
    except Exception as e:
        indicator_status['Patterns'] = f'❌ فشل: {str(e)}'
        patterns = []

    try:
        tbs_type, tbs_entry, tbs_stop, tbs_level = detect_tbs(df)
        indicator_status['TBS'] = '✅ ناجح' if tbs_type else '⚪ لم يُكتشف'
    except Exception as e:
        indicator_status['TBS'] = f'❌ فشل: {str(e)}'
        tbs_type, tbs_entry, tbs_stop, tbs_level = None, None, None, None

    last = df.iloc[-1]
    weights = get_dynamic_weights(df, asset_type)
    scores = {'BUY': 0, 'SELL': 0}
    details = {}

    # الاتجاه اليومي
    daily_trend = get_daily_trend(symbol)
    if daily_trend == "BULLISH":
        scores['BUY'] += 3
        details['Daily_Bias'] = "الاتجاه اليومي صاعد (+3)"
    elif daily_trend == "BEARISH":
        scores['SELL'] += 3
        details['Daily_Bias'] = "الاتجاه اليومي هابط (+3)"
    else:
        details['Daily_Bias'] = "الاتجاه اليومي محايد"

    # SMC/ICT
    smc_bullish_score = 0
    smc_bearish_score = 0
    if not df_smc.empty:
        last_smc = df_smc.iloc[-1]
        if last_smc.get('order_block_bullish', False):
            scores['BUY'] += weights['smc']
            details['SMC_OB'] = f"Order Block شراء (+{weights['smc']})"
            smc_bullish_score += 1
        elif last_smc.get('order_block_bearish', False):
            scores['SELL'] += weights['smc']
            details['SMC_OB'] = f"Order Block بيع (+{weights['smc']})"
            smc_bearish_score += 1
        if last_smc.get('fvg_bullish', False):
            scores['BUY'] += weights['smc']//2
            details['SMC_FVG'] = f"FVG شراء (+{weights['smc']//2})"
            smc_bullish_score += 0.5
        elif last_smc.get('fvg_bearish', False):
            scores['SELL'] += weights['smc']//2
            details['SMC_FVG'] = f"FVG بيع (+{weights['smc']//2})"
            smc_bearish_score += 0.5
        if last_smc.get('mss_bullish', False):
            scores['BUY'] += weights['smc']
            details['SMC_MSS'] = f"MSS صاعد (+{weights['smc']})"
            smc_bullish_score += 1
        elif last_smc.get('mss_bearish', False):
            scores['SELL'] += weights['smc']
            details['SMC_MSS'] = f"MSS هابط (+{weights['smc']})"
            smc_bearish_score += 1
        if last_smc.get('in_discount', False):
            scores['BUY'] += weights['smc']//2
            details['SMC_Discount'] = f"منطقة خصم (+{weights['smc']//2})"
            smc_bullish_score += 0.5
        elif last_smc.get('in_premium', False):
            scores['SELL'] += weights['smc']//2
            details['SMC_Premium'] = f"منطقة قمة (+{weights['smc']//2})"
            smc_bearish_score += 0.5
        if last_smc.get('smr_bullish', False):
            scores['BUY'] += weights['smr']
            details['SMR'] = f"SMR صاعد (+{weights['smr']})"
            smc_bullish_score += 1
        elif last_smc.get('smr_bearish', False):
            scores['SELL'] += weights['smr']
            details['SMR'] = f"SMR هابط (+{weights['smr']})"
            smc_bearish_score += 1

    if tbs_type == "BULLISH":
        scores['BUY'] += weights['tbs']
        details['TBS'] = f"TBS شراء (+{weights['tbs']})"
        smc_bullish_score += 1
    elif tbs_type == "BEARISH":
        scores['SELL'] += weights['tbs']
        details['TBS'] = f"TBS بيع (+{weights['tbs']})"
        smc_bearish_score += 1

    # الأنماط
    if patterns:
        for p in patterns:
            if p['direction'] == 'BULLISH':
                scores['BUY'] += weights['patterns']
                details[f'Pattern_{p["pattern"]}'] = f"{p['pattern']} (+{weights['patterns']})"
            else:
                scores['SELL'] += weights['patterns']
                details[f'Pattern_{p["pattern"]}'] = f"{p['pattern']} (+{weights['patterns']})"

    # المؤشرات التقليدية
    indicator_bullish = 0
    indicator_bearish = 0
    if 'senkou_a' in df.columns and 'senkou_b' in df.columns:
        if not pd.isna(last['senkou_a']) and not pd.isna(last['senkou_b']):
            if current_price > last['senkou_a'] and current_price > last['senkou_b']:
                scores['BUY'] += weights['ichimoku']
                details['Ichimoku'] = f"فوق السحابة (+{weights['ichimoku']})"
                indicator_bullish += 1
            elif current_price < last['senkou_a'] and current_price < last['senkou_b']:
                scores['SELL'] += weights['ichimoku']
                details['Ichimoku'] = f"تحت السحابة (+{weights['ichimoku']})"
                indicator_bearish += 1
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        rsi = last['rsi']
        if rsi < rsi_settings['oversold']:
            scores['BUY'] += weights['rsi']
            details['RSI'] = f"مفرط البيع (+{weights['rsi']})"
            indicator_bullish += 1
        elif rsi > rsi_settings['overbought']:
            scores['SELL'] += weights['rsi']
            details['RSI'] = f"مفرط الشراء (+{weights['rsi']})"
            indicator_bearish += 1
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if not pd.isna(last['macd']) and not pd.isna(last['macd_signal']):
            if last['macd'] > last['macd_signal']:
                scores['BUY'] += weights['macd']
                details['MACD'] = f"تقاطع صاعد (+{weights['macd']})"
                indicator_bullish += 1
            elif last['macd'] < last['macd_signal']:
                scores['SELL'] += weights['macd']
                details['MACD'] = f"تقاطع هابط (+{weights['macd']})"
                indicator_bearish += 1
    if 'mfi' in df.columns and not pd.isna(last['mfi']):
        if last['mfi'] < mfi_settings['oversold']:
            scores['BUY'] += weights['mfi']
            details['MFI'] = f"مفرط بيع (+{weights['mfi']})"
            indicator_bullish += 1
        elif last['mfi'] > mfi_settings['overbought']:
            scores['SELL'] += weights['mfi']
            details['MFI'] = f"مفرط شراء (+{weights['mfi']})"
            indicator_bearish += 1
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price > last['vwap']:
            scores['BUY'] += weights['vwap']
            details['VWAP'] = f"فوق VWAP (+{weights['vwap']})"
            indicator_bullish += 1
        else:
            scores['SELL'] += weights['vwap']
            details['VWAP'] = f"تحت VWAP (+{weights['vwap']})"
            indicator_bearish += 1
    if 'chaikin_mf' in df.columns and not pd.isna(last['chaikin_mf']):
        if last['chaikin_mf'] > 0.1:
            scores['BUY'] += weights['chaikin']
            details['Chaikin'] = f"إيجابي (+{weights['chaikin']})"
            indicator_bullish += 1
        elif last['chaikin_mf'] < -0.1:
            scores['SELL'] += weights['chaikin']
            details['Chaikin'] = f"سلبي (+{weights['chaikin']})"
            indicator_bearish += 1

    # مؤشرات إضافية
    recent_high = df['high'].iloc[-50:].max()
    recent_low = df['low'].iloc[-50:].min()
    fib_levels = calc_fibonacci_levels(recent_high, recent_low, current_price)
    if fib_levels:
        if current_price > fib_levels.get('fib_618', current_price):
            scores['BUY'] += weights['fibonacci']
            details['Fibonacci'] = f"فوق 0.618 (+{weights['fibonacci']})"
        elif current_price < fib_levels.get('fib_382', current_price):
            scores['SELL'] += weights['fibonacci']
            details['Fibonacci'] = f"تحت 0.382 (+{weights['fibonacci']})"

    div_type, div_score = detect_rsi_divergence(df)
    if div_type:
        if "BULLISH" in div_type:
            scores['BUY'] += weights['divergence']
            details['Divergence'] = f"{div_type} (+{weights['divergence']})"
        elif "BEARISH" in div_type:
            scores['SELL'] += weights['divergence']
            details['Divergence'] = f"{div_type} (+{weights['divergence']})"

    is_fresh, fresh_dir = check_fresh_order_block(df_smc)
    if is_fresh and fresh_dir:
        scores[fresh_dir] += weights['fresh_ob']
        details['Fresh_OB'] = f"كتلة أوامر طازجة لصالح {fresh_dir} (+{weights['fresh_ob']})"

    # فحص التوافق
    confluence_conflict = False
    if smc_bullish_score > 0 and indicator_bearish >= 2:
        confluence_conflict = True
    elif smc_bearish_score > 0 and indicator_bullish >= 2:
        confluence_conflict = True

    # حساب النتيجة
    net_score = scores['BUY'] - scores['SELL']
    total_weight = sum(weights.values())

    # شروط مخففة
    if net_score >= 3 and (smc_bullish_score > 0 or indicator_bullish >= 2):
        signal = "BUY"
        confidence = min(100, 55 + (net_score / total_weight) * 100)
    elif net_score <= -3 and (smc_bearish_score > 0 or indicator_bearish >= 2):
        signal = "SELL"
        confidence = min(100, 55 + (abs(net_score) / total_weight) * 100)
    else:
        signal = "WAIT"
        confidence = 50 + (net_score / total_weight) * 50

    if confluence_conflict and signal != "WAIT":
        confidence *= 0.7
        details['Confluence'] = "⚠️ تعارض بين SMC والمؤشرات ×0.7"

    # تأكيد الشموع (شمعة واحدة فقط)
    if signal != "WAIT":
        if not confirm_signal(df, signal, bars=1):
            confidence *= 0.9
            details['Confirmation'] = "⚠️ لم تتأكد الإشارة بشكل كامل"
        else:
            details['Confirmation'] = "✅ تم تأكيد الإشارة"

    # فلتر الاتجاه اليومي (مخفف)
    if signal != "WAIT" and daily_trend != "NEUTRAL":
        if (signal == "BUY" and daily_trend == "BEARISH") or (signal == "SELL" and daily_trend == "BULLISH"):
            confidence *= 0.75
            details['Daily_Trend_Filter'] = f"⚠️ عكس الاتجاه اليومي ({daily_trend}) ×0.75"
        elif (signal == "BUY" and daily_trend == "BULLISH") or (signal == "SELL" and daily_trend == "BEARISH"):
            confidence = min(100, confidence * 1.1)
            details['Daily_Trend_Filter'] = "✅ متوافق مع الاتجاه اليومي +10%"

    # فلتر الأخبار عالية التأثير
    if signal != "WAIT":
        try:
            calendar = get_fmp_economic_calendar()
            if calendar:
                now = datetime.now(pytz.timezone('US/Eastern'))
                for event in calendar:
                    if event.get('impact') in ['High', 'عالٍ']:
                        country = event.get('country', '').upper()
                        pair_currencies = symbol_name.split("/") if "/" in symbol_name else []
                        if any(curr in country for curr in pair_currencies):
                            event_time_str = f"{event.get('date', '')} {event.get('time', '')}"
                            try:
                                event_time = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
                                event_time = pytz.timezone('US/Eastern').localize(event_time)
                                time_diff = (event_time - now).total_seconds() / 60
                                if 0 <= time_diff <= 60:
                                    confidence *= 0.5
                                    details['News_Filter'] = f"⛔ خبر قوي خلال {time_diff:.0f} دقيقة"
                                    if confidence < 50:
                                        signal = "WAIT"
                            except:
                                pass
        except:
            pass

    # MTF
    mtf_signal = "NEUTRAL"
    mtf_weight = 0
    if symbol and symbol != "":
        try:
            mtf_signal, mtf_weight = get_mtf_signal(symbol, current_price)
        except:
            pass
        if signal != "WAIT" and mtf_signal != "NEUTRAL":
            if signal != mtf_signal:
                confidence *= 0.8
                details['MTF'] = f"⚠️ تعارض مع MTF ({mtf_signal}) ×0.8"
            else:
                confidence = min(100, confidence * 1.1)
                details['MTF'] = f"✅ متوافق مع MTF ({mtf_signal}) +10%"

    # News sentiment
    news_impact_score = 0
    try:
        news = get_fmp_news()
        if news:
            news_analysis = analyze_news_impact(news)
            st.session_state.news_analysis = news_analysis
            news_impact_score, _ = get_news_impact_score(news_analysis, symbol)
            if signal != "WAIT" and abs(news_impact_score) > 10:
                if (signal == "BUY" and news_impact_score > 0) or (signal == "SELL" and news_impact_score < 0):
                    confidence = min(100, confidence * 1.1)
                    details['News'] = f"✅ الأخبار تدعم ({news_impact_score:+.0f}) +10%"
                else:
                    confidence *= 0.85
                    details['News'] = f"⚠️ الأخبار تعارض ({news_impact_score:+.0f}) ×0.85"
    except:
        pass

    # Killzone
    killzone, kz_bonus = is_ict_killzone()
    if killzone and signal != "WAIT":
        confidence = min(100, confidence + kz_bonus * 2)
        details['Killzone'] = f"منطقة {killzone} (+{kz_bonus*2}%)"

    # Session
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    hour = now.hour
    if 16 <= hour < 17:
        confidence *= 0.9
        details['Session'] = "⚠️ آخر ساعة قبل الإغلاق ×0.9"
    elif 9 <= hour < 11:
        confidence = min(100, confidence * 1.05)
        details['Session'] = "✅ ذروة السيولة في نيويورك +5%"

    # ATR Filter
    if 'atr' in df.columns and len(df) > 50:
        current_atr = last['atr']
        avg_atr = df['atr'].iloc[-50:].mean()
        if not pd.isna(current_atr) and not pd.isna(avg_atr):
            if current_atr < avg_atr * 0.7:
                confidence *= 0.7
                details['ATR_Avg'] = "⚠️ تقلب منخفض ×0.7"

    # Volatility
    if 'atr' in df.columns and not pd.isna(last['atr']):
        atr_pct = (last['atr'] / current_price) * 100
        if atr_pct < 0.3:
            confidence *= 0.8
            details['Volatility'] = f"⚠️ تقلب منخفض ({atr_pct:.2f}%) ×0.8"

    # Volume Filter
    if 'volume' in df.columns:
        avg_volume = df['volume'].iloc[-20:].mean()
        if not pd.isna(last['volume']) and not pd.isna(avg_volume):
            if last['volume'] < avg_volume * 1.2:
                confidence *= 0.85
                details['Volume_Filter'] = "⚠️ حجم تداول منخفض ×0.85"

    confidence = max(0, min(100, confidence))

    # حساب مستويات الدخول والخروج
    stop_loss = None
    entry_price = None
    targets = {}
    if signal in ["BUY", "SELL"] and confidence >= 60:  # خفض من 70 إلى 60
        try:
            df_long = get_twelvedata_historical(symbol, interval="4h", outputsize=100)
            if df_long is not None and len(df_long) > 20:
                atr_long = calc_atr(df_long).iloc[-1]
                if not pd.isna(atr_long) and atr_long > 0:
                    atr_value = atr_long
                else:
                    atr_value = last['atr'] if not pd.isna(last['atr']) else 10
            else:
                atr_value = last['atr'] if not pd.isna(last['atr']) else 10
        except:
            atr_value = last['atr'] if not pd.isna(last['atr']) else 10

        entry_price = current_price
        risk_multiplier = 1.5

        if signal == "BUY":
            stop_loss = entry_price - atr_value * 2.0 * risk_multiplier
            targets = {
                'target1': entry_price + atr_value * 1.5 * risk_multiplier,
                'target2': entry_price + atr_value * 2.5 * risk_multiplier,
                'target3': entry_price + atr_value * 4.0 * risk_multiplier,
                'risk_reward_1': 1.5,
                'risk_reward_2': 2.5,
                'risk_reward_3': 4.0,
                'risk': atr_value * 2.0 * risk_multiplier
            }
        else:
            stop_loss = entry_price + atr_value * 2.0 * risk_multiplier
            targets = {
                'target1': entry_price - atr_value * 1.5 * risk_multiplier,
                'target2': entry_price - atr_value * 2.5 * risk_multiplier,
                'target3': entry_price - atr_value * 4.0 * risk_multiplier,
                'risk_reward_1': 1.5,
                'risk_reward_2': 2.5,
                'risk_reward_3': 4.0,
                'risk': atr_value * 2.0 * risk_multiplier
            }

        if targets.get('risk_reward_3', 0) < 1.5:  # خفض من 2.0 إلى 1.5
            confidence *= 0.85
            details['RiskReward'] = f"⚠️ R:R {targets.get('risk_reward_3', 0):.1f} < 1.5 ×0.85"
            if confidence < 50:
                signal = "WAIT"
                targets = {}
                stop_loss = None
                entry_price = None
        else:
            details['RiskReward'] = f"✅ R:R 1:{targets.get('risk_reward_3', 0):.1f}"
    else:
        if signal in ["BUY", "SELL"] and confidence < 60:
            signal = "WAIT"
            confidence = max(confidence, 50)

    # إرسال تنبيه تيليجرام
    if signal in ["BUY", "SELL"] and confidence >= 75:
        message = f"🔔 إشارة قوية: {signal} {symbol_name} بثقة {confidence:.0f}%\nالدخول: {current_price:.4f}\nوقف: {stop_loss:.4f}\nالأهداف: {targets.get('target1', 0):.4f}, {targets.get('target2', 0):.4f}, {targets.get('target3', 0):.4f}"
        send_telegram_alert(message)

    tbs_info = (tbs_type, tbs_entry, tbs_stop, tbs_level)
    st.session_state.indicator_status = indicator_status
    failed = [k for k, v in indicator_status.items() if '❌' in v]
    st.session_state.failed_indicators = failed

    return signal, confidence, net_score, details, patterns, tbs_info, stop_loss, entry_price, targets, indicator_status

# ==========================================
# دالة جمع الإشارات
# ==========================================
def apply_confluence_filter(all_signals_df):
    if all_signals_df is None or all_signals_df.empty:
        return all_signals_df
    df = all_signals_df.copy()
    active = df[df['الإشارة'].isin(['BUY', 'SELL'])]
    if len(active) < 2:
        return df
    active_pairs = active['الزوج'].tolist()
    active_symbols = [PAIRS.get(p, '') for p in active_pairs]
    corr_matrix = get_correlation_matrix(active_symbols)
    if corr_matrix.empty:
        return df
    for i, pair1 in enumerate(active_pairs):
        for j, pair2 in enumerate(active_pairs):
            if i >= j:
                continue
            corr_val = corr_matrix.iloc[i, j] if i < len(corr_matrix) and j < len(corr_matrix.columns) else 0
            if abs(corr_val) > 0.7:
                sig1 = active[active['الزوج'] == pair1]['الإشارة'].values[0]
                sig2 = active[active['الزوج'] == pair2]['الإشارة'].values[0]
                if sig1 != sig2:
                    idx1 = df[df['الزوج'] == pair1].index[0]
                    idx2 = df[df['الزوج'] == pair2].index[0]
                    df.at[idx1, 'الثقة'] = round(df.at[idx1, 'الثقة'] * 0.85, 1)
                    df.at[idx2, 'الثقة'] = round(df.at[idx2, 'الثقة'] * 0.85, 1)
                    df.at[idx1, 'ملاحظات'] = f"تعارض مع {pair2}"
                    df.at[idx2, 'ملاحظات'] = f"تعارض مع {pair1}"
    return df

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
            df = get_historical_data(symbol, period="3mo", interval="4h")
            if df is None or len(df) < 50:
                continue
            current_price = df['close'].iloc[-1]
            signal, confidence, net_score, _, _, _, stop_loss, entry_price, targets, _ = generate_advanced_signal(df, current_price, pair_name, symbol)
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
                "نسبة المخاطرة": trade_details.get('risk_reward', "N/A"),
                "ملاحظات": ""
            })
        except Exception as e:
            continue
    progress_bar.empty()
    status_text.empty()
    df_result = pd.DataFrame(results)
    if not df_result.empty:
        df_result = apply_confluence_filter(df_result)
    return df_result

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
            "target1": trade_data.get("target1", None),
            "target2": trade_data.get("target2", None),
            "target3": trade_data.get("target3", None),
            "partial_close_done": False,
            "partial_close_price": trade_data.get("target1", None),
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
    def check_partial_close(self, trade_id, current_price):
        for trade in self.open_trades:
            if trade["id"] == trade_id and trade["status"] == "open" and not trade["partial_close_done"] and trade["partial_close_price"]:
                if trade["direction"] == "BUY" and current_price >= trade["partial_close_price"]:
                    closed_lots = trade["lots"] / 2
                    trade["lots"] -= closed_lots
                    trade["stop_loss"] = trade["entry"]
                    trade["partial_close_done"] = True
                    trade["stage"] = 1
                    profit = (trade["partial_close_price"] - trade["entry"]) * closed_lots * 10
                    trade["partial_profit"] = round(profit, 2)
                    self.save_trades()
                    return True, f"تم إغلاق جزئي لنصف الصفقة عند {trade['partial_close_price']:.4f} ونقل الوقف للدخول"
                elif trade["direction"] == "SELL" and current_price <= trade["partial_close_price"]:
                    closed_lots = trade["lots"] / 2
                    trade["lots"] -= closed_lots
                    trade["stop_loss"] = trade["entry"]
                    trade["partial_close_done"] = True
                    trade["stage"] = 1
                    profit = (trade["entry"] - trade["partial_close_price"]) * closed_lots * 10
                    trade["partial_profit"] = round(profit, 2)
                    self.save_trades()
                    return True, f"تم إغلاق جزئي لنصف الصفقة عند {trade['partial_close_price']:.4f} ونقل الوقف للدخول"
        return False, ""
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
                if "partial_profit" in trade:
                    profit += trade["partial_profit"]
                trade["profit"] = round(profit, 2)
                trade["result"] = "win" if profit > 0 else "loss"
                trade["close_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_trades.append(trade)
                self.open_trades.pop(i)
                self.save_trades()
                return profit
        return None

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

def explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_count, patterns, tbs_info, df, current_price, stop_loss, entry_price, targets):
    explanation = ""
    if signal == "BUY":
        explanation = "🔹 **قرار الشراء** بناءً على:\n"
        for k, v in details.items():
            if v and ("+" in str(v) or any(word in str(v) for word in ["شراء", "صاعد", "فوق", "مفرط البيع", "كتلة", "FVG", "تحول", "خصم", "TBS", "SMR"])):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≥3 للشراء)\n📈 **الثقة**: {confidence:.0f}%"
    elif signal == "SELL":
        explanation = "🔻 **قرار البيع** بناءً على:\n"
        for k, v in details.items():
            if v and ("-" in str(v) or any(word in str(v) for word in ["بيع", "هابط", "تحت", "مفرط الشراء", "كتلة بيع", "تحول هابط", "TBS"])):
                explanation += f"- {k}: {v}\n"
        explanation += f"✅ **النتيجة الصافية**: {net_score} (≤-3 للبيع)\n📉 **الثقة**: {confidence:.0f}%"
    else:
        explanation = "⏳ **قرار الانتظار** بسبب:\n"
        explanation += f"- النتيجة الصافية {net_score} بين -3 و +3 (لا يوجد إجماع).\n"
        for k, v in details.items():
            if v:
                explanation += f"  - {k}: {v}\n"
        explanation += "💡 **نصيحة**: انتظر حتى تتجاوز النتيجة ±3 أو تتحسن الثقة فوق 60%."
    if stop_loss and entry_price and targets:
        explanation += f"\n\n📍 **سعر الدخول المقترح:** {entry_price:.4f}"
        explanation += f"\n🛑 **وقف الخسارة:** {stop_loss:.4f} (المسافة: {abs(entry_price - stop_loss):.4f})"
        explanation += f"\n🎯 **الأهداف:**"
        explanation += f"\n   - الهدف 1 (1:1.5): {targets['target1']:.4f}"
        explanation += f"\n   - الهدف 2 (1:2.5): {targets['target2']:.4f}"
        explanation += f"\n   - الهدف 3 (1:4): {targets['target3']:.4f}"
    explanation += f"\n\n🕒 **تحليل الأطر الزمنية**: {mtf_signal} (وزن: {mtf_count})"
    if patterns:
        explanation += "\n\n📐 **النماذج المكتشفة:**\n"
        for p in patterns:
            explanation += f"- {p['pattern']} ({p['direction']}) - قوة: {p['score']}/5\n"
    if tbs_info and tbs_info[0]:
        tbs_type, tbs_entry, tbs_stop, tbs_level = tbs_info
        if tbs_type:
            explanation += f"\n\n🐢 **TBS مكتشف:** {tbs_type}\n"
            if tbs_entry:
                explanation += f"   - سعر الدخول: {tbs_entry:.4f}\n"
            if tbs_stop:
                explanation += f"   - وقف الخسارة: {tbs_stop:.4f}\n"
    return explanation

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
# الواجهة الرئيسية
# ==========================================
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
                st.metric(f"{color} {currency}", f"{value:+.2f}%", delta_color="normal")
        if len(sorted_currencies) >= 2:
            strongest = sorted_currencies[0]
            weakest = sorted_currencies[-1]
            st.markdown(f"""
            <div style="font-size: 0.8rem; background: rgba(10,10,10,0.4); border-radius: 8px; padding: 10px; margin: 5px 0;">
                <span style="color: #00ff88;">▲ {strongest[0]} {strongest[1]:+.2f}%</span><br>
                <span style="color: #ff4444;">▼ {weakest[0]} {weakest[1]:+.2f}%</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("اضغط 'تحديث القوة'")
    st.markdown("---")

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
            df_signals[["الزوج", "الإشارة", "الثقة", "النتيجة", "السعر", "ملاحظات"]],
            column_config={
                "الزوج": st.column_config.TextColumn("الزوج", width="medium"),
                "الإشارة": st.column_config.TextColumn("الإشارة", width="small"),
                "الثقة": st.column_config.NumberColumn("الثقة", format="%.1f%%"),
                "النتيجة": st.column_config.NumberColumn("النتيجة", format="%d"),
                "السعر": st.column_config.TextColumn("السعر"),
                "ملاحظات": st.column_config.TextColumn("ملاحظات"),
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

# ==========================================
# جلب البيانات وعرض الإشارة
# ==========================================
for attempt in range(3):
    current_price, change = get_spot_price(selected_symbol)
    if current_price is not None:
        break
    time.sleep(1)

df = get_historical_data(selected_symbol, period="3mo", interval="4h")

if df is None:
    st.error("⚠️ تعذر تحميل البيانات بعد عدة محاولات. يرجى التحقق من اتصال الإنترنت أو اختيار زوج آخر.")
    if st.button("🔄 إعادة محاولة تحميل البيانات", key="retry_load_data", width='stretch'):
        st.cache_data.clear()
        st.rerun()
    st.stop()

if current_price is None:
    current_price = df['close'].iloc[-1]
    change = 0

signal, confidence, net_score, details, patterns, tbs_info, stop_loss, entry_price, targets, indicator_status = generate_advanced_signal(df, current_price, selected_pair_name, selected_symbol)

mtf_signal, mtf_weight = get_mtf_signal(selected_symbol, current_price)

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

col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 2, 1])
with col_refresh2:
    if st.button("🔄 تحديث البيانات", key="refresh_data_button", width='stretch'):
        st.session_state.refresh_trigger = not st.session_state.refresh_trigger
        st.session_state.last_update = datetime.now()
        st.cache_data.clear()
        st.success("✅ تم تحديث البيانات بنجاح!")
        st.rerun()

st.caption(f"🕐 آخر تحديث: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')} | إطار التحليل: 4 ساعات")

with st.expander("🔍 حالة المؤشرات والأدوات", expanded=False):
    if indicator_status:
        for name, status in indicator_status.items():
            if '✅' in status:
                st.success(f"{name}: {status}")
            elif '⚠️' in status or '⚪' in status:
                st.warning(f"{name}: {status}")
            else:
                st.error(f"{name}: {status}")
    if st.session_state.data_errors:
        st.warning("⚠️ أخطاء في جلب البيانات:")
        for err in st.session_state.data_errors:
            st.caption(f"- {err}")

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
    cols[0].metric("RSI", f"{last['rsi']:.1f}" if not pd.isna(last['rsi']) else "N/A")
    cols[1].metric("ATR", f"${last['atr']:.2f}" if "Gold" in selected_pair_name else f"{last['atr']:.4f}" if not pd.isna(last['atr']) else "N/A")
    cols[2].metric("VWAP", f"${last['vwap']:.2f}" if "Gold" in selected_pair_name else f"{last['vwap']:.4f}" if not pd.isna(last['vwap']) else "N/A")
    cols[3].metric("MFI", f"{last['mfi']:.1f}" if not pd.isna(last['mfi']) else "N/A")
    cols[4].metric("MACD", f"{last['macd']:.4f}" if not pd.isna(last['macd']) else "N/A")
    cols[5].metric("Chaikin MF", f"{last['chaikin_mf']:.2f}" if not pd.isna(last['chaikin_mf']) else "N/A")
else:
    st.caption("👆 اضغط 'إظهار' لعرض مؤشرات السوق")

st.markdown("---")

# عرض الصفقة المقترحة (مع خفض العتبة إلى 60)
if signal in ["BUY", "SELL"] and confidence >= 60 and stop_loss and entry_price and targets:
    direction_text = "شراء (BUY)" if signal == "BUY" else "بيع (SELL)"
    risk_reward = f"1:{targets['risk_reward_3']:.1f}"
    suggested_lot = calculate_lot_size(entry_price, stop_loss, account_balance=100000, risk_percent=1.0)
    st.markdown(f"""
    <div class="suggested-trade" style="border: 3px solid #00ff88;">
        <b>الاتجاه:</b> {direction_text} (الثقة: {confidence:.0f}%)<br>
        <b>📍 سعر الدخول المقترح:</b> {price_format.format(entry_price)}<br>
        <b>🛑 وقف الخسارة:</b> {price_format.format(stop_loss)} (المسافة: {abs(entry_price - stop_loss):.2f} نقطة)<br>
        <div class="target-zone"><b>🎯 الهدف 1 (1:1.5):</b> {price_format.format(targets['target1'])}</div>
        <div class="target-zone" style="border-left-color: #ffaa00;"><b>🎯 الهدف 2 (1:2.5):</b> {price_format.format(targets['target2'])}</div>
        <div class="target-zone" style="border-left-color: #00ff88;"><b>🎯 الهدف 3 (1:4):</b> {price_format.format(targets['target3'])}</div>
        <b>📈 نسبة المخاطرة/المكافأة القصوى:</b> {risk_reward}<br>
        <b>💰 حجم اللوت المقترح (مخاطرة 1%):</b> {suggested_lot}
        <br><span style="color: #00ff88;">✅ صفقة قوية</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("➕ إضافة هذه الصفقة", key="add_suggested_trade", width='stretch'):
        trade_manager = TradeManager()
        trailing_dist = last['atr'] * 0.3 if 'atr' in last and not pd.isna(last['atr']) else (3 if "Gold" in selected_pair_name else 0.0003)
        trade_data = {
            "direction": signal,
            "entry": entry_price,
            "lots": suggested_lot,
            "stop_loss": stop_loss,
            "take_profit": targets['target2'],
            "target1": targets['target1'],
            "target2": targets['target2'],
            "target3": targets['target3'],
            "trailing_enabled": True,
            "trailing_distance": trailing_dist,
            "notes": f"مقترحة من الإشارة المتكاملة (الثقة {confidence:.0f}%) - إطار 4 ساعات"
        }
        trade_id = trade_manager.add_trade(trade_data)
        st.success(f"✅ تم إضافة الصفقة {trade_id} بنجاح!")
        st.rerun()
else:
    st.info("⏳ لا توجد صفقة مقترحة حالياً (انتظر إشارة قوية بثقة ≥60%)")

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
        MTF إجماع: {mtf_signal} (وزن الأطر: {mtf_weight})
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander("📝 شرح القرار", expanded=True):
    explanation = explain_decision(signal, confidence, net_score, details, mtf_signal, mtf_weight, patterns, tbs_info, df, current_price, stop_loss, entry_price, targets)
    st.markdown(f'<div class="explanation-box">{explanation}</div>', unsafe_allow_html=True)

# ... (بقية الواجهة كما في النسخة السابقة: التقويم، الأخبار، الارتباط، الصفقات، الرسم البياني، التذييل)
