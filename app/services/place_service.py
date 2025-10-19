"""
Place service layer
"""
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from redis.asyncio import Redis

from app.models.postgres import Place, Menu
from app.schemas import PlaceCreate, PlaceResponse, PlaceRedisDto
from app.core.constants import PLACE_KEY_PREFIX, PLACE_EXPIRATION_DAYS


class PlaceService:
    """Place service for business logic"""
    
    def __init__(self, db: Session, redis: Optional[Redis] = None):
        self.db = db
        self.redis = redis
    
    async def process_current_month_places(self) -> PlaceRedisDto:
        """Process and cache places for current month"""
        current_month_key = datetime.now().strftime("%Y%m")
        
        # Get places by menu type
        menus = self.db.query(Menu).all()
        places_by_menu_type: Dict[str, List[PlaceResponse]] = {}
        
        for menu in menus:
            places = self.db.query(Place).filter(Place.menu_type == menu.menu_type).all()
            places_by_menu_type[menu.menu_type] = [
                PlaceResponse(
                    place_id=place.place_id,
                    place_nm=place.place_nm,
                    menu_type=place.menu_type,
                    address=place.address,
                    contact_no=place.contact_no,
                    naver_place_id=place.naver_place_id,
                    vote_cnt=len(place.votes) if hasattr(place, 'votes') else 0
                )
                for place in places
            ]
        
        place_dto = PlaceRedisDto(
            monthKey=current_month_key,
            placesByMenuType=places_by_menu_type
        )
        
        # Save to Redis
        if self.redis:
            await self.save_places_to_redis(place_dto)
        
        return place_dto
    
    async def save_places_to_redis(self, place_dto: PlaceRedisDto):
        """Save places to Redis cache"""
        if not self.redis:
            return
        
        key = f"{PLACE_KEY_PREFIX}{place_dto.month_key}"
        # Convert to dict and then to JSON string
        value = place_dto.model_dump_json()
        await self.redis.setex(key, PLACE_EXPIRATION_DAYS * 86400, value)
    
    async def get_places_from_redis(self, month_key: str) -> Optional[PlaceRedisDto]:
        """Get places from Redis cache"""
        if not self.redis:
            return None
        
        key = f"{PLACE_KEY_PREFIX}{month_key}"
        value = await self.redis.get(key)
        
        if value:
            return PlaceRedisDto.model_validate_json(value)
        
        return None
    
    def add_new_place(self, place_name: str, menu_type: str) -> Place:
        """Add a new place manually"""
        # Check if place already exists
        existing = self.db.query(Place).filter(
            Place.place_nm == place_name,
            Place.menu_type == menu_type
        ).first()
        
        if existing:
            return existing
        
        place = Place(
            place_nm=place_name,
            menu_type=menu_type
        )
        
        self.db.add(place)
        self.db.commit()
        self.db.refresh(place)
        
        return place
    
    def delete_all_places(self):
        """Delete all places (for testing)"""
        self.db.query(Place).delete()
        self.db.commit()
    
    def get_place_vote_info(self) -> List[PlaceResponse]:
        """Get all places with vote counts"""
        places = self.db.query(Place).all()
        
        return [
            PlaceResponse(
                place_id=place.place_id,
                place_nm=place.place_nm,
                menu_type=place.menu_type,
                address=place.address,
                contact_no=place.contact_no,
                naver_place_id=place.naver_place_id,
                vote_cnt=len(place.votes) if hasattr(place, 'votes') else 0
            )
            for place in places
        ]

