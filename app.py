import streamlit as st
import data_manager
import ui_components
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import importlib.util

# --- Page Configuration ---
st.set_page_config(
    page_title="Grimstveit's Portfolio",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* === Main App & Layout === */
    .stApp {
        background-color: #121212;
    }
    .block-container {
        max-width: 1400px;
        padding-top: 4rem;      /* User-adjusted value */
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Remove default padding from the inner block of all containers */
    div[data-testid="stVerticalBlock"] {
        padding: 0;
    }

    /* === Header Section Styling === */
    section[data-testid="st-container"]:nth-of-type(1) {
        border-bottom: 1px solid #444;
        padding-bottom: 2rem;
        /* Define space AFTER the header section here */
        margin-bottom: 10rem;
    }

    /* === Subheader Styling === */
    h2 {
        font-size: 1.1rem;
        font-weight: 500;
        color: #B0B0B0;
        /* Removed margin-top to avoid confusion. Spacing is now handled by margin-bottom on the containers above. */
        margin-top: 0;
        padding-bottom: 1rem;
        border-bottom: 1px solid #444;
        margin-bottom: 1.5rem; /* Space between the line and the content below */
    }

    /* === Content Container Cleanup & Spacing === */
    /* This rule now also defines the space AFTER each content section */
    section[data-testid="st-container"]:not(:nth-of-type(1)) {
        background: transparent;
        border: none;
        /* Define space AFTER the content chart/cards here */
        margin-bottom: 10rem;
    }

    /* === Direct spacing between sections === */
    /* Add space after each subheader */
    h2 + div[data-testid="stVerticalBlock"] {
        margin-bottom: 8rem !important;
    }
    
    /* Add space after the main title container */
    section[data-testid="st-container"]:has(h1) {
        margin-bottom: 8rem !important;
    }
</style>
""", unsafe_allow_html=True)

def get_instrument_price_data(instrument_name, days=90):
    """Fetch 90 days of price data for an instrument"""
    # Map instrument names to Yahoo Finance symbols
    symbol_mapping = {
        'KRON_GLOBAL': None,  # Norwegian fund, no direct price data
        'NVDA': 'NVDA',
        'GOOG': 'GOOG', 
        'AAPL': 'AAPL',
        'AMD': 'AMD',
        'HOOD': 'HOOD',
        'KOG': 'KOG.OL',  # Norwegian stock
        'BTC': 'BTC-USD',
        'SOLANA': 'SOL-USD',
        'BSU': None,  # Norwegian savings, no price data
        'CS_KNIFE': None,  # CS2 skin, no price data
    }
    
    symbol = symbol_mapping.get(instrument_name)
    if symbol is None:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get historical data
        hist = ticker.history(start=start_date, end=end_date, interval='1d')
        
        if hist.empty:
            return None
            
        # Return closing prices
        return hist['Close'].tolist()
        
    except Exception as e:
        st.error(f"Error fetching data for {instrument_name}: {e}")
        return None

def get_user_instruments():
    """Get list of unique instruments from user's transactions"""
    try:
        # Try to import private transactions
        spec = importlib.util.find_spec('transactions_private')
        if spec is not None:
            transactions_private = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(transactions_private)
            
            # Extract unique instruments
            instruments = set()
            for transaction in transactions_private.transactions:
                instruments.add(transaction[1])  # Instrument name is at index 1
            return list(instruments)
        else:
            return []
    except Exception as e:
        st.error(f"Error loading private transactions: {e}")
        return []

# --- Data Loading ---
import os
import time
# Force cache refresh by including file modification time
csv_path = "data/portfolio.csv"
file_mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else time.time()
df = data_manager.load_portfolio_data(_force_reload=file_mtime)

if not df.empty:
    # --- Data Processing ---
    end_value, absolute_change, percent_change, portfolio_over_time = data_manager.get_portfolio_summary(df)
    latest_snapshot = data_manager.get_latest_snapshot(df)

    # --- Header Section ---
    with st.container():
        st.title("🏠 Grimstveit's Portfolio")
        change_color = "green" if percent_change >= 0 else "red"
        change_symbol = "+" if percent_change >= 0 else ""
        end_value_str = f"{end_value * 1000:,.0f}".replace(",", " ")
        absolute_change_str = f"{absolute_change * 1000:,.0f}".replace(",", " ")
        # The `gap` property reduces space between the total and the change line
        header_html = f"""
        <div style="display: flex; flex-direction: column; align-items: flex-start; gap: 0.5rem;">
            <div style="font-size: 2.5rem; font-weight: 600; color: white; margin: 0; line-height: 1;">{end_value_str} NOK</div>
            <div style="font-size: 1.25rem; font-weight: bold; color: {change_color}; margin: 0; line-height: 1;">
                {change_symbol}{absolute_change_str} NOK ({change_symbol}{percent_change:.1f}%)
            </div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

    # Add space between header and development
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

    # --- Development Chart Section ---
    st.subheader("📈 Development")
    with st.container():
        portfolio_chart = ui_components.create_main_portfolio_chart(portfolio_over_time)
        st.plotly_chart(portfolio_chart, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
    
    # Add space between development and allocation
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)
    
    # --- Allocation Chart Section ---
    st.subheader("📊 Allocation")
    with st.container():
        # Filter out TOTAL from allocation chart
        allocation_data = latest_snapshot[latest_snapshot['Instrument'] != 'TOTAL']
        allocation_chart = ui_components.create_allocation_bar_chart(allocation_data)
        st.plotly_chart(allocation_chart, use_container_width=True, config={'displayModeBar': False})

    # Add space between allocation and instruments
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

    # --- Instrument Breakdown Section ---
    st.subheader("💼 Instruments")
    with st.container():
        # Filter out TOTAL from instrument cards too
        instruments_data = latest_snapshot[latest_snapshot['Instrument'] != 'TOTAL']
        
        # Get user's actual instruments and their price data
        user_instruments = get_user_instruments()
        instrument_price_data = {}
        
        # Fetch price data for each instrument
        with st.spinner("Fetching latest price data..."):
            for instrument in user_instruments:
                price_data = get_instrument_price_data(instrument)
                if price_data:
                    instrument_price_data[instrument] = price_data
        
        ui_components.render_instrument_cards(df, instruments_data, instrument_price_data)

else:
    st.warning("Could not load portfolio data. Please check the data file.")
