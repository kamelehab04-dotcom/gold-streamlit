import streamlit as st
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="Gold", layout="wide")

st.title("Gold Price")

# جلب سعر الذهب
gold = yf.Ticker("GC=F")
price = gold.history(period="1d")['Close'].iloc[-1]

st.metric("Gold Price", f"${price:.2f}")

st.caption(f"Updated: {datetime.now()}")
