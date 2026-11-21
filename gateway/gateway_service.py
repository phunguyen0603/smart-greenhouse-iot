"""
IoT Gateway Core Service (T08 & T15)
Bridges ESP32-S3 (YoloUNO) Node with CoreIOT Cloud Platform via MQTT.
- Ingests telemetry via USB Serial (or smooth simulated fallback when hardware is absent)
- Integrates Gateway Local AI (T09)
- Supports Direct Device Mode (T08: v1/devices/me/*) and Gateway Sync Mode (T15: v1/gateway/*)
- Built-in SQLite Offline Buffer: caches telemetry when offline and auto-syncs on reconnect
- Listens to RPC commands and routes them down to ESP32-S3 actuators
"""

import sys
import os
import time
import json
import math
import random
import sqlite3
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
BUFFER_DB_PATH = os.path.join(BASE_DIR, GW_SYNC_CFG.get("offline_buffer_db", "gateway_buffer.db"))

# Global States
is_connected = False
db_lock = threading.Lock()
serial_lock = threading.Lock()
serial_conn = None

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

gateway_ai = GreenhouseGatewayAI()


# ================= SQLITE OFFLINE BUFFER (T15) =================
def init_buffer_db():
    conn = sqlite3.connect(BUFFER_DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS telemetry_buffer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            ts_ms INTEGER NOT NULL,
            values_json TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


db_conn = init_buffer_db()


def save_offline_packet(device_name, ts_ms, values_dict):
    with db_lock:
        db_conn.execute(
            "INSERT INTO telemetry_buffer (device_name, ts_ms, values_json) VALUES (?, ?, ?)",
            (device_name, ts_ms, json.dumps(values_dict))
        )
        db_conn.commit()
        count = db_conn.execute("SELECT COUNT(*) FROM telemetry_buffer").fetchone()[0]
    print(f"[Offline Buffer] Mất mạng - Đã lưu vào SQLite (Tổng gói chờ đồng bộ: {count})")


def flush_offline_buffer(client):
    with db_lock:
        rows = db_conn.execute(
            "SELECT id, device_name, ts_ms, values_json FROM telemetry_buffer ORDER BY id ASC"
        ).fetchall()
        if not rows:
            return
        print(f"[Offline Sync] Phát hiện {len(rows)} gói tin offline. Đang đồng bộ bù lên CoreIOT...")
        synced = 0
        for row_id, device_name, ts_ms, values_json in rows:
            values = json.loads(values_json)
            if GATEWAY_SYNC_ENABLED:
                payload = {device_name: [{"ts": ts_ms, "values": values}]}
                topic = "v1/gateway/telemetry"
            else:
                payload = {"ts": ts_ms, "values": values}
                topic = "v1/devices/me/telemetry"

            res = client.publish(topic, json.dumps(payload), qos=1)
            if res.rc == mqtt.MQTT_ERR_SUCCESS:
                db_conn.execute("DELETE FROM telemetry_buffer WHERE id = ?", (row_id,))
                synced += 1
            else:
                break
        db_conn.commit()
        print(f"[Offline Sync] Đã đồng bộ bù thành công {synced}/{len(rows)} gói tin!")


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


def handle_rpc_command(method, params):
    method_upper = (method or "").upper()

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
        print(f"[Gateway RPC] >>> FAN -> {'ON' if new_val else 'OFF'}")
        return new_val

    if "SET" in method_upper and "PUMP" in method_upper:
        new_val = parse_bool_param(params)
        actuator_state["pump"] = new_val
        send_serial_command("PUMP_ON" if new_val else "PUMP_OFF")
        print(f"[Gateway RPC] >>> PUMP -> {'ON' if new_val else 'OFF'}")
        return new_val

    if "SET" in method_upper and ("LIGHT" in method_upper or "LED" in method_upper):
        new_val = parse_bool_param(params)
        actuator_state["light"] = new_val
        send_serial_command("LED_ON" if new_val else "LED_OFF")
        print(f"[Gateway RPC] >>> LED/LIGHT -> {'ON' if new_val else 'OFF'}")
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
    global serial_conn
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
    global is_connected
    if reason_code == 0:
        is_connected = True
        mode_str = "GATEWAY SYNC (T15)" if GATEWAY_SYNC_ENABLED else "DIRECT DEVICE (T08)"
        print(f"[Gateway] Connected to CoreIOT ({BROKER}:{PORT}) | Mode: {mode_str}")

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
    global is_connected
    is_connected = False
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

        result = handle_rpc_command(method, params)
        resp_payload = {"device": device, "id": request_id, "data": result}
        client.publish("v1/gateway/rpc", json.dumps(resp_payload), qos=1)
        print(f"[Gateway T15 RPC] Responded: {resp_payload}")
    else:
        request_id = msg.topic.split("/")[-1]
        method = req.get("method", "")
        params = req.get("params")
        print(f"[Gateway RPC] Request ID: {request_id} | Method: {method} | Params: {params}")

        result = handle_rpc_command(method, params)
        resp_topic = f"v1/devices/me/rpc/response/{request_id}"
        client.publish(resp_topic, json.dumps(result), qos=1)
        print(f"[Gateway RPC] Responded on {resp_topic}: {result}")


def calc_vpd(temp_c, humi_pct):
    svp = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    return svp * (1.0 - humi_pct / 100.0)


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

    print("[Gateway] Gateway Service is running. Ingesting telemetry & running Local AI...")

    step = 0
    while True:
        try:
            # Smooth realistic simulation when physical YoloUNO is not connected
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

                if t > 32.0 or latest_data["vpd"] > 1.4:
                    latest_data["ai_state"] = 1
                    latest_data["ai_state_str"] = "HEAT_STRESS_DRY"
                elif h > 90.0 or latest_data["vpd"] < 0.4:
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

            if is_connected:
                if GATEWAY_SYNC_ENABLED:
                    payload = {SUB_DEVICE_NAME: [{"ts": ts_ms, "values": telemetry}]}
                    client.publish("v1/gateway/telemetry", json.dumps(payload), qos=1)
                else:
                    client.publish("v1/devices/me/telemetry", json.dumps(telemetry), qos=1)

                if step % 5 == 0:
                    print(f"[Gateway Uplink] T={t:.2f}C | H={h:.1f}% | VPD={latest_data['vpd']:.2f} | AI: {latest_data['ai_state_str']} | Pred_60m={ai_insights['predicted_temp_60m']}C")
            else:
                save_offline_packet(SUB_DEVICE_NAME, ts_ms, telemetry)

            step += 1
            time.sleep(CONFIG["ai"]["sample_interval_sec"])
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
    db_conn.close()


if __name__ == "__main__":
    run_gateway()
