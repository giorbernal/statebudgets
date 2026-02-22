"""Main Streamlit application."""

import streamlit as st
from pathlib import Path

import pandas as pd

from src.analytics.analyzer import DataAnalyzer
from src.visualization.charts import StreamlitCharts
from src.pdf_processor.extractor import PDFExtractor
from src.pdf_processor.converter import CSVConverter


# Page configuration
st.set_page_config(
    page_title="PDF to CSV Analytics",
    page_icon="📊",
    layout="wide",
)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_INPUT = PROJECT_ROOT / "data" / "input"
DATA_OUTPUT = PROJECT_ROOT / "data" / "output"


def main() -> None:
    """Main application entry point."""
    st.title("📊 PDF to CSV Analytics")
    st.markdown("Upload PDFs, convert to CSV, and analyze your data.")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Upload & Convert", "Data Analysis", "Visualizations"],
    )

    if page == "Upload & Convert":
        render_upload_page()
    elif page == "Data Analysis":
        render_analysis_page()
    elif page == "Visualizations":
        render_visualization_page()


def render_upload_page() -> None:
    """Render the file upload and conversion page."""
    st.header("📁 Upload & Convert")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
    )

    if uploaded_file is not None:
        # Save uploaded file
        input_path = DATA_INPUT / uploaded_file.name
        input_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File saved: {input_path}")
        
        # Extract and convert
        if st.button("Convert to CSV"):
            with st.spinner("Converting..."):
                try:
                    extractor = PDFExtractor(str(input_path))
                    tables = extractor.extract_tables()
                    
                    if tables:
                        converter = CSVConverter(str(DATA_OUTPUT))
                        output_path = converter.convert(
                            tables[0],
                            input_path.stem,
                        )
                        st.success(f"CSV saved: {output_path}")
                    else:
                        st.warning("No tables found in PDF")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Show existing CSV files
    st.divider()
    st.subheader("Existing CSV Files")
    
    csv_files = list(DATA_OUTPUT.glob("*.csv"))
    if csv_files:
        for csv_file in csv_files:
            st.write(f"- {csv_file.name}")
    else:
        st.info("No CSV files yet. Upload a PDF to convert.")


def render_analysis_page() -> None:
    """Render the data analysis page."""
    st.header("📈 Data Analysis")
    
    # File selector
    csv_files = list(DATA_OUTPUT.glob("*.csv"))
    
    if not csv_files:
        st.warning("No CSV files found. Go to Upload & Convert first.")
        return
    
    selected_file = st.selectbox(
        "Select a CSV file",
        [f.name for f in csv_files],
    )
    
    if selected_file:
        df = pd.read_csv(DATA_OUTPUT / selected_file)
        
        # Show data preview
        st.subheader("Data Preview")
        st.dataframe(df.head(10))
        
        # Show column info
        st.subheader("Column Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Data Types:**")
            st.write(df.dtypes)
        
        with col2:
            st.write("**Missing Values:**")
            st.write(df.isnull().sum())
        
        # Summary statistics
        st.subheader("Summary Statistics")
        st.dataframe(df.describe())


def render_visualization_page() -> None:
    """Render the visualization page."""
    st.header("📉 Visualizations")
    
    # File selector
    csv_files = list(DATA_OUTPUT.glob("*.csv"))
    
    if not csv_files:
        st.warning("No CSV files found. Go to Upload & Convert first.")
        return
    
    selected_file = st.selectbox(
        "Select a CSV file",
        [f.name for f in csv_files],
    )
    
    if selected_file:
        df = pd.read_csv(DATA_OUTPUT / selected_file)
        
        # Chart type selector
        chart_type = st.selectbox(
            "Select chart type",
            ["Line Chart", "Bar Chart", "Scatter Plot", "Histogram"],
        )
        
        # Column selectors
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        all_cols = df.columns.tolist()
        
        charts = StreamlitCharts()
        
        if chart_type == "Line Chart":
            x_col = st.selectbox("X axis", all_cols)
            y_col = st.selectbox("Y axis", numeric_cols)
            
            if st.button("Generate Chart"):
                fig = charts.create_line_chart(df, x_col, y_col)
                charts.plot_to_streamlit(fig)
                
        elif chart_type == "Bar Chart":
            x_col = st.selectbox("X axis", all_cols)
            y_col = st.selectbox("Y axis", numeric_cols)
            
            if st.button("Generate Chart"):
                fig = charts.create_bar_chart(df, x_col, y_col)
                charts.plot_to_streamlit(fig)
                
        elif chart_type == "Scatter Plot":
            x_col = st.selectbox("X axis", numeric_cols)
            y_col = st.selectbox("Y axis", numeric_cols)
            
            if st.button("Generate Chart"):
                fig = charts.create_scatter_plot(df, x_col, y_col)
                charts.plot_to_streamlit(fig)
                
        elif chart_type == "Histogram":
            col = st.selectbox("Column", numeric_cols)
            bins = st.slider("Number of bins", 5, 50, 20)
            
            if st.button("Generate Chart"):
                fig = charts.create_histogram(df, col, bins)
                charts.plot_to_streamlit(fig)


if __name__ == "__main__":
    main()
