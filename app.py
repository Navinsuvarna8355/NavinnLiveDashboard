import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import time
import plotly.graph_objects as go

# --- Utility Functions ---
SYMBOL_MAP = {
    "Nifty": "NIFTY",
    "Bank Nifty": "BANKNIFTY",
    "Sensex": "SENSEX"
}

@st.cache
def fetch_option_chain(symbol_key, dummy_time_key):
    symbol_name = SYMBOL_MAP.get(symbol_key)
    if not symbol_name:
        st.error("Invalid symbol selected.")
        return None

    nse_oc_url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol_name}"
    headers = {
        "User -Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        resp = session.get(nse_oc_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "records_data": data["records"]["data"],
            "underlying_value": data["records"]["underlyingValue"],
            "expiry_dates": data["records"]["expiryDates"],
            "fetch_time": datetime.now()  # datetime object
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {symbol_key}: {e}")
        return None

def main():
    st.title("Option Chain Dashboard")

    # Select symbol
    selected_symbol = st.selectbox("Select Symbol", list(SYMBOL_MAP.keys()))

    # Use time-based dummy key to refresh cache every 60 seconds
    dummy_time_key = int(time.time() // 60)

    data_dict = fetch_option_chain(selected_symbol, dummy_time_key)

    if data_dict:
        st.write(f"Underlying Value: {data_dict['underlying_value']}")
        fetch_time = data_dict['fetch_time']
        st.caption(f"Last updated: {fetch_time.strftime('%H:%M:%S')}")

        # Example: show first 5 records in a dataframe
        df = pd.DataFrame(data_dict['records_data'])
        st.dataframe(df.head())

        # You can add your plotly charts or other UI elements here

if __name__ == "__main__":
    main()
