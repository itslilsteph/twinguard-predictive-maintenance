import csv
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "full_log.csv")
FAULT_LOG = os.path.join(LOG_DIR, "fault_log.csv")

os.makedirs(LOG_DIR, exist_ok=True)


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

    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    if not os.path.exists(FAULT_LOG):
        with open(FAULT_LOG, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


init_logs()


def log_row(row, severity):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    if severity in ["Mild", "Moderate", "Critical"]:
        with open(FAULT_LOG, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)


def compute_insights():
    if not os.path.exists(LOG_FILE):
        return 0, "None", 0

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    fault_count = 0
    last_fault_time = "None"
    max_deviation = 0

    with open(LOG_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                ts = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")

                if ts < today_start:
                    continue

                deviation = float(row["deviation"])
                severity = row["severity"]

                if deviation > max_deviation:
                    max_deviation = deviation

                if severity in ["Mild", "Moderate", "Critical"]:
                    fault_count += 1
                    last_fault_time = ts.strftime("%H:%M:%S")

            except Exception:
                continue

    return fault_count, last_fault_time, round(max_deviation, 2)