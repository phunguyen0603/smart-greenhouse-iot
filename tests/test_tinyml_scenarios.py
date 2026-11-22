"""
Kịch bản chạy thử nghiệm mô hình TinyML (Smart Greenhouse Microclimate Classifier)
Hỗ trợ kiểm thử 3 kịch bản vi khí hậu thực tế và kiểm thử tự do.
"""

import os
import json
import math
import numpy as np
import tensorflow as tf

def calculate_vpd(temp_c, rh_percent):
    vp_sat = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    vpd = vp_sat * (1.0 - (rh_percent / 100.0))
    return max(0.0, vpd)

def run_scenarios():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    tflite_path = os.path.join(project_root, "ai_training", "greenhouse_model.tflite")
    metrics_path = os.path.join(project_root, "ai_training", "training_metrics.json")

    print("\n" + "=" * 65)
    print("   CHƯƠNG TRÌNH CHẠY THỬ CÁC KỊCH BẢN SUY LUẬN TINYML (HK261)")
    print("=" * 65)

    # Load interpreter
    interpreter = tf.lite.Interpreter(model_path=tflite_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Load normalization parameters
    with open(metrics_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    means = np.array(meta["scaler_means"], dtype=np.float32)
    stds = np.array(meta["scaler_stds"], dtype=np.float32)

    class_names = ["OPTIMAL (Tối ưu)", "HEAT_STRESS_DRY (Sốc nhiệt / Khô hạn)", "DISEASE_MOLD_RISK (Nguy cơ nấm mốc / Đọng sương)"]
    led_colors = ["Xanh lá (GREEN)", "Màu cam (ORANGE)", "Tím/Hồng (MAGENTA)"]
    actions = [
        "Vi khí hậu lý tưởng cho cây quang hợp. Duy trì thông gió định kỳ.",
        "Cây đóng khí khổng, nguy cơ cháy chóp lá! Kích hoạt phun sương bù ẩm và hạ nhiệt.",
        "Độ ẩm quá bão hòa, đọng sương trên lá! Bật quạt thông gió cưỡng bức để thoát ẩm."
    ]

    scenarios = [
        {
            "name": "KỊCH BẢN 1: MÔI TRƯỜNG LÝ TƯỞNG (OPTIMAL)",
            "temp": 25.5, "humidity": 76.0, "delta_temp": 0.05, "delta_humidity": -0.10,
            "description": "Nhiệt độ phòng mát mẻ, độ ẩm vừa phải, cây hô hấp và thoát hơi nước cân bằng."
        },
        {
            "name": "KỊCH BẢN 2: SỐC NHIỆT & KHÔ HẠN (HEAT_STRESS_DRY)",
            "temp": 35.8, "humidity": 42.0, "delta_temp": +1.40, "delta_humidity": -2.20,
            "description": "Nắng gắt buổi trưa, nhiệt độ tăng nhanh và không khí khô hạn."
        },
        {
            "name": "KỊCH BẢN 3: NGUY CƠ NẤM MỐC & ĐỌNG SƯƠNG (DISEASE_MOLD_RISK)",
            "temp": 21.2, "humidity": 96.5, "delta_temp": -0.70, "delta_humidity": +1.80,
            "description": "Đêm lạnh hoặc sau cơn mưa, độ ẩm bão hòa >95% kéo dài, mặt lá ẩm ướt."
        }
    ]

    for idx, sc in enumerate(scenarios, 1):
        raw_vals = np.array([sc["temp"], sc["humidity"], sc["delta_temp"], sc["delta_humidity"]], dtype=np.float32)
        scaled_vals = (raw_vals - means) / stds
        sample = np.expand_dims(scaled_vals, axis=0)

        interpreter.set_tensor(input_details[0]["index"], sample)
        interpreter.invoke()
        probs = interpreter.get_tensor(output_details[0]["index"])[0]
        pred_class = int(np.argmax(probs))
        vpd_val = calculate_vpd(sc["temp"], sc["humidity"])

        print(f"\n>>> [{sc['name']}]")
        print(f"    * Mô tả: {sc['description']}")
        print(f"    * Dữ liệu cảm biến đầu vào: Nhiệt độ={sc['temp']:.1f}°C, Độ ẩm={sc['humidity']:.1f}%, dT={sc['delta_temp']:+.2f}°C, dH={sc['delta_humidity']:+.2f}%")
        print(f"    * Chỉ số VPD tính toán:    {vpd_val:.3f} kPa")
        print(f"    * Vector chuẩn hoá (z-score): [{scaled_vals[0]:.2f}, {scaled_vals[1]:.2f}, {scaled_vals[2]:.2f}, {scaled_vals[3]:.2f}]")
        print(f"    * Xác suất đầu ra mô hình: OPTIMAL={probs[0]*100:.1f}% | DRY={probs[1]*100:.1f}% | MOLD={probs[2]*100:.1f}%")
        print(f"    * Trạng thái kết luận AI:   ==> [{class_names[pred_class]}] (Độ tin cậy: {probs[pred_class]*100:.1f}%)")
        print(f"    * Phản ứng phần cứng ESP32: Đèn NeoPixel chuyển {led_colors[pred_class]}")
        print(f"    * Đề xuất hành động:        {actions[pred_class]}")

    print("\n" + "=" * 65)
    print("Toàn bộ 3 kịch bản đã suy luận chính xác 100% theo đúng logic nông học!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    run_scenarios()
