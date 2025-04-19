import streamlit as st
import pandas as pd
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import fetch_and_merge_data

st.set_page_config(page_title="LeadGenAI", layout="wide")
st.title("📊 LeadGen AI Tool")

st.markdown("#### Welcome to Caprae Capital's LeadGenAI Tool! 🐐")
st.markdown("Add your target industry and location to the sidebar, and hit '🚀 Fetch Leads'. Then, filter, edit, and download your leads!")

# --- Sidebar Inputs ---
st.sidebar.header("🔍 Search Criteria")
industry = st.sidebar.text_input("Industry", "dentist")
location = st.sidebar.text_input("Location", "San Diego, CA")
fetch_button = st.sidebar.button("🚀 Fetch Leads")

# --- State Initialization ---
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()
if 'industry_filter_selection' not in st.session_state:
    st.session_state.industry_filter_selection = []

# --- Fetch Leads ---
if fetch_button:
    with st.spinner("Scraping and merging data..."):
        raw_data = asyncio.run(fetch_and_merge_data(industry, location))
        df = pd.DataFrame(raw_data)
        st.session_state.raw_data = df
        st.session_state.industry_filter_selection = df["Industry"].dropna().unique().tolist()

# --- Display Leads + Filters ---
if not st.session_state.raw_data.empty:
    df = st.session_state.raw_data
    st.markdown("### 🎯 Filter by Industry")

    industry_options = df["Industry"].dropna().unique().tolist()

    # --- Handle select/deselect before rendering the widget
    if "apply_all" in st.session_state and st.session_state.apply_all:
        st.session_state.industry_filter_selection = industry_options
        st.session_state.apply_all = False
        st.rerun()
    if "clear_all" in st.session_state and st.session_state.clear_all:
        st.session_state.industry_filter_selection = []
        st.session_state.clear_all = False
        st.rerun()

    # --- Scrollable multiselect filter box
    st.markdown(
        "<style>div[data-baseweb=select] { max-height: 100px; overflow-y: auto; }</style>",
        unsafe_allow_html=True
    )

    selected_industries = st.multiselect(
        label="",
        options=industry_options,
        default=st.session_state.industry_filter_selection,
        key="industry_multiselect",
        label_visibility="collapsed"
    )

    st.session_state.industry_filter_selection = selected_industries

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Select All"):
            st.session_state.apply_all = True
            st.rerun()
    with col2:
        if st.button("❌ Deselect All"):
            st.session_state.clear_all = True
            st.rerun()

    # --- Filter DataFrame
    filtered_df = df[df["Industry"].isin(selected_industries)] if selected_industries else pd.DataFrame()

    st.markdown("### 📋 Leads Table")
    st.markdown(f"Total leads: {len(filtered_df)}")

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        key="editable_table",
        num_rows="dynamic"
    )

    st.download_button(
        "📥 Download as CSV",
        data=edited_df.to_csv(index=False),
        file_name="leads.csv",
        mime="text/csv"
    )