"""
Chat API routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db, get_mongodb, get_redis
from app.schemas import ChatMessageRequest, MenuPreference, PlaceRedisDto
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.services.vote_service import VoteService
from app.services.place_service import PlaceService
from app.services.menu_service import MenuService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/menu-date-form", response_model=PlaceRedisDto)
async def process_menu_date_form(
    request: MenuPreference,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """
    Save user's menu and date preferences
    """
    try:
        # Initialize services
        menu_service = MenuService(db)
        user_service = UserService(db)
        vote_service = VoteService(db)
        place_service = PlaceService(db, redis)
        
        # Get all existing menu types
        all_menu_types = menu_service.get_all_menu_types()
        
        # Find new menu types
        new_menu_types = [mt for mt in request.menu_types if mt not in all_menu_types]
        
        # Save new menu types
        if new_menu_types:
            menu_service.save_new_menu_types(new_menu_types)
        
        # Get or create user
        user = user_service.get_or_create_user(request.emp_no)
        
        # Save menu and date preferences
        vote_service.save_menu_date_preference(request, user)
        
        # Process current month places
        place_dto = await place_service.process_current_month_places()
        
        return place_dto
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_chat(
    request: ChatMessageRequest,
    mongodb = Depends(get_mongodb),
    redis = Depends(get_redis)
):
    """
    Save chat messages to MongoDB
    """
    try:
        chat_service = ChatService(mongodb, redis)
        await chat_service.save_chat_messages(request.emp_no, request.messages)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages")
async def get_chat_messages(
    request: ChatMessageRequest,
    mongodb = Depends(get_mongodb),
    redis = Depends(get_redis)
):
    """
    Get chat messages from MongoDB/Redis
    """
    try:
        chat_service = ChatService(mongodb, redis)
        messages = await chat_service.get_chat_messages(request.emp_no)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset")
async def reset_vote_history(
    empNo: str,
    db: Session = Depends(get_db)
):
    """
    Reset user's vote history
    """
    try:
        vote_service = VoteService(db)
        vote_service.reset_vote_history(empNo)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

