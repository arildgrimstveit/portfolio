import pandas as pd
import streamlit as st

@st.cache_data
def load_portfolio_data(data_path="data/portfolio.csv", _force_reload=None):
    """
    Loads and processes the portfolio data from a CSV file.
    Caches the data to avoid reloading on every interaction.
    _force_reload parameter can be used to force cache refresh.
    """
    try:
        df = pd.read_csv(data_path, parse_dates=["Date"])
        df.sort_values(by=["Date", "Instrument"], inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Data file not found at {data_path}")
        return pd.DataFrame()

def get_portfolio_summary(df):
    """
    Calculates the portfolio's summary statistics.
    """
    if df.empty:
        return 0, 0, 0, pd.DataFrame()

    # Filter out TOTAL rows to avoid double counting, then sum by date
    df_without_total = df[df["Instrument"] != "TOTAL"]
    portfolio_over_time = df_without_total.groupby("Date")["Value_kNOK"].sum().reset_index()
    
    if len(portfolio_over_time) < 2:
        return 0, 0, 0, portfolio_over_time

    start_value = portfolio_over_time["Value_kNOK"].iloc[0]
    end_value = portfolio_over_time["Value_kNOK"].iloc[-1]
    absolute_change = end_value - start_value
    percent_change = (absolute_change / start_value) * 100 if start_value != 0 else 0
    
    return end_value, absolute_change, percent_change, portfolio_over_time

def get_latest_snapshot(df):
    """
    Gets the most recent data for each instrument.
    """
    if df.empty:
        return pd.DataFrame()
        
    latest_date = df["Date"].max()
    return df[df["Date"] == latest_date].sort_values(by="Value_kNOK", ascending=False)
