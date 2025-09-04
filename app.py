import streamlit as st
import pandas as pd
import time
import requests

st.set_page_config(page_title="Decay + Directional Bias Detector", layout="wide")

# Auto-refresh every 10 seconds
st_autorefresh = st.experimental_rerun if time.time() % 10 < 1 else None

st.title("Decay + Directional Bias Detector")

# Fetch live data function
def fetch_live_data():
    # Replace with your actual API endpoint
    url = "https://your-backend-endpoint.com/get_data"
    try:
        data = requests.get(url).json()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Live data fetch
df = fetch_live_data()

# Show underlying value
if not df.empty:
    underlying = df.get("underlying", [None])[0]
    st.subheader(f"Underlying: {underlying}")

# Directional Strength Meter
if not df.empty:
    df["strength_score"] = df["CE_theta"] - df["PE_theta"]

    def bias_label(score):
        if score > 0:
            return "🟢 Call Bias"
        elif score < 0:
            return "🔴 Put Bias"
        else:
            return "🟡 Neutral"

    df["bias"] = df["strength_score"].apply(bias_label)

    # Display table
    st.dataframe(df[["strikePrice", "CE_theta", "PE_theta", "decay_side", "bias"]])

# Last updated time
st.caption(f"Last updated: {time.strftime('%H:%M:%S')}")
