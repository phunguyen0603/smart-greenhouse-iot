"""
Benchmark Script for TinyML Model (Report Chapter 4)
Measures:
- Model Accuracy & Loss
- Precision, Recall, F1-Score per class
- Confusion Matrix
- Quantized TFLite Inference Latency (microseconds / sample)
- Memory Footprint
"""

import os
import json
import time
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf

def run_benchmark():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    tflite_path = os.path.join(project_root, "ai_training", "greenhouse_model.tflite")
    dataset_path = os.path.join(project_root, "ai_training", "greenhouse_sensor_data.csv")
    metrics_path = os.path.join(project_root, "ai_training", "training_metrics.json")

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

    # 2. Load Scaler Parameters if available
    scaler_means = [0.0, 0.0, 0.0, 0.0]
    scaler_stds = [1.0, 1.0, 1.0, 1.0]
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            scaler_means = meta.get("scaler_means", scaler_means)
            scaler_stds = meta.get("scaler_stds", scaler_stds)

    print(f"Using Scaler Means: {[round(m, 4) for m in scaler_means]}")
    print(f"Using Scaler Stds:  {[round(s, 4) for s in scaler_stds]}")

    # 3. Load Test Data
    df = pd.read_csv(dataset_path)
    X = df[["temp", "humidity", "delta_temp", "delta_humidity"]].values.astype(np.float32)
    y_true = df["label"].values.astype(np.int32)

    # Run on last 600 samples as holdout test
    X_test_raw = X[-600:]
    y_test = y_true[-600:]

    # Apply standardization
    means_arr = np.array(scaler_means, dtype=np.float32)
    stds_arr = np.array(scaler_stds, dtype=np.float32)
    X_test_scaled = (X_test_raw - means_arr) / stds_arr

    y_pred = []
    latencies_us = []

    # 4. Measure Inference Time
    for i in range(len(X_test_scaled)):
        sample = np.expand_dims(X_test_scaled[i], axis=0)
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
