"""
serial_reader.py

This module handles real-time serial communication with the microcontroller
(Arduino/ESP32) and applies multiple validation filters to ensure data quality.

Its main responsibilities are:
1. Checking if the serial port is available
2. Establishing a stable connection
3. Reading incoming sensor data
4. Filtering out noisy, corrupted, or unrealistic values
5. Returning only validated samples for processing

This acts as a data quality gate before values enter the main system.
"""

import serial
import time
from serial.tools import list_ports

# Serial port configuration for the connected device
PORT = "/dev/cu.usbmodemDCDA0C20FC482"
BAUD = 115200

# -------------------------------
# Data validation thresholds
# -------------------------------

# Allowed raw sensor value range (to reject corrupted readings)
RAW_MIN = -5000
RAW_MAX = 5000

# Maximum allowed change between consecutive samples (noise filtering)
MAX_DELTA_XY = 300
MAX_DELTA_Z = 300

# Maximum allowed vibration magnitude (final sanity check)
MAX_MAGNITUDE = 5000

# Stores previous valid sample for spike detection
_last_sample = None


def port_available():
    # Checks whether the configured serial port is currently connected
    ports = [p.device for p in list_ports.comports()]
    return PORT in ports


def connect_once():
    # Establishes a serial connection and allows time for device reset
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    return ser


def in_raw_bounds(x, y, z):
    # Ensures raw values are within expected physical limits
    # This helps filter out corrupted or garbage readings
    return (
        RAW_MIN <= x <= RAW_MAX and
        RAW_MIN <= y <= RAW_MAX and
        RAW_MIN <= z <= RAW_MAX
    )


def passes_spike_filter(x, y, z):
    """
    Prevents sudden unrealistic jumps between consecutive readings.
    This helps reduce noise and communication glitches.
    """

    global _last_sample

    # First sample is always accepted
    if _last_sample is None:
        return True

    prev_x, prev_y, prev_z = _last_sample

    # Reject if change is too abrupt (likely noise)
    if abs(x - prev_x) > MAX_DELTA_XY:
        return False
    if abs(y - prev_y) > MAX_DELTA_XY:
        return False
    if abs(z - prev_z) > MAX_DELTA_Z:
        return False

    return True


def passes_magnitude_check(magnitude):
    # Final safety check to reject extreme outliers
    return magnitude <= MAX_MAGNITUDE


def validate_sample(x, y, z):
    """
    Runs all validation checks on incoming sensor data.

    A sample is only accepted if:
    - It is within raw sensor bounds
    - It does not contain sudden spikes
    - Its magnitude is physically reasonable
    """

    if not in_raw_bounds(x, y, z):
        return False

    if not passes_spike_filter(x, y, z):
        return False

    magnitude = (x**2 + y**2 + z**2) ** 0.5

    if not passes_magnitude_check(magnitude):
        return False

    return True


def read_line(ser):
    """
    Reads a single line from the serial buffer and returns validated data.

    Returns:
        tuple (x, y, z) if valid
        None if data is invalid or corrupted
    """

    global _last_sample

    try:
        # Read and decode serial input line
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            return None

        # Expected format: x,y,z
        parts = line.split(",")
        if len(parts) != 3:
            return None

        # Convert values to integers
        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2])

        # Apply full validation pipeline
        if not validate_sample(x, y, z):
            return None

        # Store last valid sample for future spike detection
        _last_sample = (x, y, z)

        return x, y, z

    except serial.SerialException:
        # Re-raise hardware communication errors
        raise
    except OSError:
        # Re-raise OS-level serial issues
        raise
    except ValueError:
        # Handle corrupted numeric data safely
        return None