#ifndef __OTA_SERVICE_H__
#define __OTA_SERVICE_H__

#include <Arduino.h>

#define FIRMWARE_VERSION "1.0.0"

void setup_ota();
void ota_task(void *pvParameters);
bool perform_http_ota(const char* firmware_url);

#endif // __OTA_SERVICE_H__
