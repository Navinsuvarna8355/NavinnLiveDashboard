import requests
import json
import pandas as pd
import talib
import streamlit as st

# --------------------
# Config
# --------------------
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

symbols = [
    {"name": "NIFTY", "oc_symbol": "NIFTY"},
    {"name": "BANKNIFTY", "oc_symbol": "BANKNIFTY"},
    {"name": "SENSEX", "oc_symbol": None}  # No NSE option chain
]

# --------------------
# Functions
# --------------------
def get_pcr(symbol):
    """Fetch PCR from NSE option chain"""
    if not symbol:
        return None
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    session = requests.Session()
    session.get("https://www.nseindia.com/option-chain", headers=headers)
    response = session.get(url, headers=headers)
    data = json.loads(response.text)
    expiry_dates = data["records"]["expiryDates"]
    current_expiry = expiry_dates[0]
    total_ce_oi = total_pe_oi = 0
    for item in data['records']['data']:
        if item["expiryDate"] == current_expiry:
            total_ce_oi += item.get("CE", {}).get("openInterest", 0)
            total_pe_oi += item.get("PE", {}).get("openInterest", 0)
    return total_pe_oi / total_ce_oi if total_ce_oi else None

def get_ema_trend(csv_file):
    """Calculate EMA trend from OHLC CSV"""
    df = pd.read_csv(csv_file)
    df['EMA10'] = talib.EMA(df['close'], timeperiod=10)
    df['EMA25'] = talib.EMA(df['close'], timeperiod=25)
    df['EMA50'] = talib.EMA(df['close'], timeperiod=50)
    latest = df.iloc[-1]
    if latest['EMA10'] > latest['EMA25'] and latest['EMA10'] > latest['EMA50']:
        return "Bullish"
    elif latest['EMA10'] < latest['EMA25'] and latest['EMA10'] < latest['EMA50']:
        return "Bearish"
    else:
        return "Sideways"

def interpret_pcr(pcr):
    """Interpret PCR value"""
    if pcr > 1.3:
        return "Bullish"
    elif pcr < 0.7:
        return "Bearish"
    else:
        return "Sideways"

def color_for_trend(trend):
    """Return color for trend"""
    if trend == "Bullish":
        return "🟢"
    elif trend == "Bearish":
        return "🔴"
    else:
        return "🟡"

# --------------------
# Streamlit UI
# --------------------
st.set_page_config(page_title="Multi-Index EMA & PCR Dashboard", layout="wide")
st.title("📊 Multi-Index EMA & PCR Dashboard")

for sym in symbols:
    ema_trend = get_ema_trend(f"{sym['name']}_price.csv")
    pcr_value = get_pcr(sym['oc_symbol'])
    pcr_trend = interpret_pcr(pcr_value) if pcr_value is not None else None
    
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.subheader(sym['name'])
    with col2:
        st.metric("EMA Trend", f"{color_for_trend(ema_trend)} {ema_trend}")
    with col3:
        if pcr_value is not None:
            st.metric("PCR Value", f"{pcr_value:.2f}")
        else:
            st.write("—")
    with col4:
        if pcr_trend:
            st.metric("PCR Trend", f"{color_for_trend(pcr_trend)} {pcr_trend}")
        else:
            st.write("—")

st.caption("Data updates when you refresh the page.")
