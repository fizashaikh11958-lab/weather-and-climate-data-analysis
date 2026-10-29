import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

st.set_page_config(
    page_title="Global Real-Time Flight Tracker", layout="wide"
)

st.title("✈️ Global Real-Time Flight Tracker")
st.markdown(
    "Processing high-velocity streaming ADS-B flight vector data powered by"
    " OpenSky Network."
)


@st.cache_data(ttl=60)
def fetch_flight_data():
  url = "https://opensky-network.org/api/states/all"
  try:
    # Added a 10-second timeout to prevent hanging connections
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
      data = response.json()
      states = data.get("states", [])
      if not states:
        return pd.DataFrame()

      columns = [
          "icao24",
          "callsign",
          "origin_country",
          "time_position",
          "last_contact",
          "longitude",
          "latitude",
          "baro_altitude",
          "on_ground",
          "velocity",
          "true_track",
          "vertical_rate",
          "sensors",
          "geo_altitude",
          "squawk",
          "spi",
          "position_source",
      ]
      df = pd.DataFrame(states, columns=columns)
      # Clean up missing data and select relevant columns
      df = df.dropna(subset=["latitude", "longitude"])
      df["callsign"] = df["callsign"].str.strip()
      return df
    else:
      st.warning(
          f"API returned status code {response.status_code}. Retrying shortly."
      )
      return pd.DataFrame()
  except requests.exceptions.RequestException as e:
    st.error(
        "Connection to OpenSky Network timed out or was rate-limited. Please"
        " refresh in a moment."
    )
    return pd.DataFrame()


# Load data
flight_df = fetch_flight_data()

if not flight_df.empty:
  st.success(f"Successfully loaded {len(flight_df)} active flights globally!")

  # Metrics Row
  col1, col2, col3 = st.columns(3)
  col1.metric("Active Flights Tracked", len(flight_df))
  col2.metric("Countries Represented", flight_df["origin_country"].nunique())
  col3.metric(
      "Airborne Units", len(flight_df[flight_df["on_ground"] == False])
  )

  # PyDeck Map Visualization
  layer = pdk.Layer(
      "ScatterplotLayer",
      data=flight_df,
      get_position=["longitude", "latitude"],
      get_color=[255, 140, 0, 160],
      get_radius=30000,
      pickable=True,
  )

  view_state = pdk.ViewState(
      latitude=2