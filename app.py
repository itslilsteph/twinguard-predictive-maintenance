"""
app.py

This is the main Flask backend for the TwinGuard system.

It handles:
- Real-time sensor data processing (from serial + WiFi)
- Feature extraction (RMS, peak, variance, etc.)
- Health classification using a simple statistical model
- Logging of sensor data
- Serving data to the frontend dashboard
- User authentication (basic admin login)
"""

from flask import Flask, render_template, jsonify, send_file, request, redirect, url_for, session
import threading
import time
import math
import csv
from datetime import datetime
from io import StringIO, BytesIO
from functools import wraps

from data_store import data, history
from processing import (
    compute_rms,
    compute_peak,
    compute_variance,
    compute_crest_factor,
    compute_kurtosis,
)
from model import update_baseline, get_baseline, classify
from serial_reader import connect_once, read_line, port_available
from logger import log_row, compute_insights, LOG_FILE, FAULT_LOG

# Initialize Flask application
app = Flask(__name__)
app.secret_key = "twinguard_secret_key_change_this_later"

# Maximum number of points stored in memory for live plotting
MAX_POINTS = 50

# Simple hardcoded admin credentials (used for login protection)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "twinguard123"


def login_required(func):
    """
    Decorator to restrict access to authenticated users only.
    Redirects to login page if user is not logged in.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def reset_live_values():
    """
    Resets all live system values when connection fails or resets.
    This ensures the dashboard doesn't show stale or misleading data.
    """
    data["x"] = 0
    data["y"] = 0
    data["z"] = 0
    data["health"] = "N/A"
    data["severity"] = "N/A"
    data["rms"] = 0
    data["baseline"] = 0
    data["deviation"] = 0
    data["percent_deviation"] = 0
    data["temperature"] = "--"
    data["z_score"] = 0
    data["std_dev"] = 0
    data["peak"] = 0
    data["variance"] = 0
    data["crest_factor"] = 0
    data["kurtosis"] = 0


def update_history(x: int, y: int, z: int, magnitude: float) -> None:
    """
    Keeps a rolling window of sensor history for plotting and analysis.
    Old values are removed once MAX_POINTS is exceeded.
    """
    history["x"].append(x)
    history["y"].append(y)
    history["z"].append(z)
    history["mag"].append(magnitude)

    if len(history["x"]) > MAX_POINTS:
        for key in history:
            history[key].pop(0)


def process_sample(x: int, y: int, z: int, source: str = "serial") -> float:
    """
    Core processing function.

    Takes raw sensor input, computes vibration features,
    updates model baseline, and determines machine health status.
    """
    magnitude = math.sqrt(x**2 + y**2 + z**2)

    # Update latest raw values
    data["x"] = x
    data["y"] = y
    data["z"] = z
    data["status"] = "Running"

    # Store into rolling history buffer
    update_history(x, y, z, magnitude)

    mag_window = history["mag"]

    # Feature extraction from vibration signal
    rms = compute_rms(mag_window)
    peak = compute_peak(mag_window)
    variance = compute_variance(mag_window)
    crest_factor = compute_crest_factor(mag_window)
    kurtosis = compute_kurtosis(mag_window)

    # Store computed features
    data["rms"] = round(rms, 2)
    data["peak"] = round(peak, 2)
    data["variance"] = round(variance, 4)
    data["crest_factor"] = round(crest_factor, 4)
    data["kurtosis"] = round(kurtosis, 4)

    # Update adaptive baseline model
    update_baseline(rms)

    baseline, std_dev = get_baseline()

    # Avoid division errors
    std_for_z = std_dev if std_dev >= 0.0001 else 0.0001

    # Statistical deviation scoring
    z_score = (rms - baseline) / std_for_z if baseline != 0 else 0
    deviation = abs(rms - baseline)
    percent_deviation = (deviation / baseline) if baseline != 0 else 0

    # Health classification based on model state
    if baseline == 0 and std_dev == 0:
        data["health"] = "Calibrating..."
        data["severity"] = "None"
        data["z_score"] = 0
    else:
        health, severity = classify(z_score)
        data["health"] = health
        data["severity"] = severity
        data["z_score"] = round(z_score, 2)

    # Store final computed values
    data["baseline"] = round(baseline, 2)
    data["std_dev"] = round(std_dev, 4)
    data["deviation"] = round(deviation, 2)
    data["percent_deviation"] = round(percent_deviation * 100, 2)

    data["source"] = source

    return magnitude


def log_current_sample(x: int, y: int, z: int, magnitude: float) -> None:
    """
    Logs the current processed sample into CSV files.
    Also separates normal logs and fault logs.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        timestamp,
        x,
        y,
        z,
        round(magnitude, 2),
        data["rms"],
        data["baseline"],
        data["deviation"],
        data["temperature"],
        data["health"],
        data["severity"],
        data["status"],
    ]

    log_row(row, data["severity"])


def serial_worker() -> None:
    """
    Background thread that continuously reads data from the serial port,
    processes it, and logs it at a controlled interval.
    """
    last_log_time = 0

    while True:
        ser = None
        try:
            # Check if device is connected
            if not port_available():
                data["status"] = "Failed"
                reset_live_values()
                time.sleep(2)
                continue

            data["status"] = "Connecting..."
            ser = connect_once()
            data["status"] = "Running"

            while True:
                sample = read_line(ser)

                if sample is None:
                    continue

                x, y, z = sample
                magnitude = process_sample(x, y, z, source="serial")

                # Log once per second to avoid excessive file writes
                now = time.time()
                if now - last_log_time >= 1.0:
                    log_current_sample(x, y, z, magnitude)
                    last_log_time = now

        except Exception as e:
            print(f"Serial worker error: {e}")
            data["status"] = "Failed"
            reset_live_values()

        finally:
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass

            time.sleep(2)


def parse_timestamp(ts_str: str) -> datetime:
    # Converts timestamp string into datetime object for filtering
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


def safe_float(v):
    # Safely converts values to float (avoids crashing on bad data)
    try:
        return float(v)
    except Exception:
        return None


def read_log_rows(path: str):
    # Reads CSV log files and converts timestamps for processing
    rows = []
    try:
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["_dt"] = parse_timestamp(row["timestamp"])
                    rows.append(row)
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return rows


def apply_time_filter(rows, period, start_dt=None, end_dt=None):
    """
    Filters logs based on time range (today, week, month, custom, etc.)
    """
    from datetime import timedelta

    now = datetime.now()

    if period == "today":
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return [r for r in rows if r["_dt"] >= cutoff]

    if period == "week":
        cutoff = now - timedelta(days=7)
        return [r for r in rows if r["_dt"] >= cutoff]

    if period == "month":
        cutoff = now - timedelta(days=30)
        return [r for r in rows if r["_dt"] >= cutoff]

    if period == "year":
        cutoff = now - timedelta(days=365)
        return [r for r in rows if r["_dt"] >= cutoff]

    if period == "custom":
        if start_dt is not None:
            rows = [r for r in rows if r["_dt"] >= start_dt]
        if end_dt is not None:
            rows = [r for r in rows if r["_dt"] <= end_dt]
        return rows

    return rows


def bucket_key(dt: datetime, view_by: str):
    """
    Groups timestamps into time buckets for aggregation (minute, hour, day, etc.)
    """
    from datetime import timedelta

    if view_by == "second":
        return dt.replace(microsecond=0)
    if view_by == "minute":
        return dt.replace(second=0, microsecond=0)
    if view_by == "10min":
        minute = (dt.minute // 10) * 10
        return dt.replace(minute=minute, second=0, microsecond=0)
    if view_by == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if view_by == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if view_by == "week":
        week_start = dt - timedelta(days=dt.weekday())
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    if view_by == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return dt.replace(microsecond=0)


def aggregate_rows(rows, view_by):
    """
    Aggregates raw log rows into grouped summaries for visualization.
    """
    buckets = {}

    for row in rows:
        key = bucket_key(row["_dt"], view_by)
        buckets.setdefault(key, []).append(row)

    aggregated = []

    for key in sorted(buckets.keys()):
        group = buckets[key]

        numeric_fields = ["x", "y", "z", "magnitude", "rms", "baseline", "deviation", "temperature"]
        agg = {
            "timestamp": key.strftime("%Y-%m-%d %H:%M:%S")
        }

        for field in numeric_fields:
            vals = [safe_float(r[field]) for r in group if safe_float(r[field]) is not None]
            agg[field] = round(sum(vals) / len(vals), 2) if vals else "--"

        latest = group[-1]
        agg["health"] = latest["health"]
        agg["severity"] = latest["severity"]
        agg["status"] = latest["status"]

        aggregated.append(agg)

    return aggregated


def filter_and_aggregate(rows, period, view_by, start_dt=None, end_dt=None):
    # Combines filtering + aggregation into a single pipeline
    filtered = apply_time_filter(rows, period, start_dt, end_dt)
    aggregated = aggregate_rows(filtered, view_by)
    return list(reversed(aggregated))


# ---------------------------
# Flask Routes
# ---------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    # Handles user authentication for dashboard access
    if session.get("logged_in"):
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    # Clears session and logs user out
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    # Main dashboard page
    return render_template("index.html")


@app.route("/logs")
@login_required
def logs_page():
    # Logs viewer page
    return render_template("logs.html")


@app.route("/data")
@login_required
def get_data():
    # Sends live system data to frontend dashboard (AJAX polling)
    fault_count, last_fault_time, max_deviation = compute_insights()

    return jsonify({
        "x": data["x"],
        "y": data["y"],
        "z": data["z"],
        "status": data["status"],
        "health": data["health"],
        "severity": data["severity"],
        "rms": data["rms"],
        "baseline": data["baseline"],
        "deviation": data["deviation"],
        "percent_deviation": data["percent_deviation"],
        "temperature": data["temperature"],
        "z_score": data["z_score"],
        "std_dev": data["std_dev"],
        "peak": data["peak"],
        "variance": data["variance"],
        "crest_factor": data["crest_factor"],
        "kurtosis": data["kurtosis"],
        "fault_count": fault_count,
        "last_fault_time": last_fault_time,
        "max_deviation_today": max_deviation,
        "history_x": history["x"],
        "history_y": history["y"],
        "history_z": history["z"],
        "history_mag": history["mag"],
        "source": data.get("source", "serial"),
    })


@app.route("/ingest", methods=["POST"])
def ingest():
    """
    ESP32 endpoint for sending sensor data over WiFi.
    """
    payload = request.get_json(silent=True)

    if not payload:
        return jsonify({"ok": False, "error": "No JSON received"}), 400

    try:
        x = int(payload["x"])
        y = int(payload["y"])
        z = int(payload["z"])

        if "temperature" in payload:
            data["temperature"] = payload["temperature"]

        magnitude = process_sample(x, y, z, source="wifi")
        log_current_sample(x, y, z, magnitude)

        return jsonify({"ok": True}), 200

    except KeyError:
        return jsonify({"ok": False, "error": "Missing x/y/z"}), 400
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid x/y/z values"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/get_logs")
@login_required
def get_logs():
    # Returns paginated and filtered log data for frontend table/graph
    period = request.args.get("period", "today")
    view_by = request.args.get("view_by", "second")
    log_type = request.args.get("log_type", "full")
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 25)), 1), 100)

    path = LOG_FILE if log_type == "full" else FAULT_LOG
    rows = read_log_rows(path)

    start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M") if start_str else None
    end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M") if end_str else None

    result = filter_and_aggregate(rows, period, view_by, start_dt, end_dt)

    total = len(result)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paged = result[start_idx:end_idx]

    return jsonify({
        "rows": paged,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page) if total > 0 else 1,
    })


@app.route("/download_logs")
@login_required
def download_logs():
    # Exports filtered logs as CSV download
    period = request.args.get("period", "today")
    view_by = request.args.get("view_by", "second")
    log_type = request.args.get("log_type", "full")
    start_str = request.args.get("start")
    end_str = request.args.get("end")

    path = LOG_FILE if log_type == "full" else FAULT_LOG
    rows = read_log_rows(path)

    start_dt = datetime.strptime(start_str, "%Y-%m-%dT%H:%M") if start_str else None
    end_dt = datetime.strptime(end_str, "%Y-%m-%dT%H:%M") if end_str else None

    result = filter_and_aggregate(rows, period, view_by, start_dt, end_dt)

    output = StringIO()
    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "timestamp", "x", "y", "z", "magnitude",
        "rms", "baseline", "deviation",
        "temperature", "health", "severity", "status",
    ])

    # Write rows
    for row in result:
        writer.writerow([
            row["timestamp"],
            row["x"],
            row["y"],
            row["z"],
            row["magnitude"],
            row["rms"],
            row["baseline"],
            row["deviation"],
            row["temperature"],
            row["health"],
            row["severity"],
            row["status"],
        ])

    mem = BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)

    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"logs_{today_str}{period}{view_by}.csv"

    return send_file(mem, as_attachment=True, download_name=filename, mimetype="text/csv")


if __name__ == "__main__":
    # Starts background serial thread + Flask server
    thread = threading.Thread(target=serial_worker, daemon=True)
    thread.start()

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)