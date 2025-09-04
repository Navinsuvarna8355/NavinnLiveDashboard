import streamlit as st
import pandas as pd
import datetime

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Navinn Live Dashboard",
    layout="wide"
)

# ---------------------------
# Header
# ---------------------------
st.title("📊 Navinn Live Dashboard")
st.caption("Multi-index market signals with custom strategies")

# ---------------------------
# Sidebar Filters
# ---------------------------
st.sidebar.header("Filters")
selected_index = st.sidebar.selectbox(
    "Select Index",
    ["NIFTY", "BANKNIFTY", "SENSEX"]
)

refresh_rate = st.sidebar.slider("Auto-refresh (seconds)", 5, 60, 15)

# ---------------------------
# Data Fetch Function
# ---------------------------
@st.cache_data(ttl=refresh_rate)
def fetch_data(index_name):
    # Dummy data for example — replace with your API logic
    now = datetime.datetime.now()
    return pd.DataFrame({
        "Time": [now],
        "Index": [index_name],
        "Signal": ["BUY"],
        "Price": [19500.25]
    })

# ---------------------------
# Main Content
# ---------------------------
df = fetch_data(selected_index)

st.subheader(f"Live Data — {selected_index}")
st.dataframe(df, use_container_width=True)

# ---------------------------
# Recommended Strategies Block
# ---------------------------
st.markdown("""
**📌 Recommended Strategies:**
- Sell Straddle or Strangle
- Iron Condor
- Calendar Spread
""")  # ✅ triple quotes closed here

# ---------------------------
# Footer / Notes
# ---------------------------
st.info("Signals are generated based on your custom backend logic (EMA crossover, PCR, hammer candle, etc.).")

