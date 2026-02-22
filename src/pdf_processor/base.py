"""Base classes for PDF processing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd


class BaseExtractor(ABC):
    """Abstract base class for PDF extractors.
    
    Subclasses must implement the extraction methods
    to handle different PDF formats.
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the extractor with a PDF file.
        
        Args:
            file_path: Path to the PDF file.
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

    @abstractmethod
    def extract_tables(self) -> List[pd.DataFrame]:
        """Extract tables from the PDF.
        
        Returns:
            List of DataFrames, one per table found.
        """
        pass

    @abstractmethod
    def extract_text(self) -> str:
        """Extract all text content from the PDF.
        
        Returns:
            Full text content as a string.
        """
        pass

    def validate_pdf(self) -> bool:
        """Validate that the file is a valid PDF.
        
        Returns:
            True if valid, False otherwise.
        """
        return self.file_path.suffix.lower() == ".pdf"


class BaseConverter(ABC):
    """Abstract base class for CSV converters."""

    def __init__(
        self,
        output_dir: Optional[str] = None,
        separator: str = ";",
        decimal: str = ",",
    ) -> None:
        """Initialize the converter.
        
        Args:
            output_dir: Directory for output CSV files.
            separator: CSV separator character.
            decimal: Decimal separator character.
        """
        self.output_dir = Path(output_dir) if output_dir else Path("data/output")
        self.separator = separator
        self.decimal = decimal
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def convert(
        self,
        data: pd.DataFrame,
        output_filename: str,
    ) -> Path:
        """Convert DataFrame to CSV.
        
        Args:
            data: DataFrame to convert.
            output_filename: Name for the output file.
            
        Returns:
            Path to the created CSV file.
        """
        pass

    def save_dataframe(
        self,
        df: pd.DataFrame,
        filename: str,
        index: bool = False,
    ) -> Path:
        """Save DataFrame to CSV with configured separators.
        
        Args:
            df: DataFrame to save.
            filename: Output filename.
            index: Whether to include index in CSV.
            
        Returns:
            Path to the saved file.
        """
        output_path = self.output_dir / filename
        df.to_csv(
            output_path,
            sep=self.separator,
            decimal=self.decimal,
            index=index,
            encoding="utf-8",
        )
        return output_path
