"""
Slack Authentication API routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.schemas import SlackTokenResponse, SlackUserResponse
from app.services.slack_service import SlackAuthService
from app.core.config import settings

router = APIRouter(prefix="/auth/slack", tags=["Slack Auth"])


@router.get("/callback")
async def slack_callback(code: str = Query(..., description="Authorization code from Slack")):
    """
    Slack OAuth callback endpoint
    """
    try:
        slack_service = SlackAuthService()
        
        # Exchange code for access token
        token_response = await slack_service.get_access_token(code)
        
        if not token_response.ok:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to get access token: {token_response.error}"
            )
        
        # Get user info
        user_response = await slack_service.get_user_info(token_response.access_token)
        
        if not user_response.ok:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to get user info: {user_response.error}"
            )
        
        # TODO: Store user info in database or session
        # For now, just return success
        
        return {
            "status": "success",
            "token": token_response.access_token,
            "user": user_response.user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login")
async def slack_login():
    """
    Redirect to Slack OAuth login page
    """
    slack_auth_url = (
        f"https://slack.com/oauth/v2/authorize?"
        f"client_id={settings.SLACK_CLIENT_ID}&"
        f"redirect_uri={settings.SLACK_REDIRECT_URI}&"
        f"scope=identity.basic,identity.email"
    )
    
    return RedirectResponse(url=slack_auth_url)

