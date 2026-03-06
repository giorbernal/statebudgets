"""Data loading and cleaning utilities."""

from pathlib import Path
from typing import Optional
import csv

import pandas as pd
import streamlit as st


def _parse_spending_csv(file_path: Path) -> pd.DataFrame:
    """Parse the spending.csv file with custom logic to handle malformed data.
    
    The CSV has inconsistent structure:
    - Header uses commas (year,code,name,amount,policy)
    - Data uses semicolons as delimiters but some rows have > 5 fields
    - The issue is that policy field contains "; Y OTROS" causing extra split
    
    Args:
        file_path: Path to the CSV file.
    
    Returns:
        DataFrame with proper structure.
    """
    rows = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # Skip header line
        
        for line_num, row in enumerate(reader, start=2):
            if len(row) < 4:
                # Skip incomplete rows
                continue
            
            # Handle rows with extra fields (policy contains ";")
            if len(row) > 5:
                # Rejoin excess fields back to the policy field
                # Keep first 4 fields: year, code, name, amount
                # Rejoin remaining fields as policy
                year, code, name, amount = row[:4]
                policy = ";".join(row[4:])
            else:
                year, code, name, amount = row[:4]
                policy = row[4] if len(row) > 4 else ""
            
            # Only keep rows with valid year and amount
            try:
                int(year)
                # Try to parse amount (could be "71.021.601,90" or similar)
                float(amount.replace(".", "").replace(",", "."))
            except (ValueError, AttributeError):
                continue
            
            rows.append({
                "year": year,
                "code": code,
                "name": name,
                "amount": amount,
                "policy": policy,
            })
    
    df = pd.DataFrame(rows)
    
    if df.empty:
        raise ValueError("CSV file produced empty DataFrame")
    
    return df


@st.cache_data
def load_spending_data() -> pd.DataFrame:
    """Load and clean the spending.csv dataset.
    
    Returns:
        Cleaned DataFrame with proper data types.
    """
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "data" / "input" / "spending.csv"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    
    # Parse CSV with custom logic
    df = _parse_spending_csv(data_path)
    
    # Convert year to integer
    df["year"] = df["year"].astype(int)
    
    # Clean amount column: remove spaces, dots (thousands separator), convert comma to dot
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)  # Remove thousand separators
        .str.replace(",", ".", regex=False)  # Replace comma with dot
        .astype(float)
    )
    
    # Clean policy column: remove leading/trailing spaces and HTML entities
    df["policy"] = (
        df["policy"]
        .astype(str)
        .str.strip()
        .str.replace("&uacute;", "ú", regex=False)
        .str.replace("&aacute;", "á", regex=False)
        .str.replace("&eacute;", "é", regex=False)
        .str.replace("&iacute;", "í", regex=False)
        .str.replace("&oacute;", "ó", regex=False)
        .str.replace("&Aacute;", "Á", regex=False)
        .str.replace("&Eacute;", "É", regex=False)
        .str.replace("&Iacute;", "Í", regex=False)
        .str.replace("&Oacute;", "Ó", regex=False)
        .str.replace("&Uacute;", "Ú", regex=False)
        .str.replace("&auml;", "ä", regex=False)
    )
    
    # Remove rows with empty policy
    df = df[df["policy"].notna()]
    df = df[df["policy"] != ""]
    df = df[df["policy"] != "nan"]
    
    # Remove rows with NaN in critical columns
    df = df.dropna(subset=["year", "amount"])
    
    return df.reset_index(drop=True)


def get_years(df: pd.DataFrame) -> list[int]:
    """Get sorted list of available years.
    
    Args:
        df: Spending DataFrame.
    
    Returns:
        Sorted list of years.
    """
    return sorted(df["year"].unique().tolist())


def get_policies(df: pd.DataFrame) -> list[str]:
    """Get sorted list of all spending policies.
    
    Args:
        df: Spending DataFrame.
    
    Returns:
        Sorted list of policies.
    """
    return sorted(df["policy"].unique().tolist())


def get_spending_by_policy(
    df: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    """Get total spending by policy for a specific year.
    
    Args:
        df: Spending DataFrame.
        year: Target year.
    
    Returns:
        DataFrame with policy and total amount.
    """
    year_data = df[df["year"] == year]
    
    spending_by_policy = (
        year_data.groupby("policy")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    
    return spending_by_policy


def get_spending_timeline(
    df: pd.DataFrame,
    policies: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Get spending evolution over time for selected policies.
    
    Args:
        df: Spending DataFrame.
        policies: List of policies to include. If None, uses all.
    
    Returns:
        DataFrame with year, policy, and amount columns.
    """
    if policies is None:
        policies = get_policies(df)
    
    # Filter by policies
    filtered_df = df[df["policy"].isin(policies)]
    
    # Group by year and policy
    timeline = (
        filtered_df.groupby(["year", "policy"])["amount"]
        .sum()
        .reset_index()
        .sort_values(["year", "policy"])
    )
    
    return timeline
