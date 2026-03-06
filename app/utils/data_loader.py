"""Data loading and cleaning utilities."""

from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st


def _parse_spending_csv(file_path: Path) -> pd.DataFrame:
    """Parse the spending.csv file using Pandas with error handling.
    
    The CSV uses semicolon as delimiter and may have rows with extra fields
    where the policy field contains semicolons.
    
    Args:
        file_path: Path to the CSV file.
    
    Returns:
        DataFrame with columns: year, code, name, amount, policy.
    """
    # Read CSV with semicolon delimiter, handling potential malformed rows
    df = pd.read_csv(
        file_path,
        sep=';',
        encoding='utf-8',
        on_bad_lines='skip',  # Skip rows with inconsistent field count
        engine='python'  # Python engine handles edge cases better
    )
    
    if df.empty:
        raise ValueError("CSV file produced empty DataFrame")
    
    # Ensure required columns exist
    required_columns = ['year', 'code', 'name', 'amount', 'policy']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV missing required columns. Expected: {required_columns}")
    
    # Keep only required columns
    df = df[required_columns].copy()
    
    # Validate data: remove rows with invalid year or amount
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['amount'] = df['amount'].astype(str).str.strip()
    df['amount'] = pd.to_numeric(
        df['amount'].str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors='coerce'
    )
    
    # Remove rows where year or amount couldn't be converted
    df = df.dropna(subset=['year', 'amount'])
    
    # Convert year to integer
    df['year'] = df['year'].astype(int)
    
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
    
    # Parse CSV with Pandas
    df = _parse_spending_csv(data_path)
    
    # Ensure amount is float (already converted in _parse_spending_csv)
    df["amount"] = df["amount"].astype(float)
    
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
    
    # Remove rows with empty policy or NaN values
    df = df[df["policy"].notna() & (df["policy"] != "") & (df["policy"] != "nan")]
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
