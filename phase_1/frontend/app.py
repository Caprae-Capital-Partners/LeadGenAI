import streamlit as st
import pandas as pd
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.append("phase_1")  # Adjust if needed
from backend.main import fetch_and_merge_data  # No need to change your scraper!

async def run_scraper(industry: str, location: str):
    return await fetch_and_merge_data(industry, location)

def run_async(func, *args):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        return asyncio.ensure_future(func(*args))  # Await later if needed
    else:
        return asyncio.run(func(*args))


st.set_page_config(page_title="Lead Scraper", layout="wide")
st.title("🔍 LeadGenAI Scraper")

# --- Input fields ---
industry = st.text_input("🏢 Industry", placeholder="e.g. Construction companies")
location = st.text_input("📍 Location", placeholder="e.g. Glendale, AZ")

# --- Run scraper ---
if st.button("🚀 Run Scraper"):
    if industry and location:
        with st.spinner("Scraping leads..."):
            try:
                leads = run_async(run_scraper, industry, location)
                if asyncio.isfuture(leads):  # We’re inside an async loop
                    leads = asyncio.run(leads)  # Wait for it
                if not leads:
                    st.warning("No leads found.")
                else:
                    df = pd.DataFrame(leads)
                    st.session_state["original_leads"] = df  # ✅ store in session state
                    st.success(f"Found {len(df)} leads!")
            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
    else:
        st.warning("Please enter both industry and location.")

# --- Display if data exists in session ---
if "original_leads" in st.session_state:
    df = st.session_state["original_leads"]

    st.subheader("📊 Filters")

    col1, col2 = st.columns(2)

    with col1:
        rating_slider = st.slider("Minimum Rating (NA = unrated)", 0.0, 5.0, 0.0, step=0.2)

    with col2:
        available_industries = sorted(df["Industry"].dropna().unique().tolist())
        selected_industries = st.multiselect("Select Industries", available_industries, default=available_industries)

    # Handle rating conversion
    def convert_rating(val):
        try:
            return float(val)
        except:
            return -1.0

    df["Rating_float"] = df["Rating"].apply(convert_rating)

    # Apply filters
    filtered_df = df[
        (df["Rating_float"] >= rating_slider) &
        (df["Industry"].isin(selected_industries))].drop(columns=["Rating_float"])
        
    st.subheader("✏️ Edit Your Leads")
    edited_df = st.data_editor(filtered_df, use_container_width=True, num_rows="dynamic", key="lead_editor")

    # Save back the edited version to session
    st.session_state["edited_leads"] = edited_df

    # --- Download ---
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Edited Leads", csv, "leads.csv", "text/csv")