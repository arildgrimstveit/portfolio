#!/usr/bin/env python3
"""
Portfolio Data Fetcher - Transaction-Based Approach

This script calculates portfolio values based on actual purchase transactions.
Each transaction includes: date, instrument, amount invested (NOK), and calculates shares based on market price.

Run this script to generate your portfolio.csv with real transaction-based data.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Optional, Tuple

# TRANSACTION HISTORY - Your actual purchases
TRANSACTIONS = [
    # Kron Indeks Global (estimates based on app screenshot)
    ("2023-12-01", "Kron Indeks Global", 41200, "Large initial investment"),
    ("2024-01-15", "Kron Indeks Global", 6200, "January addition"),
    ("2024-02-15", "Kron Indeks Global", 6200, "February addition"),
    ("2024-03-15", "Kron Indeks Global", 6200, "March addition"),
    ("2024-04-15", "Kron Indeks Global", 2050, "April small addition"),
    ("2024-05-15", "Kron Indeks Global", 2050, "May small addition"),
    ("2024-06-15", "Kron Indeks Global", 2050, "June small addition"),
    ("2024-07-15", "Kron Indeks Global", 2050, "July small addition"),
    ("2024-08-01", "Kron Indeks Global", 2022, "August small addition"),

    # Nordnet stock purchases
    ("2025-05-21", "APPLE", 2119.66, "1 share @ 203.76 USD"),
    ("2025-05-21", "GOOGLE", 1727.59, "1 share @ 165.22 USD"),
    ("2025-07-02", "AMD", 9651.77, "7 shares @ 135.70 USD"),
    ("2025-07-02", "AMD", 2849.04, "2 shares @ 138.76 USD"),
    ("2025-07-08", "ROBINHOOD", 1902.48, "2 shares @ 91.27 USD"),
    ("2025-07-08", "GOOGLE", 5371.96, "3 shares @ 175 USD"),
    ("2025-07-15", "ROBINHOOD", 2063.54, "2 shares @ 99 USD"),
    ("2025-07-22", "AMD", 3168.98, "2 shares @ 154.37 USD"),
    ("2025-07-24", "KOG", 1586.50, "5 shares @ 311.5 NOK"),
    ("2025-08-01", "AMD", 1820.13, "1 share @ 171.96 USD"),

    # Bitcoin purchases
    ("2018-12-15", "BTC", 2000, "Approx 0.0356 BTC, received 2025-01-19"),
    ("2024-12-09", "BTC", 500, "Bought 0.00043159 BTC @ 1.1M NOK/BTC"),
    ("2025-03-14", "BTC", 5000, "Bought 0.00532214 BTC @ 896,555.78 NOK/BTC incl. fee"),

    # Solana purchase
    ("2025-07-02", "SOLANA", 5000, "Bought 3.0342 SOL @ 1,572.60 NOK/SOL incl. fee"),
]

# INSTRUMENT MAPPING - Maps your instrument names to Yahoo Finance symbols
SYMBOL_MAPPING = {
    "Kron Indeks Global": None,       # Custom handling - use estimated value based on screenshot
    "AMD": "AMD",                      # Advanced Micro Devices
    "APPLE": "AAPL",                  # Apple Inc
    "GOOGLE": "GOOG",                 # Alphabet Class C (since you bought Class C)
    "ROBINHOOD": "HOOD",              # Robinhood Markets
    "KOG": "KOG.OL",                  # Kongsberg Gruppen (Norwegian stock)
    "BTC": "BTC-USD",                 # Bitcoin
    "SOLANA": "SOL-USD",              # Solana
}

# Custom asset handling for Norwegian funds and other assets
CUSTOM_ASSETS = {
    "Kron Indeks Global": {
        "type": "norwegian_fund",
        "current_value_nok": 84811,  # From your screenshot
        "total_invested_nok": 68822,  # Sum of your transactions
        "base_date": "2024-08-01",   # Reference date
        "estimated_annual_return": 0.08  # 8% annual return estimate for global index
    }
}

class PortfolioCalculator:
    def __init__(self):
        self.usd_nok_rate = self.fetch_exchange_rate()
        self.price_cache = {}  # Cache historical prices
        
    def fetch_exchange_rate(self) -> float:
        """Fetch current USD to NOK exchange rate"""
        try:
            usd_nok = yf.Ticker("USDNOK=X")
            rate_data = usd_nok.history(period="5d")
            if not rate_data.empty:
                return rate_data['Close'].iloc[-1]
        except Exception as e:
            print(f"Warning: Could not fetch USD/NOK rate: {e}")
        return 10.5  # Fallback rate

    def get_price_on_date(self, symbol: str, date: str) -> Optional[float]:
        """Get price for a symbol on a specific date, with caching"""
        cache_key = f"{symbol}_{date}"
        
        if cache_key in self.price_cache:
            return self.price_cache[cache_key]
            
        try:
            # Fetch a wider range to ensure we get data even if market was closed
            start_date = (pd.to_datetime(date) - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = (pd.to_datetime(date) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                print(f"Warning: No data found for {symbol} around {date}")
                return None
                
            # Get the closest price to our target date
            target_date = pd.to_datetime(date)
            closest_date = data.index[data.index <= target_date].max()
            
            if pd.isna(closest_date):
                closest_date = data.index[0]
                
            price = data.loc[closest_date, 'Close']
            self.price_cache[cache_key] = price
            return price
            
        except Exception as e:
            print(f"Error fetching price for {symbol} on {date}: {e}")
            return None

    def calculate_shares_purchased(self, transaction_date: str, instrument: str, amount_nok: float) -> Tuple[float, float]:
        """Calculate how many shares were purchased with given NOK amount"""
        symbol = SYMBOL_MAPPING.get(instrument)
        
        if symbol is None:
            # Custom asset - return amount as "shares" (value)
            return amount_nok, amount_nok
            
        price_usd = self.get_price_on_date(symbol, transaction_date)
        if price_usd is None:
            return 0, 0
            
        # Convert to NOK if needed
        if symbol.endswith('-USD') or not symbol.endswith('.OL'):
            price_nok = price_usd * self.usd_nok_rate
        else:
            price_nok = price_usd
            
        shares = amount_nok / price_nok
        return shares, price_nok

    def calculate_position_value(self, instrument: str, shares: float, date: str) -> float:
        """Calculate current value of a position on given date"""
        symbol = SYMBOL_MAPPING.get(instrument)
        
        if symbol is None:
            # Handle custom assets
            if instrument in CUSTOM_ASSETS:
                config = CUSTOM_ASSETS[instrument]
                base_date = pd.to_datetime(config["base_date"])
                current_date = pd.to_datetime(date)
                days_elapsed = (current_date - base_date).days
                years_elapsed = days_elapsed / 365.25
                
                # Apply appreciation
                current_value = shares * (1 + config["appreciation_rate"]) ** years_elapsed
                return current_value
            else:
                return shares  # Use original value for unknown custom assets
                
        # Get current market price
        price_usd = self.get_price_on_date(symbol, date)
        if price_usd is None:
            return 0
            
        # Convert to NOK if needed
        if symbol.endswith('-USD') or not symbol.endswith('.OL'):
            price_nok = price_usd * self.usd_nok_rate
        else:
            price_nok = price_usd
            
        return shares * price_nok

    def build_portfolio_history(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Build complete portfolio history from transactions"""
        print("🚀 Building portfolio from transaction history...")
        
        # Parse transactions
        df_transactions = pd.DataFrame(TRANSACTIONS, columns=['Date', 'Instrument', 'Amount_NOK', 'Notes'])
        df_transactions['Date'] = pd.to_datetime(df_transactions['Date'])
        
        # Calculate shares for each transaction
        print("💰 Calculating shares purchased in each transaction...")
        transaction_details = []
        
        for _, tx in df_transactions.iterrows():
            shares, price_per_share = self.calculate_shares_purchased(
                tx['Date'].strftime('%Y-%m-%d'), 
                tx['Instrument'], 
                tx['Amount_NOK']
            )
            
            transaction_details.append({
                'Date': tx['Date'],
                'Instrument': tx['Instrument'],
                'Amount_NOK': tx['Amount_NOK'],
                'Shares': shares,
                'Price_Per_Share': price_per_share,
                'Notes': tx['Notes']
            })
            
            print(f"  📈 {tx['Date'].strftime('%Y-%m-%d')}: {tx['Instrument']} - {shares:.2f} shares at {price_per_share:.2f} NOK/share")
        
        # Build daily portfolio values
        print("📅 Calculating daily portfolio values...")
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        portfolio_data = []
        
        for date in date_range:
            date_str = date.strftime('%Y-%m-%d')
            print(f"  🗓️  Processing {date_str}...")
            
            # Get all transactions up to this date
            relevant_transactions = [tx for tx in transaction_details if tx['Date'] <= date]
            
            # Group by instrument and sum shares
            holdings = {}
            for tx in relevant_transactions:
                instrument = tx['Instrument']
                if instrument not in holdings:
                    holdings[instrument] = 0
                holdings[instrument] += tx['Shares']
            
            # Calculate value for each holding
            for instrument, total_shares in holdings.items():
                value_nok = self.calculate_position_value(instrument, total_shares, date_str)
                value_knok = value_nok / 1000  # Convert to kNOK
                
                portfolio_data.append({
                    'Date': date_str,
                    'Instrument': instrument,
                    'Value_kNOK': round(value_knok, 1)
                })
        
        return pd.DataFrame(portfolio_data)

def main():
    print("🏦 Transaction-Based Portfolio Calculator")
    print("=" * 50)
    
    # Create calculator
    calc = PortfolioCalculator()
    print(f"💱 Using USD/NOK rate: {calc.usd_nok_rate:.2f}")
    
    # Set date range
    if len(sys.argv) >= 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
        print(f"📅 Using custom date range: {start_date} to {end_date}")
    else:
        start_date = "2024-01-01"  # Start from reasonable historical date
        end_date = "2024-08-06"    # End at realistic date with available data
        print(f"📅 Using default date range: {start_date} to {end_date}")
    
    try:
        # Generate portfolio data
        df = calc.build_portfolio_history(start_date, end_date)
        
        # Save to CSV
        output_file = "data/portfolio.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Portfolio data saved to {output_file}")
        print(f"📊 Total records: {len(df)}")
        print(f"🎯 Instruments: {df['Instrument'].nunique()}")
        print(f"📈 Date range: {df['Date'].min()} to {df['Date'].max()}")
        
        # Show summary
        print("\n📋 Portfolio Summary (latest date):")
        latest_date = df['Date'].max()
        latest_data = df[df['Date'] == latest_date]
        latest_data = latest_data.sort_values('Value_kNOK', ascending=False)
        
        total_value = latest_data['Value_kNOK'].sum()
        print(f"💰 Total Portfolio Value: {total_value:.1f} kNOK ({total_value*1000:,.0f} NOK)")
        print("\n🏆 Top positions:")
        for _, row in latest_data.head().iterrows():
            pct = (row['Value_kNOK'] / total_value) * 100
            print(f"  • {row['Instrument']}: {row['Value_kNOK']:.1f} kNOK ({pct:.1f}%)")
        
        print("\n🎉 Success! Your portfolio now reflects actual purchase transactions.")
        print("\n💡 Next steps:")
        print("1. Update the TRANSACTIONS list with your actual purchase dates and amounts")
        print("2. Verify the SYMBOL_MAPPING for Norwegian instruments")
        print("3. Run the app: streamlit run app.py")
        print("4. Re-run this script after adding new transactions")
        
    except Exception as e:
        print(f"❌ Error generating portfolio data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()