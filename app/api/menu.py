"""
Menu API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import MenuInitResponse
from app.services.menu_service import MenuService

router = APIRouter(prefix="/menu", tags=["Menu"])


@router.post("/init", response_model=MenuInitResponse)
def initialize_and_get_menus(db: Session = Depends(get_db)):
    """
    Initialize default menus and get all menu types with vote counts
    """
    try:
        menu_service = MenuService(db)
        
        # Initialize default menus
        menu_service.initialize_default_menus()
        
        # Get all menu types and vote counts
        menu_types = menu_service.get_all_menu_types()
        vote_counts = menu_service.get_vote_counts()
        
        return MenuInitResponse(
            status="S",
            message="기본 메뉴 초기화 완료",
            menu_types=menu_types,
            vote_counts=vote_counts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

