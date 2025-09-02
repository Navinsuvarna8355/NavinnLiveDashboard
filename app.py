import streamlit as st
import requests

# =========================
# CONFIG & SYMBOLS
# =========================
st.set_page_config(page_title="Market Strategy Dashboard", layout="wide")

symbol_map = {
    "NIFTY": {"oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    "BANKNIFTY": {"oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    "SENSEX": {"oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}
}

# Your proxy API base URL
PROXY_URL = "https://my-nse-proxy.onrender.com"

# =========================
# DATA FUNCTIONS
# =========================
def get_spot_price(symbol_name: str):
    try:
        r = requests.get(f"{PROXY_URL}/price/{symbol_name}", timeout=5)
        data = r.json()
        return data.get("lastPrice")
    except Exception as e:
        st.error(f"Price fetch error for {symbol_name}: {e}")
        return None

def get_ema_trend(symbol_name: str):
    # TODO: Replace with your EMA calculation logic
    return "Bullish"

def get_pcr_atm_sr(symbol: str):
    # TODO: Replace with your PCR + ATM Strike + Support/Resistance logic
    return 1.24, 19850, 19850, 19700, 20000

def interpret_pcr(pcr_value: float):
    if pcr_value is None:
        return "N/A"
    if pcr_value > 1.3:
        return "Bullish"
    elif pcr_value < 0.7:
        return "Bearish"
    else:
        return "Sideways"

# =========================
# UI LAYOUT
# =========================
st.title("📊 Market Strategy Dashboard")

for key, sym in symbol_map.items():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(key)

    with col2:
        spot_price = get_spot_price(sym['nse_symbol'])
        ema_trend = get_ema_trend(sym['nse_symbol'])

        if sym['oc_symbol']:
            pcr_value, spot_from_pcr, atm_strike, support, resistance = get_pcr_atm_sr(sym['oc_symbol'])
        else:
            pcr_value, spot_from_pcr, atm_strike, support, resistance = None, None, None, None, None

        pcr_trend = interpret_pcr(pcr_value)

        st.markdown(f"**Spot Price:** {spot_price}")
        st.markdown(f"**EMA Trend:** {ema_trend}")
        st.markdown(f"**PCR Value:** {pcr_value if pcr_value else 'N/A'} → {pcr_trend}")
        st.markdown(f"**ATM Strike:** {atm_strike if atm_strike else 'N/A'}")
        st.markdown(f"**Support:** {support if support else 'N/A'}")
        st.markdown(f"**Resistance:** {resistance if resistance else 'N/A'}")

    st.markdown("---")
