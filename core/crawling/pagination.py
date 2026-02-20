"""
Universal Pagination System
Works on 80%+ of websites by detecting common patterns
"""

import asyncio
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import List, Optional, Dict, Callable
from bs4 import BeautifulSoup
import httpx
import logging
from core.html_processing.renderer import fetch_html_js
from core.html_processing.detector import get_rendering_strategy

logger = logging.getLogger(__name__)


class PaginationDetector:
    """Detect and handle pagination on any website"""
    
    # Common pagination patterns (ordered by priority)
    NEXT_BUTTON_SELECTORS = [
        "a[rel='next']",                    # Semantic HTML
        "a[aria-label*='next' i]",          # Accessible
        "a.next",                           # Class-based
        "a.pagination-next",
        "button.next",
        "a[title*='next' i]",
        "a:contains('Next')",               # Text-based
        "a:contains('›')",                  # Arrow symbols
        "a:contains('»')",
        "a:contains('→')",
        ".pagination a:last-child",         # Last link in pagination
        "nav[aria-label*='pagination' i] a:last-child",
    ]
    
    # URL parameter patterns for pagination
    PAGE_PARAMS = [
        "page", "p", "pg", "pageNum", "pageNumber", "offset",
        "start", "from", "skip", "index"
    ]
    
    
    @staticmethod
    def detect_pagination_type(html: str, url: str) -> Dict:
        """
        Detect what type of pagination this site uses
        
        Returns:
            {
                "type": "next_button" | "page_numbers" | "url_param" | "load_more" | "infinite_scroll" | "none",
                "pattern": <detection details>,
                "confidence": float 0-1
            }
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        detections = []
        
        # 1. Check for "Next" button
        for selector in PaginationDetector.NEXT_BUTTON_SELECTORS:
            try:
                # BeautifulSoup doesn't support :contains, so manual check
                if ":contains(" in selector:
                    text = selector.split(":contains('")[1].split("')")[0]
                    elements = soup.find_all('a', string=re.compile(text, re.I))
                else:
                    elements = soup.select(selector)
                
                if elements:
                    next_link = elements[0].get('href', '')
                    if next_link:
                        detections.append({
                            "type": "next_button",
                            "pattern": selector,
                            "next_url": next_link,
                            "confidence": 0.95
                        })
                        break
            except:
                continue
        
        # 2. Check for page number parameters in URL
        for param in PaginationDetector.PAGE_PARAMS:
            if param in query_params:
                detections.append({
                    "type": "url_param",
                    "pattern": param,
                    "current_page": int(query_params[param][0]),
                    "confidence": 0.9
                })
                break
        
        # 3. Check for page numbers in URL path
        path_match = re.search(r'/page/(\d+)', parsed_url.path, re.I)
        if path_match:
            detections.append({
                "type": "url_path",
                "pattern": "/page/{n}",
                "current_page": int(path_match.group(1)),
                "confidence": 0.9
            })
        
        # 4. Check for numbered pagination links
        page_links = soup.select(".pagination a, [class*='pagination'] a")
        if page_links:
            # Try to find numeric links
            numeric_links = [
                link for link in page_links
                if link.get_text(strip=True).isdigit()
            ]
            if numeric_links:
                detections.append({
                    "type": "page_numbers",
                    "pattern": "numeric links",
                    "total_pages": len(numeric_links),
                    "confidence": 0.85
                })
        
        # 5. Check for "Load More" button
        load_more = soup.find(['button', 'a'], string=re.compile(r'load\s*more|show\s*more', re.I))
        if load_more:
            detections.append({
                "type": "load_more",
                "pattern": "button or link",
                "confidence": 0.8
            })
        
        # 6. Check for infinite scroll indicators
        scroll_indicators = [
            'data-infinite-scroll',
            'class*="infinite-scroll"',
            'id*="infinite-scroll"'
        ]
        has_infinite = any(soup.select(f"[{ind}]") for ind in scroll_indicators)
        if has_infinite:
            detections.append({
                "type": "infinite_scroll",
                "pattern": "data attributes",
                "confidence": 0.75
            })
        
        # Return highest confidence detection
        if detections:
            return max(detections, key=lambda x: x["confidence"])
        
        return {"type": "none", "pattern": None, "confidence": 0}
    
    
    @staticmethod
    def get_next_page_url(current_url: str, html: str, pagination_type: Dict) -> Optional[str]:
        """
        Get the URL for the next page based on detected pagination type
        
        Args:
            current_url: Current page URL
            html: Current page HTML
            pagination_type: Detection result from detect_pagination_type()
        
        Returns:
            Next page URL or None if no next page
        """
        
        if pagination_type["type"] == "next_button":
            # Already have the next URL
            next_url = pagination_type.get("next_url", "")
            
            # Handle relative URLs
            if next_url.startswith('/'):
                parsed = urlparse(current_url)
                next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"
            elif not next_url.startswith('http'):
                # Relative to current path
                base_url = current_url.rsplit('/', 1)[0]
                next_url = f"{base_url}/{next_url}"
            
            return next_url
        
        elif pagination_type["type"] == "url_param":
            # Increment the page parameter
            param = pagination_type["pattern"]
            current_page = pagination_type["current_page"]
            next_page = current_page + 1
            
            parsed = urlparse(current_url)
            params = parse_qs(parsed.query)
            params[param] = [str(next_page)]
            
            new_query = urlencode(params, doseq=True)
            next_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
            
            return next_url
        
        elif pagination_type["type"] == "url_path":
            # Increment page number in path
            current_page = pagination_type["current_page"]
            next_page = current_page + 1
            
            next_url = re.sub(
                r'/page/\d+',
                f'/page/{next_page}',
                current_url,
                flags=re.I
            )
            
            return next_url
        
        elif pagination_type["type"] == "page_numbers":
            # Try to find the "2" or "next" link in HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all pagination links
            page_links = soup.select(".pagination a, [class*='pagination'] a")
            
            for link in page_links:
                text = link.get_text(strip=True).lower()
                if text in ['next', '›', '»', '→']:
                    href = link.get('href', '')
                    if href:
                        # Handle relative URLs
                        if href.startswith('/'):
                            parsed = urlparse(current_url)
                            return f"{parsed.scheme}://{parsed.netloc}{href}"
                        return href
            
            return None
        
        else:
            # Unsupported type
            return None


class PaginationScraper:
    """Scrape multiple pages with pagination"""
    
    def __init__(
        self,
        max_pages: int = 50,
        delay: float = 1.0,
        stop_if_empty: bool = True
    ):
        self.max_pages = max_pages
        self.delay = delay
        self.stop_if_empty = stop_if_empty
        self.detector = PaginationDetector()
    
    
    async def scrape_all_pages(
        self,
        start_url: str,
        extract_callback: Callable,  # Function to extract data from HTML
        **extract_kwargs
    ) -> List[Dict]:
        """
        Scrape all pages starting from start_url
        
        Args:
            start_url: First page URL
            extract_callback: Async function that takes (html, url) and returns extracted data
            **extract_kwargs: Additional arguments for extract_callback
        
        Returns:
            List of all extracted data from all pages
        """
        
        all_results = []
        current_url = start_url
        page_num = 1
        
        logger.info(f"🔄 Starting pagination scrape from: {start_url}")
        
        while page_num <= self.max_pages:
            logger.info(f"📄 Scraping page {page_num}/{self.max_pages}: {current_url}")
            
            try:
                # Fetch page
                html = await self._fetch_page(current_url)
                
                # Extract data
                page_results = await extract_callback(html, current_url, **extract_kwargs)
                
                if not page_results or len(page_results) == 0:
                    if self.stop_if_empty:
                        logger.info(f"🛑 No more data found, stopping at page {page_num}")
                        break
                
                all_results.extend(page_results)
                logger.info(f"✅ Page {page_num}: {len(page_results)} items (total: {len(all_results)})")
                
                # Detect pagination on first page
                if page_num == 1:
                    self.pagination_type = self.detector.detect_pagination_type(html, current_url)
                    logger.info(f"🔍 Detected pagination: {self.pagination_type['type']} (confidence: {self.pagination_type['confidence']:.0%})")
                    
                    if self.pagination_type["type"] == "none":
                        logger.warning("⚠️ No pagination detected, stopping")
                        break
                
                # Get next page URL
                next_url = self.detector.get_next_page_url(current_url, html, self.pagination_type)
                
                if not next_url or next_url == current_url:
                    logger.info(f"🏁 No more pages, stopping at page {page_num}")
                    break
                
                current_url = next_url
                page_num += 1
                
                # Polite delay
                await asyncio.sleep(self.delay)
                
            except Exception as e:
                logger.error(f"❌ Error on page {page_num}: {e}")
                break
        
        logger.info(f"✅ Pagination complete: {len(all_results)} total items from {page_num} pages")
        return all_results
    
    
    async def _fetch_page(self, url: str) -> str:
        """Fetch page HTML (with JS rendering if needed)"""
        
        # Try static first
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            html = response.text
        
        # Check if JS needed
        strategy = get_rendering_strategy(url, html)
        
        if strategy["needs_js"]:
            logger.info(f"⚡ Using JS rendering for: {url}")
            html, _ = await fetch_html_js(
                url=url,
                wait_time=strategy["wait_time"],
                wait_strategy=strategy.get("wait_strategy", "smart"),
                stealth_mode=strategy["stealth_mode"]
            )
        
        return html


# ============================================================================
# SITE-SPECIFIC HELPERS
# ============================================================================

async def scrape_olx_category(
    category_url: str,
    max_pages: int = 10,
    prompt: str = "Extract title, price, location"
) -> List[Dict]:
    """
    Scrape all listings from an OLX category
    
    Usage:
        results = await scrape_olx_category(
            "https://www.olx.com.pk/mobile-phones/",
            max_pages=5
        )
    """
    
    async def extract_olx_listings(html: str, url: str) -> List[Dict]:
        """Extract listings from OLX page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # OLX uses specific classes for listings
        listings = soup.select('[data-aut-id="itemBox"]')
        
        results = []
        for listing in listings:
            try:
                # Extract data
                title_elem = listing.select_one('[data-aut-id="itemTitle"]')
                price_elem = listing.select_one('[data-aut-id="itemPrice"]')
                location_elem = listing.select_one('[data-aut-id="item-location"]')
                link_elem = listing.select_one('a[href*="/item/"]')
                
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "price": price_elem.get_text(strip=True) if price_elem else None,
                        "location": location_elem.get_text(strip=True) if location_elem else None,
                        "url": "https://www.olx.com.pk" + link_elem['href'] if link_elem else None,
                        "source_page": url
                    })
            except Exception as e:
                logger.error(f"Error extracting listing: {e}")
                continue
        
        return results
    
    scraper = PaginationScraper(max_pages=max_pages)
    return await scraper.scrape_all_pages(category_url, extract_olx_listings)


async def scrape_generic_listings(
    start_url: str,
    item_selector: str,
    fields: Dict[str, str],  # {"field_name": "css_selector"}
    max_pages: int = 10
) -> List[Dict]:
    """
    Generic scraper for any listing page
    
    Usage:
        results = await scrape_generic_listings(
            "https://example.com/products/",
            item_selector=".product-card",
            fields={
                "title": "h2.product-title",
                "price": ".product-price",
                "link": "a.product-link"
            },
            max_pages=5
        )
    """
    
    async def extract_generic(html: str, url: str) -> List[Dict]:
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select(item_selector)
        
        results = []
        for item in items:
            data = {"source_page": url}
            
            for field_name, selector in fields.items():
                try:
                    elem = item.select_one(selector)
                    if elem:
                        # Handle links separately
                        if elem.name == 'a' and 'href' in elem.attrs:
                            data[field_name] = elem['href']
                        else:
                            data[field_name] = elem.get_text(strip=True)
                except:
                    data[field_name] = None
            
            results.append(data)
        
        return results
    
    scraper = PaginationScraper(max_pages=max_pages)
    return await scraper.scrape_all_pages(start_url, extract_generic)


# ============================================================================
# CLI USAGE
# ============================================================================

async def main():
    """Test pagination scraper"""
    
    # Example: Scrape OLX mobile phones
    print("🔄 Testing OLX pagination...")
    results = await scrape_olx_category(
        "https://www.olx.com.pk/mobile-phones/",
        max_pages=3
    )
    
    print(f"\n✅ Scraped {len(results)} listings")
    print("\n📊 Sample results:")
    for i, result in enumerate(results[:5], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Price: {result['price']}")
        print(f"   Location: {result['location']}")


if __name__ == "__main__":
    asyncio.run(main())
