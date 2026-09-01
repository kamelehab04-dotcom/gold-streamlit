# ==========================================
# BLACK PYRAMID – الإصدار 2002 (النسخة النهائية المعدلة)
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

st.set_page_config(page_title="Black Pyramid", page_icon="▲", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# مفاتيح API الافتراضية (يمكن تغييرها من الواجهة)
# ==========================================
DEFAULT_TWELVE_API_KEY = "b46ffed1c34b4a89ac203bc5c0756fd8"
DEFAULT_FASTFOREX_API_KEY = "4cd179a14f-a982d5aedd-tkn80n"
DEFAULT_GOLD_API_KEY = "goldapi-ec1f975155d746fdd0b810cd202d0a66-io"
DEFAULT_FMP_API_KEY = "EBdaCkJXtIphxCdiZpW3EWCAb4IKpz8N"
DEFAULT_ALPHA_API_KEY = ""

if "user_twelve_key" not in st.session_state:
    st.session_state.user_twelve_key = DEFAULT_TWELVE_API_KEY
if "user_fastforex_key" not in st.session_state:
    st.session_state.user_fastforex_key = DEFAULT_FASTFOREX_API_KEY
if "user_gold_key" not in st.session_state:
    st.session_state.user_gold_key = DEFAULT_GOLD_API_KEY
if "user_fmp_key" not in st.session_state:
    st.session_state.user_fmp_key = DEFAULT_FMP_API_KEY
if "user_alpha_key" not in st.session_state:
    st.session_state.user_alpha_key = DEFAULT_ALPHA_API_KEY

TWELVE_API_KEY = st.session_state.user_twelve_key
FASTFOREX_API_KEY = st.session_state.user_fastforex_key
GOLD_API_KEY = st.session_state.user_gold_key
FMP_API_KEY = st.session_state.user_fmp_key
ALPHA_VANTAGE_API_KEY = st.session_state.user_alpha_key

# ==========================================
# الهوية البصرية
# ==========================================
st.markdown("""
<style>
    .main-header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ffd700; }
    .main-title { font-size: 2.5rem; font-weight: bold; color: #ffd700; text-align: center; text-shadow: 0 0 10px #ffd700; }
    .main-subtitle { color: #ccc; text-align: center; font-size: 1rem; margin-top: 5px; }
    .price-card { background: #1a1a2e; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #ffd700; }
    .price-label { color: #aaa; font-size: 0.9rem; }
    .price-value { font-size: 2rem; font-weight: bold; color: #fff; }
    .price-change { font-size: 1rem; margin-top: 5px; }
    .signal-box { background: #1a1a2e; padding: 20px; border-radius: 10px; text-align: center; margin: 15px 0; border: 2px solid #ffd700; }
    .signal-text { font-size: 2.5rem; font-weight: bold; }
    .signal-confidence { font-size: 1.2rem; color: #ccc; margin-top: 10px; }
    .suggested-trade { background: #1a1a2e; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #00ff88; }
    .target-zone { background: #16213e; padding: 8px; border-radius: 5px; margin: 5px 0; border-left: 4px solid #ffd700; }
    .explanation-box { background: #0f0f1a; padding: 15px; border-radius: 8px; white-space: pre-line; font-family: monospace; color: #ddd; }
    .trade-row { background: #1a1a2e; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid #ffaa00; }
    .reversal-alert { background: #2a1a1a; padding: 10px; border-radius: 5px; border-left: 3px solid #ff4444; margin: 5px 0; }
    .news-card { background: #1a1a2e; padding: 10px; border-radius: 5px; margin: 5px 0; }
    .confluence-bar { background: #16213e; border-radius: 10px; padding: 10px; margin: 10px 0; }
    .dxy-box { background: #1a1a3e; border: 1px solid #4a4a8e; border-radius: 8px; padding: 10px; margin: 5px 0; }
    .footer { text-align: center; margin-top: 30px; padding: 15px; color: #aaa; font-size: 0.8rem; border-top: 1px solid #333; }
    .brand { color: #ffd700; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div style="text-align: right;">
        <div class="main-title">▲ BLACK PYRAMID ▲</div>
        <div class="main-subtitle">Advanced Trading Intelligence • SMC/ICT • DXY • USD Strength • Gold Correlation • Smart Targets • Confluence Score</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# تهيئة حالة الجلسة
# ==========================================
if "df" not in st.session_state: st.session_state.df = None
if "current_trade" not in st.session_state: st.session_state.current_trade = None
if "show_form" not in st.session_state: st.session_state.show_form = False
if "last_update" not in st.session_state: st.session_state.last_update = datetime.now()
if "all_signals" not in st.session_state: st.session_state.all_signals = None
if "show_indicators" not in st.session_state: st.session_state.show_indicators = True
if "currency_strength" not in st.session_state: st.session_state.currency_strength = None
if "economic_events" not in st.session_state: st.session_state.economic_events = None
if "news_analysis" not in st.session_state: st.session_state.news_analysis = None
if "data_errors" not in st.session_state: st.session_state.data_errors = []
if "indicator_status" not in st.session_state: st.session_state.indicator_status = {}
if "usd_strength_cache" not in st.session_state: st.session_state.usd_strength_cache = None
if "daily_trade_count" not in st.session_state: st.session_state.daily_trade_count = 0
if "trade_date" not in st.session_state: st.session_state.trade_date = datetime.now().strftime("%Y-%m-%d")

def can_open_trade(confidence):
    today = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.trade_date != today:
        st.session_state.trade_date = today
        st.session_state.daily_trade_count = 0
    if st.session_state.daily_trade_count >= 4:
        return False, "الحد الأقصى 4 صفقات اليوم"
    if confidence < 70 and st.session_state.daily_trade_count >= 2:
        return False, "الحد الأقصى للصفقات منخفضة الثقة"
    return True, None

def increment_trade_count():
    st.session_state.daily_trade_count += 1

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

TWELVE_SYMBOL_MAP = {
    "GC=F": "XAU/USD", "SI=F": "XAG/USD", "DX-Y.NYB": "DXY",
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
    "USDCHF=X": "USD/CHF", "AUDUSD=X": "AUD/USD", "NZDUSD=X": "NZD/USD",
    "USDCAD=X": "USD/CAD", "EURGBP=X": "EUR/GBP", "EURJPY=X": "EUR/JPY",
    "EURCHF=X": "EUR/CHF", "EURAUD=X": "EUR/AUD", "EURNZD=X": "EUR/NZD",
    "EURCAD=X": "EUR/CAD", "GBPJPY=X": "GBP/JPY", "GBPCHF=X": "GBP/CHF",
    "GBPAUD=X": "GBP/AUD", "GBPNZD=X": "GBP/NZD", "GBPCAD=X": "GBP/CAD",
    "AUDJPY=X": "AUD/JPY", "AUDCHF=X": "AUD/CHF", "AUDNZD=X": "AUD/NZD",
    "AUDCAD=X": "AUD/CAD", "NZDJPY=X": "NZD/JPY", "NZDCHF=X": "NZD/CHF",
    "NZDCAD=X": "NZD/CAD", "CADJPY=X": "CAD/JPY", "CADCHF=X": "CAD/CHF",
    "BTC-USD": "BTC/USD", "ETH-USD": "ETH/USD"
}

CURRENCY_INDICES = {
    "USD": ["EURUSD=X","GBPUSD=X","USDJPY=X","USDCHF=X","AUDUSD=X","USDCAD=X","NZDUSD=X"],
    "EUR": ["EURUSD=X","EURGBP=X","EURJPY=X","EURCHF=X","EURAUD=X","EURCAD=X","EURNZD=X"],
    "GBP": ["GBPUSD=X","EURGBP=X","GBPJPY=X","GBPCHF=X","GBPAUD=X","GBPCAD=X","GBPNZD=X"],
    "JPY": ["USDJPY=X","EURJPY=X","GBPJPY=X","AUDJPY=X","NZDJPY=X","CADJPY=X"],
    "CHF": ["USDCHF=X","EURCHF=X","GBPCHF=X","AUDCHF=X","NZDCHF=X","CADCHF=X"],
    "AUD": ["AUDUSD=X","EURAUD=X","GBPAUD=X","AUDJPY=X","AUDNZD=X","AUDCAD=X"],
    "NZD": ["NZDUSD=X","EURNZD=X","GBPNZD=X","AUDNZD=X","NZDJPY=X","NZDCAD=X"],
    "CAD": ["USDCAD=X","EURCAD=X","GBPCAD=X","AUDCAD=X","NZDCAD=X","CADJPY=X","CADCHF=X"]
}

# ==========================================
# دوال جلب البيانات
# ==========================================
def get_twelvedata_price(symbol_key):
    td_symbol = TWELVE_SYMBOL_MAP.get(symbol_key, symbol_key)
    url = f"https://api.twelvedata.com/price?symbol={td_symbol}&apikey={TWELVE_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'price' in data and data['price'] is not None:
                return float(data['price'])
    except:
        pass
    return None

def get_fastforex_price(symbol_key):
    iso = symbol_key.replace("=X","")
    if len(iso) != 6: return None
    base, quote = iso[:3], iso[3:]
    url = f"https://api.fastforex.io/fetch-one?from={base}&to={quote}&api_key={FASTFOREX_API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if 'result' in data:
                return float(data['result'])
    except:
        pass
    return None

def get_twelvedata_historical(symbol_key, interval="1h", outputsize=500):
    td_symbol = TWELVE_SYMBOL_MAP.get(symbol_key, symbol_key)
    interval_map = {"1m":"1min","5m":"5min","15m":"15min","30m":"30min","1h":"1h","4h":"4h","1d":"1day"}
    td_interval = interval_map.get(interval,"1h")
    url = f"https://api.twelvedata.com/time_series?symbol={td_symbol}&interval={td_interval}&outputsize={outputsize}&apikey={TWELVE_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if 'values' in data and data['values']:
                df = pd.DataFrame(data['values'])
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.set_index('datetime')
                df = df.astype(float)
                df.columns = ['open','high','low','close','volume']
                return df.sort_index()
    except:
        pass
    return None

def get_yfinance_data(symbol, period, interval="1h"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if not df.empty and len(df) > 50:
            df.columns = [c.lower() for c in df.columns]
            return df
    except:
        pass
    return None

def get_stooq_data(symbol, interval, limit=500):
    stooq_symbol = symbol.replace("=X","").replace("-","")
    if symbol == "GC=F": stooq_symbol = "xauusd"
    elif symbol == "SI=F": stooq_symbol = "xagusd"
    url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&i={interval}&d1=20240101&d2=20261231"
    try:
        df = pd.read_csv(url)
        if len(df) > 50:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date')
            df.columns = [c.lower() for c in df.columns]
            return df
    except:
        pass
    return None

def get_alpha_vantage_data(symbol, interval, limit=500):
    if not ALPHA_VANTAGE_API_KEY: return None
    av_symbol = symbol.replace("=X","").replace("-","")
    if symbol == "GC=F": av_symbol = "XAUUSD"
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={av_symbol}&interval={interval}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if "Time Series" in data:
            ts = list(data["Time Series"].values())[0]
            df = pd.DataFrame(ts).T
            df.index = pd.to_datetime(df.index)
            df.columns = [c.lower() for c in df.columns]
            df = df.rename(columns={'1. open':'open','2. high':'high','3. low':'low','4. close':'close','5. volume':'volume'})
            return df
    except:
        pass
    return None

@st.cache_data(ttl=300)
def get_historical_data(symbol, period="3mo", interval="4h"):
    # yfinance أولاً (نستخدم 1h ثم نعيد التجميع إلى 4h)
    df = get_yfinance_data(symbol, period, "1h")
    if df is not None and len(df) > 50:
        if interval == "4h":
            df = df.resample('4h').agg({
                'open':'first','high':'max','low':'min','close':'last','volume':'sum'
            }).dropna()
        return df
    # Stooq
    df = get_stooq_data(symbol, interval)
    if df is not None and len(df) > 50:
        return df
    # Twelve Data
    df = get_twelvedata_historical(symbol, interval, 500)
    if df is not None and len(df) > 50:
        return df
    # Alpha Vantage
    df = get_alpha_vantage_data(symbol, interval)
    if df is not None and len(df) > 50:
        return df
    return None

@st.cache_data(ttl=30)
def get_spot_price(symbol="GC=F"):
    # yfinance أولاً
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
    price = get_twelvedata_price(symbol)
    if price:
        return price, 0.0
    if "=X" in symbol:
        price = get_fastforex_price(symbol)
        if price:
            return price, 0.0
    if symbol == "GC=F" and GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAU/USD"
            headers = {"x-access-token": GOLD_API_KEY}
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                return float(data.get('price',0)), float(data.get('change_percent',0))
        except:
            pass
    return None, None

# ==========================================
# دوال البيانات الأخرى
# ==========================================
@st.cache_data(ttl=60)
def get_currency_strength():
    strength = {}
    for currency, pairs in CURRENCY_INDICES.items():
        changes = []
        for pair in pairs:
            try:
                ticker = yf.Ticker(pair)
                data = ticker.history(period="1d", interval="5m")
                if not data.empty:
                    last = data['Close'].iloc[-1]
                    first = data['Close'].iloc[0]
                    change = ((last - first) / first) * 100 if first != 0 else 0
                    if pair.startswith(currency):
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
    for name, symbol in main_symbols.items():
        try:
            price, change = get_spot_price(symbol)
            if price is not None:
                results[name] = {'price': price, 'change': change}
            else:
                results[name] = {'price': 0, 'change': 0}
        except:
            results[name] = {'price': 0, 'change': 0}
    return results

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
# أنماط هيكلية (اختصار بعضها)
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
    if len(df) < lookback: return None, 0
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
    if len(df) < lookback: return None, 0
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
    if len(df) < lookback: return None, 0
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
    if len(df) < lookback: return None, 0
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
    if len(df) < lookback: return None, 0
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
    if len(df) < lookback: return None, 0
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
    if p: patterns.append({"pattern": p, "score": s, "direction": "BEARISH" if "HEAD" in p else "BULLISH"}); total_score += s
    p, s = detect_double_top_bottom(df)
    if p: patterns.append({"pattern": p, "score": s, "direction": "BEARISH" if "TOP" in p else "BULLISH"}); total_score += s
    p, s = detect_triangle_pattern(df)
    if p: patterns.append({"pattern": p, "score": s, "direction": "BULLISH" if "ASCENDING" in p else "BEARISH"}); total_score += s
    p, s = detect_triple_top_bottom(df)
    if p: patterns.append({"pattern": p, "score": s, "direction": "BEARISH" if "TOP" in p else "BULLISH"}); total_score += s
    p, s = detect_wedge(df)
    if p: patterns.append({"pattern": p, "score": s, "direction": "BEARISH" if "RISING" in p else "BULLISH"}); total_score += s
    p, s = detect_flag_pennant(df)
    if p:
        last_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-5] if len(df) >= 5 else df['close'].iloc[0]
        direction = "BULLISH" if last_close > prev_close else "BEARISH"
        patterns.append({"pattern": p, "score": s, "direction": direction}); total_score += s
    return patterns, total_score

# ==========================================
# دوال متقدمة (اختصار)
# ==========================================
def detect_candlestick_patterns(df):
    patterns = []
    if len(df) < 3: return patterns
    last = df.iloc[-1]; prev = df.iloc[-2]; prev2 = df.iloc[-3]
    body = abs(last['close'] - last['open']); total_range = last['high'] - last['low']
    if (prev['close'] < prev['open'] and last['close'] > last['open'] and last['open'] < prev['close'] and last['close'] > prev['open']):
        patterns.append({"pattern":"BULLISH_ENGULFING","direction":"BULLISH","score":3})
    if (prev['close'] > prev['open'] and last['close'] < last['open'] and last['open'] > prev['close'] and last['close'] < prev['open']):
        patterns.append({"pattern":"BEARISH_ENGULFING","direction":"BEARISH","score":3})
    lower_wick = min(last['close'],last['open'])-last['low']; upper_wick = last['high']-max(last['close'],last['open'])
    if body>0 and lower_wick>body*2 and upper_wick<body*0.3: patterns.append({"pattern":"HAMMER","direction":"BULLISH","score":2})
    if body>0 and upper_wick>body*2 and lower_wick<body*0.3: patterns.append({"pattern":"SHOOTING_STAR","direction":"BEARISH","score":2})
    if total_range>0 and body<total_range*0.15: patterns.append({"pattern":"DOJI","direction":"NEUTRAL","score":1})
    if (prev2['close']<prev2['open'] and abs(prev['close']-prev['open'])<abs(prev2['close']-prev2['open'])*0.3 and last['close']>last['open'] and last['close']>(prev2['open']+prev2['close'])/2):
        patterns.append({"pattern":"MORNING_STAR","direction":"BULLISH","score":4})
    if (prev2['close']>prev2['open'] and abs(prev['close']-prev['open'])<abs(prev2['close']-prev2['open'])*0.3 and last['close']<last['open'] and last['close']<(prev2['open']+prev2['close'])/2):
        patterns.append({"pattern":"EVENING_STAR","direction":"BEARISH","score":4})
    return patterns

def detect_rsi_divergence(df, rsi_column='rsi', lookback=20):
    if len(df) < lookback or rsi_column not in df.columns: return None, 0
    recent_highs = df['high'].iloc[-lookback:].values; recent_lows = df['low'].iloc[-lookback:].values; recent_rsi = df[rsi_column].iloc[-lookback:].values
    if len(recent_lows)>5:
        min1_idx = np.argmin(recent_lows)
        if min1_idx>2:
            prev_min_idx = np.argmin(recent_lows[:min1_idx-1])
            if recent_lows[min1_idx]<recent_lows[prev_min_idx] and recent_rsi[min1_idx]>recent_rsi[prev_min_idx]: return "BULLISH_DIVERGENCE",4
            if recent_lows[min1_idx]>recent_lows[prev_min_idx] and recent_rsi[min1_idx]<recent_rsi[prev_min_idx]: return "HIDDEN_BULLISH_DIV",3
    if len(recent_highs)>5:
        max1_idx = np.argmax(recent_highs)
        if max1_idx>2:
            prev_max_idx = np.argmax(recent_highs[:max1_idx-1])
            if recent_highs[max1_idx]>recent_highs[prev_max_idx] and recent_rsi[max1_idx]<recent_rsi[prev_max_idx]: return "BEARISH_DIVERGENCE",4
            if recent_highs[max1_idx]<recent_highs[prev_max_idx] and recent_rsi[max1_idx]>recent_rsi[prev_max_idx]: return "HIDDEN_BEARISH_DIV",3
    return None,0

def check_fresh_order_block(df_smc):
    if len(df_smc) < 10: return False, None
    bull_obs = df_smc[df_smc['order_block_bullish']==True]
    if not bull_obs.empty:
        last_idx = bull_obs.index[-1]
        if df_smc['close'].iloc[-1] > df_smc['high'].loc[last_idx]: return True,"BUY"
    bear_obs = df_smc[df_smc['order_block_bearish']==True]
    if not bear_obs.empty:
        last_idx = bear_obs.index[-1]
        if df_smc['close'].iloc[-1] < df_smc['low'].loc[last_idx]: return True,"SELL"
    return False,None

def is_ict_killzone():
    eastern = pytz.timezone('US/Eastern'); now = datetime.now(eastern); hour=now.hour; minute=now.minute; current=hour+minute/60
    if 2<=current<5: return "LONDON",3
    elif 8<=current<11: return "NY",3
    elif 18<=current or current<2: return "ASIA",1
    return None,0

def get_major_trend(df):
    if len(df)<200: return "NEUTRAL"
    ema200 = df['close'].ewm(span=200,adjust=False).mean().iloc[-1]; price=df['close'].iloc[-1]
    if price>ema200*1.01: return "BULLISH"
    elif price<ema200*0.99: return "BEARISH"
    return "NEUTRAL"

# ==========================================
# دوال MTF
# ==========================================
def get_mtf_signal(symbol, current_price):
    timeframes=['15min','1h','4h','1day']; signals=[]; weights={'15min':1,'1h':2,'4h':3,'1day':4}
    for tf in timeframes:
        try:
            df=get_twelvedata_historical(symbol, interval=tf, outputsize=100)
            if df is not None and len(df)>50:
                rsi=calc_rsi(df['close']).iloc[-1]
                if rsi<30: signals.append(('BUY',tf,weights[tf]))
                elif rsi>70: signals.append(('SELL',tf,weights[tf]))
                else: signals.append(('NEUTRAL',tf,0))
        except:
            signals.append(('NEUTRAL',tf,0))
    buy_weight=sum(w for s,tf,w in signals if s=='BUY'); sell_weight=sum(w for s,tf,w in signals if s=='SELL')
    if buy_weight>sell_weight: return "BUY",buy_weight
    elif sell_weight>buy_weight: return "SELL",sell_weight
    return "NEUTRAL",0

def get_daily_trend(symbol):
    try:
        df=get_twelvedata_historical(symbol, interval="1day", outputsize=50)
        if df is not None and len(df)>20:
            ema50=df['close'].ewm(span=50,adjust=False).mean().iloc[-1]; price=df['close'].iloc[-1]
            if price>ema50*1.01: return "BULLISH"
            elif price<ema50*0.99: return "BEARISH"
    except: pass
    return "NEUTRAL"

def confirm_signal(df,signal,bars=1):
    if len(df)<bars: return False
    for i in range(1,bars+1):
        if signal=="BUY" and df['close'].iloc[-i]<df['open'].iloc[-i]: return False
        if signal=="SELL" and df['close'].iloc[-i]>df['open'].iloc[-i]: return False
    return True

# ==========================================
# تحليل DXY وقوة الدولار
# ==========================================
def get_dxy_signal():
    df=get_historical_data("DX-Y.NYB", period="3mo", interval="4h")
    if df is None or len(df)<50: return "NEUTRAL",50,{}
    df['rsi']=calc_rsi(df['close']); df['macd'],df['macd_signal'],_=calc_macd(df['close']); df['ema20']=df['close'].ewm(span=20).mean(); df['ema50']=df['close'].ewm(span=50).mean()
    df_smc=analyze_smc_ict(df); last=df.iloc[-1]; scores={'BUY':0,'SELL':0}; details={}
    if last['close']>last['ema20'] and last['close']>last['ema50']: scores['BUY']+=3; details['Trend']="DXY فوق المتوسطات"
    elif last['close']<last['ema20'] and last['close']<last['ema50']: scores['SELL']+=3; details['Trend']="DXY تحت المتوسطات"
    if last['rsi']<30: scores['BUY']+=2; details['RSI']="تشبع بيعي"
    elif last['rsi']>70: scores['SELL']+=2; details['RSI']="تشبع شرائي"
    if last['macd']>last['macd_signal']: scores['BUY']+=2; details['MACD']="تقاطع صاعد"
    elif last['macd']<last['macd_signal']: scores['SELL']+=2; details['MACD']="تقاطع هابط"
    if df_smc is not None and not df_smc.empty:
        last_smc=df_smc.iloc[-1]
        if last_smc.get('order_block_bullish',False): scores['BUY']+=3; details['OB']="Order Block شراء"
        elif last_smc.get('order_block_bearish',False): scores['SELL']+=3; details['OB']="Order Block بيع"
        if last_smc.get('in_discount',False): scores['BUY']+=1
        elif last_smc.get('in_premium',False): scores['SELL']+=1
    net=scores['BUY']-scores['SELL']
    if net>=3: signal="BUY"
    elif net<=-3: signal="SELL"
    else: signal="NEUTRAL"
    confidence=min(100,50+abs(net)*10)
    return signal,confidence,details

def get_usd_strength_individual():
    pairs={"EUR":"EURUSD=X","GBP":"GBPUSD=X","JPY":"USDJPY=X","CHF":"USDCHF=X","AUD":"AUDUSD=X","NZD":"NZDUSD=X","CAD":"USDCAD=X"}
    results={}
    for currency,pair in pairs.items():
        try:
            df=get_twelvedata_historical(pair, interval="1h", outputsize=24)
            if df is not None and len(df)>1:
                first=df['close'].iloc[0]; last=df['close'].iloc[-1]; change=((last-first)/first)*100
                if currency in ["EUR","GBP","AUD","NZD"]: results[currency]=round(-change,3)
                else: results[currency]=round(change,3)
            else: results[currency]=0.0
        except: results[currency]=0.0
    return results

def get_usd_impact_on_pair(symbol_name, usd_strength):
    if symbol_name and "/" in symbol_name:
        base=symbol_name.split("/")[0].strip(); quote=symbol_name.split("/")[1].strip()
        if quote=="USD" and base in usd_strength:
            impact=-usd_strength[base]
            return impact, f"دولار قوي مقابل {base} يدعم البيع" if impact<0 else f"دولار ضعيف مقابل {base} يدعم الشراء"
        elif base=="USD" and quote in usd_strength:
            impact=usd_strength[quote]
            return impact, f"دولار قوي مقابل {quote} يدعم الشراء" if impact>0 else f"دولار ضعيف مقابل {quote} يدعم البيع"
    return 0,None

def get_dxy_gold_correlation(window=20):
    dxy=get_historical_data("DX-Y.NYB", period="1mo", interval="4h"); gold=get_historical_data("GC=F", period="1mo", interval="4h")
    if dxy is None or gold is None or len(dxy)<window or len(gold)<window: return None,None
    common=dxy.index.intersection(gold.index)
    if len(common)<window: return None,None
    dxy_aligned=dxy.loc[common,'close']; gold_aligned=gold.loc[common,'close']
    rolling=dxy_aligned.rolling(window).corr(gold_aligned)
    return rolling.iloc[-1],rolling

# ==========================================
# FMP API
# ==========================================
@st.cache_data(ttl=300)
def get_fmp_economic_calendar():
    try:
        r=requests.get(f"https://financialmodelingprep.com/api/v3/economic_calendar?apikey={FMP_API_KEY}", timeout=10)
        if r.status_code==200:
            data=r.json(); events=[]
            for item in data[:20]:
                events.append({'country':item.get('country',''),'event':item.get('event',''),'date':item.get('date',''),'time':item.get('time',''),'impact':item.get('impact','')})
            return events
    except: pass
    return []

@st.cache_data(ttl=300)
def get_fmp_news():
    try:
        r=requests.get(f"https://financialmodelingprep.com/api/v3/fmp-news?apikey={FMP_API_KEY}&limit=10", timeout=10)
        if r.status_code==200:
            data=r.json(); news=[]
            for item in data[:10]:
                news.append({'title':item.get('title',''),'source':'FMP','publishedAt':item.get('publishedDate',''),'content':item.get('text','')})
            return news
    except: pass
    return []

# ==========================================
# تحليل أخبار مبسط
# ==========================================
def analyze_news_impact(news_list):
    if not news_list: return {'gold_sentiment':0,'forex_sentiment':0,'overall_sentiment':0,'summary':'لا توجد أخبار','count':0}
    # نسخة مبسطة
    return {'gold_sentiment':0,'forex_sentiment':0,'overall_sentiment':0,'summary':'أخبار متاحة','count':len(news_list)}

def display_news_analysis(news_analysis):
    if news_analysis and news_analysis.get('count',0)>0:
        st.info(news_analysis['summary'])

def display_economic_events(events):
    if events:
        for e in events[:10]:
            st.markdown(f"- {e['country']} - {e['event']} ({e['date']} {e['time']})")

# ==========================================
# تنبيهات وحجم صفقة
# ==========================================
def send_telegram_alert(message):
    return False

def calculate_lot_size(entry, stop, account=100000, risk=1.0, pip_value=10):
    dist=abs(entry-stop)
    if dist==0: return 0.01
    return max(0.01, round(account*(risk/100)/(dist*100000*pip_value/100),2))

# ==========================================
# إعدادات المؤشرات
# ==========================================
def get_indicator_settings(symbol_name):
    if "Gold" in symbol_name or "XAU" in symbol_name or "Silver" in symbol_name or "XAG" in symbol_name: asset="gold"
    elif "BTC" in symbol_name or "ETH" in symbol_name: asset="crypto"
    else: asset="forex"
    settings={'asset_type':asset,'macd':{},'rsi':{},'mfi':{},'bb':{},'ichimoku':{},'atr_period':14}
    if asset=="gold":
        settings['macd']={'fast':5,'slow':13,'signal':4}; settings['rsi']={'period':14,'overbought':80,'oversold':20}; settings['mfi']={'period':9,'overbought':80,'oversold':20}; settings['bb']={'period':20,'std_dev':2.5}; settings['ichimoku']={'tenkan':10,'kijun':30,'senkou':60}
    elif asset=="crypto":
        settings['macd']={'fast':6,'slow':13,'signal':5}; settings['rsi']={'period':14,'overbought':80,'oversold':20}; settings['mfi']={'period':10,'overbought':85,'oversold':15}; settings['bb']={'period':50,'std_dev':2.3}; settings['ichimoku']={'tenkan':10,'kijun':30,'senkou':60}
    else:
        settings['macd']={'fast':12,'slow':26,'signal':9}; settings['rsi']={'period':14,'overbought':70,'oversold':30}; settings['mfi']={'period':14,'overbought':80,'oversold':20}; settings['bb']={'period':20,'std_dev':2}; settings['ichimoku']={'tenkan':9,'kijun':26,'senkou':52}
    return settings

def get_dynamic_weights(df, asset_type="forex"):
    weights={'rsi':2,'macd':3,'bb':2,'vwap':2,'ichimoku':3,'smc':5,'patterns':5,'tbs':5,'mfi':2,'smr':4,'candle':3,'divergence':5,'fresh_ob':4,'fibonacci':3,'chaikin':2}
    if asset_type=="gold": weights.update({'ichimoku':3,'smc':5,'tbs':5,'mfi':2,'chaikin':2})
    elif asset_type=="crypto": weights.update({'ichimoku':4,'smc':5,'tbs':5,'mfi':2,'chaikin':2})
    else: weights.update({'ichimoku':3,'smc':4,'tbs':5,'mfi':2,'chaikin':2})
    return weights

# ==========================================
# حساب المستويات الذكية
# ==========================================
def calculate_trade_levels(df, df_smc, signal, current_price, asset_type):
    stop=None; targets={}
    recent_lows=df['low'].iloc[-5:]; recent_highs=df['high'].iloc[-5:]
    bsl=df_smc['bsl'].iloc[-1] if not df_smc['bsl'].isna().all() else None
    ssl=df_smc['ssl'].iloc[-1] if not df_smc['ssl'].isna().all() else None
    bull_obs=df_smc[df_smc['order_block_bullish']==True]; bear_obs=df_smc[df_smc['order_block_bearish']==True]
    last_bull_ob_low=bull_obs['low'].iloc[-1] if not bull_obs.empty else None
    last_bear_ob_high=bear_obs['high'].iloc[-1] if not bear_obs.empty else None
    if signal=="BUY":
        if ssl and ssl<current_price: stop=ssl-0.1*(current_price-ssl)
        elif last_bull_ob_low and last_bull_ob_low<current_price: stop=last_bull_ob_low
        else: stop=recent_lows.min()
        target1=recent_highs.max()
        target2=bsl if bsl and bsl>current_price else current_price+(current_price-stop)*2
        target3=current_price+(current_price-stop)*3
    else:
        if bsl and bsl>current_price: stop=bsl+0.1*(bsl-current_price)
        elif last_bear_ob_high and last_bear_ob_high>current_price: stop=last_bear_ob_high
        else: stop=recent_highs.max()
        target1=recent_lows.min()
        target2=ssl if ssl and ssl<current_price else current_price-(stop-current_price)*2
        target3=current_price-(stop-current_price)*3
    if signal=="BUY":
        if target1<=current_price: target1=current_price+(current_price-stop)*0.5
        if target2<=target1: target2=target1+(current_price-stop)*0.5
        if target3<=target2: target3=target2+(current_price-stop)*0.5
    else:
        if target1>=current_price: target1=current_price-(stop-current_price)*0.5
        if target2>=target1: target2=target1-(stop-current_price)*0.5
        if target3>=target2: target3=target2-(stop-current_price)*0.5
    targets={'target1':round(target1,5),'target2':round(target2,5),'target3':round(target3,5),'risk':abs(current_price-stop),
             'risk_reward_1':abs(target1-current_price)/abs(stop-current_price) if stop!=current_price else 1,
             'risk_reward_2':abs(target2-current_price)/abs(stop-current_price) if stop!=current_price else 2,
             'risk_reward_3':abs(target3-current_price)/abs(stop-current_price) if stop!=current_price else 3}
    return stop,targets

# ==========================================
# دالة الإشارة المتكاملة (مخففة)
# ==========================================
def generate_advanced_signal(df, current_price, symbol_name="", symbol=""):
    if df is None or len(df)<50:
        return "WAIT",50,0,{},[],None,None,None,None,{},0,{}
    indicator_status={}
    settings=get_indicator_settings(symbol_name); asset_type=settings['asset_type']
    macd_settings=settings['macd']; rsi_settings=settings['rsi']; mfi_settings=settings['mfi']; bb_settings=settings['bb']; ichimoku_settings=settings['ichimoku']
    # حساب المؤشرات مع try
    try: df['rsi']=calc_rsi(df['close'], period=rsi_settings['period']); indicator_status['RSI']='✅'
    except: df['rsi']=pd.Series([np.nan]*len(df)); indicator_status['RSI']='❌'
    try: df['atr']=calc_atr(df, period=settings['atr_period']); indicator_status['ATR']='✅'
    except: df['atr']=pd.Series([np.nan]*len(df)); indicator_status['ATR']='❌'
    try:
        df['macd'],df['macd_signal'],df['macd_histogram']=calc_macd(df['close'], fast=macd_settings['fast'], slow=macd_settings['slow'], signal=macd_settings['signal']); indicator_status['MACD']='✅'
    except: df['macd']=pd.Series([np.nan]*len(df)); df['macd_signal']=pd.Series([np.nan]*len(df)); df['macd_histogram']=pd.Series([np.nan]*len(df)); indicator_status['MACD']='❌'
    try: df['bb_upper'],df['bb_middle'],df['bb_lower']=calc_bollinger_bands(df['close'], period=bb_settings['period'], std_dev=bb_settings['std_dev']); indicator_status['BB']='✅'
    except: df['bb_upper']=df['bb_middle']=df['bb_lower']=pd.Series([np.nan]*len(df)); indicator_status['BB']='❌'
    try: df['vwap']=calc_vwap(df); indicator_status['VWAP']='✅'
    except: df['vwap']=pd.Series([np.nan]*len(df)); indicator_status['VWAP']='❌'
    try:
        tenkan,kijun,senkou_a,senkou_b,chikou=calc_ichimoku(df, tenkan=ichimoku_settings['tenkan'], kijun=ichimoku_settings['kijun'], senkou=ichimoku_settings['senkou'])
        df['tenkan']=tenkan; df['kijun']=kijun; df['senkou_a']=senkou_a; df['senkou_b']=senkou_b; df['chikou']=chikou; indicator_status['Ichimoku']='✅'
    except:
        for col in ['tenkan','kijun','senkou_a','senkou_b','chikou']: df[col]=pd.Series([np.nan]*len(df))
        indicator_status['Ichimoku']='❌'
    try: df['mfi']=calc_mfi(df, period=mfi_settings['period']); indicator_status['MFI']='✅'
    except: df['mfi']=pd.Series([np.nan]*len(df)); indicator_status['MFI']='❌'
    try: df['chaikin_mf']=calc_chaikin_money_flow(df['high'],df['low'],df['close'],df['volume'], period=21); indicator_status['Chaikin']='✅'
    except: df['chaikin_mf']=pd.Series([np.nan]*len(df)); indicator_status['Chaikin']='❌'
    try: df_smc=analyze_smc_ict(df); indicator_status['SMC']='✅'
    except:
        df_smc=df.copy()
        for col in ['order_block_bullish','order_block_bearish','fvg_bullish','fvg_bearish','liquidity_sweep_bullish','liquidity_sweep_bearish','bos_bullish','bos_bearish','mss_bullish','mss_bearish','in_discount','in_premium','tbs_bullish','tbs_bearish','bsl','ssl','smr_bullish','smr_bearish']:
            if col not in df_smc.columns: df_smc[col]=False if col not in ['bsl','ssl'] else np.nan
        indicator_status['SMC']='❌'
    try: patterns,_=analyze_chart_patterns(df); indicator_status['Patterns']='✅'
    except: patterns=[]; indicator_status['Patterns']='❌'
    try: tbs_type,tbs_entry,tbs_stop,tbs_level=detect_tbs(df); indicator_status['TBS']='✅' if tbs_type else '⚪'
    except: tbs_type=tbs_entry=tbs_stop=tbs_level=None; indicator_status['TBS']='❌'

    last=df.iloc[-1]; weights=get_dynamic_weights(df,asset_type); scores={'BUY':0,'SELL':0}; details={}

    daily_trend=get_daily_trend(symbol)
    if daily_trend=="BULLISH": scores['BUY']+=3; details['Daily_Bias']="صاعد"
    elif daily_trend=="BEARISH": scores['SELL']+=3; details['Daily_Bias']="هابط"

    smc_bullish=0; smc_bearish=0
    if not df_smc.empty:
        ls=df_smc.iloc[-1]
        if ls.get('order_block_bullish',False): scores['BUY']+=weights['smc']; smc_bullish+=1
        if ls.get('order_block_bearish',False): scores['SELL']+=weights['smc']; smc_bearish+=1
        if ls.get('fvg_bullish',False): scores['BUY']+=weights['smc']//2; smc_bullish+=0.5
        if ls.get('fvg_bearish',False): scores['SELL']+=weights['smc']//2; smc_bearish+=0.5
        if ls.get('mss_bullish',False): scores['BUY']+=weights['smc']; smc_bullish+=1
        if ls.get('mss_bearish',False): scores['SELL']+=weights['smc']; smc_bearish+=1
        if ls.get('in_discount',False): scores['BUY']+=weights['smc']//2; smc_bullish+=0.5
        if ls.get('in_premium',False): scores['SELL']+=weights['smc']//2; smc_bearish+=0.5
        if ls.get('smr_bullish',False): scores['BUY']+=weights['smr']; smc_bullish+=1
        if ls.get('smr_bearish',False): scores['SELL']+=weights['smr']; smc_bearish+=1
    if tbs_type=="BULLISH": scores['BUY']+=weights['tbs']; smc_bullish+=1
    elif tbs_type=="BEARISH": scores['SELL']+=weights['tbs']; smc_bearish+=1
    if patterns:
        for p in patterns:
            if p['direction']=='BULLISH': scores['BUY']+=weights['patterns']
            else: scores['SELL']+=weights['patterns']

    ind_bull=0; ind_bear=0
    if 'senkou_a' in df.columns and not pd.isna(last['senkou_a']):
        if current_price>last['senkou_a'] and current_price>last['senkou_b']: scores['BUY']+=weights['ichimoku']; ind_bull+=1
        elif current_price<last['senkou_a'] and current_price<last['senkou_b']: scores['SELL']+=weights['ichimoku']; ind_bear+=1
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        if last['rsi']<rsi_settings['oversold']: scores['BUY']+=weights['rsi']; ind_bull+=1
        elif last['rsi']>rsi_settings['overbought']: scores['SELL']+=weights['rsi']; ind_bear+=1
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if last['macd']>last['macd_signal']: scores['BUY']+=weights['macd']; ind_bull+=1
        elif last['macd']<last['macd_signal']: scores['SELL']+=weights['macd']; ind_bear+=1
    if 'mfi' in df.columns and not pd.isna(last['mfi']):
        if last['mfi']<mfi_settings['oversold']: scores['BUY']+=weights['mfi']; ind_bull+=1
        elif last['mfi']>mfi_settings['overbought']: scores['SELL']+=weights['mfi']; ind_bear+=1
    if 'vwap' in df.columns and not pd.isna(last['vwap']):
        if current_price>last['vwap']: scores['BUY']+=weights['vwap']; ind_bull+=1
        else: scores['SELL']+=weights['vwap']; ind_bear+=1
    if 'chaikin_mf' in df.columns and not pd.isna(last['chaikin_mf']):
        if last['chaikin_mf']>0.1: scores['BUY']+=weights['chaikin']; ind_bull+=1
        elif last['chaikin_mf']<-0.1: scores['SELL']+=weights['chaikin']; ind_bear+=1

    # تأثير الدولار
    if symbol_name and "/" in symbol_name and "USD" in symbol_name:
        usd_strength=get_usd_strength_individual()
        impact,msg=get_usd_impact_on_pair(symbol_name,usd_strength)
        if impact>0.5: scores['BUY']+=2; details['USD']=msg
        elif impact<-0.5: scores['SELL']+=2; details['USD']=msg
        dxy_sig,dxy_conf,_=get_dxy_signal()
        if dxy_sig!="NEUTRAL":
            base=symbol_name.split("/")[0].strip(); quote=symbol_name.split("/")[1].strip()
            if quote=="USD":
                if dxy_sig=="BUY": scores['SELL']+=2
                else: scores['BUY']+=2
            elif base=="USD":
                if dxy_sig=="BUY": scores['BUY']+=2
                else: scores['SELL']+=2
    if "Gold" in symbol_name:
        corr,_=get_dxy_gold_correlation()
        if corr is not None and corr>-0.5: scores['BUY']-=1

    # فيبوناتشي ودايفرجنس (اختصار)
    recent_high=df['high'].iloc[-50:].max(); recent_low=df['low'].iloc[-50:].min()
    fib=calc_fibonacci_levels(recent_high,recent_low,current_price)
    if fib:
        if current_price>fib['fib_618']: scores['BUY']+=weights['fibonacci']
        elif current_price<fib['fib_382']: scores['SELL']+=weights['fibonacci']
    div,_=detect_rsi_divergence(df)
    if div and "BULLISH" in div: scores['BUY']+=weights['divergence']
    elif div and "BEARISH" in div: scores['SELL']+=weights['divergence']
    is_fresh,fresh_dir=check_fresh_order_block(df_smc)
    if is_fresh: scores[fresh_dir]+=weights['fresh_ob']

    net_score=scores['BUY']-scores['SELL']; total_weight=sum(weights.values())
    # شروط مخففة
    if net_score>=2 and (smc_bullish>0 or ind_bull>=2): signal="BUY"; confidence=min(85,45+(net_score/total_weight)*100)
    elif net_score<=-2 and (smc_bearish>0 or ind_bear>=2): signal="SELL"; confidence=min(85,45+(abs(net_score)/total_weight)*100)
    else: signal="WAIT"; confidence=50+(net_score/total_weight)*50

    # فلتر انعكاس
    candle_pats=detect_candlestick_patterns(df)
    reversal=False
    if signal=="BUY":
        if last['rsi']>75: reversal=True
        for cp in candle_pats:
            if cp['direction']=='BEARISH' and cp['score']>=3: reversal=True
    elif signal=="SELL":
        if last['rsi']<25: reversal=True
        for cp in candle_pats:
            if cp['direction']=='BULLISH' and cp['score']>=3: reversal=True
    if reversal: confidence*=0.6

    # تأكيد شمعة
    if signal!="WAIT" and not confirm_signal(df,signal,1): confidence*=0.9

    # فلتر الاتجاه اليومي
    if signal!="WAIT" and daily_trend!="NEUTRAL":
        if (signal=="BUY" and daily_trend=="BEARISH") or (signal=="SELL" and daily_trend=="BULLISH"): confidence*=0.75
        else: confidence=min(85,confidence*1.1)

    # MTF
    mtf_signal,mtf_weight=get_mtf_signal(symbol,current_price)
    if signal!="WAIT" and mtf_signal!="NEUTRAL":
        if signal!=mtf_signal: confidence*=0.8
        else: confidence=min(85,confidence*1.1)

    # فلاتر أخرى (مبسطة)
    confidence=max(0,min(85,confidence))

    # توافق
    confluence=0
    if smc_bullish>0 or smc_bearish>0: confluence+=1
    if ind_bull>0 or ind_bear>0: confluence+=1
    if daily_trend!="NEUTRAL": confluence+=1
    if mtf_signal!="NEUTRAL": confluence+=1
    required_confluence=2  # تم التخفيف
    if signal!="WAIT" and confluence<required_confluence: signal="WAIT"

    # حساب مستويات
    stop_loss=entry_price=None; targets={}
    if signal in ["BUY","SELL"] and confidence>=50:  # خفضنا العتبة
        can,msg=can_open_trade(confidence)
        if not can: signal="WAIT"; details['Trade_Limit']=msg
        else:
            entry_price=current_price
            stop_loss,targets=calculate_trade_levels(df,df_smc,signal,current_price,asset_type)
            if stop_loss is None: signal="WAIT"
            else: increment_trade_count()

    if signal in ["BUY","SELL"] and confidence>=70:
        send_telegram_alert(f"إشارة {signal} على {symbol_name} بثقة {confidence:.0f}%")

    tbs_info=(tbs_type,tbs_entry,tbs_stop,tbs_level)
    st.session_state.indicator_status=indicator_status
    return signal,confidence,net_score,details,patterns,tbs_info,stop_loss,entry_price,targets,indicator_status,confluence,{}

# ==========================================
# تجميع الإشارات
# ==========================================
def apply_confluence_filter(df):
    return df

@st.cache_data(ttl=120)
def get_all_signals_with_trades():
    results=[]
    for pair_name,symbol in PAIRS.items():
        try:
            df=get_historical_data(symbol, period="3mo", interval="4h")
            if df is None or len(df)<50: continue
            current_price=df['close'].iloc[-1]
            signal,confidence,net_score,_,_,_,stop_loss,entry_price,targets,_,_,_=generate_advanced_signal(df,current_price,pair_name,symbol)
            price_str=f"${current_price:,.2f}" if "Gold" in pair_name or "Silver" in pair_name or "Bitcoin" in pair_name or "Ethereum" in pair_name else f"{current_price:.4f}"
            results.append({"الزوج":pair_name,"الإشارة":signal,"الثقة":round(confidence,1),"النتيجة":net_score,"السعر":price_str})
        except: continue
    return pd.DataFrame(results)

class TradeManager:
    def __init__(self):
        self.trades_file="trades_data.json"
        self.load_trades()
    def load_trades(self):
        try:
            with open(self.trades_file,"r",encoding='utf-8') as f:
                data=json.load(f); self.open_trades=data.get("open_trades",[]); self.closed_trades=data.get("closed_trades",[])
        except: self.open_trades=[]; self.closed_trades=[]
    def save_trades(self):
        with open(self.trades_file,"w",encoding='utf-8') as f:
            json.dump({"open_trades":self.open_trades,"closed_trades":self.closed_trades},f,indent=2,ensure_ascii=False)
    def add_trade(self,data):
        tid=f"T{len(self.open_trades)+len(self.closed_trades)+1:03d}"
        trade={"id":tid,"date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"direction":data["direction"],"entry":data["entry"],"lots":data["lots"],"stop_loss":data["stop_loss"],"take_profit":data["take_profit"],"target1":data.get("target1"),"target2":data.get("target2"),"target3":data.get("target3"),"partial_close_done":False,"partial_close_price":data.get("target1"),"trailing_enabled":data.get("trailing_enabled",False),"trailing_distance":data.get("trailing_distance",0),"highest_price":data["entry"],"lowest_price":data["entry"],"status":"open","stage":0,"notes":data.get("notes","")}
        self.open_trades.append(trade); self.save_trades(); return tid
    def update_trailing_stop(self,tid,price):
        for t in self.open_trades:
            if t["id"]==tid and t["status"]=="open" and t["trailing_enabled"]:
                if t["direction"]=="BUY" and price>t["highest_price"]:
                    t["highest_price"]=price; new_stop=t["highest_price"]-t["trailing_distance"]
                    if new_stop>t["stop_loss"]: t["stop_loss"]=new_stop; self.save_trades(); return True
                elif t["direction"]=="SELL" and price<t["lowest_price"]:
                    t["lowest_price"]=price; new_stop=t["lowest_price"]+t["trailing_distance"]
                    if new_stop<t["stop_loss"]: t["stop_loss"]=new_stop; self.save_trades(); return True
        return False
    def check_partial_close(self,tid,price):
        for t in self.open_trades:
            if t["id"]==tid and t["status"]=="open" and not t["partial_close_done"] and t["partial_close_price"]:
                if t["direction"]=="BUY" and price>=t["partial_close_price"]:
                    t["lots"]/=2; t["stop_loss"]=t["entry"]; t["partial_close_done"]=True; t["stage"]=1; self.save_trades(); return True,"إغلاق جزئي"
                elif t["direction"]=="SELL" and price<=t["partial_close_price"]:
                    t["lots"]/=2; t["stop_loss"]=t["entry"]; t["partial_close_done"]=True; t["stage"]=1; self.save_trades(); return True,"إغلاق جزئي"
        return False,""
    def close_trade(self,tid,price):
        for i,t in enumerate(self.open_trades):
            if t["id"]==tid:
                t["exit"]=price; t["status"]="closed"
                pips=(price-t["entry"])*100 if t["direction"]=="BUY" else (t["entry"]-price)*100
                profit=pips*t["lots"]*0.1
                if "partial_profit" in t: profit+=t["partial_profit"]
                t["profit"]=round(profit,2); t["result"]="win" if profit>0 else "loss"; t["close_date"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.closed_trades.append(t); self.open_trades.pop(i); self.save_trades(); return profit
        return None

def detect_reversal(df,trade):
    if df is None or len(df)<20: return False,""
    last=df.iloc[-1]; prev=df.iloc[-2]; direction=trade["direction"]; signals=[]
    if 'rsi' in df.columns and not pd.isna(last['rsi']):
        if direction=="BUY" and last['rsi']>70: signals.append("RSI فوق 70")
        elif direction=="SELL" and last['rsi']<30: signals.append("RSI تحت 30")
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        if direction=="BUY" and last['macd']<last['macd_signal'] and prev['macd']>=prev['macd_signal']: signals.append("MACD هابط")
        elif direction=="SELL" and last['macd']>last['macd_signal'] and prev['macd']<=prev['macd_signal']: signals.append("MACD صاعد")
    return (True," | ".join(signals)) if signals else (False,"")

def explain_decision(signal,confidence,net_score,details,mtf_signal,mtf_count,patterns,tbs_info,df,current_price,stop_loss,entry_price,targets):
    exp=""
    if signal=="BUY": exp="🔹 شراء\n"
    elif signal=="SELL": exp="🔻 بيع\n"
    else: exp="⏳ انتظار\n"
    exp+=f"الثقة: {confidence:.0f}% | النتيجة: {net_score}\n"
    if stop_loss and entry_price and targets:
        exp+=f"الدخول: {entry_price:.4f} | الوقف: {stop_loss:.4f} | الأهداف: {targets['target1']:.4f}, {targets['target2']:.4f}, {targets['target3']:.4f}"
    return exp

def get_market_status():
    eastern=pytz.timezone('US/Eastern'); now=datetime.now(eastern); weekday=now.weekday()
    open_time=now.replace(hour=18,minute=0,second=0,microsecond=0); close_time=now.replace(hour=17,minute=0,second=0,microsecond=0)
    if weekday==5: return "CLOSED","عطلة نهاية الأسبوع",open_time+timedelta(days=1),close_time
    if weekday==6:
        if now<open_time: return "CLOSED","انتظار الافتتاح",open_time,close_time
        return "OPEN","مفتوح (الأحد)",close_time,close_time
    if 0<=weekday<=3:
        if close_time<=now<open_time: return "CLOSED","استراحة",open_time,close_time
        return "OPEN","مفتوح",close_time,close_time
    if weekday==4:
        if now<close_time: return "OPEN","مفتوح (الجمعة)",close_time,close_time
        return "CLOSED","نهاية الأسبوع",open_time+timedelta(days=2),close_time
    return "UNKNOWN","",None,None

def time_remaining(dt):
    if dt is None: return "N/A"
    diff=dt-datetime.now(pytz.timezone('US/Eastern'))
    if diff.total_seconds()<0: return "انتهى"
    return f"{int(diff.total_seconds()//3600)}h {int((diff.total_seconds()%3600)//60)}m"

# ==========================================
# الواجهة
# ==========================================
with st.sidebar:
    st.markdown("### 🔑 إعدادات API")
    with st.expander("تغيير المفاتيح"):
        tw=st.text_input("Twelve Data", value=st.session_state.user_twelve_key, type="password")
        ff=st.text_input("FastForex", value=st.session_state.user_fastforex_key, type="password")
        gk=st.text_input("GoldAPI", value=st.session_state.user_gold_key, type="password")
        fk=st.text_input("FMP", value=st.session_state.user_fmp_key, type="password")
        ak=st.text_input("Alpha Vantage", value=st.session_state.user_alpha_key, type="password")
        if st.button("💾 حفظ", key="save_keys", width='stretch'):
            st.session_state.user_twelve_key=tw; st.session_state.user_fastforex_key=ff; st.session_state.user_gold_key=gk; st.session_state.user_fmp_key=fk; st.session_state.user_alpha_key=ak
            st.rerun()
    st.markdown("---")
    status,status_text,next_event,close_time=get_market_status()
    st.markdown(f"### {'🟢' if status=='OPEN' else '🔴'} {status_text}")
    st.markdown(f"⏳ {time_remaining(next_event)}")
    st.markdown("---")
    st.markdown("### 📈 صفقات اليوم")
    remaining=4-st.session_state.daily_trade_count
    st.progress(st.session_state.daily_trade_count/4)
    st.caption(f"{st.session_state.daily_trade_count}/4 | متبقي {remaining}")
    st.markdown("---")
    st.markdown("### 💪 قوة الدولار")
    if st.button("🔄 تحديث", key="usd_refresh", width='stretch'):
        st.session_state.usd_strength_cache=get_usd_strength_individual(); st.rerun()
    usd_strength=st.session_state.usd_strength_cache if st.session_state.usd_strength_cache else get_usd_strength_individual()
    for cur,val in sorted(usd_strength.items(), key=lambda x:x[1], reverse=True):
        st.markdown(f"{'🟢' if val>0.3 else '🔴' if val<-0.3 else '🟡'} USD/{cur}: {val:+.2f}%")
    st.markdown("---")
    st.markdown("### 💰 قوة العملات")
    if st.button("🔄 تحديث", key="curr_refresh", width='stretch'):
        st.session_state.currency_strength=get_currency_strength(); st.rerun()
    if st.session_state.currency_strength:
        for cur,val in sorted(st.session_state.currency_strength.items(), key=lambda x:x[1], reverse=True):
            st.markdown(f"{'🟢' if val>0.5 else '🟡' if val>-0.5 else '🔴'} {cur}: {val:+.2f}%")
    st.markdown("---")
    st.markdown("### 📋 جميع الإشارات")
    if st.button("🔄 تحديث الكل", key="all_refresh", width='stretch'):
        st.session_state.all_signals=get_all_signals_with_trades(); st.rerun()
    if st.session_state.all_signals is not None and not st.session_state.all_signals.empty:
        df_sig=st.session_state.all_signals.copy()
        df_sig["الإشارة"]=df_sig["الإشارة"].replace({"BUY":"🟢","SELL":"🔴","WAIT":"⚪"})
        st.dataframe(df_sig[["الزوج","الإشارة","الثقة","السعر"]], hide_index=True, use_container_width=True, height=250)
    st.markdown("---")
    selected_pair_name=st.selectbox("اختر الزوج", list(PAIRS.keys()), index=0)
    selected_symbol=PAIRS[selected_pair_name]
    if st.button("➕ صفقة جديدة", key="new_trade", width='stretch'):
        st.session_state.show_form=not st.session_state.show_form; st.rerun()

# ==========================================
# المنطقة الرئيسية
# ==========================================
current_price,change=get_spot_price(selected_symbol)
if current_price is None: current_price=0; change=0
df=get_historical_data(selected_symbol, period="3mo", interval="4h")
if df is None:
    st.error("⚠️ تعذر تحميل البيانات. تأكد من الاتصال بالإنترنت.")
    st.stop()
else:
    st.success(f"✅ تم جلب {len(df)} شمعة")

signal,confidence,net_score,details,patterns,tbs_info,stop_loss,entry_price,targets,indicator_status,confluence,extra=generate_advanced_signal(df,current_price,selected_pair_name,selected_symbol)
mtf_signal,mtf_weight=get_mtf_signal(selected_symbol,current_price)

if "Gold" in selected_pair_name or "Silver" in selected_pair_name or "Bitcoin" in selected_pair_name or "Ethereum" in selected_pair_name:
    price_format="${:,.2f}"
else:
    price_format="{:.4f}"

st.markdown(f"""
<div class="price-card">
    <div class="price-label">{selected_pair_name}</div>
    <div class="price-value">{price_format.format(current_price)}</div>
    <div class="price-change" style="color:{'#00ff88' if change>=0 else '#ff4444'};">{change:+.2f}%</div>
</div>
""", unsafe_allow_html=True)

if st.button("🔄 تحديث", key="data_refresh", width='stretch'):
    st.cache_data.clear(); st.rerun()

# DXY
if selected_pair_name and "/" in selected_pair_name and "USD" in selected_pair_name:
    dxy_sig,dxy_conf,_=get_dxy_signal()
    st.markdown(f"### 💵 DXY: {dxy_sig} ({dxy_conf:.0f}%)")

# Gold correlation
if "Gold" in selected_pair_name:
    corr,_=get_dxy_gold_correlation()
    if corr is not None:
        st.metric("ارتباط الذهب بالدولار", f"{corr:.3f}")
        if corr>-0.5: st.warning("ضعيف")

with st.expander("🔍 حالة المؤشرات"):
    for n,s in indicator_status.items():
        if '✅' in s: st.success(f"{n}: {s}")
        elif '⚪' in s: st.warning(f"{n}: {s}")
        else: st.error(f"{n}: {s}")

if st.session_state.show_indicators:
    cols=st.columns(6)
    last=df.iloc[-1]
    cols[0].metric("RSI", f"{last['rsi']:.1f}" if not pd.isna(last['rsi']) else "N/A")
    cols[1].metric("ATR", f"{last['atr']:.2f}" if not pd.isna(last['atr']) else "N/A")
    cols[2].metric("VWAP", f"{last['vwap']:.2f}" if not pd.isna(last['vwap']) else "N/A")
    cols[3].metric("MFI", f"{last['mfi']:.1f}" if not pd.isna(last['mfi']) else "N/A")
    cols[4].metric("MACD", f"{last['macd']:.4f}" if not pd.isna(last['macd']) else "N/A")
    cols[5].metric("Chaikin", f"{last['chaikin_mf']:.2f}" if not pd.isna(last['chaikin_mf']) else "N/A")

st.markdown("### 📊 درجة التوافق")
st.progress(confluence/4)
st.markdown(f"**{confluence}/4**")

if signal in ["BUY","SELL"] and confidence>=50 and stop_loss and entry_price and targets:
    direction_text="شراء" if signal=="BUY" else "بيع"
    suggested_lot=calculate_lot_size(entry_price,stop_loss)
    st.markdown(f"""
    <div class="suggested-trade">
        <b>{direction_text}</b> (ثقة {confidence:.0f}%)<br>
        <b>📍 الدخول:</b> {price_format.format(entry_price)}<br>
        <b>🛑 الوقف:</b> {price_format.format(stop_loss)}<br>
        <div class="target-zone">🎯 الهدف1: {price_format.format(targets['target1'])}</div>
        <div class="target-zone">🎯 الهدف2: {price_format.format(targets['target2'])}</div>
        <div class="target-zone">🎯 الهدف3: {price_format.format(targets['target3'])}</div>
        <b>💰 اللوت:</b> {suggested_lot}
    </div>
    """, unsafe_allow_html=True)
    if st.button("➕ إضافة", key="add_trade", width='stretch'):
        tm=TradeManager()
        tm.add_trade({"direction":signal,"entry":entry_price,"lots":suggested_lot,"stop_loss":stop_loss,"take_profit":targets['target2'],"target1":targets['target1'],"target2":targets['target2'],"target3":targets['target3'],"trailing_enabled":True,"trailing_distance":last['atr']*0.3 if not pd.isna(last['atr']) else 1})
        st.success("تمت الإضافة")
        st.rerun()
else:
    st.info("لا توجد صفقة مقترحة حالياً")

st.markdown("### 🧠 الإشارة")
sig_color="#ffaa00" if signal=="WAIT" else ("#00ff88" if signal=="BUY" else "#ff4444")
st.markdown(f'<div class="signal-box"><div class="signal-text" style="color:{sig_color};">{signal}</div><div class="signal-confidence">الثقة: {confidence:.0f}% | النتيجة: {net_score}</div></div>', unsafe_allow_html=True)

with st.expander("📝 الشرح"):
    st.text(explain_decision(signal,confidence,net_score,details,mtf_signal,mtf_weight,patterns,tbs_info,df,current_price,stop_loss,entry_price,targets))

# التقويم والأخبار (اختصار)
st.markdown("### 📅 التقويم الاقتصادي")
if st.button("🔄 تحديث التقويم", key="cal_refresh"):
    st.session_state.economic_events=get_fmp_economic_calendar()
if st.session_state.economic_events:
    display_economic_events(st.session_state.economic_events)

st.markdown("### 📰 الأخبار")
if st.button("🔄 تحديث الأخبار", key="news_refresh"):
    news=get_fmp_news()
    if news:
        st.session_state.news_analysis=analyze_news_impact(news)
if st.session_state.news_analysis:
    display_news_analysis(st.session_state.news_analysis)

# إدارة الصفقات
st.markdown("### 💼 الصفقات")
tm=TradeManager()
for t in tm.open_trades:
    if t["status"]=="open":
        if t["trailing_enabled"]: tm.update_trailing_stop(t["id"],current_price)
        is_partial,_=tm.check_partial_close(t["id"],current_price)
        if is_partial: st.success("إغلاق جزئي")
        is_rev,msg=detect_reversal(df,t)
        if is_rev: st.warning(f"انعكاس محتمل {t['id']}: {msg}")
        st.markdown(f"<div class='trade-row'>{t['id']} {t['direction']} دخول:{t['entry']} وقف:{t['stop_loss']} هدف:{t['take_profit']}</div>", unsafe_allow_html=True)
        col1,col2=st.columns(2)
        if col1.button(f"إغلاق {t['id']}", key=f"close_{t['id']}"):
            p=tm.close_trade(t["id"],current_price)
            st.success(f"أغلق بربح {p:.2f}" if p else "تم الإغلاق")
            st.rerun()
        if col2.button(f"كشف انعكاس {t['id']}", key=f"rev_{t['id']}"):
            is_rev,msg=detect_reversal(df,t)
            st.warning(msg) if is_rev else st.success("لا انعكاس")
if not tm.open_trades:
    st.info("لا توجد صفقات")

if st.session_state.show_form:
    with st.form("manual"):
        direction=st.selectbox("اتجاه",["BUY","SELL"])
        entry=st.number_input("دخول", value=float(current_price))
        stop=st.number_input("وقف", value=float(current_price-20 if "Gold" in selected_pair_name else 0.001))
        t1=st.number_input("هدف1", value=float(entry+20 if direction=="BUY" else entry-20))
        t2=st.number_input("هدف2", value=float(entry+35 if direction=="BUY" else entry-35))
        t3=st.number_input("هدف3", value=float(entry+55 if direction=="BUY" else entry-55))
        lots=st.number_input("لوت (0 تلقائي)", value=0.0, step=0.01)
        if st.form_submit_button("إضافة"):
            if lots==0: lots=calculate_lot_size(entry,stop)
            tm.add_trade({"direction":direction,"entry":entry,"lots":lots,"stop_loss":stop,"take_profit":t2,"target1":t1,"target2":t2,"target3":t3,"trailing_enabled":False})
            st.success("تمت الإضافة")
            st.session_state.show_form=False
            st.rerun()

# الرسم
st.markdown("### 📈 الرسم")
df_smc=analyze_smc_ict(df)
df['ema20']=df['close'].ewm(span=20).mean(); df['ema50']=df['close'].ewm(span=50).mean(); df['ema200']=df['close'].ewm(span=200).mean()
fig=make_subplots(rows=3,cols=1,shared_xaxes=True,vertical_spacing=0.05,row_heights=[0.6,0.2,0.2])
fig.add_trace(go.Scatter(x=df.index,y=df['close'],name='سعر',line=dict(color='gold')),row=1,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['ema20'],name='EMA20',line=dict(color='orange',dash='dash')),row=1,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['ema50'],name='EMA50',line=dict(color='red',dash='dash')),row=1,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['ema200'],name='EMA200',line=dict(color='purple',dash='dash')),row=1,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['bb_upper'],name='BB',line=dict(color='gray',dash='dot')),row=1,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['bb_lower'],name='BB',line=dict(color='gray',dash='dot')),row=1,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['vwap'],name='VWAP',line=dict(color='blue')),row=1,col=1)
if not df_smc['bsl'].isna().all():
    fig.add_hline(y=df_smc['bsl'].iloc[-1], line_dash="dash", line_color="green", row=1, col=1)
if not df_smc['ssl'].isna().all():
    fig.add_hline(y=df_smc['ssl'].iloc[-1], line_dash="dash", line_color="red", row=1, col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['rsi'],name='RSI',line=dict(color='purple')),row=2,col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['macd'],name='MACD',line=dict(color='blue')),row=3,col=1)
fig.add_trace(go.Scatter(x=df.index,y=df['macd_signal'],name='Signal',line=dict(color='red')),row=3,col=1)
fig.add_bar(x=df.index,y=df['macd_histogram'],name='Hist',marker_color='gray',opacity=0.3,row=3,col=1)
fig.update_layout(height=800, template='plotly_dark')
st.plotly_chart(fig, use_container_width=True)

st.markdown("<div class='footer'><span class='brand'>▲ BLACK PYRAMID v2002</span></div>", unsafe_allow_html=True)
