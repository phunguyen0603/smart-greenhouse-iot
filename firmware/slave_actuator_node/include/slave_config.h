#ifndef __SLAVE_CONFIG_H__
#define __SLAVE_CONFIG_H__

// Định danh Node con
#define SLAVE_DEVICE_ID         "Slave-Relay-01"
#define SLAVE_ROLE              "Actuator"

// Cấu hình chân (Hỗ trợ cả ESP32 DevKit thông dụng và YoloUNO)
#if defined(CONFIG_IDF_TARGET_ESP32S3)
  // Dành cho ESP32-S3 / YoloUNO
  #define PIN_RELAY_FAN         4   // D4 trên YoloUNO
  #define PIN_RELAY_PUMP        5   // D5 trên YoloUNO
  #define PIN_BUTTON_PAIR       0   // Nút BOOT trên mạch
  #define PIN_STATUS_LED        48  // LED tích hợp trên YoloUNO
  #define PIN_SOIL_ANALOG       1   // Cảm biến độ ẩm đất (chân A0 / GPIO 1)
#else
  // Dành cho ESP32 DevKit / ESP32 NodeMCU thông thường
  #define PIN_RELAY_FAN         18  // Chân điều khiển Relay Quạt
  #define PIN_RELAY_PUMP        19  // Chân điều khiển Relay Máy bơm
  #define PIN_BUTTON_PAIR       0   // Nút BOOT trên ESP32 DevKit
  #define PIN_STATUS_LED        2   // LED báo trạng thái (có sẵn trên chân D2)
  #define PIN_SOIL_ANALOG       34  // Cảm biến độ ẩm đất (chân ADC GPIO 34)
#endif

// Đa số Module Relay bán trên thị trường là kích mức THẤP (Active LOW)
// Nếu Relay của bạn kích mức CAO (Active HIGH), hãy đổi thành false
#define RELAY_ACTIVE_LOW        true

// Thời gian mất kết nối với Master để tự động ngắt tải an toàn (Failsafe)
#define FAILSAFE_TIMEOUT_MS     45000  // 45 giây

#endif // __SLAVE_CONFIG_H__
