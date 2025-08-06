import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
import pandas as pd

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
        x=latest_snapshot["Value_kNOK"],
        y=latest_snapshot["Instrument"],
        orientation='h',
        marker=dict(
            color=TRADINGVIEW_COLORS['bybit_orange'],
            line=dict(color=TRADINGVIEW_COLORS['bybit_orange'], width=1)
        ),
        text=[f"{val:,.0f}k" for val in latest_snapshot["Value_kNOK"]],
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
            title="Value (kNOK)",
            showgrid=True,
            gridcolor=TRADINGVIEW_COLORS['grid']
        ),
        yaxis=dict(
            showgrid=False,
            autorange="reversed",
            tickfont=dict(size=16)
        )
    )
    return fig

def _create_sparkline(values, width=220, height=40):
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
    start_val, end_val = values[0], values[-1]
    change_percent = ((end_val - start_val) / start_val) * 100 if start_val != 0 else 0
    line_color = "#00D4AA" if change_percent >= 0 else "#FF6B6B"
    fill_points = ["5," + str(height - 5)] + points + [str(width - 5) + "," + str(height - 5)]
    return f'<svg width="{width}" height="{height}"><polygon points="{" ".join(fill_points)}" fill="{line_color}" fill-opacity="0.2"/><polyline points="{" ".join(points)}" fill="none" stroke="{line_color}" stroke-width="2"/></svg>'

def render_instrument_cards(df, latest_snapshot):
    """
    Renders instrument cards in a robust grid using Streamlit's native columns
    with the 'small' gap setting for tight, professional spacing.
    This is the definitive, correct implementation.
    """
    items_per_row = 5
    num_instruments = len(latest_snapshot)

    card_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background: transparent; }}
            .card {{ 
                background: linear-gradient(135deg, #2A2A2A 0%, #1E1E1E 100%); 
                padding: 16px; 
                border-radius: 12px; 
                border: 1px solid #3A3A3A; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
                height: 120px; 
                display: flex; 
                flex-direction: column; 
                justify-content: space-between; 
                box-sizing: border-box; 
            }}
            .card-header {{ display: flex; justify-content: space-between; align-items: center; }}
            .instrument-name {{ color: #FFFFFF; font-size: 14px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
            .change-percent {{ font-size: 12px; font-weight: 500; flex-shrink: 0; padding-left: 10px;}}
            .sparkline-container {{ text-align: center; flex: 1; display: flex; align-items: center; justify-content: center; }}
            .value {{ color: #FFFFFF; font-size: 16px; font-weight: 700; text-align: center; }}
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
    
    for row_start in range(0, num_instruments, items_per_row):
        cols = st.columns(items_per_row, gap="small")
        row_snapshot = latest_snapshot.iloc[row_start : row_start + items_per_row]
        
        for i, (_, row) in enumerate(row_snapshot.iterrows()):
            instrument_name = row["Instrument"]
            instrument_df = df[df["Instrument"] == instrument_name].sort_values("Date")
            
            latest_val = instrument_df["Value_kNOK"].iloc[-1]
            start_val = instrument_df["Value_kNOK"].iloc[0]
            change_percent = ((latest_val - start_val) / start_val) * 100 if start_val != 0 else 0
            absolute_change = latest_val - start_val
            
            change_color = "#00D4AA" if change_percent >= 0 else "#FF6B6B"
            change_symbol = "+" if change_percent >= 0 else ""
            sparkline_svg = _create_sparkline(instrument_df["Value_kNOK"].tolist())

            # Format values using our formatting functions
            latest_val_formatted = format_nok_value(latest_val, show_currency=False)
            change_formatted = format_nok_change(absolute_change, show_currency=False)
            
            final_card_html = card_template.format(
                instrument_name=instrument_name,
                change_color=change_color,
                change_symbol=change_symbol,
                change_percent=change_percent,
                sparkline_svg=sparkline_svg,
                latest_val_formatted=latest_val_formatted,
                change_formatted=change_formatted
            )

            with cols[i]:
                components.html(final_card_html, height=135)
