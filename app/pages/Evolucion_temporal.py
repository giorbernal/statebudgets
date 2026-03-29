"""Evolución Temporal - Spending timeline evolution visualization."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.shared import initialize_page
from utils.data_loader import (
    get_policies,
    get_spending_timeline,
    get_yearly_totals,
    get_policy_concepts_timeline,
    load_parties_data,
    get_party_color,
    get_party_background_color,
    add_party_to_data,
    style_dataframe_by_party,
    thousands_to_millions,
    format_millions,
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

# Get yearly totals for overview chart
yearly_totals = get_yearly_totals(df)

# Load parties data to show governing party
parties_df = load_parties_data()
overview_data = yearly_totals.merge(parties_df, on="year", how="left")

# Overview section: Total spending and income by year
st.subheader("📊 Gasto Total e Ingreso Total por Año")

# Prepare data for visualization
# Convert spending to millions for display
overview_data["gasto_millones"] = overview_data["total_spending"].apply(thousands_to_millions)

# Create chart with background shading by party
fig_overview = go.Figure()

# Add background rectangles for each party period with semi-transparent colors
for idx, row in parties_df.iterrows():
    year = row['year']
    party = row['party']
    party_color = get_party_color(party)
    
    # Add vertical band with semi-transparent background
    fig_overview.add_vrect(
        x0=year - 0.4,
        x1=year + 0.4,
        fillcolor=party_color,
        opacity=0.15,
        layer="below",
        line_width=0,
    )

# Add single spending line trace with homogeneous color (dark gray)
fig_overview.add_trace(go.Scatter(
    x=overview_data["year"],
    y=overview_data["gasto_millones"],
    name="Gasto Total",
    mode='lines+markers',
    line=dict(color='#333333', width=3),
    marker=dict(size=8, color='#333333'),
    hovertemplate="<b>Año: %{x}</b><br>Gasto: %{y:,.2f} M€<extra></extra>",
))

# TODO: Add income trace when income data is available
# fig_overview.add_trace(go.Scatter(
#     x=overview_data["year"],
#     y=overview_data["ingreso_millones"],
#     name="Ingreso Total",
#     mode='lines+markers',
#     line=dict(color='#2ca02c', width=3),
#     marker=dict(size=8),
# ))

fig_overview.update_layout(
    title="Comparativa de Gasto Total e Ingreso Total (2011-2026)",
    xaxis_title="Año",
    yaxis_title="Gasto Total (M€)",
    height=400,
    hovermode="closest",
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
    ),
    plot_bgcolor="rgba(240, 240, 240, 0.3)",
)

st.plotly_chart(fig_overview, use_container_width=True)

st.markdown("---")

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

# Add party information to timeline data
timeline_data_with_party = add_party_to_data(df, timeline_data)

# Convert amounts to millions for display
timeline_data_display = timeline_data_with_party.copy()
timeline_data_display["amount_millions"] = timeline_data_display["amount"].apply(thousands_to_millions)

# Create line chart
fig = px.line(
    timeline_data_display,
    x="year",
    y="amount_millions",
    color="policy",
    markers=True,
    title="Evolución del Gasto por Política (2011-2026)",
    labels={
        "year": "Año",
        "amount_millions": "Gasto (M€)",
        "policy": "Política",
    },
    hover_data={
        "amount_millions": ":.3f",
        "year": True,
        "policy": True,
        "party_display": True,
    },
)

fig.update_traces(
    hovertemplate="<b>%{fullData.name}</b><br>" +
                  "Año: %{x}<br>" +
                  "Gasto: %{y:,.3f} M€<extra></extra>",
)

# Add background shading based on governing party
parties_df = load_parties_data()
for idx, row in parties_df.iterrows():
    year = row['year']
    party = row['party']
    party_color = get_party_color(party)
    
    # Add vertical band with semi-transparent background
    fig.add_vrect(
        x0=year - 0.4,
        x1=year + 0.4,
        fillcolor=party_color,
        opacity=0.05,
        layer="below",
        line_width=0,
    )

fig.update_layout(
    height=600,
    font=dict(size=11),
    xaxis_title="Año",
    yaxis_title="Gasto (M€)",
    yaxis_tickformat=",.3f",
    hovermode="closest",
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

# Concepts historical section
st.divider()
st.subheader("📊 Histórico de Conceptos de Gasto por Política")

# Add selector for single policy
st.markdown("**Selecciona una política para ver el histórico de sus conceptos:**")

col1, col2 = st.columns([3, 1])

with col1:
    selected_policy_for_concepts = st.selectbox(
        "Política",
        all_policies,
        index=0,
        key="policy_concepts_selector",
        label_visibility="collapsed",
    )

with col2:
    if st.button("📊 Generar Gráfica", key="button_concepts_chart"):
        st.session_state.show_concepts_chart = True

# Show concepts chart if requested
if st.session_state.get("show_concepts_chart", False):
    # Get concepts timeline data
    concepts_timeline = get_policy_concepts_timeline(df, selected_policy_for_concepts)
    
    # Add party information
    concepts_timeline_with_party = concepts_timeline.merge(parties_df, on="year", how="left")
    
    # Convert amounts to millions for display
    concepts_timeline_display = concepts_timeline_with_party.copy()
    concepts_timeline_display["amount_millions"] = concepts_timeline_display["amount"].apply(thousands_to_millions)
    
    # Create line chart with all concepts
    fig_concepts = px.line(
        concepts_timeline_display,
        x="year",
        y="amount_millions",
        color="concept",
        markers=True,
        title=f"Histórico de Conceptos de Gasto - {selected_policy_for_concepts} (2011-2026)",
        labels={
            "year": "Año",
            "amount_millions": "Gasto (M€)",
            "concept": "Concepto",
        },
        hover_data={
            "amount_millions": ":.2f",
            "year": True,
            "concept": True,
        },
    )
    
    fig_concepts.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>" +
                      "Año: %{x}<br>" +
                      "Gasto: %{y:,.2f} M€<extra></extra>",
    )
    
    # Add background shading based on governing party
    for idx, row in parties_df.iterrows():
        year = row['year']
        party = row['party']
        party_color = get_party_color(party)
        
        # Add vertical band with semi-transparent background
        fig_concepts.add_vrect(
            x0=year - 0.4,
            x1=year + 0.4,
            fillcolor=party_color,
            opacity=0.05,
            layer="below",
            line_width=0,
        )
    
    fig_concepts.update_layout(
        height=700,
        font=dict(size=11),
        xaxis_title="Año",
        yaxis_title="Gasto (M€)",
        yaxis_tickformat=",.2f",
        hovermode="closest",
        legend=dict(
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
            orientation="v",
        ),
        margin=dict(b=300),
    )
    
    st.plotly_chart(fig_concepts, use_container_width=True)
    
    # Summary statistics for concepts
    st.markdown("---")
    st.subheader("📈 Estadísticas de Conceptos")
    
    col1, col2 = st.columns(2)
    
    num_concepts = concepts_timeline["concept"].nunique()
    max_year_spending = concepts_timeline.groupby("year")["amount"].sum().max()
    
    with col1:
        st.metric("Num. Conceptos", num_concepts)
    
    with col2:
        st.metric("Gasto Máximo Anual", format_millions(max_year_spending))

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
