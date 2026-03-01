# State Budgets

This is an analysis project for the state budgets of Spain. It is based in data obtained from https://www.sepg.pap.hacienda.gob.es/sitios/sepg/es-ES/Presupuestos/PGE/Paginas/PresupuestosGE.aspx

## Makefile Commands

### spendings
Genera el dataset de gastos de los Presupuestos Generales del Estado para el intervalo de años disponible (2011-2026).

Este comando:
1. Verifica que exista el directorio `pge/` con los datos de presupuesto
2. Invoca el script `scripts/build_spendings.sh` para cada año disponible
3. Genera un archivo `spendings.csv` por cada año en `pge/<año>/`

```bash
make spendings
```
