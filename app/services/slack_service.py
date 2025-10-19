"""
Slack authentication service
"""
import httpx
from typing import Optional

from app.core.config import settings
from app.schemas import SlackTokenResponse, SlackUserResponse


class SlackAuthService:
    """Slack OAuth service"""
    
    def __init__(self):
        self.client_id = settings.SLACK_CLIENT_ID
        self.client_secret = settings.SLACK_CLIENT_SECRET
        self.redirect_uri = settings.SLACK_REDIRECT_URI
    
    async def get_access_token(self, code: str) -> SlackTokenResponse:
        """Exchange authorization code for access token"""
        url = "https://slack.com/api/oauth.v2.access"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data, timeout=10.0)
            response.raise_for_status()
            
            result = response.json()
            return SlackTokenResponse(**result)
    
    async def get_user_info(self, access_token: str) -> SlackUserResponse:
        """Get user information from Slack"""
        url = "https://slack.com/api/users.identity"
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            
            result = response.json()
            return SlackUserResponse(**result)

