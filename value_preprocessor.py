import math
from numbers import Real


def preprocess_metric_value(value: Real) -> Real:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("Metric value must be a real number")
    if not math.isfinite(value):
        raise ValueError("Metric value must be finite")
    return value * 10 if value <= 10 else value