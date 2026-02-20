from fastapi import APIRouter, BackgroundTasks, HTTPException
from models import ScrapeRequest, ScrapeResponse, JobStatus
from storage.jobs_db import get_job, create_job, job_exists
from core.job_processor import process_scraping_job
from datetime import datetime
from core.extraction.smart_extractor import smart_extract
from core.html_processing.fetcher import fetch_html
from storage.jobs_db import jobs_db

router = APIRouter()

@router.post("/scrape", response_model=ScrapeResponse)
async def create_scrape_job(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Original endpoint - for 1-10 URLs
    Uses: caching, JS rendering, smart extraction
    """
    
    if len(request.urls) > request.max_urls:
        raise HTTPException(status_code=400, detail=f"Max {request.max_urls} URLs")
    
    job_id = f"job_{datetime.now().timestamp()}"
    
    jobs_db[job_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "urls": [str(url) for url in request.urls],
        "prompt": request.prompt
    }
    
    async def process():
        jobs_db[job_id]["status"] = "processing"
        results = []
        
        for url in request.urls:
            url_str = str(url)
            try:
                html = await fetch_html(url_str)
                extracted = await smart_extract(html, request.prompt, cache_key=url_str)
                
                results.append({
                    "url": url,
                    "data": extracted.get("data", []),
                    "strategy": extracted.get("strategy"),
                    "success": True
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "error": str(e),
                    "success": False
                })
        
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["results"] = results
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
    
    background_tasks.add_task(process)
    
    return ScrapeResponse(
        job_id=job_id,
        status="pending",
        message=f"Processing {len(request.urls)} URLs..."
    )

@router.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Check status of any job (single, batch, or pagination)"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        results=job.get("results"),
        error=job.get("error")
    )