"""Evolución Temporal - Spending timeline evolution visualization."""

import streamlit as st
import plotly.express as px

from utils.shared import initialize_page
from utils.data_loader import (
    get_policies,
    get_spending_timeline,
)


# Initialize page
df = initialize_page("Evolución Temporal", "📈")

# Title and description
st.title("💰 Presupuestos Generales del Estado")
st.markdown(
    "Análisis interactivo de los Presupuestos Generales del Estado español (2011-2026)"
)
st.markdown("---")

# Page header
st.header("📈 Evolución Temporal de Gastos por Política")

# Get all policies
all_policies = get_policies(df)

# Filters section
st.subheader("🔍 Filtros")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Selecciona las políticas a visualizar:**")
    selected_policies = st.multiselect(
        "Políticas",
        all_policies,
        default=all_policies[:5],  # Default to first 5
        key="policies_selector",
        label_visibility="collapsed",
    )

with col2:
    show_all = st.checkbox("Mostrar todas", key="show_all_policies")

if show_all:
    selected_policies = all_policies

if not selected_policies:
    st.warning("Por favor selecciona al menos una política.")
    st.stop()

# Get timeline data
timeline_data = get_spending_timeline(df, selected_policies)

# Create line chart
fig = px.line(
    timeline_data,
    x="year",
    y="amount",
    color="policy",
    markers=True,
    title="Evolución del Gasto por Política (2011-2026)",
    labels={
        "year": "Año",
        "amount": "Gasto (€)",
        "policy": "Política",
    },
    hover_data={
        "amount": ":.0f",
        "year": True,
        "policy": True,
    },
)

fig.update_traces(
    hovertemplate="<b>%{customdata[1]}</b><br>" +
                  "Año: %{customdata[0]}<br>" +
                  "Gasto: %{y:,.0f}€<extra></extra>",
    customdata=timeline_data[["year", "policy"]].values,
)

fig.update_layout(
    height=600,
    font=dict(size=11),
    xaxis_title="Año",
    yaxis_title="Gasto (€)",
    yaxis_tickformat=",.0f",
    hovermode="x unified",
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    ),
)

st.plotly_chart(fig, use_container_width=True)

# Statistics
st.divider()
st.subheader("📊 Estadísticas de la Selección")

col1, col2, col3, col4 = st.columns(4)

total_spending = timeline_data["amount"].sum()
avg_spending = timeline_data["amount"].mean()
max_spending = timeline_data["amount"].max()
num_data_points = len(timeline_data)

with col1:
    st.metric(
        "Gasto Total",
        f"{total_spending:,.0f}€",
    )

with col2:
    st.metric(
        "Gasto Promedio",
        f"{avg_spending:,.0f}€",
    )

with col3:
    st.metric(
        "Gasto Máximo",
        f"{max_spending:,.0f}€",
    )

with col4:
    st.metric(
        "Puntos de Datos",
        num_data_points,
    )

# Per-policy statistics table
st.subheader("📋 Estadísticas por Política")

policy_stats = (
    timeline_data.groupby("policy")["amount"]
    .agg([
        ("Gasto Total", "sum"),
        ("Gasto Promedio", "mean"),
        ("Gasto Máximo", "max"),
        ("Gasto Mínimo", "min"),
    ])
    .reset_index()
    .sort_values("Gasto Total", ascending=False)
)

# Format currency columns
for col in ["Gasto Total", "Gasto Promedio", "Gasto Máximo", "Gasto Mínimo"]:
    policy_stats[col] = policy_stats[col].apply(
        lambda x: f"{x:,.2f}€".replace(",", ".")
    )

policy_stats.columns = ["Política", "Gasto Total", "Gasto Promedio", 
                        "Gasto Máximo", "Gasto Mínimo"]
policy_stats = policy_stats.reset_index(drop=True)
policy_stats.index = policy_stats.index + 1

st.dataframe(
    policy_stats,
    use_container_width=True,
    height=300,
)

# Year-over-year comparison
st.subheader("📅 Comparativa por Año")

yearly_stats = (
    timeline_data.groupby("year")["amount"]
    .agg([
        ("Gasto Total", "sum"),
        ("Num. Políticas", "count"),
        ("Gasto Promedio", "mean"),
    ])
    .reset_index()
)

# Format currency columns
yearly_stats["Gasto Total"] = yearly_stats["Gasto Total"].apply(
    lambda x: f"{x:,.0f}€"
)
yearly_stats["Gasto Promedio"] = yearly_stats["Gasto Promedio"].apply(
    lambda x: f"{x:,.0f}€"
)

yearly_stats.columns = ["Año", "Gasto Total", "Num. Políticas", "Gasto Promedio"]
yearly_stats = yearly_stats.reset_index(drop=True)
yearly_stats.index = yearly_stats.index + 1

st.dataframe(
    yearly_stats,
    use_container_width=True,
    height=300,
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
