import streamlit as st
import random
import time

# Streamlit App for Trading Dashboard

# Helper function to calculate EMA
def calculate_ema(prices, period):
    """Calculates the Exponential Moving Average (EMA) for a given set of prices."""
    if not prices or len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = prices[0]
    for i in range(1, len(prices)):
        ema = prices[i] * k + ema * (1 - k)
    return ema

# Mock data for different indices
indices_data = {
    'NIFTY 50': {'base_price': 22500, 'volatility': 20},
    'BANKNIFTY': {'base_price': 48000, 'volatility': 50},
    'FINNIFTY': {'base_price': 21500, 'volatility': 30},
}

# --- UI Layout ---

# Page Configuration
st.set_page_config(layout="wide")

# App Title and Description
st.title('NSE Trading Dashboard')
st.markdown("""
    <div style='text-align: center; color: #888;'>
        <p>
            <span style='font-weight:bold; color:#f87171;'>Warning:</span> This app is for educational purposes only. The data is simulated and should not be used for real trading decisions.
        </p>
    </div>
""", unsafe_allow_html=True)

# Index Selection
st.header("Index Selection")
selected_index_name = st.selectbox(
    'Select Index:',
    list(indices_data.keys()),
    key='index_selector'
)

# Initialize session state for data history
if 'history' not in st.session_state:
    st.session_state.history = {
        'NIFTY 50': [indices_data['NIFTY 50']['base_price']],
        'BANKNIFTY': [indices_data['BANKNIFTY']['base_price']],
        'FINNIFTY': [indices_data['FINNIFTY']['base_price']],
    }

# Display a container for live data
live_data_placeholder = st.empty()

# The main loop to simulate live data updates
while True:
    with live_data_placeholder.container():
        st.subheader(f"Live Data for {selected_index_name}")
        
        # Get data for the selected index
        current_index = indices_data[selected_index_name]
        history = st.session_state.history[selected_index_name]
        
        # Simulate new spot price
        new_spot_price = history[-1] + (random.random() - 0.5) * current_index['volatility']
        
        # Update history and keep it at a reasonable length
        history.append(new_spot_price)
        st.session_state.history[selected_index_name] = history[-50:]

        latest_prices = st.session_state.history[selected_index_name]
        
        # Calculate indicators
        lowest_ema = calculate_ema(latest_prices, 3)
        medium_ema = calculate_ema(latest_prices, 13)
        longest_ema = calculate_ema(latest_prices, 9)
        
        # EMA Crossover Signal Logic
        ema_signal = 'Sideways'
        if lowest_ema and medium_ema and longest_ema:
            if lowest_ema > medium_ema and lowest_ema > longest_ema:
                ema_signal = 'Buy (CE)'
            elif lowest_ema < medium_ema and lowest_ema < longest_ema:
                ema_signal = 'Sell (PE)'

        # Simulate PCR and RSI
        pcr = 0.8 + random.random() * 0.4
        pcr_signal = 'Neutral'
        if pcr > 1.1:
            pcr_signal = 'Bullish'
        elif pcr < 0.9:
            pcr_signal = 'Bearish'
        
        rsi = 30 + random.random() * 40
        rsi_signal = 'Neutral'
        if rsi > 70:
            rsi_signal = 'Overbought'
        elif rsi < 30:
            rsi_signal = 'Oversold'
            
        # Calculate Strike Price (simulated)
        strike_price = round(new_spot_price / 50) * 50

        # --- Display metrics and signals ---
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Spot Price", f"₹{new_spot_price:.2f}")
        
        with col2:
            st.metric("Strike Price", f"₹{strike_price:.2f}")

        st.subheader("Trading Signals")
        col_ema, col_pcr, col_rsi = st.columns(3)
        
        def get_signal_color_and_icon(signal):
            if 'Buy' in signal or 'Bullish' in signal:
                return "green", "▲"
            elif 'Sell' in signal or 'Bearish' in signal:
                return "red", "▼"
            else:
                return "orange", "▬"
        
        ema_color, ema_icon = get_signal_color_and_icon(ema_signal)
        pcr_color, pcr_icon = get_signal_color_and_icon(pcr_signal)
        rsi_color, rsi_icon = get_signal_color_and_icon(rsi_signal)

        with col_ema:
            st.markdown(f"### EMA Signal")
            st.markdown(f"<p style='color:{ema_color}; font-size: 24px; font-weight: bold;'>{ema_icon} {ema_signal}</p>", unsafe_allow_html=True)
            
        with col_pcr:
            st.markdown(f"### PCR Signal")
            st.markdown(f"<p style='color:{pcr_color}; font-size: 24px; font-weight: bold;'>{pcr_icon} {pcr_signal}</p>", unsafe_allow_html=True)
            
        with col_rsi:
            st.markdown(f"### RSI Signal")
            st.markdown(f"<p style='color:{rsi_color}; font-size: 24px; font-weight: bold;'>{rsi_icon} {rsi_signal}</p>", unsafe_allow_html=True)

    # Wait for a few seconds before the next update
    time.sleep(2)
