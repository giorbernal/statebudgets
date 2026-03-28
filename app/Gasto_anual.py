"""Main Streamlit application - Gastos por Política visualization."""

import streamlit as st
import plotly.graph_objects as go

from utils.shared import initialize_page
from utils.data_loader import (
    get_years,
    get_spending_by_policy,
    thousands_to_millions,
    format_millions,
)


# Initialize page
df = initialize_page("Gastos por Política", "📊")

# Title and description
st.title("💰 Presupuestos Generales del Estado")
st.markdown(
    "Análisis interactivo de los Presupuestos Generales del Estado español (2011-2026)"
)
st.markdown("---")

# Page header
st.header("📊 Gastos por Política de Gasto")

# Year selector
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("**Selecciona el año para visualizar:**")

with col2:
    years = get_years(df)
    selected_year = st.selectbox(
        "Año",
        years,
        index=len(years) - 1,  # Default to latest year
        key="year_selector",
        label_visibility="collapsed",
    )

# Get spending by policy for selected year
spending_by_policy = get_spending_by_policy(df, selected_year)

# Convert amounts to millions for display
spending_by_policy_display = spending_by_policy.copy()
spending_by_policy_display["amount_millions"] = spending_by_policy_display["amount"].apply(thousands_to_millions)

# Create treemap visualization using plotly graph_objects
fig = go.Figure(
    go.Treemap(
        labels=spending_by_policy_display["policy"].tolist(),
        parents=[""] * len(spending_by_policy_display),
        values=spending_by_policy_display["amount_millions"].tolist(),
        marker=dict(
            colors=spending_by_policy_display["amount_millions"].tolist(),
            colorscale="Viridis",
            cmid=spending_by_policy_display["amount_millions"].median(),
            colorbar=dict(
                title="Gasto (M€)",
                tickformat=",.3f",
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

st.plotly_chart(fig, use_container_width=True)

# Summary statistics
st.divider()
st.subheader("📈 Estadísticas del Año")

col1, col2, col3, col4 = st.columns(4)

total_spending = spending_by_policy["amount"].sum()
top_policy = spending_by_policy.iloc[0]
avg_spending = spending_by_policy["amount"].mean()
num_policies = len(spending_by_policy)

with col1:
    st.metric(
        "Gasto Total",
        format_millions(total_spending),
    )

with col2:
    st.metric(
        "Política Mayor",
        f"{top_policy['policy'][:30]}...",
    )

with col3:
    st.metric(
        "Gasto Promedio",
        format_millions(avg_spending),
    )

with col4:
    st.metric(
        "Num. Políticas",
        num_policies,
    )

# Detailed table
st.subheader("📋 Detalle de Gastos")

# Format amount column for display
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
