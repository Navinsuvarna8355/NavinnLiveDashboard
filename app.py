import streamlit as st
import pandas as pd
import time
import requests

st.set_page_config(page_title="Decay + Directional Bias Detector", layout="wide")

# --- AUTO REFRESH ---
# Refresh every 10 seconds
st_autorefresh = st.experimental_autorefresh(interval=10_000, key="datarefresh")

st.title("Decay + Directional Bias Detector")

API_URL = "https://your-backend-endpoint.com/get_data"  # Replace with your API

def fetch_live_data():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code != 200:
            st.warning(f"⚠ API returned status {resp.status_code}")
            return pd.DataFrame()

        try:
            data = resp.json()
        except ValueError:
            st.error("❌ API did not return valid JSON.")
            return pd.DataFrame()

        if isinstance(data, dict) and "data" in data:
            return pd.DataFrame(data["data"])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            st.error("❌ Unexpected data format from API.")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

df = fetch_live_data()

if not df.empty:
    if "underlying" in df.columns:
        st.subheader(f"Underlying: {df['underlying'].iloc[0]}")
    elif "Underlying" in df.columns:
        st.subheader(f"Underlying: {df['Underlying'].iloc[0]}")

    if "CE_theta" in df.columns and "PE_theta" in df.columns:
        df["strength_score"] = df["CE_theta"] - df["PE_theta"]

        def bias_label(score):
            if score > 0:
                return "🟢 Call Bias"
            elif score < 0:
                return "🔴 Put Bias"
            else:
                return "🟡 Neutral"

        df["bias"] = df["strength_score"].apply(bias_label)

    st.dataframe(df)
else:
    st.info("No data available. Check API or connection.")

st.caption(f"Last updated: {time.strftime('%H:%M:%S')}")
