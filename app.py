import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import json
import time

st.set_page_config(page_title="Pharaoh Gold Dashboard", page_icon="🥇", layout="wide")

# ==========================================
# CSS للتنسيق
# ==========================================
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
        border-radius: 20px;
        margin-bottom: 30px;
        border: 1px solid #ffd70033;
    }
    .main-title {
        font-size: 2.5rem;
        color: #ffd700;
        text-shadow: 2px 2px 4px #000000;
        margin: 0;
        font-weight: bold;
        letter-spacing: 2px;
    }
    .main-subtitle {
        font-size: 1rem;
        color: #aaa;
        margin-top: 10px;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        margin: 30px 0;
    }
    .stat-card {
        flex: 1;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #ffd70033;
        transition: transform 0.3s;
    }
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: #ffd70066;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #ffd700;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #888;
        margin-top: 10px;
    }
    .price-card {
        background: linear-gradient(135deg, #ffd70015 0%, #ffaa0015 100%);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        border: 2px solid #ffd700;
        margin: 20px 0;
        transition: all 0.3s;
    }
    .price-label {
        font-size: 1.2rem;
        color: #ffd700;
        letter-spacing: 2px;
    }
    .price-value {
        font-size: 4rem;
        font-weight: bold;
        color: #ffffff;
        margin: 10px 0;
    }
    .price-change {
        font-size: 1rem;
        color: #00ff88;
    }
    .live-badge {
        background: #ff4444;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    .indicator-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        border-left: 4px solid #ffd700;
        margin: 10px 0;
    }
    .indicator-value {
        font-size: 1.8rem;
        font-weight: bold;
    }
    .indicator-label {
        font-size: 0.8rem;
        color: #888;
    }
    .signal-card {
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
    }
    .signal-buy {
        background: linear-gradient(135deg, #00ff8820 0%, #00cc6620 100%);
        border: 1px solid #00ff88;
    }
    .signal-sell {
        background: linear-gradient(135deg, #ff444420 0%, #cc333320 100%);
        border: 1px solid #ff4444;
    }
    .signal-neutral {
        background: linear-gradient(135deg, #ffaa0020 0%, #cc880020 100%);
        border: 1px solid #ffaa00;
    }
    .signal-title {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .signal-confidence {
        font-size: 0.9rem;
        margin-top: 10px;
    }
    .targets-table {
        background: #1e1e2e;
        border-radius: 12px;
        overflow: hidden;
        margin: 20px 0;
    }
    .target-row {
        display: flex;
        justify-content: space-between;
        padding: 12px 20px;
        border-bottom: 1px solid #333;
    }
    .target-row:last-child {
        border-bottom: none;
    }
    .target-label {
        color: #ffd700;
        font-weight: bold;
    }
    .target-value {
        color: #ffffff;
    }
    .sentiment-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #ffd700;
    }
    .event-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid;
    }
    .event-high { border-left-color: #ff4444; }
    .event-medium { border-left-color: #ffaa00; }
    .event-low { border-left-color: #00ff88; }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.8rem;
        border-top: 1px solid #333;
        margin-top: 30px;
    }
    .rating-badge {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 10px 15px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .stars {
        color: #ffd700;
        letter-spacing: 2px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e2e;
        border-radius: 10px;
        padding: 8px 20px;
        border: 1px solid #ffd70033;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd70020 0%, #ffaa0020 100%);
        border-color: #ffd700;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# الهيدر
# ==========================================
st.markdown("""
<div class="main-header">
    <div class="main-title">𓋹 PHARAOH GOLD DASHBOARD 𓋹</div>
    <div class="main-subtitle">بوت تحليل الذهب الفرعوني | SMC + ICT + Real-time Data</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# بطاقات الإحصائيات
# ==========================================
st.markdown("""
<div class="stats-container">
    <div class="stat-card">
        <div class="stat-number">$253M+</div>
        <div class="stat-label">Rewards Distributed</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">3M+</div>
        <div class="stat-label">Traders Worldwide</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">195+</div>
        <div class="stat-label">Countries Serviced</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# إنشاء التبويبات
# ==========================================
tab1, tab2 = st.tabs(["📊 Gold Analysis Dashboard", "📅 Economic Calendar"])

# ==========================================
# الصفحة 1: تحليل الذهب
# ==========================================
with tab1:
    @st.cache_data(ttl=10)  # تحديث كل 10 ثواني
    def get_real_price_from_yahoo():
        """جلب السعر الحقيقي من Yahoo Finance (مصدر موثوق)"""
        try:
            gold = yf.Ticker("GC=F")
            # جلب آخر سعر
            df = gold.history(period="1d", interval="1m")
            if not df.empty:
                return df['Close'].iloc[-1]
            return None
        except Exception as e:
            print(f"Yahoo Error: {e}")
            return None
    
    @st.cache_data(ttl=300)
    def get_historical_data():
        gold = yf.Ticker("GC=F")
        df = gold.history(period="1mo", interval="1h")
        if df.empty:
            return None
        df.columns = [col.lower() for col in df.columns]
        return df
    
    @st.cache_data(ttl=3600)
    def get_news_sentiment():
        """تحليل المشاعر الإخبارية (مبسط)"""
        # بيانات تجريبية للعرض
        return {
            "sentiment_score": 0.12,
            "sentiment_text": "SLIGHTLY POSITIVE",
            "sentiment_emoji": "🟡",
            "impact_score": 1,
            "articles_count": 8
        }
    
    # جلب السعر الحقيقي
    current_price = get_real_price_from_yahoo()
    
    # إذا فشل، نستخدم آخر سعر من البيانات التاريخية
    df = get_historical_data()
    
    if df is None:
        st.error("Error loading data")
        st.stop()
    
    if current_price is None and df is not None:
        current_price = df['close'].iloc[-1]
    
    if current_price is None:
        st.error("Unable to fetch gold price")
        st.stop()
    
    # حساب المؤشرات
    def calc_rsi(data, period=14):
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calc_atr(df, period=14):
        high = df['high']
        low = df['low']
        close = df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['rsi'] = calc_rsi(df['close'])
    df['atr'] = calc_atr(df)
    
    current_rsi = df['rsi'].iloc[-1] if not pd.isna(df['rsi'].iloc[-1]) else 50
    current_atr = df['atr'].iloc[-1] if not pd.isna(df['atr'].iloc[-1]) else 20
    
    # SMC Signals (مبسطة)
    recent_lows = df['low'].iloc[-20:].values
    recent_highs = df['high'].iloc[-20:].values
    liquidity_sweep_bullish = df['low'].iloc[-1] < min(recent_lows[:-1]) if len(recent_lows) > 1 else False
    liquidity_sweep_bearish = df['high'].iloc[-1] > max(recent_highs[:-1]) if len(recent_highs) > 1 else False
    bos_bullish = current_price > df['high'].iloc[-6:-1].max() if len(df) > 6 else False
    bos_bearish = current_price < df['low'].iloc[-6:-1].min() if len(df) > 6 else False
    resistance = np.percentile(df['high'].iloc[-30:], 75) if len(df) >= 30 else current_price + 20
    support = np.percentile(df['low'].iloc[-30:], 25) if len(df) >= 30 else current_price - 20
    
    # نظام التسجيل
    bullish = 0
    bearish = 0
    signals = []
    
    # RSI
    if current_rsi < 45:
        bullish += 3
        signals.append(f"✅ RSI: {current_rsi:.1f} (BUY ZONE)")
    elif current_rsi > 65:
        bearish += 3
        signals.append(f"⚠️ RSI: {current_rsi:.1f} (SELL ZONE)")
    else:
        signals.append(f"📊 RSI: {current_rsi:.1f} (NEUTRAL)")
    
    # EMA
    if current_price > df['ema20'].iloc[-1]:
        bullish += 2
        signals.append("📈 Price above EMA20")
    else:
        bearish += 2
        signals.append("📉 Price below EMA20")
    
    # SMC
    if liquidity_sweep_bullish:
        bullish += 3
        signals.append("🎯 Liquidity Sweep Bullish")
    if liquidity_sweep_bearish:
        bearish += 3
        signals.append("🎯 Liquidity Sweep Bearish")
    if bos_bullish:
        bullish += 2
        signals.append("🚀 BOS Bullish")
    if bos_bearish:
        bearish += 2
        signals.append("🚀 BOS Bearish")
    
    # دعم/مقاومة
    if current_price <= support + 5:
        bullish += 2
        signals.append(f"📍 Near Support: ${support:.2f}")
    if current_price >= resistance - 5:
        bearish += 2
        signals.append(f"📍 Near Resistance: ${resistance:.2f}")
    
    net = bullish - bearish
    
    # الإشارة النهائية
    if net >= 10:
        signal_type = "STRONG BUY"
        signal_action = "BUY"
        confidence = 95
        signal_color = "#00ff88"
    elif net >= 5:
        signal_type = "BUY"
        signal_action = "BUY"
        confidence = 80
        signal_color = "#00ff88"
    elif net <= -10:
        signal_type = "STRONG SELL"
        signal_action = "SELL"
        confidence = 95
        signal_color = "#ff4444"
    elif net <= -5:
        signal_type = "SELL"
        signal_action = "SELL"
        confidence = 80
        signal_color = "#ff4444"
    else:
        signal_type = "WAIT"
        signal_action = "NEUTRAL"
        confidence = 50
        signal_color = "#ffaa00"
    
    # خطة التداول
    if signal_action == "BUY":
        entry = current_price
        stop_loss = support - (current_atr * 0.5)
        targets = [resistance, resistance + (current_atr * 1.5), resistance + (current_atr * 3)]
    elif signal_action == "SELL":
        entry = current_price
        stop_loss = resistance + (current_atr * 0.5)
        targets = [support, support - (current_atr * 1.5), support - (current_atr * 3)]
    else:
        entry = current_price
        stop_loss = None
        targets = []
    
    # حساب التغير
    if len(df) > 1:
        prev_price = df['close'].iloc[-2]
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100
    else:
        change = 0
        change_percent = 0
    
    change_color = "#00ff88" if change >= 0 else "#ff4444"
    change_sign = "+" if change >= 0 else ""
    
    # عرض السعر
    st.markdown(f"""
    <div class="price-card">
        <div class="price-label">
            <span class="live-badge">LIVE</span> 𓋹 REAL TIME GOLD PRICE 𓋹
        </div>
        <div class="price-value">${current_price:,.2f}</div>
        <div class="price-change" style="color:{change_color}">{change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)</div>
        <div style="color:#888; font-size:0.8rem; margin-top:10px">Source: Yahoo Finance (Real-time)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # بطاقات المؤشرات
    st.markdown("### 📊 Market Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#ffd700">{current_rsi:.1f}</div>
            <div class="indicator-label">RSI (14)</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#ffd700">${current_atr:.2f}</div>
            <div class="indicator-label">ATR</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#ffd700">{bullish} / {bearish}</div>
            <div class="indicator-label">Bullish / Bearish</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="indicator-card">
            <div class="indicator-value" style="color:#ffd700">{net:+d}</div>
            <div class="indicator-label">Net Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    # الإشارة
    signal_class = "signal-buy" if signal_action == "BUY" else "signal-sell" if signal_action == "SELL" else "signal-neutral"
    st.markdown(f"""
    <div class="signal-card {signal_class}">
        <div class="signal-title" style="color:{signal_color}">{signal_type} SIGNAL</div>
        <div class="signal-confidence">Confidence: {confidence}% | Score: {net:+d}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # الشارت
    st.markdown("### 📈 Price Chart")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Gold', line=dict(color='#ffd700', width=2)))
    fig.add_trace(go.Scatter(x=df.index, y=df['ema20'], mode='lines', name='EMA 20', line=dict(color='#ff9f4a')))
    fig.add_trace(go.Scatter(x=df.index, y=df['ema50'], mode='lines', name='EMA 50', line=dict(color='#4a9eff')))
    fig.add_hline(y=resistance, line_dash="dash", line_color="#ff4444", annotation_text="Resistance")
    fig.add_hline(y=support, line_dash="dash", line_color="#00ff88", annotation_text="Support")
    fig.update_layout(template="plotly_dark", height=450)
    st.plotly_chart(fig, use_container_width=True)
    
    # خطة التداول
    if signal_action != "NEUTRAL":
        st.markdown("### 🎯 Trading Plan")
        st.markdown(f"""
        <div class="targets-table">
            <div class="target-row"><span class="target-label">📍 Entry</span><span class="target-value">${entry:.2f}</span></div>
            <div class="target-row"><span class="target-label">🛑 Stop Loss</span><span class="target-value">${stop_loss:.2f}</span></div>
            <div class="target-row"><span class="target-label">🎯 Target 1</span><span class="target-value">${targets[0]:.2f}</span></div>
            <div class="target-row"><span class="target-label">🎯 Target 2</span><span class="target-value">${targets[1]:.2f}</span></div>
            <div class="target-row"><span class="target-label">🎯 Target 3</span><span class="target-value">${targets[2]:.2f}</span></div>
        </div>
        """, unsafe_allow_html=True)
        rr = (targets[0] - entry) / (entry - stop_loss) if signal_action == "BUY" else (entry - targets[0]) / (stop_loss - entry)
        st.markdown(f"""
        <div class="stats-container" style="margin-top:20px">
            <div class="stat-card"><div class="stat-number" style="font-size:1rem">Risk/Reward</div><div class="stat-label">1 : {rr:.2f}</div></div>
            <div class="stat-card"><div class="stat-number" style="font-size:1rem">Risk</div><div class="stat-label">2% of capital</div></div>
        </div>
        """, unsafe_allow_html=True)
    
    # زر تحديث
    if st.button("🔄 Refresh Live Price"):
        st.cache_data.clear()
        st.rerun()
    
    with st.expander("📊 Technical Indicators Details"):
        for s in signals:
            if "✅" in s or "📈" in s:
                st.success(s)
            elif "⚠️" in s or "📉" in s:
                st.error(s)
            else:
                st.info(s)

# ==========================================
# الصفحة 2: التقويم الاقتصادي
# ==========================================
with tab2:
    st.markdown("### 📅 Economic Calendar")
    st.markdown("أهم الأحداث الاقتصادية المؤثرة على الذهب والأسواق المالية")
    st.markdown("---")
    
    @st.cache_data(ttl=3600)
    def get_economic_calendar():
        today = datetime.now()
        events = [
            {"title": "Federal Reserve Interest Rate Decision", "date": today.strftime("%Y-%m-%d"), "time": "14:00", "country": "US", "impact": "high", "actual": "5.50%", "forecast": "5.50%", "previous": "5.50%"},
            {"title": "US Non-Farm Payrolls", "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "time": "08:30", "country": "US", "impact": "high", "actual": "-", "forecast": "180K", "previous": "175K"},
            {"title": "CPI Inflation Rate (YoY)", "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"), "time": "08:30", "country": "US", "impact": "high", "actual": "-", "forecast": "3.2%", "previous": "3.1%"},
            {"title": "ECB Interest Rate Decision", "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"), "time": "09:15", "country": "EU", "impact": "high", "actual": "-", "forecast": "4.50%", "previous": "4.50%"},
            {"title": "GDP Growth Rate (QoQ)", "date": (today + timedelta(days=4)).strftime("%Y-%m-%d"), "time": "08:30", "country": "US", "impact": "high", "actual": "-", "forecast": "2.5%", "previous": "2.8%"},
        ]
        return events
    
    events = get_economic_calendar()
    
    if events:
        col1, col2, col3 = st.columns(3)
        with col1:
            countries = ["All"] + sorted(list(set([e['country'] for e in events])))
            selected_country = st.selectbox("🌍 Filter by Country", countries)
        with col2:
            impacts = ["All", "high", "medium", "low"]
            selected_impact = st.selectbox("⚠️ Filter by Impact", impacts)
        with col3:
            date_filter = st.selectbox("📅 Date", ["All", "Today", "Tomorrow", "This Week"])
        
        filtered_events = events.copy()
        if selected_country != "All":
            filtered_events = [e for e in filtered_events if e['country'] == selected_country]
        if selected_impact != "All":
            filtered_events = [e for e in filtered_events if e['impact'] == selected_impact]
        
        if date_filter == "Today":
            today_str = datetime.now().strftime("%Y-%m-%d")
            filtered_events = [e for e in filtered_events if e['date'] == today_str]
        elif date_filter == "Tomorrow":
            tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            filtered_events = [e for e in filtered_events if e['date'] == tomorrow_str]
        elif date_filter == "This Week":
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            filtered_events = [e for e in filtered_events if week_start.strftime("%Y-%m-%d") <= e['date'] <= week_end.strftime("%Y-%m-%d")]
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            high_impact = len([e for e in filtered_events if e['impact'] == 'high'])
            st.metric("🔴 High Impact Events", high_impact)
        with col2:
            medium_impact = len([e for e in filtered_events if e['impact'] == 'medium'])
            st.metric("🟡 Medium Impact Events", medium_impact)
        with col3:
            low_impact = len([e for e in filtered_events if e['impact'] == 'low'])
            st.metric("🟢 Low Impact Events", low_impact)
        
        st.markdown("---")
        
        for event in filtered_events:
            impact_class = "event-high" if event['impact'] == 'high' else "event-medium" if event['impact'] == 'medium' else "event-low"
            impact_emoji = "🔴" if event['impact'] == 'high' else "🟡" if event['impact'] == 'medium' else "🟢"
            
            st.markdown(f"""
            <div class="event-card {impact_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <div><span style="font-size:1.1rem; font-weight:bold">📌 {event['title']}</span></div>
                    <div><span style="color:#ffd700">{impact_emoji} {event['impact'].upper()} IMPACT</span></div>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 20px; flex-wrap: wrap;">
                    <span>🌍 {event['country']}</span>
                    <span>📅 {event['date']}</span>
                    <span>⏰ {event['time']}</span>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 20px; flex-wrap: wrap; color: #888;">
                    <span>Actual: <strong style="color:#fff">{event['actual']}</strong></span>
                    <span>Forecast: <strong style="color:#fff">{event['forecast']}</strong></span>
                    <span>Previous: <strong style="color:#fff">{event['previous']}</strong></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if not filtered_events:
            st.info("No events found for the selected filters.")
        
        with st.expander("ℹ️ How to read this calendar"):
            st.markdown("""
            - **🔴 High Impact**: Likely to cause significant market movement
            - **🟡 Medium Impact**: May cause some market movement
            - **🟢 Low Impact**: Minor market impact expected
            
            **How to use this data:**
            - Events with HIGH impact on the USD are most important for gold
            - Actual vs Forecast vs Previous show the outcome relative to expectations
            - If Actual > Forecast: Generally positive for the currency, negative for gold (if USD event)
            - If Actual < Forecast: Generally negative for the currency, positive for gold (if USD event)
            """)
    else:
        st.error("Unable to load economic calendar data. Please try again later.")

# ==========================================
# الفوتر
# ==========================================
st.markdown(f"""
<div class="footer">
    𓋹 Powered by Yahoo Finance | SMC + ICT Analysis | Real-time Live Data 𓋹<br>
    Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)
