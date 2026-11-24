#include "espnow_transport.h"
#include <esp_now.h>
#include <WiFi.h>
#include <Preferences.h>
#include "global.h"

// Preferences for persistent storage of approved slave nodes
static Preferences pref;

// Broadcast MAC address
static uint8_t broadcast_mac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

// Slaves management
SlaveNodeInfo glob_slaves[MAX_SLAVES];
int glob_slave_count = 0;

PendingSlaveReq glob_pending_slaves[MAX_PENDING_SLAVES];
int glob_pending_count = 0;

bool glob_pairing_mode = false;
uint32_t glob_pairing_end_ms = 0;

void save_slaves_to_nvs() {
    pref.begin("master_cfg", false);
    pref.putInt("num_slaves", glob_slave_count);
    for (int i = 0; i < glob_slave_count; i++) {
        char key[16];
        snprintf(key, sizeof(key), "mac_%d", i);
        pref.putBytes(key, glob_slaves[i].mac, 6);
        snprintf(key, sizeof(key), "id_%d", i);
        pref.putString(key, glob_slaves[i].device_id);
        snprintf(key, sizeof(key), "role_%d", i);
        pref.putString(key, glob_slaves[i].role);
    }
    pref.end();
    Serial.printf("[NVS] Đã lưu %d Node con đã kết nạp vào bộ nhớ Flash.\n", glob_slave_count);
}

void load_slaves_from_nvs() {
    pref.begin("master_cfg", true);
    int count = pref.getInt("num_slaves", 0);
    if (count > MAX_SLAVES) count = MAX_SLAVES;
    glob_slave_count = count;

    for (int i = 0; i < count; i++) {
        char key[16];
        snprintf(key, sizeof(key), "mac_%d", i);
        pref.getBytes(key, glob_slaves[i].mac, 6);
        snprintf(key, sizeof(key), "id_%d", i);
        String id = pref.getString(key, "Slave");
        strncpy(glob_slaves[i].device_id, id.c_str(), sizeof(glob_slaves[i].device_id));
        snprintf(key, sizeof(key), "role_%d", i);
        String role = pref.getString(key, "Actuator");
        strncpy(glob_slaves[i].role, role.c_str(), sizeof(glob_slaves[i].role));

        glob_slaves[i].is_paired = true;
        glob_slaves[i].last_seen_ms = 0;
        glob_slaves[i].sensor_val = 0.0f;
        glob_slaves[i].fan_status = false;
        glob_slaves[i].pump_status = false;

        // Đăng ký peer với ESP-NOW
        if (!esp_now_is_peer_exist(glob_slaves[i].mac)) {
            esp_now_peer_info_t peer_info = {};
            memcpy(peer_info.peer_addr, glob_slaves[i].mac, 6);
            peer_info.channel = 0;
            peer_info.encrypt = false;
            esp_now_add_peer(&peer_info);
        }
        Serial.printf("[NVS] Đã tải Node con đã kết nạp: %s [%02X:%02X:%02X:%02X:%02X:%02X]\n",
                      glob_slaves[i].device_id,
                      glob_slaves[i].mac[0], glob_slaves[i].mac[1], glob_slaves[i].mac[2],
                      glob_slaves[i].mac[3], glob_slaves[i].mac[4], glob_slaves[i].mac[5]);
    }
    pref.end();
}

static void print_mac(const uint8_t *mac, char *out, size_t max_len) {
    snprintf(out, max_len, "%02X:%02X:%02X:%02X:%02X:%02X",
             mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static bool parse_mac(const char *str, uint8_t *mac) {
    int v[6];
    if (sscanf(str, "%x:%x:%x:%x:%x:%x", &v[0], &v[1], &v[2], &v[3], &v[4], &v[5]) == 6) {
        for (int i = 0; i < 6; i++) mac[i] = (uint8_t)v[i];
        return true;
    }
    return false;
}

static int find_slave_index(const uint8_t *mac) {
    for (int i = 0; i < glob_slave_count; i++) {
        if (memcmp(glob_slaves[i].mac, mac, 6) == 0) {
            return i;
        }
    }
    return -1;
}

static int find_pending_index(const uint8_t *mac) {
    for (int i = 0; i < glob_pending_count; i++) {
        if (memcmp(glob_pending_slaves[i].mac, mac, 6) == 0) {
            return i;
        }
    }
    return -1;
}

static void on_data_sent(const uint8_t *mac_addr, esp_now_send_status_t status) {
    // Optional debug log
}

static void on_data_recv(const uint8_t *mac, const uint8_t *incoming_data, int len) {
    if (len != sizeof(struct_greenhouse_msg)) {
        return;
    }

    struct_greenhouse_msg msg;
    memcpy(&msg, incoming_data, sizeof(msg));

    char mac_str[18];
    print_mac(mac, mac_str, sizeof(mac_str));

    // 1. Xử lý yêu cầu xin ghép đôi (PAIR_REQ) từ Node con
    if (msg.msg_type == MSG_PAIR_REQ) {
        // Kiểm tra xem node này đã từng được duyệt (paired) chưa
        int existing_idx = find_slave_index(mac);
        if (existing_idx >= 0 && glob_slaves[existing_idx].is_paired) {
            // Đã được duyệt từ trước -> gửi lại PAIR_ACK ngay
            struct_greenhouse_msg ack_msg = {};
            ack_msg.msg_type = MSG_PAIR_ACK;
            strncpy(ack_msg.network_id, DEFAULT_NETWORK_ID, sizeof(ack_msg.network_id));
            strncpy(ack_msg.device_id, MASTER_NODE_ID, sizeof(ack_msg.device_id));
            strncpy(ack_msg.target_id, msg.device_id, sizeof(ack_msg.target_id));
            ack_msg.fan = glob_slaves[existing_idx].fan_status;
            ack_msg.pump = glob_slaves[existing_idx].pump_status;
            ack_msg.timestamp = millis();

            esp_now_send(mac, (uint8_t *)&ack_msg, sizeof(ack_msg));
            return;
        }

        // Nếu CHƯA được duyệt -> Đưa vào hàng đợi chờ người dùng bấm [CHẤP NHẬN] trên Web UI
        int pend_idx = find_pending_index(mac);
        if (pend_idx >= 0) {
            glob_pending_slaves[pend_idx].request_time_ms = millis();
        } else if (glob_pending_count < MAX_PENDING_SLAVES) {
            memcpy(glob_pending_slaves[glob_pending_count].mac, mac, 6);
            strncpy(glob_pending_slaves[glob_pending_count].device_id, msg.device_id, sizeof(glob_pending_slaves[glob_pending_count].device_id));
            glob_pending_slaves[glob_pending_count].request_time_ms = millis();
            glob_pending_count++;

            Serial.printf("\n[ESP-NOW] PHÁT HIỆN NODE CON MỚI XIN KẾT NỐI: %s [%s]\n", msg.device_id, mac_str);
            Serial.println("[ESP-NOW] Đang chờ người dùng bấm [CHẤP NHẬN] trên Web Dashboard...");
        }
        return;
    }

    // 2. Xử lý gói tin Trạng thái / Cảm biến riêng từ Node con
    if (strncmp(msg.network_id, DEFAULT_NETWORK_ID, sizeof(msg.network_id)) == 0) {
        int idx = find_slave_index(mac);
        if (idx >= 0) {
            glob_slaves[idx].last_seen_ms = millis();
            glob_slaves[idx].fan_status = msg.fan;
            glob_slaves[idx].pump_status = msg.pump;
            glob_slaves[idx].sensor_val = msg.temp; // Lưu độ ẩm đất riêng của node

            if (msg.msg_type == MSG_HEARTBEAT || msg.msg_type == MSG_SLAVE_STATUS) {
                static uint32_t last_hb_print = 0;
                if (millis() - last_hb_print > 5000) {
                    last_hb_print = millis();
                    Serial.printf("[ESP-NOW] ❤️ Nhận Heartbeat từ %s [%s]: Đất=%.1f%%, Fan=%s, Pump=%s [ALIVE]\n",
                                  msg.device_id, mac_str,
                                  msg.temp,
                                  msg.fan ? "ON" : "OFF",
                                  msg.pump ? "ON" : "OFF");
                }
            }
        } else {
            // Node con này chưa có trong danh sách kết nạp của Master!
            // Đưa ngay vào hàng chờ duyệt để xuất hiện trong mục Cài đặt trên Web
            int pend_idx = find_pending_index(mac);
            if (pend_idx >= 0) {
                glob_pending_slaves[pend_idx].request_time_ms = millis();
            } else if (glob_pending_count < MAX_PENDING_SLAVES) {
                memcpy(glob_pending_slaves[glob_pending_count].mac, mac, 6);
                strncpy(glob_pending_slaves[glob_pending_count].device_id, msg.device_id, sizeof(glob_pending_slaves[glob_pending_count].device_id));
                glob_pending_slaves[glob_pending_count].request_time_ms = millis();
                glob_pending_count++;
                Serial.printf("\n[ESP-NOW] Phát hiện Node con chưa kết nạp gửi tín hiệu: %s [%s] -> Đưa vào mục Cài đặt chờ duyệt!\n",
                              msg.device_id, mac_str);
            }
        }
    }
}

// Người dùng bấm [CHẤP NHẬN KẾT NẠP] trong mục Cài đặt trên Web UI
bool espnow_accept_slave(const char *mac_str) {
    uint8_t target_mac[6];
    if (!parse_mac(mac_str, target_mac)) return false;

    int pend_idx = find_pending_index(target_mac);
    if (pend_idx < 0) return false;

    if (!esp_now_is_peer_exist(target_mac)) {
        esp_now_peer_info_t peer_info = {};
        memcpy(peer_info.peer_addr, target_mac, 6);
        peer_info.channel = 0;
        peer_info.encrypt = false;
        esp_now_add_peer(&peer_info);
    }

    int idx = find_slave_index(target_mac);
    if (idx < 0 && glob_slave_count < MAX_SLAVES) {
        idx = glob_slave_count++;
    }

    if (idx >= 0) {
        memcpy(glob_slaves[idx].mac, target_mac, 6);
        strncpy(glob_slaves[idx].device_id, glob_pending_slaves[pend_idx].device_id, sizeof(glob_slaves[idx].device_id));
        strncpy(glob_slaves[idx].role, "Actuator", sizeof(glob_slaves[idx].role));
        glob_slaves[idx].fan_status = false;
        glob_slaves[idx].pump_status = false;
        glob_slaves[idx].sensor_val = 0.0f;
        glob_slaves[idx].last_seen_ms = millis();
        glob_slaves[idx].is_paired = true;
    }

    // Lưu vĩnh viễn vào bộ nhớ Flash (NVS) của Master
    save_slaves_to_nvs();

    // Gửi gói tin PAIR_ACK xác nhận cho Node con
    struct_greenhouse_msg ack_msg = {};
    ack_msg.msg_type = MSG_PAIR_ACK;
    strncpy(ack_msg.network_id, DEFAULT_NETWORK_ID, sizeof(ack_msg.network_id));
    strncpy(ack_msg.device_id, MASTER_NODE_ID, sizeof(ack_msg.device_id));
    strncpy(ack_msg.target_id, glob_pending_slaves[pend_idx].device_id, sizeof(ack_msg.target_id));
    ack_msg.fan = false;
    ack_msg.pump = false;
    ack_msg.timestamp = millis();

    esp_now_send(target_mac, (uint8_t *)&ack_msg, sizeof(ack_msg));

    Serial.printf("[ESP-NOW] ĐÃ KẾT NẠP THÀNH CÔNG VÀ LƯU FLASH NODE: %s [%s]!\n",
                  glob_pending_slaves[pend_idx].device_id, mac_str);

    for (int i = pend_idx; i < glob_pending_count - 1; i++) {
        glob_pending_slaves[i] = glob_pending_slaves[i + 1];
    }
    glob_pending_count--;
    return true;
}

// Người dùng bấm [TỪ CHỐI] trên Web UI
bool espnow_reject_slave(const char *mac_str) {
    uint8_t target_mac[6];
    if (!parse_mac(mac_str, target_mac)) return false;

    int pend_idx = find_pending_index(target_mac);
    if (pend_idx < 0) return false;

    Serial.printf("[ESP-NOW] Đã từ chối node: %s [%s]\n",
                  glob_pending_slaves[pend_idx].device_id, mac_str);

    for (int i = pend_idx; i < glob_pending_count - 1; i++) {
        glob_pending_slaves[i] = glob_pending_slaves[i + 1];
    }
    glob_pending_count--;
    return true;
}

// Người dùng bấm [HỦY KẾT NẠP / XÓA NODE] trên Web UI
bool espnow_remove_slave(const char *mac_str) {
    uint8_t target_mac[6];
    if (!parse_mac(mac_str, target_mac)) return false;

    int idx = find_slave_index(target_mac);
    if (idx < 0) return false;

    Serial.printf("[ESP-NOW] Hủy kết nạp Node: %s [%s]\n", glob_slaves[idx].device_id, mac_str);

    // Xóa peer khỏi ESP-NOW
    if (esp_now_is_peer_exist(target_mac)) {
        esp_now_del_peer(target_mac);
    }

    // Dồn mảng xóa node
    for (int i = idx; i < glob_slave_count - 1; i++) {
        glob_slaves[i] = glob_slaves[i + 1];
    }
    glob_slave_count--;

    // Cập nhật lại vào Flash
    save_slaves_to_nvs();
    return true;
}

// ĐIỀU KHIỂN RIÊNG CHO TỪNG SLAVE NODE CỤ THỂ
bool espnow_control_slave(const char *mac_str, const char *target, int state_or_toggle) {
    uint8_t target_mac[6];
    if (!parse_mac(mac_str, target_mac)) return false;

    int idx = find_slave_index(target_mac);
    if (idx < 0) return false;

    // Cập nhật trạng thái riêng của Slave này
    if (strcmp(target, "fan") == 0) {
        if (state_or_toggle < 0) glob_slaves[idx].fan_status = !glob_slaves[idx].fan_status;
        else glob_slaves[idx].fan_status = (state_or_toggle != 0);
    } else if (strcmp(target, "pump") == 0) {
        if (state_or_toggle < 0) glob_slaves[idx].pump_status = !glob_slaves[idx].pump_status;
        else glob_slaves[idx].pump_status = (state_or_toggle != 0);
    }

    // Đóng gói bản tin lệnh riêng biệt gửi tới Node con
    struct_greenhouse_msg cmd = {};
    cmd.msg_type = MSG_CMD_ACTUATOR;
    strncpy(cmd.network_id, DEFAULT_NETWORK_ID, sizeof(cmd.network_id));
    strncpy(cmd.device_id, MASTER_NODE_ID, sizeof(cmd.device_id));
    strncpy(cmd.target_id, glob_slaves[idx].device_id, sizeof(cmd.target_id));
    cmd.fan = glob_slaves[idx].fan_status;
    cmd.pump = glob_slaves[idx].pump_status;
    cmd.timestamp = millis();

    // Gửi trực tiếp Unicast đến MAC của Node con này
    esp_now_send(target_mac, (uint8_t *)&cmd, sizeof(cmd));

    Serial.printf("[ESP-NOW] Lệnh riêng gửi tới %s [%s]: Quạt=%s | Bơm=%s\n",
                  glob_slaves[idx].device_id, mac_str,
                  glob_slaves[idx].fan_status ? "ON" : "OFF",
                  glob_slaves[idx].pump_status ? "ON" : "OFF");
    return true;
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
        Serial.println("[ESP-NOW] Broadcast transport & Individual Slave Controller ready.");
    }

    // Tải các Node con đã kết nạp từ Flash (NVS)
    load_slaves_from_nvs();
}

void espnow_start_pairing(uint32_t duration_sec) {
    glob_pairing_mode = true;
    glob_pairing_end_ms = millis() + (duration_sec * 1000);
    Serial.printf("[ESP-NOW] Pairing Mode ENABLED for %u seconds\n", duration_sec);
}

void espnow_stop_pairing() {
    glob_pairing_mode = false;
    Serial.println("[ESP-NOW] Pairing Mode DISABLED");
}

void espnow_send_command(bool fan, bool pump) {
    struct_greenhouse_msg msg = {};
    msg.msg_type = MSG_CMD_ACTUATOR;
    strncpy(msg.network_id, DEFAULT_NETWORK_ID, sizeof(msg.network_id));
    strncpy(msg.device_id, MASTER_NODE_ID, sizeof(msg.device_id));
    strncpy(msg.target_id, "ALL", sizeof(msg.target_id));
    msg.temp = glob_temperature;
    msg.humi = glob_humidity;
    msg.vpd = glob_vpd;
    msg.ai_state = glob_ai_state;
    msg.fan = fan;
    msg.pump = pump;
    msg.timestamp = millis();

    // Broadcast cho các thiết bị lắng nghe
    esp_now_send(broadcast_mac, (uint8_t *)&msg, sizeof(msg));
}

void espnow_task(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(2000));
    setup_espnow();

    struct_greenhouse_msg msg = {};
    msg.msg_type = MSG_TELEMETRY;
    strncpy(msg.network_id, DEFAULT_NETWORK_ID, sizeof(msg.network_id));
    strncpy(msg.device_id, MASTER_NODE_ID, sizeof(msg.device_id));
    strncpy(msg.target_id, "ALL", sizeof(msg.target_id));

    while (1) {
        uint32_t now = millis();

        // Tự động xóa các request chờ duyệt quá hạn (30 giây)
        for (int i = 0; i < glob_pending_count; i++) {
            if (now - glob_pending_slaves[i].request_time_ms > 30000) {
                for (int j = i; j < glob_pending_count - 1; j++) {
                    glob_pending_slaves[j] = glob_pending_slaves[j + 1];
                }
                glob_pending_count--;
                i--;
            }
        }

        // Telemetry định kỳ của Master
        msg.msg_type = MSG_TELEMETRY;
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
