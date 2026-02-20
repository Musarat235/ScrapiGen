# 🕸️ Web Scraper — User Guide

A smart web scraper that automatically handles Static, JavaScript-rendered pages, and bot protection. Just give it a URL and tell it what to extract.


## 💬 How to Write Prompts

The scraper accepts a **URL** and a **plain-English prompt** describing what you want to extract. No code needed.

### Product & E-Commerce

```
Extract product title and prices
```
```
Get the product name, original price, discounted price, and availability status
```
```
Extract all products on this page with their titles, prices, ratings, and image URLs
```
```
Get the product description and list of features/specifications
```

### Real Estate & Listings

```
Extract property title, price, location, number of bedrooms and bathrooms
```
```
Get all property listings with their area in square feet, price per sqft, and agent name
```
```
Extract the address, asking price, and date listed for each property
```

### Jobs & Careers

```
Extract job title, company name, location, and salary range
```
```
Get all job listings with their required experience, skills, and application deadline
```
```
Extract the full job description and list of responsibilities
```

### News & Articles

```
Extract the article headline, author, publish date, and full body text
```
```
Get all article titles and their summaries from this news page
```
```
Extract the main content of this blog post, ignoring ads and navigation
```

### General Data

```
Extract all table data from this page
```
```
Get every phone number and email address on this page
```
```
Extract the FAQ questions and their answers
```

---

## 📡 API Usage

### Single URL

```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://daraz.pk/products/some-product",
    "prompt": "Extract product title and prices"
  }'
```

### Response

```json
{
  "url": "https://daraz.pk/products/some-product",
  "data": {
    "product_title": "Samsung Galaxy S24",
    "original_price": "PKR 189,999",
    "discounted_price": "PKR 164,999"
  },
  "cached": false,
  "render_method": "playwright"
}
```

---

## ⚙️ What Happens Automatically

You don't need to configure anything. The scraper handles everything behind the scenes:

| Situation | What the scraper does |
|---|---|
| JavaScript-heavy site (React, Next.js) | Renders with a real browser |
| Cloudflare protection | Waits for the 5-second challenge to pass |
| Rate limiting | Backs off and retries with smart delays |
| Same URL requested again | Returns cached result instantly |
| 403 Access Denied | Retries with stealth mode |

---

## 🌐 Supported Sites

These sites are pre-configured for optimal scraping:

**Pakistan**
- OLX Pakistan (`olx.com.pk`)
- Daraz (`daraz.pk`)
- Zameen (`zameen.com`)
- PakWheels (`pakwheels.com`)
- Graana (`graana.com`)

**Global**
- Amazon, eBay
- Zillow, Realtor.com
- Airbnb

Other sites work too — the scraper auto-detects what's needed.

---

## 📝 Prompt Tips

**Be specific about fields you want:**
```
# ❌ Vague
"Get product info"

# ✅ Clear
"Extract product name, price in PKR, rating out of 5, and number of reviews"
```

**Mention the format if needed:**
```
"Extract all listings as a list, each with title, price, and location"
```

**For paginated data:**
```
"Extract all items on this page only — title, price, and seller name"
```

---

## 🔧 Configuration

Key settings in `config/settings.py`:

| Setting | Default | Description |
|---|---|---|
| `CACHE_TTL` | 3600s | How long to cache pages (1 hour) |
| `RENDER_TIMEOUT` | 20s | Max wait for JS rendering |
| `MAX_RETRIES` | 5 | Max retry attempts per URL |

---

## ❓ Troubleshooting

**"Access denied by website"**
The site has strong bot protection. The scraper will automatically retry with stealth mode. If it still fails, the site may require manual verification.

**"Failed to fetch"**
Check that the URL is correct and the site is accessible from your network.

**Slow response**
JS-rendered sites take 3–8 seconds on first load. Subsequent requests for the same URL return instantly from cache.

**Got empty or wrong data**
Try a more specific prompt. For example, instead of `"Get prices"`, use `"Extract the selling price in PKR shown below the product title"`.