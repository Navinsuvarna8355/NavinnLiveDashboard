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
    {"name": "NIFTY", "oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    {"name": "BANKNIFTY", "oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    {"name": "SENSEX", "oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}  # No NSE option chain
]

# --------------------
# Fetch OHLC from NSE
# --------------------
def get_nse_ohlc(symbol_name):
    session = requests.Session()
    # Step 1: Get cookies
    session.get("https://www.nseindia.com", headers=headers)
    
    # Step 2: Hit chart API
    chart_url = f"https://www.nseindia.com/api/chart-databyindex?index={symbol_name.replace(' ', '%20')}&indices=true"
    rc = session.get(chart_url, headers=headers)

    # Step 3: Safe JSON parse
    try:
        chart_data = rc.json()
    except json.JSONDecodeError:
        st.warning(f"{symbol_name}: Market closed or data unavailable")
        return pd.DataFrame()

    # Step 4: Extract candles
    candles = chart_data.get('grapthData', [])
    if not candles:
        st.warning(f"{symbol_name}: No candle data")
        return pd.DataFrame()

    df = pd.DataFrame(candles, columns=["timestamp", "close"])
    df['close'] = df['close'].astype(float)
    return df

# --------------------
# EMA Trend
# --------------------
def get_ema_trend(symbol_name):
    df = get_nse_ohlc(symbol_name)
    if df.empty:
        return None
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

# --------------------
# PCR from NSE Option Chain
# --------------------
def get_pcr(symbol):
    if not symbol:
        return None
    session = requests.Session()
    session.get("https://www.nseindia.com/option-chain", headers=headers)
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    response = session.get(url, headers=headers)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        st.warning(f"{symbol}: PCR data unavailable")
        return None

    expiry_dates = data.get("records", {}).get("expiryDates", [])
    if not expiry_dates:
        return None
    current_expiry = expiry_dates[0]
    total_ce_oi = total_pe_oi = 0
    for item in data['records']['data']:
        if item["expiryDate"] == current_expiry:
            total_ce_oi += item.get("CE", {}).get("openInterest", 0)
            total_pe_oi += item.get("PE", {}).get("openInterest", 0)
    return total_pe_oi / total_ce_oi if total_ce_oi else None

# --------------------
# PCR Interpretation
# --------------------
def interpret_pcr(pcr):
    if pcr > 1.3:
        return "Bullish"
    elif pcr < 0.7:
        return "Bearish"
    else:
        return "Sideways"

# --------------------
# Color for Trend
# --------------------
def color_for_trend(trend):
    if trend == "Bullish":
        return "🟢"
    elif trend == "Bearish":
        return "🔴"
    else:
        return "🟡"

# --------------------
# Streamlit UI
# --------------------
st.set_page_config(page_title="Live NSE EMA & PCR Dashboard", layout="wide")
st.title("📊 Live NSE EMA & PCR Dashboard")

for sym in symbols:
    ema_trend = get_ema_trend(sym['nse_symbol'])
    pcr_value = get_pcr(sym['oc_symbol'])
    pcr_trend = interpret_pcr(pcr_value) if pcr_value is not None else None
    
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.subheader(sym['name'])
    with col2:
        if ema_trend:
            st.metric("EMA Trend", f"{color_for_trend(ema_trend)} {ema_trend}")
        else:
            st.write("—")
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

st.caption("🔄 Market closed hone par EMA/PCR unavailable ho sakta hai. Market hours me refresh karke dekhein.")
