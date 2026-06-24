"""
User Traffic Map Module
Interactive area-wise traffic visualization for citizens.
Displays congestion levels with simple color coding:
  Red = High Traffic, Orange = Medium Traffic, Green = Low Traffic
Professional, enterprise-grade dark UI.
"""

import folium
import streamlit as st
from streamlit_folium import st_folium

# Bangalore area coordinates
AREA_COORDS = {
    "Koramangala":       (12.9352, 77.6245),
    "Whitefield":        (12.9698, 77.7500),
    "Indiranagar":       (12.9784, 77.6408),
    "M.G. Road":         (12.9756, 77.6065),
    "Jayanagar":         (12.9250, 77.5938),
    "Hebbal":            (13.0358, 77.5970),
    "Yeshwanthpur":      (13.0220, 77.5500),
    "Electronic City":   (12.8399, 77.6770),
}

BANGALORE_CENTER = (12.9716, 77.5946)


def _congestion_color(level):
    """Return color based on congestion level."""
    if level > 70:
        return "#D32F2F"   # Red
    elif level > 40:
        return "#F57C00"   # Orange
    else:
        return "#388E3C"   # Green


def _congestion_label(level):
    """Return user-friendly label."""
    if level > 70:
        return "High Traffic"
    elif level > 40:
        return "Medium Traffic"
    else:
        return "Low Traffic"


def render_user_map(traffic_df):
    """
    Render an interactive area-wise traffic map for the User role.
    Shows all Bangalore areas with color-coded congestion circles.
    """

    st.header("Area-wise Traffic Overview")
    st.caption("Live congestion levels across Bangalore precincts")

    # Compute average congestion per area
    area_stats = traffic_df.groupby("Area Name").agg(
        avg_congestion=("Congestion Level", "mean"),
        avg_volume=("Traffic_Volume", "mean"),
    ).reset_index()

    # Create Folium map
    m = folium.Map(
        location=BANGALORE_CENTER,
        zoom_start=11,
        tiles="CartoDB positron",
    )

    # Professional Legend (Native Streamlit)
    with st.container():
        c1, c2, c3 = st.columns(3)
        c1.markdown("**● High Traffic**: :red[Red Zone]")
        c2.markdown("**● Medium Traffic**: :orange[Orange Zone]")
        c3.markdown("**● Low Traffic**: :green[Green Zone]")

    # Plot each area
    for _, row in area_stats.iterrows():
        area_name = row["Area Name"]
        congestion = row["avg_congestion"]

        coords = AREA_COORDS.get(area_name)
        if coords is None:
            continue

        color = _congestion_color(congestion)
        label = _congestion_label(congestion)

        # Circle size proportional to traffic volume (clamped)
        radius = max(12, min(30, row["avg_volume"] / 300))

        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=f"{area_name}: {label}",
            tooltip=f"{area_name} - {label}",
        ).add_to(m)

    # Render map in Streamlit
    st_folium(m, width=None, height=520, returned_objects=[])

    # Standard Observation Guidance
    st.info(
        "Observation Guidance:\n"
        "- Areas marked in Red indicate critical congestion levels.\n"
        "- Orange zones suggest moderate delay potential.\n"
        "- Green markers represent stable, low-density traffic conditions."
    )
