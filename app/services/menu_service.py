"""
Menu service layer
"""
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.postgres import Menu, UserMenuVote
from app.core.constants import DEFAULT_MENU_TYPES


class MenuService:
    """Menu service for business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_default_menus(self) -> List[Menu]:
        """Initialize default menu types"""
        menus = []
        for menu_type in DEFAULT_MENU_TYPES:
            existing = self.db.query(Menu).filter(Menu.menu_type == menu_type).first()
            if not existing:
                menu = Menu(menu_type=menu_type)
                self.db.add(menu)
                menus.append(menu)
        
        self.db.commit()
        return menus
    
    def get_all_menu_types(self) -> List[str]:
        """Get all menu types"""
        menus = self.db.query(Menu).all()
        return [menu.menu_type for menu in menus]
    
    def get_vote_counts(self) -> Dict[str, int]:
        """Get vote counts for each menu type"""
        menus = self.db.query(Menu).all()
        vote_counts = {}
        
        for menu in menus:
            count = self.db.query(UserMenuVote).filter(
                UserMenuVote.menu_id == menu.menu_id
            ).count()
            vote_counts[menu.menu_type] = count
        
        return vote_counts
    
    def save_new_menu_types(self, menu_types: List[str]) -> List[Menu]:
        """Save new menu types"""
        menus = []
        for menu_type in menu_types:
            menu = Menu(menu_type=menu_type)
            self.db.add(menu)
            menus.append(menu)
        
        self.db.commit()
        return menus
    
    def get_menu_by_type(self, menu_type: str) -> Menu:
        """Get menu by type"""
        return self.db.query(Menu).filter(Menu.menu_type == menu_type).first()

