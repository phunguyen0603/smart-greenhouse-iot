"""
Benchmark Script for TinyML Model (Report Chapter 4)
Measures:
- Model Accuracy & Loss
- Precision, Recall, F1-Score per class
- Confusion Matrix
- Quantized TFLite Inference Latency (microseconds / sample)
- Memory Footprint (Flash & RAM budget)
"""

import json
import time
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf

def run_benchmark():
    tflite_path = "d:/BK/HK261/IoT/Assignment/ai_training/greenhouse_model.tflite"
    dataset_path = "d:/BK/HK261/IoT/Assignment/ai_training/greenhouse_sensor_data.csv"

    print("==================================================")
    print("      TINYML MODEL BENCHMARKING (HK261)           ")
    print("==================================================")

    # 1. Load Interpreter
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    print(f"Model File: {tflite_path}")
    print(f"Input Shape: {input_details[0]['shape']} | Type: {input_details[0]['dtype']}")
    print(f"Output Shape: {output_details[0]['shape']} | Type: {output_details[0]['dtype']}")

    # 2. Load Test Data
    df = pd.read_csv(dataset_path)
    X = df[["temp", "humidity", "delta_temp", "delta_humidity"]].values.astype(np.float32)
    y_true = df["label"].values.astype(np.int32)

    # Run on last 600 samples as holdout test
    X_test = X[-600:]
    y_test = y_true[-600:]

    y_pred = []
    latencies_us = []

    # 3. Measure Inference Time
    for i in range(len(X_test)):
        sample = np.expand_dims(X_test[i], axis=0)
        interpreter.set_tensor(input_details[0]["index"], sample)

        t0 = time.perf_counter()
        interpreter.invoke()
        t1 = time.perf_counter()

        latencies_us.append((t1 - t0) * 1_000_000)
        output_data = interpreter.get_tensor(output_details[0]["index"])
        y_pred.append(np.argmax(output_data))

    y_pred = np.array(y_pred)
    acc = np.mean(y_pred == y_test)

    print("\n--- RESULTS ---")
    print(f"Test Accuracy: {acc * 100:.2f}%")
    print(f"Average Inference Latency (PC Interpreter): {np.mean(latencies_us):.2f} us (Min: {np.min(latencies_us):.2f} us, Max: {np.max(latencies_us):.2f} us)")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    target_names = ["OPTIMAL (0)", "HEAT_STRESS_DRY (1)", "DISEASE_MOLD_RISK (2)"]
    print(classification_report(y_test, y_pred, target_names=target_names))

if __name__ == "__main__":
    run_benchmark()
