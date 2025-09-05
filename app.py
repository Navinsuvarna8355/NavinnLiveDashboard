import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import plotly.graph_objects as go

# ---------------------------
# Timezone Setup
# ---------------------------
IST = ZoneInfo("Asia/Kolkata")

# ---------------------------
# Symbol Mapping
# ---------------------------
SYMBOL_MAP = {
    "Nifty": "NIFTY",
    "Bank Nifty": "BANKNIFTY",
    "Sensex": "SENSEX"
}

# ---------------------------
# Fetch Option Chain (cached)
# ---------------------------
@st.cache_data(ttl=60)
def fetch_option_chain(symbol_key: str, cache_buster: float):
    """
    Fetch option chain JSON from NSE for the given symbol_key.
    Returns a dict with records_data, underlying_value, expiry_dates, fetch_time.
    """
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
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "records_data": data["records"]["data"],
            "underlying_value": data["records"]["underlyingValue"],
            "expiry_dates": data["records"]["expiryDates"],
            "fetch_time": datetime.now(IST).strftime("%H:%M:%S IST")
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {symbol_key}: {e}")
        return None

# ---------------------------
# Decay Detection Logic
# ---------------------------
def detect_decay(oc_data: list, underlying: float, decay_range: int = 150):
    """
    Analyze CE and PE theta/change to detect which side is decaying more.
    Returns overall_decay_side and a DataFrame of strike-by-strike details.
    """
    details = []
    for item in oc_data:
        if "CE" not in item or "PE" not in item:
            continue
        strike = item["strikePrice"]
        if abs(strike - underlying) > decay_range:
            continue

        ce = item["CE"]
        pe = item["PE"]
        ce_theta = ce.get("theta", 0)
        pe_theta = pe.get("theta", 0)
        ce_chg = ce.get("change", 0)
        pe_chg = pe.get("change", 0)

        # Determine decay side
        if ce_theta != 0 and pe_theta != 0:
            if abs(ce_theta) > abs(pe_theta) and ce_chg < 0:
                side = "CE"
            elif abs(pe_theta) > abs(ce_theta) and pe_chg < 0:
                side = "PE"
            else:
                side = "Both"
        elif ce_chg < 0 and pe_chg < 0:
            if abs(ce_chg) > abs(pe_chg):
                side = "CE"
            elif abs(pe_chg) > abs(ce_chg):
                side = "PE"
            else:
                side = "Both"
        elif ce_chg < 0:
            side = "CE"
        elif pe_chg < 0:
            side = "PE"
        else:
            side = "None"

        details.append({
            "Strike Price": strike,
            "CE Theta": ce_theta,
            "PE Theta": pe_theta,
            "CE Change": ce_chg,
            "PE Change": pe_chg,
            "Decay Side": side
        })

    df = pd.DataFrame(details).sort_values("Strike Price")
    ce_count = df[df["Decay Side"] == "CE"].shape[0]
    pe_count = df[df["Decay Side"] == "PE"].shape[0]

    if ce_count > pe_count:
        overall = "CE Decay Active"
    elif pe_count > ce_count:
        overall = "PE Decay Active"
    else:
        overall = "Both Sides Decay"

    return overall, df

# ---------------------------
# Chart Builder
# ---------------------------
def create_decay_chart(df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["Strike Price"],
        y=df["CE Theta"].abs(),
        name="CE Theta (Abs)",
        marker_color="#FF5733"
    ))
    fig.add_trace(go.Bar(
        x=df["Strike Price"],
        y=df["PE Theta"].abs(),
        name="PE Theta (Abs)",
        marker_color="#0080FF"
    ))
    fig.update_layout(
        title="Absolute Theta by Strike Price",
        xaxis_title="Strike Price",
        yaxis_title="Absolute Theta",
        barmode="group"
    )
    return fig

# ---------------------------
# Streamlit UI Setup
# ---------------------------
st.set_page_config(
    page_title="Decay & Directional Bias Detector",
    layout="wide",
    page_icon="📈"
)

st.title("📊 Decay & Directional Bias Detector")

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = None
    st.session_state.symbol = "Nifty"
    st.session_state.last_fetch = 0.0

# Sidebar Controls
with st.sidebar:
    st.header("Settings")
    symbol = st.selectbox(
        "Index",
        list(SYMBOL_MAP.keys()),
        index=list(SYMBOL_MAP.keys()).index(st.session_state.symbol)
    )
    auto_refresh = st.checkbox("Auto Refresh", value=True)
    refresh_interval = st.slider("Refresh Interval (s)", 30, 120, 60, step=15)
    manual = st.button("Fetch Now")

# Fetch / Refresh Logic
now_ts = time.time()
if manual or st.session_state.data is None or symbol != st.session_state.symbol:
    st.session_state.symbol = symbol
    with st.spinner("Fetching data..."):
        st.session_state.data = fetch_option_chain(symbol, now_ts)
        st.session_state.last_fetch = now_ts

elif auto_refresh and (now_ts - st.session_state.last_fetch >= refresh_interval):
    with st.spinner("Auto-refreshing..."):
        st.session_state.data = fetch_option_chain(symbol, now_ts)
        st.session_state.last_fetch = now_ts

# Main Layout
col1, col2 = st.columns([1, 2])

with col1:
    if st.session_state.data:
        st.metric(
            label=f"{symbol} Spot Price",
            value=st.session_state.data["underlying_value"]
        )
        expiry = st.selectbox(
            "Expiry Date",
            st.session_state.data["expiry_dates"],
            format_func=lambda d: datetime.strptime(d, "%d-%b-%Y").strftime("%d %b %Y")
        )
        records = st.session_state.data["records_data"]
        filtered = [
            r for r in records if r.get("expiryDate") == expiry
        ]
        bias, df = detect_decay(filtered, st.session_state.data["underlying_value"])
        st.metric("Decay Bias", bias)
        st.caption(f"Last updated: {st.session_state.data['fetch_time']}")

    else:
        st.warning("No data available. Click ‘Fetch Now’ to load data.")

with col2:
    st.header("Analysis")
    if st.session_state.data:
        tabs = st.tabs(["Data Table", "Theta Chart"])
        with tabs[0]:
            st.dataframe(df, use_container_width=True)
        with tabs[1]:
            st.plotly_chart(create_decay_chart(df), use_container_width=True)
    else:
        st.info("Analysis will appear once data is loaded.")

# Recommendations
st.markdown("---")
st.header("Trading Recommendations")
if st.session_state.data:
    st.info("These suggestions are based on decay bias. Always use additional analysis.")

    if bias == "CE Decay Active":
        st.subheader("Bearish Bias (Downside)")
        st.write("Call options are decaying faster than puts. Consider bearish strategies:")
        st.markdown("""
        - Sell Call Options (Short Call)
        - Buy Put Options (Long Put)
        - Bear Put Spread
        """)
    elif bias == "PE Decay Active":
        st.subheader("Bullish Bias (Upside)")
        st.write("Put options are decaying faster than calls. Consider bullish strategies:")
        st.markdown("""
        - Sell Put Options (Short Put)
        - Buy Call Options (Long Call)
        - Bull Call Spread
        """)
    else:
        st.subheader("Neutral / Range-Bound Bias")
        st.write("Both calls and puts are decaying similarly. Consider range strategies:")
        st.markdown("""
        - Sell Straddle or Strangle
        - Iron Condor
        """)
else:
    st.write("Fetch data to see strategy recommendations.")
