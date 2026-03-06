"""Shared utilities for Streamlit pages."""

import pandas as pd
import streamlit as st

from utils.data_loader import load_spending_data


def initialize_page(page_title: str, page_icon: str = "💰") -> pd.DataFrame:
    """Initialize a page with common configuration and data loading.
    
    Args:
        page_title: Title for the page.
        page_icon: Icon for the page.
    
    Returns:
        Loaded spending DataFrame.
    """
    st.set_page_config(
        page_title=f"PGE - {page_title}",
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    
    # Custom CSS for metrics
    st.markdown(
        """
        <style>
        [data-testid="stMetricValue"] {
            font-size: 24px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Load data
    if "spending_data" not in st.session_state:
        try:
            with st.spinner("Cargando datos..."):
                st.session_state.spending_data = load_spending_data()
                st.success("Datos cargados correctamente")
        except FileNotFoundError as e:
            st.error(f"Error: {str(e)}")
            st.stop()
    
    return st.session_state.spending_data
