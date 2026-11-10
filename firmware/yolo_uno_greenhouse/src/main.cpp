#include <Arduino.h>
#include "global.h"
#include "sensor_lcd_task.h"
#include "tinyml_task.h"
#include "webserver_task.h"
#include "espnow_transport.h"
#include "ota_service.h"

void serial_uplink_task(void *pvParameters) {
    while (1) {
        // Output clean JSON on USB CDC Serial for PC Gateway (T08)
        Serial.printf("{\"temp\":%.2f,\"humidity\":%.2f,\"delta_temp\":%.2f,\"delta_humi\":%.2f,\"vpd\":%.3f,\"ai_state\":%d,\"ai_state_str\":\"%s\",\"ai_conf\":%.2f,\"infer_us\":%lu,\"fan\":%s,\"pump\":%s}\n",
                      glob_temperature, glob_humidity,
                      glob_delta_temp, glob_delta_humi,
                      glob_vpd,
                      glob_ai_state, getStateString((ClimateHealthState)glob_ai_state),
                      glob_ai_confidence, glob_inference_time_us,
                      glob_fan_state ? "true" : "false",
                      glob_pump_state ? "true" : "false");
        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}

void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n==================================================");
    Serial.println("   SMART GREENHOUSE MONITORING SYSTEM (HK261)    ");
    Serial.println("   Platform: ESP32-S3 YoloUNO | CoreIOT Cloud    ");
    Serial.printf("   Firmware Version: %s\n", FIRMWARE_VERSION);
    Serial.println("==================================================");

    // Create FreeRTOS Multitasking Tasks
    xTaskCreatePinnedToCore(sensor_lcd_task,     "SensorLCD", 4096, NULL, 2, NULL, 1);
    xTaskCreatePinnedToCore(tinyml_task,         "TinyML",    8192, NULL, 1, NULL, 1);
    xTaskCreatePinnedToCore(webserver_task,      "WebServer", 4096, NULL, 1, NULL, 0);
    xTaskCreatePinnedToCore(espnow_task,         "ESP-NOW",   2048, NULL, 1, NULL, 0);
    xTaskCreatePinnedToCore(ota_task,            "OTA",       4096, NULL, 1, NULL, 0);
    xTaskCreatePinnedToCore(serial_uplink_task,  "SerialUp",  2048, NULL, 1, NULL, 0);
}

void loop() {
    // Check for Serial commands from Gateway PC
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd == "FAN_ON") {
            glob_fan_state = true;
            Serial.println("[CMD] Fan switched ON");
        } else if (cmd == "FAN_OFF") {
            glob_fan_state = false;
            Serial.println("[CMD] Fan switched OFF");
        } else if (cmd == "PUMP_ON") {
            glob_pump_state = true;
            Serial.println("[CMD] Pump switched ON");
        } else if (cmd == "PUMP_OFF") {
            glob_pump_state = false;
            Serial.println("[CMD] Pump switched OFF");
        }
    }
    vTaskDelay(pdMS_TO_TICKS(50));
}
