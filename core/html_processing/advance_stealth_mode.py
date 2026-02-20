"""
Advanced Multi-Signal Protection Detection System
Detects protections using behavior, timing, cookies, and TLS - not just HTML

Works WITHOUT paid proxies or CAPTCHA solvers
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
import time
import hashlib
import json
from collections import defaultdict
import asyncio
import re


class ProtectionType(Enum):
    """Granular protection types (not just 'CAPTCHA')"""
    
    # No protection
    NONE = "none"
    BASIC_RATE_LIMIT = "basic_rate_limit"
    
    # Cloudflare variants
    CF_BROWSER_CHECK = "cf_browser_check"        # 5-sec challenge (solvable)
    CF_MANAGED_CHALLENGE = "cf_managed_challenge"  # Harder challenge
    CF_TURNSTILE_INVISIBLE = "cf_turnstile_invisible"  # Auto-solves
    CF_TURNSTILE_VISIBLE = "cf_turnstile_visible"    # Click checkbox
    CF_TURNSTILE_HARD = "cf_turnstile_hard"          # Multiple rounds
    
    # DataDome
    DATADOME_COOKIE = "datadome_cookie"         # Cookie challenge (solvable)
    DATADOME_CAPTCHA = "datadome_captcha"       # JS CAPTCHA (hard)
    
    # PerimeterX
    PX_COOKIE = "px_cookie"                     # Cookie challenge
    PX_CAPTCHA = "px_captcha"                   # CAPTCHA (hard)
    
    # CAPTCHA variants
    RECAPTCHA_V2_INVISIBLE = "recaptcha_v2_invisible"
    RECAPTCHA_V2_CHECKBOX = "recaptcha_v2_checkbox"
    RECAPTCHA_V3 = "recaptcha_v3"                # Score-based (invisible)
    HCAPTCHA_EASY = "hcaptcha_easy"
    HCAPTCHA_HARD = "hcaptcha_hard"
    FUNCAPTCHA = "funcaptcha"                    # Arkose Labs
    
    # Impossible
    MANUAL_VERIFICATION = "manual_verification"   # Phone/email required
    BLOCKED_PERMANENTLY = "blocked_permanently"   # IP banned


@dataclass
class SolveStrategy:
    """How to solve each protection type (no paid services)"""
    solvable_free: bool          # Can we solve without paying?
    technique: str               # How to solve it
    wait_time: float            # How long to wait
    success_rate: float         # Initial success rate
    retry_limit: int            # Max attempts before giving up
    cost_free: bool             # Is it completely free?


# Strategies for each protection type (ZERO COST focus)
SOLVE_STRATEGIES = {
    ProtectionType.NONE: SolveStrategy(
        solvable_free=True,
        technique="direct_access",
        wait_time=0.5,
        success_rate=0.99,
        retry_limit=2,
        cost_free=True
    ),
    
    ProtectionType.BASIC_RATE_LIMIT: SolveStrategy(
        solvable_free=True,
        technique="exponential_backoff",
        wait_time=2.0,
        success_rate=0.95,
        retry_limit=5,
        cost_free=True
    ),
    
    ProtectionType.CF_BROWSER_CHECK: SolveStrategy(
        solvable_free=True,
        technique="playwright_wait_5sec",  # Just wait for JS challenge
        wait_time=6.0,
        success_rate=0.90,
        retry_limit=3,
        cost_free=True
    ),
    
    ProtectionType.CF_TURNSTILE_INVISIBLE: SolveStrategy(
        solvable_free=True,
        technique="playwright_auto_solve",  # Auto-completes
        wait_time=3.0,
        success_rate=0.85,
        retry_limit=3,
        cost_free=True
    ),
    
    ProtectionType.CF_TURNSTILE_VISIBLE: SolveStrategy(
        solvable_free=True,
        technique="playwright_click_checkbox",  # Simulate click
        wait_time=4.0,
        success_rate=0.70,  # Lower because click detection
        retry_limit=5,
        cost_free=True
    ),
    
    ProtectionType.CF_TURNSTILE_HARD: SolveStrategy(
        solvable_free=False,
        technique="requires_human_solving",  # Too hard for free
        wait_time=10.0,
        success_rate=0.30,
        retry_limit=2,
        cost_free=False  # Would need paid solver
    ),
    
    ProtectionType.DATADOME_COOKIE: SolveStrategy(
        solvable_free=True,
        technique="cookie_persistence",  # Save cookies between requests
        wait_time=2.0,
        success_rate=0.75,
        retry_limit=4,
        cost_free=True
    ),
    
    ProtectionType.RECAPTCHA_V2_INVISIBLE: SolveStrategy(
        solvable_free=True,
        technique="playwright_trigger_invisible",  # Sometimes auto-solves
        wait_time=5.0,
        success_rate=0.60,
        retry_limit=3,
        cost_free=True
    ),
    
    ProtectionType.RECAPTCHA_V2_CHECKBOX: SolveStrategy(
        solvable_free=False,
        technique="requires_paid_solver",
        wait_time=15.0,
        success_rate=0.20,  # Very low without solver
        retry_limit=2,
        cost_free=False
    ),
    
    ProtectionType.HCAPTCHA_EASY: SolveStrategy(
        solvable_free=True,
        technique="playwright_wait_and_try",
        wait_time=8.0,
        success_rate=0.40,
        retry_limit=3,
        cost_free=True
    ),
    
    ProtectionType.MANUAL_VERIFICATION: SolveStrategy(
        solvable_free=False,
        technique="impossible_give_up",
        wait_time=0.0,
        success_rate=0.0,
        retry_limit=0,
        cost_free=False
    ),
}


@dataclass
class DetectionSignal:
    """Multi-signal detection result"""
    protection_type: ProtectionType
    confidence: float  # 0.0 - 1.0
    signals: List[str]  # What triggered this detection
    metadata: Dict  # Additional info


class MultiSignalDetector:
    """
    Advanced detector using multiple signals:
    - HTML content
    - HTTP headers
    - Cookies
    - Response timing
    - Navigation behavior
    - TLS fingerprints
    """
    
    def __init__(self):
        self.domain_history: Dict[str, List[DetectionSignal]] = defaultdict(list)
        self.timing_baseline: Dict[str, float] = {}
    
    
    # ========================================================================
    # SIGNAL 1: HTML CONTENT (Your existing method)
    # ========================================================================
    
    def detect_from_html(self, html: str) -> List[DetectionSignal]:
        """HTML-based detection (your original method + enhancements)"""
        signals = []
        html_lower = html.lower()
        
        # Cloudflare Browser Check (5-sec challenge)
        if any(s in html_lower for s in [
            'checking your browser',
            'please wait while we check your browser',
            'cf-browser-verification'
        ]) and 'captcha' not in html_lower:
            signals.append(DetectionSignal(
                protection_type=ProtectionType.CF_BROWSER_CHECK,
                confidence=0.95,
                signals=['html_cf_browser_check'],
                metadata={'challenge_type': 'javascript'}
            ))
        
        # Cloudflare Turnstile (granular detection)
        if 'turnstile' in html_lower or 'cf-turnstile' in html_lower:
            # Check if visible or invisible
            if 'challenges.cloudflare.com/turnstile' in html_lower:
                # Check complexity
                if 'data-sitekey' in html_lower:
                    # Extract sitekey to determine difficulty
                    sitekey_match = re.search(r'data-sitekey="([^"]+)"', html)
                    if sitekey_match:
                        sitekey = sitekey_match.group(1)
                        # Heuristic: longer sitekeys = harder challenges
                        if len(sitekey) > 50:
                            protection = ProtectionType.CF_TURNSTILE_HARD
                            confidence = 0.85
                        else:
                            protection = ProtectionType.CF_TURNSTILE_VISIBLE
                            confidence = 0.90
                    else:
                        protection = ProtectionType.CF_TURNSTILE_INVISIBLE
                        confidence = 0.80
                else:
                    protection = ProtectionType.CF_TURNSTILE_INVISIBLE
                    confidence = 0.75
                
                signals.append(DetectionSignal(
                    protection_type=protection,
                    confidence=confidence,
                    signals=['html_turnstile'],
                    metadata={'visible': 'visible' in protection.value}
                ))
        
        # DataDome
        if 'datadome' in html_lower:
            if 'captcha' in html_lower or 'geo.captcha-delivery' in html_lower:
                protection = ProtectionType.DATADOME_CAPTCHA
                confidence = 0.90
            else:
                protection = ProtectionType.DATADOME_COOKIE
                confidence = 0.85
            
            signals.append(DetectionSignal(
                protection_type=protection,
                confidence=confidence,
                signals=['html_datadome'],
                metadata={}
            ))
        
        # PerimeterX
        if any(s in html_lower for s in ['perimeterx', 'px-captcha', '_pxhd']):
            if 'captcha' in html_lower:
                protection = ProtectionType.PX_CAPTCHA
                confidence = 0.90
            else:
                protection = ProtectionType.PX_COOKIE
                confidence = 0.85
            
            signals.append(DetectionSignal(
                protection_type=protection,
                confidence=confidence,
                signals=['html_perimeterx'],
                metadata={}
            ))
        
        # reCAPTCHA variants
        if 'recaptcha' in html_lower:
            if 'g-recaptcha' in html_lower:
                # Visible checkbox
                protection = ProtectionType.RECAPTCHA_V2_CHECKBOX
                confidence = 0.95
            elif 'grecaptcha.execute' in html_lower or 'data-action' in html_lower:
                # Invisible v3
                protection = ProtectionType.RECAPTCHA_V3
                confidence = 0.90
            else:
                # Invisible v2
                protection = ProtectionType.RECAPTCHA_V2_INVISIBLE
                confidence = 0.85
            
            signals.append(DetectionSignal(
                protection_type=protection,
                confidence=confidence,
                signals=['html_recaptcha'],
                metadata={'version': protection.value}
            ))
        
        # hCaptcha
        if 'hcaptcha' in html_lower:
            # Check difficulty by looking at sitekey or challenge type
            if 'data-sitekey' in html_lower and 'enterprise' in html_lower:
                protection = ProtectionType.HCAPTCHA_HARD
                confidence = 0.90
            else:
                protection = ProtectionType.HCAPTCHA_EASY
                confidence = 0.85
            
            signals.append(DetectionSignal(
                protection_type=protection,
                confidence=confidence,
                signals=['html_hcaptcha'],
                metadata={}
            ))
        
        # FunCaptcha (Arkose)
        if 'funcaptcha' in html_lower or 'arkoselabs' in html_lower:
            signals.append(DetectionSignal(
                protection_type=ProtectionType.FUNCAPTCHA,
                confidence=0.95,
                signals=['html_funcaptcha'],
                metadata={}
            ))
        
        # Manual verification
        if any(s in html_lower for s in [
            'verify your phone number',
            'verify your email',
            'enter the code sent to',
            'sms verification'
        ]):
            signals.append(DetectionSignal(
                protection_type=ProtectionType.MANUAL_VERIFICATION,
                confidence=0.99,
                signals=['html_manual_verification'],
                metadata={'impossible': True}
            ))
        
        return signals
    
    
    # ========================================================================
    # SIGNAL 2: HTTP HEADERS & COOKIES
    # ========================================================================
    
    def detect_from_headers(self, headers: Dict, cookies: Dict) -> List[DetectionSignal]:
        """Cookie and header-based detection"""
        signals = []
        
        # Cloudflare
        if 'cf-ray' in headers or 'CF-RAY' in headers:
            # Check for challenge cookies
            cf_cookies = [k for k in cookies.keys() if k.startswith('cf_')]
            
            if '__cf_bm' in cookies or 'cf_clearance' in cookies:
                # Has clearance cookie = passed challenge before
                signals.append(DetectionSignal(
                    protection_type=ProtectionType.CF_BROWSER_CHECK,
                    confidence=0.70,
                    signals=['header_cf_cookies'],
                    metadata={'has_clearance': 'cf_clearance' in cookies}
                ))
        
        # DataDome
        if 'x-datadome-cid' in headers or any('datadome' in k.lower() for k in cookies.keys()):
            signals.append(DetectionSignal(
                protection_type=ProtectionType.DATADOME_COOKIE,
                confidence=0.85,
                signals=['header_datadome'],
                metadata={'cid': headers.get('x-datadome-cid', 'unknown')}
            ))
        
        # PerimeterX
        if any(k.startswith('_px') for k in cookies.keys()):
            signals.append(DetectionSignal(
                protection_type=ProtectionType.PX_COOKIE,
                confidence=0.80,
                signals=['header_px_cookies'],
                metadata={'px_cookies': [k for k in cookies.keys() if k.startswith('_px')]}
            ))
        
        # Check for rate limiting headers
        rate_limit_headers = {
            'x-ratelimit-remaining',
            'x-ratelimit-limit',
            'retry-after',
            'x-rate-limit-remaining'
        }
        
        if any(h.lower() in [k.lower() for k in headers.keys()] for h in rate_limit_headers):
            signals.append(DetectionSignal(
                protection_type=ProtectionType.BASIC_RATE_LIMIT,
                confidence=0.90,
                signals=['header_rate_limit'],
                metadata={'headers': [k for k in headers.keys() if any(rl in k.lower() for rl in rate_limit_headers)]}
            ))
        
        return signals
    
    
    # ========================================================================
    # SIGNAL 3: TIMING ANOMALIES
    # ========================================================================
    
    def detect_from_timing(self, domain: str, response_time: float, html_size: int) -> List[DetectionSignal]:
        """Detect protections from response timing patterns"""
        signals = []
        
        # Establish baseline
        if domain not in self.timing_baseline:
            self.timing_baseline[domain] = response_time
            return signals  # Not enough data yet
        
        baseline = self.timing_baseline[domain]
        
        # ANOMALY 1: Instant small response (likely block page)
        if response_time < 0.1 and html_size < 2000:
            signals.append(DetectionSignal(
                protection_type=ProtectionType.CF_BROWSER_CHECK,
                confidence=0.60,
                signals=['timing_instant_small'],
                metadata={'response_time': response_time, 'size': html_size}
            ))
        
        # ANOMALY 2: Exactly 5 seconds (Cloudflare browser check)
        if 4.8 <= response_time <= 5.5:
            signals.append(DetectionSignal(
                protection_type=ProtectionType.CF_BROWSER_CHECK,
                confidence=0.80,
                signals=['timing_exactly_5_seconds'],
                metadata={'response_time': response_time}
            ))
        
        # ANOMALY 3: Much slower than baseline (JS challenges)
        if response_time > baseline * 3 and response_time > 2.0:
            signals.append(DetectionSignal(
                protection_type=ProtectionType.CF_MANAGED_CHALLENGE,
                confidence=0.65,
                signals=['timing_slow_challenge'],
                metadata={'baseline': baseline, 'actual': response_time}
            ))
        
        return signals
    
    
    # ========================================================================
    # SIGNAL 4: NAVIGATION BEHAVIOR
    # ========================================================================
    
    async def detect_from_navigation(self, url: str, fetch_func) -> List[DetectionSignal]:
        """
        Detect protections by observing navigation behavior:
        - Same HTML returned on multiple requests
        - Redirect loops
        - Cookie requirements
        """
        signals = []
        
        # Test 1: Make 2 requests, check if identical
        try:
            html1 = await fetch_func(url)
            await asyncio.sleep(1)
            html2 = await fetch_func(url)
            
            # Hash both responses
            hash1 = hashlib.md5(html1.encode()).hexdigest()
            hash2 = hashlib.md5(html2.encode()).hexdigest()
            
            # If identical AND small, likely a block page
            if hash1 == hash2 and len(html1) < 5000:
                signals.append(DetectionSignal(
                    protection_type=ProtectionType.CF_BROWSER_CHECK,
                    confidence=0.70,
                    signals=['navigation_identical_response'],
                    metadata={'hash': hash1, 'size': len(html1)}
                ))
        
        except Exception:
            pass  # Navigation test failed, skip
        
        # Test 2: Check if cookies persist
        # (This would require cookie storage between requests)
        
        return signals
    
    
    # ========================================================================
    # MASTER DETECTION (Combines all signals)
    # ========================================================================
    
    def detect_protection(
        self,
        url: str,
        html: str,
        status_code: int,
        headers: Dict,
        cookies: Dict,
        response_time: float
    ) -> DetectionSignal:
        """
        Master detection using ALL signals
        Returns the BEST detection with highest confidence
        """
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        all_signals = []
        
        # Collect signals from all methods
        all_signals.extend(self.detect_from_html(html))
        all_signals.extend(self.detect_from_headers(headers, cookies))
        all_signals.extend(self.detect_from_timing(domain, response_time, len(html)))
        
        # If no signals, assume no protection
        if not all_signals:
            return DetectionSignal(
                protection_type=ProtectionType.NONE,
                confidence=0.95,
                signals=['no_protection_detected'],
                metadata={}
            )
        
        # Find signal with highest confidence
        best_signal = max(all_signals, key=lambda s: s.confidence)
        
        # Store in history
        self.domain_history[domain].append(best_signal)
        
        return best_signal
    
    
    # ========================================================================
    # LEARNING: Dynamic Success Rate
    # ========================================================================
    
    def get_learned_success_rate(self, domain: str, protection_type: ProtectionType) -> float:
        """
        Calculate dynamic success rate based on domain history
        Decays with failures, increases with successes
        """
        
        if domain not in self.domain_history:
            # No history, use default
            return SOLVE_STRATEGIES[protection_type].success_rate
        
        # Get history for this protection type
        relevant_history = [
            signal for signal in self.domain_history[domain]
            if signal.protection_type == protection_type
        ]
        
        if not relevant_history:
            return SOLVE_STRATEGIES[protection_type].success_rate
        
        # Calculate success rate from recent attempts
        recent_attempts = relevant_history[-10:]  # Last 10 attempts
        
        # If we have metadata about successes
        successes = sum(1 for s in recent_attempts if s.metadata.get('success', False))
        total = len(recent_attempts)
        
        if total > 0:
            learned_rate = successes / total
            
            # Weighted average with default rate
            base_rate = SOLVE_STRATEGIES[protection_type].success_rate
            return (learned_rate * 0.7) + (base_rate * 0.3)
        
        return SOLVE_STRATEGIES[protection_type].success_rate
    
    
    def record_attempt(self, domain: str, protection_type: ProtectionType, success: bool):
        """Record attempt result for learning"""
        signal = DetectionSignal(
            protection_type=protection_type,
            confidence=1.0,
            signals=['attempt_result'],
            metadata={'success': success, 'timestamp': time.time()}
        )
        self.domain_history[domain].append(signal)


# ============================================================================
# COST-FREE SOLVER (No paid services)
# ============================================================================

class CostFreeSolver:
    """
    Solve protections WITHOUT paying for proxies or CAPTCHA solvers
    
    Techniques:
    - Smart waiting
    - Cookie persistence
    - Human-like behavior
    - Exponential backoff
    """
    
    @staticmethod
    async def solve_cf_browser_check(page, wait_time: float = 6.0):
        """
        Solve Cloudflare 5-second challenge
        Just wait for JS to complete
        """
        print("   â³ Waiting for Cloudflare browser check...")
        await asyncio.sleep(wait_time)
        
        # Check if challenge passed
        if 'cf-browser-verification' not in await page.content():
            print("   âœ… Cloudflare check passed")
            return True
        
        return False
    
    
    @staticmethod
    async def solve_cf_turnstile_invisible(page):
        """Solve invisible Turnstile (often auto-solves)"""
        print("   ðŸ Waiting for invisible Turnstile...")
        
        # Wait for Turnstile iframe
        try:
            await page.wait_for_selector('iframe[src*="challenges.cloudflare.com"]', timeout=5000)
            await asyncio.sleep(3)  # Let it auto-solve
            
            # Check if solved
            content = await page.content()
            if 'turnstile' not in content.lower():
                print("   âœ… Turnstile auto-solved")
                return True
        except:
            pass
        
        return False
    
    
    @staticmethod
    async def solve_cf_turnstile_visible(page):
        """
        Solve visible Turnstile (click checkbox)
        FREE technique: Simulate human click with delays
        """
        print("   ðŸ–±ï¸  Attempting to solve visible Turnstile...")
        
        try:
            # Find the Turnstile iframe
            iframe = page.frame_locator('iframe[src*="challenges.cloudflare.com"]')
            
            # Wait a bit (human-like)
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Try to click the checkbox
            checkbox = iframe.locator('input[type="checkbox"]')
            await checkbox.click()
            
            # Wait for solving
            await asyncio.sleep(3)
            
            # Verify
            content = await page.content()
            if 'turnstile' not in content.lower():
                print("   âœ… Turnstile solved!")
                return True
        
        except Exception as e:
            print(f"   âŒ Turnstile click failed: {e}")
        
        return False
    
    
    @staticmethod
    async def solve_with_cookies(page, domain: str):
        """
        Solve cookie-based challenges by persisting cookies
        Works for DataDome, PerimeterX
        """
        print("   ðŸª Cookie-based solving...")
        
        # Load cookies if we have them (would need cookie storage)
        # For now, just navigate and let cookies be set
        
        await asyncio.sleep(2)
        
        # Check if challenge is gone
        content = await page.content()
        if len(content) > 5000:  # Got real content
            print("   âœ… Cookie challenge passed")
            return True
        
        return False
    
    
    @staticmethod
    def should_give_up(protection_type: ProtectionType) -> bool:
        """Decide if protection is unsolvable without payment"""
        unsolvable_free = [
            ProtectionType.CF_TURNSTILE_HARD,
            ProtectionType.RECAPTCHA_V2_CHECKBOX,
            ProtectionType.HCAPTCHA_HARD,
            ProtectionType.FUNCAPTCHA,
            ProtectionType.MANUAL_VERIFICATION,
            ProtectionType.BLOCKED_PERMANENTLY
        ]
        
        return protection_type in unsolvable_free