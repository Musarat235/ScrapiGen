"""
Smart detector for JS-rendered sites
Optimized for Pakistani and global e-commerce sites
"""

import re
from typing import Dict, List, Tuple
from urllib.parse import urlparse


# Domain-specific rules (Pakistan + Global)
JS_HEAVY_DOMAINS = {
    # Pakistani Sites
    "olx.com.pk": {"threshold": 5000, "wait_time": 3.0, "reason": "OLX lazy loads listings"},
    "zameen.com": {"threshold": 4000, "wait_time": 2.5, "reason": "Property listings are JS-rendered"},
    "daraz.pk": {"threshold": 6000, "wait_time": 2.0, "reason": "Product data loaded via React"},
    "graana.com": {"threshold": 4000, "wait_time": 2.0, "reason": "Real estate JS-heavy"},
    "lamudi.pk": {"threshold": 4000, "wait_time": 2.0, "reason": "Property listings JS-rendered"},
    "pakwheels.com": {"threshold": 5000, "wait_time": 2.0, "reason": "Car listings lazy-loaded"},
    
    # Global Sites
    "amazon.com": {"threshold": 8000, "wait_time": 2.0, "reason": "Dynamic product loading"},
    "ebay.com": {"threshold": 7000, "wait_time": 2.0, "reason": "Listings are JS-rendered"},
    "zillow.com": {"threshold": 6000, "wait_time": 2.5, "reason": "Real estate JS-heavy"},
    "realtor.com": {"threshold": 6000, "wait_time": 2.5, "reason": "Property data JS-loaded"},
    "airbnb.com": {"threshold": 5000, "wait_time": 3.0, "reason": "Listings are React-based"},
    "unstop.com": {"threshold": 5000, "wait_time": 3.0, "reason": "Unstop uses React and requires JS"},
}


def get_domain_info(url: str) -> Tuple[str, Dict]:
    """Extract domain and get its specific rules"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    
    # Check exact match first
    if domain in JS_HEAVY_DOMAINS:
        return domain, JS_HEAVY_DOMAINS[domain]
    
    # Check partial match (for subdomains)
    for known_domain, config in JS_HEAVY_DOMAINS.items():
        if known_domain in domain:
            return known_domain, config
    
    return domain, {}


def analyze_html_structure(html: str) -> Dict[str, any]:
    """
    ✅ IMPROVED: Better framework and content detection
    Ignores loading screens and error messages
    """
    metrics = {
        "length": len(html),
        "script_count": html.count("<script"),
        "has_frameworks": False,
        "has_content": False,
        "text_ratio": 0.0,
        "has_protection": False,
        "framework_type": None,
        "is_placeholder": False,
        "has_cookie_error": False  # ✅ NEW
    }
    
    # ✅ Check for JS frameworks
    frameworks = {
        "Next.js": [
            'id="__next"',
            '__NEXT_DATA__',
            '/_next/static/',
            'next-route-announcer'
        ],
        "React": [
            'data-reactroot',
            'data-react-helmet',
            'react-dom',
            'ReactDOM'
        ],
        "Vue": [
            'data-vue-ssr',
            '__NUXT__',
            'data-v-',
            'vue-router'
        ],
        "Angular": [
            'ng-version',
            'ng-app',
            'ng-controller',
            '<app-root'  # ✅ NEW - Angular root element
        ],
        "Svelte": [
            'data-svelte'
        ],
    }
    
    for framework, signatures in frameworks.items():
        if any(sig in html for sig in signatures):
            metrics["has_frameworks"] = True
            metrics["framework_type"] = framework
            break
    
    # ✅ NEW: Check for cookie/JavaScript requirement errors
    cookie_error_signs = [
        'Cookies are disabled',
        'Enable JavaScript and cookies',
        'Please enable cookies',
        'Cookie support is required',
        'JavaScript is required',
        'Please enable JavaScript'
    ]
    metrics["has_cookie_error"] = any(sign in html for sign in cookie_error_signs)
    
    # ✅ IMPROVED: Check for placeholder/skeleton HTML
    placeholder_signs = [
        '',
        '',
        '',
        '',
        '',  # ✅ NEW - Empty Angular root
        '<div',  # ✅ NEW - Angular with loading screen
        'class="skeleton',
        'class="loading',
        'class="loader',  # ✅ NEW
        'home-loader-screen',  # ✅ NEW - Unstop specific
        'Loading...',
        'Please wait',
        'Please Wait'
    ]
    metrics["is_placeholder"] = any(sign in html for sign in placeholder_signs)
    
    # ✅ IMPROVED: Better content detection (excludes loading/error screens)
    # First, check for REAL content indicators
    strong_content_indicators = [
        '<article',
        '<main',
        'itemprop="name"',
        'itemprop="description"',
        'schema.org/Product',
        'schema.org/Article',
        '<table',  # Data tables usually mean real content
        'class="product-detail',
        'class="item-detail',
        'class="post-content',
        'class="article-body'
    ]
    
    weak_content_indicators = [
        'class="content"',
        'class="product',
        'class="item"',
        'class="listing"',
        'class="card"',
        '<h1',
        '<h2',
        '<p'
    ]
    
    # Count strong indicators (each worth 3 points)
    strong_count = sum(3 for indicator in strong_content_indicators if indicator in html.lower())
    
    # Count weak indicators (each worth 1 point)
    weak_count = sum(1 for indicator in weak_content_indicators if indicator in html.lower())
    
    total_score = strong_count + weak_count
    
    # ✅ NEW: Subtract points for loading/error content
    loading_indicators = [
        'Please Wait',
        'Loading...',
        'Cookies are disabled',
        'class="loader',
        'class="loading'
    ]
    loading_count = sum(1 for indicator in loading_indicators if indicator in html)
    
    # Need at least 5 points AND no loading indicators
    metrics["has_content"] = (total_score >= 5) and (loading_count == 0)
    
    # Calculate text ratio (text vs tags)
    import re
    text_content = re.sub(r']+>', '', html)
    if len(html) > 0:
        metrics["text_ratio"] = len(text_content.strip()) / len(html)
    
    # Check for bot protection
    protection_signs = [
        "cf-browser-verification",
        "Just a moment",
        "Checking your browser",
        "DDoS protection",
        "Verifying you are human",
        "Please wait while we verify"
    ]
    
    metrics["has_protection"] = any(sign in html for sign in protection_signs)
    
    return metrics

def needs_js(html: str, url: str) -> bool:
    """
    ✅ FIXED: Proper decision logic with correct order
    
    Returns:
        True if Playwright should be used
        False if static HTML is sufficient
    """
    
    # Get domain-specific rules
    domain, domain_config = get_domain_info(url)
    
    # Analyze HTML structure
    metrics = analyze_html_structure(html)
    
    # ========================================================================
    # DECISION TREE - ORDER IS CRITICAL!
    # ========================================================================
    
    # 1. Bot protection ALWAYS needs JS
    if metrics["has_protection"]:
        print(f"🔒 Bot protection detected → JS needed")
        return True
    
    # 2. ✅ CRITICAL: Check domain-specific rules FIRST (before other checks)
    if domain_config:
        threshold = domain_config.get("threshold", 5000)
        if metrics["length"] < threshold:
            print(f"🌐 Domain rule: {domain_config.get('reason', 'Known JS site')} → JS needed")
            return True
    
    # 3. Placeholder HTML (almost empty div)
    if metrics["is_placeholder"]:
        print(f"📦 Placeholder HTML detected → JS needed")
        return True
    
    # 4. Very short HTML = placeholder page
    if metrics["length"] < 1000:
        print(f"📏 HTML too short ({metrics['length']} chars) → JS needed")
        return True
    
    # 5. Framework detected + no content = needs JS
    if metrics["has_frameworks"]:
        if not metrics["has_content"]:
            print(f"⚛️ {metrics['framework_type']} detected but no content → JS needed")
            return True
        elif metrics["length"] < 8000:
            print(f"⚛️ {metrics['framework_type']} with short HTML ({metrics['length']} chars) → JS needed")
            return True
    
    # 6. Low text ratio + many scripts
    if metrics["text_ratio"] < 0.05 and metrics["script_count"] > 10:
        print(f"📊 Low text ratio ({metrics['text_ratio']:.2%}) + many scripts → JS needed")
        return True
    
    # 7. Lots of scripts but no content
    if metrics["script_count"] > 15 and not metrics["has_content"]:
        print(f"📜 Many scripts ({metrics['script_count']}) but no content → JS needed")
        return True
    
    # Default: static HTML should work
    print(f"✅ Static HTML sufficient (length: {metrics['length']:,}, scripts: {metrics['script_count']}, content: {metrics['has_content']})")
    return False


def get_wait_time(url: str, html: str) -> float:
    """
    Determine optimal wait time for lazy-loaded content
    
    Returns:
        Wait time in seconds
    """
    
    # Domain-specific wait times
    domain, domain_config = get_domain_info(url)
    if domain_config and "wait_time" in domain_config:
        return domain_config["wait_time"]
    
    # Analyze HTML for indicators
    metrics = analyze_html_structure(html)
    
    # Framework-specific wait times
    if metrics["framework_type"]:
        framework_wait_times = {
            "Next.js": 2.0,
            "React": 2.0,
            "Vue": 1.5,
            "Angular": 2.5,
            "Svelte": 1.5,
        }
        return framework_wait_times.get(metrics["framework_type"], 2.0)
    
    # Default wait time
    return 1.5


def should_use_stealth(url: str, html: str) -> bool:
    """
    Decide if stealth mode is needed
    
    Stealth mode adds overhead, so only use when necessary
    """
    
    # Check for bot detection signs
    bot_detection_signs = [
        "cloudflare", "imperva", "datadome",
        "recaptcha", "hcaptcha", "turnstile"
    ]
    
    html_lower = html.lower()
    if any(sign in html_lower for sign in bot_detection_signs):
        return True
    
    # Known protected domains
    protected_domains = [
        "amazon", "ebay", "walmart", "target",
        "alibaba", "flipkart"
    ]
    
    if any(domain in url.lower() for domain in protected_domains):
        return True
    
    return False


def get_rendering_strategy(url: str, html: str) -> Dict[str, any]:
    """
    Get complete rendering strategy for a URL
    
    Returns:
        Dict with all rendering parameters
    """
    
    domain, domain_config = get_domain_info(url)
    metrics = analyze_html_structure(html)
    
    strategy = {
        "needs_js": needs_js(html, url),
        "wait_time": get_wait_time(url, html),
        "stealth_mode": should_use_stealth(url, html),
        "block_resources": True,  # Always block for speed
        "use_cache": True,        # Always cache for efficiency
        "domain": domain,
        "reason": domain_config.get("reason", "Automatic detection"),
        "metrics": metrics
    }
    
    return strategy


def html_requires_js(html: str, url: str = "") -> bool:
    """
    Backward compatible function
    (Used in your main.py)
    """
    return needs_js(html, url)


# Testing and debugging utilities
def explain_decision(url: str, html: str) -> str:
    """
    Get human-readable explanation of rendering decision
    Useful for debugging and optimization
    """
    
    strategy = get_rendering_strategy(url, html)
    
    explanation = f"""
🔍 Rendering Analysis for: {url}

📊 HTML Metrics:
  - Length: {strategy['metrics']['length']:,} chars
  - Scripts: {strategy['metrics']['script_count']}
  - Framework: {strategy['metrics']['framework_type'] or 'None'}
  - Has Content: {strategy['metrics']['has_content']}
  - Text Ratio: {strategy['metrics']['text_ratio']:.2%}
  - Protection: {strategy['metrics']['has_protection']}

🎯 Decision:
  - Needs JS: {'✅ YES' if strategy['needs_js'] else '❌ NO'}
  - Wait Time: {strategy['wait_time']}s
  - Stealth Mode: {'✅ YES' if strategy['stealth_mode'] else '❌ NO'}
  - Reason: {strategy['reason']}
"""
    
    return explanation.strip()
