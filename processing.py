"""
processing.py

This file contains all signal processing functions used in the system
to extract meaningful vibration features from raw sensor data.

These features are calculated from a rolling window of values and are
used for:
- baseline modelling
- anomaly detection
- health monitoring of the motor system

Each function represents a standard vibration analysis metric.
"""

import math
import statistics


def compute_rms(values):
    # RMS (Root Mean Square) represents overall signal energy.
    # It is one of the most important indicators of vibration intensity.
    if len(values) == 0:
        return 0
    return math.sqrt(sum(v ** 2 for v in values) / len(values))


def compute_peak(values):
    # Peak value captures the highest absolute vibration spike.
    # Useful for detecting sudden shocks or abnormal events.
    if not values:
        return 0
    return max(abs(v) for v in values)


def compute_variance(values):
    # Variance measures how spread out the signal is.
    # Higher variance usually means unstable or noisy behaviour.
    if len(values) < 2:
        return 0
    return statistics.pvariance(values)


def compute_crest_factor(values):
    # Crest factor is the ratio of peak to RMS.
    # It helps identify impulsive or irregular vibration patterns.
    rms = compute_rms(values)
    if rms <= 0:
        return 0
    peak = compute_peak(values)
    return peak / rms


def compute_kurtosis(values):
    """
    Kurtosis measures how spiky a signal is.

    In vibration analysis:
    - Normal signals ≈ 3
    - Higher values indicate sharp peaks or faults
    """

    n = len(values)
    if n < 4:
        return 0

    # Mean of the dataset
    mean_val = statistics.mean(values)

    # Variance (spread of signal)
    variance = statistics.pvariance(values)

    # Prevent division by near-zero variance
    if variance <= 1e-12:
        return 0

    # Fourth moment (used for kurtosis calculation)
    fourth_moment = sum((x - mean_val) ** 4 for x in values) / n

    return fourth_moment / (variance ** 2)