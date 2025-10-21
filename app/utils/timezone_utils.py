"""
시간대 관련 유틸리티
"""
import os
from datetime import datetime
import pytz
from app.core.config import settings


def set_korean_timezone():
    """한국 시간대로 설정"""
    os.environ['TZ'] = 'Asia/Seoul'
    
    # Python의 datetime이 한국 시간대를 사용하도록 설정
    try:
        import time
        time.tzset()
    except AttributeError:
        # Windows에서는 tzset이 없음
        pass


def get_korean_now() -> datetime:
    """한국 시간 현재 시각 반환"""
    korean_tz = pytz.timezone('Asia/Seoul')
    return datetime.now(korean_tz)


def get_korean_datetime_str() -> str:
    """한국 시간 현재 시각을 문자열로 반환"""
    return get_korean_now().strftime("%Y-%m-%d %H:%M:%S")


def convert_to_korean_time(dt: datetime) -> datetime:
    """UTC 시간을 한국 시간으로 변환"""
    if dt.tzinfo is None:
        # timezone 정보가 없으면 UTC로 가정
        dt = pytz.utc.localize(dt)
    
    korean_tz = pytz.timezone('Asia/Seoul')
    return dt.astimezone(korean_tz)


def format_korean_time(dt: datetime) -> str:
    """한국 시간 형식으로 포맷"""
    korean_dt = convert_to_korean_time(dt)
    return korean_dt.strftime("%Y-%m-%d %H:%M:%S")


def get_korean_date_str() -> str:
    """한국 시간 현재 날짜를 YYYY-MM-DD 형식으로 반환"""
    return get_korean_now().strftime("%Y-%m-%d")


def get_korean_month_str() -> str:
    """한국 시간 현재 월을 YYYYMM 형식으로 반환"""
    return get_korean_now().strftime("%Y%m")
