"""
Map Routing Module
Interactive map rendering with geocoding and road-following routes
for the Urban Traffic Advisory System.
Professional, enterprise-grade dark UI.
"""

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable


# ================== BANGALORE AREA COORDINATES ==================
BANGALORE_AREAS = {
    "Indiranagar":       (12.9784, 77.6408),
    "Whitefield":        (12.9698, 77.7500),
    "Koramangala":       (12.9352, 77.6245),
    "M.G. Road":         (12.9756, 77.6068),
    "Jayanagar":         (12.9250, 77.5938),
    "Hebbal":            (13.0358, 77.5970),
    "Yeshwanthpur":      (13.0220, 77.5500),
    "Electronic City":   (12.8399, 77.6770),
}

BANGALORE_CENTER = (12.9716, 77.5946)


# ================== GEOCODING ==================
def geocode_location(location_text):
    if not location_text or not location_text.strip():
        return None

    location_text = location_text.strip()
    for area_name, coords in BANGALORE_AREAS.items():
        if location_text.lower() == area_name.lower():
            return coords

    try:
        geolocator = Nominatim(user_agent="urban_traffic_advisory_system_v2")
        search_query = f"{location_text}, Bangalore, Karnataka, India"
        location = geolocator.geocode(search_query, timeout=10)
        if location:
            lat, lng = location.latitude, location.longitude
            if 12.5 <= lat <= 13.5 and 77.0 <= lng <= 78.5:
                return (lat, lng)
            return (lat, lng)
        return None
    except:
        return None


def validate_coordinates(coords):
    if coords is None:
        return False
    lat, lng = coords
    return -90 <= lat <= 90 and -180 <= lng <= 180


# ================== ROUTE FETCHING ==================
def get_route(start_coords, end_coords):
    try:
        start_lng, start_lat = start_coords[1], start_coords[0]
        end_lng, end_lat = end_coords[1], end_coords[0]
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == "Ok" and data.get("routes"):
            geometry = data["routes"][0]["geometry"]["coordinates"]
            return [[point[1], point[0]] for point in geometry]
    except:
        pass
    return [list(start_coords), list(end_coords)]


def get_route_info(start_coords, end_coords):
    try:
        start_lng, start_lat = start_coords[1], start_coords[0]
        end_lng, end_lat = end_coords[1], end_coords[0]
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lng},{start_lat};{end_lng},{end_lat}?overview=false"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            return {
                "distance_km": round(route["distance"] / 1000, 1),
                "duration_min": round(route["duration"] / 60, 0),
            }
    except:
        pass
    return None


# ================== MAP CREATION ==================
def create_route_map(start_coords, end_coords, route_coords, start_name, end_name):
    mid_lat = (start_coords[0] + end_coords[0]) / 2
    mid_lng = (start_coords[1] + end_coords[1]) / 2

    m = folium.Map(location=[mid_lat, mid_lng], zoom_start=12, tiles="CartoDB positron")

    folium.Marker(
        location=start_coords,
        popup=f"Start: {start_name}",
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)

    folium.Marker(
        location=end_coords,
        popup=f"Destination: {end_name}",
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
    ).add_to(m)

    folium.PolyLine(locations=route_coords, color="#2563EB", weight=5, opacity=0.8).add_to(m)
    m.fit_bounds([start_coords, end_coords], padding=(30, 30))
    return m


# ================== STREAMLIT UI SECTION ==================
def render_map_section(traffic_df):
    st.header("Intelligence Route Analysis")
    st.caption("Strategic routing and spatial analysis for optimized mobility")

    input_method = st.radio(
        "Input Method:", ["Select Precinct", "Custom Geo-Location"],
        horizontal=True, key="map_input_method"
    )

    col1, col2 = st.columns(2)
    if input_method == "Select Precinct":
        area_list = list(BANGALORE_AREAS.keys())
        start_name = col1.selectbox("Start Point", area_list, index=0, key="map_start_select")
        end_name = col2.selectbox("End Point", area_list, index=1, key="map_end_select")
    else:
        start_name = col1.text_input("Start Point", placeholder="Search location...", key="map_start_text")
        end_name = col2.text_input("End Point", placeholder="Search location...", key="map_end_text")

    if st.button("Generate Strategic Route", type="primary", key="show_route_btn"):
        if not start_name or not end_name:
            st.warning("Both start and end points must be specified.")
            return

        with st.spinner("Analyzing spatial data..."):
            start_coords = geocode_location(start_name)
            end_coords = geocode_location(end_name)

        if not start_coords or not validate_coordinates(start_coords):
            st.error(f"Inconclusive data for '{start_name}'.")
            return
        if not end_coords or not validate_coordinates(end_coords):
            st.error(f"Inconclusive data for '{end_name}'.")
            return

        with st.spinner("Calculating optimal corridor..."):
            route_coords = get_route(start_coords, end_coords)
            route_info = get_route_info(start_coords, end_coords)

        if route_info:
            c1, c2, c3 = st.columns(3)
            c1.metric("Distance", f"{route_info['distance_km']} km")
            c2.metric("Est. Duration", f"{int(route_info['duration_min'])} min")
            avg_speed = route_info["distance_km"] / (route_info["duration_min"] / 60) if route_info["duration_min"] > 0 else 0
            c3.metric("Avg Speed", f"{avg_speed:.0f} km/h")

        route_map = create_route_map(start_coords, end_coords, route_coords, start_name, end_name)
        st_folium(route_map, width=None, height=500, returned_objects=[])
    else:
        default_map = folium.Map(location=BANGALORE_CENTER, zoom_start=11, tiles="CartoDB positron")
        for area, coords in BANGALORE_AREAS.items():
            folium.CircleMarker(location=coords, radius=6, color="#1E88E5", fill=True, fill_opacity=0.6, tooltip=area).add_to(default_map)
        st_folium(default_map, width=None, height=400, returned_objects=[])
