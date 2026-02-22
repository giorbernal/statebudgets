# AGENTS.md - PDF to CSV Analytics Project

## Overview

This is a Streamlit-based data analysis project that converts PDFs to CSVs and provides interactive analytics and visualizations. It uses pandas, numpy for data processing and seaborn/matplotlib for visualizations.

## Project Structure

```
/workspace/
├── pyproject.toml              # Poetry configuration
├── poetry.lock
├── src/
│   ├── __init__.py
│   ├── pdf_processor/         # Reusable PDF → CSV conversion
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base class
│   │   ├── extractor.py      # PDF text/table extraction
│   │   └── converter.py      # CSV conversion logic
│   ├── analytics/             # Data analysis modules
│   │   ├── __init__.py
│   │   └── analyzer.py       # Statistical analysis
│   └── visualization/         # Chart generation
│       ├── __init__.py
│       └── charts.py         # Matplotlib/Seaborn charts
├── app/
│   ├── __init__.py
│   └── main.py               # Streamlit entry point
├── tests/                    # Test files
├── data/
│   ├── input/                # PDF source files
│   └── output/               # Generated CSV files
└── .streamlit/
    └── config.toml           # Streamlit configuration
```

## Commands

### Setup

```bash
# Install dependencies with Poetry
poetry install

# Activate virtual environment
poetry shell
```

### Running the Application

```bash
# Run Streamlit app
poetry run streamlit run app/main.py

# Or from project root
streamlit run app/main.py
```

### Running Tests

```bash
# Run all tests
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
from src.pdf_processor.base import BaseExtractor
from src.analytics.analyzer import DataAnalyzer
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Variables | snake_case | `data_frame`, `output_path` |
| Functions | snake_case | `convert_to_csv()`, `analyze_data()` |
| Classes | PascalCase | `PDFExtractor`, `DataAnalyzer` |
| Constants | UPPER_SNAKE_CASE | `MAX_ROWS`, `DEFAULT_ENCODING` |
| Private methods | snake_case with underscore | `_process_data()` |
| Modules | snake_case | `pdf_processor`, `data_analyzer` |

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
- Keep Streamlit app code minimal in `main.py`; delegate logic to modules
- Use columns for layout: `col1, col2 = st.columns(2)`

### PDF Processor Module Patterns

- Create abstract base class for extractors
- Implement strategy pattern for different PDF formats
- Return DataFrames from processing methods
- Support both table and text extraction

```python
class BaseExtractor(ABC):
    """Abstract base class for PDF extractors."""

    @abstractmethod
    def extract_tables(self, file_path: str) -> List[pd.DataFrame]:
        """Extract tables from PDF."""
        pass

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF."""
        pass
```

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
```

## Working with This Project

1. Always use absolute paths or set `workdir="/workspace"` in bash commands
2. Follow the import organization and naming conventions
3. Keep business logic in `src/` modules, UI in `app/`
4. Test changes before committing
5. Use type hints and docstrings
6. Run `poetry run pytest` before pushing changes
