#include "sensor_lcd_task.h"
#include <Wire.h>
#include <Adafruit_NeoPixel.h>
#include "DHT20.h"
#include "LiquidCrystal_I2C.h"
#include "global.h"

static DHT20 dht20(&Wire);
static LiquidCrystal_I2C lcd(LCD_I2C_ADDR, 16, 2);
static Adafruit_NeoPixel pixel(LED_COUNT, NEO_PIN, NEO_GRB + NEO_KHZ800);

#define FILTER_WINDOW 5
#define EMA_ALPHA     0.25f

static float get_median(float arr[], int n) {
    float sorted[FILTER_WINDOW];
    for (int i = 0; i < n; i++) sorted[i] = arr[i];

    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (sorted[j] > sorted[j + 1]) {
                float tmp = sorted[j];
                sorted[j] = sorted[j + 1];
                sorted[j + 1] = tmp;
            }
        }
    }
    return sorted[n / 2];
}

void setup_sensor_lcd() {
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(100000);
    Wire.setTimeOut(3000);

    pixel.begin();
    pixel.setBrightness(40);
    pixel.setPixelColor(0, pixel.Color(0, 0, 50)); // Blue while booting
    pixel.show();

    lcd.begin();
    lcd.backlight();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Smart Greenhouse");
    lcd.setCursor(0, 1);
    lcd.print("Init Sensors...");

    dht20.begin();
    vTaskDelay(pdMS_TO_TICKS(1000));
}

void sensor_lcd_task(void *pvParameters) {
    setup_sensor_lcd();

    float temp_raw_buf[FILTER_WINDOW];
    float humi_raw_buf[FILTER_WINDOW];

    static float ema_temp = -1.0f;
    static float ema_humi = -1.0f;
    static float prev_temp = 25.0f;
    static float prev_humi = 75.0f;

    while (1) {
        // 1. Gather 5 samples with 100ms interval for Median Filter
        for (int i = 0; i < FILTER_WINDOW; i++) {
            dht20.read();
            float t = dht20.getTemperature();
            float h = dht20.getHumidity();

            if (!isnan(t) && !isnan(h) && t > -20.0f && t < 80.0f) {
                temp_raw_buf[i] = t;
                humi_raw_buf[i] = h;
            } else {
                temp_raw_buf[i] = (ema_temp > 0) ? ema_temp : 25.0f;
                humi_raw_buf[i] = (ema_humi > 0) ? ema_humi : 75.0f;
            }
            vTaskDelay(pdMS_TO_TICKS(100));
        }

        // 2. Stage 1: Median filter to eliminate impulse spikes
        float med_t = get_median(temp_raw_buf, FILTER_WINDOW);
        float med_h = get_median(humi_raw_buf, FILTER_WINDOW);

        // 3. Stage 2: Exponential Moving Average (EMA) to smooth trends
        if (ema_temp < 0.0f) {
            ema_temp = med_t;
            ema_humi = med_h;
        } else {
            ema_temp = EMA_ALPHA * med_t + (1.0f - EMA_ALPHA) * ema_temp;
            ema_humi = EMA_ALPHA * med_h + (1.0f - EMA_ALPHA) * ema_humi;
        }

        // Update rate of change
        glob_delta_temp = ema_temp - prev_temp;
        glob_delta_humi = ema_humi - prev_humi;
        prev_temp = ema_temp;
        prev_humi = ema_humi;

        glob_temperature = ema_temp;
        glob_humidity = ema_humi;
        glob_vpd = calculate_vpd(glob_temperature, glob_humidity);

        // 4. Update NeoPixel Color based on TinyML classification
        if (glob_ai_state == STATE_OPTIMAL) {
            pixel.setPixelColor(0, pixel.Color(0, 50, 0));      // Green
        } else if (glob_ai_state == STATE_HEAT_STRESS_DRY) {
            pixel.setPixelColor(0, pixel.Color(60, 20, 0));     // Orange / Warning
        } else {
            pixel.setPixelColor(0, pixel.Color(50, 0, 50));     // Magenta / Purple (Mold risk)
        }
        pixel.show();

        // 5. Update LCD 16x2 Display
        lcd.setCursor(0, 0);
        char row0[17];
        snprintf(row0, sizeof(row0), "T:%.1fC  H:%.1f%%  ", glob_temperature, glob_humidity);
        lcd.print(row0);

        lcd.setCursor(0, 1);
        char row1[17];
        const char* tag = "OPT";
        if (glob_ai_state == STATE_HEAT_STRESS_DRY) tag = "DRY";
        else if (glob_ai_state == STATE_DISEASE_MOLD_RISK) tag = "MLD";

        snprintf(row1, sizeof(row1), "VPD:%.2f AI:%s  ", glob_vpd, tag);
        lcd.print(row1);

        vTaskDelay(pdMS_TO_TICKS(2000));
    }
}
