"""CSV conversion utilities."""

from pathlib import Path
from typing import Optional

import pandas as pd

from src.pdf_processor.base import BaseConverter


class CSVConverter(BaseConverter):
    """Converter for transforming extracted data to CSV format."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        separator: str = ";",
        decimal: str = ",",
        encoding: str = "utf-8",
    ) -> None:
        """Initialize CSV converter.
        
        Args:
            output_dir: Output directory for CSV files.
            separator: Column separator character.
            decimal: Decimal separator character.
            encoding: File encoding.
        """
        super().__init__(output_dir, separator, decimal)
        self.encoding = encoding

    def convert(
        self,
        data: pd.DataFrame,
        output_filename: str,
    ) -> Path:
        """Convert DataFrame to CSV file.
        
        Args:
            data: DataFrame to convert.
            output_filename: Name of output file.
            
        Returns:
            Path to created CSV file.
        """
        if output_filename.endswith(".csv"):
            output_filename = output_filename[:-4]
        
        output_path = self.output_dir / f"{output_filename}.csv"
        
        data.to_csv(
            output_path,
            sep=self.separator,
            decimal=self.decimal,
            index=False,
            encoding=self.encoding,
        )
        
        return output_path

    def convert_multiple(
        self,
        dataframes: list[pd.DataFrame],
        filenames: list[str],
    ) -> list[Path]:
        """Convert multiple DataFrames to CSV files.
        
        Args:
            dataframes: List of DataFrames to convert.
            filenames: List of output filenames.
            
        Returns:
            List of paths to created files.
        """
        if len(dataframes) != len(filenames):
            raise ValueError(
                "Number of DataFrames must match number of filenames"
            )
        
        output_paths = []
        for df, filename in zip(dataframes, filenames):
            output_path = self.convert(df, filename)
            output_paths.append(output_path)
        
        return output_paths


class BatchConverter(CSVConverter):
    """Converter for batch processing multiple files."""

    def __init__(self, output_dir: Optional[str] = None) -> None:
        """Initialize batch converter.
        
        Args:
            output_dir: Base output directory.
        """
        super().__init__(output_dir)

    def convert_directory(
        self,
        input_dir: str,
        file_pattern: str = "*.csv",
    ) -> list[Path]:
        """Convert all CSV files in a directory.
        
        Args:
            input_dir: Directory containing input CSV files.
            file_pattern: Pattern to match files.
            
        Returns:
            List of paths to converted files.
        """
        input_path = Path(input_dir)
        output_paths = []
        
        for csv_file in input_path.glob(file_pattern):
            df = pd.read_csv(
                csv_file,
                sep=self.separator,
                decimal=self.decimal,
            )
            output_path = self.convert(df, csv_file.stem)
            output_paths.append(output_path)
        
        return output_paths
