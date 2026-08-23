import random

from log_pipeline.constants import (
    ANOMALY_PROBABILITY,
)


def should_inject_anomaly() -> bool:
    """
    Determines whether to inject an anomaly based on the given probability.

    Args:
        anomaly_probability (float): The probability of injecting an anomaly

    Returns:
        bool: True if an anomaly should be injected, False otherwise.
    """
    return random.random() < ANOMALY_PROBABILITY
