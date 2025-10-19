"""
AI-related Pydantic schemas
"""
from pydantic import BaseModel
from typing import List, Optional


class MeetingInsight(BaseModel):
    """AI-generated meeting insights"""
    summary: str
    recommendedMenus: List[str]
    actionItems: List[str]
    sentimentScore: Optional[float] = None
    
    class Config:
        from_attributes = True


class AiPromptRequest(BaseModel):
    """AI prompt request"""
    empNo: str
    prompt: str


class AiPromptResponse(BaseModel):
    """AI prompt response"""
    response: str
    contextUsed: List[str]
    
    class Config:
        from_attributes = True
