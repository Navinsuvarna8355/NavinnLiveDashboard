import streamlit as st
import requests
import pandas as pd

# -------------------------------
# 🔧 Config
NIFTY_URL = "https://your-api.com/nifty"
BANKNIFTY_URL = "https://your-api.com/banknifty"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
    # "Authorization": "Bearer YOUR_API_KEY"  # Uncomment if needed
}

# -------------------------------
# 🔍 Fetch Function
def fetch_price_data(url, headers=None):
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200 or not response.text.strip():
            return None
        return response.json()
    except Exception as e:
        print("Fetch error:", e)
        return None

# -------------------------------
# 📊 Display Strategy Block
def display_strategy(name, data):
    st.subheader(f"{name} Strategy")

    if data is None:
        st.warning("⚠️ Data unavailable. Please check source.")
        return

    spot = data.get("spot_price")
    ema_trend = data.get("ema_trend")
    pcr = data.get("pcr_value")
    signal = data.get("signal")
    support = data.get("support")
    resistance = data.get("resistance")
    atm_strike = data.get("atm_strike")

    st.markdown(f"**Spot Price:** {spot if spot else 'Unavailable'}")
    st.markdown(f"**EMA Trend:** {ema_trend}")
    st.markdown(f"**PCR Value:** {pcr} → {signal}")
    st.markdown(f"**ATM Strike:** {atm_strike}")
    st.markdown(f"**Support:** {support}")
    st.markdown(f"**Resistance:** {resistance}")

# -------------------------------
# 🚀 Main App
def main():
    st.title("📈 Market Strategy Dashboard")

    nifty_data = fetch_price_data(NIFTY_URL, HEADERS)
    banknifty_data = fetch_price_data(BANKNIFTY_URL, HEADERS)

    col1, col2 = st.columns(2)
    with col1:
        display_strategy("NIFTY", nifty_data)
    with col2:
        display_strategy("BANKNIFTY", banknifty_data)

if __name__ == "__main__":
    main()
