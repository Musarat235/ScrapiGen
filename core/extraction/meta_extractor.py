import re
from bs4 import BeautifulSoup

# Meta Tag Extraction (NO LLM NEEDED)
def extract_meta_tags(html: str) -> dict:
    """Direct meta tag extraction - fast and free"""
    soup = BeautifulSoup(html, 'html.parser')
    
    meta = {}
    
    # Title
    title = soup.find('title')
    meta['title'] = title.text.strip() if title else None
    
    # Meta description
    desc = soup.find('meta', attrs={'name': 'description'})
    meta['description'] = desc.get('content', '').strip() if desc else None
    
    # Meta keywords
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    meta['keywords'] = keywords.get('content', '').strip() if keywords else None
    
    # Open Graph
    og_title = soup.find('meta', property='og:title')
    meta['og_title'] = og_title.get('content', '').strip() if og_title else None
    
    og_desc = soup.find('meta', property='og:description')
    meta['og_description'] = og_desc.get('content', '').strip() if og_desc else None
    
    og_image = soup.find('meta', property='og:image')
    meta['og_image'] = og_image.get('content', '').strip() if og_image else None
    
    og_url = soup.find('meta', property='og:url')
    meta['og_url'] = og_url.get('content', '').strip() if og_url else None
    
    # Twitter Card
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    meta['twitter_title'] = twitter_title.get('content', '').strip() if twitter_title else None
    
    twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
    meta['twitter_description'] = twitter_desc.get('content', '').strip() if twitter_desc else None
    
    return {k: v for k, v in meta.items() if v}  # Remove None values

def is_meta_request(prompt: str) -> bool:
    """Check if user is specifically asking for meta tags"""
    prompt_lower = prompt.lower()
    
    # Specific meta tag requests
    meta_keywords = [
        'meta tag', 'meta title', 'meta description', 
        'meta keyword', 'og:', 'twitter:', 'seo tag',
        'open graph', 'twitter card'
    ]
    
    # Check for explicit meta requests
    if any(keyword in prompt_lower for keyword in meta_keywords):
        return True
    
    # Check if ONLY asking for title/description (nothing else)
    words = prompt_lower.split()
    is_only_meta = (
        ('title' in words or 'description' in words) and
        len(words) <= 5 and  # Short prompt
        'product' not in prompt_lower and
        'page' not in prompt_lower and
        'article' not in prompt_lower
    )
    
    return is_only_meta