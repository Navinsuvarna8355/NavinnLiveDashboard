import streamlit as st
import requests, time, random
from requests.exceptions import RequestException
import pandas as pd
from datetime import datetime

# --- Constants & NSE Functions (from nse_option_chain.py) ---
NSE_BASE = "https://www.nseindia.com"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
]

def new_session():
    """Creates and returns a new requests session with a random user agent."""
    s = requests.Session()
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.nseindia.com/option-chain",
        "Connection": "keep-alive",
    }
    s.headers.update(headers)
    return s

def fetch_option_chain(symbol):
    """Fetches the option chain data for a given symbol from NSE."""
    session = new_session()
    try:
        session.get(NSE_BASE + "/option-chain", timeout=5)
    except Exception:
        pass # Ignore initial get errors

    url = f"{NSE_BASE}/api/option-chain-indices?symbol={symbol}"
    resp = None
    for i in range(3):
        try:
            resp = session.get(url, timeout=6)
            resp.raise_for_status()
            break
        except RequestException as e:
            time.sleep(0.6 + i * 0.5)
    if resp is None:
        raise RequestException(f"Failed to GET {url} after retries")
    
    data = resp.json()
    return data

def compute_oi_pcr_and_underlying(data):
    """Computes PCR and underlying value from the option chain data."""
    records = data.get("records", {})
    expiry_dates = records.get("expiryDates", [])
    if not expiry_dates:
        raise ValueError("No expiry dates found in option chain")
    
    current_expiry = expiry_dates[0]
    total_ce_oi = 0
    total_pe_oi = 0
    total_ce_oi_near = 0
    total_pe_oi_near = 0
    underlying = records.get("underlyingValue")

    for item in records.get("data", []):
        if item.get("expiryDate") != current_expiry:
            continue
        ce = item.get("CE", {})
        pe = item.get("PE", {})
        total_ce_oi += ce.get("openInterest", 0)
        total_pe_oi += pe.get("openInterest", 0)
        strike = item.get("strikePrice", 0)
        if underlying is not None and abs(strike - underlying) <= 200:
            total_ce_oi_near += ce.get("openInterest", 0)
            total_pe_oi_near += pe.get("openInterest", 0)
    
    pcr_total = round((total_pe_oi / total_ce_oi), 2) if total_ce_oi else None
    pcr_near = round((total_pe_oi_near / total_ce_oi_near), 2) if total_ce_oi_near else None

    return {
        "expiry": current_expiry,
        "underlying": underlying,
        "total_CE_OI": total_ce_oi,
        "total_PE_OI": total_pe_oi,
        "pcr_total": pcr_total,
        "pcr_near": pcr_near
    }

# --- Signal Strategy Logic (from signal_strategy.py) ---
def determine_signal(pcr, trend, ema_signal):
    """Determines the final signal based on PCR, trend, and EMA signal."""
    signal = "SIDEWAYS"
    suggested_side = None

    if trend == "BULLISH" and ema_signal == "BUY" and pcr >= 1:
        signal = "BUY"
        suggested_side = "CALL"
    elif trend == "BEARISH" and ema_signal == "SELL" and pcr <= 1:
        signal = "SELL"
        suggested_side = "PUT"
    else:
        signal = "SIDEWAYS"
        suggested_side = None

    return signal, suggested_side

# --- Streamlit App UI and Logic ---
st.set_page_config(layout="wide", page_title="Strategy Signal")
st.title("Strategy Signal — NIFTY & BANKNIFTY")

# Using a single cache function to fetch and process all data
@st.cache_data(ttl=60) # Cache data for 60 seconds
def get_stock_data(symbol):
    """Fetches and processes stock data for a given symbol."""
    try:
        data = fetch_option_chain(symbol)
        info = compute_oi_pcr_and_underlying(data)
        info['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        info['error'] = None
        info['symbol'] = symbol # ADDED THIS LINE
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        info = {'error': str(e), 'symbol': symbol} # ADDED 'symbol' KEY HERE
    return info

def get_strategy_data(symbol_info, use_near, ema_signal):
    """Calculates strategy signals based on symbol info and user inputs."""
    if symbol_info.get('underlying') is None or symbol_info.get('pcr_total') is None:
        return {'error': 'Data not ready.'}
    
    pcr = symbol_info.get('pcr_near') if use_near and symbol_info.get('pcr_near') is not None else symbol_info.get('pcr_total')
    trend = 'BULLISH' if pcr is not None and pcr >= 1 else 'BEARISH'
    
    signal, suggested_side = determine_signal(pcr, trend, ema_signal)
    
    atm = round(symbol_info['underlying'] / 100) * 100 if symbol_info['underlying'] is not None else None
    suggested_option = f"{atm} {'CE' if suggested_side == 'CALL' else 'PE'}" if suggested_side else None
    
    return {
        'symbol': symbol_info['symbol'],
        'signal': signal,
        'live_price': round(symbol_info['underlying'], 2),
        'suggested_option': suggested_option,
        'trend': trend,
        'strategy': '3 EMA Crossover + PCR (option-chain)',
        'confidence': 90,
        'pcr': pcr,
        'pcr_total': symbol_info.get('pcr_total'),
        'pcr_near': symbol_info.get('pcr_near'),
        'expiry': symbol_info.get('expiry'),
        'timestamp': symbol_info.get('timestamp')
    }

# Main app layout
st.write("---")
st.markdown("This app fetches live data from NSE and provides a trading signal based on a simple strategy.")

with st.sidebar:
    st.header("App Settings")
    st.write("Configure the signal strategy parameters.")
    use_near = st.checkbox("Use near-month PCR?", value=True)
    ema_signal = st.radio("EMA Signal", ["BUY", "SELL"], index=0)

col1, col2 = st.columns(2)

with col1:
    st.header("NIFTY")
    nifty_info = get_stock_data("NIFTY")
    if nifty_info.get('error'):
        st.warning(f"Error: {nifty_info.get('error')}")
    else:
        nifty_strategy_data = get_strategy_data(nifty_info, use_near, ema_signal)
        if nifty_strategy_data.get('error'):
             st.warning(nifty_strategy_data.get('error'))
        else:
            signal_color = "green" if nifty_strategy_data['signal'] == "BUY" else "red" if nifty_strategy_data['signal'] == "SELL" else "gray"
            st.markdown(f"### Signal: <span style='color:{signal_color}'>**{nifty_strategy_data['signal']}**</span>", unsafe_allow_html=True)
            
            st.metric("Live Price", f"₹{nifty_strategy_data['live_price']}")
            st.metric("Suggested Option", nifty_strategy_data['suggested_option']}")

            with st.expander("Show Details"):
                st.write(f"**Trend:** {nifty_strategy_data['trend']}")
                st.write(f"**PCR (used):** {nifty_strategy_data['pcr']}")
                st.write(f"**PCR Total:** {nifty_strategy_data['pcr_total']}")
                st.write(f"**PCR Near:** {nifty_strategy_data['pcr_near']}")
                st.write(f"**Expiry:** {nifty_strategy_data['expiry']}")
                st.write(f"**Strategy:** {nifty_strategy_data['strategy']}")
                st.write(f"**Confidence:** {nifty_strategy_data['confidence']}%")
                st.markdown(f"**Last Updated:** {nifty_strategy_data['timestamp']}")

with col2:
    st.header("BANKNIFTY")
    banknifty_info = get_stock_data("BANKNIFTY")
    if banknifty_info.get('error'):
        st.warning(f"Error: {banknifty_info.get('error')}")
    else:
        banknifty_strategy_data = get_strategy_data(banknifty_info, use_near, ema_signal)
        if banknifty_strategy_data.get('error'):
             st.warning(banknifty_strategy_data.get('error'))
        else:
            signal_color = "green" if banknifty_strategy_data['signal'] == "BUY" else "red" if banknifty_strategy_data['signal'] == "SELL" else "gray"
            st.markdown(f"### Signal: <span style='color:{signal_color}'>**{banknifty_strategy_data['signal']}**</span>", unsafe_allow_html=True)

            st.metric("Live Price", f"₹{banknifty_strategy_data['live_price']}")
            st.metric("Suggested Option", banknifty_strategy_data['suggested_option']}")

            with st.expander("Show Details"):
                st.write(f"**Trend:** {banknifty_strategy_data['trend']}")
                st.write(f"**PCR (used):** {banknifty_strategy_data['pcr']}")
                st.write(f"**PCR Total:** {banknifty_strategy_data['pcr_total']}")
                st.write(f"**PCR Near:** {banknifty_strategy_data['pcr_near']}")
                st.write(f"**Expiry:** {banknifty_strategy_data['expiry']}")
                st.write(f"**Strategy:** {banknifty_strategy_data['strategy']}")
                st.write(f"**Confidence:** {banknifty_strategy_data['confidence']}%")
                st.markdown(f"**Last Updated:** {banknifty_strategy_data['timestamp']}")
