/*
  TwinGuard Motor Monitoring System - Arduino Serial Reader

  Purpose:
  - Reads vibration data (X, Y, Z axes) from ADXL345 accelerometer
  - Controls a DC motor using IN1 and IN2 pins
  - Streams raw sensor data over Serial (USB) in CSV format
  - Used as input for Python-based real-time monitoring system
*/

#include <Wire.h>

// ADXL345 I2C address
#define ADXL345 0x53

// Motor control pins
#define IN1 6
#define IN2 7

// Variables to store accelerometer readings
int16_t X_out, Y_out, Z_out;

void setup() {
  // Start serial communication at 115200 baud rate
  Serial.begin(115200);

  // Initialize I2C communication
  Wire.begin();

  // Set motor control pins as outputs
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // Start motor rotation (forward direction)
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // Configure ADXL345 sensor

  // Set data format:
  // 0x0B = full resolution mode, ±16g range
  Wire.beginTransmission(ADXL345);
  Wire.write(0x31);   // Data format register
  Wire.write(0x0B);   // Configuration value
  Wire.endTransmission();

  // Enable measurement mode
  Wire.beginTransmission(ADXL345);
  Wire.write(0x2D);   // Power control register
  Wire.write(0x08);   // Measurement mode ON
  Wire.endTransmission();

  Serial.println("Motor + Accelerometer running...");
}

void loop() {
  // Request sensor data

  // Start reading from DATAX0 register
  Wire.beginTransmission(ADXL345);
  Wire.write(0x32);
  Wire.endTransmission(false);

  // Request 6 bytes (X, Y, Z data)
  Wire.requestFrom(ADXL345, 6);

  // Ensure all 6 bytes are available
  if (Wire.available() == 6) {

    // Read low and high bytes for each axis
    uint8_t x0 = Wire.read();
    uint8_t x1 = Wire.read();
    uint8_t y0 = Wire.read();
    uint8_t y1 = Wire.read();
    uint8_t z0 = Wire.read();
    uint8_t z1 = Wire.read();

    // Combine bytes into signed 16-bit integers
    X_out = (x1 << 8) | x0;
    Y_out = (y1 << 8) | y0;
    Z_out = (z1 << 8) | z0;

    // Output data via Serial (CSV)

    Serial.print(X_out);
    Serial.print(", ");
    Serial.print(Y_out);
    Serial.print(", ");
    Serial.println(Z_out);
  }

  // Sampling delay (100ms → 10 Hz sampling rate)
  delay(100);
}