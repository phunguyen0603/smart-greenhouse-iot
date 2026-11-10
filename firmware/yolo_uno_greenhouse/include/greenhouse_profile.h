#ifndef __GREENHOUSE_PROFILE_H__
#define __GREENHOUSE_PROFILE_H__

#include <Arduino.h>

enum CropType {
    CROP_GENERAL_GREENHOUSE = 0,
    CROP_STRAWBERRY,
    CROP_ORCHID,
    CROP_MUSHROOM,
    CROP_MELON
};

enum ClimateHealthState {
    STATE_OPTIMAL = 0,
    STATE_HEAT_STRESS_DRY = 1,
    STATE_DISEASE_MOLD_RISK = 2
};

struct CropProfile {
    const char* name;
    float temp_min;
    float temp_max;
    float humi_min;
    float humi_max;
    float vpd_min;
    float vpd_max;
};

// Default profiles for different greenhouse applications
static const CropProfile PROFILES[] = {
    {"General",     20.0f, 30.0f, 70.0f, 85.0f, 0.8f, 1.2f},
    {"Strawberry",  18.0f, 26.0f, 65.0f, 75.0f, 0.8f, 1.1f},
    {"Orchid",      22.0f, 28.0f, 70.0f, 85.0f, 0.7f, 1.0f},
    {"Mushroom",    24.0f, 28.0f, 80.0f, 92.0f, 0.3f, 0.6f},
    {"Melon",       24.0f, 32.0f, 60.0f, 70.0f, 0.9f, 1.3f}
};

inline const char* getStateString(ClimateHealthState state) {
    switch (state) {
        case STATE_OPTIMAL:           return "OPTIMAL";
        case STATE_HEAT_STRESS_DRY:   return "HEAT STRESS";
        case STATE_DISEASE_MOLD_RISK: return "MOLD RISK";
        default:                      return "UNKNOWN";
    }
}

#endif // __GREENHOUSE_PROFILE_H__
