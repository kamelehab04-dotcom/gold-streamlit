# market_state.py
import pandas as pd
import numpy as np

def classify_market_state(df, adx_threshold=25, atr_multiplier=1.5):
    """
    تصنيف حالة السوق بناءً على ADX و ATR
    يعيد: (state, confidence)
    state: 'TRENDING_STRONG', 'TRENDING_WEAK', 'RANGING', 'VOLATILE'
    """
    if len(df) < 50:
        return 'RANGING', 0.5
    
    adx = df['adx'].iloc[-1]
    atr = df['atr'].iloc[-1]
    avg_atr = df['atr'].iloc[-50:].mean()
    atr_ratio = atr / avg_atr if avg_atr > 0 else 1
    
    if adx > adx_threshold and atr_ratio > 1.2:
        return 'TRENDING_STRONG', min(1, (adx - 25) / 25 + 0.3)
    elif adx > adx_threshold:
        return 'TRENDING_WEAK', 0.6
    elif atr_ratio > 1.3:
        return 'VOLATILE', 0.7
    else:
        return 'RANGING', 0.8

def adjust_weights_by_state(state):
    """إرجاع قاموس الأوزان المعدلة حسب حالة السوق"""
    if state == 'TRENDING_STRONG':
        return {'rsi': 2, 'macd': 4, 'bb': 1, 'vwap': 1, 'adx': 3, 'ichimoku': 4, 'smc': 3, 'patterns': 4, 'tbs': 4, 'mfi': 1}
    elif state == 'TRENDING_WEAK':
        return {'rsi': 2, 'macd': 3, 'bb': 2, 'vwap': 1, 'adx': 3, 'ichimoku': 3, 'smc': 3, 'patterns': 4, 'tbs': 4, 'mfi': 2}
    elif state == 'RANGING':
        return {'rsi': 4, 'macd': 1, 'bb': 4, 'vwap': 1, 'adx': 1, 'ichimoku': 1, 'smc': 3, 'patterns': 3, 'tbs': 3, 'mfi': 4}
    else:  # VOLATILE
        return {'rsi': 3, 'macd': 2, 'bb': 3, 'vwap': 2, 'adx': 2, 'ichimoku': 2, 'smc': 3, 'patterns': 4, 'tbs': 4, 'mfi': 3}
