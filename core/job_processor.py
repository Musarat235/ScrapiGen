"""
Background job processing
Handles scraping jobs asynchronously
"""
from typing import List
from datetime import datetime
from core.html_processing.fetcher import fetch_html, get_domain
from core.extraction.smart_extractor import smart_extract
from storage.jobs_db import update_job
from storage.analytics_db import track_request, track_prompt


async def process_scraping_job(job_id: str, urls: List[str], prompt: str):
    """Process scraping job with per-domain selector caching"""
    
    update_job(job_id, {"status": "processing"})
    results = []
    
    # Track prompt
    track_prompt(prompt)
    
    # Group URLs by domain
    domain_map = {}
    for url in urls:
        domain = get_domain(url)
        if domain not in domain_map:
            domain_map[domain] = []
        domain_map[domain].append(url)
    
    # Process each domain group
    for domain, domain_urls in domain_map.items():
        # Cache key per domain + prompt
        cache_key = f"{domain}:{hash(prompt)}"
        
        for idx, url in enumerate(domain_urls):
            try:
                # Fetch HTML
                html = await fetch_html(url)
                
                # Extract data
                extracted = await smart_extract(
                    html=html,
                    prompt=prompt,
                    cache_key=cache_key,
                    url=url
                )
                
                # Track strategy and success
                strategy = extracted.get("strategy", "unknown")
                has_data = bool(extracted.get("data") and any(extracted["data"]))
                
                track_request(domain, strategy, has_data)
                
                results.append({
                    "url": url,
                    "data": extracted.get("data", []),
                    "strategy": strategy,
                    "domain": domain,
                    "selectors": extracted.get("selectors_used") if idx == 0 else None,
                    "success": has_data
                })
                
            except Exception as e:
                track_request(domain, "failed", False)
                
                results.append({
                    "url": url,
                    "error": str(e),
                    "domain": domain,
                    "success": False
                })
    
    # Update job with results
    update_job(job_id, {
        "status": "completed",
        "results": results,
        "completed_at": datetime.now().isoformat()
    })