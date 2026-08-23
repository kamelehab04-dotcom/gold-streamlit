# volume_proxy.py
import pandas as pd
import numpy as np

def volume_proxy(df, lookback=20):
    """
    حساب وكيل للحجم في حال عدم توفر بيانات حجم دقيقة
    يستخدم عدد تغيرات الأسعار ونطاق التداول
    """
    # 1. عدد التغيرات السعرية في كل شمعة (Tick count proxy)
    price_changes = abs(df['close'] - df['open']) + abs(df['high'] - df['low'])
    tick_volume = price_changes.rolling(lookback).mean()
    
    # 2. التقلب النسبي
    atr = df['atr'].rolling(lookback).mean()
    relative_volatility = (df['high'] - df['low']) / atr
    
    # 3. وكيل الحجم = tick_volume * (1 + relative_volatility)
    proxy = tick_volume * (1 + relative_volatility)
    return proxy

def volume_signal(proxy, current_price, entry_price):
    """
    توليد إشارة حجم لتأكيد الدخول
    """
    if proxy.iloc[-1] > proxy.iloc[-5:].mean() * 1.3:
        return 'HIGH'  # حجم مرتفع
    elif proxy.iloc[-1] > proxy.iloc[-5:].mean():
        return 'MEDIUM'
    else:
        return 'LOW'
