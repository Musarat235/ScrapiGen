"""
API module
"""
from .dependencies import groq_client, get_groq_client
from .routes import api_router

__all__ = ['groq_client', 'get_groq_client', 'api_router']