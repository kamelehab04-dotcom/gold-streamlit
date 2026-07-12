# mt5_connector.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from loguru import logger
from config import MT5Config

class MT5Connector:
    def __init__(self):
        self.connected = False
        self.account_info = None
        
    def connect(self):
        """الاتصال بـ MT5"""
        if not mt5.initialize():
            logger.error("❌ فشل تهيئة MT5")
            return False
        
        authorized = mt5.login(
            login=MT5Config.LOGIN,
            password=MT5Config.PASSWORD,
            server=MT5Config.SERVER
        )
        
        if not authorized:
            logger.error(f"❌ فشل تسجيل الدخول: {mt5.last_error()}")
            mt5.shutdown()
            return False
        
        self.connected = True
        self.account_info = mt5.account_info()
        logger.success(f"✅ تم الاتصال بحساب {self.account_info.login}")
        return True
    
    def disconnect(self):
        """قطع الاتصال"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("🔌 تم قطع الاتصال بـ MT5")
    
    def get_symbol_info(self, symbol):
        """الحصول على معلومات الرمز"""
        return mt5.symbol_info(symbol)
    
    def get_tick(self, symbol):
        """الحصول على آخر سعر"""
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            return tick.ask, tick.bid
        return None, None
    
    def get_positions(self, symbol=None):
        """الحصول على الصفقات المفتوحة"""
        if symbol:
            return mt5.positions_get(symbol=symbol)
        return mt5.positions_get()
    
    def get_positions_df(self, symbol=None):
        """الصفقات المفتوحة كـ DataFrame"""
        positions = self.get_positions(symbol)
        if positions:
            return pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        return pd.DataFrame()
    
    def place_market_order(self, symbol, direction, volume, sl=None, tp=None, comment=""):
        """تنفيذ أمر سوق"""
        if not self.connected:
            logger.error("❌ غير متصل بـ MT5")
            return None
        
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"❌ الرمز {symbol} غير موجود في MT5")
            return None
        
        if volume < symbol_info.volume_min:
            volume = symbol_info.volume_min
            logger.warning(f"⚠️ تم تعديل الحجم إلى الحد الأدنى: {volume}")
        
        order_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if direction == "buy" else mt5.symbol_info_tick(symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": comment or "Pharaoh Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        if sl:
            request["sl"] = float(sl)
        if tp:
            request["tp"] = float(tp)
        
        if MT5Config.DRY_RUN:
            logger.info(f"🧪 [DRY RUN] أمر {direction.upper()} على {symbol} بحجم {volume}")
            logger.info(f"   السعر: {price}, SL: {sl}, TP: {tp}")
            return {"retcode": mt5.TRADE_RETCODE_DONE, "order": 99999, "volume": volume}
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ فشل تنفيذ الأمر: {result.comment}")
            return None
        
        logger.success(f"✅ تم تنفيذ أمر {direction.upper()} على {symbol} بحجم {volume}")
        return result
    
    def close_position(self, position):
        """إغلاق صفقة"""
        if not self.connected:
            return False
        
        symbol = position.symbol
        volume = position.volume
        direction = "buy" if position.type == mt5.POSITION_TYPE_SELL else "sell"
        price = mt5.symbol_info_tick(symbol).ask if direction == "buy" else mt5.symbol_info_tick(symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close by Pharaoh Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        if MT5Config.DRY_RUN:
            logger.info(f"🧪 [DRY RUN] إغلاق صفقة {position.ticket}")
            return True
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"❌ فشل إغلاق الصفقة: {result.comment}")
            return False
        
        logger.success(f"✅ تم إغلاق الصفقة {position.ticket}")
        return True
    
    def get_account_balance(self):
        if self.connected:
            return self.account_info.balance
        return 0
    
    def get_free_margin(self):
        if self.connected:
            return self.account_info.margin_free
        return 0
    
    def get_account_info_df(self):
        if self.connected:
            return self.account_info._asdict()
        return {}
