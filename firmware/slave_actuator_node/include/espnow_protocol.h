#ifndef __ESPNOW_PROTOCOL_H__
#define __ESPNOW_PROTOCOL_H__

#include <Arduino.h>

#define DEFAULT_NETWORK_ID    "GH_ZONE_A"
#define MASTER_NODE_ID        "Master-YoloUNO"

enum MessageType : uint8_t {
    MSG_TELEMETRY    = 1,   // Periodic broadcast from Master
    MSG_CMD_ACTUATOR = 2,   // Targeted command to turn on/off actuators
    MSG_PAIR_REQ     = 3,   // Slave asks to pair with Master
    MSG_PAIR_ACK     = 4,   // Master approves pairing and sends credentials
    MSG_SLAVE_STATUS = 5,   // Slave reports telemetry / status back to Master
    MSG_HEARTBEAT    = 6    // Slave periodic Heartbeat ping (Keep-alive & sensor telemetry)
};

typedef struct struct_greenhouse_msg {
    uint8_t msg_type;          // MessageType enum
    char network_id[16];       // "GH_ZONE_A"
    char device_id[16];        // Sender ID: "Slave-Relay-01"
    char target_id[16];        // Target ID: "ALL" or specific slave ID
    float temp;                // Soil moisture / local sensor data
    float humi;                // Local humidity
    float vpd;                 // VPD
    int ai_state;              // AI classification
    bool fan;                  // Fan state
    bool pump;                 // Pump state
    uint32_t timestamp;        // Millis
} struct_greenhouse_msg;

#endif // __ESPNOW_PROTOCOL_H__
