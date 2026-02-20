import sys
import asyncio

# ✅ CRITICAL: Fix for Windows + Playwright + FastAPI
# Must be set BEFORE any async operations
if sys.platform == 'win32':
    # For Python 3.8+
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✅ Windows event loop policy set to ProactorEventLoop (required for Playwright)")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
from config import API_TITLE, API_DESCRIPTION, API_VERSION

# Import routes
from api.routes.scraping import router as scraping_router
from api.routes.batch import router as batch_router
from api.routes.pagination import router as pagination_router
from api.routes.crawling import router as crawling_router
from api.routes.admin import router as admin_router

# Import cleanup functions
from core.html_processing.renderer import cleanup_browser
from storage.cache_manager import get_cache_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting ScrapiGen API v3 - Fully Integrated")
    print("✅ Caching: Enabled")
    print("✅ Batch Processing: Enabled")
    print("✅ Pagination: Enabled")
    print("✅ Crawling: Enabled")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down ScrapiGen...")
    await cleanup_browser()
    
    cache = get_cache_manager()
    await cache.close()
    
    print("✅ Cleanup complete")


# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(scraping_router, tags=["Scraping"])
app.include_router(batch_router, prefix="/batch", tags=["Batch Processing"])
app.include_router(pagination_router, prefix="/pagination", tags=["Pagination"])
app.include_router(crawling_router, prefix="/crawl", tags=["Crawling"])
app.include_router(admin_router, tags=["Admin"])


# Root endpoint
@app.get("/")
async def root():
    """Health check and API info"""
    return {
        "status": "running",
        "version": API_VERSION,
        "message": "ScrapiGen API is running! Visit /docs for API documentation.",
        "features": {
            "single_scraping": True,
            "batch_processing": True,
            "pagination": True,
            "crawling": True,
            "caching": True,
            "js_rendering": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)