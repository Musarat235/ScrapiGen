"""
In-memory job storage
"""
from typing import Dict, Optional
from datetime import datetime


# In-memory storage
jobs_db: Dict[str, dict] = {}


def get_job(job_id: str) -> Optional[dict]:
    """Get job by ID"""
    return jobs_db.get(job_id)


def create_job(job_id: str, data: dict) -> dict:
    """Create new job"""
    jobs_db[job_id] = {
        **data,
        "created_at": datetime.now().isoformat()
    }
    return jobs_db[job_id]


def update_job(job_id: str, updates: dict) -> Optional[dict]:
    """Update existing job"""
    if job_id in jobs_db:
        jobs_db[job_id].update(updates)
        return jobs_db[job_id]
    return None


def job_exists(job_id: str) -> bool:
    """Check if job exists"""
    return job_id in jobs_db


def get_all_jobs() -> Dict[str, dict]:
    """Get all jobs"""
    return jobs_db
