#!/usr/bin/env python3
"""
Quick portfolio updater - regenerates portfolio data with current prices
"""

import subprocess
import sys

def main():
    """Update portfolio data and restart Streamlit if needed"""
    try:
        print("🔄 Updating portfolio data...")
        result = subprocess.run([sys.executable, "build_real_portfolio.py"], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        
        print("✅ Portfolio data updated successfully!")
        print("💡 Refresh your browser to see the latest data")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error updating portfolio: {e}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()