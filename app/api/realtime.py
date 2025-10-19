"""
Real-time voting API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, List

from app.core.database import get_db
from app.models.postgres import UserMenuVote, UserPlaceVote, UserDateVote, Menu, Place, User
from pydantic import BaseModel

router = APIRouter(prefix="/realtime", tags=["Realtime"])


class MenuVoteStats(BaseModel):
    """Menu vote statistics"""
    menu_type: str
    vote_count: int
    voters: List[str]  # emp_no list


class PlaceVoteStats(BaseModel):
    """Place vote statistics"""
    place_id: int
    place_name: str
    menu_type: str
    vote_count: int
    voters: List[str]  # emp_no list


class DateVoteStats(BaseModel):
    """Date vote statistics"""
    preferred_date: str
    vote_count: int
    voters: List[str]  # emp_no list


class VoteStatsResponse(BaseModel):
    """Real-time vote statistics response"""
    menu_votes: List[MenuVoteStats]
    place_votes: List[PlaceVoteStats]
    date_votes: List[DateVoteStats]
    total_voters: int
    active_voters: int
    last_updated: int  # timestamp


@router.get("/vote-stats", response_model=VoteStatsResponse)
def get_vote_stats(db: Session = Depends(get_db)):
    """
    Get real-time vote statistics for all categories
    실시간 투표 통계 조회
    """
    import time
    
    # Menu votes
    menu_votes_query = (
        db.query(
            Menu.menu_type,
            func.count(UserMenuVote.vote_id).label("vote_count")
        )
        .outerjoin(UserMenuVote, Menu.menu_id == UserMenuVote.menu_id)
        .group_by(Menu.menu_type)
        .all()
    )
    
    menu_votes = []
    for menu_type, vote_count in menu_votes_query:
        # Get voters for this menu
        voters = (
            db.query(User.emp_no)
            .join(UserMenuVote, User.user_id == UserMenuVote.user_id)
            .join(Menu, UserMenuVote.menu_id == Menu.menu_id)
            .filter(Menu.menu_type == menu_type)
            .all()
        )
        
        menu_votes.append(MenuVoteStats(
            menu_type=menu_type,
            vote_count=vote_count or 0,
            voters=[v[0] for v in voters]
        ))
    
    # Place votes
    place_votes_query = (
        db.query(
            Place.place_id,
            Place.place_nm,
            Place.menu_type,
            func.count(UserPlaceVote.id).label("vote_count")
        )
        .outerjoin(UserPlaceVote, Place.place_id == UserPlaceVote.place_id)
        .group_by(Place.place_id, Place.place_nm, Place.menu_type)
        .all()
    )
    
    place_votes = []
    for place_id, place_name, menu_type, vote_count in place_votes_query:
        # Get voters for this place
        voters = (
            db.query(User.emp_no)
            .join(UserPlaceVote, User.user_id == UserPlaceVote.user_id)
            .filter(UserPlaceVote.place_id == place_id)
            .all()
        )
        
        place_votes.append(PlaceVoteStats(
            place_id=place_id,
            place_name=place_name,
            menu_type=menu_type or "",
            vote_count=vote_count or 0,
            voters=[v[0] for v in voters]
        ))
    
    # Date votes
    date_votes_query = (
        db.query(
            UserDateVote.preferred_date,
            func.count(UserDateVote.id).label("vote_count")
        )
        .group_by(UserDateVote.preferred_date)
        .all()
    )
    
    date_votes = []
    for preferred_date, vote_count in date_votes_query:
        # Get voters for this date
        voters = (
            db.query(UserDateVote.emp_no)
            .filter(UserDateVote.preferred_date == preferred_date)
            .all()
        )
        
        date_votes.append(DateVoteStats(
            preferred_date=preferred_date,
            vote_count=vote_count or 0,
            voters=[v[0] for v in voters]
        ))
    
    # Count total unique voters
    total_voters = db.query(User.user_id).count()
    
    # Count active voters (users who have voted for at least one thing)
    active_voters_count = (
        db.query(User.user_id)
        .outerjoin(UserMenuVote, User.user_id == UserMenuVote.user_id)
        .outerjoin(UserPlaceVote, User.user_id == UserPlaceVote.user_id)
        .filter(
            (UserMenuVote.vote_id.isnot(None)) | 
            (UserPlaceVote.id.isnot(None))
        )
        .distinct()
        .count()
    )
    
    return VoteStatsResponse(
        menu_votes=menu_votes,
        place_votes=place_votes,
        date_votes=date_votes,
        total_voters=total_voters,
        active_voters=active_voters_count,
        last_updated=int(time.time() * 1000)
    )


@router.get("/menu-votes", response_model=List[MenuVoteStats])
def get_menu_votes(db: Session = Depends(get_db)):
    """
    Get real-time menu vote statistics
    메뉴별 실시간 투표 통계
    """
    menu_votes_query = (
        db.query(
            Menu.menu_type,
            func.count(UserMenuVote.vote_id).label("vote_count")
        )
        .outerjoin(UserMenuVote, Menu.menu_id == UserMenuVote.menu_id)
        .group_by(Menu.menu_type)
        .all()
    )
    
    result = []
    for menu_type, vote_count in menu_votes_query:
        voters = (
            db.query(User.emp_no)
            .join(UserMenuVote, User.user_id == UserMenuVote.user_id)
            .join(Menu, UserMenuVote.menu_id == Menu.menu_id)
            .filter(Menu.menu_type == menu_type)
            .all()
        )
        
        result.append(MenuVoteStats(
            menu_type=menu_type,
            vote_count=vote_count or 0,
            voters=[v[0] for v in voters]
        ))
    
    return result


@router.get("/place-votes", response_model=List[PlaceVoteStats])
def get_place_votes(db: Session = Depends(get_db)):
    """
    Get real-time place vote statistics
    식당별 실시간 투표 통계
    """
    place_votes_query = (
        db.query(
            Place.place_id,
            Place.place_nm,
            Place.menu_type,
            func.count(UserPlaceVote.id).label("vote_count")
        )
        .outerjoin(UserPlaceVote, Place.place_id == UserPlaceVote.place_id)
        .group_by(Place.place_id, Place.place_nm, Place.menu_type)
        .all()
    )
    
    result = []
    for place_id, place_name, menu_type, vote_count in place_votes_query:
        voters = (
            db.query(User.emp_no)
            .join(UserPlaceVote, User.user_id == UserPlaceVote.user_id)
            .filter(UserPlaceVote.place_id == place_id)
            .all()
        )
        
        result.append(PlaceVoteStats(
            place_id=place_id,
            place_name=place_name,
            menu_type=menu_type or "",
            vote_count=vote_count or 0,
            voters=[v[0] for v in voters]
        ))
    
    return result

