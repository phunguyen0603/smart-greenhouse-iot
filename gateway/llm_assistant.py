"""
Agricultural LLM Assistant (N01)
Integrates Google Gemini to analyze real-time vi-climate data and provide agronomic advice.
"""

import os
import json
import math

SYSTEM_PROMPT = """
Bạn là một chuyên gia Nông Nghiệp Công Nghệ Cao (Agronomist & Smart Greenhouse Specialist).
Nhiệm vụ của bạn là phân tích dữ liệu cảm biến thời gian thực, kết quả suy luận từ TinyML (Edge AI) và đưa ra:
1. Đánh giá tình trạng sinh lý của cây trồng (sự thoát hơi nước qua khí khổng, cân bằng độ hụt áp suất hơi VPD).
2. Nhận định rủi ro (nguy cơ sốc nhiệt, úa lá, hoặc nguy cơ đọng sương bùng phát nấm bệnh botrytis/phấn trắng).
3. Đề xuất hành động điều khiển cụ thể (thời gian bật quạt thông gió, thời điểm phun sương làm mát, điều chỉnh chu kỳ tưới).
Trả lời súc tích, chuyên nghiệp, khoa học.
"""

def generate_offline_analysis(temp, humi, vpd, ai_state_str, crop_name="General"):
    """
    Expert heuristic analysis fallback if API key is not yet set.
    """
    if vpd < 0.4:
        analysis = (
            f"⚠️ CẢNH BÁO VI KHÍ HẬU: VPD = {vpd:.2f} kPa quá thấp (Độ ẩm {humi:.1f}% quá bão hòa). "
            f"Cây trồng '{crop_name}' bị đình trệ thoát hơi nước, dinh dưỡng từ rễ không dẫn lên ngọn được. "
            f"Đặc biệt nguy cơ đọng sương trên mặt lá rất cao, tạo điều kiện thuận lợi cho nấm bệnh bùng phát. "
            f"Khuyến nghị: Bật ngay quạt thông gió để đối lưu không khí và hạ độ ẩm."
        )
    elif vpd > 1.4:
        analysis = (
            f"⚠️ CẢNH BÁO SỐC NHIỆT: VPD = {vpd:.2f} kPa quá cao (Nhiệt độ {temp:.1f}°C cao kết hợp ẩm thấp). "
            f"Cây trồng '{crop_name}' phải đóng khí khổng để tránh mất nước, dẫn đến ngừng quang hợp và nguy cơ cháy chóp lá. "
            f"Khuyến nghị: Kích hoạt hệ thống phun sương hạt mịn trong 5-10 phút để giảm nhiệt độ và bù ẩm."
        )
    else:
        analysis = (
            f"✅ VI KHÍ HẬU TỐI ƯU: Nhiệt độ {temp:.1f}°C, Độ ẩm {humi:.1f}% và VPD = {vpd:.2f} kPa nằm trong vùng chỉ số vàng. "
            f"Áp suất hơi nước lý tưởng kích thích khí khổng mở tối đa, quang hợp mạnh mẽ và hấp thụ khoáng chất tốt. "
            f"Duy trì thông gió nhẹ định kỳ, chưa cần kích hoạt các thiết bị cưỡng bức."
        )
    return analysis

def analyze_greenhouse_state(temp, humi, vpd, ai_state_str, crop_name="General", api_key=None):
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")

    if not api_key:
        return generate_offline_analysis(temp, humi, vpd, ai_state_str, crop_name)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = (
            f"Dữ liệu thời gian thực từ nhà kính trồng {crop_name}:\n"
            f"- Nhiệt độ: {temp:.2f} °C\n"
            f"- Độ ẩm không khí: {humi:.2f} %\n"
            f"- Chỉ số VPD: {vpd:.3f} kPa\n"
            f"- Trạng thái dự đoán từ TinyML ESP32-S3: {ai_state_str}\n\n"
            f"Hãy đưa ra phân tích sinh lý cây trồng và khuyến nghị điều khiển thiết bị phù hợp."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": SYSTEM_PROMPT}
        )
        return response.text
    except Exception as e:
        return f"[Gemini Online Fallback]: {generate_offline_analysis(temp, humi, vpd, ai_state_str, crop_name)}"

if __name__ == "__main__":
    test_res = analyze_greenhouse_state(33.5, 48.0, 2.65, "HEAT_STRESS_DRY", "Strawberry")
    print("=== Agronomist LLM Test Output ===")
    print(test_res)
