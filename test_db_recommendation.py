"""
실제 DB 데이터를 사용한 추천 시스템 테스트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 한국 시간대 설정
from app.utils.timezone_utils import set_korean_timezone
set_korean_timezone()

from app.services.date_menu_recommendation_service import DateMenuRecommendationService
from app.core.database import init_db

def test_db_recommendations():
    """DB 기반 추천 시스템 테스트"""
    print("🔧 DB 기반 추천 시스템 테스트")
    print("=" * 50)
    
    # 데이터베이스 초기화
    print("📊 데이터베이스 초기화...")
    init_db()
    
    # 서비스 인스턴스 생성
    service = DateMenuRecommendationService()
    
    # 샘플 데이터 생성
    print("📝 샘플 데이터 생성...")
    if service.create_sample_data("EMP001"):
        print("✅ 샘플 데이터 생성 완료")
    else:
        print("❌ 샘플 데이터 생성 실패")
        return
    
    # 날짜 추천 테스트
    print("\n📅 날짜 추천 테스트...")
    date_recommendations = service.get_date_recommendations("EMP001", "회식")
    print(f"추천 날짜 수: {len(date_recommendations)}")
    for rec in date_recommendations[:3]:
        print(f"  - {rec['date']} ({rec['day_of_week']}) - 점수: {rec['score']:.2f}")
        print(f"    이유: {rec['reason']}")
        print(f"    DB 투표 수: {rec.get('db_votes', 0)}")
        print(f"    요일 인기도: {rec.get('popularity', 0.0):.2f}")
        print(f"    사용자 요일 선호도: {rec.get('user_weekday_preference', 0)}")
        print(f"    공휴일 여부: {rec.get('is_holiday', False)}")
    
    # 메뉴 추천 테스트
    print("\n🍽️ 메뉴 추천 테스트...")
    menu_recommendations = service.get_menu_recommendations("EMP001", "점심", "겨울")
    print(f"추천 메뉴 수: {len(menu_recommendations)}")
    for rec in menu_recommendations[:3]:
        print(f"  - {rec['name']} - 점수: {rec['score']:.2f}")
        print(f"    이유: {rec['reason']}")
        print(f"    소스: {rec.get('sources', [])}")
        print(f"    투표 수: {rec.get('vote_count', 0)}")
        print(f"    이전달 투표 수: {rec.get('previous_month_votes', 0)}")
        print(f"    사용자 선호도: {rec.get('user_preference', False)}")
    
    # 종합 추천 테스트
    print("\n🎯 종합 추천 테스트...")
    comprehensive = service.get_comprehensive_recommendations("EMP001", "다음 주 점심 어디 갈까?")
    print(f"컨텍스트: {comprehensive.get('context')}")
    print(f"계절: {comprehensive.get('season')}")
    print(f"날짜 추천 수: {len(comprehensive.get('date_recommendations', []))}")
    print(f"메뉴 추천 수: {len(comprehensive.get('menu_recommendations', []))}")
    print(f"조합 수: {len(comprehensive.get('combinations', []))}")
    
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_db_recommendations()
