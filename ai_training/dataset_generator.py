"""
Dataset Generator for Smart Greenhouse Microclimate Monitoring
Generates synthetic agricultural data based on thermodynamic VPD formulas:
- Temperature (T): Celsius
- Relative Humidity (RH): %
- Delta Temperature (delta_T): Rate of change (°C / 5 min)
- Delta Humidity (delta_RH): Rate of change (% / 5 min)

Classes:
- 0: OPTIMAL (Cân bằng vi khí hậu, cây quang hợp & thoát hơi nước tốt, VPD 0.8 - 1.2 kPa)
- 1: HEAT_STRESS_DRY (Nhiệt độ cao hoặc ẩm thấp, nguy cơ sốc nhiệt & héo khô lá, VPD > 1.4 kPa)
- 2: DISEASE_MOLD_RISK (Độ ẩm quá bão hòa >90% kéo dài, đọng sương, dễ phát sinh nấm bệnh/mốc, VPD < 0.5 kPa)
"""

import math
import random
import csv

def calculate_vpd(temp_c, rh_percent):
    """
    Calculate Vapor Pressure Deficit (VPD) in kPa:
    VPsat = 0.61078 * exp((17.27 * T) / (T + 237.3))
    VPD = VPsat * (1 - RH / 100)
    """
    vp_sat = 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    vpd = vp_sat * (1.0 - (rh_percent / 100.0))
    return max(0.0, vpd)

def generate_sample(target_class):
    if target_class == 0:  # OPTIMAL
        temp = random.uniform(22.0, 28.5)
        rh = random.uniform(70.0, 85.0)
        delta_t = random.uniform(-0.5, 0.5)
        delta_rh = random.uniform(-1.0, 1.0)
    elif target_class == 1:  # HEAT_STRESS_DRY
        # Hot and/or dry
        mode = random.choice(["hot_dry", "very_hot", "very_dry"])
        if mode == "hot_dry":
            temp = random.uniform(31.0, 38.0)
            rh = random.uniform(35.0, 60.0)
        elif mode == "very_hot":
            temp = random.uniform(33.0, 40.0)
            rh = random.uniform(50.0, 70.0)
        else:
            temp = random.uniform(26.0, 32.0)
            rh = random.uniform(30.0, 50.0)
        delta_t = random.uniform(0.2, 1.8)     # Rising fast
        delta_rh = random.uniform(-2.5, -0.2)  # Drying fast
    else:  # DISEASE_MOLD_RISK
        # Stagnant, high humidity, dew risk
        temp = random.uniform(18.0, 26.0)
        rh = random.uniform(91.0, 99.5)
        delta_t = random.uniform(-1.2, 0.2)
        delta_rh = random.uniform(0.1, 2.5)    # Increasing humidity / saturation

    # Add minor sensor noise
    temp += random.gauss(0, 0.2)
    rh += random.gauss(0, 0.5)
    rh = max(10.0, min(100.0, rh))

    vpd = calculate_vpd(temp, rh)
    return round(temp, 2), round(rh, 2), round(delta_t, 2), round(delta_rh, 2), round(vpd, 3), target_class

def generate_dataset(output_path, num_samples=3000):
    samples_per_class = num_samples // 3
    data = []

    for c in [0, 1, 2]:
        for _ in range(samples_per_class):
            data.append(generate_sample(c))

    # Shuffle dataset
    random.shuffle(data)

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["temp", "humidity", "delta_temp", "delta_humidity", "vpd", "label"])
        for row in data:
            writer.writerow(row)

    print(f"Generated {len(data)} samples saved to: {output_path}")

if __name__ == "__main__":
    generate_dataset("d:/BK/HK261/IoT/Assignment/ai_training/greenhouse_sensor_data.csv", 3000)
