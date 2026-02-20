from typing import Dict
from bs4 import BeautifulSoup

def clean_html_for_extraction(html: str) -> str:
    """Remove scripts, styles, navigation, and focus on main content"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Step 1: Remove non-content tags completely
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'path']):
        tag.decompose()
    
    # Step 2: Remove common navigation/UI elements by tag
    for tag in soup(['nav']):
        tag.decompose()
    
    # Step 3: Remove mobile menus and navigation specifically
    mobile_patterns = ['mobile-menu', 'mobile-nav', 'mobile-header']
    for pattern in mobile_patterns:
        for element in soup.find_all(class_=lambda x: x and pattern in str(x).lower()):
            element.decompose()
    
    # Step 4: Try to find main content area (but don't remove everything else)
    main_content = (
        soup.find('main') or
        soup.find('article') or
        soup.find(role='main') or
        soup.find(class_=lambda x: x and any(word in str(x).lower() for word in ['post-content', 'article-content', 'entry-content', 'blog-content', 'product-description'])) or
        soup.find(id=lambda x: x and any(word in str(x).lower() for word in ['content', 'main-content', 'post', 'article'])) or
        soup.body or
        soup
    )
    
    # Step 5: From main content, remove headers/footers/sidebars
    if main_content:
        for tag in main_content.find_all(['header', 'footer', 'aside']):
            tag.decompose()
        
        # Remove sidebar/widget areas
        for element in main_content.find_all(class_=lambda x: x and any(word in str(x).lower() for word in ['sidebar', 'widget', 'related', 'recommended'])):
            element.decompose()

    # Step 6: Remove "related posts" / "read next" sections (but be careful!)
    # Step 6: Remove only obviously marked related content sections
    if main_content:
        for element in main_content.find_all(class_=lambda x: x and 'related-posts' in str(x).lower()):
            element.decompose()
    
    return str(main_content)

def extract_article_structure(html: str) -> str:
    """Extract article content in a cleaner format for LLM"""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # DEBUG: See what elements we find
    all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    all_paragraphs = soup.find_all('p')
    print(f"=== Found {len(all_headings)} headings and {len(all_paragraphs)} paragraphs ===")

    # Find article headings and paragraphs
    content_parts = []
    
    # Get all headings and paragraphs in order
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        text = element.get_text(strip=True)
        
        # Skip very short text (likely not real content)
        if len(text) < 10:
            continue
        
        # Skip common non-content phrases
        skip_phrases = ['what to read next', 'related articles', 'you might like', 'read more', 'minute read']
        if any(phrase in text.lower() for phrase in skip_phrases):
            continue
        
        tag_name = element.name
        content_parts.append(f"[{tag_name.upper()}] {text}")
    
    return "\n\n".join(content_parts[:100])  # Limit to first 100 elements