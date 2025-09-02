import streamlit as st
from nse_scrap import Nse  # tumhara diya hua NSE scraper module

# =========================
# 1️⃣ CONFIG & SYMBOLS
# =========================
st.set_page_config(page_title="Market Strategy Dashboard", layout="wide")

symbol_map = {
    "NIFTY": {"oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    "BANKNIFTY": {"oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    "SENSEX": {"oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}
}

# NSE scraper init
nse = Nse()

# =========================
# 2️⃣ DATA FETCHING
# =========================
def get_spot_price(symbol_name: str):
    """
    Get live spot/close price using your NSE scrape logic.
    """
    try:
        quote = nse.get_index_quote(symbol_name)
        return quote['lastPrice']
    except Exception as e:
        st.error(f"Price fetch error for {symbol_name}: {e}")
        return None

def get_ema_trend(symbol_name: str):
    """
    Tumhara EMA calculation logic yahan lagao.
    Abhi placeholder hai.
    """
    return "Bullish"

def get_pcr_atm_sr(symbol: str):
    """
    Tumhara PCR + ATM Strike + Support/Resistance logic yahan lagao.
    Abhi placeholder hai.
    """
    return 1.2, 19850, 19850, 19700, 20000

def interpret_pcr(pcr_value: float):
    """
    PCR value ko interpret karke trend return kare.
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

for key, sym in symbol_map.items():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(key)

    with col2:
        # Spot Price from nse_scrap
        spot_price = get_spot_price(sym['nse_symbol'])

        # EMA Trend
        ema_trend = get_ema_trend(sym['nse_symbol'])

        # PCR + ATM + SR
        if sym['oc_symbol']:
            pcr_value, spot_from_pcr, atm_strike, support, resistance = get_pcr_atm_sr(sym['oc_symbol'])
        else:
            pcr_value, spot_from_pcr, atm_strike, support, resistance = None, None, None, None, None

        pcr_trend = interpret_pcr(pcr_value) if pcr_value is not None else "N/A"

        # Display metrics
        st.markdown(f"**Spot Price:** {spot_price}")
        st.markdown(f"**EMA Trend:** {ema_trend}")
        st.markdown(f"**PCR Value:** {pcr_value if pcr_value else 'N/A'} → {pcr_trend}")
        st.markdown(f"**ATM Strike:** {atm_strike if atm_strike else 'N/A'}")
        st.markdown(f"**Support:** {support if support else 'N/A'}")
        st.markdown(f"**Resistance:** {resistance if resistance else 'N/A'}")

    st.markdown("---")
