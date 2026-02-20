"""
LLM-based CSS selector generation
IMPROVED: Validates content has ACTUAL TEXT, not just divs
"""
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Optional
from api.dependencies import groq_client


def has_meaningful_content(element: BeautifulSoup, min_text_length: int = 100) -> bool:
    """
    ✅ NEW: Check if element has real content, not just skeleton/placeholders
    """
    if not element:
        return False
    
    # Get visible text
    text = element.get_text(strip=True)
    
    # Must have minimum text
    if len(text) < min_text_length:
        return False
    
    # ✅ Check for skeleton/placeholder indicators
    skeleton_signs = [
        'lazy-load-skeleton',
        'skeleton-loader',
        'loading-skeleton',
        'placeholder-loading'
    ]
    
    element_html = str(element).lower()
    if any(sign in element_html for sign in skeleton_signs):
        # Check if it's ONLY skeleton or has real content too
        non_skeleton = element.find_all(string=True)
        real_text = ''.join([s.strip() for s in non_skeleton if s.strip()])
        
        if len(real_text) < min_text_length:
            return False
    
    return True


def find_main_content(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    """
    ✅ IMPROVED: Find actual content with text, not loading skeletons
    """
    
    # Priority 1: Product-specific containers WITH CONTENT
    product_patterns = [
        r'pdp-mod-product-badge',
        r'pdp-product-',
        r'product-detail-page',
        r'product-info-main',
        r'item-detail',
        r'product-container'
    ]
    
    for pattern in product_patterns:
        candidates = soup.find_all(class_=re.compile(pattern, re.I))
        
        for candidate in candidates:
            if has_meaningful_content(candidate, min_text_length=100):
                print(f"✅ Found product content: {candidate.get('class')} ({len(str(candidate)):,} chars, {len(candidate.get_text(strip=True))} text chars)")
                return candidate
    
    # Priority 2: ID-based containers
    id_patterns = [r'product', r'item', r'detail', r'content']
    
    for pattern in id_patterns:
        candidate = soup.find(id=re.compile(pattern, re.I))
        if candidate and has_meaningful_content(candidate, min_text_length=100):
            print(f"✅ Found content by ID: {candidate.get('id')} ({len(str(candidate)):,} chars)")
            return candidate
    
    # Priority 3: Semantic HTML with content
    semantic_tags = ['main', 'article']
    
    for tag in semantic_tags:
        candidate = soup.find(tag)
        if candidate and has_meaningful_content(candidate, min_text_length=100):
            print(f"✅ Found content in  ({len(str(candidate)):,} chars)")
            return candidate
    
    # Priority 4: Look for the largest content-rich div
    print("🔍 Searching for content-rich divs...")
    
    # Get all divs with substantial text
    all_divs = soup.find_all('div')
    content_divs = []
    
    for div in all_divs:
        text_length = len(div.get_text(strip=True))
        
        # Skip if too small
        if text_length < 200:
            continue
        
        # Skip navigation/menu/footer
        classes = ' '.join(div.get('class', [])).lower()
        if any(bad in classes for bad in ['menu', 'nav', 'header', 'footer', 'sidebar']):
            continue
        
        # Check text-to-HTML ratio (should have more text than tags)
        html_length = len(str(div))
        text_ratio = text_length / html_length if html_length > 0 else 0
        
        if text_ratio > 0.05:  # At least 5% text
            content_divs.append((div, text_length, text_ratio))
    
    # Sort by text length (most text = likely main content)
    content_divs.sort(key=lambda x: x[1], reverse=True)
    
    if content_divs:
        best_div, text_len, ratio = content_divs[0]
        print(f"✅ Found content-rich div: {text_len} text chars, {ratio:.1%} text ratio")
        return best_div
    
    # Fallback: Use body but remove navigation
    print("⚠️ Using body as fallback (removing navigation)")
    body = soup.find('body') or soup
    
    # Remove unwanted sections
    for unwanted in body.find_all(['nav', 'header', 'footer']):
        unwanted.decompose()
    
    for menu in body.find_all(class_=re.compile(r'menu|nav|header|footer|sidebar', re.I)):
        menu.decompose()
    
    return body


def generate_selectors_with_llm(html: str, prompt: str) -> Dict[str, str]:
    """
    ✅ IMPROVED: Better content finding and validation
    """
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove scripts, styles, SVGs
    for tag in soup(['script', 'style', 'noscript', 'svg', 'path']):
        tag.decompose()
    
    # ✅ Find ONLY the main content with ACTUAL TEXT
    main_content = find_main_content(soup)
    
    if not main_content:
        print("❌ Could not find main content area")
        return {}
    
    # Validate content has text
    content_text = main_content.get_text(strip=True)
    if len(content_text) < 100:
        print(f"⚠️ Content area has too little text ({len(content_text)} chars)")
        print(f"First 200 chars: {str(main_content)[:200]}")
        return {}
    
    print(f"📍 Content validated: {len(str(main_content)):,} HTML chars, {len(content_text):,} text chars")
    
    # Get sample from main content
    sample_html = str(main_content)[:30000]  # Increased to 30k
    
    # Extract visible text
    text_preview = content_text[:4000]
    
    # ✅ Extract important elements with ACTUAL TEXT
    important_elements = []
    
    # For product pages - find elements with actual prices
    if 'product' in prompt.lower() or 'price' in prompt.lower():
        # Find price elements that have numbers
        for elem in main_content.find_all(class_=re.compile(r'price', re.I))[:5]:
            text = elem.get_text(strip=True)
            if text and any(char.isdigit() for char in text):
                classes = ' '.join(elem.get('class', []))
                important_elements.append(f"💰 Price: {text[:50]}")
        
        # Find title elements with actual text
        for elem in main_content.find_all(['h1', 'h2'])[:3]:
            text = elem.get_text(strip=True)
            if len(text) > 10:  # Must have substantial text
                classes = ' '.join(elem.get('class', []))
                important_elements.append(f"📌 Title: {text[:50]}...</>")
    
    element_hints = '\n'.join(important_elements[:10]) if important_elements else "No elements with visible content found"
    
    # ✅ Show LLM some actual text to verify content exists
    system_prompt = """You are a CSS selector expert analyzing product/article pages.

CRITICAL RULES:
1. The HTML provided is MAIN CONTENT ONLY (navigation/menus already removed)
2. Look at the ACTUAL TEXT in elements, not just class names
3. For prices: Find elements containing numbers with currency (Rs, $, ₹)
4. For names: Find h1 or elements with substantial descriptive text
5. Selectors must be SPECIFIC enough to avoid matching multiple unrelated items
6. Test mentally: "Would this selector extract the RIGHT data?"

VALIDATION CHECKLIST:
✓ Does the element have VISIBLE TEXT? (Not just empty divs)
✓ Is the selector specific? (e.g., "span.pdp-price" not just "span")
✓ Would it match ONLY the product/article, not lists of items?

If you can't find good selectors with actual content, return empty.

Return JSON:
{
    "selectors": {
        "field_name": "specific_css_selector"
    }
}"""

    user_prompt = f"""HTML Content (main area only):
{sample_html}

Visible Text Preview (this is what the user sees):
{text_preview[:1000]}

Important Elements Found:
{element_hints}

User Request: {prompt}

IMPORTANT: 
- The visible text above shows you what content exists
- Generate selectors for elements that contain THIS TEXT
- Be specific (use full class names)

Generate selectors:"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        response = json.loads(completion.choices[0].message.content)
        selectors = response.get("selectors", {})
        
        # ✅ Validate selectors
        validated_selectors = {}
        
        for field, selector in selectors.items():
            # Skip empty selectors
            if not selector or selector.strip() == '':
                print(f"⚠️ Empty selector for '{field}'")
                continue
            
            # Check for navigation patterns
            bad_patterns = ['menu', 'nav', 'header', 'footer', 'sidebar', 'category']
            if any(bad in selector.lower() for bad in bad_patterns):
                print(f"❌ Rejected '{field}': {selector} (navigation-related)")
                continue
            
            # Too generic
            if selector in ['span', 'div', 'a', 'p', 'h1', 'h2', 'h3']:
                print(f"❌ Rejected '{field}': {selector} (too generic)")
                continue
            
            validated_selectors[field] = selector
        
        if validated_selectors:
            print(f"✅ Generated valid selectors: {validated_selectors}")
        else:
            print(f"⚠️ No valid selectors generated")
        
        return validated_selectors
    
    except Exception as e:
        print(f"❌ Selector generation failed: {e}")
        return {}