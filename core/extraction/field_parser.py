"""
Field parsing utilities
Extract and filter fields based on user prompts
"""
from typing import List

def extract_requested_fields(prompt: str) -> list:
    """Parse prompt to extract what fields user wants"""
    prompt_lower = prompt.lower()
    
    # Common field patterns
    field_keywords = [
        'title', 'name', 'price', 'description', 'image', 'url', 'author',
        'date', 'category', 'rating', 'review', 'email', 'phone', 'address',
        'sku', 'stock', 'availability', 'brand', 'heading', 'content', 'quote',
        'text', 'paragraph', 'link'
    ]
    
    found_fields = []
    for keyword in field_keywords:
        if keyword in prompt_lower:
            found_fields.append(keyword)
    
    return found_fields


def filter_to_requested_fields(data: list, requested_fields: list) -> list:
    """Keep only fields that match what user asked for"""
    if not data or not requested_fields:
        return data
    
    filtered_data = []
    for item in data:
        filtered_item = {}
        for key, value in item.items():
            key_lower = key.lower()
            # Keep field if it matches any requested field
            if any(rf in key_lower for rf in requested_fields):
                filtered_item[key] = value
        
        if filtered_item:  # Only add if we kept at least one field
            filtered_data.append(filtered_item)
    
    return filtered_data if filtered_data else data  # Return original if nothing matched
