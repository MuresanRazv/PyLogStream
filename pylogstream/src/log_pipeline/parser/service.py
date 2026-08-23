import re
from collections.abc import Iterator
from http import HTTPMethod, HTTPStatus
from pathlib import Path

from log_pipeline.benchmark.decorators import profile_performance
from log_pipeline.models.logs import LogLine
from log_pipeline.parser.utils import parse_timestamp

# Pre-compile the regex once at module level for C-speed matching
NGINX_COMBINED_PATTERN = re.compile(
    r"^(?P<ip>\S+)\s+"  # Client IP address
    r"\S+\s+\S+\s+"  # Identd and remote user (usually '- -')
    r"\[(?P<timestamp>[^\]]+)\]\s+"  # Timestamp inside brackets [DD/Mon/YYYY:HH:MM:SS +ZZZZ]
    r'"(?P<method>[A-Z]+)\s+'  # HTTP method (GET, POST, etc.)
    r"(?P<endpoint>\S+)\s+"  # Target request path
    r'[^"]*"\s+'  # HTTP version protocol (e.g., HTTP/1.1)
    r"(?P<status>\d{3})\s+"  # 3-digit HTTP status code
    r"(?P<bytes>\d+)"  # Response size in bytes
    r'(?:\s+"(?P<referer>[^"]*)")?'  # Optional Referer header
    r'(?:\s+"(?P<user_agent>[^"]*)")?'  # Optional User-Agent header
)


class LogParseError(Exception):
    """Raised when a log line fails format matching or field conversion."""


class LogParser:
    @staticmethod
    def parse_line(log_line: str) -> LogLine:
        match = NGINX_COMBINED_PATTERN.match(log_line)
        if not match:
            raise LogParseError(f"Log line does not match expected format: {log_line}")

        data = match.groupdict()

        try:
            timestamp = parse_timestamp(data["timestamp"])
            return LogLine(
                ip_address=data["ip"],
                timestamp=timestamp,
                endpoint=data["endpoint"],
                http_status=HTTPStatus(int(data["status"])),
                response_size=int(data["bytes"]),
                http_method=HTTPMethod(data["method"]),
                referer=data["referer"] or "",
                user_agent=data["user_agent"] or "",
            )
        except (ValueError, KeyError) as e:
            raise LogParseError(f"Error parsing log line fields: {e}") from e

    @profile_performance(name="Log Parsing")
    def parse_file(self, file_path: str) -> Iterator[LogLine]:
        """Yield parsed LogEntry instances line-by-line from a log file."""
        path = Path(file_path)

        with path.open("r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                if not raw_line.strip():
                    continue  # Skip empty lines
                try:
                    yield LogParser.parse_line(raw_line.strip())
                except LogParseError as e:
                    raise LogParseError(
                        f"Error parsing line {line_number} in {file_path}: {e}"
                    ) from e


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Parse Nginx log files.")
    parser.add_argument("logfile", help="Path to the log file to parse")
    args = parser.parse_args()

    log_parser = LogParser()
    try:
        for log_entry in log_parser.parse_file(args.logfile):
            print(log_entry)
    except LogParseError as e:
        print(f"Failed to parse log file: {e}")


if __name__ == "__main__":
    main()
