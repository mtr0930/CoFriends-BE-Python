"""
월별 데이터 처리 유틸리티
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_current_month() -> str:
    """현재 월을 YYYYMM 형식으로 반환"""
    return datetime.now().strftime("%Y%m")


def get_recent_months(count: int) -> List[str]:
    """최근 N개월의 YYYYMM 형식 리스트 반환"""
    months = []
    current = datetime.now()
    
    for i in range(count):
        month = current - timedelta(days=30 * i)
        months.append(month.strftime("%Y%m"))
    
    return months


def get_month_name(month_str: str) -> str:
    """YYYYMM 형식을 한국어 월 이름으로 변환"""
    try:
        year = int(month_str[:4])
        month = int(month_str[4:6])
        return f"{year}년 {month}월"
    except:
        return month_str


def calculate_monthly_weights(months: List[str]) -> Dict[str, float]:
    """월별 가중치 계산 (동일 가중치)"""
    if not months:
        return {}
    
    # 동일 가중치 적용
    weight = 1.0 / len(months)
    return {month: weight for month in months}


def get_monthly_statistics(data: List[Dict[str, Any]], month_field: str = "vote_month") -> Dict[str, int]:
    """월별 통계 계산"""
    stats = {}
    for item in data:
        month = item.get(month_field, "")
        if month:
            stats[month] = stats.get(month, 0) + 1
    return stats


def format_monthly_data(monthly_data: Dict[str, int]) -> str:
    """월별 데이터를 읽기 쉬운 형식으로 변환"""
    if not monthly_data:
        return "데이터 없음"
    
    formatted = []
    for month, count in monthly_data.items():
        month_name = get_month_name(month)
        formatted.append(f"{month_name}: {count}건")
    
    return ", ".join(formatted)
