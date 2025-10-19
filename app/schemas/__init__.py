"""
Pydantic schemas (DTOs) for request/response validation
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


# User Schemas
class UserBase(BaseModel):
    emp_no: str = Field(..., description="Employee number")
    emp_nm: Optional[str] = Field(None, description="Employee name")


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# Menu Schemas
class MenuBase(BaseModel):
    menu_type: str = Field(..., description="Menu type")


class MenuCreate(MenuBase):
    pass


class MenuResponse(MenuBase):
    menu_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MenuInitResponse(BaseModel):
    status: str
    message: str
    menu_types: List[str]
    vote_counts: Dict[str, int]


# Place Schemas
class PlaceBase(BaseModel):
    place_nm: str = Field(..., description="Place name")
    menu_type: Optional[str] = Field(None, description="Menu type")
    address: Optional[str] = Field(None, description="Address")
    contact_no: Optional[str] = Field(None, description="Contact number")
    naver_place_id: Optional[str] = Field(None, description="Naver place ID/URL")


class PlaceCreate(PlaceBase):
    pass


class PlaceResponse(PlaceBase):
    place_id: int
    vote_cnt: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class NewPlaceRequest(BaseModel):
    place_name: str = Field(..., alias="placeName")
    menu_type: str = Field(..., alias="menuType")

    model_config = ConfigDict(populate_by_name=True)


# Vote Schemas
class MenuPreference(BaseModel):
    emp_no: str = Field(..., alias="empNo", description="Employee number")
    menu_types: List[str] = Field(..., alias="menuTypes", description="Selected menu types")
    preferred_dates: List[str] = Field(..., alias="preferredDates", description="Preferred dates")

    model_config = ConfigDict(populate_by_name=True)


class PlaceVoteRequest(BaseModel):
    emp_no: str = Field(..., alias="empNo")
    place_id: int = Field(..., alias="placeId")
    action: str = Field(..., description="'like' or 'unlike'")

    model_config = ConfigDict(populate_by_name=True)


class PlaceVoteResponse(BaseModel):
    place_id: int = Field(..., alias="placeId")
    vote_count: int = Field(..., alias="voteCount")
    is_voted: bool = Field(..., alias="isVoted")

    model_config = ConfigDict(populate_by_name=True)


# Chat Schemas
class ChatMessageRequest(BaseModel):
    emp_no: str = Field(..., alias="empNo")
    messages: List[Dict[str, Any]]

    model_config = ConfigDict(populate_by_name=True)


class ChatMessageResponse(BaseModel):
    emp_no: str = Field(..., alias="empNo")
    messages: List[Dict[str, Any]]

    model_config = ConfigDict(populate_by_name=True)


# Place Redis DTO
class PlaceRedisDto(BaseModel):
    month_key: str = Field(..., alias="monthKey")
    places_by_menu_type: Dict[str, List[PlaceResponse]] = Field(..., alias="placesByMenuType")

    model_config = ConfigDict(populate_by_name=True)


# Slack Schemas
class SlackTokenResponse(BaseModel):
    ok: bool
    access_token: Optional[str] = Field(None, alias="accessToken")
    token_type: Optional[str] = Field(None, alias="tokenType")
    scope: Optional[str] = None
    bot_user_id: Optional[str] = Field(None, alias="botUserId")
    app_id: Optional[str] = Field(None, alias="appId")
    team: Optional[Dict[str, Any]] = None
    enterprise: Optional[Dict[str, Any]] = None
    authed_user: Optional[Dict[str, Any]] = Field(None, alias="authedUser")
    error: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class SlackUserResponse(BaseModel):
    ok: bool
    user: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# AI Schemas
class MeetingInsight(BaseModel):
    """AI-generated meeting insights"""
    summary: str
    recommendedMenus: List[str] = Field(..., alias="recommendedMenus")
    actionItems: List[str] = Field(..., alias="actionItems")
    sentimentScore: Optional[float] = Field(None, alias="sentimentScore")

    model_config = ConfigDict(populate_by_name=True)


# Restaurant Suggestion Schemas
class RestaurantSuggestionRequest(BaseModel):
    """Restaurant suggestion request"""
    name: str = Field(..., description="Restaurant name", alias="place_nm")
    link: Optional[str] = Field(None, description="Restaurant link (review, blog, map, etc.)")
    description: Optional[str] = Field(None, description="Introduction description", alias="memo")
    empNo: str = Field(..., description="Employee number who suggested", alias="emp_no")
    
    model_config = ConfigDict(populate_by_name=True)


class RestaurantSuggestionResponse(BaseModel):
    """Restaurant suggestion response"""
    suggestion_id: int
    place_nm: str
    link: Optional[str]
    memo: Optional[str]
    emp_no: str
    created_at: datetime
    like_count: int = 0
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)


class RestaurantSuggestionListResponse(BaseModel):
    """Restaurant suggestion list response"""
    suggestions: List[RestaurantSuggestionResponse]
    total_count: int
    page: int
    size: int


# Restaurant Comment Schemas
class RestaurantCommentRequest(BaseModel):
    """Restaurant comment request"""
    message: str = Field(..., description="Comment message")
    empNo: str = Field(..., description="Employee number", alias="emp_no")
    
    model_config = ConfigDict(populate_by_name=True)


class RestaurantCommentResponse(BaseModel):
    """Restaurant comment response"""
    comment_id: int
    suggestion_id: int
    emp_no: str
    message: str
    created_at: datetime
    like_count: int = 0
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)

