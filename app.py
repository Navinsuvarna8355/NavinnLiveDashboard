import streamlit as st

def metric_badge(label, value, color):
    st.markdown(
        f"""
        <div style="display:inline-block; padding:6px 12px; border-radius:8px; background-color:{color}; color:white; font-weight:bold; margin:2px;">
            {label}: {value}
        </div>
        """,
        unsafe_allow_html=True
    )

st.set_page_config(page_title="Live NSE Dashboard", layout="wide")
st.title("📊 Live NSE EMA, PCR, Spot, ATM, Support & Resistance")

for sym in symbols:
    ema_trend = get_ema_trend(sym['nse_symbol'])
    pcr_value, spot_price, atm_strike, support, resistance = get_pcr_atm_sr(sym['oc_symbol'])
    pcr_trend = interpret_pcr(pcr_value) if pcr_value is not None else None

    with st.container():
        st.markdown(f"### {sym['name']}")
        col1, col2 = st.columns([1,4])
        
        with col1:
            # Trend badges
            if ema_trend:
                metric_badge("EMA", ema_trend, "#28a745" if ema_trend=="Bullish" else "#dc3545" if ema_trend=="Bearish" else "#ffc107")
            if pcr_trend:
                metric_badge("PCR", pcr_trend, "#28a745" if pcr_trend=="Bullish" else "#dc3545" if pcr_trend=="Bearish" else "#ffc107")
        
        with col2:
            # Numeric metrics
            st.markdown(
                f"""
                <div style="display:flex; gap:20px; font-size:16px;">
                    <div>📈 PCR Value: <b>{pcr_value:.2f if pcr_value else '--'}</b></div>
                    <div>💹 Spot: <b>{spot_price if spot_price else '--'}</b></div>
                    <div>🎯 ATM: <b>{atm_strike if atm_strike else '--'}</b></div>
                    <div>🛡 Support: <b>{support if support else '--'}</b></div>
                    <div>🚀 Resistance: <b>{resistance if resistance else '--'}</b></div>
                </div>
                """,
                unsafe_allow_html=True
            )
