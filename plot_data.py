"""
plot_data.py

This script is used for offline analysis and visualization of motor vibration data.

It reads a recorded CSV file, computes vibration magnitude, and performs a simple
RMS-based check to determine whether the motor is operating normally or showing
possible fault behaviour.

It also plots the vibration signal to help visually inspect patterns in the data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Path to recorded dataset exported from the system logs
FILE_NAME = "/Users/steph/Desktop/fyp/motor_data_20260320_174312.csv"

# Load CSV file into a DataFrame for processing
df = pd.read_csv(FILE_NAME)

# Compute vibration magnitude from 3-axis accelerometer readings
# This converts raw X, Y, Z values into a single meaningful signal
df["magnitude"] = np.sqrt(df["x"]**2 + df["y"]**2 + df["z"]**2)

# Compute RMS (Root Mean Square) of the vibration signal
# RMS is used as a basic indicator of overall vibration energy
rms = np.sqrt(np.mean(df["magnitude"]**2))

print(f"RMS Vibration: {rms}")

# Simple threshold-based fault detection rule
# If RMS exceeds this value, it may indicate abnormal vibration
threshold = 297  # adjust based on dataset calibration

# Basic decision logic for system health
if rms > threshold:
    print("⚠️ Fault detected")
else:
    print("✅ Motor operating normally")

# Plot vibration magnitude over time (sample index)
plt.figure(figsize=(12, 6))
plt.plot(df["magnitude"])

plt.title("Motor Vibration Magnitude")
plt.xlabel("Sample Number")
plt.ylabel("Acceleration Magnitude")
plt.grid(True)

# Display the graph for visual inspection
plt.show()