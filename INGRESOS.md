# Análisis de Ingresos Presupuestarios - Guía de Uso

## Descripción General

El módulo de **Ingresos Presupuestarios** proporciona un análisis consolidado de los recursos financieros del Estado español, incluyendo:

- **ESTADO**: Ingresos tributarios y patrimoniales del Estado central
- **Seguridad Social**: Ingresos por cotizaciones y contribuciones sociales

## ¿Por qué consolidación?

### Justificación técnica

El archivo `spending.csv` incluye gastos consolidados que abarcan:
- Gasto corriente del Estado
- Gasto en Seguridad Social (pensiones, desempleo, etc.)
- Transferencias a otras administraciones

Para una comparativa coherente **ingresos vs. gastos**, es necesario consolidar también los ingresos:

```
CONSOLIDADO 2023:
├─ Ingresos
│  ├─ ESTADO:          192,544 mil millones €
│  ├─ Seguridad Social: 209,177 mil millones €
│  └─ TOTAL:           401,721 mil millones €
│
├─ Gastos (spending.csv): 650,931 mil millones €
│
└─ RESULTADO: -249,209 mil millones € (déficit 38.3%)
```

### Organismos NO incluidos en consolidado

Se excluyen deliberadamente:
- **Organismos Autónomos**: Tienen financiación específica
- **Resto de Entidades**: Presupuestos independientes

Estos organismos tienen sus propias fuentes de ingresos y no interactúan directamente con el flujo principal Estado ↔ Seguridad Social.

## Estructura de Datos

### Archivo: `data/input/revenue.csv`

```
Columnas:
├─ año:          Año presupuestario (2023)
├─ organismo:    ESTADO o SEGURIDAD SOCIAL
├─ codigo:       Clasificación económica (1-8 para capítulos, 60 para SS)
├─ descripcion:  Nombre del ingreso/capítulo
├─ total:        Importe en miles de euros
└─ cap1-cap8:    Desglose por capítulos económicos (cuando aplica)
```

### Capítulos de Ingresos del ESTADO

| Cap | Descripción | Ingresos 2023 | % del Total |
|-----|-------------|---------------|-----------|
| 1 | Impuestos Directos y Cotizaciones Sociales | 86,428,535.02 | 44.9% |
| 2 | Impuestos Indirectos | 57,809,239.51 | 30.0% |
| 3 | Tasas, Precios Públicos y Otros Ingresos | 10,778,944.06 | 5.6% |
| 4 | Transferencias Corrientes | 13,556,039.68 | 7.0% |
| 5 | Ingresos Patrimoniales | 6,170,901.99 | 3.2% |
| 6 | Enajenación de Inversiones Reales | 106,200.00 | 0.1% |
| 7 | Transferencias de Capital | 14,155,141.03 | 7.4% |
| 8 | Activos Financieros | 3,539,165.04 | 1.8% |
| **TOTAL** | | **192,544,166.33** | **100%** |

### Seguridad Social

| Concepto | Ingresos 2023 |
|----------|---------------|
| Cotizaciones de trabajadores | Principal |
| Cotizaciones de empresarios | Principal |
| Aportaciones del Estado | Complementaria |
| **TOTAL** | **209,177,262.33 miles €** |

## Comandos Disponibles

### Generar datos de ingresos
```bash
make revenue
```

Procesa los archivos CSV del PGE 2023 y genera `data/input/revenue.csv` con datos consolidados.

### Validar precisión
```bash
make validate-revenue
```

Ejecuta validaciones automáticas:
1. ✓ Verificación de sumas (capítulos → total)
2. ✓ Integridad de datos (sin nulos, duplicados)
3. ✓ Comparativa ingresos vs. gastos
4. ✓ Cálculo de déficit/superávit

Salida esperada:
```
Ingresos consolidados: 401,721,428.66 miles €
Gastos consolidados:   650,930,602.20 miles €
Déficit:               249,209,173.54 miles € (38.3%)
```

## Análisis en la Aplicación

### Página "Ingresos Consolidados"

Accesible desde el menú lateral de Streamlit:

1. **Treemap de Ingresos**
   - Visualización de distribución ESTADO vs. Seguridad Social
   - Proporcional a los ingresos
   - Interactivo (hover para detalles)

2. **Métricas Consolidadas**
   - Ingresos totales consolidados
   - Gastos totales consolidados
   - Resultado (déficit con % de gastos)
   - Principales contribuyentes

3. **Desglose por Capítulos (ESTADO)**
   - Tabla detallada con 8 capítulos
   - Importes en millones de euros
   - Porcentaje respecto al total

## Comparativa Histórica (Futuro)

Para análisis multianuales:

```bash
# Generar ingresos para múltiples años
for year in 2020 2021 2022 2023; do
    python3.10 scripts/build_revenue.py $year
done

# Luego ensamblar en único archivo (futura funcionalidad)
make ensemble-revenue
```

## Limitaciones Conocidas

1. **Período limitado**: Solo 2023 disponible actualmente
2. **Estructura simplificada**: Consolidación a nivel ESTADO + SS
3. **No incluye**: Organismos autónomos (futura expansión)

## Fuente de Datos

- **Oficial**: https://www.sepg.pap.hacienda.gob.es
- **Documento**: PGE 2023 - Serie Roja - Presupuesto de Ingresos
- **Fecha extracción**: Datos aprobados dic-2022

## Referencias

- [README.md](./README.md) - Documentación general
- [AGENTS.md](./AGENTS.md) - Arquitectura del proyecto
- [Makefile](./Makefile) - Comandos disponibles
- [scripts/build_revenue.py](./scripts/build_revenue.py) - Generador de datos
- [scripts/validate_revenue.py](./scripts/validate_revenue.py) - Validador de datos

## Contacto / Problemas

Para reportar problemas o sugerencias:
- Issues: Crear en el repositorio
- Datos: Verificar con `make validate-revenue`
- Aplicación: Revisar logs de Streamlit
