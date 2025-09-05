import streamlit as st
import pandas as pd

# --- Decay Detection Logic ---
def detect_decay(oc_data, underlying, decay_range=150):
    atm_strikes = [
        d for d in oc_data
        if abs(d["strikePrice"] - underlying) <= decay_range and "CE" in d and "PE" in d
    ]

    details = []

    for strike_data in atm_strikes:
        ce_data = strike_data["CE"]
        pe_data = strike_data["PE"]

        ce_theta = ce_data.get("theta", 0)
        pe_theta = pe_data.get("theta", 0)
        ce_chg = ce_data.get("change", 0)
        pe_chg = pe_data.get("change", 0)

        decay_side = "Both"

        if ce_theta != 0 and pe_theta != 0:
            if abs(ce_theta) > abs(pe_theta) and ce_chg < 0:
                decay_side = "CE"
            elif abs(pe_theta) > abs(ce_theta) and pe_chg < 0:
                decay_side = "PE"
        elif ce_chg < 0 and pe_chg < 0:
            if abs(ce_chg) > abs(pe_chg):
                decay_side = "CE"
            elif abs(pe_chg) > abs(ce_chg):
                decay_side = "PE"

        details.append({
            "strikePrice": strike_data["strikePrice"],
            "CE_theta": ce_theta,
            "PE_theta": pe_theta,
            "CE_Change": ce_chg,
            "PE_Change": pe_chg,
            "Decay_Side": decay_side
        })

    df = pd.DataFrame(details).sort_values(by="strikePrice")

    ce_count = df[df['Decay_Side'] == 'CE'].shape[0]
    pe_count = df[df['Decay_Side'] == 'PE'].shape[0]

    overall_decay_side = "Both Sides Decay"
    if ce_count > pe_count:
        overall_decay_side = "CE Decay Active"
    elif pe_count > ce_count:
        overall_decay_side = "PE Decay Active"

    return overall_decay_side, df

# --- Streamlit UI ---
st.set_page_config(page_title="Decay Bias Dashboard", layout="wide")

st.title("📉 Option Decay Bias Detector")

# Simulated input (replace with live API or file upload)
sample_data = [
    {
        "strikePrice": 20000,
        "CE": {"theta": -12.5, "change": -8.2},
        "PE": {"theta": -9.1, "change": -5.4}
    },
    {
        "strikePrice": 20100,
        "CE": {"theta": -10.2, "change": -6.8},
        "PE": {"theta": -11.7, "change": -7.9}
    },
    {
        "strikePrice": 20200,
        "CE": {"theta": -8.5, "change": -4.2},
        "PE": {"theta": -13.1, "change": -9.3}
    }
]

underlying_price = st.number_input("Enter Underlying Price", value=20100)
decay_range = st.slider("Decay Range (±)", min_value=50, max_value=300, value=150, step=10)

if st.button("Analyze Decay"):
    result, df = detect_decay(sample_data, underlying_price, decay_range)
    st.subheader(f"🧠 Decay Bias: {result}")
    st.dataframe(df, use_container_width=True)
