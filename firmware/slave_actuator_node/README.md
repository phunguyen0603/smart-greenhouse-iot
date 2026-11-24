# Firmware Node Chấp Hành Vệ Tinh (Slave Actuator Node)

Thư mục này chứa toàn bộ mã nguồn Firmware dành cho **Node Con (Slave Node)** trong hệ thống Smart Greenhouse IoT (HK261).

---

## 1. Vai trò của Node Con trong hệ thống
* **Chức năng chính**: Nhận lệnh không dây qua **ESP-NOW** từ Master Node để đóng/ngắt các mạch **Rơ-le (Quạt thông gió, Máy bơm tưới)** và đọc cảm biến phân khu riêng (độ ẩm đất).
* **Đặc tính kỹ thuật**:
  * **Dynamic Pairing (Cắm là xin kết nạp)**: Tự động gửi gói tin xin ghép đôi `MSG_PAIR_REQ` đến Master khi chưa ghép đôi.
  * **Cơ chế Phê duyệt an toàn (Manual Approval)**: Master chỉ cấp quyền khi người dùng bấm `[✅ CHẤP NHẬN KẾT NẠP]` trên Web Dashboard của Master.
  * **Lưu trữ vĩnh viễn (NVS Flash)**: Địa chỉ MAC của Master và Network ID được lưu vào bộ nhớ Flash của chip, khi cúp điện khởi động lại vẫn tự nhớ Master của mình mà không cần cấu hình lại.
  * **Heartbeat thời gian thực**: Cứ mỗi **3 giây**, Node con tự động bắn một nhịp tim `MSG_HEARTBEAT` kèm thông số độ ẩm đất về Master. Nếu Master mất liên lạc quá **30 giây**, Web UI sẽ báo `🔴 MẤT LIÊN LẠC`.
  * **Đổi Master dễ dàng**: Nhấn giữ nút **BOOT** trong 3 giây để xóa ghép đôi khỏi Flash và chuyển sang quét tìm Master mới.
  * **Bảo vệ an toàn (Failsafe Watchdog)**: Nếu mất tín hiệu Master quá 45 giây, Node con sẽ tự động ngắt tải (tắt bơm/quạt) để chống ngập úng hoặc cháy thiết bị.

---

## 2. Sơ đồ chân đấu nối phần cứng (Pinout)

Firmware hỗ trợ tự động nhận diện cả **ESP32 thường (DevKit/NodeMCU)** lẫn **ESP32-S3 (YoloUNO)**:

| Thiết bị ngoại vi | Chân trên ESP32 thường (esp32dev) | Chân trên YoloUNO (yolo_uno) | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Relay 1 (Quạt - FAN)** | `GPIO 18` | `GPIO 4` (D4) | Kích đóng ngắt quạt 220V/12V |
| **Relay 2 (Bơm - PUMP)**| `GPIO 19` | `GPIO 5` (D5) | Kích đóng ngắt van/bơm nước |
| **Nút Ghép đôi (Pair/Reset)**| `GPIO 0` (Nút BOOT) | `GPIO 0` (Nút BOOT) | Nhấn giữ 3s để hủy ghép đôi |
| **LED báo trạng thái** | `GPIO 2` | `GPIO 48` | Nháy nhanh: đang tìm Master; Nháy chậm: Online |
| **Cảm biến đất (Tùy chọn)** | `GPIO 34` (ADC) | `GPIO 1` (A0) | Đọc độ ẩm đất gửi về Master |

---

## 3. Cách nạp code vào board

Mở Terminal và đứng tại thư mục dự án:

* **Nếu nạp vào board ESP32 thường (ESP32 DevKit, NodeMCU, Wroom)**:
  ```bash
  pio run -d ./firmware/slave_actuator_node -e esp32dev -t upload
  ```
* **Nếu nạp vào board YoloUNO (ESP32-S3)**:
  ```bash
  pio run -d ./firmware/slave_actuator_node -e yolo_uno -t upload
  ```

---

## 4. Quy trình Ghép đôi & Thử nghiệm thực tế

1. **Kết nối Web Dashboard của Master**:
   * Dùng điện thoại / laptop kết nối vào Wi-Fi **`SmartGreenhouse-AP`** (mạng mở, không cần mật khẩu).
   * Cơ chế **Captive Portal** sẽ tự động mở trang web điều khiển (hoặc truy cập `http://192.168.4.1`).
2. **Cắm nguồn Node con**:
   * Cắm điện board Node con.
   * Node con phát sóng xin kết nạp `MSG_PAIR_REQ`.
   * Trên Web Dashboard của Master, tab **`⚙️ CÀI ĐẶT & KẾT NẠP`** sẽ sáng huy hiệu cam báo có thiết bị xin kết nạp (`⚠️ Yêu Cầu Kết Nạp Chờ Duyệt: Slave-Relay-01`).
3. **Phê duyệt trên Web**:
   * Chuyển sang tab **`⚙️ CÀI ĐẶT & KẾT NẠP`** và bấm **`[✅ CHẤP NHẬN KẾT NẠP]`**.
   * Master sẽ lưu Node này vào bộ nhớ Flash vĩnh viễn và gửi gói tin xác nhận `MSG_PAIR_ACK`.
   * Chuyển lại tab **`📊 MÀN HÌNH CHÍNH`**, bạn sẽ thấy ngay thẻ điều khiển độc lập của `Slave-Relay-01` xuất hiện với chỉ số độ ẩm đất riêng và các nút bật/tắt Quạt, Bơm.
4. **Theo dõi nhịp tim sống / chết (Heartbeat)**:
   * Node con gửi Heartbeat mỗi 3 giây: Thẻ hiển thị `🟢 ĐANG HOẠT ĐỘNG (X giây trước)` kèm chấm xanh nhấp nháy.
   * Nếu rút điện Node con quá 30 giây: Web đổi sang `🔴 MẤT LIÊN LẠC`, viền chuyển sang nét đứt đỏ và các nút điều khiển tự động khóa an toàn.
5. **Hủy kết nạp / Đổi Master**:
   * Trên Web: Vào tab **`⚙️ CÀI ĐẶT & KẾT NẠP`** $\rightarrow$ Danh Sách Node Đã Lưu $\rightarrow$ Bấm **`[🗑️ Hủy kết nạp]`**.
   * Trên phần cứng Node con: Nhấn giữ nút **BOOT** trong 3 giây để xóa cấu hình Flash và sẵn sàng kết nối Master mới.
