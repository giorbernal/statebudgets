# Presupuestos Generales del Estado - Análisis Interactivo

Proyecto de análisis interactivo de los Presupuestos Generales del Estado español (2011-2026). Proporciona herramientas para visualizar, analizar y explorar datos de gasto público.

**Fuente de datos**: https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/PGE/Paginas/PresupuestosGE.aspx

## Inicio Rápido

### Configuración
```bash
pip install pandas numpy plotly streamlit
# Or: poetry install
```

### Ejecutar la aplicación
```bash
make run
# Or: cd app && streamlit run Gasto_anual.py
# Access: http://localhost:8501
```

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

### revenue
Genera el dataset de ingresos presupuestarios consolidados (ESTADO + Seguridad Social) para 2023.

Este comando:
1. Procesa los archivos CSV de ingresos del PGE 2023
2. Extrae datos de ESTADO (8 capítulos económicos) y Seguridad Social
3. Genera `data/input/revenue.csv` con análisis consolidado

```bash
make revenue
```

### validate-revenue
Valida la precisión de los datos de ingresos y realiza comparativa vs. gastos.

Este comando:
1. Verifica que los capítulos de ESTADO sumen correctamente
2. Comprueba integridad de datos (sin nulos, duplicados)
3. Compara ingresos consolidados vs. gastos presupuestarios
4. Reporta déficit/superávit consolidado

```bash
make validate-revenue
```

## Características de la Aplicación

### Página 1: Gastos por Política 📊 (Principal)
- Treemap interactivo mostrando distribución de gastos
- Selector de año (2011-2026)
- Colorización por monto (escala Viridis)
- Métricas resumen (total, mayor política, promedio, cantidad)
- Tabla detallada con formato español

### Página 2: Evolución Temporal 📈
- Gráfico de líneas múltiples (una serie por política)
- Eje X: Años (2011-2026)
- Eje Y: Gasto acumulado
- Filtro multiselección de políticas
- Opción "Mostrar todas"
- Estadísticas por política y comparativa año a año

### Página 3: Ingresos Consolidados 📈 (Nueva)
- Análisis consolidado: **ESTADO + Seguridad Social**
- Treemap de distribución de ingresos por organismo
- Comparativa ingresos vs. gastos presupuestarios
- Métricas de déficit/superávit
- Desglose por capítulos económicos (8 categorías)
- Validación de precisión de datos

#### Justificación de la consolidación de ingresos
Los gastos presupuestarios (spending.csv) incluyen partidas de Seguridad Social (pensiones, desempleo, etc.). 
Por coherencia analítica, se consolidan los ingresos de ESTADO + Seguridad Social para una comparación equilibrada:

- **Ingresos consolidados 2023**: 401.7 mil millones €
- **Gastos consolidados 2023**: 650.9 mil millones €
- **Déficit consolidado**: 249.2 mil millones € (38.3% de gastos)

## Requisitos

- Python 3.10+
- Pandas >= 2.0.0
- NumPy >= 1.24.0
- Plotly >= 5.13.0
- Streamlit >= 1.55.0

## Documentación

Para más información sobre desarrollo y arquitectura, consulta [AGENTS.md](./AGENTS.md)
