# trading_engine.py
import time
import threading
from datetime import datetime
from loguru import logger
import MetaTrader5 as mt5
from mt5_connector import MT5Connector
from risk_manager import RiskManager
from config import MT5Config

class TradingEngine:
    def __init__(self):
        self.connector = MT5Connector()
        self.risk_manager = RiskManager(self.connector)
        self.is_running = False
        self.monitor_thread = None
        
    def start(self):
        """بدء تشغيل المحرك"""
        if not self.connector.connect():
            logger.error("❌ فشل الاتصال بـ MT5")
            return False
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.success("🚀 محرك التداول قيد التشغيل")
        return True
    
    def stop(self):
        """إيقاف المحرك"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.connector.disconnect()
        logger.info("⏹️ تم إيقاف محرك التداول")
    
    def execute_signal(self, signal_data):
        """تنفيذ إشارة تداول"""
        if not self.is_running:
            logger.warning("⚠️ المحرك متوقف")
            return False
        
        symbol = signal_data['symbol']
        direction = signal_data['direction'].lower()
        entry = signal_data['entry_price']
        
        # تحويل الرمز إلى صيغة MT5
        mt5_symbol = MT5Config.get_mt5_symbol(symbol)
        
        can_trade, reason = self.risk_manager.can_trade(mt5_symbol)
        if not can_trade:
            logger.warning(f"⚠️ لا يمكن التداول: {reason}")
            return False
        
        volume = self.risk_manager.calculate_position_size(mt5_symbol, entry, signal_data['stop_loss'])
        if volume <= 0:
            logger.warning("⚠️ حجم الصفقة غير صالح")
            return False
        
        result = self.connector.place_market_order(
            symbol=mt5_symbol,
            direction=direction,
            volume=volume,
            sl=signal_data['stop_loss'],
            tp=signal_data['take_profit'],
            comment=f"{signal_data.get('signal_type', 'Pharaoh')} ({signal_data.get('confidence', 0)}%)"
        )
        
        if result:
            logger.success(f"✅ تم تنفيذ الصفقة: {direction.upper()} {mt5_symbol} {volume} لوت")
            return True
        
        return False
    
    def close_all_positions(self, symbol=None):
        """إغلاق جميع الصفقات"""
        positions = self.connector.get_positions(symbol)
        if not positions:
            logger.info("ℹ️ لا توجد صفقات مفتوحة")
            return True
        
        closed = 0
        for pos in positions:
            if self.connector.close_position(pos):
                closed += 1
        
        logger.info(f"✅ تم إغلاق {closed} صفقة")
        return True
    
    def _monitor_loop(self):
        """مراقبة الصفقات وتحديث الوقف المتحرك"""
        while self.is_running:
            try:
                positions = self.connector.get_positions()
                if positions:
                    for pos in positions:
                        self._update_trailing_stop(pos)
                time.sleep(5)
            except Exception as e:
                logger.error(f"❌ خطأ في المراقبة: {e}")
    
    def _update_trailing_stop(self, position):
        """تحديث الوقف المتحرك للصفقة"""
        if MT5Config.DRY_RUN:
            return
        
        tick = self.connector.get_tick(position.symbol)
        if not tick:
            return
        
        current_price = tick[0] if position.type == mt5.POSITION_TYPE_BUY else tick[1]
        symbol_info = self.connector.get_symbol_info(position.symbol)
        point = symbol_info.point
        
        trail_points = MT5Config.TRAILING_STOP_DEFAULT
        trail_distance = trail_points * point
        
        if position.type == mt5.POSITION_TYPE_BUY:
            new_sl = current_price - trail_distance
            if new_sl > position.sl:
                self._modify_position_stop(position, new_sl)
        else:
            new_sl = current_price + trail_distance
            if new_sl < position.sl:
                self._modify_position_stop(position, new_sl)
    
    def _modify_position_stop(self, position, new_sl):
        """تعديل وقف الخسارة"""
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "sl": new_sl,
            "tp": position.tp,
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ تم تحديث الوقف للصفقة {position.ticket} → {new_sl}")
        else:
            logger.warning(f"⚠️ فشل تحديث الوقف: {result.comment}")
