"""
Data Normalizers for ScrapiGen Enrichment Pipeline
Cleans phones, emails, URLs without changing the data structure
"""

import re
from typing import List, Dict, Any


# ============================================================================
# PHONE NORMALIZATION
# ============================================================================

def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number:
    - Strip whitespace and common separators
    - Keep leading + for international
    - Remove non-digit chars (except leading +)
    - Return empty string if too short (<7 digits) or too long (>15 digits)
    """
    if not phone or not isinstance(phone, str):
        return ""
    
    phone = phone.strip()
    
    # Preserve leading +
    has_plus = phone.startswith("+")
    
    # Keep only digits
    digits = re.sub(r"[^\d]", "", phone)
    
    if len(digits) < 7 or len(digits) > 15:
        return ""
    
    if has_plus:
        return f"+{digits}"
    
    return digits


def is_phone_normalized(phone: str) -> bool:
    """Check if a phone is already in normalized form (only digits, optional leading +)"""
    if not phone or not isinstance(phone, str):
        return False
    cleaned = phone.strip()
    return bool(re.match(r"^\+?\d{7,15}$", cleaned))


# ============================================================================
# EMAIL NORMALIZATION
# ============================================================================

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def normalize_email(email: str) -> str:
    """
    Normalize an email:
    - Lowercase
    - Strip whitespace
    - Validate format (return empty string if invalid)
    """
    if not email or not isinstance(email, str):
        return ""
    
    email = email.strip().lower()
    
    if not _EMAIL_RE.match(email):
        return ""
    
    return email


def is_email_normalized(email: str) -> bool:
    """Check if email is already lowercase, trimmed, and valid"""
    if not email or not isinstance(email, str):
        return False
    trimmed = email.strip()
    return trimmed == trimmed.lower() and bool(_EMAIL_RE.match(trimmed))


# ============================================================================
# URL / WEBSITE NORMALIZATION
# ============================================================================

def normalize_url(url: str) -> str:
    """
    Normalize a URL:
    - Add https:// if no scheme
    - Strip trailing slashes
    - Remove common tracking params
    """
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip()
    
    if not url:
        return ""
    
    # Add scheme if missing
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = f"https://{url}"
    
    # Strip trailing slash
    url = url.rstrip("/")
    
    # Remove common tracking params
    url = re.sub(r"[?&](utm_\w+|ref|fbclid|gclid|mc_[a-z]+)=[^&]*", "", url)
    # Clean up leftover ? or &
    url = re.sub(r"\?&", "?", url)
    url = re.sub(r"\?$", "", url)
    
    return url


def is_url_normalized(url: str) -> bool:
    """Check if URL already has scheme and no trailing slash"""
    if not url or not isinstance(url, str):
        return False
    trimmed = url.strip()
    return bool(re.match(r"^https?://", trimmed)) and not trimmed.endswith("/")


# ============================================================================
# MASTER NORMALIZER
# ============================================================================

# Fields that should be treated as phones, emails, URLs
_PHONE_KEYS = {"phone", "phones", "telephone", "tel", "mobile", "cell", "fax", "phone_number", "contact_phone"}
_EMAIL_KEYS = {"email", "emails", "e-mail", "mail", "email_address", "contact_email"}
_URL_KEYS = {"website", "websites", "url", "urls", "link", "site", "homepage", "web"}


def _normalize_field_value(key: str, value: Any) -> Any:
    """Normalize a single field value based on its key name"""
    key_lower = key.lower().replace(" ", "_").replace("-", "_")
    
    if key_lower in _PHONE_KEYS:
        if isinstance(value, list):
            return [normalize_phone(v) for v in value if normalize_phone(v)]
        return normalize_phone(str(value))
    
    if key_lower in _EMAIL_KEYS:
        if isinstance(value, list):
            return [normalize_email(v) for v in value if normalize_email(v)]
        return normalize_email(str(value))
    
    if key_lower in _URL_KEYS:
        if isinstance(value, list):
            return [normalize_url(v) for v in value if normalize_url(v)]
        return normalize_url(str(value))
    
    return value


def normalize_data(data: List[Dict]) -> List[Dict]:
    """
    Normalize all known fields in a list of records.
    Returns a new list — does not mutate the input.
    """
    normalized = []
    for record in data:
        if not isinstance(record, dict):
            normalized.append(record)
            continue
        
        new_record = {}
        for key, value in record.items():
            new_record[key] = _normalize_field_value(key, value)
        normalized.append(new_record)
    
    return normalized


def count_normalization_issues(data: List[Dict]) -> Dict[str, int]:
    """
    Count how many values need normalization (for the stats block).
    Returns: {"phones_to_fix": 2, "emails_to_fix": 1, "urls_to_fix": 3}
    """
    stats = {"phones_to_fix": 0, "emails_to_fix": 0, "urls_to_fix": 0}
    
    for record in data:
        if not isinstance(record, dict):
            continue
        for key, value in record.items():
            key_lower = key.lower().replace(" ", "_").replace("-", "_")
            
            values = value if isinstance(value, list) else [value]
            
            for v in values:
                if not isinstance(v, str) or not v.strip():
                    continue
                
                if key_lower in _PHONE_KEYS and not is_phone_normalized(v):
                    stats["phones_to_fix"] += 1
                elif key_lower in _EMAIL_KEYS and not is_email_normalized(v):
                    stats["emails_to_fix"] += 1
                elif key_lower in _URL_KEYS and not is_url_normalized(v):
                    stats["urls_to_fix"] += 1
    
    return stats
