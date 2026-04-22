"""
model.py

This file contains the baseline learning model and classification logic
used for anomaly detection in the vibration monitoring system.

It performs three main roles:
1. Maintains an adaptive "healthy" baseline using RMS values.
2. Computes statistical reference values (mean and standard deviation).
3. Classifies system behaviour based on z-score thresholds.

This is the core decision-making part of the system that determines
whether the machine is operating normally or showing signs of fault.
"""

import statistics
from collections import deque

# Number of samples required before baseline stabilises
BASELINE_SAMPLES = 50

# Rolling window that stores RMS values considered "healthy"
# This is used to continuously update the baseline over time
healthy_rms_window = deque(maxlen=180)


def update_baseline(rms):
    """
    Updates the adaptive baseline using incoming RMS values.
    - During startup, initial RMS values are collected as reference data
    - After that, only values that look "normal" are accepted based on z-score filtering
    """

    # Fill initial baseline window during system startup
    if len(healthy_rms_window) < BASELINE_SAMPLES:
        healthy_rms_window.append(rms)
        return

    # Calculate current mean and spread of "healthy" values
    mean = statistics.mean(healthy_rms_window)
    std = statistics.pstdev(healthy_rms_window)

    # Prevent division errors when signal is too stable
    if std < 0.0001:
        std = 0.0001

    # Compute how far the new sample is from the baseline
    z = (rms - mean) / std

    # Only update baseline if the value still looks normal
    # This prevents faulty readings from corrupting the model
    if abs(z) < 2.0:
        healthy_rms_window.append(rms)


def get_baseline():
    """
    Returns the current baseline mean and standard deviation.
    This is used by the main system for z-score calculation.
    """

    if not healthy_rms_window:
        return 0, 0

    mean = statistics.mean(healthy_rms_window)
    std = statistics.pstdev(healthy_rms_window) if len(healthy_rms_window) > 1 else 0

    return mean, std


def classify(z_score):
    """
    Classifies machine health based on z-score deviation.

    The thresholds are based on statistical deviation rules:
    - Low deviation is Normal
    - Moderate deviation is a Mild/Moderate fault
    - High deviation is a Critical fault
    """

    z = abs(z_score)

    if z < 2:
        return "✅ Normal", "None"
    elif z < 3:
        return "🟡 Mild Fault", "Mild"
    elif z < 4:
        return "🟠 Moderate Fault", "Moderate"
    else:
        return "🔴 Critical Fault", "Critical"