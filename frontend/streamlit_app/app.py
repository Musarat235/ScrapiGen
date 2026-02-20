import streamlit as st
import requests
import time
import pandas as pd
import json

import os

# Configuration
API_URL = os.getenv("API_URL", "https://scrapigen.up.railway.app/")  # Change to your deployed API URL

st.set_page_config(
    page_title="ScrapiGen",
    page_icon="🕷️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🕷️ ScrapiGen</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Powered Web Scraping Made Simple</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("About")
    st.write("""
    ScrapiGen uses AI to extract data from any website.
    
    **How it works:**
    1. Paste URLs (max 10)
    2. Describe what you want
    3. Get structured data
    
    **v1.0 Beta** - Free tier
    """)
    
    st.divider()
    
    st.header("Example Prompts")
    st.code("Extract product name, price, and rating")
    st.code("Get all article titles and dates")
    st.code("Find contact email and phone number")

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Enter URLs")
    urls_input = st.text_area(
        "Paste URLs (one per line, max 10)",
        height=150,
        placeholder="https://example.com/product1\nhttps://example.com/product2\nhttps://example.com/product3"
    )

with col2:
    st.subheader("💬 What to Extract")
    prompt = st.text_area(
        "Describe the data you want",
        height=150,
        placeholder="Extract product name, price, and image URL"
    )

# Process URLs
if urls_input:
    urls_list = [url.strip() for url in urls_input.split('\n') if url.strip()]
    url_count = len(urls_list)
    
    if url_count > 10:
        st.error(f"⚠️ Too many URLs ({url_count}). Maximum 10 allowed in beta.")
    else:
        st.info(f"✅ {url_count} URL(s) ready to scrape")

# Scrape button
if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
    if not urls_input:
        st.error("Please enter at least one URL")
    elif not prompt:
        st.error("Please describe what data you want to extract")
    else:
        urls_list = [url.strip() for url in urls_input.split('\n') if url.strip()]
        
        if len(urls_list) > 10:
            st.error("Maximum 10 URLs allowed")
        else:
            with st.spinner("🔄 Creating scraping job..."):
                try:
                    # Create job
                    response = requests.post(
                        f"{API_URL}/scrape",
                        json={
                            "urls": urls_list,
                            "prompt": prompt,
                            "max_urls": 10
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        job_data = response.json()
                        job_id = job_data["job_id"]
                        
                        st.success(f"✅ Job created: {job_id}")
                        
                        # Progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Poll for results
                        max_attempts = 60  # 60 seconds max
                        attempt = 0
                        
                        while attempt < max_attempts:
                            time.sleep(1)
                            attempt += 1
                            
                            # Check status
                            status_response = requests.get(f"{API_URL}/job/{job_id}")
                            
                            if status_response.status_code == 200:
                                job_status = status_response.json()
                                
                                if job_status["status"] == "completed":
                                    progress_bar.progress(100)
                                    status_text.success("✅ Scraping completed!")
                                    
                                    # Display results
                                    st.subheader("📊 Results")
                                    
                                    results = job_status.get("results", [])
                                    
                                    # Success/Fail summary
                                    success_count = sum(1 for r in results if r.get("success"))
                                    fail_count = len(results) - success_count
                                    
                                    col1, col2 = st.columns(2)
                                    col1.metric("✅ Successful", success_count)
                                    col2.metric("❌ Failed", fail_count)
                                    
                                    # Show each result
                                    for idx, result in enumerate(results):
                                        with st.expander(f"🔗 {result['url']}", expanded=(idx==0)):
                                            if result.get("success"):
                                                data = result.get("data", {})
                                                
                                                # Display as JSON
                                                st.json(data)
                                                
                                                # Try to convert to DataFrame
                                                if "data" in data and isinstance(data["data"], list):
                                                    try:
                                                        df = pd.DataFrame(data["data"])
                                                        st.dataframe(df, use_container_width=True)
                                                        
                                                        # Download button
                                                        csv = df.to_csv(index=False)
                                                        st.download_button(
                                                            "📥 Download CSV",
                                                            csv,
                                                            f"ScrapiGen_{idx}.csv",
                                                            "text/csv"
                                                        )
                                                    except:
                                                        pass
                                            else:
                                                st.error(f"Error: {result.get('error')}")
                                    
                                    # Download all results as JSON
                                    st.divider()
                                    all_results_json = json.dumps(results, indent=2)
                                    st.download_button(
                                        "📥 Download All Results (JSON)",
                                        all_results_json,
                                        "ScrapiGen_results.json",
                                        "application/json",
                                        use_container_width=True
                                    )
                                    
                                    break
                                
                                elif job_status["status"] == "failed":
                                    progress_bar.progress(100)
                                    status_text.error("❌ Scraping failed")
                                    st.error(job_status.get("error", "Unknown error"))
                                    break
                                
                                else:
                                    # Still processing
                                    progress = min((attempt / max_attempts) * 100, 90)
                                    progress_bar.progress(int(progress))
                                    status_text.info(f"⏳ Processing... ({attempt}s)")
                        
                        if attempt >= max_attempts:
                            st.warning("⏱️ Job is taking longer than expected. Check back later.")
                            st.info(f"Job ID: {job_id}")
                    
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    Made with ❤️ | ScrapiGen v1.0 Beta | Free Tier: 10 URLs per job
</div>
""", unsafe_allow_html=True)

