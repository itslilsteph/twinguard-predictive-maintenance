/*
  TwinGuard IoT Motor Monitoring System - ESP32 MQTT Publisher

  Purpose:
  - Reads real-time vibration data (X, Y, Z axes) from ADXL345 accelerometer
  - Connects ESP32 to Wi-Fi network
  - Publishes sensor data to MQTT broker (HiveMQ)
  - Sends data in JSON format for cloud-based processing and dashboard visualization

  System Role:
  This file implements the IoT/cloud version of the TwinGuard system.

  Difference from arduino_serial_reader.ino:
  - arduino_serial_reader.ino sends raw sensor data via USB Serial to a local Python script
  - esp32_mqtt_publisher.ino sends structured JSON data wirelessly over MQTT
  - This ESP32 version enables remote monitoring, scalability, and cloud integration,
    while the Arduino Serial version is limited to local USB-based processing

  Architecture Flow:
  ESP32 → MQTT Broker → Python MQTT Client → Flask Backend → Web Dashboard
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>

// ADXL345 sensor configuration
#define ADXL345_ADDR 0x53

// Wi-Fi credentials
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";


// MQTT configuration
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_topic = "stephano/motor/data";
const char* client_id = "esp32_motor_publisher_01";

// Objects for communication
WiFiClient espClient;
PubSubClient client(espClient);

// Sensor data variables
int16_t X_out, Y_out, Z_out;

// Timing control (1 Hz publishing)
unsigned long lastPublishTime = 0;
const unsigned long publishInterval = 1000; // 1 second

// Initialize ADXL345 sensor
void setupADXL345() {

  // Initialize I2C on ESP32 (SDA = A4, SCL = A5 or default pins)
  Wire.begin(A4, A5);

  // Configure data format register
  Wire.beginTransmission(ADXL345_ADDR);
  Wire.write(0x31);
  Wire.write(0x0B);   // Full resolution, ±16g range
  Wire.endTransmission();

  // Enable measurement mode
  Wire.beginTransmission(ADXL345_ADDR);
  Wire.write(0x2D);
  Wire.write(0x08);
  Wire.endTransmission();
}

// Read sensor data from ADXL345
bool readADXL345(int16_t &x, int16_t &y, int16_t &z) {

  // Start reading from DATAX0 register
  Wire.beginTransmission(ADXL345_ADDR);
  Wire.write(0x32);

  if (Wire.endTransmission(false) != 0) {
    return false;
  }

  // Request 6 bytes (X, Y, Z data)
  int bytesRequested = Wire.requestFrom((uint8_t)ADXL345_ADDR, (size_t)6, true);

  if (bytesRequested != 6 || Wire.available() < 6) {
    return false;
  }

  // Read low and high bytes for each axis
  uint8_t x0 = Wire.read();
  uint8_t x1 = Wire.read();
  uint8_t y0 = Wire.read();
  uint8_t y1 = Wire.read();
  uint8_t z0 = Wire.read();
  uint8_t z1 = Wire.read();

  // Combine bytes into signed 16-bit values
  x = (int16_t)((x1 << 8) | x0);
  y = (int16_t)((y1 << 8) | y0);
  z = (int16_t)((z1 << 8) | z0);

  return true;
}

// Wi-Fi connection handler
void connectWiFi() {

  if (WiFi.status() == WL_CONNECTED) return;

  Serial.print("Connecting to Wi-Fi");
  WiFi.begin(ssid, password);

  unsigned long startAttempt = millis();

  // Try connecting for 15 seconds
  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 15000) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Wi-Fi connected");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi connection failed");
  }
}


// MQTT connection handler
void connectMQTT() {

  while (!client.connected()) {
    Serial.print("Connecting to MQTT... ");

    if (client.connect(client_id)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 2 seconds");
      delay(2000);
    }
  }
}


// Publish sensor data to MQTT
void publishSensorData(int16_t x, int16_t y, int16_t z) {

  // Build JSON payload
  String payload = "{";
  payload += "\"x\":" + String(x) + ",";
  payload += "\"y\":" + String(y) + ",";
  payload += "\"z\":" + String(z);
  payload += "}";

  // Publish to MQTT topic
  bool ok = client.publish(mqtt_topic, payload.c_str());

  // Debug output
  Serial.print("Publishing -> ");
  Serial.println(payload);

  if (ok) {
    Serial.println("Publish success");
  } else {
    Serial.println("Publish failed");
  }
}


// Setup function
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("ESP32 MQTT ADXL345 publisher starting...");

  setupADXL345();     // Initialize sensor
  connectWiFi();      // Connect to Wi-Fi

  client.setServer(mqtt_server, mqtt_port); // Set MQTT broker
}


// Main loop
void loop() {

  // Ensure Wi-Fi connection
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  // Ensure MQTT connection
  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  // Publish data at fixed interval (1 second)
  if (millis() - lastPublishTime >= publishInterval) {
    lastPublishTime = millis();

    if (readADXL345(X_out, Y_out, Z_out)) {

      // Debug serial output
      Serial.print("X: "); Serial.print(X_out);
      Serial.print(" Y: "); Serial.print(Y_out);
      Serial.print(" Z: "); Serial.println(Z_out);

      // Send to MQTT broker
      publishSensorData(X_out, Y_out, Z_out);

    } else {
      Serial.println("Failed to read ADXL345");
    }
  }
}