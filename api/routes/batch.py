from fastapi import BackgroundTasks, APIRouter
from models.requests import BatchScrapeRequest
from datetime import datetime
from core.processing.batch import BatchProcessor
from storage.jobs_db import jobs_db
from config.config import BATCH_CONFIG

router = APIRouter()

@router.post("/batch/scrape")
async def batch_scrape(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """
    NEW: Batch scraping for large jobs (100-10,000 URLs)
    
    Uses: batch_processor.py
    Features: Progress tracking, resume capability, CSV export
    """
    
    job_id = f"batch_{datetime.now().timestamp()}"
    
    jobs_db[job_id] = {
        "type": "batch",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "total_urls": len(request.urls),
        "prompt": request.prompt
    }
    
    async def process_batch():
        jobs_db[job_id]["status"] = "processing"
        
        try:
            # Use BatchProcessor
            processor = BatchProcessor(
                job_id=job_id,
                max_concurrent=request.max_concurrent or BATCH_CONFIG["max_concurrent_static"]
            )
            
            stats = await processor.process_batch(
                urls=[str(url) for url in request.urls],
                prompt=request.prompt,
                resume=False
            )
            
            # Export to CSV automatically
            processor.export_to_csv()
            
            jobs_db[job_id]["status"] = "completed"
            jobs_db[job_id]["stats"] = stats
            jobs_db[job_id]["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            jobs_db[job_id]["status"] = "failed"
            jobs_db[job_id]["error"] = str(e)
    
    background_tasks.add_task(process_batch)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Processing {len(request.urls)} URLs in batch mode...",
        "check_status": f"/job/{job_id}"
    }
