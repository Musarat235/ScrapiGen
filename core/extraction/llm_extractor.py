# Fallback: Full LLM Extraction
import json
import re
from api.dependencies import groq_client
from core.html_processing.cleaner import clean_html_for_extraction, extract_article_structure


def extract_with_llm_fallback(html: str, prompt: str) -> dict:
    """Fallback to full LLM extraction with better context"""
    
    # For content extraction, use structured text instead of raw HTML
    if 'content' in prompt.lower() or 'article' in prompt.lower() or 'heading' in prompt.lower():
        cleaned = extract_article_structure(html)[:50000]
        print(f"=== DEBUG: Using structured text extraction ===")
        print(f"=== Structured content length: {len(cleaned)} ===")
        print(f"=== First 800 chars:\n{cleaned[:800]} ===")
    else:
        # For product/other data, use HTML
        cleaned = clean_html_for_extraction(html)[:30000]
        print(f"=== DEBUG: Using HTML extraction ===")
        print(f"=== Cleaned HTML Length: {len(cleaned)} ===")
        print(f"=== First 500 chars: {cleaned[:500]} ===")
    
    system_prompt = """You are a web scraping expert. Extract data from content.

    CRITICAL RULES:
    1. IGNORE: navigation menus, headers, footers, sidebars, author bios, related posts, "read next", "you might like", comments, social buttons
    2. FOCUS ON: The main article/post/product body content ONLY

    TASK-SPECIFIC INSTRUCTIONS:

    If asked for "headings" or "get headings":
    - Extract only heading text (H1, H2, H3, etc.)
    - Format: {"data": [{"heading": "Introduction"}, {"heading": "Methods"}]}

    If asked for "content" or "extract content" or "full article":
    - Extract BOTH headings AND paragraphs that follow them
    - Pair each heading with its content
    - Format: {"data": [{"heading": "Introduction", "content": "Paragraph text here..."}, {"heading": "Next Section", "content": "More text..."}]}

    If asked for "product data" or similar:
    - Extract all product fields (name, price, SKU, description, specs)
    - Format: {"data": [{"name": "X", "price": "Y", "description": "Z"}]}

    IMPORTANT FILTERING:
    - Skip "What to read next", "Related articles", "You might like", "X minute read"
    - Skip author bios, comments, share buttons
    - If a field doesn't exist, return null - don't make up data

    Return valid JSON only."""

    user_prompt = f"""Content to extract from:
{cleaned}

User wants: {prompt}

Important: If user asks for "content", return BOTH headings and their associated paragraphs as pairs.

Return as valid JSON:"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=2000,  # Increased for longer descriptions
            response_format={"type": "json_object"}
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # Extract JSON if wrapped in text
        if not response_text.startswith('{'):
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)
        
        result = json.loads(response_text)
        result["strategy"] = "full_llm"
        
        print(f"LLM extraction result: {result}")
        return result
    
    except Exception as e:
        print(f"LLM extraction error: {e}")
        return {"data": [], "error": f"LLM extraction failed: {str(e)}", "strategy": "failed"}

def is_full_content_request(prompt: str) -> bool:
    """Check if user wants full article/blog content"""
    content_phrases = [
        'extract content', 'get content', 'full content', 'all content',
        'extract article', 'get article', 'full article', 'entire article',
        'extract post', 'blog content', 'complete content'
    ]
    return any(phrase in prompt.lower() for phrase in content_phrases)