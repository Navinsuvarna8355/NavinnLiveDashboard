@st.cache_data(ttl=300)
def fetch_option_chain():
    try:
        session = requests.Session()

        # Warm up session (required by NSE)
        session.get("https://www.nseindia.com", headers=HEADERS)

        # Actual data request
        response = session.get(NSE_URL, headers=HEADERS)

        # Check if response is JSON
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            st.warning("⚠️ NSE returned non-JSON content. Possibly blocked or rate-limited.")
            st.text("Raw response preview:")
            st.code(response.text[:1000])
            st.stop()

        # Parse JSON
        data = response.json()
        return pd.DataFrame(data["records"]["data"])

    except requests.exceptions.RequestException as e:
        st.error(f"🔌 Network error: {e}")
        st.stop()
    except ValueError as ve:
        st.error("❌ JSON decoding failed. NSE may have returned HTML or an error page.")
        st.text("Raw response preview:")
        st.code(response.text[:1000])
        st.stop()
