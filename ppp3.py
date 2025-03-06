# =============================================================================
# PPP Data Visualization Streamlit Application
# =============================================================================
# 
# Summary:
# This application provides an interactive visualization tool for exploring
# Purchasing Power Parity (PPP) data from the World Development Indicators dataset.
# It allows users to select up to 5 countries and compare their PPP trends over time
# through various chart types including line charts, bar charts, area charts, and
# ranking visualizations. The app includes detailed comparative analyses such as
# growth rates, relative performance, and summary statistics.
#
# Key Features:
# - Interactive country selection (up to 5 countries)
# - Multiple visualization types (Line, Bar, Area, Ranking charts)
# - Year range selection for focused analysis
# - Growth rate analysis and comparison
# - Summary statistics and detailed comparison tables
# - Responsive and user-friendly interface
#
# Requirements:
# - streamlit
# - pandas
# - numpy
# - matplotlib
# - seaborn
# - plotly
# - openpyxl (for Excel file reading)
#
# Author: Seawon Choi
# Date: March 6, 2025
# =============================================================================

# Import required libraries
import streamlit as st             # Core web application framework
import pandas as pd                # Data manipulation and analysis
import numpy as np                 # Numerical operations
import matplotlib.pyplot as plt    # Static plotting library
import seaborn as sns              # Statistical data visualization
import plotly.express as px        # Interactive plotting
import plotly.graph_objects as go  # Low-level interface to plotly
from plotly.subplots import make_subplots  # For creating complex subplot layouts

# Configure the Streamlit page settings
# - Setting a descriptive page title that appears in browser tabs
# - Adding a relevant emoji as page icon
# - Using a wide layout to maximize visualization space
# - Expanding the sidebar by default for immediate access to controls
st.set_page_config(
    page_title="PPP Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS to enhance the visual appearance and user experience
# This custom styling helps create a professional, polished interface with:
# - Clear visual hierarchy through distinctive headers
# - Card-based layout for organizing content into logical sections
# - Highlighted metric displays for key statistics
# - Consistent color scheme and spacing for visual coherence
st.markdown("""
<style>
    /* Main title styling for the application */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    
    /* Section header styling */
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #424242;
        margin-bottom: 1rem;
    }
    
    /* Card container styling for content sections */
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Styling for metric highlight cards */
    .metric-card {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin: 10px 0;
    }
    
    /* Styling for metric values (numbers) */
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0d47a1;
    }
    
    /* Styling for metric labels */
    .metric-label {
        font-size: 1rem;
        color: #616161;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Display the application title using custom styling
st.markdown('<div class="main-header">Purchasing Power Parity (PPP) Data Explorer</div>', unsafe_allow_html=True)

# Provide a concise description of the application's purpose and functionality
# This helps users understand what the app does and how to use it
st.markdown("""
This application visualizes GDP per capita (PPP) data from the World Development Indicators dataset.
You can select up to 5 countries to compare their PPP trends over time, explore different visualization types,
and analyze growth patterns and economic performance across nations.
""")

@st.cache_data  # Cache the data to improve performance
def load_data():
    """
    Load and preprocess the PPP data from the World Development Indicators file.
    
    This function:
    1. Detects whether the file is Excel or tab-delimited text
    2. Loads the data appropriately based on file type
    3. Restructures the data into a format suitable for visualization 
    4. Cleans and filters the data to focus on individual countries
    5. Handles missing values and converts data types
    
    Returns:
        pandas.DataFrame: Processed data with columns for Country Name, Country Code, Year, and PPP values
    """
    try:
        # Try to read the file as an Excel file first, since that's likely what it is
        # despite having a .txt extension
        try:
            df = pd.read_excel('PPP_Data_Extract_From_World_Development_Indicators.xlsx')
            st.success("Successfully loaded data from Excel file")
        except Exception as excel_error:
            # If Excel reading fails, try as a tab-delimited file with different encodings
            try:
                # Try reading with different encodings
                for encoding in ['utf-8', 'latin1', 'cp1252', 'ISO-8859-1']:
                    try:
                        df = pd.read_csv('PPP_Data_Extract_From_World_Development_Indicators.txt', 
                                        sep='\t', encoding=encoding)
                        st.success(f"Successfully loaded data using {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, try as a plain CSV
                    df = pd.read_csv('PPP_Data_Extract_From_World_Development_Indicators.txt')
                    st.success("Successfully loaded data as CSV")
            except Exception as text_error:
                # If both approaches fail, raise a comprehensive error
                raise Exception(f"Failed to read file as Excel: {excel_error}. " 
                              f"Also failed as text: {text_error}")
        
        # Extract year information from column names and create a mapping
        # The original format is like "2020 [YR2020]" and we want to extract just "2020"
        year_columns = [col for col in df.columns if '[YR' in str(col)]
        
        # If we don't find any year columns with the [YR] format, look for numeric columns
        if not year_columns:
            # Look for columns that might be years (numeric columns between 1900 and 2100)
            potential_year_cols = [col for col in df.columns 
                                 if str(col).isdigit() and 1900 <= int(col) <= 2100]
            if potential_year_cols:
                year_columns = potential_year_cols
                year_mapping = {col: int(col) for col in year_columns}
            else:
                # If still no year columns found, display columns and return sample data
                st.warning(f"Could not identify year columns. Found columns: {df.columns.tolist()}")
                return create_sample_data()
        else:
            year_mapping = {col: int(str(col).split('[YR')[1].split(']')[0]) 
                          for col in year_columns}
        
        # Rename the columns to use just the year value
        df = df.rename(columns=year_mapping)
        
        # Check if required identifier columns exist, or find alternatives
        required_cols = ['Series Name', 'Country Name', 'Country Code']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.warning(f"Missing columns: {missing_cols}. Will attempt to find alternatives.")
            # Try to find alternative column names
            for col in missing_cols:
                if col == 'Country Name' and 'Country' in df.columns:
                    df['Country Name'] = df['Country']
                elif col == 'Country Code' and 'ISO' in df.columns:
                    df['Country Code'] = df['ISO']
                elif col == 'Series Name' and 'Indicator' in df.columns:
                    df['Series Name'] = df['Indicator']
                else:
                    # If still missing, create placeholder
                    if col == 'Country Code':
                        df['Country Code'] = df['Country Name'].str[:3].str.upper() if 'Country Name' in df.columns else 'UNK'
                    elif col == 'Series Name':
                        df['Series Name'] = 'GDP per capita, PPP (current international $)'
        
        # Define which columns to keep as identifiers
        id_vars = [col for col in required_cols if col in df.columns]
        value_vars = list(year_mapping.values())
        
        # Display sample of the data to check it loaded correctly
        st.write("Sample of loaded data (first 5 rows):")
        st.dataframe(df.head())
        
        # Reshape the data from wide to long format
        # This transforms data from multiple year columns to a single 'Year' column with corresponding 'PPP' values
        melted_df = pd.melt(
            df,
            id_vars=id_vars,       # Columns to use as identifiers
            value_vars=value_vars, # Columns to unpivot (the years)
            var_name='Year',       # Name for the new column containing years
            value_name='PPP'       # Name for the new column containing PPP values
        )
        
        # Convert PPP string values to numeric, handling missing values
        # The 'coerce' parameter converts invalid strings to NaN
        melted_df['PPP'] = pd.to_numeric(melted_df['PPP'], errors='coerce')
        
        # Filter out aggregated regions to focus only on individual countries
        # The dataset includes both countries and regional aggregates which we want to exclude
        region_keywords = ['World', 'income', 'Latin America', 'East Asia', 'Europe', 
                           'Africa', 'Arab World', 'OECD', 'North America', 'South Asia']
        
        # Keep only rows where Country Name does not contain any of the region keywords
        country_df = melted_df[~melted_df['Country Name'].str.contains('|'.join(region_keywords), regex=True)]
        
        # Remove rows with missing PPP values to ensure data quality
        country_df = country_df.dropna(subset=['PPP'])
        
        # Optional data quality filter (commented out)
        # This would remove countries with fewer than 5 data points
        # count_by_country = country_df.groupby('Country Name').size()
        # countries_with_enough_data = count_by_country[count_by_country >= 5].index
        # country_df = country_df[country_df['Country Name'].isin(countries_with_enough_data)]
        
        return country_df
    
    except Exception as e:
        # If there's an error loading the data, display an error message
        st.error(f"Error loading data: {str(e)}")
        # Fall back to sample data so the app can still function
        return create_sample_data()

def create_sample_data():
    """
    Create synthetic PPP data for demonstration purposes when the real data can't be loaded.
    
    This function generates a realistic dataset that mimics the structure and patterns
    of actual PPP data, including:
    - A selection of major economies
    - Realistic starting values for different economic tiers
    - Varied growth rates to simulate different development trajectories
    - Data points at 5-year intervals from 1990 to 2020
    
    Returns:
        pandas.DataFrame: A sample dataset with the same structure as the real data
    """
    # A selection of major economies from different regions and development levels
    countries = ['United States', 'China', 'Germany', 'Japan', 'India', 'United Kingdom', 
                'France', 'Brazil', 'Italy', 'Canada']
    
    # Generate data at 5-year intervals
    years = list(range(1990, 2024, 5))
    
    data = []
    for country in countries:
        # Set different base values based on typical starting points for developed vs developing economies
        base = np.random.uniform(5000, 30000)
        
        # Assign different growth rates to simulate varied development trajectories
        # Values between 1.02 and 1.08 represent annual growth rates of 2-8%
        growth = np.random.uniform(1.02, 1.08)
        
        # Generate data points for each year using exponential growth pattern
        for i, year in enumerate(years):
            ppp = base * (growth ** i)
            data.append({
                'Series Name': 'GDP per capita, PPP (current international $)',
                'Country Name': country,
                'Country Code': country[:3].upper(),  # Create simple 3-letter country codes
                'Year': year,
                'PPP': ppp
            })
    
    return pd.DataFrame(data)

# Load and prepare the PPP data
# This initializes the application by loading the dataset once
# The @st.cache_data decorator ensures this only runs when needed
ppp_data = load_data()

# =====================================================================
# SIDEBAR CONTROLS
# =====================================================================
# Set up the user interface controls in the sidebar
# These controls allow users to filter and customize their data exploration

# Add a header for the country selection section
st.sidebar.markdown('<div class="sub-header">Country Selection</div>', unsafe_allow_html=True)

# Get a sorted list of all available countries for the selection dropdown
countries = sorted(ppp_data['Country Name'].unique())

# Create a multi-select dropdown for choosing countries
# - Limited to 5 countries maximum to maintain visualization clarity
# - Pre-selects major economies as default options if available
selected_countries = st.sidebar.multiselect(
    "Select up to 5 countries to compare",
    options=countries,
    default=['United States', 'China', 'Germany', 'Japan', 'India'][:min(5, len(countries))],
    max_selections=5  # Enforce the 5-country limit
)

# Create year range selector
# Automatically determines available min/max years from the dataset
min_year = int(ppp_data['Year'].min())
max_year = int(ppp_data['Year'].max())

# Create a slider for selecting the year range to analyze
# Default starts at 2000 to focus on more recent data
year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(2000, max_year),  # Default to showing data from 2000 onwards
    step=1
)

# Add additional visualization control options
st.sidebar.markdown('<div class="sub-header">Visualization Options</div>', unsafe_allow_html=True)

# Dropdown to select different chart types
chart_type = st.sidebar.selectbox(
    "Select Chart Type",
    options=["Line Chart", "Bar Chart", "Area Chart", "Ranking"]
)

# Option to toggle between absolute PPP values and growth rates
show_growth_rate = st.sidebar.checkbox(
    "Show Growth Rate", 
    value=False,  # Default to showing absolute PPP values
    help="Switch between PPP values and year-over-year growth rates"
)

# Information section with educational content about PPP
# This expandable section provides context for users who may be unfamiliar with PPP
with st.sidebar.expander("About PPP"):
    st.markdown("""
    **Purchasing Power Parity (PPP)** is an economic theory that compares different countries' currencies through a basket of goods approach. It allows for more accurate comparisons of economic productivity and living standards across countries by adjusting for price level differences.
    
    ### Why PPP matters:
    - Overcomes limitations of market exchange rates which can fluctuate for reasons unrelated to purchasing power
    - Provides a more accurate picture of real living standards across countries
    - Helps compare economies with different price levels and economic structures
    
    PPP is expressed in international dollars, a hypothetical unit of currency that has the same purchasing power as the U.S. dollar has in the United States.
    
    ### Example:
    If a hamburger costs $5 in the US but €4 in Germany, the PPP exchange rate for hamburgers would be 0.8 euros to the dollar, regardless of the market exchange rate.
    
    **Data Source**: World Development Indicators, World Bank
    """)

# =====================================================================
# DATA PROCESSING BASED ON USER SELECTIONS
# =====================================================================

# Process data only if countries have been selected
if selected_countries:
    # Apply filters based on user selections:
    # 1. Include only the selected countries
    # 2. Filter for the selected year range
    filtered_data = ppp_data[
        (ppp_data['Country Name'].isin(selected_countries)) & 
        (ppp_data['Year'] >= year_range[0]) & 
        (ppp_data['Year'] <= year_range[1])
    ]
    
    # If the user wants to see growth rates instead of absolute values,
    # we need to calculate year-over-year percentage changes
    if show_growth_rate:
        # Initialize an empty DataFrame to store growth rate data
        growth_data = pd.DataFrame()
        
        # Process each country separately to ensure correct growth calculation
        for country in selected_countries:
            # Extract and sort data for the current country
            country_data = filtered_data[filtered_data['Country Name'] == country].sort_values('Year')
            
            # Calculate percentage change from previous year
            # The pct_change() method calculates: (current_value - previous_value) / previous_value * 100
            country_data['Growth Rate (%)'] = country_data['PPP'].pct_change() * 100
            
            # Add the processed country data to our results
            growth_data = pd.concat([growth_data, country_data])
        
        # Replace the filtered data with the new data that includes growth rates
        filtered_data = growth_data
    
    # =====================================================================
# MAIN VISUALIZATIONS
# =====================================================================

    # Section header for the main visualizations
    st.markdown('<div class="sub-header">PPP Data Visualization</div>', unsafe_allow_html=True)
    
    # Display key metrics in a card layout with three columns
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    # Find the latest year in the selected data range for reference
    latest_year = filtered_data['Year'].max()
    # Get data for just the latest year
    latest_data = filtered_data[filtered_data['Year'] == latest_year]
    
    # COLUMN 1: Display the latest year in the selection
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{latest_year}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Latest Year in Selection</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # COLUMN 2: Display the country with highest PPP in the latest year
    with col2:
        if len(selected_countries) > 0:
            # Find the country with the highest PPP value
            highest_ppp_country = latest_data.loc[latest_data['PPP'].idxmax()]['Country Name']
            highest_ppp_value = latest_data['PPP'].max()
            
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{highest_ppp_country}</div>', unsafe_allow_html=True)
            st.markdown('<div class="metric-label">Highest PPP Country</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # COLUMN 3: Display the country with highest average annual growth rate
    with col3:
        # Only show growth metrics when not already displaying growth rate data
        if len(selected_countries) > 0 and not show_growth_rate:
            # Arrays to store growth data for each country
            highest_growth_countries = []
            highest_growth_rates = []
    
    # Main chart based on selection
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    if chart_type == "Line Chart":
        fig = px.line(
            filtered_data, 
            x='Year', 
            y='PPP' if not show_growth_rate else 'Growth Rate (%)',
            color='Country Name',
            markers=True,
            title=f"{'PPP' if not show_growth_rate else 'PPP Growth Rate'} Trends ({year_range[0]}-{year_range[1]})",
            labels={
                'PPP': 'GDP per capita, PPP (current international $)',
                'Growth Rate (%)': 'Year-over-Year Growth Rate (%)'
            }
        )
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Bar Chart":
        # Prepare data for specific years (start, middle, end)
        years_to_show = sorted(list(set([
            year_range[0], 
            year_range[0] + (year_range[1] - year_range[0]) // 2,
            year_range[1]
        ])))
        
        # Filter for these specific years
        bar_data = filtered_data[filtered_data['Year'].isin(years_to_show)]
        
        fig = px.bar(
            bar_data,
            x='Country Name',
            y='PPP' if not show_growth_rate else 'Growth Rate (%)',
            color='Country Name',
            animation_frame='Year',
            title=f"{'PPP' if not show_growth_rate else 'PPP Growth Rate'} Comparison",
            labels={
                'PPP': 'GDP per capita, PPP (current international $)',
                'Growth Rate (%)': 'Year-over-Year Growth Rate (%)'
            }
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Area Chart":
        fig = px.area(
            filtered_data,
            x='Year',
            y='PPP' if not show_growth_rate else 'Growth Rate (%)',
            color='Country Name',
            title=f"{'PPP' if not show_growth_rate else 'PPP Growth Rate'} Trends ({year_range[0]}-{year_range[1]})",
            labels={
                'PPP': 'GDP per capita, PPP (current international $)',
                'Growth Rate (%)': 'Year-over-Year Growth Rate (%)'
            }
        )
        fig.update_layout(
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Ranking":
        # Create a ranking chart showing how countries changed ranks over time
        years = sorted(filtered_data['Year'].unique())
        
        # Create a figure with subplots
        fig = make_subplots(rows=1, cols=len(years), shared_yaxes=True)
        
        for i, year in enumerate(years):
            year_data = filtered_data[filtered_data['Year'] == year].sort_values('PPP', ascending=False)
            
            fig.add_trace(
                go.Bar(
                    y=year_data['Country Name'],
                    x=year_data['PPP'],
                    orientation='h',
                    name=str(year),
                    text=year_data['PPP'].round(0).astype(int).astype(str),
                    textposition='outside',
                    marker=dict(color=px.colors.qualitative.Set2[i % len(px.colors.qualitative.Set2)])
                ),
                row=1, col=i+1
            )
        
        fig.update_layout(
            title=f"Ranking of Countries by PPP ({year_range[0]}-{year_range[1]})",
            height=400,
            showlegend=False,
            margin=dict(l=200)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional analyses
    st.markdown('<div class="sub-header">Detailed Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### PPP Comparison Table")
        
        # Create a pivot table
        pivot_table = filtered_data.pivot_table(
            index='Country Name',
            columns='Year',
            values='PPP' if not show_growth_rate else 'Growth Rate (%)',
            aggfunc='mean'
        )
        
        # Format the table
        formatted_table = pivot_table.style.format("{:,.1f}")
        
        # Display the table
        st.dataframe(formatted_table, height=400, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if not show_growth_rate:
            st.markdown("#### Relative PPP (Indexed to First Year)")
            
            # Calculate indexed values (first year = 100)
            indexed_data = pd.DataFrame()
            
            for country in selected_countries:
                country_data = filtered_data[filtered_data['Country Name'] == country].sort_values('Year')
                if not country_data.empty:
                    first_ppp = country_data['PPP'].iloc[0]
                    country_data['Indexed PPP'] = (country_data['PPP'] / first_ppp) * 100
                    indexed_data = pd.concat([indexed_data, country_data])
            
            # Create the chart
            fig = px.line(
                indexed_data,
                x='Year',
                y='Indexed PPP',
                color='Country Name',
                markers=True,
                title=f"Relative PPP Growth (First Year = 100)"
            )
            
            fig.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("#### Cumulative Growth since First Year")
            
            # Calculate cumulative growth rates
            cumulative_data = pd.DataFrame()
            
            for country in selected_countries:
                country_data = filtered_data[filtered_data['Country Name'] == country].sort_values('Year')
                if len(country_data) >= 2:
                    first_year_ppp = country_data['PPP'].iloc[0]
                    country_data['Cumulative Growth (%)'] = ((country_data['PPP'] / first_year_ppp) - 1) * 100
                    cumulative_data = pd.concat([cumulative_data, country_data])
            
            if not cumulative_data.empty:
                fig = px.line(
                    cumulative_data,
                    x='Year',
                    y='Cumulative Growth (%)',
                    color='Country Name',
                    markers=True,
                    title=f"Cumulative PPP Growth since {year_range[0]}"
                )
                
                fig.update_layout(
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Country comparison
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Country Comparison")
    
    # Create tabs for different comparison views
    tab1, tab2 = st.tabs(["Summary Statistics", "Growth Analysis"])
    
    with tab1:
        summary_stats = pd.DataFrame()
        
        for country in selected_countries:
            country_data = filtered_data[filtered_data['Country Name'] == country]
            
            if not country_data.empty:
                min_ppp = country_data['PPP'].min()
                max_ppp = country_data['PPP'].max()
                mean_ppp = country_data['PPP'].mean()
                
                first_year = country_data['Year'].min()
                last_year = country_data['Year'].max()
                first_ppp = country_data[country_data['Year'] == first_year]['PPP'].values[0]
                last_ppp = country_data[country_data['Year'] == last_year]['PPP'].values[0]
                
                total_growth = ((last_ppp / first_ppp) - 1) * 100
                years_diff = last_year - first_year
                avg_annual_growth = ((last_ppp / first_ppp) ** (1/years_diff) - 1) * 100 if years_diff > 0 else 0
                
                summary_stats = pd.concat([summary_stats, pd.DataFrame({
                    'Country': [country],
                    'Min PPP': [min_ppp],
                    'Max PPP': [max_ppp],
                    'Mean PPP': [mean_ppp],
                    'Total Growth (%)': [total_growth],
                    'Avg. Annual Growth (%)': [avg_annual_growth],
                    'First Year': [first_year],
                    'Last Year': [last_year]
                })])
        
        if not summary_stats.empty:
            summary_stats = summary_stats.reset_index(drop=True)
            summary_stats = summary_stats.sort_values('Mean PPP', ascending=False)
            
            # Format the table
            formatted_summary = summary_stats.style.format({
                'Min PPP': '{:,.1f}',
                'Max PPP': '{:,.1f}',
                'Mean PPP': '{:,.1f}',
                'Total Growth (%)': '{:.2f}%',
                'Avg. Annual Growth (%)': '{:.2f}%'
            })
            
            st.dataframe(formatted_summary, height=400, use_container_width=True)
    
    with tab2:
        # Calculate year-over-year growth for visualization
        growth_viz_data = pd.DataFrame()
        
        for country in selected_countries:
            country_data = filtered_data[filtered_data['Country Name'] == country].sort_values('Year')
            if len(country_data) >= 2:
                country_data['YoY Growth (%)'] = country_data['PPP'].pct_change() * 100
                growth_viz_data = pd.concat([growth_viz_data, country_data])
        
        if not growth_viz_data.empty:
            # Drop the first row for each country which has NaN growth
            growth_viz_data = growth_viz_data.dropna(subset=['YoY Growth (%)'])
            
            fig = px.bar(
                growth_viz_data,
                x='Year',
                y='YoY Growth (%)',
                color='Country Name',
                barmode='group',
                title="Year-over-Year PPP Growth Rates"
            )
            
            fig.update_layout(
                hovermode="x unified",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Please select at least one country to visualize the data.")

# Footer
st.markdown("""
---
### About the Data

This visualization is based on GDP per capita, PPP (current international $) data from the World Bank's World Development Indicators. 
PPP GDP is gross domestic product converted to international dollars using purchasing power parity rates. 

An international dollar has the same purchasing power over GDP as the U.S. dollar has in the United States.
""")

# Run the app with: streamlit run app.py
