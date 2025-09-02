import streamlit as st
from upstox_api.api import Upstox
from streamlit_autorefresh import st_autorefresh

# 🔐 INSERT YOUR CREDENTIALS HERE
api_key = "adc99235-baf1-4b04-8c94-b1502e573924"       # ← Replace this
api_secret = "hoxszn7cr3" # ← Replace this
redirect_uri = "http://localhost:8000"

# 🔄 Refresh every 60 seconds
st_autorefresh(interval=60000, limit=100, key="refresh")

# 🔗 Authenticate
u = Upstox(api_key, api_secret, redirect_uri)

# Step 1: Get login URL
if 'access_token' not in st.session_state:
    login_url = u.get_login_url()
    st.markdown(f"🔐 [Click here to login to Upstox]({login_url})")

    # Paste the code from redirect URL after login
    code = st.text_input("Paste the code from URL after login:")
    if code:
        u.get_access_token(code)
        st.session_state['access_token'] = u.get_access_token()
        st.success("✅ Access token received!")
else:
    u.set_access_token(st.session_state['access_token'])

    # 📈 Fetch Live Price
    try:
        live_data = u.get_live_feed('NSE_INDEX|Nifty 50', u.LiveFeedType.LTP)
        ltp = live_data['ltp']
        st.title("📊 Live Market Dashboard")
        st.markdown(f"### 🔴 Live NIFTY Price: `{ltp}`")

        # 🧠 Simple Signal Logic
        if ltp > 20000:
            signal = "BUY PE"
        elif ltp < 19500:
            signal = "BUY CE"
        else:
            signal = "SIDEWAYS"

        st.markdown(f"### 📌 Signal: **{signal}**")

    except Exception as e:
        st.error(f"Error fetching live data: {e}")
