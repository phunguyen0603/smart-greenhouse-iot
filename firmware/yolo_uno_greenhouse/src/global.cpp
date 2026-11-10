#include "global.h"
#include <math.h>

// Shared telemetry
float glob_temperature = 25.0f;
float glob_humidity = 75.0f;
float glob_delta_temp = 0.0f;
float glob_delta_humi = 0.0f;
float glob_vpd = 0.85f;

// TinyML inference results
int glob_ai_state = 0;           // 0: OPTIMAL, 1: HEAT_STRESS_DRY, 2: DISEASE_MOLD_RISK
float glob_ai_confidence = 1.0f;
uint32_t glob_inference_time_us = 0;

// Actuator states
bool glob_fan_state = false;
bool glob_pump_state = false;
bool glob_light_state = true;

// Active Crop Profile
CropType glob_active_crop = CROP_GENERAL_GREENHOUSE;

// Calculate VPD (kPa)
float calculate_vpd(float temp, float humi) {
    if (humi < 0.0f) humi = 0.0f;
    if (humi > 100.0f) humi = 100.0f;
    float vp_sat = 0.61078f * exp((17.27f * temp) / (temp + 237.3f));
    float vpd = vp_sat * (1.0f - (humi / 100.0f));
    return (vpd < 0.0f) ? 0.0f : vpd;
}
