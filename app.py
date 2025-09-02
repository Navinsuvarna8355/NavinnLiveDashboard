import streamlit as st
from streamlit_autorefresh import st_autorefresh
import upstox_client
from upstox_client.api import LoginApi
from upstox_client.models import *
from collections import Counter
import random

# 🔄 Auto-refresh every 60 seconds
st_autorefresh(interval=60000, limit=100, key="dashboard_refresh")

st.title("📊 Market Signal Dashboard")

# 🔐 Load secrets
API_KEY = st.secrets["adc99235-baf1-4b04-8c94-b1502e573924"]
API_SECRET = st.secrets["hoxszn7cr3"]
REDIRECT_URI = st.secrets["UPSTOX_REDIRECT_URI"]

# ⚙️ Configure Upstox SDK
configuration = upstox_client.Configuration()
configuration.api_key['apiKey'] = API_KEY
configuration.api_key['apiSecret'] = API_SECRET
configuration.redirect_uri = REDIRECT_URI
api_client = upstox_client.ApiClient(configuration)
login_api = LoginApi(api_client)

# 🔗 Login flow
if "access_token" not in st.session_state:
    login_url = login_api.get_login_url()
    st.markdown(f"[🔐 Login to Upstox]({login_url})")

    code = st.text_input("Paste the code from Upstox redirect URL here:")
    if code:
        try:
            token_response = login_api.get_access_token(code)
            st.session_state["access_token"] = token_response.access_token
            configuration.access_token = token_response.access_token
            st.success("✅ Logged in successfully!")
        except Exception as e:
            st.error(f"Login failed: {e}")
    st.stop()
else:
    configuration.access_token = st.session_state["access_token"]

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
signals = {strat: get_strategy_signal(strat) for strat in strategies}

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
