@st.cache_data(ttl=300)
def fetch_option_chain():
    try:
        session = requests.Session()
        # Warm up session (required by NSE)
        session.get("https://www.nseindia.com", headers=HEADERS)

        # Actual data request
        response = session.get(NSE_URL, headers=HEADERS)

        # Check content type
        if "application/json" not in response.headers.get("Content-Type", ""):
            st.error("❌ NSE returned non-JSON content. Possibly blocked or rate-limited.")
            st.stop()

        data = response.json()
        return pd.DataFrame(data["records"]["data"])

    except requests.exceptions.RequestException as e:
        st.error(f"🔌 Network error: {e}")
        st.stop()
    except ValueError:
        st.error("❌ Failed to decode JSON. NSE may have returned HTML or an error page.")
        st.stop()
