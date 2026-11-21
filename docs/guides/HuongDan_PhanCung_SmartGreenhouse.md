# DANH SÁCH PHẦN CỨNG & HƯỚNG DẪN VẬN HÀNH KHI CÓ MẠCH THẬT
*(Đề tài: Smart Greenhouse – ESP32-S3 YoloUNO & CoreIOT)*

---

## PHẦN 1: DANH SÁCH PHẦN CỨNG CHO TOÀN BỘ ASSIGNMENT

Dựa trên các chân GPIO, giao tiếp I2C và driver đã được lập trình sẵn trong mã nguồn (`firmware/yolo_uno_greenhouse/include/global.h`, `sensor_lcd_task.cpp`, `tasmota_demo/tasmota_guide.md`), dưới đây là toàn bộ phần cứng cần chuẩn bị:

| STT | Thiết bị / Linh kiện | Thông số / Chân kết nối trong code | Số lượng | Vai trò trong hệ thống |
| :-: | :--- | :--- | :-: | :--- |
| **1** | **Board YoloUNO (ESP32-S3)** | Wi-Fi, BLE, USB-C, 8MB Flash, tích hợp sẵn `LED_PIN (GPIO 48)` & `NeoPixel (GPIO 45)` | **2** *(hoặc 1 nếu demo luân phiên)* | • **Board 1:** Chạy Firmware chính (`T04`, `T06`, `T07`, `T14`) nối với PC Gateway.<br>• **Board 2:** Chạy **Tasmota (`T01`)** hoặc làm Node nhận **ESP-NOW (`T06`)**. |
| **2** | **Cảm biến nhiệt độ & độ ẩm DHT20** | Giao tiếp I2C (`SDA: GPIO 11`, `SCL: GPIO 12`) | **1–2** | Đo nhiệt độ & độ ẩm không khí cho cả Firmware chính và Tasmota (`T01`). |
| **3** | **Màn hình LCD 16x2 I2C** | Giao tiếp I2C, địa chỉ **`0x21`** (`33` theo chuẩn Lab 3), nối chung bus `GPIO 11, 12` | **1** | Hiển thị tại chỗ: Nhiệt độ (`T`), Độ ẩm (`H`), `VPD` và nhãn TinyML (`OPT`/`DRY`/`MLD`). |
| **4** | **Cáp USB Type-C truyền dữ liệu** | **Bắt buộc là cáp Data** *(không dùng cáp chỉ sạc 2 dây)* | **2** | Nạp firmware và truyền Serial JSON (`115200 baud`) lên PC Gateway. |
| **5** | **Dây nối / Chia cổng I2C (Grove / Breadboard)** | Dây 4-pin PH2.0 (Grove) hoặc dây DuPont + 1 breadboard mini | **1 bộ** | Chia chung chân `GPIO 11 (SDA)`, `GPIO 12 (SCL)`, nguồn (`3.3V`/`5V`), `GND` cho DHT20 và LCD 16x2. |
| **6** | **Relay 5V + Quạt mini + Bơm mini 5V** *(Tùy chọn mở rộng)* | Kết nối GPIO điều khiển qua Relay | **1 bộ** | Minh họa cơ cấu chấp hành quay thật khi bấm Switch; nếu không mua thêm thì dùng sẵn **LED (`GPIO 48`)** và **NeoPixel (`GPIO 45`)** trên mạch để demo bật/tắt. |
| **7** | **PC / Laptop cá nhân** | Windows / Linux, có Wi-Fi & cổng USB | **1** | Đóng vai trò **IoT Gateway (`T08`, `T09`, `T10`, `T15`, `N01`)**. |

---

## PHẦN 2: HƯỚNG DẪN TỪNG BƯỚC KHI CÓ PHẦN CỨNG TRÊN TAY

Khi đã cầm phần cứng trong tay, bạn thực hiện đúng theo **5 bước** sau:

### Bước 1: Đấu nối dây phần cứng
1. Nối **DHT20** và **LCD 16x2 I2C** chung vào cổng I2C của YoloUNO:
   * `SDA` $\to$ **`GPIO 11`**
   * `SCL` $\to$ **`GPIO 12`**
   * `VCC` $\to$ `3.3V` (cho DHT20) / `5V` (cho LCD 16x2 — *kiểm tra kỹ điện áp ghi ở mặt sau LCD*)
   * `GND` $\to$ **`GND`**
2. Cắm mạch YoloUNO vào cổng USB của máy tính.
3. Mở **Device Manager $\to$ Ports (COM & LPT)** để xem số cổng COM vừa nhận (ví dụ `COM3`, `COM5`) và cập nhật vào mục `serial.port` trong file `gateway/config.yaml` *(hoặc giữ `auto_detect: true`, phần mềm sẽ tự dò)*.

---

### Bước 2: Biên dịch và Nạp Firmware lên YoloUNO
*(Lưu ý: Tắt `gateway_service.py` trước khi nạp để không bị chiếm cổng COM).*

Mở PowerShell tại thư mục gốc `D:\BK\HK261\IoT\Assignment` và chạy:
```powershell
cd firmware\yolo_uno_greenhouse
& "$env:USERPROFILE\.platformio\penv\Scripts\pio.exe" run -e yolo_uno -t upload
```

**Kiểm tra ngay sau khi nạp xong:**
* **LCD 16x2:** Sáng đèn và hiển thị `T:..C  H:..%` ở dòng 1, `VPD:.. AI:OPT` ở dòng 2.
* **NeoPixel (`GPIO 45`):** Đổi màu theo trạng thái TinyML (Xanh lá = `OPTIMAL`, Cam = `HEAT STRESS`, Tím = `MOLD RISK`).
* **Webserver cục bộ (`T07`):** Dùng điện thoại/laptop kết nối Wi-Fi **`SmartGreenhouse-AP`** (mật khẩu `12345678`), mở trình duyệt truy cập **`192.168.4.1`** để xem thông số và chụp ảnh minh chứng.

---

### Bước 3: Chạy IoT Gateway kết nối mạch thật (`T08`)
Quay về thư mục gốc `D:\BK\HK261\IoT\Assignment` và chạy:
```powershell
python gateway/gateway_service.py
```
* **Quan sát Terminal:** Thấy dòng `[Gateway Serial] Connected to ESP32 on COM...` là Gateway đã nhận dữ liệu JSON thật từ YoloUNO và tự động đẩy lên Dashboard CoreIOT.
* **Test thực tế:**
  * Thử hà hơi hoặc dùng máy sấy làm nóng nhẹ cảm biến DHT20 $\to$ Nhiệt độ/độ ẩm trên LCD và Dashboard CoreIOT cùng tăng $\to$ RuleChain kích hoạt Alarm và Notification tự động.
  * Bấm nút **`Grow Light`** trên Dashboard CoreIOT $\to$ Đèn LED trên chân `GPIO 48` của mạch sẽ bật/tắt theo.

---

### Bước 4: Test chế độ Đồng bộ Gateway & Lưu đệm Offline (`T15`)
*(Thực hiện bước này để lấy trọn 2.0 điểm mã `T15` và quay video minh chứng).*

1. Trên web **CoreIOT**: Vào `Entities` $\to$ `Devices` $\to$ `Greenhouse_Gateway_PC` $\to$ bấm Edit (cây bút chì) $\to$ bật công tắc **`Is gateway`** thành **ON** $\to$ Save.
2. Mở `gateway/config.yaml`, sửa dòng:
   ```yaml
   gateway_sync:
     enabled: true
   ```
3. Chạy lại `python gateway/gateway_service.py`:
   * CoreIOT sẽ tự động sinh ra thiết bị con **`YoloUNO_Node1`** (gắn sẵn `Greenhouse_Profile`).
   * **Test ngắt mạng (Offline Buffering):** Tắt Wi-Fi máy tính trong 1–3 phút $\to$ Terminal báo `[Offline Buffer] Mất mạng - Đã lưu vào SQLite (Tổng gói chờ đồng bộ: ...)`. Bật Wi-Fi lại $\to$ Terminal tự động báo `[Offline Sync] Đã đồng bộ bù thành công ... gói tin!`. *(Chụp màn hình log này làm minh chứng Chương 3 & Chương 4).*
   * **Cập nhật Dashboard cho chế độ `T15`:** Vào Dashboard $\to$ `Aliases` $\to$ đổi `Greenhouse_Device` sang `YoloUNO_Node1` (và chuyển Owner của `YoloUNO_Node1` sang `Public` nếu dùng Public Link).

---

### Bước 5: Chạy đo đạc Chương 4 & Hoàn thiện các minh chứng còn lại
1. **Đo độ trễ mạng thật (`tests/latency_tester.py`):**
   * Nhớ nhấn `Ctrl + C` **tắt `gateway_service.py` trước** để tránh xung đột Access Token trên CoreIOT.
   * Chạy lệnh:
     ```powershell
     python tests/latency_tester.py
     ```
   * Copy kết quả `Average Latency`, `Min / Max` điền vào **Bảng 4.2.2** trong `BaoCao_KhungChuan_SmartGreenhouse.md`.
2. **Test Tasmota (`T01`):** Làm theo hướng dẫn tại `firmware/tasmota_demo/tasmota_guide.md` trên Board thứ 2 (hoặc nạp tạm lên Board 1 sau khi đã quay video xong phần firmware chính) để chụp ảnh Web UI Tasmota hiển thị DHT20.
3. **Test Local Dashboard (`T10`) & Trợ lý ảo LLM (`N01`):**
   * Chạy giao diện cục bộ: `streamlit run gateway/dashboard_app.py`
   * Test Trợ lý ảo LLM: `python gateway/llm_assistant.py`
4. **Cập nhật Firmware OTA (`T14`):** Sửa phiên bản `FIRMWARE_VERSION` trong `firmware/yolo_uno_greenhouse/include/ota_service.h` từ `"1.0.0"` thành `"1.0.1"`, nạp qua Wi-Fi bằng ArduinoOTA trong PlatformIO và quay lại log Serial tiến trình `[OTA] Progress: 100% -> Rebooting...`.
