"""
Adaptive Learning System for Web Scraping
Success rates learn from actual results per domain
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from datetime import datetime, timedelta
import math


@dataclass
class AttemptRecord:
    """Single attempt record"""
    timestamp: float
    protection_type: str
    success: bool
    response_time: float
    technique_used: str
    error_type: Optional[str] = None


@dataclass
class DomainStats:
    """Statistics for a domain"""
    domain: str
    total_attempts: int
    successful_attempts: int
    failed_attempts: int
    success_rate: float
    last_attempt: float
    protection_types: Dict[str, int]  # Count of each protection type seen
    avg_response_time: float
    best_technique: Optional[str] = None


class AdaptiveLearner:
    """
    Learn from scraping attempts and adapt success rates
    
    Features:
    - Per-domain learning
    - Per-protection-type learning
    - Time-decay (old data matters less)
    - Technique effectiveness tracking
    - Automatic strategy adjustment
    """
    
    def __init__(self, persistence_file: str = "scraping_knowledge.json"):
        self.persistence_file = persistence_file
        
        # Domain-level tracking
        self.domain_history: Dict[str, List[AttemptRecord]] = defaultdict(list)
        self.domain_stats: Dict[str, DomainStats] = {}
        
        # Protection-type level tracking (global)
        self.protection_stats: Dict[str, Dict] = defaultdict(lambda: {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "success_rate": 0.5,
            "last_updated": time.time()
        })
        
        # Technique effectiveness (which technique works best for each protection)
        self.technique_effectiveness: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Load previous knowledge
        self.load_knowledge()
    
    
    # ========================================================================
    # RECORDING ATTEMPTS
    # ========================================================================
    
    def record_attempt(
        self,
        domain: str,
        protection_type: str,
        technique_used: str,
        success: bool,
        response_time: float,
        error_type: Optional[str] = None
    ):
        """
        Record a scraping attempt
        
        This is the main method you'll call after each scrape
        """
        
        record = AttemptRecord(
            timestamp=time.time(),
            protection_type=protection_type,
            success=success,
            response_time=response_time,
            technique_used=technique_used,
            error_type=error_type
        )
        
        # Add to domain history
        self.domain_history[domain].append(record)
        
        # Update domain stats
        self._update_domain_stats(domain)
        
        # Update protection-type stats (global)
        self._update_protection_stats(protection_type, success)
        
        # Update technique effectiveness
        self._update_technique_effectiveness(protection_type, technique_used, success)
        
        # Persist knowledge
        self.save_knowledge()
    
    
    def _update_domain_stats(self, domain: str):
        """Recalculate stats for a domain"""
        history = self.domain_history[domain]
        
        if not history:
            return
        
        # Filter recent history (last 30 days)
        cutoff = time.time() - (30 * 24 * 60 * 60)
        recent = [r for r in history if r.timestamp > cutoff]
        
        if not recent:
            recent = history[-50:]  # At least last 50 attempts
        
        total = len(recent)
        successes = sum(1 for r in recent if r.success)
        failures = total - successes
        
        # Calculate success rate with time decay
        success_rate = self._calculate_time_weighted_success_rate(recent)
        
        # Find most common protection type
        protection_counts = defaultdict(int)
        for r in recent:
            protection_counts[r.protection_type] += 1
        
        # Average response time
        avg_response = sum(r.response_time for r in recent) / len(recent)
        
        # Find best technique
        technique_success = defaultdict(lambda: {"success": 0, "total": 0})
        for r in recent:
            technique_success[r.technique_used]["total"] += 1
            if r.success:
                technique_success[r.technique_used]["success"] += 1
        
        best_technique = None
        best_rate = 0.0
        for tech, stats in technique_success.items():
            rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            if rate > best_rate and stats["total"] >= 3:  # At least 3 attempts
                best_rate = rate
                best_technique = tech
        
        # Store stats
        self.domain_stats[domain] = DomainStats(
            domain=domain,
            total_attempts=total,
            successful_attempts=successes,
            failed_attempts=failures,
            success_rate=success_rate,
            last_attempt=recent[-1].timestamp,
            protection_types=dict(protection_counts),
            avg_response_time=avg_response,
            best_technique=best_technique
        )
    
    
    def _calculate_time_weighted_success_rate(self, records: List[AttemptRecord]) -> float:
        """
        Calculate success rate with exponential time decay
        Recent attempts matter more than old ones
        """
        
        if not records:
            return 0.5
        
        now = time.time()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        # Decay factor: half-life of 7 days
        half_life = 7 * 24 * 60 * 60  # 7 days in seconds
        
        for record in records:
            age = now - record.timestamp
            
            # Exponential decay: weight = 2^(-age/half_life)
            weight = math.exp(-age / half_life * math.log(2))
            
            weighted_sum += (1.0 if record.success else 0.0) * weight
            weight_sum += weight
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.5
    
    
    def _update_protection_stats(self, protection_type: str, success: bool):
        """Update global stats for a protection type"""
        stats = self.protection_stats[protection_type]
        
        stats["attempts"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        
        # Recalculate success rate
        stats["success_rate"] = stats["successes"] / stats["attempts"]
        stats["last_updated"] = time.time()
    
    
    def _update_technique_effectiveness(self, protection_type: str, technique: str, success: bool):
        """Track which techniques work best for each protection type"""
        
        current = self.technique_effectiveness[protection_type][technique]
        
        # Moving average: new_avg = old_avg * 0.9 + new_result * 0.1
        new_value = 1.0 if success else 0.0
        
        if current == 0.0:
            # First data point
            self.technique_effectiveness[protection_type][technique] = new_value
        else:
            # Exponential moving average
            self.technique_effectiveness[protection_type][technique] = current * 0.9 + new_value * 0.1
    
    
    # ========================================================================
    # GETTING LEARNED RATES
    # ========================================================================
    
    def get_success_rate(
        self,
        domain: str,
        protection_type: str,
        base_rate: float = 0.5
    ) -> float:
        """
        Get learned success rate for domain + protection type
        
        Returns a rate between 0.0 and 1.0
        Falls back to global rate if no domain-specific data
        """
        
        # Check domain-specific data
        if domain in self.domain_stats:
            stats = self.domain_stats[domain]
            
            # If this protection type was seen on this domain
            if protection_type in stats.protection_types:
                # Use domain-specific rate
                return stats.success_rate
        
        # Fall back to global protection type stats
        if protection_type in self.protection_stats:
            return self.protection_stats[protection_type]["success_rate"]
        
        # No data, use base rate
        return base_rate
    
    
    def get_best_technique(
        self,
        domain: str,
        protection_type: str,
        default: str = "playwright_stealth"
    ) -> str:
        """
        Get the best technique for a domain + protection type
        """
        
        # Check domain-specific best
        if domain in self.domain_stats:
            best = self.domain_stats[domain].best_technique
            if best:
                return best
        
        # Check global technique effectiveness
        if protection_type in self.technique_effectiveness:
            techniques = self.technique_effectiveness[protection_type]
            if techniques:
                best_tech = max(techniques.items(), key=lambda x: x[1])
                if best_tech[1] > 0.3:  # At least 30% success rate
                    return best_tech[0]
        
        return default
    
    
    def should_retry(
        self,
        domain: str,
        protection_type: str,
        current_attempts: int,
        max_attempts: int = 5
    ) -> Tuple[bool, str]:
        """
        Decide if we should retry based on learned data
        
        Returns:
            (should_retry: bool, reason: str)
        """
        
        # Never exceed max attempts
        if current_attempts >= max_attempts:
            return False, "max_attempts_reached"
        
        # Get learned success rate
        success_rate = self.get_success_rate(domain, protection_type)
        
        # If success rate is very low, give up early
        if success_rate < 0.1 and current_attempts >= 2:
            return False, "learned_low_success_rate"
        
        # If we've never succeeded on this domain+protection, give up after 3
        if domain in self.domain_stats:
            if self.domain_stats[domain].successful_attempts == 0 and current_attempts >= 3:
                return False, "never_succeeded_before"
        
        # Otherwise, keep trying
        return True, "worth_retrying"
    
    
    def get_recommended_wait_time(
        self,
        domain: str,
        protection_type: str,
        attempt_number: int
    ) -> float:
        """
        Get recommended wait time based on learned data
        Uses exponential backoff adjusted by success rate
        """
        
        # Base wait time (exponential backoff)
        base_wait = min(2 ** attempt_number, 30)  # Cap at 30 seconds
        
        # Adjust based on success rate
        success_rate = self.get_success_rate(domain, protection_type, 0.5)
        
        # If low success rate, wait longer
        if success_rate < 0.3:
            multiplier = 2.0
        elif success_rate < 0.6:
            multiplier = 1.5
        else:
            multiplier = 1.0
        
        return base_wait * multiplier
    
    
    # ========================================================================
    # REPORTING & ANALYTICS
    # ========================================================================
    
    def get_domain_report(self, domain: str) -> Optional[Dict]:
        """Get detailed report for a domain"""
        
        if domain not in self.domain_stats:
            return None
        
        stats = self.domain_stats[domain]
        history = self.domain_history[domain]
        
        # Calculate trends
        recent_7d = [r for r in history if r.timestamp > time.time() - (7 * 24 * 60 * 60)]
        recent_30d = [r for r in history if r.timestamp > time.time() - (30 * 24 * 60 * 60)]
        
        success_rate_7d = sum(1 for r in recent_7d if r.success) / len(recent_7d) if recent_7d else 0
        success_rate_30d = sum(1 for r in recent_30d if r.success) / len(recent_30d) if recent_30d else 0
        
        return {
            "domain": domain,
            "overall_stats": asdict(stats),
            "trends": {
                "7_day_success_rate": success_rate_7d,
                "30_day_success_rate": success_rate_30d,
                "trend": "improving" if success_rate_7d > success_rate_30d else "declining"
            },
            "recent_attempts": len(recent_7d),
            "last_attempt": datetime.fromtimestamp(stats.last_attempt).isoformat()
        }
    
    
    def get_global_report(self) -> Dict:
        """Get global statistics across all domains"""
        
        total_domains = len(self.domain_stats)
        total_attempts = sum(s.total_attempts for s in self.domain_stats.values())
        total_successes = sum(s.successful_attempts for s in self.domain_stats.values())
        
        overall_rate = total_successes / total_attempts if total_attempts > 0 else 0
        
        # Top performing domains
        top_domains = sorted(
            self.domain_stats.values(),
            key=lambda s: s.success_rate,
            reverse=True
        )[:10]
        
        # Worst performing domains
        worst_domains = sorted(
            self.domain_stats.values(),
            key=lambda s: s.success_rate
        )[:10]
        
        # Protection type breakdown
        protection_breakdown = {}
        for ptype, stats in self.protection_stats.items():
            protection_breakdown[ptype] = {
                "attempts": stats["attempts"],
                "success_rate": stats["success_rate"],
                "last_seen": datetime.fromtimestamp(stats["last_updated"]).isoformat()
            }
        
        # Best techniques
        best_techniques = {}
        for ptype, techniques in self.technique_effectiveness.items():
            best = max(techniques.items(), key=lambda x: x[1]) if techniques else None
            if best:
                best_techniques[ptype] = {"technique": best[0], "effectiveness": best[1]}
        
        return {
            "total_domains": total_domains,
            "total_attempts": total_attempts,
            "total_successes": total_successes,
            "overall_success_rate": overall_rate,
            "top_domains": [{"domain": d.domain, "rate": d.success_rate} for d in top_domains],
            "worst_domains": [{"domain": d.domain, "rate": d.success_rate} for d in worst_domains],
            "protection_types": protection_breakdown,
            "best_techniques": best_techniques
        }
    
    
    # ========================================================================
    # PERSISTENCE
    # ========================================================================
    
    def save_knowledge(self):
        """Save learned knowledge to disk"""
        
        data = {
            "domain_stats": {k: asdict(v) for k, v in self.domain_stats.items()},
            "protection_stats": dict(self.protection_stats),
            "technique_effectiveness": {
                k: dict(v) for k, v in self.technique_effectiveness.items()
            },
            "saved_at": time.time()
        }
        
        try:
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save knowledge: {e}")
    
    
    def load_knowledge(self):
        """Load previously learned knowledge"""
        
        try:
            with open(self.persistence_file, 'r') as f:
                data = json.load(f)
            
            # Load domain stats
            for domain, stats_dict in data.get("domain_stats", {}).items():
                self.domain_stats[domain] = DomainStats(**stats_dict)
            
            # Load protection stats
            self.protection_stats = defaultdict(
                lambda: {"attempts": 0, "successes": 0, "failures": 0, "success_rate": 0.5, "last_updated": time.time()},
                data.get("protection_stats", {})
            )
            
            # Load technique effectiveness
            for ptype, techniques in data.get("technique_effectiveness", {}).items():
                self.technique_effectiveness[ptype] = defaultdict(float, techniques)
            
            print(f"✅ Loaded knowledge: {len(self.domain_stats)} domains")
        
        except FileNotFoundError:
            print("📝 No previous knowledge found, starting fresh")
        except Exception as e:
            print(f"⚠️ Failed to load knowledge: {e}")