import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
import pandas as pd
from datetime import timedelta
import importlib.util
import yfinance as yf
import requests
import json

# --- Formatting Functions ---
def format_nok_value(value_knok, show_currency=True):
    """
    Format kNOK values for display.
    Args:
        value_knok: Value in thousands of NOK
        show_currency: Whether to show 'NOK' suffix
    Returns:
        Formatted string (e.g., "267 000 NOK" or "267 000")
    """
    actual_nok = value_knok * 1000
    formatted = f"{actual_nok:,.0f}".replace(",", " ")
    return f"{formatted} NOK" if show_currency else formatted

def format_nok_change(change_knok, show_currency=True):
    """
    Format kNOK change values with proper sign.
    Args:
        change_knok: Change in thousands of NOK
        show_currency: Whether to show 'NOK' suffix
    Returns:
        Formatted string with sign (e.g., "+9 000 NOK" or "-3 000")
    """
    actual_change = change_knok * 1000
    formatted = f"{actual_change:,.0f}".replace(",", " ")
    sign = "+" if change_knok >= 0 else ""
    return f"{sign}{formatted} NOK" if show_currency else f"{sign}{formatted}"

# --- Constants for Styling ---
TRADINGVIEW_COLORS = {
    'primary': '#2962FF',
    'secondary': '#FF6B6B',
    'background': '#1E1E1E',
    'text': '#FFFFFF',
    'grid': '#2A2A2A',
    'accent': '#00D4AA',
    'tradingview_green': '#00C851',  # Classic TradingView green
    'tradingview_red': '#FF4444',   # Classic TradingView red
    'bybit_orange': '#F7931A'       # Bybit orange
}

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_stock_price_history(stock_name, period="1y"):
    """
    Fetch real-time price history for stocks.
    Returns a list of price values for the sparkline.
    """
    try:
        # Stock tickers
        stock_tickers = {
            'KOG': 'KOG.OL',  # Kongsberg Gruppen
            'AAPL': 'AAPL',
            'GOOG': 'GOOGL',
            'AMD': 'AMD',
            'NVDA': 'NVDA',
            'HOOD': 'HOOD',
            'BTC': 'BTC-USD',
            'SOLANA': 'SOL-USD',
        }
        
        if stock_name not in stock_tickers:
            return None
            
        ticker = yf.Ticker(stock_tickers[stock_name])
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
            
        # Debug: Print the period being used
        print(f"Fetching {stock_name} data for period: {period}, got {len(hist)} data points")
        
        # Return closing prices as a list
        return hist['Close'].tolist()
        
    except Exception as e:
        print(f"Error fetching {stock_name} data: {e}")
        return None

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_fund_price_history(fund_name, period="1y"):
    """
    Fetch real-time price history for Norwegian funds.
    Returns a list of price values for the sparkline.
    """
    try:
        # Norwegian fund tickers (you may need to adjust these)
        fund_tickers = {
            'KRON_GLOBAL': 'KR-KINGL.OL',  # Kron Indeks Global - try alternative if this doesn't work
            'BSU': None,  # BSU doesn't have a ticker, use portfolio data
            'CS_KNIFE': None,  # Custom instrument, use portfolio data
        }
        
        # Try alternative tickers if the main one fails
        alternative_tickers = {
            'KRON_GLOBAL': ['KR-KINGL.OL', 'KR-KINGL', 'KINGL.OL', 'KRON.OL']
        }
        
        if fund_name not in fund_tickers or fund_tickers[fund_name] is None:
            return None
            
        # Try the main ticker first
        ticker_symbol = fund_tickers[fund_name]
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        
        # If main ticker fails, try alternatives
        if hist.empty and fund_name in alternative_tickers:
            for alt_ticker in alternative_tickers[fund_name]:
                if alt_ticker != ticker_symbol:  # Don't try the same one twice
                    ticker = yf.Ticker(alt_ticker)
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        ticker_symbol = alt_ticker
                        break
        
        if hist.empty:
            return None
            
        # Return closing prices as a list
        return hist['Close'].tolist()
        
    except Exception as e:
        return None

def create_main_portfolio_chart(portfolio_over_time):
    """
    Creates the main portfolio development chart using Plotly with
    dynamic colors (green for gains, red for losses) and candlestick-like styling.
    """
    fig = go.Figure()

    # Calculate if overall trend is positive or negative
    start_value = portfolio_over_time["Value_kNOK"].iloc[0]
    end_value = portfolio_over_time["Value_kNOK"].iloc[-1]
    is_positive = end_value >= start_value
    
    # Choose colors based on performance
    line_color = TRADINGVIEW_COLORS['tradingview_green'] if is_positive else TRADINGVIEW_COLORS['tradingview_red']
    
    # Create the main line trace with dynamic color
    fig.add_trace(go.Scatter(
        x=portfolio_over_time["Date"],
        y=portfolio_over_time["Value_kNOK"],
        mode='lines+markers',
        line=dict(color=line_color, width=2),
        marker=dict(size=4, color=line_color),
        name="Portfolio Value",
        hovertemplate='<b>%{customdata}</b><br><span style="color:#888">%{x|%b %d, %Y}</span><extra></extra>',
        customdata=[format_nok_value(val, show_currency=True) for val in portfolio_over_time["Value_kNOK"]]
    ))
    


    fig.update_layout(
        height=500,
        margin=dict(l=50, r=50, t=30, b=50),
        plot_bgcolor=TRADINGVIEW_COLORS['background'],
        paper_bgcolor=TRADINGVIEW_COLORS['background'],
        font=dict(color=TRADINGVIEW_COLORS['text']),
        dragmode='pan',  # Back to pan for main chart interaction
        xaxis=dict(
            gridcolor=TRADINGVIEW_COLORS['grid'],
            showgrid=True,
            zeroline=False,
            rangeslider=dict(visible=False),
            fixedrange=False,
            tickfont=dict(size=14, color=TRADINGVIEW_COLORS['text']),
            tickmode='auto',
            tickformatstops = [
                dict(dtickrange=[None, "M1"], value="%b %d"),
                dict(dtickrange=["M1", "M12"], value="%b"),
                dict(dtickrange=["M12", None], value="%Y")
            ]
        ),
        yaxis=dict(
            gridcolor=TRADINGVIEW_COLORS['grid'],
            showgrid=True,
            zeroline=False,
            title="",
            side="right",
            showticklabels=True,
            fixedrange=False,
            autorange=True,
            type='linear',
            tickmode='auto',
            nticks=8,
            tickformat='.0f',
            tickfont=dict(size=14, color=TRADINGVIEW_COLORS['text']),
            showline=False,
            ticks='outside',
            ticklen=5
        ),
        # Enable advanced interactions
        hovermode='closest',
        # Add custom interaction behavior
        uirevision=True  # Preserves zoom state
    )
    return fig

def create_allocation_bar_chart(latest_snapshot):
    """
    Creates a cleaner, more professional, and taller allocation bar chart.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=latest_snapshot["Value_kNOK"] * 1000,  # Convert to actual NOK
        y=latest_snapshot["Instrument"],
        orientation='h',
        marker=dict(
            color=TRADINGVIEW_COLORS['bybit_orange'],
            line=dict(color=TRADINGVIEW_COLORS['bybit_orange'], width=1)
        ),
        text=[f"{val*1000:,.0f}".replace(",", " ") for val in latest_snapshot["Value_kNOK"]],
        textposition='outside',
        textfont=dict(
            size=16,
            color=TRADINGVIEW_COLORS['text']
        ),
        width=0.8
    ))

    fig.update_layout(
        height=500,
        margin=dict(l=150, r=50, t=30, b=50),
        plot_bgcolor=TRADINGVIEW_COLORS['background'],
        paper_bgcolor=TRADINGVIEW_COLORS['background'],
        font=dict(color=TRADINGVIEW_COLORS['text'], size=14),
        xaxis=dict(
            title="Value (NOK)",
            showgrid=True,
            gridcolor=TRADINGVIEW_COLORS['grid'],
            tickformat='.0f'
        ),
        yaxis=dict(
            showgrid=False,
            autorange="reversed",
            tickfont=dict(size=16)
        )
    )
    return fig

def _create_sparkline(values, width=220, height=40, is_positive_return=None):
    """Internal helper to create a beautiful SVG sparkline."""
    if len(values) < 2:
        return ""
    min_val, max_val = min(values), max(values)
    val_range = max_val - min_val if max_val != min_val else 1
    points = []
    for i, val in enumerate(values):
        x = (i / (len(values) - 1)) * (width - 10) + 5
        y = height - 5 - ((val - min_val) / val_range) * (height - 10)
        points.append(f"{x:.1f},{y:.1f}")
    
    # Use the provided return status if available, otherwise use data trend
    if is_positive_return is not None:
        line_color = "#00D4AA" if is_positive_return else "#FF6B6B"
    else:
        start_val, end_val = values[0], values[-1]
        change_percent = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0
        line_color = "#00D4AA" if change_percent >= 0 else "#FF6B6B"
    
    fill_points = ["5," + str(height - 5)] + points + [str(width - 5) + "," + str(height - 5)]
    return f'<svg width="{width}" height="{height}"><polygon points="{" ".join(fill_points)}" fill="{line_color}" fill-opacity="0.2"/><polyline points="{" ".join(points)}" fill="none" stroke="{line_color}" stroke-width="2"/></svg>'

# Helper to load user transactions
spec = importlib.util.find_spec('transactions_private')
if spec is not None:
    transactions_private = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transactions_private)
    USER_TRANSACTIONS = transactions_private.transactions
else:
    USER_TRANSACTIONS = []

def get_usd_nok_rate():
    try:
        ticker = yf.Ticker("USDNOK=X")
        rate = ticker.history(period="5d")['Close'].iloc[-1]
        return float(rate)
    except Exception:
        return 10.5  # fallback
USD_NOK = get_usd_nok_rate()

def get_personal_return(instrument_name, latest_price, currency, quantity):
    total_invested_nok = 0
    total_quantity = 0
    
    # Special handling for BTC - amounts are total invested, not price per unit
    if instrument_name == 'BTC':
        for tx in USER_TRANSACTIONS:
            _, instr, qty, amount_invested, cur = tx
            if instr == instrument_name:
                total_invested_nok += amount_invested  # This is the total amount invested
                total_quantity += qty  # This is the BTC quantity
    elif instrument_name == 'SOLANA':
        # Special handling for SOLANA - use actual transaction data
        for tx in USER_TRANSACTIONS:
            _, instr, qty, price, cur = tx
            if instr == instrument_name:
                # For SOLANA, price is the total amount invested (5,000 NOK)
                total_invested_nok += price  # This is the total amount invested
                total_quantity += qty  # This is the SOLANA quantity
    else:
        # Regular handling for other instruments
        for tx in USER_TRANSACTIONS:
            _, instr, qty, price, cur = tx
            if instr == instrument_name:
                if cur == 'NOK':
                    total_invested_nok += price * qty
                elif cur == 'USD':
                    total_invested_nok += price * qty * USD_NOK
                else:
                    total_invested_nok += price * qty
                total_quantity += qty
    
    if total_quantity == 0 or total_invested_nok == 0:
        return 0, 0, 0, 0, 0
    
    # For portfolio-only instruments, convert from kNOK to NOK for comparison with transactions
    if instrument_name in ['KRON_GLOBAL', 'BSU', 'CS_KNIFE']:
        current_value_nok = latest_price * 1000  # Convert from kNOK to NOK
    elif instrument_name == 'SOLANA':
        # For SOLANA, calculate current value based on current market price
        # Get current SOL price from Yahoo Finance (cached to avoid slow loading)
        try:
            sol_ticker = yf.Ticker("SOL-USD")
            current_sol_price_usd = sol_ticker.history(period="1d")['Close'].iloc[-1]
            current_sol_price_nok = current_sol_price_usd * USD_NOK
            current_value_nok = total_quantity * current_sol_price_nok
        except:
            # Fallback to portfolio data if market data fails
            current_value_nok = latest_price * 1000
    else:
        # For market instruments, use the portfolio value directly (already calculated)
        current_value_nok = latest_price * 1000  # Convert from kNOK to NOK
    
    # Debug logging for BTC
    if instrument_name == 'BTC':
        print(f"BTC Debug: total_invested={total_invested_nok}, total_quantity={total_quantity}, latest_price={latest_price}, current_value={current_value_nok}, USD_NOK={USD_NOK}")
    
    abs_return = current_value_nok - total_invested_nok
    pct_return = (current_value_nok / total_invested_nok - 1) * 100
    
    # Debug output for SOLANA
    if instrument_name == 'SOLANA':
        print(f"SOLANA Debug: invested={total_invested_nok}, current={current_value_nok}, return={abs_return}, pct={pct_return}%")
    
    return total_invested_nok, total_quantity, current_value_nok, abs_return, pct_return

def render_instrument_cards(df, latest_snapshot, instrument_price_data=None):
    """
    Renders instrument cards in a robust grid using Streamlit's native columns
    with the 'small' gap setting for tight, professional spacing.
    This is the definitive, correct implementation.
    """
    # Add custom CSS for button styling
    st.markdown("""
    <style>
    /* Custom styling for Streamlit buttons to look like Bybit buttons */
    div[data-testid="stButton"] {
        margin: 0 !important;
        padding: 0 !important;
        display: inline-block !important;
    }
    /* Target all buttons with maximum specificity */
    div[data-testid="stButton"] button,
    div[data-testid="stButton"] button[data-baseweb="button"],
    div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="true"],
    div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="false"] {
        background-color: #2A2A2A !important;
        color: #FFFFFF !important;
        border: 1px solid #444 !important;
        padding: 2px 4px !important;
        font-size: 8px !important;
        border-radius: 2px !important;
        font-weight: 400 !important;
        transition: all 0.2s !important;
        min-width: 20px !important;
        width: 20px !important;
        height: 16px !important;
        line-height: 1 !important;
        margin: 0 1px !important;
        text-align: center !important;
        display: inline-block !important;
        box-shadow: none !important;
        outline: none !important;
    }
    /* Hover state */
    div[data-testid="stButton"] button:hover,
    div[data-testid="stButton"] button[data-baseweb="button"]:hover {
        background-color: #3A3A3A !important;
        color: #FFFFFF !important;
        border-color: #555 !important;
    }
    /* Selected state - override everything */
    div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="true"],
    div[data-testid="stButton"] button[data-baseweb="button"]:focus,
    div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="true"]:hover {
        background-color: #FF4444 !important;
        color: #FFFFFF !important;
        border-color: #FF4444 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for timeframes if not exists
    if 'timeframes' not in st.session_state:
        st.session_state.timeframes = {}
    
    # Read timeframe parameters from URL
    query_params = st.query_params
    print(f"URL parameters: {dict(query_params)}")
    for param, values in query_params.items():
        if param.startswith('tf_'):
            instrument = param.replace('tf_', '')
            period = values[0]
            print(f"Found timeframe parameter: {instrument} = {period}")
            # Clear cache for this instrument when timeframe changes
            if instrument in st.session_state.timeframes and st.session_state.timeframes[instrument] != period:
                print(f"Timeframe changed for {instrument}: {st.session_state.timeframes[instrument]} -> {period}")
                # Clear the cache for this instrument
                get_stock_price_history.clear()
                get_fund_price_history.clear()
            st.session_state.timeframes[instrument] = period
    
    print(f"Session state timeframes: {st.session_state.timeframes}")
    

    
    items_per_row = 4
    num_instruments = len(latest_snapshot)

    card_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background: transparent; }}
            .card {{ 
                background: linear-gradient(135deg, #2A2A2A 0%, #1E1E1E 100%); 
                padding: 24px; 
                border-radius: 12px; 
                border: 1px solid #3A3A3A; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
                height: 280px; 
                width: 100%; 
                display: flex; 
                flex-direction: column; 
                justify-content: space-between; 
                box-sizing: border-box; 
            }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; }}
            .instrument-name {{ color: #FFFFFF; font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
            .change-percent {{ font-size: 12px; font-weight: 500; flex-shrink: 0; padding-left: 10px;}}
            .sparkline-container {{ text-align: center; flex: 1; display: flex; align-items: center; justify-content: center; width: 100%; }}
            .value {{ color: #FFFFFF; font-size: 16px; font-weight: 700; text-align: center; }}
            
            /* Custom styling for Streamlit buttons to look like Bybit buttons */
            /* Target all button containers */
            div[data-testid="stButton"] {{
                margin: 0 !important;
                padding: 0 !important;
                display: inline-block !important;
                width: 16px !important;
                height: 12px !important;
            }}
            /* Target all buttons with maximum specificity */
            div[data-testid="stButton"] button,
            div[data-testid="stButton"] button[data-baseweb="button"],
            div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="true"],
            div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="false"] {{
                background-color: #2A2A2A !important;
                color: #FFFFFF !important;
                border: 1px solid #444 !important;
                padding: 1px 2px !important;
                font-size: 7px !important;
                border-radius: 1px !important;
                font-weight: 400 !important;
                transition: all 0.2s !important;
                min-width: 16px !important;
                width: 16px !important;
                height: 12px !important;
                line-height: 1 !important;
                margin: 0 0px !important;
                text-align: center !important;
                display: inline-block !important;
                box-shadow: none !important;
                outline: none !important;
            }}
            /* Hover state */
            div[data-testid="stButton"] button:hover,
            div[data-testid="stButton"] button[data-baseweb="button"]:hover {{
                background-color: #3A3A3A !important;
                color: #FFFFFF !important;
                border-color: #555 !important;
            }}
            /* Selected state - override everything */
            div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="true"],
            div[data-testid="stButton"] button[data-baseweb="button"]:focus,
            div[data-testid="stButton"] button[data-baseweb="button"][aria-pressed="true"]:hover {{
                background-color: #FF4444 !important;
                color: #FFFFFF !important;
                border-color: #FF4444 !important;
            }}
            /* Reduce spacing between button containers */
            div[data-testid="stButton"] + div[data-testid="stButton"] {{
                margin-left: 0px !important;
            }}

        </style>
    </head>
    <body>
        <div class="card">
            <div class="card-header">
                <span class="instrument-name">{instrument_name}</span>
                <span class="change-percent" style="color: {change_color};">{change_symbol}{change_percent:.1f}%</span>
            </div>
                        <div class="sparkline-container">{sparkline_svg}</div>
            <div class="value">{latest_val_formatted} <span style="color: {change_color};">({change_formatted})</span></div>
        </div>
    </body>
    </html>
    """
    
    bsu_interest_rate = 6.6  # Current BSU interest rate
    for row_start in range(0, num_instruments, items_per_row):
        row_end = min(row_start + items_per_row, num_instruments)
        row_snapshot = latest_snapshot.iloc[row_start:row_end]
        
        # Create a centered container for each row
        # Create a centered container for each row
        with st.container():
            # Calculate perfect centering with gap compensation
            # For 4 cards with large gaps, we need to account for the gap space
            # Let's use a ratio that compensates for the gaps
            left_pad, content, right_pad = st.columns([1, 10**18, 1])
            with content:
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1], gap="large")
            
            for i in range(len(row_snapshot)):
                
                row = row_snapshot.iloc[i]
                instrument_name = row["Instrument"]
                instrument_df = df[df["Instrument"] == instrument_name].sort_values("Date")
                
                # Determine currency
                if instrument_name in ['AAPL','GOOG','AMD','NVDA','HOOD','BTC','SOLANA']:
                    currency = 'USD' if instrument_name != 'KOG' else 'NOK'
                else:
                    currency = 'NOK'
                
                # Get latest price for calculations
                latest_price = instrument_df["Value_kNOK"].iloc[-1]
                latest_price_for_calc = latest_price

                # Calculate total quantity held for this instrument
                quantity = 0
                for tx in USER_TRANSACTIONS:
                    _, instr, qty, _, _ = tx
                    if instr == instrument_name:
                        quantity += qty
                total_invested_nok, total_quantity, current_value_nok, abs_return, pct_return = get_personal_return(instrument_name, latest_price_for_calc, currency, quantity)
                # Format for display (show NOK, not kNOK)
                change_color = "#00D4AA" if pct_return >= 0 else "#FF6B6B"
                change_symbol = "+" if pct_return >= 0 else ""
                
                # Get selected timeframe for this instrument
                selected_period = st.session_state.timeframes.get(instrument_name, "1y")
                
                # Debug: Print the selected period
                print(f"{instrument_name}: Using period {selected_period}")
                
                # Update sparkline to reflect actual return
                if instrument_name in ['KRON_GLOBAL', 'BSU', 'CS_KNIFE']:
                    price_values = get_fund_price_history(instrument_name, period=selected_period)
                    if price_values and len(price_values) >= 2:
                        sparkline_svg = _create_sparkline(price_values, is_positive_return=(pct_return >= 0))
                        print(f"{instrument_name}: Using fund price data, {len(price_values)} points")
                    else:
                        sparkline_svg = _create_sparkline(instrument_df["Value_kNOK"].tolist(), is_positive_return=(pct_return >= 0))
                        print(f"{instrument_name}: Using portfolio data, {len(instrument_df)} points")
                elif instrument_name in ['KOG', 'AAPL', 'GOOG', 'AMD', 'NVDA', 'HOOD', 'BTC', 'SOLANA']:
                    # Use real stock price data for stocks
                    price_values = get_stock_price_history(instrument_name, period=selected_period)
                    if price_values and len(price_values) >= 2:
                        sparkline_svg = _create_sparkline(price_values, is_positive_return=(pct_return >= 0))
                        print(f"{instrument_name}: Using stock price data, {len(price_values)} points")
                    else:
                        sparkline_svg = _create_sparkline(instrument_df["Value_kNOK"].tolist(), is_positive_return=(pct_return >= 0))
                        print(f"{instrument_name}: Using portfolio data, {len(instrument_df)} points")
                else:
                    sparkline_svg = _create_sparkline(instrument_df["Value_kNOK"].tolist(), is_positive_return=(pct_return >= 0))
                    print(f"{instrument_name}: Using portfolio data, {len(instrument_df)} points")
                
                # All instruments use the same formatting now
                latest_val_formatted = format_nok_value(current_value_nok/1000, show_currency=False) if current_value_nok else format_nok_value(0, show_currency=False)
                change_formatted = format_nok_change(abs_return/1000, show_currency=False) if abs_return else format_nok_change(0, show_currency=False)
                
                # Apply BSU formatting after sparkline generation
                if instrument_name == "BSU":
                    change_formatted = f"{bsu_interest_rate}% APY"
                
                final_card_html = card_template.format(
                    instrument_name=instrument_name,
                    change_color=change_color,
                    change_symbol=change_symbol,
                    change_percent=pct_return,
                    sparkline_svg=sparkline_svg,
                    latest_val_formatted=latest_val_formatted,
                    change_formatted=change_formatted
                )

                # Place cards in the appropriate column
                if i == 0:
                    with col1:
                        components.html(final_card_html, height=320)
                        # Add native Streamlit buttons below the card
                        st.markdown(f"""
                        <div style="display: flex; justify-content: center; gap: 1px; margin-top: 0px; margin-bottom: 0px;">
                        """, unsafe_allow_html=True)
                        cols = st.columns(7)
                        periods = ["7d", "1m", "3m", "6m", "1y", "3y", "5y"]
                        for j, period in enumerate(periods):
                            with cols[j]:
                                is_selected = st.session_state.timeframes.get(instrument_name, "1y") == period
                                print(f"Button {period} for {instrument_name}: selected={is_selected}")
                                if st.button(period.upper(), key=f"{instrument_name}_{period}_0", 
                                           help=f"Show {period} data",
                                           type="primary" if is_selected else "secondary"):
                                    print(f"Button {period} clicked for {instrument_name}")
                                    st.session_state.timeframes[instrument_name] = period
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                elif i == 1:
                    with col2:
                        components.html(final_card_html, height=320)
                        # Add native Streamlit buttons below the card
                        st.markdown(f"""
                        <div style="display: flex; justify-content: center; gap: 1px; margin-top: 0px; margin-bottom: 0px;">
                        """, unsafe_allow_html=True)
                        cols = st.columns(7)
                        periods = ["7d", "1m", "3m", "6m", "1y", "3y", "5y"]
                        for j, period in enumerate(periods):
                            with cols[j]:
                                is_selected = st.session_state.timeframes.get(instrument_name, "1y") == period
                                if st.button(period.upper(), key=f"{instrument_name}_{period}_1", 
                                           help=f"Show {period} data",
                                           type="primary" if is_selected else "secondary"):
                                    st.session_state.timeframes[instrument_name] = period
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                elif i == 2:
                    with col3:
                        components.html(final_card_html, height=320)
                        # Add native Streamlit buttons below the card
                        st.markdown(f"""
                        <div style="display: flex; justify-content: center; gap: 1px; margin-top: 0px; margin-bottom: 0px;">
                        """, unsafe_allow_html=True)
                        cols = st.columns(7)
                        periods = ["7d", "1m", "3m", "6m", "1y", "3y", "5y"]
                        for j, period in enumerate(periods):
                            with cols[j]:
                                is_selected = st.session_state.timeframes.get(instrument_name, "1y") == period
                                if st.button(period.upper(), key=f"{instrument_name}_{period}_2", 
                                           help=f"Show {period} data",
                                           type="primary" if is_selected else "secondary"):
                                    st.session_state.timeframes[instrument_name] = period
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                elif i == 3:
                    with col4:
                        components.html(final_card_html, height=320)
                        # Add native Streamlit buttons below the card
                        st.markdown(f"""
                        <div style="display: flex; justify-content: center; gap: 1px; margin-top: 0px; margin-bottom: 0px;">
                        """, unsafe_allow_html=True)
                        cols = st.columns(7)
                        periods = ["7d", "1m", "3m", "6m", "1y", "3y", "5y"]
                        for j, period in enumerate(periods):
                            with cols[j]:
                                is_selected = st.session_state.timeframes.get(instrument_name, "1y") == period
                                if st.button(period.upper(), key=f"{instrument_name}_{period}_3", 
                                           help=f"Show {period} data",
                                           type="primary" if is_selected else "secondary"):
                                    st.session_state.timeframes[instrument_name] = period
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                

