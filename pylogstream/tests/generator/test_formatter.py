import re

from log_pipeline.generator.formatter import generate_log_line

# Basic regex for Nginx combined log format
NGINX_LOG_REGEX = (
    r"^(?P<ip>[\d\.]+) - - \[(?P<time>[^\]]+)\] "
    r'"(?P<method>\w+) (?P<path>[^\s]+) [^"]+" '
    r"(?P<status>\d{3}) (?P<bytes>\d+) "
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"\n$'
)


def test_format_log_line() -> None:
    log_line = generate_log_line()
    assert re.match(NGINX_LOG_REGEX, str(log_line)), (
        f"Log line does not match regex: {log_line}"
    )
