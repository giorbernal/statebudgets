# Análisis de Años Faltantes - Ingresos Presupuestarios

## Resumen Ejecutivo

De los 16 años de presupuestos disponibles (2011-2026), solo **7 años tienen datos de ingresos** en formato compatible:
- ✓ **Disponibles**: 2017-2019, 2021-2023 (7 años)
- ✗ **Faltantes**: 2011-2016, 2020, 2024-2026 (9 años)

| Rango | Situación | Causa | Solución Requerida |
|-------|-----------|-------|-------------------|
| 2011-2016 | Sin CSV | Datos solo en HTM | Parser HTML |
| 2020 | Formato diferente | Cambio de nomenclatura | Adapter CSV |
| 2024-2026 | Formato nuevo | Actualización PGE | Parser nuevo |

---

## Análisis Detallado por Grupo

### Grupo 1: 2011-2016 (Datos en HTM)

**Estado actual:**
```
2011-2016 en pge/YYYY/PGE-ROM/doc/:
├── CSV/          (directorio VACÍO)
├── HTM/          (3,790-4,275 archivos)
└── ...
```

**Ejemplo de archivos disponibles:**
```
pge/2016/PGE-ROM/doc/HTM/
├── N_16_E_R_2_101_1_A_1.HTM       (ESTADO - Resumen)
├── N_16_E_R_2_101_1_7_A_1.HTM     (ESTADO - Capítulos) ← INGRESOS
├── N_16_E_R_2_105_1_7_A_1.HTM     (SS - Capítulos) ← INGRESOS
└── ... (3,800+ archivos más)
```

**Solución:**
1. Crear `parse_html_revenue()` en `build_revenue.py`
2. Usar `BeautifulSoup4` o `lxml` para parsear HTM
3. Extraer tablas de capítulos económicos (1-8)
4. Mapear campos igual que versión CSV

**Estimación de esfuerzo**: 4-6 horas
**Dependencias**: BeautifulSoup4, lxml

---

### Grupo 2: 2020 (Cambio de estructura)

**Diferencia clave:**
```
Formato 2017-2019 / 2021-2023:
  Patrón: N_XX_E_R_2_[ORGANISMO]_1_7_A_1.CSV
  ┌─────────────────────────────────────────┐
  │ N_23_E_R_2_101_1_7_A_1.CSV (ESTADO)     │
  │ N_23_E_R_2_105_1_7_A_1.CSV (SS)         │
  └─────────────────────────────────────────┘

Formato 2020:
  Patrón: N_19P_E_R_31_[ORGANISMO]_1_*
  ┌────────────────────────────────────────────────────┐
  │ N_19P_E_R_31_101_1_1_1_1911M_2.CSV (Gasto)         │
  │ N_19P_E_R_31_105_1_1_1_1912N_2.CSV (SS)            │
  │ NO EXISTE: N_19P_E_R_2_101_1_7_A_1.CSV ✗           │
  └────────────────────────────────────────────────────┘
```

**Búsqueda de equivalente en 2020:**

```bash
# Archivos CSV disponibles en 2020
ls /workspace/pge/2020/PGE-ROM/doc/CSV/ | cut -d_ -f3-5 | sort -u
# Resultado:
#   E_A_3    (Resúmenes A - posiblemente galos)
#   E_R_2    (Presupuesto - pero sin archivo 7_A_1)
#   E_R_31   (Presupuesto detallado con nueva estructura)
#   E_R_32, E_R_5, E_R_6, E_R_7, E_V_1, E_V_2, E_V_3
```

**Hallazgo**: No existe archivo equivalente a `_7_A_1` en 2020

**Posibles causas:**
1. El año 2020 fue transición de formato (COVID-19 pudo afectar)
2. Los ingresos consolidados podrían estar en otro patrón o código

**Solución:**
1. Revisar manualmente archivos en 2020 para identificar dónde están ingresos consolidados
2. Alternativa: Consultar fuente oficial PGE para verificar si 2020 tiene datos de ingresos públicos
3. Implementar fallback a gastos consolidados si ingresos no existen

**Estimación de esfuerzo**: 2-3 horas (investigación + adapter si existe)
**Dependencias**: Ninguna (solo investigación)

---

### Grupo 3: 2024-2026 (Nuevo formato)

**Cambio de nomenclatura:**
```
Formato histórico (2017-2023):
  N_23_E_R_2_101_1_7_A_1.CSV
  └─── 2023 (año)
  
Formato nuevo (2024-2026):
  N_23P_E_R_31_101_1_1_2_2_101_1_2.CSV
  └─── 23P (año + propuesta/P)
  
Y también:
  N_23P_E_V_1_101_1_1_2_2_101_1_2.CSV
  └─── Patrón V_1 (posiblemente ingresos con nueva estructura)
```

**Archivos encontrados en 2024-2026:**
```
2024/PGE-ROM/doc/CSV/:
  - N_23P_E_R_31_101_1_*.CSV     (441 archivos)
  - N_23P_E_V_1_*.CSV            (N archivos)
  - NO EXISTE: N_23P_E_R_2_101_1_7_A_1.CSV ✗
```

**Investigación requerida:**
1. Verificar si patrón `E_V_1` es de INGRESOS (Revenue)
2. Determinar si `E_R_31_101` tiene datos consolidados de ingresos
3. Mapear nueva estructura

**Solución:**
1. Analizar estructura de archivos en 2024-2026
2. Implementar nuevo parser para patrón `E_V_1` o equivalente
3. Mapear capítulos económicos 1-8 al nuevo formato
4. Mantener compatibilidad con parsers anteriores

**Estimación de esfuerzo**: 6-8 horas
**Dependencias**: Pandas, acceso a documentación técnica del PGE

---

## Plan de Acción Recomendado

### Fase 1: Corto Plazo (Inmediato)
- ✓ Ya completado: Actualizar Makefile para generar ingresos para años 2017-2023
- ✓ Ya completado: Documentar limitaciones en INGRESOS.md

**Comando actualizado:**
```bash
make revenue  # Genera ingresos para 2017-2019, 2021-2023
```

### Fase 2: Mediano Plazo (1-2 sprints)
**Prioridad: 2020 y 2024-2026** (más reciente = más relevante)

1. **Investigación de 2024-2026**
   - Determinar si existen archivos equivalentes
   - Documentar estructura nueva
   - Crear adapter si es necesario

2. **Investigación de 2020**
   - Verificar si hay datos de ingresos públicos
   - Consultar fuente oficial si necesario

### Fase 3: Largo Plazo (Próximo cuatrimestre)
**Prioridad: 2011-2016** (historial completo)

1. Implementar parser HTML
2. Generar datos históricos completos

---

## Recomendaciones

1. **Inmediato**: Usar `make revenue` para generar 7 años de datos (2017-2023)
   
2. **Usuario debe conocer**: Solo estos años están disponibles
   - Actualizar UI de Streamlit para mostrar rango disponible: 2017-2023

3. **Próximo paso**: 
   - Investigar si 2024-2026 tienen datos de ingresos públicos
   - Confirmar con fuente oficial: https://www.sepg.pap.hacienda.gob.es

---

## Referencias

- **Fuente oficial**: https://www.sepg.pap.hacienda.gob.es
- **Script**: `/workspace/scripts/build_revenue.py`
- **Documentación**: `/workspace/INGRESOS.md`
- **Makefile**: `/workspace/Makefile`

