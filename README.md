# Presupuestos Generales del Estado - Análisis Interactivo

Proyecto de análisis interactivo de los Presupuestos Generales del Estado español (2011-2026). Proporciona herramientas para visualizar, analizar y explorar datos de gasto público.

**Fuente de datos**: https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/PGE/Paginas/PresupuestosGE.aspx

## Inicio Rápido

### Instalación

```bash
# Instalar dependencias
pip install pandas numpy plotly streamlit

# O con Poetry
poetry install
```

### Ejecución

```bash
# Opción 1: Usando make (recomendado)
make run

# Opción 2: Directamente
cd app
streamlit run Gasto_anual.py
```

La aplicación estará disponible en: **http://localhost:8501**

## Makefile Commands

### run
Ejecuta la aplicación Streamlit con todos los módulos y visualizaciones.

Este comando:
1. Navega al directorio `app/`
2. Inicia el servidor Streamlit
3. Carga automáticamente los datos desde `data/input/spending.csv`
4. Abre la interfaz web en el navegador

```bash
make run
```

**Acceso**: http://localhost:8501

### spending
Genera el dataset de gastos de los Presupuestos Generales del Estado para el intervalo de años disponible (2011-2026).

Este comando:
1. Verifica que exista el directorio `pge/` con los datos de presupuesto
2. Invoca el script `scripts/build_spending.py` para cada año disponible
3. Genera un archivo `spending.csv` por cada año en `pge/<año>/`

```bash
make spending
```

### ensemble-spending
Ensambla todos los archivos `spending.csv` individuales en un único archivo global `data/input/spending.csv`.

Este comando:
1. Verifica que exista el directorio `pge/`
2. Recopila todos los archivos `spending.csv` de cada `pge/<año>/`
3. Concatena las filas añadiendo una columna adicional con el año
4. Genera `data/input/spending.csv`

```bash
make ensemble-spending
```

## Características de la Aplicación

### Tab 1: Gastos por Política 📊
- Treemap interactivo mostrando distribución de gastos
- Selector de año (2011-2026)
- Colorización por monto (escala Viridis)
- Métricas resumen (total, mayor política, promedio, cantidad)
- Tabla detallada con formato español

### Tab 2: Evolución Temporal 📈
- Gráfico de líneas múltiples (una serie por política)
- Eje X: Años (2011-2026)
- Eje Y: Gasto acumulado
- Filtro multiselección de políticas
- Opción "Mostrar todas"
- Estadísticas por política y comparativa año a año

## Requisitos

- Python 3.10+
- Pandas >= 2.0.0
- NumPy >= 1.24.0
- Plotly >= 5.13.0
- Streamlit >= 1.55.0

## Documentación

Para más información sobre desarrollo y arquitectura, consulta [AGENTS.md](./AGENTS.md)
