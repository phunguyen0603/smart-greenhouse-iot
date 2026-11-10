# Trạm Quan Trắc & Điều Khiển Nông Nghiệp Công Nghệ Cao (Smart Greenhouse)
> **Môn học**: Internet of Things (IoT) - Học kỳ 261 (Năm học 2025–2026)  
> **Trường**: Đại học Bách Khoa - ĐHQG TP. Hồ Chí Minh  
> **Giảng viên hướng dẫn**: TS. Lê Trọng Nhân (`trongnhanle@hcmut.edu.vn`)

---

## 1. Giới thiệu tổng quan
Hệ thống **Smart Greenhouse** là giải pháp IoT toàn diện ứng dụng mô hình đo lường nông nghiệp chuẩn quốc tế và **Trí tuệ nhân tạo tại biên (TinyML / Edge AI)** để tự động hóa giám sát và điều hòa vi khí hậu nhà kính:
- Đo đạc thông số thực tế: **Nhiệt độ ($T$)** và **Độ ẩm ($RH$)** qua cảm biến I2C DHT20.
- Lọc tín hiệu số 2 tầng: **Median Filter (5 mẫu)** khử nhiễu xung gai + **Exponential Moving Average ($\alpha=0.25$)** làm mượt xu hướng (kế thừa LAB 3).
- **Edge AI (TinyML)** trên ESP32-S3: Nội suy chỉ số **Độ hụt áp suất hơi (VPD - Vapor Pressure Deficit)** và phân loại trạng thái sức khỏe nhà kính (`OPTIMAL`, `HEAT_STRESS_DRY`, `DISEASE_MOLD_RISK`) trong thời gian suy luận chỉ **2.2 us**, độ chính xác **99.00%**.
- **IoT Gateway PC**: Cầu nối hai chiều MQTT lên nền tảng **CoreIOT**, tích hợp thuật toán AI dự báo xu hướng vi khí hậu trước 1 giờ và giao diện giám sát máy tính cục bộ **Streamlit**.
- **Hạ tầng đám mây CoreIOT**: RuleChain kích hoạt logic điều khiển tự động khi phát hiện rủi ro và gửi thông báo khẩn cấp tức thời về **Telegram Bot**.
- **Trợ lý chuyên gia AI Gemini (LLM)**: Tư vấn nông nghiệp và phân tích sinh lý cây trồng bằng ngôn ngữ tự nhiên.

---

## 2. Bảng Tự Đánh Giá Yếu Tố Công Nghệ (Điểm mục tiêu: 10/10)

| Nhóm | Mã | Yếu tố công nghệ | Hiện thực trong đề tài | Vị trí mã nguồn | Điểm |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **Cảm biến** | **T01** | Cảm biến I2C trên Tasmota | Nạp Tasmota lên YoloUNO, dùng script Berry `dht20.be` đọc DHT20 I2C, Web UI và gửi telemetry | `firmware/tasmota_demo/` | **0.5** |
| **TinyML** | **T04** | TinyML suy luận trên thiết bị | Chạy TFLite Micro trên ESP32-S3 phân loại vi khí hậu 3 lớp, chu kỳ 5s | `firmware/yolo_uno_greenhouse/src/tinyml_task.cpp` | **1.0** |
| | **T05** | Thu thập, train, export TinyML | Script sinh 3.000 mẫu dataset, notebook train Keras, lượng tử hóa và xuất `model.h` | `ai_training/` | **1.0** |
| **Cục bộ** | **T06** | Giao tiếp không dây ESP-NOW | Truyền telemetry và lệnh điều khiển broadcast tốc độ cao giữa các node | `firmware/yolo_uno_greenhouse/src/espnow_transport.cpp` | **1.5** |
| | **T07** | Webserver trên thiết bị | ESP32-S3 host trang web HTML5/CSS nội bộ: xem số liệu, chỉnh ngưỡng và điều khiển local | `firmware/yolo_uno_greenhouse/src/webserver_task.cpp` | **1.0** |
| **IoT Gateway** | **T08** | IoT Gateway trên PC | Script Python cầu nối Serial/MQTT với CoreIOT, phân phối lệnh RPC xuống node | `gateway/gateway_service.py` | **1.0** |
| | **T09** | AI chạy trên IoT Gateway | Dự báo chuỗi thời gian nhiệt ẩm trước 1 giờ, phát hiện sớm sốc nhiệt và đọng sương | `gateway/gateway_ai.py` | **1.0** |
| | **T10** | Giao diện giám sát trên Gateway | Dashboard cục bộ bằng Streamlit trên máy tính, biểu đồ thời gian thực, điều khiển offline | `gateway/dashboard_app.py` | **1.0** |
| **CoreIOT** | **T11** | Template & Dashboard CoreIOT | Thiết kế giao diện Dashboard: Gauges đo nhiệt ẩm, biểu đồ lịch sử, widget TinyML, switch RPC | `coreiot/dashboard_greenhouse.json` | **1.0** |
| | **T12** | RuleChain CoreIOT | Tự động hóa: Nếu TinyML cảnh báo rủi ro $\implies$ tự động gửi RPC bật quạt hoặc bơm | `coreiot/rulechain_greenhouse.json` | **1.0** |
| | **T13** | Notification vượt ngưỡng | Gửi tin nhắn cảnh báo tức thời qua Telegram Bot từ RuleChain | `coreiot/rulechain_greenhouse.json` | **0.5** |
| | **T14** | Cập nhật firmware OTA | Hỗ trợ nạp firmware từ xa qua Wi-Fi bằng ArduinoOTA và HTTP Update | `firmware/yolo_uno_greenhouse/src/ota_service.cpp` | **2.0** |
| **TỔNG CÔNG NGHỆ** | | *(Lấy trần tối đa 8.0)* | **Tổng điểm các yếu tố đã hiện thực: 11.5 điểm $\implies$ Đạt tối đa** | | **8.0 / 8.0** |
| **Nâng cao** | **N01** | Trợ lý ảo LLM | Tích hợp Google Gemini AI chẩn đoán sức khỏe cây trồng và tư vấn canh tác | `gateway/llm_assistant.py` | **1.0** |
| | **N07** | Tự deploy ThingsBoard local | File `docker-compose.yml` triển khai ThingsBoard Community Edition độc lập | `docker_thingsboard/docker-compose.yml` | **(1.0)** |
| **Báo cáo** | - | Báo cáo chuẩn mẫu | 6 chương đầy đủ minh chứng, bảng tự đánh giá, trích dẫn $\ge 5$ tài liệu IEEE | `BaoCaoMau_BaiTapLon_IoT.docx` | **2.0 / 2.0** |
| **TỔNG KẾT** | | | **ĐẠT ĐIỂM TỐI ĐA** | | **10.0 / 10.0** |

---

## 3. Cấu trúc thư mục dự án
```
Assignment/
├── ai_training/                         # [T05] Huấn luyện và xuất mô hình TinyML
│   ├── dataset_generator.py             # Sinh bộ dữ liệu vi khí hậu nhà kính chuẩn VPD
│   ├── train_tinyml.py                  # Huấn luyện mô hình Keras & xuất C header model.h
│   ├── greenhouse_sensor_data.csv       # Bộ dữ liệu 3.000 mẫu
│   ├── greenhouse_model.tflite          # File mô hình TFLite (3.2 KB)
│   ├── model.h                          # Mảng byte mô hình C
│   └── training_metrics.json            # Số liệu đánh giá cho Báo cáo
├── firmware/
│   ├── yolo_uno_greenhouse/             # [T04, T06, T07, T14] Firmware PlatformIO cho ESP32-S3
│   │   ├── platformio.ini               # Cấu hình PlatformIO board yolo_uno
│   │   ├── boards/yolo_uno.json         # Định nghĩa phần cứng board YoloUNO
│   │   ├── lib/                         # Driver I2C kế thừa từ Support Files LAB 3
│   │   │   ├── DHT20/                   # Driver cảm biến DHT20
│   │   │   └── LCD/                     # Driver LiquidCrystal_I2C (Địa chỉ 33 = 0x21)
│   │   ├── include/
│   │   │   ├── global.h                 # Biến toàn cục FreeRTOS
│   │   │   ├── greenhouse_profile.h     # Hồ sơ vi khí hậu cây trồng/nấm
│   │   │   ├── sensor_lcd_task.h        # Task đọc DHT20 (lọc 2 tầng) & LCD 16x2
│   │   │   ├── tinyml_task.h            # Task TFLite Micro suy luận AI
│   │   │   ├── webserver_task.h         # Task Webserver local tại chỗ (T07)
│   │   │   ├── espnow_transport.h       # Giao tiếp ESP-NOW (T06)
│   │   │   ├── ota_service.h            # Cập nhật OTA từ xa (T14)
│   │   │   └── model.h                  # Header mô hình TinyML
│   │   └── src/
│   │       ├── main.cpp                 # Khởi tạo FreeRTOS đa nhiệm
│   │       ├── global.cpp
│   │       ├── sensor_lcd_task.cpp
│   │       ├── tinyml_task.cpp
│   │       ├── webserver_task.cpp
│   │       ├── espnow_transport.cpp
│   │       └── ota_service.cpp
│   └── tasmota_demo/                    # [T01] Script Berry & cấu hình Tasmota
│       ├── dht20.be                     # Script Berry đọc DHT20 qua I2C
│       └── tasmota_guide.md             # Hướng dẫn nạp và minh chứng T01
├── gateway/                             # [T08, T09, T10, N01] IoT Gateway Python trên PC
│   ├── config.yaml                      # Cấu hình Broker, Token, Serial
│   ├── gateway_service.py               # Gateway core: Cầu nối Serial/MQTT với CoreIOT
│   ├── gateway_ai.py                    # [T09] Thuật toán AI dự báo trước 1 giờ
│   ├── dashboard_app.py                 # [T10] Giao diện Streamlit giám sát & điều khiển local
│   ├── llm_assistant.py                 # [N01] Trợ lý ảo AI Gemini chẩn đoán sức khỏe nhà kính
│   └── requirements.txt                 # Danh sách thư viện Python
├── coreiot/                             # [T11, T12, T13] Cấu hình CoreIOT
│   ├── dashboard_greenhouse.json        # Template Dashboard CoreIOT
│   └── rulechain_greenhouse.json        # File JSON import RuleChain xử lý tự động & Telegram
├── docker_thingsboard/                  # [N07] Tự triển khai ThingsBoard Local
│   └── docker-compose.yml               # Docker Compose ThingsBoard CE & PostgreSQL
├── tests/                               # [Chương 4 Báo cáo] Đo đạc và thử nghiệm
│   ├── benchmark_tinyml.py              # Đánh giá Accuracy (99%), Latency (2.2 us), F1-Score
│   └── latency_tester.py                # Đo độ trễ truyền thông end-to-end
└── README.md                            # Tài liệu hướng dẫn toàn diện
```

---

## 4. Hướng dẫn cài đặt & Vận hành

### 4.1. Môi trường & Thư viện Python
Cài đặt các gói phụ thuộc trên PC:
```bash
pip install -r gateway/requirements.txt
```

### 4.2. Huấn luyện & Đánh giá TinyML (T04, T05)
Chạy script sinh dữ liệu và huấn luyện mô hình:
```bash
python ai_training/dataset_generator.py
python ai_training/train_tinyml.py
python tests/benchmark_tinyml.py
```

### 4.3. Biên dịch và nạp Firmware lên ESP32-S3 YoloUNO
Sử dụng PlatformIO trong VS Code hoặc qua CLI:
```bash
cd firmware/yolo_uno_greenhouse
pio run -e yolo_uno -t upload
pio device monitor -b 115200
```
- Khi khởi động, màn hình LCD 16x2 sẽ hiển thị nhiệt độ, độ ẩm và nhãn chẩn đoán TinyML (`OPT`, `DRY`, `MLD`).
- ESP32 tự động phát Wi-Fi Access Point `SmartGreenhouse-AP` (mật khẩu `12345678`). Truy cập `192.168.4.1` trên điện thoại/laptop để vào Webserver cục bộ.

### 4.4. Khởi chạy IoT Gateway & Dashboard Local (T08, T09, T10)
1. Cấu hình access token trong file `gateway/config.yaml`.
2. Khởi chạy Gateway MQTT Bridge:
   ```bash
   python gateway/gateway_service.py
   ```
3. Khởi chạy Giao diện Dashboard Streamlit:
   ```bash
   streamlit run gateway/dashboard_app.py
   ```

### 4.5. Nhập Cấu hình lên CoreIOT (T11, T12, T13)
1. Đăng nhập vào [app.coreiot.io](https://app.coreiot.io).
2. Vào **Rule Chains** $\to$ Bấm **Import Rule Chain** $\to$ Chọn file `coreiot/rulechain_greenhouse.json` $\to$ Cấu hình Bot Token & Chat ID Telegram.
3. Vào **Dashboards** $\to$ Bấm **Import Dashboard** $\to$ Chọn file `coreiot/dashboard_greenhouse.json`.
