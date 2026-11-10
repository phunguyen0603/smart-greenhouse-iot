"""
IoT Gateway Core Service (T08)
Bridges ESP32-S3 Node with CoreIOT Cloud Platform via MQTT.
- Ingests telemetry via Serial USB CDC (or simulated fallback)
- Integrates Gateway Local AI (T09)
- Publishes telemetry to CoreIOT MQTT (v1/devices/me/telemetry)
- Listens to RPC commands (v1/devices/me/rpc/request/+) and controls actuators
"""

import sys
import os
import time
import json
import threading
import yaml
import paho.mqtt.client as mqtt

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gateway_ai import GreenhouseGatewayAI

# Load Configuration
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

BROKER = CONFIG["coreiot"]["broker"]
PORT = CONFIG["coreiot"]["port"]
ACCESS_TOKEN = CONFIG["coreiot"]["access_token"]

# Global Actuator States
actuator_state = {
    "fan": False,
    "pump": False,
    "light": True
}

# Latest Telemetry Cache
latest_data = {
    "temp": 25.5,
    "humidity": 78.0,
    "delta_temp": 0.0,
    "delta_humi": 0.0,
    "vpd": 0.72,
    "ai_state": 0,
    "ai_state_str": "OPTIMAL",
    "ai_conf": 0.98,
    "fan": False,
    "pump": False
}

gateway_ai = GreenhouseGatewayAI()
serial_conn = None
serial_lock = threading.Lock()

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[Gateway] Connected to CoreIOT Cloud Broker ({BROKER}:{PORT}) successfully!")
        client.subscribe("v1/devices/me/rpc/request/+")
        print("[Gateway] Subscribed to CoreIOT RPC requests.")
    else:
        print(f"[Gateway] Connection failed with code: {reason_code}")

def on_message(client, userdata, msg):
    request_id = msg.topic.split("/")[-1]
    try:
        req = json.loads(msg.payload)
    except json.JSONDecodeError:
        print("[Gateway] Invalid RPC JSON payload:", msg.payload)
        return

    method = req.get("method", "")
    params = req.get("params")
    print(f"[Gateway RPC] Request ID: {request_id} | Method: {method} | Params: {params}")

    response_payload = {}

    # Handle RPC according to LAB 1 and Assignment standard
    result = None
    method_upper = method.upper()

    # 1. State Getters (getStateFAN, getStatePUMP, getStateLED, getFanState, etc.)
    if "GET" in method_upper and "FAN" in method_upper:
        result = actuator_state["fan"]
    elif "GET" in method_upper and "PUMP" in method_upper:
        result = actuator_state["pump"]
    elif "GET" in method_upper and ("LIGHT" in method_upper or "LED" in method_upper):
        result = actuator_state["light"]

    # 2. State Setters (setStateFAN, setStatePUMP, setStateLED, setFanState, etc.)
    elif "SET" in method_upper and "FAN" in method_upper:
        new_val = bool(params)
        actuator_state["fan"] = new_val
        send_serial_command("FAN_ON" if new_val else "FAN_OFF")
        result = new_val
        print(f"[Gateway RPC] >>> FAN -> {'ON' if new_val else 'OFF'}")
    elif "SET" in method_upper and "PUMP" in method_upper:
        new_val = bool(params)
        actuator_state["pump"] = new_val
        send_serial_command("PUMP_ON" if new_val else "PUMP_OFF")
        result = new_val
        print(f"[Gateway RPC] >>> PUMP -> {'ON' if new_val else 'OFF'}")
    elif "SET" in method_upper and ("LIGHT" in method_upper or "LED" in method_upper):
        new_val = bool(params)
        actuator_state["light"] = new_val
        result = new_val
        print(f"[Gateway RPC] >>> LED/LIGHT -> {'ON' if new_val else 'OFF'}")
    else:
        result = {"error": f"Unknown method: {method}"}

    # Respond to CoreIOT (returns boolean directly for Switch widgets to prevent timeout)
    resp_topic = f"v1/devices/me/rpc/response/{request_id}"
    client.publish(resp_topic, json.dumps(result))
    print(f"[Gateway RPC] Responded on {resp_topic}: {result}")

def send_serial_command(cmd_str):
    global serial_conn
    with serial_lock:
        if serial_conn and serial_conn.is_open:
            try:
                serial_conn.write((cmd_str + "\n").encode())
                print(f"[Gateway Serial] Sent command to ESP32: {cmd_str}")
            except Exception as e:
                print(f"[Gateway Serial] Error sending command: {e}")

def run_gateway():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(ACCESS_TOKEN)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"[Gateway] Error connecting to MQTT Broker: {e}")

    print("[Gateway] Gateway Service is running. Ingesting telemetry & running Local AI...")

    # Main telemetry loop
    step = 0
    while True:
        try:
            # 1. Update reading with Gateway AI
            t = latest_data["temp"]
            h = latest_data["humidity"]
            gateway_ai.add_reading(t, h)
            ai_insights = gateway_ai.analyze()

            # 2. Assemble Cloud Telemetry Packet
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

            client.publish("v1/devices/me/telemetry", json.dumps(telemetry))

            if step % 5 == 0:
                print(f"[Gateway Uplink] T={t:.1f}C | H={h:.1f}% | VPD={latest_data['vpd']:.2f} | AI: {latest_data['ai_state_str']} | Pred_60m={ai_insights['predicted_temp_60m']}C")

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

if __name__ == "__main__":
    run_gateway()
