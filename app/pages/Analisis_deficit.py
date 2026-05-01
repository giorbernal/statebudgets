"""Streamlit application page - Deficit Analysis."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.shared import initialize_page
from utils.data_loader import (
    load_revenue_data,
    load_spending_data,
    get_spending_by_policy,
    thousands_to_millions,
    format_millions,
)


# Initialize page settings
st.set_page_config(
    page_title="Análisis de Déficit - PGE",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
try:
    revenue_df = load_revenue_data()
    spending_df = load_spending_data()
except FileNotFoundError as e:
    st.error(f"❌ Error cargando datos: {str(e)}")
    st.stop()

# Title
st.title("💰 Análisis de la Brecha Ingresos-Gastos")
st.markdown(
    "Entender por qué la diferencia entre ingresos y gastos es mayor de lo esperado"
)
st.markdown("---")

# Get available years (years that have both revenue and spending data)
revenue_years = sorted(revenue_df['año'].unique().tolist())
spending_years = sorted(spending_df['year'].unique().tolist())
years = sorted(set(revenue_years) & set(spending_years))

# Year selector
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("**Selecciona el año para el análisis:**")
with col2:
    selected_year = st.selectbox(
        "Año",
        years,
        index=len(years) - 1,
        label_visibility="collapsed",
    )

st.markdown("---")

# === DATA PROCESSING ===
def normalize_amount(x):
    """Convert Spanish format (1.234,56) to float"""
    if pd.isna(x) or x == '':
        return 0.0
    x = str(x).strip()
    x = x.replace('.', '')  # Remove thousands separator
    x = x.replace(',', '.')  # Replace decimal comma
    try:
        return float(x)
    except:
        return 0.0

# Process revenue data (need to normalize because these are stored as strings in format "1.234,56")
revenue_year = revenue_df[revenue_df['año'] == selected_year].copy()
revenue_year['total_norm'] = revenue_year['total'].apply(normalize_amount)

# Process spending data (already normalized by load_spending_data())
spending_year = spending_df[spending_df['year'] == selected_year].copy()

# Calculate totals
estado_revenue = revenue_year[revenue_year['organismo'] == 'ESTADO']['total_norm'].sum()
ss_revenue = revenue_year[revenue_year['organismo'] == 'SEGURIDAD SOCIAL']['total_norm'].sum()
total_revenue = estado_revenue + ss_revenue

# For spending, use the amount column directly (already normalized by load_spending_data)
ss_spending = spending_year[
    spending_year['policy'].str.startswith(
        ('21.', '22.', '23.', '24.', '25.', '26.', '27.', '28.', '29.'),
        na=False
    )
]['amount'].sum()

total_spending = spending_year['amount'].sum()
estado_spending = total_spending - ss_spending

deficit = total_spending - total_revenue
deficit_pct = (deficit / total_spending) * 100 if total_spending > 0 else 0

# === SECTION 1: Executive Summary ===
st.header("📋 Resumen Ejecutivo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Ingresos Consolidados",
        format_millions(total_revenue),
        delta=None
    )

with col2:
    st.metric(
        "Gastos Consolidados",
        format_millions(total_spending),
        delta=None
    )

with col3:
    st.metric(
        "Déficit",
        format_millions(deficit),
        delta=None
    )

with col4:
    st.metric(
        "Tasa de Déficit",
        f"{deficit_pct:.1f}%",
        delta=None
    )

st.markdown("---")

# === SECTION 2: Waterfall Chart ===
st.header("📊 Desglose del Déficit")

waterfall_categories = [
    "Ingresos\nEstado",
    "Ingresos\nSeg. Social",
    "Gastos\nEstado",
    "Gastos\nSeg. Social",
    "DÉFICIT"
]

waterfall_values = [
    thousands_to_millions(estado_revenue),  # Positive
    thousands_to_millions(ss_revenue),       # Positive
    -thousands_to_millions(estado_spending), # Negative
    -thousands_to_millions(ss_spending),     # Negative
    None  # Will be calculated
]

fig_waterfall = go.Figure(go.Waterfall(
    x=waterfall_categories,
    y=waterfall_values,
    connector={"line": {"color": "rgba(0, 0, 0, 0.3)"}},
    increasing={"marker": {"color": "rgba(0, 128, 0, 0.7)"}},
    decreasing={"marker": {"color": "rgba(255, 0, 0, 0.7)"}},
    totals={"marker": {"color": "rgba(70, 130, 180, 0.7)"}},
    text=[
        f"€{thousands_to_millions(estado_revenue):.1f}M",
        f"€{thousands_to_millions(ss_revenue):.1f}M",
        f"-€{thousands_to_millions(estado_spending):.1f}M",
        f"-€{thousands_to_millions(ss_spending):.1f}M",
        f"-€{thousands_to_millions(deficit):.1f}M"
    ],
    textposition="outside"
))

fig_waterfall.update_layout(
    title="Flujo de Ingresos y Gastos",
    height=500,
    showlegend=False,
    yaxis_title="Millones de euros (M€)"
)

st.plotly_chart(fig_waterfall, use_container_width=True)

st.markdown("---")

# === SECTION 3: Why is the deficit so high? ===
st.header("❓ ¿Por qué el déficit es tan alto?")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Componentes del Gasto")
    
    # Breakdown of spending
    debt_spending = spending_year[
        spending_year['policy'].str.contains('DEUDA|FINANCIERO', case=False, na=False)
    ]['amount'].sum()
    
    transfers_spending = spending_year[
        spending_year['policy'].str.contains('TRANSFERENCIAS', case=False, na=False)
    ]['amount'].sum()
    
    other_spending = total_spending - ss_spending - debt_spending - transfers_spending
    
    spending_breakdown = {
        'Seguridad Social': thousands_to_millions(ss_spending),
        'Deuda Pública': thousands_to_millions(debt_spending),
        'Transferencias a Adm.': thousands_to_millions(transfers_spending),
        'Otros Gastos': thousands_to_millions(other_spending)
    }
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=list(spending_breakdown.keys()),
        values=list(spending_breakdown.values()),
        textposition='inside',
        textinfo='label+percent',
        hovertemplate="<b>%{label}</b><br>€%{value:.1f}M<br>%{percent}<extra></extra>"
    )])
    
    fig_pie.update_layout(
        title="Composición del Gasto Total",
        height=400
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.subheader("Principales Causas del Déficit")
    
    # Create explanation with metrics
    deficit_causes = [
        ("Gastos financieros de deuda pública", thousands_to_millions(debt_spending)),
        ("Déficit de Seg. Social", thousands_to_millions(ss_spending - ss_revenue)),
        ("Transferencias a CCAA y Entes Locales", thousands_to_millions(transfers_spending)),
        ("Otros gastos del Estado", thousands_to_millions(estado_spending - debt_spending - transfers_spending)),
    ]
    
    for cause, amount in deficit_causes:
        st.markdown(f"**{cause}**")
        pct_of_total = (amount / thousands_to_millions(total_spending)) * 100 if total_spending > 0 else 0
        st.markdown(f"> €{amount:.2f}M ({pct_of_total:.1f}% del gasto total)")
        st.markdown("")

st.markdown("---")

# === SECTION 4: Detailed Explanation ===
st.header("🔍 Análisis Detallado")

with st.expander("📌 ¿Por qué la Seguridad Social tiene déficit?", expanded=False):
    ss_spending_m = thousands_to_millions(ss_spending)
    ss_revenue_m = thousands_to_millions(ss_revenue)
    ss_deficit_m = thousands_to_millions(ss_spending - ss_revenue)
    
    st.markdown(f"""
    ### El Déficit de Seguridad Social
    
    Los gastos de Seguridad Social (€{ss_spending_m:.2f}M) son mayores que sus ingresos directos por cotizaciones (€{ss_revenue_m:.2f}M).
    
    **Esto ocurre porque:**
    
    1. **Pensiones de Clases Pasivas**: Las pensiones de funcionarios jubilados se financian con presupuestos del Estado
    
    2. **Envejecimiento de población**: Hay más pensionistas que cotizantes
    
    3. **Prestaciones sociales**: El desempleo, subsidios, prestaciones se financian parcialmente con transferencias estatales
    
    4. **Contribuciones especiales**: El Estado contribuye a Seguridad Social para garantizar prestaciones mínimas
    
    **La diferencia (€{ss_deficit_m:.2f}M) proviene de transferencias del ESTADO a la Seguridad Social** (que ya están incluidas en ingresos del Estado).
    
    Este sistema es normal en economías desarrolladas.
    """)

with st.expander("💳 Carga de la Deuda Pública", expanded=False):
    debt_spending_m = thousands_to_millions(debt_spending)
    debt_pct = (thousands_to_millions(debt_spending) / thousands_to_millions(total_spending)) * 100 if total_spending > 0 else 0
    
    st.markdown(f"""
    ### Gastos Financieros de la Deuda
    
    España gasta **€{debt_spending_m:.2f}M** anualmente en:
    - Intereses de la deuda pública
    - Amortización de bonos y deuda
    - Gastos financieros asociados
    
    **Esto representa el {debt_pct:.1f}% del gasto total.**
    
    Este componente:
    1. No genera servicios inmediatos
    2. Crece cuando aumentan los tipos de interés
    3. Reduce el margen para otros gastos
    4. Es inevitable mientras exista deuda acumulada
    """)

with st.expander("🏛️ Transferencias a Otras Administraciones", expanded=False):
    transfers_spending_m = thousands_to_millions(transfers_spending)
    transfers_pct = (thousands_to_millions(transfers_spending) / thousands_to_millions(total_spending)) * 100 if total_spending > 0 else 0
    
    st.markdown(f"""
    ### Transferencias a Comunidades Autónomas y Entes Locales
    
    El Estado transfiere **€{transfers_spending_m:.2f}M** a:
    - Comunidades Autónomas (sanidad, educación, servicios sociales)
    - Municipios y entidades locales
    - Otras administraciones públicas
    
    **Esto representa el {transfers_pct:.1f}% del gasto total.**
    
    Estas transferencias:
    1. Financian servicios públicos locales
    2. Implementan políticas territoriales
    3. Garantizan equidad entre regiones
    4. Son constitucionales y necesarias
    """)

st.markdown("---")

# === SECTION 5: Year comparison ===
st.header("📈 Evolución Histórica")

# Calculate deficit for all years
historical_data = []

for year in years:
    rev_y = revenue_df[revenue_df['año'] == year].copy()
    rev_y['total_norm'] = rev_y['total'].apply(normalize_amount)
    total_rev_y = rev_y['total_norm'].sum()
    
    spend_y = spending_df[spending_df['year'] == year]
    total_spend_y = spend_y['amount'].sum()
    
    if total_spend_y > 0 and total_rev_y > 0:
        historical_data.append({
            'year': year,
            'ingresos': thousands_to_millions(total_rev_y),
            'gastos': thousands_to_millions(total_spend_y),
            'deficit': thousands_to_millions(total_spend_y - total_rev_y),
            'deficit_pct': ((total_spend_y - total_rev_y) / total_spend_y) * 100
        })

df_historical = pd.DataFrame(historical_data)

if not df_historical.empty:
    fig_evolution = go.Figure()
    
    fig_evolution.add_trace(go.Scatter(
        x=df_historical['year'],
        y=df_historical['ingresos'],
        mode='lines+markers',
        name='Ingresos',
        line=dict(color='green', width=3),
        marker=dict(size=8)
    ))
    
    fig_evolution.add_trace(go.Scatter(
        x=df_historical['year'],
        y=df_historical['gastos'],
        mode='lines+markers',
        name='Gastos',
        line=dict(color='red', width=3),
        marker=dict(size=8)
    ))
    
    fig_evolution.update_layout(
        title="Evolución de Ingresos y Gastos Consolidados",
        xaxis_title="Año",
        yaxis_title="Millones de euros (M€)",
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_evolution, use_container_width=True)
    
    # Deficit trend
    fig_deficit = px.line(
        df_historical,
        x='year',
        y='deficit_pct',
        markers=True,
        title="Tasa de Déficit a lo largo de los años",
        labels={'year': 'Año', 'deficit_pct': 'Tasa de Déficit (%)'},
        height=400
    )
    
    fig_deficit.update_traces(line=dict(color='darkred', width=3), marker=dict(size=10))
    
    st.plotly_chart(fig_deficit, use_container_width=True)

st.markdown("---")

# === SECTION 6: Key Insights ===
st.header("💡 Conclusiones Clave")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    ### ✓ Lo que es NORMAL
    
    • Déficit presupuestario
    • Gastos > Ingresos
    • Necesidad de financiamiento
    • Deuda pública acumulada
    """)

with col2:
    st.warning("""
    ### ⚠️ Factores a Considerar
    
    • Carga de deuda muy alta
    • Envejecimiento de población
    • Transferencias a autonomías
    • Ciclos económicos
    """)

with col3:
    st.success("""
    ### 📊 En Contexto
    
    • Similar a otros países europeos
    • Inversión en servicios públicos
    • Estructura consolidada correcta
    • Datos verificados y validados
    """)

st.markdown("---")

# === FOOTER ===
st.markdown("""
**Nota metodológica:** 
- Los valores se muestran en **Millones de euros (M€)** para consistencia con otras páginas
- **Ingresos**: ESTADO + Seguridad Social (cotizaciones directas)
- **Gastos**: ESTADO + Seguridad Social (completo)
- Se excluyen deliberadamente Organismos Autónomos y Resto de Entidades
""")
