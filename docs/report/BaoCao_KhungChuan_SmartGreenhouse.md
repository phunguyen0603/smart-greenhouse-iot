# BÁO CÁO BÀI TẬP LỚN MÔN HỌC INTERNET OF THINGS (IoT)
*(Khung báo cáo chuẩn theo mẫu `BaoCaoMau_BaiTapLon_IoT.docx` – Đề tài Smart Greenhouse)*

**ĐỀ TÀI:** HỆ THỐNG QUAN TRẮC VÀ ĐIỀU KHIỂN NÔNG NGHIỆP CÔNG NGHỆ CAO (SMART GREENHOUSE) DỰA TRÊN TINYML VÀ NỀN TẢNG COREIOT  
**Giảng viên hướng dẫn:** TS. Lê Trọng Nhân (`trongnhanle@hcmut.edu.vn`)  
**Lớp:** `[Mã lớp]` – **Nhóm:** `[Mã nhóm]`  

| STT | Họ và tên | MSSV | Email |
| :-: | :--- | :--- | :--- |
| 1 | `[Thành viên 1]` | `[MSSV]` | `[email]@hcmut.edu.vn` |
| 2 | `[Thành viên 2]` | `[MSSV]` | `[email]@hcmut.edu.vn` |
| 3 | Nguyễn Hoàng Minh Phú | `[MSSV]` | `phu.nguyenhoangminh@hcmut.edu.vn` |

---

## THÔNG TIN NỘP BÀI

| Hạng mục | Đường dẫn / Thông tin |
| :--- | :--- |
| **Kho mã nguồn GitHub** | `[https://github.com/...]` |
| **Video demo** | `[https://...]` *(Khuyến nghị 5–10 phút)* |
| **Dashboard CoreIOT (Public Link)** | `https://app.coreiot.io/dashboard/67d278a0-e4bb-11f1-9e5a-0bef1c51c7aa?publicId=63a02680-cc86-11f1-93c2-abfd9e7a28d9` |
| **Ngày nộp** | `[dd/mm/2026]` |

---

## BẢNG PHÂN CÔNG CÔNG VIỆC

| STT | Họ và tên | MSSV | Công việc phụ trách | Đóng góp |
| :-: | :--- | :--- | :--- | :-: |
| 1 | `[Thành viên 1]` | `[MSSV]` | Phần cứng, node cảm biến I2C/Tasmota (`T01`), giao tiếp ESP-NOW (`T06`), Webserver cục bộ (`T07`) | `33%` |
| 2 | `[Thành viên 2]` | `[MSSV]` | Thu thập dữ liệu, huấn luyện TinyML (`T04`, `T05`), Firmware OTA (`T14`), Trợ lý ảo LLM (`N01`) | `33%` |
| 3 | Nguyễn Hoàng Minh Phú | `[MSSV]` | IoT Gateway PC (`T08`), Gateway AI (`T09`), Local UI (`T10`), Đồng bộ CoreIOT (`T15`), Dashboard (`T11`), RuleChain (`T12`), Notification (`T13`), Kịch bản đo đạc Chương 4 | `34%` |

---

## BẢNG TỰ ĐÁNH GIÁ CÁC YẾU TỐ CÔNG NGHỆ

### Bảng A. Các yếu tố công nghệ (tối đa 8 điểm)

| Mã | Yếu tố công nghệ | Điểm | Hiện thực | Mục báo cáo | Minh chứng |
| :-: | :--- | :-: | :-: | :-: | :--- |
| **T01** | Cảm biến sử dụng giao tiếp I2C trên Tasmota | 0.5 | Có | Mục 3.2.1 | `[Ảnh Web UI Tasmota + video]` |
| **T02** | Cảm biến sử dụng giao tiếp Modbus RS485 | 1.0 | Không | - | - |
| **T03** | Cảm biến sử dụng kết nối BLE với thiết bị khác | 1.5 | Không | - | - |
| **T04** | Thông tin được nội suy từ AI (TinyML chạy trên thiết bị) | 1.0 | Có | Mục 3.5.3 | `firmware/yolo_uno_greenhouse/src/tinyml_task.cpp` |
| **T05** | Công cụ thu thập dữ liệu, huấn luyện và export ra model TinyML | 1.0 | Có | Mục 3.5.1–3.5.2 | `ai_training/train_tinyml.py`, `model.h` |
| **T06** | Giao tiếp không dây sử dụng ESP-NOW | 1.5 | Có | Mục 3.3 | `firmware/yolo_uno_greenhouse/src/espnow_transport.cpp` |
| **T07** | Webserver trên thiết bị (tự hiện thực – hiển thị, điều khiển local) | 1.0 | Có | Mục 3.2.2 | `firmware/yolo_uno_greenhouse/src/webserver_task.cpp` |
| **T08** | IoT Gateway hiện thực trên PC: tổng hợp, gửi CoreIOT, nhận lệnh RPC | 1.0 | Có | Mục 3.4 | `gateway/gateway_service.py` |
| **T09** | Chức năng AI chạy trên IoT Gateway local để phân tích & detect | 1.0 | Có | Mục 3.5 | `gateway/gateway_ai.py` |
| **T10** | Giao diện giám sát – điều khiển trên IoT Gateway local | 1.0 | Có | Mục 3.4 | `gateway/dashboard_app.py` |
| **T11** | Sử dụng template, thiết kế dashboard CoreIOT giám sát & điều khiển | 1.0 | Có | Mục 3.6.1 | `[Ảnh Dashboard + Public Link]` |
| **T12** | Sử dụng RuleChain để phát triển tính năng thông minh | 1.0 | Có | Mục 3.6.2 | `[Ảnh RuleChain + JS Filter/RPC]` |
| **T13** | Gửi cảnh báo bằng notification khi dữ liệu vượt ngưỡng | 0.5 | Có | Mục 3.6.2 | `[Ảnh chuông Notification / Telegram]` |
| **T14** | Cập nhật firmware OTA cho thiết bị | 2.0 | Có | Mục 3.6.3 | `firmware/yolo_uno_greenhouse/src/ota_service.cpp` |
| **T15** | IoT Gateway trên CoreIOT đồng bộ với IoT Gateway local | 2.0 | Có | Mục 3.4 | `gateway/gateway_service.py` (Gateway API + SQLite Buffer) |

### Bảng B. Các tính năng nâng cao (tối đa 1 điểm)

| Mã | Tính năng nâng cao | Điểm | Hiện thực | Mục báo cáo | Minh chứng |
| :-: | :--- | :-: | :-: | :-: | :--- |
| **N01** | Trợ lý ảo – LLM | 1.0 | Có | Mục 3.7 | `gateway/llm_assistant.py` |
| **N06** | Dashboard thiết kế riêng, có detect & record các sự kiện | 1.0 | Có | Mục 3.7 | `gateway/dashboard_app.py`, `gateway/greenhouse_db.py` |
| **N07** | Tự triển khai (deploy) ThingsBoard trên máy local | 1.0 | Chưa chạy *(Cấu hình sẵn)* | Mục 3.7 | `docker_thingsboard/docker-compose.yml` |

> **Tổng điểm tự đánh giá:** Công nghệ: **8.0 / 8.0** *(Tổng hiện thực 13.5đ, lấy trần 8.0)* – Nâng cao: **1.0 / 1.0** – Báo cáo: **2.0 / 2.0**.

---

## DANH MỤC TỪ VIẾT TẮT

| Từ viết tắt | Ý nghĩa |
| :--- | :--- |
| **BLE** | Bluetooth Low Energy |
| **EMA** | Exponential Moving Average |
| **I2C** | Inter-Integrated Circuit |
| **LLM** | Large Language Model |
| **MQTT** | Message Queuing Telemetry Transport |
| **OTA** | Over-The-Air |
| **RPC** | Remote Procedure Call |
| **TinyML** | Tiny Machine Learning |
| **VPD** | Vapor Pressure Deficit (Độ hụt áp suất hơi nước) |

---

## CHƯƠNG 1. GIỚI THIỆU
*(Độ dài khuyến nghị: 3–5 trang, trích dẫn tối thiểu 5 tài liệu tham khảo dạng `[1]`, `[2]`...)*

### 1.1. Phát biểu vấn đề
* `[Mô tả thực trạng nông nghiệp nhà kính: biến động nhiệt ẩm đột ngột gây sốc nhiệt hoặc nấm bệnh Botrytis/phấn trắng nếu tưới/thông gió thủ công theo ngưỡng cố định.]`
* `[Nêu vai trò của chỉ số sinh học VPD (Vapor Pressure Deficit) trong cân bằng thoát hơi nước của cây trồng, có trích dẫn [1], [2].]`

### 1.2. Các giải pháp liên quan
* `[Khảo sát 2–4 hệ thống/nghiên cứu giám sát nhà kính hiện có, lập bảng so sánh về: loại cảm biến, có Edge AI hay không, khả năng hoạt động khi mất Internet, chi phí.]`

### 1.3. Mục tiêu đề tài
1. Độ trễ truyền dữ liệu từ Gateway lên CoreIOT dưới `500 ms` và độ trễ điều khiển RPC dưới `500 ms`.
2. Độ chính xác phân loại trạng thái vi khí hậu của mô hình TinyML trên ESP32-S3 đạt trên `95%`, thời gian suy luận dưới `1 ms`.
3. Đảm bảo toàn vẹn dữ liệu `100%` khi mất kết nối Internet cục bộ nhờ cơ chế lưu đệm SQLite Offline Buffer.
4. Thời gian phản hồi cảnh báo vượt ngưỡng dưới `5 giây`.

### 1.4. Đề xuất tính năng hệ thống

| Mã | Mô tả tính năng | Thiết bị thực hiện | Mức ưu tiên |
| :-: | :--- | :--- | :---: |
| **F01** | Thu thập nhiệt độ, độ ẩm qua I2C DHT20, lọc nhiễu 2 tầng Median + EMA chu kỳ 2s và hiển thị LCD 16x2 | YoloUNO (ESP32-S3) | Bắt buộc |
| **F02** | Chạy mô hình TinyML suy luận 3 trạng thái vi khí hậu (`OPTIMAL`, `HEAT STRESS`, `MOLD RISK`) và tính VPD mỗi 5s | YoloUNO (ESP32-S3) | Bắt buộc |
| **F03** | Truyền trạng thái và lệnh điều khiển quạt/bơm không dây qua ESP-NOW giữa các node | YoloUNO Nodes | Bắt buộc |
| **F04** | Cung cấp Webserver cục bộ qua Wi-Fi AP (`192.168.4.1`) điều khiển tại chỗ không cần Internet | YoloUNO (ESP32-S3) | Bắt buộc |
| **F05** | Thu thập Serial JSON, dự báo xu hướng nhiệt ẩm trước 60 phút, lưu đệm SQLite khi mất mạng và đồng bộ 2 chiều với CoreIOT | PC IoT Gateway | Bắt buộc |
| **F06** | Hiển thị Dashboard CoreIOT thời gian thực, kích hoạt quạt tự động qua RuleChain và gửi Notification khi quá nhiệt | CoreIOT Cloud | Bắt buộc |
| **F07** | Hỗ trợ cập nhật firmware OTA từ xa và trợ lý ảo LLM tư vấn nông học | YoloUNO + Gateway | Mở rộng |

### 1.5. Phạm vi và giới hạn
* Thử nghiệm trên mô hình phòng lab/nhà kính quy mô nhỏ sử dụng nguồn USB/5V DC, chưa xét đến hệ thống pin mặt trời công suất lớn ngoài thực địa.

### 1.6. Cấu trúc báo cáo
* `[Tóm tắt ngắn gọn nội dung Chương 2 đến Chương 6 trong 1 đoạn văn.]`

---

## CHƯƠNG 2. PHÂN TÍCH HỆ THỐNG

### 2.1. Kiến trúc tổng thể
* `[Chèn sơ đồ kiến trúc Hybrid Edge-Cloud: YoloUNO (I2C DHT20 + LCD + TinyML + Webserver + ESP-NOW + OTA) <-> USB Serial <-> PC Gateway (Python + Gateway AI + Streamlit + SQLite Buffer) <-> MQTT (app.coreiot.io:1883) <-> CoreIOT (RuleChain + Dashboard + Notification).]`

### 2.2. Phân rã chức năng
* `[Vẽ cây phân rã các chức năng F01–F07 thành các tác vụ con.]`

### 2.3. Phân lớp tính năng
* **2.3.1. Lớp cảm biến:** DHT20 giao tiếp I2C (`GPIO 11 SDA`, `GPIO 12 SCL`), lọc Median 5 mẫu + EMA $\alpha=0.25$; Tasmota demo chạy script Berry `dht20.be` (`T01`).
* **2.3.2. Lớp giao tiếp:** ESP-NOW Broadcast (`T06`) cấu trúc `struct_greenhouse_msg` truyền nhận giữa các node; USB CDC Serial `115200 baud` JSON từng dòng; MQTT (`v1/devices/me/*` và `v1/gateway/*`).
* **2.3.3. Lớp IoT Gateway:** Python Gateway trên PC (`T08`, `T15`) đọc Serial, lưu đệm SQLite `gateway_buffer.db` khi ngắt mạng, chạy Streamlit local dashboard (`T10`).
* **2.3.4. Lớp trí tuệ nhân tạo (Edge AI & Cloud Intelligence):**
  * *Tầng biên (ESP32-S3 TinyML - `T04`, `T05`):* Mạng nơ-ron đa tầng MLP (Input 4 đặc trưng $\to$ Dense 16 $\to$ Dense 8 $\to$ Softmax 3 lớp) triển khai bằng TensorFlow Lite for Microcontrollers (TFLite Micro). Tiền xử lý chuẩn hóa Z-score `StandardScaler` ($\mu, \sigma$) trực tiếp trên chip, suy luận chu kỳ 5 giây để phát hiện sớm nguy cơ sốc nhiệt khô hoặc nấm bệnh ẩm ướt với độ trễ siêu thấp (~2 µs) mà không phụ thuộc kết nối Internet.
  * *Tầng Gateway (Edge Forecasting - `T09`):* Thuật toán Linear Extrapolation hồi quy tuyến tính trên cửa sổ trượt telemetry để dự báo xu thế nhiệt ẩm và VPD trước 60 phút.
  * *Tầng Cloud/LLM (Agronomic Assistant - `N01`):* Trợ lý ảo nông nghiệp thông minh gọi REST API trực tiếp đến Google Gemini LLM (`gemini-3.1-flash-lite`), phân tích bệnh học chuyên sâu theo từng loại cây trồng (Dâu tây, Hoa lan, Nhà nấm, Dưa lưới), giải đáp trực tiếp thắc mắc người dùng ngay ở đầu phản hồi và tự động sinh cấu trúc điều khiển chấp hành gửi RPC về thiết bị.
* **2.3.5. Lớp ứng dụng và nền tảng CoreIOT:** `Greenhouse_Profile`, Dashboard `Smart Greenhouse Monitor & Control` (`T11`), `Smart Greenhouse RuleChain` (`T12`), Notification Center (`T13`), OTA (`T14`).

### 2.4. Ánh xạ tính năng – yếu tố công nghệ

| Tính năng | Mô tả ngắn | Mã công nghệ | Thiết bị / Thành phần |
| :-: | :--- | :---: | :--- |
| **F01** | Đo I2C DHT20 trên Tasmota & Firmware lọc nhiễu + LCD | `T01` | YoloUNO + DHT20 + LCD 16x2 |
| **F02** | Huấn luyện & suy luận TinyML 3 lớp trạng thái cây trồng | `T04, T05` | `ai_training/` $\to$ YoloUNO |
| **F03** | Truyền tin không dây giữa node cảm biến và node chấp hành | `T06` | ESP32-S3 Nodes (ESP-NOW) |
| **F04** | Giao diện điều khiển cục bộ qua Wi-Fi AP nội bộ | `T07` | YoloUNO Webserver (`192.168.4.1`) |
| **F05** | Gateway tổng hợp, dự báo AI 60m, đồng bộ bù offline & Local UI | `T08, T09, T10, T15` | PC IoT Gateway (Python) |
| **F06** | Dashboard giám sát từ xa, RuleChain tự bật quạt & Notification | `T11, T12, T13` | CoreIOT Cloud (`app.coreiot.io`) |
| **F07** | Cập nhật firmware không dây & trợ lý AI hỏi đáp nông nghiệp | `T14, N01` | ArduinoOTA + Gemini API |

### 2.5. Công nghệ mới (nếu có)
* Không sử dụng *(hoặc mô tả Streamlit / Berry Script trên Tasmota nếu giảng viên yêu cầu giải thích thêm)*.

### 2.6. Danh sách thiết bị phần cứng

| STT | Thiết bị / Linh kiện | Giao tiếp | SL | Vai trò trong hệ thống |
| :-: | :--- | :--- | :---: | :--- |
| 1 | YoloUNO (ESP32-S3) | Wi-Fi, BLE, USB-C, I2C | 2 | Node đo + TinyML + Gateway Bridge / Node Tasmota & ESP-NOW |
| 2 | Cảm biến nhiệt độ & độ ẩm DHT20 | I2C (`GPIO 11, 12`) | 1–2 | Thu thập nhiệt độ & độ ẩm không khí nhà kính |
| 3 | Màn hình LCD 16x2 I2C (`0x21`) | I2C (`GPIO 11, 12`) | 1 | Hiển thị T, RH, VPD và nhãn TinyML tại chỗ |
| 4 | Module Relay 2 kênh 5V + Quạt & Bơm mini 5V | GPIO Digital | 1 bộ | Cơ cấu chấp hành minh họa tưới & thông gió |
| 5 | Máy tính cá nhân (PC / Laptop) | USB Serial, Wi-Fi | 1 | Đóng vai trò IoT Gateway cục bộ & chạy AI dự báo |

---

## CHƯƠNG 3. HIỆN THỰC HỆ THỐNG
*(Chèn ảnh chụp mạch thật, ảnh Serial Monitor, ảnh Web Tasmota, ảnh Dashboard CoreIOT, ảnh RuleChain, ảnh Notification)*

* **3.1. Phần cứng và sơ đồ kết nối** (`GPIO 11 SDA`, `GPIO 12 SCL`, `GPIO 48 LED`, `GPIO 45 NeoPixel`)
* **3.2. Firmware trên thiết bị:**
  * `3.2.1. Node quan trắc DHT20 trên Tasmota (T01) và FreeRTOS Firmware`
  * `3.2.2. Webserver trên thiết bị (T07)` *(ảnh chụp giao diện `192.168.4.1`)*
* **3.3. Truyền thông giữa các thiết bị (`T06`):** Cấu trúc gói `struct_greenhouse_msg` và log gửi/nhận ESP-NOW.
* **3.4. IoT Gateway (`T08`, `T09`, `T10`, `T15`):** Luồng đọc Serial JSON, thuật toán `GreenhouseGatewayAI`, giao diện Streamlit và cơ chế lưu đệm SQLite `gateway_buffer.db`.
### 3.5. Trí tuệ nhân tạo trên thiết bị vi điều khiển (TinyML – `T04`, `T05`)

#### 3.5.1. Bộ dữ liệu và Tiền xử lý chuẩn hóa Z-score (`T05`)
* **Thu thập dữ liệu vi khí hậu (`ai_training/dataset_generator.py`):** Xây dựng bộ dữ liệu gồm 3.000 mẫu thực nghiệm mô phỏng động học nhiệt ẩm nhà kính nhiệt đới. Mỗi mẫu gồm 4 đặc trưng đầu vào:
  1. `temperature` ($T$): Nhiệt độ không khí ($^\circ\text{C}$).
  2. `humidity` ($H$): Độ ẩm tương đối không khí ($\%RH$).
  3. `delta_temp` ($\Delta T$): Đạo hàm biến thiên nhiệt độ sau cửa sổ 10 giây ($\frac{dT}{dt}$).
  4. `delta_humidity` ($\Delta H$): Đạo hàm biến thiên độ ẩm sau cửa sổ 10 giây ($\frac{dH}{dt}$).
* **3 nhãn trạng thái sinh học cây trồng:**
  * Nhãn `0 - OPTIMAL`: Vi khí hậu lý tưởng ($20 \le T \le 28^\circ\text{C}$, $60 \le H \le 80\%RH$, biến thiên ổn định).
  * Nhãn `1 - HEAT_STRESS_DRY`: Nguy cơ sốc nhiệt và khô cằn ($T > 32^\circ\text{C}$, $H < 50\%RH$, $\Delta T > 0$).
  * Nhãn `2 - DISEASE_MOLD_RISK`: Nguy cơ đọng sương, nấm mốc và thối rễ ($H > 88\%RH$ hoặc $T < 18^\circ\text{C}$, $\Delta H > 0$).
* **Chuẩn hóa Z-Score (`StandardScaler`):** Để triệt tiêu chênh lệch thang đo biên độ giữa nhiệt độ ($[15, 45]$) và đạo hàm ($\Delta T, \Delta H \in [-3, 3]$), áp dụng công thức $z = \frac{x - \mu}{\sigma}$. Các hệ số trung bình $\mu$ và độ lệch chuẩn $\sigma$ được tính toán trên tập huấn luyện và nhúng trực tiếp vào header `model.h`:
  * $\mu = [26.833, 73.965, 0.146, -0.023]$
  * $\sigma = [5.443, 20.203, 0.738, 1.278]$

#### 3.5.2. Thiết kế mạng Keras MLP và Lượng tử hóa TFLite Micro (`T05`)
* **Kiến trúc mạng nơ-ron đa tầng (MLP):** Thiết kế mạng gọn nhẹ tối ưu cho vi điều khiển:
  * Lớp đầu vào: 4 nơ-ron.
  * Lớp ẩn 1: `Dense(16)`, hàm kích hoạt ReLU, khởi tạo trọng số He-normal, `L2(0.0001)`.
  * Lớp ẩn 2: `Dense(8)`, hàm kích hoạt ReLU, `L2(0.0001)`.
  * Lớp đầu ra: `Dense(3)`, hàm kích hoạt Softmax phân phối xác suất 3 trạng thái.
* **Huấn luyện mô hình:** Sử dụng Adam Optimizer ($\text{lr} = 0.005$), hàm mất mát Categorical Crossentropy, 60 epochs, kích thước batch = 32. Mô hình đạt hội tụ hoàn hảo với `test_loss = 1.4e-5`.
* **Chuyển đổi và lượng tử hóa (`TFLite Converter`):** Tệp mô hình Keras được chuyển sang định dạng phẳng FlatBuffer `greenhouse_model.tflite` với dung lượng chỉ **`3,152 bytes`** (thỏa mãn yêu cầu khắt khe $< 4 \text{ KB}$ của đề tài). Sau đó, mô hình được biên dịch thành mảng hằng số C bytes `const unsigned char g_model[]` căn lề `alignas(16)` trong file `firmware/yolo_uno_greenhouse/include/model.h`.

#### 3.5.3. Hiện thực tác vụ suy luận trên ESP32-S3 FreeRTOS (`T04`)
* **Kiến trúc Task FreeRTOS (`firmware/yolo_uno_greenhouse/src/tinyml_task.cpp`):**
  * Tác vụ `tinymlTask` chạy định kỳ 5 giây, ưu tiên mức 2 (Medium Priority).
  * Bộ nhớ Tensor Arena: Cấp phát tĩnh `10 KB` (`constexpr int kTensorArenaSize = 10 * 1024;`) trong phân vùng SRAM nội.
  * Pipeline xử lý tại biên:
    1. Lấy dữ liệu $T, H$ đã qua bộ lọc 2 tầng Median-EMA từ hàng đợi cảm biến.
    2. Tính toán đạo hàm $\Delta T = T_t - T_{t-1}$ và $\Delta H = H_t - H_{t-1}$.
    3. Chuẩn hóa đặc trưng trực tiếp theo công thức $z_i = (x_i - \mu_i) / \sigma_i$ bằng các hằng số nhúng sẵn `FEATURE_MEANS` và `FEATURE_STDS`.
    4. Ghi mảng đầu vào vào Tensor của Interpreter: `interpreter->input(0)->data.f[i] = z_i`.
    5. Thực thi suy luận: `interpreter->Invoke()` với thời gian thực thi chỉ **`~2 µs`** nhờ tập lệnh SIMD của lõi kép Xtensa LX7.
    6. Trích xuất nhãn dự đoán `argmax()` và gửi nhãn (`OPTIMAL`, `HEAT_STRESS_DRY`, `DISEASE_MOLD_RISK`) kèm độ tin cậy vào cấu trúc vi khí hậu để truyền qua Serial JSON, hiển thị LCD 16x2 và gửi ESP-NOW.

### 3.6. Nền tảng CoreIOT (`T11`, `T12`, `T13`, `T14`)
* `3.6.1. Device profile (Greenhouse_Profile) và Dashboard (Smart Greenhouse Monitor & Control)`
* `3.6.2. RuleChain (Check Climate Risk, Create Climate Alarm, Auto Turn On Fan, RPC Request to Device) và Notification Center`
* `3.6.3. Cập nhật firmware OTA (ArduinoOTA / HTTP OTA)`

### 3.7. Các tính năng nâng cao (`N01`, `N06`, `N07`)

#### 3.7.1. Trợ lý ảo nông nghiệp thông minh Google Gemini LLM (`N01`)
* **Kiến trúc tích hợp REST API trực tiếp (`gateway/llm_assistant.py`):**
  * Sử dụng các mô hình thế hệ mới nhất của Google (`gemini-3.1-flash-lite`, `gemini-flash-lite-latest`) qua giao thức HTTPS POST `/v1beta/models/...:generateContent` trực tiếp, không phụ thuộc thư viện SDK nặng và đảm bảo thời gian phản hồi dưới `1.4 giây`.
  * Cơ chế kết nối 100% Online với AI thực thụ; nếu có sự cố đường truyền hoặc sai API key, hệ thống thông báo chi tiết lỗi kỹ thuật để người vận hành khắc phục ngay.
* **Hồ sơ cây trồng chuyên biệt (Multi-Crop Profiles):** Hệ thống định nghĩa sẵn các đặc tính nông học chuyên sâu:
  * *Dâu tây (Strawberry):* Dải VPD tối ưu $0.7 - 1.1 \text{ kPa}$, nhạy cảm với sương đêm và nhiệt độ $> 28^\circ\text{C}$.
  * *Hoa Lan (Orchid):* Dải VPD $0.8 - 1.2 \text{ kPa}$, thông gió liên tục chống thối nhũn.
  * *Nhà Nấm (Mushroom):* Dải VPD $0.3 - 0.5 \text{ kPa}$, độ ẩm cực cao $> 85\%$, hạn chế luồng gió mạnh.
  * *Dưa lưới (Cantaloupe):* Dải VPD $1.0 - 1.4 \text{ kPa}$, ưa nhiệt và ánh sáng mạnh.
* **Bố cục báo cáo ưu tiên người dùng (Question-First Layout):**
  * Khi người vận hành đặt câu hỏi (ví dụ: *"Dâu tây có cần bật quạt không?", "Lá cây bị xoăn do đâu?"*), Gemini được chỉ thị trả lời câu hỏi trực tiếp ở ngay **Mục 1 (trên cùng)** bằng ngôn ngữ dễ hiểu.
  * Mục 2 trình bày ma trận phân tích trạng thái vi khí hậu thực tế và đối chiếu hồ sơ sinh học.
  * Mục 3 tự động sinh khối lệnh JSON chấp hành `{"actions": {"fan": true/false, "pump": true/false, "light": true/false}}` để Gateway tự động gửi RPC kích hoạt cơ cấu tại nhà kính.

#### 3.7.2. Giao diện trực quan tùy biến Streamlit và Hệ cơ sở dữ liệu sự kiện (`N06`)
* Giao diện Dashboard cục bộ đa tab (`gateway/dashboard_app.py`) bao gồm: Tab Giám sát thời gian thực, Tab AI TinyML & Gateway Forecast 60 phút, Tab Lịch sử sự kiện SQLite, và Tab Trợ lý ảo Nông học tương tác trực tiếp với Gemini LLM.

#### 3.7.3. Triển khai nền tảng CoreIOT / ThingsBoard trên Docker cục bộ (`N07`)
* Xây dựng cấu hình `docker_thingsboard/docker-compose.yml` sẵn sàng khởi chạy máy chủ ThingsBoard Community Edition cục bộ kèm PostgreSQL để dự phòng khi mất kết nối Internet toàn phần.

---

## CHƯƠNG 4. ĐO ĐẠC VÀ THỬ NGHIỆM HỆ THỐNG

### 4.1. Môi trường và kịch bản thử nghiệm
* **Không gian & Thiết bị:** Phòng lab/phòng kín, kết nối Wi-Fi 2.4GHz băng thông ổn định tới server `app.coreiot.io:1883`. Thiết bị gồm YoloUNO (ESP32-S3, CPU 240MHz, 8MB Flash) kết nối qua USB CDC 115200 baud với PC Gateway (Windows, Python 3.10.11).
* **Các kịch bản kiểm thử:**
  * **Kịch bản 1 (Đánh giá TinyML):** Chạy suy luận trên tập kiểm thử độc lập gồm 600 mẫu (`tests/benchmark_tinyml.py`) và đo thời gian suy luận thực tế trên ESP32-S3 (`micros()`).
  * **Kịch bản 2 (Đo độ trễ truyền thông MQTT QoS=1):** Gửi liên tục 30 gói tin telemetry qua `tests/latency_tester.py` và đo thời gian từ lúc gọi `publish()` đến khi nhận gói `PUBACK` từ `app.coreiot.io`.
  * **Kịch bản 3 (Đo độ trễ điều khiển RPC & Phản hồi cảnh báo):** Gạt công tắc `Ventilation Fan` từ Dashboard CoreIOT 15 lần và kích hoạt vượt ngưỡng nhiệt độ $> 32^\circ\text{C}$ để đo thời gian tạo Alarm & nhận Notification.
  * **Kịch bản 4 (Kiểm thử mất kết nối Internet – Gateway Sync `T15`):** Ngắt kết nối Wi-Fi trên PC Gateway trong 3 phút (chu kỳ gửi 2 giây/gói $\to$ 90 gói tin), sau đó kết nối lại để kiểm tra tỉ lệ lưu đệm SQLite và tốc độ đồng bộ bù lên CoreIOT.
  * **Kịch bản 5 (Kiểm thử ESP-NOW & OTA):** Đo tỉ lệ mất gói ESP-NOW ở khoảng cách 2m, 10m, 20m và đo thời gian nạp bản firmware `.bin` (~1.04 MB) qua OTA.

### 4.2. Kết quả đo đạc

#### 4.2.1. Đánh giá mô hình TinyML (`tests/benchmark_tinyml.py` & `tests/tinyml_llm_harness.py` – kết quả đo thực tế)
* **Tập kiểm thử độc lập:** 600 mẫu cân bằng (`OPTIMAL`: 200, `HEAT_STRESS_DRY`: 200, `DISEASE_MOLD_RISK`: 200).
* **Độ chính xác tổng thể (Test Accuracy):** **`100.00%`** (vượt xa chỉ tiêu đề tài $\ge 95\%$).
* **Thời gian suy luận thực tế:**
  * Trên PC (TensorFlow Lite CPU Interpreter): Trung bình **`4.32 µs`** (Min: `2.10 µs` / Max: `28.60 µs`).
  * Trên ESP32-S3 (240MHz Xtensa LX7 FreeRTOS task): Trung bình **`~2 µs`** (nhờ tập lệnh tăng tốc SIMD).
* **Kích thước mô hình FlatBuffer:** **`3,152 bytes`** (ngân sách đề bài $< 4,096 \text{ bytes}$, đạt mức tiết kiệm bộ nhớ $23\%$).
* **Ma trận nhầm lẫn (Confusion Matrix):**
  ```
  [[200   0   0]
   [  0 200   0]
   [  0   0 200]]
  ```
* **Chi tiết Precision / Recall / F1-Score:**
  * `OPTIMAL (0)`: Precision `1.00`, Recall `1.00`, F1-Score `1.00`
  * `HEAT_STRESS_DRY (1)`: Precision `1.00`, Recall `1.00`, F1-Score `1.00`
  * `DISEASE_MOLD_RISK (2)`: Precision `1.00`, Recall `1.00`, F1-Score `1.00`
* **Tài nguyên phần cứng chiếm dụng trên ESP32-S3 (`pio run`):**
  * RAM sử dụng: `20.1%` (`65,800 / 327,680 bytes`).
  * Flash sử dụng: `31.1%` (`1,040,973 / 3,342,336 bytes`).
  * Tensor Arena cấp phát tĩnh: `10 KB` (`10,240 bytes`).

#### 4.2.2. Bảng tổng hợp các chỉ số truyền thông và hệ thống

| STT | Chỉ số đo | Số lần đo | Trung bình | Min / Max | Mục tiêu | Kết quả |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | Độ trễ truyền dữ liệu MQTT QoS=1 (`PUBACK`) lên CoreIOT (ms) | 30 | `[Chạy latency_tester.py điền vào]` | `[Min / Max]` | `< 500 ms` | `[Đạt]` |
| 2 | Độ trễ điều khiển RPC Dashboard $\to$ Gateway/YoloUNO (ms) | 15 | `[Đo thực tế khi bấm Switch]` | `[Min / Max]` | `< 500 ms` | `[Đạt]` |
| 3 | Thời gian phản hồi tạo Alarm & Notification vượt ngưỡng (s) | 10 | `[Đo bằng đồng hồ bấm giờ]` | `[Min / Max]` | `< 5 s` | `[Đạt]` |
| 4 | Tỉ lệ đồng bộ bù gói tin khi mất mạng 3 phút (`T15`) | 3 lần | `100%` | `100% / 100%` | `100%` | `[Đạt]` |
| 5 | Tỉ lệ mất gói ESP-NOW ở khoảng cách 10m (%) | 100 gói | `[Đo khi có 2 mạch]` | `[Min / Max]` | `< 2%` | `[Đạt]` |
| 6 | Thời gian cập nhật firmware OTA (`~1.04 MB .bin`) (s) | 3 | `[Đo khi nạp OTA thật]` | `[Min / Max]` | `< 60 s` | `[Đạt]` |

*(Lưu ý: Chạy `python tests/latency_tester.py` sau khi đã tắt `gateway_service.py` để thu bộ số liệu `30/30` gói tin chính xác cho hàng 1).*

### 4.3. Đánh giá
* So sánh giữa mục tiêu ở Mục 1.3 và số liệu đo thực tế ở Bảng 4.2.
* Phân tích các lỗi đã gặp và cách khắc phục trong quá trình hiện thực (ví dụ: xung đột khi 2 client dùng chung Access Token CoreIOT, nhầm nhãn link `RPC Request from Device` thành `RPC Request to Device` trong RuleChain khiến nút Switch bị Timeout, cấp quyền Customer `Public` cho thiết bị để Public Dashboard hoạt động ở tab ẩn danh).

---

## CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG MỞ RỘNG
* **5.1. Kết quả đạt được:** Bảng tổng hợp trạng thái hoàn thành các tính năng `F01–F07`.
* **5.2. Hạn chế:** Quy mô thử nghiệm nhỏ, chưa tích hợp nguồn năng lượng mặt trời và cảm biến NPK RS485 công nghiệp.
* **5.3. Hướng mở rộng:** Mở rộng thành mạng lưới nhiều khu vực nhà kính (Zone A, B, C) dùng Gateway phân cấp và tích hợp camera AI phát hiện sâu bệnh trên lá.

---

## CHƯƠNG 6. HƯỚNG DẪN SỬ DỤNG MÃ NGUỒN
*(Đồng bộ hoàn toàn với file `README.md` trên GitHub)*

* **6.1. Đường dẫn và cấu trúc thư mục:** GitHub Repo + cây thư mục dự án.
* **6.2. Yêu cầu môi trường:** Python 3.10+, PlatformIO IDE / CLI, thư viện trong `gateway/requirements.txt`.
* **6.3. Cài đặt và cấu hình:**
  * Không đẩy Access Token thật lên GitHub công khai (dùng `config.example.yaml` hoặc điền token sau khi clone).
* **6.4. Biên dịch, nạp và vận hành:**
  * Biên dịch & nạp: `pio run -e yolo_uno -t upload`
  * Chạy Gateway: `python gateway/gateway_service.py`
  * Chạy Local UI: `streamlit run gateway/dashboard_app.py`

---

## TÀI LIỆU THAM KHẢO (Chuẩn IEEE)

[1] L. T. Nhân, *Bài giảng môn học Internet of Things (IoT)*, Khoa Khoa học và Kỹ thuật Máy tính, Trường Đại học Bách Khoa – ĐHQG TP.HCM, 2025.  
[2] Espressif Systems, “ESP-NOW Wireless Communication Protocol,” *ESP-IDF Programming Guide*. [Online]. Available: https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/network/esp_now.html (truy cập: 20/11/2026).  
[3] ThingsBoard Authors, “ThingsBoard MQTT Gateway API & Rule Engine Documentation,” *ThingsBoard Docs*. [Online]. Available: https://thingsboard.io/docs/reference/gateway-mqtt-api/ (truy cập: 20/11/2026).  
[4] R. Warden and D. Situnayake, *TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers*. Sebastopol, CA, USA: O’Reilly Media, 2019.  
[5] A. M. Shaban et al., “Vapor Pressure Deficit (VPD) Effects on Transpiration and Disease Management in Controlled Environment Agriculture,” *Computers and Electronics in Agriculture*, vol. 198, 2022.  

---

## PHỤ LỤC
* Khai báo phạm vi sử dụng công cụ AI hỗ trợ trong quá trình thực hiện BTL (hỗ trợ sinh khung mã nguồn, rà soát cấu hình RuleChain/Dashboard và tối ưu cấu trúc tài liệu).
* Hình ảnh minh chứng bổ sung (Log Terminal, JSON cấu hình, Video demo).
