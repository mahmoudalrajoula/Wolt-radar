import streamlit as st
import requests
import pandas as pd
import random

st.set_page_config(page_title="Wolt Shift Radar", layout="wide", initial_sidebar_state="collapsed")

st.title("⚡ Wolt Shift Radar")
st.caption("Live zone metrics & restaurant status")

col_lat, col_lon = st.columns(2)
with col_lat:
    lat = st.number_input("Latitude", value=56.1572, format="%.4f")
with col_lon:
    lon = st.number_input("Longitude", value=10.2107, format="%.4f")

@st.cache_data(ttl=60)  # Cache for 60s to respect rate limits
def fetch_wolt_data(lat, lon):
    target_url = f"https://consumer-api.wolt.com/v1/pages/restaurants?lat={lat}&lon={lon}"
    
    # Modern Chrome/Android Browser Headers to mimic authentic requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,da;q=0.8",
        "Origin": "https://wolt.com",
        "Referer": "https://wolt.com/"
    }

    # Attempt 1: Direct Request
    try:
        response = requests.get(target_url, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json(), None
    except Exception:
        pass

    # Attempt 2: Fallback via AllOrigins Raw gateway if Cloud IP is 429'd
    try:
        proxy_url = f"https://api.allorigins.win/raw?url={requests.utils.quote(target_url)}"
        response = requests.get(proxy_url, timeout=10)
        if response.status_code == 200:
            return response.json(), None
    except Exception as e:
        return None, str(e)

    return None, "HTTP 429 Rate Limited by Wolt. Wait 2–3 minutes before refreshing."

if st.button("🔄 Refresh Radar Data", use_container_width=True):
    st.cache_data.clear()

data, error = fetch_wolt_data(lat, lon)

if error:
    st.error(f"Failed to fetch data: {error}")
elif data:
    sections = data.get("sections", [])
    total_open_venues = 0
    venue_list = []

    for section in sections:
        items = section.get("items", [])
        for item in items:
            venue = item.get("venue", {})
            if venue:
                name = venue.get("name", "Unknown")
                online = venue.get("online", False)
                rating = venue.get("rating", {}).get("score", "N/A")
                del_price = venue.get("delivery_price", "N/A")

                if online:
                    total_open_venues += 1

                venue_list.append({
                    "Name": name,
                    "Status": "🟢 Open" if online else "🔴 Closed",
                    "Rating": rating,
                    "Delivery Cost": del_price
                })

    m1, m2, m3 = st.columns(3)
    m1.metric("Active Venues Nearby", value=total_open_venues)
    m2.metric("Total Tracked Places", value=len(venue_list))
    m3.metric("Estimated Demand", value="High 🔥" if total_open_venues > 15 else "Moderate 🟡")

    st.divider()

    if venue_list:
        st.subheader("Nearby Restaurants")
        df = pd.DataFrame(venue_list).drop_duplicates(subset=["Name"])
        st.dataframe(df, use_container_width=True, hide_index=True)
