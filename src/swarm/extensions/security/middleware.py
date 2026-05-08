"""
Security Middleware for Open-Swarm
--------------------------------
This module provides security middleware for API key validation and CORS handling.
"""

import logging
import os
from functools import wraps
from typing import Optional, List, Set
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from swarm.settings import DEBUG

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)


class SecurityConfig:
    """
    Global security configuration.
    """
    _api_keys: Set[str] = set()
    _allowed_origins: List[str] = []

    @classmethod
    def configure(cls, api_keys: Optional[List[str]] = None, allowed_origins: Optional[List[str]] = None):
        """
        Configure security settings.
        
        Args:
            api_keys: List of valid API keys
            allowed_origins: List of allowed CORS origins
        """
        if api_keys:
            cls._api_keys = set(api_keys)
        else:
            # Check environment for API key
            env_key = os.getenv('OPEN_SWARM_API_KEY')
            if env_key:
                cls._api_keys = {env_key}
            else:
                logger.warning("No API keys configured - server is insecure!")
                cls._api_keys = set()
                
        if allowed_origins:
            cls._allowed_origins = allowed_origins
        else:
            logger.warning("No CORS origins configured - defaulting to none allowed")
            cls._allowed_origins = []

    @classmethod
    def get_api_keys(cls) -> Set[str]:
        """Get configured API keys."""
        return cls._api_keys

    @classmethod
    def get_allowed_origins(cls) -> List[str]:
        """Get configured allowed origins."""
        return cls._allowed_origins


def validate_api_key(view_func):
    """
    Decorator to validate API key in request headers.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if DEBUG:
            # Skip validation in debug mode
            return view_func(request, *args, **kwargs)
            
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Request missing API key")
            return JsonResponse(
                {"error": "API key required"}, 
                status=401
            )
            
        if not SecurityConfig.get_api_keys():
            logger.warning("No API keys configured")
            return JsonResponse(
                {"error": "Server API keys not configured"}, 
                status=500
            )
            
        if api_key not in SecurityConfig.get_api_keys():
            logger.warning("Invalid API key used")
            return JsonResponse(
                {"error": "Invalid API key"}, 
                status=401
            )
            
        return view_func(request, *args, **kwargs)
        
    return wrapped_view


class CORSMiddleware:
    """
    Middleware to handle CORS (Cross-Origin Resource Sharing).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)
            
        # Add CORS headers
        allowed_origins = SecurityConfig.get_allowed_origins()
        origin = request.headers.get('Origin')
        
        if origin and (origin in allowed_origins or DEBUG):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key'
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
            
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
        return response


def init_security(api_keys: Optional[List[str]] = None, allowed_origins: Optional[List[str]] = None):
    """
    Initialize security configuration.
    
    Args:
        api_keys: List of valid API keys
        allowed_origins: List of allowed CORS origins
    """
    SecurityConfig.configure(api_keys, allowed_origins)
