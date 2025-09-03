import streamlit as st
import random
import time

# Streamlit App for Trading Dashboard

# Helper function to calculate EMA
def calculate_ema(prices, period):
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

# App Title and Description
st.title('NSE Trading Dashboard')
st.markdown('<p class="text-center text-sm sm:text-base text-gray-400 mb-6"> <span style="font-weight:bold; color:red;">Warning:</span> This app is for educational purposes only. The data is simulated and should not be used for real trading decisions.</p>', unsafe_allow_html=True)

# Index Selection
selected_index_name = st.selectbox(
    'Select Index:',
    list(indices_data.keys())
)

# Initialize session state for data history
if 'history' not in st.session_state:
    st.session_state.history = {
        'NIFTY 50': [indices_data['NIFTY 50']['base_price']],
        'BANKNIFTY': [indices_data['BANKNIFTY']['base_price']],
        'FINNIFTY': [indices_data['FINNIFTY']['base_price']],
    }

# Display a container for live data
live_data_container = st.empty()

# The main loop to simulate live data updates
while True:
    with live_data_container.container():
        # Get data for the selected index
        current_index = indices_data[selected_index_name]
        history = st.session_state.history[selected_index_name]
        
        # Simulate new spot price
        new_spot_price = history[-1] + (random.random() - 0.5) * current_index['volatility']
        
        # Update history and keep it at a reasonable length
        history.append(new_spot_price)
        history = history[-50:]
        st.session_state.history[selected_index_name] = history

        latest_prices = history
        
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

        # Display metrics
        st.metric("Spot Price", f"₹{new_spot_price:.2f}")
        st.metric("Strike Price", f"₹{strike_price:.2f}")

        # Display signals with colors
        st.subheader("Trading Signals")
        
        def display_signal(label, signal, color):
            st.markdown(
                f"""
                <div style="background-color:{color}; padding:1rem; border-radius:0.5rem; text-align:center; margin-bottom:1rem;">
                    <h3 style="margin:0; font-size:1.25rem;">{label}</h3>
                    <p style="margin:0; font-weight:bold; font-size:1.5rem;">{signal}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        if ema_signal == 'Buy (CE)':
            display_signal('EMA Signal', ema_signal, '#16a34a')
        elif ema_signal == 'Sell (PE)':
            display_signal('EMA Signal', ema_signal, '#dc2626')
        else:
            display_signal('EMA Signal', ema_signal, '#d97706')

        if pcr_signal == 'Bullish':
            display_signal('PCR Signal', pcr_signal, '#16a34a')
        elif pcr_signal == 'Bearish':
            display_signal('PCR Signal', pcr_signal, '#dc2626')
        else:
            display_signal('PCR Signal', pcr_signal, '#d97706')

        if rsi_signal == 'Overbought' or rsi_signal == 'Oversold':
            display_signal('RSI Signal', rsi_signal, '#d97706')
        else:
            display_signal('RSI Signal', rsi_signal, '#16a34a' if rsi_signal == 'Bullish' else '#dc2626' if rsi_signal == 'Bearish' else '#d97706')

    # Wait for a few seconds before the next update
    time.sleep(2)
