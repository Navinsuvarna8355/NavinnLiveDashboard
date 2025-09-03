import streamlit as st
import random
import time
import requests
import json

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

# A function to fetch real-time data from an API (Placeholder)
def fetch_live_data(index_name):
    """
    A placeholder function to fetch real-time data from a live market data API.
    You would need to update this with your API key and the correct API endpoint.
    """
    # Here you would use your chosen API.
    # For example, this is a hypothetical API call.
    # api_url = f"https://api.yourprovider.com/data?symbol={index_name}"
    # headers = {"Authorization": "Bearer YOUR_API_KEY"}

    try:
        # response = requests.get(api_url, headers=headers)
        # response.raise_for_status()  # Raises an HTTPError if the request failed.
        # data = response.json()

        # For now, we'll continue using mock data so the app keeps working.
        mock_data = {
            'NIFTY 50': {'spot_price': 22500 + (random.random() - 0.5) * 20, 'pcr': 0.95 + (random.random() - 0.5) * 0.1, 'rsi': 55 + (random.random() - 0.5) * 10},
            'BANKNIFTY': {'spot_price': 48000 + (random.random() - 0.5) * 50, 'pcr': 0.9 + (random.random() - 0.5) * 0.1, 'rsi': 60 + (random.random() - 0.5) * 10},
            'FINNIFTY': {'spot_price': 21500 + (random.random() - 0.5) * 30, 'pcr': 1.05 + (random.random() - 0.5) * 0.1, 'rsi': 45 + (random.random() - 0.5) * 10}
        }
        return mock_data.get(index_name, {})

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return {}

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

# Initialize session state for data history for all indices
if 'history' not in st.session_state:
    st.session_state.history = {
        'NIFTY 50': [indices_data['NIFTY 50']['base_price']],
        'BANKNIFTY': [indices_data['BANKNIFTY']['base_price']],
        'FINNIFTY': [indices_data['FINNIFTY']['base_price']],
    }

# Update data for all indices
live_data_nifty = fetch_live_data('NIFTY 50')
live_data_banknifty = fetch_live_data('BANKNIFTY')
live_data_finnifty = fetch_live_data('FINNIFTY')

# Update history for all indices
st.session_state.history['NIFTY 50'].append(live_data_nifty.get('spot_price', st.session_state.history['NIFTY 50'][-1]))
st.session_state.history['NIFTY 50'] = st.session_state.history['NIFTY 50'][-50:]

st.session_state.history['BANKNIFTY'].append(live_data_banknifty.get('spot_price', st.session_state.history['BANKNIFTY'][-1]))
st.session_state.history['BANKNIFTY'] = st.session_state.history['BANKNIFTY'][-50:]

st.session_state.history['FINNIFTY'].append(live_data_finnifty.get('spot_price', st.session_state.history['FINNIFTY'][-1]))
st.session_state.history['FINNIFTY'] = st.session_state.history['FINNIFTY'][-50:]
    
# Create three columns for the indices
col1, col2, col3 = st.columns(3)

# --- Function to display a single index dashboard ---
def display_index_dashboard(column, index_name, live_data, history):
    with column:
        # Use a container for a clean, bordered section
        with st.container(border=True):
            st.markdown(f"<h3 style='text-align: center; color: #6C757D; font-size: 24px;'>{index_name}</h3>", unsafe_allow_html=True)
            st.markdown("---")
            
            # Use columns for metrics
            metric_col1, metric_col2 = st.columns(2)
            
            spot_price = live_data.get('spot_price')
            strike_price = round(spot_price / 50) * 50
            
            with metric_col1:
                st.metric("Spot Price", f"₹{spot_price:.2f}")
            with metric_col2:
                st.metric("Strike Price", f"₹{strike_price:.2f}")
            
            st.markdown("---")

            # Trading Signals section
            st.markdown("#### Trading Signals")
            
            # Calculate indicators
            lowest_ema = calculate_ema(history, 3)
            medium_ema = calculate_ema(history, 13)
            longest_ema = calculate_ema(history, 9)

            # EMA Crossover Signal Logic
            ema_signal = 'Sideways'
            if lowest_ema and medium_ema and longest_ema:
                if lowest_ema > medium_ema and lowest_ema > longest_ema:
                    ema_signal = 'Buy (CE)'
                elif lowest_ema < medium_ema and lowest_ema < longest_ema:
                    ema_signal = 'Sell (PE)'

            # PCR and RSI from fetched data
            pcr = live_data.get('pcr')
            pcr_signal = 'Neutral'
            if pcr > 1.1:
                pcr_signal = 'Bullish'
            elif pcr < 0.9:
                pcr_signal = 'Bearish'
            
            rsi = live_data.get('rsi')
            rsi_signal = 'Neutral'
            if rsi > 70:
                rsi_signal = 'Overbought'
            elif rsi < 30:
                rsi_signal = 'Oversold'
            
            # Helper function to get the correct color for the signal boxes
            def get_signal_box_style(signal):
                if 'Buy' in signal or 'Bullish' in signal:
                    return "background-color: #d4edda; color: #155724; border-radius: 5px; padding: 10px; text-align: center; font-weight: bold;"
                elif 'Sell' in signal or 'Bearish' in signal:
                    return "background-color: #f8d7da; color: #721c24; border-radius: 5px; padding: 10px; text-align: center; font-weight: bold;"
                elif 'Overbought' in signal or 'Oversold' in signal:
                    return "background-color: #fff3cd; color: #856404; border-radius: 5px; padding: 10px; text-align: center; font-weight: bold;"
                else:
                    return "background-color: #e2e3e5; color: #495057; border-radius: 5px; padding: 10px; text-align: center; font-weight: bold;"
            
            st.markdown(f"**EMA**")
            st.markdown(f"<div style='{get_signal_box_style(ema_signal)}'>{ema_signal}</div>", unsafe_allow_html=True)
            
            st.markdown("---")

            st.markdown(f"**PCR**")
            st.markdown(f"<div style='{get_signal_box_style(pcr_signal)}'>{pcr_signal}</div>", unsafe_allow_html=True)

            st.markdown("---")

            st.markdown(f"**RSI**")
            st.markdown(f"<div style='{get_signal_box_style(rsi_signal)}'>{rsi_signal}</div>", unsafe_allow_html=True)


# Display each index in its own column
display_index_dashboard(col1, 'NIFTY 50', live_data_nifty, st.session_state.history['NIFTY 50'])
display_index_dashboard(col2, 'BANKNIFTY', live_data_banknifty, st.session_state.history['BANKNIFTY'])
display_index_dashboard(col3, 'FINNIFTY', live_data_finnifty, st.session_state.history['FINNIFTY'])

# Add a rerun at the end to keep the app live-updating.
time.sleep(2)
st.rerun()
