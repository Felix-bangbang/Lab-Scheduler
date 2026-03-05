import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Collective Minds Lab", page_icon="🧠")

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&family=DM+Serif+Display:ital@0;1&display=swap');

/* ── Full-page pastel mesh gradient background ── */
[data-testid="stAppViewContainer"] {
    background: 
        radial-gradient(ellipse at 15% 85%, rgba(178, 213, 210, 0.55) 0%, transparent 55%),
        radial-gradient(ellipse at 80% 10%, rgba(230, 200, 210, 0.5) 0%, transparent 50%),
        radial-gradient(ellipse at 55% 40%, rgba(240, 185, 170, 0.45) 0%, transparent 45%),
        radial-gradient(ellipse at 90% 75%, rgba(195, 220, 235, 0.5) 0%, transparent 50%),
        radial-gradient(ellipse at 30% 20%, rgba(210, 230, 240, 0.6) 0%, transparent 50%),
        linear-gradient(160deg, #e8f4f8 0%, #f5ede8 50%, #eaf4f2 100%);
    background-attachment: fixed;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* Make the main block transparent so background shows */
[data-testid="stMain"] > div,
[data-testid="block-container"] {
    background: transparent !important;
}

/* ── Room cards — glassmorphism ── */
.room-card {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1.5px solid rgba(255, 255, 255, 0.75);
    border-radius: 18px;
    box-shadow: 0 4px 24px rgba(160, 140, 150, 0.12), 0 1px 4px rgba(200, 160, 150, 0.08);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 16px;
    min-height: 190px;
    text-align: center;
    transition: box-shadow 0.25s, transform 0.2s, background 0.25s;
}
.room-card:hover {
    background: rgba(255, 255, 255, 0.62);
    box-shadow: 0 8px 36px rgba(180, 140, 150, 0.18);
    transform: translateY(-2px);
}

.room-name {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    color: #6b5b6e;
    letter-spacing: 0.14em;
    margin-bottom: 6px;
    text-transform: uppercase;
}
.room-number {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    font-weight: 400;
    color: #4a5568;
    letter-spacing: 0.04em;
    line-height: 1.1;
}
.room-tag {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.70rem;
    color: #9b8fa0;
    margin-top: 10px;
    font-style: italic;
    letter-spacing: 0.04em;
}

/* ── Floor plan wrapper ── */
.floor-wrapper {
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1.5px solid rgba(255, 255, 255, 0.55);
    border-radius: 24px;
    padding: 32px 32px 24px 32px;
    box-shadow: 0 8px 40px rgba(160, 130, 140, 0.10);
}

/* ── Book button override ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #d4a5b0 0%, #a8c4d4 100%) !important;
    border: none !important;
    border-radius: 30px !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    box-shadow: 0 2px 12px rgba(180, 140, 155, 0.28) !important;
    transition: opacity 0.2s, transform 0.15s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

.stAlert { border-radius: 14px; }
</style>
""", unsafe_allow_html=True)

# ── Room Configuration ────────────────────────────────────────────────────────
ROOMS = {
    "427": {
        "name": "EEG Spatial",
        "number": "427",
        "worksheet": "EEG_427",
        "notice": "💡 Please ensure EEG caps are cleaned and returned to the charging station after your session.",
        "equipment_options": ["EEG System A", "EEG System B", "Both Systems (Hyperscanning)", "Behavioural"],
        "color_map": {"default": "#27ae60", "B": "#f39c12", "Both": "#e74c3c"},
        "tag": "EEG · Click to book",
    },
    "426": {
        "name": "EEG Hyperscanning",
        "number": "426",
        "worksheet": "EEG_426",
        "notice": "💡 Please ensure EEG caps are cleaned and returned to the charging station after your session.",
        "equipment_options": ["EEG System A", "EEG System B", "Both Systems (Hyperscanning)", "Behavioural"],
        "color_map": {"default": "#27ae60", "B": "#f39c12", "Both": "#e74c3c"},
        "tag": "EEG · Click to book",
    },
    "429": {
        "name": "fNIRS Hyperscanning",
        "number": "429",
        "worksheet": "fNIRS_429",
        "notice": "💡 Please ensure fNIRS caps are cleaned and returned to the charging station after your session.",
        "equipment_options": ["fNIRS Frontal A (25330)", "fNIRS Frontal B (25215)", "Both (Hyperscanning)"],
        "color_map": {"default": "#3788d8", "B": "#8e44ad", "Both": "#e74c3c"},
        "tag": "fNIRS · Click to book",
    },
    "430": {
        "name": "fNIRS Hyperscanning",
        "number": "430",
        "worksheet": "fNIRS_430",
        "notice": "💡 Please ensure fNIRS caps are cleaned and returned to the charging station after your session.",
        "equipment_options": ["fNIRS Frontal A (25330)", "fNIRS Frontal B (25215)", "Both (Hyperscanning)"],
        "color_map": {"default": "#3788d8", "B": "#8e44ad", "Both": "#e74c3c"},
        "tag": "fNIRS · Click to book",
    },
}

TIME_STRINGS = [f"{hour:02d}:00" for hour in range(8, 20)]

# ── Session State ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

# ── Data Helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def get_data(worksheet: str):
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        df = conn.read(worksheet=worksheet, ttl=0)
        expected_cols = ["Researcher", "Equipment", "Date", "Start_Time", "End_Time", "Created_At"]
        if df.empty or not set(expected_cols).issubset(df.columns):
            return pd.DataFrame(columns=expected_cols)
        df["Date"] = df["Date"].astype(str)
        return df.fillna("")
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

def update_data(df, worksheet: str):
    conn = st.connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet=worksheet, data=df)
    st.cache_data.clear()

def check_conflict(df, date_str, start_time_str, end_time_str, equipment):
    """Check for time slot conflicts (supports multi-hour bookings)"""
    if df.empty:
        return False
    
    # Parse the new booking time slot
    try:
        new_start = datetime.strptime(start_time_str, "%H:%M")
        new_end = datetime.strptime(end_time_str, "%H:%M")
    except:
        return False
    
    # Check all bookings on the same day
    subset = df[df["Date"] == date_str]
    
    for _, row in subset.iterrows():
        # Check equipment conflict
        booked_equipment = row["Equipment"]
        equipment_conflict = (
            equipment == booked_equipment or 
            "Both" in equipment or 
            "Both" in booked_equipment
        )
        
        if not equipment_conflict:
            continue
        
        # Check time slot overlap
        try:
            booked_start = datetime.strptime(row["Start_Time"], "%H:%M")
            booked_end = datetime.strptime(row["End_Time"], "%H:%M")
            
            # Time overlap condition: new_start < booked_end AND new_end > booked_start
            time_overlap = (new_start < booked_end) and (new_end > booked_start)
            
            if time_overlap:
                return True
        except:
            continue
    
    return False

def get_event_color(equipment, color_map):
    if "B" in equipment and "Both" not in equipment:
        return color_map["B"]
    elif "Both" in equipment:
        return color_map["Both"]
    return color_map["default"]


# ═════════════════════════════════════════════════════════════════════════════
# PAGE: HOME — Interactive Floor Plan
# ═════════════════════════════════════════════════════════════════════════════
def render_home():
    # ── Title ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding: 18px 0 8px 0;">
        <span style="font-family:'DM Serif Display', serif; font-size:2.4rem; font-weight:400;
                     background: linear-gradient(135deg, #b07a8a, #7a9eb5, #8fbfb5);
                     -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                     background-clip: text; letter-spacing:0.02em;">
            Collective Minds Lab
        </span><br>
        <span style="font-family:'DM Sans',sans-serif; font-size:0.95rem; color:#9b8fa0; font-style:italic; letter-spacing:0.04em;">
            Room Booking System &nbsp;·&nbsp; Click a room to view schedule &amp; book
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Blueprint background ───────────────────────────────────────────────────
    st.markdown("""
    <div class="floor-wrapper">
    <p style="text-align:center; font-family:'DM Sans',sans-serif; color:#b0a0b0;
              font-size:0.75rem; margin:0 0 20px 0; letter-spacing:0.18em; text-transform:uppercase;">
        4th Floor · TCIN · Lloyd Institute
    </p>
    """, unsafe_allow_html=True)

    # ── ROW 1: 427 | 428 | 429 ───────────────────────────────────────────────
    r1c1, r1c2, r1c3 = st.columns([1, 1, 1], gap="small")

    with r1c1:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">EEG Spatial</div>
            <div class="room-number">427</div>
            <div class="room-tag">EEG</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Book / View Schedule", key="btn_427", use_container_width=True, type="primary"):
            st.session_state.page = "427"
            st.rerun()

    with r1c2:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">Store</div>
            <div class="room-number">428</div>
            <div class="room-tag">Storage</div>
        </div>
        """, unsafe_allow_html=True)

    with r1c3:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">fNIRS Hyperscanning</div>
            <div class="room-number">429</div>
            <div class="room-tag">fNIRS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Book / View Schedule", key="btn_429", use_container_width=True, type="primary"):
            st.session_state.page = "429"
            st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── ROW 2: 426 | 425 | 430 ───────────────────────────────────────────────
    r2c1, r2c2, r2c3 = st.columns([1, 1, 1], gap="small")

    with r2c1:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">EEG Hyperscanning</div>
            <div class="room-number">426</div>
            <div class="room-tag">EEG</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Book / View Schedule", key="btn_426", use_container_width=True, type="primary"):
            st.session_state.page = "426"
            st.rerun()

    with r2c2:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">Foyer</div>
            <div class="room-number">425</div>
            <div class="room-tag">Common area</div>
        </div>
        """, unsafe_allow_html=True)

    with r2c3:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">fNIRS Hyperscanning</div>
            <div class="room-number">430</div>
            <div class="room-tag">fNIRS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Book / View Schedule", key="btn_430", use_container_width=True, type="primary"):
            st.session_state.page = "430"
            st.rerun()

    # Close floor-wrapper div
    st.markdown("</div>", unsafe_allow_html=True)




# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ROOM BOOKING & CALENDAR
# ═════════════════════════════════════════════════════════════════════════════
def render_room(room_id: str):
    cfg = ROOMS[room_id]
    worksheet = cfg["worksheet"]

    # Header
    hcol1, hcol2 = st.columns([5, 1])
    with hcol1:
        st.markdown(f"""
        <div style="padding: 6px 0 2px 0;">
            <span style="font-family:'DM Serif Display', serif; font-size:1.7rem; font-weight:400;
                         background: linear-gradient(135deg, #b07a8a, #7a9eb5);
                         -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                         background-clip: text;">
                Room {cfg['number']} — {cfg['name']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with hcol2:
        if st.button("Home Page", use_container_width=True, type="primary"):
            st.session_state.page = "home"
            st.rerun()

    st.info(cfg["notice"])

    col_control, col_calendar = st.columns([1, 2.5], gap="large")

    # ── Left: Controls ────────────────────────────────────────────────────────
    with col_control:
        st.markdown('<div style="font-size:1.05rem; font-weight:700; margin-bottom:10px; color:#6b5b6e;">🛠️ Manage Bookings</div>', unsafe_allow_html=True)
        tab_book, tab_cancel = st.tabs(["📅 Book Slot", "❌ Cancel Slot"])

        with tab_book:
            with st.container(border=True):
                researcher_name = st.text_input("Researcher Name", placeholder="e.g. XSFang", key=f"name_{room_id}")
                selected_equipment = st.selectbox("Select Equipment", cfg["equipment_options"], key=f"equip_{room_id}")
                booking_date = st.date_input("Date", min_value=datetime.today(), key=f"date_{room_id}")
                booking_date_str = booking_date.strftime("%Y-%m-%d")
                start_time_str = st.selectbox("Start Time", TIME_STRINGS, index=1, key=f"time_{room_id}")
                duration_hours = st.selectbox("Duration (Hours)", options=[1, 2, 3, 4, 5, 6, 7, 8], index=0, key=f"duration_{room_id}")

                try:
                    start_dt = datetime.strptime(str(start_time_str).strip(), "%H:%M")
                    end_dt = start_dt + timedelta(hours=duration_hours)
                    end_time_str = end_dt.strftime("%H:%M")
                    
                    # Display booking time slot
                    st.caption(f"📅 Booking: **{start_time_str}** → **{end_time_str}** ({duration_hours} hour{'s' if duration_hours > 1 else ''})")
                    
                    # Check if end time exceeds 20:00
                    if end_dt.hour > 20 or (end_dt.hour == 20 and end_dt.minute > 0):
                        st.warning(f"⚠️ Selected duration extends beyond 20:00 (lab closing time).")
                except Exception:
                    st.error("Time format error.")
                    st.stop()

                if st.button("Confirm Booking", type="primary", use_container_width=True, key=f"confirm_{room_id}"):
                    if not researcher_name:
                        st.warning("Please enter your name.")
                    else:
                        df = get_data(worksheet)
                        if check_conflict(df, booking_date_str, start_time_str, end_time_str, selected_equipment):
                            st.error(f"⚠️ Conflict! {selected_equipment} is already booked during this time period.")
                        else:
                            new_entry = pd.DataFrame([{
                                "Researcher": researcher_name,
                                "Equipment": selected_equipment,
                                "Date": booking_date_str,
                                "Start_Time": start_time_str,
                                "End_Time": end_time_str,
                                "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            update_data(pd.concat([df, new_entry], ignore_index=True), worksheet)
                            st.success(f"✅ Booking Confirmed! {start_time_str} - {end_time_str}")
                            st.rerun()

        with tab_cancel:
            st.write("Select a booking below to remove it.")
            df = get_data(worksheet)
            if not df.empty:
                df = df.fillna("")
                df["display_label"] = (
                    df["Date"].astype(str) + " | " +
                    df["Start_Time"].astype(str) + "-" +
                    df["End_Time"].astype(str) + " | " +
                    df["Researcher"].astype(str) + " | " +
                    df["Equipment"].astype(str)
                )
                df = df.sort_values(by="Date", ascending=False)
                booking_to_delete = st.selectbox(
                    "Select Booking to Cancel:",
                    options=df.index,
                    format_func=lambda x: df.loc[x, "display_label"],
                    key=f"cancel_select_{room_id}"
                )
                if st.button("🗑️ Delete Selected Booking", type="primary", key=f"delete_{room_id}"):
                    df_new = df.drop(index=booking_to_delete).drop(columns=["display_label"])
                    update_data(df_new, worksheet)
                    st.success("Booking cancelled successfully.")
                    st.rerun()
            else:
                st.info("No bookings found for this room.")

    # ── Right: Calendar ───────────────────────────────────────────────────────
    with col_calendar:
        df = get_data(worksheet)
        calendar_events = []

        if not df.empty:
            for _, row in df.iterrows():
                color = get_event_color(row["Equipment"], cfg["color_map"])
                
                # Calculate duration
                try:
                    start = datetime.strptime(row["Start_Time"], "%H:%M")
                    end = datetime.strptime(row["End_Time"], "%H:%M")
                    duration = (end - start).seconds // 3600
                    duration_text = f"{duration}h"
                except:
                    duration_text = ""
                
                calendar_events.append({
                    "title": f"{row['Researcher']} — {row['Equipment']} ({duration_text})",
                    "start": f"{row['Date']}T{row['Start_Time']}",
                    "end": f"{row['Date']}T{row['End_Time']}",
                    "backgroundColor": color,
                    "borderColor": color,
                    "extendedProps": {
                        "researcher": row["Researcher"],
                        "equipment": row["Equipment"],
                        "time": f"{row['Start_Time']} - {row['End_Time']}"
                    }
                })

        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            "initialView": "timeGridWeek",
            "slotMinTime": "08:00:00",
            "slotMaxTime": "20:00:00",
            "height": 700,
            "contentHeight": "auto",
            "aspectRatio": 2,
        }

        cal_state = calendar(events=calendar_events, options=calendar_options)

        if cal_state.get("eventClick"):
            event_data = cal_state["eventClick"]["event"]
            props = event_data.get("extendedProps", {})
            with st.container(border=True):
                st.markdown("### 📌 Selected Booking Details")
                c1, c2, c3 = st.columns(3)
                c1.metric("Researcher", props.get("researcher", "Unknown"))
                c2.metric("Date", datetime.fromisoformat(event_data["start"]).strftime("%Y-%m-%d"))
                c3.metric("Time", props.get("time", "Unknown"))
                st.info(f"**Equipment:** {props.get('equipment', 'Unknown')}")


# ═════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "home":
    render_home()
elif st.session_state.page in ROOMS:
    render_room(st.session_state.page)
else:
    st.session_state.page = "home"
    st.rerun()


