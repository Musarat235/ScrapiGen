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
    
    total_urls = len(request.urls)
    
    jobs_db[job_id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "urls": [str(url) for url in request.urls],
        "prompt": request.prompt,
        "progress": 0,
        "stage": "🚀 Initializing job…",
        "current_url": None,
        "urls_completed": 0,
        "urls_total": total_urls,
    }
    
    async def process():
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["stage"] = "⏳ Preparing to scrape…"
        results = []
        
        for i, url in enumerate(request.urls, start=1):
            url_str = str(url)
            try:
                # --- Stage: Fetching ---
                jobs_db[job_id]["stage"] = f"🌐 Fetching page {i} of {total_urls}…"
                jobs_db[job_id]["current_url"] = url_str
                jobs_db[job_id]["progress"] = int(((i - 1) / total_urls) * 100)

                html = await fetch_html(url_str)
                
                # --- Stage: Extracting ---
                jobs_db[job_id]["stage"] = f"🤖 Extracting data from page {i} of {total_urls}…"
                jobs_db[job_id]["progress"] = int(((i - 0.5) / total_urls) * 100)

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
            
            # Update per-URL completion
            jobs_db[job_id]["urls_completed"] = i
        
        # --- Stage: Finalizing ---
        jobs_db[job_id]["stage"] = "📊 Analyzing results…"
        jobs_db[job_id]["progress"] = 95

        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["results"] = results
        jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["stage"] = "✅ Done!"
    
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
        error=job.get("error"),
        progress=job.get("progress"),
        stage=job.get("stage"),
        current_url=job.get("current_url"),
        urls_completed=job.get("urls_completed"),
        urls_total=job.get("urls_total"),
    )