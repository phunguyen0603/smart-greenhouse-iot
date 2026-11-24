#ifndef __ESPNOW_TRANSPORT_H__
#define __ESPNOW_TRANSPORT_H__

#include <Arduino.h>

#define DEFAULT_NETWORK_ID    "GH_ZONE_A"
#define MASTER_NODE_ID        "Master-YoloUNO"
#define MAX_SLAVES            8
#define MAX_PENDING_SLAVES    4

enum MessageType : uint8_t {
    MSG_TELEMETRY    = 1,   // Periodic broadcast from Master
    MSG_CMD_ACTUATOR = 2,   // Targeted command to turn on/off actuators on a specific node
    MSG_PAIR_REQ     = 3,   // Slave asks to pair with Master
    MSG_PAIR_ACK     = 4,   // Master approves pairing and sends credentials
    MSG_SLAVE_STATUS = 5,   // Slave reports telemetry / status back to Master
    MSG_HEARTBEAT    = 6    // Slave periodic Heartbeat ping (Keep-alive & sensor telemetry)
};

typedef struct struct_greenhouse_msg {
    uint8_t msg_type;          // MessageType enum
    char network_id[16];       // "GH_ZONE_A"
    char device_id[16];        // Sender ID: "Master-YoloUNO", "Slave-Relay-1", etc.
    char target_id[16];        // Target ID: "ALL" or specific slave MAC/ID
    float temp;                // Temperature / Soil Moisture / Sensor data
    float humi;                // Humidity
    float vpd;                 // VPD
    int ai_state;              // AI classification
    bool fan;                  // Fan state
    bool pump;                 // Pump state
    uint32_t timestamp;        // Millis
} struct_greenhouse_msg;

typedef struct {
    uint8_t mac[6];
    char device_id[16];
    char role[16];             // "Actuator", "Sensor"
    float sensor_val;          // Cảm biến riêng (ví dụ độ ẩm đất %)
    bool fan_status;           // Trạng thái quạt riêng của node này
    bool pump_status;          // Trạng thái máy bơm riêng của node này
    uint32_t last_seen_ms;
    bool is_paired;
} SlaveNodeInfo;

typedef struct {
    uint8_t mac[6];
    char device_id[16];
    uint32_t request_time_ms;
} PendingSlaveReq;

extern SlaveNodeInfo glob_slaves[MAX_SLAVES];
extern int glob_slave_count;
extern PendingSlaveReq glob_pending_slaves[MAX_PENDING_SLAVES];
extern int glob_pending_count;

extern bool glob_pairing_mode;
extern uint32_t glob_pairing_end_ms;

void setup_espnow();
void espnow_task(void *pvParameters);
void espnow_send_command(bool fan, bool pump); // Master local / broadcast
bool espnow_control_slave(const char *mac_str, const char *target, int state_or_toggle); // Điều khiển riêng từng Slave
void espnow_start_pairing(uint32_t duration_sec = 60);
void espnow_stop_pairing();

bool espnow_accept_slave(const char *mac_str);
bool espnow_reject_slave(const char *mac_str);
bool espnow_remove_slave(const char *mac_str);
void load_slaves_from_nvs();
void save_slaves_to_nvs();

#endif // __ESPNOW_TRANSPORT_H__
