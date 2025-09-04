# app.py
from __future__ import annotations
import math
import time
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

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
        "chain_url": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
    },
    "BANKNIFTY": {
        "symbol": "BANKNIFTY",
        "chain_url": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY",
    },
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    k = 1.0 / (1.0 + 0.2316419 * abs(x))
    k_sum = k * (0.319381530 + k * (-0.356563782 +
             k * (1.781477937 + k * (-1.821255978 + 1.330274429 * k))))
    cdf = 1.0 - _norm_pdf(x) * k_sum
    return cdf if x >= 0 else 1.0 - cdf

# ---------------------------
# Black–Scholes daily theta
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
# Option chain parsing
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
# Bias detection
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

# ---------------------------
# Networking with caching
# ---------------------------
@st.cache_data(show_spinner=False, ttl=30)
def fetch_json(url: str, headers: Dict[str, str], timeout: int = 6) -> Dict[str, Any]:
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
        "CE Decay Bias": "#FF8C00",
        "PE Decay Bias": "#00B8D9",
        "Both Sides Decay": "#9E9E9E",
        "No Decay Bias": "#34C759",
        "No Data": "#B00020",
    }.get(bias, "#666666")

def render_bias_block(index_name: str, bias: str, strike: float, ce_t: float,
