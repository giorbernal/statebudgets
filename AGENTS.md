# AGENTS.md - Spanish State Budget Analytics Project

## Overview

Interactive analysis tool for Spanish State Budget (Presupuestos Generales del Estado - PGE) data (2011-2026). Official data source: https://www.sepg.pap.hacienda.gob.es

## ⚠️ Important Note

**Never search or explore the `pge/` directory unless explicitly requested.** The `pge/` folder contains large budget data files that are not part of the application development scope. Searches in this directory will slow down operations and add unnecessary noise. Always exclude `pge/` from file exploration, grep searches, and glob patterns unless the user specifically asks to work with it.

## Project Structure

```
/workspace/
├── app/                           # Streamlit application
│   ├── Gasto_anual.py             # Main page: Annual spending by policy
│   ├── pages/
│   │   └── evolucion_temporal.py  # Page: Timeline evolution
│   ├── utils/
│   │   ├── shared.py              # Shared initialization logic
│   │   └── data_loader.py         # CSV parsing and cleaning
│   └── __init__.py
├── data/
│   └── input/
│       └── spending.csv           # Main dataset (1,854 rows)
├── scripts/
│   ├── build_spending.py           # Script para generar spending.csv
│   ├── politicas_gasto.txt
│   └── ensemble_spending.sh
├── Makefile
├── README.md
└── pyproject.toml
```

## Quick Start

### Setup
```bash
pip install pandas numpy plotly streamlit
# Or: poetry install
```

### Run Application
```bash
make run
# Or: cd app && streamlit run Gasto_anual.py
# Access: http://localhost:8501
```

### Build Budget Data
```bash
make spending          # Generate spending.csv for all years
make ensemble-spending # Combine all spending.csv into one
```

Para generar datos de un año específico:
```bash
python3.10 scripts/build_spending.py <año>
# Ejemplo: python3.10 scripts/build_spending.py 2026
```

## Application Architecture

### Pages

**Gasto_anual.py** - Main page
- Treemap visualization by policy
- Year selector (2011-2026)
- Summary metrics and detailed table

**evolucion_temporal.py** - Timeline page
- Line chart with multi-series
- Policy multi-select filter
- Per-policy and yearly statistics

### Data Loading

- **data_loader.py**: Pandas-based CSV parser
  - Uses `pd.read_csv()` with `on_bad_lines='skip'` for robustness
  - Converts Spanish format: 1.234,56 → 1234.56
  - Decodes HTML entities: &uacute; → ú
  - Validates and cleans data
  - Caches data with @st.cache_data
  
- **shared.py**: Shared page initialization
   - Configures Streamlit page
   - Loads and validates data
   - Handles errors

### Data Scripts

- **build_spending.py**: Generador de spending.csv
  - Procesa ficheros HTM de presupuestos (2011-2026)
  - Soporta dos formatos: `<span>` (2014+) y `<div>` (2011-2013)
  - Extrae clasificación por programas, descripción e importes
  - Mapea códigos con políticas de gasto desde `politicas_gasto.txt`
  - Genera CSV en formato: `código;descripción;importe;política`
  - Uso: `python3.10 scripts/build_spending.py <año>`

## Code Style Guide

### Imports
```python
# Standard library
import sys
from typing import List

# Third-party
import pandas as pd
import streamlit as st

# Local
from utils.data_loader import load_spending_data
```

### Naming Conventions
- **Variables/Functions**: `snake_case` (e.g., `spending_data`, `load_csv()`)
- **Classes**: `PascalCase` (e.g., `DataAnalyzer`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ROWS`)

### Type Hints
```python
def load_spending_data() -> pd.DataFrame:
    """Load and clean spending dataset.
    
    Returns:
        Cleaned DataFrame with year, amount, policy columns.
    """
```

### Error Handling
```python
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    st.error(f"File not found: {file_path}")
    st.stop()
```

## Development Guidelines

1. **Cache expensive operations**: Use `@st.cache_data` for data loading
2. **Validate input**: Check data types and ranges before processing
3. **Use relative imports**: `from utils.data_loader import load_spending_data`
4. **Keep pages independent**: Each page should work standalone
5. **Document public APIs**: Add docstrings to functions and classes

### Streamlit Best Practices

- Use `st.session_state` for persistent state
- Use `st.columns()` for layout
- Set `page_config` at top of page
- Use `st.spinner()` for long operations
- Never expose secrets in error messages

## Known Limitations

- Large number of policies may slow timeline rendering
- Requires manual `make spending` for data updates

## Future Enhancements

- [ ] Add unit tests for data_loader and analysis functions
- [ ] Add export functionality (CSV, PDF, Excel)
- [ ] Add budget comparison between years
- [ ] Add spending range filters
- [ ] Add policy search/filter by name
