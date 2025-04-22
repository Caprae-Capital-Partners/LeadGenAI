import streamlit as st
import pandas as pd
import asyncio
import sys
import os

os.system('playwright install')

# Import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import fetch_and_merge_data
from backend.services.parser import parse_address  # <-- Address parser

st.set_page_config(page_title="LeadGenAI", layout="wide")
st.title("📊 LeadGen AI Tool")

st.markdown("#### Welcome to Caprae Capital's LeadGenAI Tool! 🐐")
st.markdown("Add your target industry and location to the sidebar, and hit '🚀 Fetch Leads'. Then, filter, edit, and download your leads!")

# --- Sidebar Inputs ---
st.sidebar.header("🔍 Search Criteria")
industry = st.sidebar.text_input("Industry", placeholder="e.g. dentist")
location = st.sidebar.text_input("Location", placeholder="e.g. San Diego, CA")
fetch_button = st.sidebar.button("🚀 Fetch Leads")

# --- State Initialization ---
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()
if 'industry_filter_selection' not in st.session_state:
    st.session_state.industry_filter_selection = []
if "edited_data" not in st.session_state:
    st.session_state.edited_data = pd.DataFrame()
if "enriched_data" not in st.session_state:
    st.session_state.enriched_data = pd.DataFrame()

# --- Fetch Leads ---
if fetch_button:
    with st.spinner("Scraping and merging data..."):
        raw_data = asyncio.run(fetch_and_merge_data(industry, location))
        df = pd.DataFrame(raw_data)
        st.session_state.raw_data = df
        st.session_state.enriched_data = pd.DataFrame()  # Reset enrichment
        st.session_state.industry_filter_selection = df["Industry"].dropna().unique().tolist()

# --- Display Leads + Filters ---
if not st.session_state.raw_data.empty:
    df = st.session_state.raw_data
    st.markdown("### 🎯 Filter by Industry")

    industry_options = df["Industry"].dropna().unique().tolist()

    # Select/Deselect All Buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Select All"):
            st.session_state.industry_filter_selection = industry_options
            st.rerun()
    with col2:
        if st.button("❌ Deselect All"):
            st.session_state.industry_filter_selection = []
            st.rerun()

    st.markdown(
        "<style>div[data-baseweb=select] { max-height: 100px; overflow-y: auto; }</style>",
        unsafe_allow_html=True
    )

    selected_industries = st.multiselect(
        label="Filter by Industry",
        options=industry_options,
        default=st.session_state.industry_filter_selection,
        key="industry_multiselect",
        label_visibility="collapsed"
    )

    # Filter
    filtered_df = df[df["Industry"].isin(selected_industries)] if selected_industries else df.iloc[0:0]

    # Merge in enriched data (if any)
    if not st.session_state.enriched_data.empty:
        merged = pd.merge(filtered_df, st.session_state.enriched_data, on="Name", how="left", suffixes=('', '_enriched'))

        for col in ["Overview", "Products & Services", "Management", "Website"]:
            if f"{col}_enriched" in merged.columns:
                merged[col] = merged[f"{col}_enriched"]

        display_df = merged.drop(columns=[c for c in merged.columns if c.endswith("_enriched")])
    else:
        display_df = filtered_df

    st.markdown("### 📋 Leads Table")
    st.markdown(f"Total leads: {len(display_df)}")

    if "Name" in display_df.columns:
        display_df = display_df.sort_values(by="Name", key=lambda col: col.str.lower(), na_position='last').reset_index(drop=True)

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        key="leads_table",
        num_rows="dynamic",
        hide_index=True
    )
    st.session_state.edited_data = edited_df

    # --- Get Overviews ---
    if st.button("📄 Get Overviews"):
        if edited_df.empty:
            st.warning("No leads to enrich.")
        else:
            st.info("Scraping overviews...")

            async def enrich_selected(df):
                from backend.services.overview_scraper_hf import AsyncCompanyScraper
                scraper = AsyncCompanyScraper()
                enriched_rows = []

                for _, row in df.iterrows():
                    name = row.get("Name", "")
                    location = row.get("Address") or row.get("City", "")
                    row_dict = row.to_dict()
                    try:
                        enriched = await scraper.process_company(name, location)
                        row_dict.update(enriched)
                    except Exception as e:
                        row_dict["Overview"] = "Error"
                        row_dict["Products & Services"] = "Error"
                        print(f"Overview error for {name}: {e}")
                    enriched_rows.append(row_dict)
                return pd.DataFrame(enriched_rows)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            enriched_df = loop.run_until_complete(enrich_selected(edited_df))
            loop.close()

            st.session_state.enriched_data = enriched_df
            st.success("✅ Overviews added successfully!")
            st.rerun()

    # --- Enrich Contact Info (Website + Management) ---
    if st.button("🔍 Enrich Contact Info"):
        if edited_df.empty:
            st.warning("No leads to enrich.")
        else:
            st.info("Searching for contact info...")

            async def enrich_contact_info(df, loc):
                from backend.services.update_fields import update_websites, get_management_details
                records = df.to_dict(orient="records")
                updated_records = await update_websites(records, loc)

                company_tuples = [(rec["Name"], rec.get("Address", loc)) for rec in updated_records]
                management_info = await get_management_details(company_tuples)

                for i, rec in enumerate(updated_records):
                    people = management_info[i] if i < len(management_info) else []
                    if isinstance(people, list):
                        rec["Management"] = "; ".join(
                            [f'{p["name"]} ({p["title"]})' for p in people if isinstance(p, dict)]
                        ) if people else "NA"
                    else:
                        rec["Management"] = "NA"
                return pd.DataFrame(updated_records)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            enriched_df = loop.run_until_complete(enrich_contact_info(edited_df, location))
            loop.close()

            st.session_state.enriched_data = enriched_df
            st.success("✅ Contact info enriched!")
            st.rerun()

    # --- Download ---
    st.download_button(
        "📥 Download as CSV",
        data=st.session_state.edited_data.to_csv(index=False),
        file_name="leads.csv",
        mime="text/csv"
    )