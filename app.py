import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import time
import plotly.graph_objects as go

# --- Utility Functions ---

@st.cache_data(ttl=60)
def fetch_option_chain(symbol="BANKNIFTY"):
    """
    Fetches option chain data for a given symbol and caches it for 60 seconds.
    Includes robust error handling.
    """
    nse_oc_url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    session = requests.Session()
    session.headers.update(headers)

    try:
        resp = session.get(nse_oc_url, timeout=5)
        resp.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = resp.json()
        return data["records"]["data"], data["records"]["underlyingValue"], data["records"]["expiryDates"]
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None, None, None

def detect_decay(oc_data, underlying, decay_range=150):
    """
    Analyzes option chain data to detect decay bias around the ATM strike.
    Uses 'theta' as the primary indicator, and 'change' as a fallback.
    """
    # Filter for strikes near the underlying price
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

def create_decay_chart(df):
    """Creates an interactive bar chart for theta values."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['strikePrice'],
        y=df['CE_theta'].abs(),
        name='CE Theta (Abs)',
        marker_color='#FF5733'
    ))
    
    fig.add_trace(go.Bar(
        x=df['strikePrice'],
        y=df['PE_theta'].abs(),
        name='PE Theta (Abs)',
        marker_color='#0080FF'
    ))

    fig.update_layout(
        title='Absolute Theta Values by Strike Price',
        xaxis_title='Strike Price',
        yaxis_title='Absolute Theta Value',
        barmode='group',
        legend_title='Option Side'
    )
    return fig

# --- Streamlit UI ---
st.set_page_config(page_title="Decay + Directional Bias", layout="wide", page_icon="📈")
st.title("📊 Decay + Directional Bias Detector")

# Initialize Session State
if "oc_data" not in st.session_state:
    st.session_state.oc_data = None
    st.session_state.underlying = None
    st.session_state.expiry_dates = []

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Settings")
    
    auto_refresh = st.checkbox("Auto-Refresh Data", value=True)
    refresh_rate = st.slider("Refresh Rate (seconds)", 30, 120, 60, step=15)
    
    # **IMP CHANGE:** Ab hum button click ya first-run par data fetch karenge
    if st.button("Manual Fetch") or st.session_state.oc_data is None:
        with st.spinner("Fetching live data..."):
            oc_data, underlying, expiry_dates = fetch_option_chain()
            if oc_data:
                st.session_state.oc_data = oc_data
                st.session_state.underlying = underlying
                st.session_state.expiry_dates = expiry_dates

    if st.session_state.oc_data:
        st.metric("Underlying Value", st.session_state.underlying)
        
        selected_expiry = st.selectbox(
            "Select Expiry Date",
            st.session_state.expiry_dates,
            format_func=lambda d: datetime.strptime(d, '%d-%b-%Y').strftime('%d %b, %Y')
        )
        
        filtered_oc_data = [d for d in st.session_state.oc_data if d.get("expiryDate") == selected_expiry]
        
        decay_side, df = detect_decay(filtered_oc_data, st.session_state.underlying)
        
        st.metric("Decay Side", decay_side)
        st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    else:
        st.warning("Please fetch data to get started.")

with col2:
    st.header("Live Analysis")
    if st.session_state.oc_data:
        tab1, tab2 = st.tabs(["Data Table", "Theta Chart"])
        
        with tab1:
            st.dataframe(df, use_container_width=True)
        
        with tab2:
            chart_fig = create_decay_chart(df)
            st.plotly_chart(chart_fig, use_container_width=True)
    else:
        st.info("Live analysis will appear here after fetching data.")

# Auto-refresh loop
if auto_refresh and st.session_state.oc_data:
    time.sleep(refresh_rate)
    st.rerun()
