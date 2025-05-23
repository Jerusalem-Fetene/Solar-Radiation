import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")

st.title("Cross-Country Solar Farm Analysis Dashboard")

# --- Helper function to load data ---
@st.cache_data # Cache data to improve performance
def load_all_cleaned_data():
    base_path = '../data/' # Assuming app/main.py is run from the root of the repo (e.g., solar-challenge-week1)

    country_files = {
        'Benin': 'benin_clean.csv',
        'Sierra Leone': 'sierra_leone_clean.csv',
        'Togo': 'togo_clean.csv'
    }

    all_dfs = []
    for country, filename in country_files.items():
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, parse_dates=['Timestamp'])
            df['Country'] = country
            all_dfs.append(df)
        else:
            st.error(f"Error: Cleaned data file not found for {country} at {file_path}. Please run EDA notebooks first.")
            return pd.DataFrame() # Return empty if data is missing

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame()

df_combined = load_all_cleaned_data()

if not df_combined.empty:
    # --- Sidebar for Filtering ---
    st.sidebar.header("Filter Options")
    all_countries = df_combined['Country'].unique().tolist()
    selected_countries = st.sidebar.multiselect(
        "Select Countries:",
        options=all_countries,
        default=all_countries # Default to all countries
    )

    # Filter data based on selection
    filtered_df = df_combined[df_combined['Country'].isin(selected_countries)]

    if not filtered_df.empty:
        # --- Metrics Selection for Plots ---
        selected_metric = st.sidebar.selectbox(
            "Select Metric for Analysis:",
            options=['GHI', 'DNI', 'DHI', 'Tamb', 'RH', 'WS', 'BP']
        )

        st.subheader(f"Distribution of {selected_metric} Across Selected Countries")
        fig_box = px.box(filtered_df, x='Country', y=selected_metric, color='Country',
                         title=f'{selected_metric} Distribution',
                         labels={selected_metric: f'{selected_metric} ({filtered_df[selected_metric].name.split(" ")[-1] if "(" in filtered_df[selected_metric].name else ""})'}) # Dynamically get unit if available
        st.plotly_chart(fig_box, use_container_width=True)

        st.subheader(f"Time Series of {selected_metric}")
        fig_line = px.line(filtered_df, x='Timestamp', y=selected_metric, color='Country',
                           title=f'{selected_metric} Over Time')
        st.plotly_chart(fig_line, use_container_width=True)

        # --- Top Regions Table (e.g., by average GHI) ---
        st.subheader("Average GHI Ranking (Selected Countries)")
        if 'GHI' in filtered_df.columns:
            avg_ghi_ranking = filtered_df.groupby('Country')['GHI'].mean().sort_values(ascending=False).reset_index()
            avg_ghi_ranking.columns = ['Country', 'Average GHI ($W/m^2$)']
            st.dataframe(avg_ghi_ranking)
        else:
            st.info("GHI data not available for ranking in filtered selection.")

        # --- Cleaning Impact Chart (if 'Cleaning' column exists and is relevant) ---
        if 'Cleaning' in filtered_df.columns and filtered_df['Cleaning'].nunique() > 1:
            st.subheader("Average ModA & ModB by Cleaning Event")
            cleaning_impact_df = filtered_df.groupby(['Country', 'Cleaning'])[['ModA', 'ModB']].mean().reset_index()
            cleaning_impact_df['Cleaning Status'] = cleaning_impact_df['Cleaning'].map({0: 'No Cleaning', 1: 'Cleaning Occurred'})

            fig_cleaning = px.bar(cleaning_impact_df, x='Country', y=['ModA', 'ModB'],
                                  color='Cleaning Status', barmode='group',
                                  title='Average Module Readings Pre/Post-Cleaning')
            st.plotly_chart(fig_cleaning, use_container_width=True)

    else:
        st.info("Please select at least one country to view data.")
else:
    st.warning("No data loaded. Please ensure the EDA notebooks were run successfully and cleaned CSVs are in the 'data/' directory.")

# --- Git Hygiene & Documentation ---
# In your README.md, you would add instructions on how to run the Streamlit app:
# 1. Activate your virtual environment.
# 2. Navigate to the root of your repository (e.g., solar-challenge-week1).
# 3. Run the Streamlit app:
#    streamlit run app/main.py
#
# Remember to keep `data/` ignored in `.gitignore`.