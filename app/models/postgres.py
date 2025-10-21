"""
SQLAlchemy models for PostgreSQL database
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"

    user_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    emp_no = Column(String(50), unique=True, nullable=False, index=True)
    emp_nm = Column(String(100), nullable=True)
    
    # Relationships
    menu_votes = relationship("UserMenuVote", back_populates="user", cascade="all, delete-orphan")
    place_votes = relationship("UserPlaceVote", back_populates="user", cascade="all, delete-orphan")


class Menu(Base):
    """Menu model"""
    __tablename__ = "menu"

    menu_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    menu_type = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    votes = relationship("UserMenuVote", back_populates="menu", cascade="all, delete-orphan")


class Place(Base):
    """Place (Restaurant) model"""
    __tablename__ = "place"

    place_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    place_nm = Column(String(200), nullable=False)
    menu_type = Column(String(100), nullable=True, index=True)
    address = Column(String(500), nullable=True)
    contact_no = Column(String(50), nullable=True)
    naver_place_id = Column(String(500), nullable=True)
    
    # Relationships
    votes = relationship("UserPlaceVote", back_populates="place", cascade="all, delete-orphan")


class UserMenuVote(Base):
    """User menu vote model"""
    __tablename__ = "user_menu_vote"

    vote_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    menu_id = Column(BigInteger, ForeignKey("menu.menu_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="menu_votes")
    menu = relationship("Menu", back_populates="votes")


class UserPlaceVote(Base):
    """User place vote model"""
    __tablename__ = "user_place_vote"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False, index=True)
    place_id = Column(BigInteger, ForeignKey("place.place_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="place_votes")
    place = relationship("Place", back_populates="votes")


class UserDateVote(Base):
    """User date vote model"""
    __tablename__ = "user_date_vote"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    emp_no = Column(String(50), nullable=False, index=True)
    preferred_date = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class PlaceVote(Base):
    """Place vote model for vector integration"""
    __tablename__ = "place_votes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    emp_no = Column(String(50), nullable=False, index=True)
    place_id = Column(BigInteger, nullable=False, index=True)
    place_name = Column(String(200), nullable=False)
    menu_type = Column(String(100), nullable=True)
    action = Column(String(20), nullable=False)  # 'like', 'unlike'
    date = Column(String(20), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class RestaurantSuggestion(Base):
    """Restaurant suggestion model"""
    __tablename__ = "restaurant_suggestions"

    suggestion_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    place_nm = Column(String(200), nullable=False)
    link = Column(String(500), nullable=True)
    memo = Column(String(1000), nullable=True)
    emp_no = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    likes = relationship("RestaurantSuggestionLike", back_populates="suggestion", cascade="all, delete-orphan")
    comments = relationship("RestaurantSuggestionComment", back_populates="suggestion", cascade="all, delete-orphan")


class RestaurantSuggestionLike(Base):
    """Restaurant suggestion like model"""
    __tablename__ = "restaurant_suggestion_likes"

    like_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    suggestion_id = Column(BigInteger, ForeignKey("restaurant_suggestions.suggestion_id"), nullable=False, index=True)
    emp_no = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    suggestion = relationship("RestaurantSuggestion", back_populates="likes")


class RestaurantSuggestionComment(Base):
    """Restaurant suggestion comment model"""
    __tablename__ = "restaurant_suggestion_comments"

    comment_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    suggestion_id = Column(BigInteger, ForeignKey("restaurant_suggestions.suggestion_id"), nullable=False, index=True)
    emp_no = Column(String(50), nullable=False, index=True)
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    suggestion = relationship("RestaurantSuggestion", back_populates="comments")
    likes = relationship("RestaurantCommentLike", back_populates="comment", cascade="all, delete-orphan")


class RestaurantCommentLike(Base):
    """Restaurant comment like model"""
    __tablename__ = "restaurant_comment_likes"

    like_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    comment_id = Column(BigInteger, ForeignKey("restaurant_suggestion_comments.comment_id"), nullable=False, index=True)
    emp_no = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Relationships
    comment = relationship("RestaurantSuggestionComment", back_populates="likes")