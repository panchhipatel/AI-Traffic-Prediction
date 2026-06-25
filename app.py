import streamlit as st
import pandas as pd
import numpy as np
import os
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
import joblib
from map_routing import render_map_section
from gov_infra_map import render_gov_map_section
from user_map import render_user_map
from gov_congestion import render_gov_congestion_map

# ================== PAGE CONFIG ==================
st.set_page_config(page_title="Urban Traffic System", layout="wide")

# ================== FILE CONFIG ==================
CSV_FILE = "users.csv"
DATASET_FILE = "Banglore_traffic_Dataset.csv"
MODEL_FILE = "traffic_model.joblib"
ENCODERS_FILE = "encoders.joblib"
SCALER_FILE = "scaler.joblib"

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=["name", "email", "phone", "dob", "password", "role"]).to_csv(CSV_FILE, index=False)
else:
    # Migrate existing CSV if role column is missing
    _tmp_df = pd.read_csv(CSV_FILE)
    if "role" not in _tmp_df.columns:
        _tmp_df["role"] = "user"
        _tmp_df.to_csv(CSV_FILE, index=False)
    del _tmp_df

# ================== MODEL INITIALIZATION ==================
# Model will be trained on first use if it doesn't exist

# ================== LOAD DATA FUNCTION ==================
@st.cache_data
def load_traffic_data():
    if os.path.exists(DATASET_FILE):
        df = pd.read_csv(DATASET_FILE)
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
        df['Month'] = df['Date'].dt.month
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df['Day'] = df['Date'].dt.day
        # Create congestion categories
        df['Congestion_Category'] = pd.cut(
            df['Congestion Level'], 
            bins=[0, 40, 70, 100], 
            labels=['Low', 'Medium', 'High']
        )
        return df
    return None

# ================== CHATBOT RESPONSE FUNCTION ==================

from chatbot_engine import generate_chatbot_response

# ================== SESSION STATE ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

# =================================================
# =============== NOT LOGGED IN ===================
# =================================================
if not st.session_state.logged_in:

    # ================== EXECUTIVE HEADER SECTION ==================
    st.title("Urban Traffic Congestion Prediction System")
    st.caption("AI-Driven Traffic Intelligence for Bangalore")
    
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # -------- LOGIN PAGE --------
        if st.session_state.auth_page == "login":
            st.header("👋 Welcome Back")
            st.write("Sign in to continue to your dashboard")

            with st.container(border=True):
                with st.form("login_form"):
                    st.write("**Account Credentials**")
                    login_email = st.text_input("Username / Email", placeholder="yourname@example.com")
                    password = st.text_input("Password", type="password", placeholder="••••••••")
                    
                    st.write("**Account Access Type**")
                    login_role = st.radio(
                        "Select your role:",
                        ["User", "Government Authority"],
                        captions=["Travel Advisory & Route Maps", "Infrastructure Planning & Analytics"],
                        horizontal=True
                    )
                    
                    st.write("") # Spacing
                    login_btn = st.form_submit_button("Access Platform", use_container_width=True)

                if login_btn:
                    df = pd.read_csv(CSV_FILE)
                    # Check credentials AND role to ensure correct access
                    role_val = "government" if login_role == "Government Authority" else "user"
                    match = df[((df["name"] == login_email) |(df["email"] == login_email)) & (df["password"] == password) & (df["role"] == role_val)]
                    
                    if not match.empty:
                        st.success(f"Access Granted. Welcome, {match.iloc[0]['name']}")
                        st.session_state.logged_in = True
                        st.session_state.user_role = role_val
                        st.session_state.user_name = match.iloc[0].get("name", "")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or role selection. Please try again.")

                st.write("")
                if st.button("Sign Up for an Account", use_container_width=True):
                    st.session_state.auth_page = "signup"
                    st.rerun()

        # -------- SIGNUP PAGE --------
        else:
            st.header("📝 Create Account")
            st.write("Join the AI-driven traffic intelligence platform")

            with st.container(border=True):
                with st.form("signup_form"):
                    st.write("**Personal Information**")
                    name = st.text_input("Full Name *", placeholder="Enter your full name")
                    email = st.text_input("Email Address *", placeholder="example@mail.com")
                    phone = st.text_input("Phone Number *", placeholder="+91 XXXXX XXXXX")
                    dob = st.date_input("Date of Birth *", min_value=pd.to_datetime("1900-01-01"), max_value=pd.to_datetime("today"))
                    
                    st.write("---")
                    st.write("**Select Access Role**")
                    st.caption("This selection determines which analytics and tools you can access.")
                    signup_role = st.radio(
                        "Select Role *",
                        ["User", "Government Authority"],
                        captions=["For citizens needing route guidance", "For planners needing heavy analytics"],
                        horizontal=True
                    )
                    
                    st.write("---")
                    st.write("**Security**")
                    new_pass = st.text_input("Password *", type="password", placeholder="Create a strong password")
                    confirm_pass = st.text_input("Re-enter Password *", type="password", placeholder="Repeat for safety")
                    
                    signup_btn = st.form_submit_button("Register and Continue", use_container_width=True)

                if signup_btn:
                    if not name or not email or not phone or not new_pass:
                        st.error("Please fill in all mandatory fields.")
                    elif "@" not in email:
                        st.error("Please enter a valid email address.")
                    elif len(phone) < 10:
                        st.error("Please enter a valid 10-digit phone number.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        df = pd.read_csv(CSV_FILE)
                        if email in df["email"].values:
                            st.warning("This email is already registered.")
                        else:
                            role_value = "government" if signup_role == "Government Authority" else "user"
                            new_row = {
                                "name": name,
                                "email": email,
                                "phone": phone,
                                "dob": str(dob),
                                "password": new_pass,
                                "role": role_value
                            }
                            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                            df.to_csv(CSV_FILE, index=False)
                            st.success("Registration successful! You can now log in.")
                            st.session_state.auth_page = "login"
                            st.rerun()

                if st.button("Back to Login"):
                    st.session_state.auth_page = "login"
                    st.rerun()

# =================================================
# =================== DASHBOARD ===================
# =================================================
else:

    with st.sidebar:
        if st.session_state.user_name:
            st.write(f"Welcome, **{st.session_state.user_name}**")
            st.caption(f"Role: {'Government Authority' if st.session_state.user_role == 'government' else 'User'}")
            st.divider()

        if st.session_state.user_role == "government":
            selected = option_menu(
                "Urban Traffic System",
                ["Home", "Dashboard", "Traffic Chatbot", "Dataset", "Traffic Analysis", 
                 "Congestion Heatmap", "Predict Congestion", "Infrastructure Planning Map", "Alerts", "Profile", "Logout"],
                icons=["house", "speedometer2", "chat-dots", "database", "graph-up", 
                       "map", "cpu", "geo-alt-fill", "bell", "person", "box-arrow-right"],
                default_index=0
            )
        else:
            # USER role (default)
            selected = option_menu(
                "Urban Traffic System",
                ["Home", "Traffic Chatbot", "User Advisory", "Map", "Profile", "Logout"],
                icons=["house", "chat-dots", "person-walking", "map", "person", "box-arrow-right"],
                default_index=0
            )

    # =================== HOME (Common) ===================
    if selected == "Home":
        st.title("🏠 Urban Traffic Congestion Prediction System")
        st.caption("Bangalore City Mobility Optimization")
        
        st.write("""
        ### Welcome to the Urban Traffic Platform
        This platform leverages machine learning and data analytics 
        to solve urban traffic congestion challenges in Bangalore. 
        
        **System Objectives:**
        - **Commuter Intelligence:** Providing citizens with route advisory and real-time traffic awareness.
        - **Infrastructural Planning:** Equipping authorities with diagnostic tools for data-driven decisions.
        
        **Core Intelligence Modules:**
        - **Traffic Assistant:** Conversational AI for location-specific traffic inquiries.
        - **Predictive Engine:** Forecasting traffic volume and congestion levels.
        - **Infrastructure Optimizer:** AI recommendations for flyovers, underpasses, and expansions.
        """)
        
        st.info("Navigation: Use the sidebar to access platform modules based on your authorized role.")

    # =================== DASHBOARD (Analytics Overview) ===================
    elif selected == "Dashboard":
        if st.session_state.user_role == "government":
            st.title("📊 City Analytics Dashboard")
            st.caption("Bangalore Urban Traffic Overview")
            
            traffic_df = load_traffic_data()
            if traffic_df is not None:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", f"{len(traffic_df):,}")
                with col2:
                    st.metric("Areas Covered", traffic_df['Area Name'].nunique())
                with col3:
                    st.metric("Avg Congestion", f"{traffic_df['Congestion Level'].mean():.1f}%")
                with col4:
                    st.metric("Total Incidents", f"{traffic_df['Incident Reports'].sum():,}")
                
                st.divider()
                
                # Quick overview chart
                st.subheader("Congestion Distribution by Area")
                area_congestion = traffic_df.groupby('Area Name')['Congestion Level'].mean().sort_values(ascending=True)
                fig = px.bar(
                    x=area_congestion.values, 
                    y=area_congestion.index,
                    orientation='h',
                    color=area_congestion.values,
                    color_continuous_scale='RdYlGn_r',
                    labels={'x': 'Average Congestion Level', 'y': 'Area'}
                )
                fig.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Access denied. This module is for Government Authority only.")

    # =================== TRAFFIC CHATBOT ===================
    elif selected == "Traffic Chatbot":
        st.title("🤖 Traffic Intelligence Assistant")
        st.caption("AI-Powered Conversational Traffic Intelligence")
        
        traffic_df = load_traffic_data()
        
        # Initialize chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "Welcome. I am the Traffic Intelligence Assistant. I can provide insights on:\n\n- Current congestion levels\n- Optimal route selections\n- Infrastructure assessments\n- Traffic predictions\n\nHow may I assist you?"}
            ]
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        user_input = st.chat_input("Ask about traffic...")
        
        if user_input and traffic_df is not None:
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Generate response based on query and role
            result = generate_chatbot_response(user_input, traffic_df, user_role=st.session_state.user_role)
            response = result["content"]
            st.session_state.chat_suggestions = result["suggestions"]
            
            # Add assistant response
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            with st.chat_message("assistant"):
                st.markdown(response)
        
        # --- DYNAMIC SUGGESTED OPTIONS ---
        if "chat_suggestions" in st.session_state and st.session_state.chat_suggestions:
            st.divider()
            st.write("**Suggested Follow-up:**")
            
            # Render suggestions as clickable buttons in columns
            cols = st.columns(len(st.session_state.chat_suggestions))
            for i, suggestion in enumerate(st.session_state.chat_suggestions):
                with cols[i]:
                    if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                        # Treat suggestion as user input
                        st.session_state.chat_messages.append({"role": "user", "content": suggestion})
                        
                        # Generate response
                        result = generate_chatbot_response(suggestion, traffic_df, user_role=st.session_state.user_role)
                        st.session_state.chat_messages.append({"role": "assistant", "content": result["content"]})
                        st.session_state.chat_suggestions = result["suggestions"]
                        st.rerun()
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.chat_messages = [
                {"role": "assistant", "content": "Chat cleared! How can I help you with traffic today?"}
            ]
            st.rerun()

    # =================== USER ADVISORY MODE ===================
    elif selected == "User Advisory":
        st.title("🚶 Travel Advisory")
        st.caption("Route Optimization and Mobility Guidance for Citizens")
        
        traffic_df = load_traffic_data()
        if traffic_df is not None:
            
            st.header("🗺️ Journey Planning")
            
            col1, col2 = st.columns(2)
            with col1:
                start_location = st.selectbox("Start Location", traffic_df['Area Name'].unique())
            with col2:
                end_location = st.selectbox("Destination", traffic_df['Area Name'].unique())
            
            col3, col4 = st.columns(2)
            with col3:
                travel_date = st.date_input("Travel Date")
            with col4:
                travel_time = st.time_input("Travel Time")
            
            weather_condition = st.selectbox("Expected Weather", traffic_df['Weather Conditions'].unique())
            
            if st.button("Plan Journey", type="primary"):
                st.divider()
                
                # ---- Auto-render Map & Route (Single Submit Rule) ----
                from map_routing import geocode_location, get_route, get_route_info, create_route_map
                from streamlit_folium import st_folium
                
                with st.spinner("Calculating optimal route..."):
                    start_coords = geocode_location(start_location)
                    end_coords = geocode_location(end_location)
                    
                    if start_coords and end_coords:
                        route_coords = get_route(start_coords, end_coords)
                        route_info = get_route_info(start_coords, end_coords)
                        
                        if route_info:
                            # 1️⃣ ROUTE SUMMARY (ABOVE MAP)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Distance", f"{route_info['distance_km']} km")
                            with col2:
                                st.metric("Duration", f"{int(route_info['duration_min'])} min")
                            with col3:
                                st.metric("Avg Speed", f"{route_info['distance_km']/(route_info['duration_min']/60):.0f} km/h")
                        
                        # 2️⃣ INTERACTIVE MAP (MIDDLE)
                        route_map = create_route_map(
                            start_coords, end_coords, route_coords, 
                            start_location, end_location
                        )
                        st_folium(route_map, width=None, height=450, returned_objects=[])
                    else:
                        st.error("Unable to calculate route for the selected locations. Please try nearby landmarks.")
                
                st.divider()
                
                # Get congestion data for start and end for AI Advisory
                start_data = traffic_df[traffic_df['Area Name'] == start_location]
                end_data = traffic_df[traffic_df['Area Name'] == end_location]
                
                # Calculate congestion levels
                start_congestion = start_data['Congestion Level'].mean()
                end_congestion = end_data['Congestion Level'].mean()
                route_congestion = (start_congestion + end_congestion) / 2
                
                # Determine congestion category
                if route_congestion > 70:
                    congestion_cat = "High Congestion"
                    congestion_color = "red"
                elif route_congestion > 40:
                    congestion_cat = "Medium Congestion"
                    congestion_color = "orange"
                else:
                    congestion_cat = "Low Congestion"
                    congestion_color = "green"
                
                # Display prediction
                st.subheader("Route Analysis")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Congestion Level", congestion_cat)
                with col2:
                    avg_speed = start_data['Average Speed'].mean()
                    est_time = 30 + (route_congestion / 5)  # Simplified estimate
                    st.metric("Est. Travel Time", f"{est_time:.0f} mins")
                with col3:
                    duration = route_info.get('duration_min', 0)
                    distance = route_info.get('distance_km', 0)

                    if duration > 0:
                        avg_speed = distance / (duration / 60)
                        st.metric("Avg Speed", f"{avg_speed:.0f} km/h")
                    else:
                        st.metric("Avg Speed", "N/A")
                
                st.divider()
                
                # Reason for prediction
                st.subheader("Why This Prediction?")
                
                day_of_week = travel_date.weekday()
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                reasons = []
                if day_of_week < 5:
                    reasons.append(f"- **Weekday ({day_names[day_of_week]})**: Higher traffic expected during work hours")
                else:
                    reasons.append(f"- **Weekend ({day_names[day_of_week]})**: Generally lower traffic")
                
                hour = travel_time.hour
                if 8 <= hour <= 10 or 17 <= hour <= 20:
                    reasons.append("- **Peak Hours**: Rush hour traffic expected")
                else:
                    reasons.append("- **Off-Peak Hours**: Lower traffic expected")
                
                weather_impact = traffic_df[traffic_df['Weather Conditions'] == weather_condition]['Congestion Level'].mean()
                if weather_impact > 75:
                    reasons.append(f"- **Weather ({weather_condition})**: Increases congestion significantly")
                
                if start_data['Incident Reports'].sum() > start_data['Incident Reports'].mean() * 1.5:
                    reasons.append(f"- **{start_location}**: History of incidents in this area")
                
                for reason in reasons:
                    st.write(reason)
                
                st.divider()
                
                # Alternate Routes
                st.subheader("Alternate Routes")
                
                # Get areas sorted by congestion
                all_areas = traffic_df.groupby('Area Name')['Congestion Level'].mean().sort_values()
                
                # Find alternate routes through less congested areas
                alternate_areas = [a for a in all_areas.index if a not in [start_location, end_location]][:3]
                
                for i, alt_area in enumerate(alternate_areas, 1):
                    alt_congestion = all_areas[alt_area]
                    if alt_congestion > 70:
                        alt_cat = "High"
                        alt_color = "FAILED"
                    elif alt_congestion > 40:
                        alt_cat = "Medium"
                        alt_color = "WARNING"
                    else:
                        alt_cat = "Low"
                        alt_color = "success"
                    
                    with st.container(border=True):
                        st.write(f"**Route {i}**: {start_location} â†’ {alt_area} â†’ {end_location}")
                        st.write(f"Congestion: **{alt_cat}** ({alt_congestion:.1f}%)")
                        if i == 1 and alt_congestion < route_congestion:
                            st.success("RECOMMENDED - Best Route")
                
                st.divider()
                
                # Smart AI Tips
                st.subheader("Smart Travel Tips")
                
                tips = []
                
                # Best time to travel
                day_data = traffic_df[traffic_df['DayOfWeek'] == day_of_week]['Congestion Level']
                if day_data.mean() > 70:
                    tips.append("**Best Time**: Consider traveling before 7 AM or after 8 PM to avoid peak congestion")
                else:
                    tips.append("**Best Time**: Traffic is generally manageable throughout the day")
                
                # Fuel efficiency
                if route_congestion > 60:
                    tips.append("**Fuel Saving**: High congestion increases fuel consumption. Consider public transport")
                else:
                    tips.append("**Fuel Saving**: Maintain steady speed for optimal fuel efficiency")
                
                # Eco-friendly
                public_transport = traffic_df['Public Transport Usage'].mean()
                if public_transport > 30:
                    tips.append("**Eco-Friendly**: Good public transport availability in this route")
                
                # Safety
                if start_data['Incident Reports'].sum() > 10:
                    tips.append("**Safety**: Stay alert - higher incident reports in this area")
                
                for tip in tips:
                    st.info(tip)

    # =================== USER MAP (User role only) ===================
    elif selected == "Map":
        if st.session_state.user_role != "government":
            st.title("📍 Traffic Mobility Map")
            st.caption("Live Traffic and Congestion Overview")
            traffic_df = load_traffic_data()
            if traffic_df is not None:
                render_user_map(traffic_df)
        else:
            st.error("Access denied. This module is for Users only.")

    # =================== INFRASTRUCTURE PLANNING MAP (Government only) ===================
    elif selected == "Infrastructure Planning Map":
        if st.session_state.user_role == "government":
            st.title("🏗️ Infrastructure Planning")
            st.caption("AI-Driven Decision Support for Urban Development")
            traffic_df = load_traffic_data()
            if traffic_df is not None:
                render_gov_map_section(traffic_df)
        else:
            st.error("Access denied. This module is for Government Authority only.")

    # =================== DATASET ===================
    elif selected == "Dataset":
        st.title("📂 Traffic Repository")
        st.caption("Historical Traffic and Congestion Data Archive")
        
        if os.path.exists(DATASET_FILE):
            traffic_df = pd.read_csv(DATASET_FILE)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(traffic_df))
            with col2:
                st.metric("Total Columns", len(traffic_df.columns))
            with col3:
                st.metric("File Size", f"{os.path.getsize(DATASET_FILE) / 1024:.1f} KB")
            
            st.divider()
            
            with st.expander("Filter Options", expanded=False):
                columns_to_show = st.multiselect(
                    "Select columns to display",
                    options=traffic_df.columns.tolist(),
                    default=traffic_df.columns.tolist()
                )
                num_rows = st.slider("Number of rows to display", 10, 500, 100)
            
            st.subheader("Data Preview")
            if columns_to_show:
                st.dataframe(traffic_df[columns_to_show].head(num_rows), use_container_width=True)
            else:
                st.warning("Please select at least one column to display")
            
            st.divider()
            csv_data = traffic_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Dataset as CSV",
                data=csv_data,
                file_name="traffic_dataset.csv",
                mime="text/csv"
            )
        else:
            st.error(f"Dataset file '{DATASET_FILE}' not found!")

    # =================== TRAFFIC ANALYSIS ===================
    elif selected == "Traffic Analysis":
        st.title("📈 Statistical Analysis")
        st.caption("Advanced Patterns and Historical Traffic Trends")
        
        traffic_df = load_traffic_data()
        if traffic_df is not None:
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                selected_area = st.selectbox("Select Area", ["All"] + traffic_df['Area Name'].unique().tolist())
            with col2:
                selected_weather = st.selectbox("Select Weather", ["All"] + traffic_df['Weather Conditions'].unique().tolist())
            
            # Apply filters
            filtered_df = traffic_df.copy()
            if selected_area != "All":
                filtered_df = filtered_df[filtered_df['Area Name'] == selected_area]
            if selected_weather != "All":
                filtered_df = filtered_df[filtered_df['Weather Conditions'] == selected_weather]
            
            st.divider()
            
            # Traffic Volume Trend
            st.subheader("Traffic Volume Trend Over Time")
            daily_traffic = filtered_df.groupby('Date')['Traffic_Volume'].mean().reset_index()
            fig = px.line(daily_traffic, x='Date', y='Traffic_Volume', 
                         labels={'Traffic_Volume': 'Average Traffic Volume'})
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Peak Hours Analysis (by day of week)
                st.subheader("Congestion by Day of Week")
                day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                day_congestion = filtered_df.groupby('DayOfWeek')['Congestion Level'].mean()
                fig = px.bar(x=[day_names[i] for i in day_congestion.index], 
                            y=day_congestion.values,
                            color=day_congestion.values,
                            color_continuous_scale='RdYlGn_r',
                            labels={'x': 'Day', 'y': 'Avg Congestion'})
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Weather Impact
                st.subheader("Weather Impact on Congestion")
                weather_congestion = filtered_df.groupby('Weather Conditions')['Congestion Level'].mean().sort_values()
                fig = px.bar(x=weather_congestion.index, 
                            y=weather_congestion.values,
                            color=weather_congestion.values,
                            color_continuous_scale='RdYlGn_r',
                            labels={'x': 'Weather', 'y': 'Avg Congestion'})
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            # Road-wise Statistics
            st.subheader("Road-wise Traffic Statistics")
            road_stats = filtered_df.groupby('Road/Intersection Name').agg({
                'Traffic_Volume': 'mean',
                'Congestion Level': 'mean',
                'Average Speed': 'mean',
                'Incident Reports': 'sum'
            }).round(2)
            st.dataframe(road_stats, use_container_width=True)

    # =================== CONGESTION HEATMAP ===================
    elif selected == "Congestion Heatmap":
        traffic_df = load_traffic_data()
        
        if st.session_state.user_role == "government":
            # --- NEW INTERACTIVE MODE (PHASE 10) ---
            if traffic_df is not None:
                render_gov_congestion_map(traffic_df)
        else:
            # Standard Static Mode for Users
            st.title("🔥 Congestion Heatmap")
            st.caption("Visual Density Distribution across Bangalore Corridors")
            
            if traffic_df is not None:
                # Create heatmap data
                heatmap_data = traffic_df.pivot_table(
                    values='Congestion Level',
                    index='Area Name',
                    columns='Road/Intersection Name',
                    aggfunc='mean'
                ).fillna(0)
                
                # Plotly heatmap
                fig = go.Figure(data=go.Heatmap(
                    z=heatmap_data.values,
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    colorscale='RdYlGn_r',
                    colorbar=dict(title='Congestion Level')
                ))
                fig.update_layout(
                    title='Congestion Level by Area and Road',
                    xaxis_title='Road/Intersection',
                    yaxis_title='Area',
                    height=500
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                
                # Monthly Congestion Heatmap
                st.subheader("Monthly Congestion Pattern")
                monthly_area = traffic_df.pivot_table(
                    values='Congestion Level',
                    index='Area Name',
                    columns='Month',
                    aggfunc='mean'
                ).fillna(0)
                
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                fig2 = go.Figure(data=go.Heatmap(
                    z=monthly_area.values,
                    x=[month_names[m-1] for m in monthly_area.columns],
                    y=monthly_area.index,
                    colorscale='RdYlGn_r',
                    colorbar=dict(title='Congestion')
                ))
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

    # =================== PREDICT CONGESTION ===================
    elif selected == "Predict Congestion":
        st.title("🔮 Predictive Intelligence")
        st.caption("Machine Learning-Based Traffic Congestion Forecasting")
        
        # Check if model exists
        if not os.path.exists(MODEL_FILE):
            st.warning("Model not trained yet. Training model...")
            from traffic_model import train_model
            train_model()
            st.success("Model trained successfully!")
            st.rerun()
        
        # Load model
        model = joblib.load(MODEL_FILE)
        encoders = joblib.load(ENCODERS_FILE)
        scaler = joblib.load(SCALER_FILE)
        
        traffic_df = load_traffic_data()
        
        st.subheader("Enter Traffic Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            area_name = st.selectbox("Area Name", encoders['Area Name'].classes_)
            road_name = st.selectbox("Road/Intersection", encoders['Road/Intersection Name'].classes_)
            weather = st.selectbox("Weather Conditions", encoders['Weather Conditions'].classes_)
            roadwork = st.selectbox("Roadwork Activity", encoders['Roadwork and Construction Activity'].classes_)
            
        with col2:
            traffic_volume = st.number_input("Traffic Volume", min_value=0, max_value=10000, value=5000)
            avg_speed = st.number_input("Average Speed (km/h)", min_value=0.0, max_value=100.0, value=30.0)
            travel_time_index = st.number_input("Travel Time Index", min_value=0.0, max_value=5.0, value=1.5)
            road_capacity = st.number_input("Road Capacity Utilization (%)", min_value=0.0, max_value=100.0, value=70.0)
        
        col3, col4 = st.columns(2)
        
        with col3:
            incidents = st.number_input("Incident Reports", min_value=0, max_value=50, value=0)
            env_impact = st.number_input("Environmental Impact", min_value=0.0, max_value=100.0, value=50.0)
            public_transport = st.number_input("Public Transport Usage (%)", min_value=0.0, max_value=100.0, value=30.0)
            
        with col4:
            signal_compliance = st.number_input("Signal Compliance (%)", min_value=0.0, max_value=100.0, value=80.0)
            parking_usage = st.number_input("Parking Usage (%)", min_value=0.0, max_value=100.0, value=50.0)
            pedestrian_count = st.number_input("Pedestrian Count", min_value=0, max_value=5000, value=500)
        
        day = st.slider("Day of Month", 1, 31, 15)
        month = st.slider("Month", 1, 12, 6)
        day_of_week = st.slider("Day of Week (0=Mon, 6=Sun)", 0, 6, 2)
        
        if st.button("Predict Congestion", type="primary"):
            # Encode inputs
            area_encoded = encoders['Area Name'].transform([area_name])[0]
            road_encoded = encoders['Road/Intersection Name'].transform([road_name])[0]
            weather_encoded = encoders['Weather Conditions'].transform([weather])[0]
            roadwork_encoded = encoders['Roadwork and Construction Activity'].transform([roadwork])[0]
            
            features = np.array([[
                area_encoded, road_encoded,
                traffic_volume, avg_speed, travel_time_index, road_capacity,
                incidents, env_impact, public_transport, signal_compliance,
                parking_usage, pedestrian_count, weather_encoded, roadwork_encoded,
                day, month, day_of_week
            ]])
            
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)
            probability = model.predict_proba(features_scaled)[0]
            
            congestion_level = encoders['target'].inverse_transform(prediction)[0]
            
            st.divider()
            st.subheader("Prediction Result")
            
            col1, col2, col3 = st.columns(3)
            
            # Color based on congestion level
            if congestion_level == "Low":
                color = "green"
            elif congestion_level == "Medium":
                color = "orange"
            else:
                color = "red"
            
            with col1:
                st.metric("Predicted Congestion", congestion_level)
            with col2:
                st.metric("Confidence", f"{max(probability)*100:.1f}%")
            with col3:
                st.metric("Risk Level", "High" if congestion_level == "High" else "Normal")
            
            # Probability breakdown
            st.write("**Probability Distribution:**")
            prob_df = pd.DataFrame({
                'Level': encoders['target'].classes_,
                'Probability': probability
            })
            fig = px.bar(prob_df, x='Level', y='Probability', color='Level',
                        color_discrete_map={'Low': 'green', 'Medium': 'orange', 'High': 'red'})
            st.plotly_chart(fig, use_container_width=True)

    # =================== ALERTS ===================
    elif selected == "Alerts":
        st.title("⚠️ System Alerts")
        st.caption("Critical Notifications and Mitigation Recommendations")
        
        traffic_df = load_traffic_data()
        if traffic_df is not None:
            
            # High congestion zones
            st.subheader("High Congestion Zones (Historical)")
            high_congestion = traffic_df[traffic_df['Congestion Level'] > 80].groupby(
                ['Area Name', 'Road/Intersection Name']
            ).agg({
                'Congestion Level': 'mean',
                'Traffic_Volume': 'mean',
                'Incident Reports': 'sum'
            }).round(2).sort_values('Congestion Level', ascending=False).head(10)
            
            if not high_congestion.empty:
                st.dataframe(high_congestion, use_container_width=True)
            
            st.divider()
            
            # Recommendations
            st.subheader("Mobility Recommendations")
            
            # Best travel times
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Best Days to Travel:**")
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                best_days = traffic_df.groupby('DayOfWeek')['Congestion Level'].mean().sort_values().head(3)
                for idx, (day_idx, congestion) in enumerate(best_days.items(), 1):
                    st.write(f"{idx}. {day_names[day_idx]} (Avg Congestion: {congestion:.1f}%)")
            
            with col2:
                st.write("**Least Congested Areas:**")
                best_areas = traffic_df.groupby('Area Name')['Congestion Level'].mean().sort_values().head(3)
                for idx, (area, congestion) in enumerate(best_areas.items(), 1):
                    st.write(f"{idx}. {area} (Avg Congestion: {congestion:.1f}%)")
            
            st.divider()
            
            # Weather advisories
            st.subheader("Weather Impact Advisory")
            weather_impact = traffic_df.groupby('Weather Conditions')['Congestion Level'].mean().sort_values(ascending=False)
            
            worst_weather = weather_impact.idxmax()
            best_weather = weather_impact.idxmin()
            
            st.info(f"**Highest congestion during:** {worst_weather} weather ({weather_impact[worst_weather]:.1f}% avg)")
            st.success(f"**Lowest congestion during:** {best_weather} weather ({weather_impact[best_weather]:.1f}% avg)")
            
            # Incident hotspots
            st.divider()
            st.subheader("Incident Hotspots")
            incident_hotspots = traffic_df.groupby('Area Name')['Incident Reports'].sum().sort_values(ascending=False)
            
            fig = px.pie(values=incident_hotspots.values, names=incident_hotspots.index,
                        title='Incident Distribution by Area')
            st.plotly_chart(fig, use_container_width=True)

    # =================== PROFILE ===================
    elif selected == "Profile":
        st.title("👤 User Profile")
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Name:**")
                st.write("**Email:**")
                st.write("**Role:**")
                st.write("**Account Type:**")
            with col2:
                st.write(st.session_state.user_name)
                # We don't store email in session state yet, but we can get it if needed.
                # For now, let's just show role and name.
                st.write("---") 
                st.write("Government Authority" if st.session_state.user_role == "government" else "Regular User")
                st.info("Your access is restricted based on your assigned role.")
        
        if st.button("Edit Details"):
            st.warning("Profile editing is currently disabled.")

    # =================== LOGOUT ===================
    elif selected == "Logout":
        st.session_state.logged_in = False
        st.session_state.auth_page = "login"
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()
