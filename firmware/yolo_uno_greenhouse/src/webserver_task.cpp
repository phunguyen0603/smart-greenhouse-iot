#include "webserver_task.h"
#include <WiFi.h>
#include <WebServer.h>
#include "global.h"

static WebServer server(80);

// Wi-Fi Configuration: AP Mode by default, connects to STA if configured
static const char* AP_SSID = "SmartGreenhouse-AP";
static const char* AP_PASS = "12345678";

static const char HTML_INDEX[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Greenhouse - Local Node</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }
    .card { background: white; border-radius: 12px; padding: 20px; max-width: 500px; margin: 0 auto 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    h1 { font-size: 20px; margin-top: 0; color: #2e7d32; display: flex; align-items: center; justify-content: space-between; }
    .badge { font-size: 12px; padding: 4px 8px; border-radius: 6px; background: #e8f5e9; color: #2e7d32; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
    .metric { background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 12px; text-align: center; }
    .metric .val { font-size: 26px; font-weight: bold; color: #1b5e20; }
    .metric .label { font-size: 12px; color: #666; margin-top: 4px; }
    .ai-box { padding: 14px; border-radius: 8px; font-weight: 600; text-align: center; margin-bottom: 16px; transition: 0.3s; }
    .ai-optimal { background: #e8f5e9; color: #2e7d32; border: 1px solid #c8e6c9; }
    .ai-heat { background: #fff3e0; color: #e65100; border: 1px solid #ffe0b2; }
    .ai-mold { background: #f3e5f5; color: #6a1b9a; border: 1px solid #e1bee7; }
    .actuators { display: flex; gap: 10px; }
    .btn { flex: 1; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: 0.2s; }
    .btn-on { background: #2e7d32; color: white; }
    .btn-off { background: #e0e0e0; color: #555; }
    .footer { text-align: center; font-size: 11px; color: #999; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Smart Greenhouse <span class="badge">ESP32-S3 Node</span></h1>
    <div id="aiBox" class="ai-box ai-optimal">AI State: Loading...</div>
    <div class="grid">
      <div class="metric"><div class="val" id="temp">--</div><div class="label">Temperature (&deg;C)</div></div>
      <div class="metric"><div class="val" id="humi">--</div><div class="label">Humidity (%)</div></div>
      <div class="metric"><div class="val" id="vpd">--</div><div class="label">VPD (kPa)</div></div>
      <div class="metric"><div class="val" id="time">--</div><div class="label">AI Inference (us)</div></div>
    </div>
    <h3>Local Manual Control</h3>
    <div class="actuators">
      <button class="btn btn-off" id="fanBtn" onclick="toggleActuator('fan')">FAN: OFF</button>
      <button class="btn btn-off" id="pumpBtn" onclick="toggleActuator('pump')">PUMP: OFF</button>
    </div>
  </div>
  <div class="footer">IoT Assignment HK261 - CoreIOT & Edge AI Architecture</div>
  <script>
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

        const fBtn = document.getElementById('fanBtn');
        fBtn.innerText = "FAN: " + (d.fan ? "ON" : "OFF");
        fBtn.className = "btn " + (d.fan ? "btn-on" : "btn-off");

        const pBtn = document.getElementById('pumpBtn');
        pBtn.innerText = "PUMP: " + (d.pump ? "ON" : "OFF");
        pBtn.className = "btn " + (d.pump ? "btn-on" : "btn-off");
      } catch(e) {}
    }
    async function toggleActuator(type) {
      await fetch('/api/toggle?target=' + type);
      updateData();
    }
    setInterval(updateData, 2000);
    updateData();
  </script>
</body>
</html>
)rawliteral";

static void handle_root() {
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
    if (server.hasArg("target")) {
        String target = server.arg("target");
        if (target == "fan") {
            glob_fan_state = !glob_fan_state;
        } else if (target == "pump") {
            glob_pump_state = !glob_pump_state;
        }
    }
    server.send(200, "application/json", "{\"status\":\"ok\"}");
}

void setup_webserver() {
    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID, AP_PASS);

    Serial.println("[WebServer] Access Point started:");
    Serial.printf("  SSID: %s\n", AP_SSID);
    Serial.printf("  IP:   %s\n", WiFi.softAPIP().toString().c_str());

    server.on("/", HTTP_GET, handle_root);
    server.on("/api/data", HTTP_GET, handle_data);
    server.on("/api/toggle", HTTP_GET, handle_toggle);
    server.begin();
    Serial.println("[WebServer] HTTP Server listening on port 80");
}

void webserver_task(void *pvParameters) {
    vTaskDelay(pdMS_TO_TICKS(1000));
    setup_webserver();

    while (1) {
        server.handleClient();
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}
