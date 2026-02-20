"""
Batch processor for handling 10,000+ URLs efficiently
Includes: Progress tracking, resume capability, parallel processing
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import httpx
from tqdm import tqdm
import logging
from core.html_processing.renderer import fetch_html_js, fetch_multiple_urls
from core.html_processing.detector import get_rendering_strategy
from config.config import BATCH_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process large batches of URLs with progress tracking"""
    
    def __init__(
        self,
        job_id: str,
        output_dir: str = "./batch_results",
        max_concurrent: int = None
    ):
        self.job_id = job_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.max_concurrent = max_concurrent or BATCH_CONFIG["max_concurrent_static"]
        self.batch_size = BATCH_CONFIG["batch_size"]
        
        # Progress tracking
        self.progress_file = self.output_dir / f"{job_id}_progress.json"
        self.results_file = self.output_dir / f"{job_id}_results.jsonl"
        self.failed_file = self.output_dir / f"{job_id}_failed.json"
        
        self.stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "js_rendered": 0,
            "static_only": 0,
            "start_time": None,
            "end_time": None,
        }
        
        self.failed_urls = []
    
    
    async def process_batch(
        self,
        urls: List[str],
        prompt: str,
        resume: bool = True
    ) -> Dict:
        """
        Main batch processing function
        
        Args:
            urls: List of URLs to scrape
            prompt: Extraction prompt
            resume: Resume from saved progress
        
        Returns:
            Statistics dictionary
        """
        
        self.stats["total"] = len(urls)
        self.stats["start_time"] = datetime.now().isoformat()
        
        # Load progress if resuming
        processed_urls = set()
        if resume and self.progress_file.exists():
            processed_urls = self._load_progress()
            logger.info(f"📂 Resuming: {len(processed_urls)} already processed")
        
        # Filter out already processed URLs
        remaining_urls = [url for url in urls if url not in processed_urls]
        logger.info(f"🎯 Processing {len(remaining_urls)} URLs")
        
        # Process in batches
        with tqdm(total=len(remaining_urls), desc="Scraping") as pbar:
            for i in range(0, len(remaining_urls), self.batch_size):
                batch = remaining_urls[i:i + self.batch_size]
                
                results = await self._process_batch_chunk(batch, prompt)
                
                # Save results incrementally
                self._save_results(results)
                self._save_progress([r["url"] for r in results])
                
                # Update stats
                self.stats["completed"] += len([r for r in results if not r.get("error")])
                self.stats["failed"] += len([r for r in results if r.get("error")])
                
                pbar.update(len(batch))
                
                # Small delay between batches
                await asyncio.sleep(0.5)
        
        # Final cleanup
        self.stats["end_time"] = datetime.now().isoformat()
        self._save_failed_urls()
        self._save_final_stats()
        
        logger.info(f"✅ Batch complete: {self.stats['completed']}/{self.stats['total']} successful")
        
        return self.stats
    
    
    async def _process_batch_chunk(self, urls: List[str], prompt: str) -> List[Dict]:
        """Process a chunk of URLs"""
        
        results = []
        
        # Step 1: Fetch all HTML (static first)
        html_results = await self._fetch_all_html(urls)
        
        # Step 2: Extract data from each
        for html_result in html_results:
            try:
                if html_result.get("error"):
                    results.append({
                        "url": html_result["url"],
                        "error": html_result["error"],
                        "data": None
                    })
                    continue
                
                # Import extraction function (from your main.py)
                from main import smart_extract
                
                extracted = await smart_extract(
                    html=html_result["html"],
                    prompt=prompt,
                    cache_key=None  # No caching in batch mode
                )
                
                results.append({
                    "url": html_result["url"],
                    "final_url": html_result["final_url"],
                    "data": extracted.get("data", []),
                    "strategy": extracted.get("strategy"),
                    "error": None
                })
                
            except Exception as e:
                results.append({
                    "url": html_result["url"],
                    "error": str(e),
                    "data": None
                })
                self.failed_urls.append({"url": html_result["url"], "error": str(e)})
        
        return results
    
    
    async def _fetch_all_html(self, urls: List[str]) -> List[Dict]:
        """Efficiently fetch HTML for all URLs"""
        
        results = []
        
        # Separate into static and JS-heavy
        static_urls = []
        js_urls = []
        
        # Quick pre-check (fetch first to see if JS needed)
        for url in urls:
            # For now, try static first for all
            static_urls.append(url)
        
        # Fetch static HTML in parallel
        async def fetch_static(url: str) -> Dict:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    html = response.text
                    
                    # Check if JS needed
                    from core.html_processing.detector import get_rendering_strategy
                    strategy = get_rendering_strategy(url, html)
                    
                    if strategy["needs_js"]:
                        # Need to re-fetch with Playwright
                        rendered_html, final_url = await fetch_html_js(
                            url=url,
                            wait_time=strategy["wait_time"],
                            wait_strategy=strategy.get("wait_strategy", "smart"),
                            stealth_mode=strategy["stealth_mode"]
                        )
                        self.stats["js_rendered"] += 1
                        return {"url": url, "html": rendered_html, "final_url": final_url, "error": None}
                    else:
                        self.stats["static_only"] += 1
                        return {"url": url, "html": html, "final_url": url, "error": None}
                        
            except Exception as e:
                return {"url": url, "html": None, "final_url": None, "error": str(e)}
        
        # Process with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_with_limit(url: str):
            async with semaphore:
                return await fetch_static(url)
        
        results = await asyncio.gather(*[fetch_with_limit(url) for url in urls])
        
        return results
    
    
    def _save_results(self, results: List[Dict]):
        """Save results to JSONL file (append mode)"""
        with open(self.results_file, "a", encoding="utf-8") as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    
    def _save_progress(self, urls: List[str]):
        """Save processed URLs for resume capability"""
        existing = set()
        if self.progress_file.exists():
            with open(self.progress_file, "r") as f:
                existing = set(json.load(f))
        
        existing.update(urls)
        
        with open(self.progress_file, "w") as f:
            json.dump(list(existing), f)
    
    
    def _load_progress(self) -> set:
        """Load previously processed URLs"""
        with open(self.progress_file, "r") as f:
            return set(json.load(f))
    
    
    def _save_failed_urls(self):
        """Save failed URLs for retry"""
        if self.failed_urls:
            with open(self.failed_file, "w") as f:
                json.dump(self.failed_urls, f, indent=2)
    
    
    def _save_final_stats(self):
        """Save final statistics"""
        stats_file = self.output_dir / f"{self.job_id}_stats.json"
        with open(stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)
    
    
    def export_to_csv(self, output_file: Optional[str] = None):
        """Export results to CSV"""
        output_file = output_file or self.output_dir / f"{self.job_id}_results.csv"
        
        # Read JSONL
        all_data = []
        with open(self.results_file, "r", encoding="utf-8") as f:
            for line in f:
                result = json.loads(line)
                if result.get("data"):
                    for item in result["data"]:
                        item["source_url"] = result["url"]
                        all_data.append(item)
        
        if not all_data:
            logger.warning("No data to export")
            return
        
        # Write CSV
        keys = set()
        for item in all_data:
            keys.update(item.keys())
        
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            writer.writerows(all_data)
        
        logger.info(f"📊 Exported {len(all_data)} rows to {output_file}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def batch_scrape_from_file(
    url_file: str,
    prompt: str,
    job_id: Optional[str] = None
) -> Dict:
    """
    Scrape URLs from a file (one URL per line or CSV)
    
    Usage:
        results = await batch_scrape_from_file("urls.txt", "Extract product name and price")
    """
    
    # Load URLs
    urls = []
    file_path = Path(url_file)
    
    if file_path.suffix == ".csv":
        # Assume first column is URLs
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            urls = [row[0] for row in reader if row]
    else:
        # Plain text file
        with open(file_path, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    
    # Generate job ID
    job_id = job_id or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Process
    processor = BatchProcessor(job_id)
    stats = await processor.process_batch(urls, prompt)
    
    # Export to CSV
    processor.export_to_csv()
    
    return stats


async def batch_scrape_olx_category(
    category_url: str,
    max_pages: int = 10,
    prompt: str = "Extract title, price, location, and image"
) -> Dict:
    """
    Scrape all listings from an OLX category
    
    Usage:
        results = await batch_scrape_olx_category(
            "https://www.olx.com.pk/mobile-phones/",
            max_pages=5
        )
    """
    
    # This will be implemented in pagination section!
    # For now, just a placeholder
    pass


# ============================================================================
# CLI Interface
# ============================================================================

async def main():
    """CLI for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ScrapiGen Batch Processor")
    parser.add_argument("urls_file", help="File with URLs (one per line or CSV)")
    parser.add_argument("prompt", help="Extraction prompt")
    parser.add_argument("--job-id", help="Job ID (auto-generated if not provided)")
    parser.add_argument("--resume", action="store_true", help="Resume from previous run")
    parser.add_argument("--max-concurrent", type=int, default=5, help="Max concurrent requests")
    
    args = parser.parse_args()
    
    # Run batch
    stats = await batch_scrape_from_file(
        args.urls_file,
        args.prompt,
        args.job_id
    )
    
    print("\n" + "="*80)
    print("📊 Batch Processing Complete")
    print("="*80)
    print(f"Total URLs: {stats['total']}")
    print(f"✅ Successful: {stats['completed']}")
    print(f"❌ Failed: {stats['failed']}")
    print(f"⚡ JS Rendered: {stats['js_rendered']}")
    print(f"📄 Static Only: {stats['static_only']}")
    print(f"⏱️  Duration: {stats['start_time']} → {stats['end_time']}")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
