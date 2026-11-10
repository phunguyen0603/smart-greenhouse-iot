"""
Gateway AI Module (T09)
Runs on PC/Gateway to perform:
1. Time-series trend analysis (Linear & Quadratic Extrapolation)
2. Predictive vi-climate projection (15m, 30m, 60m future horizon)
3. Predictive VPD forecasting
4. Thermal Shock & Dew Condensation Risk Detection
"""

import collections
import time
import math
import numpy as np

class GreenhouseGatewayAI:
    def __init__(self, window_size=60):
        self.window_size = window_size
        self.timestamps = collections.deque(maxlen=window_size)
        self.temps = collections.deque(maxlen=window_size)
        self.humis = collections.deque(maxlen=window_size)

    def calculate_vpd(self, temp, humi):
        vp_sat = 0.61078 * math.exp((17.27 * temp) / (temp + 237.3))
        vpd = vp_sat * (1.0 - (humi / 100.0))
        return max(0.0, vpd)

    def add_reading(self, temp, humi, ts=None):
        if ts is None:
            ts = time.time()
        self.timestamps.append(ts)
        self.temps.append(temp)
        self.humis.append(humi)

    def analyze(self):
        """
        Analyzes the time-series and returns predictive insights.
        """
        n = len(self.temps)
        current_temp = self.temps[-1] if n > 0 else 25.0
        current_humi = self.humis[-1] if n > 0 else 75.0
        current_vpd = self.calculate_vpd(current_temp, current_humi)

        if n < 5:
            return {
                "status": "warming_up",
                "samples": n,
                "current_temp": current_temp,
                "current_humi": current_humi,
                "current_vpd": round(current_vpd, 3),
                "predicted_temp_60m": current_temp,
                "predicted_humi_60m": current_humi,
                "predicted_vpd_60m": round(current_vpd, 3),
                "temp_rate_per_min": 0.0,
                "humi_rate_per_min": 0.0,
                "thermal_shock_risk": False,
                "dew_risk": False
            }

        # Normalize time in minutes relative to start of window
        t_arr = np.array(self.timestamps)
        t_rel = (t_arr - t_arr[0]) / 60.0  # in minutes
        temp_arr = np.array(self.temps)
        humi_arr = np.array(self.humis)

        # 1. Linear regression for rate of change (°C / min, % / min)
        t_poly = np.polyfit(t_rel, temp_arr, 1)
        h_poly = np.polyfit(t_rel, humi_arr, 1)

        temp_rate = float(t_poly[0])  # slope per minute
        humi_rate = float(h_poly[0])  # slope per minute

        # 2. Project 60 minutes ahead (clamp to physical limits)
        current_rel_t = t_rel[-1]
        t_future = current_rel_t + 60.0

        pred_temp_60m = float(np.clip(np.polyval(t_poly, t_future), 10.0, 50.0))
        pred_humi_60m = float(np.clip(np.polyval(h_poly, t_future), 15.0, 100.0))
        pred_vpd_60m = self.calculate_vpd(pred_temp_60m, pred_humi_60m)

        # 3. Anomaly & Risk Detection
        # Thermal shock: Temperature rising or falling faster than 0.5 °C/min
        thermal_shock = abs(temp_rate) > 0.4
        # Dew risk: Humidity approaching saturation with negative temp drift
        dew_risk = (current_humi > 88.0 and temp_rate < -0.1) or (pred_humi_60m > 95.0)

        return {
            "status": "ready",
            "samples": n,
            "current_temp": round(current_temp, 2),
            "current_humi": round(current_humi, 2),
            "current_vpd": round(current_vpd, 3),
            "temp_rate_per_min": round(temp_rate, 3),
            "humi_rate_per_min": round(humi_rate, 3),
            "predicted_temp_60m": round(pred_temp_60m, 2),
            "predicted_humi_60m": round(pred_humi_60m, 2),
            "predicted_vpd_60m": round(pred_vpd_60m, 3),
            "thermal_shock_risk": thermal_shock,
            "dew_risk": dew_risk
        }

if __name__ == "__main__":
    ai = GreenhouseGatewayAI()
    for i in range(15):
        ai.add_reading(26.0 + i * 0.15, 75.0 - i * 0.5, ts=time.time() - (15 - i) * 60)
    res = ai.analyze()
    print("Gateway AI Test Result:", res)
