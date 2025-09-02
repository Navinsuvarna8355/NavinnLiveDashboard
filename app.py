import requests
import json
import pandas as pd
import talib
import streamlit as st

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

symbols = [
    {"name": "NIFTY", "oc_symbol": "NIFTY", "nse_symbol": "NIFTY 50"},
    {"name": "BANKNIFTY", "oc_symbol": "BANKNIFTY", "nse_symbol": "NIFTY BANK"},
    {"name": "SENSEX", "oc_symbol": None, "nse_symbol": "S&P BSE SENSEX"}
]

def get_nse_ohlc(symbol_name):
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    chart_url = f"https://www.nseindia.com/api/chart-databyindex?index={symbol_name.replace(' ', '%20')}&indices=true"
    rc = session.get(chart_url, headers=headers)
    try:
        chart_data = rc.json()
    except json.JSONDecodeError:
        return pd.DataFrame()
    candles = chart_data.get('grapthData', [])
    if not candles:
        return pd.DataFrame()
    df = pd.DataFrame(candles, columns=["timestamp", "close"])
    df['close'] = df['close'].astype(float)
    return df

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

def get_pcr_atm_sr(symbol):
    if not symbol:
        return None, None, None, None, None
    session = requests.Session()
    session.get("https://www.nseindia.com/option-chain", headers=headers)
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    response = session.get(url, headers=headers)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        return None, None, None, None, None

    spot_price = data.get("records", {}).get("underlyingValue", None)
    expiry_dates = data.get("records", {}).get("expiryDates", [])
    if not expiry_dates:
        return None, spot_price, None, None, None
    current_expiry = expiry_dates[0]

    total_ce_oi = total_pe_oi = 0
    strikes = []
    ce_oi_map = {}
    pe_oi_map = {}

    for item in data['records']['data']:
        if item["expiryDate"] == current_expiry:
            strike = item.get("strikePrice")
            strikes.append(strike)
            ce_oi = item.get("CE", {}).get("openInterest", 0)
            pe_oi = item.get("PE", {}).get("openInterest", 0)
            total_ce_oi += ce_oi
            total_pe_oi += pe_oi
            ce_oi_map[strike] = ce_oi
            pe_oi_map[strike] = pe_oi

    pcr = total_pe_oi / total_ce_oi if total_ce_oi else None
    atm_strike = min(strikes, key=lambda x: abs(x - spot_price)) if spot_price and strikes else None

    # Resistance = CE OI max
    resistance = max(ce_oi_map, key=ce_oi_map.get) if ce_oi_map else None
    # Support = PE OI max
    support = max(pe_oi_map, key=pe_oi_map.get) if pe_oi_map else None

    return pcr, spot_price, atm_strike, support, resistance

def interpret_pcr(pcr):
    if pcr is None:
        return None
    if pcr > 1.3:
        return "Bullish"
    elif pcr < 0.7:
        return "Bearish"
    else:
        return "Sideways"

def color_for_trend(trend):
    if trend == "Bullish":
        return "🟢"
    elif trend == "Bearish":
        return "🔴"
    else:
        return "🟡"

st.set_page_config(page_title="Live NSE EMA, PCR, Spot, ATM, S/R Dashboard", layout="wide")
st.title("📊 Live NSE EMA, PCR, Spot, ATM, Support & Resistance Dashboard")

for sym in symbols:
    ema_trend = get_ema_trend(sym['nse_symbol'])
    pcr_value, spot_price, atm_strike, support, resistance = get_pcr_atm_sr(sym['oc_symbol'])
    pcr_trend = interpret_pcr(pcr_value) if pcr_value is not None else None
    
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1,1,1,1,1,1,1,1])
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
    with col5:
        if spot_price:
            st.metric("Spot Price", f"{spot_price:.2f}")
        else:
            st.write("—")
    with col6:
        if atm_strike:
            st.metric("ATM Strike", f"{atm_strike}")
        else:
            st.write("—")
    with col7:
        if support:
            st.metric("Support", f"{support}")
        else:
            st.write("—")
    with col8:
        if resistance:
            st.metric("Resistance", f"{resistance}")
        else:
            st.write("—")

st.caption("🔄 Market closed hone par EMA/PCR/Spot/ATM/SR unavailable ho sakta hai. Market hours me refresh karke dekhein.")
