#!/usr/bin/env python3
"""
Build real portfolio data from transactions with current market prices
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
try:
    from transactions_private import transactions
except ImportError:
    # Fallback to public transactions for demo purposes
    from transactions import transactions
import warnings
warnings.filterwarnings('ignore')

# Ticker mapping
TICKER_MAPPING = {
    'AMD': 'AMD',
    'GOOG': 'GOOG',
    'AAPL': 'AAPL',
    'NVDA': 'NVDA',
    'HOOD': 'HOOD',
    'BTC': 'BTC-USD',
    'SOLANA': 'SOL-USD',
    'KOG': 'KOG.OL',
    'KRON_GLOBAL': None,  # Not available on Yahoo Finance, use book value
}

def get_historical_data(start_date, end_date):
    """Get historical market data for all tradeable symbols"""
    print(f"📈 Fetching historical data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    historical_data = {}
    
    # Get USD/NOK historical data
    try:
        print("📊 Fetching USD/NOK exchange rates...")
        usd_nok_ticker = yf.Ticker("USDNOK=X")
        usd_nok_hist = usd_nok_ticker.history(start=start_date, end=end_date + timedelta(days=1))
        if not usd_nok_hist.empty:
            historical_data['USDNOK'] = usd_nok_hist['Close']
            print(f"✓ USD/NOK: {len(usd_nok_hist)} days of data")
        else:
            # Create synthetic USD/NOK data around 10.24
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            historical_data['USDNOK'] = pd.Series([10.24] * len(dates), index=dates)
            print(f"⚠️  USD/NOK: Using synthetic data")
    except Exception as e:
        print(f"❌ Error fetching USD/NOK: {e}")
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        historical_data['USDNOK'] = pd.Series([10.24] * len(dates), index=dates)
    
    # Get historical data for each tradeable symbol
    for symbol, ticker in TICKER_MAPPING.items():
        if ticker is None:  # Skip non-tradeable assets like KRON_GLOBAL
            print(f"⚠️  {symbol}: Using book value (no market data)")
            continue
            
        try:
            print(f"📊 Fetching {symbol} ({ticker})...")
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date + timedelta(days=1))
            
            if not hist.empty:
                historical_data[symbol] = hist['Close']
                print(f"✓ {symbol}: {len(hist)} days of data")
            else:
                print(f"⚠️  {symbol}: No historical data available")
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
    
    return historical_data

def get_current_prices():
    """Get current market prices for all symbols"""
    print("📈 Fetching current market prices...")
    
    # Get USD/NOK rate
    try:
        usd_nok = yf.Ticker("USDNOK=X")
        usd_nok_rate = usd_nok.info.get('regularMarketPrice', 10.24)
        print(f"✓ USD/NOK: {usd_nok_rate:.4f}")
    except:
        usd_nok_rate = 10.24
        print(f"⚠️  Using fallback USD/NOK: {usd_nok_rate}")
    
    prices = {}
    
    for symbol, ticker in TICKER_MAPPING.items():
        if ticker is None:  # Skip non-tradeable assets
            print(f"⚠️  {symbol}: Using book value (no market price)")
            continue
            
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            if price is None:
                hist = stock.history(period="5d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            
            if price:
                if symbol == 'KOG':
                    # KOG is already in NOK
                    prices[symbol] = price
                else:
                    # Convert USD to NOK
                    prices[symbol] = price * usd_nok_rate
                print(f"✓ {symbol}: {price:.2f} {'NOK' if symbol == 'KOG' else 'USD'} = {prices[symbol]:.2f} NOK")
            else:
                print(f"❌ Could not get price for {symbol}")
                
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
    
    return prices, usd_nok_rate

def calculate_holdings():
    """Calculate current holdings from transactions"""
    print("\n📊 Calculating holdings...")
    
    holdings = {}
    total_invested = {}  # Track total amount invested for funds
    
    for date, symbol, quantity, price, currency in transactions:
        if symbol not in holdings:
            holdings[symbol] = 0
            total_invested[symbol] = 0
            
        if symbol == 'KRON_GLOBAL':
            # For KRON_GLOBAL, track total amount invested (price = amount invested)
            total_invested[symbol] += price
            holdings[symbol] = total_invested[symbol]  # Use total invested as "quantity"
            print(f"  {date}: {symbol} +{price:,.0f} NOK = {holdings[symbol]:,.0f} NOK invested")
        else:
            # Regular assets - track actual quantity
            holdings[symbol] += quantity
            print(f"  {date}: {symbol} +{quantity} = {holdings[symbol]:.6f}")
    
    return holdings

def build_portfolio_data():
    """Build portfolio data for the dashboard"""
    
    # Calculate holdings first to determine what data we need
    holdings = calculate_holdings()
    
    # Determine comprehensive date range
    transaction_dates = [pd.to_datetime(t[0]) for t in transactions]
    earliest_transaction = min(transaction_dates)
    start_date = earliest_transaction - timedelta(days=30)
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get historical market data
    historical_data = get_historical_data(start_date, end_date)
    
    # Get current market prices for final valuation
    market_prices, usd_nok_rate = get_current_prices()
    
    # Create portfolio data
    portfolio_data = []
    
    print(f"\n💰 Portfolio Valuation:")
    total_value = 0
    
    for symbol, quantity in holdings.items():
        if quantity <= 0:
            continue
            
        print(f"\n--- {symbol} ---")
        print(f"Holdings: {quantity:.6f}")
        
        if symbol == 'KRON_GLOBAL':
            # KRON_GLOBAL: quantity = total invested amount, need to calculate current value
            total_invested_nok = quantity  # quantity is actually total invested amount
            if symbol in market_prices:
                # Get current fund price and estimate shares
                current_price_nok = market_prices[symbol]
                # Estimate fund performance (this is simplified - real calculation would need historical prices)
                # For now, assume we can get current value by checking fund performance
                # Using current price as approximation of performance
                print(f"Total invested: {total_invested_nok:,.0f} NOK")
                print(f"Current fund price: {current_price_nok:,.2f} NOK")
                # Simplified: assume we can estimate current value based on fund price trend
                # In reality, you'd need to track actual fund shares purchased at different times
                current_value = total_invested_nok * 1.1  # Assume 10% growth for now - should be calculated properly
                print(f"Estimated current value: {current_value:,.0f} NOK")
            else:
                # Fallback to book value if no price data
                current_value = total_invested_nok
                print(f"Using book value: {current_value:,.0f} NOK")
        elif symbol in ['BSU', 'CS_KNIFE']:
            # Fixed value assets
            if symbol == 'BSU':
                value_per_unit = 27500  # Latest BSU value
                current_value = quantity * value_per_unit
            else:  # CS_KNIFE
                current_value = 15000
        elif symbol in market_prices:
            price_nok = market_prices[symbol]
            current_value = quantity * price_nok
            print(f"Price: {price_nok:,.2f} NOK")
        else:
            print(f"⚠️  No price data for {symbol}, skipping")
            continue
        
        print(f"Value: {current_value:,.0f} NOK")
        total_value += current_value
        
        # Store current data for this instrument
        instrument_data = {
            'symbol': symbol,
            'quantity': quantity,
            'current_value': current_value
        }
        
        # Add to list for later processing
        if 'instrument_list' not in locals():
            instrument_list = []
        instrument_list.append(instrument_data)
    
    print(f"\n🎯 Total Portfolio Value: {total_value:,.0f} NOK")
    
    # Create comprehensive time series with real historical data
    portfolio_data = []
    
    # Determine date range: from earliest transaction to today, plus some history
    transaction_dates = [pd.to_datetime(t[0]) for t in transactions]
    earliest_transaction = min(transaction_dates)
    start_date = earliest_transaction - timedelta(days=30)  # Add 30 days before first transaction
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create daily date range for comprehensive historical data
    date_range = pd.date_range(start=start_date, end=end_date, freq='D').tolist()
    
    # Create comprehensive time series with real historical data
    print(f"📊 Generating time series from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    # First, get all instruments that have any holdings
    all_instruments = set()
    for trans_date, symbol, quantity, price, currency in transactions:
        all_instruments.add(symbol)
    
    print(f"📊 Instruments to track: {sorted(all_instruments)}")
    
    # Debug: Show which instruments have historical data
    print(f"📊 Instruments with historical data: {list(historical_data.keys())}")
    
    # Debug: Count records per instrument
    instrument_counts = {}
    
    # First, calculate when each instrument first has holdings
    instrument_start_dates = {}
    for symbol in all_instruments:
        first_holding_date = None
        for trans_date, trans_symbol, quantity, price, currency in transactions:
            if trans_symbol == symbol:
                trans_date_obj = pd.to_datetime(trans_date)
                if first_holding_date is None or trans_date_obj < first_holding_date:
                    first_holding_date = trans_date_obj
        
        if first_holding_date:
            instrument_start_dates[symbol] = first_holding_date
            print(f"📅 {symbol}: First holding on {first_holding_date.strftime('%Y-%m-%d')}")
    
    for date in pd.date_range(start=start_date, end=end_date, freq='D'):
        # Calculate holdings as of this date (based on transactions up to this date)
        date_holdings = {}
        date_total_invested = {}
        
        for trans_date, symbol, quantity, price, currency in transactions:
            trans_date_obj = pd.to_datetime(trans_date)
            if trans_date_obj <= date:
                if symbol not in date_holdings:
                    date_holdings[symbol] = 0
                    date_total_invested[symbol] = 0
                    
                if symbol == 'KRON_GLOBAL':
                    date_total_invested[symbol] += price
                    date_holdings[symbol] = date_total_invested[symbol]
                else:
                    date_holdings[symbol] += quantity
        
        # Generate data for all instruments that have holdings on this date
        for symbol in all_instruments:
            quantity = date_holdings.get(symbol, 0)
            
            # Only generate data if we have holdings
            if quantity <= 0:
                continue
            
        # Calculate values for each holding on this date
        for symbol, quantity in date_holdings.items():
            if quantity <= 0:
                continue
                
            # Get historical price for this date
            if symbol in ['BSU', 'CS_KNIFE']:
                # Fixed value assets
                if symbol == 'BSU':
                    value_nok = quantity * 27500  # Use consistent BSU value
                else:  # CS_KNIFE
                    # CS_KNIFE only exists after its transaction date
                    cs_knife_date = pd.to_datetime('2025-07-06')
                    if date >= cs_knife_date:
                        value_nok = 15000
                    else:
                        continue
            elif symbol == 'KRON_GLOBAL':
                # Use book value for KRON_GLOBAL (total invested)
                value_nok = quantity  # quantity is already the total invested amount
            elif symbol in historical_data:
                # Get historical market price
                # Debug: Track which instruments are being processed
                if symbol not in instrument_counts:
                    instrument_counts[symbol] = 0
                

                
                try:
                    symbol_prices = historical_data[symbol]
                    # Find closest available date
                    # Convert date to UTC timezone to match Yahoo Finance data
                    date_utc = date.tz_localize('UTC')
                    available_dates = symbol_prices.index[symbol_prices.index <= date_utc]
                    
                    if len(available_dates) > 0:
                        closest_date = available_dates[-1]
                        price_usd = symbol_prices[closest_date]
                        
                        # Get USD/NOK rate for this date
                        if 'USDNOK' in historical_data:
                            usd_nok_series = historical_data['USDNOK']
                            usd_nok_dates = usd_nok_series.index[usd_nok_series.index <= date_utc]
                            if len(usd_nok_dates) > 0:
                                usd_nok_date = usd_nok_dates[-1]
                                usd_nok_rate = usd_nok_series[usd_nok_date]
                            else:
                                usd_nok_rate = 10.24
                        else:
                            usd_nok_rate = 10.24
                        
                        if symbol == 'KOG':
                            # KOG is already in NOK
                            value_nok = quantity * price_usd
                        else:
                            # Convert USD to NOK
                            value_nok = quantity * price_usd * usd_nok_rate
                        

                    else:
                        # No data available for this date - skip this date for this symbol
                        continue
                except Exception as e:
                    # Skip on error
                    continue
            else:
                # No historical data for this symbol - these are handled above (BSU, CS_KNIFE, KRON_GLOBAL)
                # This should not happen since we handle all cases above
                continue
            
            portfolio_data.append({
                'Date': date,
                'Instrument': symbol,
                'Quantity': quantity,
                'Value_kNOK': value_nok / 1000
            })
            
            # Debug: Count records per instrument
            if symbol not in instrument_counts:
                instrument_counts[symbol] = 0
            instrument_counts[symbol] += 1
    
    # Create DataFrame
    df = pd.DataFrame(portfolio_data)
    
    # Debug: Show record counts
    print(f"📊 Records generated per instrument: {instrument_counts}")
    
    if not df.empty:
        # Add total portfolio values
        totals = []
        for date in df['Date'].unique():
            date_data = df[df['Date'] == date]
            total_value_kNOK = date_data['Value_kNOK'].sum()
            
            totals.append({
                'Date': date,
                'Instrument': 'TOTAL',
                'Quantity': 1,
                'Value_kNOK': total_value_kNOK
            })
        
        # Combine data
        df_totals = pd.DataFrame(totals)
        df_final = pd.concat([df, df_totals], ignore_index=True)
        df_final = df_final.sort_values(['Date', 'Instrument'])
        
        return df_final
    
    return pd.DataFrame()

def main():
    """Main function"""
    print("🚀 Building real portfolio data from transactions...")
    
    df = build_portfolio_data()
    
    if not df.empty:
        # Save to CSV
        df.to_csv('data/portfolio.csv', index=False)
        print(f"\n💾 Portfolio data saved to data/portfolio.csv")
        
        # Show summary
        print(f"\n📊 Dashboard Data Summary:")
        print(f"Records: {len(df)}")
        print(f"Date range: {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
        
        latest_date = df['Date'].max()
        latest_data = df[df['Date'] == latest_date]
        
        print(f"\n🎯 Latest Portfolio (as of {latest_date.strftime('%Y-%m-%d')}):")
        for _, row in latest_data.iterrows():
            if row['Instrument'] != 'TOTAL':
                print(f"  {row['Instrument']}: {row['Value_kNOK']*1000:,.0f} NOK")
        
        total_row = latest_data[latest_data['Instrument'] == 'TOTAL']
        if not total_row.empty:
            total_value = total_row['Value_kNOK'].iloc[0] * 1000
            print(f"  📊 TOTAL: {total_value:,.0f} NOK")
            
        print(f"\n✅ Portfolio dashboard is ready!")
        
    else:
        print("❌ Failed to build portfolio data")

if __name__ == "__main__":
    main()