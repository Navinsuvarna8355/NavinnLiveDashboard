import math
from scipy.stats import norm

def calculate_theta(S, K, T, r, sigma, option_type="call"):
    """
    S: Spot price
    K: Strike price
    T: Time to expiry in years
    r: Risk-free rate (e.g., 0.06 for 6%)
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

# Inside detect_decay():
if CE and PE:
    ce_theta = CE.get("theta", 0)
    pe_theta = PE.get("theta", 0)

    # Fallback if theta is 0 or missing
    if ce_theta == 0:
        ce_theta = calculate_theta(
            S=underlying,
            K=strike_data["strikePrice"],
            T=2/252,  # example: 2 days to expiry
            r=0.06,
            sigma=CE.get("impliedVolatility", 0) / 100,
            option_type="call"
        )
    if pe_theta == 0:
        pe_theta = calculate_theta(
            S=underlying,
            K=strike_data["strikePrice"],
            T=2/252,
            r=0.06,
            sigma=PE.get("impliedVolatility", 0) / 100,
            option_type="put"
        )
