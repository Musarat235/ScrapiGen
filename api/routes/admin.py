from fastapi import APIRouter
from storage.cache_manager import get_cache_manager
from storage.jobs_db import jobs_db
from storage.analytics_db import analytics_db
from config.settings import selector_cache
from typing import Optional
from core.html_processing.renderer import get_cache_stats

router = APIRouter()

@router.get("/cache/stats")
async def cache_stats():
    """Get cache performance statistics"""
    cache = get_cache_manager()
    cache_stats = await cache.get_stats()
    
    return {
        "cache_manager": cache_stats,
        "render_cache": await get_cache_stats(),
        "analytics": {
            "cache_hits": analytics_db["cache_hits"],
            "cache_misses": analytics_db["cache_misses"],
            "hit_rate": round(analytics_db["cache_hits"] / (analytics_db["cache_hits"] + analytics_db["cache_misses"]) * 100, 1) if (analytics_db["cache_hits"] + analytics_db["cache_misses"]) > 0 else 0
        }
    }


@router.post("/cache/clear")
async def clear_cache(namespace: Optional[str] = None):
    """Clear cache (useful for testing)"""
    cache = get_cache_manager()
    
    if namespace:
        await cache.clear_namespace(namespace)
        return {"status": "cleared", "namespace": namespace}
    else:
        # Clear all caches
        await cache.clear_namespace("rendered_html")
        await cache.clear_namespace("extracted_data")
        return {"status": "cleared", "namespace": "all"}

@router.get("/")
async def health():
    return {
        "status": "running",
        "version": "3.0.0",
        "features": {
            "single_scraping": True,
            "batch_processing": True,
            "pagination": True,
            "caching": True,
            "js_rendering": True
        }
    }

@router.get("/stats")
async def stats():
    """Get analytics and stats"""
    
    # Calculate success rate
    total = analytics_db["total_requests"]
    success_rate = (analytics_db["success_count"] / total * 100) if total > 0 else 0
    
    # Top domains
    top_domains = sorted(
        analytics_db["domains_tried"].items(),
        key=lambda x: x[1]["success"] + x[1]["fail"],
        reverse=True
    )[:10]
    
    # Format domain stats
    domain_stats = [
        {
            "domain": domain,
            "total": stats["success"] + stats["fail"],
            "success": stats["success"],
            "fail": stats["fail"],
            "success_rate": round(stats["success"] / (stats["success"] + stats["fail"]) * 100, 1) if (stats["success"] + stats["fail"]) > 0 else 0,
            "top_strategy": max(stats["strategies"].items(), key=lambda x: x[1])[0] if stats["strategies"] else "none"
        }
        for domain, stats in top_domains
    ]
    
    return {
        "total_jobs": len(jobs_db),
        "total_urls_scraped": total,
        "success_count": analytics_db["success_count"],
        "fail_count": analytics_db["fail_count"],
        "success_rate": round(success_rate, 1),
        "strategies_used": analytics_db["strategies_used"],
        "top_domains": domain_stats,
        "top_prompts": sorted(analytics_db["common_prompts"].items(), key=lambda x: x[1], reverse=True)[:5],
        "cached_selectors": len(selector_cache),
        "cache_performance": {
            "hits": analytics_db["cache_hits"],
            "misses": analytics_db["cache_misses"],
            "hit_rate": round(analytics_db["cache_hits"] / (analytics_db["cache_hits"] + analytics_db["cache_misses"]) * 100, 1) if (analytics_db["cache_hits"] + analytics_db["cache_misses"]) > 0 else 0
        }
    }

# Add this endpoint to monitor rendering performance
@router.get("/rendering/stats")
async def rendering_stats():
    """Get rendering statistics and cache performance"""
    
    cache_stats = await get_cache_stats()
    
    return {
        "cache": cache_stats,
        "strategies": analytics_db["strategies_used"],
        "domains": {
            domain: {
                "total": stats["success"] + stats["fail"],
                "success_rate": round(stats["success"] / (stats["success"] + stats["fail"]) * 100, 1) if (stats["success"] + stats["fail"]) > 0 else 0
            }
            for domain, stats in list(analytics_db["domains_tried"].items())[:20]
        }
    }