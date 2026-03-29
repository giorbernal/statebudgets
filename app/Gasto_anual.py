"""Main Streamlit application - Gastos por Política visualization."""

import streamlit as st
import plotly.graph_objects as go

from utils.shared import initialize_page
from utils.data_loader import (
    get_years,
    get_spending_by_policy,
    get_spending_by_code_and_name,
    thousands_to_millions,
    format_millions,
)


# Initialize page
df = initialize_page("Gastos por Política", "📊")

# Initialize session state with explicit defaults
if "view_state" not in st.session_state:
    st.session_state.view_state = "main"  # "main" or "detail"
if "detail_policy" not in st.session_state:
    st.session_state.detail_policy = None
if "last_policy_select" not in st.session_state:
    st.session_state.last_policy_select = None

# Title and description
st.title("💰 Presupuestos Generales del Estado")
st.markdown(
    "Análisis interactivo de los Presupuestos Generales del Estado español (2011-2026)"
)
st.markdown("---")

# Year selector (always at the top)
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Selecciona el año para visualizar:**")

with col2:
    years = get_years(df)
    selected_year = st.selectbox(
        "Año",
        years,
        index=len(years) - 1,
        key="year_selector",
        label_visibility="collapsed",
    )

st.markdown("---")

# Get spending data for the year
spending_by_policy = get_spending_by_policy(df, selected_year)
policies_list = spending_by_policy["policy"].tolist()

# VIEW 1: Main view - Policy Level
if st.session_state.view_state == "main":
    st.header("📊 Gastos por Política de Gasto")
    
    # Convert amounts to millions for display
    spending_by_policy_display = spending_by_policy.copy()
    spending_by_policy_display["amount_millions"] = spending_by_policy_display["amount"].apply(thousands_to_millions)
    
    # Create treemap visualization with minimum colorscale at 0
    fig = go.Figure(
        go.Treemap(
            labels=spending_by_policy_display["policy"].tolist(),
            parents=[""] * len(spending_by_policy_display),
            values=spending_by_policy_display["amount_millions"].tolist(),
            marker=dict(
                colors=spending_by_policy_display["amount_millions"].tolist(),
                colorscale="Viridis",
                cmin=0,
                cmax=spending_by_policy_display["amount_millions"].max(),
                colorbar=dict(
                    title="Gasto (M€)",
                    tickformat=",.3f",
                    nticks=5,
                    tickvals=[i * spending_by_policy_display["amount_millions"].max() / 4 for i in range(5)],
                ),
            ),
            textposition="middle center",
            hovertemplate="<b>%{label}</b><br>Gasto: %{value:,.3f} M€<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=f"Distribución de Gastos por Política - Año {selected_year}",
        height=700,
        font=dict(size=11),
        margin=dict(t=50, l=0, r=0, b=0),
    )
    
    fig.update_traces(
        marker=dict(line=dict(width=2))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 Selecciona una política abajo para ver el desglose por código y nombre")
    
    # Selection of policy with manual trigger
    st.divider()
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**Selecciona una política:**")
    
    with col2:
        selected_policy_value = st.selectbox(
            "Política",
            policies_list,
            label_visibility="collapsed",
            index=0,
        )
    
    with col3:
        if st.button("📌 Ver desglose", key="button_detail"):
            st.session_state.detail_policy = selected_policy_value
            st.session_state.view_state = "detail"
            st.rerun()
    
    # Summary statistics
    st.divider()
    st.subheader("📈 Estadísticas del Año")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_spending = spending_by_policy["amount"].sum()
    top_policy = spending_by_policy.iloc[0]
    avg_spending = spending_by_policy["amount"].mean()
    num_policies = len(spending_by_policy)
    
    with col1:
        st.metric("Gasto Total", format_millions(total_spending))
    
    with col2:
        st.metric("Política Mayor", f"{top_policy['policy'][:30]}...")
    
    with col3:
        st.metric("Gasto Promedio", format_millions(avg_spending))
    
    with col4:
        st.metric("Num. Políticas", num_policies)
    
    # Detailed table
    st.subheader("📋 Detalle de Gastos")
    
    display_df = spending_by_policy.copy()
    display_df["amount"] = display_df["amount"].apply(format_millions)
    display_df.columns = ["Política de Gasto", "Gasto (M€)"]
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
    )

# VIEW 2: Detail view - Code Level
elif st.session_state.view_state == "detail":
    col1, col2 = st.columns([1, 9])
    
    with col1:
        if st.button("← Volver", key="button_back"):
            st.session_state.view_state = "main"
            st.session_state.detail_policy = None
            st.rerun()
    
    with col2:
        st.header(f"📊 Desglose: {st.session_state.detail_policy}")
    
    st.markdown("---")
    
    # Get spending by code and name for selected policy
    spending_by_code = get_spending_by_code_and_name(
        df,
        selected_year,
        st.session_state.detail_policy
    )
    
    # Convert amounts to millions for display
    spending_by_code_display = spending_by_code.copy()
    spending_by_code_display["amount_millions"] = spending_by_code_display["amount"].apply(thousands_to_millions)
    
    # Create combined label
    spending_by_code_display["label"] = (
        spending_by_code_display["code"].astype(str) + " - " +
        spending_by_code_display["name"].astype(str)
    )
    
    # Create treemap
    fig = go.Figure(
        go.Treemap(
            labels=spending_by_code_display["label"].tolist(),
            parents=[""] * len(spending_by_code_display),
            values=spending_by_code_display["amount_millions"].tolist(),
            marker=dict(
                colors=spending_by_code_display["amount_millions"].tolist(),
                colorscale="Viridis",
                cmin=0,
                cmax=spending_by_code_display["amount_millions"].max(),
                colorbar=dict(
                    title="Gasto (M€)",
                    tickformat=",.3f",
                    nticks=5,
                    tickvals=[i * spending_by_code_display["amount_millions"].max() / 4 for i in range(5)],
                ),
            ),
            textposition="middle center",
            hovertemplate="<b>%{label}</b><br>Gasto: %{value:,.3f} M€<extra></extra>",
        )
    )
    
    fig.update_layout(
        title=f"Distribución por Código y Nombre - {st.session_state.detail_policy} ({selected_year})",
        height=700,
        font=dict(size=11),
        margin=dict(t=50, l=0, r=0, b=0),
    )
    
    fig.update_traces(
        marker=dict(line=dict(width=2))
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.divider()
    st.subheader("📈 Estadísticas de la Política")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_spending = spending_by_code["amount"].sum()
    top_code = spending_by_code.iloc[0]
    avg_spending = spending_by_code["amount"].mean()
    num_codes = len(spending_by_code)
    
    with col1:
        st.metric("Gasto Total", format_millions(total_spending))
    
    with col2:
        st.metric("Concepto Mayor", f"{top_code['code']}")
    
    with col3:
        st.metric("Gasto Promedio", format_millions(avg_spending))
    
    with col4:
        st.metric("Num. Conceptos", num_codes)
    
    # Detailed table
    st.subheader("📋 Detalle por Código y Nombre")
    
    display_df = spending_by_code.copy()
    display_df["amount"] = display_df["amount"].apply(format_millions)
    display_df.columns = ["Código", "Nombre", "Gasto (M€)"]
    display_df = display_df[["Código", "Nombre", "Gasto (M€)"]].reset_index(drop=True)
    display_df.index = display_df.index + 1
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
    )

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
