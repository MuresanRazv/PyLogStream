from http import HTTPMethod, HTTPStatus

HTTP_STATUS_CODES = [b"200", b"200", b"200", b"201", b"204", b"301", b"304"]
HTTP_METHODS = [m.value.encode("ascii") for m in HTTPMethod]
HTTP_ENDPOINTS: tuple[bytes, ...] = (
    b"/wp-admin",
    b"/wp-login",
    b"/.env",
    b"/config.",
    b"/phpmyadmin",
    b"/.git",
    b"/etc/passwd",
    b"/xmlrpc.php",
    b"/actuator",
    b"/admin",
    b"/",
    b"/login",
    b"/logout",
    b"/dashboard",
    b"/profile",
    b"/settings",
    b"/search",
    b"/upload",
    b"/download",
)
HTTP_REFERERS = [
    b"https://www.google.com",
    b"https://www.bing.com",
    b"https://www.yahoo.com",
    b"https://www.example.com",
    b"https://www.test.com",
]
HTTP_USER_AGENTS = [
    b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    b"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    b"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    b"Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    b"Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

ANOMALY_PROBABILITY = 0.01  # 1% chance of generating an anomalous log line
ANOMALY_BATCH_SIZE = 50  # Number of anomalous log lines to generate in a batch
ANOMALY_STATUS_CODES = [
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.SERVICE_UNAVAILABLE,
    HTTPStatus.GATEWAY_TIMEOUT,
    HTTPStatus.UNAUTHORIZED,
]
ANOMALY_ENDPOINTS: tuple[bytes, ...] = (
    b"/wp-admin",
    b"/wp-login",
    b"/.env",
    b"/config.",
    b"/phpmyadmin",
    b"/.git",
    b"/etc/passwd",
    b"/xmlrpc.php",
    b"/actuator",
    b"/admin",
)

DEFAULT_LINES_TO_GENERATE = 1_000_000  # Number of log lines to generate
DEFAULT_OUTPUT_PATH = "logs.txt"  # Default output file path
