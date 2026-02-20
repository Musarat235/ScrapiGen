from .requests import (
    ScrapeRequest,
    BatchScrapeRequest,
    PaginationScrapeRequest,
    CrawlRequest
)
from .responses import (
    ScrapeResponse,
    JobStatus
)

__all__ = [
    'ScrapeRequest',
    'BatchScrapeRequest',
    'PaginationScrapeRequest',
    'CrawlRequest',
    'ScrapeResponse',
    'JobStatus'
]