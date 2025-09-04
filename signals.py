from signals import compute_decay_bias_for_chain, summarize_bias_across_strikes

# Example:
bias_row = compute_decay_bias_for_chain(
    chain=option_chain_json,  # your parsed JSON
    spot=spot_price,          # float
    days_to_expiry=2,         # e.g., 2 trading days
    risk_free_rate=0.06,      # adjustable
    strike_mode="ATM"         # or "SPECIFIC", specific_strike=45000
)

summary = summarize_bias_across_strikes(
    chain=option_chain_json,
    spot=spot_price,
    days_to_expiry=2,
    risk_free_rate=0.06,
    strikes_limit=15,
    around_atm=7
)

