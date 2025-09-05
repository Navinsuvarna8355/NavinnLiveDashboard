# app.py : ऑप्शन प्रीमियम डिके बायस एनालिटिक्स एवं ट्रेडिंग डैशबोर्ड (हिंदी में)
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import plotly.graph_objs as go
from streamlit_autorefresh import st_autorefresh  # Auto refresh के लिए
# pnsea लाइब्रेरी इंडेक्स ऑप्शन डेटा के लिए
try:
    from pnsea import NSE
except ImportError:
    NSE = None  # अगर लाइब्रेरी न मिले तो alternate fetch यूज़ करें

# --------------------------------------
# Streamlit Page Config और Title
st.set_page_config(page_title="CE/PE Decay Bias Analytics (हिंदी)", layout='wide')
st.markdown("## 📊 ऑप्शन प्रीमियम डिके बायस एनालिटिक्स (निफ्टी/बैंक निफ्टी/सेंसेक्स)", unsafe_allow_html=True)
st.caption("**हिंदी में दिशानिर्देश एवं सभी स्ट्रेटेजी सुझाव**")

# --------------------------------------
# Sidebar - यूजर इनपुट्स
indices = ['NIFTY', 'BANKNIFTY', 'SENSEX']
symbol = st.sidebar.selectbox('इंडेक्स चुनें', indices, index=0)
refresh_in_sec = st.sidebar.slider('लाइव रिफ्रेश अंतराल (सेकंड में)', 15, 300, 60)
expiry_date = st.sidebar.text_input('Expiry Date (DD-MMM-YYYY):', '')  # ऑटो-फिल या यूजर डालें
decay_threshold = st.sidebar.slider('Decay Bias Threshold (%)', 5, 30, 12)
st.sidebar.markdown("---")

#---------------------------------------
# Auto-refresh enable (User interval)
st_autorefresh(interval=refresh_in_sec*1000, key="data_refresh")

#---------------------------------------
# Option Chain Data Fetch Function (Cache with expiry 3 min)
@st.cache_data(ttl=180)
def fetch_option_chain(symbol, expiry=None):
    """ऑप्शन चेन लाइव डेटा प्राप्त करें (pnsea प्राथमिक, नहीं तो Requests Scrape)"""
    if NSE:
        nse = NSE()
        if expiry:
            try:
                data = nse.options.option_chain(symbol, expiry_date=expiry)[0]
                return data['records']['data'] if 'records' in data else data
            except Exception:
                pass  # नीचे रिक्वेस्ट मेथड पर fallback करें
    # Alternate - Direct NSE API
    url_map = {
        "NIFTY": "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY",
        "BANKNIFTY": "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY",
        "SENSEX": "https://www.nseindia.com/api/option-chain-equities?symbol=SENSEX"
    }
    url = url_map.get(symbol)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }
    try:
        sess = requests.Session()
        # Cookie प्री-फेचिंग (NSE security protocol)
        _ = sess.get("https://www.nseindia.com/option-chain", headers=headers, timeout=5)
        response = sess.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            data = response.json()
            raw = data['records']['data']
            # Expiry filter
            if expiry:
                raw = [item for item in raw if item.get('expiryDate', '') == expiry]
            return raw
    except Exception as e:
        st.error(f"डेटा लाने में समस्या: {e}")
        return []
    return []

#---------------------------------------
# डेटा को DataFrame में प्रोसेस करें
def prepare_option_df(raw, symbol):
    """Raw JSON से कम्प्लीट DataFrame बनाएँ"""
    rows = []
    for d in raw:
        strike = d['strikePrice']
        expiry = d.get('expiryDate', None)
        ce = d.get('CE', {})
        pe = d.get('PE', {})
        row = {
            'strike': strike,
            'expiry': expiry,
            'CE_ltp': ce.get('lastPrice', np.nan),
            'CE_oi': ce.get('openInterest', np.nan),
            'CE_chngOI': ce.get('changeinOpenInterest', np.nan),
            'PE_ltp': pe.get('lastPrice', np.nan),
            'PE_oi': pe.get('openInterest', np.nan),
            'PE_chngOI': pe.get('changeinOpenInterest', np.nan),
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    df.sort_values('strike', inplace=True)
    return df

#---------------------------------------
# Decay Calculations: फ़ंक्शन
def calculate_decay(df_prev, df_now):
    """दो टाइमस्टैम्प के DF के बीच CE/PE प्रीमियम डिके प्रतिशत निकालें"""
    result = []
    keys = ['strike', 'expiry']
    joined = pd.merge(df_prev, df_now, on=keys, suffixes=('_prev', '_now'))
    for idx, row in joined.iterrows():
        ce_decay = np.nan
        pe_decay = np.nan
        if row['CE_ltp_prev'] > 0:
            ce_decay = ((row['CE_ltp_prev'] - row['CE_ltp_now'])/row['CE_ltp_prev'])*100
        if row['PE_ltp_prev'] > 0:
            pe_decay = ((row['PE_ltp_prev'] - row['PE_ltp_now'])/row['PE_ltp_prev'])*100
        result.append({
            'strike': row['strike'],
            'CE_decay': ce_decay,
            'PE_decay': pe_decay,
        })
    decay_df = pd.DataFrame(result)
    return decay_df

#---------------------------------------
# Session State में पिछले डेटा को सुरक्षित रखें
if 'option_prev' not in st.session_state:
    st.session_state['option_prev'] = None

# डेटा फेच
raw = fetch_option_chain(symbol, expiry_date if expiry_date else None)
if raw:
    df = prepare_option_df(raw, symbol)
else:
    st.error("डेटा उपलब्ध नहीं। कृपया इंस्टेंट रिफ्रेश या expiry/date बदलें।")
    st.stop()

# Session State लॉजिक
df_prev = st.session_state['option_prev']
st.session_state['option_prev'] = df.copy()

#---------------------------------------
# ATM स्ट्राइक चयन (default: nearest to median/underlying)
spot_guess = None
if not df.empty:
    median_strike = df['strike'].median()
    spot_guess = median_strike if median_strike else df['strike'].mean()
else:
    spot_guess = 0

atm_range = st.sidebar.slider("ATM स्ट्राइक के आसपास कितनी स्ट्राइक्स रखें?", 3, 15, 7)
atm_df = df[(df['strike'] >= spot_guess - atm_range*100) & (df['strike'] <= spot_guess + atm_range*100)].copy()

#---------------------------------------
st.markdown("#### 📝 ऑप्शन चेन (ATM के करीब)")
st.dataframe(atm_df[['strike','CE_ltp','PE_ltp','CE_oi','PE_oi']], use_container_width=True)

#---------------------------------------
# Decay और Bias detection - केवल तब जब पिछला डेटा उपलब्ध हो
if df_prev is not None:
    decay_df = calculate_decay(df_prev, df)
    avg_ce_decay = decay_df['CE_decay'].mean()
    avg_pe_decay = decay_df['PE_decay'].mean()

    st.markdown("### 📉 डिके प्रतिशत की तुलना")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=decay_df['strike'],
        y=decay_df['CE_decay'],
        name='CE Decay (%)',
        marker=dict(color='orange')
    ))
    fig.add_trace(go.Bar(
        x=decay_df['strike'],
        y=decay_df['PE_decay'],
        name='PE Decay (%)',
        marker=dict(color='green')
    ))
    fig.update_layout(title='CE vs PE Premium Decay %',
                     barmode='group',
                     xaxis_title="स्ट्राइक",
                     yaxis_title="डिके %")
    st.plotly_chart(fig, use_container_width=True)

    # Bias detection logic
    bias_message = ""
    recommendation = ""
    bias_type = None
    if abs(avg_ce_decay - avg_pe_decay) < decay_threshold:
        bias_message = "कोई स्पष्ट डिके बायस नहीं है। मार्केट साइडवेज़ या लो-वोलैटिलिटी है।"
        recommendation = "ट्रेडिंग से बचें या छोटे स्कैल्पिंग ट्रेड लें।"
        bias_type = 'neutral'
    elif avg_ce_decay > avg_pe_decay + decay_threshold:
        bias_message = "CE डिके बायस एक्टिव है! कॉल्स में प्रीमियम तेज़ी से गिर रहा है।"
        recommendation = "ATM/OTM CE बेचें या PE खरीदें। SL आवश्यक।"
        bias_type = 'ce'
    elif avg_pe_decay > avg_ce_decay + decay_threshold:
        bias_message = "PE डिके बायस एक्टिव है! पुट्स में प्रीमियम तेज़ी से गिर रहा है।"
        recommendation = "ATM/OTM PE बेचें या CE खरीदें। SL आवश्यक।"
        bias_type = 'pe'
    else:
        bias_message = "दोनों ऑप्शंस में decay तेज़ है। Expiry Straddle Sell या Market Neutral रणनीति आज़माएँ।"
        recommendation = "ATM CE एवं PE दोनों बेचें, परंतु SL अवश्य लगाएँ।"
        bias_type = 'both'

    # Display Bias
    if bias_type == 'ce':
        st.info(f"🟠 **{bias_message}**\n\n➡️ *{recommendation}*")
    elif bias_type == 'pe':
        st.success(f"🟢 **{bias_message}**\n\n➡️ *{recommendation}*")
    elif bias_type == 'neutral':
        st.warning(f"🟡 **{bias_message}**\n\n➡️ *{recommendation}*")
    else:
        st.error(f"🔴 **{bias_message}**\n\n➡️ *{recommendation}*")

    # विस्तारपूर्वक रणनीति table
    strat_table = pd.DataFrame([
        {"Decay Bias": "CE Decay", "रणनीति": "ATM/OTM CE SELL, PE BUY", "बाजार संकेत": "साइडवेज़ या गिरावट"},
        {"Decay Bias": "PE Decay", "रणनीति": "ATM/OTM PE SELL, CE BUY", "बाजार संकेत": "तेजी/कम वोलैटिलिटी"},
        {"Decay Bias": "दोनों Decay", "रणनीति": "ATM Straddle Sell", "बाजार संकेत": "Expiry/Low Move"},
        {"Decay Bias": "None/Neutral", "रणनीति": "No Trade/सावधानी", "बाजार संकेत": "अनिश्चित"}
    ])
    st.markdown("#### ⚡ रणनीति सारांश तालिका")
    st.table(strat_table)

    # अतिरिक्त नोट्स
    st.markdown("""
> **एलर्ट:**  
> • हर ट्रेड पर SL लगाएँ।  
> • दूर-दूर के स्ट्राइक का प्रीमियम तेजी से गिर सकता है, इसलिए कमपोजिशन का ध्यान रखें।  
> • PCR, OI Change, वॉल्यूम आदि अतिरिक्त संकेत भी देखें।  
> • टुल्स जैसे justticks.in, tradingtick.com, आदि से लाइव PCR/Straddle डेटा को सहायक संकेतक की तरह देखें।
    """)

else:
    st.info("पहला डेटा स्नैपशॉट लिया जा रहा है... कुछ सेकंड बाद डिके बायस का विश्लेषण दिखेगा।")

#---------------------------------------
# Footer
st.markdown("---")
st.markdown(
    """
#### 🟢 डैशबोर्ड सुविधाएँ:
- लाइव डेटा ऑटो रिफ्रेश
- CE/PE Decay Analytics
- हिंदी में स्पष्ट ट्रेडिंग सुझाव
- ATM स्ट्राइक्स केंद्रित उपलब्धता
- Plotly तथा Streamlit विज़ुअल्स

⚠️ *यह सुझाव केवल शैक्षिक प्रयोजन के लिए है। ट्रेडिंग जोखिम के अधीन है—कृपया स्वयं से पुष्टि करें।*
""")

# --------------------------------------
# END OF FILE
