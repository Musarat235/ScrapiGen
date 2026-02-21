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
    .stats-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stats-card h3 {
        margin: 0;
        font-size: 2rem;
    }
    .stats-card p {
        margin: 0.3rem 0 0 0;
        color: #aaa;
        font-size: 0.85rem;
    }
    .clean-banner {
        background: linear-gradient(135deg, #0f3d0f 0%, #1a472a 100%);
        border: 1px solid #2d6a2d;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    .stage-msg {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.95rem;
        color: #ccc;
        margin-top: 0.3rem;
    }
    .stage-msg .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4fc3f7;
        animation: pulse-dot 1.2s ease-in-out infinite;
    }
    .url-tracker {
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.2rem;
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
    4. Clean & enrich with one click
    
    **v1.0 Beta** - Free tier
    """)
    
    st.divider()
    
    st.header("Example Prompts")
    st.code("Extract product name, price, and rating")
    st.code("Get all article titles and dates")
    st.code("Find contact email and phone number")

# Initialize session state for enrichment flow
if "raw_results" not in st.session_state:
    st.session_state.raw_results = None
if "enrichment_stats" not in st.session_state:
    st.session_state.enrichment_stats = None
if "cleaned_results" not in st.session_state:
    st.session_state.cleaned_results = None
if "scrape_done" not in st.session_state:
    st.session_state.scrape_done = False

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


# ============================================================================
# HELPER: Collect flat data records from scrape results for enrichment
# ============================================================================
def _collect_data_records(results):
    """Extract all data dicts from the scrape results structure."""
    records = []
    for r in results:
        if not r.get("success"):
            continue
        data = r.get("data", [])
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    records.append(item)
        elif isinstance(data, dict):
            records.append(data)
    return records


# ============================================================================
# HELPER: Display results (used for both raw and cleaned)
# ============================================================================
def _display_results(results, label_prefix=""):
    """Show results as expanders with JSON + DataFrame + download."""
    for idx, result in enumerate(results):
        with st.expander(f"🔗 {result.get('url', f'Record {idx+1}')}", expanded=(idx == 0)):
            if result.get("success"):
                data = result.get("data", {})
                st.json(data)
                
                items = data if isinstance(data, list) else data.get("data", data) if isinstance(data, dict) else []
                if isinstance(items, list) and items:
                    try:
                        df = pd.DataFrame(items)
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            f"📥 Download CSV",
                            csv,
                            f"ScrapiGen_{label_prefix}{idx}.csv",
                            "text/csv",
                            key=f"dl_{label_prefix}{idx}"
                        )
                    except Exception:
                        pass
            else:
                st.error(f"Error: {result.get('error')}")


# ============================================================================
# SCRAPE BUTTON
# ============================================================================
if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
    # Reset enrichment state for new scrape
    st.session_state.raw_results = None
    st.session_state.enrichment_stats = None
    st.session_state.cleaned_results = None
    st.session_state.scrape_done = False
    
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
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        stage_text = st.empty()
                        
                        max_attempts = 120
                        attempt = 0
                        
                        while attempt < max_attempts:
                            time.sleep(1)
                            attempt += 1
                            
                            status_response = requests.get(f"{API_URL}/job/{job_id}")
                            
                            if status_response.status_code == 200:
                                job_status = status_response.json()
                                
                                if job_status["status"] == "completed":
                                    progress_bar.progress(100)
                                    status_text.success("✅ Scraping completed!")
                                    stage_text.empty()
                                    
                                    results = job_status.get("results", [])
                                    st.session_state.raw_results = results
                                    st.session_state.scrape_done = True
                                    
                                    # --- Analyze for stats ---
                                    data_records = _collect_data_records(results)
                                    if data_records:
                                        try:
                                            analyze_resp = requests.post(
                                                f"{API_URL}/enrichment/analyze",
                                                json={"data": data_records},
                                                timeout=15
                                            )
                                            if analyze_resp.status_code == 200:
                                                st.session_state.enrichment_stats = analyze_resp.json()
                                        except Exception:
                                            pass  # stats are nice-to-have
                                    
                                    break
                                
                                elif job_status["status"] == "failed":
                                    progress_bar.progress(100)
                                    status_text.error("❌ Scraping failed")
                                    stage_text.empty()
                                    st.error(job_status.get("error", "Unknown error"))
                                    break
                                
                                else:
                                    # --- Stage-aware progress ---
                                    api_progress = job_status.get("progress", 0)
                                    stage = job_status.get("stage", "⏳ Processing…")
                                    urls_done = job_status.get("urls_completed", 0)
                                    urls_total = job_status.get("urls_total", len(urls_list))
                                    
                                    progress_bar.progress(min(api_progress, 95))
                                    status_text.info(stage)
                                    
                                    if urls_total > 0:
                                        stage_text.markdown(
                                            f'<div class="url-tracker">'
                                            f'📄 URLs processed: {urls_done} / {urls_total}'
                                            f'</div>',
                                            unsafe_allow_html=True
                                        )
                        
                        if attempt >= max_attempts:
                            st.warning("⏱️ Job is taking longer than expected. Check back later.")
                            st.info(f"Job ID: {job_id}")
                    
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


# ============================================================================
# DISPLAY RESULTS + ENRICHMENT FLOW
# ============================================================================
if st.session_state.scrape_done and st.session_state.raw_results:
    results = st.session_state.raw_results
    
    st.subheader("📊 Raw Scraped Data")
    
    # Success/Fail summary
    success_count = sum(1 for r in results if r.get("success"))
    fail_count = len(results) - success_count
    
    col1, col2 = st.columns(2)
    col1.metric("✅ Successful", success_count)
    col2.metric("❌ Failed", fail_count)
    
    # Show raw results
    _display_results(results, label_prefix="raw_")
    
    # ================================================================
    # ENRICHMENT STATS BLOCK
    # ================================================================
    stats = st.session_state.enrichment_stats
    if stats and stats.get("total_issues", 0) > 0:
        st.divider()
        st.subheader("🔍 Data Quality Report")
        
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>🔄 {stats.get('duplicates_found', 0)}</h3>
                <p>Duplicates Found</p>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            st.markdown(f"""
            <div class="stats-card">
                <h3>📱 {stats.get('phones_to_fix', 0)}</h3>
                <p>Phones to Format</p>
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            st.markdown(f"""
            <div class="stats-card">
                <h3>📧 {stats.get('emails_to_fix', 0)}</h3>
                <p>Emails to Fix</p>
            </div>
            """, unsafe_allow_html=True)
        
        with c4:
            st.markdown(f"""
            <div class="stats-card">
                <h3>🌐 {stats.get('urls_to_fix', 0)}</h3>
                <p>URLs to Fix</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        
        # CLEAN DATA BUTTON
        if st.session_state.cleaned_results is None:
            if st.button("🧹 Clean Data", type="primary", use_container_width=True, key="clean_btn"):
                with st.spinner("🧹 Cleaning and enriching data..."):
                    data_records = _collect_data_records(results)
                    try:
                        clean_resp = requests.post(
                            f"{API_URL}/enrichment/clean",
                            json={
                                "data": data_records,
                                "stages": ["normalize", "deduplicate"]
                            },
                            timeout=30
                        )
                        if clean_resp.status_code == 200:
                            st.session_state.cleaned_results = clean_resp.json()
                            st.rerun()
                        else:
                            st.error("Failed to clean data. Please try again.")
                    except Exception as e:
                        st.error(f"Enrichment error: {str(e)}")
    
    elif stats and stats.get("total_issues", 0) == 0:
        st.divider()
        st.success("✨ Data looks clean! No duplicates or formatting issues detected.")
    
    # ================================================================
    # SHOW CLEANED DATA (after user clicked Clean Data)
    # ================================================================
    if st.session_state.cleaned_results is not None:
        cleaned = st.session_state.cleaned_results
        
        st.divider()
        st.markdown('<div class="clean-banner">', unsafe_allow_html=True)
        st.subheader("✨ Cleaned & Enriched Data")
        
        # Before → After metrics
        bc1, bc2, bc3 = st.columns(3)
        bc1.metric("Original Records", cleaned.get("original_count", 0))
        bc2.metric("After Cleaning", cleaned.get("enriched_count", 0))
        bc3.metric(
            "Duplicates Removed",
            cleaned.get("duplicates_removed", 0)
        )
        
        stages = cleaned.get("stages_applied", [])
        st.success(f"✅ Applied: {', '.join(s.title() for s in stages)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Show cleaned data as a DataFrame
        cleaned_data = cleaned.get("data", [])
        if cleaned_data:
            try:
                df = pd.DataFrame(cleaned_data)
                st.dataframe(df, use_container_width=True)
                
                # Download cleaned CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download Cleaned CSV",
                    csv,
                    "ScrapiGen_cleaned.csv",
                    "text/csv",
                    use_container_width=True,
                    key="dl_cleaned_csv"
                )
            except Exception:
                st.json(cleaned_data)
        
        # Download cleaned JSON
        cleaned_json = json.dumps(cleaned_data, indent=2)
        st.download_button(
            "📥 Download Cleaned JSON",
            cleaned_json,
            "ScrapiGen_cleaned.json",
            "application/json",
            use_container_width=True,
            key="dl_cleaned_json"
        )
    
    # ================================================================
    # DOWNLOAD RAW (always available)
    # ================================================================
    st.divider()
    all_results_json = json.dumps(results, indent=2)
    st.download_button(
        "📥 Download Raw Results (JSON)",
        all_results_json,
        "ScrapiGen_raw_results.json",
        "application/json",
        use_container_width=True,
        key="dl_raw_json"
    )

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    Made with ❤️ | ScrapiGen v1.0 Beta | Free Tier: 10 URLs per job
</div>
""", unsafe_allow_html=True)
