#include <Wire.h>

#define ADXL345 0x53    // I2C address for ADXL345
#define IN1 6           // Motor control pin 1
#define IN2 7           // Motor control pin 2

int16_t X_out, Y_out, Z_out;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  // Start the motor (IN1 HIGH, IN2 LOW = forward)
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  // Configure ADXL345: Data Format Register (0x31)
  // 0x0B = Full resolution, +/- 16g, right-justified
  Wire.beginTransmission(ADXL345);
  Wire.write(0x31);
  Wire.write(0x0B);
  Wire.endTransmission();

  // Enable ADXL345 Measurement Mode (0x2D)
  Wire.beginTransmission(ADXL345);
  Wire.write(0x2D);
  Wire.write(0x08);
  Wire.endTransmission();

  Serial.println("Motor + Accelerometer running...");
}

void loop() {
  // Request 6 bytes starting at DATAX0 (0x32)
  Wire.beginTransmission(ADXL345);
  Wire.write(0x32);
  Wire.endTransmission(false);

  Wire.requestFrom(ADXL345, 6);

  if (Wire.available() == 6) {
    uint8_t x0 = Wire.read();
    uint8_t x1 = Wire.read();
    uint8_t y0 = Wire.read();
    uint8_t y1 = Wire.read();
    uint8_t z0 = Wire.read();
    uint8_t z1 = Wire.read();

    // Combine high + low bytes
    X_out = (x1 << 8) | x0;
    Y_out = (y1 << 8) | y0;
    Z_out = (z1 << 8) | z0;

    // Output to Serial Monitor
    Serial.print(X_out);
    Serial.print(", ");
    Serial.print(Y_out);
    Serial.print(", ");
    Serial.println(Z_out);
  }

  delay(100);
}