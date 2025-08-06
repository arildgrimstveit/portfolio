import streamlit as st
import data_manager
import ui_components

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


# --- Data Loading ---
df = data_manager.load_portfolio_data()

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
        allocation_chart = ui_components.create_allocation_bar_chart(latest_snapshot)
        st.plotly_chart(allocation_chart, use_container_width=True, config={'displayModeBar': False})

    # Add space between allocation and instruments
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

    # --- Instrument Breakdown Section ---
    st.subheader("💼 Instruments")
    with st.container():
        ui_components.render_instrument_cards(df, latest_snapshot)

else:
    st.warning("Could not load portfolio data. Please check the data file.")
