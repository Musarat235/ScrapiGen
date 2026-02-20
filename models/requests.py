"""
Request models for ScrapiGen API
"""
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict


class ScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    prompt: str
    max_urls: int = 10


class BatchScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    prompt: str
    max_concurrent: Optional[int] = 5


class PaginationScrapeRequest(BaseModel):
    start_url: HttpUrl
    prompt: str
    max_pages: int = 10
    item_selector: Optional[str] = None
    fields: Optional[Dict[str, str]] = None


class CrawlRequest(BaseModel):
    start_url: HttpUrl
    prompt: str
    max_depth: int = 2
    max_pages: int = 50
    link_selector: Optional[str] = None
    auto_detect: bool = True