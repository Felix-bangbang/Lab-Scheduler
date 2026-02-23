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
.room-card {
    background: rgba(173, 196, 215, 0.35);
    border: 2px solid rgba(80, 120, 160, 0.55);
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 28px 12px;
    min-height: 190px;
    text-align: center;
}

.room-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1a3a5c;
    letter-spacing: 0.04em;
    margin-bottom: 6px;
    text-transform: uppercase;
}
.room-number {
    font-size: 2.2rem;
    font-weight: 300;
    color: #2c5f8a;
    letter-spacing: 0.08em;
}
.room-tag {
    font-size: 0.72rem;
    color: #3a6e99;
    margin-top: 8px;
    font-style: italic;
}
.stAlert { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Room Configuration ────────────────────────────────────────────────────────
ROOMS = {
    "427": {
        "name": "EEG Spatial",
        "number": "427",
        "worksheet": "EEG_427",
        "notice": "💡 Please clean EEG electrodes and return the amplifier to its storage case after your session.",
        "equipment_options": ["EEG System A", "EEG System B", "Both Systems (Hyperscanning)"],
        "color_map": {"default": "#27ae60", "B": "#f39c12", "Both": "#e74c3c"},
        "tag": "🔵 EEG · Click to book",
    },
    "426": {
        "name": "EEG Hyperscanning",
        "number": "426",
        "worksheet": "EEG_426",
        "notice": "💡 Please clean EEG electrodes and return both amplifiers to their storage cases after your session.",
        "equipment_options": ["EEG System A", "EEG System B", "Both Systems (Hyperscanning)"],
        "color_map": {"default": "#27ae60", "B": "#f39c12", "Both": "#e74c3c"},
        "tag": "🟢 EEG · Click to book",
    },
    "429": {
        "name": "fNIRS Hyperscanning",
        "number": "429",
        "worksheet": "fNIRS_429",
        "notice": "💡 Please ensure fNIRS caps are cleaned and returned to the charging station after your session.",
        "equipment_options": ["fNIRS Frontal A (25330)", "fNIRS Frontal B (25215)", "Both (Hyperscanning)"],
        "color_map": {"default": "#3788d8", "B": "#8e44ad", "Both": "#e74c3c"},
        "tag": "🔴 fNIRS · Click to book",
    },
    "430": {
        "name": "fNIRS Hyperscanning",
        "number": "430",
        "worksheet": "fNIRS_430",
        "notice": "💡 Please ensure fNIRS caps are cleaned and returned to the charging station after your session.",
        "equipment_options": ["fNIRS Frontal A (25330)", "fNIRS Frontal B (25215)", "Both (Hyperscanning)"],
        "color_map": {"default": "#3788d8", "B": "#8e44ad", "Both": "#e74c3c"},
        "tag": "🟣 fNIRS · Click to book",
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

def check_conflict(df, date_str, start_time_str, equipment):
    if df.empty:
        return False
    subset = df[(df["Date"] == date_str) & (df["Start_Time"] == start_time_str)]
    if subset.empty:
        return False
    for booked in subset["Equipment"].tolist():
        if equipment == booked or "Both" in equipment or "Both" in booked:
            return True
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
    <div style="padding: 10px 0 6px 0;">
        <span style="font-size:2.0rem; font-weight:800; color:#1a3a5c; letter-spacing:0.04em;">
            COLLECTIVE MINDS Lab
        </span><br>
        <span style="font-size:1.0rem; color:#4a7fa5; font-style:italic;">
            Room Booking System &nbsp;·&nbsp; Click a room to view schedule & book
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Blueprint background ───────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #c8d8e8 0%, #dce8f0 50%, #c5d5e5 100%);
        border: 2.5px solid #6a9ab8;
        border-radius: 10px;
        padding: 28px 28px 20px 28px;
    ">
    <p style="text-align:center; color:#3a6080; font-size:0.8rem; margin:0 0 14px 0; letter-spacing:0.12em; text-transform:uppercase;">
        4th Floor · Building A
    </p>
    """, unsafe_allow_html=True)

    # ── ROW 1: 427 | 428 | 429 ───────────────────────────────────────────────
    r1c1, r1c2, r1c3 = st.columns([1, 1, 1], gap="small")

    with r1c1:
        st.markdown("""
        <div class="room-card">
            <div class="room-name">EEG Spatial</div>
            <div class="room-number">427</div>
            <div class="room-tag">🔵 EEG</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("📅 Book / View Schedule", key="btn_427", use_container_width=True, type="primary"):
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
            <div class="room-tag">🔴 fNIRS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("📅 Book / View Schedule", key="btn_429", use_container_width=True, type="primary"):
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
            <div class="room-tag">🟢 EEG</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("📅 Book / View Schedule", key="btn_426", use_container_width=True, type="primary"):
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
            <div class="room-tag">🟣 fNIRS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("📅 Book / View Schedule", key="btn_430", use_container_width=True, type="primary"):
            st.session_state.page = "430"
            st.rerun()

    # Close blueprint div
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
            <span style="font-size:1.6rem; font-weight:800; color:#1a3a5c;">
                Room {cfg['number']} — {cfg['name']}
            </span>
        </div>
        """, unsafe_allow_html=True)
    with hcol2:
        if st.button("⬅️ Floor Plan", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

    st.info(cfg["notice"])

    col_control, col_calendar = st.columns([1, 2.5], gap="large")

    # ── Left: Controls ────────────────────────────────────────────────────────
    with col_control:
        st.markdown('<div style="font-size:1.05rem; font-weight:700; margin-bottom:10px; color:#1a3a5c;">🛠️ Manage Bookings</div>', unsafe_allow_html=True)
        tab_book, tab_cancel = st.tabs(["📅 Book Slot", "❌ Cancel Slot"])

        with tab_book:
            with st.container(border=True):
                researcher_name = st.text_input("Researcher Name", placeholder="e.g. Shane", key=f"name_{room_id}")
                selected_equipment = st.selectbox("Select Equipment", cfg["equipment_options"], key=f"equip_{room_id}")
                booking_date = st.date_input("Date", min_value=datetime.today(), key=f"date_{room_id}")
                booking_date_str = booking_date.strftime("%Y-%m-%d")
                start_time_str = st.selectbox("Start Time (1 Hour)", TIME_STRINGS, index=1, key=f"time_{room_id}")

                try:
                    start_dt = datetime.strptime(str(start_time_str).strip(), "%H:%M")
                    end_time_str = (start_dt + timedelta(hours=1)).strftime("%H:%M")
                except Exception:
                    st.error("Time format error.")
                    st.stop()

                if st.button("Confirm Booking", type="primary", use_container_width=True, key=f"confirm_{room_id}"):
                    if not researcher_name:
                        st.warning("Please enter your name.")
                    else:
                        df = get_data(worksheet)
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
                            update_data(pd.concat([df, new_entry], ignore_index=True), worksheet)
                            st.success("✅ Booking Confirmed!")
                            st.rerun()

        with tab_cancel:
            st.write("Select a booking below to remove it.")
            df = get_data(worksheet)
            if not df.empty:
                df = df.fillna("")
                df["display_label"] = (
                    df["Date"].astype(str) + " | " +
                    df["Start_Time"].astype(str) + " | " +
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
                calendar_events.append({
                    "title": f"{row['Researcher']} — {row['Equipment']}",
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
