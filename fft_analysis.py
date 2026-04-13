import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

FILE_NAME = "/Users/steph/Desktop/fyp/motor_data_20260320_174312.csv"   # replace this

# Load data
df = pd.read_csv(FILE_NAME)

# Magnitude signal
magnitude = np.sqrt(df["x"]**2 + df["y"]**2 + df["z"]**2)

# Remove DC offset (very important)
magnitude = magnitude - np.mean(magnitude)

# Sampling frequency
fs = 10   # because your Arduino delay is 100 ms => 10 samples/sec

# FFT
N = len(magnitude)
fft_vals = np.fft.fft(magnitude)
freqs = np.fft.fftfreq(N, d=1/fs)

# Keep only positive frequencies
positive_freqs = freqs[:N // 2]
positive_magnitude = np.abs(fft_vals[:N // 2])

# Plot
plt.figure(figsize=(12, 6))
plt.plot(positive_freqs, positive_magnitude)
plt.title("FFT of Motor Vibration Signal")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.grid(True)
plt.show()