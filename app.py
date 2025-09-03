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
    लाइव बाज़ार डेटा API से वास्तविक डेटा लाने का एक प्लेसहोल्डर फ़ंक्शन।
    आपको अपनी API कुंजी और सही API endpoint के साथ इसे अपडेट करना होगा।
    """
    # यहाँ आपको अपने चुने हुए API का उपयोग करना होगा।
    # उदाहरण के लिए, यह एक काल्पनिक API कॉल है।
    # api_url = f"https://api.yourprovider.com/data?symbol={index_name}"
    # headers = {"Authorization": "Bearer YOUR_API_KEY"}

    try:
        # response = requests.get(api_url, headers=headers)
        # response.raise_for_status()  # अगर अनुरोध असफल हो तो एक HTTPError उठाता है।
        # data = response.json()

        # वास्तविक डेटा के बजाय, हम यहाँ नकली डेटा का उपयोग जारी रखेंगे
        # ताकि ऐप काम करता रहे।
        mock_data = {
            'NIFTY 50': {'spot_price': 22500 + (random.random() - 0.5) * 20, 'pcr': 0.95 + (random.random() - 0.5) * 0.1, 'rsi': 55 + (random.random() - 0.5) * 10},
            'BANKNIFTY': {'spot_price': 48000 + (random.random() - 0.5) * 50, 'pcr': 0.9 + (random.random() - 0.5) * 0.1, 'rsi': 60 + (random.random() - 0.5) * 10},
            'FINNIFTY': {'spot_price': 21500 + (random.random() - 0.5) * 30, 'pcr': 1.05 + (random.random() - 0.5) * 0.1, 'rsi': 45 + (random.random() - 0.5) * 10}
        }
        return mock_data.get(index_name, {})

    except requests.exceptions.RequestException as e:
        st.error(f"API से डेटा लाने में त्रुटि: {e}")
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
            <span style='font-weight:bold; color:#f87171;'>चेतावनी:</span> यह ऐप केवल शैक्षिक उद्देश्यों के लिए है। डेटा नकली है और वास्तविक व्यापारिक निर्णयों के लिए इसका उपयोग नहीं किया जाना चाहिए।
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

# Create three columns for the indices
col1, col2, col3 = st.columns(3)

# The main loop to simulate live data updates
while True:
    # Update data for all indices in each loop
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
    
    # --- Function to display a single index dashboard ---
    def display_index_dashboard(column, index_name, live_data, history):
        with column:
            st.subheader(index_name)
            st.divider()

            # Calculate and display metrics
            spot_price = live_data.get('spot_price')
            strike_price = round(spot_price / 50) * 50
            st.metric("स्पॉट प्राइस", f"₹{spot_price:.2f}")
            st.metric("स्ट्राइक प्राइस", f"₹{strike_price:.2f}")
            
            st.markdown("---")

            # Calculate and display signals
            st.markdown("#### ट्रेडिंग सिग्नल")
            
            # Calculate indicators
            lowest_ema = calculate_ema(history, 3)
            medium_ema = calculate_ema(history, 13)
            longest_ema = calculate_ema(history, 9)

            # EMA Crossover Signal Logic
            ema_signal = 'Sideways'
            if lowest_ema and medium_ema and longest_ema:
                if lowest_ema > medium_ema and lowest_ema > longest_ema:
                    ema_signal = 'खरीदें (CE)'
                elif lowest_ema < medium_ema and lowest_ema < longest_ema:
                    ema_signal = 'बेचें (PE)'

            # PCR and RSI from fetched data
            pcr = live_data.get('pcr')
            pcr_signal = 'तटस्थ'
            if pcr > 1.1:
                pcr_signal = 'बुलिश'
            elif pcr < 0.9:
                pcr_signal = 'बेयरिश'
            
            rsi = live_data.get('rsi')
            rsi_signal = 'तटस्थ'
            if rsi > 70:
                rsi_signal = 'ओवरबॉट'
            elif rsi < 30:
                rsi_signal = 'ओवरसोल्ड'

            def get_signal_color_and_icon(signal):
                if 'खरीदें' in signal or 'बुलिश' in signal:
                    return "green", "▲"
                elif 'बेचें' in signal or 'बेयरिश' in signal:
                    return "red", "▼"
                else:
                    return "orange", "▬"
            
            ema_color, ema_icon = get_signal_color_and_icon(ema_signal)
            pcr_color, pcr_icon = get_signal_color_and_icon(pcr_signal)
            rsi_color, rsi_icon = get_signal_color_and_icon(rsi_signal)

            st.markdown(f"**EMA:** <span style='color:{ema_color}'>{ema_icon} {ema_signal}</span>", unsafe_allow_html=True)
            st.markdown(f"**PCR:** <span style='color:{pcr_color}'>{pcr_icon} {pcr_signal}</span>", unsafe_allow_html=True)
            st.markdown(f"**RSI:** <span style='color:{rsi_color}'>{rsi_icon} {rsi_signal}</span>", unsafe_allow_html=True)


    # Display each index in its own column
    display_index_dashboard(col1, 'NIFTY 50', live_data_nifty, st.session_state.history['NIFTY 50'])
    display_index_dashboard(col2, 'BANKNIFTY', live_data_banknifty, st.session_state.history['BANKNIFTY'])
    display_index_dashboard(col3, 'FINNIFTY', live_data_finnifty, st.session_state.history['FINNIFTY'])

    # Wait for a few seconds before the next update
    time.sleep(2)
