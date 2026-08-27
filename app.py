# ==========================================
# BLACK PYRAMID – الإصدار 2002 (مطور)
# تاريخ التحديث: 2026-08-26
# الإضافات: مستويات السيولة (BSL/SSL) + انعكاسات Smart Money (SMR)
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
# 🖤 BLACK PYRAMID – الهوية البصرية
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    /* ===== الخطوط ===== */
    .main-title, .signal-text, .price-value {
        font-family:
