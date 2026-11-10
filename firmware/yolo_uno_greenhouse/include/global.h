#ifndef __GLOBAL_H__
#define __GLOBAL_H__

#include <Arduino.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "greenhouse_profile.h"

// Pin definitions on YoloUNO (ESP32-S3)
#define LED_PIN         48
#define NEO_PIN         45
#define LED_COUNT       1
#define I2C_SDA_PIN     11
#define I2C_SCL_PIN     12
#define LCD_I2C_ADDR    33  // 0x21 as in LAB 3 Support Files

// Shared variables across FreeRTOS tasks (inherited from LAB 3 Support Files)
extern float glob_temperature;
extern float glob_humidity;
extern float glob_delta_temp;
extern float glob_delta_humi;
extern float glob_vpd;

// TinyML inference results
extern int glob_ai_state;      // 0: OPTIMAL, 1: HEAT_STRESS_DRY, 2: DISEASE_MOLD_RISK
extern float glob_ai_confidence;
extern uint32_t glob_inference_time_us;

// Actuator states
extern bool glob_fan_state;
extern bool glob_pump_state;
extern bool glob_light_state;

// Active Crop Profile
extern CropType glob_active_crop;

// Function helpers
float calculate_vpd(float temp, float humi);

#endif // __GLOBAL_H__
