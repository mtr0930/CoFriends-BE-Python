"""
API router module - combines all API routes
"""
from fastapi import APIRouter

from app.api import chat, menu, place, ai_chat, ai_insights, realtime
from app.api import restaurant_suggestions, scheduler, conversational, chat_history, personalized_recommendation, hybrid_recommendation, hybrid_chat, date_menu_recommendation

api_router = APIRouter()

# Include all sub-routers (excluding slack - handled separately)
api_router.include_router(chat.router)
api_router.include_router(menu.router)
api_router.include_router(place.router)
api_router.include_router(ai_chat.router)
api_router.include_router(ai_insights.router)
api_router.include_router(realtime.router)
api_router.include_router(restaurant_suggestions.router)
api_router.include_router(scheduler.router)
api_router.include_router(conversational.router)
api_router.include_router(chat_history.router)
api_router.include_router(personalized_recommendation.router)
api_router.include_router(hybrid_recommendation.router)
api_router.include_router(hybrid_chat.router)
api_router.include_router(date_menu_recommendation.router)

