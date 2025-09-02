import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from collections import Counter
import random

# 🔄 Auto-refresh every 60 seconds
st_autorefresh(interval=60000, limit=100, key="dashboard_refresh")

st.title("📊 Market Signal Dashboard")

# 🔐 API credentials
API_KEY = "adc99325-baf1-4b04-8c94-b1502e573924"
API_SECRET = "hoxszn7cr3"
REDIRECT_URI = "https://navinn.streamlit.app"

# 🔗 Login flow
if "access_token" not in st.session_state:
    login_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    st.markdown(f"[🔐 Login to Upstox]({login_url})")

    code = st.text_input("Paste the code from Upstox redirect URL here:")
    if code:
        try:
            token_url = "https://api.upstox.com/v2/login/authorization/token"
            payload = {
                "code": code,
                "client_id": API_KEY,
                "client_secret": API_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code"
            }
            response = requests.post(token_url, data=payload)
            token_data = response.json()

            if "access_token" in token_data:
                st.session_state["access_token"] = token_data["access_token"]
                st.success("✅ Logged in successfully!")
            else:
                st.error(f"Login failed: {token_data.get('error_description', 'Unknown error')}")
        except Exception as e:
            st.error(f"Login failed: {e}")
    st.stop()

# 🧠 Dummy strategy logic
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
