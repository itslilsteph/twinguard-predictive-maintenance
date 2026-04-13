import math
import statistics


def compute_rms(values):
    if len(values) == 0:
        return 0
    return math.sqrt(sum(v ** 2 for v in values) / len(values))


def compute_peak(values):
    if not values:
        return 0
    return max(abs(v) for v in values)


def compute_variance(values):
    if len(values) < 2:
        return 0
    return statistics.pvariance(values)


def compute_crest_factor(values):
    rms = compute_rms(values)
    if rms <= 0:
        return 0
    peak = compute_peak(values)
    return peak / rms


def compute_kurtosis(values):
    """
    Pearson kurtosis:
    E[(x-mu)^4] / sigma^4
    Normal distribution is about 3.
    """
    n = len(values)
    if n < 4:
        return 0

    mean_val = statistics.mean(values)
    variance = statistics.pvariance(values)

    if variance <= 1e-12:
        return 0

    fourth_moment = sum((x - mean_val) ** 4 for x in values) / n
    return fourth_moment / (variance ** 2)