"""
Government Congestion Monitoring Module
Dynamic Continuous Heatmap-based investigative tool for authorities.
Optimized for high-stability, zero-flicker monitoring.
"""

import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

# ================== BANGALORE AREA COORDINATES ==================
AREA_COORDS = {
    "Indiranagar":       (12.9784, 77.6408),
    "Whitefield":        (12.9698, 77.7500),
    "Koramangala":       (12.9352, 77.6245),
    "M.G. Road":         (12.9756, 77.6068),
    "Jayanagar":         (12.9250, 77.5938),
    "Hebbal":            (13.0358, 77.5970),
    "Yeshwanthpur":      (13.0220, 77.5500),
    "Electronic City":   (12.8399, 77.6770),
}

# DETERMINISTIC JITTER SET (To prevent blinking)
# Fixed offsets to create a "cloud" look without using random on every run
JITTER_OFFSETS = [
    (0,0), (0.01, 0.01), (-0.01, -0.01), (0.01, -0.01), (-0.01, 0.01),
    (0.005, 0), (0, 0.005), (-0.005, 0), (0, -0.005),
    (0.015, 0.015), (-0.015, -0.015), (0.008, 0.012), (-0.012, 0.008)
]

def render_gov_congestion_map(traffic_df):
    st.title("Strategic Area Congestion Heatmap")
    st.caption("Strategic Density-Based Investigative Intelligence | Professional Light Theme")

    # 1. STATE PERSISTENCE
    if "heat_focus_coords" not in st.session_state:
        st.session_state.heat_focus_coords = None

    # 2. DATA AGGREGATION
    area_stats = traffic_df.groupby("Area Name").agg({
        "Congestion Level": "mean",
        "Traffic_Volume": "mean",
        "Average Speed": "mean",
        "Incident Reports": "sum"
    }).reset_index()

    # 3. DETERMINISTIC HEATMAP GENERATION
    heat_data = []
    for _, row in area_stats.iterrows():
        area = row["Area Name"]
        coords = AREA_COORDS.get(area)
        if not coords: continue

        base_intensity = (row["Congestion Level"] / 100.0)
        
        # Focus logic (Intensity Boost)
        focus_boost = 1.0
        if st.session_state.heat_focus_coords:
            dist = np.sqrt((coords[0] - st.session_state.heat_focus_coords[0])**2 + 
                           (coords[1] - st.session_state.heat_focus_coords[1])**2)
            if dist < 0.05:
                focus_boost = 2.5
            else:
                focus_boost = 0.3 # Fade non-selected areas

        # Use Fixed Jitter Offsets (NO RANDOM = NO BLINKING)
        for dlat, dlon in JITTER_OFFSETS:
            heat_data.append([coords[0] + dlat, coords[1] + dlon, base_intensity * focus_boost])

    # 4. MAP VISUALIZATION (STABLE)
    # Using a container to isolate the map layout
    map_container = st.container()
    with map_container:
        st.write("**Investigative Density Layer**")
        st.info("Interactive Focus: Click any region to boost local density intensity. The map is optimized for stability.")
        
        m = folium.Map(location=(12.9716, 77.5946), zoom_start=12, tiles="CartoDB positron")
        
        gradient = {
            0.1: '#31a354', 0.3: '#addd8e', 0.5: '#feb24c', 
            0.7: '#f03b20', 0.9: '#bd0026'
        }

        HeatMap(
            data=heat_data,
            radius=35,
            blur=20,
            min_opacity=0.4,
            gradient=gradient
        ).add_to(m)

        # Render with specific settings to prevent unnecessary redraws
        map_interaction = st_folium(
            m, 
            width=None, 
            height=500, 
            key="gov_stable_heatmap",
            returned_objects=["last_clicked"] 
        )

    # 5. DYNAMIC INTERACTION LOGIC
    if map_interaction and map_interaction.get("last_clicked"):
        click = map_interaction["last_clicked"]
        new_focus = (click["lat"], click["lng"])
        # Only trigger RERUN if the selection actually changed
        if st.session_state.heat_focus_coords != new_focus:
            st.session_state.heat_focus_coords = new_focus
            st.rerun()

    # 6. DETAILS PANEL (ISOLATED)
    # This panel updates WITHOUT affecting the map's initialization logic
    details_container = st.container()
    with details_container:
        if st.session_state.heat_focus_coords:
            st.divider()
            # Find nearest area for metrics
            nearest_area = None
            min_dist = float('inf')
            for area, coords in AREA_COORDS.items():
                dist = np.sqrt((coords[0] - st.session_state.heat_focus_coords[0])**2 + 
                               (coords[1] - st.session_state.heat_focus_coords[1])**2)
                if dist < min_dist:
                    min_dist = dist
                    nearest_area = area
            
            if nearest_area and min_dist < 0.1:
                row = area_stats[area_stats["Area Name"] == nearest_area].iloc[0]
                st.subheader(f"📍 Sector Intelligence: {nearest_area}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Local Intensity", f"{row['Congestion Level']:.1f}%")
                m2.metric("Flow Mass", int(row['Traffic_Volume']))
                m3.metric("Velocity", f"{row['Average Speed']:.1f} km/h")
                m4.metric("Incidents", int(row['Incident Reports']))

                with st.container(border=True):
                    st.write(f"**Integrity Assessment for {nearest_area} Sector**")
                    status = "Critical" if row['Congestion Level'] > 70 else "Elevated" if row['Congestion Level'] > 40 else "Stable"
                    color = "red" if status == "Critical" else "orange" if status == "Elevated" else "green"
                    st.markdown(f"Current operational status: :{color}[**{status}**]")
                    st.write("Visual intensity indicates high-precision cumulative infrastructure pressure.")
            
            if st.button("Reset Global Monitor", type="secondary"):
                st.session_state.heat_focus_coords = None
                st.rerun()
        else:
            st.divider()
            st.info("System operational. Select a coordinate to focus cumulative intensity analytics.")
