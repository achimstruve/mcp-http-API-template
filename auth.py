"""
Simple authentication module for MCP server.
This is a minimal implementation that can be extended for production use.
"""
import os
from typing import Optional, Dict, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class AuthContext:
    """Holds authentication context for a request"""
    def __init__(self, user_id: str, api_key: str, metadata: Optional[Dict[str, Any]] = None):
        self.user_id = user_id
        self.api_key = api_key
        self.metadata = metadata or {}


class SimpleAuthProvider:
    """
    Simple API key-based authentication provider.
    In production, replace with proper authentication (JWT, OAuth, etc.)
    """
    
    def __init__(self):
        # Load API keys from environment
        # Format: "user1:key1,user2:key2"
        api_keys_str = os.getenv("API_KEYS", "")
        self.api_keys = {}
        
        if api_keys_str:
            for pair in api_keys_str.split(","):
                if ":" in pair:
                    user_id, api_key = pair.strip().split(":", 1)
                    self.api_keys[api_key] = user_id
        
        # For demo purposes, add a default key if none configured
        if not self.api_keys and os.getenv("AUTH_ENABLED", "false").lower() == "true":
            logger.warning("No API keys configured. Using default demo key.")
            self.api_keys["demo-api-key"] = "demo-user"
    
    def validate_api_key(self, api_key: str) -> Optional[AuthContext]:
        """Validate API key and return auth context if valid"""
        if not api_key:
            return None
            
        user_id = self.api_keys.get(api_key)
        if user_id:
            return AuthContext(user_id=user_id, api_key=api_key)
        
        return None
    
    def extract_api_key(self, authorization: Optional[str]) -> Optional[str]:
        """Extract API key from Authorization header"""
        if not authorization:
            return None
            
        # Support "Bearer <token>" format
        if authorization.startswith("Bearer "):
            return authorization[7:]
        
        # Support direct API key
        return authorization


# Global auth provider instance
auth_provider = SimpleAuthProvider()


def get_auth_context(authorization: Optional[str]) -> Optional[AuthContext]:
    """Get authentication context from authorization header"""
    if not os.getenv("AUTH_ENABLED", "false").lower() == "true":
        # Authentication disabled, return default context
        return AuthContext(user_id="anonymous", api_key="")
    
    api_key = auth_provider.extract_api_key(authorization)
    if not api_key:
        return None
    
    return auth_provider.validate_api_key(api_key)


def require_auth(func):
    """Decorator to require authentication for MCP tools"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # In a real implementation, you'd get the auth context from the request
        # For this template, we'll check if auth is enabled
        if os.getenv("AUTH_ENABLED", "false").lower() == "true":
            # This is where you'd validate the current request's auth
            # For now, we'll just log a warning
            logger.info(f"Auth required for {func.__name__}")
        
        return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
    
    return wrapper


# For async functions
import asyncio