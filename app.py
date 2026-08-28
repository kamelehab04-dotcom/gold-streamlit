# BLACK PYRAMID PRO â€” Confluence Trading Engine
# Streamlit app | Gold + FX + Crypto
# Important: this is a decision-support/backtesting-oriented signal engine.
# It does NOT guarantee profitable trades.

import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
import requests


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="BLACK PYRAMID PRO",
    page_icon="â–²",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAIRS = {
    "XAU/USD (Gold)": "XAUUSD=X",
    "XAG/USD (Silver)": "XAGUSD=X",
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
    "GBP/JPY": "GBPJPY=X",
    "BTC/USD (Bitcoin)": "BTC-USD",
    "ETH/USD (Ethereum)": "ETH-USD",
}

MAJOR_SCAN = [
    "XAU/USD (Gold)",
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
]

DATA_SYMBOLS = {
    "XAUUSD=X": ["XAUUSD=X", "GC=F"],
    "XAGUSD=X": ["XAGUSD=X", "SI=F"],
    "DX-Y.NYB": ["DX-Y.NYB", "DX=F"],
}

STATE_FILE = "black_pyramid_state.json"


# =========================================================
# SECRETS
# =========================================================

def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
        return str(value) if value else default
    except Exception:
        return os.getenv(name, default)


GOLD_API_KEY = get_secret("GOLD_API_KEY")
NEWS_API_KEY = get_secret("NEWS_API_KEY")


# =========================================================
# STATE / TRADE LOCK
# =========================================================

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active_trade": None, "closed_trades": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


if "bp_state" not in st.session_state:
    st.session_state.bp_state = load_state()


# =========================================================
# DATA
# =========================================================

@st.cache_data(ttl=45, show_spinner=False)
def download_ohlcv(symbol: str, period: str, interval: str):
    symbols = DATA_SYMBOLS.get(symbol, [symbol])
    for sym in symbols:
        try:
            df = yf.download(
                sym,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if df is None or df.empty:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]

            df.columns = [str(c).lower() for c in df.columns]
            required = ["open", "high", "low", "close"]
            if not all(c in df.columns for c in required):
                continue

            if "volume" not in df.columns:
                df["volume"] = 0.0

            df = df[required + ["volume"]].copy()
            for c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

            df = df.dropna(subset=["open", "high", "low", "close"])
            df = df[~df.index.duplicated(keep="last")]
            df = df.sort_index()

            if len(df) >= 100:
                return df

        except Exception:
            continue

    return None


@st.cache_data(ttl=15, show_spinner=False)
def get_live_price(symbol: str):
    # XAU/USD spot
    if symbol == "XAUUSD=X" and GOLD_API_KEY:
        try:
            r = requests.get(
                "https://www.goldapi.io/api/XAU/USD",
                headers={
                    "x-access-token": GOLD_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=8,
            )
            if r.ok:
                data = r.json()
                price = float(data.get("price", 0))
                change = float(data.get("change_percent", 0))
                if price > 0:
                    return price, change, "GoldAPI Spot"
        except Exception:
            pass

    try:
        df = download_ohlcv(symbol, "5d", "5m")
        if df is not None and not df.empty:
            price = float(df["close"].iloc[-1])
            first = float(df["close"].iloc[0])
            change = ((price - first) / first * 100) if first else 0.0
            return price, change, "yfinance"
    except Exception:
        pass

    return None, None, "Unavailable"


# =========================================================
# INDICATORS â€” NO LOOK-AHEAD
# =========================================================

def rsi_wilder(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr_wilder(df, period=14):
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def adx_wilder(df, period=14):
    high, low = df["high"], df["low"]
    up = high.diff()
    down = -low.diff()

    plus_dm = pd.Series(
        np.where((up > down) & (up > 0), up, 0.0), index=df.index
    )
    minus_dm = pd.Series(
        np.where((down > up) & (down > 0), down, 0.0), index=df.index
    )

    atr = atr_wilder(df, period)
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr

    denom = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / denom
    adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return adx, plus_di, minus_di


def macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    line = ema12 - ema26
    signal = line.ewm(span=9, adjust=False).mean()
    return line, signal, line - signal


def add_indicators(df):
    df = df.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    df["rsi"] = rsi_wilder(df["close"])
    df["atr"] = atr_wilder(df)
    df["adx"], df["plus_di"], df["minus_di"] = adx_wilder(df)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(df["close"])

    typical = (df["high"] + df["low"] + df["close"]) / 3
    volume = df["volume"].replace(0, np.nan)
    if volume.notna().sum() >= 20:
        df["vwap"] = (typical * volume).cumsum() / volume.cumsum()
    else:
        # FX feeds often have unusable volume; do not fabricate volume.
        df["vwap"] = np.nan

    df["range"] = df["high"] - df["low"]
    df["body"] = (df["close"] - df["open"]).abs()
    df["body_ratio"] = df["body"] / df["range"].replace(0, np.nan)

    return df


# =========================================================
# STRUCTURE / LIQUIDITY / SMC
# =========================================================

def market_structure(df, lookback=5):
    """
    Uses confirmed historical highs/lows only.
    No future candles are used for the current signal.
    """
    d = df.copy()
    prev_high = d["high"].rolling(lookback).max().shift(1)
    prev_low = d["low"].rolling(lookback).min().shift(1)

    d["bos_bull"] = d["close"] > prev_high
    d["bos_bear"] = d["close"] < prev_low

    # Recent directional state
    state = 0
    states = []
    for i in range(len(d)):
        if bool(d["bos_bull"].iloc[i]):
            state = 1
        elif bool(d["bos_bear"].iloc[i]):
            state = -1
        states.append(state)
    d["structure"] = states
    return d


def liquidity_sweep(df, lookback=20):
    d = df.copy()
    prior_high = d["high"].rolling(lookback).max().shift(1)
    prior_low = d["low"].rolling(lookback).min().shift(1)

    # Bullish sweep = takes sell-side liquidity then closes back above it.
    d["sweep_bull"] = (d["low"] < prior_low) & (d["close"] > prior_low)

    # Bearish sweep = takes buy-side liquidity then closes back below it.
    d["sweep_bear"] = (d["high"] > prior_high) & (d["close"] < prior_high)
    return d


def detect_fvg(df):
    d = df.copy()
    d["fvg_bull"] = d["low"] > d["high"].shift(2)
    d["fvg_bear"] = d["high"] < d["low"].shift(2)

    d["fvg_bull_low"] = np.where(
        d["fvg_bull"], d["high"].shift(2), np.nan
    )
    d["fvg_bull_high"] = np.where(
        d["fvg_bull"], d["low"], np.nan
    )
    d["fvg_bear_low"] = np.where(
        d["fvg_bear"], d["high"], np.nan
    )
    d["fvg_bear_high"] = np.where(
        d["fvg_bear"], d["low"].shift(2), np.nan
    )
    return d


def detect_order_blocks(df, displacement_mult=1.2):
    d = df.copy()
    d["ob_bull"] = False
    d["ob_bear"] = False

    atr = d["atr"]
    for i in range(2, len(d)):
        body = abs(d["close"].iloc[i] - d["open"].iloc[i])
        atr_i = atr.iloc[i]
        if pd.isna(atr_i) or atr_i <= 0:
            continue

        # Bullish displacement after a bearish candle.
        if (
            d["close"].iloc[i] > d["open"].iloc[i]
            and body >= atr_i * displacement_mult
            and d["close"].iloc[i - 1] < d["open"].iloc[i - 1]
        ):
            d.iloc[i - 1, d.columns.get_loc("ob_bull")] = True

        # Bearish displacement after a bullish candle.
        if (
            d["close"].iloc[i] < d["open"].iloc[i]
            and body >= atr_i * displacement_mult
            and d["close"].iloc[i - 1] > d["open"].iloc[i - 1]
        ):
            d.iloc[i - 1, d.columns.get_loc("ob_bear")] = True

    return d


def smc_features(df):
    d = market_structure(df, 5)
    d = liquidity_sweep(d, 20)
    d = detect_fvg(d)
    d = detect_order_blocks(d)

    high50 = d["high"].rolling(50).max()
    low50 = d["low"].rolling(50).min()
    mid50 = (high50 + low50) / 2
    d["premium"] = d["close"] > mid50
    d["discount"] = d["close"] < mid50

    return d


# =========================================================
# MTF
# =========================================================

def resample_4h(df1h):
    d = df1h.copy()
    d = d.resample("4h", label="right", closed="right").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    return d.dropna()


def timeframe_bias(df):
    if df is None or len(df) < 220:
        return "WAIT", 0

    d = smc_features(add_indicators(df))
    last = d.iloc[-1]

    bull = 0
    bear = 0

    if last["close"] > last["ema200"]:
        bull += 2
    else:
        bear += 2

    if last["ema20"] > last["ema50"]:
        bull += 2
    elif last["ema20"] < last["ema50"]:
        bear += 2

    if last["structure"] > 0:
        bull += 2
    elif last["structure"] < 0:
        bear += 2

    if last["adx"] >= 20:
        if last["plus_di"] > last["minus_di"]:
            bull += 1
        elif last["minus_di"] > last["plus_di"]:
            bear += 1

    if bull >= bear + 2:
        return "BULLISH", bull
    if bear >= bull + 2:
        return "BEARISH", bear
    return "NEUTRAL", max(bull, bear)


@st.cache_data(ttl=60, show_spinner=False)
def get_mtf(symbol):
    h1 = download_ohlcv(symbol, "90d", "1h")
    m15 = download_ohlcv(symbol, "30d", "15m")
    if h1 is None or m15 is None:
        return {
            "4H": ("WAIT", 0),
            "1H": ("WAIT", 0),
            "15M": ("WAIT", 0),
            "h1": None,
            "m15": None,
        }

    h1i = add_indicators(h1)
    h4 = resample_4h(h1)
    h4i = add_indicators(h4)
    m15i = add_indicators(m15)

    return {
        "4H": timeframe_bias(h4i),
        "1H": timeframe_bias(h1i),
        "15M": timeframe_bias(m15i),
        "h1": h1i,
        "m15": m15i,
    }


# =========================================================
# DXY FILTER
# =========================================================

@st.cache_data(ttl=60, show_spinner=False)
def get_dxy_context():
    dxy = download_ohlcv("DX-Y.NYB", "90d", "1h")
    if dxy is None:
        return {"bias": "UNKNOWN", "corr": 0.0, "df": None}

    di = add_indicators(dxy)
    bias, _ = timeframe_bias(di)
    return {"bias": bias, "corr": 0.0, "df": di}


def dxy_relation(symbol, gold_or_fx_df):
    if symbol == "DX-Y.NYB":
        return "SELF", 0.0, "NEUTRAL"

    ctx = get_dxy_context()
    dxy = ctx["df"]
    if dxy is None or gold_or_fx_df is None:
        return "UNKNOWN", 0.0, "UNKNOWN"

    common = gold_or_fx_df.index.intersection(dxy.index)
    if len(common) < 40:
        return "UNKNOWN", 0.0, "UNKNOWN"

    a = gold_or_fx_df.loc[common, "close"].pct_change().dropna()
    b = dxy.loc[common, "close"].pct_change().dropna()
    common2 = a.index.intersection(b.index)
    if len(common2) < 30:
        return "UNKNOWN", 0.0, "UNKNOWN"

    corr = float(a.loc[common2].tail(60).corr(b.loc[common2].tail(60)))

    # Gold is normally inversely related to DXY.
    if symbol == "XAUUSD=X":
        relation = "INVERSE"
    else:
        relation = "DIRECT"

    return relation, corr, ctx["bias"]


# =========================================================
# SETUP / ENTRY / SL / TP
# =========================================================

def latest_zone(d, direction):
    look = d.tail(80)

    if direction == "BUY":
        ob = look[look["ob_bull"]]
        if not ob.empty:
            row = ob.iloc[-1]
            return float(row["low"]), float(row["high"])

        fvg = look[look["fvg_bull"]]
        if not fvg.empty:
            row = fvg.iloc[-1]
            return float(row["fvg_bull_low"]), float(row["fvg_bull_high"])

    else:
        ob = look[look["ob_bear"]]
        if not ob.empty:
            row = ob.iloc[-1]
            return float(row["low"]), float(row["high"])

        fvg = look[look["fvg_bear"]]
        if not fvg.empty:
            return float(fvg["fvg_bear_low"].iloc[-1]), float(fvg["fvg_bear_high"].iloc[-1])

    return None


def build_trade(d, direction, live_price):
    atr = float(d["atr"].iloc[-1])
    if not np.isfinite(atr) or atr <= 0:
        return None

    zone = latest_zone(d, direction)
    recent_low = float(d["low"].tail(30).min())
    recent_high = float(d["high"].tail(30).max())

    if direction == "BUY":
        structural_stop = recent_low
        if zone:
            structural_stop = min(structural_stop, zone[0])

        stop = min(structural_stop, live_price - atr * 1.2)
        risk = live_price - stop

        if risk <= atr * 0.45:
            risk = atr * 0.8
            stop = live_price - risk

        tp1 = live_price + risk * 1.5
        tp2 = live_price + risk * 2.0
        tp3 = live_price + risk * 3.0

    else:
        structural_stop = recent_high
        if zone:
            structural_stop = max(structural_stop, zone[1])

        stop = max(structural_stop, live_price + atr * 1.2)
        risk = stop - live_price

        if risk <= atr * 0.45:
            risk = atr * 0.8
            stop = live_price + risk

        tp1 = live_price - risk * 1.5
        tp2 = live_price - risk * 2.0
        tp3 = live_price - risk * 3.0

    rr = abs(tp2 - live_price) / abs(live_price - stop)

    if rr < 1.8:
        return None

    return {
        "direction": direction,
        "entry": round(float(live_price), 4),
        "stop_loss": round(float(stop), 4),
        "target1": round(float(tp1), 4),
        "target2": round(float(tp2), 4),
        "target3": round(float(tp3), 4),
        "risk_distance": round(float(abs(live_price - stop)), 4),
        "rr": round(float(rr), 2),
    }


def analyze_symbol(name, symbol):
    live, change, source = get_live_price(symbol)
    mtf = get_mtf(symbol)

    if live is None or mtf["h1"] is None or mtf["m15"] is None:
        return None

    h1 = smc_features(add_indicators(mtf["h1"]))
    m15 = smc_features(add_indicators(mtf["m15"]))

    last1 = h1.iloc[-1]
    last15 = m15.iloc[-1]

    b4, _ = mtf["4H"]
    b1, _ = mtf["1H"]
    b15, _ = mtf["15M"]

    buy = 0.0
    sell = 0.0
    reasons_buy = []
    reasons_sell = []

    # ----------------------------
    # HARD TREND FILTER
    # ----------------------------
    if b4 == "BULLISH":
        buy += 20
        reasons_buy.append("4H طµط§ط¹ط¯")
    elif b4 == "BEARISH":
        sell += 20
        reasons_sell.append("4H ظ‡ط§ط¨ط·")

    if b1 == "BULLISH":
        buy += 15
        reasons_buy.append("1H طµط§ط¹ط¯")
    elif b1 == "BEARISH":
        sell += 15
        reasons_sell.append("1H ظ‡ط§ط¨ط·")

    # ----------------------------
    # 15M EXECUTION
    # ----------------------------
    if b15 == "BULLISH":
        buy += 8
        reasons_buy.append("15M طµط§ط¹ط¯")
    elif b15 == "BEARISH":
        sell += 8
        reasons_sell.append("15M ظ‡ط§ط¨ط·")

    # ----------------------------
    # LIQUIDITY SWEEP + MSS
    # ----------------------------
    if bool(last15["sweep_bull"]):
        buy += 18
        reasons_buy.append("Bullish Liquidity Sweep")

    if bool(last15["sweep_bear"]):
        sell += 18
        reasons_sell.append("Bearish Liquidity Sweep")

    if bool(last15["bos_bull"]):
        buy += 12
        reasons_buy.append("Bullish BOS")

    if bool(last15["bos_bear"]):
        sell += 12
        reasons_sell.append("Bearish BOS")

    # ----------------------------
    # OB / FVG
    # ----------------------------
    if bool(last15["ob_bull"]):
        buy += 10
        reasons_buy.append("Bullish OB")

    if bool(last15["ob_bear"]):
        sell += 10
        reasons_sell.append("Bearish OB")

    if bool(last15["fvg_bull"]):
        buy += 7
        reasons_buy.append("Bullish FVG")

    if bool(last15["fvg_bear"]):
        sell += 7
        reasons_sell.append("Bearish FVG")

    # ----------------------------
    # MOMENTUM
    # ----------------------------
    rsi = float(last15["rsi"])
    adx = float(last15["adx"])
    macdh = float(last15["macd_hist"])

    # RSI is confirmation, NOT a standalone trigger.
    if 50 <= rsi <= 68:
        buy += 4
        reasons_buy.append(f"RSI ط¯ط§ط¹ظ… ({rsi:.1f})")
    elif 32 <= rsi <= 50:
        sell += 4
        reasons_sell.append(f"RSI ط¯ط§ط¹ظ… ظ„ظ„ط¨ظٹط¹ ({rsi:.1f})")

    if macdh > 0:
        buy += 4
        reasons_buy.append("MACD momentum +")
    elif macdh < 0:
        sell += 4
        reasons_sell.append("MACD momentum -")

    if adx >= 20:
        if last15["plus_di"] > last15["minus_di"]:
            buy += 4
        elif last15["minus_di"] > last15["plus_di"]:
            sell += 4

    # ----------------------------
    # PREMIUM / DISCOUNT
    # ----------------------------
    if bool(last15["discount"]):
        buy += 5
        reasons_buy.append("Discount")
    if bool(last15["premium"]):
        sell += 5
        reasons_sell.append("Premium")

    # ----------------------------
    # DXY
    # ----------------------------
    relation, corr, dxy_bias = dxy_relation(symbol, h1)

    if abs(corr) >= 0.30 and dxy_bias in ("BULLISH", "BEARISH"):
        if symbol == "XAUUSD=X":
            if dxy_bias == "BEARISH":
                buy += 8
                reasons_buy.append(f"DXY ط¯ط§ط¹ظ… ظ„ظ„ط°ظ‡ط¨ ({corr:.2f})")
            elif dxy_bias == "BULLISH":
                sell += 8
                reasons_sell.append(f"DXY ط¶ط§ط؛ط· ط¹ظ„ظ‰ ط§ظ„ط°ظ‡ط¨ ({corr:.2f})")
        elif relation == "DIRECT":
            if dxy_bias == "BULLISH":
                sell += 5
            elif dxy_bias == "BEARISH":
                buy += 5

    total = buy + sell
    if total <= 0:
        return None

    direction = "BUY" if buy > sell else "SELL"
    raw_conf = max(buy, sell) / 100 * 100
    edge = abs(buy - sell)

    # ---------------------------------------------------------
    # HARD GATES:
    # These prevent "high score" trades without structure.
    # ---------------------------------------------------------
    gate = False
    if direction == "BUY":
        gate = (
            b4 == "BULLISH"
            and b1 == "BULLISH"
            and (
                bool(last15["sweep_bull"])
                or bool(last15["bos_bull"])
            )
            and (bool(last15["ob_bull"]) or bool(last15["fvg_bull"]))
            and rsi < 70
        )
    else:
        gate = (
            b4 == "BEARISH"
            and b1 == "BEARISH"
            and (
                bool(last15["sweep_bear"])
                or bool(last15["bos_bear"])
            )
            and (bool(last15["ob_bear"]) or bool(last15["fvg_bear"]))
            and rsi > 30
        )

    # Conservative confidence: score alone cannot exceed 69.
    # It becomes 70+ only when the structural gates pass.
    if gate:
        confidence = min(96.0, 62.0 + edge * 0.55 + raw_conf * 0.18)
    else:
        confidence = min(69.0, 50.0 + edge * 0.35)

    if not gate:
        signal = "WAIT"
        trade = None
    else:
        signal = direction
        trade = build_trade(m15, direction, live)
        if trade is None:
            signal = "WAIT"

    return {
        "name": name,
        "symbol": symbol,
        "price": live,
        "change": change,
        "source": source,
        "signal": signal,
        "confidence": round(confidence, 1),
        "buy_score": round(buy, 1),
        "sell_score": round(sell, 1),
        "4H": b4,
        "1H": b1,
        "15M": b15,
        "RSI": round(rsi, 1),
        "ADX": round(adx, 1),
        "DXY": dxy_bias,
        "DXY_corr": round(corr, 3),
        "reasons_buy": reasons_buy,
        "reasons_sell": reasons_sell,
        "trade": trade,
        "data": m15,
    }


# =========================================================
# SCANNER
# =========================================================

@st.cache_data(ttl=60, show_spinner=False)
def scan_pairs(names):
    rows = []
    for name in names:
        symbol = PAIRS[name]
        result = analyze_symbol(name, symbol)
        if result:
            rows.append(result)

    rows.sort(key=lambda x: x["confidence"], reverse=True)
    return rows


# =========================================================
# UI
# =========================================================

st.markdown(
    """
    <style>
    .stApp { background:#050505; color:#f2f2f2; }
    .bp-card {
        border:1px solid #b99300;
        border-radius:14px;
        padding:18px;
        margin:8px 0;
        background:linear-gradient(135deg,#0a0a0a,#111);
    }
    .bp-title { font-size:32px; font-weight:800; letter-spacing:2px; }
    .bp-sub { color:#c8a92e; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="bp-card"><div class="bp-title">â–² BLACK PYRAMID PRO</div>'
    '<div class="bp-sub">SMC/ICT â€¢ Liquidity â€¢ MTF â€¢ DXY â€¢ Risk/Reward â€¢ No Look-Ahead</div></div>',
    unsafe_allow_html=True,
)

state = st.session_state.bp_state
active = state.get("active_trade")

with st.sidebar:
    st.header("âڑ™ï¸ڈ ط¥ط¹ط¯ط§ط¯ط§طھ")
    selected_name = st.selectbox("ط§ظ„ط³ظˆظ‚", list(PAIRS.keys()), index=0)
    scan_all = st.checkbox("ظپط­طµ ط§ظ„ط£ط³ظˆط§ظ‚ ط§ظ„ط±ط¦ظٹط³ظٹط©", value=False)

    st.markdown("---")
    st.caption("ط­ط¯ ط£ط¯ظ†ظ‰ ظ…ظ‚طھط±ط­ ظ„ظ„ط¥ط´ط§ط±ط©: 70% ظ…ط¹ ط´ط±ظˆط· ظ‡ظٹظƒظ„ظٹط© ط¥ظ„ط²ط§ظ…ظٹط©.")
    if st.button("ًں§¹ ظ…ط³ط­ Cache"):
        st.cache_data.clear()
        st.rerun()


# =========================================================
# ACTIVE TRADE LOCK
# =========================================================

if active:
    st.warning(
        f"ًں”’ ظٹظˆط¬ط¯ AI Trade ظ…ظپطھظˆط­ط©: {active['direction']} {active['name']} "
        f"| Entry {active['entry']} | SL {active['stop_loss']} | TP2 {active['target2']}"
    )

    c1, c2 = st.columns(2)
    if c1.button("â‌Œ ط¥ط؛ظ„ط§ظ‚ ط§ظ„طµظپظ‚ط©"):
        active["status"] = "closed_manual"
        active["close_time"] = datetime.now(timezone.utc).isoformat()
        state["closed_trades"].append(active)
        state["active_trade"] = None
        save_state(state)
        st.session_state.bp_state = state
        st.rerun()

    if c2.button("ًں”“ ط¥ظ„ط؛ط§ط، ط§ظ„ظ‚ظپظ„ ط¨ط¯ظˆظ† طھط³ط¬ظٹظ„ طµظپظ‚ط©"):
        state["active_trade"] = None
        save_state(state)
        st.session_state.bp_state = state
        st.rerun()


# =========================================================
# CURRENT ANALYSIS
# =========================================================

with st.spinner("ط¬ط§ط±ظٹ طھط­ظ„ظٹظ„ 4H â†’ 1H â†’ 15M ..."):
    result = analyze_symbol(selected_name, PAIRS[selected_name])

if not result:
    st.error("طھط¹ط°ط± ط§ظ„ط­طµظˆظ„ ط¹ظ„ظ‰ ط¨ظٹط§ظ†ط§طھ ظƒط§ظپظٹط©. ط¬ط±ظ‘ط¨ طھط­ط¯ظٹط« ط§ظ„ط¨ظٹط§ظ†ط§طھ.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("ط§ظ„ط³ط¹ط±", f"{result['price']:,.2f}")
c2.metric("4H", result["4H"])
c3.metric("1H", result["1H"])
c4.metric("15M", result["15M"])

st.markdown("### ًں§  ط§ظ„ظ‚ط±ط§ط± ط§ظ„ظ†ظ‡ط§ط¦ظٹ")

signal = result["signal"]
confidence = result["confidence"]

if signal == "BUY":
    st.success(f"ًںں¢ BUY â€” Confidence {confidence:.1f}%")
elif signal == "SELL":
    st.error(f"ًں”´ SELL â€” Confidence {confidence:.1f}%")
else:
    st.info(f"âڑھ WAIT â€” Confidence {confidence:.1f}%")


# =========================================================
# TRADE
# =========================================================

trade = result["trade"]

if trade and signal in ("BUY", "SELL"):
    if active:
        st.info("ًں”’ ظ„ظ† ظٹطھظ… ط¥ظ†ط´ط§ط، طµظپظ‚ط© AI ط¬ط¯ظٹط¯ط© ط­طھظ‰ طھظڈط؛ظ„ظ‚ ط§ظ„طµظپظ‚ط© ط§ظ„ط­ط§ظ„ظٹط©.")
    else:
        st.markdown("### ًںژ¯ ط§ظ„طµظپظ‚ط© ط§ظ„ظ…ظ‚طھط±ط­ط©")

        a, b, c, d = st.columns(4)
        a.metric("Entry", f"{trade['entry']:,.4f}")
        b.metric("Stop Loss", f"{trade['stop_loss']:,.4f}")
        c.metric("TP2", f"{trade['target2']:,.4f}")
        d.metric("R/R", f"1:{trade['rr']:.2f}")

        st.write(
            f"**TP1:** {trade['target1']:,.4f}  |  "
            f"**TP2:** {trade['target2']:,.4f}  |  "
            f"**TP3:** {trade['target3']:,.4f}"
        )

        if st.button("ًں”’ طھط«ط¨ظٹطھ ظ‡ط°ظ‡ ط§ظ„طµظپظ‚ط© ظƒظ€ AI Trade", use_container_width=True):
            new_trade = {
                "id": f"BP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "name": result["name"],
                "symbol": result["symbol"],
                "direction": trade["direction"],
                "entry": trade["entry"],
                "stop_loss": trade["stop_loss"],
                "target1": trade["target1"],
                "target2": trade["target2"],
                "target3": trade["target3"],
                "rr": trade["rr"],
                "confidence": confidence,
                "opened_at": datetime.now(timezone.utc).isoformat(),
                "status": "open",
            }
            state["active_trade"] = new_trade
            save_state(state)
            st.session_state.bp_state = state
            st.success("طھظ… طھط«ط¨ظٹطھ ط§ظ„طµظپظ‚ط©. ظ„ظ† طھطھط؛ظٹط± ط§ظ„ط¥ط´ط§ط±ط© ط­طھظ‰ ط§ظ„ط¥ط؛ظ„ط§ظ‚.")
            st.rerun()
else:
    st.caption("ظ„ط§ طھظˆط¬ط¯ طµظپظ‚ط© طھط³طھظˆظپظٹ ط´ط±ظˆط· ط§ظ„ط¯ط®ظˆظ„ ط§ظ„طµط§ط±ظ…ط© ط­ط§ظ„ظٹظ‹ط§.")


# =========================================================
# CONFLUENCE
# =========================================================

st.markdown("### ًں”ژ ط£ط³ط¨ط§ط¨ ط§ظ„ظ‚ط±ط§ط±")

if signal == "BUY":
    for x in result["reasons_buy"]:
        st.write("ًںں¢", x)
elif signal == "SELL":
    for x in result["reasons_sell"]:
        st.write("ًں”´", x)
else:
    st.write("ظ„ط§ ظٹظˆط¬ط¯ طھظˆط§ظپظ‚ ظ‡ظٹظƒظ„ظٹ ظƒط§ظپظچ. ط§ظ„ط§ظ†طھط¸ط§ط± ط£ظپط¶ظ„ ظ…ظ† ط¥ط¬ط¨ط§ط± ط§ظ„ظ†ط¸ط§ظ… ط¹ظ„ظ‰ طµظپظ‚ط©.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("RSI", result["RSI"])
m2.metric("ADX", result["ADX"])
m3.metric("DXY", result["DXY"])
m4.metric("DXY Corr", result["DXY_corr"])


# =========================================================
# CHART
# =========================================================

d = result["data"].tail(250)

fig = go.Figure()
fig.add_trace(
    go.Candlestick(
        x=d.index,
        open=d["open"],
        high=d["high"],
        low=d["low"],
        close=d["close"],
        name="Price",
    )
)
fig.add_trace(
    go.Scatter(x=d.index, y=d["ema20"], name="EMA20")
)
fig.add_trace(
    go.Scatter(x=d.index, y=d["ema50"], name="EMA50")
)
fig.add_trace(
    go.Scatter(x=d.index, y=d["ema200"], name="EMA200")
)

if trade:
    fig.add_hline(y=trade["entry"], line_dash="dash", annotation_text="ENTRY")
    fig.add_hline(y=trade["stop_loss"], line_dash="dot", annotation_text="SL")
    fig.add_hline(y=trade["target2"], line_dash="dot", annotation_text="TP2")

fig.update_layout(
    height=650,
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
)
st.plotly_chart(fig, use_container_width=True)


# =========================================================
# SCANNER
# =========================================================

st.markdown("---")
st.markdown("### ًںڑ¨ ط£ظپط¶ظ„ ط§ظ„ظپط±طµ")

if scan_all:
    names = MAJOR_SCAN
else:
    names = [selected_name]

with st.spinner("ظپط­طµ ط§ظ„ظپط±طµ..."):
    scan = scan_pairs(tuple(names))

if scan:
    table = []
    for r in scan:
        table.append(
            {
                "ط§ظ„ط³ظˆظ‚": r["name"],
                "ط§ظ„ط¥ط´ط§ط±ط©": r["signal"],
                "ط§ظ„ط«ظ‚ط©": r["confidence"],
                "4H": r["4H"],
                "1H": r["1H"],
                "15M": r["15M"],
                "RSI": r["RSI"],
                "ADX": r["ADX"],
                "DXY": r["DXY"],
                "Corr": r["DXY_corr"],
            }
        )
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    best = next((r for r in scan if r["signal"] in ("BUY", "SELL")), None)
    if best:
        st.success(
            f"ط£ظپط¶ظ„ ظپط±طµط© ط­ط§ظ„ظٹط§ظ‹: {best['name']} â€” {best['signal']} "
            f"â€” {best['confidence']:.1f}%"
        )
else:
    st.info("ظ„ط§ طھظˆط¬ط¯ ط¨ظٹط§ظ†ط§طھ ظƒط§ظپظٹط© ظ„ظ„ظ…ط§ط³ط­.")

# =========================================================
# CLOSED HISTORY
# =========================================================

st.markdown("---")
st.markdown("### ًں“ڑ ط³ط¬ظ„ ط§ظ„طµظپظ‚ط§طھ ط§ظ„ظ…ط«ط¨طھط©")

closed = state.get("closed_trades", [])
if closed:
    rows = [
        {
            "ID": x.get("id"),
            "ط§ظ„ط³ظˆظ‚": x.get("name"),
            "ط§ظ„ط§طھط¬ط§ظ‡": x.get("direction"),
            "Entry": x.get("entry"),
            "SL": x.get("stop_loss"),
            "TP2": x.get("target2"),
            "ط§ظ„ط«ظ‚ط©": x.get("confidence"),
            "ط§ظ„ط­ط§ظ„ط©": x.get("status"),
        }
        for x in closed[-50:]
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("ظ„ط§ طھظˆط¬ط¯ طµظپظ‚ط§طھ ظ…ط؛ظ„ظ‚ط© ظ…ط³ط¬ظ„ط©.")

st.caption(
    "BLACK PYRAMID PRO: ظ„ط§ طھظˆط¬ط¯ ط®ظˆط§ط±ط²ظ…ظٹط© طھط¶ظ…ظ† طµظپظ‚ط© ط±ط§ط¨ط­ط©. "
    "ظٹط¬ط¨ ط§ط®طھط¨ط§ط± ط§ظ„ظ†ط¸ط§ظ… طھط§ط±ظٹط®ظٹظ‹ط§ ظˆForward Test ظ‚ط¨ظ„ ط§ط³طھط®ط¯ط§ظ…ظ‡ ط¨ط£ظ…ظˆط§ظ„ ط­ظ‚ظٹظ‚ظٹط©."
)
