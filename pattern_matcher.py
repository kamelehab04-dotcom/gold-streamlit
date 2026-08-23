# pattern_matcher.py
import pandas as pd
import numpy as np

class PatternMatcher:
    def __init__(self, max_history=500):
        self.patterns_db = []
        self.max_history = max_history
    
    def add_pattern(self, pattern_data):
        """إضافة نمط جديد مع نتيجته بعد 5 شموع"""
        if len(self.patterns_db) >= self.max_history:
            self.patterns_db.pop(0)
        self.patterns_db.append(pattern_data)
    
    def match_pattern(self, current_pattern, top_k=10):
        """
        مقارنة النمط الحالي مع الأنماط المخزنة
        إرجاع: (متوسط الربح, نسبة النجاح, عدد التطابقات)
        """
        if len(self.patterns_db) < 20:
            return None, None, 0
        
        # حساب التشابه (بساطة: مقارنة الـ Open, High, Low, Close)
        similarities = []
        for p in self.patterns_db:
            # تشابه بسيط على أساس التغيرات النسبية
            sim = 1 - np.mean(np.abs(current_pattern - p['pattern']) / (np.abs(p['pattern']) + 1e-6))
            similarities.append((sim, p['outcome']))
        
        # ترتيب حسب التشابه
        similarities.sort(key=lambda x: x[0], reverse=True)
        top = similarities[:top_k]
        
        if not top:
            return None, None, 0
        
        # حساب النتائج
        profits = [out['profit'] for _, out in top]
        wins = [1 for out in top if out['profit'] > 0]
        
        avg_profit = np.mean(profits) if profits else 0
        win_rate = len(wins) / len(top) if top else 0
        
        return avg_profit, win_rate, len(top)
