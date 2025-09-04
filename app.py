import math
from scipy.stats import norm

def calculate_theta(S, K, T, r, sigma, option_type="call"):
    """
    Black-Scholes daily theta calculation.
    S: Spot price
    K: Strike price
    T: Time to expiry in years
    r: Risk-free rate (decimal)
    sigma: Implied volatility (decimal)
    option_type: "call" or "put"
    """
    if T <= 0 or sigma <= 0:
        return 0

    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "call":
        theta = (- (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
                 - r * K * math.exp(-r * T) * norm.cdf(d2))
    else:
        theta = (- (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
                 + r * K * math.exp(-r * T) * norm.cdf(-d2))

    return theta / 365  # per day theta


def detect_decay(strike_data, underlying, days_to_expiry=2, risk_free_rate=0.06):
    """
    Detects decay bias between CE and PE with theta fallback.
    strike_data: dict containing 'CE' and 'PE' option chain data
    underlying: spot price
    days_to_expiry: days left to expiry
    risk_free_rate: annual risk-free rate
    """
    CE = strike_data.get("CE")
    PE = strike_data.get("PE")

    if not CE or not PE:
        return "No Data"

    ce_theta = CE.get("theta", 0)
    pe_theta = PE.get("theta", 0)

    # Convert days to expiry into years for BS model
    T = days_to_expiry / 252

    # Fallback for CE theta
    if ce_theta == 0:
        ce_theta = calculate_theta(
            S=underlying,
            K=strike_data["strikePrice"],
            T=T,
            r=risk_free_rate,
            sigma=CE.get("impliedVolatility", 0) / 100,
            option_type="call"
        )

    # Fallback for PE theta
    if pe_theta == 0:
        pe_theta = calculate_theta(
            S=underlying,
            K=strike_data["strikePrice"],
            T=T,
            r=risk_free_rate,
            sigma=PE.get("impliedVolatility", 0) / 100,
            option_type="put"
        )

    # Bias detection logic
    if ce_theta < 0 and pe_theta < 0:
        if abs(ce_theta) > abs(pe_theta):
            return "CE Decay Bias"
        elif abs(pe_theta) > abs(ce_theta):
            return "PE Decay Bias"
        else:
            return "Both Sides Decay"
    elif ce_theta < 0:
        return "CE Decay Bias"
    elif pe_theta < 0:
        return "PE Decay Bias"
    else:
        return "No Decay Bias"


# Example usage inside your multi-index loop
if __name__ == "__main__":
    # Mock NSE API data
    strike_data_example = {
        "strikePrice": 45000,
        "CE": {"theta": 0, "impliedVolatility": 12.5},
        "PE": {"theta": 0, "impliedVolatility": 14.2}
    }
    spot_price = 45120

    bias = detect_decay(strike_data_example, spot_price, days_to_expiry=2)
    print("Decay Bias:", bias)
