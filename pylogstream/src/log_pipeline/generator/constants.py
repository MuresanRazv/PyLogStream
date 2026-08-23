from enum import Enum
from http import HTTPStatus


class HTTPEndpoint(Enum):
    HOME = "/"
    LOGIN = "/login"
    LOGOUT = "/logout"
    DASHBOARD = "/dashboard"
    PROFILE = "/profile"
    SETTINGS = "/settings"
    SEARCH = "/search"
    UPLOAD = "/upload"
    DOWNLOAD = "/download"


ANOMALY_PROBABILITY = 0.01  # 1% chance of generating an anomalous log line
ANOMALY_BATCH_SIZE = 50  # Number of anomalous log lines to generate in a batch
ANOMALY_STATUS_CODES = [
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.SERVICE_UNAVAILABLE,
    HTTPStatus.GATEWAY_TIMEOUT,
    HTTPStatus.UNAUTHORIZED,
]
ANOMALY_ENDPOINTS = [
    HTTPEndpoint.LOGIN,
    HTTPEndpoint.UPLOAD,
    HTTPEndpoint.DOWNLOAD,
]

DEFAULT_LINES_TO_GENERATE = 1_000_000  # Number of log lines to generate
DEFAULT_OUTPUT_PATH = "logs.txt"  # Default output file path
