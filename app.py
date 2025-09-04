import streamlit as st
import pandas as pd
import time
import requests

st.set_page_config(page_title="Decay + Directional Bias Detector", layout="wide")

# --- CONFIG ---
API_URL = "https://your-backend-endpoint.com/get_data"  # <-- Replace with your API

# --- AUTO REFRESH ---
st_autorefresh = st.experimental_rerun if time.time() % 10 < 1 else None

st.title("Decay + Directional Bias Detector")

# --- FETCH LIVE DATA FUNCTION ---
def fetch_live_data():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if resp.status_code != 200:
            st.warning(f"⚠ API returned status {resp.status_code}")
            return pd.DataFrame()

        # Debug: show raw response if needed
        # st.write("Raw Response:", resp.text)

        try:
            data = resp.json()
        except ValueError:
            st.error("❌ API did not return valid JSON.")
            return pd.DataFrame()

        # Ensure data is in DataFrame format
        if isinstance(data, dict) and "data" in data:
            df = pd.DataFrame(data["data"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            st.error("❌ Unexpected data format from API.")
            return pd.DataFrame()

        return df

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data: {e}")
        return pd.DataFrame()

# --- GET DATA ---
df = fetch_live_data()

# --- DISPLAY ---
if not df.empty:
    # Show underlying if available
    if "underlying" in df.columns:
        st.subheader(f"Underlying: {df['underlying'].iloc[0]}")
    elif "Underlying" in df.columns:
        st.subheader(f"Underlying: {df['Underlying'].iloc[0]}")

    # Calculate strength score
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

    # Display table
    st.dataframe(df)

else:
    st.info("No data available. Check API or connection.")

# --- LAST UPDATED ---
st.caption(f"Last updated: {time.strftime('%H:%M:%S')}")
