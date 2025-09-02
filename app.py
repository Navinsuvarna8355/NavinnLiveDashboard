import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="📈 Bank Nifty Signals", layout="wide")
st.title("📊 Bank Nifty Option Chain — NSE API")

# NSE endpoint
NSE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
}

@st.cache_data(ttl=300)
def fetch_option_chain():
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=HEADERS)
    response = session.get(NSE_URL, headers=HEADERS)
    data = response.json()
    return pd.DataFrame(data["records"]["data"])

def extract_signals(df):
    ce_data = []
    pe_data = []
    for row in df.itertuples():
        strike = row.strikePrice
        ce = row.CE if hasattr(row, "CE") else None
        pe = row.PE if hasattr(row, "PE") else None
        if ce:
            ce_data.append([strike, ce["openInterest"], ce["changeinOpenInterest"]])
        if pe:
            pe_data.append([strike, pe["openInterest"], pe["changeinOpenInterest"]])
    ce_df = pd.DataFrame(ce_data, columns=["Strike", "CE_OI", "CE_Change"])
    pe_df = pd.DataFrame(pe_data, columns=["Strike", "PE_OI", "PE_Change"])
    return ce_df, pe_df

df = fetch_option_chain()
ce_df, pe_df = extract_signals(df)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📘 Call Options (CE)")
    st.dataframe(ce_df.sort_values("CE_Change", ascending=False).head(10), use_container_width=True)

with col2:
    st.subheader("📕 Put Options (PE)")
    st.dataframe(pe_df.sort_values("PE_Change", ascending=False).head(10), use_container_width=True)

