"""
Enrichment API routes
POST /enrichment/analyze — stats only (read-only scan)
POST /enrichment/clean  — apply normalize + deduplicate
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional
from core.enrichment import analyze, enrich

router = APIRouter()


class EnrichRequest(BaseModel):
    data: List[Dict]
    stages: Optional[List[str]] = ["normalize", "deduplicate"]


class AnalyzeResponse(BaseModel):
    total_records: int
    duplicates_found: int
    phones_to_fix: int
    emails_to_fix: int
    urls_to_fix: int
    total_issues: int


class EnrichResponse(BaseModel):
    data: List[Dict]
    stages_applied: List[str]
    original_count: int
    enriched_count: int
    duplicates_removed: int


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(request: EnrichRequest):
    """
    Scan raw scraped data and return quality stats.
    Does NOT modify the data — just counts issues.
    
    Used by the frontend to show the stats block before the user clicks "Clean Data".
    """
    stats = analyze(request.data)
    return AnalyzeResponse(**stats)


@router.post("/clean", response_model=EnrichResponse)
async def clean_data(request: EnrichRequest):
    """
    Apply enrichment stages (normalize + deduplicate) to the data.
    
    Called when the user clicks "Clean Data" in the frontend.
    """
    result = enrich(request.data, stages=request.stages)
    return EnrichResponse(**result)
