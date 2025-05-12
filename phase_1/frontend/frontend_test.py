import streamlit as st
import pandas as pd
import time
import sys
import os

# Setup environment and import background scraper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.background import start_background_scraping  # <-- adjust if path/module differs

st.set_page_config(page_title="Lead Scraper", layout="wide")
st.title("📊 Real-Time Lead Scraper Dashboard")

# --- Session State Init ---
if 'get_processed' not in st.session_state:
    st.session_state.get_processed = None
if 'is_scraping' not in st.session_state:
    st.session_state.is_scraping = False
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()

# --- Sidebar ---
st.sidebar.header("Scraper Settings")
industry = st.sidebar.text_input("Industry", value="dentist")
location = st.sidebar.text_input("Location", value="San Diego, CA")
start_button = st.sidebar.button("🚀 Start Scraping", disabled=st.session_state.is_scraping)

# --- Start Scraper ---
if start_button and not st.session_state.is_scraping:
    st.session_state.get_processed = start_background_scraping(industry, location)
    st.session_state.is_scraping = True
    st.rerun()

# --- Scraper Status Loop ---
if st.session_state.is_scraping:
    status_box = st.empty()
    data_box = st.empty()

    while st.session_state.is_scraping:
        raw_data = st.session_state.get_processed()

        if raw_data:
            elapsed = raw_data["elapsed_time"]
            total = raw_data["total_scraped"]
            processed = raw_data["processed_data"]

            with status_box:
                st.info(f"⏱ Elapsed: {elapsed:.2f}s | ✅ Scraped: {total} | 🧹 Processed: {len(processed)}")

            if processed:
                df = pd.DataFrame(processed)
                st.session_state.raw_data = df
                with data_box:
                    st.dataframe(df, use_container_width=True)

            if raw_data["is_complete"]:
                st.session_state.is_scraping = False
                st.success("✅ Scraping complete!")
                break
        else:
            with status_box:
                st.info("⏳ Initializing scraper...")
        time.sleep(2)
        st.rerun()

# --- Display Results if Any ---
if not st.session_state.raw_data.empty and not st.session_state.is_scraping:
    st.markdown("### 🎯 Scraped Results")
    st.dataframe(st.session_state.raw_data, use_container_width=True)
