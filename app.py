import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# --- CONFIG ---
REFRESH_RATE = 15  # seconds
st.set_page_config(page_title="Decay + Directional Bias", layout="wide")

# Inject meta refresh tag
st.markdown(f"<meta http-equiv='refresh' content='{REFRESH_RATE}'>", unsafe_allow_html=True)

# --- NSE Fetch ---
NSE_OC_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_option_chain():
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        resp = session.get(NSE_OC_URL, timeout=5)
        data = resp.json()
        return data["records"]["data"], data["records"]["underlyingValue"]
    except Exception as e:
        st.error(f"❌ Fetch error: {e}")
        return [], None

def bias_label(ce_theta, pe_theta):
    score = ce_theta - pe_theta
    if score > 0:
        return "🟢 Call Bias"
    elif score < 0:
        return "🔴 Put Bias"
    else:
        return "🟡 Neutral"

def detect_decay(oc_data, underlying):
    atm_strikes = [d for d in oc_data if abs(d["strikePrice"] - underlying) <= 100]
    ce_count, pe_count = 0, 0
    details = []

    for strike_data in atm_strikes:
        CE = strike_data.get("CE")
        PE = strike_data.get("PE")
        if CE and PE:
            ce_theta = CE.get("theta", 0)
            pe_theta = PE.get("theta", 0)
            ce_chg = CE.get("change", 0)
            pe_chg = PE.get("change", 0)
            ce_oi = CE.get("openInterest", 0)
            pe_oi = PE.get("openInterest", 0)

            if abs(ce_theta) > abs(pe_theta) and ce_chg < 0 and ce_oi > 0:
                side = "CE"
                ce_count += 1
            elif abs(pe_theta) > abs(ce_theta) and pe_chg < 0 and pe_oi > 0:
                side = "PE"
                pe_count += 1
            else:
                side = "Both"

            details.append({
                "strikePrice": strike_data["strikePrice"],
                "CE_theta": ce_theta,
                "PE_theta": pe_theta,
                "decay_side": side,
                "bias": bias_label(ce_theta, pe_theta)
            })

    if ce_count > pe_count:
        decay_side = "CE Decay Active"
    elif pe_count > ce_count:
        decay_side = "PE Decay Active"
    else:
        decay_side = "Both Sides Decay"

    return decay_side, pd.DataFrame(details)

# --- MAIN ---
st.title("📊 Decay + Directional Bias Detector (Live)")

oc_data, underlying = fetch_option_chain()

if oc_data and underlying:
    decay_side, df = detect_decay(oc_data, underlying)
    st.subheader(f"Underlying: {underlying}")
    st.metric("Decay Side", decay_side)
    st.dataframe(df)
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
else:
    st.info("No data available. Waiting for next refresh...")
