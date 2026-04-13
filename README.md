# TwinGuard: Digital Twin-Based Predictive Maintenance System

## Overview

TwinGuard is a real-time predictive maintenance system designed to monitor electric motor health using vibration data. It combines edge signal processing with a digital twin dashboard to provide real-time visualization and anomaly detection.

## Features

- Real-time vibration monitoring (X, Y, Z axes)
- RMS, variance, crest factor, and kurtosis analysis
- Adaptive anomaly detection using statistical methods
- Digital twin dashboard for visualization
- Data logging and CSV export
- Admin login system
- Serial and Wi-Fi (ESP32) data integration

## Technologies Used

- Python (Flask)
- ESP32 Microcontroller
- ADXL345 Accelerometer
- Chart.js
- MQTT / HTTP / Serial Communication

## How to Run

1. Install dependencies:
      `
   pip install -r requirements.txt
   `

2. Run the system:
      `
   python app.py
   `

3. Open in browser:
      `
   http://localhost:5000
   `

## Login Credentials

- Username: admin
- Password: twinguard123

## Author

Stephano Mazaba
