#include "espnow_transport.h"
#include <esp_now.h>
#include <WiFi.h>
#include "global.h"

// Broadcast MAC address
static uint8_t broadcast_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

static void on_data_sent(const uint8_t *mac_addr, esp_now_send_status_t status) {
    // Optional debug log
}

static void on_data_recv(const uint8_t *mac, const uint8_t *incoming_data, int len) {
    if (len == sizeof(struct_greenhouse_msg)) {
        struct_greenhouse_msg msg;
        memcpy(&msg, incoming_data, sizeof(msg));
        // If receiver node gets command
        glob_fan_state = msg.fan;
        glob_pump_state = msg.pump;
    }
}

void setup_espnow() {
    if (esp_now_init() != ESP_OK) {
        Serial.println("[ESP-NOW] Init Failed!");
        return;
    }

    esp_now_register_send_cb(on_data_sent);
    esp_now_register_recv_cb(on_data_recv);

    esp_now_peer_info_t peer_info = {};
    memcpy(peer_info.peer_addr, broadcast_mac, 6);
    peer_info.channel = 0;
    peer_info.encrypt = false;

    if (esp_now_add_peer(&peer_info) != ESP_OK) {
        Serial.println("[ESP-NOW] Failed to add broadcast peer!");
    } else {
        Serial.println("[ESP-NOW] Broadcast transport ready.");
    }
}

void espnow_task(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(2000));
    setup_espnow();

    struct_greenhouse_msg msg;
    snprintf(msg.device_id, sizeof(msg.device_id), "YoloUNO-Node1");

    while (1) {
        msg.temp = glob_temperature;
        msg.humi = glob_humidity;
        msg.vpd = glob_vpd;
        msg.ai_state = glob_ai_state;
        msg.fan = glob_fan_state;
        msg.pump = glob_pump_state;
        msg.timestamp = millis();

        esp_now_send(broadcast_mac, (uint8_t *)&msg, sizeof(msg));
        vTaskDelay(pdMS_TO_TICKS(3000));
    }
}
