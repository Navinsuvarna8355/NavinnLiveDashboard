Railway        y=df['PE_theta'].abs(),
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

# Init session state
if "data_container" not in st.session_state:
    st.session_state.data_container = None
    st.session_state.selected_symbol = "Bank Nifty"
if "last_fetch_time" not in st.session_state:
    st.session_state.last_fetch_time = time.time()

# --- Settings Sidebar ---
col1, col2 = st.columns([1, 2])
with col1:
    st.header("Settings")
    selected_symbol = st.selectbox(
        "Select an Index",
        ["Bank Nifty", "Nifty", "Sensex"],
        index=["Bank Nifty", "Nifty", "Sensex"].index(st.session_state.selected_symbol)
    )
    auto_refresh = st.checkbox("Auto-Refresh Data", value=True)
    refresh_rate = st.slider("Refresh Rate (seconds)", 30, 120, 60, step=15)
    fetch_button = st.button("Manual Fetch")

# --- Fetch Logic ---
current_time = time.time()
if st.session_state.data_container is None or selected_symbol != st.session_state.selected_symbol or fetch_button:
    st.session_state.selected_symbol = selected_symbol
    with st.spinner(f"Fetching live data for {selected_symbol}..."):
        data_dict = fetch_option_chain(selected_symbol, current_time // refresh_rate)
        if data_dict:
            st.session_state.data_container = data_dict
            st.session_state.last_fetch_time = current_time
        else:
            st.session_state.data_container = None

# --- Auto-refresh logic (UPDATED) ---
if auto_refresh and (current_time - st.session_state.last_fetch_time >= refresh_rate):
    with st.spinner(f"Auto-refreshing data for {st.session_state.selected_symbol}..."):
        data_dict = fetch_option_chain(st.session_state.selected_symbol, current_time // refresh_rate)
        if data_dict:
            st.session_state.data_container = data_dict
            st.session_state.last_fetch_time = current_time
    st.rerun()

# --- Left Column UI ---
with col1:
    if st.session_state.data_container:
        st.metric(f"{st.session_state.selected_symbol} Value", st.session_state.data_container["underlying_value"])
        selected_expiry = st.selectbox(
            "Select Expiry Date",
            st.session_state.data_container["expiry_dates"],
            format_func=lambda d: datetime.strptime(d, '%d-%b-%Y').strftime('%d %b, %Y')
        )
        filtered_oc_data = [d for d in st.session_state.data_container["records_data"] if d.get("expiryDate") == selected_expiry]
        decay_side, df = detect_decay(filtered_oc_data, st.session_state.data_container["underlying_value"])
        st.metric("Decay Side", decay_side)
        st.caption(f"Last updated: {st.session_state.data_container['fetch_time']}")
    else:
        st.warning("Please fetch data to get started.")

# --- Right Column UI ---
with col2:
    st.header("Live Analysis")
    if st.session_state.data_container:
        tab1, tab2 = st.tabs(["Data Table", "Theta Chart"])
        with tab1:
            st.dataframe(df, width='stretch')
        with tab2:
            chart_fig = create_decay_chart(df)
            st.plotly_chart(chart_fig, use_container_width=True)
    else:
        st.info("Live analysis will appear here after fetching data.")

# --- Recommendations ---
st.divider()
st.header("Trading Recommendations")
if st.session_state.data_container:
    decay_side, _ = detect_decay(st.session_state.data_container["records_data"], st.session_state.data_container["underlying_value"])
    st.info("Note: These are trading ideas based on the decay analysis. Always combine with other market analysis.")
    if decay_side == "CE Decay Active":
        st.subheader("Market Bias: Bearish (Downside)")
        st.write("Call options are losing premium faster than Put options, indicating that traders are actively selling calls. This suggests a bearish or non-trending market sentiment.")
        st.markdown("""
        **Recommended Strategies:**
        * **Sell Call Options (Short Call)**
        * **Buy Put Options (Long Put)**
        * **Bear Put Spread**
        """)
    elif decay_side == "PE Decay Active":
        st.subheader("Market Bias: Bullish (Upside)")
        st.write("Put options are losing premium faster than Call options. This suggests a bullish or upward-trending market sentiment, as traders are actively selling puts.")
        st.markdown("""
        **Recommended Strategies:**
        * **Sell Put Options (Short Put)**
        * **Buy Call Options (Long Call)**
        * **Bull Call Spread**
        """)
    else:
        st.subheader("Market Bias: Neutral/Range-bound")
        st.write
