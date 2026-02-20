"""
HTML Processing module
"""
from .cleaner import clean_html_for_extraction, extract_article_structure
from .fetcher import fetch_html, get_domain

__all__ = [
    'clean_html_for_extraction',
    'extract_article_structure',
    'fetch_html',
    'get_domain'
]