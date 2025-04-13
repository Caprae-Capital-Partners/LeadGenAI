import streamlit as st
import pandas as pd
import asyncio
import sys

sys.path.append("../backend")  # Adjust if needed
from google_maps_scraper import scrape_lead_by_industry  # No need to change your scraper!

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
                leads = asyncio.run(scrape_lead_by_industry(industry, location))
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