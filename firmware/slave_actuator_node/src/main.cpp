#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Preferences.h>
#include "slave_config.h"
#include "espnow_protocol.h"

// Biến trạng thái ghép đôi & mạng
static Preferences pref;
static uint8_t master_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static uint8_t broadcast_mac[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static char active_network_id[16] = DEFAULT_NETWORK_ID;
static bool is_paired = false;

// Trạng thái chấp hành
static bool current_fan_state = false;
static bool current_pump_state = false;

// Chu kỳ Heartbeat gửi về Master (mỗi 3 giây)
#define HEARTBEAT_INTERVAL_MS   3000

// Thời gian theo dõi
static uint32_t last_master_ping_ms = 0;
static uint32_t last_heartbeat_send_ms = 0;
static uint32_t last_pair_req_ms = 0;
static uint32_t button_press_start_ms = 0;
static bool button_held = false;

// Hàm điều khiển Relay (xử lý Active LOW / Active HIGH)
void set_relay(uint8_t pin, bool turn_on) {
#if RELAY_ACTIVE_LOW
    digitalWrite(pin, turn_on ? LOW : HIGH);
#else
    digitalWrite(pin, turn_on ? HIGH : LOW);
#endif
}

// Đọc giá trị cảm biến đất (hoặc giả lập nếu chưa cắm cảm biến)
float read_soil_moisture() {
    int raw = analogRead(PIN_SOIL_ANALOG);
    // Ánh xạ ADC (0-4095) thành phần trăm độ ẩm (0-100%)
    // Cảm biến điện dung/điện trở: giá trị càng thấp đất càng ướt
    if (raw > 4000) {
        // Chưa cắm cảm biến đất -> trả về 65.0% giả lập
        return 65.0f;
    }
    float moisture = map(raw, 3200, 1200, 0, 100);
    return constrain(moisture, 0.0f, 100.0f);
}

// Đăng ký Peer vào ESP-NOW
void register_peer(const uint8_t *mac) {
    if (!esp_now_is_peer_exist(mac)) {
        esp_now_peer_info_t peer_info = {};
        memcpy(peer_info.peer_addr, mac, 6);
        peer_info.channel = 0;
        peer_info.encrypt = false;
        esp_now_add_peer(&peer_info);
    }
}

// Callback xác nhận gửi gói tin ESP-NOW
void on_data_sent(const uint8_t *mac, esp_now_send_status_t status) {
    // Chỉ debug nếu cần, tránh spam
}

// Gửi bản tin Heartbeat định kỳ về cho Master Node (Keep-alive & dữ liệu cảm biến)
void send_heartbeat_to_master() {
    float soil_val = read_soil_moisture();
    struct_greenhouse_msg msg = {};
    msg.msg_type = MSG_HEARTBEAT;
    strncpy(msg.network_id, active_network_id, sizeof(msg.network_id));
    strncpy(msg.device_id, SLAVE_DEVICE_ID, sizeof(msg.device_id));
    msg.temp = soil_val; // Đưa độ ẩm đất vào trường temp
    msg.fan = current_fan_state;
    msg.pump = current_pump_state;
    msg.timestamp = millis();

    if (is_paired) {
        esp_err_t res = esp_now_send(master_mac, (uint8_t *)&msg, sizeof(msg));
        Serial.printf("[Heartbeat] ❤️ Đã gửi Heartbeat -> Master [%02X:%02X:%02X:%02X:%02X:%02X]: Đất=%.1f%% | Quạt=%s | Bơm=%s (Mã gửi: %d)\n",
                      master_mac[0], master_mac[1], master_mac[2],
                      master_mac[3], master_mac[4], master_mac[5],
                      soil_val,
                      current_fan_state ? "ON" : "OFF",
                      current_pump_state ? "ON" : "OFF",
                      res);
    } else {
        esp_now_send(broadcast_mac, (uint8_t *)&msg, sizeof(msg));
    }
}

// Bắn yêu cầu xin ghép đôi (Broadcast PAIR_REQ)
void send_pair_request() {
    struct_greenhouse_msg req = {};
    req.msg_type = MSG_PAIR_REQ;
    strncpy(req.network_id, DEFAULT_NETWORK_ID, sizeof(req.network_id));
    strncpy(req.device_id, SLAVE_DEVICE_ID, sizeof(req.device_id));
    req.timestamp = millis();

    esp_now_send(broadcast_mac, (uint8_t *)&req, sizeof(req));
    Serial.println("[Slave] Đang gửi yêu cầu ghép đôi (PAIR_REQ)...");
}

// Callback khi có gói tin ESP-NOW gửi đến
void on_data_recv(const uint8_t *mac, const uint8_t *incoming_data, int len) {
    if (len != sizeof(struct_greenhouse_msg)) return;

    struct_greenhouse_msg msg;
    memcpy(&msg, incoming_data, sizeof(msg));

    // 1. Nhận phản hồi ghép đôi từ Master (PAIR_ACK)
    if (msg.msg_type == MSG_PAIR_ACK) {
        memcpy(master_mac, mac, 6);
        strncpy(active_network_id, msg.network_id, sizeof(active_network_id));
        is_paired = true;

        // Lưu vào bộ nhớ Flash (NVS) để lần sau cắm điện tự nhớ
        pref.putBool("paired", true);
        pref.putBytes("master_mac", master_mac, 6);
        pref.putString("net_id", active_network_id);

        register_peer(master_mac);

        // Áp dụng ngay trạng thái quạt & bơm từ Master
        current_fan_state = msg.fan;
        current_pump_state = msg.pump;
        set_relay(PIN_RELAY_FAN, current_fan_state);
        set_relay(PIN_RELAY_PUMP, current_pump_state);
        last_master_ping_ms = millis();

        Serial.printf("\n==================================================\n");
        Serial.printf("[Slave] GHÉP ĐÔI THÀNH CÔNG VỚI MASTER!\n");
        Serial.printf("  Master ID:  %s\n", msg.device_id);
        Serial.printf("  Master MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                      mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
        Serial.printf("  Network ID: %s\n", active_network_id);
        Serial.printf("==================================================\n");
        return;
    }

    // 2. Nhận lệnh điều khiển riêng hoặc Telemetry từ Master
    if (msg.msg_type == MSG_TELEMETRY) {
        // Cập nhật keep-alive từ Master để không bị watchdog ngắt
        if (strncmp(msg.network_id, active_network_id, 16) == 0) {
            static uint32_t last_telemetry_log_ms = 0;
            last_master_ping_ms = millis();
            if (millis() - last_telemetry_log_ms > 10000) {
                last_telemetry_log_ms = millis();
                Serial.printf("[Slave] Đã nhận tín hiệu Heartbeat từ Master: Temp=%.1f, Humi=%.1f (Kết nối tốt)\n",
                              msg.temp, msg.humi);
            }
        }
        return;
    }

    if (msg.msg_type == MSG_CMD_ACTUATOR) {
        // Kiểm tra đúng Network ID và lệnh dành cho Node này (hoặc "ALL")
        bool is_target = (strcmp(msg.target_id, "ALL") == 0 || strcmp(msg.target_id, SLAVE_DEVICE_ID) == 0);
        bool is_valid_source = (is_paired && memcmp(mac, master_mac, 6) == 0) || (strncmp(msg.network_id, active_network_id, 16) == 0);

        if (is_target && is_valid_source) {
            last_master_ping_ms = millis();

            current_fan_state = msg.fan;
            current_pump_state = msg.pump;

            set_relay(PIN_RELAY_FAN, current_fan_state);
            set_relay(PIN_RELAY_PUMP, current_pump_state);

            Serial.printf("[Slave] ĐÃ NHẬN LỆNH RIÊNG TỪ MASTER: Quạt=%s | Bơm=%s\n",
                          current_fan_state ? "BẬT [ON]" : "TẮT [OFF]",
                          current_pump_state ? "BẬT [ON]" : "TẮT [OFF]");

            // Phản hồi xác nhận trạng thái riêng về cho Master
            send_heartbeat_to_master();
        }
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);

    Serial.println("\n==================================================");
    Serial.println("   SMART GREENHOUSE - SLAVE ACTUATOR NODE         ");
    Serial.printf("   Device ID: %s | Role: %s\n", SLAVE_DEVICE_ID, SLAVE_ROLE);
    Serial.println("==================================================");

    // Cấu hình chân Relay & LED
    pinMode(PIN_RELAY_FAN, OUTPUT);
    pinMode(PIN_RELAY_PUMP, OUTPUT);
    pinMode(PIN_STATUS_LED, OUTPUT);
    pinMode(PIN_BUTTON_PAIR, INPUT_PULLUP);

    // Ban đầu tắt hết Relay để an toàn
    set_relay(PIN_RELAY_FAN, false);
    set_relay(PIN_RELAY_PUMP, false);
    digitalWrite(PIN_STATUS_LED, LOW);

    // Đọc cấu hình ghép đôi từ Flash (NVS)
    pref.begin("slave_cfg", false);
    is_paired = pref.getBool("paired", false);
    if (is_paired) {
        pref.getBytes("master_mac", master_mac, 6);
        String net = pref.getString("net_id", DEFAULT_NETWORK_ID);
        strncpy(active_network_id, net.c_str(), sizeof(active_network_id));
        Serial.printf("[NVS] Đã tải Master MAC: %02X:%02X:%02X:%02X:%02X:%02X (Mạng: %s)\n",
                      master_mac[0], master_mac[1], master_mac[2],
                      master_mac[3], master_mac[4], master_mac[5], active_network_id);
    } else {
        Serial.println("[NVS] Node chưa ghép đôi. Sẽ tự động quét tìm Master...");
    }

    // Khởi tạo Wi-Fi STA mode (Bắt buộc cho ESP-NOW)
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    Serial.printf("[Wi-Fi] Địa chỉ MAC của Slave Node này: %s\n", WiFi.macAddress().c_str());

    if (esp_now_init() != ESP_OK) {
        Serial.println("[ESP-NOW] Khởi tạo thất bại!");
        return;
    }
    Serial.println("[ESP-NOW] Khởi tạo ESP-NOW thành công!");

    esp_now_register_recv_cb(on_data_recv);
    esp_now_register_send_cb(on_data_sent);
    register_peer(broadcast_mac);

    if (is_paired) {
        register_peer(master_mac);
        Serial.println("[ESP-NOW] Đã đăng ký Master peer. Bắt đầu lắng nghe & gửi báo cáo...");
    } else {
        Serial.println("[ESP-NOW] Đang chờ ghép đôi với Master qua nút duyệt trên Web...");
    }

    last_master_ping_ms = millis();
    Serial.println("==================================================\n");
}

void loop() {
    uint32_t now = millis();

    // 1. Xử lý nút bấm BOOT (Nhấn giữ 3 giây để HỦY GHÉP ĐÔI và TÌM MASTER MỚI)
    if (digitalRead(PIN_BUTTON_PAIR) == LOW) {
        if (button_press_start_ms == 0) {
            button_press_start_ms = now;
        } else if (now - button_press_start_ms >= 3000 && !button_held) {
            button_held = true;
            Serial.println("\n[RESET] Đã giữ nút 3s -> XÓA GHÉP ĐÔI! Chuyển sang tìm Master mới...");
            is_paired = false;
            pref.putBool("paired", false);
            // Nháy LED nhanh báo hiệu
            for (int i = 0; i < 5; i++) {
                digitalWrite(PIN_STATUS_LED, HIGH); delay(80);
                digitalWrite(PIN_STATUS_LED, LOW); delay(80);
            }
        }
    } else {
        button_press_start_ms = 0;
        button_held = false;
    }

    // 2. Chế độ chưa ghép đôi -> Gửi PAIR_REQ mỗi 1.5s & nháy LED nhanh
    if (!is_paired) {
        digitalWrite(PIN_STATUS_LED, (now / 150) % 2); // Nháy nhanh 150ms
        if (now - last_pair_req_ms >= 1500) {
            last_pair_req_ms = now;
            send_pair_request();
        }
    } else {
        // Đã ghép đôi -> Bật LED sáng nhẹ nếu có thiết bị đang chạy, hoặc nháy chậm báo sống
        if (current_fan_state || current_pump_state) {
            digitalWrite(PIN_STATUS_LED, HIGH);
        } else {
            digitalWrite(PIN_STATUS_LED, (now / 1000) % 2); // Nháy chậm 1s
        }

        // 3. Định kỳ gửi Heartbeat & cảm biến về Master mỗi 3 giây
        if (now - last_heartbeat_send_ms >= HEARTBEAT_INTERVAL_MS) {
            last_heartbeat_send_ms = now;
            send_heartbeat_to_master();
        }

        // 4. Cơ chế Failsafe Watchdog: Mất kết nối Master quá 45s -> Tự động tắt rơ-le để bảo vệ
        if (now - last_master_ping_ms > FAILSAFE_TIMEOUT_MS) {
            if (current_fan_state || current_pump_state) {
                current_fan_state = false;
                current_pump_state = false;
                set_relay(PIN_RELAY_FAN, false);
                set_relay(PIN_RELAY_PUMP, false);
                Serial.println("[FAILSAFE] MẤT TÍN HIỆU MASTER > 45s! Tự động ngắt Quạt & Bơm để bảo đảm an toàn.");
            }
        }
    }

    delay(20);
}
