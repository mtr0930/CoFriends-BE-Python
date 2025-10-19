"""
AI Insights API for meeting analysis and recommendations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.postgres import User, Menu, Place, UserMenuVote, UserDateVote, UserPlaceVote
from app.schemas import MeetingInsight

router = APIRouter(prefix="/ai", tags=["AI Insights"])


@router.get("/insights", response_model=MeetingInsight)
async def get_meeting_insights(
    empNo: str,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered meeting insights and recommendations
    
    Args:
        empNo: Employee number
        
    Returns:
        MeetingInsight: AI-generated insights including summary, recommended menus, and action items
    """
    try:
        # Get user's voting history
        user_votes = await get_user_voting_history(db, empNo)
        
        # Get popular choices from all users
        popular_choices = await get_popular_choices(db)
        
        # Generate AI insights
        insights = await generate_ai_insights(user_votes, popular_choices, empNo)
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")


async def get_user_voting_history(db: Session, emp_no: str) -> Dict:
    """Get user's voting history"""
    try:
        # Get user's menu votes
        menu_votes = db.query(UserMenuVote).filter(
            UserMenuVote.emp_no == emp_no
        ).all()
        
        # Get user's place votes  
        place_votes = db.query(UserPlaceVote).filter(
            UserPlaceVote.emp_no == emp_no
        ).all()
        
        # Get user's date votes
        date_votes = db.query(UserDateVote).filter(
            UserDateVote.emp_no == emp_no
        ).all()
        
        return {
            "menu_votes": [{"menu_type": vote.menu_type, "vote_date": vote.vote_date} for vote in menu_votes],
            "place_votes": [{"place_id": vote.place_id, "vote_date": vote.vote_date} for vote in place_votes],
            "date_votes": [{"preferred_date": vote.preferred_date, "vote_date": vote.vote_date} for vote in date_votes]
        }
    except Exception as e:
        print(f"Error getting user voting history: {e}")
        return {"menu_votes": [], "place_votes": [], "date_votes": []}


async def get_popular_choices(db: Session) -> Dict:
    """Get popular choices from all users"""
    try:
        # Get popular menu types
        menu_stats = db.query(UserMenuVote.menu_type, db.func.count(UserMenuVote.menu_type)).group_by(
            UserMenuVote.menu_type
        ).all()
        
        # Get popular places
        place_stats = db.query(UserPlaceVote.place_id, db.func.count(UserPlaceVote.place_id)).group_by(
            UserPlaceVote.place_id
        ).all()
        
        # Get popular dates
        date_stats = db.query(UserDateVote.preferred_date, db.func.count(UserDateVote.preferred_date)).group_by(
            UserDateVote.preferred_date
        ).all()
        
        return {
            "popular_menus": [{"menu_type": menu_type, "count": count} for menu_type, count in menu_stats],
            "popular_places": [{"place_id": place_id, "count": count} for place_id, count in place_stats],
            "popular_dates": [{"date": date, "count": count} for date, count in date_stats]
        }
    except Exception as e:
        print(f"Error getting popular choices: {e}")
        return {"popular_menus": [], "popular_places": [], "popular_dates": []}


async def generate_ai_insights(user_votes: Dict, popular_choices: Dict, emp_no: str) -> MeetingInsight:
    """Generate AI insights based on voting data"""
    
    # Analyze user preferences
    user_menu_preferences = [vote["menu_type"] for vote in user_votes.get("menu_votes", [])]
    user_place_preferences = [vote["place_id"] for vote in user_votes.get("place_votes", [])]
    user_date_preferences = [vote["preferred_date"] for vote in user_votes.get("date_votes", [])]
    
    # Get popular choices
    popular_menus = [choice["menu_type"] for choice in popular_choices.get("popular_menus", [])[:3]]
    popular_places = [choice["place_id"] for choice in popular_choices.get("popular_places", [])[:3]]
    popular_dates = [choice["date"] for choice in popular_choices.get("popular_dates", [])[:3]]
    
    # Generate summary
    summary = f"사용자 {emp_no}님의 투표 패턴을 분석한 결과, "
    
    if user_menu_preferences:
        summary += f"선호하는 메뉴는 {', '.join(set(user_menu_preferences))}입니다. "
    else:
        summary += "아직 메뉴 투표 기록이 없습니다. "
        
    if user_place_preferences:
        summary += f"선호하는 식당은 {', '.join(map(str, set(user_place_preferences)))}입니다. "
    else:
        summary += "아직 식당 투표 기록이 없습니다. "
        
    if user_date_preferences:
        summary += f"선호하는 날짜는 {', '.join(set(user_date_preferences))}입니다."
    else:
        summary += "아직 날짜 투표 기록이 없습니다."
    
    # Generate recommended menus
    recommended_menus = []
    if popular_menus:
        recommended_menus = popular_menus[:3]
    else:
        recommended_menus = ["한식", "중식", "일식"]  # Default recommendations
    
    # Generate action items
    action_items = []
    
    if not user_menu_preferences:
        action_items.append("메뉴 투표에 참여하여 선호도를 알려주세요")
    
    if not user_place_preferences:
        action_items.append("식당 투표에 참여하여 추천해주세요")
        
    if not user_date_preferences:
        action_items.append("선호하는 날짜를 선택해주세요")
    
    if not action_items:
        action_items.append("팀원들과 함께 투표에 참여해보세요")
        action_items.append("새로운 식당을 추천해보세요")
    
    # Calculate sentiment score (simple algorithm)
    total_votes = len(user_menu_preferences) + len(user_place_preferences) + len(user_date_preferences)
    sentiment_score = min(1.0, total_votes / 10.0)  # Scale 0-1 based on participation
    
    return MeetingInsight(
        summary=summary,
        recommendedMenus=recommended_menus,
        actionItems=action_items,
        sentimentScore=sentiment_score
    )
