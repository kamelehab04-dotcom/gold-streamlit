# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class MT5Config:
    # بيانات الاتصال بـ MT5
    LOGIN = int(os.getenv("MT5_LOGIN", 0))
    PASSWORD = os.getenv("MT5_PASSWORD", "")
    SERVER = os.getenv("MT5_SERVER", "MetaQuotes-Demo")
    
    # إعدادات التداول
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", 2.0))  # 2% من رأس المال
    MAX_SPREAD = float(os.getenv("MAX_SPREAD", 50))           # الحد الأقصى للسبريد (نقاط)
    MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", 3))        # الحد الأقصى للصفقات المتزامنة
    TRAILING_STOP_DEFAULT = int(os.getenv("TRAILING_STOP_DEFAULT", 20))  # نقاط
    
    # وضع الاختبار (بدون تنفيذ فعلي)
    DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
    
    # تعيين الرموز (تطابق Yahoo Finance مع MT5)
    SYMBOL_MAP = {
        "GC=F": "XAUUSD",
        "SI=F": "XAGUSD",
        "DX-Y.NYB": "USDX",
        "EURUSD=X": "EURUSD",
        "GBPUSD=X": "GBPUSD",
        "USDJPY=X": "USDJPY",
        "USDCHF=X": "USDCHF",
        "AUDUSD=X": "AUDUSD",
        "NZDUSD=X": "NZDUSD",
        "USDCAD=X": "USDCAD",
        "EURGBP=X": "EURGBP",
        "EURJPY=X": "EURJPY",
        "EURCHF=X": "EURCHF",
        "EURAUD=X": "EURAUD",
        "EURNZD=X": "EURNZD",
        "EURCAD=X": "EURCAD",
        "GBPJPY=X": "GBPJPY",
        "GBPCHF=X": "GBPCHF",
        "GBPAUD=X": "GBPAUD",
        "GBPNZD=X": "GBPNZD",
        "GBPCAD=X": "GBPCAD",
        "AUDJPY=X": "AUDJPY",
        "AUDCHF=X": "AUDCHF",
        "AUDNZD=X": "AUDNZD",
        "AUDCAD=X": "AUDCAD",
        "NZDJPY=X": "NZDJPY",
        "NZDCHF=X": "NZDCHF",
        "NZDCAD=X": "NZDCAD",
        "CADJPY=X": "CADJPY",
        "CADCHF=X": "CADCHF",
        "BTC-USD": "BTCUSD",
        "ETH-USD": "ETHUSD",
    }
    
    @classmethod
    def get_mt5_symbol(cls, yahoo_symbol):
        """تحويل رمز Yahoo Finance إلى رمز MT5"""
        return cls.SYMBOL_MAP.get(yahoo_symbol, yahoo_symbol.replace("=X", "").replace("-", ""))
