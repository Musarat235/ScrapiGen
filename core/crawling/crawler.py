"""
ScrapiGen Intelligent Crawler
Handles multi-level scraping: List pages → Detail pages → Data extraction

Perfect for:
- Scraping dealer directories (MachineryZone, YellowPages)
- Product listings → Product details
- Category pages → Item pages
- Any nested structure
"""

import asyncio
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Set, Callable
from bs4 import BeautifulSoup
import httpx
import logging
from datetime import datetime


from core.html_processing.renderer import fetch_html_js
from core.html_processing.detector import get_rendering_strategy
from core.html_processing.adaptive_learning_sytem import AdaptiveLearner
from core.html_processing.advance_stealth_mode import MultiSignalDetector, ProtectionType

logger = logging.getLogger(__name__)


class SmartCrawler:
    """
    Intelligent multi-level web crawler
    
    Features:
    - Auto-detects link patterns
    - Respects crawl depth
    - Deduplicates URLs
    - Parallel processing
    - Progress tracking
    - Adaptive Learning & Stealth
    """
    
    def __init__(
        self,
        max_depth: int = 2,
        max_pages: int = 100,
        delay: float = 1.0,
        same_domain_only: bool = True,
        max_concurrent: int = 5
    ):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.same_domain_only = same_domain_only
        self.max_concurrent = max_concurrent
        
        # Tracking
        self.visited_urls: Set[str] = set()
        self.queued_urls: Set[str] = set()
        self.results: List[Dict] = []
        self.start_domain = None
        
        # AI Systems
        self.learner = AdaptiveLearner()
        self.detector = MultiSignalDetector()
        
        # Statistics
        self.stats = {
            "pages_crawled": 0,
            "urls_found": 0,
            "data_extracted": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Convert relative URLs to absolute and normalize"""
        # Handle relative URLs
        if not url.startswith('http'):
            url = urljoin(base_url, url)
        
        # Remove fragments
        url = url.split('#')[0]
        
        # Remove trailing slash for consistency
        url = url.rstrip('/')
        
        return url
    
    
    def should_crawl_url(self, url: str) -> bool:
        """Decide if URL should be crawled"""
        
        # Already visited or queued
        if url in self.visited_urls or url in self.queued_urls:
            return False
        
        # Check domain restriction
        if self.same_domain_only and self.start_domain:
            parsed = urlparse(url)
            if parsed.netloc != self.start_domain:
                return False
        
        # Skip common non-content URLs
        skip_patterns = [
            r'/login', r'/signup', r'/cart', r'/checkout',
            r'/account', r'/profile', r'/settings',
            r'\.(pdf|jpg|jpeg|png|gif|zip|xml|json|css|js)$'
        ]
        
        if any(re.search(pattern, url, re.I) for pattern in skip_patterns):
            return False
        
        return True
    
    
    def extract_links(
        self,
        html: str,
        base_url: str,
        link_selector: Optional[str] = None
    ) -> List[str]:
        """
        Extract links from HTML
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            link_selector: CSS selector for links (optional)
        
        Returns:
            List of normalized URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        if link_selector:
            # Use specific selector
            elements = soup.select(link_selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    normalized = self.normalize_url(href, base_url)
                    if self.should_crawl_url(normalized):
                        links.append(normalized)
        else:
            # Get all links
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                normalized = self.normalize_url(href, base_url)
                if self.should_crawl_url(normalized):
                    links.append(normalized)
        
        return list(set(links))  # Deduplicate
    
    
    def smart_link_detection(self, html: str, base_url: str) -> Dict[str, List[str]]:
        """
        Intelligently categorize links by type
        
        Returns:
            {
                "detail_pages": [...],  # Links likely to be detail pages
                "list_pages": [...],    # Links likely to be more listings
                "external": [...]       # External links
            }
        """
        soup = BeautifulSoup(html, 'html.parser')
        categorized = {
            "detail_pages": [],
            "list_pages": [],
            "external": []
        }
        
        # Patterns for detail pages
        detail_patterns = [
            r'/item/', r'/product/', r'/detail/', r'/view/',
            r'/listing/', r'/ad/', r'/profile/', r'/company/',
            r'/dealer/', r'/seller/', r'\?id=', r'/\d+/?$'
        ]
        
        # Patterns for list pages
        list_patterns = [
            r'/list/', r'/category/', r'/search/', r'/browse/',
            r'page=', r'/page/\d+', r'?p=', r'offset='
        ]
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            normalized = self.normalize_url(href, base_url)
            
            if not self.should_crawl_url(normalized):
                continue
            
            # Check domain
            parsed = urlparse(normalized)
            if parsed.netloc != self.start_domain:
                categorized["external"].append(normalized)
                continue
            
            # Categorize by pattern
            if any(re.search(p, normalized, re.I) for p in detail_patterns):
                categorized["detail_pages"].append(normalized)
            elif any(re.search(p, normalized, re.I) for p in list_patterns):
                categorized["list_pages"].append(normalized)
            else:
                # Default to detail if contains ID or number
                if re.search(r'\d{3,}', normalized):
                    categorized["detail_pages"].append(normalized)
                else:
                    categorized["list_pages"].append(normalized)
        
        # Deduplicate
        for key in categorized:
            categorized[key] = list(set(categorized[key]))
        
        logger.info(f"📊 Links found - Detail: {len(categorized['detail_pages'])}, "
                   f"List: {len(categorized['list_pages'])}, "
                   f"External: {len(categorized['external'])}")
        
        return categorized
    
    
    async def fetch_page(self, url: str) -> str:
        """Fetch page HTML (with JS rendering + Stealth if needed)"""
        
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # 🧠 ADAPTIVE LEARNING: Get recommended wait time
        # Assume "None" protection initially or use history default
        wait_time = self.learner.get_recommended_wait_time(domain, "unknown", 1)
        wait_time = max(wait_time, 1.5) # Minimum 1.5s
        
        logger.info(f"🧠 Adaptive Wait: {wait_time:.2f}s for {domain}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # ⚡ FETCH with Auto-Solve
            html, final_url = await fetch_html_js(
                url=url,
                wait_time=wait_time,
                stealth_mode=True, # Always use stealth for safety
                try_auto_solve=True
            )
            
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # 🕵️ DETECT (Post-Fetch Verification)
            # Did we actually get the content or are we still blocked?
            signal = self.detector.detect_protection(
                url=final_url,
                html=html,
                status_code=200, # Assumed success if no error
                headers={},
                cookies={},
                response_time=elapsed
            )
            
            success = signal.protection_type == ProtectionType.NONE
            
            # 📝 RECORD KNOWLEDGE
            self.learner.record_attempt(
                domain=domain,
                protection_type=signal.protection_type.value,
                technique_used="playwright_auto",
                success=success,
                response_time=elapsed
            )
            
            if not success:
                logger.warning(f"⚠️ Still blocked by {signal.protection_type.value} after auto-solve")
            
            return html
            
        except Exception as e:
            logger.error(f"❌ Fetch failed: {url} - {e}")
            raise
    
    
    async def crawl_and_extract(
        self,
        start_url: str,
        extract_callback: Callable,
        link_selector: Optional[str] = None,
        auto_detect_links: bool = True
    ) -> List[Dict]:
        """
        Main crawling function
        
        Args:
            start_url: Starting URL
            extract_callback: Async function(html, url) -> data
            link_selector: CSS selector for links to follow (optional)
            auto_detect_links: Auto-detect detail vs list pages
        
        Returns:
            List of extracted data from all crawled pages
        """
        
        self.stats["start_time"] = datetime.now().isoformat()
        
        # Set starting domain
        parsed = urlparse(start_url)
        self.start_domain = parsed.netloc
        
        # Queue for BFS crawling
        queue = [(start_url, 0)]  # (url, depth)
        
        logger.info(f"🚀 Starting crawl from: {start_url}")
        logger.info(f"📊 Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        while queue and self.stats["pages_crawled"] < self.max_pages:
            current_url, depth = queue.pop(0)
            
            # Skip if already visited
            if current_url in self.visited_urls:
                continue
            
            logger.info(f"🔍 Crawling [{depth}]: {current_url}")
            
            try:
                # Fetch page
                html = await self.fetch_page(current_url)
                self.visited_urls.add(current_url)
                self.stats["pages_crawled"] += 1
                
                # Extract data from this page
                try:
                    extracted_data = await extract_callback(html, current_url)
                    
                    if extracted_data:
                        self.results.extend(extracted_data)
                        self.stats["data_extracted"] += len(extracted_data)
                        logger.info(f"✅ Extracted {len(extracted_data)} items from {current_url}")
                
                except Exception as e:
                    logger.error(f"⚠️ Extraction failed for {current_url}: {e}")
                
                # Find more links if not at max depth
                if depth < self.max_depth:
                    if auto_detect_links:
                        # Smart detection
                        categorized = self.smart_link_detection(html, current_url)
                        
                        # Prioritize detail pages
                        new_links = categorized["detail_pages"][:50]  # Limit per page
                        
                        # Add some list pages if at depth 0
                        if depth == 0:
                            new_links.extend(categorized["list_pages"][:10])
                    
                    else:
                        # Use selector or get all links
                        new_links = self.extract_links(html, current_url, link_selector)
                    
                    # Add to queue
                    for link in new_links:
                        if link not in self.visited_urls and link not in self.queued_urls:
                            queue.append((link, depth + 1))
                            self.queued_urls.add(link)
                            self.stats["urls_found"] += 1
                    
                    logger.info(f"📎 Queued {len(new_links)} new URLs (total queue: {len(queue)})")
                
                # Polite delay
                await asyncio.sleep(self.delay)
            
            except Exception as e:
                logger.error(f"❌ Error crawling {current_url}: {e}")
                self.stats["errors"] += 1
                continue
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        logger.info(f"✅ Crawl complete!")
        logger.info(f"📊 Pages crawled: {self.stats['pages_crawled']}")
        logger.info(f"📊 Data extracted: {self.stats['data_extracted']} items")
        logger.info(f"📊 Errors: {self.stats['errors']}")
        
        return self.results
    
    
    def get_stats(self) -> Dict:
        """Get crawling statistics"""
        return {
            **self.stats,
            "visited_urls": len(self.visited_urls),
            "queued_urls": len(self.queued_urls),
            "success_rate": round(
                (self.stats["pages_crawled"] - self.stats["errors"]) / 
                max(self.stats["pages_crawled"], 1) * 100, 
                1
            )
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def crawl_directory_site(
    start_url: str,
    extract_prompt: str,
    max_depth: int = 2,
    max_pages: int = 100
) -> Dict:
    """
    Easy function for directory-style sites
    
    Perfect for:
    - MachineryZone dealers
    - YellowPages listings
    - Business directories
    
    Usage:
        results = await crawl_directory_site(
            "https://www.machineryzone.com/pros/list/1.html",
            "Extract company name, website, phone, email",
            max_depth=2,
            max_pages=50
        )
    """
    
    # Import from main (circular import, so import here)
    # from main import smart_extract
    # Use core directly to avoid circular
    from core.extraction.smart_extractor import smart_extract
    
    crawler = SmartCrawler(
        max_depth=max_depth,
        max_pages=max_pages,
        delay=1.0,
        same_domain_only=True
    )
    
    async def extract_callback(html: str, url: str):
        result = await smart_extract(html, extract_prompt, cache_key=url)
        return result.get("data", [])
    
    results = await crawler.crawl_and_extract(
        start_url=start_url,
        extract_callback=extract_callback,
        auto_detect_links=True
    )
    
    return {
        "data": results,
        "stats": crawler.get_stats()
    }


async def crawl_with_selectors(
    start_url: str,
    link_selector: str,
    data_selectors: Dict[str, str],
    max_depth: int = 2,
    max_pages: int = 100
) -> Dict:
    """
    Crawl with specific CSS selectors (for advanced users)
    
    Usage:
        results = await crawl_with_selectors(
            "https://example.com/dealers",
            link_selector="a.dealer-profile",
            data_selectors={
                "name": "h1.company-name",
                "website": "a.website",
                "phone": ".contact-phone"
            },
            max_depth=2
        )
    """
    
    # from main import extract_with_selectors
    from core.extraction.selector_extractor import extract_with_selectors
    
    crawler = SmartCrawler(
        max_depth=max_depth,
        max_pages=max_pages,
        delay=1.0
    )
    
    async def extract_callback(html: str, url: str):
        result = extract_with_selectors(html, data_selectors)
        return result.get("data", [])
    
    results = await crawler.crawl_and_extract(
        start_url=start_url,
        extract_callback=extract_callback,
        link_selector=link_selector,
        auto_detect_links=False
    )
    
    return {
        "data": results,
        "stats": crawler.get_stats()
    }


# ============================================================================
# EXAMPLE: MachineryZone Scraper
# ============================================================================

async def scrape_machineryzone_dealers(max_pages: int = 50) -> Dict:
    """
    Specific scraper for MachineryZone dealer directory
    
    This is what you need for your use case!
    """
    
    logger.info("🏭 Starting MachineryZone scraper...")
    
    result = await crawl_directory_site(
        start_url="https://www.machineryzone.com/pros/list/1.html",
        extract_prompt="Extract company name, website URL, phone number, email address, and full address",
        max_depth=2,
        max_pages=max_pages
    )
    
    logger.info(f"✅ Scraped {len(result['data'])} dealers")
    
    return result


# ============================================================================
# CLI USAGE
# ============================================================================

async def main():
    """Test the crawler"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ScrapiGen Crawler")
    parser.add_argument("url", help="Starting URL")
    parser.add_argument("prompt", help="What to extract")
    parser.add_argument("--depth", type=int, default=2, help="Max crawl depth")
    parser.add_argument("--pages", type=int, default=50, help="Max pages to crawl")
    
    args = parser.parse_args()
    
    print(f"\n🚀 Starting crawl...")
    print(f"URL: {args.url}")
    print(f"Prompt: {args.prompt}")
    print(f"Max depth: {args.depth}")
    print(f"Max pages: {args.pages}")
    print("="*80 + "\n")
    
    result = await crawl_directory_site(
        start_url=args.url,
        extract_prompt=args.prompt,
        max_depth=args.depth,
        max_pages=args.pages
    )
    
    print("\n" + "="*80)
    print("📊 CRAWL COMPLETE")
    print("="*80)
    print(f"Total items extracted: {len(result['data'])}")
    print(f"Pages crawled: {result['stats']['pages_crawled']}")
    print(f"Success rate: {result['stats']['success_rate']}%")
    print("="*80)
    
    # Save results
    import json
    with open("crawl_results.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\n💾 Results saved to: crawl_results.json")


if __name__ == "__main__":
    asyncio.run(main())
