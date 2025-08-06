#!/usr/bin/env python3
"""
Clear Streamlit cache to force fresh data loading
"""

import streamlit as st
import os
import time

def clear_streamlit_cache():
    """Clear Streamlit cache"""
    try:
        # Clear all Streamlit caches
        st.cache_data.clear()
        print("✅ Streamlit cache cleared")
        
        # Also check file modification time
        csv_path = "data/portfolio.csv"
        if os.path.exists(csv_path):
            mod_time = os.path.getmtime(csv_path)
            print(f"📁 CSV file last modified: {time.ctime(mod_time)}")
        
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

if __name__ == "__main__":
    clear_streamlit_cache()
    print("💡 Now refresh your browser to see updated data")