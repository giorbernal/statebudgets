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


def thousands_to_millions(amount_thousands: float) -> float:
    """Convert amount from thousands of euros to millions of euros.
    
    Args:
        amount_thousands: Amount in thousands of euros.
    
    Returns:
        Amount in millions of euros.
    """
    return amount_thousands / 1000


def format_millions(amount_thousands: float, decimals: int = 3) -> str:
    """Format amount from thousands to millions with specified decimals.
    
    Args:
        amount_thousands: Amount in thousands of euros.
        decimals: Number of decimal places (default 3).
    
    Returns:
        Formatted string with millions of euros (M€).
    """
    millions = thousands_to_millions(amount_thousands)
    return f"{millions:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".") + " M€"


def get_spending_by_code_and_name(
    df: pd.DataFrame,
    year: int,
    policy: str,
) -> pd.DataFrame:
    """Get spending breakdown by code and name for a specific policy and year.
    
    Args:
        df: Spending DataFrame.
        year: Target year.
        policy: Target policy.
    
    Returns:
        DataFrame with code, name, and total amount grouped by code-name combination.
    """
    filtered_data = df[(df["year"] == year) & (df["policy"] == policy)]
    
    spending_by_code = (
        filtered_data.groupby(["code", "name"])["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    
    return spending_by_code


@st.cache_data
def load_parties_data() -> pd.DataFrame:
    """Load and cache the parties.csv dataset.
    
    Returns:
        DataFrame with year and party columns.
    """
    project_root = Path(__file__).parent.parent.parent
    parties_path = project_root / "data" / "input" / "parties.csv"
    
    if not parties_path.exists():
        raise FileNotFoundError(f"Parties dataset not found at {parties_path}")
    
    df = pd.read_csv(parties_path)
    df['year'] = pd.to_numeric(df['year'], errors='coerce').astype(int)
    
    return df


def get_party_color(party: str) -> str:
    """Get the color for a political party.
    
    Args:
        party: Party name (PSOE or PP).
    
    Returns:
        Hex color code for the party.
    """
    party_colors = {
        "PSOE": "#E41E3F",  # Red
        "PP": "#0066CC",    # Blue
    }
    return party_colors.get(party, "#999999")  # Gray as default


def add_party_to_data(df: pd.DataFrame, timeline_data: pd.DataFrame) -> pd.DataFrame:
    """Add party information to timeline data based on year.
    
    Args:
        df: Original spending DataFrame (to load parties if needed).
        timeline_data: Timeline data with year, policy, and amount columns.
    
    Returns:
        Timeline data with added 'party' column.
    """
    parties_df = load_parties_data()
    result = timeline_data.merge(parties_df, on="year", how="left")
    result["party_display"] = result["party"].fillna("Desconocido")
    
    return result


def get_party_background_color(party: str, opacity: float = 0.15) -> str:
    """Get a light background color for a political party.
    
    Args:
        party: Party name (PSOE or PP).
        opacity: Opacity value (0.0 to 1.0).
    
    Returns:
        RGBA color code for the party background.
    """
    party_colors = {
        "PSOE": f"rgba(228, 30, 63, {opacity})",      # Light red
        "PP": f"rgba(0, 102, 204, {opacity})",        # Light blue
    }
    return party_colors.get(party, f"rgba(153, 153, 153, {opacity})")  # Light gray as default


def style_dataframe_by_party(
    df: pd.DataFrame,
    party: str,
    opacity: float = 0.15
):
    """Style a dataframe with party-based background color for Streamlit display.
    
    Args:
        df: DataFrame to style.
        party: Party name (PSOE or PP).
        opacity: Background opacity (0.0-1.0).
    
    Returns:
        Styled object compatible with st.dataframe().
    """
    background_color = get_party_background_color(party, opacity)
    
    # Create a styled dataframe with party background for all cells
    def apply_party_color(val):
        return f'background-color: {background_color}'
    
    # Use map method for cell-by-cell styling (pandas 1.4+)
    try:
        styled = df.style.map(apply_party_color)
    except AttributeError:
        # Fallback for older pandas versions
        styled = df.style.applymap(apply_party_color)
    
    return styled


def get_policy_concepts_timeline(
    df: pd.DataFrame,
    policy: str,
) -> pd.DataFrame:
    """Get spending timeline for all concepts (code+name) within a policy.
    
    Args:
        df: Spending DataFrame.
        policy: Target policy name.
    
    Returns:
        DataFrame with year, code, name, amount columns, grouped by concept.
    """
    # Filter by policy
    policy_df = df[df["policy"] == policy].copy()
    
    # Create concept label combining code and name
    policy_df["concept"] = policy_df["code"].astype(str) + " - " + policy_df["name"].astype(str)
    
    # Group by year and concept
    timeline = (
        policy_df.groupby(["year", "concept"])["amount"]
        .sum()
        .reset_index()
        .sort_values(["concept", "year"])
    )
    
    return timeline


def get_yearly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Get total spending by year and TODO: total income by year.
    
    Args:
        df: Spending DataFrame.
    
    Returns:
        DataFrame with year, total_spending, and total_income columns.
        Note: total_income is currently a placeholder and needs to be implemented
        when income data source is available.
    """
    yearly_spending = (
        df.groupby("year")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "total_spending"})
    )
    
    # TODO: Add income data once source is available
    # yearly_income = load_income_data()
    # yearly_totals = yearly_spending.merge(yearly_income, on="year", how="left")
    
    yearly_totals = yearly_spending.copy()
    yearly_totals["total_income"] = None  # Placeholder for income data
    
    return yearly_totals.sort_values("year")
