import streamlit as st

# =========================
# 1️⃣ CONFIG & SYMBOLS
# =========================
st.set_page_config(page_title="Market Dashboard", layout="wide")

symbols = [
    {"name": "NIFTY", "oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    {"name": "BANKNIFTY", "oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    {"name": "SENSEX", "oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}
]

# =========================
# 2️⃣ DATA FUNCTIONS
# =========================
def get_ema_trend(symbol_name: str):
    """
    Replace this with your EMA calculation logic.
    Should return a string like 'Bullish', 'Bearish', or 'Sideways'.
    """
    # Example placeholder:
    return "Bullish"

def get_pcr_atm_sr(symbol: str):
    """
    Replace this with your PCR + ATM Strike + Support/Resistance logic.
    Should return: (pcr_value, spot_price, atm_strike, support, resistance)
    """
    # Example placeholder:
    return 1.2, 19850, 19850, 19700, 20000

def interpret_pcr(pcr_value: float):
    """
    Interpret PCR value into a trend signal.
    """
    if pcr_value > 1.3:
        return "Bullish"
    elif pcr_value < 0.7:
        return "Bearish"
    else:
        return "Sideways"

# =========================
# 3️⃣ UI LAYOUT
# =========================
st.title("📊 Market Strategy Dashboard")

for sym in symbols:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(sym['name'])

    with col2:
        # Fetch EMA trend
        ema_trend = get_ema_trend(sym['nse_symbol'])

        # Fetch PCR + ATM + SR
        pcr_value, spot_price, atm_strike, support, resistance = get_pcr_atm_sr(sym['oc_symbol'])
        pcr_trend = interpret_pcr(pcr_value)

        # Display metrics
        st.markdown(f"**EMA Trend:** {ema_trend}")
        st.markdown(f"**PCR Value:** {pcr_value} → {pcr_trend}")
        st.markdown(f"**Spot Price:** {spot_price}")
        st.markdown(f"**ATM Strike:** {atm_strike}")
        st.markdown(f"**Support:** {support}")
        st.markdown(f"**Resistance:** {resistance}")

    st.markdown("---")
