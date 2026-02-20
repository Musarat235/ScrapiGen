"""
API Routes module
Import all route blueprints
"""
from fastapi import APIRouter
from . import scraping, batch, pagination, crawling, admin

# Create main router
api_router = APIRouter()