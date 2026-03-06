# AGENTS.md - Spanish State Budget Analytics Project

## Overview

This project analyzes the Spanish State Budget (Presupuestos Generales del Estado - PGE). It provides tools to download budget data from the official SEPG source, parse the HTML files, and generate CSV files with spending information organized by policy areas.

The data is sourced from the official government portal (Secretaría de Estado de Presupuestos y Gastos) and includes budgets from multiple years (2020, 2022, 2024, 2025, 2026).

## Project Structure

```
/workspace/
├── .opencode/                 # OpenCode configuration
│   ├── agents/
│   │   └── state-budget-collector.md
│   └── skills/
│       ├── build-budgets-csv/
│       ├── download-budgets/
│       └── get-policy-spending/
├── pge/                       # Spanish State Budget data (PGE)
│   ├── 2011-2026/             # Budget data for all years (16 years)
├── scripts/
│   ├── build_spending.sh      # Shell script to generate CSV from HTM files
│   └── politicas_gasto.txt    # List of spending policies by area
├── app/                       # Streamlit application (MAIN)
│   ├── Gasto_anual.py         # Main page: Annual spending by policy
│   ├── pages/                 # Page modules
│   │   └── Evolución_Temporal.py  # Page: Timeline evolution with filters
│   ├── utils/                 # Utility modules
│   │   ├── shared.py          # Shared initialization logic
│   │   └── data_loader.py     # CSV parsing, cleaning, and data caching
│   └── __init__.py
├── src/
│   ├── __init__.py
│   ├── analytics/             # Data analysis modules
│   │   ├── __init__.py
│   │   └── analyzer.py        # DataAnalyzer and TimeSeriesAnalyzer classes
│   └── visualization/         # Chart generation (legacy)
│       ├── __init__.py
│       └── charts.py
├── tests/                     # Test files (empty - future work)
├── data/
│   ├── input/
│   │   └── spending.csv       # Main dataset (1,854 valid rows)
│   └── output/
├── .streamlit/
│   └── config.toml
├── Makefile                   # Build automation with help command
├── AGENTS.md                  # This file
├── pyproject.toml             # Poetry dependencies
└── README.md
```

## Commands

### Setup

```bash
# Install dependencies with pip
pip install pandas numpy plotly streamlit

# Or with Poetry
poetry install
poetry shell
```

### Running the Application

```bash
# Run from app directory (recommended)
cd app
streamlit run Gasto_anual.py

# Or from project root
streamlit run app/Gasto_anual.py

# Access at http://localhost:8501
```

### Build Budget Data

```bash
# Show available commands
make

# Generate spending.csv for all years
make spending

# Ensemble all spending.csv into one global file
make ensemble-spending
```

### Running Tests

```bash
# Run all tests (currently empty)
poetry run pytest

# Run a single test file
poetry run pytest tests/test_analyzer.py

# Run a single test
poetry run pytest tests/test_analyzer.py::test_function_name -v
```

### Development

```bash
# Add new dependency
poetry add <package>

# Add dev dependency
poetry add --dev <package>

# Update dependencies
poetry update
```

## Streamlit Application Overview

The application provides interactive visualization and analysis of Spanish State Budget data (2011-2026).

### Architecture

**Main Page**: `app/Gasto_anual.py`
- Annual spending visualization by policy
- Year selector with treemap
- Statistics and detailed breakdown table

**Tab 1 - Spending by Policy** (`app/pages/tab_policies.py`)
- Treemap visualization (Plotly) showing spending distribution
- Year selector (2011-2026)
- Color-coded by spending amount (Viridis scale)
- Summary metrics: total, average, largest policy, count
- Detailed table with Spanish number formatting

**Tab 2 - Temporal Evolution** (`app/pages/tab_timeline.py`)
- Line chart with multiple series (one per policy)
- X-axis: Years (2011-2026)
- Y-axis: Cumulative spending amount
- Multi-select filter for policies
- "Show all" checkbox for convenience
- Unified hover information
- Statistics tables: per-policy and year-over-year

**Data Loading** (`app/utils/data_loader.py`)
- Custom CSV parser handling malformed rows
- Converts Spanish number format (1.234,56 → 1234.56)
- Decodes HTML entities (&uacute; → ú)
- Validates and cleans data
- Caches data with `@st.cache_data` for performance
- Parses 1,854 valid rows from 1,982 total lines

### Data Processing Pipeline

```
data/input/spending.csv (raw, 1,982 lines)
    ↓
Custom CSV Parser (handles malformations)
    ↓
DataFrame Cleaning (format conversion, validation)
    ↓
Streamlit Cache (@st.cache_data)
    ↓
Visualizations & Analysis
```

### Dependencies

**Core**:
- `streamlit` (^1.55.0) - Web framework
- `pandas` (^2.0.0) - Data manipulation
- `plotly` (^5.13.0) - Interactive visualizations
- `numpy` (^1.24.0) - Numerical operations

**Development**:
- `poetry` - Dependency management
- `pytest` - Testing framework (future)

### Key Features

✅ **Interactive Visualizations**
- Treemap with hover tooltips
- Multi-series line charts
- Color-coded by spending amount
- Responsive and mobile-friendly

✅ **Data Handling**
- Robust CSV parsing with error recovery
- Spanish locale support (comma decimals)
- HTML entity decoding
- Missing value handling

✅ **Performance**
- Session state caching
- Data caching with decorators
- Efficient pandas operations
- Lazy loading of visualizations

✅ **User Experience**
- Tab-based organization
- Intuitive filters and selectors
- Real-time metric updates
- Detailed data tables
- Government source attribution

### Known Limitations

- Initial data load is slower due to custom parsing
- Large number of policies may slow timeline rendering
- Requires manual `make spending` command for data updates
- No export functionality (future enhancement)

## Code Style Guidelines

### General Principles

- Write clean, readable, and maintainable code
- Use descriptive names for variables, functions, and classes
- Keep functions focused on single responsibility (SOLID principles)
- Add docstrings for public APIs and complex logic
- Write tests for business logic

### Imports

Organize imports in this order:
```python
# Standard library
import re
import sys
import argparse
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

# Third-party packages
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Local application
from src.analytics.analyzer import DataAnalyzer
from src.visualization.charts import ChartGenerator
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `data_frame`, `output_path` |
| Functions | snake_case | `convert_to_csv()`, `analyze_data()` |
| Classes | PascalCase | `DataAnalyzer`, `ChartGenerator` |
| Constants | UPPER_SNAKE_CASE | `MAX_ROWS`, `DEFAULT_ENCODING` |
| Private methods | snake_case with underscore | `_process_data()` |
| Modules | snake_case | `analytics`, `visualization` |

### Types and Type Hints

Use type hints for function signatures and return types:
```python
def process_file(file_path: str, options: Optional[Dict] = None) -> pd.DataFrame:
    """Process a file and return a DataFrame.
    
    Args:
        file_path: Path to the input file.
        options: Optional processing parameters.
    
    Returns:
        Processed DataFrame.
    """
    pass
```

### Formatting

- **Indentation**: 4 spaces (no tabs)
- **Line length**: Maximum 100 characters
- **Spacing**: Add spaces around operators (`x = x + 1`)
- **Blank lines**: Use to separate logical sections in functions
- **Trailing commas**: Use for multi-line imports

### Docstrings

Use Google-style docstrings:
```python
def function_name(param: str, param2: int = 10) -> bool:
    """Short description of what the function does.

    Longer description if needed.

    Args:
        param: Description of param.
        param2: Description of param2. Defaults to 10.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param is invalid.
    """
```

### Error Handling

- Use specific exception types
- Provide meaningful error messages
- Log errors appropriately
- Never expose secrets in error messages

```python
try:
    df = pd.read_csv(file_path, encoding='utf-8')
except FileNotFoundError:
    st.error(f"File not found: {file_path}")
    raise
except pd.errors.EmptyDataError:
    st.warning(f"Empty file: {file_path}")
    return pd.DataFrame()
```

### Streamlit-Specific Guidelines

- Use `st.` prefix for Streamlit components
- Cache expensive computations with `@st.cache_data` or `@st.cache_resource`
- Use `st.session_state` for persistent state
- Keep Streamlit app code minimal in pages; delegate logic to utils modules
- Use columns for layout: `col1, col2 = st.columns(2)`

### Data Processing Patterns

- Use pandas for tabular data operations
- Use numpy for numerical computations
- Use `melt()` for reshaping wide-to-long
- Use `merge()`/`join()` for combining datasets
- Use method chaining when readable

### Testing Guidelines

- Test file naming: `test_<module>.py`
- Test class naming: `Test<ModuleName>`
- Use descriptive test names: `test_extract_tables_returns_dataframe`
- Use fixtures for common test data
- Aim for high coverage on business logic

### File Paths

- Use `pathlib.Path` for path operations
- Use relative paths from project root
- Define paths as constants when used repeatedly

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_INPUT = PROJECT_ROOT / "data" / "input"
DATA_OUTPUT = PROJECT_ROOT / "data" / "output"
PGE_BASE = PROJECT_ROOT / "pge"
SCRIPTS = PROJECT_ROOT / "scripts"
```

## Working with This Project

### General Guidelines

1. Always use absolute paths or set `workdir="/workspace"` in bash commands
2. Follow the import organization and naming conventions
3. Keep business logic in `src/` modules, UI in `app/`
4. Test changes before committing
5. Use type hints and docstrings
6. Run `poetry run pytest` before pushing changes

### Streamlit App Development

1. **Use relative imports** in `app/pages/` and `app/utils/`
   - Import as: `from utils.data_loader import load_spending_data`
   - Not: `from app.utils.data_loader import load_spending_data`

2. **Cache expensive operations**
   ```python
   @st.cache_data
   def load_spending_data() -> pd.DataFrame:
       # Expensive operation here
   ```

3. **Use session state for persistence**
   ```python
   if "spending_data" not in st.session_state:
       st.session_state.spending_data = load_spending_data()
   ```

4. **Delegate logic to separate modules**
   - UI code stays in `app/pages/`
   - Data logic in `app/utils/`
   - Analysis in `src/analytics/`

5. **Handle CSV parsing carefully**
   - The spending.csv has malformed rows with extra semicolons
   - Use the custom parser in `data_loader.py`
   - Never use plain `pd.read_csv()` without custom logic

### Important Notes

- **Do NOT inspect `pge/` folder without explicit order** — contains large budget data files
- **CSV format**: Header uses commas, data uses semicolons (inconsistent)
- **Spanish locale**: Numbers use commas as decimal separator (1.234,56)
- **Data validation**: Always validate and clean input before visualization
- **Performance**: Initial load may be slow due to CSV parsing; subsequent loads are instant due to caching

### Future Enhancements

Suggested improvements (not yet implemented):

- [ ] Add unit tests for `data_loader.py` and analysis functions
- [ ] Add export functionality (CSV, PDF, Excel)
- [ ] Add budget comparison between years
- [ ] Add spending range filters
- [ ] Add policy search/filter by name
- [ ] Add spending trends analysis
- [ ] Add budget allocation pie charts
- [ ] Update README.md with screenshots and usage examples
- [ ] Add error logging and monitoring
- [ ] Add data refresh mechanism
