"""Data analysis utilities."""

from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd


class DataAnalyzer:
    """Main class for data analysis operations."""

    def __init__(self, dataframe: pd.DataFrame) -> None:
        """Initialize analyzer with a DataFrame.
        
        Args:
            dataframe: Data to analyze.
        """
        self.df = dataframe

    def get_summary_statistics(self) -> pd.DataFrame:
        """Generate summary statistics for numeric columns.
        
        Returns:
            DataFrame with statistical summary.
        """
        return self.df.describe()

    def get_column_types(self) -> Dict[str, str]:
        """Get data types of all columns.
        
        Returns:
            Dictionary mapping column names to types.
        """
        return {col: str(dtype) for col, dtype in self.df.dtypes.items()}

    def get_missing_values(self) -> pd.Series:
        """Count missing values per column.
        
        Returns:
            Series with missing value counts.
        """
        return self.df.isnull().sum()

    def get_unique_values(self, column: str) -> int:
        """Count unique values in a column.
        
        Args:
            column: Column name.
            
        Returns:
            Number of unique values.
        """
        return self.df[column].nunique()

    def filter_by_column(
        self,
        column: str,
        value: Any,
    ) -> pd.DataFrame:
        """Filter DataFrame by column value.
        
        Args:
            column: Column name to filter by.
            value: Value to filter for.
            
        Returns:
            Filtered DataFrame.
        """
        return self.df[self.df[column] == value]

    def group_and_aggregate(
        self,
        group_by: List[str],
        agg_func: str = "sum",
    ) -> pd.DataFrame:
        """Group data and apply aggregation.
        
        Args:
            group_by: Columns to group by.
            agg_func: Aggregation function.
            
        Returns:
            Aggregated DataFrame.
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        return self.df.groupby(group_by)[numeric_cols].agg(agg_func)

    def calculate_percentiles(
        self,
        column: str,
        percentiles: List[float] = [0.25, 0.5, 0.75],
    ) -> Dict[str, float]:
        """Calculate percentiles for a numeric column.
        
        Args:
            column: Column name.
            percentiles: List of percentiles to calculate.
            
        Returns:
            Dictionary mapping percentiles to values.
        """
        return {
            f"p{int(p * 100)}": self.df[column].quantile(p)
            for p in percentiles
        }

    def get_correlation_matrix(self) -> pd.DataFrame:
        """Calculate correlation matrix for numeric columns.
        
        Returns:
            Correlation matrix DataFrame.
        """
        return self.df.select_dtypes(include=[np.number]).corr()


class TimeSeriesAnalyzer(DataAnalyzer):
    """Specialized analyzer for time series data."""

    def __init__(
        self,
        dataframe: pd.DataFrame,
        date_column: str = "date",
    ) -> None:
        """Initialize time series analyzer.
        
        Args:
            dataframe: Data with time series.
            date_column: Name of the date column.
        """
        super().__init__(dataframe)
        self.date_column = date_column
        self._ensure_datetime()

    def _ensure_datetime(self) -> None:
        """Convert date column to datetime if needed."""
        if self.date_column in self.df.columns:
            self.df[self.date_column] = pd.to_datetime(
                self.df[self.date_column],
                errors="coerce",
            )

    def resample_data(self, freq: str = "M") -> pd.DataFrame:
        """Resample time series data.
        
        Args:
            freq: Resampling frequency (D, W, M, Q, Y).
            
        Returns:
            Resampled DataFrame.
        """
        self.df.set_index(self.date_column, inplace=True)
        resampled = self.df.resample(freq).sum()
        self.df.reset_index(inplace=True)
        return resampled

    def calculate_moving_average(
        self,
        column: str,
        window: int = 7,
    ) -> pd.Series:
        """Calculate moving average.
        
        Args:
            column: Column to calculate average for.
            window: Window size.
            
        Returns:
            Series with moving average.
        """
        return self.df[column].rolling(window=window).mean()

    def detect_outliers(
        self,
        column: str,
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> pd.Series:
        """Detect outliers in a column.
        
        Args:
            column: Column to check.
            method: Detection method ('iqr' or 'zscore').
            threshold: Threshold for outlier detection.
            
        Returns:
            Boolean Series indicating outliers.
        """
        if method == "iqr":
            q1 = self.df[column].quantile(0.25)
            q3 = self.df[column].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            return (self.df[column] < lower) | (self.df[column] > upper)
        else:
            z_scores = np.abs(
                (self.df[column] - self.df[column].mean()) 
                / self.df[column].std()
            )
            return z_scores > threshold
