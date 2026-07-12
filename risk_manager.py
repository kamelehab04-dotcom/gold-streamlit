# risk_manager.py
import MetaTrader5 as mt5
from config import MT5Config
from loguru import logger

class RiskManager:
    def __init__(self, connector):
        self.connector = connector
        
    def calculate_position_size(self, symbol, entry_price, stop_loss):
        """حساب حجم الصفقة بناءً على نسبة المخاطرة"""
        balance = self.connector.get_account_balance()
        if balance <= 0:
            return 0
        
        risk_amount = balance * (MT5Config.RISK_PER_TRADE / 100)
        risk_distance = abs(entry_price - stop_loss)
        if risk_distance <= 0:
            return 0
        
        symbol_info = self.connector.get_symbol_info(symbol)
        if symbol_info is None:
            return 0
        
        point_value = symbol_info.trade_tick_value / symbol_info.trade_tick_size
        volume = risk_amount / (risk_distance * point_value)
        volume = round(volume / 0.01) * 0.01
        volume = max(volume, symbol_info.volume_min)
        volume = min(volume, symbol_info.volume_max)
        
        logger.info(f"📊 حجم الصفقة المحسوب: {volume} لوت (المخاطرة: ${risk_amount:.2f})")
        return volume
    
    def can_trade(self, symbol):
        """التحقق من إمكانية التداول"""
        positions = self.connector.get_positions()
        if positions and len(positions) >= MT5Config.MAX_POSITIONS:
            logger.warning(f"⚠️ تم الوصول إلى الحد الأقصى للصفقات ({MT5Config.MAX_POSITIONS})")
            return False, "الحد الأقصى للصفقات"
        
        free_margin = self.connector.get_free_margin()
        if free_margin < 100:
            logger.warning(f"⚠️ الهامش المتاح منخفض: ${free_margin:.2f}")
            return False, "هامش غير كافٍ"
        
        symbol_info = self.connector.get_symbol_info(symbol)
        if symbol_info:
            spread = symbol_info.spread
            if spread > MT5Config.MAX_SPREAD:
                logger.warning(f"⚠️ السبريد مرتفع: {spread} نقطة")
                return False, f"السبريد مرتفع ({spread})"
        
        return True, "مسموح بالتداول"
