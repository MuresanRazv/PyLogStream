import random
from collections.abc import Sequence
from datetime import datetime
from http import HTTPStatus

from log_pipeline.models.logs import WeightedHTTPStatus

HTTP_STATUS_WEIGHTS: Sequence[WeightedHTTPStatus] = [
    WeightedHTTPStatus(HTTPStatus.OK, 0.8),
    WeightedHTTPStatus(HTTPStatus.NOT_FOUND, 0.10),
    WeightedHTTPStatus(HTTPStatus.BAD_REQUEST, 0.05),
    WeightedHTTPStatus(HTTPStatus.UNAUTHORIZED, 0.03),
    WeightedHTTPStatus(HTTPStatus.INTERNAL_SERVER_ERROR, 0.02),
]


def get_weighted_random_http_status() -> HTTPStatus:
    """
    Returns a random HTTP status code based on the defined weights.
    """
    statuses = [status.status for status in HTTP_STATUS_WEIGHTS]
    weights = [status.weight for status in HTTP_STATUS_WEIGHTS]
    return random.choices(statuses, weights=weights, k=1)[0]


def generate_ipv4_address() -> str:
    """
    Generates a random IPv4 address.
    """
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


def generate_nginx_timestamp(date: datetime) -> str:
    """
    Generates a timestamp in the Nginx log format.
    Example: 10/Oct/2000:13:55:36 -0700
    """
    return date.strftime("%d/%b/%Y:%H:%M:%S %z")
