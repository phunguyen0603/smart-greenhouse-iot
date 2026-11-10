#include "ota_service.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <Update.h>
#include <ArduinoOTA.h>

void setup_ota() {
    ArduinoOTA.setHostname("SmartGreenhouse-YoloUNO");
    ArduinoOTA.setPassword("admin123");

    ArduinoOTA.onStart([]() {
        String type;
        if (ArduinoOTA.getCommand() == U_FLASH) {
            type = "sketch";
        } else {
            type = "filesystem";
        }
        Serial.println("[OTA] Start updating " + type);
    });

    ArduinoOTA.onEnd([]() {
        Serial.println("\n[OTA] Firmware update complete! Rebooting...");
    });

    ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
        Serial.printf("[OTA] Progress: %u%%\r", (progress / (total / 100)));
    });

    ArduinoOTA.onError([](ota_error_t error) {
        Serial.printf("[OTA] Error[%u]: ", error);
        if (error == OTA_AUTH_ERROR) Serial.println("Auth Failed");
        else if (error == OTA_BEGIN_ERROR) Serial.println("Begin Failed");
        else if (error == OTA_CONNECT_ERROR) Serial.println("Connect Failed");
        else if (error == OTA_RECEIVE_ERROR) Serial.println("Receive Failed");
        else if (error == OTA_END_ERROR) Serial.println("End Failed");
    });

    ArduinoOTA.begin();
    Serial.printf("[OTA] ArduinoOTA service initialized (Version: %s)\n", FIRMWARE_VERSION);
}

bool perform_http_ota(const char* firmware_url) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[OTA] HTTP OTA failed: Wi-Fi not connected!");
        return false;
    }

    HTTPClient http;
    http.begin(firmware_url);
    int httpCode = http.GET();

    if (httpCode != HTTP_CODE_OK) {
        Serial.printf("[OTA] HTTP GET failed, error: %s\n", http.errorToString(httpCode).c_str());
        http.end();
        return false;
    }

    int contentLength = http.getSize();
    if (contentLength <= 0) {
        Serial.println("[OTA] Invalid content length!");
        http.end();
        return false;
    }

    bool canBegin = Update.begin(contentLength);
    if (!canBegin) {
        Serial.println("[OTA] Not enough space for OTA update!");
        http.end();
        return false;
    }

    WiFiClient* stream = http.getStreamPtr();
    size_t written = Update.writeStream(*stream);

    if (written != contentLength) {
        Serial.printf("[OTA] Written only : %d/%d bytes\n", written, contentLength);
        http.end();
        return false;
    }

    if (!Update.end()) {
        Serial.printf("[OTA] Update error #: %u\n", Update.getError());
        http.end();
        return false;
    }

    if (!Update.isFinished()) {
        Serial.println("[OTA] Update not finished?");
        http.end();
        return false;
    }

    Serial.println("[OTA] HTTP OTA successfully finished! Restarting...");
    http.end();
    ESP.restart();
    return true;
}

void ota_task(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(3000));
    setup_ota();

    while (1) {
        ArduinoOTA.handle();
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
