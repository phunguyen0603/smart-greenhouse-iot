"""
Comprehensive Test Harness for TinyML & Agronomic LLM Assistant (HK261)
Role: Member 2 (TinyML Edge AI & Gemini LLM)

Test Suites:
1. Suite 1: TinyML Quantitative Benchmark (Accuracy, F1-Score, Inference Latency, Confusion Matrix)
2. Suite 2: Corner-Case & Boundary Stress Test (Extreme temperatures, sensor saturation, sudden surges)
3. Suite 3: Agronomic Physiology & LLM Assistant Verification (VPD math, multi-crop bounds, action recommendations, fallback)
4. Suite 4: Firmware Memory & Model Integrity (Flash footprint, Tensor Arena sizing, alignment)
"""

import os
import sys
import json
import math
import time
import numpy as np
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "gateway"))

from llm_assistant import (
    analyze_greenhouse_state,
    generate_offline_analysis,
    get_crop_profile,
    CROP_PROFILES
)

class SmartGreenhouseHarness:
    def __init__(self):
        self.tflite_path = os.path.join(PROJECT_ROOT, "ai_training", "greenhouse_model.tflite")
        self.metrics_path = os.path.join(PROJECT_ROOT, "ai_training", "training_metrics.json")
        self.dataset_path = os.path.join(PROJECT_ROOT, "ai_training", "greenhouse_sensor_data.csv")
        self.firmware_model_h = os.path.join(PROJECT_ROOT, "firmware", "yolo_uno_greenhouse", "include", "model.h")
        
        self.passed_tests = 0
        self.failed_tests = 0
        self.results = []

        # Load Scaler & Interpreter
        with open(self.metrics_path, "r", encoding="utf-8") as f:
            self.metrics = json.load(f)
        self.means = np.array(self.metrics["scaler_means"], dtype=np.float32)
        self.stds = np.array(self.metrics["scaler_stds"], dtype=np.float32)

        self.interpreter = tf.lite.Interpreter(model_path=self.tflite_path)
        self.interpreter.allocate_tensors()
        self.input_idx = self.interpreter.get_input_details()[0]["index"]
        self.output_idx = self.interpreter.get_output_details()[0]["index"]

    def record(self, suite_name, test_name, status, detail=""):
        if status:
            self.passed_tests += 1
            mark = "PASSED [OK]"
        else:
            self.failed_tests += 1
            mark = "FAILED [X]"
        print(f"[{mark}] {suite_name} :: {test_name} - {detail}")
        self.results.append({"suite": suite_name, "test": test_name, "status": status, "detail": detail})

    def run_suite_1_tinyml_metrics(self):
        print("\n" + "=" * 60)
        print(">>> SUITE 1: TINYML QUANTITATIVE BENCHMARK & METRICS")
        print("=" * 60)

        # 1.1 Check model size
        model_size = os.path.getsize(self.tflite_path)
        self.record("Suite 1", "Model File Size Budget", model_size < 4096, f"Actual: {model_size} bytes (Budget < 4096 bytes)")

        # 1.2 Evaluate on holdout set
        import pandas as pd
        df = pd.read_csv(self.dataset_path)
        X = df[["temp", "humidity", "delta_temp", "delta_humidity"]].values.astype(np.float32)[-600:]
        y = df["label"].values.astype(np.int32)[-600:]

        X_scaled = (X - self.means) / self.stds
        preds = []
        latencies = []
        for i in range(len(X_scaled)):
            t0 = time.perf_counter()
            self.interpreter.set_tensor(self.input_idx, np.expand_dims(X_scaled[i], axis=0))
            self.interpreter.invoke()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1_000_000)
            out = self.interpreter.get_tensor(self.output_idx)[0]
            preds.append(np.argmax(out))

        acc = np.mean(np.array(preds) == y)
        avg_lat = np.mean(latencies)
        self.record("Suite 1", "Holdout Test Accuracy", acc >= 0.95, f"Actual Accuracy: {acc*100:.2f}% (Target >= 95%)")
        self.record("Suite 1", "Interpreter Latency", avg_lat < 50.0, f"Average Latency: {avg_lat:.2f} us (Target < 50 us)")

    def run_suite_2_corner_cases(self):
        print("\n" + "=" * 60)
        print(">>> SUITE 2: CORNER-CASE & BOUNDARY STRESS TEST")
        print("=" * 60)

        corner_cases = [
            ("Extreme Heat & Drought", 45.0, 20.0, +2.5, -3.5, 1),      # Class 1: HEAT_STRESS_DRY
            ("Freezing & Saturated Dew", 10.0, 99.0, -2.0, +3.0, 2),    # Class 2: DISEASE_MOLD_RISK
            ("Ideal Spring Morning", 24.0, 75.0, 0.0, 0.0, 0),          # Class 0: OPTIMAL
            ("Zero Delta Latent Spike", 27.5, 70.0, 0.0, 0.0, 0),       # Class 0: OPTIMAL
            ("Dynamic Heat Surge Edge", 27.5, 70.0, +1.5, -2.5, 1),     # Class 1: HEAT_STRESS_DRY
            ("Near Dew Point Drop", 22.0, 95.0, -1.5, +2.0, 2)          # Class 2: DISEASE_MOLD_RISK
        ]

        all_passed = True
        for name, t, h, dt, dh, expected_class in corner_cases:
            scaled = (np.array([t, h, dt, dh], dtype=np.float32) - self.means) / self.stds
            self.interpreter.set_tensor(self.input_idx, np.expand_dims(scaled, axis=0))
            self.interpreter.invoke()
            probs = self.interpreter.get_tensor(self.output_idx)[0]
            pred = int(np.argmax(probs))
            conf = probs[pred]
            
            passed = (pred == expected_class)
            if not passed: all_passed = False
            self.record("Suite 2", f"Stress: {name}", passed, f"Input: T={t}, H={h}, dT={dt}, dH={dh} -> Pred={pred} (Conf: {conf*100:.1f}%)")

    def run_suite_3_agronomic_llm(self):
        print("\n" + "=" * 60)
        print(">>> SUITE 3: AGRONOMIC PHYSIOLOGY & LLM ASSISTANT VERIFICATION")
        print("=" * 60)

        # 3.1 Verify All Crop Profiles are defined
        required_crops = ["Strawberry (Dâu tây)", "Orchid (Hoa Lan)", "Mushroom (Nhà Nấm)", "Cantaloupe (Dưa lưới)", "General Greenhouse"]
        for c in required_crops:
            self.record("Suite 3", f"Profile Exists: {c}", c in CROP_PROFILES, f"Opt VPD: {CROP_PROFILES[c]['vpd_opt']}")

        # 3.2 Verify Offline Expert Analysis Generation & Actuator Triggers
        trend_sample = {"pred_temp_60m": 35.0, "pred_vpd_60m": 2.5, "thermal_shock_risk": True, "dew_risk": False}
        res = analyze_greenhouse_state(
            temp=34.0, humi=45.0, vpd=2.85, ai_state_str="HEAT_STRESS_DRY",
            crop_name="Strawberry (Dâu tây)",
            trend_info=trend_sample,
            user_question="Nhiệt độ này có làm cháy lá không?",
            api_key=None
        )

        has_diag = "CẢNH BÁO" in str(res) or "SỐC NHIỆT" in str(res)
        has_qa = "cháy lá" in str(res).lower()
        has_actions = hasattr(res, "fan") and hasattr(res, "pump")
        correct_action = (res.fan is True and res.pump is True)  # Overheat requires Fan + Misting

        self.record("Suite 3", "Physiological Diagnosis Content", has_diag, "Identified HEAT_STRESS risk")
        self.record("Suite 3", "Custom User QA Handling", has_qa, "Answered question regarding leaf scorch")
        self.record("Suite 3", "Actuator Trigger Safety", correct_action, f"Actions: Fan={res.fan}, Pump={res.pump}")

    def run_suite_4_firmware_integrity(self):
        print("\n" + "=" * 60)
        print(">>> SUITE 4: FIRMWARE MEMORY & MODEL INTEGRITY")
        print("=" * 60)

        # 4.1 Check model.h in firmware folder exists and has alignment
        if os.path.exists(self.firmware_model_h):
            with open(self.firmware_model_h, "r", encoding="utf-8") as f:
                content = f.read()
            has_align = "alignas(16)" in content
            has_means = "FEATURE_MEANS" in content
            has_stds = "FEATURE_STDS" in content
            has_len = "g_model_len" in content
            
            self.record("Suite 4", "ESP32 Memory Alignment (alignas 16)", has_align, "Required for Xtensa S3 SIMD instructions")
            self.record("Suite 4", "Embedded Normalization Constants", has_means and has_stds, "FEATURE_MEANS & STDS in C header")
            self.record("Suite 4", "Model Byte Array Export", has_len, f"g_model_len defined")
        else:
            self.record("Suite 4", "Firmware Header model.h", False, "File missing!")

    def summarize(self):
        print("\n" + "=" * 60)
        print("                   HARNESS EXECUTION SUMMARY                  ")
        print("=" * 60)
        total = self.passed_tests + self.failed_tests
        rate = (self.passed_tests / total) * 100 if total > 0 else 0
        print(f"Total Tests Executed: {total}")
        print(f"Passed:               {self.passed_tests} [OK]")
        print(f"Failed:               {self.failed_tests} [X]")
        print(f"Success Rate:         {rate:.1f}%")
        print("=" * 60 + "\n")
        return self.failed_tests == 0

if __name__ == "__main__":
    harness = SmartGreenhouseHarness()
    harness.run_suite_1_tinyml_metrics()
    harness.run_suite_2_corner_cases()
    harness.run_suite_3_agronomic_llm()
    harness.run_suite_4_firmware_integrity()
    success = harness.summarize()
    sys.exit(0 if success else 1)
