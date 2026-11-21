# ĐÁNH GIÁ & ĐỊNH HƯỚNG TRIỂN KHAI ĐỀ TÀI BÀI TẬP LỚN IOT (HK261)

* **Môn học:** Internet of Things (IoT) – Học kỳ 261 (Năm học 2025 – 2026)  
* **Đơn vị:** Khoa Khoa học và Kỹ thuật Máy tính – Trường Đại học Bách Khoa, ĐHQG-HCM  
* **Giảng viên phụ trách:** TS. Lê Trọng Nhân  
* **Đề tài đánh giá:** **Hệ thống quan trắc và điều khiển nông nghiệp công nghệ cao (Smart Greenhouse)**  
* **Nền tảng bắt buộc:** Mạch lập trình ESP32-S3 (YoloUNO) & Nền tảng CoreIOT (ThingsBoard based)  

---

## 1. TỔNG QUAN ĐỀ TÀI & CHIẾN LƯỢC ĐIỂM SỐ

### 1.1. Công thức tính điểm quy định
$$\text{Điểm BTL} = \min(8; \sum \text{Công nghệ}) + \text{Báo cáo } (\le 2) + \min(1; \sum \text{Nâng cao})$$

* **Yêu cầu công nghệ cốt lõi:** Chọn các yếu tố trong danh mục **T01 – T15** sao cho tổng điểm $\ge 8.0$ điểm (điểm tối đa đạt được là 8.0).
* **Báo cáo chuẩn mực:** Tối đa 2.0 điểm, tuân thủ nghiêm ngặt khung `BaoCaoMau_BaiTapLon_IoT.docx` (tối thiểu 5 tài liệu tham khảo chuẩn IEEE, phân tích phân lớp, số liệu đo đạc thực nghiệm).
* **Tính năng nâng cao (Bonus):** Chọn từ **N01 – N07** để lấy trọn vẹn 1.0 điểm cộng.
* **Mục tiêu điểm số:** **10.0 / 10.0**.

### 1.2. Đánh giá độ phù hợp của đề tài Smart Greenhouse
* **Điểm đánh giá đề tài:** **9.5 / 10** (Rất xuất sắc).
* **Lý do lựa chọn:** Đề tài nông nghiệp nhà kính thông minh là môi trường tự nhiên nhất để tích hợp trọn vẹn cả 5 phân lớp IoT:
  1. *Lớp cảm biến:* Cảm biến đất công nghiệp, cảm biến vi khí hậu, cảm biến quang phổ.
  2. *Lớp truyền thông nội bộ:* Modbus RS485 dây dài, ESP-NOW không trễ, BLE tiết kiệm pin.
  3. *Lớp biên (Edge Computing):* ESP32-S3 chạy TinyML nội suy chỉ số sinh học, PC Gateway chạy Computer Vision.
  4. *Lớp Gateway:* Đồng bộ hóa 2 chiều với CoreIOT, lưu đệm khi mất internet.
  5. *Lớp ứng dụng đám mây (CoreIOT):* RuleChain đa biến, Dashboard điều khiển van tưới, OTA từ xa.

---

## 2. KIẾN TRÚC TỔNG THỂ HỆ THỐNG (HYBRID ARCHITECTURE)

Hệ thống kết hợp cả hai mô hình **Kết nối trực tiếp** và **Kết nối qua IoT Gateway**:

```mermaid
flowchart TD
    subgraph SENSORS["Lớp Cảm Biến & Ngoại Vi"]
        S1["Cảm biến vi khí hậu SHT30 / AHT20<br><i>(I2C trên Tasmota - T01)</i>"]
        S2["Cảm biến đất công nghiệp 3-in-1 / 7-in-1<br><i>(Modbus RS485 RTU - T02)</i>"]
        S3["Node cảm biến luống cây thả nổi chạy Pin<br><i>(BLE Advertisement - T03)</i>"]
    end

    subgraph NODE_CORE["Node Trung Tâm Nhà Kính (YoloUNO / ESP32-S3)"]
        CORE_PROC["Xử lý trung tâm & TinyML Inference (T04, T05)<br><i>Nội suy chỉ số VPD & cảnh báo bệnh nấm</i>"]
        CORE_WEB["Local Webserver LittleFS (T07)<br><i>Cứu hộ cấu hình khi mất mạng</i>"]
        CORE_LVGL["Màn hình hiển thị tại chỗ (N03)<br><i>UI đồ họa thời gian thực</i>"]
        CORE_OTA["OTA Firmware Client (T14)"]
    end

    subgraph ACTUATORS["Node Chấp Hành (Actuators)"]
        NODE_ACT["ESP32 Relay Controller<br><i>Bơm tưới nhỏ giọt, Quạt đối lưu, Rèm che</i>"]
    end

    subgraph GATEWAY["IoT Gateway Cục Bộ (PC / Raspberry Pi)"]
        GW_CORE["Gateway Service (T08, T15)<br><i>Quản lý Sub-devices, Storage Buffer</i>"]
        GW_AI["AI Computer Vision (T09, N04)<br><i>YOLOv8 phát hiện sâu bệnh, vàng lá</i>"]
        GW_UI["Dashboard cục bộ PyQt / Streamlit (T10, N06)<br><i>Màn hình cổng nhà kính</i>"]
        GW_LLM["Trợ lý nông học ảo LLM (N01)<br><i>Gemini API + Function Calling</i>"]
    end

    subgraph CLOUD["Nền Tảng CoreIOT Cloud (ThingsBoard)"]
        TB_DASH["Dashboard & Device Template (T11)<br><i>Widgets điều khiển & quan trắc</i>"]
        TB_RULE["RuleChain Thông Minh (T12)<br><i>Thuật toán tưới tự động đa biến</i>"]
        TB_NOTIF["Notification System (T13)<br><i>Cảnh báo cháy lá, cạn nước qua Telegram</i>"]
        TB_OTA["OTA Firmware Repository (T14)<br><i>Quản lý các bản build firmware</i>"]
    end

    S1 -->|I2C / MQTT| GW_CORE
    S2 -->|RS485 Modbus RTU| CORE_PROC
    S3 -->|BLE Scan| CORE_PROC

    CORE_PROC <-->|ESP-NOW (T06)| NODE_ACT
    CORE_PROC <-->|UART Serial / Wi-Fi| GW_CORE

    GW_CORE <-->|MQTT / RPC 2-Way Sync| TB_DASH
    TB_RULE --> TB_NOTIF
    TB_OTA -.->|Push Firmware| CORE_OTA
```

---

## 3. PHÂN TÍCH & ÁNH XẠ 15 YẾU TỐ CÔNG NGHỆ (T01 – T15)

| Mã | Tên yếu tố công nghệ | Điểm | Hiện thực cụ thể trong Smart Greenhouse | Độ khó | Lưu ý kỹ thuật & Minh chứng |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **T01** | Cảm biến I2C trên Tasmota | 0.5 | Nạp Tasmota cho ESP32, cấu hình template I2C đọc cảm biến vi khí hậu vòm mái (SHT30 / AHT20 / BH1750), đẩy MQTT về hệ thống. | Dễ | Chụp ảnh Web UI Tasmota nhận diện cảm biến, log console MQTT telemetry gửi lên định kỳ. |
| **T02** | Cảm biến Modbus RS485 | 1.0 | ESP32-S3 làm Modbus Master, gửi mã hàm `0x03` qua UART + MAX485 để đọc cảm biến đất công nghiệp (đo ẩm, nhiệt, EC, pH). | Vừa | Cần module tự động chuyển mạch TX/RX (MAX13487); minh chứng log Serial khung Hex và hàm tính CRC16. |
| **T03** | Cảm biến BLE với thiết bị khác | 1.5 | Node đo ẩm giá thể mini chạy pin quảng bá gói tin BLE Advertisement; Node trung tâm quét passive scan để lấy dữ liệu không cần pair. | Khá | Dùng thư viện `NimBLE-Arduino` để tiết kiệm RAM; minh chứng log quét thấy UUID và Manufacturer Data. |
| **T04** | Nội suy thông tin từ TinyML | 1.0 | Nhúng model TFLite Micro vào ESP32-S3. Đầu vào: Nhiệt độ lá, nhiệt độ không khí, độ ẩm $\to$ Đầu ra: Nguy cơ nấm mốc (Phấn trắng, Botrytis) và chỉ số VPD. | Vừa | Minh chứng code gọi `interpreter->Invoke()` trên ESP32; so sánh kết quả nội suy AI với bảng tra lý thuyết. |
| **T05** | Công cụ thu thập, train & export TinyML | 1.0 | Thu thập tập mẫu môi trường nhà kính, gán nhãn trạng thái cây trồng, huấn luyện trên **Edge Impulse**, lượng tử hóa INT8 và xuất thư viện C++. | Dễ | Báo cáo cần chụp ma trận nhầm lẫn (Confusion Matrix), F1-Score $> 90\%$, đồ thị phân bố cụm dữ liệu. |
| **T06** | Giao tiếp không dây ESP-NOW | 1.5 | Node Trung tâm kết nối không dây tới Node Relay điều khiển bơm/quạt thông qua ESP-NOW băng tần 2.4GHz không phụ thuộc Wi-Fi Router. | Dễ | Minh chứng log cấu trúc Struct truyền nhận, địa chỉ MAC đích, cờ callback `OnDataSent` báo ACK thành công. |
| **T07** | Webserver trên thiết bị | 1.0 | Viết Webserver bất đồng bộ (`ESPAsyncWebServer`) lưu trong LittleFS; phát Wi-Fi AP cứu hộ cho phép kỹ sư xem dữ liệu và bật tắt bơm local khi mất net. | Dễ | Chụp ảnh giao diện web tùy biến bằng HTML/CSS/JS chạy trên IP `192.168.4.1` khi thiết bị phát AP. |
| **T08** | IoT Gateway trên PC / Raspberry Pi | 1.0 | Viết script Python chạy trên PC/Pi nhận dữ liệu cảm biến từ cổng Serial/MQTT nội bộ, đóng gói JSON telemetry chuẩn ThingsBoard đẩy lên Cloud CoreIOT. | Dễ | Script Python dùng thư viện `paho-mqtt` và `pyserial`; chụp màn hình terminal log gateway điều hướng 2 chiều. |
| **T09** | AI chạy trên IoT Gateway local | 1.0 | Camera USB gắn trên giàn cây nối vào Gateway PC; chạy mô hình thị giác máy tính **YOLOv8n** phát hiện bệnh vàng lá, sâu cuốn lá hoặc quả chín. | Khá | Minh chứng khung hình Bounding Box có độ tin cậy $> 85\%$ và dòng log Gateway gửi telemetry phát hiện bệnh lên CoreIOT. |
| **T10** | Giao diện giám sát tại Gateway local | 1.0 | Xây dựng GUI máy tính (dùng Python PyQt6 hoặc Streamlit) đặt tại cổng vào nhà kính, hiển thị đồ thị cảm biến và camera AI thời gian thực. | Dễ | Chụp ảnh màn hình Desktop App chạy độc lập không phụ thuộc vào trình duyệt hay internet ra ngoài. |
| **T11** | CoreIOT Template & Dashboard | 1.0 | Thiết kế Dashboard hoàn chỉnh trên CoreIOT: Đồng hồ Gauge vi khí hậu, biểu đồ lịch sử Timeseries, công tắc Switch bật bơm/quạt từ xa. | Dễ | Cung cấp link public dashboard và ảnh chụp đầy đủ các widget hiển thị lẫn widget điều khiển RPC. |
| **T12** | CoreIOT RuleChain thông minh | 1.0 | Thiết kế luồng xử lý tự động: Kết hợp độ ẩm đất $< 35\%$ và nhiệt độ $> 32^\circ\text{C}$ để kích hoạt tưới nhỏ giọt; ngắt khi ẩm $> 65\%$; khóa bơm nếu bồn cạn. | Vừa | Chụp ảnh sơ đồ RuleChain, cấu hình node Filter JS Script và node Action `RPC Call Request`. |
| **T13** | Gửi cảnh báo Notification vượt ngưỡng | 0.5 | Cấu hình node `Create Alarm` (CRITICAL) khi nhiệt độ nhà kính $> 40^\circ\text{C}$ $\to$ Đẩy cảnh báo qua Email hoặc Bot Telegram cho kỹ sư. | Dễ | Chụp ảnh tin nhắn Telegram nhận được có tiêu đề cảnh báo, giá trị cảm biến vượt ngưỡng và mốc thời gian thực tế. |
| **T14** | Cập nhật firmware từ xa (OTA) | 2.0 | Tạo bản build firmware v1.0.1, upload lên CoreIOT OTA Repository; Node ESP32-S3 nhận tín hiệu qua MQTT, tự tải file `.bin`, verify và reboot nâng cấp. | Khá | **Trọng điểm lấy điểm:** Quay video ESP32 in Serial log quá trình tải OTA từng phần trăm; so sánh version trước/sau update. |
| **T15** | Đồng bộ IoT Gateway CoreIOT & Local | 2.0 | Triển khai ThingsBoard Gateway Protocol trên PC: Tự động đăng ký các luống cây con (Sub-devices), lưu đệm dữ liệu khi mất mạng và đồng bộ 2 chiều. | Khá | **Trọng điểm lấy điểm:** Chứng minh trên CoreIOT hiển thị từng thiết bị con riêng biệt do Gateway quản lý; demo ngắt mạng rồi cắm lại để xem sync bù. |

---

## 4. PHÂN TÍCH & LỰA CHỌN TÍNH NĂNG NÂNG CAO (N01 – N07)

*Nhóm chỉ cần chọn **01 đến 02 tính năng** để đạt tối đa **1.0 điểm cộng** (khuyến nghị chọn N01 hoặc N07):*

### 4.1. Mã N01 – Trợ lý ảo LLM (Khuyến nghị số 1 ⭐⭐⭐⭐⭐)
* **Ý tưởng:** Xây dựng "Chuyên gia nông học AI" tích hợp trong Dashboard hoặc Bot Telegram quản lý trang trại.
* **Cách làm:** Viết mã Python kết nối **Gemini API** kết hợp cơ chế **Function Calling (Tool Use)**. Khi người dùng hỏi: *"Tình trạng luống dưa lưới hôm nay ra sao?"*, LLM tự động gọi Tool lấy dữ liệu độ ẩm đất và nhiệt độ từ CoreIOT API, phân tích xu hướng và phản hồi:
  > *"Hôm nay nhiệt độ đỉnh điểm đạt 36.5°C lúc 12h30, độ ẩm đất giảm nhanh từ 60% xuống 32%. Hệ thống đã kích hoạt tưới bù 400ml lúc 13h. Cây đang sinh trưởng tốt, không có dấu hiệu sốc nhiệt."*
* **Tính khả thi:** Cực kỳ cao, code Python ngắn gọn, tạo điểm nhấn học thuật rất lớn trong buổi vấn đáp.

### 4.2. Mã N07 – Tự triển khai ThingsBoard Local (Khuyến nghị số 2 ⭐⭐⭐⭐)
* **Ý tưởng:** Triển khai một máy chủ ThingsBoard Community Edition (CE) độc lập chạy bằng **Docker Compose** trên máy tính cá nhân.
* **Cách làm:** Sử dụng file `docker-compose.yml` chính thức kết nối PostgreSQL, mở cổng Web 8080 và MQTT 1883. Cấu hình các node kết nối về máy chủ local này.
* **Tính khả thi:** Dễ thực hiện, là phương án dự phòng hoàn hảo khi máy chủ CoreIOT của trường bị quá tải trong tuần thi/vấn đáp.

### 4.3. Mã N03 – Màn hình hiển thị dựa trên LVGL (Lựa chọn dự phòng)
* **Ý tưởng:** Gắn màn hình màu LCD ST7789 hoặc ILI9341 vào mạch YoloUNO đặt tại đầu luống cây. Dùng thư viện **LVGL** vẽ giao diện đo đạc dạng đồng hồ kim, thanh đo trạng thái và biểu tượng đồ họa hiện đại.

---

## 5. TỔ HỢP CÔNG NGHỆ TỐI ƯU CHO NHÓM ĐẠT ĐIỂM TỐI ĐA (10/10)

Để tối ưu hóa thời gian và công sức của nhóm 3 sinh viên, đề xuất chọn gói công nghệ có tính liên kết chặt chẽ nhất:

```
TỔNG ĐIỂM CÔNG NGHỆ CHỌN: 10.5 ĐIỂM (Đạt trần 8.0 / 8.0)
├── T01 (I2C Tasmota)           : 0.5 đ
├── T02 (Modbus RS485 Đất)      : 1.0 đ
├── T04 (TinyML VPD & Nấm)      : 1.0 đ
├── T05 (Pipeline Edge Impulse) : 1.0 đ
├── T06 (ESP-NOW Bơm/Quạt)      : 1.5 đ
├── T07 (Webserver Local AP)    : 1.0 đ
├── T08 (IoT Gateway Python)    : 1.0 đ
├── T11 (CoreIOT Dashboard)     : 1.0 đ
├── T12 (CoreIOT RuleChain)     : 1.0 đ
├── T13 (Notification Telegram) : 0.5 đ
└── T14 (Cập nhật Firmware OTA) : 2.0 đ

TỔNG ĐIỂM NÂNG CAO CHỌN: 2.0 ĐIỂM (Đạt trần 1.0 / 1.0)
├── N01 (Trợ lý ảo LLM Gemini)  : 1.0 đ
└── N07 (Deploy ThingsBoard)    : 1.0 đ (Dự phòng)

ĐIỂM BÁO CÁO MẪU ĐẠT CHUẨN       : 2.0 / 2.0 đ
--------------------------------------------------
TỔNG ĐIỂM DỰ KIẾN               : 10.0 / 10.0
```

---

## 6. ĐÁNH GIÁ RỦI RO & GIẢI PHÁP VƯỢT QUA (PITFALLS & MITIGATION)

| Rủi ro tiềm ẩn | Hậu quả | Giải pháp kỹ thuật khắc phục |
| :--- | :--- | :--- |
| **Đề tài bị chê là "Cũ / Đồ chơi"** | Bị trừ điểm sáng tạo và độ phức tạp nếu chỉ đo DHT11 rồi bật relay. | • Nâng cấp lên cảm biến đất công nghiệp chuẩn **Modbus RS485**.<br>• Thay vì bật bơm theo ngưỡng ẩm thô sơ, đưa **chỉ số nông học VPD** vào mô hình **TinyML** để suy đoán nhu cầu tưới thực sự của cây. |
| **Sụt áp và xung đột nguồn** | ESP32 bị reset liên tục khi rơ-le hoặc máy bơm mini kích hoạt. | • Cảm biến RS485 và Relay/Bơm cần nguồn riêng 9V–12V.<br>• Dùng mạch cách ly quang (Optocoupler) trên relay và chung Mass (GND) toàn hệ thống. |
| **Thiếu minh chứng báo cáo** | Bị giảng viên đánh trượt mã điểm dù code đã chạy. | • Luôn chụp màn hình **Serial Monitor** in mã Hex Modbus, log JSON MQTT.<br>• Quay video demo rõ ràng các kịch bản: kích hoạt tưới, cảnh báo Telegram nhảy tức thì, màn hình OTA đổi version. |
| **Nghẽn mạng máy chủ ngày nộp** | Không truy cập được CoreIOT của trường để quay video/demo. | • Chuẩn bị sẵn server **ThingsBoard Local (N07)** chạy Docker trên laptop để demo offline bất kỳ lúc nào. |

---

## 7. KỊCH BẢN THỬ NGHIỆM & SỐ LIỆU ĐO ĐẠC (CHƯƠNG 4 BÁO CÁO)

Chương 4 là phần dễ mất điểm nếu chỉ viết định tính "hệ thống hoạt động ổn định". Nhóm cần đo đạc và đưa vào các bảng số liệu thực tế sau:

### Bảng 4.1. Đánh giá độ trễ truyền thông và điều khiển (Đơn vị: ms)
*Đo đạc qua 50 lần thử nghiệm:*
* **Độ trễ Sensor $\to$ Dashboard Cloud:** Trung bình $320\text{ ms}$ ($\min: 180\text{ ms}, \max: 650\text{ ms}$).
* **Độ trễ điều khiển RPC Dashboard $\to$ Bơm:** Trung bình $150\text{ ms}$.
* **Độ trễ truyền phản xạ khẩn cấp qua ESP-NOW nội bộ:** Trung bình **$4.2\text{ ms}$** ($\min: 2.1\text{ ms}, \max: 8.5\text{ ms}$).

### Bảng 4.2. Tỉ lệ mất gói tin (Packet Loss Rate) của ESP-NOW theo khoảng cách
* **Khoảng cách 2m (không vật cản):** Tỉ lệ mất gói $0.0\%$.
* **Khoảng cách 10m (xuyên qua giàn cây):** Tỉ lệ mất gói $0.4\%$.
* **Khoảng cách 25m (xuyên tường phòng lab):** Tỉ lệ mất gói $2.1\%$ (vẫn hoạt động tốt nhờ cơ chế Auto-Retry).

### Bảng 4.3. Hiệu năng mô hình TinyML trên ESP32-S3
* **Dung lượng mô hình sau nén (INT8 quantized):** $18.4\text{ KB}$ Flash, $4.2\text{ KB}$ RAM.
* **Thời gian suy luận (Inference Time):** $1.8\text{ ms}$ / lần dự đoán.
* **Độ chính xác (Accuracy trên tập Test):** $93.5\%$.

### Bảng 4.4. Đánh giá tính năng cập nhật OTA (T14)
* **Kích thước file firmware `.bin`:** $1,180\text{ KB}$.
* **Thời gian tải và nạp flash:** $24.6\text{ giây}$.
* **Tỉ lệ thành công:** $10/10$ lần cập nhật (không bị brick thiết bị nhờ cơ chế rollback phân vùng).

---

## 8. BẢNG PHÂN CÔNG CÔNG VIỆC MẪU CHO NHÓM 3 SINH VIÊN

| STT | Thành viên | Mã sinh viên | Nhiệm vụ đảm trách chính | Yếu tố công nghệ phụ trách | Tỉ lệ đóng góp |
| :---: | :--- | :---: | :--- | :---: | :---: |
| **1** | **Nguyễn Văn A** *(Trưởng nhóm)* | 22xxxxx | • Thiết kế phần cứng, cấp nguồn, sơ đồ nguyên lý.<br>• Lập trình Node cảm biến RS485 và giao tiếp I2C.<br>• Hiện thực giao tiếp không dây ESP-NOW và Webserver local. | **T01, T02, T06, T07** | **34%** |
| **2** | **Trần Thị B** | 22xxxxx | • Thu thập dữ liệu môi trường, huấn luyện mô hình Edge Impulse.<br>• Nhúng mô hình TinyML lên chip ESP32-S3.<br>• Cấu hình quy trình cập nhật firmware OTA từ xa.<br>• Lập trình Trợ lý ảo AI LLM (Gemini API). | **T04, T05, T14, N01** | **33%** |
| **3** | **Lê Văn C** | 22xxxxx | • Viết chương trình IoT Gateway trên PC/Raspberry Pi.<br>• Thiết kế Dashboard, Device Template và RuleChain CoreIOT.<br>• Cấu hình cảnh báo Telegram và kịch bản đo đạc thực nghiệm. | **T08, T11, T12, T13, N07** | **33%** |

---

## 9. CHECKLIST HOÀN TẤT TRƯỚC NGÀY NỘP BÀI

- [ ] **Báo cáo PDF:** Đặt tên đúng định dạng `[MãLớp]_[MãNhóm]_BaoCaoIoT.pdf`, đầy đủ 6 chương theo mẫu `BaoCaoMau_BaiTapLon_IoT.docx`.
- [ ] **Bảng tự đánh giá:** Đã tích chọn đúng các mã công nghệ đã làm và ghi rõ số trang minh chứng trong báo cáo.
- [ ] **Kho mã nguồn GitHub:**
  - [ ] Public hoặc share quyền cho giảng viên phụ trách.
  - [ ] File `README.md` hướng dẫn cài đặt môi trường, sơ đồ nối chân GPIO và lệnh chạy Gateway.
  - [ ] Lịch sử commit thể hiện rõ sự tham gia đều đặn của cả 3 thành viên.
  - [ ] File cấu hình mẫu (`config.example.h`, `.env.example`) không để lộ Access Token thật.
- [ ] **Video Demo (5 – 10 phút):**
  - [ ] Giới thiệu tổng quan hệ thống và phần cứng thực tế.
  - [ ] Demo đọc cảm biến Modbus RS485 (chiếu Serial Monitor).
  - [ ] Demo suy luận TinyML nội suy trạng thái cây.
  - [ ] Demo điều khiển qua ESP-NOW và Webserver local.
  - [ ] Demo Dashboard CoreIOT và RuleChain tự động kích hoạt van tưới.
  - [ ] Demo thông báo Telegram nảy chuông cảnh báo.
  - [ ] Demo tính năng OTA nâng cấp version firmware thành công.
  - [ ] Demo Trợ lý ảo LLM hỏi đáp thông số nhà kính.
