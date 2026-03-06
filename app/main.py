"""Main Streamlit application for Spanish State Budget Analysis."""

import streamlit as st

from utils.data_loader import load_spending_data
from pages import tab_policies, tab_timeline


# Page configuration
st.set_page_config(
    page_title="Presupuestos Generales del Estado",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
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


def initialize_session_state() -> None:
    """Initialize session state with data."""
    if "spending_data" not in st.session_state:
        try:
            with st.spinner("Cargando datos..."):
                st.session_state.spending_data = load_spending_data()
                st.success("Datos cargados correctamente")
        except FileNotFoundError as e:
            st.error(f"Error: {str(e)}")
            st.stop()


def main() -> None:
    """Main application entry point."""
    # Initialize data
    initialize_session_state()
    
    # Title and description
    st.title("💰 Presupuestos Generales del Estado")
    st.markdown(
        "Análisis interactivo de los Presupuestos Generales del Estado español (2011-2026)"
    )
    st.markdown("---")
    
    # Tab selection
    tab1, tab2 = st.tabs(
        ["📊 Gastos por Política", "📈 Evolución Temporal"]
    )
    
    with tab1:
        tab_policies.render()
    
    with tab2:
        tab_timeline.render()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: gray; font-size: 12px;">
            <p>Datos obtenidos de: 
            <a href="https://www.sepg.pap.hacienda.gob.es" target="_blank">
            Secretaría de Estado de Presupuestos y Gastos
            </a></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
