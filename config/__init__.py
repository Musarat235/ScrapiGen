"""
Configuration module
"""
from .settings import (
    API_URL,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    GROQ_API_KEY,
    GROQ_MODEL,
    selector_cache,
    DEFAULT_HEADERS
)

# Import existing config
try:
    from .config import BATCH_CONFIG, PAGINATION_CONFIG
except ImportError:
    BATCH_CONFIG = {}
    PAGINATION_CONFIG = {}

__all__ = [
    'API_URL',
    'API_TITLE',
    'API_DESCRIPTION',
    'API_VERSION',
    'GROQ_API_KEY',
    'GROQ_MODEL',
    'selector_cache',
    'DEFAULT_HEADERS',
    'BATCH_CONFIG',
    'PAGINATION_CONFIG'
]