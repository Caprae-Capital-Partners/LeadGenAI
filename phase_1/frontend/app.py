import streamlit as st
import pandas as pd
import asyncio
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
SERVICES_DIR = os.path.join(BASE_DIR, 'services')

sys.path.append(BASE_DIR)
sys.path.append(SERVICES_DIR)

# Import scrapers
from google_maps_scraper import scrape_lead_by_industry
from overview_scraper_hf import AsyncCompanyScraper

st.set_page_config(page_title="Lead Scraper", layout="wide")
st.title("🔍 LeadGenAI Scraper")

industry = st.text_input("🏢 Industry", placeholder="e.g. Construction companies")
location = st.text_input("📍 Location", placeholder="e.g. Glendale, AZ")

# ---------- Main Scraper Section ----------
if st.button("🚀 Run Scraper"):
    if industry and location:
        with st.spinner("Launching and navigating browser..."):
            try:
                progress = st.progress(0)
                status = st.empty()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                leads = loop.run_until_complete(
                    scrape_lead_by_industry(industry, location)
                )
                loop.close()

                if not leads:
                    st.warning("No leads found.")
                    st.stop()

                df = pd.DataFrame(leads)
                st.session_state["original_leads"] = df
                st.success(f"✅ Scraped {len(df)} leads!")

            except Exception as e:
                st.error(f"❌ Scraping failed: {e}")
    else:
        st.warning("Please enter both industry and location.")

# ---------- Display & Filter Leads ----------
if "original_leads" in st.session_state:
    df = st.session_state["original_leads"]

    st.subheader("📊 Filters")
    col1, col2 = st.columns([1, 1])

    # Convert ratings
    def convert_rating(val):
        try:
            return float(val)
        except:
            return -1.0

    df["Rating_float"] = df["Rating"].apply(convert_rating)

    available_industries = sorted(df["Industry"].dropna().unique().tolist())

    # Initialize filter session state only before widgets render
    if "rating_slider" not in st.session_state:
        st.session_state["rating_slider"] = 0.0
    if "industry_multiselect" not in st.session_state:
        st.session_state["industry_multiselect"] = available_industries

    with col1:
        rating_slider = st.slider(
            "Minimum Rating (NA = unrated)",
            0.0, 5.0,
            value=st.session_state["rating_slider"],
            step=0.1,
            key="rating_slider"
        )

    with col2:
        st.markdown(
            """
            <style>
            div[data-baseweb="select"] > div {
                max-height: 50px;
                overflow-y: auto;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        new_selection = st.multiselect(
            "Select Industries",
            options=available_industries,
            default=st.session_state["industry_multiselect"],
            key="industry_multiselect_internal"
        )

    # Safely update session state *after* widget renders
    st.session_state["industry_multiselect"] = new_selection
 
    if st.button("🔄 Reset Filters"):
        st.session_state["industry_multiselect"] = available_industries
        st.rerun()

    # Apply filtering
    selected_industries = st.session_state["industry_multiselect"]
    filtered_df = df[
        (df["Rating_float"] >= st.session_state["rating_slider"]) &
        (df["Industry"].isin(selected_industries))
    ].drop(columns=["Rating_float"])

    st.subheader("✏️ Edit Your Leads")

    # Merge enriched data if available
    if "edited_leads" in st.session_state:
        merged = pd.merge(filtered_df, st.session_state["edited_leads"], on="Name", how="left", suffixes=('', '_enriched'))
        if "Overview_enriched" in merged.columns:
            merged["Overview"] = merged["Overview_enriched"]
        df_to_edit = merged.drop(columns=[col for col in merged.columns if col.endswith("_enriched")])
    else:
        df_to_edit = filtered_df

    edited_df = st.data_editor(
        df_to_edit,
        use_container_width=True,
        num_rows="dynamic",
        key="lead_editor"
    )
    st.session_state["edited_leads"] = edited_df

    col_overview, _, col_download = st.columns([1, 6, 1])

    # ---------- Enrichment ----------
    with col_overview:
        if st.button("📄 Get Overviews"):
            st.info("Retrieving…")

            async def enrich_selected(df):
                scraper = AsyncCompanyScraper()
                enriched_rows = []
                for _, row in df.iterrows():
                    name = row.get("Name", "")
                    try:
                        result = await scraper.process_company(name)
                        row_dict = row.to_dict()
                        row_dict.update(result)
                    except Exception as e:
                        row_dict = row.to_dict()
                        row_dict["Overview"] = "NA"
                        print(f"Overview error for {name}: {e}")
                    enriched_rows.append(row_dict)
                return pd.DataFrame(enriched_rows)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            enriched_df = loop.run_until_complete(enrich_selected(edited_df))
            loop.close()

            st.session_state["edited_leads"] = enriched_df
            st.success("✅ Overviews generated.")
            st.rerun()

    # ---------- CSV Download ----------
    with col_download:
        csv = st.session_state["edited_leads"].to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Leads", csv, "leads.csv", "text/csv")