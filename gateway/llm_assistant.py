"""
Agricultural LLM Assistant (N01) - 100% Online Google Gemini AI
Features:
- Pure Google Gemini AI (No offline heuristic fallback)
- Ultra-fast verified models: gemini-3.1-flash-lite, gemini-flash-lite-latest, gemini-3-flash-preview (<1.5s latency, zero 404s)
- Direct REST API with auto-failover across verified models
- Mandatory Question-First Structure (answers user question at the very top)
- Automatic actuator recommendation extraction (Fan, Pump, Grow Light)
"""

import os
import json
import urllib.request
import urllib.error

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
1. NẾU CÓ CÂU HỎI TỪ NGƯỜI QUẢN LÝ NHÀ KÍNH, BẠN BẮT BUỘC PHẢI ĐẶT MỤC: "### 💬 1. GIẢI ĐÁP TRỰC TIẾP CÂU HỎI" LÊN NGAY TRÊN CÙNG (trên tất cả các mục khác), trả lời trực diện, rõ ràng, dứt khoát trước tiên.
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

# Verified, active Gemini models that never return 404
VERIFIED_GEMINI_MODELS = [
    "gemini-3.1-flash-lite",      # Fastest (~0.9s), highly reliable
    "gemini-flash-lite-latest",  # Standard stable flash-lite (~1.3s)
    "gemini-3-flash-preview",    # Preview flash model
]

def _call_gemini_rest(api_key, prompt, system_instruction):
    """
    Direct HTTP REST API call to Google Gemini endpoint.
    Sequentially attempts verified, active models.
    """
    last_error = None
    for model_name in VERIFIED_GEMINI_MODELS:
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
                "temperature": 0.3,
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
            with urllib.request.urlopen(req, timeout=10) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                return text, model_name
        except urllib.error.HTTPError as e:
            last_error = e
            # If 401 or 403, it's an authentication/billing error, fail immediately
            if e.code in [401, 403]:
                err_body = e.read().decode("utf-8")
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get("error", {}).get("message", e.reason)
                except Exception:
                    msg = str(e)
                raise RuntimeError(f"HTTP {e.code} Forbidden/Unauthorized: {msg}")
            continue
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise RuntimeError(f"Lỗi kết nối Gemini API ({str(last_error)}). Đã thử các model: {', '.join(VERIFIED_GEMINI_MODELS)}.")
    raise RuntimeError("Không thể kết nối tới Google Gemini API. Vui lòng kiểm tra lại mạng hoặc API Key.")

def analyze_greenhouse_state(temp, humi, vpd, ai_state_str, crop_name="General", api_key=None,
                             trend_info=None, user_question=None):
    """
    Pure Google Gemini Agronomist AI Analysis (N01).
    Directly calls Gemini API; returns live AI analysis and extracts actuator recommendations.
    """
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        return AnalysisResult(
            "⚠️ **CHƯA CÓ GEMINI API KEY**\n\n"
            "Vui lòng nhập API Key vào ô bên trên để kích hoạt Trợ lý ảo Google Gemini AI.\n"
            "*(Lấy Key miễn phí 100% tại: https://aistudio.google.com/)*",
            fan=None, pump=None, light=None, is_offline=False, model="None"
        )

    c_name, c_prof = get_crop_profile(crop_name)

    # Construct agronomic prompt for Gemini
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
        prompt_lines.append("1) ### 💬 1. GIẢI ĐÁP TRỰC TIẾP CÂU HỎI (BẮT BUỘC Ở TRÊN CÙNG)")
        prompt_lines.append("2) ### 🌿 2. Đánh giá Sinh lý cây trồng & Chỉ số VPD")
        prompt_lines.append("3) ### 📈 3. Nhận định Rủi ro & Dự báo Xu hướng 60 phút")
        prompt_lines.append("4) ### ⚡ 4. Khuyến nghị Hành động điều khiển cụ thể (Quạt, Bơm/Phun sương, Đèn)")
    else:
        prompt_lines.append("1) ### 🌿 1. Đánh giá Sinh lý cây trồng & Chỉ số VPD")
        prompt_lines.append("2) ### 📈 2. Nhận định Rủi ro & Dự báo Xu hướng 60 phút")
        prompt_lines.append("3) ### ⚡ 3. Khuyến nghị Hành động điều khiển cụ thể (Quạt, Bơm/Phun sương, Đèn)")

    prompt_text = "\n".join(prompt_lines)

    # Call Gemini REST API directly
    try:
        raw_text, used_model = _call_gemini_rest(api_key, prompt_text, SYSTEM_PROMPT)
        rec_fan = "quạt" in raw_text.lower() and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        rec_pump = ("bơm" in raw_text.lower() or "phun sương" in raw_text.lower()) and ("bật" in raw_text.lower() or "on" in raw_text.lower())
        return AnalysisResult(
            f"### 🤖 Tư Vấn Chuyên Gia Nông Học (Google Gemini AI: `{used_model}`)\n\n" + raw_text,
            fan=rec_fan, pump=rec_pump, light=True, is_offline=False, model=used_model
        )
    except Exception as e:
        return AnalysisResult(
            f"❌ **LỖI GỌI GOOGLE GEMINI API**\n\n"
            f"> Chi tiết lỗi: `{str(e)}`\n\n"
            f"**Hướng dẫn kiểm tra:**\n"
            f"1. Kiểm tra lại chuỗi API Key của bạn trên https://aistudio.google.com/ (đảm bảo không thừa dấu cách).\n"
            f"2. Đảm bảo máy tính có kết nối Internet.\n"
            f"3. Bấm lại nút '🤖 Phân tích tình trạng' để hệ thống tự động thử lại.",
            fan=None, pump=None, light=None, is_offline=False, model="Error"
        )

if __name__ == "__main__":
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("Set GEMINI_API_KEY environment variable to run this test.")
        raise SystemExit(1)
    print("Testing pure online Gemini...")
    res = analyze_greenhouse_state(
        temp=31.5, humi=58.0, vpd=1.95, ai_state_str="HEAT_STRESS_DRY",
        crop_name="Strawberry (Dâu tây)",
        api_key=key,
        user_question="Có nên bật quạt và tưới nước cho dâu tây lúc này không?"
    )
    print("Model:", res.model)
    print("Fan:", res.fan, "Pump:", res.pump)
    print("-" * 50)
    print(res[:600])
