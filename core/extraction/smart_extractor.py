# from services.cache_manager import get_cached_extraction, cache_extracted_data
# from core.html_processing.fetcher import fetch_html
# from services.multi_layer_extraction import extract_with_multi_layer
# from .selector_generator import generate_selectors_with_llm
# from .selector_extractor import extract_with_selectors
# from .meta_extractor import extract_meta_tags, is_meta_request
# from .field_parser import extract_requested_fields, filter_to_requested_fields
# from .llm_extractor import extract_with_llm_fallback, is_full_content_request
# from services.enhanced_extraction import detect_list_page, smart_field_detection, scrape_multi_level
# from config.settings import selector_cache

# # Smart Hybrid Extraction
# async def smart_extract(html: str, prompt: str, cache_key: str = None, url: str = None) -> dict:
#     """
#     Enhanced smart extraction with multi-layer approach
    
#     Flow:
#     1. Check cache
#     2. Detect if list page → crawl all items
#     3. Use hybrid extraction (rules + LLM)
#     4. Return structured data
#     """
    
#     # ========================================================================
#     # STEP 1: Check cache first
#     # ========================================================================
#     if cache_key:
#         cached = await get_cached_extraction(cache_key, prompt)
#         if cached:
#             print(f"📦 Extraction cache HIT")
#             return cached
    
#     # ========================================================================
#     # STEP 2: Check if it's a list page that needs crawling
#     # ========================================================================
#     if url:
#         list_detection = detect_list_page(html)
        
#         if list_detection["is_list"] and list_detection["total_items"] > 1:
#             print(f"🔍 Detected list page with {list_detection['total_items']} items")
#             print(f"🕷️ Crawling all items...")
            
#             # Use multi-level scraper
#             results = await scrape_multi_level(
#                 list_url=url,
#                 prompt=prompt,
#                 max_detail_pages=100,  # Pro tier limit
#                 fetch_html_func=fetch_html
#             )
            
#             # Cache the combined result
#             if cache_key:
#                 await cache_extracted_data(cache_key, prompt, results)
            
#             return {
#                 "data": results,
#                 "strategy": "multi_level_crawl",
#                 "total_crawled": len(results)
#             }
    
#     # ========================================================================
#     # STEP 3: Single page extraction (hybrid approach)
#     # ========================================================================
    
#     # Strategy 1: Meta tags (instant, free)
#     if is_meta_request(prompt):
#         meta_data = extract_meta_tags(html)
#         result = {"data": [meta_data], "strategy": "meta_direct"}
        
#         # Cache and return
#         if cache_key:
#             await cache_extracted_data(cache_key, prompt, [meta_data])
        
#         return result
    
#     # Parse prompt to understand what user wants
#     requested_fields = extract_requested_fields(prompt)
    
#     # Strategy 2: Full content extraction (articles, blogs)
#     if is_full_content_request(prompt):
#         print("📄 Full content request detected, using LLM directly")
#         result = extract_with_llm_fallback(html, prompt)
        
#         # Filter to requested fields
#         if requested_fields and result.get("data"):
#             result["data"] = filter_to_requested_fields(result["data"], requested_fields)
        
#         # Cache and return
#         if cache_key:
#             await cache_extracted_data(cache_key, prompt, result.get("data", []))
        
#         return result
    
#     # Strategy 3: Hybrid selector approach (e-commerce, structured data)
#     # Strategy 3: Try multi-layer extraction FIRST (better for hidden data)
        
#     print("🔍 Using multi-layer extraction (finds hidden data)...")
#     multi_layer_result = extract_with_multi_layer(html, fields=["phones", "emails", "websites"])
        
#     # Combine with basic field extraction
#     detected_fields = smart_field_detection(html, multi_layer_result)
        
#     # Check if we got good data
#     if detected_fields and any(detected_fields.values()):
#         print(f"✅ Multi-layer found: {len(multi_layer_result.get('phones', []))} phones, {len(multi_layer_result.get('emails', []))} emails")
            
#         # Format for output
#         result = {
#             "data": [detected_fields],
#             "strategy": "multi_layer",
#             "confidence": multi_layer_result.get("confidence", 0.0)
#         }
            
#         # Cache and return
#         if cache_key:
#             await cache_extracted_data(cache_key, prompt, [detected_fields])
            
#         return result

#     # If multi-layer didn't find enough, try selectors as fallback
#     print("⚠️ Multi-layer found limited data, trying CSS selectors...")

#     # Check if we have cached selectors
#     selectors = selector_cache.get(cache_key) if cache_key else None

#     if not selectors:
#         # Generate selectors with LLM (ONCE per domain)
#         selectors = generate_selectors_with_llm(html, prompt)
#         if selectors and cache_key:
#             selector_cache[cache_key] = selectors
    
#     if selectors:
#         # Extract using selectors (fast, no LLM)
#         result = extract_with_selectors(html, selectors)
#         data = result.get("data", [])
        
#         # Validate data quality
#         has_valid_data = False
        
#         if data:
#             prompt_lower = prompt.lower()
#             prompt_keywords = set(prompt_lower.replace(',', ' ').split())
            
#             # Check each extracted item
#             for item in data:
#                 # Must be a dict
#                 if not isinstance(item, dict):
#                     continue
                
#                 # Get field names
#                 field_names = set(item.keys())
                
#                 # Check if item has non-null values
#                 values = [v for v in item.values() if v]
                
#                 # Filter out URLs, IDs, UI elements
#                 meaningful_values = [
#                     v for v in values 
#                     if v 
#                     and not str(v).startswith(('http', '/', 'item?id='))
#                     and len(str(v)) > 3
#                     and not any(ui_word in str(v).lower() for ui_word in ['filter', 'menu', 'tab', 'button', 'any', 'spoken language'])
#                 ]
                
#                 # Check if field names match what user asked for
#                 has_matching_fields = any(
#                     keyword in field_name.lower() 
#                     for keyword in prompt_keywords 
#                     for field_name in field_names
#                     if keyword not in ['extract', 'get', 'all', 'find', 'scrape', 'and', 'the', 'from', 'a']
#                 )
                
#                 # Calculate field coverage
#                 critical_fields = ['price', 'cost', 'amount', 'sku']
                
#                 if requested_fields:
#                     matched_fields = sum(1 for rf in requested_fields if any(rf in fn.lower() for fn in field_names))
#                     field_coverage = matched_fields / len(requested_fields) if requested_fields else 0
                    
#                     # Check if missing critical fields
#                     missing_critical = any(
#                         cf in prompt.lower() and not any(cf in fn.lower() for fn in field_names)
#                         for cf in critical_fields
#                     )
#                 else:
#                     field_coverage = 1.0
#                     missing_critical = False
                
#                 # Validate: has meaningful data + matches prompt + good coverage + no missing critical
#                 if meaningful_values and (has_matching_fields or len(field_names) <= 3) and field_coverage >= 0.6 and not missing_critical:
#                     has_valid_data = True
#                     break
        
#         # If selectors gave us good data, use it
#         if has_valid_data:
#             # Filter to requested fields
#             if requested_fields:
#                 filtered_data = filter_to_requested_fields(data, requested_fields)
#                 result["data"] = filtered_data
            
#             result["selectors_used"] = selectors
#             print(f"✅ Selectors validated. Fields: {list(data[0].keys()) if data else []}")
            
#             # Cache and return
#             if cache_key:
#                 await cache_extracted_data(cache_key, prompt, result.get("data", []))
            
#             return result
        
#         # Selectors didn't work well, log it
#         print(f"⚠️ Selectors returned invalid data, falling back to LLM")
#         print(f"   Expected: {requested_fields or prompt_keywords}")
#         print(f"   Got: {list(data[0].keys()) if data else 'empty'}")
    
#     # Strategy 4: Fallback to full LLM extraction
#     print("🤖 Using full LLM extraction")
#     result = extract_with_llm_fallback(html, prompt)
    
#     # Filter to requested fields
#     if requested_fields and result.get("data"):
#         result["data"] = filter_to_requested_fields(result["data"], requested_fields)
    
#     # Cache and return
#     if cache_key:
#         await cache_extracted_data(cache_key, prompt, result.get("data", []))
    
#     return result
"""
Smart extraction orchestrator
Decides which extraction strategy to use BASED ON USER PROMPT
"""
from typing import Optional
from .meta_extractor import extract_meta_tags, is_meta_request
from .selector_generator import generate_selectors_with_llm
from .selector_extractor import extract_with_selectors
from .llm_extractor import extract_with_llm_fallback, is_full_content_request
from .field_parser import extract_requested_fields, filter_to_requested_fields
from core.extraction.enhanced import detect_list_page
from core.extraction.multi_layer import extract_with_multi_layer
from storage.cache_manager import get_cached_extraction, cache_extracted_data
from config.settings import selector_cache

def is_blocked_by_bot_protection(html: str, url: str) -> bool:
    """
    ✅ NEW: Detect if we got a bot protection page instead of real content
    """
    block_indicators = [
        # Cloudflare
        'Just a moment',
        'Checking your browser',
        'Enable JavaScript and cookies',
        'cf-browser-verification',
        
        # Distil Networks
        'distilnetworks.com',
        'Third-Party Browser Plugins',
        'Our website is made possible by displaying',
        
        # Other protections
        'Access Denied',
        'Access denied',
        'You have been blocked',
        'Suspicious activity',
        'Please verify you are human',
        
        # Common bot block patterns
        'bot protection',
        'security check',
    ]
    
    html_lower = html.lower()
    
    # Check for indicators
    for indicator in block_indicators:
        if indicator.lower() in html_lower:
            print(f"🚫 Bot protection detected: {indicator}")
            return True
    
    # Check if HTML is suspiciously short for a real page
    if len(html) < 5000 and url:
        # Real product/listing pages are usually 50k+ chars
        print(f"⚠️ Page too short ({len(html)} chars) - might be blocked")
        return True
    
    return False

def is_contact_info_request(prompt: str) -> bool:
    """Check if user is asking for contact information"""
    contact_keywords = ['phone', 'email', 'contact', 'telephone', 'mobile', 'call', 'fax']
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in contact_keywords)


async def smart_extract(html: str, prompt: str, cache_key: str = None, url: str = None) -> dict:
    """
    Enhanced smart extraction with multi-layer approach
    
    Flow:
    1. Check cache
    2. Detect if list page → crawl all items
    3. Check prompt type → route to correct extractor
    4. Return structured data
    """
    # ========================================================================
    # STEP 0: Check if we got blocked
    # ========================================================================
    if is_blocked_by_bot_protection(html, url):
        print("🚫 Bot protection detected - cannot extract data")
        return {
            "data": [],
            "strategy": "blocked",
            "error": "Website blocked the scraper. This site uses bot protection (Cloudflare/Distil Networks).",
            "suggestion": "Try using a different URL or contact site owner for API access."
        }
    # ========================================================================
    # STEP 1: Check cache first
    # ========================================================================
    if cache_key:
        cached = await get_cached_extraction(cache_key, prompt)
        if cached:
            print(f"📦 Extraction cache HIT")
            return cached
    
    # ========================================================================
    # STEP 2: Check if it's a list page that needs crawling
    # ========================================================================
    if url:
        list_detection = detect_list_page(html)
        
        if list_detection["is_list"] and list_detection["total_items"] > 1:
            print(f"📋 Detected list page with {list_detection['total_items']} items")
            print(f"🕷️ Crawling all items...")
            
            # Import here to avoid circular dependency
            from core.html_processing.fetcher import fetch_html
            from core.extraction.enhanced import scrape_multi_level
            
            # Use multi-level scraper
            results = await scrape_multi_level(
                list_url=url,
                prompt=prompt,
                max_detail_pages=100,
                fetch_html_func=fetch_html
            )
            
            # Cache the combined result
            if cache_key:
                await cache_extracted_data(cache_key, prompt, results)
            
            return {
                "data": results,
                "strategy": "multi_level_crawl",
                "total_crawled": len(results)
            }
    
    # ========================================================================
    # STEP 3: Route to correct extraction strategy based on prompt
    # ========================================================================
    
    # Parse prompt to understand what user wants
    requested_fields = extract_requested_fields(prompt)
    
    # Strategy 1: Meta tags (instant, free)
    if is_meta_request(prompt):
        print("🏷️ Meta tag request detected")
        meta_data = extract_meta_tags(html)
        result = {"data": [meta_data], "strategy": "meta_direct"}
        
        if cache_key:
            await cache_extracted_data(cache_key, prompt, [meta_data])
        
        return result
    
    # Strategy 2: Full content extraction (articles, blogs)
    if is_full_content_request(prompt):
        print("📄 Full content request detected, using LLM directly")
        result = extract_with_llm_fallback(html, prompt)
        
        if requested_fields and result.get("data"):
            result["data"] = filter_to_requested_fields(result["data"], requested_fields)
        
        if cache_key:
            await cache_extracted_data(cache_key, prompt, result.get("data", []))
        
        return result
    
    # Strategy 3: Contact info extraction (ONLY if user asks for it!)
    if is_contact_info_request(prompt):
        print("📞 Contact info request detected, using multi-layer extraction")
        multi_layer_result = extract_with_multi_layer(html, fields=["phones", "emails", "websites"])
        
        # Check if we got good data
        if multi_layer_result and any(multi_layer_result.get("phones", []) or multi_layer_result.get("emails", [])):
            print(f"✅ Multi-layer found: {len(multi_layer_result.get('phones', []))} phones, {len(multi_layer_result.get('emails', []))} emails")
            
            # Format for output
            result = {
                "data": [multi_layer_result],
                "strategy": "multi_layer",
                "confidence": multi_layer_result.get("confidence", 0.0)
            }
            
            if cache_key:
                await cache_extracted_data(cache_key, prompt, [multi_layer_result])
            
            return result
    
    # Strategy 4: CSS Selectors (for product data, prices, etc.)
    print("🎯 Using CSS selector strategy (for structured data like prices, names, etc.)")
    
    selectors = selector_cache.get(cache_key) if cache_key else None
    
    if not selectors:
        print("🤖 Generating CSS selectors with LLM...")
        selectors = generate_selectors_with_llm(html, prompt)
        if selectors and cache_key:
            selector_cache[cache_key] = selectors
            print(f"💾 Cached selectors for future use: {list(selectors.keys())}")
    else:
        print(f"📦 Using cached selectors: {list(selectors.keys())}")
    
    if selectors:
        result = extract_with_selectors(html, selectors)
        data = result.get("data", [])
        
        # Validate data quality
        has_valid_data = bool(data and any(
            isinstance(item, dict) and any(v for v in item.values() if v)
            for item in data
        ))
        
        if has_valid_data:
            # Filter to requested fields if specified
            if requested_fields:
                filtered_data = filter_to_requested_fields(data, requested_fields)
                result["data"] = filtered_data
            
            result["selectors_used"] = selectors
            print(f"✅ Selectors worked! Extracted {len(data)} items with fields: {list(data[0].keys()) if data else []}")
            
            if cache_key:
                await cache_extracted_data(cache_key, prompt, result.get("data", []))
            
            return result
        else:
            print(f"⚠️ Selectors returned no valid data")
    else:
        print("⚠️ Could not generate selectors")
    
    # Strategy 5: Fallback to full LLM extraction
    print("🤖 Falling back to full LLM extraction")
    result = extract_with_llm_fallback(html, prompt)
    
    if requested_fields and result.get("data"):
        result["data"] = filter_to_requested_fields(result["data"], requested_fields)
    
    if cache_key:
        await cache_extracted_data(cache_key, prompt, result.get("data", []))
    
    return result