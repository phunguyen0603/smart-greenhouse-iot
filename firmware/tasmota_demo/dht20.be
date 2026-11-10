# dht20.be - Berry script for Tasmota on ESP32-S3 YoloUNO
# Môn học: Internet of Things (HK261) - Trường ĐH Bách Khoa ĐHQG-HCM
# Giảng viên: TS. Lê Trọng Nhân

class DHT20 : Driver
  var wire, temp, hum

  def init()
    # Khởi tạo bus I2C trên YoloUNO (SDA = GPIO 11, SCL = GPIO 12)
    self.wire = tasmota.wire_scan(0x38)
    print("DHT20 I2C Driver Initialized on address 0x38")
  end

  def every_250ms()
    # Đọc dữ liệu từ DHT20 qua I2C
    # Gửi lệnh đo: 0xAC, 0x33, 0x00
    var cmd = bytes("AC3300")
    tasmota.wire_write(0x38, cmd)
    tasmota.set_timer(80, /-> self.read_data())
  end

  def read_data()
    var r = tasmota.wire_read(0x38, 7)
    if size(r) >= 7
      # Byte 0: status, Byte 1-2-3 (MSB): Humidity, Byte 3-4-5: Temperature
      var raw_humi = ((r[1] << 12) | (r[2] << 4) | (r[3] >> 4))
      var raw_temp = (((r[3] & 0x0F) << 16) | (r[4] << 8) | r[5])

      self.hum  = (raw_humi * 100.0) / 1048576.0
      self.temp = (raw_temp * 200.0) / 1048576.0 - 50.0
    end
  end

  # Hiển thị lên trang chủ Web UI của Tasmota
  def web_sensor()
    if self.temp == nil  return  end
    import string
    tasmota.web_send_decimal(string.format("{s}DHT20 Nhiệt độ{m}%.1f °C{e}", self.temp))
    tasmota.web_send_decimal(string.format("{s}DHT20 Độ ẩm{m}%.1f %%{e}", self.hum))
  end

  # Ghép vào bản tin Telemetry JSON định kỳ (TelePeriod) gửi lên CoreIOT
  def json_append()
    if self.temp == nil  return  end
    import string
    tasmota.response_append(string.format(',"temperature":%.1f,"humidity":%.1f', self.temp, self.hum))
  end
end

dht20 = DHT20()
tasmota.add_driver(dht20)
print("DHT20 Driver added to Tasmota!")
