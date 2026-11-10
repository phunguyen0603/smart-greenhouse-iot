#include "tinyml_task.h"
#include "global.h"
#include "model.h"

#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"

namespace {
    tflite::ErrorReporter *error_reporter = nullptr;
    const tflite::Model *model = nullptr;
    tflite::MicroInterpreter *interpreter = nullptr;
    TfLiteTensor *input = nullptr;
    TfLiteTensor *output = nullptr;

    constexpr int kTensorArenaSize = 10 * 1024;
    alignas(16) uint8_t tensor_arena[kTensorArenaSize];
}

void setup_tinyml() {
    Serial.println("[TinyML] Initializing TensorFlow Lite Micro...");
    static tflite::MicroErrorReporter micro_error_reporter;
    error_reporter = &micro_error_reporter;

    model = tflite::GetModel(g_model_data);
    if (model->version() != TFLITE_SCHEMA_VERSION) {
        error_reporter->Report("Model schema version mismatch: %d != %d",
                               model->version(), TFLITE_SCHEMA_VERSION);
        return;
    }

    static tflite::AllOpsResolver resolver;
    static tflite::MicroInterpreter static_interpreter(
        model, resolver, tensor_arena, kTensorArenaSize, error_reporter);
    interpreter = &static_interpreter;

    TfLiteStatus allocate_status = interpreter->AllocateTensors();
    if (allocate_status != kTfLiteOk) {
        error_reporter->Report("AllocateTensors() failed");
        return;
    }

    input = interpreter->input(0);
    output = interpreter->output(0);
    Serial.println("[TinyML] Model loaded and tensors allocated successfully.");
}

void tinyml_task(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(1500)); // Allow sensor task to collect initial data
    setup_tinyml();

    while (1) {
        if (!interpreter) {
            vTaskDelay(pdMS_TO_TICKS(5000));
            continue;
        }

        // Fill 4 input features: [temp, humidity, delta_temp, delta_humidity]
        input->data.f[0] = glob_temperature;
        input->data.f[1] = glob_humidity;
        input->data.f[2] = glob_delta_temp;
        input->data.f[3] = glob_delta_humi;

        uint32_t t_start = micros();
        TfLiteStatus invoke_status = interpreter->Invoke();
        uint32_t t_elapsed = micros() - t_start;
        glob_inference_time_us = t_elapsed;

        if (invoke_status == kTfLiteOk) {
            float p_opt  = output->data.f[0];
            float p_dry  = output->data.f[1];
            float p_mold = output->data.f[2];

            int best_class = 0;
            float max_prob = p_opt;

            if (p_dry > max_prob) {
                best_class = 1;
                max_prob = p_dry;
            }
            if (p_mold > max_prob) {
                best_class = 2;
                max_prob = p_mold;
            }

            glob_ai_state = best_class;
            glob_ai_confidence = max_prob;

            Serial.printf("[TinyML] T=%.1f H=%.1f | State: %s (Prob: %.2f) | Inference Time: %lu us\n",
                          glob_temperature, glob_humidity,
                          getStateString((ClimateHealthState)glob_ai_state),
                          glob_ai_confidence, glob_inference_time_us);
        } else {
            Serial.println("[TinyML] Inference invocation failed!");
        }

        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}
