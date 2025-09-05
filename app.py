# app.py

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from streamlit_autorefresh import st_autorefresh
import time

# -----------------
# PAGE CONFIGURATION
st.set_page_config(
    page_title="Decay Bias Dashboard",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="auto"
)

# -----------------
# AUTO-REFRESH (Set to refresh every 15 seconds)
st_autorefresh(interval=15 * 1000, key="refresh_dashboard")

# -----------------
# TIMEZONE & TIMESTAMP (display in IST)
IST = pytz.timezone('Asia/Kolkata')
def now_ist():
    return datetime.now(IST)

def format_ist(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " IST"  # display milliseconds, trim trailing

# -----------------
# PLACEHOLDER: Simulate metric data (replace with your data loading call)
@st.cache_data
def load_demo_data(num_points=200):
    np.random.seed(42)
    time_stamps = pd.date_range(
        end=datetime.now(),
        periods=num_points,
        freq='min'
    ).tz_localize('UTC').tz_convert('Asia/Kolkata')
    base = np.cumsum(np.random.randn(num_points) * 0.15 + 0.1)
    # Inject decay event
    if num_points > 80:
        base[100:120] -= 5   # sudden drop (decay)
    df = pd.DataFrame({'timestamp': time_stamps, 'signal': base})
    return df

# -----------------
# DECAY ALGORITHM (FASD logic)
def compute_decay(series, alpha=0.9):
    decay = np.zeros_like(series)
    decay[0] = series[0]
    for i in range(1, len(series)):
        decay[i] = max(series[i], alpha * decay[i-1])
    return decay

# -----------------
# STATE: User choices and adjustable parameters
if 'alpha' not in st.session_state:
    st.session_state['alpha'] = 0.9
if 'threshold' not in st.session_state:
    st.session_state['threshold'] = -3.0  # Example negative decay threshold

# SIDEBAR: Controls
with st.sidebar:
    st.markdown("## :orange-badge [Decay Bias Dashboard Controls]")
    st.session_state['alpha'] = st.slider(
        "Decay rate (α, higher is slower decay)", 0.50, 0.99, st.session_state['alpha'], 0.01
    )
    st.session_state['threshold'] = st.slider(
        "Decay Alert Threshold", float(-10), float(0), float(st.session_state['threshold']), 0.1
    )
    st.markdown("Latest update: :green-badge [{}]".format(format_ist(now_ist())))

# -----------------
# MAIN DASHBOARD CONTENT
st.title("Decay Bias Monitoring Dashboard")
st.caption("Auto-refreshes every 15 seconds. All times displayed in IST.")

# LOAD DATA
df = load_demo_data()

# DECAY TRACKING
alpha = st.session_state['alpha']
df['decay'] = compute_decay(df['signal'].to_numpy(), alpha=alpha)
recent_value = df['signal'].iloc[-1]
recent_decay = df['decay'].iloc[-1]

# DEVIATION/DECAY DETECTION
decay_detected = (recent_decay - recent_value) < st.session_state['threshold']

# Responsive dashboard layout
col_metrics, col_chart = st.columns([1, 2])
with col_metrics:
    st.metric("Current Metric", f"{recent_value:.2f}")
    st.metric("Decay-tracked Value", f"{recent_decay:.2f}", delta=f"{recent_decay-recent_value:.2f}")

    st.markdown("---")
    if decay_detected:
        st.markdown(
            ":red-badge [Decay detected!]\n\n"
            "**Recommendation:**\n"
            "- Review possible reasons for sudden drop\n"
            "- Check recent deployments, upstream data sources\n"
            "- If persistent, escalate to engineering\n"
        )
        st.toast(":red[Decay detected! Review recommendations on left panel.]", icon="🚨")
    else:
        st.markdown(
            ":green-badge [No decay detected]\n\n"
            "Status: All signals are within expected range. "
            "No action required at this time."
        )

with col_chart:
    st.markdown("### Metric & Decay Over Time")
    chart_data = df[['timestamp', 'signal', 'decay']].set_index('timestamp')
    st.line_chart(chart_data, use_container_width=True, height=350)

with st.expander("Show historical data table"):
    st.dataframe(df, use_container_width=True, height=320, hide_index=True)

# -----------------
# Additional UI: Tabs for exploration
tab1, tab2 = st.tabs([":bar_chart: Trend", ":scroll: Recommendations Log"])

with tab1:
    st.write("View historical trends and compare decay filter to actual signal data.")
    st.line_chart(chart_data[-60:], use_container_width=True)  # last 60 points

with tab2:
    st.write("Recommendation history and actions will appear here (future extension).")

# -----------------
# Footer
st.markdown('---')
st.markdown(
    ":small[🕒 Last updated: **{}**] | "
    ":small[© 2025 Decay Bias Dashboard, built with :streamlit:]"
    .format(format_ist(now_ist()))
)

# EOF

