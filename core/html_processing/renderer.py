import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)
# Global browser instance and cache
_browser: Optional[Browser] = None
_playwright = None
_render_cache = {}  # Simple in-memory cache (use Redis in production)
_cache_ttl = 3600  # 1 hour cache
_context = None
_context_lock = asyncio.Lock()

# Configuration
BROWSER_CONFIG = {
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--no-first-run",
        "--no-zygote",
        "--disable-gpu",
        "--disable-blink-features=AutomationControlled",
    ]
}

# Resources to block (saves 70-80% bandwidth and time)
BLOCKED_RESOURCES = [
    "image", "media", "font", "stylesheet",  # Visual stuff we don't need
    "beacon", "csp_report", "imageset",      # Tracking/Analytics
]

# Alternative: Only block non-essential (keep CSS for some sites)
MINIMAL_BLOCK = ["image", "media", "font", "beacon", "csp_report"]

async def init_browser() -> Browser:
    """Initialize browser once and reuse"""
    global _browser, _playwright
    
    if _browser is None or not _browser.is_connected():
        try:
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(**BROWSER_CONFIG)
            logger.info("✅ Browser initialized")
        except Exception as e:
            logger.error(f"❌ Browser init failed: {e}")
            raise
    
    return _browser


# async def get_or_create_context(browser: Browser) -> BrowserContext:
#     """Reuse browser context to save ~2 seconds per request"""
#     global _context
    
#     if _context is None or _context._impl_obj._is_closed_or_closing:
#         _context = await browser.new_context(
#             viewport={"width": 1920, "height": 1080},
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#             locale="en-US",
#             timezone_id="America/New_York",
            
#             # 🔥 SPEED OPTIMIZATIONS
#             java_script_enabled=True,
#             bypass_csp=True,  # Bypass Content Security Policy
#             ignore_https_errors=True,  # Skip SSL verification
#         )
#         logger.info("✅ Browser context created")
    
#     return _context

async def get_or_create_context(browser):
    # ...existing code...
    global _context, _browser
    _browser = browser
    # ensure only one coroutine races to create a context
    async with _context_lock:
        if _context is None:
            _context = await browser.new_context()
            return _context

        # safe attribute checks instead of direct attribute access
        try:
            impl = getattr(_context, "_impl_obj", None)
            closed_flag = False
            if impl is not None:
                closed_flag = bool(getattr(impl, "_is_closed_or_closing", False))
        except Exception:
            closed_flag = True

        if _context is None or closed_flag:
            # create a new context if closed or missing
            try:
                _context = await browser.new_context()
            except Exception:
                # fallback: ensure we clear broken context and re-raise
                _context = None
                raise
        return _context


async def create_fast_page(context: BrowserContext, stealth_mode: bool = False) -> Page:
    """Create optimized page with minimal overhead"""
    page = await context.new_page()
    
    # Only add stealth if needed (saves ~1 second)
    if stealth_mode:
        print("🕵️ Enhanced stealth mode activated")
        
        # ✅ Add more realistic headers
        await context.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        })
        
        # ✅ Add random realistic viewport
        import random
        viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
        ]
        viewport = random.choice(viewports)
        
        await page.set_viewport_size(viewport)
        print(f"🖥️ Viewport: {viewport['width']}x{viewport['height']}")
        
        # ✅ Inject anti-detection scripts
        await page.add_init_script("""
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Randomize plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // More realistic chrome object
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Hide automation
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Realistic permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    return page


def get_cache_key(url: str, wait_time: float) -> str:
    """Generate cache key"""
    key = f"{url}:{wait_time}"
    return hashlib.md5(key.encode()).hexdigest()


def is_cache_valid(cache_entry: dict) -> bool:
    """Check cache validity"""
    if not cache_entry:
        return False
    cached_time = datetime.fromisoformat(cache_entry.get("timestamp", "2000-01-01"))
    return datetime.now() - cached_time < timedelta(seconds=_cache_ttl)



async def create_stealth_page(browser: Browser) -> Page:
    """Create a page with stealth settings to avoid detection"""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-US",
        timezone_id="America/New_York",
    )
    
    page = await context.new_page()
    
    # Inject stealth scripts to avoid detection
    await page.add_init_script("""
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Chrome runtime
        window.chrome = { runtime: {} };
        
        // Permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    
    return page


async def fetch_html_js(
    url: str,
    wait_time: float = 1.5,  # 🔥 Reduced from 2.0s
    timeout: int = 20000,    # 🔥 Reduced from 30s (fail fast)
    block_resources: bool = True,
    use_cache: bool = True,
    stealth_mode: bool = False,
    wait_strategy: str = "smart"  # 🔥 NEW: smart, fast, thorough
) -> Tuple[str, str]:
    """
    Optimized HTML fetching with Playwright
    
    wait_strategy options:
    - "smart": Try domcontentloaded, fallback to networkidle (default)
    - "fast": Only domcontentloaded (~3-5s faster, might miss lazy content)
    - "thorough": Use networkidle (~5-8s slower, gets everything)
    """
    
    # Check cache
    if use_cache:
        cache_key = get_cache_key(url, wait_time)
        cached = _render_cache.get(cache_key)
        if cached and is_cache_valid(cached):
            logger.info(f"📦 Cache HIT: {url}")
            return cached["html"], cached["final_url"]
    
    logger.info(f"🌐 Rendering: {url} (strategy: {wait_strategy})")
    start_time = asyncio.get_event_loop().time()
    
    browser = await init_browser()
    context = await get_or_create_context(browser)  # 🔥 Reuse context
    page = await create_fast_page(context, stealth_mode)
    
    try:
        # Block resources (saves 60-70% time)
        if block_resources:
            await page.route("**/*", lambda route: (
                route.abort() if route.request.resource_type in BLOCKED_RESOURCES
                else route.continue_()
            ))
        
        # 🔥 SMART WAIT STRATEGY
        if wait_strategy == "fast":
            # Fastest: Just wait for DOM (3-5s)
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        
        elif wait_strategy == "thorough":
            # Slowest but most complete (10-15s)
            await page.goto(url, timeout=timeout, wait_until="networkidle")
        
        else:  # "smart" (default)
            # Try fast first, fallback to thorough if needed
            try:
                await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                
                # Quick check: Did we get content?
                content_check = await page.evaluate("""
                    () => {
                        const body = document.body.innerText;
                        return body.length > 1000;  // Has meaningful content?
                    }
                """)
                
                if not content_check:
                    # Not enough content, wait for networkidle
                    logger.info("⏳ Waiting for more content...")
                    await page.wait_for_load_state("networkidle", timeout=10000)
                
            except Exception:
                # Fallback to networkidle
                await page.goto(url, timeout=timeout, wait_until="networkidle")
        
        # Reduced wait time for lazy content
        await asyncio.sleep(wait_time)
        
        # 🔥 PARALLEL EXTRACTION - Get URL while getting content
        html_task = page.content()
        url_task = page.evaluate("window.location.href")
        
        html, final_url = await asyncio.gather(html_task, url_task)
        
        # Cache result
        if use_cache:
            cache_key = get_cache_key(url, wait_time)
            _render_cache[cache_key] = {
                "html": html,
                "final_url": final_url,
                "timestamp": datetime.now().isoformat()
            }
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"✅ Rendered in {elapsed:.2f}s: {len(html):,} chars")
        
        return html, final_url
    
    except Exception as e:
        logger.error(f"❌ Rendering failed: {e}")
        raise
    
    finally:
        # Only close page, keep context alive
        await page.close()


async def fetch_multiple_urls(
    urls: list[str],
    wait_time: float = 1.5,
    max_concurrent: int = 3,  # 🔥 Process 3 pages simultaneously
    **kwargs
) -> list[dict]:
    """
    Efficiently fetch multiple URLs with concurrency
    
    Returns list of: {"url": str, "html": str, "final_url": str, "error": str}
    """
    
    async def fetch_one(url: str) -> dict:
        try:
            html, final_url = await fetch_html_js(url, wait_time=wait_time, **kwargs)
            return {"url": url, "html": html, "final_url": final_url, "error": None}
        except Exception as e:
            return {"url": url, "html": None, "final_url": None, "error": str(e)}
    
    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_limit(url: str) -> dict:
        async with semaphore:
            return await fetch_one(url)
    
    # Process all URLs concurrently (with limit)
    logger.info(f"🚀 Fetching {len(urls)} URLs with max {max_concurrent} concurrent")
    results = await asyncio.gather(*[fetch_with_limit(url) for url in urls])
    
    return results

# async def cleanup_browser():
#     """Cleanup browser resources (call on shutdown)"""
#     global _browser, _playwright
    
#     if _browser:
#         await _browser.close()
#         _browser = None
    
#     if _playwright:
#         await _playwright.stop()
#         _playwright = None

async def cleanup_browser():
    """Close context and browser safely (call on shutdown)."""
    global _context, _browser
    try:
        if _context is not None:
            try:
                await _context.close()
            except Exception:
                pass
            _context = None
    finally:
        if _browser is not None:
            try:
                await _browser.close()
            except Exception:
                pass
            _browser = None    
    logger.info("🧹 Browser cleanup completed")


async def clear_cache():
    """Clear render cache (useful for testing)"""
    global _render_cache
    _render_cache = {}
    logger.info("🗑️ Cache cleared")



from core.html_processing.advance_stealth_mode import MultiSignalDetector, CostFreeSolver, ProtectionType

# Performance monitoring
async def get_cache_stats() -> dict:
    """Get cache statistics"""
    valid_entries = sum(1 for entry in _render_cache.values() if is_cache_valid(entry))
    
    return {
        "total_cached": len(_render_cache),
        "valid_entries": valid_entries,
        "expired_entries": len(_render_cache) - valid_entries,
        "cache_ttl": _cache_ttl
    }


async def fetch_html_js(
    url: str,
    wait_time: float = 1.5,
    timeout: int = 20000,
    block_resources: bool = True,
    use_cache: bool = True,
    stealth_mode: bool = False,
    wait_strategy: str = "smart",
    try_auto_solve: bool = True  # 🔥 New parameter
) -> Tuple[str, str]:
    """
    Optimized HTML fetching with Playwright + Auto-Solving
    """
    
    # Check cache
    if use_cache:
        cache_key = get_cache_key(url, wait_time)
        cached = _render_cache.get(cache_key)
        if cached and is_cache_valid(cached):
            logger.info(f"📦 Cache HIT: {url}")
            return cached["html"], cached["final_url"]
    
    logger.info(f"🌐 Rendering: {url} (strategy: {wait_strategy})")
    start_time = asyncio.get_event_loop().time()
    
    browser = await init_browser()
    context = await get_or_create_context(browser)
    page = await create_fast_page(context, stealth_mode)
    
    try:
        # Block resources
        if block_resources:
            await page.route("**/*", lambda route: (
                route.abort() if route.request.resource_type in BLOCKED_RESOURCES
                else route.continue_()
            ))
        
        # Navigate
        try:
            response = await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            status_code = response.status if response else 0
        except Exception as e:
            logger.warning(f"⚠️ Navigation warning: {e}")
            status_code = 0

        # Wait
        await asyncio.sleep(wait_time)
        
        # DETECT PROTECTIONS
        detector = MultiSignalDetector()
        html = await page.content()
        final_url = page.url
        
        # Get headers/cookies for detection
        cookies = {c['name']: c['value'] for c in await context.cookies()}
        # Note: We don't easily get response headers here without response interception, 
        # but we can pass empty headers to detector for now or improve this later.
        headers = {} 
        
        elapsed_nav = asyncio.get_event_loop().time() - start_time
        
        signal = detector.detect_protection(
            url=final_url,
            html=html,
            status_code=status_code,
            headers=headers,
            cookies=cookies,
            response_time=elapsed_nav
        )
        
        if signal.protection_type != ProtectionType.NONE:
            logger.info(f"🛡️ Protection detected: {signal.protection_type.value} (Confidence: {signal.confidence})")
            
            if try_auto_solve:
                solver = CostFreeSolver()
                
                if not solver.should_give_up(signal.protection_type):
                    logger.info(f"🔧 Attempting to solve {signal.protection_type.value}...")
                    
                    solved = False
                    if signal.protection_type == ProtectionType.CF_BROWSER_CHECK:
                        solved = await solver.solve_cf_browser_check(page)
                    elif signal.protection_type == ProtectionType.CF_TURNSTILE_INVISIBLE:
                        solved = await solver.solve_cf_turnstile_invisible(page)
                    elif signal.protection_type == ProtectionType.CF_TURNSTILE_VISIBLE:
                        solved = await solver.solve_cf_turnstile_visible(page)
                    elif signal.protection_type in [ProtectionType.DATADOME_COOKIE, ProtectionType.PX_COOKIE]:
                        solved = await solver.solve_with_cookies(page, url)
                    elif signal.protection_type == ProtectionType.BASIC_RATE_LIMIT:
                        logger.info("⏳ Rate limit detected, waiting...")
                        await asyncio.sleep(5)
                        solved = True
                    
                    if solved:
                        logger.info("✅ Protection solved! Refreshing content...")
                        await asyncio.sleep(1)
                        html = await page.content()
                        final_url = page.url
                    else:
                        logger.warning("❌ Failed to solve protection.")
                else:
                    logger.warning("⛔ Protection considered unsolvable free.")
        
        # Cache result
        if use_cache:
            cache_key = get_cache_key(url, wait_time)
            _render_cache[cache_key] = {
                "html": html,
                "final_url": final_url,
                "timestamp": datetime.now().isoformat()
            }
        
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.info(f"✅ Rendered in {elapsed:.2f}s: {len(html):,} chars")
        
        return html, final_url
    
    except Exception as e:
        logger.error(f"❌ Rendering failed: {e}")
        raise
    
    finally:
        await page.close()
