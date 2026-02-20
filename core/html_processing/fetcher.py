"""
HTML fetching with intelligent caching and JS rendering
Main entry point for fetching web pages
"""
import httpx
from fastapi import HTTPException
from core.html_processing.detector import get_rendering_strategy
from core.html_processing.renderer import fetch_html_js
from storage.cache_manager import get_cached_html, cache_rendered_html
from storage.analytics_db import track_cache_hit, track_cache_miss
from config.settings import DEFAULT_HEADERS
from storage.analytics_db import analytics_db

# HTML Fetching
async def fetch_html(url: str) -> str:
    """
    Fetch HTML with intelligent caching and JS rendering
    
    Flow:
    1. Check cache first (instant if cached)
    2. Try static HTML
    3. Check if JS needed (detector.py)
    4. Render with Playwright if needed (utils_js_renderer.py)
    5. Cache the result (cache_manager.py)
    """
    
    # Step 1: Check cache first
    cached = await get_cached_html(url)
    if cached:
        print(f"📦 Cache HIT: {url}")
        analytics_db["cache_hits"] += 1
        return cached["html"]
    
    analytics_db["cache_misses"] += 1
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            # Step 2: Fetch static HTML first
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            html_content = response.text.replace('\x00', '')
            
            print(f"📄 Static HTML: {len(html_content):,} chars from {url}")
            
            # Step 3: Get intelligent rendering strategy
            strategy = get_rendering_strategy(url, html_content)
            
            print(f"🎯 Strategy: {strategy['reason']}")
            
            # Step 4: Decide if JS rendering needed
            if strategy['needs_js']:
                print(f"⚡ JS Rendering (wait: {strategy['wait_time']}s, stealth: {strategy['stealth_mode']})")
                
                try:
                    rendered_html, final_url = await fetch_html_js(
                        url=url,
                        wait_time=strategy['wait_time'],
                        timeout=45000,
                        block_resources=strategy['block_resources'],
                        use_cache=False,  # We handle caching here
                        stealth_mode=strategy['stealth_mode'],
                        wait_strategy=strategy.get('wait_strategy', 'smart')
                    )
                    
                    print(f"✅ Rendered: {len(rendered_html):,} chars")
                    
                    analytics_db["strategies_used"]["playwright_renders"] += 1
                    
                    # Only use rendered if significantly better
                    if len(rendered_html) > len(html_content) + 500:
                        # Step 5: Cache the rendered result
                        await cache_rendered_html(url, rendered_html, final_url)
                        return rendered_html
                    else:
                        print("⚠️ Rendered not better, using static")
                        await cache_rendered_html(url, html_content, url)
                        return html_content
                
                except Exception as e:
                    print(f"⚠️ Playwright failed: {e} → Using static HTML")
                    analytics_db["strategies_used"]["playwright_failed"] = analytics_db["strategies_used"].get("playwright_failed", 0) + 1
                    await cache_rendered_html(url, html_content, url)
                    return html_content
            else:
                print("✅ Static HTML sufficient")
                # Cache static HTML too
                await cache_rendered_html(url, html_content, url)
                return html_content
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                # Last resort: Try Playwright with stealth
                print("🔒 403 error, trying stealth mode...")
                try:
                    rendered_html, _ = await fetch_html_js(
                        url=url,
                        wait_time=3.0,
                        stealth_mode=True,
                        block_resources=True
                    )
                    await cache_rendered_html(url, rendered_html, url)
                    return rendered_html
                except:
                    raise HTTPException(status_code=403, detail="Access denied by website")
            raise HTTPException(status_code=e.response.status_code, detail=f"HTTP {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch: {str(e)}")
        
def get_domain(url: str) -> str:
    """Extract domain from URL for caching"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc