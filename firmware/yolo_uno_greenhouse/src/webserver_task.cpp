#include "webserver_task.h"
#include <WiFi.h>
#include <WebServer.h>
#include <DNSServer.h>
#include "global.h"
#include "espnow_transport.h"

static WebServer server(80);
static DNSServer dnsServer;
static const byte DNS_PORT = 53;

// Wi-Fi Configuration: AP Mode (Open Network - No Password required)
static const char* AP_SSID = "SmartGreenhouse-AP";

static const char HTML_INDEX[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Greenhouse - IoT System</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 16px; color: #333; }
    .container { max-width: 540px; margin: 0 auto; }
    .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
    .tab-btn { flex: 1; padding: 12px 8px; border: none; border-radius: 10px; font-weight: bold; font-size: 13px; cursor: pointer; background: #e0e0e0; color: #555; transition: 0.2s; position: relative; }
    .tab-btn.active { background: #2e7d32; color: white; box-shadow: 0 2px 8px rgba(46,125,50,0.3); }
    .badge-dot { position: absolute; top: 6px; right: 8px; background: #e65100; color: white; font-size: 10px; border-radius: 10px; padding: 1px 6px; font-weight: bold; }
    .card { background: white; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    h1 { font-size: 19px; margin: 0 0 12px; color: #2e7d32; display: flex; align-items: center; justify-content: space-between; }
    .badge { font-size: 11px; padding: 4px 8px; border-radius: 6px; font-weight: 600; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
    .metric { background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 10px; text-align: center; }
    .metric .val { font-size: 22px; font-weight: bold; color: #1b5e20; }
    .metric .label { font-size: 11px; color: #666; margin-top: 3px; }
    .ai-box { padding: 10px; border-radius: 8px; font-weight: 600; text-align: center; margin-bottom: 14px; font-size: 12px; }
    .ai-optimal { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
    .ai-heat { background: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; }
    .ai-mold { background: #f3e5f5; color: #6a1b9a; border: 1px solid #e1bee7; }
    .actuators { display: flex; gap: 8px; }
    .btn { flex: 1; padding: 10px; border: none; border-radius: 8px; font-weight: bold; font-size: 12px; cursor: pointer; transition: 0.2s; text-align: center; }
    .btn-on { background: #2e7d32; color: white; }
    .btn-off { background: #e0e0e0; color: #555; }
    .btn-danger { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }
    .slave-card { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .progress-bar { background: #e0e0e0; border-radius: 4px; height: 8px; overflow: hidden; margin-top: 4px; }
    .progress-fill { height: 100%; background: #0288d1; border-radius: 4px; transition: width 0.4s; }
    .footer { text-align: center; font-size: 11px; color: #999; margin: 20px 0; }
    @keyframes pulse-green {
      0% { box-shadow: 0 0 0 0 rgba(46, 125, 50, 0.7); }
      70% { box-shadow: 0 0 0 6px rgba(46, 125, 50, 0); }
      100% { box-shadow: 0 0 0 0 rgba(46, 125, 50, 0); }
    }
    .dot-online { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #2e7d32; animation: pulse-green 1.5s infinite; margin-right: 4px; vertical-align: middle; }
    .dot-offline { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #d32f2f; margin-right: 4px; vertical-align: middle; }
  </style>
</head>
<body>
  <div class="container">
    <!-- NAVIGATION TABS -->
    <div class="tabs">
      <button class="tab-btn active" id="btnTabDash" onclick="switchTab('dash')">📊 MÀN HÌNH CHÍNH</button>
      <button class="tab-btn" id="btnTabSet" onclick="switchTab('set')">
        ⚙️ CÀI ĐẶT &amp; QUẢN LÝ NODE
        <span id="pendingBadgeNav" class="badge-dot" style="display:none;">0</span>
      </button>
    </div>

    <!-- TAB 1: MÀN HÌNH CHÍNH (DASHBOARD) -->
    <div id="viewDash">
      <!-- Master Node Card -->
      <div class="card">
        <h1>Smart Greenhouse <span class="badge" style="background:#e8f5e9; color:#2e7d32;">Master ESP32-S3</span></h1>
        <div id="aiBox" class="ai-box ai-optimal">AI State: Đang tải...</div>
        <div class="grid">
          <div class="metric"><div class="val" id="temp">--</div><div class="label">Nhiệt độ (&deg;C)</div></div>
          <div class="metric"><div class="val" id="humi">--</div><div class="label">Độ ẩm không khí (%)</div></div>
          <div class="metric"><div class="val" id="vpd">--</div><div class="label">VPD (kPa)</div></div>
          <div class="metric"><div class="val" id="time">--</div><div class="label">AI Inference (us)</div></div>
        </div>
        <h4 style="margin:0 0 8px; color:#444; font-size:13px;">ĐIỀU KHIỂN TẠI CHỖ (MASTER NODE):</h4>
        <div class="actuators">
          <button class="btn btn-off" id="masterFanBtn" onclick="toggleMaster('fan')">QUẠT MASTER: OFF</button>
          <button class="btn btn-off" id="masterPumpBtn" onclick="toggleMaster('pump')">BƠM MASTER: OFF</button>
        </div>
      </div>

      <!-- Enrolled Slave Nodes List -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div>
            <h3 style="margin:0; font-size:15px; color:#2e7d32;">Mạng Lưới Node Con Đã Kết Nạp</h3>
            <div style="font-size:11px; color:#777;">Hiển thị và điều khiển độc lập các Node con trong hệ thống</div>
          </div>
          <span id="slaveCountBadge" class="badge" style="background:#e8f5e9; color:#2e7d32;">0 Node</span>
        </div>
        <div id="slaveDashboardContainer">
          <!-- Sẽ render động các Node con đã kết nạp -->
        </div>
      </div>
    </div>

    <!-- TAB 2: CÀI ĐẶT & QUẢN LÝ (SETTINGS) -->
    <div id="viewSet" style="display:none;">
      <!-- Danh sách Chờ Duyệt (Pending) -->
      <div class="card" id="pendingSection" style="border:2px solid #ffb74d; background:#fffbf0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <h3 style="margin:0; color:#e65100; font-size:15px;">⚠️ Yêu Cầu Kết Nạp Chờ Duyệt</h3>
          <span class="badge" style="background:#ffe082; color:#b78103;" id="pendingCountBadge">0</span>
        </div>
        <p style="font-size:12px; color:#666; margin:0 0 10px;">Khi Node con cắm điện, hệ thống sẽ tự động phát hiện và hiện tại đây. Bấm <b>[CHẤP NHẬN]</b> để lưu Flash:</p>
        <div id="pendingList">
          <em style="font-size:12px; color:#888;">Không có yêu cầu kết nạp nào đang chờ...</em>
        </div>
      </div>

      <!-- Danh sách Node Đang Quản Lý & Xóa Node -->
      <div class="card">
        <h3 style="margin:0 0 8px; font-size:15px; color:#2e7d32;">🗑️ Quản Lý &amp; Xóa Node (Lưu Flash NVS)</h3>
        <p style="font-size:12px; color:#666; margin:0 0 12px;">Các Node con này được lưu vĩnh viễn trong bộ nhớ Flash. Bạn có thể xóa bỏ Node khỏi hệ thống tại đây:</p>
        <div id="enrolledList">
          <em style="font-size:12px; color:#888;">Chưa có Node con nào được kết nạp...</em>
        </div>
      </div>
    </div>

    <div class="footer">Smart Greenhouse IoT HK261 - CoreIOT &amp; ESP-NOW Mesh</div>
  </div>

  <script>
    let currentTab = 'dash';
    function switchTab(tab) {
      currentTab = tab;
      document.getElementById('viewDash').style.display = (tab === 'dash') ? 'block' : 'none';
      document.getElementById('viewSet').style.display = (tab === 'set') ? 'block' : 'none';
      document.getElementById('btnTabDash').className = 'tab-btn ' + (tab === 'dash' ? 'active' : '');
      document.getElementById('btnTabSet').className = 'tab-btn ' + (tab === 'set' ? 'active' : '');
    }

    async function updateData() {
      try {
        const res = await fetch('/api/data');
        const d = await res.json();
        document.getElementById('temp').innerText = d.temp.toFixed(1);
        document.getElementById('humi').innerText = d.humi.toFixed(1);
        document.getElementById('vpd').innerText = d.vpd.toFixed(2);
        document.getElementById('time').innerText = d.infer_us;
        const box = document.getElementById('aiBox');
        box.innerText = "TinyML State: " + d.state_str + " (" + (d.conf * 100).toFixed(0) + "%)";
        box.className = "ai-box " + (d.state == 0 ? "ai-optimal" : (d.state == 1 ? "ai-heat" : "ai-mold"));

        const fBtn = document.getElementById('masterFanBtn');
        fBtn.innerText = "QUẠT MASTER: " + (d.fan ? "ON" : "OFF");
        fBtn.className = "btn " + (d.fan ? "btn-on" : "btn-off");

        const pBtn = document.getElementById('masterPumpBtn');
        pBtn.innerText = "BƠM MASTER: " + (d.pump ? "ON" : "OFF");
        pBtn.className = "btn " + (d.pump ? "btn-on" : "btn-off");
      } catch(e) {}
    }

    async function updateSlaves() {
      try {
        const res = await fetch('/api/slaves');
        const d = await res.json();

        // 1. Tab Navigation Badge (Báo hiệu nếu có pending)
        const navBadge = document.getElementById('pendingBadgeNav');
        const pCountBadge = document.getElementById('pendingCountBadge');
        const pList = document.getElementById('pendingList');
        const pCount = (d.pending && d.pending.length) ? d.pending.length : 0;

        if (pCount > 0) {
          navBadge.style.display = 'inline-block';
          navBadge.innerText = pCount;
          pCountBadge.innerText = pCount + ' Chờ Duyệt';

          let html = '';
          d.pending.forEach(p => {
            html += '<div style="background:white; border:1px solid #ffd54f; border-radius:8px; padding:10px; margin-bottom:8px;">';
            html += '  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">';
            html += '    <div><b style="font-size:14px; color:#2e7d32;">' + p.id + '</b><div style="font-size:11px; color:#777;">MAC: ' + p.mac + '</div></div>';
            html += '    <span style="font-size:11px; color:#e65100; font-weight:600;">' + p.age_s + 's trước</span>';
            html += '  </div>';
            html += '  <div style="display:flex; gap:8px;">';
            html += '    <button onclick="approveSlave(\'' + p.mac + '\', true)" style="flex:1; padding:8px; background:#2e7d32; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">✅ CHẤP NHẬN KẾT NẠP</button>';
            html += '    <button onclick="approveSlave(\'' + p.mac + '\', false)" style="padding:8px 12px; background:#e0e0e0; color:#444; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">❌ Từ chối</button>';
            html += '  </div>';
            html += '</div>';
          });
          pList.innerHTML = html;
        } else {
          navBadge.style.display = 'none';
          pCountBadge.innerText = '0';
          pList.innerHTML = '<em style="font-size:12px; color:#888;">Không có yêu cầu kết nạp nào đang chờ...</em>';
        }

        // 3. Tab Cài đặt: Danh sách Node Đã lưu trong Flash
        const enrolledList = document.getElementById('enrolledList');
        if (!d.slaves || d.slaves.length === 0) {
          enrolledList.innerHTML = '<em style="font-size:12px; color:#888;">Chưa có Node con nào được kết nạp...</em>';
        } else {
          let html = '';
          d.slaves.forEach(s => {
            const statusColor = s.online ? '#2e7d32' : '#888';
            const statusHtml = s.online ?
              '<span style="color:#2e7d32; font-weight:600;"><span class="dot-online"></span> Đang sống (' + s.age_s + 's trước)</span>' :
              '<span style="color:#d32f2f; font-weight:600;"><span class="dot-offline"></span> Mất kết nối (' + s.age_s + 's trước)</span>';
            html += '<div style="display:flex; justify-content:space-between; align-items:center; background:#fafafa; border:1px solid #e0e0e0; border-radius:8px; padding:12px; margin-bottom:10px;">';
            html += '  <div>';
            html += '    <b style="font-size:14px; color:#1b5e20;">🌿 ' + s.id + '</b>';
            html += '    <div style="font-size:11px; color:#666; margin-top:2px;">MAC: ' + s.mac + ' | ' + statusHtml + '</div>';
            html += '  </div>';
            html += '  <button onclick="removeSlave(\'' + s.mac + '\', \'' + s.id + '\')" class="btn btn-danger" style="flex:none; padding:8px 14px; font-size:12px; font-weight:bold; cursor:pointer;">🗑️ XÓA NODE</button>';
            html += '</div>';
          });
          enrolledList.innerHTML = html;
        }

        // 4. Tab Màn hình chính: Render card dữ liệu & điều khiển riêng cho TỪNG NODE ĐÃ KẾT NẠP
        const dashContainer = document.getElementById('slaveDashboardContainer');
        const countBadge = document.getElementById('slaveCountBadge');
        const totalSlaves = (d.slaves ? d.slaves.length : 0);
        const onlineSlaves = (d.slaves ? d.slaves.filter(s => s.online).length : 0);
        countBadge.innerText = onlineSlaves + '/' + totalSlaves + ' Đang sống';
        countBadge.style.background = (onlineSlaves > 0) ? '#e8f5e9' : (totalSlaves > 0 ? '#ffebee' : '#f5f5f5');
        countBadge.style.color = (onlineSlaves > 0) ? '#2e7d32' : (totalSlaves > 0 ? '#c62828' : '#777');

        if (!d.slaves || d.slaves.length === 0) {
          dashContainer.innerHTML = `
            <div style="text-align:center; padding:22px 14px; background:#fafafa; border:1px dashed #bdbdbd; border-radius:10px;">
              <div style="font-size:30px; margin-bottom:6px;">📡</div>
              <b style="color:#444; font-size:14px;">Chưa có Node con nào được kết nạp</b>
              <p style="font-size:12px; color:#777; margin:6px 0 14px;">Chỉ các Node con đã được phê duyệt trong mục Cài đặt mới hiển thị tại đây.</p>
              <button onclick="switchTab('set')" class="btn btn-on" style="display:inline-block; max-width:240px; margin:0 auto;">👉 Đi đến Cài đặt để thêm Node</button>
            </div>
          `;
        } else {
          let html = '';
          d.slaves.forEach(s => {
            const isAlive = s.online;
            const cardBorder = isAlive ? 'border:1px solid #c8e6c9; background:white;' : 'border:1px dashed #ef9a9a; background:#fffdfd;';
            const badgeBg = isAlive ? '#e8f5e9' : '#ffebee';
            const badgeColor = isAlive ? '#2e7d32' : '#c62828';
            const badgeBorder = isAlive ? '#c8e6c9' : '#ffcdd2';
            const badgeDot = isAlive ? '<span class="dot-online"></span>' : '<span class="dot-offline"></span>';
            const badgeText = isAlive ? 'ĐANG HOẠT ĐỘNG (' + s.age_s + 's trước)' : 'MẤT LIÊN LẠC (' + s.age_s + 's trước)';
            const sensorVal = s.sensor.toFixed(1);

            html += '<div class="slave-card" style="' + cardBorder + '">';
            html += '  <div style="display:flex; justify-content:space-between; align-items:center;">';
            html += '    <div>';
            html += '      <b style="font-size:15px; color:' + (isAlive ? '#1b5e20' : '#888') + ';">🌿 ' + s.id + '</b>';
            html += '      <div style="font-size:11px; color:#777;">MAC: ' + s.mac + '</div>';
            html += '    </div>';
            html += '    <span class="badge" style="background:' + badgeBg + '; color:' + badgeColor + '; border:1px solid ' + badgeBorder + ';">' + badgeDot + ' ' + badgeText + '</span>';
            html += '  </div>';

            if (!isAlive) {
              html += '  <div style="background:#fff3e0; color:#e65100; border:1px solid #ffe0b2; padding:8px 10px; border-radius:6px; font-size:11px; margin:10px 0; font-weight:600;">⚠️ Node không gửi Heartbeat (> 30s). Thiết bị có thể đã tắt nguồn hoặc mất kết nối!</div>';
            }

            // Dữ liệu cảm biến riêng của Node này
            html += '  <div style="margin:10px 0; background:' + (isAlive ? '#f0f4f8' : '#f5f5f5') + '; border-radius:6px; padding:10px;">';
            html += '    <div style="display:flex; justify-content:space-between; font-size:12px;">';
            html += '      <span>Độ ẩm đất (Khu vực riêng):</span>';
            html += '      <b style="color:' + (isAlive ? '#0277bd' : '#999') + '; font-size:14px;">' + sensorVal + '%</b>';
            html += '    </div>';
            html += '    <div class="progress-bar"><div class="progress-fill" style="width:' + Math.min(100, Math.max(0, sensorVal)) + '%; background:' + (isAlive ? '#0288d1' : '#bbb') + ';"></div></div>';
            html += '  </div>';

            // Cụm nút điều khiển riêng biệt cho Node này
            html += '  <div style="font-size:11px; font-weight:600; color:#555; margin-bottom:6px;">ĐIỀU KHIỂN RIÊNG CHO NODE NÀY:</div>';
            html += '  <div class="actuators">';
            if (isAlive) {
              html += '    <button class="btn ' + (s.fan ? 'btn-on' : 'btn-off') + '" onclick="toggleSlave(\'' + s.mac + '\', \'fan\')">';
              html += '      QUẠT: ' + (s.fan ? 'BẬT' : 'TẮT');
              html += '    </button>';
              html += '    <button class="btn ' + (s.pump ? 'btn-on' : 'btn-off') + '" onclick="toggleSlave(\'' + s.mac + '\', \'pump\')">';
              html += '      BƠM: ' + (s.pump ? 'BẬT' : 'TẮT');
              html += '    </button>';
            } else {
              html += '    <button class="btn" style="background:#eee; color:#999; cursor:not-allowed;" onclick="alert(\'Không thể điều khiển: Node con đang mất kết nối (Offline)!\')">QUẠT: OFFLINE</button>';
              html += '    <button class="btn" style="background:#eee; color:#999; cursor:not-allowed;" onclick="alert(\'Không thể điều khiển: Node con đang mất kết nối (Offline)!\')">BƠM: OFFLINE</button>';
            }
            html += '  </div>';

            // Nút XÓA NODE trực tiếp ngay trên thẻ Màn hình chính
            html += '  <div style="margin-top:12px; padding-top:10px; border-top:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">';
            html += '    <span style="font-size:11px; color:#888;">Quản lý thiết bị:</span>';
            html += '    <button class="btn btn-danger" style="flex:none; padding:6px 14px; font-size:11px; font-weight:bold; cursor:pointer;" onclick="removeSlave(\'' + s.mac + '\', \'' + s.id + '\')">🗑️ XÓA NODE</button>';
            html += '  </div>';

            html += '</div>';
          });
          dashContainer.innerHTML = html;
        }
      } catch(e) {}
    }

    async function toggleMaster(target) {
      await fetch('/api/toggle?node=master&target=' + target);
      updateData();
    }

    async function toggleSlave(mac, target) {
      await fetch('/api/toggle?node=' + encodeURIComponent(mac) + '&target=' + target);
      updateSlaves();
    }

    async function approveSlave(mac, isAccept) {
      await fetch('/api/pairing?action=' + (isAccept ? 'accept' : 'reject') + '&mac=' + encodeURIComponent(mac));
      updateSlaves();
    }

    async function removeSlave(mac, name) {
      const nodeName = name || mac;
      if (confirm('Xác nhận XÓA Node [' + nodeName + '] khỏi hệ thống?\n(Node sẽ bị gỡ khỏi bộ nhớ Flash vĩnh viễn và không còn hiển thị)')) {
        await fetch('/api/pairing?action=remove&mac=' + encodeURIComponent(mac));
        updateSlaves();
      }
    }

    setInterval(() => {
      updateData();
      updateSlaves();
    }, 2000);
    updateData();
    updateSlaves();
  </script>
</body>
</html>
)rawliteral";

static void handle_root() {
    server.send(200, "text/html", HTML_INDEX);
}

static void handle_captive_redirect() {
    String host = server.hostHeader();
    String ap_ip = WiFi.softAPIP().toString();

    if (host != ap_ip && host != (ap_ip + ":80")) {
        server.sendHeader("Location", String("http://") + ap_ip + "/", true);
        server.send(302, "text/plain", "");
        return;
    }
    server.send(200, "text/html", HTML_INDEX);
}

static void handle_data() {
    char json[256];
    snprintf(json, sizeof(json),
             "{\"temp\":%.2f,\"humi\":%.2f,\"vpd\":%.3f,\"state\":%d,\"state_str\":\"%s\",\"conf\":%.2f,\"infer_us\":%lu,\"fan\":%s,\"pump\":%s}",
             glob_temperature, glob_humidity, glob_vpd,
             glob_ai_state, getStateString((ClimateHealthState)glob_ai_state),
             glob_ai_confidence, glob_inference_time_us,
             glob_fan_state ? "true" : "false",
             glob_pump_state ? "true" : "false");
    server.send(200, "application/json", json);
}

static void handle_toggle() {
    String node = server.hasArg("node") ? server.arg("node") : "master";
    String target = server.hasArg("target") ? server.arg("target") : "fan";

    if (node == "master") {
        // Điều khiển thiết bị Master tại chỗ
        if (target == "fan") {
            glob_fan_state = !glob_fan_state;
        } else if (target == "pump") {
            glob_pump_state = !glob_pump_state;
        }
        espnow_send_command(glob_fan_state, glob_pump_state);
    } else {
        // Điều khiển riêng cho Slave Node có địa chỉ MAC tương ứng
        espnow_control_slave(node.c_str(), target.c_str(), -1);
    }

    server.send(200, "application/json", "{\"status\":\"ok\"}");
}

static void handle_slaves() {
    uint32_t now = millis();
    uint32_t remain_s = 0;
    if (glob_pairing_mode && glob_pairing_end_ms > now) {
        remain_s = (glob_pairing_end_ms - now) / 1000;
    }

    String json = "{";
    json += "\"pairing_mode\":" + String(glob_pairing_mode ? "true" : "false") + ",";
    json += "\"remain_s\":" + String(remain_s) + ",";
    json += "\"slave_count\":" + String(glob_slave_count) + ",";

    // 1. Pending approval queue
    json += "\"pending\":[";
    for (int i = 0; i < glob_pending_count; i++) {
        if (i > 0) json += ",";
        char mac_str[18];
        snprintf(mac_str, sizeof(mac_str), "%02X:%02X:%02X:%02X:%02X:%02X",
                 glob_pending_slaves[i].mac[0], glob_pending_slaves[i].mac[1], glob_pending_slaves[i].mac[2],
                 glob_pending_slaves[i].mac[3], glob_pending_slaves[i].mac[4], glob_pending_slaves[i].mac[5]);
        uint32_t req_age_s = (now - glob_pending_slaves[i].request_time_ms) / 1000;
        json += "{\"id\":\"" + String(glob_pending_slaves[i].device_id) + "\",\"mac\":\"" + String(mac_str) + "\",\"age_s\":" + String(req_age_s) + "}";
    }
    json += "],";

    // 2. Paired slaves list
    json += "\"slaves\":[";
    for (int i = 0; i < glob_slave_count; i++) {
        if (i > 0) json += ",";
        char mac_str[18];
        snprintf(mac_str, sizeof(mac_str), "%02X:%02X:%02X:%02X:%02X:%02X",
                 glob_slaves[i].mac[0], glob_slaves[i].mac[1], glob_slaves[i].mac[2],
                 glob_slaves[i].mac[3], glob_slaves[i].mac[4], glob_slaves[i].mac[5]);

        bool online = (glob_slaves[i].last_seen_ms > 0 && (now - glob_slaves[i].last_seen_ms) <= 30000);
        uint32_t age_s = (glob_slaves[i].last_seen_ms > 0) ? (now - glob_slaves[i].last_seen_ms) / 1000 : 999;

        json += "{";
        json += "\"id\":\"" + String(glob_slaves[i].device_id) + "\",";
        json += "\"mac\":\"" + String(mac_str) + "\",";
        json += "\"role\":\"" + String(glob_slaves[i].role) + "\",";
        json += "\"age_s\":" + String(age_s) + ",";
        json += "\"online\":" + String(online ? "true" : "false") + ",";
        json += "\"fan\":" + String(glob_slaves[i].fan_status ? "true" : "false") + ",";
        json += "\"pump\":" + String(glob_slaves[i].pump_status ? "true" : "false") + ",";
        json += "\"sensor\":" + String(glob_slaves[i].sensor_val, 1);
        json += "}";
    }

    json += "]}";
    server.send(200, "application/json", json);
}

static void handle_pairing() {
    if (server.hasArg("action")) {
        String action = server.arg("action");
        if (action == "start") {
            espnow_start_pairing(60);
        } else if (action == "stop") {
            espnow_stop_pairing();
        } else if (action == "accept" && server.hasArg("mac")) {
            String mac = server.arg("mac");
            espnow_accept_slave(mac.c_str());
        } else if (action == "reject" && server.hasArg("mac")) {
            String mac = server.arg("mac");
            espnow_reject_slave(mac.c_str());
        } else if (action == "remove" && server.hasArg("mac")) {
            String mac = server.arg("mac");
            espnow_remove_slave(mac.c_str());
        }
    }
    server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void setup_webserver() {
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID); // Open Wi-Fi Network

    Serial.println("[WebServer] Access Point started:");
    Serial.printf("  SSID: %s\n", AP_SSID);
    Serial.printf("  IP:   %s\n", WiFi.softAPIP().toString().c_str());

    dnsServer.start(DNS_PORT, "*", WiFi.softAPIP());
    Serial.println("[WebServer] Captive Portal DNS Server started on port 53");

    server.on("/", HTTP_GET, handle_root);
    server.on("/api/data", HTTP_GET, handle_data);
    server.on("/api/toggle", HTTP_GET, handle_toggle);
    server.on("/api/slaves", HTTP_GET, handle_slaves);
    server.on("/api/pairing", HTTP_GET, handle_pairing);

    server.on("/hotspot-detect.html", HTTP_GET, handle_root);
    server.on("/library/test/success.html", HTTP_GET, handle_root);
    server.on("/generate_204", HTTP_GET, handle_captive_redirect);
    server.on("/gen_204", HTTP_GET, handle_captive_redirect);
    server.on("/ncsi.txt", HTTP_GET, handle_captive_redirect);
    server.on("/connecttest.txt", HTTP_GET, handle_captive_redirect);
    server.on("/redirect", HTTP_GET, handle_captive_redirect);
    server.on("/canonical.html", HTTP_GET, handle_root);

    server.onNotFound(handle_captive_redirect);

    server.begin();
    Serial.println("[WebServer] HTTP Server listening on port 80");
}

void webserver_task(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(1000));
    setup_webserver();

    while (1) {
        dnsServer.processNextRequest();
        server.handleClient();
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}
