import streamlit as st
import requests
import urllib.parse

# Load credentials from secrets
API_KEY = st.secrets["UPSTOX_API_KEY"]
API_SECRET = st.secrets["UPSTOX_API_SECRET"]
REDIRECT_URI = st.secrets["UPSTOX_REDIRECT_URI"]

# Session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None

# Step 1: Generate login URL
def get_login_url():
    base_url = "https://api.upstox.com/v2/login/authorization/dialog"
    params = {
        "response_type": "code",
        "client_id": API_KEY,
        "redirect_uri": REDIRECT_URI,
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

# Step 2: Exchange code for access token
def get_access_token(auth_code):
    url = "https://api.upstox.com/v2/login/authorization/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "code": auth_code,
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error("❌ Failed to get access token")
        return None

# Step 3: Fetch user profile
def get_user_profile(token):
    url = "https://api.upstox.com/v2/user/profile"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        st.error("❌ Failed to fetch profile")
        return None

# UI
st.title("📊 Upstox OAuth Login")

if st.session_state.access_token:
    st.success("✅ Logged in successfully!")
    profile = get_user_profile(st.session_state.access_token)
    if profile:
        st.subheader("👤 User Profile")
        st.json(profile)
else:
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        auth_code = query_params["code"][0]
        with st.spinner("🔄 Authenticating..."):
            token = get_access_token(auth_code)
            if token:
                st.session_state.access_token = token
                st.experimental_rerun()
    else:
        login_url = get_login_url()
        st.markdown(f"[🔐 Click here to login with Upstox]({login_url})")

