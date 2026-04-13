import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

FILE_NAME = "/Users/steph/Desktop/fyp/motor_data_20260320_174312.csv"

df = pd.read_csv(FILE_NAME)

# Compute magnitude
df["magnitude"] = np.sqrt(df["x"]**2 + df["y"]**2 + df["z"]**2)

# RMS calculation
rms = np.sqrt(np.mean(df["magnitude"]**2))

print(f"RMS Vibration: {rms}")

threshold = 297  # adjust based on your data

if rms > threshold:
    print("⚠️ Fault detected")
else:
    print("✅ Motor operating normally")

plt.figure(figsize=(12, 6))
plt.plot(df["magnitude"])

plt.title("Motor Vibration Magnitude")
plt.xlabel("Sample Number")
plt.ylabel("Acceleration Magnitude")
plt.grid(True)

plt.show()