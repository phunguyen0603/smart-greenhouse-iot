"""
IoT Gateway Core Service (T08 & T15) + Event Detection Feed (N06)
Bridges ESP32-S3 (YoloUNO) Node with CoreIOT Cloud Platform & Local Custom Dashboard.
- Ingests telemetry via USB Serial (or smooth simulated fallback when hardware is absent)
- Integrates Gateway Local AI (T09)
- Supports Direct Device Mode (T08: v1/devices/me/*) and Gateway Sync Mode (T15: v1/gateway/*)
- Built-in SQLite Offline Buffer & Event Recording (greenhouse_db.py)
- Listens to both CoreIOT RPC commands and Local Custom Dashboard command queue
"""

import sys
import os
import time
import json
import math
import random
import threading
import yaml
import paho.mqtt.client as mqtt

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
from gateway_ai import GreenhouseGatewayAI
from greenhouse_db import GreenhouseStore

# Load Configuration
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

BROKER = CONFIG["coreiot"]["broker"]
PORT = CONFIG["coreiot"]["port"]
ACCESS_TOKEN = CONFIG["coreiot"]["access_token"]

GW_SYNC_CFG = CONFIG.get("gateway_sync", {})
GATEWAY_SYNC_ENABLED = bool(GW_SYNC_CFG.get("enabled", False))
SUB_DEVICE_NAME = GW_SYNC_CFG.get("sub_device_name", "YoloUNO_Node1")
MASTER_NODE_ID = "MASTER-ZONE-A"
BUFFER_DB_PATH = os.path.join(BASE_DIR, GW_SYNC_CFG.get("offline_buffer_db", "gateway_buffer.db"))

AI_CFG = CONFIG.get("ai", {})
TEMP_HIGH = float(AI_CFG.get("temp_high_threshold", 32.0))
HUMI_HIGH = float(AI_CFG.get("humi_high_threshold", 90.0))

# Initialize Shared Store & Gateway AI
store = GreenhouseStore(BUFFER_DB_PATH)
gateway_ai = GreenhouseGatewayAI()

# Global States
is_connected = False
was_disconnected = False
serial_lock = threading.Lock()
serial_conn = None

# Track active alert flags to record clean state-transition events without duplicate spam
active_alerts = {
    "heat_stress": False,
    "mold_risk": False,
    "thermal_shock": False,
    "dew_risk": False,
}

actuator_state = {
    "fan": False,
    "pump": False,
    "light": True
}

latest_data = {
    "temp": 26.2,
    "humidity": 77.5,
    "delta_temp": 0.0,
    "delta_humi": 0.0,
    "vpd": 0.77,
    "ai_state": 0,
    "ai_state_str": "OPTIMAL",
    "ai_conf": 0.98,
    "infer_us": 2,
    "fan": False,
    "pump": False,
    "light": True
}


# ================= OFFLINE SYNC & EVENT DETECTION =================
def flush_offline_buffer(client):
    rows = store.get_offline_packets()
    if not rows:
        return
    print(f"[Offline Sync] Phát hiện {len(rows)} gói tin offline. Đang đồng bộ bù lên CoreIOT...")
    synced = 0
    for row in rows:
        values = json.loads(row["values_json"])
        if GATEWAY_SYNC_ENABLED:
            payload = {row["device_name"]: [{"ts": row["ts_ms"], "values": values}]}
            topic = "v1/gateway/telemetry"
        else:
            payload = {"ts": row["ts_ms"], "values": values}
            topic = "v1/devices/me/telemetry"

        res = client.publish(topic, json.dumps(payload), qos=1)
        if res.rc == mqtt.MQTT_ERR_SUCCESS:
            store.delete_offline_packet(row["id"])
            synced += 1
        else:
            break
    print(f"[Offline Sync] Đã đồng bộ bù thành công {synced}/{len(rows)} gói tin!")
    if synced > 0:
        store.record_event(
            SUB_DEVICE_NAME, MASTER_NODE_ID, "OFFLINE_SYNC_OK", "INFO",
            f"Đồng bộ bù thành công {synced}/{len(rows)} gói tin từ SQLite lên CoreIOT.",
            {"synced": synced, "total": len(rows)},
        )


def detect_and_record_events(telemetry):
    t = telemetry["temperature"]
    h = telemetry["humidity"]
    vpd = telemetry["vpd"]
    ai_state = telemetry["tinyml_state"]
    snap = {"temperature": t, "humidity": h, "vpd": vpd, "ai_state": telemetry["tinyml_state_str"]}

    heat_now = (ai_state == 1) or (t > TEMP_HIGH)
    mold_now = (ai_state == 2) or (h > HUMI_HIGH)
    shock_now = bool(telemetry.get("thermal_shock_risk", False))
    dew_now = bool(telemetry.get("dew_risk", False))

    if heat_now and not active_alerts["heat_stress"]:
        store.record_event(
            SUB_DEVICE_NAME, MASTER_NODE_ID, "HEAT_STRESS", "CRITICAL" if t > TEMP_HIGH + 3 else "WARNING",
            f"Phát hiện quá nhiệt/khô (T={t:.1f}°C, VPD={vpd:.2f} kPa).", snap
        )
    if mold_now and not active_alerts["mold_risk"]:
        store.record_event(
            SUB_DEVICE_NAME, MASTER_NODE_ID, "MOLD_RISK", "CRITICAL" if h > 93 else "WARNING",
            f"Phát hiện nguy cơ nấm mốc (H={h:.1f}%, VPD={vpd:.2f} kPa).", snap
        )
    if shock_now and not active_alerts["thermal_shock"]:
        store.record_event(
            SUB_DEVICE_NAME, MASTER_NODE_ID, "THERMAL_SHOCK", "CRITICAL",
            f"AI dự báo tốc độ biến thiên nhiệt nhanh ({telemetry['temp_rate_per_min']} °C/phút).", snap
        )
    if dew_now and not active_alerts["dew_risk"]:
        store.record_event(
            SUB_DEVICE_NAME, MASTER_NODE_ID, "DEW_RISK", "WARNING",
            f"Cảnh báo nguy cơ đọng sương bề mặt lá (H={h:.1f}%).", snap
        )

    was_alerting = any(active_alerts.values())
    active_alerts["heat_stress"] = heat_now
    active_alerts["mold_risk"] = mold_now
    active_alerts["thermal_shock"] = shock_now
    active_alerts["dew_risk"] = dew_now

    if was_alerting and not any(active_alerts.values()):
        store.record_event(
            SUB_DEVICE_NAME, MASTER_NODE_ID, "RETURN_TO_OPTIMAL", "INFO",
            f"Vi khí hậu đã trở lại vùng an toàn (T={t:.1f}°C, H={h:.1f}%, VPD={vpd:.2f} kPa).", snap
        )


# ================= SERIAL & RPC HELPERS =================
def parse_bool_param(params):
    if isinstance(params, bool):
        return params
    if isinstance(params, str):
        return params.strip().lower() in ("true", "1", "on", "yes")
    return bool(params)


def send_serial_command(cmd_str):
    global serial_conn
    with serial_lock:
        if serial_conn and serial_conn.is_open:
            try:
                serial_conn.write((cmd_str + "\n").encode())
                print(f"[Gateway Serial] Sent command to ESP32: {cmd_str}")
            except Exception as e:
                print(f"[Gateway Serial] Error sending command: {e}")


def handle_rpc_command(method, params, source="CoreIOT RPC", target_node=None):
    method_upper = (method or "").upper()
    node = target_node or SUB_DEVICE_NAME

    if "GET" in method_upper and "FAN" in method_upper:
        return actuator_state["fan"]
    if "GET" in method_upper and "PUMP" in method_upper:
        return actuator_state["pump"]
    if "GET" in method_upper and ("LIGHT" in method_upper or "LED" in method_upper):
        return actuator_state["light"]

    if "SET" in method_upper and "FAN" in method_upper:
        new_val = parse_bool_param(params)
        actuator_state["fan"] = new_val
        send_serial_command("FAN_ON" if new_val else "FAN_OFF")
        store.update_node_actuators(node, fan=new_val)
        store.record_event(node, MASTER_NODE_ID, "ACTUATOR_RPC", "INFO", f"[{source}] Quạt thông gió -> {'ON' if new_val else 'OFF'}")
        print(f"[Gateway RPC] >>> FAN -> {'ON' if new_val else 'OFF'} ({source})")
        return new_val

    if "SET" in method_upper and "PUMP" in method_upper:
        new_val = parse_bool_param(params)
        actuator_state["pump"] = new_val
        send_serial_command("PUMP_ON" if new_val else "PUMP_OFF")
        store.update_node_actuators(node, pump=new_val)
        store.record_event(node, MASTER_NODE_ID, "ACTUATOR_RPC", "INFO", f"[{source}] Máy bơm tưới -> {'ON' if new_val else 'OFF'}")
        print(f"[Gateway RPC] >>> PUMP -> {'ON' if new_val else 'OFF'} ({source})")
        return new_val

    if "SET" in method_upper and ("LIGHT" in method_upper or "LED" in method_upper):
        new_val = parse_bool_param(params)
        actuator_state["light"] = new_val
        send_serial_command("LED_ON" if new_val else "LED_OFF")
        store.update_node_actuators(node, light=new_val)
        store.record_event(node, MASTER_NODE_ID, "ACTUATOR_RPC", "INFO", f"[{source}] Đèn quang hợp -> {'ON' if new_val else 'OFF'}")
        print(f"[Gateway RPC] >>> LED/LIGHT -> {'ON' if new_val else 'OFF'} ({source})")
        return new_val

    return {"error": f"Unknown method: {method}"}


def init_serial():
    global serial_conn
    if serial is None:
        print("[Gateway Serial] pyserial chưa được cài. Chạy ở chế độ giả lập (Simulation Mode).")
        return False

    ser_cfg = CONFIG.get("serial", {})
    port = ser_cfg.get("port", "COM3")
    baud = ser_cfg.get("baudrate", 115200)
    timeout = ser_cfg.get("timeout", 1.0)

    try:
        serial_conn = serial.Serial(port, baud, timeout=timeout)
        print(f"[Gateway Serial] Connected to ESP32 on {port} ({baud} baud).")
        return True
    except Exception as e:
        if ser_cfg.get("auto_detect", False):
            for p in serial.tools.list_ports.comports():
                if any(k in (p.description or "").upper() for k in ["USB", "UART", "CP210", "CH340", "ESP32", "JTAG"]):
                    try:
                        serial_conn = serial.Serial(p.device, baud, timeout=timeout)
                        print(f"[Gateway Serial] Auto-detected ESP32 on {p.device}.")
                        return True
                    except Exception:
                        pass
        print(f"[Gateway Serial] Chưa có mạch cắm ở {port} ({e}). Đang chạy chế độ giả lập (Simulation Mode).")
        serial_conn = None
        return False


def serial_reader_loop():
    while True:
        if serial_conn and serial_conn.is_open:
            try:
                if serial_conn.in_waiting > 0:
                    line = serial_conn.readline().decode("utf-8", errors="ignore").strip()
                    if line.startswith("{") and line.endswith("}"):
                        pkt = json.loads(line)
                        for k in ("temp", "humidity", "delta_temp", "delta_humi", "vpd", "ai_state", "ai_state_str", "ai_conf", "infer_us"):
                            if k in pkt:
                                latest_data[k] = pkt[k]
                        for act in ("fan", "pump", "light"):
                            if act in pkt:
                                actuator_state[act] = bool(pkt[act])
            except Exception as e:
                print(f"[Gateway Serial] Read error: {e}")
                time.sleep(1)
        time.sleep(0.05)


# ================= MQTT CALLBACKS =================
def on_connect(client, userdata, flags, reason_code, properties=None):
    global is_connected, was_disconnected
    if reason_code == 0:
        is_connected = True
        mode_str = "GATEWAY SYNC (T15)" if GATEWAY_SYNC_ENABLED else "DIRECT DEVICE (T08)"
        print(f"[Gateway] Connected to CoreIOT ({BROKER}:{PORT}) | Mode: {mode_str}")

        if was_disconnected:
            was_disconnected = False
        else:
            store.record_event(SUB_DEVICE_NAME, MASTER_NODE_ID, "GATEWAY_ONLINE", "INFO", f"Gateway kết nối CoreIOT thành công ({mode_str}).")

        if GATEWAY_SYNC_ENABLED:
            connect_payload = {"device": SUB_DEVICE_NAME, "type": "Greenhouse_Profile"}
            client.publish("v1/gateway/connect", json.dumps(connect_payload), qos=1)
            client.subscribe("v1/gateway/rpc")
            print(f"[Gateway T15] Auto-provisioned & subscribed RPC for sub-device: {SUB_DEVICE_NAME}")
        else:
            client.subscribe("v1/devices/me/rpc/request/+")
            print("[Gateway] Subscribed to CoreIOT RPC requests (v1/devices/me/rpc/request/+).")

        flush_offline_buffer(client)
    else:
        is_connected = False
        print(f"[Gateway] Connection failed with code: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    global is_connected, was_disconnected
    is_connected = False
    if not was_disconnected:
        was_disconnected = True
        store.record_event(SUB_DEVICE_NAME, MASTER_NODE_ID, "NETWORK_OFFLINE", "WARNING", "Mất kết nối CoreIOT! Kích hoạt lưu đệm SQLite Offline Buffer.")
    print("[Gateway] Mất kết nối CoreIOT! Kích hoạt chế độ lưu đệm Offline...")


def on_message(client, userdata, msg):
    try:
        req = json.loads(msg.payload)
    except json.JSONDecodeError:
        print("[Gateway] Invalid RPC JSON payload:", msg.payload)
        return

    if msg.topic == "v1/gateway/rpc":
        device = req.get("device", SUB_DEVICE_NAME)
        data = req.get("data", {})
        request_id = data.get("id")
        method = data.get("method", "")
        params = data.get("params")
        print(f"[Gateway T15 RPC] Device: {device} | ID: {request_id} | Method: {method} | Params: {params}")

        result = handle_rpc_command(method, params, source="CoreIOT T15 RPC", target_node=device)
        resp_payload = {"device": device, "id": request_id, "data": result}
        client.publish("v1/gateway/rpc", json.dumps(resp_payload), qos=1)
    else:
        request_id = msg.topic.split("/")[-1]
        method = req.get("method", "")
        params = req.get("params")
        print(f"[Gateway RPC] Request ID: {request_id} | Method: {method} | Params: {params}")

        result = handle_rpc_command(method, params, source="CoreIOT RPC", target_node=SUB_DEVICE_NAME)
        resp_topic = f"v1/devices/me/rpc/response/{request_id}"
        client.publish(resp_topic, json.dumps(result), qos=1)


def calc_vpd(temp_c, humi_pct):
    svp = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    return svp * (1.0 - humi_pct / 100.0)


def process_local_commands():
    pending = store.pop_pending_commands()
    for cmd in pending:
        params = json.loads(cmd["params_json"])
        handle_rpc_command(cmd["method"], params, source="Local Dashboard (N06)", target_node=cmd["node_id"])


def run_gateway():
    has_serial = init_serial()
    if has_serial:
        threading.Thread(target=serial_reader_loop, daemon=True).start()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(ACCESS_TOKEN)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect_async(BROKER, PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"[Gateway] Error initiating MQTT connection: {e}")

    print("[Gateway] Gateway Service is running. Ingesting telemetry, Event Detection (N06) & Local AI...")

    step = 0
    while True:
        try:
            # 1. Execute any queued commands from the local Custom Dashboard
            process_local_commands()

            # 2. Acquire sensor values (real USB Serial or smooth simulation)
            if not has_serial:
                prev_t = latest_data["temp"]
                prev_h = latest_data["humidity"]
                target_t = 26.5 + 1.8 * math.sin(step * 0.08) + random.uniform(-0.03, 0.03)
                target_h = 77.5 - 3.5 * math.sin(step * 0.08) + random.uniform(-0.08, 0.08)
                t = round(prev_t * 0.85 + target_t * 0.15, 2)
                h = round(prev_h * 0.85 + target_h * 0.15, 2)

                latest_data["delta_temp"] = round(t - prev_t, 3)
                latest_data["delta_humi"] = round(h - prev_h, 3)
                latest_data["temp"] = t
                latest_data["humidity"] = h
                latest_data["vpd"] = round(calc_vpd(t, h), 3)

                if t > TEMP_HIGH or latest_data["vpd"] > 1.4:
                    latest_data["ai_state"] = 1
                    latest_data["ai_state_str"] = "HEAT_STRESS_DRY"
                elif h > HUMI_HIGH or latest_data["vpd"] < 0.4:
                    latest_data["ai_state"] = 2
                    latest_data["ai_state_str"] = "DISEASE_MOLD_RISK"
                else:
                    latest_data["ai_state"] = 0
                    latest_data["ai_state_str"] = "OPTIMAL"
            else:
                t = latest_data["temp"]
                h = latest_data["humidity"]

            gateway_ai.add_reading(t, h)
            ai_insights = gateway_ai.analyze()

            telemetry = {
                "temperature": round(t, 2),
                "humidity": round(h, 2),
                "delta_temp": latest_data["delta_temp"],
                "delta_humi": latest_data["delta_humi"],
                "vpd": round(latest_data["vpd"], 3),
                "tinyml_state": latest_data["ai_state"],
                "tinyml_state_str": latest_data["ai_state_str"],
                "tinyml_confidence": latest_data["ai_conf"],
                "predicted_temp_60m": ai_insights["predicted_temp_60m"],
                "predicted_humi_60m": ai_insights["predicted_humi_60m"],
                "predicted_vpd_60m": ai_insights["predicted_vpd_60m"],
                "temp_rate_per_min": ai_insights["temp_rate_per_min"],
                "thermal_shock_risk": ai_insights["thermal_shock_risk"],
                "dew_risk": ai_insights["dew_risk"],
                "fan_state": actuator_state["fan"],
                "pump_state": actuator_state["pump"],
                "light_state": actuator_state["light"]
            }

            ts_ms = int(time.time() * 1000)

            # 3. Record live telemetry & automated events locally for Custom Dashboard (T10 / N06)
            store.record_telemetry(SUB_DEVICE_NAME, ts_ms, telemetry)
            detect_and_record_events(telemetry)

            # 4. Publish to CoreIOT or save to offline buffer
            if is_connected:
                if GATEWAY_SYNC_ENABLED:
                    payload = {SUB_DEVICE_NAME: [{"ts": ts_ms, "values": telemetry}]}
                    client.publish("v1/gateway/telemetry", json.dumps(payload), qos=1)
                else:
                    client.publish("v1/devices/me/telemetry", json.dumps(telemetry), qos=1)

                if step % 5 == 0:
                    print(f"[Gateway Uplink] T={t:.2f}C | H={h:.1f}% | VPD={latest_data['vpd']:.2f} | AI: {latest_data['ai_state_str']} | Pred_60m={ai_insights['predicted_temp_60m']}C")
            else:
                buffered_count = store.save_offline_packet(SUB_DEVICE_NAME, ts_ms, telemetry)
                print(f"[Offline Buffer] Đã lưu SQLite (Tổng chờ đồng bộ: {buffered_count})")

            step += 1
            time.sleep(AI_CFG.get("sample_interval_sec", 2))
        except KeyboardInterrupt:
            print("\n[Gateway] Shutting down...")
            break
        except Exception as e:
            print(f"[Gateway] Loop error: {e}")
            time.sleep(2)

    client.loop_stop()
    client.disconnect()
    if serial_conn and serial_conn.is_open:
        serial_conn.close()


if __name__ == "__main__":
    run_gateway()
