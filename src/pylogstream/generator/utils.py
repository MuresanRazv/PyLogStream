import random
from collections.abc import Sequence
from datetime import datetime
from http import HTTPStatus

from pylogstream.models.logs import WeightedHTTPStatus

HTTP_STATUS_WEIGHTS: Sequence[WeightedHTTPStatus] = [
    WeightedHTTPStatus(HTTPStatus.OK, 0.8),
    WeightedHTTPStatus(HTTPStatus.NOT_FOUND, 0.10),
    WeightedHTTPStatus(HTTPStatus.BAD_REQUEST, 0.05),
    WeightedHTTPStatus(HTTPStatus.UNAUTHORIZED, 0.03),
    WeightedHTTPStatus(HTTPStatus.INTERNAL_SERVER_ERROR, 0.02),
]


def get_weighted_random_http_status() -> bytes:
    """
    Returns a random HTTP status code based on the defined weights.
    """
    statuses = [status.status for status in HTTP_STATUS_WEIGHTS]
    weights = [status.weight for status in HTTP_STATUS_WEIGHTS]
    return random.choices(statuses, weights=weights, k=1)[0].value.to_bytes(3, "big")


def pre_generate_ipv4_address() -> Sequence[bytes]:
    """Pre-generates a fixed pool of IP addresses."""
    return [f"192.168.1.{i}".encode("ascii") for i in range(1, 255)]


def generate_nginx_timestamp(date: datetime) -> bytes:
    """
    Generates a timestamp in the Nginx log format.
    Example: 10/Oct/2000:13:55:36 -0700
    """
    return date.strftime("%d/%b/%Y:%H:%M:%S %z").encode("ascii")
