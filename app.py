# app.py
# Streamlit dashboard: multi-index decay bias with no-SciPy theta fallback.
from __future__ import annotations

import math
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import streamlit as st

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(page_title="Navinn Live Dashboard — Decay Bias", layout="wide")

# ---------------------------
# Constants and index config
# ---------------------------
INDEX_CONFIG = {
    "NIFTY": {
        "symbol": "NIFTY",
        # Update to your reliable endpoint; these are placeholders
        "chain_url": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
        "spot_url": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",  # spot derived from records
    },
    "BANKNIFTY": {
        "symbol": "BANKNIFTY",
        "chain_url": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY",
        "spot_url": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY",
    },
    "SENSEX": {
        # If you fetch from BSE or a custom API, update URLs accordingly
        "symbol": "SENSEX",
        "chain_url": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",  # placeholder if SENSEX not on NSE OC
        "spot_url": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
    },
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com",
}

# ---------------------------
# Normal distribution helpers (no SciPy)
# ---------------------------
def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def _norm_cdf(x: float) -> float:
    # Abramowitz–Stegun approximation
    k = 1.0 / (1.0 + 0.2316419 * abs(x))
    k_sum = k * (0.319381530 + k * (-0.356563782 +
             k * (1.781477937 + k * (-1.821255978 + 1.330274429 * k))))
    cdf = 1.0 - _norm_pdf(x) * k_sum
    return cdf if x >= 0 else 1.0 - cdf

# ---------------------------
# Black–Scholes daily theta (per day)
# ---------------------------
def calculate_theta(S: float, K: float, T_years: float, r: float, sigma: float, option_type: str = "call") -> float:
    if S <= 0 or K <= 0 or T_years <= 0 or sigma <= 0:
        return 0.0
    sqrtT = math.sqrt(T_years)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T_years) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT
    if option_type == "call":
        theta = (-(S * _norm_pdf(d1) * sigma) / (2 * sqrtT) - r * K * math.exp(-r * T_years) * _norm_cdf(d2))
    else:
        theta = (-(S * _norm_pdf(d1) * sigma) / (2 * sqrtT) + r * K * math.exp(-r * T_years) * _norm_cdf(-d2))
    return theta / 365.0

# ---------------------------
# Option chain parsing helpers
# ---------------------------
def extract_records(chain: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not chain:
        return []
    data = chain.get("records", {}).get("data", [])
    if not data and isinstance(chain.get("data"), list):
        data = chain["data"]
    return data or []

def extract_spot(chain: Dict[str, Any]) -> Optional[float]:
    try:
        return float(chain.get("records", {}).get("underlyingValue"))
    except Exception:
        return None

def extract_strikes(chain: Dict[str, Any]) -> List[float]:
    strikes: List[float] = []
    for row in extract_records(chain):
        k = row.get("strikePrice")
        if isinstance(k, (int, float)):
            strikes.append(float(k))
    return sorted(set(strikes))

def pick_atm(spot: float, strikes: List[float]) -> Optional[float]:
    if not strikes or spot is None or spot <= 0:
        return None
    return min(strikes, key=lambda k: abs(k - spot))

def row_for_strike(chain: Dict[str, Any], strike: float) -> Optional[Dict[str, Any]]:
    for row in extract_records(chain):
        try:
            if float(row.get("strikePrice", -1)) == float(strike):
                return row
        except Exception:
            continue
    return None

# ---------------------------
# Bias detection per strike
# ---------------------------
def detect_decay_bias_for_row(row: Dict[str, Any], spot: float, days_to_expiry: float, r: float = 0.06) -> Tuple[str, float, float]:
    CE = row.get("CE")
    PE = row.get("PE")
    K = float(row.get("strikePrice", 0) or 0)
    if not CE or not PE or K <= 0 or not spot or spot <= 0:
        return "No Data", 0.0, 0.0

    ce_theta = float(CE.get("theta", 0) or 0)
    pe_theta = float(PE.get("theta", 0) or 0)
    ce_iv = float(CE.get("impliedVolatility", 0) or 0) / 100.0
    pe_iv = float(PE.get("impliedVolatility", 0) or 0) / 100.0

    T = max(0.0, (days_to_expiry or 0) / 252.0)
    if ce_theta == 0.0:
        ce_theta = calculate_theta(spot, K, T, r, max(1e-8, ce_iv), "call")
    if pe_theta == 0.0:
        pe_theta = calculate_theta(spot, K, T, r, max(1e-8, pe_iv), "put")

    if ce_theta < 0 and pe_theta < 0:
        if abs(ce_theta) > abs(pe_theta):
            bias = "CE Decay Bias"
        elif abs(pe_theta) > abs(ce_theta):
            bias = "PE Decay Bias"
        else:
            bias = "Both Sides Decay"
    elif ce_theta < 0:
        bias = "CE Decay Bias"
    elif pe_theta < 0:
        bias = "PE Decay Bias"
    else:
        bias = "No Decay Bias"
    return bias, ce_theta, pe_theta

def summarize_window(chain: Dict[str, Any], spot: float, days_to_expiry: float, window_strikes: List[float], r: float = 0.06):
    results: List[Dict[str, Any]] = []
    counts = {
        "CE Decay Bias": 0,
        "PE Decay Bias": 0,
        "Both Sides Decay": 0,
        "No Decay Bias": 0,
        "No Data": 0,
    }
    for k in window_strikes:
        row = row_for_strike(chain, k)
        if not row:
            results.append({"strike": k, "bias": "No Data", "ce_theta": 0.0, "pe_theta": 0.0})
            counts["No Data"] += 1
            continue
        bias, ce_t, pe_t = detect_decay_bias_for_row(row, spot, days_to_expiry, r)
        results.append({"strike": k, "bias": bias, "ce_theta": ce_t, "pe_theta": pe_t})
        counts[bias] += 1
    return results, counts

# ---------------------------
# Networking with caching and resilience
# ---------------------------
@st.cache_data(show_spinner=False, ttl=30)
def fetch_json(url: str, headers: Dict[str, str], timeout: int = 6) -> Dict[str, Any]:
    # First do a session warm-up to get cookies (important for NSE)
    with requests.Session() as s:
        s.headers.update(headers)
        try:
            s.get("https://www.nseindia.com", timeout=timeout)
        except Exception:
            pass
        resp = s.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

def safe_fetch_chain(cfg: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]], Optional[float], Optional[str]]:
    name = cfg["symbol"]
    url = cfg["chain_url"]
    try:
        data = fetch_json(url, DEFAULT_HEADERS)
        spot = extract_spot(data)
        return name, data, spot, None
    except Exception as e:
        return name, None, None, str(e)

def parallel_fetch(configs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=min(8, len(configs))) as ex:
        futs = {ex.submit(safe_fetch_chain, cfg): name for name, cfg in configs.items()}
        for fut in as_completed(futs):
            name = futs[fut]
            sym, data, spot, err = fut.result()
            out[name] = {"data": data, "spot": spot, "error": err}
    return out

# ---------------------------
# UI helpers
# ---------------------------
def bias_color(bias: str) -> str:
    return {
        "CE Decay Bias": "#FF8C00",   # orange
        "PE Decay Bias": "#00B8D9",   # cyan
        "Both Sides Decay": "#9E9E9E",# gray
        "No Decay Bias": "#34C759",   # green
        "No Data": "#B00020",         # red
    }.get(bias, "#666666")

def render_bias_block(index_name: str, result: Dict[str, Any], evaluated: List[Dict[str, Any]]):
    bias = result.get("bias", "No Data")
    strike = result.get("strike")
    ce_t = result.get("ce_theta", 0.0)
    pe_t = result.get("pe_theta", 0.0)
    color = bias_color(bias)

    st.markdown(f"#### {index_name}")
    st.markdown(
        f"""
        <div style="padding:12px;border-radius:10px;border:1px solid #eee;background:{color}20">
          <div style="font-size:18px;"><b>Bias:</b> <span style="color:{color};font-weight:700">{bias}</span></div>
          <div style="margin-top:6px;">
            <b>ATM:</b> {strike if strike is not None else '-'} &nbsp; | &nbsp;
            <b>CE θ:</b> {ce_t:.4f} &nbsp; | &nbsp; <b>PE θ:</b> {pe_t:.4f}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if evaluated:
        st.dataframe(
            {
                "Strike": [int(x["strike"]) if isinstance(x["strike"], (int, float)) else x["strike"] for x in evaluated],
                "Bias": [x["bias"] for x in evaluated],
                "CE θ": [round(x["ce_theta"], 5) for x in evaluated],
                "PE θ": [round(x["pe_theta"], 5) for x in evaluated],
            },
            use_container_width=True,
            hide_index=True,
        )

# ---------------------------
# Main UI
# ---------------------------
st.title("Decay Bias Dashboard (ATM + Window)")

with st.sidebar:
    st.header("Controls")
    indices = st.multiselect(
        label="Select indices",
        options=list(INDEX_CONFIG.keys()),
        default=["NIFTY", "BANKNIFTY"],
    )
    days_to_expiry = st.number_input("Days to expiry (trading days)", min_value=0.0, max_value=30.0, value=2.0, step=0.5)
    risk_free_rate = st.number_input("Risk-free rate (annual, decimal)", min_value=0.0, max_value=0.20, value=0.06, step=0.005, format="%.3f")
    window_half = st.slider("Strikes around ATM (each side)", min_value=2, max_value=15, value=7)
    refresh_sec = st.slider("Auto-refresh seconds", min_value=5, max_value=60, value=20)
    st.caption("Tip: Lower refresh during market hours, higher during off-peak.")

# Autorefresh
st_autorefresh_count = st.experimental_rerun  # dummy reference to avoid lint; we use st_autorefresh next
st.experimental_set_query_params(ts=str(int(time.time())))  # ensure fresh cache per refresh
st_autorefresh = st.autorefresh(interval=refresh_sec * 1000, key="autorefresh")

# Info strip
st.markdown(
    "> Data fetched in parallel with caching and timeouts. Theta falls back to Black–Scholes when API theta is 0 or missing."
)

if not indices:
    st.info("Select at least one index from the sidebar to start.")
    st.stop()

# Fetch
sel_config = {k: INDEX_CONFIG[k] for k in indices if k in INDEX_CONFIG}

with st.spinner("Fetching option chains..."):
    fetched = parallel_fetch(sel_config)

cols = st.columns(len(sel_config))
for i, name in enumerate(sel_config.keys()):
    with cols[i]:
        entry = fetched.get(name, {})
        data = entry.get("data")
        spot = entry.get("spot")
        err = entry.get("error")

        if err or not data:
            st.error(f"{name}: Unable to fetch data. {('Error: ' + err) if err else ''}")
            continue

        strikes = extract_strikes(data)
        atm = pick_atm(spot, strikes)
        if atm is None:
            st.error(f"{name}: ATM not found.")
            continue

        # Build window around ATM
        if atm in strikes:
            try:
                idx = strikes.index(atm)
            except ValueError:
                idx = min(range(len(strikes)), key=lambda j: abs(strikes[j] - atm))
        else:
            idx = min(range(len(strikes)), key=lambda j: abs(strikes[j] - atm))
        lo = max(0, idx - window_half)
        hi = min(len(strikes), idx + window_half + 1)
        window = strikes[lo:hi]

        # ATM bias
        atm_row = row_for_strike(data, atm)
        bias, ce_t, pe_t = detect_decay_bias_for_row(atm_row, spot, days_to_expiry, r=risk_free_rate) if atm_row else ("No Data", 0.0, 0.0)

        # Window summary
        evaluated, counts = summarize_window(data, spot, days_to_expiry, window, r=risk_free_rate)
        result = {"strike": atm, "bias": bias, "ce_theta": ce_t, "pe_theta": pe_t}

        render_bias_block(name, result, evaluated)

# Footer
st.caption("Note: If an endpoint rate-limits or changes, update INDEX_CONFIG URLs and headers accordingly.")
