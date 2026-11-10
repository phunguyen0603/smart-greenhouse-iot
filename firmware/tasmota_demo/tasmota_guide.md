# Hướng Dẫn Thực Hiện & Minh Chứng Yếu Tố T01: Cảm Biến I2C Trên Tasmota

## 1. Giới thiệu
Mã công nghệ **T01** (0.5 điểm) yêu cầu: *Cảm biến sử dụng giao tiếp I2C trên Tasmota*.
Tasmota là nền tảng Zero Coding mã nguồn mở cho ESP32. Trên board **YoloUNO (ESP32-S3)**, Tasmota hỗ trợ ngôn ngữ kịch bản **Berry** cho phép viết driver tương tác trực tiếp với thanh ghi I2C của cảm biến **DHT20**.

## 2. Các bước tiến hành (Thực hiện trong 5 phút)

### Bước 1: Nạp firmware Tasmota vào YoloUNO
1. Cắm board YoloUNO vào cổng USB máy tính.
2. Dùng trình duyệt Chrome hoặc Edge truy cập: [https://tasmota.github.io/install](https://tasmota.github.io/install)
3. Chọn bản **Tasmota ESP32-S3 (hoặc Tasmota32 CDC)** và bấm **Install**.

### Bước 2: Kết nối Wi-Fi & Cấu hình chân I2C
1. Sau khi nạp xong, ESP32 sẽ phát Wi-Fi tên `tasmota-xxxxxx`. Kết nối vào Wi-Fi này và truy cập `192.168.4.1` để nhập tên & mật khẩu Wi-Fi nhà bạn.
2. Vào **Configuration -> Configure Module**:
   * Chọn `GPIO 11` là `I2C SDA`
   * Chọn `GPIO 12` là `I2C SCL`
   * Bấm **Save** (Board sẽ khởi động lại).

### Bước 3: Nạp script Berry `dht20.be`
1. Vào **Consoles -> Manage File System**.
2. Tạo file mới tên `dht20.be` và dán toàn bộ nội dung file [dht20.be](file:///d:/BK/HK261/IoT/Assignment/firmware/tasmota_demo/dht20.be) vào.
3. Tạo (hoặc mở) file `autoexec.be` và thêm dòng:
   ```berry
   load("dht20.be")
   ```
4. Khởi động lại board bằng lệnh `Restart 1` trên Console.

## 3. Minh chứng cho Báo cáo & Video Demo (T01)
1. **Giao diện Web UI**: Trên trang chủ Tasmota xuất hiện 2 dòng thông số:
   * `DHT20 Nhiệt độ: 28.5 °C`
   * `DHT20 Độ ẩm: 75.2 %`
2. **Bản tin JSON trên Console**:
   ```json
   {"Time":"2026-10-30T10:00:00","temperature":28.5,"humidity":75.2}
   ```
3. Chụp ảnh màn hình Web UI Tasmota và quay clip ngắn 30s – 1 phút làm minh chứng đưa vào Báo cáo (Chương 3, Mục 3.2.1) và Video Demo!
