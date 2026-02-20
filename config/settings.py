"""
Configuration settings for ScrapiGen
All environment variables and constants in one place
"""
import os
from dotenv import load_dotenv, dotenv_values

# Determine project root and explicit .env path so env is loaded reliably
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

if os.path.exists(DOTENV_PATH):
    loaded = load_dotenv(DOTENV_PATH)
else:
    loaded = load_dotenv()  # fallback to default search

print(f"DEBUG: DOTENV_PATH={DOTENV_PATH} exists={os.path.exists(DOTENV_PATH)} loaded={bool(loaded)}")

# Normalize BOM-prefixed keys parsed by dotenv (e.g. '\ufeffGROQ_API_KEY')
try:
    parsed = dotenv_values(DOTENV_PATH) if os.path.exists(DOTENV_PATH) else {}
    for raw_k, raw_v in parsed.items():
        if raw_k and raw_k[0] == "\ufeff":
            clean_k = raw_k.lstrip("\ufeff")
            if raw_v is not None:
                os.environ.setdefault(clean_k, raw_v)
                print(f"DEBUG: normalized env key {repr(raw_k)} -> {repr(clean_k)}")
except Exception:
    pass

# ============================================================================
# API CONFIGURATION
# ============================================================================
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_TITLE = "ScrapiGen API v3 - Fully Integrated"
API_DESCRIPTION = "AI-Powered Web Scraping with Batch Processing, Pagination, and Smart Caching"
API_VERSION = "3.0.0"

# ============================================================================
# GROQ AI CONFIGURATION
# ============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# Validate that API key exists
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file")

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================
# Cache for CSS selectors (per domain)
# This stores generated selectors so we don't regenerate them for same domain
selector_cache = {}

# Cache TTL (Time To Live) in seconds
CACHE_HTML_TTL = 3600  # 1 hour for HTML cache
CACHE_EXTRACTION_TTL = 1800  # 30 minutes for extraction cache

# ============================================================================
# HTTP REQUEST CONFIGURATION
# ============================================================================
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# ============================================================================
# SCRAPING LIMITS
# ============================================================================
# Free tier limits
MAX_URLS_PER_REQUEST = 10
MAX_PAGES_PAGINATION = 10
MAX_CRAWL_DEPTH = 2
MAX_CRAWL_PAGES = 50

# Pro tier limits (for future use)
PRO_MAX_URLS = 100
PRO_MAX_PAGES = 100
PRO_MAX_CRAWL_PAGES = 500

# ============================================================================
# BATCH PROCESSING CONFIGURATION
# ============================================================================
MAX_CONCURRENT_STATIC = 5  # Static HTML requests
MAX_CONCURRENT_JS = 2      # JS-rendered requests (slower)

# ============================================================================
# PLAYWRIGHT CONFIGURATION
# ============================================================================
PLAYWRIGHT_TIMEOUT = 45000  # 45 seconds
PLAYWRIGHT_WAIT_TIME = 2.0  # Default wait time for JS rendering
PLAYWRIGHT_STEALTH_MODE = True  # Enable stealth mode by default

# ============================================================================
# CORS CONFIGURATION
# ============================================================================
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8501",  # Streamlit
    # Add your production domains here
]

# For development, you can allow all origins
ALLOW_ALL_ORIGINS = os.getenv("ALLOW_ALL_ORIGINS", "true").lower() == "true"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# DATABASE CONFIGURATION (Future: Redis/PostgreSQL)
# ============================================================================
# Currently using in-memory storage, but ready for upgrade
REDIS_URL = os.getenv("REDIS_URL", None)
DATABASE_URL = os.getenv("DATABASE_URL", None)

# ============================================================================
# FEATURE FLAGS
# ============================================================================
ENABLE_CACHING = True
ENABLE_JS_RENDERING = True
ENABLE_MULTI_LAYER_EXTRACTION = True
ENABLE_BATCH_PROCESSING = True
ENABLE_PAGINATION = True
ENABLE_CRAWLING = True

# ============================================================================
# RATE LIMITING (Future)
# ============================================================================
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600   # window in seconds (1 hour)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_max_urls(tier: str = "free") -> int:
    """Get max URLs based on subscription tier"""
    return PRO_MAX_URLS if tier == "pro" else MAX_URLS_PER_REQUEST


def get_max_pages(tier: str = "free") -> int:
    """Get max pages based on subscription tier"""
    return PRO_MAX_PAGES if tier == "pro" else MAX_PAGES_PAGINATION


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled"""
    features = {
        "caching": ENABLE_CACHING,
        "js_rendering": ENABLE_JS_RENDERING,
        "multi_layer": ENABLE_MULTI_LAYER_EXTRACTION,
        "batch": ENABLE_BATCH_PROCESSING,
        "pagination": ENABLE_PAGINATION,
        "crawling": ENABLE_CRAWLING,
    }
    return features.get(feature, False)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration on startup"""
    errors = []
    
    # Check required environment variables
    if not GROQ_API_KEY:
        errors.append("GROQ_API_KEY is not set")
    
    # Check that limits make sense
    if MAX_URLS_PER_REQUEST < 1:
        errors.append("MAX_URLS_PER_REQUEST must be at least 1")
    
    if MAX_CONCURRENT_STATIC < 1:
        errors.append("MAX_CONCURRENT_STATIC must be at least 1")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# Validate on import
try:
    validate_config()
    print("✅ Configuration validated successfully")
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    raise


# ============================================================================
# EXPORT SUMMARY
# ============================================================================

if __name__ == "__main__":
    """Print configuration summary"""
    print("\n" + "="*60)
    print("SCRAPIGEN CONFIGURATION SUMMARY")
    print("="*60)
    print(f"\n🌐 API Configuration:")
    print(f"  - URL: {API_URL}")
    print(f"  - Version: {API_VERSION}")
    print(f"\n🤖 Groq AI:")
    print(f"  - Model: {GROQ_MODEL}")
    print(f"  - API Key: {'✅ Set' if GROQ_API_KEY else '❌ Not Set'}")
    print(f"\n📊 Limits:")
    print(f"  - Max URLs/Request: {MAX_URLS_PER_REQUEST}")
    print(f"  - Max Pages (Pagination): {MAX_PAGES_PAGINATION}")
    print(f"  - Max Crawl Depth: {MAX_CRAWL_DEPTH}")
    print(f"\n⚡ Performance:")
    print(f"  - Concurrent Static: {MAX_CONCURRENT_STATIC}")
    print(f"  - Concurrent JS: {MAX_CONCURRENT_JS}")
    print(f"\n🎯 Features:")
    print(f"  - Caching: {'✅' if ENABLE_CACHING else '❌'}")
    print(f"  - JS Rendering: {'✅' if ENABLE_JS_RENDERING else '❌'}")
    print(f"  - Multi-Layer Extraction: {'✅' if ENABLE_MULTI_LAYER_EXTRACTION else '❌'}")
    print(f"  - Batch Processing: {'✅' if ENABLE_BATCH_PROCESSING else '❌'}")
    print(f"  - Pagination: {'✅' if ENABLE_PAGINATION else '❌'}")
    print(f"  - Crawling: {'✅' if ENABLE_CRAWLING else '❌'}")
    print("\n" + "="*60 + "\n")