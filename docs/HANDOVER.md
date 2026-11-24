# TÀI LIỆU BÀN GIAO KỸ THUẬT & HƯỚNG DẪN VẬN HÀNH (HANDOVER GUIDE)
## Đề tài: Trạm Quan Trắc & Điều Khiển Nông Nghiệp Công Nghệ Cao (Smart Greenhouse IoT)
**Môn học**: Internet of Things (IoT) - Học kỳ 261 | **Trường**: ĐH Bách Khoa - ĐHQG TP.HCM  
**Phiên bản bàn giao**: v2.5.0 (Multi-node Mesh, Heartbeat 30s, Captive Portal, Flash NVS Persistence)

---

## 1. Tổng quan Trạng thái Hệ thống

Hệ thống đã được hiện thực hoàn chỉnh 100% các tiêu chí từ cơ bản đến nâng cao (13.5/8.0 điểm công nghệ, mục tiêu 10/10 môn học):

| Phân hệ | Thành phần mã nguồn | Trạng thái hiện tại |
| :--- | :--- | :--- |
| **Master Node (ESP32-S3 YoloUNO)** | `firmware/yolo_uno_greenhouse/` | • Thu thập DHT20 qua I2C, lọc số 2 tầng (Median 5 + EMA $\alpha=0.25$).<br>• Hiển thị màn hình LCD 16x2 (địa chỉ I2C `0x21`).<br>• Suy luận TinyML tại biên: thời gian **2.2 us**, độ chính xác **99.0%**.<br>• Mở Wi-Fi AP không mật khẩu `SmartGreenhouse-AP` tích hợp **Captive Portal** (DNS port 53).<br>• Quản lý mạng lưới ESP-NOW, lưu danh sách Node vào **Flash NVS**.<br>• Web Dashboard 2 Tab: Màn hình chính & Cài đặt kết nạp. |
| **Slave Node (ESP32 / YoloUNO)** | `firmware/slave_actuator_node/` | • Tự động gửi gói tin xin kết nạp `MSG_PAIR_REQ`.<br>• Lưu MAC Master vào Flash (NVS) tự kết nối lại sau khi cúp điện.<br>• Định kỳ gửi **Heartbeat mỗi 3 giây** (`MSG_HEARTBEAT`).<br>• Điều khiển độc lập Rơ-le Quạt & Rơ-le Bơm.<br>• Đọc độ ẩm đất phân khu.<br>• Watchdog Failsafe: ngắt tải an toàn nếu mất tín hiệu Master > 45s.<br>• Nút BOOT giữ 3s để hủy ghép đôi và đổi Master mới. |
| **IoT Gateway PC (Python)** | `gateway/` | • Đọc cổng USB CDC Native của YoloUNO qua Serial JSON.<br>• SQLite Offline Buffer tự lưu bù dữ liệu khi đứt mạng.<br>• Cầu nối MQTT lên CoreIOT Cloud (`v1/gateway/telemetry`).<br>• Thuật toán AI dự báo xu hướng vi khí hậu trước 1 giờ.<br>• Giao diện Streamlit Dashboard cục bộ (`dashboard_app.py`).<br>• Trợ lý AI Google Gemini (`llm_assistant.py`). |
| **Đám mây CoreIOT** | `app.coreiot.io` | • RuleChain tự động hóa kích hoạt RPC bật/tắt thiết bị.<br>• Cảnh báo tức thời qua Telegram Bot & Notification Center. |

---

## 2. Sơ đồ Kiến trúc & Luồng Dữ liệu

```
[Vườn ươm / Khu canh tác]
    ├── Cảm biến DHT20 (I2C: SDA=11, SCL=12)
    └── Màn hình LCD 16x2 (I2C Addr: 0x21)
                │
                ▼
      ┌───────────────────────────┐
      │  MASTER NODE (YoloUNO)    │ ◄── Wi-Fi AP + Captive Portal ──► [Smartphone / Laptop]
      │  ESP32-S3 (FreeRTOS)      │     (SSID: SmartGreenhouse-AP)    (Web Dashboard: 192.168.4.1)
      │  • TinyML Edge AI         │
      │  • NVS Flash (Master Cfg) │
      └─────────────┬─────────────┘
                    │
       ESP-NOW (2.4GHz, < 5ms)
       Unicast / Broadcast
                    │
      ┌─────────────┴─────────────┐
      │                           │
      ▼                           ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   SLAVE ACTUATOR NODE 1  │  │   SLAVE ACTUATOR NODE 2  │
│   (ESP32 / YoloUNO)      │  │   (ESP32 / YoloUNO)      │
│   • Heartbeat: 3s        │  │   • Heartbeat: 3s        │
│   • Rơ-le Quạt 1         │  │   • Rơ-le Quạt 2         │
│   • Rơ-le Bơm 1          │  │   • Rơ-le Bơm 2          │
│   • Độ ẩm đất Vùng 1     │  │   • Độ ẩm đất Vùng 2     │
└──────────────────────────┘  └──────────────────────────┘
```

---

## 3. Sơ đồ Đấu nối Phần cứng (Pinout)

### 3.1. Master Node (YoloUNO ESP32-S3)
* **Cảm biến DHT20**:
  * VCC $\rightarrow$ `3.3V` / `5V`
  * GND $\rightarrow$ `GND`
  * SDA $\rightarrow$ `GPIO 11`
  * SCL $\rightarrow$ `GPIO 12`
* **Màn hình LCD 16x2 (I2C Module)**:
  * SDA $\rightarrow$ `GPIO 11`
  * SCL $\rightarrow$ `GPIO 12`
  * Địa chỉ I2C: `33` (Thập phân) = `0x21` (Hex).
* **Đèn LED & Báo hiệu**:
  * NeoPixel RGB tích hợp: `GPIO 45`
  * Grow Light / LED trạng thái: `GPIO 48`
* **Cổng cắm PC Gateway**: Cắm trực tiếp vào cổng **Native USB Type-C** của YoloUNO (nhận diện qua USB CDC).

### 3.2. Slave Node (ESP32 Thường vs YoloUNO)

| Chức năng thiết bị | Chân trên ESP32 DevKit (esp32dev) | Chân trên YoloUNO (yolo_uno) | Ghi chú kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Relay Quạt (FAN)** | `GPIO 18` | `GPIO 4` (D4) | Rơ-le Active LOW (mặc định) |
| **Relay Bơm (PUMP)** | `GPIO 19` | `GPIO 5` (D5) | Rơ-le Active LOW (mặc định) |
| **Nút BOOT (Reset Pair)**| `GPIO 0` | `GPIO 0` | Giữ 3 giây để xóa Flash & tìm Master |
| **LED trạng thái** | `GPIO 2` | `GPIO 48` | Nháy nhanh: Chưa pair; Nháy chậm: Online |
| **Cảm biến độ ẩm đất** | `GPIO 34` (ADC1_CH6) | `GPIO 1` (A0) | Đọc giá trị Analog 0 - 4095 |

---

## 4. Giao thức ESP-NOW Nhị phân (`struct_greenhouse_msg`)

Tất cả các bản tin truyền qua ESP-NOW đều tuân thủ cấu trúc nhị phân đồng nhất (kích thước **52 bytes**, nhỏ hơn nhiều so với giới hạn 250 bytes của ESP-NOW):

```c
enum MessageType : uint8_t {
    MSG_TELEMETRY    = 1,   // Master phát quảng bá dữ liệu khí hậu định kỳ
    MSG_CMD_ACTUATOR = 2,   // Master gửi lệnh đích danh điều khiển rơ-le
    MSG_PAIR_REQ     = 3,   // Slave cắm điện phát sóng xin kết nạp
    MSG_PAIR_ACK     = 4,   // Master chấp thuận và xác nhận kết nạp
    MSG_SLAVE_STATUS = 5,   // Slave phản hồi trạng thái chấp hành
    MSG_HEARTBEAT    = 6    // Slave bắn nhịp tim định kỳ mỗi 3s
};

typedef struct struct_greenhouse_msg {
    uint8_t msg_type;          // Loại bản tin (MessageType enum)
    char network_id[16];       // Mã mạng (mặc định "GH_ZONE_A")
    char device_id[16];        // Định danh người gửi (VD: "Slave-Relay-01")
    char target_id[16];        // Định danh đích ("ALL" hoặc ID Node con)
    float temp;                // Nhiệt độ Master / Độ ẩm đất Slave (%)
    float humi;                // Độ ẩm khí quyển Master (%)
    float vpd;                 // Áp suất hụt hơi VPD (kPa)
    int ai_state;              // Phân loại AI (0: Optimal, 1: Dry, 2: Mold)
    bool fan;                  // Trạng thái quạt
    bool pump;                 // Trạng thái máy bơm
    uint32_t timestamp;        // Millis gửi
} struct_greenhouse_msg;
```

---

## 5. Hướng dẫn Vận hành Web Dashboard & Mạng Lưới Node

1. **Kết nối vào mạng Wi-Fi**:
   * Dùng điện thoại / laptop tìm Wi-Fi: **`SmartGreenhouse-AP`** (mạng mở, không có mật khẩu).
   * Do có **Captive Portal (DNS port 53)**, thiết bị sẽ tự động bật màn hình đăng nhập / giao diện điều khiển. Nếu không tự mở, hãy gõ địa chỉ: `http://192.168.4.1`.
2. **Quy trình Tự động Phát hiện & Chấp thuận Node con mới**:
   * Hệ thống **hoàn toàn tự động phát hiện** các Node con mới khi chúng cắm nguồn (không cần phải bật/tắt thủ công "Chế độ ghép đôi" như các hệ thống cũ).
   * Khi Node con mới gửi tín hiệu xin gia nhập hoặc gửi trạng thái, Master tự động bắt gói tin và đưa vào danh sách chờ duyệt.
   * Trên Web Dashboard, tab **`⚙️ CÀI ĐẶT & QUẢN LÝ NODE`** sẽ sáng huy hiệu cam thông báo có thiết bị chờ duyệt:
     > `⚠️ Yêu Cầu Kết Nạp Chờ Duyệt: Slave-Relay-01 [XX:XX:XX:XX:XX:XX]`
   * Bấm nút **`[✅ CHẤP NHẬN KẾT NẠP]`**.
   * Master sẽ lưu thông tin Node con vào bộ nhớ Flash vĩnh viễn và gửi gói tin xác nhận.
3. **Giám sát & Điều khiển độc lập trên Màn hình chính**:
   * Chuyển sang tab **`📊 MÀN HÌNH CHÍNH`**: Thẻ riêng của Node con sẽ xuất hiện ngay lập tức.
   * Thẻ hiển thị độ ẩm đất riêng của phân khu đó.
   * **Nút điều khiển độc lập**: Bấm bật/tắt Quạt hoặc Bơm trên thẻ này chỉ tác động đến đúng Node con tương ứng, không làm ảnh hưởng các Node khác.
4. **Cơ chế Giám sát Sống / Chết (Heartbeat 3s & Timeout 30s)**:
   * **Online**: Node con gửi Heartbeat mỗi 3 giây $\rightarrow$ Huy hiệu xanh nhấp nháy: `🟢 ĐANG HOẠT ĐỘNG (X giây trước)`.
   * **Offline**: Nếu Node con bị rút điện hoặc mất sóng **quá 30 giây** $\rightarrow$ Web tự động chuyển sang `🔴 MẤT LIÊN LẠC (X giây trước)`, viền thẻ đổi nét đứt đỏ và các nút điều khiển tự động khóa an toàn.
   * **Phục hồi**: Cắm nguồn lại cho Node con, ngay nhịp tim đầu tiên (trong vòng 3s), Web sẽ tự động chuyển xanh trở lại.
5. **Hủy kết nạp & Xóa Node linh hoạt**:
   * **Xóa trực tiếp trên Màn hình chính**: Ngay trên thẻ riêng của mỗi Node con ở Dashboard, có sẵn nút **`[🗑️ XÓA NODE]`**. Bấm xác nhận là Node sẽ được xóa ngay tức khắc.
   * **Xóa trong tab Cài đặt**: Vào tab **`⚙️ CÀI ĐẶT & QUẢN LÝ NODE`** $\rightarrow$ Khu vực **`🗑️ Quản Lý & Xóa Node (Lưu Flash NVS)`** $\rightarrow$ Bấm nút **`[🗑️ XÓA NODE]`**. Node sẽ bị hủy đăng ký trong Flash NVS của Master.
   * **Xóa trên Local Gateway Streamlit**: Vào tab `Topology Manager` trên Streamlit app $\rightarrow$ mục `🗑️ Xóa Sub-Node khỏi hệ thống` để dọn dẹp cơ sở dữ liệu SQLite.

---

## 6. Các "Bẫy" Kỹ thuật & Kinh nghiệm Debug (Crucial Traps)

Khi tiếp quản dự án, bạn **BẮT BUỘC** phải chú ý 5 điểm cốt lõi sau để tránh mất thời gian debug:

> [!WARNING]
> ### Trap 1: Cỡ Stack của Task FreeRTOS trên ESP32 tính bằng BYTES
> * Trên FreeRTOS chuẩn (ARM Cortex-M), tham số stack trong `xTaskCreate` tính bằng **Words** (4 bytes).
> * **TUY NHIÊN trên ESP-IDF / ESP32 Arduino Core**, tham số stack được tính bằng **BYTES**!
> * Khi gọi các hàm in định dạng dài như `Serial.printf(...)` trên cổng USB CDC của ESP32-S3, thư viện cần bộ đệm lớn. Stack size **bắt buộc phải $\ge 4096$ bytes**, nếu để $2048$ bytes chip sẽ bị `Stack canary watchpoint triggered` và bootloop liên tục.

> [!IMPORTANT]
> ### Trap 2: Lỗi cổng COM bị bận (PermissionError / Access is denied)
> * Nếu bạn đang mở các phần mềm Serial Terminal như **Tera Term (`ttermpro`)**, Arduino IDE Serial Monitor hoặc PlatformIO Monitor thì cổng COM sẽ bị chiếm độc quyền.
> * Khi chạy lệnh nạp firmware `pio run -t upload`, PlatformIO sẽ báo lỗi:
>   `could not open port 'COMxx': PermissionError(13, 'Access is denied.')`
> * **Khắc phục**: Luôn **ngắt kết nối hoặc đóng Tera Term** trước khi bấm upload firmware.

> [!NOTE]
> ### Trap 3: Lưu trữ cấu hình Flash (NVS Preferences)
> * Cả Master lẫn Slave đều dùng `Preferences.h` để lưu cấu hình.
> * Namespace của Master: `"master_cfg"`.
> * Namespace của Slave: `"slave_cfg"`.
> * Nếu bạn muốn xóa trắng ghép đôi trên Slave bằng phần cứng: Nhấn giữ nút **BOOT trong 3 giây** khi Slave đang cắm điện, đèn LED sẽ nháy nhanh báo hiệu bộ nhớ Flash đã được reset về mặc định.

> [!TIP]
> ### Trap 4: Wi-Fi Channel trong ESP-NOW
> * ESP-NOW truyền nhận trên cùng một kênh vô tuyến (Wi-Fi Channel).
> * Mặc định Master khởi tạo SoftAP trên **Kênh 1 (Channel 1)**.
> * Slave ở chế độ `WIFI_STA` chưa kết nối router cũng hoạt động ở Kênh 1.
> * Cả 2 đều để `peer_info.channel = 0` (sử dụng kênh hiện hành của radio). Tuyệt đối không hardcode kênh khác nếu không có hàm quét kênh động.

---

## 7. Bảng Lệnh Thao Tác Nhanh (Cheat Sheet)

```powershell
# 1. Nạp Firmware Master Node (ESP32-S3 YoloUNO)
pio run -d .\firmware\yolo_uno_greenhouse -t upload

# 2. Nạp Firmware Slave Node (Board ESP32 DevKit thông thường)
pio run -d .\firmware\slave_actuator_node -e esp32dev -t upload

# 3. Nạp Firmware Slave Node (Board YoloUNO làm Slave)
pio run -d .\firmware\slave_actuator_node -e yolo_uno -t upload

# 4. Mở Serial Monitor xem log Realtime (Tốc độ baud: 115200)
pio device monitor -b 115200

# 5. Khởi chạy IoT Gateway Python kết nối CoreIOT
python .\gateway\gateway_service.py

# 6. Khởi chạy Giao diện Dashboard máy tính (Streamlit)
streamlit run .\gateway\dashboard_app.py

# 7. Huấn luyện lại mô hình TinyML khi có dữ liệu mới
python .\ai_training\dataset_generator.py
python .\ai_training\train_tinyml.py
```

---
*Tài liệu được lập và chuẩn hóa cho toàn bộ thành viên nhóm và kỹ sư tiếp quản dự án HK261.*
