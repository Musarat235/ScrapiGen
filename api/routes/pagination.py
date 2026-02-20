from fastapi import APIRouter, BackgroundTasks
from models.requests import PaginationScrapeRequest
from datetime import datetime
from core.crawling.pagination import PaginationScraper, scrape_olx_category, scrape_generic_listings
from core.extraction.smart_extractor import smart_extract
from storage.jobs_db import jobs_db

router = APIRouter()
@router.post("/pagination/scrape")
async def pagination_scrape(request: PaginationScrapeRequest, background_tasks: BackgroundTasks):
    """
    NEW: Automatically scrape all pages from a category/listing
    
    Uses: pagination.py
    Features: Auto-detects pagination, works on 80%+ sites
    """
    
    job_id = f"pagination_{datetime.now().timestamp()}"
    
    jobs_db[job_id] = {
        "type": "pagination",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "start_url": str(request.start_url),
        "max_pages": request.max_pages,
        "prompt": request.prompt
    }
    
    async def process_pagination():
        jobs_db[job_id]["status"] = "processing"
        
        try:
            start_url = str(request.start_url)
            
            # Check if it's OLX (use optimized scraper)
            if "olx.com.pk" in start_url:
                results = await scrape_olx_category(
                    category_url=start_url,
                    max_pages=request.max_pages,
                    prompt=request.prompt
                )
            
            # Check if generic selectors provided
            elif request.item_selector and request.fields:
                results = await scrape_generic_listings(
                    start_url=start_url,
                    item_selector=request.item_selector,
                    fields=request.fields,
                    max_pages=request.max_pages
                )
            
            # Use generic pagination scraper
            else:
                scraper = PaginationScraper(
                    max_pages=request.max_pages,
                    delay=1.0
                )
                
                # Define extraction callback
                async def extract_callback(html, url):
                    extracted = await smart_extract(html, request.prompt, cache_key=url)
                    return extracted.get("data", [])
                
                results = await scraper.scrape_all_pages(
                    start_url=start_url,
                    extract_callback=extract_callback
                )
            
            jobs_db[job_id]["status"] = "completed"
            jobs_db[job_id]["results"] = results
            jobs_db[job_id]["total_items"] = len(results)
            jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = str(e)
    
    background_tasks.add_task(process_pagination)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Scraping up to {request.max_pages} pages from {request.start_url}...",
        "check_status": f"/job/{job_id}"
    }