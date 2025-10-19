"""
Place API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db, get_redis
from app.schemas import (
    PlaceRedisDto, 
    NewPlaceRequest, 
    PlaceVoteRequest, 
    PlaceVoteResponse
)
from app.services.place_service import PlaceService
from app.services.vote_service import VoteService
# SSE 매니저 제거 - 단순한 SSE 구현 사용

router = APIRouter(prefix="/places", tags=["Place"])


@router.post("/search", response_model=PlaceRedisDto)
async def search_places(
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Get recommended restaurant information for current month
    """
    try:
        place_service = PlaceService(db, redis)
        
        place_dto = await place_service.process_current_month_places()
        return place_dto
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/newPlace", response_model=int)
def add_new_place(
    request: NewPlaceRequest,
    db: Session = Depends(get_db)
):
    """
    Add a new place/restaurant
    """
    try:
        place_service = PlaceService(db)
        place = place_service.add_new_place(request.place_name, request.menu_type)
        return place.place_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vote", response_model=PlaceVoteResponse)
async def process_vote(
    request: PlaceVoteRequest,
    db: Session = Depends(get_db)
):
    """
    Process place vote (like/unlike)
    실시간 WebSocket 업데이트 포함
    """
    try:
        vote_service = VoteService(db)
        response = vote_service.process_place_vote(request)
        
        # 🔥 실시간 업데이트: SSE 매니저 제거 (단순한 SSE 구현 사용)
        print(f"📊 Place vote: {request.place_id} by {request.emp_no} - {request.action}")
        
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deleteAll")
def delete_all_places(db: Session = Depends(get_db)):
    """
    Delete all places (temporary API for testing)
    """
    try:
        place_service = PlaceService(db)
        place_service.delete_all_places()
        return {"message": "모든 식당 데이터가 삭제되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

