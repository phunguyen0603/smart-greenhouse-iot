"""
Agricultural LLM Assistant (N01)
Integrates Google Gemini API to analyze real-time microclimate data and provide agronomic advice.
Features:
- Multi-crop profile support (Strawberry, Orchid, Mushroom, Cantaloupe, General)
- Deep physiological diagnosis based on VPD and Edge TinyML classification
- Resilient Gemini API client: google-genai -> google-generativeai -> Direct REST API
- Intelligent Offline Expert Heuristic System when offline or API key is absent
- Interactive QA support for farmer questions
- Actuator action recommendation (Fan, Pump, Grow Light)
"""

import os
import json
import math
import time

CROP_PROFILES = {
    "Strawberry (Dâu tây)": {
        "temp_opt": (18.0, 25.0),
        "humi_opt": (65.0, 80.0),
        "vpd_opt": (0.7, 1.1),
        "description": "Cây dâu tây ưa khí hậu ôn hòa mát mẻ. Rất nhạy cảm với nấm phấn trắng khi ẩm >85% và dễ rụng hoa/cháy rìa lá khi VPD > 1.4 kPa."
    },
    "Orchid (Hoa Lan)": {
        "temp_opt": (20.0, 28.0),
        "humi_opt": (60.0, 80.0),
        "vpd_opt": (0.8, 1.2),
        "description": "Hoa lan cần môi trường thông thoáng, đối lưu không khí liên tục. Tuyệt đối tránh đọng sương/giọt nước trên đọt non gây thối nhũn ngọn."
    },
    "Mushroom (Nhà Nấm)": {
        "temp_opt": (22.0, 26.0),
        "humi_opt": (85.0, 95.0),
        "vpd_opt": (0.3, 0.5),
        "description": "Nhà nấm đòi hỏi độ ẩm bão hòa cao để phát triển tai nấm. Cần thông khí nhẹ để đối lưu thải CO2 nhưng tránh quạt gió mạnh làm khô tơ nấm."
    },
    "Cantaloupe (Dưa lưới)": {
        "temp_opt": (25.0, 32.0),
        "humi_opt": (55.0, 70.0),
        "vpd_opt": (1.0, 1.4),
        "description": "Dưa lưới là cây nhiệt đới ưa nhiệt, nắng mạnh. Giai đoạn tạo lưới và chín cần kiểm soát độ ẩm chặt chẽ để tránh nứt vỏ quả và đọng sương rỉ sắt."
    },
    "General Greenhouse": {
        "temp_opt": (22.0, 28.0),
        "humi_opt": (65.0, 80.0),
        "vpd_opt": (0.8, 1.2),
        "description": "Mô hình tiêu chuẩn duy trì cân bằng thoát hơi nước qua khí khổng và vận chuyển dòng nhựa luyện."
    }
}

SYSTEM_PROMPT = """
Bạn là một Chuyên Gia Nông Nghiệp Công Nghệ Cao (Agronomist & Smart Greenhouse Specialist).
Nhiệm vụ của bạn là phân tích dữ liệu cảm biến thời gian thực, kết quả suy luận từ TinyML (Edge AI) và đưa ra:
1. Đánh giá sinh lý cây trồng: trạng thái mở/đóng khí khổng, khả năng thoát hơi nước, dòng chảy dinh dưỡng Ca2+/K+ từ rễ lên ngọn.
2. Nhận định rủi ro: nguy cơ sốc nhiệt/cháy chóp lá (khi VPD cao), hoặc nguy cơ đọng sương bùng phát nấm bệnh botrytis/phấn trắng (khi VPD thấp, ẩm bão hòa).
3. Đề xuất hành động điều khiển cụ thể: Quạt thông gió (Bật/Tắt, thời gian), Máy bơm/Phun sương (Bật/Tắt, chu kỳ), Đèn quang hợp.
4. Trả lời thỏa đáng và chuyên sâu câu hỏi cụ thể của người quản lý trang trại nếu có.
Phong cách trả lời: Khoa học, súc tích, chuyên nghiệp, dùng định dạng Markdown rõ ràng có biểu tượng trực quan.
"""

class AnalysisResult(str):
    def __new__(cls, content, fan=None, pump=None, light=None, is_offline=False, model="gemini"):
        obj = str.__new__(cls, content)
        obj.fan = fan
        obj.pump = pump
        obj.light = light
        obj.is_offline = is_offline
        obj.model = model
        return obj

def get_crop_profile(crop_name):
    for key, val in CROP_PROFILES.items():
        if key.lower() in crop_name.lower() or crop_name.lower() in key.lower():
            return key, val
    return "General Greenhouse", CROP_PROFILES["General Greenhouse"]

def generate_offline_analysis(temp, humi, vpd, ai_state_str, crop_name="General", trend_info=None, user_question=None):
    """
    Intelligent Offline Expert Heuristic System.
    Provides agronomic diagnosis when offline or when API key is not configured.
    """
    c_name, c_prof = get_crop_profile(crop_name)
    vpd_min, vpd_max = c_prof["vpd_opt"]
    t_min, t_max = c_prof["temp_opt"]

    rec_fan = False
    rec_pump = False
    rec_light = True

    sections = []
    sections.append(f"### 🌿 Báo Cáo Chẩn Đoán Nông Học (Chế độ Chuyên Gia Cục Bộ)")
    sections.append(f"**Đối tượng cây trồng:** `{c_name}` | **Đặc tính:** *{c_prof['description']}*\n")

    # 1. Physiological Assessment
    if vpd < vpd_min:
        rec_fan = True
        rec_pump = False
        state_title = "⚠️ CẢNH BÁO: ĐỘ HỤT ÁP SUẤT HƠI (VPD) QUÁ THẤP – NGUY CƠ NẤM BỆNH"
        body = (
            f"- **Chỉ số:** VPD = `{vpd:.2f} kPa` (Ngưỡng chuẩn `{vpd_min} – {vpd_max} kPa`), Độ ẩm không khí cao `{humi:.1f}%`.\n"
            f"- **Sinh lý học cây:** Không khí bão hòa hơi nước khiến áp suất chênh lệch không đủ để kích thích thoát hơi nước qua khí khổng. "
            f"Dòng dịch mao mạch từ rễ bị ngưng trệ, cây thiếu hụt các khoáng chất vận chuyển thụ động như Canxi (dễ gây thối đọt).\n"
            f"- **Nguy cơ bệnh:** Mặt lá dễ đọng giọt sương vi thể, tạo môi trường ủ mầm cho nấm phấn trắng và nấm *Botrytis cinerea* bùng phát."
        )
    elif vpd > vpd_max:
        rec_fan = True
        rec_pump = True
        state_title = "⚠️ CẢNH BÁO: VPD QUÁ CAO – NGUY CƠ SỐC NHIỆT & CHÁY LÁ"
        body = (
            f"- **Chỉ số:** VPD = `{vpd:.2f} kPa` (Vượt mức trần `{vpd_max} kPa`), Nhiệt độ cao `{temp:.1f}°C`.\n"
            f"- **Sinh lý học cây:** Áp suất bốc hơi quá lớn buộc khí khổng đóng chặt để chống mất nước (phản ứng ABA sinh học). "
            f"Quá trình quang hợp bị gián đoạn, nhiệt độ nội tại lá tăng vọt dẫn đến nguy cơ cháy chóp lá và thui hoa.\n"
            f"- **Nguy cơ:** Sốc nhiệt cục bộ, khô héo tế bào biểu bì, rụng quả non."
        )
    else:
        rec_fan = False
        rec_pump = False
        state_title = "✅ TRẠNG THÁI VI KHÍ HẬU TỐI ƯU (VÙNG CHỈ SỐ VÀNG)"
        body = (
            f"- **Chỉ số:** Nhiệt độ `{temp:.1f}°C`, Độ ẩm `{humi:.1f}%`, VPD = `{vpd:.2f} kPa` nằm hoàn toàn trong vùng vàng sinh học `{vpd_min} – {vpd_max} kPa`.\n"
            f"- **Sinh lý học cây:** Chênh lệch áp suất hơi nước lý tưởng giúp khí khổng mở tối đa, quá trình quang hợp diễn ra mạnh mẽ và rễ hấp thu khoáng chất cân bằng.\n"
            f"- **Đánh giá Edge AI (TinyML):** Node biên ESP32-S3 chẩn đoán trạng thái: `{ai_state_str}`."
        )

    sections.append(f"#### 1. Đánh giá sinh lý cây trồng\n{state_title}\n{body}\n")

    # 2. Trend & Predictive Section
    if trend_info:
        p_temp = trend_info.get("pred_temp_60m", temp)
        p_vpd = trend_info.get("pred_vpd_60m", vpd)
        shock = trend_info.get("thermal_shock_risk", False)
        dew = trend_info.get("dew_risk", False)
        sections.append("#### 2. Dự báo xu hướng từ Gateway AI (Tầm nhìn 60 phút)")
        sections.append(f"- Dự kiến sau 60 phút: Nhiệt độ `~{p_temp:.1f}°C`, VPD `~{p_vpd:.2f} kPa`.")
        if shock:
            sections.append("- 🚨 **Cảnh báo sớm:** Phát hiện tốc độ gia nhiệt nhanh, cần can thiệp trước 15 phút!")
            rec_fan = True
        if dew:
            sections.append("- 🚨 **Cảnh báo sớm:** Phát hiện nguy cơ đọng sương do nhiệt hạ nhanh kết hợp ẩm bão hòa!")
            rec_fan = True
        sections.append("")

    # 3. Actionable Recommendations
    sections.append("#### 3. Khuyến nghị điều khiển thiết bị")
    if rec_fan and rec_pump:
        sections.append("- **Quạt đối lưu (FAN):** 🟢 **BẬT** (30 phút) để giải nhiệt tầng mái nhà kính.")
        sections.append("- **Hệ thống tưới / Phun sương (PUMP):** 🟢 **BẬT** (5-10 phút) dạng hạt mịn để bù ẩm và hạ nhiệt độ bề mặt lá.")
    elif rec_fan:
        sections.append("- **Quạt đối lưu (FAN):** 🟢 **BẬT** liên tục để hạ ẩm và đối lưu không khí, ngăn đọng sương.")
        sections.append("- **Hệ thống tưới (PUMP):** 🔴 **TẮT** để hạn chế gia tăng độ ẩm nền đất.")
    else:
        sections.append("- **Quạt đối lưu (FAN):** 🔴 **TẮT** (Duy trì chế độ thông gió tự nhiên, tiết kiệm điện).")
        sections.append("- **Hệ thống tưới (PUMP):** 🔴 **TẮT** (Độ ẩm đất và không khí đang cân bằng).")
    sections.append(f"- **Đèn quang hợp (LIGHT):** 🟢 **BẬT** để hỗ trợ cây tiếp tục chu trình tổng hợp tinh bột.")

    # 4. Custom User Question Answer
    if user_question and user_question.strip():
        q_lower = user_question.lower()
        sections.append(f"\n#### 4. Phản hồi câu hỏi riêng: *\"{user_question.strip()}\"*")
        if "sốc nhiệt" in q_lower or "cháy lá" in q_lower:
            sections.append(f"-> **Chuyên gia giải đáp:** Hiện tại VPD đang ở mức `{vpd:.2f} kPa`. " +
                           ("Cây đang có dấu hiệu sốc nhiệt! Hãy bật phun sương làm mát ngay." if vpd > vpd_max else "Cây chưa có nguy cơ sốc nhiệt, tế bào khí khổng vẫn hoạt động an toàn."))
        elif "tưới" in q_lower or "bơm" in q_lower:
            sections.append(f"-> **Chuyên gia giải đáp:** " +
                           ("Không nên tưới thêm vào lúc này vì độ ẩm không khí đang quá cao, tưới thêm dễ gây úng rễ." if humi > 85 else f"Có thể kích hoạt tưới nhỏ giọt ngắn hạn nếu độ ẩm giá thể dưới 60%."))
        elif "quạt" in q_lower or "thông gió" in q_lower:
            sections.append(f"-> **Chuyên gia giải đáp:** " +
                           ("Nên bật quạt thông gió ngay lập tức để đẩy ẩm dư thừa ra ngoài." if (vpd < vpd_min or humi > 80) else "Chưa cần bật quạt cưỡng bức, duy trì thông gió thụ động."))
        elif "nấm" in q_lower or "bệnh" in q_lower or "mốc" in q_lower:
            sections.append(f"-> **Chuyên gia giải đáp:** Đối với `{c_name}`, nguy cơ nấm bùng phát khi độ ẩm $>85\%$ kéo dài quá 4 giờ liên tục. " +
                           ("Nguy cơ hiện tại rất cao, hãy kiểm tra mặt dưới lá và bật quạt lưu chuyển không khí!" if humi > 85 else "Hiện tại nguy cơ nấm mốc thấp, mặt lá khô ráo."))
        else:
            sections.append(f"-> **Chuyên gia giải đáp:** Với điều kiện hiện tại (T={temp:.1f}°C, RH={humi:.1f}%, VPD={vpd:.2f} kPa) cho giống cây `{c_name}`, "
                           f"bạn nên ưu tiên duy trì trạng thái vi khí hậu ổn định theo các khuyến nghị điều khiển ở mục 3.")

    sections.append("\n*(Chế độ: Offline Agronomist Expert System — Tích hợp sẵn trong IoT Gateway)*")
    result_text = "\n".join(sections)
    return AnalysisResult(result_text, fan=rec_fan, pump=rec_pump, light=rec_light, is_offline=True, model="Expert Heuristic")

def _call_gemini_rest(api_key, prompt, system_instruction):
    """
    Direct HTTP REST API call to Google Gemini endpoint.
    Eliminates dependencies on specific SDK packaging.
    """
    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=12) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        text = res_data["candidates"][0]["content"]["parts"][0]["text"]
        return text

def analyze_greenhouse_state(temp, humi, vpd, ai_state_str, crop_name="General", api_key=None,
                             trend_info=None, user_question=None):
    """
    Main entrypoint for Agronomist AI Analysis (N01).
    Attempts online Gemini generation first; falls back cleanly to the Offline Expert System.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    c_name, c_prof = get_crop_profile(crop_name)

    # If no API key is provided, use the Offline Expert System immediately
    if not api_key:
        return generate_offline_analysis(temp, humi, vpd, ai_state_str, c_name, trend_info, user_question)

    # Construct rich agronomic prompt for Gemini
    prompt_lines = [
        f"Dữ liệu thời gian thực từ trạm quan trắc nhà kính thông minh:",
        f"- Cây trồng đang canh tác: {c_name} (Đặc tính: {c_prof['description']})",
        f"- Dải sinh lý tối ưu cho {c_name}: Nhiệt độ {c_prof['temp_opt'][0]}-{c_prof['temp_opt'][1]}°C, Độ ẩm {c_prof['humi_opt'][0]}-{c_prof['humi_opt'][1]}%, VPD {c_prof['vpd_opt'][0]}-{c_prof['vpd_opt'][1]} kPa",
        f"- Nhiệt độ không khí đo thực tế: {temp:.2f} °C",
        f"- Độ ẩm tương đối đo thực tế: {humi:.2f} %",
        f"- Chỉ số độ hụt áp suất hơi VPD: {vpd:.3f} kPa",
        f"- Trạng thái chẩn đoán Edge AI (TinyML ESP32-S3): {ai_state_str}",
    ]

    if trend_info:
        prompt_lines.append(f"- Dự báo xu hướng vi khí hậu 60 phút tới (Gateway AI): Nhiệt độ {trend_info.get('pred_temp_60m', temp):.1f}°C, VPD {trend_info.get('pred_vpd_60m', vpd):.2f} kPa")
        if trend_info.get("thermal_shock_risk"):
            prompt_lines.append(f"- CẢNH BÁO SỚM: Gateway AI phát hiện tốc độ gia nhiệt nhanh (nguy cơ sốc nhiệt!).")
        if trend_info.get("dew_risk"):
            prompt_lines.append(f"- CẢNH BÁO SỚM: Gateway AI phát hiện nguy cơ đọng sương trên lá.")

    if user_question and user_question.strip():
        prompt_lines.append(f"\nCâu hỏi từ người quản lý nhà kính: \"{user_question.strip()}\"")
        prompt_lines.append(f"Vui lòng trả lời câu hỏi này một cách cụ thể dựa trên số liệu thực tế ở trên.")

    prompt_lines.append("\nHãy phân tích: 1) Sinh lý cây trồng và VPD; 2) Nhận định rủi ro; 3) Khuyến nghị hành động điều khiển cụ thể (Quạt, Bơm/Phun sương, Đèn quang hợp); 4) Trả lời câu hỏi (nếu có).")
    prompt_text = "\n".join(prompt_lines)

    # 1. Try google-genai SDK (v0.1.0+)
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        raw_text = resp.text
        rec_fan = "quạt" in raw_text.lower() and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        rec_pump = ("bơm" in raw_text.lower() or "phun sương" in raw_text.lower()) and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        return AnalysisResult(f"### 🤖 Tư Vấn Chuyên Gia Nông Học (Google Gemini AI)\n\n" + raw_text,
                              fan=rec_fan, pump=rec_pump, light=True, is_offline=False, model="gemini-2.5-flash")
    except Exception:
        pass

    # 2. Try google-generativeai SDK
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel("gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)
        resp = model.generate_content(prompt_text)
        raw_text = resp.text
        rec_fan = "quạt" in raw_text.lower() and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        rec_pump = ("bơm" in raw_text.lower() or "phun sương" in raw_text.lower()) and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        return AnalysisResult(f"### 🤖 Tư Vấn Chuyên Gia Nông Học (Google Gemini AI)\n\n" + raw_text,
                              fan=rec_fan, pump=rec_pump, light=True, is_offline=False, model="gemini-1.5-flash")
    except Exception:
        pass

    # 3. Try Direct REST API call
    try:
        raw_text = _call_gemini_rest(api_key, prompt_text, SYSTEM_PROMPT)
        rec_fan = "quạt" in raw_text.lower() and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        rec_pump = ("bơm" in raw_text.lower() or "phun sương" in raw_text.lower()) and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        return AnalysisResult(f"### 🤖 Tư Vấn Chuyên Gia Nông Học (Google Gemini AI - REST)\n\n" + raw_text,
                              fan=rec_fan, pump=rec_pump, light=True, is_offline=False, model="gemini-1.5-flash-rest")
    except Exception as e:
        # Graceful fallback to Expert Heuristic System if network or API call fails
        fb = generate_offline_analysis(temp, humi, vpd, ai_state_str, c_name, trend_info, user_question)
        err_msg = str(e)
        tip = ""
        if "403" in err_msg or "Forbidden" in err_msg:
            tip = " [Nguyên nhân: Google chặn Free Tier đối với tài khoản trường/tổ chức (Google Workspace/Cloud Org). Khắc phục: Dùng tài khoản Gmail cá nhân (@gmail.com) đăng nhập aistudio.google.com để tạo API key miễn phí 100%]."
        note = f"\n\n> *[Ghi chú hệ thống: Không thể kết nối tới Google Gemini API ({err_msg[:60]}...).{tip} Hệ thống đã tự động kích hoạt bộ phân tích chuyên gia cục bộ Offline Heuristic System].*"
        return AnalysisResult(str(fb) + note, fan=fb.fan, pump=fb.pump, light=fb.light, is_offline=True, model="Expert Heuristic (Fallback)")

if __name__ == "__main__":
    test_trend = {
        "pred_temp_60m": 34.5,
        "pred_vpd_60m": 2.2,
        "thermal_shock_risk": True,
        "dew_risk": False
    }
    print("=== TEST OFFLINE EXPERT HEURISTIC ===")
    res_offline = analyze_greenhouse_state(
        temp=27.5, humi=70.0, vpd=1.10, ai_state_str="HEAT_STRESS_DRY",
        crop_name="Strawberry (Dâu tây)",
        trend_info=test_trend,
        user_question="Nhiệt độ đang tăng nhanh thế này thì bao lâu nữa dâu tây sẽ bị sốc nhiệt?"
    )
    print(res_offline)
    print(f"\nRecommended Actuators: Fan={res_offline.fan}, Pump={res_offline.pump}, Light={res_offline.light}")
