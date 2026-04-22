"""
fft_analysis.py

This script is used for offline frequency analysis of motor vibration data.

It loads recorded sensor data from a CSV file, computes the vibration magnitude,
and then performs a Fast Fourier Transform (FFT) to extract frequency components.

The main goal is to identify dominant vibration frequencies in the motor,
which can help in fault detection (e.g., imbalance, misalignment, bearing issues).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Path to recorded dataset (this is updated depending on the file needed to be analysed)
FILE_NAME = "/Users/steph/Desktop/fyp/motor_data_20260320_174312.csv"

# Load CSV file into a DataFrame
df = pd.read_csv(FILE_NAME)

# Compute vibration magnitude from 3-axis accelerometer data
# This gives a single combined signal representing overall vibration strength
magnitude = np.sqrt(df["x"]**2 + df["y"]**2 + df["z"]**2)

# Remove DC offset (important step in signal processing)
# This ensures FFT focuses on vibration changes rather than constant bias
magnitude = magnitude - np.mean(magnitude)

# Sampling frequency (based on Arduino delay of 100ms → 10 samples per second)
fs = 10

# Number of samples in the signal
N = len(magnitude)

# Perform Fast Fourier Transform to move from time domain → frequency domain
fft_vals = np.fft.fft(magnitude)

# Generate corresponding frequency values for each FFT bin
freqs = np.fft.fftfreq(N, d=1/fs)

# We only use the positive half of the spectrum (real signals are symmetric)
positive_freqs = freqs[:N // 2]
positive_magnitude = np.abs(fft_vals[:N // 2])

# Plot frequency spectrum
plt.figure(figsize=(12, 6))
plt.plot(positive_freqs, positive_magnitude)

plt.title("FFT of Motor Vibration Signal")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Amplitude")
plt.grid(True)

plt.show()