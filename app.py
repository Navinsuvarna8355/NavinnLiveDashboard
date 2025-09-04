import streamlit as st
import pandas as pd
import time
import requests

# ---------- CONFIG ----------
st.set_page_config(page_title="Decay + Directional Bias Detector", layout="wide")
API_URL = "https://your-backend-endpoint.com/get_data"  # <-- Replace with your API
REFRESH_RATE = 10  # seconds

# ---------- AUTO-REFRESH (works on all versions) ----------
last_refresh = st.session_state.get("last_refresh", 0)
now = time.time()
if now - last_refresh > REFRESH_RATE:
    st.session_state["last_refresh"] = now
    st.experimental_rerun()

st.title("Decay + Directional Bias Detector")

# ---------- FETCH LIVE DATA ----------
def fetch_live_data():
    try:
        resp = requests.get(API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)

        if resp.status_code != 200:
            st.warning(f"⚠ API returned status {resp.status_code}")
            return pd.DataFrame()

        raw = resp.text.strip()
        if not raw or (not raw.startswith("{") and not raw.startswith("[")):
            st.warning("⚠ API returned empty or non‑JSON data.")
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
            st.warning("⚠ Unexpected data format.")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Fetch error: {e}")
        return pd.DataFrame()

# ---------- GET DATA ----------
df = fetch_live_data()

# ---------- DISPLAY ----------
if not df.empty:
    # Underlying value
    if "underlying" in df.columns:
        st.subheader(f"Underlying: {df['underlying'].iloc[0]}")
    elif "Underlying" in df.columns:
        st.subheader(f"Underlying: {df['Underlying'].iloc[0]}")

    # Bias calculation
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

    # Show table
    st.dataframe(df)

else:
    st.info("No data available. Check API or connection.")

# ---------- LAST UPDATED ----------
st.caption(f"Last updated: {time.strftime('%H:%M:%S')}")
