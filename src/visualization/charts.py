"""Chart and visualization utilities."""

from typing import Optional, List, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class ChartGenerator:
    """Main class for generating charts."""

    def __init__(self, style: str = "whitegrid") -> None:
        """Initialize chart generator.
        
        Args:
            style: Seaborn style for plots.
        """
        self.style = style
        sns.set_style(style)

    def create_line_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        hue: Optional[str] = None,
    ) -> plt.Figure:
        """Create a line chart.
        
        Args:
            df: Data to plot.
            x: Column for x-axis.
            y: Column for y-axis.
            title: Chart title.
            xlabel: X-axis label.
            ylabel: Y-axis label.
            hue: Column for color grouping.
            
        Returns:
            Matplotlib Figure.
        """
        fig, ax = plt.subplots()
        sns.lineplot(data=df, x=x, y=y, hue=hue, ax=ax)
        
        if title:
            ax.set_title(title)
        if xlabel:
            ax.set_xlabel(xlabel)
        if ylabel:
            ax.set_ylabel(ylabel)
        
        return fig

    def create_bar_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "",
        orient: str = "v",
    ) -> plt.Figure:
        """Create a bar chart.
        
        Args:
            df: Data to plot.
            x: Column for x-axis.
            y: Column for y-axis.
            title: Chart title.
            orient: Orientation ('v' or 'h').
            
        Returns:
            Matplotlib Figure.
        """
        fig, ax = plt.subplots()
        sns.barplot(data=df, x=x, y=y, orient=orient, ax=ax)
        
        if title:
            ax.set_title(title)
        
        return fig

    def create_histogram(
        self,
        df: pd.DataFrame,
        column: str,
        bins: int = 30,
        title: str = "",
    ) -> plt.Figure:
        """Create a histogram.
        
        Args:
            df: Data to plot.
            column: Column to plot.
            bins: Number of bins.
            title: Chart title.
            
        Returns:
            Matplotlib Figure.
        """
        fig, ax = plt.subplots()
        sns.histplot(data=df, x=column, bins=bins, ax=ax)
        
        if title:
            ax.set_title(title)
        
        return fig

    def create_scatter_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        hue: Optional[str] = None,
        title: str = "",
    ) -> plt.Figure:
        """Create a scatter plot.
        
        Args:
            df: Data to plot.
            x: Column for x-axis.
            y: Column for y-axis.
            hue: Column for color grouping.
            title: Chart title.
            
        Returns:
            Matplotlib Figure.
        """
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x=x, y=y, hue=hue, ax=ax)
        
        if title:
            ax.set_title(title)
        
        return fig

    def create_heatmap(
        self,
        df: pd.DataFrame,
        title: str = "",
        annot: bool = True,
    ) -> plt.Figure:
        """Create a heatmap.
        
        Args:
            df: Data to plot (must be numeric).
            title: Chart title.
            annot: Whether to show values in cells.
            
        Returns:
            Matplotlib Figure.
        """
        fig, ax = plt.subplots()
        sns.heatmap(data=df, annot=annot, ax=ax)
        
        if title:
            ax.set_title(title)
        
        return fig

    def create_box_plot(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "",
    ) -> plt.Figure:
        """Create a box plot.
        
        Args:
            df: Data to plot.
            x: Column for x-axis (categorical).
            y: Column for y-axis (numeric).
            title: Chart title.
            
        Returns:
            Matplotlib Figure.
        """
        fig, ax = plt.subplots()
        sns.boxplot(data=df, x=x, y=y, ax=ax)
        
        if title:
            ax.set_title(title)
        
        return fig


class StreamlitCharts(ChartGenerator):
    """Chart generator optimized for Streamlit integration."""

    def __init__(self) -> None:
        """Initialize Streamlit-compatible chart generator."""
        super().__init__()

    def plot_to_streamlit(self, fig: plt.Figure) -> None:
        """Display matplotlib figure in Streamlit.
        
        Args:
            fig: Matplotlib Figure to display.
        """
        import streamlit as st
        st.pyplot(fig)

    def create_interactive_line(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
    ) -> None:
        """Create interactive line chart for Streamlit.
        
        Args:
            df: Data to plot.
            x: Column for x-axis.
            y: Column for y-axis.
        """
        import streamlit as st
        st.line_chart(data=df, x=x, y=y)

    def create_interactive_bar(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
    ) -> None:
        """Create interactive bar chart for Streamlit.
        
        Args:
            df: Data to plot.
            x: Column for x-axis.
            y: Column for y-axis.
        """
        import streamlit as st
        st.bar_chart(data=df, x=x, y=y)
