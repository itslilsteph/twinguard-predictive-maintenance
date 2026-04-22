"""
read.py

This script is used to collect raw vibration data directly from an Arduino/ESP32
via serial communication.

It continuously reads X, Y, Z accelerometer values and stores them into a CSV file
for offline analysis and model testing.

This is mainly used during data collection phase of the project.
"""

import serial
import csv
from datetime import datetime
import os

# Serial port configuration for the connected microcontroller
PORT = "/dev/cu.usbmodemDCDA0C20FC482"
BAUD = 115200

# Base directory where all recorded datasets will be saved
BASE_DIR = "/Users/steph/Desktop/fyp"

# Create a unique filename using timestamp to avoid overwriting data
filename = os.path.join(
    BASE_DIR,
    f"motor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)

# Open serial connection to Arduino/ESP32
ser = serial.Serial(PORT, BAUD, timeout=1)

print(f"Connected to {PORT}")
print(f"Saving to: {filename}")

# Create and open CSV file for writing sensor data
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)

    # Write header row for clarity in dataset
    writer.writerow(["x", "y", "z"])

    try:
        # Continuous data collection loop
        while True:
            # Read a line from serial buffer
            line = ser.readline().decode(errors="ignore").strip()

            # Skip empty lines
            if not line:
                continue

            # Expecting format: x,y,z
            parts = line.split(",")
            if len(parts) != 3:
                continue

            try:
                # Convert incoming values to integers
                x = int(parts[0])
                y = int(parts[1])
                z = int(parts[2])

                # Save data to CSV file
                writer.writerow([x, y, z])

                # Print live values for debugging/monitoring
                print(f"x={x}, y={y}, z={z}")

            except ValueError:
                # Skip corrupted or non-numeric data
                continue

    except KeyboardInterrupt:
        # Allow safe exit using Ctrl+C without corrupting file
        print("\nStopped. File saved successfully.")

# Close serial connection properly
ser.close()