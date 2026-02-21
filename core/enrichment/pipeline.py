"""
Enrichment Pipeline for ScrapiGen
Orchestrates: analyze (stats only) and enrich (normalize + deduplicate)
"""

from typing import List, Dict
from .normalizers import normalize_data, count_normalization_issues
from .deduplication import deduplicate_data, count_duplicates


def analyze(data: List[Dict]) -> Dict:
    """
    Analyze raw data and return stats WITHOUT modifying anything.
    
    This powers the stats block shown to the user before they click "Clean Data".
    
    Returns:
        {
            "total_records": 5,
            "duplicates_found": 2,
            "phones_to_fix": 3,
            "emails_to_fix": 1,
            "urls_to_fix": 2,
            "total_issues": 8
        }
    """
    norm_stats = count_normalization_issues(data)
    dup_count = count_duplicates(data)
    
    total_issues = dup_count + sum(norm_stats.values())
    
    return {
        "total_records": len(data),
        "duplicates_found": dup_count,
        "phones_to_fix": norm_stats["phones_to_fix"],
        "emails_to_fix": norm_stats["emails_to_fix"],
        "urls_to_fix": norm_stats["urls_to_fix"],
        "total_issues": total_issues
    }


def enrich(data: List[Dict], stages: List[str] = None) -> Dict:
    """
    Run enrichment stages on the data.
    
    Default stages: ["normalize", "deduplicate"]
    
    Returns:
        {
            "data": [...cleaned records...],
            "stages_applied": ["normalize", "deduplicate"],
            "original_count": 5,
            "enriched_count": 3,
            "duplicates_removed": 2
        }
    """
    if stages is None:
        stages = ["normalize", "deduplicate"]
    
    result_data = list(data)  # shallow copy
    applied = []
    duplicates_removed = 0
    
    if "normalize" in stages:
        result_data = normalize_data(result_data)
        applied.append("normalize")
    
    if "deduplicate" in stages:
        result_data, duplicates_removed = deduplicate_data(result_data)
        applied.append("deduplicate")
    
    return {
        "data": result_data,
        "stages_applied": applied,
        "original_count": len(data),
        "enriched_count": len(result_data),
        "duplicates_removed": duplicates_removed
    }
