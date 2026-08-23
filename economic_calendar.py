# economic_calendar.py
from datetime import datetime, timedelta
import pytz

# بيانات تقويمية مبسطة (يمكن جلبها من API خارجي)
ECONOMIC_EVENTS = {
    'FOMC': {'impact': 'HIGH', 'time': '14:00'},
    'NFP': {'impact': 'HIGH', 'time': '08:30'},
    'CPI': {'impact': 'HIGH', 'time': '08:30'},
    'PPI': {'impact': 'MEDIUM', 'time': '08:30'},
    'Retail Sales': {'impact': 'MEDIUM', 'time': '08:30'},
    'GDP': {'impact': 'HIGH', 'time': '08:30'},
    'Jobless Claims': {'impact': 'MEDIUM', 'time': '08:30'},
}

def get_next_event(eastern_tz):
    """إرجاع أقرب حدث اقتصادي وتأثيره"""
    now = datetime.now(eastern_tz)  # الآن بتوقيت شرق أمريكا (aware)
    today = now.date()
    
    for event, data in ECONOMIC_EVENTS.items():
        event_time = datetime.strptime(data['time'], '%H:%M').time()
        # إنشاء وقت الحدث وجعله aware بنفس المنطقة الزمنية
        event_dt = eastern_tz.localize(datetime.combine(today, event_time))
        if event_dt > now:
            time_diff = (event_dt - now).total_seconds() / 60  # دقائق
            if time_diff < 60:
                return event, data['impact'], time_diff
    return None, None, None

def apply_news_filter(signal_confidence, impact, minutes_until_event):
    """تعديل الثقة بناءً على الأخبار القادمة"""
    if impact == 'HIGH' and minutes_until_event < 30:
        return signal_confidence * 0.4
    elif impact == 'HIGH' and minutes_until_event < 60:
        return signal_confidence * 0.7
    elif impact == 'MEDIUM' and minutes_until_event < 30:
        return signal_confidence * 0.7
    else:
        return signal_confidence
