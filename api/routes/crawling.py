from fastapi import APIRouter, BackgroundTasks
from models.requests import CrawlRequest
from datetime import datetime
from core.crawling.crawler import crawl_directory_site, scrape_machineryzone_dealers
from storage.jobs_db import jobs_db

router = APIRouter()
@router.post("/crawl")
async def crawl_website(request: CrawlRequest, background_tasks: BackgroundTasks):
    """
    NEW: Intelligent multi-level crawling
    
    Perfect for:
    - Directory sites (MachineryZone, YellowPages)
    - Nested listings (Category → Products)
    - Any multi-level structure
    
    Example:
    {
      "start_url": "https://www.machineryzone.com/pros/list/1.html",
      "prompt": "Extract company name, website, phone, email",
      "max_depth": 2,
      "max_pages": 50
    }
    """
    
    job_id = f"crawl_{datetime.now().timestamp()}"
    
    jobs_db[job_id] = {
        "type": "crawl",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "start_url": str(request.start_url),
        "max_depth": request.max_depth,
        "max_pages": request.max_pages,
        "prompt": request.prompt
    }
    
    async def process_crawl():
        jobs_db[job_id]["status"] = "processing"
        
        try:
            result = await crawl_directory_site(
                start_url=str(request.start_url),
                extract_prompt=request.prompt,
                max_depth=request.max_depth,
                max_pages=request.max_pages
            )
            
            jobs_db[job_id]["status"] = "completed"
            jobs_db[job_id]["results"] = result["data"]
            jobs_db[job_id]["stats"] = result["stats"]
            jobs_db[job_id]["total_items"] = len(result["data"])
            jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = str(e)
    
    background_tasks.add_task(process_crawl)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Crawling up to {request.max_pages} pages from {request.start_url}...",
        "check_status": f"/job/{job_id}"
    }


# Add convenience endpoint for MachineryZone
@router.post("/crawl/machineryzone")
async def crawl_machineryzone(max_pages: int = 50, background_tasks: BackgroundTasks = None):
    """
    Quick endpoint for MachineryZone dealers
    
    Usage: POST /crawl/machineryzone?max_pages=100
    """
    
    job_id = f"mz_{datetime.now().timestamp()}"
    
    jobs_db[job_id] = {
        "type": "crawl",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "site": "MachineryZone"
    }
    
    async def process():
        jobs_db[job_id]["status"] = "processing"
        
        try:
            result = await scrape_machineryzone_dealers(max_pages=max_pages)
            
            jobs_db[job_id]["status"] = "completed"
            jobs_db[job_id]["results"] = result["data"]
            jobs_db[job_id]["stats"] = result["stats"]
            jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = str(e)
    
    background_tasks.add_task(process)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Scraping MachineryZone dealers...",
        "check_status": f"/job/{job_id}"
    }