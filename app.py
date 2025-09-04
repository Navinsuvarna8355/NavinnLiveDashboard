# signals.py
# Dependency-free signal engine for decay bias with theta fallback.

from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple


# ---------------------------
# Normal distribution helpers
# ---------------------------

def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def _norm_cdf(x: float) -> float:
    # Abramowitz-Stegun approximation for N(0,1) CDF
    k = 1.0 / (1.0 + 0.2316419 * abs(x))
    k_sum = k * (0.319381530 + k * (-0.356563782 +
             k * (1.781477937 + k * (-1.821255978 + 1.330274429 * k))))
    cdf = 1.0 - _norm_pdf(x) * k_sum
    return cdf if x >= 0 else 1.0 - cdf


# ---------------------------
# Core Greeks (theta fallback)
# ---------------------------

def calculate_theta(
    S: float,
    K: float,
    T_years: float,
    r: float,
    sigma: float,
    option_type: str = "call"
) -> float:
    """
    Daily theta using Black-Scholes (no dividends).
    Returns theta per day (same units as S and K).
    """
    if S <= 0 or K <= 0 or T_years <= 0 or sigma <= 0:
        return 0.0

    sqrtT = math.sqrt(T_years)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T_years) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT

    if option_type == "call":
        theta = (
            - (S * _norm_pdf(d1) * sigma) / (2 * sqrtT)
            - r * K * math.exp(-r * T_years) * _norm_cdf(d2)
        )
    else:
        theta = (
            - (S * _norm_pdf(d1) * sigma) / (2 * sqrtT)
            + r * K * math.exp(-r * T_years) * _norm_cdf(-d2)
        )

    # Return per day
    return theta / 365.0


# ---------------------------
# Bias detection per strike
# ---------------------------

def detect_decay_bias_for_strike(
    strike_row: Dict[str, Any],
    spot: float,
    days_to_expiry: float,
    risk_free_rate: float = 0.06
) -> Tuple[str, float, float]:
    """
    Determine decay bias for a single strike row with CE/PE data.
    Returns (bias_label, ce_theta, pe_theta).
    - bias_label in {"CE Decay Bias", "PE Decay Bias", "Both Sides Decay", "No Decay Bias", "No Data"}
    """
    CE = strike_row.get("CE")
    PE = strike_row.get("PE")
    K = float(strike_row.get("strikePrice", 0) or 0)

    if not CE or not PE or K <= 0 or spot <= 0:
        return "No Data", 0.0, 0.0

    # Raw theta from API (may be 0 or missing)
    ce_theta = float(CE.get("theta", 0) or 0)
    pe_theta = float(PE.get("theta", 0) or 0)

    # Sigma from IV in percentage -> decimal
    ce_sigma = float(CE.get("impliedVolatility", 0) or 0) / 100.0
    pe_sigma = float(PE.get("impliedVolatility", 0) or 0) / 100.0

    # Time to expiry in years (252 trading days)
    T_years = max(0.0, (days_to_expiry or 0) / 252.0)

    # Fallbacks if theta is missing or exactly zero
    if ce_theta == 0.0:
        ce_theta = calculate_theta(
            S=spot, K=K, T_years=T_years, r=risk_free_rate, sigma=max(1e-8, ce_sigma), option_type="call"
        )
    if pe_theta == 0.0:
        pe_theta = calculate_theta(
            S=spot, K=K, T_years=T_years, r=risk_free_rate, sigma=max(1e-8, pe_sigma), option_type="put"
        )

    # Bias logic
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
# Helpers: ATM selection, summaries
# ---------------------------

def pick_atm_strike(spot: float, strikes: List[float]) -> Optional[float]:
    """Pick the strike closest to spot."""
    strikes = [float(s) for s in strikes if s is not None]
    if not strikes or spot <= 0:
        return None
    return min(strikes, key=lambda k: abs(k - spot))

def extract_strike_list_from_chain(chain: Dict[str, Any]) -> List[float]:
    """
    Accepts a chain structure like NSE's 'records' -> 'data' (list of rows with 'strikePrice').
    Returns list of strike prices found.
    """
    strikes = []
    if not chain:
        return strikes
    # Try common layouts
    data = chain.get("records", {}).get("data", [])
    if not data and isinstance(chain.get("data"), list):
        data = chain["data"]
    for row in data:
        k = row.get("strikePrice")
        if isinstance(k, (int, float)):
            strikes.append(float(k))
    return sorted(set(strikes))

def find_row_for_strike(chain: Dict[str, Any], strike_price: float) -> Optional[Dict[str, Any]]:
    """
    Returns the row dict (with CE, PE) matching a strike, if present.
    Works with typical NSE option chain-like structure.
    """
    if not chain:
        return None
    data = chain.get("records", {}).get("data", [])
    if not data and isinstance(chain.get("data"), list):
        data = chain["data"]
    for row in data:
        if float(row.get("strikePrice", -1)) == float(strike_price):
            return row
    return None


# ---------------------------
# Public API
# ---------------------------

def compute_decay_bias_for_chain(
    chain: Dict[str, Any],
    spot: float,
    days_to_expiry: float,
    risk_free_rate: float = 0.06,
    strike_mode: str = "ATM",
    specific_strike: Optional[float] = None
) -> Dict[str, Any]:
    """
    Compute decay bias for a chain.
    - strike_mode: "ATM" to auto-select nearest strike, or "SPECIFIC" to use specific_strike.
    Returns a dict with:
      {
        "strike": float | None,
        "bias": str,
        "ce_theta": float,
        "pe_theta": float
      }
    """
    strikes = extract_strike_list_from_chain(chain)

    if strike_mode.upper() == "SPECIFIC" and specific_strike:
        strike = float(specific_strike)
    else:
        strike = pick_atm_strike(spot, strikes)

    if strike is None:
        return {"strike": None, "bias": "No Data", "ce_theta": 0.0, "pe_theta": 0.0}

    row = find_row_for_strike(chain, strike)
    if row is None:
        return {"strike": strike, "bias": "No Data", "ce_theta": 0.0, "pe_theta": 0.0}

    bias, ce_theta, pe_theta = detect_decay_bias_for_strike(
        strike_row=row,
        spot=spot,
        days_to_expiry=days_to_expiry,
        risk_free_rate=risk_free_rate
    )
    return {"strike": strike, "bias": bias, "ce_theta": ce_theta, "pe_theta": pe_theta}

def summarize_bias_across_strikes(
    chain: Dict[str, Any],
    spot: float,
    days_to_expiry: float,
    risk_free_rate: float = 0.06,
    strikes_limit: int = 15,
    around_atm: int = 7
) -> Dict[str, Any]:
    """
    Evaluate bias for a band of strikes around ATM and produce a summary.
    Returns:
      {
        "atm_strike": float | None,
        "evaluated": List[Dict[str, Any]],  # per strike results
        "summary": { "CE Decay Bias": int, "PE Decay Bias": int, "Both Sides Decay": int, "No Decay Bias": int, "No Data": int }
      }
    """
    strikes = extract_strike_list_from_chain(chain)
    if not strikes or spot <= 0:
        return {"atm_strike": None, "evaluated": [], "summary": {}}

    atm = pick_atm_strike(spot, strikes)

    # Pick a centered window around ATM
    strikes_sorted = sorted(strikes, key=lambda k: (abs(k - atm), k))
    window = strikes_sorted[:strikes_limit]
    # Optionally enforce symmetric band (atm +/- around_atm)
    if atm in strikes:
        try:
            idx = strikes.index(atm)
            lo = max(0, idx - around_atm)
            hi = min(len(strikes), idx + around_atm + 1)
            window = strikes[lo:hi]
        except Exception:
            pass

    results: List[Dict[str, Any]] = []
    counts = {
        "CE Decay Bias": 0,
        "PE Decay Bias": 0,
        "Both Sides Decay": 0,
        "No Decay Bias": 0,
        "No Data": 0
    }

    for k in window:
        row = find_row_for_strike(chain, k)
        if not row:
            results.append({"strike": k, "bias": "No Data", "ce_theta": 0.0, "pe_theta": 0.0})
            counts["No Data"] += 1
            continue

        bias, ce_theta, pe_theta = detect_decay_bias_for_strike(
            strike_row=row, spot=spot, days_to_expiry=days_to_expiry, risk_free_rate=risk_free_rate
        )
        results.append({"strike": k, "bias": bias, "ce_theta": ce_theta, "pe_theta": pe_theta})
        counts[bias] += 1

    return {
        "atm_strike": atm,
        "evaluated": results,
        "summary": counts
    }
