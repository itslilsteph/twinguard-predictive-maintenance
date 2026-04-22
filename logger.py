"""
logger.py

This file is responsible for handling all data logging and storage for the system.

It manages two main log files:
1. A full log that stores every processed sensor reading.
2. A fault log that only stores abnormal or faulty readings.

It also provides a function to compute daily insights such as:
- number of detected faults
- last fault occurrence time
- maximum deviation recorded in a day

These logs are later used for dashboard visualization and system analysis.
"""

import csv
import os
from datetime import datetime

# Directory where all log files are stored
LOG_DIR = "logs"

# File that stores all sensor readings (complete history)
LOG_FILE = os.path.join(LOG_DIR, "full_log.csv")

# File that stores only fault-related events for easier analysis
FAULT_LOG = os.path.join(LOG_DIR, "fault_log.csv")

# Ensure logging directory exists before writing files
os.makedirs(LOG_DIR, exist_ok=True)


# Creates log files with headers if they don't already exist.
# This ensures consistent CSV structure for later processing.
def init_logs():
    headers = [
        "timestamp",
        "x",
        "y",
        "z",
        "magnitude",
        "rms",
        "baseline",
        "deviation",
        "temperature",
        "health",
        "severity",
        "status"
    ]

    # Create full log file if missing
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    # Create fault log file if missing
    if not os.path.exists(FAULT_LOG):
        with open(FAULT_LOG, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


# Initialise logs at system startup
init_logs()


# Writes a processed sensor row into the log files.
# Faults are also stored separately in the fault log.
def log_row(row, severity):

    # Always store every reading in the main log file
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    # Only store abnormal events in the fault log
    # This makes it easier to review system failures
    if severity in ["Mild", "Moderate", "Critical"]:
        with open(FAULT_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)


# Extracts useful daily statistics from the log file.
# Used by the dashboard for summary insights and monitoring.
def compute_insights():

    if not os.path.exists(LOG_FILE):
        return 0, "None", 0

    # Only consider data from today for reporting
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    fault_count = 0
    last_fault_time = "None"
    max_deviation = 0

    # Read log file and process each recorded entry
    with open(LOG_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Convert timestamp back into datetime object
                ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")

                # Ignore old data outside today's window
                if ts < today_start:
                    continue

                deviation = float(row["deviation"])
                severity = row["severity"]

                # Track maximum deviation observed
                if deviation > max_deviation:
                    max_deviation = deviation

                # Count fault occurrences
                if severity in ["Mild", "Moderate", "Critical"]:
                    fault_count += 1
                    last_fault_time = ts.strftime("%H:%M:%S")

            except Exception:
                # Skip corrupted or incomplete rows safely
                continue

    return fault_count, last_fault_time, round(max_deviation, 2)