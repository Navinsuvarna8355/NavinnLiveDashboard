import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# =========================
# 1️⃣ CONFIG & SYMBOLS
# =========================
st.set_page_config(page_title="Market Dashboard", layout="wide")

# Map for consistent API calls
symbol_map = {
    "NIFTY": {"oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    "BANKNIFTY": {"oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    "SENSEX": {"oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}
}

# =========================
# 2️⃣ DATA FETCHING
# =========================
def get_spot_price(symbol_name: str):
    """
    Fetch latest spot/close price from NSE/BSE.
    Replace with your preferred API.
    """
    try:
        # Example NSE API endpoint (replace if using paid API)
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol_name}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        return data['priceInfo']['lastPrice']
    except Exception as e:
        st.error(f"Price fetch error for {symbol_name}: {e}")
        return None

def get_ema_trend(symbol_name: str):
    """
    Calculate EMA trend using spot price history.
    Replace with your actual EMA logic.
    """
    # Example placeholder
    return "Bullish"

def get_pcr_atm_sr(symbol: str):
    """
    Fetch PCR, ATM Strike, Support, Resistance from option chain.
    Replace with your actual logic.
    """
    # Example placeholder
    return 1.2, 19850, 19850, 19700, 20000

def interpret_pcr(pcr_value: float):
    """
    Interpret PCR value into a trend signal.
    """
    if pcr_value > 1.3:
        return "Bullish"
    elif pcr_value < 0.7:
        return "Bearish"
    else:
        return "Sideways"

# =========================
# 3️⃣ UI LAYOUT
# =========================
st.title("📊 Market Strategy Dashboard")

for key, sym in symbol_map.items():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(key)

    with col2:
        # Unified spot price
        spot_price = get_spot_price(sym['nse_symbol'])

        # EMA trend
        ema_trend = get_ema_trend(sym['nse_symbol'])

        # PCR + ATM + SR
        pcr_value, atm_strike, support, resistance = None, None, None, None
        if sym['oc_symbol']:
            pcr_value, spot_from_pcr, atm_strike, support, resistance = get_pcr_atm_sr(sym['oc_symbol'])
        else:
            # For SENSEX, PCR may not be available
            pcr_value, spot_from_pcr, atm_strike, support, resistance = None, None, None, None, None

        pcr_trend = interpret_pcr(pcr_value) if pcr_value is not None else "N/A"

        # Display metrics
        st.markdown(f"**Spot Price:** {spot_price}")
        st.markdown(f"**EMA Trend:** {ema_trend}")
        st.markdown(f"**PCR Value:** {pcr_value if pcr_value else 'N/A'} → {pcr_trend}")
        st.markdown(f"**ATM Strike:** {atm_strike if atm_strike else 'N/A'}")
        st.markdown(f"**Support:** {support if support else 'N/A'}")
        st.markdown(f"**Resistance:** {resistance if resistance else 'N/A'}")

    st.markdown("---")
