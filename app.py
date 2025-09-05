import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import time
import plotly.graph_objects as go

# --- Timezone Setup ---
IST = ZoneInfo("Asia/Kolkata")

# --- Symbol Mapping ---
SYMBOL_MAP = {
    "Nifty": "NIFTY",
    "Bank Nifty": "BANKNIFTY",
    "Sensex": "SENSEX"
}

# --- Cached Fetch ---
@st.cache_data(ttl=60)
def fetch_option_chain(symbol_key, current_time_key):
    symbol_name = SYMBOL_MAP.get(symbol_key)
    if not symbol_name:
        st.error("Invalid symbol selected.")
        return None

    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol_name}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        resp = session.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {
            "records_data": data["records"]["data"],
            "underlying_value": data["records"]["underlyingValue"],
            "expiry_dates": data["records"]["expiryDates"],
            "fetch_time": datetime.now(IST).strftime('%H:%M:%S')
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {symbol_key}: {e}")
        return None

# --- Decay Detection ---
def detect_decay(oc_data, underlying, decay_range=150):
    atm_strikes = [d for d in oc_data if abs(d["strikePrice"] - underlying) <= decay_range and "CE" in d and "PE" in d]
    details = []

    for strike_data in atm_strikes:
        ce_data = strike_data["CE"]
        pe_data = strike_data["PE"]

        ce_theta = ce_data.get("theta", 0)
        pe_theta = pe_data.get("theta", 0)
        ce_chg = ce_data.get("change", 0)
        pe_chg = pe_data.get("change", 0)

        decay_side = "Both"
        if ce_theta != 0 and pe_theta != 0:
            if abs(ce_theta) > abs(pe_theta) and ce_chg < 0:
                decay_side = "CE"
            elif abs(pe_theta) > abs(ce_theta) and pe_chg < 0:
                decay_side = "PE"
        elif ce_chg < 0 and pe_chg < 0:
            if abs(ce_chg) > abs(pe_chg):
                decay_side = "CE"
            elif abs(pe_chg) > abs(ce_chg):
                decay_side = "PE"

        details.append({
            "strikePrice": strike_data["strikePrice"],
            "CE_theta": ce_theta,
            "PE_theta": pe_theta,
            "CE_Change": ce_chg,
            "PE_Change": pe_chg,
            "Decay_Side": decay_side
        })

    df = pd.DataFrame(details).sort_values(by="strikePrice")
    ce_count = df[df['Decay_Side'] == 'CE'].shape[0]
    pe_count = df[df['Decay_Side'] == 'PE'].shape[0]

    overall_decay_side = "Both Sides Decay"
    if ce_count > pe_count:
        overall_decay_side = "CE Decay Active"
    elif pe_count > ce_count:
        overall_decay_side = "PE Decay Active"

    return overall_decay_side, df

# --- Chart ---
def create_decay_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['strikePrice'], y=df['CE_theta'].abs(), name='CE Theta', marker_color='#FF5733'))
    fig.add_trace(go.Bar(x=df['strikePrice'], y=df['PE_theta'].abs(), name='PE Theta', marker_color='#0080FF'))
    fig.update_layout(title='Absolute Theta Values by Strike Price', xaxis_title='Strike Price', yaxis_title='Theta', barmode='group')
    return fig

# --- UI Setup ---
st.set_page_config(page_title="Decay + Directional Bias", layout="wide", page_icon="📈")
st.title("📊 Decay + Directional Bias Detector")

if "data_container" not in st.session_state:
    st.session_state.data_container = None
    st.session_state.selected_symbol = "Bank Nifty"

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Settings")
    selected_symbol = st.selectbox("Select an Index", list(SYMBOL_MAP.keys()), index=list(SYMBOL_MAP.keys()).index(st.session_state.selected_symbol))
    auto_refresh = st.checkbox("Auto-Refresh Data", value=True)
    refresh_rate = st.slider("Refresh Rate (seconds)", 30, 120, 60, step=15)
    fetch_button = st.button("Manual Fetch")

    if fetch_button or st.session_state.data_container is None or selected_symbol != st.session_state.selected_symbol:
        st.session_state.selected_symbol = selected_symbol
        with st.spinner(f"Fetching live data for {selected_symbol}..."):
            data_dict = fetch_option_chain(selected_symbol, datetime.now())
            st.session_state.data_container = data_dict if data_dict else None

    if st.session_state.data_container:
        st.metric(f"{selected_symbol} Value", st.session_state.data_container["underlying_value"])
        selected_expiry = st.selectbox("Select Expiry Date", st.session_state.data_container["expiry_dates"], format_func=lambda d: datetime.strptime(d, '%d-%b-%Y').strftime('%d %b, %Y'))
        filtered_oc_data = [d for d in st.session_state.data_container["records_data"] if d.get("expiryDate") == selected_expiry]
        decay_side, df = detect_decay(filtered_oc_data, st.session_state.data_container["underlying_value"])
        st.metric("Decay Side", decay_side)
        st.caption(f"Last updated: {st.session_state.data_container['fetch_time']}")
    else:
        st.warning("Please fetch data to get started.")

with col2:
    st.header("Live Analysis")
    if st.session_state.data_container:
        tab1, tab2 = st.tabs(["Data Table", "Theta Chart"])
        with tab1:
            st.dataframe(df, use_container_width=True)
        with tab2:
            st.plotly_chart(create_decay_chart(df), use_container_width=True)
    else:
        st.info("Live analysis will appear here after fetching data.")

# --- Auto Refresh ---
if auto_refresh and st.session_state.data_container:
    time.sleep(refresh_rate)
    st.rerun()

# --- Recommendations ---
st.divider()
st.header("Trading Recommendations")

if st.session_state.data_container:
    st.info("Note: These are trading ideas based on the decay analysis. Always combine with other market analysis.")
    if decay_side == "CE Decay Active":
        st.subheader("Market Bias: Bearish (Downside)")
        st.write("Call options are losing premium faster than Put options, indicating active call selling and bearish sentiment.")
        st.markdown("""
        **Recommended Strategies:**
        * **Sell Call Options (Short Call)**
        * **Buy Put Options (Long Put)**
        * **Bear Put Spread**
        """)
    elif decay_side == "PE Decay Active":
        st.subheader("Market Bias: Bullish (Upside)")
        st.write("Put options are losing premium faster than Calls, suggesting bullish sentiment and active put selling.")
        st.markdown("""
        **Recommended Strategies:**
        * **Sell Put Options (Short Put)**
        * **Buy Call Options (Long Call)**
        * **Bull Call Spread**
        """)
    else:
        st.subheader("Market Bias: Neutral/Range-bound")
        st.write("Both sides are decaying similarly, indicating a range-bound or low-volatility market.")
        st.markdown("""
        **Recommended Strategies:**
        * **Sell Straddle or Strangle**
        * **Iron Condor**
        """)

