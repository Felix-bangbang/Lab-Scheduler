import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, time
from streamlit_calendar import calendar

# --- 1. 页面配置 ---
st.set_page_config(layout="wide", page_title="fNIRS Lab Booking", page_icon="🧠")

# 自定义一些CSS来复刻截图的风格
st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .main-header { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 辅助函数与常量 ---
EQUIPMENT_OPTIONS = [
    "fNIRS Frontal A (25330)", 
    "fNIRS Frontal B (25215)", 
    "Both (Hyperscanning)"
]

# 直接生成 "09:00", "10:00" ... 确保格式绝对统一
TIME_STRINGS = [f"{hour:02d}:00" for hour in range(9, 19)]

def get_data():
    """从 Google Sheets 读取数据"""
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        # ttl=0 确保每次刷新都从云端获取最新数据
        df = conn.read(worksheet="Sheet1", ttl=0)
        # 确保列名存在，防止空表报错
        expected_cols = ["Researcher", "Equipment", "Date", "Start_Time", "End_Time", "Created_At"]
        if df.empty or not set(expected_cols).issubset(df.columns):
            return pd.DataFrame(columns=expected_cols)
        return df
    except Exception as e:
        st.error(f"无法连接数据库，请检查 secrets.toml 配置。错误: {e}")
        return pd.DataFrame()

def save_booking(conn, new_row_df, existing_df):
    """保存数据到 Google Sheets"""
    updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)

def check_conflict(df, date_str, start_time_str, equipment):
    """检查冲突逻辑"""
    if df.empty:
        return False
    
    # 筛选当天的预约
    day_bookings = df[df["Date"] == date_str]
    # 筛选同一时间段的预约
    slot_bookings = day_bookings[day_bookings["Start_Time"] == start_time_str]
    
    if slot_bookings.empty:
        return False

    # 检查设备冲突
    booked_equipments = slot_bookings["Equipment"].tolist()
    
    for booked in booked_equipments:
        # 1. 直接冲突：选了A，A已经被约
        if equipment == booked: 
            return True
        # 2. Hyperscanning 冲突：
        # 如果我想约 Both，只要 A 或 B 任何一个被约，就冲突
        if equipment == "Both (Hyperscanning)":
            return True 
        # 如果我想约 A，但是有人约了 Both，也冲突
        if booked == "Both (Hyperscanning)":
            return True
            
    return False

# --- 3. 侧边栏/顶部通知 ---
st.info("💡 **Lab Notice:** 实验结束后请务必清洗 fNIRS 头皮帽并放回充电站。数据实时同步 Google Sheets。")

# --- 4. 布局容器 ---
col_form, col_calendar = st.columns([1, 2.5], gap="large")

# --- 5. 左侧：预约表单 ---
with col_form:
    st.markdown('<div class="main-header">📅 Book Equipment</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        researcher_name = st.text_input("Researcher Name", placeholder="e.g. Dr. Jane Doe")
        
        selected_equipment = st.selectbox("Select Equipment", EQUIPMENT_OPTIONS)
        
        # 默认选中明天
        booking_date = st.date_input("Date", min_value=datetime.today())
        booking_date_str = booking_date.strftime("%Y-%m-%d")
        
        start_time_str = st.selectbox("Time (1 Hour Slot)", TIME_STRINGS, index=2) # 默认 11:00
        
        # 计算结束时间用于显示
        # 加上 try-except 块，万一出错能看到具体是什么字符串导致的问题
        try:
            # 确保 start_time_str 是字符串并去除空格
            start_dt = datetime.strptime(str(start_time_str).strip(), "%H:%M")
            end_time_str = (start_dt + timedelta(hours=1)).strftime("%H:%M")
        except ValueError as e:
            st.error(f"时间格式错误: {start_time_str}")
            st.stop()
        
        submit = st.button("Confirm Booking", type="primary", use_container_width=True)

        if submit:
            if not researcher_name:
                st.warning("Please enter your name.")
            else:
                # 获取最新数据进行检查
                df = get_data()
                
                # 冲突检测
                if check_conflict(df, booking_date_str, start_time_str, selected_equipment):
                    st.error(f"⚠️ 冲突！该时间段 {selected_equipment} 已被占用。")
                else:
                    # 准备写入的数据
                    # 如果是 Hyperscanning，为了日历显示清晰，我们写入两条记录（A 和 B）
                    # 或者写入一条标记为 Both。为了防止逻辑混乱，这里写入一条 "Both" 记录，
                    # 冲突检测逻辑已经处理了 "Both" 会挡住 A 和 B 的情况。
                    
                    new_entry = pd.DataFrame([{
                        "Researcher": researcher_name,
                        "Equipment": selected_equipment,
                        "Date": booking_date_str,
                        "Start_Time": start_time_str,
                        "End_Time": end_time_str,
                        "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    save_booking(conn, new_entry, df)
                    st.success("✅ Booking Confirmed!")
                    st.rerun()

    with st.expander("Instructions"):
        st.markdown("""
        * **Hyperscanning:** 选择 "Both" 将同时锁定两顶帽子。
        * **取消:** 暂时请联系管理员或直接修改 Google Sheet。
        * **冲突:** 红色不可选区域代表已被占用。
        """)

# --- 6. 右侧：日历视图 ---
with col_calendar:
    # 准备日历数据
    df = get_data()
    calendar_events = []
    
    if not df.empty:
        for index, row in df.iterrows():
            # 定义颜色
            color = "#3788d8" # 默认蓝色 (Cap A)
            if "Frontal B" in row["Equipment"]:
                color = "#8e44ad" # 紫色 (Cap B)
            elif "Both" in row["Equipment"]:
                color = "#e74c3c" # 红色 (Hyperscanning)
            
            # 组合日期和时间成 ISO 格式
            start_iso = f"{row['Date']}T{row['Start_Time']}"
            end_iso = f"{row['Date']}T{row['End_Time']}"
            
            calendar_events.append({
                "title": f"{row['Researcher']} - {row['Equipment']}",
                "start": start_iso,
                "end": end_iso,
                "backgroundColor": color,
                "borderColor": color
            })

    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay"
        },
        "initialView": "timeGridWeek",
        "slotMinTime": "09:00:00",
        "slotMaxTime": "19:00:00",
        "allDaySlot": False,
        "height": 650,
    }
    
    # 渲染日历
    calendar(events=calendar_events, options=calendar_options)
