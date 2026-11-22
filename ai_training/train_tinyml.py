"""
Training script for TinyML Smart Greenhouse Microclimate Classifier
Enhanced with StandardScaler (inherited from TinyML_ESP32 course lab)

Inputs: [temp, humidity, delta_temp, delta_humidity] (4 features)
Standardization: z = (x - mean) / std (StandardScaler)
Outputs: 3 classes
- 0: OPTIMAL
- 1: HEAT_STRESS_DRY
- 2: DISEASE_MOLD_RISK

Generates:
1. greenhouse_model.h5 (Keras Model)
2. greenhouse_model.tflite (Quantized TFLite Micro)
3. model.h (C array with embedded FEATURE_MEANS and FEATURE_STDS for ESP32-S3)
4. ESP32_Config.txt (Summary config file for developers)
5. training_metrics.json (Evaluation metrics for Report Chapter 4)
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf

def train_and_export():
    # Dynamic absolute paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    dataset_path = os.path.join(base_dir, "greenhouse_sensor_data.csv")
    h5_path = os.path.join(base_dir, "greenhouse_model.h5")
    tflite_path = os.path.join(base_dir, "greenhouse_model.tflite")
    config_txt_path = os.path.join(base_dir, "ESP32_Config.txt")
    metrics_path = os.path.join(base_dir, "training_metrics.json")
    
    header_destinations = [
        os.path.join(base_dir, "model.h"),
        os.path.join(project_root, "firmware", "yolo_uno_greenhouse", "include", "model.h")
    ]

    if not os.path.exists(dataset_path):
        import dataset_generator
        dataset_generator.generate_dataset(dataset_path, 3000)

    print("Loading dataset from:", dataset_path)
    df = pd.read_csv(dataset_path)

    feature_cols = ["temp", "humidity", "delta_temp", "delta_humidity"]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values.astype(np.int32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # 1. Feature Standardization using StandardScaler (from TinyML_ESP32 lab)
    print("Standardizing features with StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train).astype(np.float32)
    X_test_scaled = scaler.transform(X_test).astype(np.float32)

    means = [float(m) for m in scaler.mean_]
    stds = [float(s) for s in scaler.scale_]

    print("Scaler Means:", [round(m, 4) for m in means])
    print("Scaler Stds: ", [round(s, 4) for s in stds])

    # 2. Model Architecture: MLP (Multi-Layer Perceptron)
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(4,), name="sensor_input"),
        tf.keras.layers.Dense(16, activation="relu", name="dense_1"),
        tf.keras.layers.Dense(8, activation="relu", name="dense_2"),
        tf.keras.layers.Dense(3, activation="softmax", name="output_probabilities")
    ])

    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.005),
        metrics=["accuracy"]
    )

    model.summary()

    # 3. Train model
    history = model.fit(
        X_train_scaled, y_train,
        epochs=60,
        batch_size=32,
        validation_data=(X_test_scaled, y_test),
        verbose=1
    )

    # 4. Evaluate on Test Set
    loss, accuracy = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"\n[Test Set Results] Loss: {loss:.4f} | Accuracy: {accuracy * 100:.2f}%")

    y_pred_probs = model.predict(X_test_scaled)
    y_pred = np.argmax(y_pred_probs, axis=1)

    cls_report = classification_report(
        y_test, y_pred,
        target_names=["OPTIMAL", "HEAT_STRESS_DRY", "DISEASE_MOLD_RISK"],
        output_dict=True
    )
    conf_mat = confusion_matrix(y_test, y_pred).tolist()

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["OPTIMAL", "HEAT_STRESS_DRY", "DISEASE_MOLD_RISK"]))

    # 5. Save Keras Model
    model.save(h5_path)
    print(f"Saved Keras model to: {h5_path}")

    # 6. Convert to TFLite (Optimized for Microcontrollers)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"Saved TFLite model to: {tflite_path} (Size: {len(tflite_model)} bytes)")

    # 7. Export C Header Array (model.h) with embedded normalization constants
    hex_lines = [
        ', '.join([f'0x{byte:02x}' for byte in tflite_model[i:i + 12]])
        for i in range(0, len(tflite_model), 12)
    ]
    hex_array = ',\n  '.join(hex_lines)

    c_header_content = f"""// Auto-generated TinyML model header for ESP32-S3 YoloUNO
// Model: Smart Greenhouse Climate State Classifier (VPD + Trend)
// Input features: [0: temp (C), 1: humi (%), 2: delta_temp (C/5m), 3: delta_humi (%/5m)]
// Normalization: StandardScaler (z = (x - mean) / std)
// Size: {len(tflite_model)} bytes

#ifndef __GREENHOUSE_MODEL_H__
#define __GREENHOUSE_MODEL_H__

#include <Arduino.h>

// -------------------------------------------------------------
// StandardScaler Parameters (Inherited from TinyML_ESP32 lab)
// -------------------------------------------------------------
const float FEATURE_MEANS[4] = {{ {means[0]:.6f}f, {means[1]:.6f}f, {means[2]:.6f}f, {means[3]:.6f}f }};
const float FEATURE_STDS[4]  = {{ {stds[0]:.6f}f, {stds[1]:.6f}f, {stds[2]:.6f}f, {stds[3]:.6f}f }};

const int NUM_CLASSES = 3;
const char* const CLASS_NAMES[3] = {{ "OPTIMAL", "HEAT_STRESS_DRY", "DISEASE_MOLD_RISK" }};

const unsigned int g_model_len = {len(tflite_model)};
alignas(16) const unsigned char g_model_data[] = {{
  {hex_array}
}};

#endif // __GREENHOUSE_MODEL_H__
"""

    for dest in header_destinations:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(c_header_content)
        print(f"Exported C header to: {dest}")

    # 8. Export ESP32_Config.txt (following TinyML_ESP32 reference)
    with open(config_txt_path, "w", encoding="utf-8") as f:
        f.write("=== THONG SO CHUAN HOA STANDARDSCALER CHO ESP32-S3 ===\n\n")
        f.write("1. Tham so Mean va Std do StandardScaler cung cap:\n")
        f.write(f"float temp_mean = {means[0]:.4f};\n")
        f.write(f"float temp_std  = {stds[0]:.4f};\n")
        f.write(f"float humi_mean = {means[1]:.4f};\n")
        f.write(f"float humi_std  = {stds[1]:.4f};\n")
        f.write(f"float delta_temp_mean = {means[2]:.4f};\n")
        f.write(f"float delta_temp_std  = {stds[2]:.4f};\n")
        f.write(f"float delta_humi_mean = {means[3]:.4f};\n")
        f.write(f"float delta_humi_std  = {stds[3]:.4f};\n\n")
        f.write("2. Cong thuc chuan hoa truoc khi Invoke():\n")
        f.write("input->data.f[0] = (glob_temperature - temp_mean) / temp_std;\n")
        f.write("input->data.f[1] = (glob_humidity    - humi_mean) / humi_std;\n")
        f.write("input->data.f[2] = (glob_delta_temp  - delta_temp_mean) / delta_temp_std;\n")
        f.write("input->data.f[3] = (glob_delta_humi  - delta_humi_mean) / delta_humi_std;\n\n")
        f.write("3. Bang tra ma nhan:\n")
        f.write("Index 0 => OPTIMAL\n")
        f.write("Index 1 => HEAT_STRESS_DRY\n")
        f.write("Index 2 => DISEASE_MOLD_RISK\n")
    print(f"Saved developer config to: {config_txt_path}")

    # 9. Save metrics for Report Chapter 4
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_accuracy": float(accuracy),
            "test_loss": float(loss),
            "model_size_bytes": len(tflite_model),
            "scaler_means": means,
            "scaler_stds": stds,
            "confusion_matrix": conf_mat,
            "classification_report": cls_report
        }, f, indent=2)
    print(f"Saved training metrics to: {metrics_path}")

if __name__ == "__main__":
    train_and_export()
