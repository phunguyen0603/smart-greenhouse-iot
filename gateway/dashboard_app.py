"""
Smart Greenhouse Custom Local Dashboard (T10 + N06 + N01)
Features:
- Real-time telemetry feed from gateway_service.py via SQLite (with standalone fallback)
- Automated Event Detection & Persistent Event Recording with CSV export (N06)
- Multi-Gateway -> Multi-MasterNode -> Multi-SubNode Topology & Re-assignment Manager
- Gateway Predictive AI (T09) & Gemini LLM Agronomist Assistant (N01)
Run with: streamlit run gateway/dashboard_app.py
"""

import os
import sys
import math
import time
import yaml
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from greenhouse_db import GreenhouseStore
from llm_assistant import analyze_greenhouse_state

CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
if not os.path.exists(CONFIG_PATH):
    CONFIG_PATH = os.path.join(BASE_DIR, "config.example.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

DB_NAME = CONFIG.get("gateway_sync", {}).get("offline_buffer_db", "gateway_buffer.db")
DB_PATH = os.path.join(BASE_DIR, DB_NAME)
DEFAULT_SUB_DEVICE = CONFIG.get("gateway_sync", {}).get("sub_device_name", "YoloUNO_Node1")

st.set_page_config(
    page_title="Smart Greenhouse - Local Control & Event Center",
    page_icon="🌱",
    layout="wide",
)

st.markdown("""
<style>
    .status-optimal { color: #2e7d32; font-weight: 700; }
    .status-warning { color: #e65100; font-weight: 700; }
    .status-danger  { color: #b71c1c; font-weight: 700; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_store():
    return GreenhouseStore(DB_PATH)


store = get_store()


def get_telemetry_df():
    rows = store.get_recent_telemetry(limit=180)
    if rows:
        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["ts_ms"], unit="ms")
        return df, True

    # Fallback preview data when gateway_service.py hasn't written any rows yet
    now = time.time()
    times = [now - (20 - i) * 60 for i in range(20)]
    temps = [25.5 + math.sin(i * 0.3) * 1.2 + np.random.normal(0, 0.08) for i in range(20)]
    humis = [77.0 - math.sin(i * 0.3) * 2.5 + np.random.normal(0, 0.15) for i in range(20)]
    vpds = [0.61078 * math.exp((17.27 * t) / (t + 237.3)) * (1.0 - h / 100.0) for t, h in zip(temps, humis)]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(times, unit="s"),
        "node_id": [DEFAULT_SUB_DEVICE] * 20,
        "temperature": np.round(temps, 2),
        "humidity": np.round(humis, 2),
        "vpd": np.round(vpds, 3),
        "ai_state": [0] * 20,
        "ai_state_str": ["OPTIMAL"] * 20,
        "predicted_temp_60m": np.round(temps, 2),
        "predicted_vpd_60m": np.round(vpds, 3),
        "thermal_shock_risk": [0] * 20,
        "dew_risk": [0] * 20,
        "fan_state": [0] * 20,
        "pump_state": [0] * 20,
        "light_state": [1] * 20,
    })
    return df, False


# ================= SIDEBAR: TOPOLOGY FILTER & ACTUATORS =================
st.sidebar.title("🌱 Greenhouse Center")
st.sidebar.caption("Custom Dashboard (N06) | Local Gateway (T10)")

gateways = store.get_gateways()
gw_ids = [g["gateway_id"] for g in gateways]
selected_gw = st.sidebar.selectbox("Gateway", gw_ids if gw_ids else ["GW-PC-01"])

masters = store.get_masters(selected_gw)
master_ids = [m["master_id"] for m in masters]
selected_master = st.sidebar.selectbox("MasterNode", master_ids if master_ids else ["MASTER-ZONE-A"])

nodes = store.get_nodes(selected_master)
node_ids = [n["node_id"] for n in nodes]
selected_node = st.sidebar.selectbox("Active Node", node_ids if node_ids else [DEFAULT_SUB_DEVICE])

selected_crop = st.sidebar.selectbox(
    "Crop Profile",
    ["General Greenhouse", "Strawberry (Dâu tây)", "Orchid (Hoa Lan)", "Mushroom (Nhà Nấm)", "Cantaloupe (Dưa lưới)"],
)

st.sidebar.divider()
st.sidebar.subheader(f"Actuator Control ({selected_node})")

node_info = next((n for n in nodes if n["node_id"] == selected_node), None)
cur_fan = bool(node_info["fan_state"]) if node_info else False
cur_pump = bool(node_info["pump_state"]) if node_info else False
cur_light = bool(node_info["light_state"]) if node_info else True

fan_toggle = st.sidebar.toggle("Ventilation FAN", value=cur_fan, key="sb_fan")
pump_toggle = st.sidebar.toggle("Irrigation PUMP", value=cur_pump, key="sb_pump")
light_toggle = st.sidebar.toggle("Grow LIGHT", value=cur_light, key="sb_light")

if fan_toggle != cur_fan:
    store.update_node_actuators(selected_node, fan=fan_toggle)
    store.enqueue_command(selected_node, "setStateFAN", fan_toggle)
    store.record_event(selected_node, selected_master, "ACTUATOR_RPC", "INFO", f"[Custom Dashboard] Quạt -> {'ON' if fan_toggle else 'OFF'}")
    st.sidebar.success(f"FAN -> {'ON' if fan_toggle else 'OFF'}")

if pump_toggle != cur_pump:
    store.update_node_actuators(selected_node, pump=pump_toggle)
    store.enqueue_command(selected_node, "setStatePUMP", pump_toggle)
    store.record_event(selected_node, selected_master, "ACTUATOR_RPC", "INFO", f"[Custom Dashboard] Bơm -> {'ON' if pump_toggle else 'OFF'}")
    st.sidebar.success(f"PUMP -> {'ON' if pump_toggle else 'OFF'}")

if light_toggle != cur_light:
    store.update_node_actuators(selected_node, light=light_toggle)
    store.enqueue_command(selected_node, "setStateLED", light_toggle)
    store.record_event(selected_node, selected_master, "ACTUATOR_RPC", "INFO", f"[Custom Dashboard] Đèn -> {'ON' if light_toggle else 'OFF'}")
    st.sidebar.success(f"LIGHT -> {'ON' if light_toggle else 'OFF'}")

st.sidebar.divider()
auto_refresh = st.sidebar.toggle("Live Auto-Refresh (3s)", value=True)
buffered_cnt = store.count_offline_packets()
st.sidebar.metric("Offline Buffer (SQLite)", f"{buffered_cnt} pkts")


# ================= MAIN HEADER =================
st.title("🌱 Smart Greenhouse — Custom Control & Event Center")
st.caption(f"Hierarchy: **{selected_gw}** ➔ **{selected_master}** ➔ **{selected_node}** | Crop: **{selected_crop}**")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Real-Time Monitor (T10)",
    "🚨 Event Detection & Log (N06)",
    "🕸️ Topology & Node Manager",
    "🧠 Predictive AI (T09) & LLM (N01)",
])


# ----------------- TAB 1: REAL-TIME MONITOR -----------------
with tab1:
    def render_live_monitor():
        df, is_live = get_telemetry_df()
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        status_badge = "🟢 LIVE GATEWAY FEED" if is_live else "🟡 PREVIEW MODE (Chạy gateway_service.py để nhận dữ liệu live)"
        st.caption(status_badge)

        ai_str = str(latest.get("ai_state_str", "OPTIMAL"))
        ai_state = int(latest.get("ai_state", 0))
        ai_cls = "status-optimal" if ai_state == 0 else ("status-warning" if ai_state == 1 else "status-danger")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Air Temperature", f"{latest['temperature']:.2f} °C", delta=f"{latest['temperature'] - prev['temperature']:+.2f} °C")
        c2.metric("Air Humidity", f"{latest['humidity']:.1f} %", delta=f"{latest['humidity'] - prev['humidity']:+.2f} %")
        c3.metric("VPD Index", f"{latest['vpd']:.3f} kPa", help="Vùng tối ưu: 0.8 – 1.2 kPa")
        c4.markdown(f"**Edge AI (TinyML):**<br><span class='{ai_cls}' style='font-size: 22px;'>{ai_str}</span>", unsafe_allow_html=True)

        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Temperature & Humidity History")
            st.line_chart(df.set_index("timestamp")[["temperature", "humidity"]])
        with g2:
            st.subheader("Vapor Pressure Deficit (VPD)")
            st.line_chart(df.set_index("timestamp")[["vpd"]])

    if auto_refresh:
        @st.fragment(run_every=3)
        def live_fragment():
            render_live_monitor()
        live_fragment()
    else:
        render_live_monitor()


# ----------------- TAB 2: EVENT DETECTION & RECORDING (N06) -----------------
with tab2:
    st.subheader("Event Detection & Persistent Recording (N06)")
    all_events = store.get_events(limit=500)
    unack_cnt = sum(1 for e in all_events if e["acknowledged"] == 0)
    crit_cnt = sum(1 for e in all_events if e["severity"] == "CRITICAL")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Recorded Events", len(all_events))
    k2.metric("Unacknowledged Alerts", unack_cnt)
    k3.metric("Critical Events", crit_cnt)
    k4.metric("Last Event", all_events[0]["event_type"] if all_events else "NONE")

    f1, f2, a1, a2 = st.columns([1.2, 1.4, 1.2, 1.2])
    sev_filter = f1.selectbox("Filter Severity", ["ALL", "CRITICAL", "WARNING", "INFO"])
    type_options = ["ALL"] + sorted(list({e["event_type"] for e in all_events}))
    type_filter = f2.selectbox("Filter Event Type", type_options)

    if a1.button("✓ Acknowledge All", use_container_width=True):
        store.acknowledge_all_events()
        st.rerun()

    if a2.button("🔥 Simulate Overheat Event", use_container_width=True):
        store.record_event(
            selected_node, selected_master, "HEAT_STRESS", "CRITICAL",
            "[Test Demo N06] Phát hiện sốc nhiệt giả lập T=36.8°C, VPD=2.15 kPa -> Tự động kích hoạt quạt!",
            {"temperature": 36.8, "humidity": 52.0, "vpd": 2.15, "ai_state": "HEAT_STRESS_DRY"},
        )
        st.rerun()

    filtered = store.get_events(severity=sev_filter, event_type=type_filter, limit=200)
    if filtered:
        ev_df = pd.DataFrame(filtered)[
            ["id", "timestamp_str", "master_id", "node_id", "event_type", "severity", "description", "sensor_snapshot_json", "acknowledged"]
        ]
        ev_df.columns = ["ID", "Timestamp", "MasterNode", "Node ID", "Event Type", "Severity", "Description", "Snapshot", "Ack"]
        st.dataframe(ev_df, use_container_width=True, hide_index=True)

        csv_bytes = ev_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 Export Event History (.CSV)",
            data=csv_bytes,
            file_name="greenhouse_event_log.csv",
            mime="text/csv",
        )
    else:
        st.info("Chưa có sự kiện nào khớp bộ lọc. Hãy bật `gateway_service.py` hoặc bấm `Simulate Overheat Event` để kiểm tra.")


# ----------------- TAB 3: MULTI-GATEWAY / MASTERNODE / SUB-NODE MANAGER -----------------
with tab3:
    st.subheader("Multi-Gateway & Multi-MasterNode Hierarchy Manager")
    st.caption("Quản lý tập trung nhiều Gateway, MasterNode và Node con mà không cần tạo Webserver riêng trên từng ESP32 con.")

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("**1. Danh sách Gateways & MasterNodes**")
        st.dataframe(pd.DataFrame(store.get_gateways()), use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame(store.get_masters()), use_container_width=True, hide_index=True)

    with t_col2:
        st.markdown("**2. Danh sách Sub-Nodes (Cảm biến & Chấp hành)**")
        all_nodes = store.get_nodes()
        if all_nodes:
            nd_df = pd.DataFrame(all_nodes)[["node_id", "name", "master_id", "gateway_id", "protocol", "mac_addr", "role", "status"]]
            st.dataframe(nd_df, use_container_width=True, hide_index=True)

    st.divider()
    m1, m2, m3 = st.columns(3)

    with m1:
        with st.form("add_node_form"):
            st.markdown("➕ **Thêm Sub-Node mới**")
            new_nid = st.text_input("Node ID", placeholder="Node_Soil_ZoneB")
            new_nname = st.text_input("Tên hiển thị", placeholder="Zone B Soil Moisture")
            new_nmac = st.text_input("MAC Address", placeholder="AA:BB:CC:11:22:33")
            new_nproto = st.selectbox("Giao thức", ["ESP-NOW", "USB Serial", "BLE", "I2C Tasmota", "Modbus RS485"])
            all_masters = [m["master_id"] for m in store.get_masters()]
            target_m = st.selectbox("Gắn vào MasterNode", all_masters)
            if st.form_submit_button("Đăng ký Node"):
                if new_nid and new_nname:
                    store.add_node(new_nid, target_m, new_nname, new_nmac, new_nproto)
                    store.record_event(new_nid, target_m, "NODE_REGISTERED", "INFO", f"Thêm node mới '{new_nid}' ({new_nproto}) vào {target_m}.")
                    st.success(f"Đã thêm {new_nid}!")
                    st.rerun()

    with m2:
        with st.form("reassign_form"):
            st.markdown("🔄 **Chuyển vùng MasterNode / Gateway**")
            node_choices = [n["node_id"] for n in store.get_nodes()]
            master_choices = [m["master_id"] for m in store.get_masters()]
            gw_choices = [g["gateway_id"] for g in store.get_gateways()]

            mv_node = st.selectbox("Chọn Sub-Node cần chuyển", node_choices)
            to_master = st.selectbox("Chuyển sang MasterNode", master_choices)
            if st.form_submit_button("Chuyển MasterNode cho Node"):
                store.reassign_node_master(mv_node, to_master)
                store.record_event(mv_node, to_master, "NODE_REASSIGNED", "INFO", f"Chuyển liên kết {mv_node} sang {to_master}.")
                st.success(f"Đã gán {mv_node} -> {to_master}!")
                st.rerun()

            st.divider()
            mv_master = st.selectbox("Chọn MasterNode cần đổi Gateway", master_choices)
            to_gw = st.selectbox("Chuyển sang Gateway", gw_choices)
            if st.form_submit_button("Đổi Gateway cho MasterNode"):
                store.reassign_master_gateway(mv_master, to_gw)
                store.record_event("SYSTEM", mv_master, "MASTER_REASSIGNED", "INFO", f"Chuyển {mv_master} sang Gateway {to_gw}.")
                st.success(f"Đã gán {mv_master} -> {to_gw}!")
                st.rerun()

    with m3:
        with st.form("add_infra_form"):
            st.markdown("🖥️ **Thêm MasterNode / Gateway mới**")
            new_mid = st.text_input("MasterNode ID", placeholder="MASTER-ZONE-C")
            new_mname = st.text_input("Tên MasterNode", placeholder="YoloUNO Master Zone C")
            parent_gw = st.selectbox("Thuộc Gateway", [g["gateway_id"] for g in store.get_gateways()])
            if st.form_submit_button("Thêm MasterNode"):
                if new_mid and new_mname:
                    store.add_master(new_mid, parent_gw, new_mname)
                    store.record_event("SYSTEM", new_mid, "MASTER_ADDED", "INFO", f"Thêm MasterNode {new_mid} thuộc {parent_gw}.")
                    st.success(f"Đã thêm {new_mid}!")
                    st.rerun()

            st.divider()
            new_gid = st.text_input("Gateway ID", placeholder="GW-PI-02")
            new_gname = st.text_input("Tên Gateway", placeholder="Raspberry Pi Zone C")
            if st.form_submit_button("Thêm Gateway"):
                if new_gid and new_gname:
                    store.add_gateway(new_gid, new_gname)
                    store.record_event("SYSTEM", "GLOBAL", "GATEWAY_ADDED", "INFO", f"Thêm Gateway {new_gid}.")
                    st.success(f"Đã thêm {new_gid}!")
                    st.rerun()


# ----------------- TAB 4: PREDICTIVE AI (T09) & LLM ASSISTANT (N01) -----------------
with tab4:
    df_ai, _ = get_telemetry_df()
    latest_ai = df_ai.iloc[-1]

    st.subheader("Gateway Predictive Analytics (T09 — Horizon: 60 mins)")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Predicted Temp (+60m)", f"{latest_ai['predicted_temp_60m']:.2f} °C")
    p2.metric("Predicted VPD (+60m)", f"{latest_ai['predicted_vpd_60m']:.3f} kPa")
    p3.metric("Thermal Shock Risk", "WARNING" if latest_ai["thermal_shock_risk"] else "SAFE")
    p4.metric("Dew Condensation Risk", "WARNING" if latest_ai["dew_risk"] else "SAFE")

    st.divider()
    st.subheader(f"Agricultural LLM Expert Assistant (N01) — {selected_crop}")
    st.caption("Trợ lý chuyên gia nông học tích hợp mô hình Google Gemini AI trực tuyến.")

    c_key, c_mode = st.columns([2.5, 1.5])
    api_key_input = c_key.text_input(
        "Gemini API Key:",
        value=os.environ.get("GEMINI_API_KEY", ""),
        placeholder="AQ.Ab8RN6... hoặc AIzaSy...",
        type="password"
    )
    c_mode.markdown(
        "**Trạng thái AI:**<br>" + 
        ("🟢 Sẵn sàng gọi Google Gemini" if api_key_input else "🔴 Cần nhập API Key"),
        unsafe_allow_html=True
    )

    # Preset Question Buttons
    st.markdown("**Gợi ý câu hỏi nhanh:**")
    q_col1, q_col2, q_col3 = st.columns(3)
    preset_q = ""
    if q_col1.button("🔥 Cây có nguy cơ sốc nhiệt không?", use_container_width=True):
        preset_q = "Với tốc độ tăng nhiệt và chỉ số VPD hiện tại, cây có nguy cơ bị sốc nhiệt hoặc cháy rìa lá không?"
    if q_col2.button("💧 Điều kiện này có dễ sinh nấm mốc?", use_container_width=True):
        preset_q = "Độ ẩm và VPD hiện tại có tạo điều kiện cho nấm phấn trắng hoặc đọng sương hại lá không?"
    if q_col3.button("⚡ Có nên bật quạt và tưới lúc này?", use_container_width=True):
        preset_q = "Tôi nên bật quạt đối lưu hay kích hoạt bơm tưới lúc này? Thời gian khuyến nghị là bao lâu?"

    user_question = st.text_input(
        "Câu hỏi chuyên sâu cho chuyên gia AI:",
        value=preset_q if preset_q else "",
        placeholder="Ví dụ: Giống cây này cần duy trì VPD bao nhiêu để đậu quả tốt nhất?",
        key="llm_question_input"
    )

    trend_ctx = {
        "pred_temp_60m": float(latest_ai.get("predicted_temp_60m", latest_ai["temperature"])),
        "pred_vpd_60m": float(latest_ai.get("predicted_vpd_60m", latest_ai["vpd"])),
        "thermal_shock_risk": bool(latest_ai.get("thermal_shock_risk", False)),
        "dew_risk": bool(latest_ai.get("dew_risk", False)),
    }

    if st.button("🤖 Phân tích tình trạng & Chẩn đoán sinh lý cây", type="primary", use_container_width=True):
        with st.spinner("Đang tổng hợp dữ liệu vi khí hậu và hỏi ý kiến Chuyên gia AI..."):
            advice = analyze_greenhouse_state(
                temp=float(latest_ai["temperature"]),
                humi=float(latest_ai["humidity"]),
                vpd=float(latest_ai["vpd"]),
                ai_state_str=str(latest_ai["ai_state_str"]),
                crop_name=selected_crop,
                api_key=api_key_input or None,
                trend_info=trend_ctx,
                user_question=user_question or None
            )
            st.session_state["last_llm_advice"] = advice
            st.session_state["last_advice_node"] = selected_node
            st.session_state["last_advice_master"] = selected_master

    # Display persistent advice if present in session state
    if "last_llm_advice" in st.session_state:
        adv = st.session_state["last_llm_advice"]
        st.markdown(str(adv))

        # Actionable Recommendation Triggers
        rec_fan = getattr(adv, "fan", None)
        rec_pump = getattr(adv, "pump", None)
        if rec_fan or rec_pump:
            st.markdown("---")
            st.markdown("#### ⚡ Thao Tác Chấp Hành Nhanh Theo Khuyến Nghị AI")
            act_col1, act_col2 = st.columns(2)

            if rec_fan:
                if act_col1.button("🌀 Bật Quạt Đối Lưu Ngay (Theo AI)", type="secondary", use_container_width=True):
                    store.update_node_actuators(selected_node, fan=True)
                    store.enqueue_command(selected_node, "setStateFAN", True)
                    store.record_event(selected_node, selected_master, "ACTUATOR_RPC", "INFO", "[LLM Assistant] Tự động bật quạt theo khuyến nghị chuyên gia AI.")
                    st.success("Đã gửi lệnh BẬT Quạt!")
                    st.rerun()

            if rec_pump:
                if act_col2.button("💧 Bật Bơm / Phun Sương Ngay (Theo AI)", type="secondary", use_container_width=True):
                    store.update_node_actuators(selected_node, pump=True)
                    store.enqueue_command(selected_node, "setStatePUMP", True)
                    store.record_event(selected_node, selected_master, "ACTUATOR_RPC", "INFO", "[LLM Assistant] Tự động kích hoạt bơm theo khuyến nghị chuyên gia AI.")
                    st.success("Đã gửi lệnh BẬT Bơm!")
                    st.rerun()
