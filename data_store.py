"""
data_store.py

This file acts as a shared in-memory storage for the system.

It holds:
- The latest sensor readings (x, y, z)
- Real-time computed health status of the machine
- Statistical features like RMS, variance, peak, etc.
- A rolling history buffer used for plotting and analysis

Basically, this is the central place where both live data and short-term history are stored
so different parts of the system (Flask app, processing module, dashboard) can access them easily.
"""

# Holds the latest processed sensor values and system status
data = {
    "x": 0,
    "y": 0,
    "z": 0,
    "status": "Waiting...",
    "health": "Calibrating...",
    "severity": "None",
    "rms": 0,
    "baseline": 0,
    "deviation": 0,
    "percent_deviation": 0,
    "temperature": "--",
    "z_score": 0,
    "std_dev": 0,
    "peak": 0,
    "variance": 0,
    "crest_factor": 0,
    "kurtosis": 0
}

# Stores recent samples for plotting and time-series analysis
# This acts like a sliding window over the latest sensor readings
history = {
    "x": [],
    "y": [],
    "z": [],
    "mag": []
}