import streamlit as st
import requests
from datetime import datetime

# =========================
# 1️⃣ NSE SCRAPER (embedded)
# =========================
class Nse:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        })

    def get_index_quote(self, symbol_name: str):
        """
        Fetch index quote from NSE India.
        symbol_name examples: 'NIFTY 50', 'NIFTY BANK', 'S&P BSE SENSEX'
        """
        try:
            url = f"https://www.nseindia.com/api/equity-stockIndices?index={symbol_name}"
            r = self.session.get(url, timeout=5)
            data = r.json()
            # NSE returns a list of data points; find matching symbol
            for item in data.get("data", []):
                if item.get("index") == symbol_name:
                    return {"lastPrice": item.get("lastPrice")}
            return {"lastPrice": None}
        except Exception as e:
            raise RuntimeError(f"NSE fetch error: {e}")

# Init scraper
nse = Nse()

# =========================
# 2️⃣ CONFIG & SYMBOLS
# =========================
st.set_page_config(page_title="Market Strategy Dashboard", layout="wide")

symbol_map = {
    "NIFTY": {"oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    "BANKNIFTY": {"oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    "SENSEX": {"oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}
}

# =========================
# 3️⃣ DATA FUNCTIONS
# =========================
def get_spot_price(symbol_name: str):
    try:
        quote = nse.get_index_quote(symbol_name)
        return quote['lastPrice']
    except Exception as e:
        st.error(f"Price fetch error for {symbol_name}: {e}")
        return None

def get_ema_trend(symbol_name: str):
    # TODO: Replace with your EMA calculation logic
    return "Bullish"

def get_pcr_atm_sr(symbol: str):
    # TODO: Replace with your PCR + ATM Strike + Support/Resistance logic
    return 1.2, 19850, 19850, 19700, 20000

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
# 4️⃣ UI LAYOUT
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
