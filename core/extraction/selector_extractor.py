from typing import Dict
from bs4 import BeautifulSoup

# Fast Extraction with Selectors
def extract_with_selectors(html: str, selectors: Dict[str, str]) -> dict:
    """Extract data using CSS selectors - NO LLM"""
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    if not selectors:
        return {"data": []}
    
    try:
        # Strategy 1: Try to find repeating containers
        # Look for common parent elements that would contain multiple items
        first_field = list(selectors.keys())[0]
        first_selector = selectors[first_field]
        
        # Find all elements matching the first selector
        first_elements = soup.select(first_selector)
        
        if len(first_elements) > 1:
            # We found multiple elements! Extract from each
            for element in first_elements[:10]:  # Max 10 items
                item = {}
                
                # For each field, try to find it relative to this element
                for field, selector in selectors.items():
                    try:
                        # Try relative to current element first
                        found = element.select_one(selector)
                        
                        # If not found, try going up to parent and searching
                        if not found and element.parent:
                            # Try from parent container
                            parent = element.parent
                            while parent and not found and parent.name != 'body':
                                # Look for the field in siblings or parent
                                found = parent.select_one(selector)
                                if found:
                                    # Make sure it's close to our element (not from another item)
                                    break
                                parent = parent.parent
                        
                        if found:
                            # Extract value
                            if found.name == 'a':
                                # For links, prefer text over href
                                item[field] = found.get_text(strip=True) or found.get('href', '')
                            elif found.name == 'img':
                                item[field] = found.get('src', '')
                            else:
                                item[field] = found.get_text(strip=True)
                        else:
                            item[field] = None
                            
                    except Exception as e:
                        item[field] = None
                
                # Only add if we got at least one field
                if any(v for v in item.values()):
                    results.append(item)
        
        else:
            # Only one element found - single item page
            item = {}
            for field, selector in selectors.items():
                try:
                    found = soup.select_one(selector)
                    
                    if found:
                        if found.name == 'a':
                            item[field] = found.get_text(strip=True) or found.get('href', '')
                        elif found.name == 'img':
                            item[field] = found.get('src', '')
                        else:
                            item[field] = found.get_text(strip=True)
                    else:
                        item[field] = None
                        
                except Exception as e:
                    item[field] = None
            
            if any(v for v in item.values()):
                results.append(item)
        
        return {"data": results, "strategy": "css_selectors"}
    
    except Exception as e:
        return {"data": [], "error": f"Selector extraction failed: {str(e)}"}