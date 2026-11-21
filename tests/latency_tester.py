"""
Latency & Performance Tester (Report Chapter 4)
Measures real MQTT QoS=1 publish-acknowledgment (PUBACK) latency
from local PC Gateway to CoreIOT Cloud Broker (app.coreiot.io).
"""

import os
import time
import json
import yaml
import numpy as np
import paho.mqtt.client as mqtt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "gateway", "config.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

BROKER = CONFIG["coreiot"]["broker"]
PORT = CONFIG["coreiot"]["port"]
ACCESS_TOKEN = CONFIG["coreiot"]["access_token"]


def run_test(num_packets=30):
    latencies_ms = []
    connected_event = False

    def on_connect(client, userdata, flags, reason_code, properties=None):
        nonlocal connected_event
        if reason_code == 0:
            connected_event = True
            print(f"[Latency Tester] Connected to {BROKER}:{PORT}")
        else:
            print(f"[Latency Tester] Connection failed: {reason_code}")

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
        nonlocal connected_event
        connected_event = False
        print("[Latency Tester] Disconnected! (Lưu ý: Tắt gateway_service.py trước khi chạy test để không bị đụng Access Token)")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(ACCESS_TOKEN)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"Cannot connect to broker: {e}")
        return

    # Wait up to 5 seconds for connection
    wait_start = time.time()
    while not connected_event and (time.time() - wait_start < 5.0):
        time.sleep(0.1)

    if not connected_event:
        print("[Latency Tester] Connection timeout.")
        client.loop_stop()
        return

    print(f"Measuring MQTT QoS=1 PUBACK latency for {num_packets} packets...")
    failed = 0
    for i in range(num_packets):
        payload = {
            "latency_probe_id": i + 1,
            "temperature": round(25.0 + (i % 5) * 0.2, 2),
            "humidity": 75.0
        }
        t0 = time.perf_counter()
        info = client.publish("v1/devices/me/telemetry", json.dumps(payload), qos=1)
        try:
            info.wait_for_publish(timeout=5.0)
            t1 = time.perf_counter()
            dt_ms = (t1 - t0) * 1000.0
            latencies_ms.append(dt_ms)
            print(f"  Packet {i+1:02d}/{num_packets}: {dt_ms:.2f} ms")
        except Exception as e:
            failed += 1
            print(f"  Packet {i+1:02d}/{num_packets}: FAILED ({e})")
        time.sleep(0.3)

    client.loop_stop()
    client.disconnect()

    if latencies_ms:
        arr = np.array(latencies_ms)
        print("\n=== CHAPTER 4 TELEMETRY LATENCY SUMMARY ===")
        print(f"Total Sent      : {num_packets}")
        print(f"Delivered (QoS1): {len(latencies_ms)} ({(len(latencies_ms)/num_packets)*100:.1f}%)")
        print(f"Average Latency : {np.mean(arr):.2f} ms")
        print(f"Min / Max       : {np.min(arr):.2f} ms / {np.max(arr):.2f} ms")
        print(f"P95 Latency     : {np.percentile(arr, 95):.2f} ms")
        print(f"Std Dev         : {np.std(arr):.2f} ms")
    else:
        print("No packets measured.")


if __name__ == "__main__":
    run_test(30)
