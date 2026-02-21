"""
Deduplication for ScrapiGen Enrichment Pipeline
Detects and merges duplicate records based on shared phone/email/website
"""

from typing import List, Dict, Any, Set, Tuple


# Fields used to detect duplicates
_DEDUP_KEYS = {"phone", "phones", "email", "emails", "website", "websites",
               "telephone", "tel", "mobile", "e-mail", "mail", "url", "site",
               "phone_number", "email_address", "contact_phone", "contact_email"}


def _extract_fingerprints(record: Dict) -> Set[str]:
    """
    Build a set of identity fingerprints from a record.
    Each non-empty phone/email/website value becomes a fingerprint.
    """
    fingerprints = set()
    
    if not isinstance(record, dict):
        return fingerprints
    
    for key, value in record.items():
        key_lower = key.lower().replace(" ", "_").replace("-", "_")
        if key_lower not in _DEDUP_KEYS:
            continue
        
        values = value if isinstance(value, list) else [value]
        for v in values:
            if isinstance(v, str) and v.strip():
                # Normalize for comparison: lowercase, strip, digits-only for phones
                cleaned = v.strip().lower()
                fingerprints.add(f"{key_lower}:{cleaned}")
    
    return fingerprints


def _merge_records(base: Dict, other: Dict) -> Dict:
    """
    Merge two records, keeping the most complete version.
    - For scalar fields: keep non-empty value (prefer base)
    - For list fields: union the values
    """
    merged = dict(base)
    
    for key, value in other.items():
        if key not in merged or not merged[key]:
            merged[key] = value
        elif isinstance(merged[key], list) and isinstance(value, list):
            # Union lists, preserving order
            existing = set(str(v) for v in merged[key])
            for v in value:
                if str(v) not in existing:
                    merged[key].append(v)
                    existing.add(str(v))
    
    return merged


def deduplicate_data(data: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Remove duplicate records by merging those that share phone/email/website.
    
    Returns:
        (deduped_list, duplicate_count)
    """
    if not data:
        return [], 0
    
    # Each record gets an index into groups
    # groups[i] = merged record for group i
    # record_group[j] = which group record j belongs to
    groups: List[Dict] = []
    group_fingerprints: List[Set[str]] = []
    
    for record in data:
        if not isinstance(record, dict):
            groups.append(record)
            group_fingerprints.append(set())
            continue
        
        fps = _extract_fingerprints(record)
        
        # Find if any existing group shares a fingerprint
        matched_group = None
        for idx, gfps in enumerate(group_fingerprints):
            if fps & gfps:  # intersection — shared identity
                matched_group = idx
                break
        
        if matched_group is not None:
            # Merge into existing group
            groups[matched_group] = _merge_records(groups[matched_group], record)
            group_fingerprints[matched_group] |= fps
        else:
            # New group
            groups.append(dict(record))
            group_fingerprints.append(fps)
    
    duplicate_count = len(data) - len(groups)
    return groups, duplicate_count


def count_duplicates(data: List[Dict]) -> int:
    """
    Count how many duplicate records exist (for the stats block).
    Does NOT modify the data.
    """
    if not data:
        return 0
    
    # Quick pass: collect all fingerprints and check overlaps
    all_fps: List[Set[str]] = []
    for record in data:
        all_fps.append(_extract_fingerprints(record))
    
    # Count records that share fingerprints with an earlier record
    duplicates = 0
    for i in range(len(all_fps)):
        for j in range(i):
            if all_fps[i] & all_fps[j]:
                duplicates += 1
                break  # Only count once per record
    
    return duplicates
