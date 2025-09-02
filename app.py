import streamlit as st
from streamlit_autorefresh import st_autorefresh
import upstox_client
from collections import Counter
import random

# 🔄 Auto-refresh every 60 seconds
st_autorefresh(interval=60000, limit=100, key="dashboard_refresh")

st.title("📊 Market Signal Dashboard")

# 🔐 Load secrets
API_KEY = st.secrets["adc99235-baf1-4b04-8c94-b1502e573924"]
API_SECRET = st.secrets["hoxszn7cr3"]
REDIRECT_URI = st.secrets["http://localhost:8000"]

# 🧠 Initialize Upstox SDK
u = Upstox(api_key=API_KEY, api_secret=API_SECRET, redirect_uri=REDIRECT_URI)

# 🔗 Login flow
if "access_token" not in st.session_state:
    login_url = u.get_login_url()
    st.markdown(f"[🔐 Login to Upstox]({login_url})")

    code = st.text_input("Paste the code from Upstox redirect URL here:")
    if code:
        try:
            access_token = u.get_access_token(code)
            u.set_access_token(access_token)
            st.session_state["access_token"] = access_token
            st.success("✅ Logged in successfully!")
        except Exception as e:
            st.error(f"Login failed: {e}")
    st.stop()
else:
    u.set_access_token(st.session_state["access_token"])

# 🧠 Dummy strategy logic (replace with real signals later)
def get_strategy_signal(strategy_name):
    return random.choice(["Buy CE", "Buy PE", "Sideways"])

# 🧮 Aggregate final market view
def aggregate_signals(signals):
    count = Counter(signals)
    most_common = count.most_common(1)[0][0]
    return most_common

# 📈 Strategy-wise signals
strategies = ["EMA Crossover", "RSI Divergence", "MACD Momentum", "Option Chain Bias"]
signals = {}

for strat in strategies:
    signal = get_strategy_signal(strat)
    signals[strat] = signal

# 🧠 Final market view
final_view = aggregate_signals(list(signals.values()))

# 📋 Display
st.subheader("🔍 Strategy Signals")
for strat, signal in signals.items():
    st.metric(label=strat, value=signal)

st.subheader("🧠 Final Market View")
if final_view == "Buy CE":
    st.success("📈 Bullish")
elif final_view == "Buy PE":
    st.error("📉 Bearish")
else:
    st.warning("🔄 Sideways")
