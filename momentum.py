# momentum.py
import pandas as pd
import numpy as np

def modified_momentum(df, period=14, smoothing=3):
    """
    حساب الزخم المعدل باستخدام ATR لتعديل التقلبات
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # المدى الحقيقي المعدل
    tr = pd.concat([high - low, 
                    abs(high - close.shift()), 
                    abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    # الزخم السعري
    raw_momentum = close - close.shift(period)
    
    # تعديل الزخم بمتوسط ATR
    momentum = raw_momentum / atr.shift(1)  # نسبة إلى ATR
    momentum = momentum.rolling(smoothing).mean()
    return momentum
