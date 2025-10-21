"""
Personalized Recommendation Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from pydantic import ConfigDict


class PersonalizedRecommendationRequest(BaseModel):
    """Personalized recommendation request"""
    emp_no: str = Field(..., description="Employee number")
    query_text: Optional[str] = Field(None, description="Search query text")
    
    model_config = ConfigDict(populate_by_name=True)


class PersonalizedRecommendationResponse(BaseModel):
    """Personalized recommendation response"""
    id: str = Field(..., description="Recommendation ID")
    document: str = Field(..., description="Document content")
    metadata: dict = Field(..., description="Recommendation metadata")
    personalization_score: float = Field(..., description="Personalization score")
    recommendation_reason: str = Field(..., description="Recommendation reason")
    distance: float = Field(..., description="Similarity distance")
    
    model_config = ConfigDict(from_attributes=True)


class VoteEmbeddingRequest(BaseModel):
    """Vote embedding request"""
    emp_no: str = Field(..., description="Employee number")
    place_name: str = Field(..., description="Place name")
    menu_type: str = Field(..., description="Menu type")
    date: Optional[str] = Field(None, description="Vote date")
    preferences: Optional[str] = Field(None, description="User preferences")
    vote_type: str = Field("restaurant", description="Type of vote")
    
    model_config = ConfigDict(populate_by_name=True)


class RestaurantEmbeddingRequest(BaseModel):
    """Restaurant embedding request"""
    place_id: str = Field(..., description="Place ID")
    place_name: str = Field(..., description="Place name")
    menu_type: Optional[str] = Field(None, description="Menu type")
    address: Optional[str] = Field(None, description="Address")
    category: Optional[str] = Field(None, description="Category")
    
    model_config = ConfigDict(populate_by_name=True)
