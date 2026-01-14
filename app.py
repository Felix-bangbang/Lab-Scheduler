import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# --- 1. Page Config ---
st.set_page_config(layout="wide", page_title="fNIRS Slot Booking", page_icon="🧠")

# Custom CSS for better spacing and styling
st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .main-header { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Constants & Helpers ---
EQUIPMENT_OPTIONS = [
    "fNIRS Frontal A (25330)", 
    "fNIRS Frontal B (25215)", 
    "Both (Hyperscanning)"
]

# Generate standard time strings "09:00", "10:00"...
TIME_STRINGS = [f"{hour:02d}:00" for hour in range(8, 21)] # Extended to 8am - 8pm

def get_data():
    """Fetch data from Google Sheets"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet="Sheet1", ttl=0) # Ensure worksheet name matches your GSheet tab
        expected_cols = ["Researcher", "Equipment", "Date", "Start_Time", "End_Time", "Created_At"]
        # Handle empty sheet case
        if df.empty or not set(expected_cols).issubset(df.columns):
            return pd.DataFrame(columns=expected_cols)
        # Ensure Date is string for consistency
        df["Date"] = df["Date"].astype(str)
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

def update_data(df):
    """Write updated dataframe back to Google Sheets"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="Sheet1", data=df)

def check_conflict(df, date_str, start_time_str, equipment):
    """Check for booking conflicts"""
    if df.empty:
        return False
    
    # Filter by date and time
    conflict_subset = df[
        (df["Date"] == date_str) & 
        (df["Start_Time"] == start_time_str)
    ]
    
    if conflict_subset.empty:
        return False

    booked_equipments = conflict_subset["Equipment"].tolist()
    
    for booked in booked_equipments:
        if equipment == booked: return True
        if equipment == "Both (Hyperscanning)": return True 
        if booked == "Both (Hyperscanning)": return True
            
    return False

# --- 3. Layout ---
st.info("💡 **Lab Notice:** Please ensure fNIRS caps are cleaned and returned to the charging station after your session.")

col_control, col_calendar = st.columns([1, 2.5], gap="large")

# --- 4. Left Column: Control Panel ---
with col_control:
    st.markdown('<div class="main-header">🛠️ Management</div>', unsafe_allow_html=True)
    
    # Use Tabs for Booking vs Canceling
    tab_book, tab_cancel = st.tabs(["🧠 Book Slot", "❌ Cancel Slot"])

    # --- TAB 1: BOOKING ---
    with tab_book:
        with st.container(border=True):
            researcher_name = st.text_input("Researcher Name", placeholder="e.g. Shane")
            selected_equipment = st.selectbox("Select Equipment", EQUIPMENT_OPTIONS)
            booking_date = st.date_input("Date", min_value=datetime.today())
            booking_date_str = booking_date.strftime("%Y-%m-%d")
            
            start_time_str = st.selectbox("Start Time (1 Hour)", TIME_STRINGS, index=1)
            
            # Calculate End Time
            try:
                start_dt = datetime.strptime(str(start_time_str).strip(), "%H:%M")
                end_time_str = (start_dt + timedelta(hours=1)).strftime("%H:%M")
            except:
                st.error("Time format error.")
                st.stop()

            if st.button("Confirm Booking", type="primary", use_container_width=True):
                if not researcher_name:
                    st.warning("Please enter your name.")
                else:
                    df = get_data()
                    if check_conflict(df, booking_date_str, start_time_str, selected_equipment):
                        st.error(f"⚠️ Conflict! {selected_equipment} is already booked at this time.")
                    else:
                        new_entry = pd.DataFrame([{
                            "Researcher": researcher_name,
                            "Equipment": selected_equipment,
                            "Date": booking_date_str,
                            "Start_Time": start_time_str,
                            "End_Time": end_time_str,
                            "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        update_data(pd.concat([df, new_entry], ignore_index=True))
                        st.success("✅ Booking Confirmed!")
                        st.rerun()

    # --- TAB 2: CANCELLATION ---
    with tab_cancel:
        st.write("Select a booking below to remove it.")
        df = get_data()
        
        # Filter for future bookings only (optional, keeps list clean)
        today_str = datetime.now().strftime("%Y-%m-%d")
        if not df.empty:
            # Create a readable label for the selectbox
            df = df.fillna("") 
            df['display_label'] = (
                df['Date'].astype(str) + " | " + 
                df['Start_Time'].astype(str) + " | " + 
                df['Researcher'].astype(str) + " | " + 
                df['Equipment'].astype(str)
            )
            
            # Sort by date (reverse) so newest is top
            df = df.sort_values(by="Date", ascending=False)
            
            booking_to_delete = st.selectbox(
                "Select Booking to Cancel:", 
                options=df.index, 
                format_func=lambda x: df.loc[x, 'display_label']
            )

            if st.button("🗑️ Delete Selected Booking", type="primary"):
                # Drop the row by index
                df_new = df.drop(index=booking_to_delete).drop(columns=['display_label'])
                update_data(df_new)
                st.success("Booking cancelled successfully.")
                st.rerun()
        else:
            st.info("No bookings found in the database.")

# --- 5. Right Column: Calendar ---
with col_calendar:
    df = get_data()
    calendar_events = []
    
    if not df.empty:
        for index, row in df.iterrows():
            # Color coding
            color = "#3788d8" # Blue (A)
            if "Frontal B" in row["Equipment"]: color = "#8e44ad" # Purple (B)
            elif "Both" in row["Equipment"]: color = "#e74c3c" # Red (Both)
            
            calendar_events.append({
                "title": f"{row['Researcher']} ({row['Equipment']})", # Short title
                "start": f"{row['Date']}T{row['Start_Time']}",
                "end": f"{row['Date']}T{row['End_Time']}",
                "backgroundColor": color,
                "borderColor": color,
                # Extended props allow us to show details on click
                "extendedProps": {
                    "researcher": row['Researcher'],
                    "equipment": row['Equipment'],
                    "time": f"{row['Start_Time']} - {row['End_Time']}"
                }
            })

    # Calendar Configuration
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "timeGridWeek",
        "slotMinTime": "08:00:00", # Start day earlier
        "slotMaxTime": "20:00:00", # End day later
        "height": 700, # Taller calendar
        "contentHeight": 'auto',
        "aspectRatio": 2,
    }
    
    # Render Calendar & Capture Click Event
    cal_state = calendar(events=calendar_events, options=calendar_options)

    # --- 6. Event Detail Popup (Solving the Visibility Issue) ---
    if cal_state.get("eventClick"):
        event_data = cal_state["eventClick"]["event"]
        props = event_data.get("extendedProps", {})
        
        # Use a nice success box or expander to show details when clicked
        with st.container(border=True):
            st.markdown(f"### 📌 Selected Booking Details")
            c1, c2, c3 = st.columns(3)
            c1.metric("Researcher", props.get('researcher', 'Unknown'))
            c2.metric("Date", datetime.fromisoformat(event_data['start']).strftime('%Y-%m-%d'))
            c3.metric("Time", props.get('time', 'Unknown'))
            st.info(f"**Equipment:** {props.get('equipment', 'Unknown')}")
