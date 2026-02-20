"""
ScrapiGen Configuration
Centralized settings for easy management
"""

import os
from typing import Dict, List

# ============================================================================
# GENERAL SETTINGS
# ============================================================================

APP_NAME = "ScrapiGen"
APP_VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Wait strategies per site type
WAIT_STRATEGIES = {
    "fast": {
        "wait_time": 1.0,
        "strategy": "fast",
        "use_for": ["product pages", "article pages", "static content"]
    },
    "smart": {
        "wait_time": 1.5,
        "strategy": "smart",
        "use_for": ["most sites", "default"]
    },
    "thorough": {
        "wait_time": 3.0,
        "strategy": "thorough",
        "use_for": ["heavy SPAs", "infinite scroll", "lazy loading"]
    }
}

# ============================================================================
# API SETTINGS
# ============================================================================

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Rate Limiting (Free Tier)
MAX_URLS_PER_REQUEST = 10
MAX_REQUESTS_PER_DAY = 100  # Per user (implement later with auth)

# ============================================================================
# SCRAPING SETTINGS
# ============================================================================

# Timeouts
STATIC_FETCH_TIMEOUT = 30.0  # seconds
JS_RENDER_TIMEOUT = 45000    # milliseconds
DEFAULT_WAIT_TIME = 2.0      # seconds for lazy-loaded content

# Cache
ENABLE_CACHE = True
CACHE_TTL = 3600  # 1 hour (increase to 24h in production)

# ============================================================================
# PLAYWRIGHT SETTINGS
# ============================================================================

# Performance optimization
BLOCK_RESOURCES = True  # Block images, fonts, etc.
BLOCKED_RESOURCE_TYPES = [
    "image", 
    "media", 
    "font", 
    "stylesheet",  # Can enable if CSS is needed for some sites
    "beacon", 
    "csp_report",
]

# Stealth mode (anti-detection)
STEALTH_MODE_DEFAULT = True
STEALTH_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Browser pool (for high-volume scraping)
BROWSER_POOL_SIZE = 1  # Increase to 3-5 in production
REUSE_BROWSER = True   # Keep browser alive between requests

# ============================================================================
# DETECTION RULES
# ============================================================================

# Minimum HTML length to consider valid
MIN_HTML_LENGTH = 1000

# When to use JS rendering (per domain)
JS_HEAVY_SITES: Dict[str, dict] = {
    # Pakistani Sites
    "olx.com.pk": {
        "threshold": 5000,
        "wait_time": 3.0,
        "stealth": True,
        "reason": "OLX lazy loads listings"
    },
    "zameen.com": {
        "threshold": 4000,
        "wait_time": 2.5,
        "stealth": False,
        "reason": "Property listings JS-rendered"
    },
    "daraz.pk": {
        "threshold": 6000,
        "wait_time": 2.0,
        "stealth": True,
        "reason": "React-based product pages"
    },
    "graana.com": {
        "threshold": 4000,
        "wait_time": 2.0,
        "stealth": False,
        "reason": "Real estate JS-heavy"
    },
    "pakwheels.com": {
        "threshold": 5000,
        "wait_time": 2.0,
        "stealth": False,
        "reason": "Car listings lazy-loaded"
    },
    
    # Global Sites
    "amazon.com": {
        "threshold": 8000,
        "wait_time": 2.0,
        "stealth": True,
        "reason": "Dynamic product loading"
    },
    "ebay.com": {
        "threshold": 7000,
        "wait_time": 2.0,
        "stealth": True,
        "reason": "JS-rendered listings"
    },
}

# ============================================================================
# LLM EXTRACTION SETTINGS
# ============================================================================

# Token limits
SELECTOR_GENERATION_TOKENS = 800
FULL_EXTRACTION_TOKENS = 2000

# HTML cleaning
REMOVE_TAGS = ["script", "style", "noscript", "iframe", "svg", "path"]
MAX_HTML_FOR_LLM = 50000  # chars (to stay within token limits)

# ============================================================================
# EXPORT SETTINGS
# ============================================================================

SUPPORTED_FORMATS = ["json", "csv", "excel"]
MAX_RESULTS_PER_EXPORT = 10000  # rows

# ============================================================================
# TEMPLATES (for future)
# ============================================================================

SITE_TEMPLATES: Dict[str, dict] = {
    "olx_pakistan": {
        "domain": "olx.com.pk",
        "selectors": {
            "title": "h1[data-aut-id='itemTitle']",
            "price": "span[data-aut-id='itemPrice']",
            "location": "span[data-aut-id='item-location']",
            "description": "div[data-aut-id='itemDescriptionContent']",
        },
        "description": "Extract listings from OLX Pakistan"
    },
    "zameen_properties": {
        "domain": "zameen.com",
        "selectors": {
            "title": "h1.c1d13dc1",
            "price": "span.f343d9ce",
            "location": "div._3cb2c1a3",
            "description": "div._162863c9",
        },
        "description": "Extract property listings from Zameen.com"
    },
    # Add more templates as you discover patterns
}

# ============================================================================
# ANALYTICS & MONITORING
# ============================================================================

TRACK_ANALYTICS = True
ANALYTICS_RETENTION_DAYS = 30

# Log levels
LOG_LEVEL = "INFO" if not DEBUG else "DEBUG"

# ============================================================================
# DEPLOYMENT SETTINGS (for later)
# ============================================================================

# Database (when you add it)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///scrapigen.db")

# Redis (for production caching)
REDIS_URL = os.getenv("REDIS_URL", None)

# Celery (for background jobs at scale)
CELERY_BROKER = os.getenv("CELERY_BROKER", None)

# AWS S3 (for large result storage)
AWS_BUCKET = os.getenv("AWS_BUCKET", None)

# ============================================================================
# FREEMIUM LIMITS
# ============================================================================

FREE_TIER = {
    "max_urls_per_request": 10,
    "max_requests_per_day": 50,
    "max_requests_per_month": 1000,
    "js_rendering": True,      # Allow in free tier for now
    "api_access": True,         # Basic API access
    "export_formats": ["json", "csv"],
}

PRO_TIER = {
    "max_urls_per_request": 100,
    "max_requests_per_day": 1000,
    "max_requests_per_month": 50000,
    "js_rendering": True,
    "stealth_mode": True,
    "priority_queue": True,
    "api_access": True,
    "export_formats": ["json", "csv", "excel"],
    "webhooks": True,
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_domain_config(domain: str) -> dict:
    """Get configuration for a specific domain"""
    for known_domain, config in JS_HEAVY_SITES.items():
        if known_domain in domain:
            return config
    return {}


def get_template(domain: str) -> dict:
    """Get pre-built template for a domain"""
    for template_name, template_config in SITE_TEMPLATES.items():
        if template_config["domain"] in domain:
            return template_config
    return {}


# ============================================================================
# BATCH PROCESSING
# ============================================================================

BATCH_CONFIG = {
    "max_concurrent_renders": 3,      # Process 3 pages at once
    "max_concurrent_static": 10,      # Process 10 static fetches at once
    "batch_size": 100,                # Process in chunks of 100
    "retry_failed": True,             # Retry failed URLs
    "max_retries": 2,                 # Max retry attempts
    "save_interval": 50,              # Save progress every 50 URLs
}

# ============================================================================
# CACHING
# ============================================================================

CACHE_CONFIG = {
    "enabled": True,
    "ttl": 3600,                      # 1 hour (in-memory)
    "redis_ttl": 86400,               # 24 hours (Redis)
    "cache_static": True,             # Cache static HTML too
    "cache_rendered": True,           # Cache Playwright renders
}

# ============================================================================
# PAGINATION SETTINGS
# ============================================================================

PAGINATION_CONFIG = {
    "max_pages": 50,                  # Safety limit
    "delay_between_pages": 1.0,       # Seconds between page requests
    "auto_detect": True,              # Try to detect pagination automatically
    
    # Common pagination patterns
    "patterns": {
        "next_button": [
            "a[rel='next']",
            "a.next",
            "a.pagination-next",
            "button.next",
            "[aria-label*='next' i]",
            "[title*='next' i]",
        ],
        "page_numbers": [
            "a.page-link",
            "li.page-item a",
            ".pagination a",
            "[class*='pagination'] a",
        ],
        "infinite_scroll": {
            "enabled": False,         # Complex, add in V2
            "scroll_pause": 2.0,
            "max_scrolls": 10,
        }
    }
}

# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

PERFORMANCE_TARGETS = {
    "static_fetch": 2.0,              # Target: <2s
    "js_render_fast": 8.0,            # Target: <8s
    "js_render_smart": 12.0,          # Target: <12s
    "js_render_thorough": 20.0,       # Target: <20s
}