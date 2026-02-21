"""
Response models for ScrapiGen API
"""
from pydantic import BaseModel
from typing import Optional, List


class ScrapeResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str
    results: Optional[List[dict]] = None
    error: Optional[str] = None
    progress: Optional[int] = None
    stage: Optional[str] = None
    current_url: Optional[str] = None
    urls_completed: Optional[int] = None
    urls_total: Optional[int] = None