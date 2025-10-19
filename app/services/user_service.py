"""
User service layer
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.postgres import User


class UserService:
    """User service for business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_user(self, emp_no: str, emp_nm: Optional[str] = None) -> User:
        """Get user by emp_no or create if not exists"""
        user = self.db.query(User).filter(User.emp_no == emp_no).first()
        
        if not user:
            user = User(emp_no=emp_no, emp_nm=emp_nm)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def get_user_by_emp_no(self, emp_no: str) -> Optional[User]:
        """Get user by employee number"""
        return self.db.query(User).filter(User.emp_no == emp_no).first()

