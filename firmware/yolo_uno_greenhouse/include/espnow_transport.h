#ifndef __ESPNOW_TRANSPORT_H__
#define __ESPNOW_TRANSPORT_H__

#include <Arduino.h>

typedef struct struct_greenhouse_msg {
    char device_id[16];
    float temp;
    float humi;
    float vpd;
    int ai_state;
    bool fan;
    bool pump;
    uint32_t timestamp;
} struct_greenhouse_msg;

void setup_espnow();
void espnow_task(void *pvParameters);

#endif // __ESPNOW_TRANSPORT_H__
