import serial
import csv
from datetime import datetime
import os

PORT = "/dev/cu.usbmodemDCDA0C20FC482"
BAUD = 115200

# Force save location to your project folder
BASE_DIR = "/Users/steph/Desktop/fyp"

filename = os.path.join(
    BASE_DIR,
    f"motor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)

ser = serial.Serial(PORT, BAUD, timeout=1)

print(f"Connected to {PORT}")
print(f"Saving to: {filename}")

with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x", "y", "z"])

    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()

            if not line:
                continue

            parts = line.split(",")
            if len(parts) != 3:
                continue

            try:
                x = int(parts[0])
                y = int(parts[1])
                z = int(parts[2])

                writer.writerow([x, y, z])
                print(f"x={x}, y={y}, z={z}")

            except ValueError:
                continue

    except KeyboardInterrupt:
        print("\nStopped. File saved successfully.")

ser.close()