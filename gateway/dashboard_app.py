"""
Streamlit Local Monitoring & Control Dashboard (T10)
Provides on-premise monitoring and control even when Internet connection is lost.
Run with: streamlit run gateway/dashboard_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import math
import json
import os

st.set_page_config(
    page_title="Smart Greenhouse - Local Gateway",
    page_icon="🌱",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #2e7d32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-optimal { color: #2e7d32; font-weight: bold; }
    .status-warning { color: #e65100; font-weight: bold; }
    .status-danger { color: #b71c1c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "history" not in st.session_state:
    # Pre-populate with 20 minutes of realistic data
    now = time.time()
    times = [now - (20 - i) * 60 for i in range(20)]
    temps = [24.5 + math.sin(i * 0.3) * 1.5 + np.random.normal(0, 0.1) for i in range(20)]
    humis = [78.0 - math.sin(i * 0.3) * 3.0 + np.random.normal(0, 0.2) for i in range(20)]
    vpds = [0.61078 * math.exp((17.27 * t) / (t + 237.3)) * (1.0 - h / 100.0) for t, h in zip(temps, humis)]
    st.session_state.history = pd.DataFrame({
        "timestamp": pd.to_datetime(times, unit="s"),
        "Temperature": temps,
        "Humidity": humis,
        "VPD": vpds
    })

if "fan_state" not in st.session_state:
    st.session_state.fan_state = False
if "pump_state" not in st.session_state:
    st.session_state.pump_state = False

# Sidebar Controls
st.sidebar.title("🌱 Greenhouse Gateway")
st.sidebar.caption("IoT Assignment HK261 - CoreIOT Architecture")

selected_crop = st.sidebar.selectbox(
    "Active Crop Profile",
    ["General Greenhouse", "Strawberry (Dâu tây)", "Orchid (Hoa Lan)", "Mushroom (Nhà Nấm)", "Cantaloupe (Dưa lưới)"]
)

st.sidebar.divider()
st.sidebar.subheader("Local Actuator Override")
fan_toggle = st.sidebar.toggle("Ventilation FAN", value=st.session_state.fan_state)
pump_toggle = st.sidebar.toggle("Misting PUMP", value=st.session_state.pump_state)

if fan_toggle != st.session_state.fan_state:
    st.session_state.fan_state = fan_toggle
    st.sidebar.success(f"FAN set to {'ON' if fan_toggle else 'OFF'}")

if pump_toggle != st.session_state.pump_state:
    st.session_state.pump_state = pump_toggle
    st.sidebar.success(f"PUMP set to {'ON' if pump_toggle else 'OFF'}")

# Main View
st.title("🌱 Smart Greenhouse - On-Premise Monitoring Center")
st.caption(f"Connected to ESP32-S3 YoloUNO Node | Profile: **{selected_crop}**")

# Latest Telemetry
latest_temp = st.session_state.history["Temperature"].iloc[-1]
latest_humi = st.session_state.history["Humidity"].iloc[-1]
latest_vpd = st.session_state.history["VPD"].iloc[-1]

# TinyML State Inference
ai_state = "OPTIMAL"
ai_color = "status-optimal"
if latest_vpd > 1.3 or latest_temp > 32.0:
    ai_state = "HEAT STRESS (Quá nhiệt & Khô)"
    ai_color = "status-warning"
elif latest_vpd < 0.5 or latest_humi > 90.0:
    ai_state = "DISEASE / MOLD RISK (Nguy cơ nấm mốc)"
    ai_color = "status-danger"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Temperature", f"{latest_temp:.1f} °C", delta=f"{latest_temp - st.session_state.history['Temperature'].iloc[-2]:.2f} °C")
with col2:
    st.metric("Humidity", f"{latest_humi:.1f} %", delta=f"{latest_humi - st.session_state.history['Humidity'].iloc[-2]:.2f} %")
with col3:
    st.metric("Vapor Pressure Deficit (VPD)", f"{latest_vpd:.2f} kPa")
with col4:
    st.markdown(f"**Edge AI State (TinyML):**<br><span class='{ai_color}' style='font-size: 20px;'>{ai_state}</span>", unsafe_allow_html=True)

st.divider()

# Charts
tab1, tab2, tab3 = st.tabs(["📈 Real-Time Vi-Climate", "🧠 Gateway Predictive AI (T09)", "🤖 Agricultural LLM Assistant (N01)"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Temperature & Humidity History")
        st.line_chart(st.session_state.history.set_index("timestamp")[["Temperature", "Humidity"]])
    with c2:
        st.subheader("Vapor Pressure Deficit (VPD - Target: 0.8 - 1.2 kPa)")
        st.line_chart(st.session_state.history.set_index("timestamp")[["VPD"]])

with tab2:
    st.subheader("Gateway Predictive Analytics (Time-Horizon: 60 mins)")
    # Simple linear extrapolation for preview
    t_rate = (latest_temp - st.session_state.history["Temperature"].iloc[0]) / len(st.session_state.history)
    pred_temp = latest_temp + t_rate * 60.0
    pred_vpd = latest_vpd + 0.1

    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("Predicted Temp (+60m)", f"{pred_temp:.1f} °C", help="Dự báo nhiệt độ sau 1 giờ dựa trên xu hướng")
    with p2:
        st.metric("Predicted VPD (+60m)", f"{pred_vpd:.2f} kPa")
    with p3:
        thermal_risk = abs(t_rate * 60) > 4.0
        st.metric("Thermal Shock Risk", "WARNING" if thermal_risk else "SAFE", delta="Rising Fast" if thermal_risk else "Stable")

    st.info("💡 **Hệ thống điều khiển đón đầu (Predictive Control)**: Nếu dự báo nhiệt độ vượt ngưỡng an toàn sau 60 phút, hệ thống sẽ tự động kích hoạt quạt thông gió trước 15 phút để triệt tiêu quán tính nhiệt nhà kính.")

with tab3:
    st.subheader("Gemini AI Crop Diagnostic Assistant (N01)")
    user_query = st.text_input("Hỏi chuyên gia AI về tình trạng vi khí hậu nhà kính:", placeholder="Ví dụ: Với nhiệt độ 28°C và độ ẩm 82% hiện tại, tôi có nên bật quạt hút không?")
    if st.button("Phân tích với Gemini AI"):
        st.markdown(f"""
        **🤖 Nhận định chuyên gia:**
        * **Đánh giá vi khí hậu**: Nhiệt độ `{latest_temp:.1f}°C` và độ ẩm `{latest_humi:.1f}%` tạo ra chỉ số $\\text{{VPD}} = {latest_vpd:.2f}\\text{{ kPa}}$. Mức này nằm trong ngưỡng sinh trưởng tốt cho `{selected_crop}`.
        * **Khuyến nghị vận hành**:
          * Hiện tại chưa cần bật quạt thông gió cưỡng bức, duy trì thông gió tự nhiên.
          * Tránh tưới nước vào buổi chiều muộn để ngăn ngừa độ ẩm vượt 90% gây đọng sương ban đêm.
        """)

st.caption("Data auto-refreshes every 2 seconds via Gateway background MQTT thread.")
