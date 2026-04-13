import serial
import time
from serial.tools import list_ports

PORT = "/dev/cu.usbmodemDCDA0C20FC482"
BAUD = 115200

# Validation settings
RAW_MIN = -5000
RAW_MAX = 5000
MAX_DELTA_XY = 300
MAX_DELTA_Z = 300
MAX_MAGNITUDE = 5000

_last_sample = None


def port_available():
    ports = [p.device for p in list_ports.comports()]
    return PORT in ports


def connect_once():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    return ser


def in_raw_bounds(x, y, z):
    return (
        RAW_MIN <= x <= RAW_MAX and
        RAW_MIN <= y <= RAW_MAX and
        RAW_MIN <= z <= RAW_MAX
    )


def passes_spike_filter(x, y, z):
    global _last_sample

    if _last_sample is None:
        return True

    prev_x, prev_y, prev_z = _last_sample

    if abs(x - prev_x) > MAX_DELTA_XY:
        return False
    if abs(y - prev_y) > MAX_DELTA_XY:
        return False
    if abs(z - prev_z) > MAX_DELTA_Z:
        return False

    return True


def passes_magnitude_check(magnitude):
    return magnitude <= MAX_MAGNITUDE


def validate_sample(x, y, z):
    if not in_raw_bounds(x, y, z):
        return False

    if not passes_spike_filter(x, y, z):
        return False

    magnitude = (x**2 + y**2 + z**2) ** 0.5
    if not passes_magnitude_check(magnitude):
        return False

    return True


def read_line(ser):
    global _last_sample

    try:
        line = ser.readline().decode(errors="ignore").strip()

        if not line:
            return None

        parts = line.split(",")
        if len(parts) != 3:
            return None

        x = int(parts[0])
        y = int(parts[1])
        z = int(parts[2])

        if not validate_sample(x, y, z):
            return None

        _last_sample = (x, y, z)
        return x, y, z

    except serial.SerialException:
        raise
    except OSError:
        raise
    except ValueError:
        return None