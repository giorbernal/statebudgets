# State Budgets

This is an analysis project for the state budgets of Spain. It is based in data obtained from https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/PGE/Paginas/PresupuestosGE.aspx

## Makefile Commands

### spending
Genera el dataset de gastos de los Presupuestos Generales del Estado para el intervalo de años disponible (2011-2026).

Este comando:
1. Verifica que exista el directorio `pge/` con los datos de presupuesto
2. Invoca el script `scripts/build_spending.sh` para cada año disponible
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
