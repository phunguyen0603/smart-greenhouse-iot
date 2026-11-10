"""
Training script for TinyML Smart Greenhouse Microclimate Classifier
Inputs: [temp, humidity, delta_temp, delta_humidity] (4 features)
Outputs: 3 classes
- 0: OPTIMAL
- 1: HEAT_STRESS_DRY
- 2: DISEASE_MOLD_RISK

Generates:
1. greenhouse_model.h5
2. greenhouse_model.tflite (quantized / optimized)
3. model.h (C array for ESP32-S3 firmware)
4. training_metrics.json (for Report Chapter 4)
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf

def train_and_export():
    dataset_path = "d:/BK/HK261/IoT/Assignment/ai_training/greenhouse_sensor_data.csv"
    if not os.path.exists(dataset_path):
        import dataset_generator
        dataset_generator.generate_dataset(dataset_path, 3000)

    print("Loading dataset from:", dataset_path)
    df = pd.read_csv(dataset_path)

    # Features and Labels
    feature_cols = ["temp", "humidity", "delta_temp", "delta_humidity"]
    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values.astype(np.int32)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")

    # Model Architecture: MLP (Multi-Layer Perceptron)
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

    # Train model
    history = model.fit(
        X_train, y_train,
        epochs=60,
        batch_size=32,
        validation_data=(X_test, y_test),
        verbose=1
    )

    # Evaluate on Test Set
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n[Test Set Results] Loss: {loss:.4f} | Accuracy: {accuracy * 100:.2f}%")

    y_pred_probs = model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)

    cls_report = classification_report(y_test, y_pred, target_names=["OPTIMAL", "HEAT_STRESS_DRY", "DISEASE_MOLD_RISK"], output_dict=True)
    conf_mat = confusion_matrix(y_test, y_pred).tolist()

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["OPTIMAL", "HEAT_STRESS_DRY", "DISEASE_MOLD_RISK"]))

    # Save Keras Model
    h5_path = "d:/BK/HK261/IoT/Assignment/ai_training/greenhouse_model.h5"
    model.save(h5_path)
    print(f"Saved Keras model to: {h5_path}")

    # Convert to TFLite (Optimized for Microcontrollers)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path = "d:/BK/HK261/IoT/Assignment/ai_training/greenhouse_model.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"Saved TFLite model to: {tflite_path} (Size: {len(tflite_model)} bytes)")

    # Export to C Header Array (model.h)
    hex_lines = [
        ', '.join([f'0x{byte:02x}' for byte in tflite_model[i:i + 12]])
        for i in range(0, len(tflite_model), 12)
    ]
    hex_array = ',\n  '.join(hex_lines)

    c_header_content = f"""// Auto-generated TinyML model header for ESP32-S3 YoloUNO
// Model: Smart Greenhouse Climate State Classifier
// Size: {len(tflite_model)} bytes

#ifndef __GREENHOUSE_MODEL_H__
#define __GREENHOUSE_MODEL_H__

const unsigned int g_model_len = {len(tflite_model)};
alignas(16) const unsigned char g_model_data[] = {{
  {hex_array}
}};

#endif // __GREENHOUSE_MODEL_H__
"""

    header_destinations = [
        "d:/BK/HK261/IoT/Assignment/ai_training/model.h",
        "d:/BK/HK261/IoT/Assignment/firmware/yolo_uno_greenhouse/include/model.h"
    ]
    for dest in header_destinations:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(c_header_content)
        print(f"Exported C header to: {dest}")

    # Save metrics for Report
    metrics_path = "d:/BK/HK261/IoT/Assignment/ai_training/training_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_accuracy": accuracy,
            "test_loss": loss,
            "model_size_bytes": len(tflite_model),
            "confusion_matrix": conf_mat,
            "classification_report": cls_report
        }, f, indent=2)
    print(f"Saved training metrics to: {metrics_path}")

if __name__ == "__main__":
    train_and_export()
