"""
Government Infrastructure Map Advisory Module
AI-based location-specific corridor analysis and infrastructure
decision visualization for the Urban Traffic Advisory System.
Professional, default light theme UI.
"""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


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

# ================== AREA-SPECIFIC PHYSICAL PROFILES ==================
AREA_PROFILES = {
    "Koramangala": {
        "road_width": "narrow",
        "land_use": "mixed_dense",
        "junction_density": "high",
        "signal_frequency": "high",
        "building_density": "very_high",
        "open_land": "very_low",
        "elevation_constraint": "none",
        "suitable_vertical": True,
        "suitable_underground": True,
        "suitable_horizontal": False,
        "primary_problem": "signal_delay_dense_traffic",
        "key_bottleneck": "Sony World Junction",
    },
    "Whitefield": {
        "road_width": "moderate",
        "land_use": "it_corridor",
        "junction_density": "moderate",
        "signal_frequency": "moderate",
        "building_density": "moderate",
        "open_land": "moderate",
        "elevation_constraint": "none",
        "suitable_vertical": True,
        "suitable_underground": False,
        "suitable_horizontal": True,
        "primary_problem": "volume_overload_peak_hours",
        "key_bottleneck": "Marathahalli Bridge",
    },
    "Indiranagar": {
        "road_width": "mixed",
        "land_use": "residential_commercial",
        "junction_density": "high",
        "signal_frequency": "high",
        "building_density": "high",
        "open_land": "low",
        "elevation_constraint": "none",
        "suitable_vertical": True,
        "suitable_underground": True,
        "suitable_horizontal": False,
        "primary_problem": "cross_traffic_conflict",
        "key_bottleneck": "CMH Road",
    },
    "M.G. Road": {
        "road_width": "wide",
        "land_use": "central_business",
        "junction_density": "high",
        "signal_frequency": "high",
        "building_density": "very_high",
        "open_land": "none",
        "elevation_constraint": "metro_above",
        "suitable_vertical": False,
        "suitable_underground": True,
        "suitable_horizontal": False,
        "primary_problem": "intersection_conflict_cbd",
        "key_bottleneck": "Trinity Circle",
    },
    "Jayanagar": {
        "road_width": "moderate",
        "land_use": "residential",
        "junction_density": "moderate",
        "signal_frequency": "moderate",
        "building_density": "moderate",
        "open_land": "low",
        "elevation_constraint": "none",
        "suitable_vertical": True,
        "suitable_underground": False,
        "suitable_horizontal": True,
        "primary_problem": "capacity_limitation",
        "key_bottleneck": "South End Circle",
    },
    "Hebbal": {
        "road_width": "wide",
        "land_use": "transit_hub",
        "junction_density": "low",
        "signal_frequency": "low",
        "building_density": "moderate",
        "open_land": "moderate",
        "elevation_constraint": "existing_flyover",
        "suitable_vertical": True,
        "suitable_underground": False,
        "suitable_horizontal": True,
        "primary_problem": "merge_conflict_highway",
        "key_bottleneck": "Hebbal Flyover",
    },
    "Yeshwanthpur": {
        "road_width": "wide",
        "land_use": "industrial_commercial",
        "junction_density": "moderate",
        "signal_frequency": "moderate",
        "building_density": "low",
        "open_land": "moderate",
        "elevation_constraint": "rail_crossing",
        "suitable_vertical": True,
        "suitable_underground": True,
        "suitable_horizontal": True,
        "primary_problem": "rail_road_conflict",
        "key_bottleneck": "Yeshwanthpur Circle",
    },
    "Electronic City": {
        "road_width": "moderate",
        "land_use": "it_industrial",
        "junction_density": "low",
        "signal_frequency": "low",
        "building_density": "moderate",
        "open_land": "high",
        "elevation_constraint": "expressway",
        "suitable_vertical": True,
        "suitable_underground": False,
        "suitable_horizontal": True,
        "primary_problem": "entry_exit_bottleneck",
        "key_bottleneck": "Silk Board Junction",
    },
}

# ================== INFRASTRUCTURE TYPE DEFINITIONS ==================
INFRA_TYPES = {
    "Flyover / Overbridge": {
        "color": "blue",
        "line_color": "#2563EB",
        "icon": "arrow-up",
        "label": "Proposed Flyover",
        "dash": None,
    },
    "Underpass": {
        "color": "purple",
        "line_color": "#9333EA",
        "icon": "arrow-down",
        "label": "Proposed Underpass",
        "dash": None,
    },
    "Road Expansion": {
        "color": "orange",
        "line_color": "#EA580C",
        "icon": "road",
        "label": "Road Expansion Zone",
        "dash": None,
    },
    "Alternate Road": {
        "color": "green",
        "line_color": "#16A34A",
        "icon": "code-branch",
        "label": "Suggested Alternate Route",
        "dash": "10 6",
    },
}

# ================== LOCATION-SPECIFIC DECISION ENGINE ==================
def decide_infrastructure(area_name, corridor_metrics):
    profile = AREA_PROFILES.get(area_name)
    if not profile:
        return None

    congestion = corridor_metrics["congestion"]
    capacity = corridor_metrics["capacity_util"]
    volume = corridor_metrics["volume"]

    recommended = None
    reason = ""
    rejected = []
    problem_type = profile["primary_problem"]

    # Decision Logic
    if (profile["suitable_underground"]
            and not profile["suitable_horizontal"]
            and profile["signal_frequency"] == "high"
            and profile["building_density"] in ["very_high", "high"]):
        recommended = "Underpass"
        reason = (f"Dense urban fabric in {area_name} restricts surface widening. "
                  f"Underpass at {profile['key_bottleneck']} addresses signal conflicts effectively.")
        rejected.append({"type": "Road Expansion", "reason": "No land available for widening."})
        rejected.append({"type": "Flyover", "reason": "Visual impact and clearance constraints."})

    elif (profile["suitable_vertical"]
            and profile["junction_density"] == "low"
            and profile["elevation_constraint"] != "metro_above"):
        recommended = "Flyover / Overbridge"
        reason = (f"High throughput requirement and vertical clearance availability at {area_name} "
                  f"supports grade separation via {profile['key_bottleneck']} flyover expansion.")
        rejected.append({"type": "Road Expansion", "reason": "Cost-benefit favors grade-separation for arterial flow."})

    else:
        recommended = "Road Expansion"
        reason = (f"Surface level optimization is the most feasible solution for {area_name}. "
                  f"Increasing lane capacity at {profile['key_bottleneck']} will reduce volume-to-capacity ratios.")
        rejected.append({"type": "Major Infra", "reason": "Metrics do not warrant high-cost intervention."})

    return {
        "recommended": recommended,
        "reason": reason,
        "rejected": rejected,
        "problem_type": problem_type.replace("_", " ").title(),
        "impact": _get_impact(recommended, area_name, congestion),
        "key_bottleneck": profile["key_bottleneck"],
        "area_profile": profile,
    }


def _get_impact(infra_type, area_name, congestion):
    if infra_type == "Flyover / Overbridge":
        return {"congestion_reduction": "30-40%", "travel_time_improvement": "25-35%", "redistribution": f"Interruption-free flow through {area_name}"}
    elif infra_type == "Underpass":
        return {"congestion_reduction": "25-35%", "travel_time_improvement": "20-30%", "redistribution": f"Signal conflict elimination in {area_name}"}
    elif infra_type == "Road Expansion":
        return {"congestion_reduction": "20-25%", "travel_time_improvement": "15-20%", "redistribution": f"Increased lane capacity for {area_name}"}
    return {"congestion_reduction": "0%", "travel_time_improvement": "0%", "redistribution": "N/A"}


def evaluate_strategy(area_name, user_choice):
    """Evaluate user-proposed infrastructure strategy."""
    profile = AREA_PROFILES.get(area_name)
    if not profile:
        return "Not worth it", "Location data missing."

    # Recommendation logic
    # (Simplified for validation purposes)
    if user_choice == "Flyover / Overbridge":
        if profile["suitable_vertical"] and profile["junction_density"] != "high":
            return "Worth it!", f"Vertical clearance and junction profile at {area_name} are optimal for an elevated bypass."
        return "Not worth it", f"Constraints like building density or existing metro lines make vertical structures unfeasible in {area_name}."
    
    elif user_choice == "Underpass":
        if profile["suitable_underground"]:
            return "Worth it!", f"Grade-level separation via an underpass is ideal for resolving chronic signal delays in the dense {area_name} core."
        return "Not worth it", f"Sub-surface constraints (utility lines/soil type) or lack of chronic signal conflicts make an underpass redundant for {area_name}."
    
    elif user_choice == "Road Expansion":
        if profile["suitable_horizontal"] or profile["road_width"] != "narrow":
            return "Worth it!", f"Widening the existing corridor in {area_name} is the most cost-effective way to handle current volume overloads."
        return "Not worth it", f"The dense urban fabric of {area_name} makes horizontal expansion impossible without massive displacement."
    
    elif user_choice == "Alternate Road":
        return "Worth it!", f"When core corridors are saturated, redistributing demand to parallel mixed-use grids in {area_name} is a highly effective strategy."

    return "Needs Review", "Parameters for this specific intervention are inconclusive."


def analyze_corridors(traffic_df, focus_area):
    other_areas = [a for a in traffic_df['Area Name'].unique() if a != focus_area]
    focus_data = traffic_df[traffic_df['Area Name'] == focus_area]
    focus_metrics = {
        "congestion": focus_data['Congestion Level'].mean(),
        "capacity": focus_data['Road Capacity Utilization'].mean(),
        "volume": focus_data['Traffic_Volume'].mean()
    }

    corridors = []
    for dest_area in other_areas:
        dest_data = traffic_df[traffic_df['Area Name'] == dest_area]
        metrics = {
            "congestion": round((focus_metrics["congestion"] + dest_data['Congestion Level'].mean()) / 2, 1),
            "capacity_util": round((focus_metrics["capacity"] + dest_data['Road Capacity Utilization'].mean()) / 2, 1),
            "volume": round((focus_metrics["volume"] + dest_data['Traffic_Volume'].mean()) / 2, 0),
        }
        pressure = "CRITICAL" if metrics["congestion"] > 75 else "HIGH" if metrics["congestion"] > 60 else "MODERATE"
        decision = decide_infrastructure(dest_area, metrics)
        corridors.append({
            "from_area": focus_area, "to_area": dest_area, "metrics": metrics,
            "pressure": pressure, "decision": decision
        })
    return corridors


def create_infra_map(focus_area, corridors, selected_types):
    m = folium.Map(location=BANGALORE_AREAS[focus_area], zoom_start=13, tiles="CartoDB positron")

    # Focus area marker
    folium.Marker(
        location=BANGALORE_AREAS[focus_area],
        popup=f"ANALYSIS CENTER: {focus_area}",
        tooltip=focus_area,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

    for c in corridors:
        d = c["decision"]
        if d["recommended"] not in selected_types:
            continue

        meta = INFRA_TYPES[d["recommended"]]
        dest_coords = BANGALORE_AREAS[c["to_area"]]

        # Corridor Line
        folium.PolyLine(
            locations=[BANGALORE_AREAS[focus_area], dest_coords],
            color=meta["line_color"],
            weight=5,
            opacity=0.6,
            dash_array=meta["dash"],
            tooltip=f"{focus_area} → {c['to_area']} ({d['recommended']})"
        ).add_to(m)

        # Recommendation Marker
        folium.Marker(
            location=dest_coords,
            popup=f"<b>{d['recommended']}</b><br>{d['reason']}",
            tooltip=f"{c['to_area']}: {d['recommended']}",
            icon=folium.Icon(color=meta["color"], icon=meta["icon"], prefix='fa')
        ).add_to(m)

    return m


def render_gov_map_section(traffic_df):
    st.header("Infrastructure Development Planning")
    st.caption("AI-driven corridor analysis and grade-separated solution optimization")

    focus_area = st.selectbox("Strategic Analysis Focus Area", list(BANGALORE_AREAS.keys()))
    corridors = analyze_corridors(traffic_df, focus_area)

    st.subheader("Corridor Pressure Summary")
    summary_df = pd.DataFrame([{
        "Destination": c["to_area"], "Pressure": c["pressure"], 
        "Congestion": f"{c['metrics']['congestion']}%", "Recommended": c["decision"]["recommended"]
    } for c in corridors])
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.write("**Integrated Map Controls**")
        selected_types = []
        cols = st.columns(4)
        for i, (name, d) in enumerate(INFRA_TYPES.items()):
            if cols[i].checkbox(d["label"], value=True, key=f"check_{name}"):
                selected_types.append(name)

    # Native Legend (Colorized)
    with st.container():
        l1, l2, l3, l4 = st.columns(4)
        l1.markdown("**● Flyover**: :blue[Blue]")
        l2.markdown("**● Underpass**: :purple[Purple]")
        l3.markdown("**● Expansion**: :orange[Orange]")
        l4.markdown("**● Alternate**: :green[Green]")

    m = create_infra_map(focus_area, corridors, selected_types)
    st_folium(m, width=None, height=550, returned_objects=[])

    st.subheader("Decision Support Documents")
    for c in corridors:
        d = c["decision"]
        if d["recommended"] in selected_types:
            with st.expander(f"{c['to_area']} - {c['pressure']} Risk"):
                st.write(f"**Recommendation:** {d['recommended']}")
                st.write(f"**Justification:** {d['reason']}")
                st.write("**Impact Projections:**")
                c1, c2 = st.columns(2)
                c1.metric("Congestion Delta", d["impact"]["congestion_reduction"])
                c2.metric("Flow Improvement", d["impact"]["travel_time_improvement"])

    st.divider()

    # --- INFRASTRUCTURE STRATEGY VALIDATOR (PHASE 9) ---
    st.subheader("Infrastructure Strategy Validator")
    st.caption("Test and validate custom infrastructure hypotheses with AI evaluation")
    
    with st.container(border=True):
        scol1, scol2 = st.columns(2)
        with scol1:
            target_area = st.selectbox("Select Target Area", list(BANGALORE_AREAS.keys()), key="val_area")
        with scol2:
            propose_type = st.selectbox("Propose Infrastructure", list(INFRA_TYPES.keys()), key="val_type")
        
        if st.button("Validate Strategy", type="primary"):
            status, explain = evaluate_strategy(target_area, propose_type)
            
            st.markdown("---")
            if status == "Worth it!":
                st.success(f"**{status}**")
            else:
                st.warning(f"**{status}**")
            
            st.info(explain)
