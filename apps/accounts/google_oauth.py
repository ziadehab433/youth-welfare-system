"""
Google OAuth 2.0 Service for SSO
Handles token exchange and user data retrieval
"""

import requests
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """
    Service to handle Google OAuth authentication
    """
    
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    CLIENT_ID = config('GOOGLE_OAUTH_CLIENT_ID')
    CLIENT_SECRET = config('GOOGLE_OAUTH_CLIENT_SECRET')
    REDIRECT_URI = config('GOOGLE_OAUTH_REDIRECT_URI')
    
    @staticmethod
    def get_authorization_url():
        """Generate Google OAuth authorization URL"""
        from urllib.parse import urlencode
        
        google_auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,  # ← Uses settings
            'response_type': 'code',
            'scope': 'email profile',
            'access_type': 'offline',
        }
        
        return f"{google_auth_url}?{urlencode(params)}"
    
    @classmethod
    def exchange_code_for_token(cls, code):
        """
        Exchange authorization code for access token
        
        Args:
            code (str): Authorization code from Google
            
        Returns:
            dict: Contains 'access_token', 'id_token', 'expires_in', etc.
                 or None if exchange fails
        """
        try:
            data = {
                'client_id': cls.CLIENT_ID,
                'client_secret': cls.CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': cls.REDIRECT_URI,
            }
            
            response = requests.post(cls.GOOGLE_TOKEN_URL, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Successfully exchanged authorization code for token")
                return response.json()
            else:
                logger.error(f"Token exchange failed: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Token exchange request failed: {e}")
            return None
    
    @classmethod
    def get_user_info(cls, access_token):
        """
        Fetch user info from Google using access token
        
        Args:
            access_token (str): Google access token
            
        Returns:
            dict: User info containing 'id', 'email', 'name', 'picture'
                 or None if request fails
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(
                cls.GOOGLE_USERINFO_URL,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Successfully retrieved user info for: {user_info.get('email')}")
                return user_info
            else:
                logger.error(f"Failed to get user info: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"User info request failed: {e}")
            return None
    
    @staticmethod
    def authenticate_user(code):
        """Exchange authorization code for user info"""
        import requests
        
        token_url = 'https://oauth2.googleapis.com/token'
        
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,  # ← MUST match
            'grant_type': 'authorization_code',
        }
        
        try:
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            tokens = response.json()
            access_token = tokens.get('access_token')
            
            # Get user info
            user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            
            user_response = requests.get(user_info_url, headers=headers)
            user_response.raise_for_status()
            
            user_data = user_response.json()
            
            return {
                'google_id': user_data.get('id'),
                'email': user_data.get('email'),
                'name': user_data.get('name'),
                'picture': user_data.get('picture'),
            }
        
        except Exception as e:
            logger.error(f"Google OAuth authentication failed: {e}")
            return None