"""
Multi-Layer Extraction System
Extracts data with 90%+ accuracy using multiple methods
"""

import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Set
import json
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class MultiLayerExtractor:
    """
    3-Layer extraction system:
    Layer 1: Fast rules (tel:, mailto:, obvious patterns)
    Layer 2: Deep pattern matching (regex, context analysis)
    Layer 3: LLM verification (check if extracted data is valid)
    """
    
    def __init__(self, html: str):
        self.html = html
        self.soup = BeautifulSoup(html, 'html.parser')
        self.extracted = {
            "phones": set(),
            "emails": set(),
            "websites": set(),
            "addresses": set(),
            "companies": set()
        }
    
    # Add this NEW method to MultiLayerExtractor class:

    def extract_phones_from_links(self) -> Set[str]:
        """
        Extract phones hidden in various link formats
        
        Catches:
        - tel: links
        - WhatsApp links (wa.me)
        - Skype links (callto:)
        - Data attributes
        """
        phones = set()
        
        # All links
        for link in self.soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            original_href = link.get('href', '')  # Keep original for extraction
            
            # ✅ FIX 1: Pattern 1 - tel: links (FIXED ORDER)
            if href.startswith('tel'):
                # Remove tel:// or tel: in correct order
                phone = original_href
                phone = re.sub(r'^tel:?/*', '', phone, flags=re.IGNORECASE)
                # ✅ FIX 2: Remove ALL non-digit chars (no spaces!)
                phone = re.sub(r'[^\d]', '', phone)
                if 10 <= len(phone) <= 15:
                    # Format nicely (optional)
                    if len(phone) == 10:
                        phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                    phones.add(phone)
                    print(f"   📞 Found tel: link → {phone}")
            
            # Pattern 2: WhatsApp (wa.me/PHONE)
            elif 'wa.me/' in href:
                wa_match = re.search(r'wa\.me/(\d{10,15})', href)
                if wa_match:
                    phone = wa_match.group(1)
                    phones.add('+' + phone)
                    print(f"   📱 Found WhatsApp → +{phone}")
            
            # Pattern 3: WhatsApp (whatsapp://send?phone=)
            elif 'whatsapp://' in href or 'api.whatsapp.com' in href:
                wa_param = re.search(r'phone=(\d{10,15})', href)
                if wa_param:
                    phone = wa_param.group(1)
                    phones.add('+' + phone)
                    print(f"   📱 Found WhatsApp param → +{phone}")
            
            # Pattern 4: Skype callto:
            elif href.startswith('callto:'):
                phone = original_href.replace('callto:', '').strip()
                phone = re.sub(r'[^\d\+\(\)\-]', '', phone)  # No spaces!
                if len(re.sub(r'\D', '', phone)) >= 10:
                    phones.add(phone)
                    print(f"   📞 Found Skype → {phone}")
            
            # ✅ FIX 3: Skip social media links (they have numbers but aren't phones!)
            elif any(social in href for social in ['facebook.com', 'twitter.com', 'linkedin.com', 
                                                    'instagram.com', 'youtube.com', 'tiktok.com']):
                continue  # Skip these!
            
            # Pattern 5: Generic numbers in URLs (ONLY if not social media)
            elif not any(social in href for social in ['facebook', 'twitter', 'linkedin', 'instagram']):
                # Only extract if URL looks phone-related
                if any(keyword in href for keyword in ['phone', 'tel', 'call', 'contact']):
                    numbers = re.findall(r'\d{10,15}', href)
                    for num in numbers:
                        if 10 <= len(num) <= 15:
                            phones.add(num)
                            print(f"   📞 Found in URL → {num}")
        
        # Check data attributes
        for elem in self.soup.find_all(attrs={'data-phone': True}):
            phone = elem.get('data-phone', '').strip()
            phone = re.sub(r'[^\d\+\(\)\-]', '', phone)  # No spaces!
            if len(re.sub(r'\D', '', phone)) >= 10:
                phones.add(phone)
                print(f"   📞 Found data-phone → {phone}")
        
        for elem in self.soup.find_all(attrs={'data-tel': True}):
            phone = elem.get('data-tel', '').strip()
            phone = re.sub(r'[^\d\+\(\)\-]', '', phone)  # No spaces!
            if len(re.sub(r'\D', '', phone)) >= 10:
                phones.add(phone)
                print(f"   📞 Found data-tel → {phone}")
        
        # ✅ NEW: Check itemprop="telephone"
        for elem in self.soup.find_all(itemprop='telephone'):
            phone = elem.get_text(strip=True)
            phone = re.sub(r'[^\d\+\(\)\-]', '', phone)  # No spaces!
            digit_count = len(re.sub(r'\D', '', phone))
            if 10 <= digit_count <= 15:
                phones.add(phone)
                print(f"   📞 Found itemprop=telephone → {phone}")
        
        return phones
    
    def debug_phone_extraction(self):
        """Debug: Show ALL potential phone sources"""
        print("\n" + "="*60)
        print("🔍 DEBUGGING PHONE EXTRACTION")
        print("="*60)
        
        # 1. Find ALL tel: links
        print("\n1️⃣ Checking tel: links...")
        tel_links = self.soup.find_all('a', href=re.compile(r'^tel:', re.I))
        print(f"   Found {len(tel_links)} tel: links")
        for link in tel_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            print(f"   - href: {href}")
            print(f"     text: {text}")
            print(f"     parent: {link.parent.get('class', 'no-class')}")
        
        # 2. Check data attributes
        print("\n2️⃣ Checking data-* attributes...")
        data_attrs = ['data-p', 'data-pdisplay', 'data-phone', 'data-tel']
        for attr in data_attrs:
            elements = self.soup.find_all(attrs={attr: True})
            if elements:
                print(f"   Found {len(elements)} elements with {attr}")
                for elem in elements[:3]:  # Show first 3
                    print(f"   - {attr}: {elem.get(attr, '')[:50]}")
        
        # 3. Check hidden elements
        print("\n3️⃣ Checking hidden containers...")
        hidden = self.soup.find_all(style=re.compile(r'display:\s*none', re.I))
        print(f"   Found {len(hidden)} hidden elements")
        for elem in hidden[:3]:
            inner_links = elem.find_all('a', href=True)
            if inner_links:
                print(f"   - Hidden container has {len(inner_links)} links")
                for link in inner_links:
                    print(f"     → {link.get('href', '')}")
        
        # 4. Check itemprop
        print("\n4️⃣ Checking itemprop...")
        tel_props = self.soup.find_all(itemprop=re.compile(r'telephone|faxNumber', re.I))
        print(f"   Found {len(tel_props)} itemprop elements")
        for elem in tel_props:
            print(f"   - itemprop: {elem.get('itemprop')}")
            print(f"     href: {elem.get('href', 'N/A')}")
            print(f"     text: {elem.get_text(strip=True)}")
        
        print("\n" + "="*60 + "\n")

    def decode_machineryzone_phone(self, encoded: str) -> Optional[str]:
        """
        ✅ IMPROVED: Better phone number decoding
        """
        if not encoded or len(encoded) < 16:
            return None
        
        import base64
        
        # Try multiple strategies
        strategies = [
            encoded[-24:],   # Last 24 chars (original)
            encoded[-20:],   # Last 20 chars
            encoded[-32:],   # Last 32 chars (some sites use longer)
        ]
        
        for phone_part in strategies:
            try:
                # Add padding if needed
                padding = (4 - len(phone_part) % 4) % 4
                phone_part_padded = phone_part + "=" * padding
                
                decoded = base64.b64decode(phone_part_padded).decode('utf-8', errors='ignore')
                
                # Extract ALL digits (including leading zeros)
                digits = re.findall(r'\d+', decoded)
                if not digits:
                    continue
                
                # Join all digit groups
                full_number = ''.join(digits)
                
                # ✅ FIX: Handle duplicate digits at start
                if len(full_number) == 11 and full_number[0] == full_number[1]:
                    full_number = full_number[1:]
                
                # Validate: Must be 10-15 digits
                if 10 <= len(full_number) <= 15:
                    print(f"   🔓 Decoded: {encoded[:10]}...{encoded[-10:]} → {full_number}")
                    return full_number
            
            except Exception:
                continue
        
        return None


    def extract_hidden_phones(self) -> Set[str]:
        """
        Extract phone numbers from MachineryZone's encoded attributes
        ✅ FIXED: Now properly returns decoded phones
        """
        phones = set()
        
        print("   🔍 Decoding MachineryZone phone data...")
        
        # Decode data-p attributes
        for elem in self.soup.find_all(attrs={'data-p': True}):
            encoded = elem.get('data-p', '')
            decoded = self.decode_machineryzone_phone(encoded)
            
            if decoded:
                # ✅ FIX: Format international numbers properly
                if decoded.startswith('00'):
                    # Convert 00 to +
                    formatted = '+' + decoded[2:]
                elif len(decoded) == 10:
                    # US format: XXX-XXX-XXXX
                    formatted = f"{decoded[:3]}-{decoded[3:6]}-{decoded[6:]}"
                else:
                    # Keep as-is for international
                    formatted = decoded
                
                phones.add(formatted)
                print(f"   ✅ Decoded phone: {formatted}")
        
        # Decode data-pdisplay attributes
        for elem in self.soup.find_all(attrs={'data-pdisplay': True}):
            encoded = elem.get('data-pdisplay', '')
            decoded = self.decode_machineryzone_phone(encoded)
            
            if decoded:
                if decoded.startswith('00'):
                    formatted = '+' + decoded[2:]
                elif len(decoded) == 10:
                    formatted = f"{decoded[:3]}-{decoded[3:6]}-{decoded[6:]}"
                else:
                    formatted = decoded
                
                phones.add(formatted)
                print(f"   ✅ Decoded phone: {formatted}")
        
        # ✅ NEW: Also check for hidden tel: links
        for link in self.soup.find_all('a', href=re.compile(r'^tel:', re.I)):
            href = link.get('href', '')
            # Check if it's encoded
            if 'data-p' in link.attrs or 'data-pdisplay' in link.attrs:
                continue  # Already handled above
            
            # Regular tel: link
            phone = re.sub(r'^tel:?/*', '', href, flags=re.IGNORECASE)
            phone = re.sub(r'[^\d\+]', '', phone)
            
            if 10 <= len(phone) <= 15:
                phones.add(phone)
                print(f"   ✅ Found tel: link → {phone}")
        
        if phones:
            print(f"   ✅ Total decoded phones: {len(phones)}")
        else:
            print(f"   ⚠️ No phones found in encoded data")
        
        return phones

    # ========================================================================
    # LAYER 1: FAST RULES (90% of data, instant)
    # ========================================================================
    
    def layer1_extract_phones(self) -> Set[str]:
        """Layer 1: Fast phone extraction (including hidden numbers)"""
        
        # NEW: Extract hidden phones first!
        phones = self.extract_hidden_phones()
        
        print(f"   Found {len(phones)} hidden phones")
        
        # Also check visible elements
        for elem in self.soup.find_all(itemprop='telephone'):
            phone = elem.get_text(strip=True)
            phone = re.sub(r'[^\d\+\(\)\-]', '', phone)
            if len(re.sub(r'\D', '', phone)) >= 10:
                phones.add(phone)
        
        # Check common class names
        phone_classes = ['phone', 'telephone', 'tel', 'contact-phone', 'mobile']
        for class_name in phone_classes:
            for elem in self.soup.find_all(class_=re.compile(class_name, re.I)):
                text = elem.get_text(strip=True)
                phone = re.sub(r'[^\d\+\(\)\-]', '', text)
                if len(re.sub(r'\D', '', phone)) >= 10:
                    phones.add(phone)
        
        return phones
    
    
    def layer1_extract_emails(self) -> Set[str]:
        """Layer 1: Fast email extraction"""
        emails = set()
        
        # Method 1: mailto: links
        for link in self.soup.find_all('a', href=re.compile(r'mailto:', re.I)):
            email = link.get('href', '').replace('mailto:', '').strip()
            if '@' in email and '.' in email:
                emails.add(email.lower())
        
        # Method 2: itemprop="email"
        for elem in self.soup.find_all(itemprop='email'):
            email = elem.get_text(strip=True)
            if '@' in email:
                emails.add(email.lower())
        
        # Method 3: data-email attributes
        for elem in self.soup.find_all(attrs={'data-email': True}):
            email = elem.get('data-email', '').strip()
            if '@' in email:
                emails.add(email.lower())
        
        return emails
    
    
    def layer1_extract_websites(self) -> Set[str]:
        """Layer 1: Fast website URL extraction"""
        websites = set()
        
        # Look for external links
        for link in self.soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Must be http/https
            if not href.startswith('http'):
                continue
            
            # Skip social media
            social = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 'youtube.com']
            if any(s in href for s in social):
                continue
            
            # Skip current domain (not external)
            # This is a simple check, improve as needed
            
            websites.add(href)
        
        return websites
    
    
    # ========================================================================
    # LAYER 2: DEEP PATTERN MATCHING (Search entire HTML)
    # ========================================================================
    
    def layer2_extract_phones(self) -> Set[str]:
        """Layer 2: Deep regex search for phone patterns"""
        phones = set()
        
        # # First, check ALL href attributes (even hidden ones)
        # for link in self.soup.find_all('a', href=True):
        #     href = link.get('href', '')
        #     
        #     # Skip social media
        #     if any(s in href.lower() for s in ['facebook', 'twitter', 'linkedin', 'instagram']):
        #         continue
        #     
        #     # Look for tel: links
        #     if href.lower().startswith('tel'):
        #         phone = re.sub(r'^tel:?/*', '', href, flags=re.IGNORECASE)
        #         phone = re.sub(r'[^\d]', '', phone)
        #         
        #         if 10 <= len(phone) <= 15:
        #             phones.add(phone)
        #             print(f"   📞 Layer2: Found tel: → {phone}")
        
        # Get all text from HTML (including hidden)
        all_text = self.soup.get_text()
        
        # Phone patterns (international + local)
        patterns = [
            r'\+?\d{1,4}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}',
            r'\(\d{3}\)\s?\d{3}[-\s]?\d{4}',
            r'\d{3}[-\s]\d{3}[-\s]\d{4}',
            r'\+92[\s\-]?\d{2,4}[\s\-]?\d{6,8}',  # Pakistan
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                cleaned = re.sub(r'[^\d\+\(\)\-]', '', match)  # ✅ NO SPACES!
                digit_count = len(re.sub(r'\D', '', cleaned))
                if 10 <= digit_count <= 15:
                    phones.add(cleaned.strip())
        
        # ✅ NEW: Also check href attributes for numbers (but skip social media!)
        for link in self.soup.find_all('a', href=True):
            href = link.get('href', '')
            
            # Skip social media
            if any(s in href.lower() for s in ['facebook', 'twitter', 'linkedin', 'instagram']):
                continue
            
            # Look for phone patterns in URLs
            phone_in_url = re.findall(r'[\+\d]{10,15}', href)
            for phone in phone_in_url:
                digit_count = len(re.sub(r'\D', '', phone))
                if 10 <= digit_count <= 15:
                    # Clean it
                    cleaned = re.sub(r'[^\d\+\(\)\-]', '', phone)
                    phones.add(cleaned)
                    print(f"   📞 Layer2: Found in href → {cleaned}")
        
        return phones
    
    
    def layer2_extract_emails(self) -> Set[str]:
        """Layer 2: Deep regex search for email patterns"""
        emails = set()
        
        all_text = self.soup.get_text()
        
        # Email pattern
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        matches = re.findall(pattern, all_text)
        for email in matches:
            # Validate
            if email.count('@') == 1 and email.count('.') >= 1:
                emails.add(email.lower())
        
        return emails
    
    
    # ========================================================================
    # LAYER 3: LLM VERIFICATION (Check if data is valid)
    # ========================================================================
    
    def layer3_verify_with_llm(self, field_type: str, candidates: Set[str]) -> Set[str]:
        """
        Layer 3: Use LLM to verify extracted data
        
        Why? Because sometimes we extract:
        - Phone: "123-456-7890" but it's actually a fax or fake
        - Email: "noreply@example.com" (not useful)
        - Website: Internal link, not company website
        """
        
        if not candidates or len(candidates) == 0:
            return set()
        
        # Only verify if we have few candidates (save tokens)
        if len(candidates) > 10:
            return candidates  # Trust Layer 1+2 for large sets
        
        system_prompt = f"""You are a data validator. 
Check if these {field_type}s are REAL and USEFUL.

Rules:
- Remove fake/placeholder data
- Remove "noreply@" or "no-reply@" emails
- Remove obvious test data
- Keep only real, useful {field_type}s

Return JSON: {{"valid": ["item1", "item2"], "removed": ["fake1"]}}"""

        user_prompt = f"""Candidates: {list(candidates)}

Which are REAL {field_type}s? Return JSON."""

        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(completion.choices[0].message.content)
            valid = set(result.get("valid", []))
            
            if valid:
                print(f"✅ LLM verified {len(valid)}/{len(candidates)} {field_type}s")
                return valid
            
        except Exception as e:
            print(f"⚠️ LLM verification failed: {e}")
        
        # Fallback: return original
        return candidates
    
    
    # ========================================================================
    # MASTER EXTRACT (Combines all 3 layers)
    # ========================================================================
    
    def extract_all(self, use_llm_verification: bool = True) -> Dict[str, List[str]]:
        """
        Master extraction using all 3 layers
        
        Returns:
            {
                "phones": ["phone1", "phone2"],
                "emails": ["email1", "email2"],
                "websites": ["url1", "url2"],
                "confidence": 0.95
            }
        """
        
        print("📊 Multi-Layer Extraction Started")
        
        # Layer 1: Fast extraction
        print("⚡ Layer 1: Fast rules...")
        layer1_phones = self.layer1_extract_phones()
        layer1_emails = self.layer1_extract_emails()
        layer1_websites = self.layer1_extract_websites()
        
        print(f"  Found: {len(layer1_phones)} phones, {len(layer1_emails)} emails")
        
        # Layer 2: Deep pattern search (only if Layer 1 found few results)
        print("🔍 Layer 2: Deep patterns...")
        layer2_phones = set()
        layer2_emails = set()
        
        if len(layer1_phones) < 3:
            layer2_phones = self.layer2_extract_phones()
            print(f"  Found: {len(layer2_phones)} additional phones")
        
        if len(layer1_emails) < 2:
            layer2_emails = self.layer2_extract_emails()
            print(f"  Found: {len(layer2_emails)} additional emails")
        
        # Combine Layer 1 + Layer 2
        all_phones = layer1_phones.union(layer2_phones)
        all_emails = layer1_emails.union(layer2_emails)
        all_websites = layer1_websites
        
        # Layer 3: LLM verification (optional, for accuracy)
        if use_llm_verification and (all_phones or all_emails):
            print("🤖 Layer 3: LLM verification...")
            
            if all_phones:
                all_phones = self.layer3_verify_with_llm("phone", all_phones)
            
            if all_emails:
                all_emails = self.layer3_verify_with_llm("email", all_emails)
        
        # Calculate confidence
        confidence = 0.95 if (all_phones and all_emails) else 0.8 if (all_phones or all_emails) else 0.5
        
        result = {
            "phones": sorted(list(all_phones)),
            "emails": sorted(list(all_emails)),
            "websites": sorted(list(all_websites))[:5],  # Limit to top 5
            "confidence": confidence,
            "extraction_method": "multi_layer"
        }
        
        print(f"✅ Final: {len(result['phones'])} phones, {len(result['emails'])} emails (confidence: {confidence:.0%})")
        
        return result


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def extract_with_multi_layer(html: str, fields: List[str] = None) -> Dict:
    """
    Easy-to-use function for multi-layer extraction
    
    Usage:
        result = extract_with_multi_layer(html, fields=["phone", "email"])
    """
    
    extractor = MultiLayerExtractor(html)
    result = extractor.extract_all(use_llm_verification=True)
    
    # Filter to requested fields if specified
    if fields:
        filtered = {}
        for field in fields:
            if field in result:
                filtered[field] = result[field]
        return filtered
    
    return result
