"""
In-memory analytics storage
"""
from typing import Dict


# Analytics storage
analytics_db: Dict = {
    "total_requests": 0,
    "success_count": 0,
    "fail_count": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "domains_tried": {},
    "strategies_used": {
        "meta_direct": 0,
        "css_selectors": 0,
        "full_llm": 0,
        "playwright_renders": 0
    },
    "common_prompts": {}
}


def track_request(domain: str, strategy: str, success: bool):
    """Track a scraping request"""
    analytics_db["total_requests"] += 1
    
    if success:
        analytics_db["success_count"] += 1
    else:
        analytics_db["fail_count"] += 1
    
    # Track domain stats
    if domain not in analytics_db["domains_tried"]:
        analytics_db["domains_tried"][domain] = {
            "success": 0,
            "fail": 0,
            "strategies": {}
        }
    
    if success:
        analytics_db["domains_tried"][domain]["success"] += 1
    else:
        analytics_db["domains_tried"][domain]["fail"] += 1
    
    # Track strategy
    analytics_db["strategies_used"][strategy] = \
        analytics_db["strategies_used"].get(strategy, 0) + 1
    analytics_db["domains_tried"][domain]["strategies"][strategy] = \
        analytics_db["domains_tried"][domain]["strategies"].get(strategy, 0) + 1


def track_prompt(prompt: str):
    """Track common prompts"""
    prompt_key = prompt.lower()[:50]
    analytics_db["common_prompts"][prompt_key] = \
        analytics_db["common_prompts"].get(prompt_key, 0) + 1


def track_cache_hit():
    """Track cache hit"""
    analytics_db["cache_hits"] += 1


def track_cache_miss():
    """Track cache miss"""
    analytics_db["cache_misses"] += 1


def get_analytics() -> dict:
    """Get all analytics"""
    return analytics_db


def get_success_rate() -> float:
    """Calculate success rate"""
    total = analytics_db["total_requests"]
    if total == 0:
        return 0.0
    return (analytics_db["success_count"] / total) * 100