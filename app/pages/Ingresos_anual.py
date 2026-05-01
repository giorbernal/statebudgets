"""Streamlit application page - Ingresos Consolidados visualization."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.shared import initialize_page
from utils.data_loader import (
    load_revenue_data,
    load_spending_data,
    get_revenue_by_organism,
    thousands_to_millions,
    format_millions,
)


# Initialize page
try:
    df = load_revenue_data()
except FileNotFoundError:
    st.error("❌ El archivo de ingresos (revenue.csv) no ha sido generado. "
             "Por favor, ejecuta `make revenue` para generar los datos.")
    st.stop()

# Initialize page settings
st.set_page_config(
    page_title="Ingresos - PGE",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("📈 Ingresos Presupuestarios del Estado (Consolidado)")
st.markdown(
    "Análisis consolidado de ingresos: ESTADO + Seguridad Social (2023) "
    "vs. Gastos presupuestarios"
)
st.markdown("---")

# Get available years
years = sorted(df['año'].unique().tolist())

# Year selector
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Selecciona el año para visualizar:**")

with col2:
    selected_year = st.selectbox(
        "Año",
        years,
        index=len(years) - 1,
        key="year_selector_revenue",
        label_visibility="collapsed",
    )

st.markdown("---")

# Get revenue data for the year
revenue_by_organism = get_revenue_by_organism(df, selected_year)

# ===== VIEW 1: Treemap by Organism =====
st.header("📊 Ingresos por Organismo")

# Convert amounts to millions for display
revenue_display = revenue_by_organism.copy()
revenue_display["total_millions"] = revenue_display["total"].apply(thousands_to_millions)

# Create treemap visualization
fig_treemap = go.Figure(
    go.Treemap(
        labels=revenue_display["organismo"].tolist(),
        parents=[""] * len(revenue_display),
        values=revenue_display["total_millions"].tolist(),
        textposition="middle center",
        hovertemplate="<b>%{label}</b><br>Ingresos: €%{value:.2f}M<extra></extra>",
        marker=dict(
            colorscale="RdYlGn",
            cmid=revenue_display["total_millions"].median(),
        ),
    )
)

fig_treemap.update_layout(
    title=f"Ingresos Presupuestarios por Organismo - {selected_year}",
    height=500,
    margin=dict(t=50, l=10, r=10, b=10),
)

st.plotly_chart(fig_treemap, use_container_width=True)

# ===== VIEW 2: Summary Statistics =====
st.header("📊 Análisis Consolidado")

# Load spending data for comparison
try:
    spending_df = load_spending_data()
    spending_2023 = spending_df[spending_df['year'] == selected_year]
    total_gastos = spending_2023['amount'].sum()
except:
    total_gastos = 0

year_data = df[df['año'] == selected_year]
total_revenue = year_data['total'].sum()
num_organisms = year_data['organismo'].nunique()

# Create metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Ingresos Consolidados",
        value=format_millions(total_revenue, decimals=2),
        delta="miles €"
    )

with col2:
    st.metric(
        label="Gastos Consolidados",
        value=format_millions(total_gastos, decimals=2),
        delta="miles €"
    )

with col3:
    if total_gastos > 0:
        deficit = total_gastos - total_revenue
        deficit_pct = (deficit / total_gastos) * 100
        
        if deficit > 0:
            delta_text = f"Déficit {deficit_pct:.1f}%"
            delta_color = "off"
        else:
            delta_text = f"Superávit {-deficit_pct:.1f}%"
            delta_color = "inverse"
        
        st.metric(
            label="Resultado",
            value=format_millions(deficit, decimals=2),
            delta=delta_text,
            delta_color=delta_color
        )

with col4:
    st.metric(
        label="Organismo (ESTADO)",
        value="Contribuyente principal",
        delta=format_millions(revenue_by_organism.iloc[0]['total'] if not revenue_by_organism.empty else 0, decimals=2)
    )

st.markdown("---")

# ===== VIEW 3: Detailed Table =====
st.header("📋 Desglose por Organismo")

# Create detailed view with expansion
if not revenue_by_organism.empty:
    # Summary table
    summary_df = revenue_by_organism.copy()
    summary_df.columns = ["Organismo", "Total (miles €)"]
    summary_df["Total (millones €)"] = summary_df["Total (miles €)"].apply(
        lambda x: format_millions(x, decimals=3)
    )
    summary_df["% del Total"] = (
        summary_df["Total (miles €)"] / summary_df["Total (miles €)"].sum() * 100
    ).apply(lambda x: f"{x:.1f}%")
    
    # Remove the thousands column for display
    summary_df = summary_df[["Organismo", "Total (millones €)", "% del Total"]]
    
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Detailed breakdown
    st.subheader("Desglose Detallado por Servicio/Sección")
    
    for organism in revenue_by_organism["organismo"].tolist():
        organism_data = year_data[year_data["organismo"] == organism]
        
        if len(organism_data) > 1 or organism_data['codigo'].iloc[0] != '':
            with st.expander(f"🔍 {organism}"):
                org_detail = organism_data[['codigo', 'descripcion', 'total']].copy()
                org_detail.columns = ["Código", "Descripción", "Total (miles €)"]
                org_detail["Total (millones €)"] = org_detail["Total (miles €)"].apply(
                    lambda x: format_millions(x, decimals=2)
                )
                org_detail = org_detail[["Código", "Descripción", "Total (millones €)"]]
                
                st.dataframe(
                    org_detail,
                    use_container_width=True,
                    hide_index=True,
                )
else:
    st.info("No hay datos disponibles para el año seleccionado.")

st.markdown("---")

# ===== Information Section =====
st.subheader("📌 Sobre este análisis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Datos incluidos:**
    - ✓ ESTADO (8 capítulos económicos)
    - ✓ Seguridad Social
    - ✗ Organismos Autónomos (no incluidos en consolidado)
    - ✗ Resto de Entidades (no incluidos en consolidado)
    
    **Justificación de la consolidación:**
    Los gastos en el archivo spending.csv incluyen partidas de Seguridad Social 
    (pensiones, desempleo, etc.). Por coherencia, se consolidan los ingresos de 
    ESTADO + Seguridad Social para una comparación equilibrada.
    """)

with col2:
    st.markdown("""
    **Definición de términos:**
    - **Ingresos**: Recursos financieros del estado (impuestos, tasas, transferencias)
    - **Gastos**: Erogaciones presupuestarias por políticas públicas
    - **Déficit**: Diferencia entre gastos e ingresos (cuando gastos > ingresos)
    - **Consolidado**: Suma de ESTADO + Seguridad Social
    
    **Fuente:**
    Ministerio de Hacienda y Función Pública - Presupuestos Generales del Estado 2023
    """)
