import statistics
from collections import deque

BASELINE_SAMPLES = 50
healthy_rms_window = deque(maxlen=180)


def update_baseline(rms):
    """
    Adaptive healthy baseline:
    - During startup, fill the baseline window
    - After that, only learn samples that look healthy
    """
    if len(healthy_rms_window) < BASELINE_SAMPLES:
        healthy_rms_window.append(rms)
        return

    mean = statistics.mean(healthy_rms_window)
    std = statistics.pstdev(healthy_rms_window)

    if std < 0.0001:
        std = 0.0001

    z = (rms - mean) / std

    if abs(z) < 2.0:
        healthy_rms_window.append(rms)


def get_baseline():
    if not healthy_rms_window:
        return 0, 0

    mean = statistics.mean(healthy_rms_window)
    std = statistics.pstdev(healthy_rms_window) if len(healthy_rms_window) > 1 else 0
    return mean, std


def classify(z_score):
    z = abs(z_score)

    if z < 2:
        return "✅ Normal", "None"
    elif z < 3:
        return "🟡 Mild Fault", "Mild"
    elif z < 4:
        return "🟠 Moderate Fault", "Moderate"
    else:
        return "🔴 Critical Fault", "Critical"