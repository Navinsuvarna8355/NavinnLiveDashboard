@st.cache_data(ttl=60)
def fetch_option_chain(symbol_key, current_time_key):
    symbol_name = SYMBOL_MAP.get(symbol_key)
    if not symbol_name:
        st.error("Invalid symbol selected.")
        return None

    nse_oc_url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol_name}"
    headers = {
        "User -Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        resp = session.get(nse_oc_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        return {
            "records_data": data["records"]["data"],
            "underlying_value": data["records"]["underlyingValue"],
            "expiry_dates": data["records"]["expiryDates"],
            "fetch_time": datetime.now()  # datetime object here
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {symbol_key}: {e}")
        return None

# Later in your Streamlit UI code, when displaying the timestamp:
if st.session_state.data_container:
    fetch_time = st.session_state.data_container['fetch_time']
    st.caption(f"Last updated: {fetch_time.strftime('%H:%M:%S')}")
