import random
from copy import replace

from log_pipeline.generator.constants import (
    ANOMALY_ENDPOINTS,
    ANOMALY_PROBABILITY,
    ANOMALY_STATUS_CODES,
)
from log_pipeline.generator.models import LogLine


def should_inject_anomaly() -> bool:
    """
    Determines whether to inject an anomaly based on the given probability.

    Args:
        anomaly_probability (float): The probability of injecting an anomaly

    Returns:
        bool: True if an anomaly should be injected, False otherwise.
    """
    return random.random() < ANOMALY_PROBABILITY


def inject_anomaly(log_line: LogLine) -> str:
    """
    Injects an anomaly into the given log line.

    Args:
        log_line (LogLine): The original log line.

    Returns:
        str: The log line with an injected anomaly.
    """
    anomaly_status = random.choice(ANOMALY_STATUS_CODES)
    anomaly_endpoint = random.choice(ANOMALY_ENDPOINTS)
    return str(
        replace(log_line, http_status=anomaly_status, endpoint=anomaly_endpoint.value)
    )
