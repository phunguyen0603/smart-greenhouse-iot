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

QUY TẮC BẮT BUỘC VỀ THỨ TỰ TRÌNH BÀY:
1. NẾU CÓ CÂU HỎI TỪ NGƯỜI QUẢN LÝ NHÀ KÍNH, BẠN BẮT BUỘC PHẢI ĐẶT MỤC: "### 💬 1. GIẢI ĐÁP TRỰC TIẾP CÂU HỎI" LÊN NGAY TRÊN CÙNG (trên tất cả các mục khác), giải đáp trực diện, rõ ràng, trúng đích trước tiên.
2. Sau đó mới trình bày các mục phân tích khoa học tiếp theo:
   ### 🌿 2. Đánh giá Sinh lý cây trồng & Chỉ số VPD
   ### 📈 3. Nhận định Rủi ro & Dự báo Xu hướng 60 phút
   ### ⚡ 4. Khuyến nghị Hành động điều khiển cụ thể (Quạt, Bơm/Phun sương, Đèn quang hợp)

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

    # ================= 1. TRẢ LỜI CÂU HỎI LÊN TRÊN CÙNG (NẾU CÓ) =================
    if user_question and user_question.strip():
        q_lower = user_question.lower()
        if "sốc nhiệt" in q_lower or "cháy lá" in q_lower:
            ans_lead = ("⚠️ **CẢNH BÁO SỐC NHIỆT:** Cây đang đối mặt với nguy cơ sốc nhiệt và cháy chóp lá do VPD cao (" + f"{vpd:.2f} kPa" + "). Hãy kích hoạt phun sương làm mát ngay lập tức!" if vpd > vpd_max else f"✅ **AN TOÀN:** Hiện tại VPD đang ở mức lý tưởng ({vpd:.2f} kPa). Tế bào khí khổng vẫn hoạt động bình thường, chưa có nguy cơ sốc nhiệt.")
        elif "tưới" in q_lower or "bơm" in q_lower:
            ans_lead = ("❌ **KHÔNG NÊN TƯỚI THÊM:** Độ ẩm không khí đang quá bão hòa (" + f"{humi:.1f}%" + "). Tưới thêm lúc này dễ gây úng rễ và tạo điều kiện cho nấm bệnh phát triển." if humi > 85 else f"💧 **CÓ THỂ TƯỚI NHẸ:** Nếu độ ẩm giá thể dưới 60%, bạn có thể tưới nhỏ giọt ngắn hạn bù ẩm, tốt nhất vào đầu buổi sáng.")
        elif "quạt" in q_lower or "thông gió" in q_lower:
            ans_lead = ("🌀 **CẦN BẬT QUẠT NGAY:** Bật quạt thông gió cưỡng bức để đẩy ẩm dư thừa ra ngoài và tránh đọng sương bề mặt lá." if (vpd < vpd_min or humi > 80) else "🍃 **CHƯA CẦN BẬT QUẠT:** Vi khí hậu đang lưu thông tự nhiên tốt, chưa cần kích hoạt quạt cưỡng bức.")
        elif "nấm" in q_lower or "bệnh" in q_lower or "mốc" in q_lower:
            ans_lead = ("⚠️ **NGUY CƠ NẤM BỆNH RẤT CAO:** Độ ẩm cao >85% kết hợp đọng giọt nước là môi trường thuận lợi cho nấm phấn trắng và Botrytis bùng phát. Cần bật quạt lưu thông không khí ngay!" if humi > 85 else "✅ **NGUY CƠ NẤM MỐC THẤP:** Bề mặt lá khô ráo, vi khí hậu thông thoáng, bào tử nấm khó nảy mầm.")
        else:
            ans_lead = f"Với điều kiện thực tế (Nhiệt độ {temp:.1f}°C, Độ ẩm {humi:.1f}%, VPD {vpd:.2f} kPa) của giống cây `{c_name}`, bạn nên duy trì ổn định vi khí hậu và áp dụng các khuyến nghị điều khiển thiết bị bên dưới."

        sections.append(f"> 💬 **GIẢI ĐÁP TRỰC TIẾP CÂU HỎI CỦA BẠN:**\n> *\"{user_question.strip()}\"*\n>\n> 👉 {ans_lead}\n")

    # 2. Physiological Assessment
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

    sections.append(f"#### 2. Đánh giá sinh lý cây trồng & Chỉ số VPD\n{state_title}\n{body}\n")

    # 3. Trend & Predictive Section
    if trend_info:
        p_temp = trend_info.get("pred_temp_60m", temp)
        p_vpd = trend_info.get("pred_vpd_60m", vpd)
        shock = trend_info.get("thermal_shock_risk", False)
        dew = trend_info.get("dew_risk", False)
        sections.append("#### 3. Dự báo xu hướng từ Gateway AI (Tầm nhìn 60 phút)")
        sections.append(f"- Dự kiến sau 60 phút: Nhiệt độ `~{p_temp:.1f}°C`, VPD `~{p_vpd:.2f} kPa`.")
        if shock:
            sections.append("- 🚨 **Cảnh báo sớm:** Phát hiện tốc độ gia nhiệt nhanh, cần can thiệp trước 15 phút!")
            rec_fan = True
        if dew:
            sections.append("- 🚨 **Cảnh báo sớm:** Phát hiện nguy cơ đọng sương do nhiệt hạ nhanh kết hợp ẩm bão hòa!")
            rec_fan = True
        sections.append("")

    # 4. Actionable Recommendations
    sections.append("#### 4. Khuyến nghị điều khiển thiết bị")
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

    sections.append("\n*(Chế độ: Offline Agronomist Expert System — Tích hợp sẵn trong IoT Gateway)*")
    result_text = "\n".join(sections)
    return AnalysisResult(result_text, fan=rec_fan, pump=rec_pump, light=rec_light, is_offline=True, model="Expert Heuristic")

def _call_gemini_rest(api_key, prompt, system_instruction):
    """
    Direct HTTP REST API call to Google Gemini endpoint.
    Dynamically tries available models in order of latency and availability.
    """
    import urllib.request
    import urllib.error

    candidate_models = [
        "gemini-flash-lite-latest",
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]

    last_error = None
    for model_name in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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

        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return text, model_name
        except urllib.error.HTTPError as e:
            last_error = e
            # If 403 or 401, trying other models won't help (billing or auth issue)
            if e.code in [401, 403]:
                raise e
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    raise RuntimeError("Tất cả các model Gemini đều không khả dụng.")

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
        prompt_lines.append(f"\n⚠️ CÂU HỎI QUAN TRỌNG CỦA NGƯỜI QUẢN LÝ: \"{user_question.strip()}\"")
        prompt_lines.append("YÊU CẦU BẮT BUỘC: Bạn PHẢI đưa mục '### 💬 1. GIẢI ĐÁP TRỰC TIẾP CÂU HỎI' lên vị trí ĐẦU TIÊN TRÊN CÙNG của câu trả lời, trả lời trọng tâm và dứt khoát trước khi phân tích các mục khác!")

    prompt_lines.append("\nCấu trúc bắt buộc cần trình bày:")
    if user_question and user_question.strip():
        prompt_lines.append("1) ### 💬 1. Giải đáp trực tiếp câu hỏi (BẮT BUỘC Ở TRÊN CÙNG)")
        prompt_lines.append("2) ### 🌿 2. Đánh giá sinh lý cây trồng & Chỉ số VPD")
        prompt_lines.append("3) ### 📈 3. Nhận định rủi ro & Dự báo xu hướng 60 phút")
        prompt_lines.append("4) ### ⚡ 4. Khuyến nghị hành động điều khiển cụ thể (Quạt, Bơm/Phun sương, Đèn)")
    else:
        prompt_lines.append("1) ### 🌿 1. Đánh giá sinh lý cây trồng & Chỉ số VPD")
        prompt_lines.append("2) ### 📈 2. Nhận định rủi ro & Dự báo xu hướng 60 phút")
        prompt_lines.append("3) ### ⚡ 3. Khuyến nghị hành động điều khiển cụ thể (Quạt, Bơm/Phun sương, Đèn)")
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
        raw_text, used_model = _call_gemini_rest(api_key, prompt_text, SYSTEM_PROMPT)
        rec_fan = "quạt" in raw_text.lower() and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        rec_pump = ("bơm" in raw_text.lower() or "phun sương" in raw_text.lower()) and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        return AnalysisResult(f"### 🤖 Tư Vấn Chuyên Gia Nông Học (Google Gemini AI: `{used_model}`)\n\n" + raw_text,
                              fan=rec_fan, pump=rec_pump, light=True, is_offline=False, model=used_model)
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
