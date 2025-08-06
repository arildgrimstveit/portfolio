#!/usr/bin/env python3
"""
Simple Portfolio Data Generator

This creates sample portfolio data based on your transaction list.
Since we're having issues with the complex API fetching, this creates
realistic sample data that will power your dashboard.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Your actual transactions
TRANSACTIONS = [
    # 📈 Kron Indeks Global
    ("2023-12-01", "Kron Indeks Global", 41200, "Large initial investment"),
    ("2024-01-15", "Kron Indeks Global", 6200, "January addition"),
    ("2024-02-15", "Kron Indeks Global", 6200, "February addition"),
    ("2024-03-15", "Kron Indeks Global", 6200, "March addition"),
    ("2024-04-15", "Kron Indeks Global", 2050, "April small addition"),
    ("2024-05-15", "Kron Indeks Global", 2050, "May small addition"),
    ("2024-06-15", "Kron Indeks Global", 2050, "June small addition"),
    ("2024-07-15", "Kron Indeks Global", 2050, "July small addition"),
    ("2024-08-01", "Kron Indeks Global", 2022, "August small addition"),

    # 📊 Stocks from Nordnet (using 2024 dates since 2025 market data doesn't exist yet)
    ("2024-05-21", "Apple", 2119.66, "1 share @ 203.76 USD"),
    ("2024-05-21", "Alphabet C", 1727.59, "1 share @ 165.22 USD"),
    ("2024-07-02", "Advanced Micro Devices", 9651.77, "7 shares @ 135.70 USD"),
    ("2024-07-02", "Advanced Micro Devices", 2849.04, "2 shares @ 138.76 USD"),
    ("2024-07-08", "Robinhood Markets A", 1902.48, "2 shares @ 91.27 USD"),
    ("2024-07-08", "Alphabet C", 5371.96, "3 shares @ 175.00 USD"),
    ("2024-07-15", "Robinhood Markets A", 2063.54, "2 shares @ 99.00 USD"),
    ("2024-07-22", "Advanced Micro Devices", 3168.98, "2 shares @ 154.37 USD"),
    ("2024-07-24", "Kongsberg Gruppen", 1586.50, "5 shares @ 311.50 NOK"),
    ("2024-08-01", "Advanced Micro Devices", 1820.13, "1 share @ 171.96 USD"),

    # 🪙 Bitcoin
    ("2018-12-15", "BTC", 2000, "Approx 0.0356 BTC, received 2025-01-19"),
    ("2024-06-09", "BTC", 500, "Bought 0.00043159 BTC @ 1.1M NOK/BTC"),
    ("2024-06-14", "BTC", 5000, "Bought 0.00532214 BTC @ 896,555.78 NOK/BTC incl. fee"),

    # ☀️ Solana
    ("2024-07-02", "SOLANA", 5000, "Bought 3.0342 SOL @ 1,572.60 NOK/SOL incl. fee"),

    # 🎮 Karambit Black Laminate + inventory
    ("2024-07-06", "CS2 SKINS", 15000, "Estimated inventory value incl. Karambit Black Laminate"),
]

# Realistic portfolio progression for a smooth development chart
PORTFOLIO_VALUES = {
    "2023-12-01": {
        "Kron Indeks Global": 41.2,  # Initial investment
        "Apple": 0,
        "Alphabet C": 0,
        "Advanced Micro Devices": 0,
        "Robinhood Markets A": 0,
        "Kongsberg Gruppen": 0,
        "BTC": 2.0,                  # Old Bitcoin position
        "SOLANA": 0,
        "CS2 SKINS": 0,
    },
    "2024-01-01": {
        "Kron Indeks Global": 43.5,  # Growth + January addition
        "Apple": 0,
        "Alphabet C": 0,
        "Advanced Micro Devices": 0,
        "Robinhood Markets A": 0,
        "Kongsberg Gruppen": 0,
        "BTC": 15.0,                 # Bitcoin bull run starts
        "SOLANA": 0,
        "CS2 SKINS": 0,
    },
    "2024-04-01": {
        "Kron Indeks Global": 58.0,  # Continued growth + additions
        "Apple": 0,
        "Alphabet C": 0,
        "Advanced Micro Devices": 0,
        "Robinhood Markets A": 0,
        "Kongsberg Gruppen": 0,
        "BTC": 35.0,                 # Bitcoin strong performance
        "SOLANA": 0,
        "CS2 SKINS": 0,
    },
    "2024-06-01": {
        "Kron Indeks Global": 65.0,  # Steady growth
        "Apple": 0,
        "Alphabet C": 0,
        "Advanced Micro Devices": 0,
        "Robinhood Markets A": 0,
        "Kongsberg Gruppen": 0,
        "BTC": 42.0,                 # More Bitcoin purchases
        "SOLANA": 0,
        "CS2 SKINS": 0,
    },
    "2024-07-01": {
        "Kron Indeks Global": 68.0,  # Continued growth
        "Apple": 2.1,                # New stock purchases begin
        "Alphabet C": 1.7,
        "Advanced Micro Devices": 12.5,
        "Robinhood Markets A": 0,
        "Kongsberg Gruppen": 0,
        "BTC": 45.0,
        "SOLANA": 5.0,               # Solana purchase
        "CS2 SKINS": 15.0,           # CS2 inventory
    },
    "2024-08-06": {
        "Kron Indeks Global": 84.8,  # Final value matching your screenshot
        "Apple": 2.3,                # Small growth
        "Alphabet C": 7.2,           # Combined positions with growth
        "Advanced Micro Devices": 25.0,  # Strong AMD performance
        "Robinhood Markets A": 4.2,  # Added positions
        "Kongsberg Gruppen": 16.0,   # Norwegian stock boom
        "BTC": 52.0,                 # Bitcoin continued strength
        "SOLANA": 5.2,               # Solana holding value
        "CS2 SKINS": 15.5,           # CS2 skins slight appreciation
    }
}

def interpolate_values(start_date, end_date, start_values, end_values, current_date):
    """Smooth interpolation between two value sets"""
    total_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    if total_days == 0:
        return start_values.copy()
    
    progress = (pd.to_datetime(current_date) - pd.to_datetime(start_date)).days / total_days
    progress = max(0, min(1, progress))  # Clamp between 0 and 1
    
    interpolated = {}
    for instrument in start_values:
        start_val = start_values[instrument]
        end_val = end_values.get(instrument, start_val)
        interpolated[instrument] = start_val + (end_val - start_val) * progress
    
    # Add any new instruments that appear in end_values
    for instrument in end_values:
        if instrument not in interpolated:
            interpolated[instrument] = end_values[instrument] * progress
    
    return interpolated

def generate_sample_data():
    """Generate sample portfolio data with smooth progression over 8+ months"""
    print("🚀 Generating comprehensive portfolio data...")
    
    # Create longer date range for better chart
    start_date = "2023-12-01"
    end_date = "2024-08-06"
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Key milestone dates in chronological order
    milestone_dates = [
        "2023-12-01", "2024-01-01", "2024-04-01", 
        "2024-06-01", "2024-07-01", "2024-08-06"
    ]
    
    all_data = []
    
    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        
        # Find which milestone period we're in
        if date_str <= "2024-01-01":
            start_milestone = "2023-12-01"
            end_milestone = "2024-01-01"
        elif date_str <= "2024-04-01":
            start_milestone = "2024-01-01"
            end_milestone = "2024-04-01"
        elif date_str <= "2024-06-01":
            start_milestone = "2024-04-01"
            end_milestone = "2024-06-01"
        elif date_str <= "2024-07-01":
            start_milestone = "2024-06-01"
            end_milestone = "2024-07-01"
        else:
            start_milestone = "2024-07-01"
            end_milestone = "2024-08-06"
        
        # Interpolate values for this date
        start_values = PORTFOLIO_VALUES[start_milestone]
        end_values = PORTFOLIO_VALUES[end_milestone]
        day_values = interpolate_values(start_milestone, end_milestone, start_values, end_values, date_str)
        
        # Add realistic market volatility
        np.random.seed(hash(date_str) % 2147483647)  # Consistent daily "randomness"
        
        for instrument, value in day_values.items():
            if value > 0:  # Only add variation to non-zero holdings
                # Different volatility for different asset types
                if instrument == "BTC":
                    daily_vol = 0.05  # Bitcoin: 5% daily volatility
                elif instrument == "SOLANA":
                    daily_vol = 0.06  # Solana: 6% daily volatility  
                elif "Advanced Micro Devices" in instrument:
                    daily_vol = 0.04  # AMD: 4% volatility
                elif instrument == "CS2 SKINS":
                    daily_vol = 0.01  # CS2 skins: 1% volatility
                elif "Kron Indeks Global" in instrument:
                    daily_vol = 0.015  # Fund: 1.5% volatility
                else:
                    daily_vol = 0.03  # Other stocks: 3% volatility
                
                variation = np.random.normal(0, daily_vol)
                adjusted_value = value * (1 + variation)
                
                # Ensure no negative values
                adjusted_value = max(0.1, adjusted_value)
                
                all_data.append({
                    'Date': date_str,
                    'Instrument': instrument,
                    'Value_kNOK': round(adjusted_value, 1)
                })
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    output_file = "data/portfolio.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✅ Comprehensive portfolio data saved to {output_file}")
    print(f"📊 Total records: {len(df)}")
    print(f"🎯 Instruments: {df['Instrument'].nunique()}")
    print(f"📈 Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"⏱️  Time span: {(pd.to_datetime(df['Date'].max()) - pd.to_datetime(df['Date'].min())).days} days")
    
    # Show summary
    print("\n📋 Portfolio Summary (latest date):")
    latest_date = df['Date'].max()
    latest_data = df[df['Date'] == latest_date]
    latest_data = latest_data.sort_values('Value_kNOK', ascending=False)
    
    total_value = latest_data['Value_kNOK'].sum()
    print(f"💰 Total Portfolio Value: {total_value:.1f} kNOK ({total_value*1000:,.0f} NOK)")
    print("\n🏆 Top positions:")
    for _, row in latest_data.iterrows():
        pct = (row['Value_kNOK'] / total_value) * 100
        print(f"  • {row['Instrument']}: {row['Value_kNOK']:.1f} kNOK ({pct:.1f}%)")
    
    # Show growth progression
    start_date_data = df[df['Date'] == df['Date'].min()]
    start_total = start_date_data['Value_kNOK'].sum()
    growth = ((total_value - start_total) / start_total) * 100
    print(f"\n📈 Total Growth: {growth:.1f}% over {(pd.to_datetime(latest_date) - pd.to_datetime(df['Date'].min())).days} days")
    
    return df

if __name__ == "__main__":
    print("🏦 Sample Portfolio Data Generator")
    print("=" * 50)
    
    try:
        df = generate_sample_data()
        print("\n🎉 Success! Your portfolio now has realistic sample data.")
        print("\n💡 Next steps:")
        print("1. Run the app: streamlit run app.py")
        print("2. Later, we can replace this with real API data")
        
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        import traceback
        traceback.print_exc()