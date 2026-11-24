"""
Shared SQLite Storage & Event/Topology Manager for Smart Greenhouse Gateway & Custom Dashboard.
Uses SQLite WAL mode for safe concurrent access between gateway_service.py and dashboard_app.py.
Supports:
- Offline telemetry buffering (T15)
- Real-time telemetry history feed (T10 / N06)
- Automated Event Detection & Recording logs (N06)
- Multi-Gateway -> Multi-MasterNode -> Multi-SubNode topology management
- Local Dashboard -> Gateway command queue
"""

import json
import os
import sqlite3
import threading
import time
from datetime import datetime


class GreenhouseStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_schema()
        self._seed_default_topology()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_schema(self):
        with self._lock, self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS telemetry_buffer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_name TEXT NOT NULL,
                    ts_ms INTEGER NOT NULL,
                    values_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telemetry_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    ts_ms INTEGER NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    vpd REAL,
                    ai_state INTEGER,
                    ai_state_str TEXT,
                    predicted_temp_60m REAL,
                    predicted_vpd_60m REAL,
                    thermal_shock_risk INTEGER DEFAULT 0,
                    dew_risk INTEGER DEFAULT 0,
                    fan_state INTEGER DEFAULT 0,
                    pump_state INTEGER DEFAULT 0,
                    light_state INTEGER DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS event_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_ms INTEGER NOT NULL,
                    timestamp_str TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    master_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    sensor_snapshot_json TEXT,
                    acknowledged INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS topology_gateways (
                    gateway_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host_info TEXT,
                    status TEXT DEFAULT 'ONLINE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS topology_masters (
                    master_id TEXT PRIMARY KEY,
                    gateway_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    mac_addr TEXT,
                    protocol TEXT DEFAULT 'USB Serial / Wi-Fi',
                    status TEXT DEFAULT 'ACTIVE',
                    FOREIGN KEY (gateway_id) REFERENCES topology_gateways(gateway_id)
                );

                CREATE TABLE IF NOT EXISTS topology_nodes (
                    node_id TEXT PRIMARY KEY,
                    master_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    mac_addr TEXT,
                    protocol TEXT DEFAULT 'ESP-NOW',
                    role TEXT DEFAULT 'Hybrid Sensor/Actuator',
                    fan_state INTEGER DEFAULT 0,
                    pump_state INTEGER DEFAULT 0,
                    light_state INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'ONLINE',
                    FOREIGN KEY (master_id) REFERENCES topology_masters(master_id)
                );

                CREATE TABLE IF NOT EXISTS command_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT NOT NULL,
                    method TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    processed INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                );
            """)

    def _seed_default_topology(self):
        with self._lock, self._connect() as conn:
            gw_count = conn.execute("SELECT COUNT(*) FROM topology_gateways").fetchone()[0]
            if gw_count > 0:
                return
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO topology_gateways (gateway_id, name, host_info, status, created_at) VALUES (?, ?, ?, ?, ?)",
                ("GW-PC-01", "Greenhouse_Gateway_PC", "PC Python Gateway (app.coreiot.io)", "ONLINE", now_str),
            )
            conn.executemany(
                "INSERT INTO topology_masters (master_id, gateway_id, name, mac_addr, protocol, status) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("MASTER-ZONE-A", "GW-PC-01", "YoloUNO Master Zone A", "AA:BB:CC:11:22:01", "USB Serial (115200)", "ACTIVE"),
                    ("MASTER-ZONE-B", "GW-PC-01", "YoloUNO Master Zone B", "AA:BB:CC:11:22:02", "Wi-Fi MQTT Bridge", "STANDBY"),
                ],
            )
            conn.executemany(
                "INSERT INTO topology_nodes (node_id, master_id, name, mac_addr, protocol, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    ("YoloUNO_Node1", "MASTER-ZONE-A", "Zone A Climate & TinyML Node", "AA:BB:CC:11:22:01", "I2C + TinyML", "Sensor + Actuator", "ONLINE"),
                    ("Node_Relay_A2", "MASTER-ZONE-A", "Zone A Irrigation & Fan Relay", "AA:BB:CC:11:22:12", "ESP-NOW", "Actuator", "ONLINE"),
                    ("Node_Roof_Tasmota", "MASTER-ZONE-B", "Roof DHT20 Tasmota Node", "AA:BB:CC:11:22:21", "I2C Tasmota", "Sensor", "ONLINE"),
                ],
            )

    # ---------------- Offline Buffer (T15) ----------------
    def save_offline_packet(self, device_name, ts_ms, values_dict):
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO telemetry_buffer (device_name, ts_ms, values_json) VALUES (?, ?, ?)",
                (device_name, ts_ms, json.dumps(values_dict)),
            )
            return conn.execute("SELECT COUNT(*) FROM telemetry_buffer").fetchone()[0]

    def get_offline_packets(self):
        with self._lock, self._connect() as conn:
            return conn.execute(
                "SELECT id, device_name, ts_ms, values_json FROM telemetry_buffer ORDER BY id ASC"
            ).fetchall()

    def delete_offline_packet(self, row_id):
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM telemetry_buffer WHERE id = ?", (row_id,))

    def count_offline_packets(self):
        with self._lock, self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM telemetry_buffer").fetchone()[0]

    # ---------------- Live Telemetry Feed (T10 / N06) ----------------
    def record_telemetry(self, node_id, ts_ms, t):
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO telemetry_history (
                    node_id, ts_ms, temperature, humidity, vpd, ai_state, ai_state_str,
                    predicted_temp_60m, predicted_vpd_60m, thermal_shock_risk, dew_risk,
                    fan_state, pump_state, light_state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    ts_ms,
                    t.get("temperature"),
                    t.get("humidity"),
                    t.get("vpd"),
                    t.get("tinyml_state", 0),
                    t.get("tinyml_state_str", "OPTIMAL"),
                    t.get("predicted_temp_60m"),
                    t.get("predicted_vpd_60m"),
                    int(bool(t.get("thermal_shock_risk", False))),
                    int(bool(t.get("dew_risk", False))),
                    int(bool(t.get("fan_state", False))),
                    int(bool(t.get("pump_state", False))),
                    int(bool(t.get("light_state", True))),
                ),
            )
            # Keep the most recent 2000 rows to prevent unbounded file growth
            conn.execute(
                "DELETE FROM telemetry_history WHERE id NOT IN (SELECT id FROM telemetry_history ORDER BY id DESC LIMIT 2000)"
            )

    def get_recent_telemetry(self, node_id=None, limit=180):
        with self._lock, self._connect() as conn:
            if node_id:
                rows = conn.execute(
                    "SELECT * FROM telemetry_history WHERE node_id = ? ORDER BY id DESC LIMIT ?",
                    (node_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM telemetry_history ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in reversed(rows)]

    # ---------------- Event Detection & Recording (N06) ----------------
    def record_event(self, node_id, master_id, event_type, severity, description, snapshot=None):
        ts_ms = int(time.time() * 1000)
        ts_str = datetime.fromtimestamp(ts_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
        snap_json = json.dumps(snapshot or {}, ensure_ascii=False)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO event_logs (
                    ts_ms, timestamp_str, node_id, master_id, event_type,
                    severity, description, sensor_snapshot_json, acknowledged
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (ts_ms, ts_str, node_id, master_id, event_type, severity, description, snap_json),
            )

    def get_events(self, severity=None, event_type=None, limit=200):
        query = "SELECT * FROM event_logs WHERE 1=1"
        params = []
        if severity and severity != "ALL":
            query += " AND severity = ?"
            params.append(severity)
        if event_type and event_type != "ALL":
            query += " AND event_type = ?"
            params.append(event_type)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def acknowledge_all_events(self):
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE event_logs SET acknowledged = 1 WHERE acknowledged = 0")

    def acknowledge_event(self, event_id):
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE event_logs SET acknowledged = 1 WHERE id = ?", (event_id,))

    # ---------------- Command Queue ----------------
    def enqueue_command(self, node_id, method, params):
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO command_queue (node_id, method, params_json, processed, created_at) VALUES (?, ?, ?, 0, ?)",
                (node_id, method, json.dumps(params), int(time.time() * 1000)),
            )

    def pop_pending_commands(self):
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id, node_id, method, params_json FROM command_queue WHERE processed = 0 ORDER BY id ASC"
            ).fetchall()
            if rows:
                ids = [(r["id"],) for r in rows]
                conn.executemany("UPDATE command_queue SET processed = 1 WHERE id = ?", ids)
            return [dict(r) for r in rows]

    # ---------------- Multi-Gateway / MasterNode / Sub-Node Topology ----------------
    def get_gateways(self):
        with self._lock, self._connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM topology_gateways ORDER BY gateway_id").fetchall()]

    def add_gateway(self, gateway_id, name, host_info="PC Python Gateway"):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO topology_gateways (gateway_id, name, host_info, status, created_at) VALUES (?, ?, ?, 'ONLINE', ?)",
                (gateway_id.strip(), name.strip(), host_info.strip(), now_str),
            )

    def get_masters(self, gateway_id=None):
        with self._lock, self._connect() as conn:
            if gateway_id:
                rows = conn.execute("SELECT * FROM topology_masters WHERE gateway_id = ? ORDER BY master_id", (gateway_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM topology_masters ORDER BY master_id").fetchall()
            return [dict(r) for r in rows]

    def add_master(self, master_id, gateway_id, name, mac_addr="", protocol="USB Serial / Wi-Fi"):
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO topology_masters (master_id, gateway_id, name, mac_addr, protocol, status) VALUES (?, ?, ?, ?, ?, 'ACTIVE')",
                (master_id.strip(), gateway_id, name.strip(), mac_addr.strip(), protocol),
            )

    def reassign_master_gateway(self, master_id, new_gateway_id):
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE topology_masters SET gateway_id = ? WHERE master_id = ?", (new_gateway_id, master_id))

    def get_nodes(self, master_id=None):
        with self._lock, self._connect() as conn:
            if master_id:
                rows = conn.execute("SELECT * FROM topology_nodes WHERE master_id = ? ORDER BY node_id", (master_id,)).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT n.*, m.gateway_id, m.name AS master_name
                    FROM topology_nodes n
                    LEFT JOIN topology_masters m ON n.master_id = m.master_id
                    ORDER BY n.node_id
                    """
                ).fetchall()
            return [dict(r) for r in rows]

    def add_node(self, node_id, master_id, name, mac_addr="", protocol="ESP-NOW", role="Sensor + Actuator"):
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO topology_nodes
                (node_id, master_id, name, mac_addr, protocol, role, status)
                VALUES (?, ?, ?, ?, ?, ?, 'ONLINE')
                """,
                (node_id.strip(), master_id, name.strip(), mac_addr.strip(), protocol, role),
            )

    def reassign_node_master(self, node_id, new_master_id):
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE topology_nodes SET master_id = ? WHERE node_id = ?", (new_master_id, node_id))

    def delete_node(self, node_id):
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM topology_nodes WHERE node_id = ?", (node_id.strip(),))

    def update_node_actuators(self, node_id, fan=None, pump=None, light=None):
        with self._lock, self._connect() as conn:
            if fan is not None:
                conn.execute("UPDATE topology_nodes SET fan_state = ? WHERE node_id = ?", (int(bool(fan)), node_id))
            if pump is not None:
                conn.execute("UPDATE topology_nodes SET pump_state = ? WHERE node_id = ?", (int(bool(pump)), node_id))
            if light is not None:
                conn.execute("UPDATE topology_nodes SET light_state = ? WHERE node_id = ?", (int(bool(light)), node_id))
