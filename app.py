def detect_decay(oc_data, underlying, decay_range=150):
    """
    Analyzes option chain data to detect decay bias around the ATM strike.
    Uses 'theta' as the primary indicator, and 'change' as a fallback.
    """
    # Filter for strikes near the underlying price
    atm_strikes = [d for d in oc_data if abs(d["strikePrice"] - underlying) <= decay_range and "CE" in d and "PE" in d]

    details = []

    for strike_data in atm_strikes:
        ce_data = strike_data["CE"]
        pe_data = strike_data["PE"]

        # Use .get() to avoid key errors if data is missing
        ce_theta = ce_data.get("theta", 0)
        pe_theta = pe_data.get("theta", 0)
        ce_chg = ce_data.get("change", 0)
        pe_chg = pe_data.get("change", 0)

        decay_side = "Both"

        # Primary Logic: Compare absolute theta values if they are non-zero
        if ce_theta != 0 and pe_theta != 0:
            if abs(ce_theta) > abs(pe_theta) and ce_chg < 0:
                decay_side = "CE"
            elif abs(pe_theta) > abs(ce_theta) and pe_chg < 0:
                decay_side = "PE"

        # Fallback Logic: If theta values are zero, use the change in price
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
    
    # Calculate overall decay bias from the counts
    ce_count = df[df['Decay_Side'] == 'CE'].shape[0]
    pe_count = df[df['Decay_Side'] == 'PE'].shape[0]
    
    overall_decay_side = "Both Sides Decay"
    if ce_count > pe_count:
        overall_decay_side = "CE Decay Active"
    elif pe_count > ce_count:
        overall_decay_side = "PE Decay Active"

    return overall_decay_side, df
